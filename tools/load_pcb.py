#!/usr/bin/env python3
"""Load every footprint and net from the schematic netlist into odin.kicad_pcb.

This is what 'Update PCB from Schematic' does in the GUI; doing it here means
the committed board is a real board, not an empty outline. Placement is a
coarse grid grouped by sheet -- a starting point for human placement, not a
layout."""
import re, sys, os
import pcbnew

BOARD = 'kicad/odin.kicad_pcb'
NET   = 'kicad/odin.net'
LIBS  = ['/usr/share/kicad/footprints', os.path.abspath('kicad')]

def libdir(fp_id):
    lib, name = fp_id.split(':', 1)
    if lib == 'odin': return os.path.abspath('kicad/odin.pretty'), name
    for base in LIBS:
        p = os.path.join(base, lib + '.pretty')
        if os.path.isdir(p): return p, name
    raise FileNotFoundError(fp_id)

def parse():
    t = open(NET).read()
    comps = {}
    # split on component boundaries rather than regex the whole section: the
    # last entry's terminator differs and a lookahead silently drops it
    sec = t[t.index('(components'):t.index('(libparts') if '(libparts' in t else len(t)]
    for chunk in sec.split('(comp (ref "')[1:]:
        ref = chunk[:chunk.index('"')]
        val = re.search(r'\(value "([^"]*)"\)', chunk)
        fp  = re.search(r'\(footprint "([^"]*)"\)', chunk)
        sh  = re.search(r'\(sheetpath \(names "([^"]*)"', chunk)
        comps[ref] = dict(value=val.group(1) if val else '',
                          fp=fp.group(1) if fp else '',
                          sheet=sh.group(1) if sh else '/',
                          dnp='(property (name "dnp")' in chunk)
    nets = {}
    for m in re.finditer(r'\(net \(code "\d+"\) \(name "([^"]+)"\)(.*?)(?=\n    \(net \(code|\Z)',
                         t, re.S):
        nets[m.group(1)] = re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', m.group(2))
    return comps, nets

def main():
    comps, nets = parse()
    board = pcbnew.LoadBoard(BOARD)
    for fp in list(board.GetFootprints()): board.Remove(fp)

    netmap = {}
    for name in nets:
        n = board.FindNet(name)
        if n is None:
            n = pcbnew.NETINFO_ITEM(board, name); board.Add(n)
        netmap[name] = n
    pin2net = {}
    for name, nodes in nets.items():
        for ref, pin in nodes: pin2net[(ref, pin)] = name

    # coarse placement: a band per sheet, outside the board outline so the
    # human can drag groups in rather than untangle a pile in the middle
    order, bands = [], {}
    for ref, c in comps.items():
        s = c['sheet']
        if s not in bands: bands[s] = []; order.append(s)
        bands[s].append(ref)

    placed = miss = 0
    y = 145.0
    for s in order:
        x, rowh = 30.0, 0.0
        for ref in sorted(bands[s]):
            c = comps[ref]
            if not c['fp'] or ':' not in c['fp']: miss += 1; continue
            try:
                d, nm = libdir(c['fp'])
                fp = pcbnew.FootprintLoad(d, nm)
            except Exception:
                fp = None
            if fp is None: miss += 1; continue
            lib_nick = c['fp'].split(':', 1)[0]
            fp.SetFPID(pcbnew.LIB_ID(lib_nick, nm))
            fp.SetReference(ref); fp.SetValue(c['value'])
            if c.get('dnp'): fp.SetDNP(True)
            bb = fp.GetBoundingBox()
            w = max(pcbnew.ToMM(bb.GetWidth()), 2.0) + 3.0
            h = max(pcbnew.ToMM(bb.GetHeight()), 2.0) + 3.0
            if x + w > 330.0: x, y, rowh = 30.0, y + rowh + 2.0, 0.0
            fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x + w/2), pcbnew.FromMM(y + h/2)))
            for pad in fp.Pads():
                nn = pin2net.get((ref, pad.GetNumber()))
                if nn: pad.SetNet(netmap[nn])
            board.Add(fp)
            x += w; rowh = max(rowh, h); placed += 1
        y += rowh + 6.0
    pcbnew.SaveBoard(BOARD, board)
    print(f"placed {placed} footprints, {len(netmap)} nets"
          + (f", {miss} FAILED TO LOAD" if miss else ", none missing"))

main()
