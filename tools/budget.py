#!/usr/bin/env python3
"""Executable power limits and the generated Odin power-budget report."""
import sys

# (name, minimum voltage at the connector, current the source guarantees, note)
# Currents are what the source profile promises, not what the board may take.
# What the controller can observe (findings item 55): the CC lines go only to
# the CH224K, which has no data interface (the CH224A/Q I2C status register
# exists on those parts, not on the K; WCH CH224 manual 1 v2.1, Table 5-3),
# so a 5 V Type-C advertisement (default / 1.5 A / 3 A) is not readable.
# Observable are PD_PG (the 9 V request succeeded), VBUS5_ST (which input
# feeds +5V) and MON_VSYS (the screw input is present). A 9 V contract is a
# guarantee in itself: any source that offers 9 V must offer it at 15 W or
# more, 1.67 A at 9 V (USB PD power rules, PD3 section 10.2 [verify]); 3 A at
# 9 V is only guaranteed above 27 W and is not observable, so it is not
# planned on. The 5 V rows above 500 mA are user-declared ports: firmware
# may use them only on a stored setting the user made, never by detection.
SOURCES = [
    ('USB 2.0 port', 4.75, 0.5, 'configured bus power; an SDP guarantees no more; the planning default for any 5 V source'),
    ('USB-C 5V/1.5A', 4.75, 1.5, 'Type-C 1.5 A advertisement (Rp): NOT observable by the controller; user-declared only'),
    ('USB-C 5V/3A', 4.75, 3.0, 'Type-C 3 A advertisement: NOT observable; user-declared only'),
    ('USB-PD 9V', 9.00, 1.67, 'the only contract above 5 V the CFG pins can form; a 9 V PDO is 15 W or more (PD power rules [verify])'),
    ('J50 VIN', 9.00, 3.0, 'official 9-21 V screw-input range; 3 A is the planning figure; U34 (Q7) puts the whole board on it, USB connected or not'),
]
# Hardware limits on the two USB paths: U26 (eFuse to VSYS) and U34 (mux to
# +5V) draw from the same connector when the source is plain 5 V.
I_U26_MIN, I_U26_TYP = 1.70, 2.03     # TPS259470A 1.65k ILM, SLVSFC9C
I_U34_MIN, I_U34_TYP = 2.00, 2.50     # TPS2121 44.2k RILM, SLVSEA3F Table 7.5
ETA = 0.90                            # planning efficiency per conversion stage
# Rails whose regulator is held off in recovery mode (EN low from the
# controller's reset state): nothing on them draws in recovery.
RECOVERY_OFF = {'+1V0', '+2V5', '+1V2_MGT'}

# Connector exports: planning allowances per protected bus, each the switch's
# typical limit or, for the PIN V domains, one slot fuse's hold current.
# They are not additive guarantees: ref/extension-ux.md.
EXPORTS = [
    ('+5V_EXT', 5.0, 1.00, 'U21 TPS22950C 1.15k, 1.0 A typical'),
    ('+3V3_EXT', 3.3, 0.50, 'U22 TPS22950C 2.21k, 0.5 A typical'),
    ('VCCIO_1_EXT', 3.3, 0.50, 'U23 TPS22953, no limit of its own: one 500 mA PINV PTC'),
    ('VCCIO_2_EXT', 3.3, 0.50, 'U24 TPS22953, no limit of its own: one 500 mA PINV PTC'),
]

VF_SS34 = 0.45
RON_U26 = 0.05
I_VSYS_HI = 0.60
V_OR_DROP = VF_SS34 + RON_U26 * I_VSYS_HI
VSYS_MIN = min(v for _, v, _, _ in SOURCES) - V_OR_DROP
VSYS_MAX = 21.0

# design.py consumes this exact table, so arithmetic and fitted parts cannot
# silently diverge.
INDUCTOR = {
    '1uH_core': dict(mpn='FTC201610S1R0MBCA', l=1.0e-6, isat=4.60,
                     dcr=0.035, size='2.0 x 1.6 mm',
                     fp='EasyEDA:IND-SMD_L2.0-W1.6-B', lcsc='C5832342',
                     cite='cjiang FTC201610S1R0MBCA: Irms 4.50 A, Isat 4.60 A'),
    '4.7uH': dict(mpn='SRN6045TA-4R7M', l=4.7e-6, isat=6.80, dcr=0.026,
                  size='6.0 x 6.0 x 4.5 mm', fp='EasyEDA:IND-SMD_L6.0-W6.0',
                  lcsc='C2044594', cite='Bourns SRN6045TA: Irms 4.50 A, Isat 6.80 A'),
    '10uH': dict(mpn='SRN6045TA-100M', l=10e-6, isat=4.60, dcr=0.052,
                  size='6.0 x 6.0 x 4.5 mm', fp='EasyEDA:IND-SMD_L6.0-W6.0-1',
                  lcsc='C2046332', cite='Bourns SRN6045TA: Irms 3.20 A, Isat 4.60 A'),
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
# Recovery is the controller alone with the FPGA unconfigured, +1V0/+2V5/
# +1V2_MGT held off, the PHY in reset, the memories idle on their always-on
# rails: standby or reset currents, never zero for a part that is powered,
# never the active figure (findings, re-audit 2026-10-29).
LOADS = [
    # ---- +1V0, FPGA core
    ('+1V0', 'XC7A100T VCCINT, busy design', 1.50, 0.0, 'estimate',
     'pre-bitstream planning allowance; replace with an AMD XPE result'),
    ('+1V0', 'VCCBRAM', 0.05, 0.0, 'estimate', 'share of the 0.25 W AUX/BRAM line'),
    ('+1V0', '+1V0_MGT (MGTAVCC, filtered off +1V0)', 0.10, 0.0, 'estimate',
     '2 lanes, share of the 0.4 W transceiver line'),
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
     'SN74LXC8T245 SCES916A section 6.5: ICCA 4 uA max per device; '
     'switching current is counted in the bank 13 line'),
    # ---- +1V2_MGT
    ('+1V2_MGT', 'MGTAVTT, 2 lanes', 0.15, 0.0, 'estimate',
     'share of the 0.4 W transceiver line'),
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
    ('+3V3', 'RTL8211FD-CG, 1000Base-T link', 0.20, 0.05, 'estimate',
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
    ('+2V5', 'RTL8211FD-CG DVDD_RG (RGMII pads)', 0.02, 0.0, 'estimate',
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
    ('U11', 'AP63300WU-7', 'VSYS', '+5V', 3.8, 32.0, 3.0),
    ('U12', 'AP63300WU-7', 'VSYS', '+3V3', 3.8, 32.0, 3.0),
    ('U13', 'TLV62569DRLR', '+5V', '+2V5', 2.5, 5.5, 2.0),
    ('U14', 'TLV62569DRLR', '+5V', '+1V8_IO', 2.5, 5.5, 2.0),
    ('U15', 'SY8047QDC', '+5V', '+1V0', 2.5, 5.5, 4.0),
    ('U16', 'TLV62569DRLR', '+5V', '+1V2_MGT', 2.5, 5.5, 2.0),
]
# Per regulator: the net its capacitors sit on, inductor key, switching
# frequency, and what the datasheet has actually validated for COUT
# (findings item 40). Anything above the validated figure is a bench
# qualification item, not a build error: load-step and start-up on the
# assembled board, every jumper position.
REG_DETAIL = {
    'U11': dict(node='+5V_BUCK', ind='4.7uH', fsw=500e3, vin=9.0, vin_max=21.0,
                cout_ok=68e-6, cite='DS42002 p. 19: 22-68 uF ceramic for most applications'),
    'U12': dict(node='+3V3', ind='4.7uH', fsw=500e3, vin=9.0, vin_max=21.0,
                cout_ok=68e-6, cite='DS42002 p. 19: 22-68 uF ceramic for most applications'),
    'U13': dict(vin_max=5.5, node='+2V5', ind='2.2uH', fsw=1.5e6, vin=5.0,
                cout_ok=47e-6, cite='SLVSDG1C 8.2.2.5: 10-47 uF, Table 4 up to 2 x 22 uF'),
    'U14': dict(vin_max=5.5, node='+1V8_IO', ind='2.2uH', fsw=1.5e6, vin=5.0,
                cout_ok=47e-6, cite='SLVSDG1C 8.2.2.5: 10-47 uF, Table 4 up to 2 x 22 uF'),
    'U15': dict(vin_max=5.5, node='+1V0', ind='1uH_core', fsw=1.25e6, vin=5.0,
                cout_ok=44e-6, cite='Silergy SY8047 rev 0.9 reference circuit: 2 x 22 uF'),
    'U16': dict(vin_max=5.5, node='+1V2_MGT', ind='2.2uH', fsw=1.5e6, vin=5.0,
                cout_ok=47e-6, cite='SLVSDG1C 8.2.2.5: 10-47 uF, Table 4 up to 2 x 22 uF'),
}
# Rails that hang off a regulator node through a bead or inductor: their
# capacitance is a frequency-dependent load, listed beside the direct sum.
BEHIND = {'+1V8_IO': ('+1V8', 'FB1'), '+1V0': ('+1V0_MGT', 'L9')}


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
        vout = {'+5V': 5.0, '+3V3': 3.3, '+2V5': 2.5, '+1V8_IO': 1.8, '+1V0': 1.0, '+1V2_MGT': 1.2}[out]
        iload = loads[out]
        if out == '+5V': iload += 1.0          # +5V_EXT allowance rides on U11
        if out == '+3V3': iload += 0.5 + 1.0   # +3V3_EXT and both PIN V domains at 3.3 V
        ripple = vout * (1 - vout / d['vin']) / (ind['l'] * d['fsw'])
        ripple_env = vout * (1 - vout / d['vin_max']) / (ind['l'] * L_TOL * d['fsw'])
        ipk = iload + ripple / 2
        ipk_env = iload + ripple_env / 2
        rows.append((ref, ind['mpn'], iload, ripple, ipk, d['vin_max'], ipk_env, ind['isat'],
                     ipk_env <= ind['isat']))
    return rows


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
    modes = [('recovery', p33_rec, p5_rec), ('light', p33, p5_board),
             ('full', p33 + sum(v*a for n, v, a, _c in EXPORTS if n != '+5V_EXT'),
              p5_board + 5.0 * 1.0)]
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

def board_loads():
    own = {rail: sum(amps for r, _, amps, _rec, _k, _n in LOADS if r == rail)
           for rail in ('+5V', '+3V3', '+2V5', '+1V8_IO', '+1V0', '+1V1', '+1V2_MGT')}
    own['+5V'] += sum(own[r]*v/(4.7*0.90) for r,v in
                     (('+2V5',2.5),('+1V8_IO',1.8),('+1V0',1),('+1V2_MGT',1.2)))
    own['+3V3'] += own['+1V1']*1.1/(3.3*0.90)
    return own

def recovery_loads():
    """Like board_loads, from the recovery column; rails in RECOVERY_OFF
    are zero whatever their line says."""
    own = {rail: (0.0 if rail in RECOVERY_OFF else
                  sum(rec for r, _, _a, rec, _k, _n in LOADS if r == rail))
           for rail in ('+5V', '+3V3', '+2V5', '+1V8_IO', '+1V0', '+1V1', '+1V2_MGT')}
    own['+5V'] += sum(own[r]*v/(4.7*0.90) for r,v in
                     (('+2V5',2.5),('+1V8_IO',1.8),('+1V0',1),('+1V2_MGT',1.2)))
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
    for mode, src, v, p, i, lim, ok, hw in mode_rows():
        if ((mode == 'recovery' and src == 'USB 2.0 port') or
                (mode in ('recovery', 'light') and src == 'USB-PD 9V') or
                (mode == 'full' and src == 'J50 VIN')) and not ok:
            problems.append(f'{mode} mode does not fit {src}: {i:.2f} A against {lim:g} A ({hw})')
    if VSYS_MIN < 3.8:
        problems.append(f'AP63300 minimum 3.8 V exceeds VSYS minimum {VSYS_MIN:.2f} V')
    if VSYS_MAX > 32.0:
        problems.append('21 V VIN exceeds AP63300 operating maximum')
    loads = board_loads()
    for ref, part, src, rail, lo, hi, cap in REGULATORS:
        if loads[rail] > cap:
            problems.append(f'{ref}: board-only {loads[rail]:.3f} A exceeds {cap:g} A')
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
        f'| {m} | {s} | {v:g} V | {p:.2f} W | {i:.2f} A | {lim:.2f} A | {"fits" if ok else "**does not fit**"} | {hw} |'
        for m, s, v, p, i, lim, ok, hw in mode_rows())
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

USB-C can start at 4.75 V. The SS34 plus USB eFuse model loses
{V_OR_DROP:.2f} V at 0.6 A, leaving **{VSYS_MIN:.2f} V**. The screw input is
**9–21 V DC**. U11/U12 are AP63300 devices (3.8–32 V operating) and cover
the full VSYS envelope. Both run without an enable: +3V3, +5V and the 1.8 V
rail behind U14 are present whenever the board has power, so the FPGA's
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
+5V consumer accepts; firmware asks for 9 V before it enables EXT_EN.
Both of U34's inputs block reverse current and the rail is limited to
{I_U34_TYP:g} A typical.

The VIN clamp is SMBJ22A: 22 V standoff and 35.5 V maximum rated pulse clamp.
The AP63300's 40 V/400 ms transient limit is the lowest transient limit after
D4. VSYS capacitors are 50 V X7R. No switching node on the board sees VSYS
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

Recovery is the controller alone with the FPGA unconfigured: +1V0, +2V5 and
+1V2_MGT are held off, everything on +3V3, +1V8_IO and +5V is still
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
rail carries (+5V: 1 A for +5V_EXT; +3V3: 0.5 A for +3V3_EXT and 1 A for
both PIN V domains at 3.3 V). The envelope column repeats the peak at the
highest input the converter can see (21 V on U11/U12, 5.5 V on the 5 V
row) with the inductance at -20 % (the fitted parts are "M" tolerance);
that is the figure checked against saturation.

| Ref | Inductor | Load | Ripple | Peak | Peak, envelope | Isat | |
|---|---|---:|---:|---:|---:|---:|---|
{inds}

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
USB cable attached: USB then carries nothing but the CH224K.

**Source policy (findings item 55).** The controller cannot read a 5 V
Type-C advertisement: the CC lines go only to the CH224K, which has no
data interface (that is the CH224A/Q, not the fitted K). What it can read
is PD_PG (the 9 V request was granted), VBUS5_ST (which input feeds +5V)
and MON_VSYS (J50 present). So:

1. Any 5 V source is planned as a USB 2.0 port, 500 mA: recovery mode only.
   Recovery draws about {mode_rows()[0][4]*1000:.0f} mA at 4.75 V. That fits
   the configured 500 mA but not the 100 mA USB 2.0 allows an unconfigured
   device: the PHY, SDRAM and oscillator sit on the always-on
   +3V3 with no switch. Open item: accept it (ports rarely police the
   100 mA step) or give those loads a switch in rev B; this table does not
   claim the pre-enumeration allowance is met.
2. A granted 9 V request is a 15 W guarantee (a 9 V PDO is offered at 1.67 A
   or more under the PD power rules [verify PD3 10.2]): light mode fits,
   full export does not, and firmware rations EXT_EN inside what U26's
   minimum limit leaves over the board load.
3. A 5 V port above 500 mA (1.5 A / 3 A rows) is a user-declared setting the
   controller stores; it is never detected. J50 is detected (MON_VSYS) and
   carries full mode.

The hardware limits (U26, U34, the PTCs) protect the board and the
connector, not the source. The contract checked by `budget.py`: recovery
fits a USB 2.0 port, recovery and light fit a 9 V PD contract, full fits
J50.

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
per-zone PTCs remain 500 mA PINV, 300 mA 3V3, and 500 mA 5V. These are fault
isolation, not additive current allocations: an overloaded external supply
droops the shared rail; a branch short heats and opens that branch PTC. AUX
has no active reverse blocking: never drive voltage back into a connector AUX
pin.
'''

def main():
    problems = analyse()
    print(f'VSYS envelope: {VSYS_MIN:.2f}..{VSYS_MAX:.2f} V')
    print(f'AP63300 minimum operating input: 3.80 V -> {"PASS" if VSYS_MIN >= 3.8 else "FAIL"}')
    if problems:
        print('PROBLEMS')
        for p in problems: print(' -', p)
    if '--write' in sys.argv:
        open('ref/power-budget.md', 'w').write(report())
        print('wrote ref/power-budget.md')
    return 1 if problems else 0

if __name__ == '__main__':
    sys.exit(main())
