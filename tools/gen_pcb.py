#!/usr/bin/env python3
"""Emit an empty 4-layer kicad_pcb with outline + stackup + net classes.
Populate it in the PCB editor with Update PCB from Schematic (F8)."""
W, H, R = 120.0, 100.0, 3.0        # board size and corner radius
X0, Y0 = 30.0, 30.0
OUT = 'kicad/odin.kicad_pcb'

LAYERS = [(0,'F.Cu','signal'), (1,'In1.Cu','signal','GND plane'),
          (2,'In2.Cu','signal','power planes'), (31,'B.Cu','signal'),
          (32,'B.Adhes','user','B.Adhesive'), (33,'F.Adhes','user','F.Adhesive'),
          (34,'B.Paste','user'), (35,'F.Paste','user'),
          (36,'B.SilkS','user','B.Silkscreen'), (37,'F.SilkS','user','F.Silkscreen'),
          (38,'B.Mask','user'), (39,'F.Mask','user'),
          (40,'Dwgs.User','user','User.Drawings'), (41,'Cmts.User','user','User.Comments'),
          (42,'Eco1.User','user','User.Eco1'), (43,'Eco2.User','user','User.Eco2'),
          (44,'Edge.Cuts','user'), (45,'Margin','user'),
          (46,'B.CrtYd','user','B.Courtyard'), (47,'F.CrtYd','user','F.Courtyard'),
          (48,'B.Fab','user'), (49,'F.Fab','user')]

def main():
    o = ['(kicad_pcb', '\t(version 20241229)', '\t(generator "odin-tools")',
         '\t(generator_version "9.0")',
         '\t(general\n\t\t(thickness 1.6)\n\t\t(legacy_teardrops no)\n\t)',
         '\t(paper "A3")', '\t(layers']
    for l in LAYERS:
        o.append(f'\t\t({l[0]} "{l[1]}" {l[2]}' + (f' "{l[3]}"' if len(l) > 3 else '') + ')')
    o.append('\t)')
    o.append('''\t(setup
\t\t(pad_to_mask_clearance 0)
\t\t(allow_soldermask_bridges_in_footprints no)
\t\t(tenting front back)
\t\t(stackup
\t\t\t(layer "F.SilkS" (type "Top Silk Screen"))
\t\t\t(layer "F.Paste" (type "Top Solder Paste"))
\t\t\t(layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))
\t\t\t(layer "F.Cu" (type "copper") (thickness 0.035))
\t\t\t(layer "dielectric 1" (type "prepreg") (thickness 0.2104) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
\t\t\t(layer "In1.Cu" (type "copper") (thickness 0.0175))
\t\t\t(layer "dielectric 2" (type "core") (thickness 1.065) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
\t\t\t(layer "In2.Cu" (type "copper") (thickness 0.0175))
\t\t\t(layer "dielectric 3" (type "prepreg") (thickness 0.2104) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
\t\t\t(layer "B.Cu" (type "copper") (thickness 0.035))
\t\t\t(layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))
\t\t\t(layer "B.Paste" (type "Bottom Solder Paste"))
\t\t\t(layer "B.SilkS" (type "Bottom Silk Screen"))
\t\t\t(copper_finish "ENIG")
\t\t\t(dielectric_constraints no)
\t\t)
\t\t(pcbplotparams
\t\t\t(layerselection 0x00010fc_ffffffff)
\t\t\t(plot_on_all_layers_selection 0x0000000_00000000)
\t\t\t(disableapertmacros no) (usegerberextensions no) (usegerberattributes yes)
\t\t\t(usegerberadvancedattributes yes) (creategerberjobfile yes)
\t\t\t(dashed_line_dash_ratio 12.000000) (dashed_line_gap_ratio 3.000000)
\t\t\t(svgprecision 4) (plotframeref no) (mode 1) (useauxorigin no)
\t\t\t(dxfpolygonmode yes) (dxfimperialunits yes) (dxfusepcbnewfont yes)
\t\t\t(psnegative no) (psa4output no) (plot_black_and_white yes)
\t\t\t(sketchpadsonfab no) (plotpadnumbers no) (hidednponfab no)
\t\t\t(sketchdnponfab yes) (crossoutdnponfab yes) (subtractmaskfromsilk no)
\t\t\t(outputformat 1) (mirror no) (drillshape 1) (scaleselection 1)
\t\t\t(outputdirectory "")
\t\t)
\t)''')
    o.append('\t(net 0 "")')
    # rounded rectangular outline
    x1, y1, x2, y2 = X0, Y0, X0 + W, Y0 + H
    seg = lambda ax, ay, bx, by: (f'\t(gr_line (start {ax} {ay}) (end {bx} {by}) '
                                  f'(stroke (width 0.1) (type default)) (layer "Edge.Cuts"))')
    arc = lambda ax, ay, mx, my, bx, by: (f'\t(gr_arc (start {ax} {ay}) (mid {mx} {my}) '
                                          f'(end {bx} {by}) (stroke (width 0.1) (type default)) '
                                          f'(layer "Edge.Cuts"))')
    k = R * (1 - 0.70710678)
    o += [seg(x1+R, y1, x2-R, y1), seg(x2, y1+R, x2, y2-R),
          seg(x2-R, y2, x1+R, y2), seg(x1, y2-R, x1, y1+R),
          arc(x2-R, y1, x2-k, y1+k, x2, y1+R),
          arc(x2, y2-R, x2-k, y2-k, x2-R, y2),
          arc(x1+R, y2, x1+k, y2-k, x1, y2-R),
          arc(x1, y1+R, x1+k, y1+k, x1+R, y1)]
    for tx, ty, txt, sz in ((x1+4, y1+5, 'ODIN', 3.0),
                            (x1+4, y1+10, 'XC7A50T + RP2350B  |  4 layer  |  see README.md', 1.5)):
        o.append(f'\t(gr_text "{txt}" (at {tx} {ty}) (layer "F.SilkS") '
                 f'(effects (font (size {sz} {sz}) (thickness {sz/6:.2f})) (justify left)))')
    o.append(')')
    open(OUT, 'w').write('\n'.join(o) + '\n')
    print(f"wrote {OUT}: {W}x{H}mm, 4 layers, ENIG")

main()
