"""Drawing-based SFP cage geometry; see ref/sfp-cage.md for datums/sources.

Footprint origin: PCB edge at cage centreline; +x into board, +y transverse.
All dimensions mm. Numbering is local (all twenty tails are chassis GND).
"""
from pathlib import Path

MPN = 'U77A11133001'
FOOTPRINT = 'Amphenol_' + MPN
DATASHEET = 'https://datasheet.lcsc.com/datasheet/pdf/5e6fc7644f810f07d5f295a13622bd1b.pdf?productCode=C5355132'
MOUTH_OVERHANG = 11.50 - 4.50
CONNECTOR_DEPTH = 34.50 + 0.90
# P-U77-A111X-XX0X rev H, sheet 4. Rear row: datum F + 7.10.
# Transverse dimensions originate at the -7.125 side row.
HOLES = [
    (4.5, -7.125, 1.05), (14.5, -7.125, 1.05),
    (24.5, -7.125, 1.05), (27.3, -7.125, .95),
    (32.0, -7.125, .95), (34.5, -7.125, .85),
    (37.0, -7.125, .95), (41.6, -4.8, .95),
    (41.6, 0, .95), (41.6, 4.8, .95),
    (39.5, 7.125, 1.05), (37.0, 7.125, .95),
    (32.0, 7.125, .95), (29.5, 7.125, 1.05),
    (27.3, 7.125, .95), (19.5, 7.125, 1.05),
    (9.5, 7.125, 1.05), (4.5, 8.58-7.125, 1.05),
    (24.5, 11.08-7.125, 1.05), (24.5, 5.68-7.125, 1.05),
]

def symbol(gen_box_symbol):
    pins = [(str(n), str(n), 'passive', 'L' if n <= 10 else 'R')
            for n in range(1, 21)]
    return gen_box_symbol(MPN, pins, 'odin:' + FOOTPRINT, DATASHEET,
                          'SFP cage, 3.2 mm solder tails, all tails GND').replace(
                              '(property "Reference" "U"', '(property "Reference" "SH"')

def generate(directory):
    out = [f'(footprint "{FOOTPRINT}" (version 20241229) (generator "freyja")',
           '(layer "F.Cu") (attr through_hole)',
           '(descr "Amphenol P-U77-A111X-XX0X rev H; edge-datum origin; nose -X")',
           '(property "Reference" "SH**" (at 18 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
           f'(property "Value" "{MPN}" (at 18 3) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))']
    # Courtyard encompasses shell, all lands, and connector; intentional overlap
    # with J60/J61. A 17 mm cage pitch leaves 0.25 mm between courtyards.
    for layer, box, width in [('F.Fab', (-7, -7.925, 41.98, 7.925), .1),
                               ('F.CrtYd', (-7.25, -8.375, 42.65, 8.375), .05)]:
        x0,y0,x1,y1 = box
        for a,b,c,d in [(x0,y0,x1,y0),(x1,y0,x1,y1),(x1,y1,x0,y1),(x0,y1,x0,y0)]:
            out.append(f'(fp_line (start {a} {b}) (end {c} {d}) (stroke (width {width}) (type solid)) (layer "{layer}"))')
    out += ['(fp_line (start 0 -8.125) (end 0 8.125) (stroke (width 0.1) (type solid)) (layer "Dwgs.User"))',
            '(fp_text user "PCB EDGE" (at 0 -10 90) (layer "Dwgs.User") (effects (font (size 1 1) (thickness 0.15))))']
    for n,(x,y,drill) in enumerate(HOLES,1):
        size, shape = (2, 'rect') if drill != .95 else (1.55, 'circle')
        out.append(f'(pad "{n}" thru_hole {shape} (at {x:.3f} {y:.3f}) (size {size} {size}) (drill {drill}) (layers "*.Cu" "*.Mask"))')
    # Conservative front-surface keepout: ground pours allowed, tracks/vias
    # excluded (the drawing permits chassis-ground tracks too).
    out.append('''(zone (net 0) (net_name "") (layer "F.Cu") (hatch edge 0.5)
      (connect_pads (clearance 0)) (min_thickness 0.25)
      (keepout (tracks not_allowed) (vias not_allowed) (pads allowed)
               (copperpour allowed) (footprints not_allowed))
      (fill (thermal_gap 0.3) (thermal_bridge_width 0.3))
      (polygon (pts (xy 0 -8.125) (xy 26.8 -8.125) (xy 26.8 8.125) (xy 0 8.125))))''')
    out.append(')\n')
    Path(directory, FOOTPRINT + '.kicad_mod').write_text('\n'.join(out))
