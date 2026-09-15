# SFP solder-tail cage qualification

Selected **Amphenol U77A11133001**, LCSC **C5355132**, for SH1/SH2.
Keep **TE 1888247-1**, C305914, for J60/J61. A combined connector/cage is
unnecessary: the standalone solder cage has the required connector datum.

## Evidence

- [Amphenol product](https://www.amphenol-cs.com/product/u77a11133001.html):
  single SFP cage, matte tin, 3.2 mm solder tails, tray; listed at **2.5 Gb/s**.
- [LCSC part](https://www.lcsc.com/product-detail/C5355132.html).
- [JLC assembly listing](https://jlcpcb.com/partdetail/AmphenolICC-U77A11133001/C5355132):
  Extended, Wave Soldering, Economic and Standard PCBA (2026-09-15).
- [Amphenol P-U77-A111X-XX0X rev H](https://datasheet.lcsc.com/datasheet/pdf/5e6fc7644f810f07d5f295a13622bd1b.pdf?productCode=C5355132):
  sheet 2 shell/tails, sheet 3 bezel, sheet 4 host-board pattern.
- [TE 2007198 rev C3](https://www.micro-semiconductor.sk/datasheet/d2-2007198-2.pdf):
  sheet 3 recommended host-board layout and Detail A connector datum.
- [TE 1888247 rev N](https://datasheet.lcsc.com/datasheet/pdf/5c88f30056df913b4d2315b79af60ec8.pdf?productCode=C305914):
  sheet 3 connector mounting-side land pattern.

The drawings are manufacturer documents; the PDF links are distributor mirrors.
The 16 Gb/s rating of the old TE cage is removed. Operation above the selected
cage's listed 2.5 Gb/s requires separate qualification; this swap does not
establish a 6.6 Gb/s SFP assembly rating.

## Datum comparison (mm)

| Feature | Amphenol cage | TE 2007198 / 1888247 |
|---|---:|---:|
| Side shield-hole row separation | 14.25 | 14.25 |
| Datum F behind PCB front edge | 34.50 | 34.50 |
| Connector locating-hole spacing | 9.60 | 9.60 |
| Connector locating-hole diameter | 1.55 | 1.55 ±0.05 |
| Connector datum behind F | Drawing references connector layout | 0.90 (2007198 Detail A) |
| Front component/trace exclusion depth | 26.80 | 26.80 |
| Rear component exclusion extent | 42.30 | 42.30 |

Therefore the connector peg centreline is **34.50 + 0.90 = 35.40 mm** behind
the PCB-edge datum. The first shield tail is 11.50 mm behind the cage mouth
and 4.50 mm behind the PCB edge, giving **7.00 mm mouth overhang**, and
**42.40 mm mouth-to-connector datum**. The 48.98 mm shell reaches 41.98 mm
inside the board. These are different datums: 35.40 is not measured from the
cage centre or the enclosure faceplate. The drawings specify 3.50 ±0.30 mm
from the inside of the bezel to the PCB edge.

`tools/sfp_cage.py` generates `odin:Amphenol_U77A11133001` with its origin at
the edge datum, +X into the board. `tools/placement.py` rotates it 270° to
put its mouth beyond the top edge. The retained connector footprint has its
origin midway between its locating holes; rotation 180° puts pads 1–10 toward
the mouth. Its 20 contact lands retain TE 1888247's 0.8 mm pitch and 8.2 mm
row separation. Its imported 1.70 mm plated locating holes are corrected to
1.55 mm NPTH per TE sheet 3.

## Footprint and assembly boundaries

The cage has 10 × 1.05 mm holes, 9 × 0.95 mm holes and one 0.85 mm datum hole.
Eleven specified chassis lands are 2 × 2 mm; the nine optional-plating holes
are also plated and grounded, with 1.55 mm circular lands. All twenty local
pad numbers connect to GND. The rear row is F + 7.10 = 41.60 mm. No connector
pads or locating holes are duplicated in the cage footprint.

The footprint marks the PCB edge and includes a front-surface rule area:
no tracks, vias or other component bodies in the front 26.8 mm. Ground pours
are permitted; ensure pours there are GND. This conservatively also excludes
ground tracks, which the drawing allows. The full cage courtyard reserves
its body; the enclosed J60/J61 courtyard overlaps are intentional. The rear
opening permits connector traces; reserve the remaining rear area for the
cage, per sheet 4. The 17 mm cage pitch exceeds the 16.25 mm layout width.

On a 1.6 mm PCB the 3.2 mm tails project approximately 1.6 mm below the board.
Allow underside solder/fixture clearance. Reflow J60/J61 first, then install
and wave solder SH1/SH2 using JLC's listed process. Final enclosure cutouts
and the assembly fixture must use the drawings' bezel dimensions.
