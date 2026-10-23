#!/usr/bin/env python3
"""Executable power limits and the generated Odin power-budget report."""
import sys, math

SOURCES = [
    ('USB-C default', 4.75, 0.9, 'USB vSafe5V minimum; source-current limited'),
    ('USB-C 5V/3A', 5.00, 3.0, 'Type-C 3A advertisement'),
    ('USB-PD 9V', 9.00, 3.0, 'Odin requests only 9 V'),
    ('J50 VIN', 9.00, 3.0, 'official 9-21 V screw-input range'),
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
    # AUX has no internal board load; it feeds the ten fused branches.
]

REGULATORS = [
    ('U11', 'AP63300WU-7', 'VSYS', '+5V', 3.8, 32.0, 3.0),
    ('U12', 'AP63300WU-7', 'VSYS', '+3V3', 3.8, 32.0, 3.0),
    ('U13', 'TLV62569DRLR', '+5V', '+2V5', 2.5, 5.5, 2.0),
    ('U14', 'TLV62569DRLR', '+5V', '+1V8', 2.5, 5.5, 2.0),
    ('U15', 'SY8047QDC', '+5V', '+1V0', 2.5, 5.5, 4.0),
    ('U16', 'TLV62569DRLR', '+5V', '+1V2_MGT', 2.5, 5.5, 2.0),
    ('U28', 'LM5157RTER SEPIC', 'VSYS', 'AUX_REG', 2.9, 45.0, None),
]

AUX_POWER_W = 12.0
AUX_VOUTS = (9, 12, 15, 24)
AUX_VSYS = (5, 9, 12, 19)
BASE_RESERVE_W = 8.0  # conservative planning reservation, not a measured load
AUX_ETA = 0.85       # efficiency assumption; must be verified on prototypes
USB_VSYS_LIMIT = 1.70  # conservative allocation below U26's 2.03 A typical
AUX_FSW = 2.21e10 / (49900 + 955)
AUX_L_MIN = 4.7e-6 * 0.8

def aux_current(vout, vsys):
    # 5/9 V columns assume the USB/U26 path. 12/19 V assume the screw input.
    source_amps = USB_VSYS_LIMIT if vsys <= 9 else 3.0
    available = max(0.0, vsys * source_amps - BASE_RESERVE_W) * AUX_ETA
    # Round DOWN: do not publish more current than the computed allocation.
    return math.floor(100 * min(1.0, AUX_POWER_W / vout, available / vout)) / 100

def board_loads():
    own = {rail: sum(amps for r, _, amps, _, _ in LOADS if r == rail)
           for rail in ('+5V', '+3V3', '+2V5', '+1V8', '+1V0', '+1V1', '+1V2_MGT')}
    own['+5V'] += sum(own[r]*v/(4.7*0.90) for r,v in
                     (('+2V5',2.5),('+1V8',1.8),('+1V0',1),('+1V2_MGT',1.2)))
    own['+3V3'] += own['+1V1']*1.1/(3.3*0.90)
    return own

def analyse():
    problems = []
    if VSYS_MIN < 2.9:
        problems.append(f'LM5157 minimum 2.9 V exceeds VSYS minimum {VSYS_MIN:.2f} V')
    if VSYS_MIN < 3.8:
        problems.append(f'AP63300 minimum 3.8 V exceeds VSYS minimum {VSYS_MIN:.2f} V')
    if VSYS_MAX > 32.0:
        problems.append('21 V VIN exceeds AP63300 operating maximum')
    iin = AUX_POWER_W / (5.0 * 0.85)
    if iin >= 5.0:
        problems.append(f'AUX worst-case input current {iin:.2f} A exceeds 5 A winding rating')
    loads = board_loads()
    for ref, part, src, rail, lo, hi, cap in REGULATORS:
        if cap and loads[rail] > cap:
            problems.append(f'{ref}: board-only {loads[rail]:.3f} A exceeds {cap:g} A')
    for vin in (VSYS_MIN, 5, 9, 12, 19, VSYS_MAX):
        for vo in AUX_VOUTS:
            io = min(1.0, AUX_POWER_W / vo)
            ii = vo*io/(vin*AUX_ETA)
            duty = (vo+0.56)/(vin+vo+0.56)
            # Equal, strongly coupled SEPIC windings: ripple per winding
            # is Vin*D/(2*L*f). Evaluate L -20% and frequency -15%.
            ripple = vin*duty/(2*AUX_L_MIN*AUX_FSW*0.85)
            peak = ii+io+ripple
            if peak >= 6.5:
                problems.append(f'AUX {vin:g}->{vo:g} V: peak {peak:.2f} A >= 6.5 A')
            if math.hypot(ii, ripple/math.sqrt(12)) >= 5:
                problems.append(f'AUX {vin:g}->{vo:g} V: input winding exceeds 5 A RMS')
            if 1.3*(ii+io+ripple) >= 15:
                problems.append('AUX saturation margin below 30%')
            if vin+vo+0.56 >= 48:
                problems.append(f'AUX {vin:g}->{vo:g} V exceeds 48 V SW operating ceiling')
    return problems, iin

def table():
    head = '| AUX output | ' + ' | '.join(f'VSYS={v} V' for v in AUX_VSYS) + ' |'
    sep = '|---|' + '|'.join('---:' for _ in AUX_VSYS) + '|'
    rows = [head, sep]
    for vo in AUX_VOUTS:
        rows.append(f'| {vo} V | ' + ' | '.join(f'{aux_current(vo,vi):.2f} A' for vi in AUX_VSYS) + ' |')
    return '\n'.join(rows)

def report(iin):
    regs = '\n'.join(
        f'| `{r}` | `{p}` | {src} | {out} | {lo:g}–{hi:g} V | '
        f'{("12 W" if cap is None else f"{cap:g} A")} |'
        for r, p, src, out, lo, hi, cap in REGULATORS)
    return f'''# Odin power budget

**Generated by `tools/budget.py`. Do not hand-edit.**

## Input envelope

USB-C can start at 4.75 V. The SS34 plus USB eFuse model loses
{V_OR_DROP:.2f} V at 0.6 A, leaving **{VSYS_MIN:.2f} V**. The screw input is
**9–21 V DC**. U11/U12 are AP63300 devices (3.8–32 V operating); U28 is an
LM5157 (2.9–45 V operating), so all three cover the full VSYS envelope.

The VIN clamp is SMBJ22A: 22 V standoff and 35.5 V maximum rated pulse clamp.
The AP63300's 40 V/400 ms transient limit is the lowest transient limit after
D4. VSYS capacitors are 50 V X7R.

## Regulator ratings

| Ref | Part | Source | Output | Input rating | Output class |
|---|---|---|---|---|---:|
{regs}

## AUX output-current derating

These are **calculated planning allocations, not measured current ratings**.
The converter target is 1 A / 12 W, with {AUX_ETA:.0%} assumed efficiency.
The 5/9 V columns reserve {BASE_RESERVE_W:g} W for the base board and use a
{USB_VSYS_LIMIT:.2f} A VSYS allocation below U26's 2.03 A typical limit.
The 12/19 V columns assume J50 and a 3 A source/path. Extension loads on
other rails consume the same source budget and reduce these numbers.

{table()}

A default 5 V / 0.9 A host cannot supply the 8 W board reservation: its
full-board AUX allocation is zero. A reduced-load configuration needs a
separate budget. Real 5 V USB produces VSYS below 5 V after OR-ing; therefore
the 5 V column is already optimistic for a nominal 5 V adapter. Advertising
3 A does not bypass U26's limit. [verify] startup and all operating corners.

The magnetics/switch check independently sizes the converter for 12 W at
24 V from a dedicated 5 V VSYS source: {iin:.2f} A input. It includes -20%
inductance, -15% switching frequency, both winding currents and ripple.
R132=49.9k programs approximately {AUX_FSW/1000:.0f} kHz. A 2.1 MHz setup
cannot guarantee the required duty ratio at low input. Compensation,
DC-biased capacitance, DCM behavior, efficiency and thermal rise still need
prototype validation; these calculations do not constitute a measured rating.

## Base-board load model retained

The per-load estimates are retained in `LOADS`; cascaded 90%-efficient
conversion gives {board_loads()['+5V']:.3f} A on +5V and
{board_loads()['+3V3']:.3f} A on +3V3 before connector exports. Both SFP
modules are included. FPGA values are planning estimates pending AMD XPE.
The two VCCIO domains and the separate 3V3 export share U12's 3 A ceiling;
their maximum switch-limit tolerances are not additive guaranteed allowances.

## Release hold: surge and layout

The DC input envelope passes, but SMBJ22A's 35.5 V surge clamp plus a charged
24 V SEPIC output can exceed the LM5157 SW pin's 50 V absolute maximum.
The ADC divider is sized for 21 V DC, not that surge. Surge protection is
**not qualified**; do not claim the complete input protection passes or
manufacture without resolving this. The 3 A source header/shunt also limits
RAW current even though AUX_RAIL's copper class targets 5 A.

## Extension limits

`AUX_RAIL` is a 5 A routing class, but source capacity remains the table above.
Each of ten AUX branches has its own 33 V, 1.1 A-hold PTC. The other per-zone
PTCs remain 500 mA PINV, 300 mA 3V3, and 500 mA 5V. These are fault isolation,
not additive current allocations: a converter overload droops the shared rail;
a branch short heats and opens that branch PTC.
'''

def main():
    problems, iin = analyse()
    print(f'VSYS envelope: {VSYS_MIN:.2f}..{VSYS_MAX:.2f} V')
    print(f'LM5157 minimum operating input: 2.90 V -> {"PASS" if VSYS_MIN >= 2.9 else "FAIL"}')
    print(f'AUX 12 W at 5 V, 85% efficiency: {iin:.2f} A input')
    print(table())
    if problems:
        print('PROBLEMS')
        for p in problems: print(' -', p)
    if '--write' in sys.argv:
        open('ref/power-budget.md', 'w').write(report(iin))
        print('wrote ref/power-budget.md')
    return 1 if problems else 0

if __name__ == '__main__':
    sys.exit(main())
