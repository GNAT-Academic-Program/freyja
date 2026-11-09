#!/usr/bin/env python3
"""Executable power limits and the generated Odin power-budget report."""
import sys

# (name, minimum voltage at the connector, current the source guarantees, note)
# Currents are what the source profile promises, not what the board may take.
# What the controller can observe (findings item 55, revisited 2026-10-30):
# U18 is a HUSB238 on I2C1 since the CH224K left the JLCPCB library. Its
# PD_STATUS0 register reports the contract voltage and current and
# PD_STATUS1 bits 1:0 the 5 V Type-C advertisement (default / 1.5 A / 2.4 A
# / 3 A), so a 5 V advertisement IS readable now. This table keeps the
# user-declared policy for the 5 V rows until the owner decides to use that
# register (it reverses item 55's premise, not its decision). Observable
# besides: VBUS5_ST (which input feeds +5V) and MON_VSYS. A 9 V contract is a
# guarantee in itself: any source that offers 9 V must offer it at 15 W or
# more, 1.67 A at 9 V (USB PD power rules, PD3 section 10.2 [verify]); 3 A at
# 9 V is only guaranteed above 27 W and is not observable, so it is not
# planned on. The 5 V rows above 500 mA are user-declared ports: firmware
# may use them only on a stored setting the user made, never by detection.
SOURCES = [
    ('USB 2.0 port', 4.75, 0.5, 'configured bus power; what any 5 V source is until PD_STATUS1 says more (default Rp)'),
    ('USB-C 5V/1.5A', 4.75, 1.5, 'Type-C 1.5 A advertisement (Rp), read by firmware in HUSB238 PD_STATUS1 bits 1:0 (2026-11-03: detected, no longer user-declared)'),
    ('USB-C 5V/3A', 4.75, 3.0, 'Type-C 3 A advertisement, read in PD_STATUS1; a 5 V source never carries full export (the port is 15 W; firmware holds EXT_EN to it)'),
    ('USB-PD 9V', 9.00, 1.67, 'the 9 V PDO firmware selects, at its 15 W floor (PD power rules [verify PD3 10.2]); PD_STATUS0 bits 3:0 report the granted current'),
    ('USB-PD 9V/3A', 9.00, 3.0, '9 V granted at 3 A (PD_STATUS0 PD_SRC_CURRENT = 3 A, any 27 W or larger charger); 3 A is the Type-C cable limit without an e-marker; exports rationed to U26\'s guaranteed limit, RATIONED below'),
    ('J50 VIN', 9.00, 3.0, 'official 9-21 V screw-input range; 3 A is the planning figure; U34 (Q7) puts the whole board on it, USB connected or not'),
]
# Hardware limits on the two USB paths: U26 (eFuse to VSYS) and U34 (mux to
# +5V) draw from the same connector when the source is plain 5 V.
I_U26_MIN, I_U26_TYP = 2.79, 3.03     # TPS25942A 29.4k ILIM: 89/R (SLVSCE9D Equation 4), +/-8 %; the 24.9k row of 7.5 reads 3.25-3.81 A
# TPS2121 RILM, SLVSEA3F 7.5 and Equation 2 (ILM = 65.2 / R^0.861, R in kohm). 29.4k
# since 2026-11-09; 44.2k before, 2.0 / 2.5 / 3.0 A, under the 2.77 A the rail carries
# at full export. The table's 29.8k row reads 3.0 / 3.5 / 4.0 A. A 29.4k resistor at
# 1 % and 100 ppm/C over 60 K lies between 28.93k and 29.87k, so the limit is 2.99 A
# at least, 3.55 A typical and 4.10 A at most. The minimum is what the rail may count
# on; the maximum is what +5V copper and the source see in a fault.
I_U34_MIN, I_U34_TYP, I_U34_MAX = 2.99, 3.55, 4.10
I_U34_RATED = 4.5                     # TPS2121 continuous input current, SLVSEA3F 7.3
RON_U34 = (0.056, 0.085, 0.100)       # typical at 25 C; maximum to 85 C; maximum to 125 C junction (7.5)
RTH_U34 = 72.2                        # K/W junction to ambient, JEDEC board (7.4): a comparison figure
ETA = 0.90                            # planning efficiency per conversion stage
# Rails whose regulator is held off in recovery mode (EN low from the
# controller's reset state): nothing on them draws in recovery.
RECOVERY_OFF = {'+1V0', '+2V5'}

# Connector exports: planning allowances per protected bus, each the switch's
# typical limit or, for the PIN V domains, one slot fuse's hold current.
# They are not additive guarantees: ref/extension-ux.md.
EXPORTS = [
    ('+5V_EXT', 5.0, 2.00, 'U21 TPS22950C 604 ohm, 2.0 A typical (1.54-2.46 A, SLVSFJ2B 7.5 at 610 ohm)'),
    ('+3V3_EXT', 3.3, 1.00, 'U22 TPS22950C 1.15k, 1.0 A typical (0.75-1.25 A)'),
    ('VCCIO_1_EXT', 3.3, 0.50, 'U23 TPS22975, no limit of its own: one 500 mA PINV PTC'),
    ('VCCIO_2_EXT', 3.3, 0.50, 'U24 TPS22975, no limit of its own: one 500 mA PINV PTC'),
]
# Per-slot branch PTCs, hold current at 25 C (design.py fits these values;
# the LCSC parts are in its F() table). Fault isolation, not an allowance:
# ten slots share each bus above. 2026-11-03: 5 V 500 mA -> 1.1 A and
# 3V3 300 -> 500 mA so one slot can carry a real load (a display, a radio
# module, a small servo); the buses above went to 2 A and 1 A to match.
SLOT_PTC = {'PIN_VOLTAGE': '500mA', '5V': '1.1A', '3V3': '500mA', 'AUX': '1.1A 33V'}
PTC_TRIP = {'500mA': 1.0, '1.1A': 2.2, '300mA': 0.65, '1.1A 33V': 2.2}   # trip at 25 C, datasheets

VF_OR = 0.45          # SS54 at the 0.6 A planning current; about 0.5 V at 3 A
RON_U26 = 0.05
I_VSYS_HI = 0.60
V_OR_DROP = VF_OR + RON_U26 * I_VSYS_HI
VSYS_MIN = min(v for _, v, _, _ in SOURCES) - V_OR_DROP
VSYS_MAX = 21.0

# design.py consumes this exact table, so arithmetic and fitted parts cannot
# silently diverge.
INDUCTOR = {
    # Sunlord SWPA6045S catalog (rev 2025/5/8, SWPA6045S table): 4R7MT
    # Isat 4.97 A guaranteed / 5.50 A typical, Irms 3.30 / 3.60 A, DCR
    # 34 mohm max / 26 typ; the Bourns SRN6045TA-4R7M it replaces is not in
    # the JLCPCB library (2026-10-30). Same 6.0 x 6.0 x 4.5 mm class; the
    # land is the C78804 import (2.47 x 5.02 mm pads on 5.2 mm centres,
    # Sunlord Fig. 2 pattern a 2.8 / b 1.7 / c 5.7).
    '4.7uH': dict(mpn='SWPA6045S4R7MT', l=4.7e-6, isat=4.97, dcr=0.034,
                  size='6.0 x 6.0 x 4.5 mm', fp='EasyEDA:IND-SMD_L6.0-W6.0_SWPA6045S',
                  lcsc='C78804', cite='Sunlord SWPA6045S4R7MT: Irms 3.30 A, Isat 4.97 A (guaranteed), 5.50 A typical'),
    # L2 and L3 since 2026-11-09. Sunlord MWSA-S catalog (rev 2023/09/13,
    # MWSA0603S table): 100MT Isat 4.40 A guaranteed / 5.50 A typical (30 %
    # inductance drop), Irms 3.80 A guaranteed for a 20 K rise / 4.50 A typical
    # for 40 K, DCR 68 mohm max. Moulded metal composite, so the inductance
    # falls gradually with current: the catalog's typical curves follow
    # L(i) = L0 (1 - 0.3 (i / Isat)^1.6); BIAS_N below takes 1.4, which loses
    # more below Isat. 6.6 x 7.0 x 2.8 mm; the land is Sunlord's recommended
    # pattern, I 2.35 / J 3.7 / H 3.5. The Bourns SRN6045TA-100M this key
    # named before (unused since the LM5157 left) has typical ratings only,
    # Isat 4.6 A and Irms 3.2 A for 40 K, and was not taken.
    '10uH': dict(mpn='MWSA0603S-100MT', l=10e-6, isat=4.40, isat_typ=5.50, irms=3.80, dcr=0.068,
                 size='6.6 x 7.0 x 2.8 mm', fp='EasyEDA:IND-SMD_L7.0-W6.6_MWSA0603S',
                 lcsc='C132141', cite='Sunlord MWSA0603S-100MT: Irms 3.80 A for 20 K (guaranteed), Isat 4.40 A guaranteed, 5.50 A typical'),
    '2.2uH': dict(mpn='SRN4018-2R2M', l=2.2e-6, isat=3.00, dcr=0.044,
                  size='4.0 x 4.0 x 1.8 mm', fp='EasyEDA:IND-SMD_L4.0-W4.0_SNR4018',
                  lcsc='C913207', cite='Bourns SRN4018: Irms 2.90 A, Isat 3.00 A'),
    '1uH': dict(mpn='VLS252010HBX-1R0M-1', l=1e-6, isat=3.57, dcr=0.054,
                 size='2.5 x 2.0 x 1.0 mm', fp='EasyEDA:IND-SMD_L2.5-W2.0-1',
                 lcsc='C88211', cite='TDK VLS252010HBX: Irms 3.00 A, Isat 3.57 A'),
    '3.3uH': dict(mpn='AOTA-B201610S3R3-101-T', l=3.3e-6, isat=2.40,
                   dcr=0.140, size='2.0 x 1.6 x 1.0 mm',
                   fp='EasyEDA:IND-SMD_L2.0-W1.6_AOTA-B201610S3R3-101-T',
                   lcsc='C42411119',
                   cite='Abracon part mandated by RP-008280: Irms 2.10 A, Isat 2.40 A'),
}

# (rail, load, active current, recovery current, basis, note)
# Recovery is the controller alone with the FPGA unconfigured, +1V0 and
# +2V5 held off, the PHY in reset, the memories idle on their always-on
# rails: standby or reset currents, never zero for a part that is powered,
# never the active figure (findings, re-audit 2026-10-29).
LOADS = [
    # ---- +1V0, FPGA core
    ('+1V0', 'XC7A100T VCCINT, busy design', 2.00, 0.0, 'estimate',
     'planning allowance for a design that keeps the four PSRAM ports, the SDRAM, '
     'the PHY and HDMI busy at once (raised from 1.5 A, 2026-11-03); replace with an AMD XPE result'),
    ('+1V0', 'VCCBRAM', 0.05, 0.0, 'estimate', 'share of the 0.25 W AUX/BRAM line'),
    # MGTAVCC and MGTAVTT are grounded (UG482 v1.9 Table 5-4): the 0.10 A
    # and 0.15 A transceiver allowances and U16 are gone.
    # ---- +1V8_IO: U14's output. VCCAUX/VCCADC hang off it as +1V8 through
    # a bead; bank 13 and the 1.8 V memory are on the node itself.
    ('+1V8_IO', 'XC7A100T VCCAUX and VCCADC (+1V8, through FB1)', 0.18, 0.05, 'estimate',
     'pre-bitstream planning allowance; replace with an AMD XPE result. '
     'Recovery: unconfigured quiescent ICCAUXQ, planning figure [verify DS181]'),
    ('+1V8_IO', 'FPGA bank 13 VCCO and its I/O', 0.10, 0.005, 'estimate',
     'one third of the 1.0 W VCCO/IO line, as for bank 14; recovery: VCCO quiescent'),
    ('+1V8_IO', 'PSRAM x4 APS6404L-SQN-SN, all reading', 0.028, 0.0008, 'datasheet',
     'APS6404L-SQN datasheet rev 4.0 Table 9 (p. 26): ICC read/write 7 mA '
     'max per chip, output load not included; standby ISBSTD 200 uA each'),
    ('+1V8_IO', 'U9/U10 VCCA, quiescent', 0.0001, 0.0001, 'datasheet',
     'SN74LVC8T245 SCES584D 5.5: ICCA 8 uA max per device at 5 V; '
     'switching current is counted in the bank 13 line'),
    # ---- +3V3, the crowded one
    ('+3V3', 'RP2350B supervisor + boot flash', 0.07, 0.07, 'estimate',
     'ref/power-input.md: 0.2 W; the controller runs in recovery'),
    ('+3V3', 'FPGA bank 14 VCCO and its I/O', 0.10, 0.005, 'estimate',
     'one third of the 1.0 W VCCO/IO line; recovery: VCCO quiescent, core off'),
    ('+3V3', 'config flash W25Q256, program', 0.03, 0.0001, 'datasheet',
     'W25Q256JV: 25 mA page-program peak; standby under 100 uA [verify W25Q256JV 9.3]'),
    ('+3V3', 'microSD card in J74, writing', 0.10, 0.002, 'estimate',
     'SD specification: up to 100 mA average for a 3.3 V card; peaks are '
     'carried by the 10 uF at the socket; an idle inserted card about 1-2 mA'),
    ('+3V3', 'W9825G6KH-6 SDRAM, burst read/write', 0.085, 0.030, 'datasheet',
     'W9825G6KH rev A03 p. 14, DC characteristics: IDD4 85 mA max at the -6 grade; '
     'recovery: IDD2 30 mA, the standby figure with CKE high, taken because the '
     'unconfigured FPGA leaves its inputs floating (PUDC_B high)'),
    ('+3V3', 'U33 MR25H10 MRAM', 0.027, 0.000115, 'datasheet',
     'MR25H10 DC table: IDDW 27 mA max at 40 MHz; ISB 115 uA max'),
    ('+3V3', 'RTL8211FDI-CG, 1000Base-T link', 0.20, 0.05, 'estimate',
     'datasheet rev 1.7 gives no active-mode consumption table; planning '
     'allowance for a 1 Gb PHY with internal LDO, verify on the prototype. '
     'Recovery: held in reset by the unconfigured FPGA strap state, still '
     'powered; planning figure [verify on the prototype]'),
    ('+3V3', 'ETH jack LEDs x2 through 510 ohm', 0.006, 0.0, 'datasheet',
     'RTL8211F Figure 5; about 3 mA each; no link in recovery'),
    ('+3V3', 'X4 50 MHz CMOS oscillator', 0.01, 0.01, 'estimate',
     'typical 3225 CMOS oscillator at 50 MHz into a 15 pF load; always powered'),
    ('+3V3', 'Heartbeat and user LEDs x3, all on', 0.005, 0.005, 'estimate',
     'D9-D11 via 1k each; 5 mA budget allowance'),
    ('+3V3', 'U20, pull-ups, LED', 0.03, 0.03, 'estimate',
     'quiescent logic'),
    ('+3V3', 'FPGA bank 15 VCCO, worst case jumpered to 3.3V', 0.10, 0.005, 'estimate',
     'bank load only; connector export is checked from switch maximum below'),
    ('+3V3', 'FPGA bank 34 VCCO, worst case jumpered to 3.3V', 0.10, 0.005, 'estimate',
     'bank load only; connector export is checked from switch maximum below'),
    ('+3V3', 'FPGA bank 35 VCCO and bank 0', 0.06, 0.005, 'estimate',
     'bank 35 drives HDMI (TMDS_33 current comes from the monitor\'s 3.3 V '
     'pull-ups, not from VCCO); bank 13 is on +1V8_IO'),
    ('+3V3', 'U31 TPD12S016 VCCA, level shifters on', 0.001, 0.0002, 'datasheet',
     'SLLSE96F 8.2.2: about 200 uA fully on'),
    # ---- +2V5: bank 16 I/O and the PHY RGMII pads
    ('+2V5', 'FPGA bank 16 VCCO: RGMII and eight LVDS_25 pairs', 0.12, 0.0, 'estimate',
     'LVDS_25 drivers about 3.5 mA each plus RGMII switching; replace with XPE'),
    ('+2V5', 'RTL8211FDI-CG DVDD_RG (RGMII pads)', 0.02, 0.0, 'estimate',
     'external 2.5 V I/O supply, CFG_EXT=1 CFG_LDO=01'),
    # ---- +1V1, the supervisor's core, off the RP2350's own regulator
    ('+1V1', 'RP2350B core (DVDD)', 0.06, 0.06, 'estimate',
     'RP2350 at 150 MHz; the on-chip regulator is rated 200 mA'),
    # ---- +5V
    ('+5V', 'U9/U10 VCCB', 0.02, 0.001, 'estimate', 'quiescent translator supply'),
    ('+5V', 'HDMI 5 V to the monitor through U31', 0.055, 0.0, 'datasheet',
     'TPD12S016 5V_OUT current limit, SLLSE96F; U31 is off in recovery'),
    # AUX has no internal board load; it feeds the ten fused branches.
]

REGULATORS = [
    ('U11', 'LMR33630ADDAR', 'VSYS', '+5V', 3.8, 36.0, 3.0),
    ('U12', 'LMR33630ADDAR', 'VSYS', '+3V3', 3.8, 36.0, 3.0),
    ('U13', 'TLV62569PDRLR', '+5V', '+2V5', 2.5, 5.5, 2.0),
    ('U14', 'TLV62569PDRLR', '+5V', '+1V8_IO', 2.5, 5.5, 2.0),
    ('U15', 'TPS564201DDCR', '+5V', '+1V0', 4.5, 17.0, 4.0),
]
# Per regulator: the net its capacitors sit on, inductor key, switching
# frequency, and what the datasheet has actually validated for COUT
# (findings item 40). Anything above the validated figure is a bench
# qualification item, not a build error: load-step and start-up on the
# assembled board, every jumper position.
REG_DETAIL = {
    # LMR33630ADDA, SNVSAN3F 7.5: high-side current limit 3.85 A minimum (4.5 typical,
    # 5.05 maximum), switching frequency 340 kHz minimum, DDA on-resistance 160 and
    # 110 mohm maximum. vset_hi: the setpoint's upper limit with the 0.1 % divider.
    'U11': dict(node='+5V_BUCK', ind='10uH', fsw=400e3, vin=9.0, vin_max=21.0,
                isc_min=3.85, isc_max=5.05, fsw_min=340e3, r_hs=0.160, r_ls=0.110, vset_hi=5.112,
                cout_ok=880e-6, cite='SNVSAN3F 9.2.2.5: 4 x 22 uF at 400 kHz (Table 9-2), at most 10 x the design value or 1000 uF'),
    'U12': dict(node='+3V3', ind='10uH', fsw=400e3, vin=9.0, vin_max=21.0,
                isc_min=3.85, isc_max=5.05, fsw_min=340e3, r_hs=0.160, r_ls=0.110, vset_hi=3.376,
                cout_ok=880e-6, cite='SNVSAN3F 9.2.2.5: 4 x 22 uF at 400 kHz (Table 9-2), at most 10 x the design value or 1000 uF'),
    'U13': dict(vin_max=5.5, node='+2V5', ind='2.2uH', fsw=1.5e6, vin=5.0,
                cout_ok=47e-6, cite='SLVSDG1C 8.2.2.5: 10-47 uF, Table 4 up to 2 x 22 uF'),
    'U14': dict(vin_max=5.5, node='+1V8_IO', ind='2.2uH', fsw=1.5e6, vin=5.0,
                cout_ok=47e-6, cite='SLVSDG1C 8.2.2.5: 10-47 uF, Table 4 up to 2 x 22 uF'),
    'U15': dict(vin_max=5.5, node='+1V0', ind='4.7uH', fsw=560e3, vin=5.0,
                cout_ok=68e-6, cite='TPS564201 SLVSDJ7B Table 2: 20-68 uF, L 1.5-4.7 uH at 1 V'),
}
# Rails that hang off a regulator node through a bead or inductor: their
# capacitance is a frequency-dependent load, listed beside the direct sum.
BEHIND = {'+1V8_IO': ('+1V8', 'FB1')}


def _farads(value):
    import re
    m = re.match(r'\s*([\d.]+)\s*(pF|nF|uF)', value)
    if not m: return 0.0
    return float(m.group(1)) * {'pF': 1e-12, 'nF': 1e-9, 'uF': 1e-6}[m.group(2)]


def rail_caps(parts):
    """Nominal rail-to-GND capacitance per net from the design parts."""
    tot = {}
    for p in parts:
        if p['lib_id'] not in ('Device:C', 'Device:C_Polarized') or p.get('dnp'): continue
        nets = set(p['pins'].values())
        if 'GND' not in nets or len(nets) != 2: continue
        rail = (nets - {'GND'}).pop()
        tot[rail] = tot.get(rail, 0.0) + _farads(p['value'])
    return tot


def cout_rows(parts):
    caps = rail_caps(parts)
    rows = []
    for ref, part, _src, out, _lo, _hi, _cap in REGULATORS:
        d = REG_DETAIL[ref]
        direct = caps.get(d['node'], 0.0)
        extra = ''
        if d['node'] in BEHIND:
            r, via = BEHIND[d['node']]
            extra = f'{caps.get(r, 0)*1e6:.1f} uF on {r} behind {via}'
        if ref == 'U11':
            extra = f'{caps.get("+5V", 0)*1e6:.1f} uF on +5V behind U34'
        ok = direct <= d['cout_ok'] * 1.001
        rows.append((ref, d['node'], direct, d['cout_ok'], extra, ok, d['cite']))
    return rows


L_TOL = 0.80     # inductance at the low end of a +/-20 % ("M") part


def inductor_rows(parts):
    """Peak inductor current per rail (TLV62569 SLVSDG1C eq. 3, the same
    arithmetic for every buck) against the fitted part's saturation rating,
    at the planning input and at the envelope: the highest input the
    converter can see (21 V on the wide-input pair, 5.5 V on the 5 V row)
    with the inductance at its -20 % tolerance (re-audit 2026-10-29)."""
    loads = board_loads()
    rows = []
    for ref, part, _src, out, _lo, _hi, _cap in REGULATORS:
        d = REG_DETAIL[ref]; ind = INDUCTOR[d['ind']]
        vout = {'+5V': 5.0, '+3V3': 3.3, '+2V5': 2.5, '+1V8_IO': 1.8, '+1V0': 1.0}[out]
        iload = loads[out] + export_on(out)
        ripple = vout * (1 - vout / d['vin']) / (ind['l'] * d['fsw'])
        ripple_env = vout * (1 - vout / d['vin_max']) / (ind['l'] * L_TOL * d['fsw'])
        ipk = iload + ripple / 2
        ipk_env = iload + ripple_env / 2
        rows.append((ref, ind['mpn'], iload, ripple, ipk, d['vin_max'], ipk_env, ind['isat'],
                     ipk_env <= ind['isat']))
    return rows


BIAS_N = 1.4     # exponent of the inductance fall under DC bias, see INDUCTOR['10uH']


def _psi(i, l0, isat):
    """Flux linkage of an inductor whose inductance falls 30 % at isat: the integral of L(i)."""
    return l0 * (i - 0.3 * i ** (BIAS_N + 1) / ((BIAS_N + 1) * isat ** BIAS_N)) if i > 0 else l0 * i


def _i_of_psi(p, l0, isat):
    lo, hi = -5.0, 30.0
    for _ in range(60):
        m = (lo + hi) / 2
        if _psi(m, l0, isat) < p: lo = m
        else: hi = m
    return (lo + hi) / 2


def guaranteed_output(ref, vin):
    """Average output current at which the inductor's peak reaches the regulator's minimum
    current limit: what the regulator delivers on its guaranteed figures alone. Worst part
    of everything at once: inductance at -20 % with the guaranteed (lowest) saturation
    current, minimum switching frequency, the setpoint at its upper limit, conduction drops
    at the maximum on-resistances and the inductor's maximum resistance at 85 C.
    Returns (output, ripple, inductance at the peak)."""
    d = REG_DETAIL[ref]; ind = INDUCTOR[d['ind']]
    l0 = ind['l'] * L_TOL; isat = ind['isat']; dcr = ind['dcr'] * (1 + 0.0039 * 65); vo = d['vset_hi']
    ipk = d['isc_min']; iav = ipk
    for _ in range(30):
        von = vin - iav * (d['r_hs'] + dcr) - vo
        voff = vo + iav * (d['r_ls'] + dcr)
        vs = von * voff / (von + voff) / d['fsw_min']          # volt-seconds of the on-time
        ppk = _psi(ipk, l0, isat); n = 200
        new = sum(_i_of_psi(ppk - vs * (k + .5) / n, l0, isat) for k in range(n)) / n
        if abs(new - iav) < 1e-5: break
        iav = new
    return iav, ipk - _i_of_psi(ppk - vs, l0, isat), l0 * (1 - 0.3 * (ipk / isat) ** BIAS_N)


def limit_rows():
    """U11 and U12: the declared load (board plus exports) against the output the minimum
    current limit guarantees at 9 V and at the top of the input range, the rms current
    against the inductor's guaranteed 20 K rating, and what is left of the inductance at
    the maximum current limit, which is where a fault takes the inductor."""
    loads = board_loads(); rows = []
    for ref, part, _src, out, _lo, _hi, _cap in REGULATORS:
        d = REG_DETAIL[ref]
        if 'isc_min' not in d: continue
        ind = INDUCTOR[d['ind']]; iload = loads[out] + export_on(out)
        lo = guaranteed_output(ref, d['vin']); hi = guaranteed_output(ref, d['vin_max'])
        rms = (iload ** 2 + hi[1] ** 2 / 12) ** 0.5
        l_fault = ind['l'] * L_TOL * (1 - 0.3 * (d['isc_max'] / ind['isat']) ** BIAS_N)
        rows.append((ref, ind['mpn'], iload, d['vin'], lo[0], d['vin_max'], hi[0], hi[0] - iload,
                     rms, ind.get('irms', 0.0), l_fault, hi[0] >= iload and rms <= ind.get('irms', 0.0)))
    return rows


# Rows of the source table the contract does not promise in full. Firmware holds the
# exports to what U26's guaranteed limit carries (source policy, rule 3). 2026-11-09:
# full export from a 9 V contract at 3 A is 2.91 A at the connector with the +5V
# export at its declared 2 A. That is inside the source's 3 A and 0.12 A above U26's
# 2.79 A minimum. The row passed only while mode_rows counted that export at 1 A.
# No allowance is reduced: the shortfall is stated. Raising U26's limit to cover it
# would put its maximum above the 3 A of an unmarked Type-C cable.
RATIONED = {('full', 'USB-PD 9V/3A')}


def ration_rows():
    """(mode, source, export power U26's minimum limit carries, export allowances, shortfall)."""
    loads = board_loads()
    board = loads['+3V3'] * 3.3 + loads['+5V'] * 5.0
    allow = sum(v * a for _n, v, a, _c in EXPORTS)
    out = []
    for m, s, v, p, i, lim, ok, hw in mode_rows():
        if (m, s) in RATIONED:
            carried = min(I_U26_MIN, lim) * v * ETA - board
            out.append((m, s, carried, allow, allow - carried))
    return out


def mode_rows():
    """Input-source envelope per operating mode (findings items 46, 53, 55).

    recovery: controller only (+3V3 and the always-on +5V/+1V8 chain with the
              FPGA unconfigured, the recovery column of LOADS); light: every
              board load; full: board loads plus the connector export
              allowances. Powers are at the connector, with ETA per
              conversion stage; on a plain 5 V source the +5V loads come
              straight from VBUS through U34 and only the +3V3 side passes
              U26 and U12. Each hardware path is checked against its own
              limit, and the sum against the source. With J50 connected U34
              puts the whole board on U11 (Q7), USB or not, so the J50 row
              is also the J50 + USB row."""
    loads = board_loads()
    rec = recovery_loads()
    p33 = loads['+3V3'] * 3.3
    p5_board = loads['+5V'] * 5.0
    p33_rec = rec['+3V3'] * 3.3
    p5_rec = rec['+5V'] * 5.0
    # full: every declared allowance of EXPORTS at once. Until 2026-11-09 the +5V
    # side stood here as a literal 1 A, the allowance of 2026-10-29, while EXPORTS
    # had said 2 A since 2026-11-03.
    modes = [('recovery', p33_rec, p5_rec), ('light', p33, p5_board),
             ('full', p33 + sum(v*a for n, v, a, _c in EXPORTS if n != '+5V_EXT'),
              p5_board + sum(v*a for n, v, a, _c in EXPORTS if n == '+5V_EXT'))]
    rows = []
    for name, p33m, p5m in modes:
        for sname, v, imax, _note in SOURCES:
            if v < 5.5:      # plain 5 V: +5V straight from VBUS (U34), +3V3 via U26/U12
                i_mux = p5m / v
                i_efuse = p33m / ETA / v
                i_tot = i_mux + i_efuse
                ok = i_tot <= imax and i_mux <= I_U34_MIN and i_efuse <= I_U26_MIN
                limit = imax
                hw = (f'U34 {i_mux:.2f} A of {I_U34_MIN:.2f} A + '
                      f'U26 {i_efuse:.2f} A of {I_U26_MIN:.2f} A')
            else:            # 9 V and up: everything through U26 (USB) or D4 (J50), U11 and U12
                i_tot = (p33m + p5m) / ETA / v
                if sname.startswith('J50'):
                    limit, hw, ok = imax, 'D4 path, no limiter of its own', i_tot <= imax
                else:
                    limit = imax
                    ok = i_tot <= imax and i_tot <= I_U26_MIN
                    hw = f'U26 {i_tot:.2f} A of {I_U26_MIN:.2f} A'
            rows.append((name, sname, v, p33m + p5m, i_tot, limit, ok, hw))
    return rows

def export_on(rail):
    """Connector export allowance a regulator carries: +5V_EXT on U11,
    +3V3_EXT and both PIN V domains (worst case jumpered to 3.3 V) on U12."""
    if rail == '+5V':
        return sum(a for n, _v, a, _c in EXPORTS if n == '+5V_EXT')
    if rail == '+3V3':
        return sum(a for n, _v, a, _c in EXPORTS if n != '+5V_EXT')
    return 0.0


def or_diode_rows():
    """Current and dissipation in D3 (USB) or D4 (J50) in full mode at 9 V:
    the SS54 is a 5 A SMA part, 0.55 V at 5 A; about 0.5 V at these currents."""
    out = []
    for m, s, v, p, i, lim, ok, hw in mode_rows():
        if m == 'full' and v >= 9.0:
            out.append((s, i, 0.5 * i))
    return out


def board_loads():
    own = {rail: sum(amps for r, _, amps, _rec, _k, _n in LOADS if r == rail)
           for rail in ('+5V', '+3V3', '+2V5', '+1V8_IO', '+1V0', '+1V1')}
    own['+5V'] += sum(own[r]*v/(4.7*0.90) for r,v in
                     (('+2V5',2.5),('+1V8_IO',1.8),('+1V0',1)))
    own['+3V3'] += own['+1V1']*1.1/(3.3*0.90)
    return own

def recovery_loads():
    """Like board_loads, from the recovery column; rails in RECOVERY_OFF
    are zero whatever their line says."""
    own = {rail: (0.0 if rail in RECOVERY_OFF else
                  sum(rec for r, _, _a, rec, _k, _n in LOADS if r == rail))
           for rail in ('+5V', '+3V3', '+2V5', '+1V8_IO', '+1V0', '+1V1')}
    own['+5V'] += sum(own[r]*v/(4.7*0.90) for r,v in
                     (('+2V5',2.5),('+1V8_IO',1.8),('+1V0',1)))
    own['+3V3'] += own['+1V1']*1.1/(3.3*0.90)
    return own

def analyse():
    problems = []
    import design
    parts = design.build().parts
    for ref, mpn, iload, ripple, ipk, vmax, ipk_env, isat, ok in inductor_rows(parts):
        if not ok:
            problems.append(f'{ref}: {mpn} peak {ipk_env:.2f} A at {vmax:g} V in, L -20 %, '
                            f'exceeds its {isat:g} A saturation rating')
    # Contract: recovery fits a plain USB 2.0 port (the planning default for
    # any 5 V source, item 55); recovery and light fit a 9 V PD contract;
    # full export (every allowance at once) needs J50. A PD source carries
    # full mode only as far as U26's minimum current limit allows.
    # Contract (2026-11-03, corrected 2026-11-09): recovery fits a plain USB 2.0
    # port; light fits a 3 A Type-C port and the 15 W PD floor; full export fits
    # J50. A 27 W PD charger (9 V at 3 A) carries full export as far as U26's
    # guaranteed limit goes: RATIONED. Firmware reads which source it has.
    for mode, src, v, p, i, lim, ok, hw in mode_rows():
        if (mode, src) in RATIONED:
            # the source itself must carry it, and the board load alone must fit U26
            if i > lim:
                problems.append(f'{mode} mode exceeds the source {src}: {i:.2f} A against {lim:g} A')
            continue
        if ((mode == 'recovery' and src == 'USB 2.0 port') or
                (mode == 'light' and src in ('USB-C 5V/3A', 'USB-PD 9V', 'USB-PD 9V/3A')) or
                (mode == 'full' and src == 'J50 VIN')) and not ok:
            problems.append(f'{mode} mode does not fit {src}: {i:.2f} A against {lim:g} A ({hw})')
    for m, s, carried, allow, short in ration_rows():
        if carried <= 0:
            problems.append(f'{m} mode on {s}: U26 carries no export at all')
    # U34 stands between U11 and the +5V rail: its guaranteed limit must cover the
    # rail's declared load, and its highest limit must stay inside its own rating.
    i5 = board_loads()['+5V'] + export_on('+5V')
    if i5 > I_U34_MIN:
        problems.append(f'U34: +5V carries {i5:.2f} A at full export, its limit guarantees {I_U34_MIN:.2f} A')
    if I_U34_MAX > I_U34_RATED:
        problems.append(f'U34: limit can reach {I_U34_MAX:.2f} A, above its {I_U34_RATED:g} A rating')
    for ref, mpn, iload, v1, o1, v2, o2, margin, rms, irms, lf, ok in limit_rows():
        if o2 < iload or o1 < iload:
            problems.append(f'{ref}: {mpn} leaves {min(o1, o2):.2f} A guaranteed by the minimum current limit, load {iload:.2f} A')
        if rms > irms:
            problems.append(f'{ref}: {mpn} carries {rms:.2f} A rms, rated {irms:.2f} A')
    for src, i, p in or_diode_rows():
        if i > 5.0:
            problems.append(f'full mode on {src} puts {i:.2f} A through the 5 A OR diode')
    for n, v, a, c in EXPORTS:
        for rail, cap in (('+5V', 3.0), ('+3V3', 3.0)):
            pass
    loads = board_loads()
    for ref, part, src, rail, lo, hi, cap in REGULATORS:
        if loads[rail] + export_on(rail) > cap:
            problems.append(f'{ref}: board {loads[rail]:.2f} A plus export {export_on(rail):.2f} A exceeds {cap:g} A')
    if VSYS_MIN < 3.8:
        problems.append(f'LMR33630 minimum 3.8 V exceeds VSYS minimum {VSYS_MIN:.2f} V')
    if VSYS_MAX > 36.0:
        problems.append('21 V VIN exceeds the LMR33630 operating maximum')
    return problems

def report():
    import design
    parts = design.build().parts
    couts = '\n'.join(
        f'| `{ref}` | {node} | {c*1e6:.1f} uF | {ok_*1e6:.0f} uF | {extra or "-"} | '
        f'{"inside" if ok else "**beyond: bench qualification**"} | {cite} |'
        for ref, node, c, ok_, extra, ok, cite in cout_rows(parts))
    inds = '\n'.join(
        f'| `{ref}` | `{mpn}` | {il:.2f} A | {rp:.2f} A | {ipk:.2f} A | {ipk_env:.2f} A at {vmax:g} V | {isat:g} A | {"PASS" if ok else "FAIL"} |'
        for ref, mpn, il, rp, ipk, vmax, ipk_env, isat, ok in inductor_rows(parts))
    modes = '\n'.join(
        f'| {m} | {s} | {v:g} V | {p:.2f} W | {i:.2f} A | {lim:.2f} A | {"fits" if ok else "**rationed**" if (m, s) in RATIONED else "**does not fit**"} | {hw} |'
        for m, s, v, p, i, lim, ok, hw in mode_rows())
    limits = '\n'.join(
        f'| `{ref}` | `{mpn}` | {iload:.2f} A | {o1:.2f} A at {v1:g} V | {o2:.2f} A at {v2:g} V | {margin:+.2f} A | {rms:.2f} A of {irms:.2f} A | {lf*1e6:.1f} uH | {"PASS" if ok else "FAIL"} |'
        for ref, mpn, iload, v1, o1, v2, o2, margin, rms, irms, lf, ok in limit_rows())
    rat = ration_rows()[0]
    i5 = board_loads()['+5V'] + export_on('+5V')
    exps = '\n'.join(f'| {n} | {v:g} V | {a:g} A | {c} |' for n, v, a, c in EXPORTS)
    regs = '\n'.join(
        f'| `{r}` | `{p}` | {src} | {out} | {lo:g}–{hi:g} V | {cap:g} A |'
        for r, p, src, out, lo, hi, cap in REGULATORS)
    loads = board_loads()
    rec = recovery_loads()
    totals = '\n'.join(
        f'| `{r}` | {out} | {loads[out]:.3f} A | {rec[out]:.3f} A | {cap:g} A | {100*loads[out]/cap:.0f} % |'
        for r, _p, _src, out, _lo, _hi, cap in REGULATORS)
    lines = '\n'.join(
        f'| {rail} | {what} | {amps:.3f} A | {("off" if rail in RECOVERY_OFF else f"{recamps:.4f} A")} | {kind} | {note} |'
        for rail, what, amps, recamps, kind, note in LOADS)
    return f'''# Odin power budget

**Generated by `tools/budget.py`. Do not hand-edit.**

## Input envelope

USB-C can start at 4.75 V. The SS54 OR diode plus USB eFuse model loses
{V_OR_DROP:.2f} V at 0.6 A, leaving **{VSYS_MIN:.2f} V**. In full mode at 9 V
the OR diode carries {' / '.join(f'{i:.2f} A ({p:.2f} W) on {s}' for s, i, p in or_diode_rows())}:
the SS54 (SMA, 5 A) wants its copper; give D3 and D4 a wide VSYS pour. The screw input is
**9–21 V DC**. U11/U12 are LMR33630 devices (3.8–36 V operating, 400 kHz)
and cover the full VSYS envelope. Both have EN tied to VIN: +3V3, +5V and the
1.8 V rail behind U14 are present whenever the board has power, so the FPGA's
VCCAUX never waits on firmware (DS181 Table 7, findings 34).

On a plain 5 V source U11 cannot make 5 V from 4.3 V; U34 (TPS2121) then
passes VBUS to the +5V rail directly. The rail goes to U11 (findings
items 52, 53) while the controller asks for 9 V and for 2-7 s after it
stops (Q6, so the handoff happens before VBUS moves and lasts until it is
back at 5 V, not at a comparator threshold that cannot separate a 5.5 V
vSafe5V from the TLV62569's 5.5 V operating maximum), while the screw input
carries voltage (Q7: J50 connected means the whole board runs from J50,
USB cable or not), and if VBUS goes above 5.3-5.9 V unasked (OV1, a fault
backstop inside the 6 V absolute maximum) or away. During a 5 V -> 9 V
negotiation the rail is U11 in low-dropout mode, about 4.5 V, which every
+5V consumer accepts except the core regulator U15 (TPS564201, 4.5 V
minimum input since 2026-10-30): firmware asks for 9 V before it enables
EXT_EN, and enables EN_1V0 only once the source is settled (9 V granted,
or a 5 V source confirmed: 4.75 V less U34's drop is 4.69 V).
Both of U34's inputs block reverse current and the rail is limited to
{I_U34_TYP:g} A typical ({I_U34_MIN:.2f} A at least, {I_U34_MAX:.2f} A at most; 29.4k). At full
export the rail carries {i5:.2f} A through it: {i5*RON_U34[2]*1000:.0f} mV and {i5**2*RON_U34[2]:.2f} W at its
125 C on-resistance, {i5**2*RON_U34[2]*RTH_U34:.0f} K above ambient on TI's comparison board. U26 limits
the USB path into VSYS to {I_U26_TYP:.2f} A typical ({I_U26_MIN:.2f} A minimum), the Type-C cable figure.

The VIN clamp is SMBJ22A: 22 V standoff and 35.5 V maximum rated pulse clamp.
The LMR33630's 38 V absolute maximum on VIN is the lowest limit after D4.
VSYS capacitors are 50 V X7R. No switching node on the board sees VSYS
plus a stored output any more, so the former surge release hold against the
LM5157 SW pin is gone with the converter.

## Regulator ratings

| Ref | Part | Source | Output | Input rating | Output class |
|---|---|---|---|---|---:|
{regs}

## Board loads per regulator

Sum of the `LOADS` lines below on each output, with the downstream rails
reflected into +5V and +3V3 at 90 % conversion efficiency. Connector exports
are not in these numbers.

| Ref | Output | Board load | Recovery | Rating | Used |
|---|---|---:|---:|---:|---:|
{totals}

| Rail | Load | Current | Recovery | Basis | Note |
|---|---|---:|---:|---|---|
{lines}

Recovery is the controller alone with the FPGA unconfigured: +1V0 and +2V5
are held off, everything on +3V3, +1V8_IO and +5V is still
powered and listed at its standby or reset current (datasheet where one
exists, a planning figure marked [verify] otherwise), never at zero.

## Output capacitance against the datasheets (findings 40)

Nominal values summed from the netlist: every capacitor directly between
the regulator's output node and ground, FPGA decoupling and jumper-position
capacitors included. The figures are BOM values, not effective capacitance
(DC bias and temperature derate X5R/X7R by up to half); the loads behind a
bead or inductor are frequency-dependent and listed beside, not added.

| Ref | Node | Direct COUT | Validated | Behind a filter | Status | Datasheet |
|---|---|---:|---:|---|---|---|
{couts}

"Beyond" means the datasheet has not validated this much output
capacitance, not that the regulator oscillates. Qualification is on the
assembled board: start-up into the full bank, a load step at each jumper
position, loop phase margin if the vendor supplies a model. Do not remove
FPGA decoupling to make a row fit.

## Inductor peak current

Ripple from the buck equation (TLV62569 SLVSDG1C eq. 3) at the planning
input voltage, load from the table above plus the connector allowance the
rail carries (+5V: {export_on('+5V'):g} A for +5V_EXT; +3V3: {export_on('+3V3'):g} A for
+3V3_EXT and both PIN V domains at 3.3 V). The envelope column repeats the peak at the
highest input the converter can see (21 V on U11/U12, 5.5 V on the 5 V
row) with the inductance at -20 % (the fitted parts are "M" tolerance);
that is the figure checked against saturation.

| Ref | Inductor | Load | Ripple | Peak | Peak, envelope | Isat | |
|---|---|---:|---:|---:|---:|---:|---|
{inds}

## Output the current limit guarantees

U11 and U12 limit the inductor's peak current. The output they deliver without
touching that limit is the average current whose peak is the limit's minimum,
{REG_DETAIL['U11']['isc_min']:g} A, so the ripple decides it. Worst part of everything at once: the
inductance at -20 % with the guaranteed saturation current, the switching
frequency at its {REG_DETAIL['U11']['fsw_min']/1e3:.0f} kHz minimum, the setpoint at its upper limit, the
switches at their maximum resistance and the inductor's copper at 85 C. The
last column is what remains of the inductance at the limit's maximum,
{REG_DETAIL['U11']['isc_max']:g} A, where a fault takes the inductor.

| Ref | Inductor | Declared load | Guaranteed output | at the top of the range | Margin | rms against the 20 K rating | Inductance at the maximum limit | |
|---|---|---:|---:|---:|---:|---:|---:|---|
{limits}

## Input source envelope (findings 46)

| Export | Voltage | Allowance | Source of the figure |
|---|---:|---:|---|
{exps}

| Mode | Source | V | Board + export power | Current at the connector | Source or hardware limit | | Path |
|---|---|---:|---:|---:|---:|---|---|
{modes}

Modes: *recovery* is the controller alone with the FPGA unconfigured (the
recovery column of the load table); *light* is every board load with no
connector export; *full* adds the export allowances. On a plain 5 V source
the +5V loads come straight from VBUS through U34 and only the +3V3 side
passes U26, so the port carries the sum of both paths; each path is checked
against its own limiter and the sum against the source. With J50 connected
U34 puts the whole board on U11 (Q7), so the J50 row also covers J50 with a
USB cable attached: USB then carries nothing but the HUSB238.

**Source policy (findings item 55, settled 2026-11-03).** The PD sink is a
HUSB238 on I2C1. Firmware reads the source instead of guessing it:
PD_STATUS1 bits 1:0 give the 5 V Type-C advertisement (default / 1.5 A /
2.4 A / 3 A), PD_STATUS0 bits 7:4 the granted PD voltage and bits 3:0 the
granted current (0.5-5 A in steps), VBUS5_ST which input feeds +5V and
MON_VSYS whether J50 is present. Item 55's premise (not readable) is gone
with the CH224K. The rules:

1. Until PD_STATUS1 says otherwise, a 5 V source is a USB 2.0 port, 500 mA:
   recovery mode only. Recovery draws about {mode_rows()[0][4]*1000:.0f} mA at
   4.75 V, inside the configured 500 mA but not the 100 mA USB 2.0 allows an
   unconfigured device (the PHY, SDRAM and oscillator sit on the always-on
   +3V3 with no switch; ports rarely police that step; rev B item).
2. A 1.5 A or 3 A advertisement is believed. Light mode (every board load,
   no export) fits a 3 A port; a 5 V source never carries full export: the
   whole port is 15 W. That is firmware's rule to keep: U34 limits at
   {I_U34_MIN:.2f} to {I_U34_MAX:.2f} A, which is no port's advertisement, and no
   limiter on the board ever knew one.
3. A granted 9 V is at least 15 W: light mode. Above that firmware rations
   EXT_EN to (the smaller of the granted current and U26's {I_U26_MIN:.2f} A
   minimum limit) x 9 V x {ETA}, less the board load. With PD_SRC_CURRENT at
   3 A (any 27 W or larger charger) that is {rat[2]:.1f} W of the {rat[3]:.1f} W
   of export allowances: full export is {mode_rows()[16][4]:.2f} A at the connector,
   inside the charger's 3 A and {mode_rows()[16][4]-I_U26_MIN:.2f} A above what U26 guarantees.
4. J50 (detected on MON_VSYS) carries full mode from 9 V up.

The hardware limits (U26, U34, U21, U22, the PTCs) protect the board and the
connector, not the source. The contract checked by `budget.py`: recovery
fits a USB 2.0 port; light fits a 3 A Type-C port and the 15 W PD floor;
full fits J50; a 27 W PD charger carries full export less {rat[4]:.1f} W.

## AUX: raw pass-through, no converter

Rev A has no on-board AUX converter. J68 AUX IN (9–28 V DC, correct polarity)
feeds `AUX_RAIL` directly; the only parts on that net are J68 and the ten
branch PTCs, one per slot power row. Source capacity is whatever is wired to
J68. The board neither regulates, measures nor switches this rail: EXT_EN does
not control it and nothing on the base board draws from it. Capacitors on
`AUX_RAIL` and `VSYS` carry an explicit 50 V rating in their schematic value.

## Base-board load model retained

The per-load estimates are retained in `LOADS`; cascaded 90%-efficient
conversion gives {board_loads()['+5V']:.3f} A on +5V and
{board_loads()['+3V3']:.3f} A on +3V3 before connector exports. FPGA values
are planning estimates pending AMD XPE.
The two VCCIO domains and the separate 3V3 export share U12's 3 A ceiling;
their maximum switch-limit tolerances are not additive guaranteed allowances.

## Extension limits

`AUX_RAIL` is a 5 A routing class, but source capacity is the external supply
on J68. Each of ten AUX branches has its own 33 V, 1.1 A-hold PTC. The other
per-slot PTCs are {SLOT_PTC['PIN_VOLTAGE']} PIN V, {SLOT_PTC['3V3']} 3V3 and {SLOT_PTC['5V']} 5V
(hold at 25 C; trip at twice that; hold falls with temperature). They are
fault isolation, not additive current allocations: the bus above each is
the real ceiling ({' / '.join(f'{n} {a:g} A' for n, _v, a, _c in EXPORTS)}),
so two slots at their PTC rating already exceed the 5 V and 3.3 V buses. A
sustained overload on one slot heats and opens that slot's PTC; a dead
short is cleared by the bus switch first (U21 at 1.54-2.46 A, U22 at
0.75-1.25 A, both auto-retry and report EXT_FAULT), which drops every slot
on that bus until firmware clears it: the PTC trip points sit at or above
the switch minimums, so a short is not isolated to one slot. PIN V has no
switch limit: a short there is the PTC (1 A trip) against U12. An
overloaded external supply droops the shared AUX rail. AUX has no active
reverse blocking: never drive voltage back into a connector AUX pin.

Realistic loads this covers, per slot: a 5 V display or radio module
(300-800 mA), two small servos idling (5 V), a 3.3 V sensor stack with an
OLED (under 200 mA), and on AUX a motor driver or LED strip up to 1 A from
the supply you wire to J68. Not covered: a 2 A LED strip on one 5 V pin
(use AUX), or every slot loaded at once (the bus limits above).
'''

def main():
    problems = analyse()
    print(f'VSYS envelope: {VSYS_MIN:.2f}..{VSYS_MAX:.2f} V')
    print(f'LMR33630 minimum operating input: 3.80 V -> {"PASS" if VSYS_MIN >= 3.8 else "FAIL"}')
    for ref, mpn, iload, v1, o1, v2, o2, margin, rms, irms, lf, ok in limit_rows():
        print(f'{ref} {mpn}: load {iload:.3f} A; current limit guarantees {o1:.2f} A at {v1:g} V, {o2:.2f} A at {v2:g} V ({margin:+.2f} A); '
              f'{rms:.2f} A rms of {irms:.2f} A -> {"PASS" if ok else "FAIL"}')
    i5 = board_loads()['+5V'] + export_on('+5V')
    print(f'U34 limit {I_U34_MIN:.2f}..{I_U34_MAX:.2f} A against {i5:.3f} A on +5V at full export -> {"PASS" if i5 <= I_U34_MIN else "FAIL"}')
    for m, s, carried, allow, short in ration_rows():
        print(f'RATIONED {m} mode on {s}: U26 guarantees {carried:.1f} W of the {allow:.1f} W of export allowances, {short:.1f} W short')
    if problems:
        print('PROBLEMS')
        for p in problems: print(' -', p)
    if '--write' in sys.argv:
        open('ref/power-budget.md', 'w').write(report())
        print('wrote ref/power-budget.md')
    return 1 if problems else 0

if __name__ == '__main__':
    sys.exit(main())
