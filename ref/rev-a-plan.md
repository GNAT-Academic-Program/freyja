# Freya rev A: rebased audit and plan

Rebased on `bf28a92` (2026-10-23). This supersedes the "audit and
implementation plan for the IDE agent" written against `4eea232`.

**Status 2026-10-23:** phases A0, A1, A2, A3+A4, A4b (system clock, an
audit gap found in A5), A5 and B1 are done, one commit each, numbers in
`ref/rev-a-report.md`. B2 (snapshot, `load_pcb.py`, compare, zero moves)
was performed inside every phase that touched the netlist. B3 to B5 are the
owner's hand placement and routing in KiCad; `tools/placement.py` holds the
proposed top-edge positions for the three jacks and J50, `floorplan.md` and
`ref/decoupling.md` the placement rules, and `python3 tools/gate.py` the
checks to keep green. Every number
below was measured on `bf28a92`; every datasheet value carries its table.

Goal is unchanged: a board that configures, runs NEORV32, exposes the
extension slots, and has `ETH`, `LINK P`, `LINK Q` on the top edge. Nothing
else new.

## 1. Baseline on `bf28a92`

| Item | `4eea232` (old plan) | `bf28a92` |
|---|---|---|
| Footprints in PCB | 498 | 520 |
| Inside outline / staged outside | 194 / 304 | 209 / 311 |
| On B.Cu | 96 | 0 |
| Tracks / vias | 0 / 0 | 0 / 0 |
| Layers | 6 | 6 |
| ERC (`tools/check_erc.py`) | 1 error (`SUP_SWCLK`) | **pass**, only the 2 allowlisted DXP/DXN warnings |
| DRC errors | 688 violations total | 49 errors, 343 warnings, 499 unrouted |
| Schematic parity | 2 (SFP `CAGE` pin) | 0 |
| Signal balls / depth 7 or more | 173 / 58 | 173 / 58 (allocation unchanged) |

Parts per sheet on `bf28a92`: FPGA 121, Power 151, Memory 34, Board Controller 63,
Slots 98, Fast Links 53.

The 49 DRC errors on `bf28a92` are all placement collisions, none electrical
design errors:

- AUX parts C236, C237, C238 and R96 sit on top of U9/U10 (11 shorts, 11 mask bridges, clearances).
- C185/C186/C192 overlap, J57/F4 overlap, C158/F31 clearance.
- J60/J61/X2 pad clearances. These go away with Fast Links.
- J1 USB-C: 4 `hole_clearance` errors, inside the footprint itself (pad to its own NPTH).

## 2. What the new work already settled

- **Extension connectors (old A1): done.** J3/J5 are single WingTAT 2x32
  through-hole bodies, A to D right and E to H left. Signal rows are
  `IO IO GND`, exactly 4 GND per section, asserted in `design.py`. Each zone has
  a 21 mm long grounded post (MK65 to MK72, MK76, MK77) at position 1 and a 1x7
  female power socket at 2 to 8. That is the decided key arrangement, modelled
  as a separate part. The old plan's "remove every MK part" is obsolete. Left
  to do: place J3/J5 at the contract y = 50.0 (a hand move, see
  `ref/kicad-validation.md`).
- **Decoupling is off B.Cu.** 57 FPGA-rail capacitors are inside the outline
  on F.Cu and 26 are staged outside. They are still the old 96 x 100 nF +
  14 x 4.7 µF set, which A2 replaces.
- **`load_pcb.py` now keeps placement.** Existing references keep position,
  rotation and side; only new references go to the import band. The last sync
  moved 0 of 500 footprints (`tools/check_positions.py` snapshot/compare).
  Use it with a snapshot before and a compare after. **Still forbidden:**
  - `gen_pcb.py` without `--rules-only`.
  - `place.py` without `--check`. Its step 4 still flips decoupling to B.Cu,
    which contradicts single-sided assembly; remove the rule in A2.
  - `place.py --stage`.
- **New since the old plan:**
  - The AUX lab rail: U28 LM5157 SEPIC, 9/12/15/24 V jumper selector, J66/J68
    raw input, 10 x 1.1 A branch PTCs.
  - +12V removed.
  - Extension power behind TPS22950 switches.
  - VSYS ceiling 21 V.

## 3. Corrections to the old plan (checked against the attached PDFs)

### RTL8211F (datasheet rev 1.7)

| Old plan says | Datasheet says |
|---|---|
| Inductor list in Table 50 | Table 50 is the EEE wake-error register. Table 8 only says 2.2 or 4.7 µH; the approved list is in the separate *RTL8211F Series Layout Guide* (§9.1). |
| Wait 30 ms after reset (Table 5) | Table 5 gives the 10 ms low time only. §7.17 (revised in 1.7): wait at least **72 ms** before the first MDIO access, not counting the 1.0 V rise. |
| Crystal load from Table 54 §10.3 | Table 54 is absolute maximum ratings. Crystal is **Table 56**: 25 MHz, ±50 ppm including caps and aging, ESR ≤ 50 Ω, drive ≤ 0.5 mW. No load capacitance is given; it comes from the crystal's CL. |
| RSET value "from the reference schematic section" | This datasheet has no reference schematic and no RSET value. Get the Realtek RTL8211F reference design and cite it. |
| Every strap 4.7 k to `DVDD_RG` | Only the RXD straps go to DVDD_RG (Table 11: PLLOFF, TXDLY, RXDLY). `CFG_EXT` and `CFG_LDO[1:0]` go **to 3.3 V** (Table 11, §7.8). LED pins are 3.3 V pins. |
| LED wiring "as the reference schematic shows" | §7.9 Figure 5 fixes it: a pin strapped high is active-low (LED + 510 Ω to 3.3 V), strapped low is active-high (LED + 510 Ω to GND). With `CFG_EXT` = 1, `CFG_LDO1` = 0, `CFG_LDO0` = 1: LED0 and LED1 are active-low, LED2 is active-high. |
| (not mentioned) | `PLLOFF` strap on RXD2, pin 23: every config pin needs an external pull (§7.8). Pull it down (PLL keeps running in ALDPS). |
| (not mentioned) | `INTB` pin 31 is open drain and needs a pull-up. `CLKOUT` pin 35: leave floating; it outputs 125 MHz by default (PHYCR2 bit 0), so gateware should clear it. |
| `PHYRSTB` from bank 16, 10 k pull-down | `PHYRSTB` is a 3.3 V pin (Table 58 note: pins not listed stay at 3.3 V; VIH 2.0 V). LVCMOS25 VOH min is about VCCO − 0.4, which can fall just below 2.0 V. Also PUDC_B is strapped low, so the FPGA's internal pull-up is on during configuration and fights a 10 k pull-down. **Put `PHY_RESET_N` and `PHY_INT_N` on a 3.3 V bank (13).** Use a 1 k pull-down on reset (stays below 0.8 V against the worst-case internal pull-up; read the IRPU maximum from DS181 in A3, about 330 µA at 3.3 V) and a 4.7 k pull-up to +3V3 on INT. |

Confirmed as the old plan has them:
- Pin numbers in Tables 1 to 9.
- `CFG_EXT` high with `CFG_LDO` = `01` gives 2.5 V external I/O (§7.8).
- `TXDLY` (RXD1) and `RXDLY` (RXD0) high.
- PHYAD bits: PHYAD0 = RXD3, PHYAD1 = RXC, PHYAD2 = RXCTL. Address 1 means only RXD3 pulled up.
- MDIO 1.5 k pull-up (§7.11.2) to the I/O supply. MDIO and MDC follow `DVDD_RG` (Table 58).
- MDI internal termination (§7.7).
- `REG_OUT`/`LDO_OUT` feeds only DVDD10/AVDD10 (§9.1, §9.2).

Power sequence (Table 53 note 5, Case II): `DVDD_RG` comes from +2V5, which the
supervisor enables after +3V3. That is allowed only if `PHYRSTB` stays low
until +2V5 is up. The pull-down on reset provides that, so keep it.

`ETH` jack: confirm the part is a 4-pair 1000BASE-T integrated-magnetics jack.
Several HanRun HR9111xx parts are 10/100. The magnetics centre-tap connection
comes from the Realtek reference design, not from this datasheet.

### UG483 v1.14

- **Wrong table.** Table 2-1 covers Spartan-7. The XC7A100T in FGG676 is
  **Table 2-2**. Artix-7 has no capacitors inside the package (p. 14), so these
  board capacitors are the only high-frequency decoupling.
- **Counts:**
  - VCCINT: 1 × 330 µF, 6 × 4.7 µF, 8 × 0.47 µF.
  - VCCBRAM: 1 × 100 µF, 2 × 0.47 µF.
  - VCCAUX: 1 × 47 µF, 3 × 4.7 µF, 5 × 0.47 µF.
  - VCCO bank 0: 1 × 47 µF.
  - Each other bank: 2 × 4.7 µF, 4 × 0.47 µF, plus 1 × 47/100 µF per group of up to four banks on one voltage (note 3).
- **Totals on this board.** Banks 13, 14, 15, 16, 34, 35 and four VCCO nets
  (+3V3 for 13/14/35, +2V5, VCCIO_1, VCCIO_2):
  - 15 + 3 + 9 + 1 + 36 + 4 = **68 capacitors**, not "20 to 40".
  - That replaces 110, so the net change is −42, not −80.
  - MGT rails are not in Table 2-2; they come from UG482.
- **Packages are Table 2-5**, not 2-3:

  | Value | Package | Type | ESR |
  |---|---|---|---|
  | 330 µF | D/7343 | tantalum T520V337M2R5ATE025 or NbO | 5–40 mΩ (100 mΩ NbO) |
  | 100 µF / 47 µF | 1210 | ceramic X5R/X7R | 1–40 mΩ |
  | 4.7 µF | 0805 | ceramic | 1–20 mΩ |
  | 0.47 µF | 0603 | ceramic | 1–20 mΩ |

  A ceramic in place of a tantalum loses about 50 % effective capacitance (p. 23).
- **VCCBRAM shares +1V0 with VCCINT** (`tools/gen_sch.py:22`). Keep both groups
  as listed; consolidating is allowed only if ESR and ESL stay equivalent (p. 24).
- **Placement** (p. 24, Figure 2-1): within two electrical inches of the load;
  vias butted to or beside the pads; no shared vias; no trace between pad and
  via. The old plan's "0.47 µF within 12.7 mm" is stricter and fine.

### 7-series clocking

Every 7-series bank has **2 MRCC + 2 SRCC pairs**, not 4 + 4. In bank 16 these
are L11 (SRCC), L12, L13 (MRCC) and L14 (SRCC). RGMII `RXC` plus the two
link receive clocks use 3 of the 4. A single-ended clock uses the P side and
takes the whole pair.

### UG470 v1.17

- **Mode-pin strap resistors are too high.** `CFG_M0/M1/M2` use 4.7 k
  (`design.py:279`). UG470 Table 2-4: "directly, or via a ≤ 1 kΩ resistor".
  Change them to 1 k.
- **Checked and fine:**
  - PROGRAM_B and INIT_B 4.7 k pull-ups (≤ 4.7 k).
  - DONE 4.7 k plus the internal 10 k, driving the Q4 LED.
  - PUDC_B 1 k to GND.
  - CFGBVS to +3V3.
  - VCCBATT to GND (no encryption).
  - Bank 14 at 3.3 V, matching bank 0 for master SPI.
- **Table 5-13.** If the VCCIO_1 jumper puts bank 15 at 1.8 V or lower, slot
  pins on bank 15's multi-function balls can show a 0-1-0 input glitch one
  CFGCLK after EOS. Gateware ignores slot inputs for 200 ns after EOS. This is
  a gateware note, not a board change.

### Ball allocation (old A4)

The old A4 rule "slots A to D from bank 15 first, then bank 13" would break
the design: A to D get their selectable voltage from bank 15's VCCIO_1, and
E to H from bank 34's VCCIO_2. Those two banks are completely full (48 of 50
balls), so their 29 deep balls are inherent.

| Bank | Used | Free | Deep (≥ 7) used | Note |
|---|---|---|---|---|
| 13 | 10 | 40 | 0 | bus M; 19 free shallow |
| 14 | 46 | 4 | 18 | flash, PSRAM, sideband, bus L: the only bank where reordering helps |
| 15 | 48 | 2 | 21 | slots A to D, forced |
| 16 | 0 | 50 | 0 | free, goes to Network |
| 34 | 48 | 2 | 8 | slots E to H, forced |
| 35 | 0 | 50 | 0 | free |

(Table as of A4; since 2026-10-29 bank 13 is the 1.8 V PSRAM bank and
bank 14 holds the SDRAM address bus, see ref/ballmap.md.)
Moving bus L with its DIR/OE into bank 13, and depth-sorting within each
bank, takes allocator-chosen deep balls from **47 to 31**. 29 of those are in
banks 15/34 and 2 in bank 14. The flash/PUDC_B balls stay deep regardless.
The old target of "at most 20" is not reachable without giving up the
selectable voltage. The 8-layer decision stands on this alone.

Bank 16 orientation: U1 is at 0°, column 26 faces the top board edge and row
A faces the left edge. Bank 16 is rows A to H, columns 14 to 26, the
top-left quadrant of the package. The old plan's "rows 1 to 4" means
**columns 23 to 26**, the top edge. Prefer those for the link pairs.

## 4. Findings in the new work

1. **Release hold, input surge versus AUX** (`ref/power-budget.md`): the
   SMBJ22A clamps at 35.5 V; with a charged 24 V SEPIC output on top, the
   LM5157 SW pin can exceed its 50 V absolute maximum. The budget page itself
   says do not manufacture. See decision D1.
2. `design.py:279`: mode straps 4.7 k, should be ≤ 1 k (UG470).
3. `tools/place.py` step 4 (B.Cu decap mirror) contradicts single-sided
   assembly; delete it.
4. RP2350B GPIO 32 to 39 and GPIO 46 are SFP nets; GPIO 14/31 are
   `SFP_SCL/SDA`. After Fast Links goes, rename the bus to `SUP_SCL/SDA` (U17
   stays on it) and leave the nine freed GPIOs unconnected, named spare. Do
   not invent uses.
5. `budget.py` still counts both SFP modules on +3V3. U13 (+2V5, 2 A) already
   feeds the VCCIO jumpers at their 2.5 V setting, so its worst case is two
   VCCIO domains (each up to 0.5 A exported plus the bank) plus bank 16 plus
   the PHY's DVDD_RG. That is about 1.4 A, inside 2 A; the budget must say so.
6. 26 files still mention SFP (tools, `ref/`, `floorplan.md`, `findings.md`,
   `ref/user-manual.md`). A3 has to clear them all or say they are history.
7. DRC placement collisions from section 1. These are hand moves in phase B.

## 5. Decisions needed from the owner

- **D1. AUX lab rail in rev A?** Recommended: remove the SEPIC (U28, L10, D12,
  the voltage-select ladder and J67, U29, Q5 to Q8, D13 to D16, their R/C,
  about 40 parts) and feed the AUX pin of every power row only from J68 through
  the existing 10 branch PTCs. The user brings the lab voltage. This clears
  the surge hold, deletes the one unqualified converter and the custom
  coupled-inductor footprint, and keeps the connector pinout. Keeping it means
  solving the 50 V SW margin before ordering.
- **D2. RTL8211F-CG versus RTL8211FD-CG.** Old plan: FD if both are stocked
  with JLC assembly (no inductor). This stands; it is checked at BOM time, not
  a design blocker.
- **D3. Who does JLC upload and quote** (old B6.3 and B6.4). It is
  outward-facing; the owner does it, or explicitly hands it over.

## 6. Rebased phases

Rules from the old plan section 0 still hold. One phase, one commit, owner's
voice, no attribution. Each phase ends with:
- `design.py`, `budget.py`, `qualified.py` exiting 0;
- regeneration;
- netlist export;
- `check_erc.py`;
- DRC with parity;
- an entry in `ref/rev-a-report.md`.

Expected parts: 520 − about 42 (Fast Links) − 110 + 68 (decaps) + about 35
(Network) ≈ **471**, or about 433 with D1 as recommended.

- **A0. Small fixes.**
  - Mode straps to 1 k.
  - Delete `place.py` step 4 and its header line.
  - Add `tools/depth.py` (old plan §1.4).
- **A1. AUX** per D1, if removing.
- **A2. Decoupling** per §3 UG483: 68 parts, groups `decap <rail>`, citing Table 2-2/2-5.
- **A3. Fast Links out, Network in** (old A3), with these corrections:
  - Sheet renamed `Network`.
  - U17 renamed `status expander`, bus `SUP_SCL/SDA`, P7 spare.
  - RTL8211F straps and LEDs per §3.
  - `PHY_RESET_N` and `PHY_INT_N` on bank 13 (moved to bank 35 on 2026-10-29, when bank 13 went to 1.8 V).
  - Link pinout table into `ref/link-ports.md`.
  - SFP docs deleted or marked history.
- **A4. Allocation.**
  - VCCO_16 → +2V5.
  - Bank 16: RGMII (14 balls, RXC on a clock-capable P) and LINK (8 pairs, the
    two RX clocks on clock-capable pairs), columns 23 to 26 first.
  - Bus L and its controls to bank 13 (still there; the bank runs at 1.8 V since 2026-10-29).
  - Depth sort inside each bank.
  - `alloc.py --check`.
  - Report the new histogram; expect about 31 deep plus 6 inherent flash balls.
- **A5. `tools/gen_xdc.py` and the Vivado gate.** Vivado 2026.1 is installed
  at `/tools/Xilinx/2026.1`, so this runs locally.
- **B1. 8-layer JLC stackup**, `LVDS_100R` and `RGMII` classes, drop `MGT_100R`
  (`gen_pcb.py --rules-only` only).
- **B2. Sync** with `load_pcb.py`, between a `check_positions.py` snapshot and
  compare. Every pre-existing reference must report unmoved.
- **B3 to B5. Placement and routing by hand in KiCad**, in the old plan's order.
  - No autoplacement.
  - No autorouter except the old B5.6 slot-signal case, after everything else
    is locked.
  - Any script here only reports (overlaps, lengths); it never moves a footprint.
- **B6 and C.** As in the old plan, with the checklists corrected per §3.

Link-port operating rule to document in `ref/link-ports.md` (no hardware for
it in rev A): **power both boards before connecting the cable.** The link
pairs are DC-coupled into HR inputs. Driving them into an unpowered board
pushes current through its input clamps (the DS181 input limit is about
VCCO + 0.55 V; verify the exact figure in DS181 when writing the page).
