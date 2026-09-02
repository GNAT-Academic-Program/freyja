#!/usr/bin/env python3
"""Derive a canonical IR from Altium ASCII .schdoc exports (EasyEDA Pro origin).
Connectivity rules:
  - wire-wire: shared vertex, or junction on segment
  - pin/netlabel/port/powerport: point lies on a wire segment (inclusive)
Pins: electrical point = LOCATION + PINLENGTH along orientation (PINCONGLOMERATE & 3).
"""
import sys, glob, math
from collections import defaultdict

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
    comps = []          # index-aligned with OWNERINDEX ordering of RECORD=1
    pins = []           # (comp_idx, name, desig, ex, ey)
    wires = []          # list of vertex lists
    junctions = []      # (x,y)
    labels = []         # (text, x, y)   RECORD=25 netlabel, 17 powerport
    ports = []          # (name, x, y)
    idx = -1
    order = []          # record stream to map OWNERINDEX: Altium OWNERINDEX counts all primitives; simpler: track component sequence and attach pins by OWNERINDEX
    allrecs = list(records(path))
    # OWNERINDEX refers to index in the flat record list (1-based, excluding header/sheet? ) -> empirical: RECORD=1 positions
    comp_by_recidx = {}
    for i, r in enumerate(allrecs):
        rec = r.get('RECORD')
        if rec == '1':
            comps.append({'lib': r.get('LIBREFERENCE',''), 'designator': None, 'value': None,
                          'footprint': None, 'recidx': i})
            comp_by_recidx[i] = len(comps)-1
    # attach child records: OWNERINDEX is index into records-after-header (1-based)
    def owner_comp(r):
        oi = r.get('OWNERINDEX')
        if oi is None: return None
        oi = int(oi)  # 1-based index into allrecs[0:] where allrecs[0] is RECORD=31? header line excluded
        # empirical mapping: allrecs[oi] should be the owning RECORD=1 (offset by leading header rec)
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
        elif rec == '25':
            labels.append((r.get('TEXT',''), fnum(r,'LOCATION.X'), fnum(r,'LOCATION.Y')))
        elif rec == '17':
            labels.append((r.get('TEXT',''), fnum(r,'LOCATION.X'), fnum(r,'LOCATION.Y')))
        elif rec == '18':
            ports.append((r.get('NAME',''), fnum(r,'LOCATION.X'), fnum(r,'LOCATION.Y')))
    return comps, pins, wires, junctions, labels, ports

def build_nets(comps, pins, wires, junctions, labels, ports):
    uf = UF()
    segs = []  # (x1,y1,x2,y2, wire_id, seg_id)
    for wi, vs in enumerate(wires):
        for si in range(len(vs)-1):
            (x1,y1),(x2,y2) = vs[si], vs[si+1]
            segs.append((x1,y1,x2,y2,wi,si))
            uf.union(('w',wi), ('w',wi))  # ensure node
        for (x,y) in vs:
            uf.union(('w',wi), ('v', key(x,y)))
    # junctions merge wires crossing at that point
    def attach_point(node, x, y):
        hit = False
        for (x1,y1,x2,y2,wi,si) in segs:
            if on_seg(x,y,x1,y1,x2,y2):
                uf.union(node, ('w',wi)); hit = True
        return hit
    for (x,y) in junctions:
        attach_point(('v', key(x,y)), x, y)
    dangling_pins, pin_net_nodes = [], []
    for pi,(ci,nm,des,x,y) in enumerate(pins):
        node = ('p', pi)
        uf.union(node, ('v', key(x,y)))   # pin-to-pin direct touch
        if not attach_point(node, x, y):
            # not on any wire; may still touch another pin at same point (handled by vertex union)
            dangling_pins.append(pi)
    for (t,x,y) in labels:
        attach_point(('lbl', (t,key(x,y))), x, y) or uf.union(('lbl',(t,key(x,y))), ('v',key(x,y)))
        if t: uf.union(('lbl',(t,key(x,y))), ('name', t))
    for (t,x,y) in ports:
        attach_point(('prt', (t,key(x,y))), x, y) or uf.union(('prt',(t,key(x,y))), ('v',key(x,y)))
        if t: uf.union(('prt',(t,key(x,y))), ('name', t))
    # collect
    groups = defaultdict(lambda: {'pins': [], 'names': set(), 'portnames': set()})
    for pi,(ci,nm,des,x,y) in enumerate(pins):
        g = groups[uf.find(('p',pi))]
        g['pins'].append((ci,des,nm))
    for (t,x,y) in labels:
        groups[uf.find(('lbl',(t,key(x,y))))]['names'].add(t)
    for (t,x,y) in ports:
        groups[uf.find(('prt',(t,key(x,y))))]['portnames'].add(t)
    return groups, dangling_pins

def main():
    out_parts, out_nets = [], []
    anon = 0
    for f in sorted(glob.glob('*.schdoc')):
        sheet = f[:-7]
        comps, pins, wires, junctions, labels, ports = parse_sheet(f)
        groups, dangling = build_nets(comps, pins, wires, junctions, labels, ports)
        for c in comps:
            out_parts.append((c['designator'] or f'?{sheet}', c['value'] or '', c['lib'], sheet))
        stats_conn = 0
        for g in groups.values():
            if not g['pins'] and not g['names']: continue
            name = sorted(g['names'])[0] if g['names'] else (sorted(g['portnames'])[0] if g['portnames'] else None)
            if name is None:
                anon += 1; name = f'N${anon:04d}'
            members = sorted(f"{comps[ci]['designator'] or '?'}.{des}" for ci,des,nm in g['pins'])
            if members:
                out_nets.append((sheet, name, ' '.join(members), sorted(g['portnames'])))
                stats_conn += len(members)
        print(f"{sheet:12s} comps={len(comps):3d} pins={len(pins):4d} pin-endpoints-on-nets={stats_conn:4d} dangling={len(dangling):3d}", file=sys.stderr)
    with open('odin.parts.ir','w') as fh:
        fh.write("# part <designator> value=<v> lib=<libref> sheet=<s>\n")
        for d,v,l,s in sorted(out_parts):
            fh.write(f"part {d} value={v} lib={l} sheet={s}\n")
    with open('odin.nets.ir','w') as fh:
        fh.write("# net <sheet>/<name>: <refdes.pin> ...   [ports: ...]\n")
        for s,n,m,p in sorted(out_nets):
            fh.write(f"net {s}/{n}: {m}" + (f"   [ports: {','.join(p)}]" if p else "") + "\n")

main()
