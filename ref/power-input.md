# Powering Odin

The current hardware manual is [power.md](power.md). It supersedes the old
fixed-12 V boost/selector architecture formerly described here.

USB-C accepts 5 V fallback and requests at most 9 V PD. J50 accepts 9-21 V
DC. They feed VSYS through D3/D4; U26 limits the USB-to-VSYS path to about
2.03 A typical and provides automatic inrush limiting, OVLO and reverse
blocking. U11 and U12 are AP63300 devices. On a plain 5 V source the supervisor
must keep U11 disabled and use Q2's +5V bypass; Q2 must stay off at 9 V.

J68 AUX IN is a separate 9-28 V raw input feeding `AUX_RAIL` and the ten
slot AUX branch PTCs, nothing else. It does not power the supervisor or
negotiate anything. Rev A has no on-board AUX converter: the LM5157 SEPIC
and its selectors were removed. There are no per-zone AUX selectors,
+12V/+12V_EXT nets, U19 boost or U25.

U21-U24 still protect the low-voltage connector supplies under EXT_EN and
report EXT_FAULT. AUX has branch PTCs but no equivalent active reverse
blocking. Never drive external voltage back into a connector power pin.

The base-board load estimates are in [power-budget.md](power-budget.md).
Neither 3 A advertisement nor PD implies that every extension can draw its
individual fuse rating simultaneously; AUX capacity is whatever is wired to
J68.

**Not fabrication-ready:** placement and routing remain pending. The complete
input-component audit and release holds are in [power.md](power.md).
