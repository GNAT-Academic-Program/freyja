# KiCad regeneration and validation

Validated with KiCad CLI / pcbnew 9.0.8 on 2026-09-15.

**Current ERC:** zero errors; only FPGA_DXP and FPGA_DXN dangling-label
warnings. Run `python3 tools/check_erc.py` to enforce the exact list.
Earlier sections below record historical results before pin-type normalization.

## Synchronized changes

- Six copper layers: signal / GND / signal / power / GND / signal.
- R35 and R89: independent 100 ohm, 1% MGTRREF resistors to +1V2_MGT.
- Quad 213 RX pins and unused quad 216 RX lanes connected to GND.
- U1.P12 VREFP connected to GND for the internal XADC reference.
- R90–R95: 100k regulator-enable pulldowns to GND.
- R96/R97: 10k bus-enable pull-ups to +3V3; OE_N controlled by P16/Y25.

The schematic and PCB contain 457 components. Every populated component's
reference/value and every connected pad were compared against `design.build()`.
All checks passed. All 447 retained footprint positions, orientations and
sides match the pre-sync board, including footprints updated to the current
library selection. The obsolete VREFP decoupler C1 was removed; subsequent
capacitors were renumbered while retaining their physical placement.

Eight new resistors and two previously missing SFP cages (SH1/SH2) were added
in a staging area outside the board during the electrical sync. The cage
swap below subsequently placed SH1/SH2 and J60/J61. The eight resistors
remain staged; placement and routing remain unfinished.

Standard symbol libraries are now explicitly listed in the project library
table. Silkscreen user labels use separate fields, preserving the schematic
values used for BOM and parity checks.

## Checks and remaining findings

Commands:

```sh
python3 tools/gen_project.py
kicad-cli sch export netlist --format kicadsexpr -o kicad/odin.net kicad/odin.kicad_sch
kicad-cli sch erc --format json -o /tmp/freyja-sync/erc.json kicad/odin.kicad_sch
kicad-cli pcb drc --schematic-parity --format json -o /tmp/freyja-sync/drc.json kicad/odin.kicad_pcb
```

- ERC: 1 error (`SUP_SWCLK` input has no output driver), 317 pin-type warnings
  involving imported symbols, 2 dangling FPGA temperature-diode labels.
- DRC: 783 violations, including shorts, clearances, courtyard/silkscreen
  collisions, and invalid outlines; 499 unrouted connections.
- Schematic parity: 2 warnings. J60/J61 use the standard SFP symbol containing
  a `CAGE` pin, while their electrical connector footprints have only 20 pads.
  SH1/SH2 represent the separate physical cages. This symbol/footprint mismatch
  remains to be resolved; no fictitious pad was added to suppress it.

The six requested electrical changes are synchronized. ERC/DRC are not clean,
and the board is not ready for fabrication.

## Solder-tail cage update

Replaced SH1/SH2 with Amphenol U77A11133001 / C5355132 and regenerated the
custom library, schematic, qualified-parts table and netlist. The PCB's four
SFP footprints now follow the drawing-derived placement contract. The other
453 footprints retain their previous positions, sides and orientations.
All 457 component references, values, footprint IDs and connected pad nets
match the regenerated netlist.

Actual KiCad pad-coordinate checks passed for both assemblies:

- 20 grounded cage tails: ten 1.05 mm, nine 0.95 mm, one 0.85 mm drill.
- Connector peg spacing 9.60 mm; both holes 1.55 mm NPTH.
- Peg centreline 35.40 mm behind board edge.
- Front contacts 1–10 at depth 31.30 mm, rear contacts 11–20 at 39.50 mm.
- Placement contract geometry clean; EasyEDA audit passes for 125 instances.

Latest KiCad CLI results (`/tmp/freyja-cage/erc.json` and `drc.json`):
ERC 1 error and 279 warnings (277 pin-type, 2 dangling labels); DRC 688
violations, 499 unrouted connections, 2 existing SFP-symbol parity warnings.
The only DRC violations involving the four SFP footprints are the two
intentional connector-inside-cage courtyard overlaps. These checks establish
footprint consistency, not completed routing or higher-rate port qualification.

## DONE LED buffer update

Added R98 (4.7k from +3V3 to CFG_DONE) and Q4 (BSS138LT1G low-side
LED driver). R7 now feeds D1 from +3V3; D1's cathode connects to Q4's drain.
The gate connects to CFG_DONE and source to GND. Existing SUP_DONE wiring
and all previous component designators are preserved. No DriveDone setting
is required for LED operation.

Regenerated schematic, netlist and qualified-parts table; synchronized PCB.
All 459 component values, footprint IDs and connected pad nets match the
netlist. All 457 previous footprint positions, orientations and sides are
preserved. Q4 and R98 are staged outside the board; the board still requires
physical placement and routing, including the previously staged DONE LED.

Topology checks verify R7 → D1 → Q4, the pull-up and G/S/D pin mapping, and
confirm only R7/D1 connections changed among existing parts. EasyEDA audit
passes for 126 fitted instances. KiCad ERC/DRC counts remain unchanged:
1 ERC error, 279 warnings; 688 DRC violations, 499 unrouted connections and
2 schematic-parity warnings. Latest reports: `/tmp/freyja-done/erc.json`
and `/tmp/freyja-done/drc.json`.

## SFP I2C isolation update

Added U27 (PCA9543APW,118), C231 and R99–R103. J60/J61 now use separate
SFP0/SFP1 SDA/SCL nets behind the switch; upstream supervisor/U17 wiring
is preserved. Verified the manufacturer pin map, grounded address pins,
SUP_RUN reset connection and distinct connector channels. Existing parts
retain their references; only J60/J61's management connections changed.

All 466 component values, footprint IDs and connected pad nets match the
regenerated netlist. All 459 previous placements, orientations and sides
are preserved. Seven new footprints are staged outside the board; placement
and routing remain unfinished. The placement source includes an SFP mux
group anchor. The import audit passes for 126 fitted EasyEDA instances;
U27 instead uses a generated symbol and standard KiCad TSSOP-14 footprint.

KiCad counts are unchanged: ERC 1 error/279 warnings, DRC 688 violations,
499 unrouted connections, 2 existing SFP parity warnings. Latest reports
are `/tmp/freyja-mux/erc.json` and `/tmp/freyja-mux/drc.json`. There is no
hardware enumeration test or implemented supervisor firmware yet.

## PSRAM series resistor update

Added R104–R127, 33 ohm 0402, on all 24 PSRAM signals. Each FPGA-side net
has exactly two nodes (U1 and resistor pad 1); each `_MEM` net has exactly
two nodes (resistor pad 2 and its own PSRAM). All four ports remain isolated,
and the FPGA assignments and all existing designators are preserved.

All 490 component values, footprint IDs and connected pad nets match the
exported netlist. All 466 previous positions/orientations/sides are preserved.
The new resistors sit beside U1 under the new placement rule; U1 itself is
still in the staged layout outside the board. Routing remains unfinished.
Their reference/value text uses fabrication layers to avoid silkscreen
collisions at 1 mm spacing.

ERC: 1 error / 279 warnings. DRC: 688 violations, 499 unrouted connections,
2 existing SFP parity warnings; counts unchanged after text cleanup. Reports:
`/tmp/freyja-psram/erc.json` and `/tmp/freyja-psram/drc.json`. EasyEDA audit
passes for 126 fitted instances. No electrical waveform or timing validation
has been performed on hardware.

## +12V_EXT output capacitor update

C232 is 10uF 25V / C15850 from U25 pin 6 (+12V_EXT) to GND. Generator,
schematic, netlist and PCB agree. All 491 component values, footprint IDs
and pad nets match the netlist; all 490 previous components and placements
are unchanged. C232 is staged outside the board and assigned to U25's group
for subsequent placement close to OUT.

ERC and DRC counts remain unchanged: 1 ERC error / 279 warnings;
688 DRC violations, 499 unrouted connections and 2 existing parity warnings.
Reports: `/tmp/freyja-cout/erc.json` and `/tmp/freyja-cout/drc.json`.

## Q2 gate divider and external-input TVS

R49 is now 47k, preserving its VBUS5_PULL/VBUS5_GATE connections. D8 is
SMBJ15A-13-F / C135046: cathode (pad 1) to VIN_EXT, anode (pad 2) to GND,
on the terminal side of D4. Verified nominal divider VGS (-6.122V at 9V),
1% resistor/+5% source tolerance (6.470V magnitude), and 3.197ms gate RC.

All 492 component values, footprint IDs and pad nets match the exported
netlist. All 491 previous positions/orientations/sides are unchanged. D8 is
staged for placement next to J50; its short surge-current path is not routed.
ERC/DRC counts are unchanged (1/279 ERC error/warnings; 688 DRC violations,
499 unrouted, 2 parity warnings). Reports are in
`/tmp/freyja-input-protection/`. No physical surge testing has been performed.

## Supervisor indicators and core PG input

Added D9–D11 (green LEDs) and R128–R130 (1k); U17 P0–P2 sink their
cathodes and P3 reads CORE_1V0_GOOD. The 100k PG pull-up and P7 SFP control
remain. Verified all three LED polarities/current paths and the expander
physical pin map. All 498 component values, footprint IDs and connected
pad nets match the exported netlist; all 492 earlier placements are preserved.

The new parts are staged outside the board, with visible CTRL HB/USER 1/
USER 2 labels; their final group anchor is in the placement source. The
power budget includes a 5mA allowance and passes. EasyEDA audit passes for
129 fitted instances. Firmware behavior is documented but not implemented.

KiCad ERC: 1 error, 286 warnings (284 pin-type, 2 dangling labels), adding
seven pin-type warnings from the imported expander/LED symbols. DRC:
694 violations, 499 unrouted connections and 2 existing parity warnings;
the six additional violations are silkscreen warnings on the added LEDs.
No new ERC/DRC errors. Reports: `/tmp/freyja-status/erc.json` and `drc.json`.

## ERC pin-type normalization and regression guard

`tools/gen_kicad.py` now normalizes eleven imported symbols using reviewed
pin roles. J51 pins 1/3 model bidirectional SWD debugger connections; its
ground/mechanical pins are passive. Connector/LED pins are passive and U17
PCF8574 pins use actual supply, address/clock input, bidirectional port/data,
and open-drain interrupt roles. Pin names, numbers, positions and connectivity
are unchanged. The normalization is idempotent and survives regeneration.

After library/schematic regeneration, ERC reports **0 errors, 2 warnings**:
only the FPGA_DXP/FPGA_DXN global labels. U20 produces no warning, so none
is exempted. No ERC exclusions or severity changes were introduced.
`tools/check_erc.py` runs KiCad with all severities and compares exact rule,
severity and item descriptions. Checked that extra warnings (including U20),
renamed labels, changed severities and missing expected warnings fail.

The regenerated netlist still matches all 498 PCB components and pad nets;
no board mutation was needed. EasyEDA audit passes for 129 instances.
The latest standalone ERC report is `/tmp/erc-typed.json`; the regression
command creates and checks a fresh report each run.

## Six-layer routing classes and impedance rules

`python3 tools/gen_pcb.py --rules-only` updates JLC06161H-1080B material
parameters, project net classes and custom DRC constraints. It preserves
all board content outside the stackup block byte-for-byte; a second run
produces identical PCB, project and rules files.

The JLC coated-microstrip solver predicts 99.8515 Ω for the rounded
0.099 mm width / 0.200 mm gap. Inputs and original solver responses are
recorded in [PCB impedance](pcb-impedance.md). MGT routing is constrained
to the outer layers; PSRAM minimum width is 0.1 mm, default clearance is
0.15 mm, and MGT intra-pair skew is limited to 0.1 mm.

KiCad 9.0.8 command:

```sh
kicad-cli pcb drc --format json --schematic-parity \
  -o /tmp/freyja-routing-rules/after.json kicad/odin.kicad_pcb
```

Full output (exit status 0; no rule syntax errors):

```text
Found 693 violations
Found 499 unconnected items
Found 2 schematic parity issues
Saved DRC Report to /tmp/freyja-routing-rules/after.json
```

Baseline was 694 / 499 / 2. The clearance violation count decreased from
15 to 14; all other violation-type counts are unchanged. This is a rule
parser check, not a clean fabrication DRC.

A separate temporary routed test board using the generated project and
rules verified that a 0.20 mm mismatch on MGTPTXP0/MGTPTXN0 produces
`skew_out_of_range`, while a 0.05 mm mismatch on the much longer
MGTREFCLK0P/N pair does not. Thus the limit applies within each pair,
not across all MGT lanes. A 0.09 mm PSRAM0_SCK track produces `track_width`.
KiCad recognizes all ten real-board differential pairs, including names
with trailing channel digits. Test artifacts: `/tmp/freyja-routing-rules/`.
