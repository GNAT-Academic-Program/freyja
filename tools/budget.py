#!/usr/bin/env python3
"""Rail-by-rail power qualification for Odin.

Every current figure this board publishes should be derivable, and every
regulator should be checked against the thing it is actually asked to do. This
file is the single source for both: a load table with a stated basis per line,
a regulator table with datasheet citations, and the arithmetic that turns them
into "how much can a slot actually take".

    python3 tools/budget.py            # print the tables
    python3 tools/budget.py --write    # also regenerate ref/power-budget.md

Exit status is non-zero if any rail fails its own check, so a design that does
not meet its published numbers cannot be quietly committed.

Bases, in decreasing order of trust:
  datasheet  a number lifted from a manufacturer document
  computed   derived here from datasheet numbers
  estimate   engineering judgement; the honest label for most FPGA loads
  target     a design goal not yet backed by measurement
"""
import sys, os

# --------------------------------------------------------------- the source
# USB-C sources guarantee vSafe5V = 4.75 V minimum at the receptacle. The weak
# host port is the interesting case: it sets the floor for everything.
SOURCES = [
    ('USB-C, weak host port',  4.75, 0.9,  'USB-C vSafe5V min, 5V/0.9A default'),
    ('USB-C, 5V/3A port',      5.00, 3.0,  'Type-C 3A advertised over CC'),
    ('USB-PD, 9V contract',    9.00, 3.0,  'PD Power Rules: 9V mandatory >15W'),
    ('J50 external input',     9.00, 3.0,  'documented range 9-14V'),
]

# OR-ing loss between the connector and VSYS: the SS34 Schottky plus the
# input eFuse in series with it.
VF_SS34   = 0.45     # SS34 forward drop around 0.5 A, 25 C
RON_U26   = 0.05     # TPS259470A, conservative above its 28.3 mohm typical
I_VSYS_HI = 0.60     # VSYS current at which that drop is evaluated
V_OR_DROP = VF_SS34 + RON_U26 * I_VSYS_HI

# ------------------------------------------------------------- regulators
# vin_min/vin_max/iout/fsw are datasheet numbers; l is what design.py fits.
REGS = [
    dict(ref='U11', part='TPS54202DDC', topo='buck', src='VSYS', rail='+5V',
         vout=5.0, vin_min=4.5, vin_max=28.0, iout=2.0, fsw=500e3, ind='10uH',
         ripple_max=0.40, cite='SLVSD26C: 4.5-28V in, 2A out, 500kHz fixed',
         # U11 cannot make 5V from 5V and is never meant to: on a plain 5V
         # source the rail is VBUS through Q2 instead. Firmware enables exactly
         # one of the two, so U11's input floor is the 9V case, not the 5V one.
         enabled_above=9.0 - V_OR_DROP),
    dict(ref='U12', part='AP63300WU-7', topo='buck', src='VSYS', rail='+3V3',
         vout=3.3, vin_min=3.8, vin_max=32.0, iout=3.0, fsw=500e3, ind='4.7uH',
         ripple_max=0.50, cite='Diodes DS42002: 3.8-32V in, 3A, 500kHz; '
         '3.3V reference circuit uses 4.7uH'),
    dict(ref='U13', part='TLV62569DRL', topo='buck', src='+5V', rail='+2V5',
         vout=2.5, vin_min=2.5, vin_max=5.5, iout=2.0, fsw=1.5e6, ind='2.2uH',
         ripple_max=0.35, cite='SLVSDG1C: 2.5-5.5V in, 2A out, 1.5MHz'),
    dict(ref='U14', part='TLV62569DRL', topo='buck', src='+5V', rail='+1V8',
         vout=1.8, vin_min=2.5, vin_max=5.5, iout=2.0, fsw=1.5e6, ind='2.2uH',
         ripple_max=0.35, cite='SLVSDG1C: recommends 2.2uH for 5V->1.8V/2A'),
    dict(ref='U15', part='SY8047QDC', topo='buck', src='+5V', rail='+1V0',
         vout=1.0, vin_min=2.5, vin_max=5.5, iout=4.0, fsw=1.25e6,
         ind='1uH_core', ripple_max=0.35,
         cite='Silergy SY8047 Rev 0.9: 2.5-5.5V in, 4A out, 1.25MHz; '
              'reference circuit uses 1.0uH and 2x22uF output'),
    dict(ref='U16', part='TLV62569DRL', topo='buck', src='+5V', rail='+1V2_MGT',
         vout=1.2, vin_min=2.5, vin_max=5.5, iout=2.0, fsw=1.5e6, ind='2.2uH',
         ripple_max=0.35, cite='SLVSDG1C: 2.5-5.5V in, 2A out, 1.5MHz'),
    dict(ref='U19', part='TPS61085PW', topo='boost', src='+5V', rail='+12V',
         vout=12.0, vin_min=2.3, vin_max=6.0, ilim=2.0, fsw=650e3, ind='10uH',
         ripple_max=0.35,
         cite='SLVS859B: 2.3-6V in, 18.5V max out, ILIM 2.0A min, '
              '650kHz with FREQ=GND, 6-13uH recommended at 650kHz'),
    # Not ours to size: Raspberry Pi specify the inductor, the three 4.7uF
    # caps and the layout, and say plainly that deviating is at your own risk.
    # So the ripple check is skipped rather than applied to someone else's
    # qualified design with a switching frequency we would have to invent.
    dict(ref='U7',  part='RP2350B VREG', topo='buck', src='+3V3', rail='+1V1',
         vout=1.1, vin_min=2.7, vin_max=3.6, iout=0.20, fsw=None, ind='3.3uH',
         ripple_max=None, mandated=True,
         cite='RP-008280 s2.1: 200mA, L1 = AOTA-B201610S3R3-101-T'),
]

# ------------------------------------------------------------------ loads
# (rail, what, amps, basis, citation). Worst case, all at once -- which is the
# only version of a budget that is any use.
LOADS = [
    # ---- +1V0, FPGA core
    ('+1V0', 'XC7A100T VCCINT, busy design', 1.50, 'estimate',
     'pre-bitstream planning allowance; replace with an AMD XPE result'),
    ('+1V0', 'VCCBRAM', 0.05, 'estimate', 'share of the 0.25 W AUX/BRAM line'),
    ('+1V0', '+1V0_MGT (MGTAVCC, filtered off +1V0)', 0.10, 'estimate',
     '2 lanes, share of the 0.4 W transceiver line'),
    # ---- +1V8, FPGA VCCAUX
    ('+1V8', 'XC7A100T VCCAUX', 0.18, 'estimate',
     'pre-bitstream planning allowance; replace with an AMD XPE result'),
    # ---- +1V2_MGT
    ('+1V2_MGT', 'MGTAVTT, 2 lanes', 0.15, 'estimate',
     'share of the 0.4 W transceiver line'),
    # ---- +3V3, the crowded one
    ('+3V3', 'RP2350B supervisor + boot flash', 0.07, 'estimate',
     'ref/power-input.md: 0.2 W'),
    ('+3V3', 'FPGA bank 14 VCCO and its I/O', 0.10, 'estimate',
     'one third of the 1.0 W VCCO/IO line'),
    ('+3V3', 'PSRAM x4, all active', 0.20, 'estimate',
     'ref/power-input.md: 0.66 W across four chips'),
    ('+3V3', 'config flash W25Q256, program', 0.03, 'datasheet',
     'W25Q256JV: 25 mA page-program peak'),
    ('+3V3', 'SFP modules x2 (SFP_VCC, gated by Q1)', 0.61, 'estimate',
     'ref/power-input.md: 2.0 W for two modules'),
    ('+3V3', 'Heartbeat and user LEDs x3, all on', 0.005, 'estimate',
     'D9-D11 via 1k each; 5 mA budget allowance'),
    ('+3V3', '125MHz LVDS oscillator', 0.04, 'estimate',
     'typical 6-pin LVDS oscillator'),
    ('+3V3', 'U9/U10 VCCA, U20, pull-ups, LED', 0.03, 'estimate',
     'quiescent logic'),
    ('+3V3', 'FPGA bank 15 VCCO, worst case jumpered to 3.3V', 0.10, 'estimate',
     'bank load only; connector export is checked from switch maximum below'),
    ('+3V3', 'FPGA bank 34 VCCO, worst case jumpered to 3.3V', 0.10, 'estimate',
     'bank load only; connector export is checked from switch maximum below'),
    ('+3V3', 'FPGA unused banks 13/16/35 VCCO', 0.06, 'estimate',
     'powered at 3.3V so every VCCO ball has a defined supply'),
    # ---- +1V1, the supervisor's core, off the RP2350's own regulator
    ('+1V1', 'RP2350B core (DVDD)', 0.06, 'estimate',
     'RP2350 at 150 MHz; the on-chip regulator is rated 200 mA'),
    # ---- +5V
    ('+5V', 'U9/U10 VCCB', 0.02, 'estimate', 'quiescent translator supply'),
    # ---- +12V AUX has no board-side load at all; it exists for the slots.
]

RAIL_ORDER = ['VSYS', '+5V', '+3V3', '+1V1', '+2V5', '+1V8', '+1V0',
              '+1V2_MGT', '+12V']
# Rails that leave the board on a connector have to be sized for their rating,
# because a slot is allowed to ask for the spare. The rest are sized for their
# actual load plus transient headroom -- +1V0 and +1V2_MGT never reach a pin.
EXPORTED = {'+5V', '+3V3', '+12V', '+2V5', '+1V8'}
TRANSIENT = 1.5
# The rails a slot can draw from, and the per-slot fuse fitted on each.
SLOT_RAILS = {'+5V': '500mA', '+3V3': '300mA', '+12V': '200mA',
              'VCCIO': '500mA'}
ETA = 0.90      # conversion efficiency assumption, per TI's own guidance

# ---------------------------------------------------------------- inductors
# L value comes out of the arithmetic below; Isat/DCR are datasheet numbers for
# the part named. design.py imports INDUCTOR so the schematic and this file
# cannot disagree about what is fitted. Two part numbers cover seven positions.
INDUCTOR = {
    '1uH_core': dict(mpn='FTC201610S1R0MBCA', l=1.0e-6, isat=4.60,
                     dcr=0.035, size='2.0 x 1.6 mm',
                     fp='EasyEDA:IND-SMD_L2.0-W1.6-B', lcsc='C5832342',
                     cite='cjiang FTC201610S1R0MBCA: 1.0uH +/-20%, '
                          'DCR 35 mohm, Irms 4.50 A, Isat 4.60 A'),
    '4.7uH': dict(mpn='SRN6045TA-4R7M', l=4.7e-6, isat=6.80, dcr=0.026,
                  size='6.0 x 6.0 x 4.5 mm',
                  fp='EasyEDA:IND-SMD_L6.0-W6.0', lcsc='C2044594',
                  cite='Bourns SRN6045TA: 4.7uH +/-20%, DCR 26 mohm, '
                       'Irms 4.50 A, Isat 6.80 A'),
    '10uH':  dict(mpn='SRN6045TA-100M', l=10.0e-6, isat=4.60, dcr=0.052,
                  size='6.0 x 6.0 x 4.5 mm',
                  fp='EasyEDA:IND-SMD_L6.0-W6.0-1', lcsc='C2046332',
                  cite='Bourns SRN6045TA: 10uH +/-20%, DCR 52 mohm, '
                       'Irms 3.20 A, Isat 4.60 A'),
    '2.2uH': dict(mpn='SRN4018-2R2M', l=2.2e-6, isat=3.00, dcr=0.044,
                  size='4.0 x 4.0 x 1.8 mm',
                  fp='EasyEDA:IND-SMD_L4.0-W4.0_SNR4018',
                  cite='Bourns SRN4018: 2.2uH +/-20%, DCR 44 mohm, '
                       'Irms 2.90 A, Isat 3.00 A', lcsc='C913207'),
    '1uH':   dict(mpn='VLS252010HBX-1R0M-1', l=1.0e-6, isat=3.57, dcr=0.054,
                  size='2.5 x 2.0 x 1.0 mm',
                  fp='EasyEDA:IND-SMD_L2.5-W2.0-1',
                  cite='TDK VLS252010HBX: 1.0uH +/-20%, DCR 54 mohm, '
                       'rated current 3.00 A, saturation current 3.57 A',
                  lcsc='C88211'),
    '3.3uH': dict(mpn='AOTA-B201610S3R3-101-T', l=3.3e-6, isat=2.40, dcr=0.140,
                  size='2.0 x 1.6 x 1.0 mm',
                  fp='EasyEDA:IND-SMD_L2.0-W1.6_AOTA-B201610S3R3-101-T',
                  lcsc='C42411119',
                  cite='Abracon: 3.3uH +/-20%, DCR 140 mohm max, Irms 2.10 A '
                       'min, Isat 2.40 A min; mandated by RP-008280 s2.1'),
}


def buck_ripple(vout, vin, l, fsw):
    """Peak-to-peak inductor ripple current of a CCM buck."""
    return vout * (1.0 - vout / vin) / (l * fsw)


def boost_capability(vin, vout, ilim, fsw, l, eta=ETA):
    """TPS61085 datasheet equations 1-4. Returns (D, dIL, Iout_max, Isw_peak)."""
    d = 1.0 - vin * eta / vout
    dil = vin * d / (fsw * l)
    iout = (ilim - dil / 2.0) * (1.0 - d)
    ipk = dil / 2.0 + iout / (1.0 - d)
    return d, dil, iout, ipk


def rail_load(rail):
    return sum(a for r, _, a, _, _ in LOADS if r == rail)


def analyse():
    reg = {r['rail']: r for r in REGS}
    rows, problems, notes = [], [], []

    vsys_min = min(v for _, v, _, _ in SOURCES) - V_OR_DROP
    vsys_max = 14.0                                 # J50 documented maximum
    railv = {'VSYS': (vsys_min, vsys_max)}
    for r in REGS:
        railv[r['rail']] = (r['vout'], r['vout'])
    # In 5V-only mode the +5V rail is VBUS through Q2, not U11's output.
    railv['+5V'] = (min(v for _, v, _, _ in SOURCES) - 0.05, 5.5)

    # ---- the boost, which is what AUX actually is
    b = reg['+12V']
    d12, dil12, iout12, ipk12 = boost_capability(
        railv['+5V'][0], b['vout'], b['ilim'], b['fsw'],
        INDUCTOR[b['ind']]['l'])
    aux_from_boost = iout12
    aux_input_i = iout12 * b['vout'] / (railv['+5V'][0] * ETA)

    # ---- own loads, then cascade child input currents onto parents
    load = {r: rail_load(r) for r in RAIL_ORDER}
    # children of +5V: the four TLV62569 and the boost
    for r in REGS:
        if r['src'] == '+5V' and r['rail'] != '+12V':
            iin = load[r['rail']] * r['vout'] / (railv['+5V'][0] * ETA)
            load['+5V'] += iin
    # children of +3V3: the RP2350's own core regulator
    load['+3V3'] += load['+1V1'] * 1.1 / (3.3 * ETA)
    # VSYS carries U11 and U12
    load['VSYS'] = 0.0

    # ---- per-regulator checks
    for r in REGS:
        rail = r['rail']
        vin_lo, vin_hi = railv[r['src']]
        used = load[rail]
        cap = r.get('iout', aux_from_boost if r['topo'] == 'boost' else 0.0)
        ind = INDUCTOR[r['ind']]
        design_i = (r['iout'] if rail in EXPORTED and 'iout' in r
                    else used * TRANSIENT)
        if r['topo'] == 'boost':
            cap, dil, ipk = aux_from_boost, dil12, ipk12
            ripple = dil / (aux_from_boost / (1 - d12)) if aux_from_boost else 0
        elif r.get('mandated'):
            dil, ipk, ripple = 0.0, used, 0.0
        else:
            dil = buck_ripple(r['vout'], vin_hi, ind['l'], r['fsw'])
            ipk = design_i + dil / 2.0
            ripple = dil / r['iout']
        # 30% over the peak, which is what the TLV62569 datasheet asks for.
        isat_req = 1.3 * max(ipk, dil / 2.0)
        if not r.get('mandated') and ind['isat'] < isat_req:
            problems.append(
                f"{r['ref']}: {ind['mpn']} saturates at {ind['isat']:.2f}A but "
                f"the rail needs {isat_req:.2f}A ({ipk:.2f}A peak +30%)")
        vin_lo_eff = max(vin_lo, r.get('enabled_above', 0.0))
        if vin_lo_eff < r['vin_min']:
            problems.append(
                f"{r['ref']} ({r['part']}) needs Vin >= {r['vin_min']}V but its "
                f"source {r['src']} falls to {vin_lo_eff:.2f}V on the weakest "
                f"input it is enabled on")
        if vin_hi > r['vin_max']:
            problems.append(f"{r['ref']} sees {vin_hi:.2f}V, over its "
                            f"{r['vin_max']}V maximum")
        if r['ripple_max'] is not None and ripple > r['ripple_max']:
            problems.append(
                f"{r['ref']} inductor ripple is {ripple*100:.0f}% of full load "
                f"with L={r['l']*1e6:g}uH, over the {r['ripple_max']*100:.0f}% "
                f"guideline")
        rows.append(dict(ref=r['ref'], part=r['part'], rail=rail,
                         vout=r['vout'], src=r['src'], vin_lo=vin_lo,
                         vin_hi=vin_hi, vin_lo_eff=vin_lo_eff,
                         cap=cap, used=used, l=ind['l'], mpn=ind['mpn'],
                         isat_have=ind['isat'], lsize=ind['size'],
                         design_i=design_i,
                         dil=dil, ipk=ipk, isat=isat_req, cite=r['cite'],
                         spare=cap - used))
    # ---- what a slot can have.
    # AUX is not simply the boost's capability: every milliamp out of the boost
    # costs Vout/(Vin*eta) milliamps of the +5V rail, and the +5V rail is also
    # what the slots' own +5V pins come from. Report the binding limit.
    spare = {row['rail']: row['spare'] for row in rows}
    aux_from_5v = spare['+5V'] * railv['+5V'][0] * ETA / b['vout']
    aux_cost = b['vout'] / (railv['+5V'][0] * ETA)     # mA of +5V per mA of AUX
    spare['+12V'] = min(aux_from_boost, aux_from_5v)
    for rail in ('+5V', '+3V3', '+12V'):
        if spare[rail] < 0:
            problems.append(f"{rail} is oversubscribed by "
                            f"{-spare[rail]*1000:.0f} mA before any slot draws")
    # Both VCCIO domains can select the same source. Use the load switch's
    # maximum specified limit, not its typical label, and add both FPGA banks.
    ext_sw_max = 0.620
    bank_pair = 0.200
    selector_cases = {
        '+3V3': load['+3V3'] + 2 * ext_sw_max,
        '+2V5': load['+2V5'] + bank_pair + 2 * ext_sw_max,
        '+1V8': load['+1V8'] + bank_pair + 2 * ext_sw_max,
    }
    for rail, worst in selector_cases.items():
        cap = reg[rail]['iout']
        if worst > cap:
            problems.append(f"{rail}: both VCCIO domains at 620mA max plus "
                            f"bank/base loads need {worst:.3f}A, over {cap:.3f}A")
    return rows, spare, problems, dict(
        vsys_min=vsys_min, vsys_max=vsys_max, v5_min=railv['+5V'][0],
        d12=d12, dil12=dil12, iout12=iout12, ipk12=ipk12,
        aux_input_i=aux_input_i, load=load, aux_from_5v=aux_from_5v,
        aux_cost=aux_cost, aux_limit=spare['+12V'], selector_cases=selector_cases)


def fmt(rows):
    o = []
    o.append('| Ref | Part | Rail | Source | Vin seen | Capability | '
             'Board load | Spare |')
    o.append('|---|---|---|---|---|---|---|---|')
    for r in rows:
        o.append(f"| `{r['ref']}` | `{r['part']}` | {r['rail']} | {r['src']} | "
                 f"{r['vin_lo_eff']:.2f}–{r['vin_hi']:.2f} V | {r['cap']*1000:.0f} mA "
                 f"| {r['used']*1000:.0f} mA | {r['spare']*1000:.0f} mA |")
    return '\n'.join(o)


HEAD = """# Odin power budget

**Generated by `tools/budget.py`. Do not hand-edit.** Every number below is
either a datasheet figure, or arithmetic on datasheet figures, or an estimate
that says so. Nothing here is a round number chosen because it looked right.

The load table is worst case *simultaneous*: both VCCIO domains jumpered to
3.3 V, two SFP modules fitted and powered, all four PSRAMs active, the FPGA
core busy. That is a case you can build, so it is the case the rails have to
survive.
"""


def main():
    rows, spare, problems, x = analyse()
    print(f"OR-ing drop VBUS->VSYS: {V_OR_DROP:.2f} V "
          f"(SS34 {VF_SS34} V + {RON_U26} ohm x {I_VSYS_HI} A)")
    print(f"VSYS: {x['vsys_min']:.2f} V worst case .. {x['vsys_max']:.2f} V "
          f"(J50 documented maximum)\n")
    print(f"{'ref':5s} {'rail':9s} {'src':6s} {'Vin':13s} {'cap':>8s} "
          f"{'load':>8s} {'spare':>8s} {'L':>7s} {'dIL':>8s} {'Ipk':>7s} "
          f"{'Isat>=':>7s}")
    for r in rows:
        print(f"{r['ref']:5s} {r['rail']:9s} {r['src']:6s} "
              f"{r['vin_lo_eff']:5.2f}-{r['vin_hi']:5.2f}V "
              f"{r['cap']*1e3:7.0f}m {r['used']*1e3:7.0f}m "
              f"{r['spare']*1e3:7.0f}m {r['l']*1e6:6.1f}u "
              f"{r['dil']*1e3:7.0f}m {r['ipk']:6.2f}A {r['isat']:6.2f}A")
    print(f"\nAUX 12V boost, worst-case input {x['v5_min']:.2f} V:")
    print(f"  duty {x['d12']*100:.1f}%  ripple {x['dil12']*1000:.0f} mA  "
          f"Iout(max) {x['iout12']*1000:.0f} mA  Ipk(switch) {x['ipk12']:.2f} A")
    print(f"  which draws {x['aux_input_i']*1000:.0f} mA from +5V at full load"
          f"  ({x['aux_cost']:.2f} mA of +5V per mA of AUX)")
    print(f"  +5V can only spare {x['aux_from_5v']*1000:.0f} mA of AUX, so the "
          f"binding AUX limit is {x['aux_limit']*1000:.0f} mA")
    if problems:
        print("\nPROBLEMS")
        for p in problems:
            print(f"  - {p}")
    if '--write' in sys.argv:
        out = [HEAD, '\n## Regulators, loads and what is left over\n',
               fmt(rows), '']
        out.append(f"""
`Vin seen` is the range that rail's *source* covers across every documented
input, including the {V_OR_DROP:.2f} V OR-ing drop from `VBUS` to `VSYS`
(SS34 forward drop plus the input eFuse). `Capability` is the
datasheet output rating, except for `+12V`, where it is computed below.
`Spare` is what remains for the extension slots after the board's own worst
case.

Two caveats on the +5 V row. It is `U11`'s 2 A rating, which only applies once
a 9 V contract or `J50` is present; **on a plain 5 V source the rail is `VBUS`
through `Q2`, so its ceiling is whatever the USB source gives** — 0.9 A on a
weak host port, against a board that already wants more than that. And the AUX
boost draws from this same rail, as the next section works out.

## The AUX 12 V rail, computed rather than asserted

`U19` is a `TPS61085` boost from +5 V. Its capability is not "5 V x 2 A / 12 V";
it is TI's design procedure (SLVS859B equations 1-4) at the worst-case input:

| | |
|---|---|
| Input, worst case | {x['v5_min']:.2f} V |
| Duty cycle | {x['d12']*100:.1f}% |
| Inductor | {[r for r in rows if r['rail']=='+12V'][0]['l']*1e6:g} µH at 650 kHz |
| Inductor ripple | {x['dil12']*1000:.0f} mA p-p |
| Switch current limit | 2.0 A **minimum** |
| **Iout(max)** | **{x['iout12']*1000:.0f} mA** |
| Peak switch current | {x['ipk12']:.2f} A |
| Draw on +5 V at full load | {x['aux_input_i']*1000:.0f} mA |

Two things follow. First, the honest boost figure is around
{x['iout12']*1000:.0f} mA, not 700 mA — and even that assumes 90% efficiency
and ignores thermals, so treat it as a **provisional design target** until a
board is measured. Second, AUX at full output would pull
{x['aux_input_i']*1000:.0f} mA out of the +5 V rail, which only has
{spare['+5V']*1000:.0f} mA spare, so the boost is not the binding constraint
— the 5 V rail is. **AUX is therefore {x['aux_limit']*1000:.0f} mA**, and
every milliamp of it costs {x['aux_cost']:.2f} mA of +5 V, so AUX and the
slots' own +5 V pins are drawing from the same pot.

## Active extension-bus limits

These switches sit before the per-slot PTCs. The resistor calculations use
the equations in TI SLVSFJ2B and SLVSFC9C.

| Protected bus | Part | Programming | Typical trip/limit | Datasheet range |
|---|---|---|---:|---:|
| `+5V_EXT` | TPS22950CDDCR | `RILIM=1.15 kohm`; `1.18 x 1.15^-1.072` | 1.000 A | 0.75-1.25 A; below 1.615 A source headroom |
| `+3V3_EXT` | TPS22950CDDCR | `RILIM=2.21 kohm`; `1.18 x 2.21^-1.072` | 0.500 A | 0.38-0.62 A |
| `VCCIO_1_EXT` | TPS22950CDDCR | same 2.21 kohm | 0.500 A | 0.38-0.62 A |
| `VCCIO_2_EXT` | TPS22950CDDCR | same 2.21 kohm | 0.500 A | 0.38-0.62 A |
| `+12V_EXT` | TPS259470LRPWR | `RILM=6.65 kohm`; `3334/6650` | 0.501 A | 0.425-0.575 A |

The +12 V switch, not the provisional 569 mA rail calculation, is now the
connector-facing ceiling. Its OVLO divider is 121 kohm / 12.1 kohm:
`1.2 x (121+12.1)/12.1 = 13.2 V` nominal. A 3.3 nF `dVdt` capacitor gives
about 20 ms rise time at 12 V. C232 adds 10 uF / 25 V directly on
+12V_EXT after U25, ahead of the selectors and PTCs. At this nominal
slew rate its added charging current is about 6 mA (`10uF * 12V / 20ms`),
excluding extension capacitance. Place it close to OUT and its ground return.

Worst-case selectable-rail checks use **620 mA**, the maximum limit of each
VCCIO switch, for both domains at once:

| Source selected by both domains | Base + two FPGA banks + two switch maxima | Regulator rating |
|---|---:|---:|
| +3V3 | {x['selector_cases']['+3V3']:.3f} A | 3.000 A |
| +2V5 | {x['selector_cases']['+2V5']:.3f} A | 2.000 A |
| +1V8 | {x['selector_cases']['+1V8']:.3f} A | 2.000 A |

Note that TI's equation 2 is written with `ILIM(min)` but the accompanying
symbol list says "minimum switch current limit = 3.2 A", which is the
datasheet's *maximum*. The 2.0 A minimum from the electrical table is used
here, because that is the value guaranteed for every part.

## Inductors: what each rail requires

| Ref | Rail | L | Ripple | Peak | Isat required | Part fitted |
|---|---|---|---|---|---|---|""")
        for r in rows:
            lu = round(r['l'] * 1e6, 1)
            out.append(f"| `{r['ref']}` | {r['rail']} | {lu:g} µH | "
                       f"{r['dil']*1000:.0f} mA p-p | {r['ipk']:.2f} A | "
                       f"**{r['isat']:.2f} A** | `{r['mpn']}`, "
                       f"Isat {r['isat_have']:.2f} A, {r['lsize']} |")
        out.append("""
`Isat required` is the peak inductor current with 30% margin, which is what
the TLV62569 datasheet asks for; `Peak` is taken at the rail's *rating* for
rails that reach a connector, and at 1.5x the actual load for +1V0, +1V2_MGT
and +1V1, which do not. Two part numbers cover seven positions, and
`tools/budget.py` fails if any of them saturates below what its rail needs.

## Load table, with the basis for every line

| Rail | Consumer | Current | Basis | Where it comes from |
|---|---|---|---|---|""")
        for rail, what, a, basis, cite in LOADS:
            out.append(f"| {rail} | {what} | {a*1000:.0f} mA | {basis} | {cite} |")
        out.append("""
Rails also load their parents: each buck's input current is added to the rail
it runs from, at 90% efficiency. That is why the +5 V and +3V3 figures in the
first table exceed the sum of their own lines.

## What a slot actually gets""")
        out.append('\n| Rail | Shared total, all ten extension ports | Per-port fuse |')
        out.append('|---|---|---|')
        for rail, protected, fuse in (('+5V', '1000 mA typical (750-1250 mA)', '500 mA'),
                                      ('+3V3', '500 mA typical (380-620 mA)', '300 mA'),
                                      ('+12V (AUX)', '500 mA typical (425-575 mA)', '200 mA')):
            out.append(f"| {rail} | **{protected}** | {fuse} |")
        out.append("""
The fuses are fault protection. Nine of them do not add up to an allowance,
and the protected totals above are the connector-facing limits.

VCCIO is not in that table because it has no source of its own: the jumper
points a whole domain at +3V3, +2V5 or +1V8, and the domain's slots then share
whatever that rail has spare after the FPGA bank takes its share.
""")
        if problems:
            out.append('## Failing checks\n')
            out.append('`tools/budget.py` exits non-zero while these stand:\n')
            for p in problems:
                out.append(f"- {p}")
            out.append('')
        open('ref/power-budget.md', 'w').write('\n'.join(out))
        print("\nwrote ref/power-budget.md")
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
