# Powering Odin

The current hardware manual is [power.md](power.md). It supersedes the old
fixed-12 V boost/selector architecture formerly described here.

USB-C accepts 5 V fallback and requests at most 9 V PD. J50 accepts 9-21 V
DC. They feed VSYS through D3/D4; U26 limits the USB-to-VSYS path to about
2.03 A typical and provides automatic inrush limiting, OVLO and reverse
blocking. U11 and U12 are AP63300 devices with no enable: +3V3, +5V and the
1.8 V rail are present whenever the board has power. On a plain 5 V source
U34 (TPS2121) passes VBUS to the +5V rail directly. The rail is handed to
U11 by intent, not by a voltage threshold (findings items 52, 53): Q6 holds
the mux on U11 while the controller asks for 9 V and for 2-7 s after it
stops asking, so the rail leaves VBUS before the charger moves it and
returns only once VBUS is back at 5 V; Q7 holds it on U11 while J50 carries
voltage, so a connected bench supply carries the whole board even with a
5 V USB cable attached (before, the USB port kept the 5 V load). OV1 at
5.3-5.9 V is only a backstop against a source that raises VBUS unasked.
During a negotiation the rail is U11 in dropout, about 4.5 V, which every
+5V consumer accepts; firmware asks for 9 V before it enables extension
power. Both of U34's inputs block reverse current and it limits the rail to
about 2.5 A. The CH224K asks for 5 V by default and its CFG pins cannot
form any request above 9 V.

What the controller can know about the source (item 55): PD_PG says the
9 V request was granted (a 15 W guarantee under the PD power rules),
VBUS5_ST says which input feeds +5V, MON_VSYS says J50 is present. A 5 V
Type-C advertisement is not readable (the CC lines go only to the CH224K,
which has no data interface), so any 5 V source is planned as a 500 mA
port unless the user has stored a declaration; see
[power-budget.md](power-budget.md).

J68 AUX IN is a separate 9-28 V raw input feeding `AUX_RAIL` and the ten
slot AUX branch PTCs, nothing else. It does not power the supervisor or
negotiate anything. Rev A has no on-board AUX converter: the LM5157 SEPIC
and its selectors were removed. There are no per-zone AUX selectors,
+12V/+12V_EXT nets, U19 boost or U25.

U21-U24 still protect the low-voltage connector supplies under EXT_EN;
U21/U22 (TPS22950C) limit current and report EXT_FAULT, U23/U24 (TPS22953,
biased from +3V3 so the 1.8 V setting is inside their rating, PG tied to
ground as the datasheet asks of an unused PG) block reverse current while
off, report nothing, and leave the overload limit to the 500 mA slot fuses;
they restart by themselves after an output undervoltage, which the bench
must see with a shorted branch (item 56). AUX
has branch PTCs but no equivalent active reverse blocking. Never drive
external voltage back into a connector power pin.

The base-board load estimates are in [power-budget.md](power-budget.md).
Neither 3 A advertisement nor PD implies that every extension can draw its
individual fuse rating simultaneously; AUX capacity is whatever is wired to
J68.

**Not fabrication-ready:** placement and routing remain pending. The complete
input-component audit and release holds are in [power.md](power.md).
