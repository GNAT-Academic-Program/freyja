#!/usr/bin/env python3
"""Render tools/design.py into a complete KiCad 9 project."""
import sys, os, re, uuid, hashlib
sys.path.insert(0, os.path.dirname(__file__))
import symlib
from design import build

OUT, PRO = 'kicad/odin.kicad_sch', 'kicad/odin.kicad_pro'
PWRLIB = '/usr/share/kicad/symbols/power.kicad_sym'
SHEET_W, LBL, MARGIN = 1120.0, 33.0, 12.0
RAILS = ('GND','+1V0','+1V1','+1V8','+2V5','+3V3','+5V','+12V',
         'VCCIO_1','VCCIO_2','+1V0_MGT','+1V2_MGT','VBUS','SFP_VCC')

def snap(v): return round(round(v / 1.27) * 1.27, 2)
def uid(*a): return str(uuid.UUID(hashlib.md5(('odin'+''.join(map(str,a))).encode()).hexdigest()))
def esc(s): return s.replace('\\','\\\\').replace('"','\\"')

def top_props(blk):
    """Yield (start, end) of each top-level (property ...) in a symbol block."""
    out, i = [], 0
    while True:
        i = blk.find('\n\t\t(property "', i)
        if i < 0: return out
        j, dep = i + 1, 0
        while True:
            if blk[j] == '(': dep += 1
            elif blk[j] == ')':
                dep -= 1
                if dep == 0: break
            j += 1
        out.append((i, j + 1)); i = j

def flatten(lib_id):
    """Return a self-contained lib_symbols block for lib_id (resolving `extends`)."""
    lib, name = lib_id.split(':', 1)
    s = symlib.get(lib_id)
    ext = re.search(r'\(extends "([^"]+)"\)', s['block'])
    if not ext:
        blk = s['block']
    else:
        base, der = s['base'], s['block']
        bname = ext.group(1)
        blk = re.sub(r'\(symbol "%s(_\d+_\d+)?"' % re.escape(bname),
                     lambda m: f'(symbol "{name}{m.group(1) or ""}"', base)
        # the derived symbol's property blocks replace the base's wholesale --
        # KiCad compares position and effects too, not just the value string
        dtext = [der[a:b] for a, b in top_props(der)]
        spans = top_props(blk)
        if spans and dtext:
            blk = blk[:spans[0][0]] + ''.join(dtext) + blk[spans[-1][1]:]
        blk = blk.replace(f'(extends "{bname}")', '', 1)
    # top-level name carries the library prefix; sub-unit names must not
    return '\t\t' + re.sub(r'^\(symbol "%s"' % re.escape(name),
                           f'(symbol "{lib_id}"', blk, count=1)

def pwr_flag():
    t = open(PWRLIB).read(); i = t.index('(symbol "PWR_FLAG"')
    d, j = 1, i + len('(symbol "PWR_FLAG"')
    while d > 0:
        if t[j] == '(': d += 1
        elif t[j] == ')': d -= 1
        j += 1
    return '\t\t' + t[i:j].replace('(symbol "PWR_FLAG"', '(symbol "power:PWR_FLAG"', 1)

def pin_geom(lib_id):
    """-> {pin_number: (x, y, rot, unit)} in symbol coordinates."""
    s = symlib.get(lib_id)
    src = s['base']
    out = {}
    for m in re.finditer(r'\(symbol "[^"]*_(\d+)_(\d+)"(.*?)(?=\n\t\t\(symbol "|\Z)', src, re.S):
        u = int(m.group(1))
        for pm in re.finditer(r'\(pin \w+ line\s*\n?\s*\(at ([-\d.]+) ([-\d.]+) (\d+)\)'
                              r'.*?\(number "([^"]*)"', m.group(3), re.S):
            out[pm.group(4)] = (float(pm.group(1)), float(pm.group(2)), int(pm.group(3)), u)
    return out

DIRV = {0: (-2.54, 0), 180: (2.54, 0), 90: (0, 2.54), 270: (0, -2.54)}
JUST = {0: 'right', 180: 'left', 90: 'right', 270: 'left'}

def main():
    d = build()
    libs = sorted({p['lib_id'] for p in d.parts})
    geom = {l: pin_geom(l) for l in libs}

    o = ['(kicad_sch', '\t(version 20250114)', '\t(generator "odin-tools")',
         '\t(generator_version "9.0")', f'\t(uuid "{uid("root")}")',
         '\t(paper "User" %.0f %.0f)' % (SHEET_W + 60, 0), '\t(lib_symbols']
    for l in libs: o.append(flatten(l))
    o.append(pwr_flag())
    o.append('\t)')

    # one cell per part; multi-unit parts take one cell per unit.
    # Symbols range from a 2-pin 0402 to a 57-pin FPGA bank, so pack by real extent.
    def extent(lib_id, unit):
        g = [(x, y) for (x, y, r, pu) in geom[lib_id].values()
             if pu == unit or pu == 0] or [(0, 0)]
        return (max(abs(x) for x, _ in g), max(abs(y) for _, y in g))
    slots = []
    for p in d.parts:
        for u in symlib.get(p['lib_id'])['units']: slots.append((p, u))
    placed, cx, cy, rowh = [], MARGIN + 60, 60.0, 0.0
    for p, u in slots:
        ex, ey = extent(p['lib_id'], u)
        w, h = 2*(ex + LBL) + MARGIN, 2*ey + 34.0
        if cx + w > SHEET_W:
            cx, cy, rowh = MARGIN + 60, cy + rowh + MARGIN, 0.0
        placed.append((p, u, snap(cx + w/2), snap(cy + h/2)))
        cx += w; rowh = max(rowh, h)
    sheet_h = cy + rowh + 40
    nets_used = set()
    for p, u, ox, oy in placed:
        o.append(f'\t(symbol (lib_id "{p["lib_id"]}") (at {ox} {oy} 0) (unit {u})')
        o.append('\t\t(exclude_from_sim no) (in_bom yes) (on_board yes) '
                 f'(dnp {"yes" if p["dnp"] else "no"})')
        o.append(f'\t\t(uuid "{uid(p["ref"], u)}")')
        for k, v, hide in (('Reference', p['ref'], False), ('Value', p['value'], False),
                           ('Footprint', p['fp'], True), ('LCSC', p['lcsc'], True)):
            if k == 'LCSC' and not v: continue
            o.append(f'\t\t(property "{k}" "{esc(v)}" (at {ox} {oy-34} 0) '
                     f'(effects (font (size 1.27 1.27)){" (hide yes)" if hide else ""}))')
        o.append(f'\t\t(instances (project "odin" (path "/{uid("root")}" '
                 f'(reference "{p["ref"]}") (unit {u}))))')
        o.append('\t)')
        u0 = symlib.get(p['lib_id'])['units'][0]
        for num, (px, py, rot, pu) in geom[p['lib_id']].items():
            if pu != u and not (pu == 0 and u == u0): continue
            sx, sy = snap(ox + px), snap(oy - py)
            net = p['pins'].get(num)
            if not net:
                o.append(f'\t(no_connect (at {sx} {sy}) (uuid "{uid("nc",p["ref"],num)}"))')
                continue
            dx, dy = DIRV[rot]
            ex, ey = snap(sx + dx), snap(sy + dy)
            o.append(f'\t(wire (pts (xy {sx} {sy}) (xy {ex} {ey})) '
                     f'(stroke (width 0) (type default)) (uuid "{uid("w",p["ref"],num)}"))')
            o.append(f'\t(global_label "{esc(net)}" (shape passive) (at {ex} {ey} {rot}) '
                     f'(fields_autoplaced yes) (effects (font (size 1.27 1.27)) '
                     f'(justify {JUST[rot]})) (uuid "{uid("gl",p["ref"],num)}"))')
            nets_used.add(net)

    o[5] = '\t(paper "User" %.0f %.0f)' % (SHEET_W + 60, sheet_h + 40)
    rails = [r for r in RAILS if r in nets_used]
    for i, r in enumerate(rails):
        fx, fy = snap(60 + i * 55.88), snap(20)
        o.append(f'\t(symbol (lib_id "power:PWR_FLAG") (at {fx} {fy} 0) (unit 1)')
        o.append('\t\t(exclude_from_sim no) (in_bom no) (on_board yes) (dnp no)')
        o.append(f'\t\t(uuid "{uid("flg",r)}")')
        o.append(f'\t\t(property "Reference" "#FLG{i}" (at {fx} {fy-4} 0) '
                 '(effects (font (size 1.27 1.27)) (hide yes)))')
        o.append(f'\t\t(property "Value" "PWR_FLAG" (at {fx} {fy-6} 0) '
                 '(effects (font (size 1.27 1.27))))')
        o.append(f'\t\t(instances (project "odin" (path "/{uid("root")}" '
                 f'(reference "#FLG{i}") (unit 1))))')
        o.append('\t)')
        o.append(f'\t(wire (pts (xy {fx} {fy}) (xy {fx} {snap(fy+5.08)})) '
                 f'(stroke (width 0) (type default)) (uuid "{uid("fw",r)}"))')
        o.append(f'\t(global_label "{r}" (shape passive) (at {fx} {snap(fy+5.08)} 270) '
                 f'(fields_autoplaced yes) (effects (font (size 1.27 1.27)) '
                 f'(justify right)) (uuid "{uid("fgl",r)}"))')

    o.append('\t(sheet_instances (path "/" (page "1")))')
    o.append(')')
    open(OUT, 'w').write('\n'.join(o) + '\n')
    if not os.path.exists(PRO):
        open(PRO,'w').write('{\n "board": {},\n "libraries": {"pinned_footprint_libs": [],'
                            ' "pinned_symbol_libs": []},\n "meta": {"filename":'
                            ' "odin.kicad_pro", "version": 3},\n "sheets": [["%s", "Root"]],\n'
                            ' "text_variables": {}\n}\n' % uid("root"))
    print(f"{len(d.parts)} parts / {len(slots)} symbol placements, "
          f"{len(nets_used)} nets, {len(rails)} power flags -> {OUT}")

if __name__ == '__main__':
    main()
