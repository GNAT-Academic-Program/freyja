#!/usr/bin/env python3
"""Render ref/floorplan.svg from tools/placement.py. No KiCad needed."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import placement as pl

S = 7.0  # px per mm

def rect(x0, y0, x1, y1, fill, label='', stroke='#444'):
    w, h = (x1 - x0) * S, (y1 - y0) * S
    r = (f'<rect x="{x0*S:.1f}" y="{y0*S:.1f}" width="{w:.1f}" height="{h:.1f}" '
         f'fill="{fill}" stroke="{stroke}" stroke-width="1"/>')
    if label:
        cx, cy = (x0 + x1) / 2 * S, (y0 + y1) / 2 * S
        vert = (y1 - y0) > (x1 - x0) * 2
        tr = f' transform="rotate(-90 {cx:.1f} {cy:.1f})"' if vert else ''
        r += (f'<text x="{cx:.1f}" y="{cy:.1f}" font-size="9" text-anchor="middle" '
              f'dominant-baseline="middle" font-family="monospace"{tr}>{label}</text>')
    return r

def main():
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{int(110*S)}" '
           f'height="{int(110*S)}" viewBox="{-5*S} {-9*S} {110*S} {115*S}">',
           rect(0, 0, pl.BOARD_W, pl.BOARD_H, '#f7f5ef', stroke='#000')]
    colors = {'J': '#cfe3f5', 'M': '#f5d9cf', 'S': '#ddd', 'U': '#d9f0d0', 'X': '#f5eecf'}
    for p in pl.contract():
        stem = pl.CONTRACT_FP.get(p.ref)
        b = pl._fp_bbox(stem) if stem else None
        if b:
            x0, x1, y0, y1 = pl._rot_bbox(b, p.rot)
            out.append(rect(p.x + x0, p.y + y0, p.x + x1, p.y + y1,
                            colors.get(p.ref[0], '#eee'), p.ref))
        else:
            out.append(rect(p.x - 2, p.y - 2, p.x + 2, p.y + 2, '#f5eecf', p.ref))
    for g, (x, y, d) in pl.ANCHORS.items():
        out.append(f'<circle cx="{x*S:.1f}" cy="{y*S:.1f}" r="2.5" fill="#a33"/>')
        out.append(f'<text x="{x*S+4:.1f}" y="{y*S+3:.1f}" font-size="7" '
                   f'font-family="monospace" fill="#a33">{g[:22]}</text>')
    out.append('</svg>')
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'ref', 'floorplan.svg')
    open(path, 'w').write('\n'.join(out))
    print('wrote', path)

if __name__ == '__main__':
    main()
