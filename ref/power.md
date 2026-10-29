# Odin power inputs and the AUX pass-through

**Prototype update, not fabrication approval.** See release holds below.

| Input | Allowed operating range | Destination |
|---|---|---|
| USB-C | 5 V by default; 9 V PD on the controller's request, nothing higher | base board through VSYS; plain 5 V also straight to the +5V rail through U34, except while the controller asks for 9 V or J50 is powered (then U11) |
| J50 VIN | 9-21 V DC | base board through D4 to VSYS |
| J68 AUX IN | 9-28 V DC, correct polarity | `AUX_RAIL` and the ten slot AUX branch PTCs only; no base-board supply |

USB and J50 are diode-ORed into VSYS; a powered J50 also moves the +5V
rail onto U11 (U34, Q7), so with both connected the whole board runs from
J50. USB must never negotiate above 9 V.

## AUX in rev A

There is **no on-board AUX converter**. The LM5157 SEPIC (U28, L10, D12),
its 9/12/15/24 V cap-selected feedback ladder (J67, U29, Q5-Q8, D13-D16) and
the REG/AUX/RAW source selector J66 were removed before rev A: the SMBJ22A
input clamp (35.5 V rated pulse clamp) on top of a charged 24 V output could
exceed the LM5157 SW pin's 50 V absolute maximum, and the converter was not
needed for a board that configures and runs. The connector pinout is
unchanged: pin 7 of every power row is still that slot's AUX pin.

J68 is **AUX IN 9-28V UNREGULATED, YOUR RAIL, YOUR PROBLEM**. Its + terminal
is `AUX_RAIL`; the only other parts on that net are the ten C70150 branch
PTCs (33 V, **1.1 A hold / 2.2 A trip at 25 C**, a disclosed deviation from
exactly 1 A hold; hold current falls with temperature). Nothing on the base
board regulates, measures, switches or draws from this rail. EXT_EN does not
control it. Change the external supply with the board unpowered.

## Shared and branch limits

`AUX_RAIL` has a **5 A copper design target**; source capacity is the external
supply on J68. The KF301 terminal is rated well above that. A short heats and
trips the branch PTC; an aggregate overload is the external supply's problem
and droops the shared rail. Existing branch fuses remain PIN V 500 mA, 3V3
300 mA, 5V 500 mA. U21/U22 limit and report; U23/U24 (TPS22953) block
reverse current while off and rely on the PINV fuses for overload. AUX has no
active reverse blocking. Do not backfeed any connector power pin. The input
envelope per source profile and operating mode is in
[power-budget.md](power-budget.md): a plain USB 2.0 port carries the
controller alone, full extension export needs J50.

## VIN and VSYS component audit

The generated netlist has only J50, D8 and D4 directly on VIN_EXT.
VSYS additionally reaches exactly the parts listed below.

| Parts / node | Continuous 21 V assessment |
|---|---|
| J50 / VIN_EXT | KF301 terminal, 250 V component rating |
| D8 / VIN_EXT | SMBJ22A, 22 V standoff; 35.5 V rated pulse clamp |
| D4 / VIN_EXT and VSYS; D3 / VSYS | SS34, 40 V reverse rating; 3 A path class |
| U11/U12 / VSYS | AP63300WU-7, 3.8-32 V operating; 35 V DC absolute maximum, 40 V/400 ms transient |
| C185/C186/C192 / VSYS | explicitly 50 V rated |
| R81 / VSYS | 100k/16k monitor divider: 2.90 V at ADC for 21 V input; resistor dissipation below 4 mW |

U19's only output consumer was U25; U25 supplied the ten old per-zone AUX
selectors. U19/U25 and their dedicated passives are removed. No +12V,
+12V_EXT, AUX_REG or AUX_RAW net remains.

## Release holds

- The SMBJ22A clamp versus the AP63300 40 V/400 ms transient limit is the
  input protection claim. With the SEPIC gone no switching node adds a stored
  output to the clamp voltage, so the former LM5157 SW surge hold is closed.
  The ADC divider protects the 21 V DC case, not the surge.
- C70150 is 1.1 A hold, not the exact requested 1 A hold; do not hide this
  behind a "1 A" label.
- J68 placement and screwdriver access are the owner's hand placement in
  phase B; see `ref/extension-ux.md` for the keep-out table.

Detailed arithmetic: [power-budget.md](power-budget.md).
