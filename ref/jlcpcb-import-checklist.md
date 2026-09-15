# JLCPCB / EasyEDA import checklist

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
| 4 | `APS1604M-3SQR-SN` | work memory | `C18214056` |
| 1 | `W25Q256JVEIQ` | FPGA startup memory | `C97522` |
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
| 1 | `BSS138` from a named manufacturer | power-switch drive | C82045 |
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
| 1 | `DSC1123CI2-125.0000` | 125 MHz LVDS clock | `C617173` — imported, pin map confirmed and linked |
| 2 | `1888247-1` | SFP/SFP+ 20-contact connector | `C305914` — imported and linked |
| 2 | `2007198-1` | SFP+ press-fit cage | `C573949` — imported and linked |
| 2 | `SRN6045TA-100M` | 5 V and 12 V supply inductors | C2046332 |
| 1 | `SRN6045TA-4R7M` | 3.3 V supply inductor | C2044594 |
| 1 | `2.54-2*5P` | keyed FPGA JTAG header | `C5665` — imported and linked |
| 1 | `BM03B-SRSS-TB(LF)(SN)` | keyed controller SWD header | `C160389` — imported and linked |
| 1 | `KF301-5.0-2P` | 9–14 V external power terminal | `C474881` — imported and linked |
| 1 | `F.0603.00025/P2-0603G1TS2-06T-002` | green FPGA-DONE LED | `C7496818` — imported and linked |
| 13 | `F254D-02-PT-B` | removable 2.54 mm selector shunts | `C501335` — imported; loose accessory |
| 1 | `PCF8574T_3,518` | SFP control I/O expander | `C7605` — imported and linked |

Import the exact orderable suffix shown. A nearby family member in the same
search result is not interchangeable.

## Import audit result

The fitted design currently uses **127 instances** backed by the EasyEDA
library. Their connected schematic pin numbers exist in both the imported
symbol and imported footprint, and their LCSC identities agree.

The imported TPS259470 footprint was rejected: its pad geometry violates the
board's 0.20 mm copper clearance in 18 places. `U25` and `U26` keep KiCad's
official TI `RPU0010A` footprint; their exact LCSC numbers remain in the
schematic and BOM. An imported file is not automatically better than the
manufacturer-package footprint.

The slot fuses, SFP cages and complete extension connector system are selected,
linked and audited. Only ordinary passive BOM matching remains below.

## Extension hardware — imported and linked

| Item | Selected part |
|---|---|
| four 2x16 signal sockets | `C3975161` — imported and linked |
| four 1x16 power sockets | `C7499334` — imported and linked |
| two 5V-bus 2x8 signal sockets | `C3975153` — imported and linked |
| two 1x8 power sockets | `C27438` — imported and linked |
| ten guide/key posts | `C42431799` — imported and linked |
| twelve 2x3 selectors | `C65114` — imported and linked; `C501335` shunts are loose accessories |
| one 1x2 external-JTAG selector | `C492401` — imported and linked; uses a `C501335` shunt |

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
