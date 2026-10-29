#!/usr/bin/env python3
"""Load every footprint and net from the schematic netlist into odin.kicad_pcb.

This is what 'Update PCB from Schematic' does in the GUI. Existing references
retain their authoritative position, rotation, side and locked state. Only new
references enter the coarse import band outside the board."""
import re, sys, os, json
import pcbnew

BOARD = 'kicad/odin.kicad_pcb'
NET   = 'kicad/odin.net'
LIBS  = ['/usr/share/kicad/footprints', os.path.abspath('kicad')]

def libdir(fp_id):
    lib, name = fp_id.split(':', 1)
    if lib == 'odin': return os.path.abspath('kicad/odin.pretty'), name
    if lib == 'EasyEDA': return os.path.abspath('easyeda/EasyEDA.pretty'), name
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
        # the component's own description comes before (libsource ...)
        desc = re.search(r'\(description "((?:[^"\\]|\\.)*)"\)', chunk.split('(libsource')[0])
        lcsc = re.search(r'\(field \(name "LCSC"\) "([^"]*)"\)', chunk)
        comps[ref] = dict(value=val.group(1) if val else '',
                          role=desc.group(1).replace('\\"', '"') if desc else '',
                          lcsc=lcsc.group(1) if lcsc else '',
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
    old_fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    old = {ref: dict(pos=(fp.GetPosition().x, fp.GetPosition().y),
                     rot=fp.GetOrientationDegrees(), back=fp.IsFlipped(),
                     locked=fp.IsLocked()) for ref, fp in old_fps.items()}

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
    changed = []
    load_errors = []
    # Start the band below everything already on the board, staged parts from
    # earlier imports included, so a new part is never stacked on an old one.
    y = 145.0
    if old_fps:
        y = max(y, 6.0 + max(pcbnew.ToMM(fp.GetBoundingBox().GetBottom())
                             for fp in old_fps.values()))
    for s in order:
        x, rowh = 30.0, 0.0
        for ref in sorted(bands[s]):
            c = comps[ref]
            if ref.startswith('#'): continue  # schematic-only power symbols
            if not c['fp'] or ':' not in c['fp']:
                miss += 1
                load_errors.append(f'{ref}: missing footprint assignment')
                continue
            nm = c['fp'].split(':', 1)[1]
            prior = old_fps.get(ref)
            replace = (prior is None or str(prior.GetFPID().GetLibItemName()) != nm
                       or str(prior.GetFPID().GetLibNickname()) != c['fp'].split(':', 1)[0])
            if replace and prior is not None: changed.append(ref)
            if replace:
                try:
                    d, nm = libdir(c['fp'])
                    fp = pcbnew.FootprintLoad(d, nm)
                except Exception as exc:
                    if len(load_errors) < 8:
                        load_errors.append(f'{ref} {c["fp"]}: {exc}')
                    fp = None
            else:
                fp = prior
            if fp is None: miss += 1; continue
            if replace:
                lib_nick = c['fp'].split(':', 1)[0]
                lib_id = pcbnew.LIB_ID(lib_nick, nm)
                fp.SetFPID(lib_id)
            fp.SetReference(ref); fp.SetValue(c['value'])
            # What the part is for (tools/roles.py), in KiCad's standard
            # Description field (Footprint Properties dialog), never printed.
            fp.GetFieldByName('Description').SetText(c.get('role', ''))
            # The same text as the library description, which is what KiCad
            # shows in the bottom message bar on a single click and as
            # "Library Description" in the Properties panel.
            fp.SetLibDescription(c.get('role', ''))
            # The order number travels with the schematic symbol; the copy an
            # imported footprint carries is only refreshed here, so a part
            # swap that keeps its package cannot leave the old number behind.
            if c.get('lcsc'):
                fld = fp.GetFieldByName('LCSC Part')
                if fld is None:
                    fld = fp.AddField(pcbnew.PCB_FIELD(fp, -1, 'LCSC Part'))
                    fld.SetVisible(False)
                fld.SetText(c['lcsc'])
            fp.SetDNP(bool(c.get('dnp')))
            if replace:
                # A package change swaps the footprint object; the island
                # group it was reviewed in must follow it, or the part falls
                # out of its island and the next islands.py run relays it.
                grp = prior.GetParentGroup() if prior is not None else None
                if prior is not None:
                    if grp is not None: grp.RemoveItem(prior)
                    board.Remove(prior)
                board.Add(fp)       # Flip() requires a board-owned footprint
                if grp is not None: grp.AddItem(fp)
            bb = fp.GetBoundingBox()
            w = max(pcbnew.ToMM(bb.GetWidth()), 2.0) + 3.0
            h = max(pcbnew.ToMM(bb.GetHeight()), 2.0) + 3.0
            if ref in old:
                state = old[ref]
                fp.SetPosition(pcbnew.VECTOR2I(*state['pos']))
                if fp.IsFlipped() != state['back']:
                    fp.Flip(fp.GetPosition(), False)
                fp.SetOrientationDegrees(state['rot'])
                fp.SetLocked(state['locked'])
            else:
                if x + w > 330.0: x, y, rowh = 30.0, y + rowh + 2.0, 0.0
                fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x + w/2), pcbnew.FromMM(y + h/2)))
            for pad in fp.Pads():
                pad.SetNetCode(0)
                nn = pin2net.get((ref, pad.GetNumber()))
                if nn: pad.SetNet(netmap[nn])
            if ref not in old:
                x += w; rowh = max(rowh, h)
            placed += 1
        y += rowh + 6.0
    for ref, fp in old_fps.items():
        if ref not in comps:
            board.Remove(fp)
    if miss:
        raise SystemExit('PCB NOT SAVED: missing footprints: ' + '\n'.join(load_errors))
    current = {fp.GetReference(): fp for fp in board.GetFootprints()}
    moved = []
    for ref in old.keys() & current.keys():
        fp, state = current[ref], old[ref]
        if ((fp.GetPosition().x, fp.GetPosition().y) != state['pos'] or
                fp.GetOrientationDegrees() != state['rot'] or
                fp.IsFlipped() != state['back']):
            moved.append(ref)
    if moved:
        raise SystemExit('PCB NOT SAVED: common references moved: ' + ', '.join(sorted(moved)))
    pcbnew.SaveBoard(BOARD, board)
    changes = dict(added=sorted(current.keys() - old.keys()),
                   removed=sorted(old.keys() - current.keys()),
                   changed_in_place=sorted(changed), moved=moved)
    with open('/tmp/odin-sync-changes.json', 'w') as report:
        json.dump(changes, report, indent=2)
    print(json.dumps(changes, indent=2))
    print(f"placed {placed} footprints, {len(netmap)} nets"
          + (f", {miss} FAILED TO LOAD" if miss else ", none missing"))
    for err in load_errors:
        print('  load error:', err)

    # References are manufacturing information; functional labels are the
    # human interface. Keep this true after every netlist reload.
    # Reloading hundreds of library footprints exposes a KiCad 9 SWIG lifetime
    # bug if a second board is opened in this process. Use a clean interpreter.
    import subprocess
    subprocess.run([sys.executable, os.path.join('tools', 'update_silkscreen.py')],
                   check=True)

if __name__ == '__main__':
    main()
