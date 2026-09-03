#!/usr/bin/env python3
"""Render tools/design.py into a hierarchical, multi-sheet KiCad 9 project.

One page per functional block. Parts are grouped, not scattered: the big parts
go in a row along the top, their passives cluster underneath by what they
connect to. Power and ground use real power symbols, so only actual signals
carry a label."""
import sys, os, re, uuid, hashlib
sys.path.insert(0, os.path.dirname(__file__))
import symlib
from design import build

DIR    = 'kicad'
PWRLIB = '/usr/share/kicad/symbols/power.kicad_sym'
SHEETS = ['FPGA', 'Power', 'Memory', 'Supervisor', 'Slots', 'HighSpeed']
TITLE  = {'FPGA':'FPGA, decoupling and configuration straps',
          'Power':'Power tree: 12V input to every rail, with monitoring',
          'Memory':'PSRAM x4 (independent buses) and configuration flash',
          'Supervisor':'RP2350B supervisor, USB-C, flash, and the links to the FPGA',
          'Slots':'Nine extension slots, rail selection, fusing, level shifting',
          'HighSpeed':'Four serial lanes: SFP cages, reference clock, power gate'}
GNDS   = {'GND'}
RAILS  = {'+1V0':'power:+1V0', '+1V1':'power:+1V1', '+1V8':'power:+1V8',
          '+2V5':'power:+2V5', '+3V3':'power:+3V3', '+5V':'power:+5V',
          'VSYS':'odin:VSYS', 'VBUS':'power:VBUS',
          'VCCIO_1':'odin:VCCIO_1', 'VCCIO_2':'odin:VCCIO_2',
          '+1V0_MGT':'odin:+1V0_MGT', '+1V2_MGT':'odin:+1V2_MGT',
          'PD_VDD':'odin:PD_VDD',
          'SFP_VCC':'odin:SFP_VCC'}
PWRSYM = dict(RAILS); PWRSYM['GND'] = 'power:GND'
# a rail's flag belongs on the page where that rail is actually made
RAIL_HOME = {'GND':'Power', 'VSYS':'Power', '+5V':'Power', '+3V3':'Power',
             '+2V5':'Power', '+1V8':'Power', '+1V0':'Power',
             '+1V2_MGT':'Power', '+1V0_MGT':'Power',
             '+1V1':'Supervisor', 'VBUS':'Supervisor', 'PD_VDD':'Supervisor',
             'SFP_VCC':'HighSpeed', 'VCCIO_1':'Slots', 'VCCIO_2':'Slots'}
DIRV = {0: (-2.54, 0), 180: (2.54, 0), 90: (0, 2.54), 270: (0, -2.54)}
JUST = {0: 'right', 180: 'left', 90: 'right', 270: 'left'}

def snap(v): return round(round(v / 1.27) * 1.27, 2)
def uid(*a): return str(uuid.UUID(hashlib.md5(('odin'+''.join(map(str,a))).encode()).hexdigest()))
def esc(s): return s.replace('\\','\\\\').replace('"','\\"')

def top_props(blk):
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
    lib, name = lib_id.split(':', 1)
    s = symlib.get(lib_id)
    ext = re.search(r'\(extends "([^"]+)"\)', s['block'])
    if not ext:
        blk = s['block']
    else:
        base, der, bname = s['base'], s['block'], ext.group(1)
        blk = re.sub(r'\(symbol "%s(_\d+_\d+)?"' % re.escape(bname),
                     lambda m: f'(symbol "{name}{m.group(1) or ""}"', base)
        dtext = [der[a:b] for a, b in top_props(der)]
        spans = top_props(blk)
        if spans and dtext:
            blk = blk[:spans[0][0]] + ''.join(dtext) + blk[spans[-1][1]:]
        blk = blk.replace(f'(extends "{bname}")', '', 1)
    return '\t\t' + re.sub(r'^\(symbol "%s"' % re.escape(name),
                           f'(symbol "{lib_id}"', blk, count=1)

def pin_geom(lib_id):
    src = symlib.get(lib_id)['base']
    out = {}
    for m in re.finditer(r'\(symbol "[^"]*_(\d+)_(\d+)"(.*?)(?=\n\t\t\(symbol "|\Z)', src, re.S):
        u = int(m.group(1))
        for pm in re.finditer(r'\(pin \w+ line\s*\n?\s*\(at ([-\d.]+) ([-\d.]+) (\d+)\)'
                              r'.*?\(number "([^"]*)"', m.group(3), re.S):
            out[pm.group(4)] = (float(pm.group(1)), float(pm.group(2)), int(pm.group(3)), u)
    return out

GEOM = {}
def geom(lib_id):
    if lib_id not in GEOM: GEOM[lib_id] = pin_geom(lib_id)
    return GEOM[lib_id]

def extent(lib_id, unit):
    g = [(x, y) for (x, y, r, pu) in geom(lib_id).values() if pu in (unit, 0)] or [(0, 0)]
    return max(abs(x) for x, _ in g), max(abs(y) for _, y in g)

def sig(part):
    """Cluster key: identical passives on identical nets sit together."""
    return (part['value'], tuple(sorted(set(part['pins'].values()))))

# --------------------------------------------------------------------- render
PWRN = [0]

def render_sheet(name, parts, root_uuid, sheet_uuid):
    o, body = [], []
    libs = sorted({p['lib_id'] for p in parts})
    used_pwr, nets_used = set(), set()

    # --- lay each logical group out as its own compact block, then pack blocks
    groups, order = {}, []
    for p in parts:
        g = p.get('group') or name
        if g not in groups: groups[g] = []; order.append(g)
        groups[g].append(p)

    def layout(gparts):
        """-> (items[(part,unit,relx,rely)], w, h) laid out inside one block."""
        anc = [q for q in gparts if len(geom(q['lib_id'])) > 4]
        pas = sorted([q for q in gparts if len(geom(q['lib_id'])) <= 4], key=sig)
        items, x, y, rowh, w = [], 0.0, 0.0, 0.0, 0.0
        WRAP = 640.0
        for q in anc:
            for u in symlib.get(q['lib_id'])['units']:
                ex, ey = extent(q['lib_id'], u)
                cw, ch = 2*(ex + 32) + 12, 2*ey + 34
                if x and x + cw > WRAP: x, y, rowh = 0.0, y + rowh + 10, 0.0
                items.append((q, u, x + cw/2, y + ch/2))
                x += cw; rowh = max(rowh, ch); w = max(w, x)
        if anc and pas: x, y, rowh = 0.0, y + rowh + 8, 0.0
        for q in pas:
            ex, ey = extent(q['lib_id'], 1)
            cw, ch = 2*(ex + 14) + 5, 2*ey + 30
            if x and x + cw > WRAP: x, y, rowh = 0.0, y + rowh + 8, 0.0
            items.append((q, 1, x + cw/2, y + ch/2))
            x += cw; rowh = max(rowh, ch); w = max(w, x)
        return items, w, y + rowh

    blocks = []
    for g in order:
        items, w, h = layout(groups[g])
        blocks.append((g, items, w, h))

    SHEET_W = max(360.0, min(1100.0, 1.25 * (sum(b[2]+18 for b in blocks) ** 0.5) * 9))
    placed, boxes = [], []
    cx, cy, rowh, used_w = 30.0, 42.0, 0.0, 0.0
    for g, items, w, h in blocks:
        if cx > 30.0 and cx + w + 18 > SHEET_W:
            cx, cy, rowh = 30.0, cy + rowh + 20, 0.0
        gx, gy = cx + 9, cy + 12
        for q, u, rx, ry in items:
            placed.append((q, u, snap(gx + rx), snap(gy + ry)))
        boxes.append((g, snap(cx), snap(cy), snap(cx + w + 18), snap(cy + h + 18)))
        cx += w + 18 + 12; rowh = max(rowh, h + 18); used_w = max(used_w, cx)
    sheet_h = cy + rowh + 30

    for g, x1, y1, x2, y2 in boxes:
        body.append(f'\t(rectangle (start {x1} {y1}) (end {x2} {y2}) '
                    '(stroke (width 0.15) (type dash)) (fill (type none)) '
                    f'(uuid "{uid("box", name, g)}"))')
        body.append(f'\t(text "{esc(g)}" (at {snap(x1+2)} {snap(y1+4)} 0) '
                    '(effects (font (size 2.2 2.2) (thickness 0.3)) (justify left)))')

    for p, u, ox, oy in placed:
        body.append(f'\t(symbol (lib_id "{p["lib_id"]}") (at {ox} {oy} 0) (unit {u})')
        body.append('\t\t(exclude_from_sim no) (in_bom yes) (on_board yes) '
                    f'(dnp {"yes" if p["dnp"] else "no"})')
        body.append(f'\t\t(uuid "{uid(p["ref"], u)}")')
        ey = extent(p['lib_id'], u)[1]
        for k, v, hide in (('Reference', p['ref'], False), ('Value', p['value'], False),
                           ('Footprint', p['fp'], True), ('LCSC', p['lcsc'], True)):
            if k == 'LCSC' and not v: continue
            yy = snap(oy - ey - 3.81) if k == 'Reference' else snap(oy + ey + 3.81)
            body.append(f'\t\t(property "{k}" "{esc(v)}" (at {ox} {yy} 0) '
                        f'(effects (font (size 1.27 1.27)){" (hide yes)" if hide else ""}))')
        body.append(f'\t\t(instances (project "odin" (path "/{root_uuid}/{sheet_uuid}" '
                    f'(reference "{p["ref"]}") (unit {u}))))')
        body.append('\t)')
        u0 = symlib.get(p['lib_id'])['units'][0]
        for num, (px, py, rot, pu) in geom(p['lib_id']).items():
            if pu != u and not (pu == 0 and u == u0): continue
            sx, sy = snap(ox + px), snap(oy - py)
            net = p['pins'].get(num)
            if not net:
                body.append(f'\t(no_connect (at {sx} {sy}) (uuid "{uid("nc",p["ref"],num)}"))')
                continue
            dx, dy = DIRV[rot]
            ex_, ey_ = snap(sx + dx), snap(sy + dy)
            body.append(f'\t(wire (pts (xy {sx} {sy}) (xy {ex_} {ey_})) '
                        f'(stroke (width 0) (type default)) (uuid "{uid("w",p["ref"],num)}"))')
            if net in PWRSYM:
                want = 1 if net in GNDS else -1              # gnd goes down, rails go up
                if dy == 0:
                    # No vertical bend here. Pins on a big IC sit 2.54 apart, so a
                    # bend runs straight through the neighbouring pin's stub and
                    # shorts them. Rotate the symbol to lie along the stub instead.
                    fx, fy = ex_, ey_
                    prot = 90 if dx < 0 else 270
                else:
                    fx, fy = ex_, ey_
                    prot = 0 if (dy > 0) == (want > 0) else 180
                body.append(f'\t(symbol (lib_id "{PWRSYM[net]}") (at {fx} {fy} {prot}) (unit 1)')
                body.append('\t\t(exclude_from_sim no) (in_bom no) (on_board yes) (dnp no)')
                body.append(f'\t\t(uuid "{uid("pw",p["ref"],num)}")')
                PWRN[0] += 1
                pref = f'#PWR{PWRN[0]:04d}'
                body.append(f'\t\t(property "Reference" "{pref}" (at {fx} {fy} 0) '
                            '(effects (font (size 1.27 1.27)) (hide yes)))')
                voff = (0, 3.81*want) if prot == 0 else ((-3.81 if prot == 90 else 3.81), 0)
                body.append(f'\t\t(property "Value" "{net}" '
                            f'(at {snap(fx+voff[0])} {snap(fy+voff[1])} 0) '
                            '(effects (font (size 1.27 1.27))))')
                body.append(f'\t\t(instances (project "odin" (path "/{root_uuid}/{sheet_uuid}" '
                            f'(reference "{pref}") (unit 1))))')
                body.append('\t)')
                used_pwr.add(net)
            else:
                body.append(f'\t(global_label "{esc(net)}" (shape passive) '
                            f'(at {ex_} {ey_} {rot}) (fields_autoplaced yes) '
                            f'(effects (font (size 1.27 1.27)) (justify {JUST[rot]})) '
                            f'(uuid "{uid("gl",p["ref"],num)}"))')
                nets_used.add(net)

    mine = [r for r in sorted(PWRSYM) if RAIL_HOME[r] == name]
    if mine:
        for i, r in enumerate(mine):
            fx, fy = snap(40 + i * 35.56), snap(sheet_h + 20)
            up = -1 if r not in GNDS else 1
            body.append(f'\t(symbol (lib_id "power:PWR_FLAG") (at {fx} {fy} 0) (unit 1)')
            body.append('\t\t(exclude_from_sim no) (in_bom no) (on_board yes) (dnp no)')
            body.append(f'\t\t(uuid "{uid("flg", r)}")')
            body.append(f'\t\t(property "Reference" "#FLG{name[:2].upper()}{i:02d}" (at {fx} {fy} 0) '
                        '(effects (font (size 1.27 1.27)) (hide yes)))')
            body.append(f'\t\t(property "Value" "PWR_FLAG" (at {fx} {snap(fy-6)} 0) '
                        '(effects (font (size 1.27 1.27))))')
            body.append(f'\t\t(instances (project "odin" (path "/{root_uuid}/{sheet_uuid}" '
                        f'(reference "#FLG{name[:2].upper()}{i:02d}") (unit 1))))')
            body.append('\t)')
            ty = snap(fy + up * 5.08)
            body.append(f'\t(wire (pts (xy {fx} {fy}) (xy {fx} {ty})) '
                        f'(stroke (width 0) (type default)) (uuid "{uid("fw", r)}"))')
            PWRN[0] += 1
            body.append(f'\t(symbol (lib_id "{PWRSYM[r]}") (at {fx} {ty} 0) (unit 1)')
            body.append('\t\t(exclude_from_sim no) (in_bom no) (on_board yes) (dnp no)')
            body.append(f'\t\t(uuid "{uid("fpw", r)}")')
            body.append(f'\t\t(property "Reference" "#PWR{PWRN[0]:04d}" (at {fx} {ty} 0) '
                        '(effects (font (size 1.27 1.27)) (hide yes)))')
            body.append(f'\t\t(property "Value" "{r}" (at {fx} {snap(ty+up*3.81)} 0) '
                        '(effects (font (size 1.27 1.27))))')
            body.append(f'\t\t(instances (project "odin" (path "/{root_uuid}/{sheet_uuid}" '
                        f'(reference "#PWR{PWRN[0]:04d}") (unit 1))))')
            body.append('\t)')
            used_pwr.add(r)
        body.append(f'\t(text "Power flags for the rails made on this page" '
                    f'(at 30 {snap(sheet_h+4)} 0) '
                    '(effects (font (size 2 2)) (justify left)))')
        sheet_h += 40
        libs = sorted(set(libs) | {'power:PWR_FLAG'})

    o = ['(kicad_sch', '\t(version 20250114)', '\t(generator "odin-tools")',
         '\t(generator_version "9.0")', f'\t(uuid "{sheet_uuid}")',
         f'\t(paper "User" {max(used_w+50, 297):.0f} {sheet_h+40:.0f})', '\t(lib_symbols']
    for l in libs: o.append(flatten(l))
    for r in sorted(used_pwr): o.append(flatten(PWRSYM[r]))
    o.append('\t)')
    o.append(f'\t(text "{esc(name.upper())}  —  {esc(TITLE[name])}" (at 40 20 0) '
             '(effects (font (size 4 4) (thickness 0.6)) (justify left)))')
    o += body
    o.append(')')
    return '\n'.join(o) + '\n', len(placed), sheet_h

def main():
    d = build()
    root = uid('root')
    sh_uuid = {s: uid('sheet', s) for s in SHEETS}
    total = 0
    for s in SHEETS:
        parts = [p for p in d.parts if p['sheet'] == s]
        txt, n, h = render_sheet(s, parts, root, sh_uuid[s])
        open(f'{DIR}/{s.lower()}.kicad_sch', 'w').write(txt)
        print(f"  {s:11s} {len(parts):4d} parts, {n:4d} placements")
        total += len(parts)

    r = ['(kicad_sch', '\t(version 20250114)', '\t(generator "odin-tools")',
         '\t(generator_version "9.0")', f'\t(uuid "{root}")', '\t(paper "A3")',
         '\t(lib_symbols\n\t)',
         '\t(text "ODIN" (at 30 25 0) (effects (font (size 8 8) (thickness 1.2)) (justify left)))',
         '\t(text "Artix-7 dev board. Every page is generated — see kicad/README.md"'
         ' (at 30 34 0) (effects (font (size 3 3)) (justify left)))']
    for i, s in enumerate(SHEETS):
        x, y = 30 + (i % 3) * 120, 55 + (i // 3) * 60
        r.append(f'\t(sheet (at {x} {y}) (size 95 40)')
        r.append('\t\t(stroke (width 0.1524) (type solid)) (fill (color 0 0 0 0.0000))')
        r.append(f'\t\t(uuid "{sh_uuid[s]}")')
        r.append(f'\t\t(property "Sheetname" "{s}" (at {x} {y-1} 0) '
                 '(effects (font (size 2.5 2.5)) (justify left bottom)))')
        r.append(f'\t\t(property "Sheetfile" "{s.lower()}.kicad_sch" (at {x} {y+41} 0) '
                 '(effects (font (size 2 2)) (justify left top)))')
        r.append(f'\t\t(instances (project "odin" (path "/{root}" (page "{i+2}"))))')
        r.append('\t)')
        r.append(f'\t(text "{esc(TITLE[s])}" (at {x+3} {y+12} 0) '
                 '(effects (font (size 2 2)) (justify left)))')
    r.append('\t(sheet_instances (path "/" (page "1")))')
    r.append(')')
    open(f'{DIR}/odin.kicad_sch', 'w').write('\n'.join(r) + '\n')
    print(f"  root + {len(SHEETS)} pages, {total} parts")

if __name__ == '__main__':
    main()
