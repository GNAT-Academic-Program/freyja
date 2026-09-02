#!/usr/bin/env python3
"""Derive a canonical IR for Odin.

Identity source is the EasyEDA Protel netlist (real designators). The Altium
ASCII .schdoc exports contribute sheet grouping, port structure and pin
geometry only -- their designators were renumbered by the exporter and are
never emitted downstream except inside odin.desigmap.

Outputs:
  odin.parts.ir    one line per netlist part, with BOM facts and home sheet
  odin.nets.ir     one line per netlist net, global, with the sheets it spans
  odin.desigmap    netlist refdes <-> schdoc refdes, per schdoc symbol part
  odin.bomdiff     netlist-vs-BOM designator differences

Schdoc connectivity rules (used only to derive the schdoc-side signature):
  - wire-wire: shared vertex, or junction on segment
  - pin/netlabel/port/powerport: point lies on a wire segment (inclusive)
Pins: electrical point = LOCATION + PINLENGTH along orientation (PINCONGLOMERATE & 3).
"""
import sys, os, glob, math, zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict

NETLIST = 'Netlist_Odin_0_2026-09-02.net'
SCHDOC_GLOB = 'Odin_V1.0.0/Odin/*.schdoc'
BOM_GLOB = 'BOM_*.xlsx'

# ---------------------------------------------------------------- schdoc side

def fnum(d, k):
    v = float(d.get(k, 0) or 0)
    fr = d.get(k + '_FRAC')
    if fr: v += float(fr) / 100000.0 * (1 if v >= 0 else -1)
    return v

def records(path):
    txt = open(path, encoding='utf-8', errors='replace').read()
    for line in txt.replace('\r', '\n').split('\n'):
        if not line.startswith('|'): continue
        d = {}
        for kv in line.strip('|').split('|'):
            if '=' in kv:
                k, v = kv.split('=', 1); d[k] = v
        yield d

class UF:
    def __init__(self): self.p = {}
    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]; x = self.p[x]
        return x
    def union(self, a, b): self.p[self.find(a)] = self.find(b)

def key(x, y): return (round(x * 100), round(y * 100))

def on_seg(px, py, x1, y1, x2, y2, tol=0.51):
    if min(x1,x2)-tol <= px <= max(x1,x2)+tol and min(y1,y2)-tol <= py <= max(y1,y2)+tol:
        cross = abs((x2-x1)*(py-y1) - (y2-y1)*(px-x1))
        seglen = math.hypot(x2-x1, y2-y1) or 1e-9
        return cross / seglen < tol
    return False

def parse_sheet(path):
    comps, pins, wires, junctions, labels, ports = [], [], [], [], [], []
    allrecs = list(records(path))
    comp_by_recidx = {}
    for i, r in enumerate(allrecs):
        if r.get('RECORD') == '1':
            comps.append({'lib': r.get('LIBREFERENCE',''), 'designator': None,
                          'value': None, 'footprint': None, 'recidx': i})
            comp_by_recidx[i] = len(comps)-1
    def owner_comp(r):
        oi = r.get('OWNERINDEX')
        if oi is None: return None
        oi = int(oi)
        for off in (0, 1, -1):
            j = oi + off
            if 0 <= j < len(allrecs) and j in comp_by_recidx:
                return comp_by_recidx[j]
        return None
    for r in allrecs:
        rec = r.get('RECORD')
        if rec == '34':
            ci = owner_comp(r)
            if ci is not None: comps[ci]['designator'] = r.get('TEXT','')
        elif rec == '41':
            ci = owner_comp(r)
            nm = (r.get('NAME') or '').lower()
            if ci is not None and nm == 'value': comps[ci]['value'] = r.get('TEXT','')
        elif rec == '45':
            ci = owner_comp(r)
            if ci is not None and comps[ci]['footprint'] is None:
                comps[ci]['footprint'] = r.get('MODELNAME','')
        elif rec == '2':
            ci = owner_comp(r)
            x, y = fnum(r,'LOCATION.X'), fnum(r,'LOCATION.Y')
            ln = float(r.get('PINLENGTH', 0) or 0)
            o = int(r.get('PINCONGLOMERATE', 0) or 0) & 3
            dx, dy = [(1,0),(0,1),(-1,0),(0,-1)][o]
            pins.append((ci, r.get('NAME',''), r.get('DESIGNATOR',''), x+dx*ln, y+dy*ln))
        elif rec == '27':
            n = int(r.get('LOCATIONCOUNT', 0) or 0)
            vs = [(fnum(r,f'X{i}'), fnum(r,f'Y{i}')) for i in range(1, n+1)]
            if len(vs) >= 2: wires.append(vs)
        elif rec == '29':
            junctions.append((fnum(r,'LOCATION.X'), fnum(r,'LOCATION.Y')))
        elif rec in ('25', '17'):
            labels.append((r.get('TEXT',''), fnum(r,'LOCATION.X'), fnum(r,'LOCATION.Y')))
        elif rec == '18':
            ports.append((r.get('NAME',''), fnum(r,'LOCATION.X'), fnum(r,'LOCATION.Y')))
    return comps, pins, wires, junctions, labels, ports

def build_nets(comps, pins, wires, junctions, labels, ports):
    uf = UF()
    segs = []
    for wi, vs in enumerate(wires):
        for si in range(len(vs)-1):
            (x1,y1),(x2,y2) = vs[si], vs[si+1]
            segs.append((x1,y1,x2,y2,wi,si))
            uf.union(('w',wi), ('w',wi))
        for (x,y) in vs:
            uf.union(('w',wi), ('v', key(x,y)))
    def attach_point(node, x, y):
        hit = False
        for (x1,y1,x2,y2,wi,si) in segs:
            if on_seg(x,y,x1,y1,x2,y2):
                uf.union(node, ('w',wi)); hit = True
        return hit
    for (x,y) in junctions:
        attach_point(('v', key(x,y)), x, y)
    dangling = []
    for pi,(ci,nm,des,x,y) in enumerate(pins):
        node = ('p', pi)
        uf.union(node, ('v', key(x,y)))
        if not attach_point(node, x, y):
            dangling.append(pi)
    for (t,x,y) in labels:
        attach_point(('lbl', (t,key(x,y))), x, y) or uf.union(('lbl',(t,key(x,y))), ('v',key(x,y)))
        if t: uf.union(('lbl',(t,key(x,y))), ('name', t))
    for (t,x,y) in ports:
        attach_point(('prt', (t,key(x,y))), x, y) or uf.union(('prt',(t,key(x,y))), ('v',key(x,y)))
        if t: uf.union(('prt',(t,key(x,y))), ('name', t))
    groups = defaultdict(lambda: {'pins': [], 'names': set(), 'portnames': set()})
    for pi,(ci,nm,des,x,y) in enumerate(pins):
        groups[uf.find(('p',pi))]['pins'].append((ci,des,nm))
    for (t,x,y) in labels:
        groups[uf.find(('lbl',(t,key(x,y))))]['names'].add(t)
    for (t,x,y) in ports:
        groups[uf.find(('prt',(t,key(x,y))))]['portnames'].add(t)
    return groups, dangling

# --------------------------------------------------------------- netlist side

def parse_netlist(path):
    """Protel 2.0: '[' part blocks (key/value on alternating lines), '(' net blocks."""
    lines = [l.rstrip() for l in open(path, encoding='utf-8', errors='replace')]
    parts, nets = {}, {}
    i, n = 0, len(lines)
    while i < n:
        s = lines[i].strip()
        if s == '[':
            body = []
            i += 1
            while i < n and lines[i].strip() != ']':
                body.append(lines[i].strip()); i += 1
            i += 1
            # positional header then free key/value pairs
            kv = {}
            for j in range(0, len(body) - 1, 2):
                k, v = body[j], body[j+1]
                if k and k not in kv: kv[k] = v
            des = kv.get('DESIGNATOR') or kv.get('Designator')
            if des: parts[des] = kv
        elif s == '(':
            i += 1
            name = lines[i].strip(); i += 1
            conns = []
            while i < n and lines[i].strip() != ')':
                tok = lines[i].split()
                if tok:
                    ref = tok[0]                       # e.g. U35-7 or U1-B16
                    d, _, pin = ref.rpartition('-')
                    etype = tok[-1] if len(tok) > 2 else ''
                    if d: conns.append((d, pin, etype))
                i += 1
            i += 1
            if name: nets.setdefault(name, []).extend(conns)
        else:
            i += 1
    return parts, nets

# ------------------------------------------------------------------- BOM side

def parse_bom(path):
    NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
    z = zipfile.ZipFile(path)
    shared = [''.join(t.text or '' for t in si.iter(NS+'t'))
              for si in ET.fromstring(z.read('xl/sharedStrings.xml'))]
    rows = []
    for row in ET.fromstring(z.read('xl/worksheets/sheet1.xml')).iter(NS+'row'):
        cells = {}
        for c in row.findall(NS+'c'):
            v = c.find(NS+'v')
            if v is None: continue
            col = ''.join(ch for ch in c.get('r') if ch.isalpha())
            cells[col] = shared[int(v.text)] if c.get('t') == 's' else v.text
        rows.append(cells)
    hdr = rows[0]
    col = {name: letter for letter, name in hdr.items()}
    out = {}
    for r in rows[1:]:
        des_field = r.get(col.get('Designator',''), '') or ''
        rec = {name: r.get(letter, '') for letter, name in hdr.items()}
        for d in [x.strip() for x in des_field.split(',') if x.strip()]:
            out[d] = rec
    return out

# -------------------------------------------------------------------- matching

def match_designators(sheets, nl_parts, nl_nets):
    """Map each schdoc symbol part -> netlist designator.

    Hard filter on LIBREFERENCE == PARTTYPE, then score by how many
    (pin, netname) facts the schdoc symbol shares with the netlist part.
    """
    nl_sig = defaultdict(set)     # netlist desig -> {(pin, net)}
    nl_pins = defaultdict(set)
    for net, conns in nl_nets.items():
        for d, pin, _ in conns:
            nl_sig[d].add((pin, net)); nl_pins[d].add(pin)
    by_type = defaultdict(list)
    for d, kv in nl_parts.items():
        by_type[(kv.get('PARTTYPE') or '').strip()].append(d)

    cands = []                    # (score, sheet, ci, netlist_desig)
    sch_sig = {}
    for sheet, (comps, groups) in sheets.items():
        for ci, c in enumerate(comps):
            sig = set()
            for g in groups.values():
                names = g['names'] or g['portnames']
                if not names: continue
                nm = sorted(names)[0]
                for (gci, des, _) in g['pins']:
                    if gci == ci: sig.add((des, nm))
            sch_sig[(sheet, ci)] = sig
            pool = by_type.get(c['lib'].strip()) or []
            if not pool:                      # libref did not match a PARTTYPE
                pool = list(nl_parts)
            for d in pool:
                score = len(sig & nl_sig[d])
                pin_overlap = len({p for p, _ in sig} & nl_pins[d])
                exact = 1 if c['lib'].strip() == (nl_parts[d].get('PARTTYPE') or '').strip() else 0
                cands.append((score, pin_overlap, exact, sheet, ci, d))

    cands.sort(key=lambda t: (-t[0], -t[1], -t[2], t[3], t[4], t[5]))
    assign, used_pins = {}, defaultdict(set)
    for score, pov, exact, sheet, ci, d in cands:
        if (sheet, ci) in assign: continue
        if not exact: continue
        mypins = {p for p, _ in sch_sig[(sheet, ci)]}
        if mypins and used_pins[d] & mypins:
            continue                          # another symbol part already owns these pins
        if score == 0 and pov == 0 and mypins:
            continue                          # no evidence at all
        assign[(sheet, ci)] = (d, score, pov)
        used_pins[d] |= mypins
    # single-candidate fallback: unique libref instance
    for sheet, (comps, groups) in sheets.items():
        for ci, c in enumerate(comps):
            if (sheet, ci) in assign: continue
            pool = by_type.get(c['lib'].strip()) or []
            free = [d for d in pool if not used_pins[d]]
            if len(pool) == 1:
                assign[(sheet, ci)] = (pool[0], 0, 0)
            elif len(free) == 1:
                assign[(sheet, ci)] = (free[0], 0, 0)
                used_pins[free[0]] |= {p for p, _ in sch_sig[(sheet, ci)]}
    return assign

# ------------------------------------------------------------------------ main

def main():
    if not os.path.exists(NETLIST):
        sys.exit(f"missing {NETLIST}: the Protel netlist is the identity source")
    nl_parts, nl_nets = parse_netlist(NETLIST)
    bom_files = sorted(glob.glob(BOM_GLOB))
    bom = parse_bom(bom_files[0]) if bom_files else {}

    sheets = {}
    for f in sorted(glob.glob(SCHDOC_GLOB)):
        sheet = os.path.basename(f)[:-7]
        comps, pins, wires, junctions, labels, ports = parse_sheet(f)
        groups, dangling = build_nets(comps, pins, wires, junctions, labels, ports)
        sheets[sheet] = (comps, groups)
        print(f"{sheet:12s} symbols={len(comps):3d} pins={len(pins):4d} dangling={len(dangling):3d}",
              file=sys.stderr)

    assign = match_designators(sheets, nl_parts, nl_nets)

    # netlist desig -> sheets it appears on
    home = defaultdict(set)
    mapping = []
    for (sheet, ci), (d, score, pov) in sorted(assign.items()):
        comps, _ = sheets[sheet]
        home[d].add(sheet)
        mapping.append((d, sheet, comps[ci]['designator'] or '?', comps[ci]['lib'], score))

    # ---- odin.parts.ir
    with open('odin.parts.ir', 'w') as fh:
        fh.write("# part <desig> type=<parttype> fp=<footprint> value=<v> lcsc=<sup> "
                 "class=<jlcpcb> pins=<n> sheets=<s,..>\n")
        for d in sorted(nl_parts, key=lambda s: (s.rstrip('0123456789'),
                                                 int(''.join(c for c in s if c.isdigit()) or 0))):
            kv = nl_parts[d]
            b = bom.get(d, {})
            npin = len({p for net in nl_nets.values() for dd, p, _ in net if dd == d})
            fh.write(f"part {d} type={kv.get('PARTTYPE','')} fp={kv.get('FOOTPRINT','')} "
                     f"value={kv.get('Value','') or b.get('Comment','')} "
                     f"lcsc={kv.get('Supplier Part','') or b.get('Supplier Part','')} "
                     f"class={(kv.get('JLCPCB Part Class','') or b.get('JLCPCB Part Class','')).replace(' ','_')} "
                     f"pins={npin} sheets={','.join(sorted(home.get(d,['?'])))}\n")

    # ---- odin.nets.ir  (global; the netlist is already sheet-stitched)
    with open('odin.nets.ir', 'w') as fh:
        fh.write("# net <name>: <desig.pin> ...   [sheets: ...]\n")
        for name in sorted(nl_nets):
            conns = sorted(set((d, p) for d, p, _ in nl_nets[name]))
            sh = sorted({s for d, _ in conns for s in home.get(d, [])})
            fh.write(f"net {name}: " + ' '.join(f"{d}.{p}" for d, p in conns)
                     + (f"   [sheets: {','.join(sh)}]" if sh else "") + "\n")

    # ---- odin.desigmap
    with open('odin.desigmap', 'w') as fh:
        fh.write("# map <netlist_desig> <- <sheet>/<schdoc_desig> lib=<libref> confidence=<shared (pin,net) facts>\n")
        for d, sheet, sd, lib, score in sorted(mapping):
            fh.write(f"map {d} <- {sheet}/{sd} lib={lib} confidence={score}\n")
        unmapped = [(s, c['designator'], c['lib'])
                    for s, (comps, _) in sheets.items()
                    for ci, c in enumerate(comps) if (s, ci) not in assign]
        for s, sd, lib in sorted(set(unmapped)):
            fh.write(f"# UNMAPPED schdoc symbol {s}/{sd} lib={lib}\n")

    # ---- odin.bomdiff
    nl_set, bom_set = set(nl_parts), set(bom)
    with open('odin.bomdiff', 'w') as fh:
        fh.write("# designators in the netlist but not the BOM\n")
        for d in sorted(nl_set - bom_set): fh.write(f"netlist-only {d} type={nl_parts[d].get('PARTTYPE','')}\n")
        fh.write("# designators in the BOM but not the netlist\n")
        for d in sorted(bom_set - nl_set): fh.write(f"bom-only {d} mfr={bom[d].get('Manufacturer Part','')}\n")
        fh.write("# placed parts with no LCSC supplier part\n")
        for d in sorted(nl_set & bom_set):
            if not (bom[d].get('Supplier Part') or '').strip(): fh.write(f"no-lcsc {d}\n")

    # ---- odin.srcdiff : do the schdocs and the netlist describe the same board?
    sch_types = defaultdict(int)
    for sheet, (comps, _) in sheets.items():
        for c in comps: sch_types[c['lib'].strip()] += 1
    nl_types = defaultdict(int)
    for d, kv in nl_parts.items(): nl_types[(kv.get('PARTTYPE') or '').strip()] += 1
    with open('odin.srcdiff', 'w') as fh:
        fh.write("# part types in the schdoc export but not the netlist (schdoc symbol count)\n")
        for t in sorted(set(sch_types) - set(nl_types)):
            fh.write(f"schdoc-only {t} symbols={sch_types[t]}\n")
        fh.write("# part types in the netlist but not the schdoc export (netlist instance count)\n")
        for t in sorted(set(nl_types) - set(sch_types)):
            fh.write(f"netlist-only {t} instances={nl_types[t]}\n")
        fh.write("# part types in both\n")
        for t in sorted(set(nl_types) & set(sch_types)):
            fh.write(f"both {t} schdoc_symbols={sch_types[t]} netlist_instances={nl_types[t]}\n")

    mapped_syms = len(assign)
    total_syms = sum(len(c) for c, _ in sheets.values())
    print(f"\nnetlist parts={len(nl_parts)} nets={len(nl_nets)}  "
          f"schdoc symbols mapped={mapped_syms}/{total_syms}  "
          f"netlist-only={len(nl_set-bom_set)} bom-only={len(bom_set-nl_set)}", file=sys.stderr)
    shared_types = len(set(nl_types) & set(sch_types))
    print(f"part types: schdoc={len(sch_types)} netlist={len(nl_types)} shared={shared_types}",
          file=sys.stderr)

main()
