#!/usr/bin/env python3
"""Generate KiCad 9 symbol + footprint for XC7A50T-2CSG325I from the AMD
package file. Reproducible:  python3 tools/gen_kicad.py
Outputs kicad/odin.kicad_sym and kicad/odin.pretty/*.kicad_mod
"""
import re, os
from collections import defaultdict, OrderedDict

PKG   = 'ref/xc7a50tcsg325pkg.txt'
SYM   = 'kicad/odin.kicad_sym'
PRET  = 'kicad/odin.pretty'
FPNAME= 'BGA-324_15x15mm_Layout18x18_P0.8mm'
PART  = 'XC7A50T-2CSG325I'
LCSC  = ''   # filled from BOM when the new export lands
DS    = 'https://docs.amd.com/v/u/en-US/ds181_Artix_7_Data_Sheet'

ROWS = list('ABCDEFGH') + list('JKLMN') + ['P','R','T','U','V']   # 18, I/O/Q/S skipped
NCOL = 18
PITCH = 0.8

def load():
    out = []
    for l in open(PKG, encoding='utf-8', errors='replace'):
        l = l.replace('\r', '').rstrip()
        if not l.strip() or l.startswith(('Device/Package', 'Pin ', 'Total Number')): continue
        f = re.split(r'\s{2,}', l.strip())
        if len(f) >= 7: out.append((f[0], f[1], f[3], f[6]))   # ball, name, bank, iotype
    return out

def etype(name, iot):
    n = name.upper()
    if n.startswith('GND'):                       return 'power_in'
    if n.startswith(('VCC', 'VREFP', 'VREFN')):   return 'power_in'
    if n.startswith('NC'):                        return 'no_connect'
    if n.startswith('MGTPTX'):                    return 'output'
    if n.startswith('MGTPRX'):                    return 'input'
    if n.startswith('MGTREFCLK'):                 return 'input'
    if n.startswith('MGTRREF'):                   return 'passive'
    if n.startswith(('TCK', 'TMS', 'TDI')):       return 'input'
    if n.startswith('TDO'):                       return 'output'
    if n.startswith('DONE'):                      return 'output'
    if n.startswith(('CCLK', 'INIT_B', 'PROGRAM_B')): return 'bidirectional'
    if n.startswith(('M0_', 'M1_', 'M2_', 'CFGBVS')): return 'input'
    if n.startswith(('VP_', 'VN_', 'DXP', 'DXN')):    return 'passive'
    if iot == 'HR':                               return 'bidirectional'
    return 'passive'

def esc(s): return s.replace('\\', '\\\\').replace('"', '\\"')

def pin(x, y, rot, et, name, num, length=5.08):
    return (f'\t\t\t(pin {et} line\n'
            f'\t\t\t\t(at {x:.2f} {y:.2f} {rot})\n'
            f'\t\t\t\t(length {length})\n'
            f'\t\t\t\t(name "{esc(name)}" (effects (font (size 1.27 1.27))))\n'
            f'\t\t\t\t(number "{num}" (effects (font (size 1.27 1.27))))\n'
            f'\t\t\t)\n')

def build_units(pins):
    """-> OrderedDict unit_label -> list[(ball,name,etype)]"""
    bybank = defaultdict(list)
    for ball, name, bank, iot in pins:
        bybank[bank].append((ball, name, etype(name, iot)))
    units = OrderedDict()
    units['Bank 0 / config'] = sorted(bybank['0'])
    for bk in ('14', '15', '34'):
        units[f'Bank {bk}'] = sorted(bybank[bk])
    units['Bank 216 / GTP'] = sorted(bybank['216'])
    na = bybank['NA']
    units['GND']    = sorted([p for p in na if p[1].upper().startswith('GND')])
    units['Supply'] = sorted([p for p in na if not p[1].upper().startswith('GND')])
    return units

def unit_body(idx, items):
    """Two columns: first half left (pointing right), second half right."""
    half = (len(items) + 1) // 2
    left, right = items[:half], items[half:]
    h = max(len(left), len(right))
    top = (h - 1) * 2.54 / 2
    W = 63.5
    s  = f'\t\t(symbol "{PART}_{idx}_1"\n'
    s += (f'\t\t\t(rectangle (start {-W/2:.2f} {top+5.08:.2f}) (end {W/2:.2f} {top-(h-1)*2.54-5.08:.2f})\n'
          f'\t\t\t\t(stroke (width 0.254) (type default)) (fill (type background))\n\t\t\t)\n')
    for i, (ball, name, et) in enumerate(left):
        s += pin(-W/2 - 5.08, top - i*2.54, 0, et, name, ball)
    for i, (ball, name, et) in enumerate(right):
        s += pin(W/2 + 5.08, top - i*2.54, 180, et, name, ball)
    return s + '\t\t)\n'

def gen_symbol(pins):
    units = build_units(pins)
    o  = '(kicad_symbol_lib\n\t(version 20241209)\n\t(generator "odin-tools")\n\t(generator_version "9.0")\n'
    o += f'\t(symbol "{PART}"\n'
    o += '\t\t(pin_names (offset 1.016))\n\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n'
    props = [('Reference','U',False), ('Value',PART,False),
             ('Footprint',f'odin:{FPNAME}',True), ('Datasheet',DS,True),
             ('Description','Xilinx Artix-7 XC7A50T, CSG325 0.8mm 18x18 BGA, 324 balls',True),
             ('LCSC',LCSC,True)]
    for i,(k,v,hide) in enumerate(props):
        o += (f'\t\t(property "{k}" "{esc(v)}"\n\t\t\t(at 0 {40-i*2.54:.2f} 0)\n'
              f'\t\t\t(effects (font (size 1.27 1.27)){" (hide yes)" if hide else ""})\n\t\t)\n')
    for i, (label, items) in enumerate(units.items(), start=1):
        o += unit_body(i, items)
    o += '\t)\n)\n'
    open(SYM, 'w').write(o)
    return units

def gen_footprint():
    os.makedirs(PRET, exist_ok=True)
    span = (NCOL - 1) * PITCH
    off  = span / 2.0
    body = 15.0
    o  = f'(footprint "{FPNAME}"\n\t(version 20241229)\n\t(generator "odin-tools")\n\t(generator_version "9.0")\n'
    o += '\t(layer "F.Cu")\n\t(descr "Xilinx CSG325, 18x18 BGA, 0.8mm pitch, 324 balls, 15x15mm body")\n'
    o += '\t(tags "BGA 324 0.8mm")\n\t(attr smd)\n'
    o += ('\t(property "Reference" "U**" (at 0 -9 0) (layer "F.SilkS")\n'
          '\t\t(effects (font (size 1 1) (thickness 0.15)))\n\t)\n')
    o += (f'\t(property "Value" "{FPNAME}" (at 0 9 0) (layer "F.Fab")\n'
          '\t\t(effects (font (size 1 1) (thickness 0.15)))\n\t)\n')
    # silk: corner ticks + pin-A1 dot
    b = body/2
    for (x1,y1,x2,y2) in [(-b,-b,-b+2,-b), (-b,-b,-b,-b+2), (b-2,-b,b,-b), (b,-b,b,-b+2),
                          (-b,b-2,-b,b), (-b,b,-b+2,b), (b-2,b,b,b), (b,b-2,b,b)]:
        o += (f'\t(fp_line (start {x1} {y1}) (end {x2} {y2}) (stroke (width 0.12) (type solid))'
              f' (layer "F.SilkS"))\n')
    o += f'\t(fp_circle (center {-b-0.8} {-b-0.8}) (end {-b-0.4} {-b-0.8}) (stroke (width 0.3) (type solid)) (fill solid) (layer "F.SilkS"))\n'
    o += (f'\t(fp_rect (start {-b-0.25} {-b-0.25}) (end {b+0.25} {b+0.25})'
          f' (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd"))\n')
    o += (f'\t(fp_rect (start {-b} {-b}) (end {b} {b})'
          f' (stroke (width 0.1) (type solid)) (fill none) (layer "F.Fab"))\n')
    n = 0
    for r, rl in enumerate(ROWS):
        for c in range(1, NCOL+1):
            x = -off + (c-1)*PITCH
            y = -off + r*PITCH
            o += (f'\t(pad "{rl}{c}" smd circle (at {x:.3f} {y:.3f}) (size 0.4 0.4)'
                  f' (layers "F.Cu" "F.Paste" "F.Mask"))\n')
            n += 1
    o += ')\n'
    open(f'{PRET}/{FPNAME}.kicad_mod', 'w').write(o)
    return n

if __name__ == '__main__':
    pins = load()
    units = gen_symbol(pins)
    npads = gen_footprint()
    print(f"symbol  {SYM}: {len(pins)} pins in {len(units)} units")
    for k, v in units.items(): print(f"   unit {k:18s} {len(v):3d} pins")
    print(f"footprint {PRET}/{FPNAME}.kicad_mod: {npads} pads")
    assert npads == len(pins) == 324, (npads, len(pins))
    print("pad count matches ball count")
