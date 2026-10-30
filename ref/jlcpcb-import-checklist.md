# JLCPCB / EasyEDA import checklist

## AUX rework import checkpoint (2026-09-21; superseded 2026-10-23)

Of the eight imports requested for the AUX lab rail, only C70150 (branch
PTC) and C151920 (D8 SMBJ22A) remain in the design. The LM5157 SEPIC and its
selectors were removed for rev A (`ref/power.md`), so C5219222, C552792,
C5590, C81598, C2937625, the rejected C9139 and its C124386 replacement, and
the locally drawn C54563336 coupled inductor are no longer used. The EasyEDA
imports stay in `easyeda/` as library files; `tools/audit_easyeda.py` only
checks parts the design fits.

The rest of this document records the older generated project and must be
reconciled with the completed batch before release. This checkpoint is not
an ERC, DRC, PCB-sync or complete power-stage qualification result.

The imported library is in `easyeda/` beside `kicad/`. The checked parts below
are now linked from the textual design by exact footprint and LCSC number.
`python3 tools/audit_easyeda.py` verifies those links, symbol pin numbers and
footprint pad numbers every time the design changes.

An imported symbol and footprint are evidence, not proof. Before use, Odin
must compare pin numbers, exposed pads, package dimensions and orientation
against the manufacturer datasheet.

## Imported parts

| Qty | Manufacturer part number | Used for | Known LCSC number |
|---:|---|---|---|
| 1 | `XC7A100T-2FGG676I` | programmable logic | `C1521803` — imported |
| 4 | `APS6404L-SQN-SN` | work memory, 1.8 V | `C5360304` |
| 1 | `W25Q256JVEIQ` | FPGA startup memory | `C97522` |
| 1 | `W9825G6KH-6` | SDRAM, 32 MB, 3.3 V | `C62246` |
| 1 | `MR25H10CDF` | SPI MRAM | `C246234` |
| 1 | `TF-01A` | microSD socket, SPI mode | `C91145` — imported with easyeda2kicad |
| 1 | `RP2350B` | board controller | C42415655 |
| 1 | `ABM8-272-T3` | controller 12 MHz crystal | C20625731 |
| 1 | `W25Q32JVZPIQ` | controller memory | `C571260` — imported and linked |
| 1 | `HC-TYPE-C-16P-01A` | USB-C connector | C2894897 |
| 1 | `ESDA6V1BC6` | USB data/CC protection | C495220 |
| 1 | `SMBJ13A` from a named manufacturer | USB power surge protection | C133675 |
| 1 | `CH224K` | USB power request | C970725 |
| 1 | `B3U-1000P` | controller boot button | C231329 |
| 1 | `SN74CB3Q3384APWR` | JTAG owner switch | C469874 |
| 2 | `SN74LXC8T245PWR` | Two complete 8-bit 5 V buses | C4363995 |
| 2 | `DMG2305UX` | switched power | C5261054 |
| 2 | `BSS138LT1G` (onsemi) | Q3 power-switch drive; Q4 DONE LED buffer | C82045 |
| 1 | `TPS259470ARPWR` | USB input protection | C3662799 |
| 3 | `SS34` from a named manufacturer | power diodes | C8678 |
| 1 | `TPS54202DDCR` | 5 V supply | `C191884` |
| 1 | `AP63300WU-7` | always-on 3.3 V supply | C2158012 |
| 3 | `TLV62569DRLR` | 2.5/1.8/1.2 V supplies | `C163217` |
| 1 | `SY8047QDC` | 4 A FPGA 1.0 V supply | `C3018651` — imported and linked |
| 1 | `TPS61085PWR` | 12 V slot-power supply | C13505 |
| 4 | `TPS22950CDDCR` | low-voltage slot-power protection | C7587833 |
| 1 | `TPS259470LRPWR` | 12 V slot-power protection | C3662793 |
| 1 | `AOTA-B201610S3R3-101-T` | controller 1.1 V inductor | C42411119 |
| 1 | `VLS252010HBX-1R0M-1` | FPGA transceiver filter | `C88211` — imported and linked |
| 3 | `SRN4018-2R2M` | 2.5/1.8/1.2 V supply inductors | `C913207` — imported and linked |
| 1 | `FTC201610S1R0MBCA` | FPGA 1.0 V supply inductor | `C5832342` — imported and linked |
| 10 | `SMD1206B020TF/24` | 12 V slot PTC, 200 mA | `C269111` — imported and linked |
| 20 | `SMD1206B050TF` | 5 V and pin-voltage PTC, 500 mA | `C269115` — imported and linked |
| 10 | `BSMD1206-030-16V` | 3.3 V slot PTC, 300 mA | `C22378340` — imported and linked |
| 2 | `SRN6045TA-100M` | 5 V and 12 V supply inductors | C2046332 |
| 1 | `SRN6045TA-4R7M` | 3.3 V supply inductor | C2044594 |
| 1 | `2.54-2*5P` | keyed FPGA JTAG header | `C5665` — imported and linked |
| 1 | `BM03B-SRSS-TB(LF)(SN)` | keyed controller SWD header | `C160389` — imported and linked |
| 1 | `KF301-5.0-2P` | 9–21 V external power terminal | `C474881` — imported and linked |
| 4 | `F.0603.00025/P2-0603G1TS2-06T-002` | green DONE, heartbeat and two user LEDs | `C7496818` — imported and linked |
| 13 | `F254D-02-PT-B` | removable 2.54 mm selector shunts | `C501335` — imported; loose accessory |
| 1 | `RTL8211FD-CG` | gigabit Ethernet PHY (LDO model) | `C2687133` — imported 2026-10-23 with easyeda2kicad, pins checked against datasheet rev 1.7 |
| 1 | `HR911130A` | ETH 1000Base-T magjack with LEDs | `C54408` — imported 2026-10-23, pin names checked against the HanRun drawing |
| 2 | `KH-RJ45-58-8P8C` | LINK P / LINK Q plain shielded jacks | `C2683360` — imported 2026-10-23 |
| 1 | `X322525MOB4SI` | PHY 25 MHz crystal | `C9006` (Basic) — imported 2026-10-23 |
| 4 | `TPD4E1U06DBVR` | link-port ESD arrays | `C124691` — imported 2026-10-23 |

Import the exact orderable suffix shown. A nearby family member in the same
search result is not interchangeable.

## Import audit result

The fitted design currently uses **129 instances** backed by the EasyEDA
library. Their connected schematic pin numbers exist in both the imported
symbol and imported footprint, and their LCSC identities agree.

The imported TPS259470 footprint was rejected: its pad geometry violates the
board's 0.20 mm copper clearance in 18 places. `U25` and `U26` keep KiCad's
official TI `RPU0010A` footprint; their exact LCSC numbers remain in the
schematic and BOM. An imported file is not automatically better than the
manufacturer-package footprint.

The slot fuses, network parts and complete extension connector system are
selected, linked and audited. Only ordinary passive BOM matching remains below.

## Fast Links removed (2026-10-23)

The SFP connectors, cages, 125 MHz oscillator and I²C switch left the design
in rev A (`ref/rev-a-plan.md` A3). Their library imports stay in `easyeda/`
as files; `tools/audit_easyeda.py` only checks parts the design fits.

## Extension hardware — imported and linked

| Item | Selected part |
|---|---|
| two 2x32 signal sockets | `C49569844` — imported and linked |
| ten 1x7 keyed power sockets | `C2832270` — imported and linked |
| two 5V-bus 2x8 signal sockets | `C3975153` — imported and linked |
| 2x8 through-hole signal sockets | `C2897409` — imported and linked |
| ten 21 mm cut-to-1P key posts | `C51353` — imported; custom single-pad cut footprint |
| twelve 2x3 selectors | `C65114` — imported and linked; `C501335` shunts are loose accessories |
| one 1x2 external-JTAG selector | `C492401` — imported and linked; uses a `C501335` shunt |

## PSRAM series resistors

R104–R127 are 24 populated 33 ohm 0402 resistors, **C25105**, one per
SCK/CE_B/IO0–IO3 signal across the four PSRAM ports. They use standard KiCad
resistor footprints. Keep them in the assembly BOM; these are tuning parts,
not optional unpopulated links.

## +12V_EXT output capacitor

C232 is **10uF 25V**, Samsung CL21A106KAYNNNE / **C15850**, X5R, 0805.
It connects U25 OUT (+12V_EXT) to GND before the selectors and PTC branches.
Place it beside U25; the 25V rating is explicit in the generated BOM value.

## Input protection additions

- D8: **SMBJ15A-13-F**, Diodes Incorporated, **C135046**, unidirectional
  TVS in standard KiCad `Diode_SMD:D_SMB`; cathode pad 1 to VIN_EXT.
- R49 and the Q2 gate network are gone (2026-10-29): U34 TPS2121RUXR
  (C485916) selects the +5V source; U23/U24 are TPS22953DSQR (C2680343).
  Use 1% resistors for the documented divider tolerance calculation.

## Ordinary resistors and capacitors

These do not need imported custom symbols or footprints. They do need exact
LCSC stock numbers in the BOM.

Prefer Basic or Promotional Extended parts, but only after matching:

- package: 0402, 0603 or 0805 exactly as designed;
- resistance/capacitance and tolerance;
- capacitor dielectric: X5R or X7R;
- voltage rating: 16 V minimum unless the schematic explicitly says 25 V;
- effective capacitance after DC-bias derating, especially 10 uF and 22 uF;
- power rating for resistors in dividers and current-setting networks.

The ordinary parts are **not release-ready yet**. The values and package sizes
exist, but LCSC numbers and capacitor DC-bias checks are still missing. Do not
bulk-assign the cheapest search result.

## What to send back after importing

For every imported part, retain:

1. manufacturer part number;
2. LCSC number;
3. EasyEDA symbol;
4. EasyEDA footprint;
5. datasheet link;
6. whether JLCPCB currently marks it Basic, Promotional Extended or Extended.

Then Odin can replace library references systematically and run symbol-pin,
footprint, ERC, power-budget and schematic-parity checks again.
