# Odin — findings

Two eras are recorded here. **Items 1–4 are historical** — they describe the
EasyEDA/Altium input set and are closed: the design now lives in `kicad/`,
generated from `tools/`, and those inputs are reference material only. **Items
5 onward are live**, against the current KiCad design.

Regenerate everything with the commands in `kicad/README.md`.

---

# Part I — historical (EasyEDA era, closed)

*Kept for the reasoning, not as open work. The netlist/BOM/pcbdoc revision
mismatch that these describe is moot now that the design is generated.*


## 1. BLOCKER — the netlist, BOM and pcbdoc are the *previous* revision

**Entities:** `Netlist_Odin_0_2026-09-02.net`,
`BOM_Odin_V1.0.0_Odin_0_2026-09-02.xlsx`, `Odin_V1.0.0/Odin_0.pcbdoc`
versus `Odin_V1.0.0/Odin/*.schdoc`.

**What is wrong.** The netlist and BOM agree with each other exactly (0
designators netlist-only, 0 BOM-only) and both agree with the pcbdoc. All
three describe a **single-FPGA ECP5 board programmed over an FT232H**. The
schdoc export describes a **different, later board**: Artix-7 + ECP5 + RP2040
with a new power tree. Only 9 of 40 schdoc part types appear in the netlist
(`odin.srcdiff`).

Present in the schdocs, absent from netlist/BOM/pcbdoc:

| Part | Schdoc symbols | Role |
|---|---|---|
| `XC7A50T-2CSG325I` | 8 | the Artix-7 that Goals 1–2 are about |
| `RP2040_C2040` | 1 | the supervisor that Goal 1 is about |
| `W25Q32JVZPIQ` | 1 | RP2040 boot flash |
| `TPS563257DRLR` | 6 | new buck rails |
| `TPS55340RTER` | 1 | boost |
| `TPS25940ARVCR` | 1 | eFuse |
| `APS1604M-3SQR-SN` | 4 | PSRAM |
| `SN74LXCH8T245PWR` | 4 | level shifters |
| `ADS7950SBRGET` | 1 | ADC |
| `2.54-2*8P_`, `PM2.54-1X8PM-H85`, `ZX-PZ2.54-2-4PZZ`, `PH2.54-01-03PZD` | 6/4/4/4 | new extension headers |

Present in netlist/BOM/pcbdoc, absent from the schdocs: `FT232HQ-REEL`,
`IS61WV25616BLL-10BLI`, `FM25V02A-GTR`, `TLV62569DRLR` ×3, `TPS54202DDCR` ×4,
`TYPE-C-31-E-07`, `TYPE-C-31-M-12`, `PS-1049SVD-4PN`.

**Consequence for the prompt's ground rules.** The prompt makes the Protel
netlist the identity source and forbids citing schdoc refdes. That rule cannot
be satisfied: the netlist contains no Artix-7 and no RP2040, so there is no
real designator to cite for any part in Goal 1. Symbol matching bears this
out — 25 of 230 schdoc symbols map to a netlist part (`odin.desigmap`), and
the matches are confined to the 9 shared part types.

**Proposed change (EasyEDA).** Re-export both the Protel netlist and the BOM
from the schematic that contains the Artix-7 and RP2040 — the one exported to
`Odin_V1.0.0/Odin/`. In EasyEDA Pro the netlist is exported per board, and
`Odin_0` is the old board; the new schematic appears to have no board/PCB yet,
which is why its netlist was never produced. If the new schematic needs a PCB
created before a netlist can be exported, that is the prerequisite step.

---

## 2. BLOCKER — the ECP5 is still instantiated in the new schematic

**Entities:** `LFE5U-25F-6BG256C`, 9 symbol parts on `fpga.schdoc`.

**What is wrong.** You have confirmed the ECP5 is a mistake and the board is
meant to be dual Artix-7. It is not a stray symbol: in the *old* netlist the
same part is `U1` with **170 connected balls**, driven through an
`SN74CB3T3245PWR` level shifter on a `TOL_*` bus. Whatever of that carried
into the new schematic is real wiring, not a placement error, so removing it
is a schematic-scale edit rather than a symbol delete.

**Proposed change (EasyEDA).** Delete the `LFE5U-25F-6BG256C` symbol parts
from `fpga.schdoc` and replace with a second `XC7A50T-2CSG325I`. The second
Artix-7 needs its own config chain — flash, `PROG_B`/`INIT_B`/`DONE`, `M[2:0]`
strap, JTAG — which feeds directly into item 3.

**Blocked on item 1**: I cannot enumerate which nets the ECP5 currently holds
in the *new* schematic, only in the old one.

---

## 3. BLOCKER — RP2040 GPIO count cannot carry Goal 1; assume RP2350B

Per your decision, the review will be run against an **RP2350B (48 GPIO)** and
the swap reported as a blocker. The sizing that forces it, for a dual Artix-7
board with the supervisor scope in Goal 1:

| Function | GPIO |
|---|---|
| Config flash SPI (CS, CLK, MOSI, MISO), shared across both FPGAs | 4 |
| Second flash CS (one CS per FPGA, bus shared) | 1 |
| FPGA A config: `PROG_B`, `INIT_B`, `DONE`, `CCLK`, `DIN` | 5 |
| FPGA B config: same | 5 |
| `M[2:0]` ×2 — driven, not hard-strapped, to switch master-SPI vs slave-serial | 6 |
| FPGA JTAG (TCK/TMS/TDI/TDO), both parts daisy-chained on one port | 4 |
| Fabric sideband JTAG for NEORV32 debug | 4 |
| Sideband UART TX/RX | 2 |
| Spare GPIO bus | 4–8 |
| Regulator enables (8 rails: 6× buck, boost, eFuse) | 8 |
| Power-good readback | 8 |
| Extension board-ID | 2–4 |
| **Total** | **53–59** |

Against 30 on an RP2040 this overflows by roughly 2×; against 48 on an
RP2350B it still overflows unless something gives. The cheapest reductions
that keep the "direct wiring" philosophy:

- **Hard-strap `M[2:0]`** to master-SPI and reach slave-serial by holding
  `PROG_B` and driving `CCLK`/`DIN` only — saves 6, and `M[2:0]` is a
  build-time choice, not a runtime one.
- **Share one JTAG port** across both Artix-7s via the standard daisy chain —
  already assumed above, saves 4.
- **Power-good as a single wired-OR fault line** plus per-rail readback over
  the ADC already on the board (`ADS7950SBRGET`, 12-bit 16-ch) — saves 7,
  and rail voltage readback is strictly better information than a PG bit.

With those three, the count lands near **40**, which fits a RP2350B with
headroom for the spare bus. This is a proposal, not a verified finding —
confirming it needs item 1.

---

## 4. Extension connector keying — the 16-pin unit reads as 14 + 2

You asked me to work out the pattern. From the old netlist, where the
connectors are fully wired, one group is:

- `J4` `2.54-2*7P母` — 2×7 female, **14 pins**
- `H5` `3-644456-2` — 2×1, **2 pins**
- `P3` `2.54-1*1P针` — 1×1 male post, **1 pin**

14 + 2 = **16 pins = 8 columns × 2 rows**, with the 1×1 post as the
polarizing key. There are 8 of each (`J4–J11`, `H5–H12`, `P3–P10`), so the old
board carries **8 × 16 = 128 positions**, i.e. two 64-pin extension sites of
four 16-pin patterns each — which is the 16/32/64 prefix rule you described,
and the split into a 7-column block plus a 1-column block is what makes the
mating polarity unambiguous.

Two cautions. First, this is the **old** board; the new schdocs carry a
different connector mix (`2.54-2*8P_` ×6, `PM2.54-1X8PM-H85` ×4,
`ZX-PZ2.54-2-4PZZ` ×4, `PH2.54-01-03PZD` ×4 alongside the 8× `2.54-2*7P_` and
8× `3-644456-2`), so the new pattern is not yet 14+2. Second, your arithmetic
"8+7+1" counts *columns* and reaches 16 columns (a 2×8 block + a 2×7 block + a
key), which matches the new schdoc's part mix rather than the old board's. If
16 **columns** (32 pins) is the intended unit, then a 64-**column** extension
is 128 pins, and the new mix is the right one. Which of the two — 16 pins or
16 columns — is the unit needs to be your call; item 1 has to land first
either way, since `ref/extension-pinout.md` needs real designators and FPGA
bank data.

---

## Steps not yet run

| Step | Status |
|---|---|
| 0 setup | done — baseline commits, `ref/adabmp` cloned, `extract.py` read |
| 1 netlist-first IR | tooling done; output is of the wrong revision (item 1) |
| 2 FPGA datasheet facts | not started — blocked on the Artix-7 count (item 2) |
| 3 power review | not started — the new power tree is in no netlist |
| 4 config/boot review | not started — no RP2040 in any netlist |
| 5 extension connector | not started — see item 4 |
| 6 Gameboy gap analysis | not started — depends on step 5 |
| 7 BOM check | partial — the BOM is self-consistent with the old netlist; every placed part has an LCSC number; see below |

**Step 7, valid only for the old revision.** Zero JLCPCB stock:
`TC211A106M016Y` (C128289, 10 parts) and `CA45-A6R3K226T` (C122912, 4 parts).
Near-zero: `RT1206FRE07120KL` (C136861, stock 9), `2NM27000C33YC` (C668764,
stock 3), `1SMA5918A` (C19077487, stock 71), `FT232HQ-REEL` (C82158, stock 28)
— the FT232H is being removed anyway. 51 of 56 BOM lines are Extended Part;
only `0603WAF8202T5E`, `0603WAF5101T5E`, `0603WAF200JT5E` are Basic. Most of
the Extended lines are ordinary 0402/0603 passives with Basic equivalents;
that consolidation pass is worth doing once the BOM is re-exported, not now.


---

---

# Part II — live, against the current KiCad design

## 5. FIXED — differential oscillator pinout confirmed

**Entities:** `X2`, `DSC1123CI2-125.0000` (`C617173`), footprint
`EasyEDA:OSC-SMD_6P-L3.2-W2.5-BL`.

The Microchip datasheet and imported part agree: 1 EN, 2 NC, 3 GND, 4 OUT+,
5 OUT-, 6 VDD. This differs from the old assumed mapping; the schematic now
uses the imported exact symbol and footprint.

## 6. FIXED — MGTRREF was connected to the wrong rail

**Entities:** `R35` (formerly `R30`), 100R 1% 0603, from `U1.A15`
(`MGTRREF_216`, FGG676) to `+1V2_MGT` (MGTAVTT).

The old circuit used 100R to GND with no explicit tolerance. The ground
connection was wrong. [UG482 v1.9, Figure 5-1 and pp. 217–219](https://0x04.net/~mwk/xidocs/ug/ug482_7Series_GTP_Transceivers.pdf#page=218)
specifies 100 ohm, 1% to MGTAVTT for Artix-7 GTP calibration, not 499/500 ohm
to GND. The design source, schematic, netlist and PCB now specify `100 1%`
and connect the resistor to the 1.2 V MGT supply. This closes the schematic
error; high-speed link performance still requires hardware validation.

## 7. FIXED — board outline now matches the mechanical contract

`kicad/odin.kicad_pcb` is now 100 x 100 mm, matching the required board size.
A–H use four continuous 2x16 signal bodies plus four parallel 1x16 power
bodies (two logical zones per body), plus two complete 5V-bus signal and power
connector pairs. Placement
and routing remain deliberately absent. The exact stack-through connector MPN
is still a mechanical purchasing choice; the schematic fixes 2.54 mm pitch.


## 8. FIXED — nonexistent extension board-ID promise removed

**Entities:** `ref/extension-ux.md`, the nine slot connectors, `PD_CFG1..3`.

An earlier `ref/extension-ux.md` stated that each module had board-ID pins so
the supervisor could tell what was plugged in. **It had none.** The four
`BOARDID_*` nets that existed went to the supervisor and a pull-down each and
reached no connector; they have since been repurposed for the USB-PD sink,
which genuinely needed them.

The options considered were:

1. **Give up one I/O per module** for a strapped ID pin.
2. **Drop the claim.** Extensions are identified by the human. Honest, and
   costs nothing but the feature.
3. **Widen the module** solely to add identification.

Option 2 was chosen. The claim and dead nets are gone. The newer third power
row is used for clear, well-grounded power distribution, not to silently
reintroduce an identification protocol. The supervisor still power-gates the
extension rails and reports SFP module identity.


## 9. FIXED — the supervisor could not enable its own power rail

`EN_3V3` was driven by supervisor GPIO21 and gated `U12`, which produced the
+3V3 that powers the supervisor. A deadlock: the board could never start.
`EN_5V` compounded it, since +3V3 was derived from +5V.

Fixed: +3V3 is now always on, from a wide-input `AP63300` (`U12`) straight off
`VSYS`. Its datasheet permits automatic startup with EN floating, so no GPIO
is involved. GPIO21 was freed and reused for the VBUS pass switch below.

## 10. FIXED — a Schottky from VBUS to the 5V rail was an overvoltage hazard

`D2` fed USB `VBUS` into the +5V rail so the board could run from a plain 5 V
source. The moment the PD sink negotiated 9 V, that diode would have put
~8.6 V onto a rail feeding four `TLV62569` regulators rated 5.5 V maximum —
destroying them on the first PD handshake.

Fixed: replaced with a supervisor-commanded high-side switch (`Q2` P-MOS,
`Q3` gate driver), **default open**. Firmware measures `VSYS` and only closes
it when the input really is 5 V.


## 11. CLOSED — level translator pinout confirmed

**Entities:** `U9`, `U10`, symbol `odin:SN74LXC8T245PW`.

The original `SN74AVC8T245PW` was wrong: the AVC family is specified for
1.2–3.6 V supplies and 5 V on `VCCB` exceeded its absolute maximum. It has been
replaced with `SN74LXC8T245PW` (1.1–5.5 V both rails).

KiCad ships no symbol for it, so the generated one is AVC8T245's symbol
renamed. That mapping has since been checked against TI's TSSOP-24 pinout for
`SN74LXC8T245PW` — 1 `VCCA`, 2 `DIR`, 3–10 `A1..A8`, 11–13 `GND`, 14–21
`B8..B1`, 22 `OE`, 23–24 `VCCB` — and matches. **Closed.**

## 12. FIXED — two complete 5V buses replace the 8+2 orphan

`SN74LXC8T245` is direction-controlled: one `DIR` pin steers eight signals
together. An earlier Slot L was an eight-bit bus plus an awkward two-bit tail,
costing 12 FPGA I/O for ten connector signals. A two-bit Nexperia converter
was briefly qualified for that tail, but optimizing the orphan did not fix the
interface. Odin now provides two identical complete eight-bit 5V buses, each
with one direction control. The second bus uses fixed bank 13.

`ref/extension-ux.md` now says this plainly. If per-pin bidirectional 5 V is
actually wanted, the part is a `TXB0108`-class auto-direction translator,
which trades away drive strength and forbids external pull-ups. There is no
option that gives strong drive, per-pin direction and 5 V at once.

## 13. partly fixed — qualify the placeholder components before layout

Inductor saturation current and capacitor voltage rating are not purchasing
details — a 22 µF 6.3 V part on the 12 V AUX rail fails immediately, and an
undersized inductor saturates under load. These need real part numbers
**before layout**, not before ordering, because package size affects
placement.

**Done since:**

- **A qualified-parts table exists and is enforced.** `tools/qualified.py`
  records MPN, manufacturer package code, footprint, the ratings that matter
  on this board, and how the pin map was confirmed, for every non-generic
  part. `tools/design.py` refuses to build if a part is missing from it or is
  fitted with a different footprint, so a new IC cannot enter the netlist
  anonymously. Rendered to `ref/qualified-parts.md`.
- **Every inductor is selected and checked.** `tools/budget.py` computes the
  ripple, peak current and required saturation current per rail and names the
  part: `SRN6045TA-100M` (10 µH, Isat 4.6 A) on `U11` and the boost,
  `SRN6045TA-4R7M` (4.7 µH, Isat 6.8 A) on `U12`, `SRN4018-2R2M`
  (2.2 µH, Isat 3.0 A) on the four `TLV62569`s,
  `SRN4018-1R0Y` on the MGT filter, and the mandated Abracon part on the
  supervisor. The tool fails if any of them saturates below its rail's
  requirement.
- **MOSFETs are real parts.** `Q1` and `Q2` are `DMG2305UX`; `Q3` is a
  `BSS138`. Reading the DMG2305UX datasheet is what turned up item 21.
- **Capacitors on rails above 3.3 V carry their rating in the value field**,
  set automatically from the net rather than typed: `25V` on `VSYS`, `VBUS`
  and `+12V`. Everything unmarked is 16 V minimum, X5R or better.

**Still open:**

- The SFP electrical connectors are selected; their separate metal cages are
  still not encoded because the `C5164658` mechanical import failed.
- The nine 300 mA +3.3 V polyfuses still need an exact MPN. The 200 mA and
  500 mA positions are selected.
- **Capacitor DC-bias derating is not accounted for.** A 22 µF 25 V X5R 0805
  at 12 V retains well under half its nominal value. The bulk capacitance is
  ample enough that this is unlikely to bite, but "22 µF" on the `VSYS` rail
  means perhaps 8 µF in circuit and nothing in the design says so yet.
- The ~340 ordinary passives can take LCSC numbers later via the JLCPCB
  plugin.

## 14. open — the 16/32/64 mechanical claim is unproven

Adjacent 16/32/64 module compatibility is a *mechanical* property: it depends
on slot pitch, board-edge geometry and the position of the keying posts, none
of which exist until placement. The electrical numbering supports it. Verify
it on the board, and until then treat the claim in `ref/extension-ux.md` as an
intent rather than a fact.


## 15. FIXED — the JTAG owner is now selected in hardware

`J2` sits directly in parallel with the FPGA's JTAG nets. The supervisor is
separated only by its 33 R series resistors, so an external programmer and a
misbehaving supervisor GPIO can both drive the same line. The comment claiming
a jumper isolates the supervisor was wrong and has been corrected.

Two ways to make it true:

1. **Firmware contract** (currently assumed): the supervisor tri-states
   GPIO0–3 whenever an external programmer may be attached, and does so as its
   *reset default*, not only when asked. Free, but it depends on firmware
   being correct — which is a poor guard for a debug path you reach for
   precisely when things are broken.
2. **A bus switch** (`SN74CB3T3245`, the part Odin_0 used) between the
   supervisor and the JTAG net, with its enable strapped or jumpered. Real
   isolation. Costs one part and one control line, and there is no spare
   supervisor GPIO — it would have to be a physical jumper.

Recommendation: option 2 with a jumper, because "hold the board in a known
state so I can debug it" should not itself depend on working firmware.

**Fixed with option 2.** `U20` is an `SN74CB3Q3384APW` 10-bit FET bus switch;
the supervisor's four JTAG lines pass through bank 1 (`1A1..1A4` to
`1B1..1B4`) on their way to the FPGA and to `J2`. `~{1OE}` is held low by a
10 k pull-down, so the switch is closed and the supervisor owns JTAG in the
shipped state — that is the primary programming path and it has to work out of
the box. Fitting **`EXT JTAG` (`J52`)** pulls `~{1OE}` to +3V3
and takes the supervisor electrically out of the chain, whatever its firmware
is doing. The controlling net is named `EXTERNAL_JTAG_SELECTED`, so its high
state says exactly what happened.
Bank 2 is unused with `~{2OE}` tied high.

This adds one intentional ERC warning: the FPGA's `TDO` output meets a
tri-state switch pin, which is what a FET bus switch pin always looks like to
ERC.

## 16. FIXED — RP2350 support parts now match the reference design

`U7`'s internal switcher uses a generic `3.3uH SRN4018` inductor and generic
15 pF crystal loading capacitors. Raspberry Pi's hardware-design guide is
explicit that RP2350's on-chip regulator depends on the prescribed inductor
selection, orientation and placement, and on specific capacitor choices.

This is a **netlist-level** task, not a layout note: copy the exact component
values and manufacturer part numbers from the RP2350B minimal-board reference
into `tools/design.py`, then follow the placement guidance during layout.
Getting this wrong produces a supervisor that mostly works, which is the worst
failure mode available.

**Fixed, from RP-008280 sections 2.1, 2.2.1, 3 and 4:**

| Reference | What it is | Now in the netlist |
|---|---|---|
| `L1` | `AOTA-B201610S3R3-101-T`, the 3.3 µH part Abracon made for Raspberry Pi with a polarity dot | `L1`, on a generated `odin:L_Abracon_AOTA-B201610S_2.0x1.6mm` land taken from the datasheet's Recommended Land Pattern (1.00 × 1.60 mm pads, 1.00 mm gap) |
| `C6`, `C7`, `C9` | 4.7 µF 0402 at `VREG_VIN`, at the output, and on `VREG_AVDD` | three 4.7 µF 0402 |
| `R3` | 33 Ω, RC-filtering the analogue supply | 33 Ω 0402 into net `SUP_VREG_AVDD` |
| `Y1` | `ABM8-272-T3`, 12 MHz, CL 10 pF, ESR 50 Ω max | named in the value field |
| `R2` | **1 kΩ in series with `XOUT`**, so the crystal is not over-driven | added; it was missing entirely |
| `C3`, `C4` | 15 pF at the crystal terminals | were already right, and now sit on the crystal side of `R2` |
| `R1` | 10 kΩ pull-up on `QSPI_SS`, shipped Do-Not-Fit | added, DNP |
| decoupling | one 100 nF per supply pin | 11 on +3V3 (8 IOVDD, QSPI_IOVDD, USB_OTP_VDD, ADC_AVDD) and 3 on +1V1 (3 DVDD) |

The 1 kΩ `XOUT` resistor is the important one: without it the crystal is
over-driven, which is a slow reliability failure rather than an obvious one.

**Still a layout obligation.** Raspberry Pi are explicit that the regulator's
performance depends on the inductor's *orientation* as well as its part
number, and on their exact placement. The footprint carries a polarity dot on
silk and a solid pin-1 marker on `F.Fab` so the requirement survives into the
assembly drawing, but honouring it is placement work, guided by RP-008280
Figure 4.

## 17. FIXED — eleven components had footprints for the wrong package

Symbol and footprint disagreed on the physical package for `U2`–`U6`, `U8`,
`U13`–`U16`, `U17`, `U18`, `U19` and `D6`. Neither ERC nor schematic parity can
see this class of error; it surfaces at assembly.

Corrected: PSRAM to SOP-8 150 mil, `W25Q256JVEIQ` to WSON-8 8x6, `W25Q32JVZP`
to WSON-8 6x5, `TLV62569DRL` to SOT-563, `CH224K` to SSOP-10-1EP, `PCF8574T`
to SOIC-16W, `TPS61085PW` to TSSOP-8 4.4x3, `ESDA6V1BC6` to SOT-23-6.

**Prevented from recurring:** `Design.add()` now checks every footprint against
the symbol's `ki_fp_filters` and refuses to build on a mismatch. The one
deliberate exception is the polyfuse, where KiCad ships no `*polyfuse*`
footprint and a 1206 chip PTC is the physically correct package; that override
is explicit in the source and carries its reason.

## 18. FIXED — per-slot fuse ratings implied nine times the available current

Nine slots x 500 mA suggested 4.5 A per rail. The real sources are far
smaller. Fuse ratings have been rebalanced (AUX 200 mA, +3V3 300 mA, +5V
500 mA) and `ref/extension-ux.md` states the shared budget per rail
explicitly, with the note that fuses are fault protection and not an
allowance.

The `~700 mA` first quoted for AUX was `5 V x 2 A x η / 12 V` — an ideal
upper bound from a nominal switch rating, not an available current. It has
been replaced by TI's own design procedure (SLVS859B equations 1–4) at the
worst-case input, run by `tools/budget.py`:

- the boost, with a 10 µH inductor at 650 kHz and the **2.0 A minimum**
  switch limit, can deliver **622 mA**;
- but AUX at full output draws 1766 mA from a +5 V rail with 1615 mA spare,
  so the binding limit is **570 mA**, and the constraint is the 5 V rail, not
  the boost;
- and that is still arithmetic at an assumed 90% efficiency with no thermal
  derating, so it is published as a **provisional design target**.

The inductor changed as part of this: 4.7 µH at 650 kHz sat outside TI's
recommended 6–13 µH range and gave 69% ripple. 10 µH gives 26% ripple *and*
more output current.

Every other shared-rail figure was equally unsubstantiated. `+3V3` was
described as having "~1.5 A spare"; the worst-case load table puts it at
**500 mA**, because `U12` also carries the supervisor, four PSRAMs, the config
flash, FPGA bank 14, the oscillator, two SFP modules (610 mA on their own) and
both VCCIO domains when they are jumpered to 3.3 V. See
`ref/power-budget.md`.

## 19. constraint — firmware must never request more than 9 V over USB-PD

`D7` is an `SMBJ13A`, a 13 V standoff TVS on `VBUS`. The `CH224K`
configuration pins are supervisor-driven, so this limit lives in firmware and
must be an assertion there, not a comment. Raising the ceiling means
re-selecting `D7` first.

Two corrections to how this was first written. The mechanism is **avalanche,
not forward conduction**: the part is unidirectional with its cathode on
`VBUS`, so a 20 V contract drives it into sustained reverse breakdown, which a
600 W *transient* device does not survive as a DC condition. Forward
conduction is what happens if it is fitted backwards, which is a different
failure — and the reason the schematic no longer uses KiCad's bidirectional
`Device:D_TVS` symbol. And the margin is narrower than "13 V" suggests but not
zero: `VBR` is 14.4 V minimum, so a 15 V contract sits in the region above the
rated standoff where leakage climbs steeply rather than in hard avalanche.

## 20. FIXED — the always-on +3V3 rail now starts on a weak 5 V port

**Entities:** `U12` (`AP63300WU-7`), `D3`, `U26`, net `VSYS`.

The original `TPS54202` needed 4.5 V at its input, while the weak-host path
could provide only about 4.24 V after protection and OR-ing. It was therefore
wrong for the one rail that must always start.

`U12` is now an `AP63300WU-7`, rated from 3.8–32 V and 3 A. The worst-case
path is now:

| | |
|---|---|
| `VBUS` on a weak host port, guaranteed minimum | 4.75 V |
| less `D3` forward drop | −0.45 V |
| less conservative `U26` on-resistance drop | −0.03 V |
| **`VSYS`** | **4.27 V** |
| `AP63300` minimum input voltage | **3.8 V** |

That leaves 0.47 V of startup margin. Its 3.3 V feedback network, 4.7 µH
inductor, input capacitor, three output capacitors, bootstrap capacitor and
feed-forward capacitor copy the manufacturer's reference circuit.
`tools/budget.py` checks its full load and inductor peak current and passes.

## 21. FIXED — Q2 gate overvoltage under a 9 V firmware fault

**Entities:** Q2 (DMG2305UX), Q3, R49, EN_VBUS5.

R49, between VBUS5_PULL and VBUS5_GATE, is now **47k**, replacing 10k.
Together with the existing 100k gate-source pull-up, it sets
`VGS = -VBUS * 100/(100+47)`: -3.40 V at 5 V and -6.12 V at 9 V.
Even 9.45 V with 1% resistor tolerances gives only 6.47 V magnitude,
below the [DMG2305UX's ±8 V gate limit](https://www.diodes.com/datasheet/download/DMG2305UX.pdf).

The weaker gate drive at 5 V increases on-resistance compared with -4.5 V
characterization. With the existing 100nF gate-source capacitor, the gate
RC time constant becomes approximately **3.20ms**; it is not a specified
linear output ramp or current limiter. Firmware must still forbid turning
Q2 on at 9 V, because doing so overvolts the +5V rail and its loads.

## 22. FIXED — screw-terminal input lacked a transient clamp

**Entities:** J50, new D8, VIN_EXT, D4, VSYS.

Added **SMBJ15A-13-F / C135046** on VIN_EXT, before D4, with cathode on
VIN_EXT and anode on GND. The standard SMB footprint uses pad 1 cathode,
pad 2 anode. Put it at J50 with a short, wide surge-current return to J50 GND.

[Diodes rates this unidirectional TVS](https://www.diodes.com/part/view/SMBJ15A)
at 15 V standoff, 16.7–19.2 V breakdown, 24.4 V maximum clamp at its rated
pulse current, and 600 W pulse power. It suppresses transients; it is not a
15 V regulator or a sustained-overvoltage disconnect. A bench supply left
at 24 V can still overload the TVS. The permitted input remains **9–14 V**;
continuous fault protection would require current limiting/fusing or cutoff.
PCB parasitic overshoot and surge energy still require validation.

## 23. FIXED — the `VSYS` monitor divider overdrove the supervisor's ADC

**Entities:** `MON_VSYS`, `MON_5V`, `GPIO40/ADC0`, `GPIO41/ADC1`.

The divider was 100 k / 33 k, which is 33/133 of the input. At 9 V that reads
2.23 V and is fine. At the 20 V `ref/power-input.md` then permitted on `J50`
it reads **4.96 V** — onto an RP2350 GPIO whose maximum is `ADC_AVDD`, 3.3 V.
A rail monitor that destroys the microcontroller in the fault it exists to
report is the wrong way round.

Fixed by sizing every monitor divider from an **absolute maximum**, not a
nominal:

| Monitor | Divider | Nominal reading | At absolute maximum |
|---|---|---|---|
| `MON_VSYS` | 100 k / 16 k | 1.24 V at 9 V | 2.76 V at 20 V |
| `MON_5V` | 100 k / 47 k | 1.60 V at 5 V | 2.88 V at 9 V |

`MON_5V` was 100 k / 100 k, safe at 5 V and 4.5 V in the same firmware fault
item 21 describes; it is now sized for that fault too.

`tools/design.py` computes both from `adc_divider()`, which rounds the bottom
resistor **down** through E24 — rounding to nearest can put the result back
over the ceiling — and raises if the absolute maximum would exceed 3.0 V.
E24 rather than E96 because firmware calibrates a monitor ratio, so precision
buys nothing and stock availability buys something.

Each of the six monitor nodes also gained a 100 nF capacitor. Two reasons: the
ADC's sample-and-hold needs charge that a 14 kΩ Thevenin divider cannot
supply, and firmware compares these readings against thresholds, so switching
ripple should not be in them.

## 24. FIXED — USB attach inrush exceeded the specification by 5x

**Entities:** `U26`, `D3`, `VBUS`, `VSYS`.

USB limits a device's `VBUS` bypass capacitance to 10 µF, or 50 µC of inrush
charge; USB-PD raises that to `cSnkBulkPd` = 100 µF only *after* a contract
exists, and at cable insertion there is no contract. The board presented
10 µF on `VBUS` plus 44 µF of `VSYS` bulk through a forward-biased `D3` —
about 54 µF and 270 µC, five times the allowance. Symptoms would have been
source droop, connector arcing, and starting reliably on some chargers and not
others.

Fixed with `U26`, a `TPS259470A` eFuse. Its 2.2 nF `dVdt` capacitor sets an
approximately 0.91 V/ms output rise, so 44 µF charges at about 40 mA. It is
autonomous rather than firmware-controlled: this path produces +3V3, which
firmware needs in order to exist. UVLO is about 3.75 V, OVLO about 9.98 V and
the typical current limit about 2.03 A. The 10 µF left directly on `VBUS` is
the attach allowance, spent deliberately.

`Q2` has a series gate resistor and 100 nF gate-source capacitor because
closing it connects `VBUS` to 66 µF of +5V bulk. R49 is now 47k (item 21),
giving a 3.20ms gate RC time constant with the 100k pull-up. This provides
slew control, not a specified inrush-current limit.

Unlike the passive RC, the eFuse also controls PD voltage-transition current
and disconnects on an overvoltage request. `D7` remains the independent TVS;
firmware must still enforce the 9 V PD ceiling in item 19.

## 25. FIXED — extension power faults could reach the base-board rails

**Entities:** `U21`–`U25`, `EXT_EN`, `EXT_FAULT`, all slot power PTCs.

Every connector rail previously branched directly from an internal rail. A
short, back-powered shield or large startup capacitor could therefore pull
down or energize the FPGA, supervisor and memories through the shared source.

There are now five protected connector buses. Four `TPS22950CDDCR` switches
protect +5 V, +3V3 and the two selectable VCCIO domains. A
`TPS259470LRPWR` protects +12 V with true reverse blocking, 13.2 V nominal
OVLO, a 500 mA typical limit, controlled rise and latch-off. All switches have
a hardware-default-off `EXT_EN`; their fault outputs wire-OR to `EXT_FAULT`.
The old per-slot PTCs remain downstream.

`TPS22950C` has an off-state output-discharge path. With an extension applying
5 V, its nominal 160 Ω path draws about 31 mA and dissipates about 0.16 W;
reverse current into the internal source remains blocked. Its output absolute
maximum is 6 V, so this closes the stated 5 V-on-low-rail mistake, not an
arbitrary 12 V miswire. That boundary is now explicit in the user documents.

## 26. FIXED — larger FPGA has a 4 A 1.0 V supply

**Entities:** `U1`, `U15`, the +1V0 inductor, the future FPGA image.

`U1` is now `XC7A100T-2FGG676I` (`C1521803`) in the imported 676-ball,
27 x 27 mm package. Its 676 symbol pin numbers match all 676 footprint pads,
every supply ball is connected. Both GTP supply groups remain powered:
G10 serves quad 213 and G11 serves quad 216 (UG482 Table 5-2).

The unused-quad wiring is now corrected in `tools/gen_sch.py:net_for()`.
Quad 213 has all eight RX pins grounded and its own 100R 1% resistor (`R89`)
from `MGTRREF_213` to MGTAVTT; its TX and reference clocks float. Quad 216's
unused lanes 2/3 also have their RX pins grounded and TX pins floating.
These follow [UG482 Tables 5-5 and 5-6](https://0x04.net/~mwk/xidocs/ug/ug482_7Series_GTP_Transceivers.pdf#page=223).

U15 is now a 4 A `SY8047QDC` (`C3018651`) with its datasheet reference circuit
and a 1 uH `FTC201610S1R0MBCA` (`C5832342`). At the conservative 1.5x FPGA
transient target, calculated peak inductor current is 2.80 A and the project's
required saturation rating is 3.64 A; the fitted inductor is rated 4.60 A.
The power audit passes. AMD XPE remains useful before fabrication, but it is
no longer needed to justify an undersized regulator.

## 27. FIXED — press-fit SFP cages replaced with solder-tail cages

**Entities:** SH1/SH2, J60/J61, `tools/placement.py`.

TE 2007198-1 was a press-fit part unsuitable for the requested JLC solder
assembly. SH1/SH2 now use **Amphenol U77A11133001 / C5355132**, which JLC lists
as Extended with wave soldering for Economic and Standard PCBA. The
standalone cage's host-board pattern matches the TE connector datum, so
**1888247-1 is retained** and no integrated connector/cage replacement is
needed. A new drawing-based `odin` footprint replaces the old cage import.

The connector depth is **35.40 mm from PCB edge** (34.50 to cage datum F,
then 0.90 to the locating-peg centreline), or 42.40 mm from the cage mouth.
The mouth overhang is 7.00 mm. Placement now uses an explicit edge-datum
origin and correct relative cage/connector rotations. TE's two connector
locating holes are also corrected from the import's 1.70 mm plated holes
to the specified 1.55 mm NPTH.

Amphenol lists this cage at **2.5 Gb/s**; the old TE cage's 16 Gb/s rating
is not retained. Higher-rate operation remains unqualified. See
[the source drawings, comparison and assembly notes](ref/sfp-cage.md).

## 28. FIXED — DONE LED loaded the open-drain configuration signal

**Entities:** CFG_DONE, R7, D1, new R98 and Q4, SUP_DONE.

D1 previously drew current directly from DONE through 330 ohms. Its brightness
and the DONE high level therefore depended on the weak pull-up or an actively
driven DONE output. The circuit no longer uses DONE as an LED supply.

R98 adds 4.7k from CFG_DONE to +3V3 (bank 0 VCCO). Q4, BSS138LT1G / C82045,
has gate on CFG_DONE, source on GND and drain on D1's cathode. The LED current
path is +3V3 → R7 (330 ohms) → D1 → Q4 → GND. With the specified green LED's
2.0–2.6 V forward drop, expected current is approximately 2–4 mA. DONE sees
the MOSFET gate and the existing supervisor input path, not that LED current.
The added pull-up draws about 0.70 mA when DONE is held low.

No `DriveDone=Yes` requirement is imposed on reference bitstreams. The LED
illuminates when DONE is released high and extinguishes when DONE is low;
SUP_DONE retains its existing connection. This follows the default open-drain
behavior described in [AMD UG470](https://docs.amd.com/v/u/en-US/ug470_7Series_Config).
Q4's low-voltage switching rating is checked against the
[onsemi BSS138LT1/D datasheet](https://www.onsemi.com/pdf/datasheet/bss138lt1-d.pdf).
The LED reports the DONE level, not application health, and is not a reliable
indicator during supply ramp-up.

## 29. FIXED — PUDC_B low strap was too weak

R6 is now **1k** (0402, C11702), from PUDC_B to GND, replacing 4.7k.
This follows the ≤1k strap recommendation in
[AMD UG470, Configuration Pins](https://docs.amd.com/v/u/en-US/ug470_7Series_Config)
and retains the intended internal I/O pull-ups during configuration.
Generator, schematic, netlist and PCB are synchronized; R6's connections
and physical placement are unchanged.

## 30. FIXED — two SFP EEPROMs collided on the shared I2C bus

**Entities:** J60/J61, U27, C231, R99–R103, SFP_SCL/SFP_SDA.

Both modules formerly connected their fixed-address 0x50 EEPROMs directly
to the same bus. Added **PCA9543APW,118 / C2652904** at 0x70, with one
channel per cage and separate downstream pull-ups. Both modules can remain
powered while firmware enumerates them separately. This chooses the mux
option; Q1 and U17 P7 retain shared power control. Documentation now states
that power removal affects both ports.

Select 0x01 or 0x02, finish selection with STOP, then read 0x50; never
select 0x03. Deselect with 0x00 before shared power-off. RESET is tied to
SUP_RUN, providing a hardware recovery path if a module holds I2C low;
a software controller reset alone may leave the mux selected. These rules,
startup handling and stuck-bus limits are in [sfp-i2c.md](ref/sfp-i2c.md),
with the NXP datasheet and procurement links. Firmware remains to be written.

## 31. FIXED — PSRAM series termination was documented but absent

Added **R104–R127**, 24 populated 33 ohm 0402 resistors (C25105), one on
each port's SCK, CE_B and IO0–IO3. FPGA-side nets and ball allocation remain
unchanged. Each resistor connects its original FPGA net to a distinct `_MEM`
net at the PSRAM; connectivity checks verify there is no direct bypass.

The generator, schematic, netlist and PCB are synchronized. `tools/place.py`
places the resistor bank at U1's right-hand escape edge instead of beside
the memory chips. Exact positions still require escape routing. 33 ohms is
a bring-up value; FPGA-end damping does not establish source termination
for PSRAM-driven reads or guarantee 100 MHz timing. The tuning and placement
requirements are in [ref/psram.md](ref/psram.md).

## 32. FIXED — +12V_EXT lacked local output capacitance

Added **C232, 10uF 25V**, 0805 X5R, Samsung CL21A106KAYNNNE / C15850,
from U25 OUT (+12V_EXT) to GND, before the selectors and branch PTCs.
The generator now explicitly rates capacitors on +12V_EXT at 25V.
Existing designators and connections are preserved. C232 belongs to U25's
placement group and must sit close to its OUT pin and ground return.

At the existing approximately 20ms output ramp, the nominal added charging
current is about 6mA; extension capacitance remains additional. The capacitor
provides local output charge storage, not a substitute for extension-side
decoupling. The selected part's voltage and package are confirmed by
[LCSC C15850](https://www.lcsc.com/product-detail/C15850.html).

## 33. FIXED — no supervisor/user indicators and unused core power-good

U17 P0/P1/P2 now sink three green LEDs (D9/D10/D11), labeled CTRL HB,
USER 1 and USER 2, with individual 1k resistors R128–R130 from +3V3.
They default off, need no extra supervisor GPIOs, and use the same qualified
LED as DONE. P3 now reads CORE_1V0_GOOD with its existing 100k pull-up.
P7 retains shared SFP power control; P4–P6 remain unused.

The [firmware contract](ref/status-leds.md) requires a shadow output byte,
P3–P6 always written high, and masked updates so heartbeat/user LEDs cannot
change SFP power or drive PG low. PG polling and LED control share the SFP
upstream bus, so a stuck bus also stops heartbeat updates. This implements
the hardware; supervisor firmware and physical placement/routing remain.
