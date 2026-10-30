# Powering Odin

The current hardware manual is [power.md](power.md). It supersedes the old
fixed-12 V boost/selector architecture formerly described here.

USB-C accepts 5 V fallback and requests at most 9 V PD. J50 accepts 9-21 V
DC. They feed VSYS through D3/D4; U26 (TI TPS25942A since 2026-10-30) limits
the USB-to-VSYS path to about 2.0 A typical and provides automatic inrush
limiting (1.2 V/ms), undervoltage lockout at 3.7 V, overvoltage cut-off at
10 V and reverse blocking. Its absolute maximum is 20 V, so the VBUS TVS D7 is
an SMBJ12A, 19.9 V clamp at full surge, 12 V standoff above the 9 V contract. U11 and U12 are LMR33630 devices with EN tied to VIN: +3V3, +5V and the
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
about 2.5 A. The PD sink is a Hynetek HUSB238 (since 2026-10-30, the CH224K
being out of the JLCPCB library): its strap resistors ask for 5 V at 1.5 A
on their own, and the controller asks for 9 V over I2C1 (address 0x08).
That I2C path can select any PDO the charger offers, so the 9 V ceiling is
firmware's to keep, not the pins': U26 opens above 10.07 V and D7 (SMBJ12A,
13.3-14.7 V breakdown) avalanches on a 12 V or higher contract, backstops,
not a design.

What the controller can know about the source (item 55): the HUSB238's
PD_STATUS0 says what contract was granted (9 V is a 15 W guarantee under
the PD power rules), PD_STATUS1 what a plain Type-C source advertises at
5 V (default, 1.5 A, 2.4 A or 3 A), VBUS5_ST says which input feeds +5V,
MON_VSYS says J50 is present. The 5 V advertisement is readable now; the
budget still plans any 5 V source as a 500 mA port unless the user has
stored a declaration, until that policy is revisited; see
[power-budget.md](power-budget.md).

J68 AUX IN is a separate 9-28 V raw input feeding `AUX_RAIL` and the ten
slot AUX branch PTCs, nothing else. It does not power the supervisor or
negotiate anything. Rev A has no on-board AUX converter: the LM5157 SEPIC
and its selectors were removed. There are no per-zone AUX selectors,
+12V/+12V_EXT nets, U19 boost or U25.

U21-U24 still protect the low-voltage connector supplies under EXT_EN;
U21/U22 (TPS22950C) limit current and report EXT_FAULT; U23/U24 (TPS22975
since 2026-10-30, biased from +3V3 so the 1.8 V setting is inside their
rating) have no PG, no reverse current blocking and no current limit of
their own: EXT_FAULT reflects U21, U22 and U26 only, the 500 mA slot fuses
are the PIN V overload limit, and while EXT_EN is low the switch discharges
its output through 230 ohm but a voltage forced onto a PIN V pin reaches the
domain through the switch's body diode. Neither PIN V nor AUX has active
reverse blocking. Never drive external voltage back into a connector power
pin.

The base-board load estimates are in [power-budget.md](power-budget.md).
Neither 3 A advertisement nor PD implies that every extension can draw its
individual fuse rating simultaneously; AUX capacity is whatever is wired to
J68.

**Not fabrication-ready:** placement and routing remain pending. The complete
input-component audit and release holds are in [power.md](power.md).
