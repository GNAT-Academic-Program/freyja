# Odin power inputs and AUX lab rail

**Prototype update, not fabrication approval.** See release holds below.

| Input | Allowed operating range | Destination |
|---|---|---|
| USB-C | 5 V fallback; request at most 9 V PD | base board through VSYS; 5 V bypass via Q2 |
| J50 VIN | 9-21 V DC | base board through D4 to VSYS |
| J68 AUX IN | 9-28 V DC, correct polarity | only J66 RAW and ground; no base-board supply |

USB and J50 are diode-ORed. The AUX LM5157 SEPIC is fed from **VSYS**,
not VIN_EXT or +5V. Its 2.9 V operating floor covers the 4.27 V weak-USB
planning case (4.75 V minus 0.48 V OR/eFuse loss at 0.6 A); loss at heavier
load must be checked separately. USB must never negotiate above 9 V.

## Jumpers

J67 is one straight, unshrouded 2x4 header, C124386 / B-2100S08P-B110.
Its standard KiCad footprint is checked against the manufacturer drawing;
it does not depend on the rejected right-angle C9139 import.

| J67 cap across pins | Selected output |
|---|---:|
| 1-2 | 9 V (nominal ladder setting 9.06 V) |
| 3-4 | 12 V (12.07 V) |
| 5-6 | 15 V (15.08 V) |
| 7-8 | 24 V (24.17 V) |

**One cap only. Ships with no cap: converter disabled.**
The cap grounds a detect input; U29 drives the corresponding Q5-Q8 feedback
tap switch and diode-OR enable. The ordered series feedback ladder means
simultaneous selections short intervening segments and select the lowest
requested voltage. No firmware or I2C state selects this rail. Change jumpers
with power removed; the output capacitors may remain charged after disabling.

J66 has three pins: **1 REG / 2 AUX / 3 RAW**. Fit one cap on 1-2 for
regulated output or 2-3 for AUX IN. A single standard cap cannot bridge both
sources. J68 is **UNREGULATED 9-28V, YOUR RAIL, YOUR PROBLEM**.
Neither voltage selection nor EXT_EN controls the RAW input.
J19/J20 remain the independent VCCIO selectors; old J10-J18/J21 are gone.

## Output-current allocation

Calculated planning maxima, **not measured ratings**. The 5/9 V VSYS columns
assume the USB path with 1.70 A allocated below U26's 2.03 A typical limit;
12/19 V assume a 3 A screw source. Reserve 8 W for the base board, assume
85% AUX efficiency, and cap the converter target at 1 A / 12 W.
Other extension loads reduce these allocations.

| AUX output | VSYS=5 V | VSYS=9 V | VSYS=12 V | VSYS=19 V |
|---|---:|---:|---:|---:|
| 9 V | 0.04 A | 0.68 A | 1.00 A | 1.00 A |
| 12 V | 0.03 A | 0.51 A | 1.00 A | 1.00 A |
| 15 V | 0.02 A | 0.41 A | 0.80 A | 0.80 A |
| 24 V | 0.01 A | 0.25 A | 0.50 A | 0.50 A |

The 5 V column means **5 V at VSYS**, not a nominal 5 V adapter before
OR-ing loss. A default 0.9 A USB host cannot supply the 8 W reservation:
its full-board AUX allocation is zero. Reduced FPGA/SFP loading needs a
separate budget. A 3 A USB advertisement does not remove U26's current limit.

**[verify] 5 V-only USB:** test startup, negotiated/source current, reduced-load
behavior, duty-cycle margin, voltage regulation, compensation, temperature
and shutdown. The magnetics/switch are sized for a separate 12 W / 24 V
test from a dedicated 5 V VSYS supply (about 2.82 A input at 85%), but
Odin's USB input path cannot deliver that corner with the board running.

## Shared and branch limits

AUX_RAIL has a **5 A copper design target**, not 5 A source capacity.
J66's selected header is rated 3 A; the fitted shunt may limit it further.
Do not run 5 A RAW through it. Each AUX branch has C70150, 33 V and
**1.1 A hold / 2.2 A trip at 25 C**, a disclosed deviation from exactly
1 A hold. PTC hold current falls with temperature. Existing branch fuses
remain PIN V 500 mA, 3V3 300 mA, 5V 500 mA.

A short heats/trips the branch PTC; aggregate overload may first collapse
the shared converter or trip its hiccup/thermal protection. RAW overload
behavior depends on the external supply. U21-U24 protect the low-voltage
exports; no active U25 reverse blocking remains on AUX. Do not backfeed it.

## VIN and VSYS component audit

The generated netlist has only J50, D8 and D4 directly on VIN_EXT.
VSYS additionally reaches exactly the parts listed below.

| Parts / node | Continuous 21 V assessment |
|---|---|
| J50 / VIN_EXT | KF301 terminal, 250 V component rating |
| D8 / VIN_EXT | SMBJ22A, 22 V standoff; 35.5 V rated pulse clamp |
| D4 / VIN_EXT and VSYS; D3 / VSYS | SS34, 40 V reverse rating; 3 A path class |
| U11/U12 / VSYS | AP63300WU-7, 3.8-32 V operating; 35 V DC absolute maximum, 40 V/400 ms transient |
| U28 BIAS / VSYS | LM5157, 2.9-45 V operating, 50 V absolute maximum |
| C185/C186/C192/C233/C234/C235 / VSYS | explicitly 50 V rated |
| L10 pin 1 / VSYS | 4.7 uH coupled, 5 A thermal / 15 A saturation; winding stress checked in budget |
| R81 / VSYS | 100k/16k monitor divider: 2.90 V at ADC for 21 V input; resistor dissipation below 4 mW |

U19's only output consumer was U25; U25 supplied the ten now-deleted
AUX selectors. U19/U25 and their dedicated passives are removed. No
+12V or +12V_EXT net remains. AUX_REG reaches the source selector REG
side, not the RAW terminal.

## Release holds

- **Surge qualification fails the complete-system requirement:** a 35.5 V
  input clamp combined with a charged 24 V SEPIC output can exceed the
  LM5157 SW pin's 50 V absolute maximum. The ADC divider likewise protects
  the 21 V DC case, not that surge. Resolve protection before manufacturing.
- C70150 is 1.1 A hold, not the exact requested 1 A hold; do not hide this
  behind a “1 A” label.
- The converter is electrically generated, not thermally or dynamically
  validated. Verify all four output settings, multi-cap fail-low behavior,
  no-cap shutdown, capacitor DC bias, loop stability and input transients.
- Preserve the LM5157 exposed-pad thermal via field, short switching loops
  and local bypass placement during human layout. Existing hand placement
  was not changed and routing DRC is not clean.

Detailed arithmetic: [power-budget.md](power-budget.md).
