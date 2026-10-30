#!/usr/bin/env python3
"""What every part on the board is for, in plain words.

    python3 tools/roles.py            # coverage report, exit 1 if incomplete
    python3 tools/roles.py --write    # also write ref/parts-guide.md

tools/design.py says what is connected; this file says why. The text goes
into the schematic (symbol Description field, and each group's paragraph
inside its dashed box), into the PCB (footprint Description field, shown in
KiCad's properties panel) and into ref/parts-guide.md, the newcomer's tour.

Three kinds of entry, keyed by what design.py already makes stable:
  GROUP  one paragraph per schematic group (d.group name): what the block
         does for the board and where its values come from.
  PART   one entry per active part (ICs, connectors, crystals, LEDs,
         transistors, protection), keyed by reference: a short name used
         everywhere the part is mentioned, then one or two sentences.
  NET    notes on nets whose resistors or capacitors mean more than their
         topology says (straps, calibration resistors).
Resistors, capacitors, inductors and fuses get their line derived from the
nets on their two pins (bypass, pull-up, pull-down, series, filter), plus
any NET note and the group's main part. Anything the rules cannot place
falls back to its group paragraph.

`check()` fails on a group or active part with no text and on entries that
no longer match the design, so a part cannot enter the board unexplained.
Sheets listed in COVERED are enforced; the rest are reported.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUIDE = os.path.join(ROOT, 'ref', 'parts-guide.md')

# Sheets whose text is written and enforced (set below, after the text).
COVERED = set()

PASSIVE = {'Device:R', 'Device:C', 'Device:C_Polarized', 'Device:L',
           'Device:Polyfuse', 'Device:FerriteBead'}

# --------------------------------------------------------------- groups
GROUP = {
    # ---- FPGA sheet
    'U1  FPGA':
        'The FPGA is the board: every user design (a NEORV32 RISC-V core, '
        'a video pipeline, a protocol bridge) runs here. Its six user I/O '
        'banks are dedicated by job: bank 13 at 1.8 V carries the four PSRAMs '
        'and the two 5 V bus translators, bank 14 the configuration flash, '
        'the board-controller sideband, the 50 MHz clock, the SDRAM address '
        'bus, the MRAM and the microSD socket, banks 15 and 34 the direct '
        'extension slots A-D and E-H at a jumper-selected voltage, bank 16 '
        'the network at 2.5 V, bank 35 the HDMI output, the SDRAM data bus '
        'and the PHY reset/interrupt. Ball-by-ball list: ref/ballmap.md; '
        'constraints: ref/freya.xdc.',
    'config straps (UG470)':
        'How the FPGA loads its design at power-on. M[2:0] = 001 selects '
        'master SPI: the FPGA clocks its bitstream out of the W25Q256 flash '
        '(U6) by itself. The mode straps are 1 k, the most UG470 v1.17 Table '
        '2-4 allows. PROGRAM_B and INIT_B are pulled up so the board '
        'controller can restart configuration; PUDC_B is strapped high so '
        'the FPGA adds no pull-ups while it configures: every line that needs '
        'a level (PHY reset, SDRAM CS/CKE, MRAM and microSD CS, the 5 V bus '
        'OE, the PSRAM clock and data) has its own resistor, and nothing '
        'fights it. DONE lights D1 through Q4 once a design is running.',
    'GTP calibration':
        'The XC7A100T has two quads of multi-gigabit transceivers (GTP). '
        'Rev A uses none of them, but UG482 Tables 5-5 and 5-6 still want '
        'their supplies powered, their receive inputs grounded and one 100 '
        'ohm 1 % calibration resistor per quad to MGTAVTT. These two '
        'resistors are that.',
    'X4 system clock':
        'The FPGA\'s own clock. X4 runs at 50 MHz from power-on and enters '
        'bank 14 on a clock-capable (MRCC) ball, so it can feed an MMCM and '
        'make any frequency the design needs. Without it nothing in the '
        'fabric would run until a network link came up.',
    # ---- Network sheet
    'U30  gigabit PHY':
        'U30 is the Ethernet PHY: it turns the FPGA\'s RGMII bus (four data '
        'bits each way plus clock and control, 2.5 V, bank 16) into '
        '1000Base-T signals on the ETH jack\'s four twisted pairs. The FPGA '
        'still needs a MAC; the PHY handles the line, link negotiation and '
        'the analog side. It runs from +3V3, takes its RGMII pad supply from '
        '+2V5 and makes its own 1.0 V core supply with an internal LDO (the '
        'FD variant, so no inductor). The capacitors here bypass those '
        'supplies (RTL8211F datasheet rev 1.7, Table 9).',
    'PHY straps and LEDs':
        'Resistors that configure U30 at reset and drive its LEDs. During '
        'reset the PHY reads the level on several output pins as '
        'configuration: PHY address 1, PLL kept running, 2 ns clock delays '
        'on both RGMII directions (so the FPGA needs none), and an external '
        '2.5 V I/O supply (RTL8211F Tables 10 and 11). The same LED pins '
        'later drive the jack\'s LEDs, whose polarity follows the strap '
        '(section 7.9, Figure 5). Also here: the reset pull-down that holds '
        'the PHY in reset until the FPGA is configured, the interrupt and '
        'MDIO pull-ups. Full table: ref/network.md.',
    'ETH jack':
        'The Ethernet connector, with the 1000Base-T transformers and two '
        'LEDs built into the jack. The transformers isolate the cable from '
        'the board; the capacitor returns their centre taps to ground '
        '(ref/network.md).',
    'PHY clock':
        'The 25 MHz crystal U30 needs as its reference (RTL8211F Table 56: '
        '25 MHz, +/-50 ppm all in). The two capacitors set the crystal\'s '
        'load; the 0 ohm resistor is a placeholder to limit crystal drive if '
        'measurement shows it needs it.',
    'LINK P':
        'A board-to-board link port, not Ethernet. Four LVDS pairs from FPGA '
        'bank 16 go straight to an RJ45 so two boards can be cabled with '
        'shielded twisted pair: a clock and a data pair out, a clock and a '
        'data pair in. Cable LINK P of one board to LINK Q of the other, and '
        'power both boards before plugging in (ref/link-ports.md). The two '
        'arrays clamp ESD at the jack.',
    # ---- Video sheet
    'HDMI out':
        'A video output for monitors and TVs. Bank 35 drives the four HDMI '
        'lanes directly as TMDS_33 pairs, the standard Artix-7 way: the '
        'monitor\'s own 50 ohm pull-ups to 3.3 V terminate them, so the '
        'board adds none. 720p at 60 Hz fits comfortably; 1080p at 60 Hz '
        'does not. U31 sits at the connector: it clamps ESD on every line, '
        'shifts the DDC (EDID) and CEC lines between 3.3 V and the cable\'s '
        '5 V, buffers hot plug, and feeds the cable\'s 5 V pin through a 55 '
        'mA current limit (TI SLLSE96F, Figure 18). Its two enables are '
        'pulled on, so EDID works under any design. The unused utility pin '
        'goes to ground through 75 ohm, as TI\'s layout example asks.',
    'LINK Q':
        'The second link port, wired as the mirror of LINK P so a straight '
        'cable from a P to a Q connects outputs to inputs. Same rules: STP '
        'cable, power both boards first (ref/link-ports.md).',
}

# FPGA decoupling groups follow one pattern: `decap <supply>`.
SUPPLY = {
    'VCCINT': ('+1V0', 'the FPGA core logic'),
    'VCCBRAM': ('+1V0', 'the FPGA block RAM'),
    'VCCAUX': ('+1V8', 'the FPGA auxiliary circuits (clocking, I/O pre-drivers)'),
    'VCCADC': ('+1V8', 'the FPGA\'s on-chip ADC (XADC)'),
    'VCCO_0': ('+3V3', 'configuration bank 0'),
    '+1V0_MGT': ('+1V0_MGT', 'the unused but powered transceivers (MGTAVCC)'),
    '+1V2_MGT': ('+1V2_MGT', 'the unused but powered transceivers (MGTAVTT)'),
}

def _decap_group(g):
    sup = g[len('decap '):]
    if sup.startswith('VCCO group '):
        rail = sup[len('VCCO group '):]
        return (f'Bulk capacitor shared by every FPGA I/O bank powered from {rail}: '
                'UG483 Table 2-2 note 3 asks one 47 uF per group of up to four '
                'banks on one voltage. See ref/decoupling.md.')
    m = re.match(r'VCCO_(\d+)$', sup)
    if m and sup != 'VCCO_0':
        return (f'Decoupling for FPGA I/O bank {m.group(1)}\'s supply (VCCO): 2 x 4.7 uF '
                'and 4 x 0.47 uF, UG483 Table 2-2. They keep the bank\'s supply '
                'steady while its outputs switch. Placement rule: ref/decoupling.md.')
    rail, what = SUPPLY[sup]
    src = ('the MGT supplies are UG482\'s, not in UG483 Table 2-2: one 100 nF per '
           'ball plus 4.7 uF' if 'MGT' in sup else
           'quantities from UG483 Table 2-2, row FGG676 / XC7A100T' if sup != 'VCCADC'
           else 'not in UG483 Table 2-2; one 100 nF bypass')
    return (f'Decoupling for {sup} ({rail}), which powers {what}; {src}. '
            'Placement rule: ref/decoupling.md.')

# ---------------------------------------------------------------- parts
# ref -> (short name, what it does for the board)
PART = {
    'U1': ('FPGA',
           'Xilinx/AMD Artix-7 XC7A100T-2FGG676I: 101k logic cells, 4.9 Mb '
           'block RAM, 240 DSP slices. Runs whatever design you load; '
           'configures itself from U6 at power-on or is loaded by the board '
           'controller over JTAG.'),
    'D1': ('FPGA DONE LED',
           'Green LED, lit once the FPGA has finished loading a design.'),
    'Q4': ('DONE LED driver',
           'Small N-MOSFET that sinks D1\'s current when DONE goes high, so the '
           'LED never loads the FPGA\'s open-drain DONE pin.'),
    'X4': ('50 MHz FPGA clock',
           'YXC OT322550MJBA4SL 50 MHz CMOS oscillator: the fabric\'s '
           'always-running clock (SYS_CLK), into a bank 14 MRCC ball.'),
    'U30': ('gigabit Ethernet PHY',
            'Realtek RTL8211FD-CG: 10/100/1000Base-T transceiver between the '
            'FPGA\'s RGMII bus and the ETH jack. Managed over MDIO from the '
            'FPGA; reset and interrupt on bank 35 at 3.3 V.'),
    'U31': ('HDMI protection and level shifter',
            'TI TPD12S016: ESD clamps on the four HDMI pairs, DDC and CEC '
            'level shifting from 3.3 V to 5 V, hot plug buffer and a 55 mA '
            'current-limited 5 V for the cable.'),
    'J73': ('HDMI OUT jack',
            'Amphenol 10029449 HDMI type A socket: video out from FPGA bank '
            '35, DVI-compatible, 720p60 and below.'),
    'J70': ('ETH jack',
            'HanRun HR911130A RJ45 with 1000Base-T magnetics and green/yellow '
            'LEDs. Green: link and activity; yellow: 1000 Mb/s link.'),
    'X3': ('PHY 25 MHz crystal',
           'YXC X322525MOB4SI, 25 MHz, +/-10 ppm, 12 pF load: U30\'s reference '
           'clock.'),
    'J71': ('LINK P jack',
            'Plain shielded RJ45 (no magnetics) carrying four LVDS pairs of '
            'link port P. Not an Ethernet port.'),
    'J72': ('LINK Q jack',
            'Plain shielded RJ45 (no magnetics) carrying four LVDS pairs of '
            'link port Q, mirrored from P. Not an Ethernet port.'),
    'D20': ('LINK P ESD, pins 1-2 and 3-6',
            'TI TPD4E1U06 four-line ESD clamp (0.8 pF) on LINK P\'s outgoing '
            'clock and data pairs.'),
    'D21': ('LINK P ESD, pins 4-5 and 7-8',
            'TI TPD4E1U06 four-line ESD clamp (0.8 pF) on LINK P\'s incoming '
            'clock and data pairs.'),
    'D22': ('LINK Q ESD, pins 1-2 and 3-6',
            'TI TPD4E1U06 four-line ESD clamp (0.8 pF) on LINK Q\'s incoming '
            'clock and data pairs.'),
    # Passives whose derived line would mislead.
    'C244': (None, '18 pF load capacitor on the crystal\'s input side (X3, CL 12 pF '
                   'with about 3 pF stray: 2 x (12 - 3))'),
    'C245': (None, '18 pF load capacitor on the crystal\'s output side (X3)'),
    'R146': (None, '0 ohm in series with U30\'s crystal drive pin: a spot to fit a '
                   'resistor if the measured drive level exceeds 0.5 mW (Table 56)'),
    'C133': (None, '15 pF load capacitor on the 12 MHz crystal\'s input (RP-008280 section 4)'),
    'C134': (None, '15 pF load capacitor on the 12 MHz crystal\'s output (RP-008280 section 4)'),
    'D23': ('LINK Q ESD, pins 4-5 and 7-8',
            'TI TPD4E1U06 four-line ESD clamp (0.8 pF) on LINK Q\'s outgoing '
            'clock and data pairs.'),
}

# ----------------------------------------------------------------- nets
# Notes appended to the derived line of any R/C on that net.
NET = {
    'CFG_M0': 'mode pin M0 = 1: master SPI boot (UG470 Table 2-4, at most 1 k)',
    'CFG_M1': 'mode pin M1 = 0: master SPI boot (UG470 Table 2-4)',
    'CFG_M2': 'mode pin M2 = 0: master SPI boot (UG470 Table 2-4)',
    'CFG_PROG_B': 'keeps PROGRAM_B released; pulling it low restarts configuration',
    'CFG_INIT_B': 'keeps INIT_B released; it goes low on a configuration error',
    'PUDC_B': 'PUDC_B high: no I/O pull-ups during configuration, the external resistors set every line (UG470)',
    'DONE_LED_A': 'sets D1\'s current',
    'MGTRREF': 'calibration resistor for GTP quad 216 (UG482 Figure 5-1)',
    'MGTRREF_213': 'calibration resistor for GTP quad 213 (UG482 Table 5-5)',
    'SYS_CLK': 'damps ringing on the clock line',
    'SDRAM_CLK': 'damps ringing on the SDRAM clock (22 ohm at the FPGA)',
    'SD_CS': 'SPI mode: CS (DAT3) idles high so the card does not select',
    'SD_MOSI': 'SPI mode: CMD line idles high',
    'SD_MISO': 'SPI mode: DAT0 idles high',
    'SD_DAT1': 'unused DAT1 held high, as the SD specification asks in SPI mode',
    'SD_DAT2': 'unused DAT2 held high, as the SD specification asks in SPI mode',
    'MRAM_CS': 'keeps the MRAM deselected and tracking VDD during power-up (datasheet section 4)',
    'MRAM_WP': 'write protect released: writes to the status register allowed',
    'MRAM_HOLD': 'hold released: transfers never pause',
    'SDRAM_CS_N': 'keeps the SDRAM deselected until a design drives CS',
    'SDRAM_CKE': 'holds the SDRAM clock disabled (power-down) until a design drives CKE',
    'PHY_RSET': 'sets U30\'s transmit bias current (2.49 k 1 %, [verify] ref/network.md)',
    'PHY_1V0': 'U30\'s internal 1.0 V LDO output; feeds only its own core pins',
    'PHY_RESET_N': 'holds U30 in reset until the FPGA drives it (Table 53 note 5)',
    'PHY_INT_N': 'U30\'s open-drain interrupt (Table 4)',
    'PHY_MDIO': 'MDIO idle-high pull-up, 1.5 k (section 7.11.2)',
    'PHY_RXD3': 'strap PHYAD0 = 1: PHY address 1 (Table 10)',
    'PHY_RXC': 'strap PHYAD1 = 0 (Table 10)',
    'PHY_RX_CTL': 'strap PHYAD2 = 0 (Table 10)',
    'PHY_RXD2': 'strap PLLOFF = 0: PLL keeps running in power saving (Table 11)',
    'PHY_RXD1': 'strap TXDLY = 1: 2 ns transmit clock delay inside U30 (Table 11)',
    'PHY_RXD0': 'strap RXDLY = 1: 2 ns receive clock delay inside U30 (Table 11)',
    'PHY_LED0': 'strap CFG_EXT = 1: external RGMII pad supply (Table 11)',
    'PHY_LED1': 'strap CFG_LDO0 = 1, with CFG_LDO1 = 0: 2.5 V pads (Table 11)',
    'PHY_LED2': 'strap CFG_LDO1 = 0 (Table 11)',
    'ETH_LED_GREEN_A': 'current limit for the jack\'s green LED (LED0, active low)',
    'ETH_LED_YELLOW_K': 'current limit for the jack\'s yellow LED (LED2, active high)',
    'ETH_CT': 'returns the jack\'s transformer centre taps to ground ([verify] ref/network.md)',
}

# ---------------------------------------------- other sheets
GROUP.update({
    # ---- Power sheet
    'input OR-ing':
        'Where power enters. Two inputs feed one internal supply, VSYS: '
        'USB-C (5 V, or 9 V when a USB-PD charger agrees) and the J50 screw '
        'terminal (9-21 V). A diode on each (D3, D4) lets whichever is higher '
        'supply the board and stops one input from back-feeding the other. '
        'On the USB side, U26 is an electronic fuse: it ramps the voltage up '
        'gently so plugging in does not spark, cuts off above about 10 V or '
        'below 3.75 V, and limits current to about 2 A. D8 clamps voltage '
        'spikes on the screw input. VSYS then feeds the two main regulators.',
    'U34  +5V source select':
        'Chooses what feeds the +5V rail: USB power straight from the '
        'connector, or U11. A regulator cannot make 5 V out of 5 V, so on a '
        'plain 5 V USB source the mux passes VBUS to the rail. It hands the '
        'rail to U11 while the board controller asks the charger for 9 V and '
        'for a few seconds after (Q6), while the screw input is powered (Q7), '
        'and, as a backstop, if VBUS rises above about 5.6 V unasked or goes '
        'away. The choice is wired, not firmware: dividers and two small '
        'transistors. The chip blocks current flowing backwards into either '
        'source, limits the rail current to about 2.5 A and ramps it up '
        'gently. ST tells the board controller which source is in use.',
    'Q6  mux hold: 9 V request':
        'Keeps U34 on U11 around a 9 V negotiation. The controller\'s 9 V '
        'request charges a capacitor through D24 at once and the capacitor '
        'drains through its resistor in 2-7 s, so the rail leaves VBUS before '
        'the charger moves it and returns only when VBUS is back at 5 V. No '
        'voltage threshold can do that within the tolerances involved.',
    'Q7  mux hold: screw input present':
        'Keeps U34 on U11 whenever the screw input carries voltage, so a '
        'bench supply on J50 carries the whole board even with a 5 V USB '
        'cable plugged in; before, the USB port kept the 5 V load.',
    'U11  VSYS to +5V':
        'Switching regulator (buck converter) that makes +5V from VSYS. It '
        'runs whenever power is present (no enable), like U12, so the FPGA\'s '
        '1.8 V auxiliary supply is never missing while its 3.3 V banks are '
        'powered. Its output goes to the +5V rail through U34. +5V feeds the '
        '5 V buses, the extension 5 V pins and the four small regulators '
        'below. The two feedback resistors set the output voltage; the '
        'inductor and capacitors are its power stage; the 10 uF across its '
        'input is its own switching-current reservoir.',
    'U12  VSYS to +3V3  (always-on AP63300 reference circuit)':
        'Switching regulator that makes +3V3 from VSYS. It has no enable: it '
        'starts as soon as any power is present, because +3V3 runs the board '
        'controller, which then switches everything else on. Also powers the '
        'PSRAM, the flashes, the PHY and most logic. The two feedback '
        'resistors set 3.3 V; the inductor and capacitors are its power stage.',
    'U13  5V to +2V5':
        'Small switching regulator that makes +2V5 from +5V for FPGA bank 16 '
        '(network) and the PHY\'s RGMII pins. Enabled by the board controller '
        '(EN_2V5); the feedback resistors set 2.5 V.',
    'U14  5V to +1V8_IO':
        'Small switching regulator that makes 1.8 V from +5V. Its output '
        'node is +1V8_IO: FPGA bank 13 and the 1.8 V memory on it, the 1.8 V '
        'position of the J19/J20 jumpers, and, through the bead below, the '
        'FPGA\'s auxiliary supply (VCCAUX) and its ADC as +1V8. Its enable is '
        'tied to +5V, so it runs whenever U11 does: the FPGA\'s 3.3 V banks '
        'are never left on an unpowered VCCAUX (DS181 Table 7). The feedback '
        'resistors set 1.8 V; the 4.7 uF at VIN is its own input reservoir.',
    'VCCAUX filter':
        'The split between +1V8_IO and +1V8. VCCAUX and VCCADC are the '
        'FPGA\'s internal supplies (clocking, I/O pre-drivers, the XADC) and '
        'should not share copper with switching 1.8 V I/O loads, so they '
        'hang off U14\'s output through one ferrite bead (120 ohm at 100 '
        'MHz, 2 A, 50 mohm: 9 mV at the 0.18 A VCCAUX allowance, inside '
        'VCCAUX\'s 1.71 V minimum). The 10 uF and 100 nF sit at U14\'s '
        'output beside its own capacitors; VCCAUX keeps its UG483 decoupling '
        'on the +1V8 side.',
    'U16  5V to +1V2_MGT':
        'Small switching regulator that makes +1V2_MGT from +5V for the FPGA '
        'transceivers\' MGTAVTT supply. The transceivers are unused in rev A '
        'but must stay powered. Enabled by the board controller (EN_1V2).',
    'U15  5V to +1V0  (4A FPGA core supply)':
        'The FPGA core supply: up to 4 A at 1.0 V from +5V, the heaviest rail '
        'on the board. Enabled by the board controller (EN_1V0); its '
        'power-good output (CORE_1V0_GOOD) goes to the board controller '
        '(GPIO38) so firmware knows the core is up. The soft-start capacitor '
        'makes it ramp slowly; the feedback resistors set 1.0 V.',
    'MGTAVCC filter':
        'A small inductor and capacitor that make +1V0_MGT from +1V0: the '
        'same voltage, with the core\'s switching noise filtered out, for the '
        'transceivers\' MGTAVCC supply.',
    'extension power protection control':
        'Shared control for the four protected extension supplies (U21-U24). '
        'EXT_EN, from the board controller, turns them all on; the pull-down '
        'keeps them off until firmware decides. EXT_FAULT is pulled up and '
        'goes low if any of them (or the USB eFuse) detects a fault, so one '
        'controller pin hears all of them.',
    'U21  +5V to +5V_EXT':
        'Protected switch between the board\'s +5V and the 5 V pins of every '
        'extension port. Limits current to about 1 A and blocks current '
        'flowing back from an extension. Without it, a shorted extension '
        'would pull the whole board\'s 5 V down.',
    'U22  +3V3 to +3V3_EXT':
        'Protected switch between +3V3 and the 3.3 V pins of every extension '
        'port, limited to about 0.5 A, with reverse blocking. Keeps a faulty '
        'extension from taking down the board controller\'s supply.',
    'U23  VCCIO_1 to VCCIO_1_EXT':
        'Switch for the PIN V supply of slots A-D (the voltage chosen on '
        'J19). It is biased from +3V3 so it works down to the 1.8 V setting, '
        'blocks current flowing back in while off, ramps its output in about '
        '1.5 ms and shuts down when hot. Overload protection is each slot\'s '
        '500 mA fuse; the switch itself has no current limit.',
    'U24  VCCIO_2 to VCCIO_2_EXT':
        'Switch for the PIN V supply of slots E-H (the voltage chosen on '
        'J20). It is biased from +3V3 so it works down to the 1.8 V setting, '
        'blocks current flowing back in while off, ramps its output in about '
        '1.5 ms and shuts down when hot. Overload protection is each slot\'s '
        '500 mA fuse; the switch itself has no current limit.',
    'rail monitors':
        'Lets the board controller measure every supply. Each rail goes to '
        'one of its eight analog inputs (ADC), which read 0-3.3 V. Rails at '
        'or below 3.3 V go through a 1 k resistor that protects the pin; VSYS '
        'and +5V are higher, so two resistors divide them down first. A 100 '
        'nF capacitor on each input steadies the reading. MON_1V8 reads +1V8 '
        'itself, the FPGA\'s VCCAUX behind the bead, so an open bead shows; '
        'the two jumpered domains are measured so firmware knows how J19/J20 '
        'are set. +1V2_MGT is the one rail not measured. Firmware uses this '
        'to check each regulator came up before enabling the next.',
    'AUX IN':
        'Optional extra power for extensions that need more than 5 V (motors, '
        'LED strips, displays). Whatever you connect here (9-28 V DC) goes, '
        'unregulated, to the AUX pin of every extension port through each '
        'port\'s own fuse. The board itself never uses it.',
    # ---- Memory sheet
    'PSRAM0': 'Working-memory chip 0: 8 MB of fast RAM for the FPGA design, on its own '
              'four-bit (QSPI) bus to bank 13 at 1.8 V. The four chips are independent, so a '
              'design can use them in parallel. Notes: ref/psram.md.',
    'PSRAM1': 'Working-memory chip 1: 8 MB of RAM on its own QSPI bus to bank 13, at 1.8 V.',
    'PSRAM2': 'Working-memory chip 2: 8 MB of RAM on its own QSPI bus to bank 13, at 1.8 V.',
    'PSRAM3': 'Working-memory chip 3: 8 MB of RAM on its own QSPI bus to bank 13, at 1.8 V.',
    'config flash':
        'The FPGA\'s non-volatile memory. At power-on the FPGA reads its '
        'design (bitstream) from this 32 MB flash by itself (master SPI, set '
        'by the mode straps). The board controller can rewrite it through the '
        'series resistors on the Board Controller sheet, and spare space can '
        'hold user data or software for a soft CPU.',
    'U1 SDRAM clock source':
        'The 22 ohm resistor in the SDRAM clock line. It sits at the FPGA ball '
        'that drives the clock, so it damps the edge at its source; it is in '
        'U1\'s island, not the SDRAM\'s (findings 44).',
    'SDRAM':
        'A 32 MB SDR SDRAM (Winbond W9825G6KH-6, 16 bits wide, up to 166 '
        'MHz) for designs that outgrow the PSRAMs: a framebuffer, a soft '
        'CPU\'s main memory, a capture buffer. Its data and control lines '
        'come from bank 35 and its address lines from bank 14, both at 3.3 '
        'V. One 100 nF per VDD/VDDQ pin pair (seven, datasheet pins 1, 14, '
        '27 and 3, 9, 43, 49) and a 10 uF bulk; a 22 ohm series resistor at '
        'the FPGA damps the clock; CS is pulled up and CKE pulled down so '
        'the chip stays deselected and in power-down until a design drives '
        'them.',
    'MRAM':
        'A 128 KB non-volatile SPI memory (Everspin MR25H10CDF) that keeps '
        'its contents without power and has no write wear: settings, logs, '
        'a boot menu, a save file. CS is pulled up so '
        'the chip stays deselected while power comes up (datasheet section '
        '4); WP and HOLD are pulled up and not connected to the FPGA, so '
        'writes are allowed and transfers never pause. The exposed pad is '
        'ground only, with two vias under it. Four bank 14 lines at 3.3 V.',
    'microSD socket':
        'A push-push microSD socket (Hroparts TF-01A) wired for SPI mode: '
        'chip select on DAT3, data in on CMD, data out on DAT0, clock on '
        'CLK, five bank 14 lines at 3.3 V including the card-detect switch. '
        'The 10k pull-ups hold CS, the two data lines and the two unused '
        'DAT lines high, as the SD specification asks for SPI mode; the '
        '100 nF and 10 uF feed the card\'s supply at the socket; the shell '
        'is grounded. Cheap removable storage for a soft CPU: a filesystem, '
        'images to load into the PSRAMs, logs.',
    'U1 PSRAM0 series termination': 'One 33 ohm resistor per PSRAM0 line, placed next to the '
        'FPGA: they soften the fast signal edges so they do not ring along '
        'the trace. Values can be tuned after measurement (ref/psram.md).',
    'U1 PSRAM1 series termination': 'One 33 ohm resistor per PSRAM1 line, next to the FPGA, to damp ringing.',
    'U1 PSRAM2 series termination': 'One 33 ohm resistor per PSRAM2 line, next to the FPGA, to damp ringing.',
    'U1 PSRAM3 series termination': 'One 33 ohm resistor per PSRAM3 line, next to the FPGA, to damp ringing.',
    'PSRAM0 power-up state': 'Six 10k resistors at the PSRAM0 pins: CE# pulled up to its own '
        'supply, clock and the four data lines pulled down. The chip requires these '
        'levels from the first moment of its supply ramp until 150 us after it, and '
        'an unconfigured FPGA leaves its pins floating, so resistors, not the FPGA, '
        'guarantee them (APS6404L section 8, findings 39).',
    'PSRAM1 power-up state': 'Six 10k resistors at the PSRAM1 pins: CE# up, clock and data down, from power-up (APS6404L section 8).',
    'PSRAM2 power-up state': 'Six 10k resistors at the PSRAM2 pins: CE# up, clock and data down, from power-up (APS6404L section 8).',
    'PSRAM3 power-up state': 'Six 10k resistors at the PSRAM3 pins: CE# up, clock and data down, from power-up (APS6404L section 8).',
    # ---- Board Controller (Supervisor) sheet
    'U7  USB series resistors':
        'Two 27 ohm resistors in the USB data lines, right at the board '
        'controller, as Raspberry Pi\'s hardware design guide (section 5.1) '
        'asks. The ESD clamp D6 stays at the connector.',
    'U7  board controller':
        'The board controller, a Raspberry Pi RP2350B microcontroller that is '
        'always on. It is what the USB cable talks to: it loads designs into '
        'the FPGA over JTAG or writes them to the FPGA\'s flash, turns the '
        'supplies on in order and watches them, asks a USB-PD charger for '
        '9 V, enables extension power, and gives the FPGA a debug and UART '
        'link. One 100 nF capacitor per supply pin (RP-008280 section 2.2.1).',
    'U7 core regulator (RP-008280 s2.1)':
        'Parts for the RP2350\'s built-in switching regulator, which makes its '
        '1.1 V core supply (+1V1) from +3V3. Values and the inductor are the '
        'ones Raspberry Pi specifies in their hardware design guide '
        '(RP-008280 section 2.1).',
    'crystal (RP-008280 s4)':
        'The board controller\'s 12 MHz clock: the exact crystal, load '
        'capacitors and 1 k drive-limiting resistor Raspberry Pi specifies '
        '(RP-008280 section 4).',
    'RUN':
        'The board controller\'s reset input. The pull-up keeps it running; '
        'the capacitor holds it in reset briefly at power-on until +3V3 is '
        'stable.',
    'board controller startup memory':
        'The board controller\'s own 4 MB flash, holding its firmware. '
        'Separate from the FPGA\'s flash.',
    'USB-C':
        'The main connector: power in, and the USB link to your computer for '
        'programming and talking to the board.',
    'USB protection':
        'Clamps for static discharge and voltage spikes on the USB connector: '
        'D6 on the data and CC lines, D7 on the power line (VBUS).',
    'USB-PD sink':
        'Negotiates the supply voltage with a USB-PD charger. Out of the box '
        'it asks for 5 V: CFG1 is pulled up to the chip\'s own 3.3 V and '
        'CFG2/CFG3 are grounded, so the only other request the pins can form '
        'is 9 V, which the board controller selects by turning Q3 on '
        '(PD_REQ_9V). A dead or resetting controller leaves it at 5 V. PD_PG '
        'tells the controller whether the charger agreed.',
    'BOOTSEL':
        'Hold CTRL BOOT while plugging in USB to put the board controller in '
        'its built-in USB bootloader, for installing or recovering its '
        'firmware. The 1 k resistor lets the button win without fighting the '
        'chip. The 10 k pull-up is not fitted, as in Raspberry Pi\'s design.',
    'board controller SWD':
        'Debug connector for the board controller\'s own processor (SWD): for '
        'developing its firmware with a debug probe. Not for the FPGA.',
    'series resistors to FPGA':
        'One 33 ohm resistor on every wire between the board controller and '
        'the FPGA: JTAG, the configuration pins, the FPGA flash bus, the '
        'debug sideband and the UART. They limit current if both sides ever '
        'drive the same wire at once, and damp ringing.',
    'JTAG owner selection':
        'Decides who programs the FPGA over JTAG. Normally (J52 open) the '
        'board controller does, through the U20 switch. Fit a jumper on J52 '
        'and U20 disconnects the board controller completely, so an external '
        'programmer plugged into J2 has the FPGA to itself. A jumper, not '
        'software, so it works even when the board controller is broken.',
    'manual JTAG header':
        'Standard 2x5 JTAG header for an external FPGA programmer (Xilinx/AMD '
        'cable or similar). Fit J52 first.',
    'board status LEDs':
        'Three green LEDs on board controller GPIO35-37, lit by driving the '
        'pin low: CTRL HB blinks while the board controller firmware is '
        'alive; USER 1 and USER 2 are for software. Each has a 1 k '
        'current-limiting resistor from +3V3. Rules: ref/status-leds.md.',
    # ---- Slots sheet
    'SHIELD HEADER ABCD':
        'One long 2x32 socket on the right edge carrying the signals of slots '
        'A, B, C and D: twelve FPGA pins each (bank 15), with grounds between '
        'groups. Their voltage is whatever J19 selects.',
    'SHIELD HEADER EFGH':
        'One long 2x32 socket on the left edge carrying the signals of slots '
        'E, F, G and H: twelve FPGA pins each (bank 34), voltage set by J20.',
    'SHIELD HEADER L':
        'The signal socket of slot L (5V BUS 0): eight 5 V data lines from U9, '
        'with four grounds between them.',
    'SHIELD HEADER M':
        'The signal socket of slot M (5V BUS 1): eight 5 V data lines from '
        'U10, with four grounds between them.',
    '5V BUS 0 converter':
        'Lets the FPGA (3.3 V) talk to 5 V extensions on slot L. U9 shifts '
        'eight lines between 3.3 V and 5 V, all in one direction at a time '
        '(BUS5V0_DIR). It stays off until the FPGA pulls BUS5V0_OE_N low; the '
        'pull-up keeps the bus off while the FPGA is still loading.',
    '5V BUS 1 converter':
        'Same as 5V BUS 0, for slot M: U10 shifts eight lines between the '
        'FPGA\'s 3.3 V and 5 V, direction BUS5V1_DIR, off until BUS5V1_OE_N '
        'goes low.',
    'VCCIO_1 selector':
        'Jumper that picks the signal voltage of slots A-D: one shunt on '
        'J19 selects 3.3, 2.5 or 1.8 V. It powers FPGA bank 15 and the PIN V '
        'pin of those four slots. One position only; change it with the '
        'board unpowered.',
    'VCCIO_2 selector':
        'Jumper that picks the signal voltage of slots E-H (J20): 3.3, 2.5 or '
        '1.8 V for FPGA bank 34 and those slots\' PIN V pin.',
})
for _s in 'ABCDEFGHLM':
    _v = ('3.3 V' if _s in 'LM' else
          'the J19 voltage' if _s in 'ABCD' else 'the J20 voltage')
    GROUP[f'SLOT {_s} branches'] = (
        f'Power for whatever is plugged into slot {_s}. The 1x7 power socket '
        f'carries PIN V ({_v}), 3.3 V, 5 V and AUX, each beside a ground, and '
        'each through its own resettable fuse, so a short on one extension '
        'trips only that slot\'s fuse and the rest of the board keeps running. '
        'The long grounded pin in front of the socket is the key that stops '
        'an extension going in the wrong way, and a ground probe point.')

PART.update({
    'J50': ('POWER IN screw terminal', 'Main power input, 9-21 V DC. Polarity marked on the board.'),
    'U26': ('USB input eFuse', 'TI TPS259470A: ramps USB power in gently, cuts off outside 3.75-10 V, limits current to about 2 A, blocks reverse current. Reports faults on EXT_FAULT.'),
    'D3': ('USB input diode', 'SS34 Schottky diode: lets USB power reach VSYS and stops the screw input feeding back into USB.'),
    'D4': ('screw input diode', 'SS34 Schottky diode: lets the screw input reach VSYS and stops USB feeding back into it.'),
    'D8': ('screw input surge clamp', 'SMBJ22A TVS diode: absorbs voltage spikes on the screw input above about 24 V.'),
    'U34': ('+5V source mux', 'TI TPS2121 power mux: passes plain 5 V USB straight to the +5V rail; hands the rail to U11 while the board controller asks for 9 V (Q6), while the screw input is powered (Q7), or if VBUS goes above about 5.6 V or away. Blocks reverse current both ways, limits to about 2.5 A.'),
    'Q3': ('9 V request switch', 'Small N-MOSFET the board controller (PD_REQ_9V) uses to pull the CH224K\'s CFG1 low and ask the charger for 9 V. Off: 5 V.'),
    'Q6': ('mux: 9 V request hold', 'Small N-MOSFET that pulls U34\'s PR1 to ground while the board controller asks for 9 V and for 2-7 s after it stops (D24, R, C hold), so the +5V rail is on U11 before VBUS moves and until it is back at 5 V.'),
    'D24': ('mux hold diode', '1N4148W: charges the Q6 hold capacitor from PD_REQ_9V at once and lets it drain slowly through its own resistor.'),
    'Q7': ('mux: screw input present', 'Small N-MOSFET that pulls U34\'s PR1 to ground while the screw input (J50) carries voltage, so the whole board runs from J50 through U11 even with a 5 V USB cable plugged in.'),
    'U11': ('5 V regulator, always on', 'Diodes AP63300, 3 A switching regulator: VSYS to +5V_BUCK, then U34 to +5V. Starts by itself.'),
    'U12': ('3.3 V regulator, always on', 'Diodes AP63300, 3 A switching regulator: VSYS to +3V3. Starts by itself.'),
    'U13': ('2.5 V regulator', 'TI TLV62569, 2 A switching regulator: +5V to +2V5.'),
    'U14': ('1.8 V regulator, always on', 'TI TLV62569, 2 A switching regulator: +5V to +1V8_IO (bank 13, the 1.8 V memory) and, through FB1, +1V8 (VCCAUX, VCCADC). Enable tied to +5V.'),
    'U16': ('1.2 V transceiver regulator', 'TI TLV62569, 2 A switching regulator: +5V to +1V2_MGT.'),
    'U15': ('FPGA core regulator', 'Silergy SY8047, 4 A switching regulator: +5V to +1V0 for the FPGA core, with power-good output.'),
    'U21': ('extension 5 V switch', 'TI TPS22950C load switch: +5V to every slot\'s 5 V pin, about 1 A limit, reverse blocking.'),
    'U22': ('extension 3.3 V switch', 'TI TPS22950C load switch: +3V3 to every slot\'s 3.3 V pin, about 0.5 A limit.'),
    'U23': ('slots A-D PIN V switch', 'TI TPS22953 load switch, biased from +3V3 so it works at 1.8 V: VCCIO_1 to the PIN V pin of slots A-D. Blocks reverse current while off; the slot fuses limit the current.'),
    'U24': ('slots E-H PIN V switch', 'TI TPS22953 load switch, biased from +3V3 so it works at 1.8 V: VCCIO_2 to the PIN V pin of slots E-H. Blocks reverse current while off; the slot fuses limit the current.'),
    'J68': ('AUX IN screw terminal', 'Optional 9-28 V DC input feeding only the AUX pin of every extension port, unregulated. Your supply, your current limit.'),
    'U2': ('PSRAM 0', 'AP Memory APS6404L-SQN, 64 Mbit (8 MB) QSPI pseudo-static RAM, 1.8 V, on bank 13.'),
    'U3': ('PSRAM 1', 'AP Memory APS6404L-SQN, 8 MB QSPI RAM, 1.8 V, on bank 13.'),
    'U4': ('PSRAM 2', 'AP Memory APS6404L-SQN, 8 MB QSPI RAM, 1.8 V, on bank 13.'),
    'U5': ('PSRAM 3', 'AP Memory APS6404L-SQN, 8 MB QSPI RAM, 1.8 V, on bank 13.'),
    'J74': ('microSD socket', 'Hroparts TF-01A push-push microSD socket, SPI mode to FPGA bank 14 at 3.3 V; card detect on the switch.'),
    'U33': ('SPI MRAM', 'Everspin MR25H10CDF, 1 Mbit (128 KB) SPI MRAM, 3.3 V, DFN-8: non-volatile, unlimited writes; bank 14.'),
    'U32': ('SDRAM', 'Winbond W9825G6KH-6, 256 Mbit (32 MB) 16-bit SDR SDRAM, 3.3 V, TSOP-54: bank 35 data and control, bank 14 address.'),
    'U6': ('FPGA configuration flash', 'Winbond W25Q256JV, 256 Mbit (32 MB) quad-SPI flash: the FPGA boots from it.'),
    'U7': ('board controller', 'Raspberry Pi RP2350B microcontroller (two Cortex-M33 cores, 150 MHz): USB, FPGA programming, power sequencing and monitoring.'),
    'Y1': ('controller 12 MHz crystal', 'Abracon ABM8-272-T3, the crystal Raspberry Pi specifies for the RP2350.'),
    'U8': ('controller firmware flash', 'Winbond W25Q32JV, 32 Mbit (4 MB) quad-SPI flash holding the board controller\'s firmware.'),
    'J1': ('USB-C connector', 'Power in and USB 2.0 data to the board controller.'),
    'D6': ('USB data ESD clamp', 'ST ESDA6V1BC6: clamps static discharge on D+, D-, CC1 and CC2.'),
    'D7': ('USB power surge clamp', 'SMBJ13A TVS diode: clamps spikes on VBUS above about 14 V.'),
    'U18': ('USB-PD negotiator', 'WCH CH224K: asks a USB-PD charger for 5 V by default, or 9 V when the board controller turns Q3 on. Its pins cannot form any higher request.'),
    'SW1': ('CTRL BOOT button', 'Hold while plugging in USB to enter the board controller\'s USB bootloader.'),
    'J51': ('CTRL SWD connector', '3-pin JST-SH debug port for the board controller\'s processor.'),
    'U20': ('JTAG switch', 'TI SN74CB3Q3384 bus switch: connects or isolates the board controller\'s JTAG from the FPGA, set by J52.'),
    'J52': ('EXT JTAG jumper', 'Fit a shunt to hand the FPGA\'s JTAG to an external programmer on J2.'),
    'J2': ('FPGA JTAG header', '2x5 keyed header for an external FPGA programmer.'),
    'D9': ('CTRL HB LED', 'Green LED: blinks while the board controller firmware runs.'),
    'D10': ('USER 1 LED', 'Green LED for software use.'),
    'D11': ('USER 2 LED', 'Green LED for software use.'),
    'U9': ('5V BUS 0 translator', 'TI SN74LXC8T245: 8-bit 3.3 V to 5 V level shifter with direction control, for slot L.'),
    'U10': ('5V BUS 1 translator', 'TI SN74LXC8T245: 8-bit 3.3 V to 5 V level shifter with direction control, for slot M.'),
    'J3': ('slots A-D signal socket', '2x32 female socket, right edge: signals of slots A, B, C, D.'),
    'J5': ('slots E-H signal socket', '2x32 female socket, left edge: signals of slots E, F, G, H.'),
    'J7': ('slot L signal socket', '2x8 female socket: 5V BUS 0 data lines.'),
    'J8': ('slot M signal socket', '2x8 female socket: 5V BUS 1 data lines.'),
    'J19': ('A-D PIN VOLTAGE jumper', '2x3 header: one shunt selects 3.3, 2.5 or 1.8 V for slots A-D.'),
    'J20': ('E-H PIN VOLTAGE jumper', '2x3 header: one shunt selects 3.3, 2.5 or 1.8 V for slots E-H.'),
})
for _s, _j in {'A':'J53', 'B':'J62', 'C':'J54', 'D':'J63', 'E':'J55',
               'F':'J64', 'G':'J56', 'H':'J65', 'L':'J57', 'M':'J58'}.items():
    PART[_j] = (f'slot {_s} power socket',
                '1x7 female socket: PIN V, 3.3 V, 5 V and AUX for the extension, each beside a ground.')
    PART[f'MK{ord(_s)}'] = (f'slot {_s} key post',
                            'Long grounded pin in front of the power socket: keys the extension so it fits one way only, and doubles as a ground probe point.')

NET.update({
    'VBUS_UVLO': 'sets U26\'s turn-on voltage, 3.75 V',
    'VBUS_OVLO': 'sets U26\'s cut-off voltage, about 10 V',
    'VBUS_ILM': 'sets U26\'s current limit, about 2 A',
    'VBUS_DVDT': 'sets how slowly U26 ramps VSYS up, about 0.9 V/ms',
    'VBUS5_PR1': 'U34 priority sense: VBUS wins above 4.44 V (PR1 above CP2) unless Q6 (9 V request) or Q7 (screw input present) holds it at ground',
    'SEL_IN2': 'Q6\'s gate: charged from PD_REQ_9V through D24, drains through 470k/10 uF in 2-7 s',
    'EXT_PRESENT': 'Q7\'s gate: 100k/33k from the screw input, on above 3.2-6 V of VIN_EXT',
    'VBUS5_CP2': 'U34 comparison level, 1.19 V from +3V3; enables the 5 us switchover',
    'VBUS5_OV1': 'U34 VBUS overvoltage backstop: VBUS is dropped above 5.3-5.9 V (5.63 V typical) if a source raises it unasked',
    'VBUS5_ILIM': 'sets U34\'s current limit, about 2.5 A',
    'VBUS5_SS': 'sets how fast U34 ramps the +5V rail, about 780 V/s',
    'VBUS5_ST': 'U34 status to the board controller: low when U11 feeds +5V',
    'PD_CFG1': 'CH224K request: high (pull-up) = 5 V, pulled low by Q3 = 9 V',
    'PD_REQ_9V': 'Q3\'s gate; off (5 V) unless the board controller drives it high',
    'USB_DP_MCU': 'USB D+ at the controller, after its 27 ohm series resistor',
    'USB_DM_MCU': 'USB D- at the controller, after its 27 ohm series resistor',
    'CORE_1V0_GOOD': 'U15 power-good, read by the board controller (GPIO38)',
    'CORE_1V0_SS': 'U15 soft-start: slows the core supply\'s ramp',
    'CORE_1V0_SVIN': 'filtered supply for U15\'s control circuit',
    'EXT_EN': 'from the board controller: turns extension power on; off by default',
    'EXT_FAULT': 'shared fault line, low when a protected supply trips',
    'PD_PG': 'CH224K: high when the charger accepted the request',
    'PD_VDD': 'CH224K\'s internal regulator output',
    'SUP_RUN': 'board controller reset',
    'SUP_VREG_AVDD': 'filtered analog supply for the RP2350\'s regulator',
    'SUP_XOUT': 'limits the crystal drive level (RP-008280)',
    'SUP_XIN': 'crystal input',
    'SUP_XTAL_OUT': 'crystal output, after the drive-limit resistor',
    'BOOTSEL_SW': 'button side of the BOOTSEL resistor',
    'SUPF_CS': 'controller flash chip-select; pulled low by CTRL BOOT for the bootloader',
    'EXTERNAL_JTAG_SELECTED': 'high when J52 is fitted: U20 disconnects the board controller',
    'JTAG_TDO_SW': 'probe point between the FPGA\'s TDO and U20',
})
NET_PREFIX = {
    'FB_': 'feedback divider, sets the regulator\'s output voltage',
    'FB+': 'feedback divider, sets the regulator\'s output voltage',
    'SW_': 'regulator switching node',
    'SW+': 'regulator switching node',
    'BOOT_': 'bootstrap capacitor for the regulator\'s high-side switch',
    'EN_': 'keeps the regulator off until the board controller enables it',
    'MON_': 'rail monitor input to the board controller\'s ADC',
    'PSRAM': 'damps ringing on the PSRAM line (ref/psram.md)',
    'BUS5V': 'keeps the 5 V bus translator disabled until the FPGA enables it',
    'LED_': 'LED current limit',
    'U2': 'sets the switch\'s current limit (TI equation in design.py)',
    'U23_CT': 'sets how fast U23 ramps its output, about 1.5 ms (TPS22953 CT)',
    'U24_CT': 'sets how fast U24 ramps its output, about 1.5 ms (TPS22953 CT)',
    'SUP_': 'board controller to FPGA link (33 ohm series)',
}
COVERED = {'FPGA', 'Network', 'Power', 'Memory', 'Supervisor', 'Slots', 'Video'}


# Nets that are supplies, for telling a bypass capacitor from a filter one.
def _is_supply(n):
    if n.startswith('MON_'): return False         # a measurement, not a supply
    return (n.startswith('+') or n in ('VSYS', 'VBUS', 'PD_VDD', 'SUP_VREG_AVDD', 'AUX_RAIL',
                                       'PHY_1V0') or
            re.match(r'VCCIO_\d(_EXT)?$', n) is not None or
            re.search(r'_(3V3|5V|PIN_VOLTAGE|AUX|VCC)$', n) is not None)


def _named(q):
    return f"{q['ref']} ({PART[q['ref']][0]})" if q['ref'] in PART else q['ref']


def _net_note(n):
    if n in NET: return NET[n]
    hits = [k for k in NET_PREFIX if n.startswith(k)]
    return NET_PREFIX[max(hits, key=len)] if hits else None


def _is_pull(net):
    """A resistor on this net is a pull (default level), not a load or a
    reference: active-low lines, straps, and any net without its own note."""
    return (_net_note(net) is None or net.endswith(('_N', '_B', '_MDIO')) or
            net.startswith(('EN_', 'BUS5V', 'EXT_', 'PD_PG', 'SUP_RUN')) or
            net.startswith(('PHY_RX', 'PHY_LED', 'CFG_', 'PUDC')))


def _hub(part, by_group, by_net):
    """Who this passive serves. A signal part names the active part it shares
    a signal net with; a bypass part names its group's main active part."""
    sig = [n for n in part['pins'].values() if n != 'GND' and not _is_supply(n)]
    # U1 touches nearly every signal; name it only when nothing else does.
    sharers = [q for n in sig for q in by_net.get(n, [])
               if q['lib_id'] not in PASSIVE and q['ref'] != part['ref']]
    for q in sorted(sharers, key=lambda q: (q['ref'] == 'U1', q['ref'].startswith('MK'))):
        return _named(q)
    if sig:
        return None
    rank = lambda q: ('U', 'J', 'X', 'Y', 'Q', 'D', 'SW', 'MK').index(
        re.match(r'[A-Z]+', q['ref']).group()) if re.match(r'[A-Z]+', q['ref']).group() in \
        ('U', 'J', 'X', 'Y', 'Q', 'D', 'SW', 'MK') else 9
    act = [q for q in by_group.get(part['group'], []) if q['lib_id'] not in PASSIVE]
    return _named(min(act, key=rank)) if act else None


def derive(part, by_group, by_net):
    """One line for a resistor, capacitor, inductor or fuse."""
    nets = sorted(set(part['pins'].values()))
    v = part['value']
    kind = {'R': 'resistor', 'C': 'capacitor', 'L': 'inductor', 'F': 'fuse'}.get(
        re.match(r'[A-Z]+', part['ref']).group()[0], 'part')
    note = '; '.join(dict.fromkeys(filter(None, (_net_note(n) for n in nets))))
    hub = _hub(part, by_group, by_net)
    g = part['group']
    if g.endswith('power-up state'):
        sig = [n for n in nets if n != 'GND' and not _is_supply(n)][0]
        if 'CE_B' in sig:
            return (f'{v} pull-up of {sig} to +1V8_IO, for {hub}: CE# high and tracking VDD '
                    'from power-up until the FPGA drives it (APS6404L section 8)')
        return (f'{v} pull-down on {sig}, for {hub}: holds the line low from power-up '
                'until the FPGA drives it (APS6404L section 8)')
    if g.startswith('decap '):
        rail = nets[0] if nets[0] != 'GND' else nets[-1]
        where = g[6:] if g[6:] == rail else f'{g[6:]} ({rail})'
        return f'{v} FPGA decoupling on {where}, UG483'
    if len(nets) == 1:
        line = f'{v} {kind} with both ends on {nets[0]}'
    else:
        a, b = nets[0], nets[1]
        if 'GND' in nets:
            other = b if a == 'GND' else a
            if kind == 'capacitor':
                line = (f'{v} bypass on {other}' if _is_supply(other)
                        else f'{v} capacitor from {other} to GND' if other in NET
                        else f'{v} filter capacitor on {other}')
            elif kind == 'resistor':
                line = (f'{v} pull-down on {other}' if _is_pull(other)
                        else f'{v} resistor from {other} to GND')
            else:
                line = f'{v} {kind} from {other} to GND'
        elif kind == 'resistor' and (_is_supply(a) != _is_supply(b)):
            sig, rail = (b, a) if _is_supply(a) else (a, b)
            line = (f'{v} pull-up of {sig} to {rail}' if _is_pull(sig)
                    else f'{v} resistor from {sig} to {rail}')
        elif kind == 'resistor':
            line = f'{v} series resistor between {a} and {b}'
        elif kind == 'fuse':
            src, out = (a, b) if a.startswith('+') or a == 'AUX_RAIL' else (b, a)
            line = f'{v} resettable fuse feeding {out} from {src}'
        else:
            line = f'{v} {kind} between {a} and {b}'
    if hub and 'decoupling' not in line:
        line += f', for {hub}'
    return line + (f': {note}' if note else '')


def group_role(g):
    if g in GROUP: return GROUP[g]
    if g.startswith('decap '): return _decap_group(g)
    return None


def part_role(part, by_group, by_net):
    """-> (short name or None, sentence)."""
    if part['ref'] in PART:
        return PART[part['ref']]
    if part['lib_id'] in PASSIVE:
        return None, derive(part, by_group, by_net)
    return None, None


def annotate(parts):
    """Add 'role' (one line) and 'group_role' to every part dict in place."""
    by_group, by_net = {}, {}
    for p in parts:
        by_group.setdefault(p['group'], []).append(p)
        for n in set(p['pins'].values()): by_net.setdefault(n, []).append(p)
    for p in parts:
        name, text = part_role(p, by_group, by_net)
        p['role_name'] = name
        p['role'] = (f'{name}: {text}' if name and text else text) or ''
        if p.get('dnp') and p['role']:
            p['role'] = 'NOT FITTED. ' + p['role']
        p['group_role'] = group_role(p['group']) or ''
    return parts


def check(parts):
    """-> (problems that fail, gaps reported only)."""
    probs, gaps = [], []
    refs = {p['ref'] for p in parts}
    groups = {p['group'] for p in parts}
    for p in parts:
        bucket = probs if p['sheet'] in COVERED else gaps
        if not group_role(p['group']):
            bucket.append(f"group '{p['group']}' ({p['sheet']}) has no paragraph")
        if p['lib_id'] not in PASSIVE and p['ref'] not in PART:
            bucket.append(f"{p['ref']} {p['value']} ({p['sheet']}) has no PART entry")
    probs = sorted(set(probs)); gaps = sorted(set(gaps))
    probs += [f'PART entry {r} is not in the design' for r in PART if r not in refs]
    probs += [f"GROUP entry '{g}' is not in the design" for g in GROUP if g not in groups]
    nets = {n for p in parts for n in p['pins'].values()}
    probs += [f'NET note {n} is not a net in the design' for n in NET if n not in nets]
    return probs, gaps


# ---------------------------------------------------------------- guide
SHEET_ORDER = ['FPGA', 'Power', 'Memory', 'Supervisor', 'Slots', 'Network', 'Video']
SHEET_INTRO = {
    'FPGA': 'The Artix-7 itself, its decoupling, how it boots and its clock.',
    'Power': 'Inputs, the regulators that make every rail, extension power protection.',
    'Memory': 'Four PSRAM chips for working memory and the flash the FPGA boots from.',
    'Supervisor': 'The RP2350B board controller: USB, power sequencing, programming the FPGA.',
    'Slots': 'The ten extension ports: connectors, per-slot fuses, 5 V level shifting.',
    'Network': 'Gigabit Ethernet (PHY and jack) and the two raw LVDS link ports.',
    'Video': 'HDMI output straight from the FPGA, with its protection chip.',
}


def guide(parts):
    o = ['# Parts guide', '',
         '**Generated by `tools/roles.py --write` from `tools/design.py` and the',
         'text in `tools/roles.py`. Do not hand-edit; change the text there.**', '',
         'What every part on the board is for. The same text is in the schematic',
         '(hover a symbol, or read the paragraph in each dashed group box) and in',
         'the PCB (select a footprint, Description field). Start with the sheet',
         'you care about; within it, groups appear in schematic order.', '']
    for sh in SHEET_ORDER:
        sp = [p for p in parts if p['sheet'] == sh]
        if not sp: continue
        o += [f'- [{sh}](#{sh.lower()}) ({len(sp)} parts): {SHEET_INTRO[sh]}']
    o.append('')
    for sh in SHEET_ORDER:
        sp = [p for p in parts if p['sheet'] == sh]
        if not sp: continue
        o += [f'## {sh}', '', SHEET_INTRO[sh], '']
        order = []
        for p in sp:
            if p['group'] not in order: order.append(p['group'])
        for g in order:
            gp = [p for p in sp if p['group'] == g]
            o += [f'### {g}', '']
            o += [gp[0]['group_role'] or '_No description yet._', '']
            o += ['| Ref | Value | What it does |', '|---|---|---|']
            act = [p for p in gp if p['lib_id'] not in PASSIVE]
            pas = [p for p in gp if p['lib_id'] in PASSIVE]
            key = lambda p: (re.match(r'[A-Z]+', p['ref']).group(), int(re.search(r'\d+', p['ref']).group()))
            for p in sorted(act, key=key) + sorted(pas, key=key):
                val = p['value'].replace('|', '/')
                o.append(f"| {p['ref']} | {val} | {p['role'].replace('|', '/') or '_not yet described_'} |")
            o.append('')
    return '\n'.join(o) + '\n'


def main():
    from design import build
    import io, contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        parts = annotate(build().parts)
    probs, gaps = check(parts)
    total = len(parts)
    done = sum(1 for p in parts if p['role'])
    print(f'{done}/{total} parts described; {len(gaps)} gaps on uncovered sheets '
          f'({", ".join(s for s in SHEET_ORDER if s not in COVERED)})')
    for p in probs: print('PROBLEM', p)
    if '--write' in sys.argv:
        open(GUIDE, 'w').write(guide(parts))
        print(f'wrote {os.path.relpath(GUIDE, ROOT)}')
    return 1 if probs else 0


if __name__ == '__main__':
    sys.exit(main())
