#!/usr/bin/env python3
"""Connectivity islands: which parts want to sit close together.

Reads tools/design.py (the netlist source of truth) and clusters parts
bound by short local nets. The output is a hand-placement worklist: keep
each island tight, then drop the island as a whole near the hubs it
hangs off. No KiCad required; plain python3.

    python3 tools/islands.py               # console list
    python3 tools/islands.py --md          # markdown to stdout
    python3 tools/islands.py --netclasses  # write one colored net class per
                                           # island into kicad/odin.kicad_pro
                                           # (ISLxx_*), so the ratsnest is the
                                           # island map and the Nets panel
                                           # filters one island at a time

--netclasses merges: existing classes (Default, MGT_100R...) and their
patterns are kept untouched; nets already matched by a non-ISL pattern
(the MGT pairs) are left out of island classes so impedance rules stay
authoritative. Previous ISL* classes are replaced. Island classes copy
Default's electrical parameters at the lowest priority: they carry color
and grouping, never rules.

Rules:
  - GND, power rails, and any net with more than LOCAL_MAX pins bind
    nothing (they go everywhere; proximity along them is meaningless).
  - Hub parts (more than HUB_PINS pins: FPGA, controller, slot sockets,
    SFP connectors...) join no island. Each island instead reports which
    hubs its nets reach and on how many nets, which tells you where on
    the board the island belongs.
  - Parts left with no local net at all (rail-only: bulk and decoupling
    caps) are summarised per group, not clustered: they follow their
    load, the decap rule already handles the FPGA 100nF.
"""
import colorsys, fnmatch, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from design import build

PRO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'kicad', 'odin.kicad_pro')


def class_name(i, bygrp):
    g = max(bygrp, key=lambda k: len(bygrp[k]))          # dominant group
    slug = re.sub(r'[^A-Za-z0-9]+', '_', g).strip('_').upper()[:18]
    return f'ISL{i:02d}_{slug}'


def write_netclasses(rows, parts, local):
    pro = json.load(open(PRO))
    ns = pro.setdefault('net_settings', {})
    classes = [c for c in ns.get('classes', [])
               if not c['name'].startswith('ISL')]
    default = next(c for c in classes if c['name'] == 'Default')
    keep_patterns = [p for p in ns.get('netclass_patterns') or []
                     if not p['netclass'].startswith('ISL')]
    foreign = [p['pattern'] for p in keep_patterns]
    assigned, patterns = set(), list(keep_patterns)
    for i, (members, att) in enumerate(rows, 1):
        bygrp = {}
        for r in members:
            bygrp.setdefault(parts[r]['group'], []).append(r)
        name = class_name(i, bygrp)
        h = (i * 0.61803398875) % 1.0                    # golden-angle hues
        r_, g_, b_ = (int(v * 255) for v in colorsys.hsv_to_rgb(h, 0.85, 0.95))
        c = dict(default)
        c.update(name=name, priority=10000 + i,
                 pcb_color=f'rgba({r_}, {g_}, {b_}, 0.800)',
                 schematic_color=f'rgba({r_}, {g_}, {b_}, 0.800)')
        classes.append(c)
        nets = sorted(n for n, refs in local.items()
                      if any(r in members for r in refs))
        for n in nets:
            if n in assigned or any(fnmatch.fnmatch(n, f) for f in foreign):
                continue                                 # MGT rules keep it
            assigned.add(n)
            patterns.append({'netclass': name, 'pattern': n})
    ns['classes'] = classes
    ns['netclass_patterns'] = patterns
    json.dump(pro, open(PRO, 'w'), indent=2, sort_keys=True)
    print(f'{PRO}: {len(rows)} ISL classes, {len(assigned)} nets assigned, '
          f'{len(keep_patterns)} foreign patterns kept')

LOCAL_MAX = 8      # a net wider than this binds nothing
HUB_PINS  = 24     # a part wider than this is a hub, not an island member


def is_rail(net):
    return (net == 'GND' or net.startswith('+') or 'VCC' in net
            or net in ('VSYS', 'VBUS'))


def compute():
    """Return (rows, parts, local, hubs, loose): the islands, the part table,
    the binding local nets, the hub refs, and the rail-only parts per group.
    Pure data; used by main() below and by tools/place.py for staging."""
    d = build()
    parts = {p['ref']: p for p in d.parts if not p.get('dnp')}

    net_pins = {}
    for p in parts.values():
        for net in p['pins'].values():
            net_pins.setdefault(net, []).append(p['ref'])

    hubs = {r for r, p in parts.items() if len(p['pins']) > HUB_PINS}
    local = {n: refs for n, refs in net_pins.items()
             if not is_rail(n) and len(refs) <= LOCAL_MAX}

    # union-find over non-hub parts sharing a local net
    up = {r: r for r in parts if r not in hubs}
    def find(r):
        while up[r] != r:
            up[r] = up[up[r]]; r = up[r]
        return r
    for refs in local.values():
        members = [r for r in refs if r not in hubs]
        for a, b in zip(members, members[1:]):
            up[find(a)] = find(b)

    islands = {}
    for r in up:
        islands.setdefault(find(r), []).append(r)

    rows, loose = [], {}
    for root, members in islands.items():
        nets = {n for n, refs in local.items()
                if any(r in members for r in refs)}
        att = {}
        for n in nets:
            for r in net_pins[n]:
                if r in hubs:
                    att[r] = att.get(r, 0) + 1
        if not nets:                       # rail-only: bulk / decoupling
            for r in members:
                loose.setdefault(parts[r]['group'], []).append(r)
            continue
        rows.append((sorted(members, key=lambda r: (r[0] not in 'UQXY', r)),
                     att))
    rows.sort(key=lambda t: -len(t[0]))
    return rows, parts, local, hubs, loose


def main():
    rows, parts, local, hubs, loose = compute()

    if '--netclasses' in sys.argv:
        write_netclasses(rows, parts, local)
        return

    md = '--md' in sys.argv
    def label(r):
        v = parts[r]['value']
        return f'{r}({v})' if v and len(v) <= 12 else r

    if md:
        print('# Placement islands (generated by tools/islands.py)\n')
    for i, (members, att) in enumerate(rows, 1):
        near = ', '.join(f'{h} x{c}' for h, c in
                         sorted(att.items(), key=lambda t: -t[1])) or 'self-contained'
        bygrp = {}
        for r in members:
            bygrp.setdefault(parts[r]['group'], []).append(r)
        if md:
            print(f'## Island {i} ({len(members)} parts) near: {near}')
            for g in sorted(bygrp):
                print(f'- **{g}:** ' + ', '.join(label(r) for r in bygrp[g]))
            print()
        else:
            print(f'[{i:2d}] near: {near}')
            for g in sorted(bygrp):
                print(f'     {g}: ' + ', '.join(label(r) for r in bygrp[g]))
    if loose:
        print('\nrail-only parts (follow their load, no island):'
              if not md else '\n## Rail-only parts (follow their load)\n')
        for g in sorted(loose):
            line = f'  {g}: {", ".join(sorted(loose[g]))}'
            print(('- ' + line.strip()) if md else line)
    print(f'\n{len(rows)} islands, {len(hubs)} hubs '
          f'({", ".join(sorted(hubs))})' if not md else
          f'\n*{len(rows)} islands; hubs: {", ".join(sorted(hubs))}*')


if __name__ == '__main__':
    main()
