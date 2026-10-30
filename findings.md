# Odin — findings

Two eras are recorded here. **Items 1–4 are historical** — they describe the
EasyEDA/Altium input set and are closed: the design now lives in `kicad/`,
generated from `tools/`, and those inputs are reference material only. **Items
5 onward are live**, against the current KiCad design.

Regenerate everything with the commands in `kicad/README.md`.

**Latest review:** [final practical audit, 2026-10-29](#final-practical-verdict),
against `6ad8068`. **The earlier three P1 circuit findings are corrected;
no additional confirmed schematic blocker was found. Proceed with detailed
placement.** Connector mechanics, source-policy details and prototype
measurements remain. Parts III–IV and their correction tables are history;
**Part V is the current verdict**, including what merits action and what
does not justify further redesign.

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

# Part III — independent schematic and city audit, 2026-10-29

## Audit conclusion and scope

**The architecture and much of the voltage-domain planning are sound, but
the schematic needs corrections before detailed placement is frozen.** The
most consequential findings are the FPGA's indefinite partial-power state,
USB backfeed through Q2, missing USB termination, an unsafe PD startup
default, inadequate local buck input bypass, and PSRAM power-up pin states.
Passing ERC has not established correct bring-up.

This review covers the current seven-sheet KiCad design, `tools/design.py`,
ball allocation, actual PCB island membership, `ref/city/plan.yaml`, the city
preview, and the floorplan/routing rules. Baseline: commit `82cb093` plus the
working tree at review time. Earlier EasyEDA exports are historical. The
older statements marked FIXED above are not evidence that the current
design still satisfies the associated requirement; some reference numbers
have since been reused.

This is a review of the schematic and placement intent. Unrouted connections,
staging outside the outline, and the absence of final copper are expected
at this stage. They are not counted as design defects. No parts, nets,
placement, routing, or generator behavior were changed for this audit.

**Priorities:** P1 = correct before committing the prototype PCB; P2 = resolve
the design choice or qualification before placement/routing is frozen;
P3 = resolve during the normal footprint/fabrication review. A qualification
gap means the decision is unproven, not that failure has been demonstrated.

| Independently reproduced check | Result |
|---|---|
| Schematic export versus stored netlist | Matches |
| Declarative design pin nets versus actual PCB pads | 0 mismatches across 499 parts |
| XDC and gate top versus allocation generator | Matches |
| ERC | 0 errors; the 2 documented temperature-diode label warnings |
| PCB schematic parity | 0 differences |
| Copper / assembly | 8 copper layers, all components on front; 0 tracks, 0 vias |
| Footprint staging | 66 origins inside the board, 433 outside |
| DRC | 4 hole-clearance errors, 296 warnings, 499 unconnected items |
| Mechanical lattice checker | Fails; not propagated into `GATE PASS` |

The last two rows need interpretation; see items 47 and 49. Machine-readable
snapshot evidence is in
[audit-2026-10-29.json](ref/board-review/audit-2026-10-29.json).

## 34. P1 — always-on FPGA VCCO with switchable VCCAUX violates the recovery case

**Evidence:** `tools/gen_sch.py` connects bank 0 and banks 14/35, plus the
unbonded-bank supply balls, directly to always-on `+3V3`. `U14` supplies
`+1V8_IO`, then FB1 supplies VCCAUX/VCCADC as `+1V8`. U14 depends on `+5V`
and `EN_1V8`; both can remain off while a blank RP2350 flash sits in the ROM
USB loader. The same condition occurs during controller reset or a policy
that powers down the FPGA while retaining the supervisor.

AMD distinguishes its recommended supply order from a reliability limit:
with 3.3 V VCCO, VCCO minus VCCAUX must not exceed 2.625 V beyond the
per-cycle time allowance. DS181 Table 7 specifies 500 ms at the stated
100 °C condition. Here the difference is about 3.27 V for an unbounded
time. Holding PROGRAM_B low does not change the supply voltages.
[AMD DS181, Power-On/Off Power Supply Sequencing and Table 7](https://docs.amd.com/v/u/en-US/ds181_Artix_7_Data_Sheet).

**Required change:** separate the supervisor's always-on domain from the
FPGA supply policy, or provide an autonomous AUX/VCCO relationship that
satisfies this bound. Prove it during ROM recovery, reset, faults and
power-down, including discharge of the large capacitor banks. Firmware
alone cannot fix the blank-flash case. Also check powered peripheral signals
against any FPGA bank that the revised scheme leaves unpowered.

## 35. P1 — Q2 bypasses USB reverse blocking and current protection

**Evidence:** Q2 source/pin 2 is VBUS; drain/pin 3 is `+5V`. Its intrinsic
diode conducts from `+5V` toward VBUS. With J50 powering U11 and the USB
source absent or falling, USB VBUS can therefore be energized even with
Q2 commanded off. When Q2 is on, its channel conducts both ways. D3/D4 and
U26 do not interrupt this separate path.

This follows from the actual net connections and the MOSFET internal
schematic; it is not a firmware hypothesis.
[Diodes DMG2305UX, internal schematic and ratings](https://www.diodes.com/datasheet/download/DMG2305UX.pdf).

The forward bypass also feeds the `+5V` loads without U26's current limit
or specified output slew. C183 slows the gate; it does not establish a
bounded load-current ramp. A firmware mistake or reset during a PD voltage
transition can still pass 9 V into 5.5 V-rated consumers.

**Required change:** give the bypass reverse blocking and a defined current/
inrush limit, with a hardware voltage-valid interlock if it must be safe
independently of firmware. Back-to-back FETs or a suitable power-path device
are candidate implementations, not an audited replacement circuit. Verify
USB alone, J50 alone, both sources, either source being removed, and 5-to-9 V
transitions. This reopens the system-level protection claims in items 10/24.

## 36. P1 — RP2350 USB D+ and D− lack their required 27 ohm resistors

**Evidence:** J1, D6 and U7 pins 66/67 share `USB_DM` and `USB_DP` directly.
Neither path contains a series resistor. The 33 ohm supervisor-to-FPGA
resistors serve unrelated nets.

Raspberry Pi requires 27 ohm USB series termination close to the MCU.
Add both resistors to the U7 island, with separate connector-side net names.
Keep D6 at J1 and route the pair through the protection point without stubs.
[Hardware design with RP2350, section 5.1](https://datasheets.raspberrypi.com/rp2350/hardware-design-with-rp2350.pdf).

This is a schematic correction even though the USB cable carries only
full-speed data. USB enumeration and ROM recovery are not established until
this is corrected and tested.

## 37. P1 — CH224K has no independent safe voltage default

**Evidence:** U18 CFG1/2/3 go directly to RP2350 GPIO27/28/29. There is no
external configuration resistor on CFG1. The board relies on firmware to
forbid requests above 9 V, but U18 starts from VBUS before that firmware.

WCH explicitly warns that MCU startup/default pin states can select 20 V,
and specifies a configuration resistor when the downstream system cannot
tolerate that. A 6.8 kohm CFG1-to-ground setting selects 9 V in resistor
configuration. The exact interaction with subsequent GPIO drive must be
checked before adopting that implementation.
[WCH CH224 datasheet, section 5.2, manufacturer-authored mirror](https://uelectronics.com/wp-content/uploads/2025/04/ch224k-Datasheet.pdf).

**Consequence:** U26's approximately 10 V OVLO disconnects the supervisor
path at a high request, potentially removing the controller that would
correct it. D7 is a 13 V-standoff TVS, not a continuous 20 V regulator.
RP2350 internal pulls are not an independently powered startup strap.
This is a missing guarantee; an actual 20 V startup was not measured.

**Required change:** establish a safe hardware default valid before MCU
power-up and through ROM recovery/reset. Verify cold attach on a PD source
offering 20 V, then every permitted voltage transition. Retain the 9 V
firmware ceiling after adding the hardware default.

## 38. P1 — several buck islands lack local input energy storage

| Converter | What its island currently contains at VIN | Conclusion |
|---|---|---|
| U11 AP63300, VSYS to 5 V | No VIN-to-GND capacitor | C185/C186 belong to U26, C192 to U12; none travels with U11 |
| U12 AP63300, VSYS to 3.3 V | C192, 10 uF | Correct ownership; verify effective capacitance at 21 V |
| U13 / U14 / U16 TLV62569 | C200 / C203 / C206, each 100 nF | Small HF bypass only; no local multi-uF input reservoir |
| U15 SY8047 | C207, 22 uF, plus SVIN RC filter | Correct reference topology; retain the tight power loop |

TI's TLV62569 example uses 4.7 uF at VIN. Its layout guidance requires a
short input-capacitor loop. The AP63300 guidance likewise places input
capacitors directly across VIN/GND. A common upstream capacitor is not
proof of an adequate local switching-current loop.
[TI TLV62569, sections 8.2.2.5 and 10](https://www.ti.com/lit/ds/symlink/tlv62569.pdf),
[Diodes AP63300, PCB Layout](https://www.diodes.com/datasheet/download/AP63300_AP63301.pdf).

**Required change:** assign or add a properly rated local input capacitor
to U11; add the reference-sized local input capacitors to U13/U14/U16 and
their island profiles. Select against DC bias and ripple current. Place
these before the inductor/output row and close the VIN-cap-GND loop locally.
The regulator street can remain; its shared supply does not replace these
capacitors.

## 39. P1 — PSRAM startup pin states conflict with PUDC_B low

**Evidence:** all four PSRAMs share U14's `+1V8_IO` with bank 13. Their CE,
clock and data pins have series resistors but no external state-setting
resistors. PUDC_B is strapped low, enabling FPGA configuration pull-ups.

AP Memory requires, from the start of the supply ramp through 150 us after
stable VDD: CE high tracking VDD within 200 mV, clock low, and all four
data pins low. Initialization then requires the reset command sequence.
FPGA pull-ups on clock/data give the opposite idle state; before FPGA
initialization their availability is also not established.
[APS6404L-SQN rev 4.0, section 8](ref/datasheets/aps6404l-sqn.pdf).

**Required change:** define hardware pin states that satisfy the entire
power-up interval, including FPGA-unconfigured operation. Candidate pulls
must overcome the worst configuration pull-up and meet the PSRAM thresholds
without excessive operating load. An alternative supply/isolation scheme
must provide the same guarantee. Put these parts at the PSRAM-side nodes,
then explicitly implement 150 us wait, reset-enable/reset, and reset recovery
in the memory controller. A reset command after boot is not evidence that
the earlier electrical requirement was met.

## 40. P2 — total regulator output capacitance has not been qualified

Summing actual direct rail-to-ground capacitor values, rather than only the
two capacitors inside each regulator box, gives:

| Rail | Nominal direct capacitance | Additional state-dependent load |
|---|---:|---|
| U13 `+2V5` | 103.38 uF | J19/J20 bank capacitors and enabled connector branches |
| U14 `+1V8_IO` | 112.98 uF | 63.55 uF behind FB1, plus selected banks/branches |
| U16 `+1V2_MGT` | 49.90 uF | No connector export |
| U15 `+1V0` | 506.90 uF | MGT filter capacitance behind L9 |
| U12 `+3V3` | 221.16 uF | Selected VCCIO banks, switched branches, inserted cards/modules |

These are BOM-value sums, not measured effective capacitances. The bead and
inductor loads are frequency-dependent, not simply parallel capacitors.
The selectable banks add 44 uF each before the branch loads are enabled.

TLV62569 Table 4 validates particular LC combinations up to 2 x 22 uF for
these voltages; it asks for other combinations to be checked individually.
Matching the local two-cap example therefore does not qualify U13/U14's
assembled load. Do not remove FPGA decoupling just to make this table fit.
[TI TLV62569, sections 8.2.2.3–5](https://www.ti.com/lit/ds/symlink/tlv62569.pdf).

U15's recovered Silergy datasheet confirms the pin map, 0.6 V feedback,
22 uF PVIN bypass, 1 uF SVIN bypass and programmed soft-start topology.
It does not demonstrate stability with this board's approximately 507 uF
direct output network.
[Silergy SY8047 rev 0.9, manufacturer-authored mirror](https://atta.szlcsc.com/upload/public/pdf/source/20220517/73BFF7B078F09CB6F3A268820B2D4DA9.pdf).

**Required resolution:** qualify startup, loop stability and load release
with effective capacitance/ESR bounds and every jumper/load state; use vendor
support, simulation and representative load-step measurements as appropriate.
Revisit compensation or regulator selection if necessary. Oscillation has
not been established by this audit.

## 41. P2 — the 1.8 V extension setting has no load-switch input margin

U23/U24 take their VIN from selectable VCCIO_1/VCCIO_2. The 1.8 V setting is
nominally 1.8024 V, while TPS22950C specifies VIN >= 1.8 V. Even a 1% low
rail is below that bound, before divider tolerance, ripple and copper loss.
[TI TPS22950x, Recommended Operating Conditions](https://www.ti.com/lit/ds/symlink/tps22950.pdf).

This does not invalidate the FPGA/PSRAM 1.8 V domain, whose operating window
is wider. It invalidates a guaranteed protected extension supply across that
domain's tolerance. Select a switch qualified below the minimum rail, or
choose a rail target/tolerance that simultaneously meets every consumer's
limits. Bench success at room-temperature nominal voltage is insufficient.

The switch choices otherwise make sense: reverse blocking, externally held
OFF enables, fault reporting, local input bypass and the documented
current-limit settings are useful protections.

## 42. P2 — RP2350 pin allocation requires avoidable custom peripheral handling

| Board function | Assigned GPIO | Native peripheral function |
|---|---:|---|
| SUP_SCL | 14 | I2C1 SDA |
| SUP_SDA | 31 | I2C1 SCL |
| SUP_UART_TX | 19 | UART0 RTS, or auxiliary UART0 RX |
| SUP_UART_RX | 20 | UART1 TX, or auxiliary UART0 TX |

The I2C roles are reversed. The UART assignments do not form a native
transmit/receive pair for one UART. Swapping just the UART signal names
does not automatically make a valid pair.
[RP2350 datasheet, GPIO functions](https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf).

**Recommendation:** swap the I2C assignments and allocate a legal UART pair
while spare GPIOs remain. Otherwise explicitly budget PIO/software drivers
and test recovery when the expander bus stalls. The shared FPGA-flash SPI
pins also do not form a native SPI peripheral pinout; that interface needs
an intentional PIO/software implementation. These are functional planning
issues, not electrically crossed I2C wires: software can implement the
present mapping, at additional complexity.

## 43. P2 — hard-strapped master SPI cannot also provide slave-serial loading

M[2:0] are hard-strapped to 001. The RP2350 cannot change M1/M2. AMD assigns
001 to master SPI and 111 to slave serial; PROGRAM_B resets configuration
but does not override mode straps. After release the FPGA drives CCLK in
master mode, so the supervisor must not also drive it as a slave-serial
source.
[AMD UG470, Configuration Modes and Serial Configuration](https://docs.amd.com/v/u/en-US/ug470_7Series_Config).

The direct flash-writing plan remains plausible while PROGRAM_B holds the
FPGA reset, with correct bus ownership. For volatile FPGA loading, either
use the already-wired JTAG path and correct the slave-serial promise, or add
a deliberate mode-selection circuit. Firmware must also restore the flash's
boot-compatible address/protocol state before releasing PROGRAM_B. Verify
golden/fallback addressing with the actual 256 Mbit flash rather than
assuming every MultiBoot address is interchangeable.

## 44. P2 — several island memberships do not preserve the intended electrical location

The actual PCB groups, not the older placement prose, contain:

| Parts | Current group | Required placement decision |
|---|---|---|
| R104–R109, R110–R115, R116–R121, R122–R127 | U2, U3, U4, U5 respectively | FPGA-driven clock/CE source damping belongs at the FPGA escape, not locked to the memory island |
| R151, 22 ohm SDRAM clock | U32 | Source is U1; move its ownership/location to the FPGA clock escape |
| Q2 | J1 | Keep with the reviewed power path |
| Q2 gate parts R46/C183 | U26 | They serve Q2, not U26; prevent their separation when moving blocks |
| X4, R147, C246 | Ungrouped | Keep the oscillator, source resistor and bypass as one clock island attached to U1 |

A membership error is significant now because a rigid group move preserves
the error. `place.py` can place PSRAM resistors at the FPGA, but that is not
where their current city groups keep them. Split source parts from memory
load parts deliberately, or add an explicit source-location constraint.
R147 should remain at X4, which is the source of SYS_CLK.

Bidirectional PSRAM data needs separate consideration: an FPGA-end resistor
does not source-terminate memory-driven reads. Retain tuning footprints and
verify both directions; do not add a second 33 ohm automatically. The
existing warning in `ref/psram.md` is correct.

## 45. P2 — the inboard microSD socket needs an access contract

The city script deliberately gives J74 no edge reservation. Its opening
faces toward the bottom, broadly behind J72's edge position. A push-push
socket needs space for the card's travel and a finger/tool to latch and
eject it; a no-overlap rectangle around the socket body does not supply that.

**Resolution:** choose explicit access from above with a keep-out through
any shield/enclosure, or reserve a board-edge opening and move other blocks.
Check insertion and ejection with adjacent jacks populated and a shield
installed. Inboard placement can be acceptable; the current plan does not
yet establish usable access. Do not treat J74 as an ordinary wired IC.

## 46. P2 — power checks do not establish the aggregate input-source envelope

`budget.py` currently checks board-only rail load against regulator ratings
and the VSYS input window. It does not enforce source-profile power,
simultaneous exported loads, thermal limits, or the inductor checks claimed
in some documentation.

The current planning model consumes approximately 0.721 A from 5 V and
0.919 A from 3.3 V: about **6.64 W** before upstream losses and extensions.
Its default-USB profile supplies only 4.75 V x 0.9 A = 4.28 W. That profile
can support a restricted mode, not the modeled full board. Moreover, 900 mA
is not a universal USB default; ordinary USB 2.0 configured bus power is
500 mA, and higher Type-C current requires the corresponding advertisement
or contract.
[USB-IF power compliance policy](https://compliance.usb.org/index.asp?Format=Standard&UpdateFile=Policies).

For both VCCIO domains selected to 3.3 V, nominal low-voltage switch limits
allow another 1 A x 5 V + 3 x 0.5 A x 3.3 V = 9.95 W. Together this is
16.59 W. Assuming 90% upstream efficiency and roughly 8.5 V after the USB
path requires about 2.17 A, already above U26's 2.03 A typical limit.
Using the switch upper-limit tolerances raises this to about 2.49 A. These
are planning calculations, not measured efficiencies or available allocations.

**Resolution:** define recovery/light/full-power input modes and a shared
export allowance for each. Include source-current knowledge, U26 minimum
limit, jumper combinations, conversion losses, DC-biased capacitors,
inductor peak current and hot-board thermals in qualification. Existing
warnings that fuse ratings are not additive remain necessary. A 4 A
regulator label also does not prove a 4 A core at temperature; XPE and the
chosen inductor's tolerance/saturation curve remain open work.

## 47. P2 — a green gate currently conceals a failed mechanical check

`tools/gate.py` prints `place.py --check exit 1`, then still prints
`GATE PASS`: that return code never updates `ok`. The present lattice
failure is understandable while connectors and posts are staged or remain
in old hand positions; reporting a complete pass is nevertheless misleading.
Separate electrical-consistency and mechanical gates, or make the final
status depend on every check it claims to enforce.

The existing Vivado gate has a different, deliberate limit:
`gateware/gate/gate.xdc` false-paths all inputs and outputs. Its routed
bitstream is useful evidence for legal balls/I/O primitives and internal
implementation, not for PSRAM, SDRAM, RGMII, HDMI or cable timing. The
existing timing report's success must be interpreted within that scope.
No new Vivado functional timing sign-off was performed in this audit.

Before routing, define real interface budgets: flight time, clock-to-data,
setup/hold, skew and allowable via/layer changes. RGMII clock skew must be
provided once; the PHY's enabled delay straps should not be combined with
another automatic MAC-side delay without analysis.

## 48. P2 — contradictory documents can produce an incorrectly wired shield

`ref/user-manual.md` still shows the old signal-row grounds in the last
two columns. The current schematic uses columns 3 and 6 for ground. It also
describes obsolete connector bodies, per-slot selectors and a 14 V input
ceiling. `floorplan.md` retains its old opposite slot sides/top-network
contract above the accepted rotated city. `ref/network.md` still calls the
PHY controls bank 13, although they now correctly use bank 35.

Other stale examples include the old VCCO grouping in `ref/decoupling.md`,
the deleted boost in `ref/supervisor-flash.md`, and SFP-related details in
older findings. These are not just prose discrepancies when a user builds
a mating PCB from the wrong pin table.

**Resolution:** establish one current connector/power/floorplan contract,
mark earlier revisions as historical, and regenerate all dependent tables.
Keep item 14's shield mating, key projection and height qualification open.
The circuit-to-PCB net map is consistent; the human-facing contract is not.

## 49. P3 — USB-C footprint holes violate the current drill-clearance rule

All four actual DRC errors are J1: ground pads A1/A12/B1/B12 versus its
NPTH locating holes. Actual hole clearance is 0.1847 mm; the board rule is
0.2500 mm. This is a footprint/fabrication issue independent of unfinished
routing. Check the connector drawing and the chosen fabricator's hole-to-
copper capability; correct the footprint or justify a local rule. Do not
silently lower the global hole clearance.

## 50. P2 — telemetry does not cover every rail the supervisor claims to verify

The six ADC connections measure VSYS, 5 V, 3.3 V, 2.5 V, `+1V8_IO` and
1.0 V. There is no measurement of `+1V2_MGT`, either selected VCCIO domain,
or actual `+1V8` **after FB1**. Core PG is additionally read through U17.
Consequently, an open/missing FB1 can leave VCCAUX absent while MON_1V8
reports a healthy regulator output. The jumpers are not automatically sensed.

**Resolution:** measure the rails needed for the intended sequencing/fault
policy, especially actual VCCAUX, or narrow the claimed observability and
document the checks firmware cannot make. Spare ADC-capable GPIO46 is
available, but all desired measurements may need further pin allocation or
a multiplexer. Keep monitor bypass capacitors at the ADC inputs and evaluate
fault voltages as well as nominal divider ratios. This is separate from
item 34: observing a supply cannot enforce its required startup relationship.

## 51. P2 — city planning assigns the wrong key posts to the 5 V buses

Both city variants associate MK71 with J7 and MK72 with J8. In the current
design, `MK{ord(slot)}` makes MK71/MK72 the **G/H** keys; L/M require
**MK76/MK77**. The latter remain in the board's fixed-ghost set instead of
traveling with the proposed top bus neighborhoods. All these posts are GND,
so electrical parity cannot detect the semantic mistake.

Correct the city anchor references and group each post with the power row
it actually keys. Keep G/H keys with their side-edge sections. This is a
specific planning error beyond the expected unfinished placement, and one
reason the mating lattice must be verified from real pad coordinates.

## City planning verdict

**A regulator street is acceptable.** Regulator proximity should minimize
the high-current output path and input switching loop, while quiet feedback
and clocks remain protected. Putting all regulator bodies in a neat row is
not itself an electrical requirement. The accepted U1 rotation and opposite
slot sides are a reasonable starting point; the score is a wiring heuristic,
not a routing or power-integrity proof.

| Neighborhood | Assessment and placement instruction |
|---|---|
| U15 core supply above U1 | Keep its priority and a wide output corridor into the core balls. Align the **inductor output/output capacitor copper**, not merely the IC centre. Keep FB sensing away from SW and take the sense point from the intended regulated output. |
| U14 1.8 V / U16 MGT in the same row | The row is reasonable. With the actual 90-degree U1 rotation, bank 13's PSRAM/buffer balls are toward the upper-left. Consider U14 on that side before spending the left corridor on the unused-MGT regulator. VCCAUX still needs its filtered, quiet distribution. |
| U13 2.5 V below U1 beside U30 | Good relative location for bank 16 and the PHY's 2.5 V pads. Keep its switching loop clear of the PHY crystal and pair escape. Resolve its capacitor qualification first. |
| U11 feeding the low-voltage regulators | Good upstream relationship to the row. Add its own input bypass and local bypass at every downstream converter; keep the wide 5 V distribution out of sensitive clock corridors. |
| U12 3.3 V on the left | Acceptable for a distributed rail with broad plane copper; it need not sit beside the RP2350. Keep VSYS input routing and local CIN controlled, and check worst-case drop to the distant supervisor/SDRAM. |
| U2–U5 PSRAM | Give all four short escapes toward their bank-13 balls before legalizing slow support circuitry. U2 is currently to the right while the others are left; this is an avoidable detour candidate, not proof of an unroutable board. Group by timing-critical nets, and split the source resistors as in item 44. |
| U7 supervisor with U8/Y1 | Correct neighborhood and useful satellites. Keep the regulator loop as a protected sub-island, USB resistors at U7, crystal loop quiet, and QSPI short. Avoid putting U14/U15 switch-node fields across Y1 or VREG_AVDD. |
| U30 / X3 / J70 | Keeping the PHY between bank 16 and its jack is sound. Its present lateral offset from J70 still needs a clear four-pair MDI corridor; prefer moving slow/status blocks over bending those pairs through power circuitry. |
| J71/J72 and ESD arrays | Correct ownership of connector-side ESD; use flow-through paths and very short ground returns. Their bottom-left position agrees with the network-facing bank. |
| J73 with U31 | Correct satellite choice and edge location for bank 35. Preserve the direct connector-to-protection paths and differential pair corridors. |
| U32 SDRAM | The lower corner between bank 35 data/control and bank 14 address is a reasonable compromise. Orient its data and address pin rows toward their actual escapes and prioritize the forwarded clock; move R151 to its source. |
| U33 MRAM | Correct low-speed bank-14 neighborhood; lower placement priority than PSRAM/SDRAM/clock escapes. |
| J74 microSD | Connectivity attracts it to the right functional neighborhood, but access must override the wire-count solution. See item 45. |
| Slots, power rows, keys | The intended parallel lattice is appropriate for bridging shields. Correct the MK71/MK72 versus MK76/MK77 planning error in item 51, then reconcile old positions and run the real pad-coordinate check. |
| J1/U26/Q2 and J50/D4/D8 | Correct to treat these as source-entry neighborhoods. Rework the electrical path first, put TVS return loops at the entry, and keep Q2's gate network with Q2. |
| J68 AUX | Keep an edge position with wire bend/screwdriver clearance and an independent wide path to the branch fuses. Its raw, unswitched behavior is a deliberate product constraint. |

### Power plane and routing implications

The eight-layer S/GND/S/PWR/GND/S/GND/S concept is sensible: signal escape
layers have nearby ground references, and the power/ground pair is tight.
Keep these ground planes continuous; the small RP2350 LX clearance called
for by its reference layout is a local exception, not permission to split
signal return planes. Outer-layer differential geometry must not be reused
on an inner layer without recalculation. USB also needs a defined 90 ohm
pair geometry; it currently has no dedicated net class. The 0.125 mm RGMII/
SDRAM width is an outer-layer estimate, not a universal 50 ohm rule for
In2/In5.

The power doors are a useful way to reserve corridors. They do not prove
that In3 has room for every split rail or that narrow In5 power traces can
replace plane areas without cost. Draw those polygons and trial-escape a
representative set of core supply vias and deep signal balls before fixing
every neighborhood. The depth report contains 80 assigned signal balls at
depth >=7, of which 63 are classified as allocation choices; this is a
reason to trial-route the escapes, not proof that 63 can all be eliminated.

As an illustrative copper calculation, a 15 mm x 5 mm corridor of 15.2 um
copper is about 3.4 milliohms at room temperature, or 14 mV drop at 4 A,
before vias and necks. The 1 V rail has little voltage margin after regulator
and resistor tolerances. Check the complete supply/return path, hot copper,
and output-capacitor/load locations; a favourable centroid score cannot
establish this. The 4 A figure here is a sizing example, not a measured load.

### Island rules to preserve during compaction

1. Reserve connector mating/card/cable/tool space before packing circuitry.
2. Place local switching loops and the RP2350 reference regulator first;
   keep feedback/analogue nodes away from SW/LX and inductor fields.
3. Place FPGA/source clock resistors at their actual drivers, then memory
   loads and timing-critical escapes. Keep ESD at the external entry.
4. Preserve each bank's capacitor ownership while changing U1 orientation.
   The top-side-only decoupling ring is not inherently wrong: UG483 permits
   these mid-frequency capacitors within two electrical inches, with low-
   inductance mounting. Vias and plane continuity decide whether this ring
   actually works.
   [AMD UG483, PCB Capacitor Placement](https://docs.amd.com/v/u/en-US/ug483_7Series_PCB).
5. Pack slow expanders, LEDs and service details into the remaining space.
   A rigid island is a convenience, not a reason to retain an electrically
   wrong orientation or separated input capacitor.

## Electrical decisions supported by this audit

| Decision | Conclusion and evidence boundary |
|---|---|
| FPGA bank voltages | Coherent: bank 13 at 1.8 V for PSRAM/translators; bank 14 at 3.3 V for configuration; bank 16 at 2.5 V for RGMII/LVDS; bank 35 at 3.3 V for HDMI/SDRAM; selectable banks 15/34. This does not resolve item 34's sequencing defect. |
| Configuration straps | CFGBVS high agrees with 3.3 V configuration; 001 straps agree with master SPI; PROGRAM_B/INIT_B pull-ups, low PUDC_B strap and buffered DONE LED have sensible topology. Slave serial and startup defaults are separate findings. |
| Hardware JTAG ownership | U20 plus J52 gives a useful independent isolation path for external recovery. Verify the header's chosen cable pinout; it is not a standard AMD 14-pin header. |
| FPGA decoupling values | The VCCINT/VCCBRAM/VCCAUX and per-bank networks match the cited UG483 device/package prescription. Keep local bank placement and via inductance under review; capacitance quantity does not qualify the regulators' control loops. |
| PSRAM part/voltage | APS6404L-SQN-SN is the 1.8 V, 64 Mbit SOP-8 part, giving 8 MB per chip and 32 MB total. Bank 13 now matches it. Four independent buses are correctly connected; initialization and SI remain open. |
| SDRAM / MRAM / SD | The present pin maps and 3.3 V supply domains are coherent. SDRAM has seven supply bypasses and CS/CKE bias parts; MRAM has CS/WP/HOLD pull-ups; SD SPI contacts and five pulls are present. This is topology evidence, not 166 MHz SDRAM qualification or a guarantee for every SD card's peak current. |
| 5 V translators | SN74LXC8T245 supports the 1.8 V A side; DIR/OE reference that side, with OE held disabled externally. The B side is 5 V. A-H remain direct FPGA pins; the existence of translators on L/M does not protect A-H. |
| Extension power | Bank voltage and selected PIN V have the same upstream source; separate protected low-voltage exports preserve the base-board domains during a branch fault. The 1.8 V switch margin, aggregate budget and mechanical pin map still need resolution. |
| PHY digital interface | Realtek rev 1.7 supports external 2.5 V RGMII with CFG_EXT=1/CFG_LDO=01. Reset held low permits its delayed I/O supply; 10 ms reset and at least 72 ms settling remain gateware obligations. The 3.3 V reset/interrupt controls correctly moved to bank 35. |
| Ethernet jack wiring | HanRun's current rev B drawing confirms P1 as common chip-side centre taps, P10 as the internal 75 ohm/capacitor network return, MDI polarities, and LED 11/12 and 14/13 polarity. The current schematic agrees. |
| PHY analogue passives | A published FriendlyELEC RTL8211F design supports the 2.49 kohm RSET and capacitively grounded centre-tap approach. That board uses the switching-core variant: it does **not** independently prove the exact FD internal-LDO output capacitor requirement. Keep that distinction and verify FD loop/rail behavior. |
| Raw LVDS links | Real pair positions and clock-capable receive pins are allocated; bank voltage and internal DIFF_TERM intent agree. Existing STP-only, common-ground, both-boards-powered restrictions are substantive electrical constraints. They do not establish arbitrary cable length, hot-plug or unpowered-peer tolerance. |
| HDMI | TMDS_33 in a 3.3 V bank with receiver termination and the TPD12S016 companion is coherent. VCCA/VCC5V/5V_OUT bypass, enables, DDC/HPD/CEC paths and utility-pin resistor are present. Keep U31 at the jack; 720p operation still needs actual serializer/timing and SI validation. |
| Supervisor regulator/crystal | The selected inductor, AVDD RC filter, crystal load and damping topology are reasonable. Preserve winding orientation and the reference local copper arrangement; consider the recommended extra remote DVDD bulk capacitor. A generic ring profile alone does not prove regulator layout equivalence. |
| Input ratings | The stated 21 V J50 operating range is consistent with the wide-input bucks and explicit VSYS capacitor ratings. TVS clamps are pulse limits, not continuous overvoltage regulation; bench/surge testing must use a defined source impedance and waveform. |
| AUX pass-through | A separate raw input with 33 V branch PTCs is coherent for the stated 9–28 V use. It is unregulated and unswitched; EXT_EN does not isolate it. Preserve the explicit no-backfeed and shared-capacity contract. |

Sources for the cross-checks above:
[AMD UG470](https://docs.amd.com/v/u/en-US/ug470_7Series_Config),
[AMD UG483](https://docs.amd.com/v/u/en-US/ug483_7Series_PCB),
[AP Memory datasheet](ref/datasheets/aps6404l-sqn.pdf),
[Winbond SDRAM datasheet](ref/datasheets/w9825g6kh.pdf),
[Everspin MRAM datasheet](ref/datasheets/mr25h10cdf.pdf),
[TI SN74LXC8T245](https://www.ti.com/lit/ds/symlink/sn74lxc8t245.pdf),
[Realtek rev 1.7, manufacturer-authored mirror](https://static.chipdip.ru/lib/595/DOC042595102.pdf),
[HanRun rev B drawing](https://hrdzcn.oss-cn-beijing.aliyuncs.com/202601/ab534667d942f65.pdf),
[FriendlyELEC NanoPi R2S Plus schematic, sheet 11](https://wiki.friendlyelec.com/wiki/images/d/da/NanoPi_R2S_Plus_2309_SCH.PDF),
[TI TPD12S016](https://www.ti.com/lit/ds/symlink/tpd12s016.pdf),
[Raspberry Pi hardware guide](https://datasheets.raspberrypi.com/rp2350/hardware-design-with-rp2350.pdf).

### Optional simplification, not a defect

The unused GTPs do not have to consume a powered regulator neighborhood.
UG482 Table 5-4 permits grounding MGTAVCC/MGTAVTT/MGTRREF when the entire
power-supply group is unused, with the specified RX/TX/reference-clock
connections. The current powered treatment is also a valid design choice
if its supply requirements are met. If rev A will truly never use GTP,
evaluate removing U16 and the associated filtering/decoupling; do not ground
only one of the supplies or mix the two prescribed schemes.
[AMD UG482, Unused GTP Quad Power Supply Group](https://docs.amd.com/v/u/en-US/ug482_7Series_GTP_Transceivers).

## Recommended order of resolution

Correct items 34–39 first, because they can change the power tree, nets and
island contents. Resolve regulator/load-switch qualification and source
budgets next. Then settle native peripheral use and the FPGA-loading modes,
repair island ownership, and reconcile the mechanical/access contract.
Only then compact the city, trial-route critical escapes and freeze the
plane corridors. Final routing/SI, prototype measurements and fabrication
checks remain later milestones; the absence of those results at this stage
is expected.

## Status of items 34–51 after the corrections of 2026-10-29

Commits a557379, 49ebd65, b9d464b, cd02e23 and the documents commit that
follows. Every step ends with the electrical gate passing (ERC 0 errors,
DRC 0 errors, parity 0) and nothing inside the board outline moved; the new
parts (53 footprints) are staged in the import band for the owner to island.
The entries in `ref/rev-a-report.md` carry the numbers.

| Item | Status | What changed |
|---|---|---|
| 34 VCCO/VCCAUX | **FIXED** | U11 (EN floating, DS42002 automatic start) and U14 (EN tied to +5V, SLVSDG1C EN ≤ 6 V) run whenever +3V3 does, so VCCAUX is up within the regulators' own start-up of the 3.3 V banks and never depends on firmware or a blank flash. Power-down: both banks discharge through their loads within tens of ms (221 µF on +3V3 into ≥ 100 mA; 176 µF on 1.8 V); **[verify]** the DS181 Table 7 500 ms bound on the prototype with a scope. GPIO23/26 freed. |
| 35 Q2 backfeed | **FIXED** | Q2/Q3 gate network removed. U34 TPS2121 power mux: IN1 VBUS, IN2 U11 (+5V_BUCK), OUT +5V; reverse blocking both inputs, 2.5 A limit, 100 nF soft start, 5 µs switchover; dividers select VBUS only between 4.44 V (PR1 > CP2) and 5.63 V (OV1), so a 9 V contract hands the rail to U11 without firmware. ST on GPIO21. Items 10/21/24 are superseded by this path. **[verify]** the five source cases on the bench. |
| 36 USB 27 Ω | **FIXED** | R162/R163, 27 Ω 0402 at U7 (USB_DP_MCU/USB_DM_MCU); J1 and D6 stay on USB_DP/USB_DM. |
| 37 PD default | **FIXED** | CFG1 10k pull-up to the CH224K's own 3.3 V (5 V request before any controller, WCH Table 5-2); Q3 pulls it low for 9 V (PD_REQ_9V, GPIO27, gate pull-down); CFG2/CFG3 grounded, so 9 V is the highest code the pins can form. Firmware ceiling in item 19 is now also copper. |
| 38 input caps | **FIXED** | 10 µF 50 V 1210 across U11's VIN; 4.7 µF 0603 at each TLV62569 VIN (U13/U14/U16). Island profiles place them on the VIN flank. |
| 39 PSRAM power-up | **FIXED** | PUDC_B strapped high (no configuration pull-ups; every line that needs a level already had its resistor). Per PSRAM: CE#_MEM 10k up to +1V8_IO, SCK/IO0-3_MEM 10k down. Gateware obligation: 150 µs wait and the 66h/99h reset pair (ref/psram.md). |
| 40 COUT qualification | **open, now tracked** | `budget.py` sums the direct output capacitance per regulator against each datasheet's validated figure: U12 221 µF, U13 103 µF, U14 113 µF, U15 507 µF, U16 50 µF are beyond it. Bench qualification (start-up, load step per jumper position) before fabrication sign-off; table in ref/power-budget.md. |
| 41 1.8 V switch | **FIXED** | U23/U24 are TPS22953DSQR: BIAS from +3V3, input 0.7 V to VBIAS, reverse blocking while off, CT 1 nF. No programmable current limit; the 500 mA PINV fuses are the overload protection. |
| 42 controller pins | **FIXED** | SPI1 for the flash bus (SCK 10, TX 11, RX 12, CSn 9; FD2 13, FD3 7 by PIO for quad), I2C1 SDA 14 / SCL 31, UART0 TX 32 / RX 33, EXT_FAULT 34. Verified against the RP2350 pin-function table (Zephyr `rpi-pico-pinctrl-common.h`, generated from the datasheet). |
| 43 slave serial | **documented** | No slave-serial path exists or is promised: M[2:0] are 001 in copper; volatile loading is JTAG through U20; MultiBoot addressing and the W25Q256 address mode are called out in ref/supervisor-flash.md. |
| 44 island ownership | **FIXED** | `islands.py`: the anchor a part's design.py group names wins, and a part parked in another island is reclaimed when its group names the run's anchor. Groups renamed `U1 PSRAM{n} series termination`, `U1 SDRAM clock source`, `X4 system clock`. Applied (owner's go-ahead): R104–R127 and R151 are in U1's island at its escape, X4/R147/C246 are one island, Q2's parts are gone. |
| 45 microSD access | **decided** | Access from above: card travel plus 12 mm finger room kept clear of tall parts, shield/enclosure cut-out over it, no edge opening (floorplan.md). Check with J72/J2 populated before freezing. |
| 46 source envelope | **FIXED (tool), contract set** | `budget.py` models recovery / light / full modes per source profile with the U26 and U34 limits: a USB 2.0 port carries recovery only; light fits any Type-C ≥ 1.5 A or PD 9 V; full export fits J50 only (2.05 A against U26's 1.7 A minimum on PD). Inductor peak current is now checked (all pass). Firmware must ration EXT_EN by source. |
| 47 gate | **FIXED** | `gate.py` prints `GATE electrical` and `GATE mechanical` separately; the exit code follows the electrical gate, `--strict` adds the mechanical one. Today: electrical PASS, mechanical FAIL (B3 open). |
| 48 stale documents | **FIXED** | user-manual.md (pin tables, connector bodies, AUX instead of per-slot selectors, 21 V input, slot sides), floorplan.md (current plan header, microSD contract, historical top-edge section), network.md (bank 35), decoupling.md (groups), supervisor-flash.md (start-up order, no slave serial), psram.md, power*.md, extension-ux.md, island-layouts.md, status-leds.md, gameboy-extension.md, jlcpcb-import-checklist.md. |
| 49 J1 holes | **FIXED** | odin copy of the KiCad footprint with A1/A12/B1/B12 shortened to 0.6 × 1.15 mm on the hole side: 0.31 mm hole-to-copper (rule 0.25, JLC NPTH-to-track 0.20). DRC: 0 errors. **[verify]** against the HCTL drawing (LCSC serves it only through a browser). |
| 50 telemetry | **FIXED** | MON_1V8 reads +1V8 (VCCAUX, after FB1); ADC6/ADC7 read VCCIO_1/VCCIO_2 so the jumpers are sensed. +1V2_MGT is the one unmeasured rail (no GTP load in rev A; U16 has no PG). |
| 51 key posts | **FIXED** | city.py maps MK76/MK77 to J7/J8; an off-board post whose row is on the board goes onto the board at position 1 of that row, a post on the board whose row is a planned block joins the block at the same offset. Applied (owner's go-ahead): MK71/MK72 stand one pitch before J56/J65 on the board, MK76/MK77 ride with J57/J58 at the top edge; slots G, H, L and M pass `place.py --check`. Consequence to decide: the zero-gap contract makes the KiCad courtyards of each post and its neighbouring rows overlap by about 0.5 mm (10 DRC courtyard errors; the plastic bodies touch but do not overlap). Either a documented courtyard exception for the posts, or more than 20.32 mm per zone. |

Not changed on purpose: the unused GTP quads stay powered (the audit's
optional simplification), the TPS22950C stays on U21/U22, and the hand
placement inside the outline. Same day, on the owner's go-ahead: every
staged footprint islanded (X4, U34, Q3, U11, U13, U14, U16, U7, U2–U5, U23,
U24, U8, Y1, U1 extended with the source resistors), the city re-planned
and applied, the four key posts placed. Remaining owner work: the post
courtyard decision above, the six hand-placed posts A–F that `place.py`
flags, compaction of the city onto the board, routing, the bench items
(COUT, U34 source cases, power-down timing) and the J1 drawing check (LCSC
refuses non-browser access).

---

# Part IV — independent re-audit after corrections, 2026-10-29

## Re-audit verdict

**Most corrections are present and electrically coherent, but the schematic
still needs three corrections before committing a prototype PCB:** U34's
overvoltage threshold permits the 5 V rail outside its loads' operating
range; connecting J50 does not relieve USB of the 5 V load; and U6's flash
chip select lacks its required pull-up. Four additional P2 findings cover
source-current detection, load-switch support and the applied city plan.

Baseline: `9dd5fa85e318972e9969e3accb2eaf53ae8f3831`, compared with the
previous audit's `82cb093`. This review checked the changed generator,
schematic/netlist, all actual PCB pin nets, island memberships and positions,
the current city preview, and the cited manufacturer requirements. The
correction-status table above was treated as a claim to verify. No circuit,
placement, routing or generator was changed. Unrouted staging remains
appropriate to this phase. P1/P2/P3 retain the definitions in Part III.

Evidence, baseline hashes, relevant pin connections, source-case calculations,
DRC pairs and selected pad coordinates are saved in
[reaudit-2026-10-29.json](ref/board-review/reaudit-2026-10-29.json).

| Independently reproduced check | Current result |
|---|---|
| Design model versus PCB pads | 544 parts / 544 footprints; **0 pin-net mismatches** |
| Schematic export versus stored netlist | Matches |
| Allocation versus XDC and gate top | Matches |
| Parts-role coverage | 544/544; 0 problems or gaps |
| ERC / schematic parity | 0 errors, 2 allowlisted temperature-diode warnings / 0 differences |
| Assembly / copper | All footprints front; 8 copper layers; 0 tracks, 0 vias |
| Footprint origins | 66 inside the outline, 478 staged outside |
| DRC | **10 courtyard errors**, 298 warnings, 499 reported unconnected items; no remaining J1 hole-clearance errors |
| Mechanical checker | **Fails with 10 findings**: four lattice/row findings and six A–F key-position findings |
| Gate | Electrical PASS; mechanical FAIL; ordinary exit code 0, as now explicitly documented |
| Deep FPGA signal balls | 80 at depth >=7: 17 inherent, 63 classified as allocation choices |

The electrical gate now reports its scope honestly. Its PASS establishes
consistency and the checks it implements; the analogue issues below remain
outside those checks.

## Verification of the earlier corrections

| Earlier item | Independent disposition |
|---|---|
| 34 VCCO/VCCAUX sequencing | **Original indefinite firmware-dependent state removed.** U11 automatically starts; U14 EN is tied to its input. Keep the DS181 rail-ramp and power-down waveform check open. A load estimate is not a guaranteed discharge path. |
| 35 USB backfeed | **Q2 body-diode defect removed.** U34 is correctly pinned and provides the intended reverse-blocking topology. Its threshold and source-priority implementation need items 52–53. |
| 36 USB termination | **Verified.** The fitted pair is **R170/R171**, 27 ohm, between the connector/ESD nets and U7. The correction table's R162/R163 are actually U34 divider resistors. Final placement must keep the pair at U7. |
| 37 PD default | **Verified topology.** CFG1 is pulled to PD_VDD, Q3 has a gate pull-down, and CFG2/CFG3 are grounded: default 5 V, asserted request 9 V. No higher digital code is available. This proves voltage selection, not available current. |
| 38 Converter input caps | **Schematic and ownership verified.** C267 is 10 uF/50 V at U11; C268–C270 are 4.7 uF at U13/U14/U16, in their respective islands. Preserve short VIN/GND loops during compaction. |
| 39 PSRAM startup | **Original conflict removed.** PUDC_B is high; all four memories have CE pull-ups and five clock/data pull-downs on their memory-side nets. The 150 us wait/reset sequence remains a gateware obligation. The global strap change also exposes item 54. |
| 40 Regulator COUT | **Still open, now tracked.** Direct sums agree with the report. U11 also has **81.7 uF downstream of U34**, in addition to its direct 66 uF; the mux does not establish control-loop isolation. Qualify the complete network, jumper choices, effective capacitance and ESR. Exceeding an example's capacitor range is a qualification gap, not proof of instability. |
| 41 Switch operation at 1.8 V | **Voltage-margin defect removed.** TPS22953 BIAS is +3V3 and the selected rails are within its input range. Support-pin and fault-coverage conditions remain in item 56. |
| 42 Native controller peripherals | **Verified against the RP2350 function table.** SPI1 SCK/TX/RX = GPIO10/11/12, CSn = GPIO9; I2C1 SDA/SCL = GPIO14/31; UART0 TX/RX = GPIO32/33. Quad flash still needs the documented PIO handling. |
| 43 Slave serial | **Closed by scope decision.** Fixed master SPI and volatile JTAG loading are now the contract; no copper change is required for that decision. |
| 44 Island ownership | **Ownership fixed.** R104–R127 and R151 belong to U1; X4/R147/C246 are together and merged into U1; U8/Y1 are back with U7; Q2 is gone. Correct membership does not establish the final source-termination distance or clock-side placement; see item 58. |
| 45 microSD access | **Design choice documented, mechanical proof pending.** Above-board card travel and 12 mm finger space must survive compaction and the populated shield/enclosure arrangement. |
| 46 Source envelope | **Substantially improved, incomplete.** The model now distinguishes modes and hardware limits. It omits the mixed-source case in item 53 and relies on unavailable source information in item 55. Further model limits are listed below. |
| 47 Gate scope | **Verified fixed.** Separate electrical/mechanical verdicts and `--strict` remove the earlier ambiguity. |
| 48 Documentation | **Partly fixed.** Main pin maps are improved. The manual still calls the network edge “top” while the current city puts it below U1, and still offers full export on PD9 despite the budget rejecting it. `floorplan.md` still describes a left-side X4 that is now above U1. |
| 49 J1 clearance | **DRC defect fixed; footprint qualification pending.** The custom pads clear the holes. The shortened land pattern still needs comparison with the HCTL drawing; the public PDF redirects to a JavaScript viewer and direct retrieval was denied in this review. No manufacturer-pattern match is claimed. |
| 50 Telemetry | **Verified.** MON_1V8 senses the post-FB1 VCCAUX rail; ADC6/7 sense both selected VCCIO rails. The explicitly unmeasured, unused-GTP 1.2 V rail remains an accepted limitation. |
| 51 Key posts | **Reference/ownership correction verified; mechanical closure incomplete.** MK76/MK77 follow the 5 V buses, and G/H/L/M pass the individual key-offset test. However, **J7/J57/MK76 still fails the signal-to-power-row lattice check**. This is separate from the six A–F key failures. See the mechanical disposition below. |

The native-peripheral cross-check uses the
[Raspberry Pi RP2350 datasheet](https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf).
USB and local regulator placement remain governed by the
[Raspberry Pi hardware guide](https://datasheets.raspberrypi.com/rp2350/hardware-design-with-rp2350.pdf).

## 52. P1 — U34 hands off above the downstream 5.5 V operating limit

**Entities:** U34 OV1, R164 = 100k, R165 = 23.2k; U13/U14/U16 and the other
5 V consumers. See `tools/design.py`, U34 support network.

The rising trip is `1.06 × (1 + 100/23.2) = 5.629 V`. Using the specified
1.01–1.10 V comparator reference and assuming 1% divider resistors, the static trip
envelope is approximately **5.277–5.937 V**, before leakage and dynamics.
U34 selects the rising VBUS until this trip. At light load its output can
therefore exceed 5.5 V during a normal 5→9 V negotiation. The reverse
transition also needs checking. The TLV62569's operating maximum is 5.5 V;
its 6 V absolute maximum is not an operating allowance.
[TI TPS2121, sections 7.5 and 9.3.5](https://www.ti.com/lit/ds/symlink/tps2121.pdf),
[TI TLV62569, sections 6.1 and 6.3](https://www.ti.com/lit/ds/symlink/tlv62569.pdf).

**Required correction:** establish a handoff/clamp design whose worst-case
output stays within the downstream operating limits while accepting the
allowed 5 V input range. Include divider/comparator tolerances and source
slew. The advertised 5 us is a typical switchover figure, **not a guaranteed
OV-response bound**; the comments currently treat it as one. Scope both
negotiation directions after the schematic is corrected.

## 53. P1 — J50 does not take over the 5 V load while USB supplies 5 V

**Entities:** U34 PR1/CP2 dividers, D3/D4, J50; `budget.py::mode_rows()` and
the manual's simultaneous-input claim.

With both sources connected, PR1 is about 1.337 V at VBUS = 5 V and CP2 is
about 1.187 V at +3V3 = 3.3 V. OV1 has not tripped. Table 9-3 consequently
selects **IN1 = USB VBUS**, even if J50 supplies VSYS. This is a deliberate
result of the fitted dividers, not an uncertain handoff race.
[TI TPS2121, Table 9-3](https://www.ti.com/lit/ds/symlink/tps2121.pdf).

| Connected sources | Actual source of the +5V rail |
|---|---|
| USB 5 V alone | USB through U34 IN1 |
| USB 9 V alone | U11 through IN2 after OV1 trips; item 52 applies |
| J50 alone | U11 through IN2 |
| **J50 + USB 5 V** | **USB through IN1**, including downstream converters and +5V_EXT |
| J50 + USB 9 V | U11 through IN2; D3/D4 select the VSYS source |

The model's full J50 row assumes all loads come through D4. That assumption
fails in the highlighted case. Its own 5 V allowance is about 1.72 A at
the rail: a programming cable attached to a 500 mA computer port cannot
supply it, despite the bench supply being connected. U34's 2–3 A current
limit does not protect that source allocation.

**Required correction:** give the external input an effective way to take
the complete board load, or explicitly support and budget this hybrid
case with the USB load capped appropriately. Update the source-state
table and user contract together. The existing hardware has no MCU mux
select connection that firmware can simply toggle.

## 54. P1 — FPGA configuration-flash chip select has no startup pull-up

**Entities:** U6 pin 1, U1 P18/FCS_B, R22, U7 GPIO9, PUDC_B.

`FLASH_CS_B` connects only U1, U6 and R22; `SUP_FCS_B` continues through
R22 to U7. Neither net has a pull-up. The FPGA's internal configuration
pull-ups are now disabled, and its core remains off in recovery. The
controller does not provide a hardware-guaranteed high CS during the
flash supply ramp.

UG470 Table 2-4 explicitly requires an **external pull-up of at most 4.7k
to VCCO_14 on FCS_B**. Winbond also requires CS to follow VCC through
power-up/down. Add that bias at the flash/configuration bus and include the
controller's reset state in its sizing. This is a missing schematic part,
not a firmware initialization fix.
[AMD UG470, Table 2-4](https://docs.amd.com/v/u/en-US/ug470_7Series_Config),
[Winbond W25Q256JV rev Q, sections 4.1 and 9.3, manufacturer-authored PDF hosted by TI](https://e2e.ti.com/cfs-file/__key/communityserver-discussions-components-files/908/W25Q256JV-SPI-RevQ-02072025-Plus.pdf).

This finding is specifically CS. The fitted **IQ** ordering option has QE
fixed high, so the WP/HOLD pins' quad-I/O behavior does not independently
justify alleging two more missing control pull-ups.
[Winbond ordering information and section 7.1.4](https://e2e.ti.com/cfs-file/__key/communityserver-discussions-components-files/908/W25Q256JV-SPI-RevQ-02072025-Plus.pdf).

## 55. P2 — the source-current policy depends on information U7 cannot read

**Entities:** U18 CH224K, USB_CC1/2, PD_PG, VBUS5_ST; `budget.py::SOURCES`
and the generated power-budget instructions.

The budget says Type-C Rp is “read by the CH224K” and that firmware reads
the advertisement. CC1/2 connect only J1 and U18. U7 gets a voltage-request
control and **PG**, not a current/contract data interface. VBUS5_ST reports
the mux selection. These signals cannot distinguish 5 V/default, 1.5 A and
3 A capability, or establish a 3 A PD contract.

The WCH manual distinguishes the CH224K's resistor/logic configuration from
the **CH224A/Q** I2C interface that can report contract current. That newer
interface must not be attributed to the fitted K part.
[WCH CH224 manual 1 v2.1, overview, Table 4-2 and section 5.2.3, manufacturer-authored mirror](https://atta.szlcsc.com/upload/public/pdf/source/20250227/6D68A1393FFD6E9F0B2393231A5DDBA5.pdf).

**Required resolution:** provide observable source capability, or define a
conservative/user-declared power policy that works with the existing
signals. A successful voltage request alone cannot authorize the table's
current allowance. Retain the safe hardware 9 V ceiling if changing the
PD controller. Verify USB startup and the load allowed before enumeration
separately from the table's explicitly configured 500 mA case.

## 56. P2 — TPS22953 support and fault coverage are not fully closed

**Entities:** U23/U24 pin 7 PG, their CT/BIAS bypass networks, PIN V branches.

Both PG pins are marked unconnected. TI section 9.3.3 explicitly says to
**tie unused PG to ground for proper functionality**. Ground them, or use
them with the specified pull-ups in a deliberate reporting circuit.
[TI TPS22953, section 9.3.3](https://www.ti.com/lit/ds/symlink/tps22953.pdf).

The 1.8 V operating-range fix is valid, but the old aggregate current limit
and fault indication were removed. Four slots share each PIN V domain;
four 500 mA PTCs do not impose a 500 mA aggregate ceiling. `EXT_FAULT` now
connects U26/U21/U22, not U23/U24. With SNS tied to OUT, the switches also
have the documented automatic restart after an output-undervoltage fault.
Qualify that behavior with a shorted branch and the upstream shared rail;
do not assume a PTC necessarily trips before a base-board brownout.
[TI TPS22953, sections 9.3.4 and 9.4](https://www.ti.com/lit/ds/symlink/tps22953.pdf).

This tradeoff is acknowledged in the new extension document. The older item
25's blanket “fault isolation fixed” description no longer describes this
hardware. A 0.5 A software allocation remains possible, but is not enforced
by U23/U24. At the 1.8 V jumper setting the upstream source also supplies
VCCAUX, making this a meaningful fault test.

Before freezing these islands, shorten the CT and BIAS loops. The current
C272/C275 pad-to-CT distance is about 5.35 mm and C271/C274 to BIAS about
4.94 mm, with other parts occupying the intervening area. The profile name
“at pin” does not establish local placement. TI calls for CT and bypass
close to the device and a copper clearance beneath CT.
[TI TPS22953, section 12.1](https://www.ti.com/lit/ds/symlink/tps22953.pdf).

## 57. P2 — the regulator street is missing its new high-current junction

**Entities:** U11 → U34 → +5V → U14/U15/U16, the city `CRITICAL`/`DOORS`
rules, and U34's IN2 bypass.

The regulator row remains a sensible arrangement, but U34 is planned below
U7 on the far right. In the staged city, U11→U34 is about 111 mm and
U34→U15 about 94 mm; U11→U15 directly is only 21 mm. These are planning
distances, not final trace lengths. The important error is that the
planner still strongly attracts **U11 directly to U15**, while every ampere
of regulated +5V now passes through U34.

Move U34 into the upstream supply junction near U11 and the low-voltage
row, and reserve the actual U11→U34→loads copper path. Reassess its
connection toward J1 at the same time. IN2 has no bypass in U34's own
island; the documented plan borrows U11's capacitors, which only works if
the two become genuinely adjacent. TI calls for short, wide paths and
local bypass on IN1, IN2 and OUT.
[TI TPS2121, sections 11 and 12.1](https://www.ti.com/lit/ds/symlink/tps2121.pdf).

This is a relative-placement correction worth doing before city
compaction. Grouping the power converters into a street remains acceptable;
aligning the real supply path is what makes that street useful.

## 58. P2 — X4 returned to the power-door side instead of the SYS_CLK side

**Entities:** X4/R147/C246, U1 M21, `city.py::attach`, `SATELLITES`, `RESEAT`.

The latest satellite restoration recovered membership, but the actual PCB
puts X4 at `(759.38, 95.51)` above U1 `(760.00, 122.83)`. SYS_CLK is ball
M21 at `(752.50, 124.33)`, on the left side. R147's SYS_CLK pad is about
31.55 mm straight-line from that ball in this staged placement. The plan
explicitly labels the satellite **N side**, contradicting the floorplan's
left-side correction and placing the clock beside the power door again.

`attach()` averages shared supply pads along with the clock connection;
its result can be dominated by +3V3. The pin-specific `RESEAT` rule only
runs when its parts already belong to the host at planning time, so it
did not govern the separately restored X4 island in this plan.

Use the actual SYS_CLK pin to choose the side, independent of temporary
group state. Keep **X4, R147 and C246** together when applying that rule
(the current RESEAT list names only X4/R147). Put R147 at the oscillator
output and retain a quiet, short clock corridor toward M21. The distance
here flags the wrong neighborhood; it is not a claimed final SI failure.

## Remaining mechanical and qualification work

**The key-post correction is useful but has not proved the mating lattice.**
`place.py --check` still reports J5/J3 pad-lattice disagreement; the
J5/J55/MK69, J3/J53/MK65 and J7/J57/MK76 row-lattice failures; and the six
A–F key offsets. Passing G/H/L/M's individual position-1 check does not
close the row checks. Preserve the recorded above-board microSD access
volume while settling these connector positions.

The ten courtyard errors are six post-to-header pairs and **four
post-to-capacitor pairs**: MK71/C159, MK72/C161, MK76/C143 and MK77/C145.
The latter need their own clearance review; the zero-gap header-body
argument alone does not dispose of them. These are courtyard findings,
not demonstrated body intersections. Reposition the nearby capacitors or
justify each exception from actual body, lead and assembly clearances.
The full DRC pairs are in the evidence file.

**The budget is a better planning model, not a power qualification.** Its
recovery mode selects only RP2350/flash/U20 entries on +3V3, but X4 and the
PHY's 3.3 V supply/internal LDO remain physically powered. SDRAM standby,
other always-on circuitry and the controller's own regulator input power
also need a consistent recovery accounting. Reset is not a supply switch;
use reset/standby current evidence rather than the full-active figures or
zero. This does not prove recovery exceeds 500 mA; it leaves its guarantee
unproven. The light-mode 1.47 A estimate also has only about 30 mA margin
against a 1.5 A source before estimate/efficiency uncertainty.

`mode_rows()` additionally combines U26/U34 limits rather than checking
each path separately, and the new inductor calculation uses nominal L,
frequency and a 9 V input for the wide-input converters. Extend the checks
to each path and the 21 V/tolerance envelope before treating PASS as
qualification. The fitted inductors' nominal margins are a useful positive
result; no saturation failure was demonstrated here.

Keep item 40's complete regulator-network qualification and item 34's
power-down/ramp measurements open. Final FPGA XPE/load estimates, escape
trials, return paths, impedance geometry and prototype SI remain later
milestones. In particular, source-resistor membership in U1 does not
prove sufficiently short driver-side stubs after escape routing.

**Neighborhoods that still make sense:** all four PSRAMs now occupy the
bank-13 side; U13 remains beside bank 16 and the PHY; PHY/crystal/jack and
connector-side ESD ownership remain coherent; SDRAM is between its bank
14/35 escapes; the RP2350 still owns its flash and crystal. Keep these
relationships while correcting U34 and X4. The unused-MGT supply remains
a valid, optional simplification opportunity, not a new defect.

Address 52–54 first, settle 55–56 before freezing the schematic, then
repair 57–58 and the connector lattice while compacting. The earlier
architecture/bank-voltage conclusions remain supported within their stated
boundaries; the changes above are necessary to close the remaining gaps.


## Status of the Part IV findings, 2026-10-29

Corrected the same day, against `9dd5fa8`. Commits `cd74e9f` (schematic
and budget), `e243a09`..`dd31f75` (one island each: Q6, Q7, U34 twice,
J57, J58, U23, U24), `bb9ab7f` (city re-planned and applied). Gate
electrical PASS (parts 553, ERC 0, netlist/XDC/guide in step, parity 0);
DRC 8 courtyard errors (was 10); mechanical 9 findings (was 10). The
entries "Re-audit corrections, part 1 and 2" in `ref/rev-a-report.md`
carry the numbers.

| Item | Status | What changed |
|---|---|---|
| 52 U34 handoff above 5.5 V | **FIXED** | The handoff is decided by intent, not by a threshold: Q6 (BSS138) pulls PR1 to ground while PD_REQ_9V is high and, through D24 (1N4148W) into 470k/10 uF, for 2.4-7.2 s after it falls (Table 9-3: PR1 < VREF with CP2 ≥ VREF selects IN2). The rail is on U11 before the charger moves VBUS and stays there until VBUS is back at 5 V; a dead or resetting controller releases the request through R173 and the same hold covers the fall. During the negotiation the rail is U11 in dropout, about 4.5 V (AP63300 LDO mode), inside every +5V consumer's range; EXT_EN stays off until the request is settled. OV1 stays at 5.63 V typical as a fault backstop only; `design.py` now computes its 5.26-5.96 V worst case (reference 1.01-1.10 V, 1 % resistors) and refuses a build that exceeds the TLV62569's 6 V absolute maximum or rejects a 5.25 V USB 2.0 port. The 5 us figure is called typical where it appears. |
| 53 J50 + USB 5 V | **FIXED** | Q7 (BSS138) pulls PR1 to ground while VIN_EXT carries voltage (100k/33k before D4: on between 3.2 and 6.0 V, 2.2 V on the gate at the 9 V minimum, 5.2 V at 21 V). With J50 connected the whole board runs from J50 through U11, whatever is on USB. `budget.py`: the J50 row is also the J50 + USB row; each path (U34, U26) is checked against its own limit and the sum against the source. `user-manual.md`, `power-input.md`, `power.md` say so. |
| 54 FCS_B pull-up | **FIXED** | R203, 4.7k from FLASH_CS_B to +3V3 (UG470 Table 2-4; W25Q256JV CS# follows VCC). Sized with the controller's reset state: an RP2350 pad at reset has its pull-down enabled, which through R22 (33 ohm) leaves CS near 3.0 V [verify the RP2350 pad reset defaults]. |
| 55 source-current policy | **RESOLVED by policy, hardware option recorded** | No readable Rp: the CC lines go only to the CH224K, which has no data interface. The CH224A is pin-compatible but its I2C mode is the single-resistor mode, where register 0x0A can request up to 28 V (CH224 manual 1 v2.1, 5.2.3, Table 5-3), which would give up the 9 V ceiling by construction; not fitted. `budget.py` SOURCES now say what is observable: any 5 V source is a 500 mA port unless user-declared; a granted 9 V request (PD_PG) is a 15 W guarantee under the PD power rules [verify PD3 10.2], so light mode fits and full export does not; J50 is detected on MON_VSYS. Recovery is 0.21 A at 4.75 V: inside 500 mA, above the 100 mA an unconfigured USB 2.0 device may draw, stated as open (PHY, SDRAM, X4 and U20 sit on the always-on +3V3 with no switch). Hardware alternative if wanted: two dual comparators on CC1/CC2 at 0.66 V and 1.23 V into four spare GPIOs, through 1 M series resistors so Rd is not loaded. |
| 56 TPS22953 PG and fault coverage | **PG FIXED; coverage stated, bench open** | U23/U24 PG tied to ground (SLVSCT5D 9.3.3); the symbol pin typed passive so ERC does not call the tie a driver conflict. `extension-ux.md` and `power-input.md` now say plainly: no fault report from U23/U24, four 500 mA PTCs are not a 500 mA ceiling, automatic restart after an output undervoltage (9.3.4, 9.4); the shorted-branch test against the shared rail is a bench item. Islands U23/U24 re-applied with the TPS22953 profile: CT pin to its capacitor pad 1.43 mm (was 5.35), BIAS 1.60 mm (was 4.94). |
| 57 regulator junction | **FIXED** | C280, 1 uF at U34 IN2 (SLVSEA3F 11), innermost at pin 2 by profile rule; the 3 x 22 uF at U11 stay the bulk. `city.py`: U34 closes the top door row (U16, U15, U14, U34) on the USB side; CRITICAL pulls U11-U34 (6), U34-U15 (4), U34-J1 (2) replace U11-U15, so U11 sits above the row against the mux; Q6 and Q7 are satellites of U34 on its PR1 pin (same-side satellites now stack outward). U11 inside the row was tried both ways and rejected: at the right end it pushed U26 off J1, at the left end it pushed PSRAM U2 off the bank-13 side, which the audit asked to keep. Applied, in the 2.2x staged city: U11 to U34 45 mm (was 111), U34 to U15 40 (was 94), U34 to U14 23, U34 to U26 18; U26 kept its place at J1; the four PSRAMs stay on the bank-13 side. |
| 58 X4 side | **FIXED** | `city.py` SATELLITES take a deciding net (X4: SYS_CLK), so attach() uses the M21 ball alone, not the +3V3 pads; RESEAT lists X4, R147 and C246. Applied: X4 on U1's west side at the ball row, R147's SYS_CLK pad 22.7 mm from M21 in the staged city (was 31.6, north side, beside the power door). floorplan.md corrected. |
| mechanical | **PARTLY** | J7/J57/MK76 row lattice: `city.py` snaps the inboard L/M rows to the bus headers' 2.54 mm lattice (J57 is now 6 pitches below J7, MK76/MK77 at position 1 of their rows). J57/J58 re-applied with the slot-row profile change (PIN V fuse and 10 uF inboard, on the AUX fuse's row), which clears MK76/C143 and MK77/C145. Left to the owner (hand placement is authoritative): C159 and C161 on the board, 1.2 mm from MK71/MK72 (park them off the board and re-run J56/J65 with the same profile, or nudge them inboard by hand); the J5/J3 lattice (J5 sits 0.81 mm off J3's row); the A-F posts; the six post-to-header courtyard pairs are the zero-gap contract. |
| budget model | **FIXED as asked** | Per-path limits; inductor peaks at the 21 V / 5.5 V envelope with L at -20 % (all pass, U12 3.19 A of 6.8 A worst); recovery column per load with standby/reset figures (U33 MRAM added to the table); the pre-enumeration allowance stated as not met. |

Still open after this pass: item 40 (COUT beyond the validated range on
U12-U16, bench), item 34 (DS181 ramp and power-down waveforms), the
U23/U24 shorted-branch test, the J1 land pattern against the HCTL drawing
[verify], the pre-enumeration current, the A-F posts and the J5/J3 lattice,
compaction and routing.

---

# Part V — final practical audit, 2026-10-29

## Final practical verdict

**The schematic and district plan are a reasonable basis for detailed
placement and a first prototype. The previous three P1 circuit findings
are corrected. I found no additional confirmed schematic blocker.**

This is the verdict at `6ad8068`, including the new Q6/Q7 mux controls and
the `districts` city plan. It supersedes the older audit's open/closed
language. It is approval to advance the design to placement, not a claim
that the present staged board is ready to order. No hardware or placement
was changed during this review.

The earlier reviews mixed schematic defects with normal layout and
prototype work too readily. In particular, a nominal capacitor sum above
a datasheet example, or a few millimetres in an unfinished island, does
not establish a faulty circuit. Those points are treated proportionately
below.

| Reproduced check | Result |
|---|---|
| Design model versus every connected PCB pad | **553 parts, 553 footprints, 0 mismatches** |
| Schematic netlist, XDC, gate top and parts guide | Match their generators; 553/553 roles covered |
| ERC / schematic parity | **0 errors / 0 differences**; the two intentional temperature-diode warnings remain |
| DRC | 8 courtyard errors, 297 warnings; a separate error-only run also finds just those 8 courtyard errors |
| Mechanical checker | 9 findings: 3 lattice/row findings and 6 A–F key-position findings |
| Gate | Electrical PASS, mechanical FAIL |
| Stage | 66 origins on-board, 487 staged outside; all front-side; no tracks or vias |

The old phase-report note about an L1/R8 copper-clearance error was not
reproduced by either current DRC run; it is not counted as another blocker.
The saved evidence is
[final-audit-2026-10-29.json](ref/board-review/final-audit-2026-10-29.json).

## Previous findings: final disposition

| Item | Verdict now |
|---|---|
| 52 Mux overvoltage during negotiation | **Original normal-transition defect addressed.** Q6 pulls PR1 low during the 9 V request and holds it afterward; the mux selects U11 rather than waiting for OV1. The circuit is sensible for the intended startup sequence. Confirm transitions and controller resets on the prototype. |
| 53 J50 plus USB 5 V | **Fixed.** Q7 senses VIN_EXT before D4 and overrides PR1. At the valid 9–21 V J50 input, it selects U11 even with USB connected. |
| 54 Flash chip-select bias | **Fixed.** R203 is fitted, 4.7k from FLASH_CS_B to +3V3. |
| 55 Source-current policy | **No automatic Type-C current claim remains, but the source-qualification wording still needs the clarification below.** This can be resolved in policy/firmware without a new power-tree design. |
| 56 TPS22953 support | **Pin/bypass corrections verified.** Both PG pins are grounded. CT and BIAS pad distances are now about 1.43 and 1.60 mm respectively: reasonable. The accepted PTC-based fault behavior is a prototype test, not an unfinished pin-map fix. |
| 57 Power junction placement | **Fixed at planning level.** U34 is in the power district, C280 supplies its local IN2 bypass, and the planner follows the actual U11→U34→loads path. |
| 58 Oscillator side | **Fixed.** X4/R147/C246 are together west of U1, selected from SYS_CLK/M21 rather than shared supply pins. |

The mux selection agrees with
[TI TPS2121 Table 9-3](https://www.ti.com/lit/ds/symlink/tps2121.pdf).
Q6/Q7 are switching a small divider current, not the board load; their
threshold/headroom is appropriate to that task.
[onsemi BSS138L datasheet](https://www.onsemi.com/pdf/datasheet/bss138lt1-d.pdf).

The long Q6 hold is a reasonable practical solution. Its exact “2–7 s”
value is an estimate, not a precision timer specification. USB PD allows a
25–35 ms preparation interval before a fixed-voltage transition, and a
normal SPR voltage transition settles within 275 ms of transition start.
Check the actual gate charging and release waveforms; there is no reason
to redesign this circuit merely because the RC timing is approximate.
[USB-IF PD R3.2 v1.1, section 7 timing parameters, author-issued specification mirrored at HWWiki](https://www.hwwiki.net/lib/exe/fetch.php?media=%E6%A0%87%E5%87%86%3Ausb%3Apd%3Ausb_pd_r3_2_v1.1_2024-10.pdf).

## What still merits action

**Finish the extension connector geometry before ordering.** J5/J3 still
have different pad lattices, J5/J55/MK69 and J3/J53/MK65 still fail their
row tests, and the A–F keys remain out of position. Those errors affect
whether an extension physically plugs in. They are real, expected
placement work at the present stage.

Six of the eight courtyard errors are the acknowledged zero-gap
post/header arrangement. A justified courtyard exception is reasonable
where the real bodies fit; it does not warrant expanding the board just
to satisfy a library outline. The other two are MK71/C159 and MK72/C161:
move/check those capacitors when legalizing the connectors. No body
intersection or copper short was demonstrated by these courtyard reports.

**Make source qualification explicit in firmware and the power contract.**
Two current statements are too strong:

- **MON_VSYS alone does not identify J50.** USB-PD at 9 V and J50 near
  9 V can produce the same VSYS voltage; with USB attached, PD_PG and the
  mux status can also agree in those two cases. Before authorizing the
  J50-only full-export budget, require a declared external supply or a
  source test, for example requesting USB 5 V and confirming that VSYS
  remains in the external-input range after settling. No additional
  detector is necessary if that policy is acceptable.
- **A granted 9 V request is not universally a 15 W guarantee.** Managed
  multi-port sources may offer 9 V at a reduced available power, and
  optional PDOs also exist. The fitted CH224K still does not report that
  current to U7. For this prototype, specify a qualified source providing
  at least 9 V / 1 A for the present board-only estimate of about 0.83 A,
  with practical headroom, and keep full export on the qualified J50
  supply. Do not infer the 1.67 A budget solely from PD_PG.

The second point follows from the actual source rules, including the
managed-port cases in Table 10-3; it does not require designing around
every possible charger. A stated, qualified supply requirement is enough.
[USB-IF PD R3.2 v1.1, sections 10.2 and 10.2.3, Table 10-3](https://www.hwwiki.net/lib/exe/fetch.php?media=%E6%A0%87%E5%87%86%3Ausb%3Apd%3Ausb_pd_r3_2_v1.1_2024-10.pdf).

**Keep the known USB cold-start limitation visible.** The approximately
0.21 A recovery estimate exceeds legacy USB 2.0's 100 mA allowance before
configuration. This does not mean every computer port will fail; many
will power the board. It does mean universal bus-powered startup has not
been established. For an engineering prototype, a qualified port or J50
is a practical operating restriction. If guaranteed startup on arbitrary
legacy computer ports is a release requirement, the always-powered load
needs reduction or switching before that guarantee can be made. This is
already acknowledged in the budget, rather than a new hidden defect.

## District and island verdict

**The regulator street is acceptable.** It now contains the real mux
junction, with U11/U12 together in the input district and U13 beside the
PHY. U11→U34 is about 30 mm in the staged city, versus 111 mm in the old
plan. These distances are not final copper lengths. During compaction,
prioritize each converter's switching loop, then its output-capacitor
connection to the rail, and preserve a wide U34 output corridor to the
low-voltage row. The row itself does not need further rearrangement for
appearance or marginal centroid improvements.

| District | Practical assessment |
|---|---|
| Four PSRAMs in a 2×2 block | Good use of the bank-13 neighborhood. Source resistors stay with U1; shorten the actual escapes when routing. |
| FPGA clock | Correct west-side ownership and direction now. The staged distance is not a reason to reopen item 58. |
| RP2350, its flash and crystal | Correct grouping. Preserve the local regulator/crystal sub-islands when moving the whole controller block. |
| USB input and converters | Coherent: J1/U26/U18 together, U34 at the power row, U11/U12 adjacent. Reserve the VSYS route from the separate J50 entry. |
| PHY, crystal, jack and 2.5 V regulator | Sensible arrangement; the PHY is now directly above its jack. Keep MDI pairs clear of switching circuitry. |
| Configuration flash and MRAM shelf | Acceptable. Keep the configuration SPI run direct; there is no benefit in pulling the much wider SDRAM bus into this shelf. |
| SDRAM below U1 | Reasonable compromise between its bank-14 and bank-35 connections. Actual clock/data routing decides timing. |
| PIN V controls in opposite service corners | Reasonable relative to their separate banks and slot columns. They need wide supply distribution, not side-by-side placement. |
| JTAG corner and LED dashboard | Sensible access/ownership choices; both have low placement priority compared with memory and power loops. |
| Inboard microSD | Accepted above-board access choice. Preserve the already documented travel/finger space. |

The 2.2× city is a planning diagram. Fitting connector bodies and routing
corridors into the real 100×100 mm outline still has to be done. That is
the next design phase, not evidence that these neighborhoods are wrong.
The new district names should be reflected in the current-plan paragraph
of `floorplan.md` eventually; stale “best” wording is documentation cleanup.

## Prototype checks, rather than another schematic redesign

Use the first board to answer the following concrete questions:

1. **Mux:** capture VBUS, +5V and the hold signal through 5→9 V, 9→5 V,
   controller reset, and USB/J50 connection changes. Confirm handoff
   occurs before VBUS rises and lasts through its return.
2. **Regulators:** check startup and load steps on the assembled output
   networks, especially the large 1 V FPGA capacitor bank, at relevant
   input voltages and jumper choices. Do not remove required FPGA
   decoupling to match a regulator's example schematic.
3. **FPGA supplies:** capture +3V3/VCCAUX ramps and power-down, including
   recovery/reset. The hardware no longer leaves VCCAUX waiting on
   firmware; verify the resulting waveforms.
4. **PIN V faults:** short a protected extension branch under a controlled
   supply and observe the shared rail/restart behavior. A base-board
   reset is possible under the documented PTC-only contract; decide
   whether that behavior is acceptable from the measurement.

## Minor points that do not block progress

- U16's approximately 50 uF nominal sum versus a 47 uF example is not an
  independent defect. Part tolerance and effective capacitance are larger
  effects. Include it in ordinary bring-up, without a special redesign.
- The corrected CT/BIAS placement is adequately local for this stage.
  There is no useful audit action in shaving fractions of a millimetre.
- BOOTSEL button distance is an access/low-speed routing choice; it is
  not equivalent to moving the QSPI flash away from U7.
- A small series resistor in D24's charging path would be sensible
  cleanup to limit the 10 uF capacitor's initial GPIO charge pulse. The
  present waveform deserves observation; no damaging current or failed
  negotiation has been demonstrated. RP2350 drive-strength settings are
  not hard current limits.
  [Raspberry Pi RP2350 datasheet, section 14.9.4.1](https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf).
- J1's modified land pattern still deserves the usual connector-drawing
  comparison before fabrication. Its drill-clearance error is fixed; the
  outstanding comparison is ordinary footprint review, not a renewed
  electrical blocker.

**Advance to placement.** Resolve the physical connector fit before PCB
ordering, implement the conservative source policy, and use prototype
measurements to close the remaining analogue questions. The current
evidence does not justify another broad architectural redesign.
