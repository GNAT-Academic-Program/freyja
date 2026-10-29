#!/usr/bin/env python3
"""Executable power limits and the generated Odin power-budget report."""
import sys

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
    # ---- +1V8_IO: U14's output. VCCAUX/VCCADC hang off it as +1V8 through
    # a bead; bank 13 and the 1.8 V memory are on the node itself.
    ('+1V8_IO', 'XC7A100T VCCAUX and VCCADC (+1V8, through FB1)', 0.18, 'estimate',
     'pre-bitstream planning allowance; replace with an AMD XPE result'),
    ('+1V8_IO', 'FPGA bank 13 VCCO and its I/O', 0.10, 'estimate',
     'one third of the 1.0 W VCCO/IO line, as for bank 14'),
    ('+1V8_IO', 'PSRAM x4 APS6404L-SQN-SN, all reading', 0.028, 'datasheet',
     'APS6404L-SQN datasheet rev 4.0 Table 9 (p. 26): ICC read/write 7 mA '
     'max per chip, output load not included'),
    ('+1V8_IO', 'U9/U10 VCCA, quiescent', 0.0001, 'datasheet',
     'SN74LXC8T245 SCES916A section 6.5: ICCA 4 uA max per device; '
     'switching current is counted in the bank 13 line'),
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
    ('+3V3', 'RTL8211FD-CG, 1000Base-T link', 0.20, 'estimate',
     'datasheet rev 1.7 gives no active-mode consumption table; planning '
     'allowance for a 1 Gb PHY with internal LDO, verify on the prototype'),
    ('+3V3', 'ETH jack LEDs x2 through 510 ohm', 0.006, 'datasheet',
     'RTL8211F Figure 5; about 3 mA each'),
    ('+3V3', 'X4 50 MHz CMOS oscillator', 0.01, 'estimate',
     'typical 3225 CMOS oscillator at 50 MHz into a 15 pF load'),
    ('+3V3', 'Heartbeat and user LEDs x3, all on', 0.005, 'estimate',
     'D9-D11 via 1k each; 5 mA budget allowance'),
    ('+3V3', 'U9/U10 VCCA, U20, pull-ups, LED', 0.03, 'estimate',
     'quiescent logic'),
    ('+3V3', 'FPGA bank 15 VCCO, worst case jumpered to 3.3V', 0.10, 'estimate',
     'bank load only; connector export is checked from switch maximum below'),
    ('+3V3', 'FPGA bank 34 VCCO, worst case jumpered to 3.3V', 0.10, 'estimate',
     'bank load only; connector export is checked from switch maximum below'),
    ('+3V3', 'FPGA banks 13/35 VCCO and bank 0', 0.06, 'estimate',
     'bank 13 carries the two 5V buses; 35 drives HDMI (TMDS_33 current '
     'comes from the monitor\'s 3.3 V pull-ups, not from VCCO)'),
    ('+3V3', 'U31 TPD12S016 VCCA, level shifters on', 0.001, 'datasheet',
     'SLLSE96F 8.2.2: about 200 uA fully on'),
    # ---- +2V5: bank 16 I/O and the PHY RGMII pads
    ('+2V5', 'FPGA bank 16 VCCO: RGMII and eight LVDS_25 pairs', 0.12, 'estimate',
     'LVDS_25 drivers about 3.5 mA each plus RGMII switching; replace with XPE'),
    ('+2V5', 'RTL8211FD-CG DVDD_RG (RGMII pads)', 0.02, 'estimate',
     'external 2.5 V I/O supply, CFG_EXT=1 CFG_LDO=01'),
    # ---- +1V1, the supervisor's core, off the RP2350's own regulator
    ('+1V1', 'RP2350B core (DVDD)', 0.06, 'estimate',
     'RP2350 at 150 MHz; the on-chip regulator is rated 200 mA'),
    # ---- +5V
    ('+5V', 'U9/U10 VCCB', 0.02, 'estimate', 'quiescent translator supply'),
    ('+5V', 'HDMI 5 V to the monitor through U31', 0.055, 'datasheet',
     'TPD12S016 5V_OUT current limit, SLLSE96F'),
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

def board_loads():
    own = {rail: sum(amps for r, _, amps, _, _ in LOADS if r == rail)
           for rail in ('+5V', '+3V3', '+2V5', '+1V8_IO', '+1V0', '+1V1', '+1V2_MGT')}
    own['+5V'] += sum(own[r]*v/(4.7*0.90) for r,v in
                     (('+2V5',2.5),('+1V8_IO',1.8),('+1V0',1),('+1V2_MGT',1.2)))
    own['+3V3'] += own['+1V1']*1.1/(3.3*0.90)
    return own

def analyse():
    problems = []
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
    regs = '\n'.join(
        f'| `{r}` | `{p}` | {src} | {out} | {lo:g}–{hi:g} V | {cap:g} A |'
        for r, p, src, out, lo, hi, cap in REGULATORS)
    loads = board_loads()
    totals = '\n'.join(
        f'| `{r}` | {out} | {loads[out]:.3f} A | {cap:g} A | {100*loads[out]/cap:.0f} % |'
        for r, _p, _src, out, _lo, _hi, cap in REGULATORS)
    lines = '\n'.join(
        f'| {rail} | {what} | {amps:.3f} A | {kind} | {note} |'
        for rail, what, amps, kind, note in LOADS)
    return f'''# Odin power budget

**Generated by `tools/budget.py`. Do not hand-edit.**

## Input envelope

USB-C can start at 4.75 V. The SS34 plus USB eFuse model loses
{V_OR_DROP:.2f} V at 0.6 A, leaving **{VSYS_MIN:.2f} V**. The screw input is
**9–21 V DC**. U11/U12 are AP63300 devices (3.8–32 V operating) and cover
the full VSYS envelope.

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

| Ref | Output | Board load | Rating | Used |
|---|---|---:|---:|---:|
{totals}

| Rail | Load | Current | Basis | Note |
|---|---|---:|---|---|
{lines}

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
