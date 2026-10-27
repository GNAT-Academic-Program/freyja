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

# Sheets whose text is written and enforced. The others are reported only.
COVERED = {'FPGA', 'Network'}

PASSIVE = {'Device:R', 'Device:C', 'Device:C_Polarized', 'Device:L',
           'Device:Polyfuse', 'Device:FerriteBead'}

# --------------------------------------------------------------- groups
GROUP = {
    # ---- FPGA sheet
    'U1  FPGA':
        'The FPGA is the board: every user design (a NEORV32 RISC-V core, '
        'a video pipeline, a protocol bridge) runs here. Its six user I/O '
        'banks are dedicated by job: bank 13 drives the two 5 V buses and '
        'the PHY reset/interrupt, bank 14 the PSRAM, the configuration flash, '
        'the board-controller sideband and the 50 MHz clock, banks 15 and 34 '
        'the direct extension slots A-D and E-H at a jumper-selected voltage, '
        'bank 16 the network at 2.5 V, bank 35 nothing. Ball-by-ball list: '
        'ref/ballmap.md; constraints: ref/freya.xdc.',
    'config straps (UG470)':
        'How the FPGA loads its design at power-on. M[2:0] = 001 selects '
        'master SPI: the FPGA clocks its bitstream out of the W25Q256 flash '
        '(U6) by itself. The mode straps are 1 k, the most UG470 v1.17 Table '
        '2-4 allows. PROGRAM_B and INIT_B are pulled up so the board '
        'controller can restart configuration; PUDC_B is strapped low so I/O '
        'pull-ups stay on while the FPGA configures, which holds outputs '
        'such as PHY_RESET_N in a known state. DONE lights D1 through Q4 '
        'once a design is running.',
    'GTP calibration':
        'The XC7A100T has two quads of multi-gigabit transceivers (GTP). '
        'Rev A uses none of them, but UG482 Tables 5-5 and 5-6 still want '
        'their supplies powered, their receive inputs grounded and one 100 '
        'ohm 1 % calibration resistor per quad to MGTAVTT. These two '
        'resistors are that.',
    'system clock':
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
            'FPGA; reset and interrupt on bank 13 at 3.3 V.'),
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
    'PUDC_B': 'PUDC_B low: I/O pull-ups on during configuration (UG470)',
    'DONE_LED_A': 'sets D1\'s current',
    'MGTRREF': 'calibration resistor for GTP quad 216 (UG482 Figure 5-1)',
    'MGTRREF_213': 'calibration resistor for GTP quad 213 (UG482 Table 5-5)',
    'SYS_CLK': 'damps ringing on the clock line',
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

# Nets that are supplies, for telling a bypass capacitor from a filter one.
def _is_supply(n):
    return (n.startswith('+') or n in ('VSYS', 'VBUS', 'PD_VDD', 'SUP_VREG_AVDD', 'AUX_RAIL',
                                       'PHY_1V0') or
            re.match(r'VCCIO_\d(_EXT)?$', n) is not None or
            re.search(r'_(3V3|5V|PIN_VOLTAGE|AUX|VCC)$', n) is not None)


def _named(q):
    return f"{q['ref']} ({PART[q['ref']][0]})" if q['ref'] in PART else q['ref']


def _is_pull(net):
    """A resistor on this net is a pull (default level), not a load or a
    reference: active-low lines, straps, and any net without its own note."""
    return (net not in NET or net.endswith(('_N', '_B', '_MDIO')) or
            net.startswith(('PHY_RX', 'PHY_LED', 'CFG_', 'PUDC')))


def _hub(part, by_group, by_net):
    """Who this passive serves. A signal part names the active part it shares
    a signal net with; a bypass part names its group's main active part."""
    sig = [n for n in part['pins'].values() if n != 'GND' and not _is_supply(n)]
    # U1 touches nearly every signal; name it only when nothing else does.
    sharers = [q for n in sig for q in by_net.get(n, [])
               if q['lib_id'] not in PASSIVE and q['ref'] != part['ref']]
    for q in sorted(sharers, key=lambda q: q['ref'] == 'U1'):
        return _named(q)
    if sig:
        return None
    for q in by_group.get(part['group'], []):
        if q['lib_id'] not in PASSIVE:
            return _named(q)
    return None


def derive(part, by_group, by_net):
    """One line for a resistor, capacitor, inductor or fuse."""
    nets = sorted(set(part['pins'].values()))
    v = part['value']
    kind = {'R': 'resistor', 'C': 'capacitor', 'L': 'inductor', 'F': 'fuse'}.get(
        re.match(r'[A-Z]+', part['ref']).group()[0], 'part')
    note = '; '.join(NET[n] for n in nets if n in NET)
    hub = _hub(part, by_group, by_net)
    g = part['group']
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
SHEET_ORDER = ['FPGA', 'Power', 'Memory', 'Supervisor', 'Slots', 'Network']
SHEET_INTRO = {
    'FPGA': 'The Artix-7 itself, its decoupling, how it boots and its clock.',
    'Power': 'Inputs, the regulators that make every rail, extension power protection.',
    'Memory': 'Four PSRAM chips for working memory and the flash the FPGA boots from.',
    'Supervisor': 'The RP2350B board controller: USB, power sequencing, programming the FPGA.',
    'Slots': 'The ten extension ports: connectors, per-slot fuses, 5 V level shifting.',
    'Network': 'Gigabit Ethernet (PHY and jack) and the two raw LVDS link ports.',
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
