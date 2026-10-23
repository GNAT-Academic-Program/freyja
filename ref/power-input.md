# Powering Odin

The current hardware manual is [power.md](power.md). It supersedes the old
fixed-12 V boost/selector architecture formerly described here.

USB-C accepts 5 V fallback and requests at most 9 V PD. J50 accepts 9-21 V
DC. They feed VSYS through D3/D4; U26 limits the USB-to-VSYS path to about
2.03 A typical and provides automatic inrush limiting, OVLO and reverse
blocking. U11 and U12 are AP63300 devices. On a plain 5 V source the supervisor
must keep U11 disabled and use Q2's +5V bypass; Q2 must stay off at 9 V.

J68 AUX IN is a separate 9-28 V raw input, only to J66's RAW side. It does
not power the supervisor or negotiate anything. The regulated alternative is
an LM5157 SEPIC from VSYS, with 9/12/15/24 V selected by J67 and no cap = off.
There are no per-zone AUX selectors, +12V/+12V_EXT nets, U19 boost or U25.

U21-U24 still protect the low-voltage connector supplies under EXT_EN and
report EXT_FAULT. AUX has branch PTCs but no equivalent active reverse
blocking. Never drive external voltage back into a connector power pin.

The base-board load estimates and source-aware AUX current table are in
[power-budget.md](power-budget.md). Plain 0.9 A USB cannot run the published
full-load board plus AUX; reduced-load operation needs hardware verification.
Neither 3 A advertisement nor PD implies that every extension can draw its
individual fuse rating simultaneously.

**Not fabrication-ready:** the full VIN surge-protection requirement is
unresolved, and placement/routing and converter validation remain pending.
The complete input-component audit and release holds are in [power.md](power.md).
