#!/usr/bin/env python3
"""Power rails stay on the power layer.

Fails when a power net has a copper run on a signal layer (F.Cu, B.Cu and the
inner signal layers) longer than LIMIT_MM. A run is the copper between two vias
or pads of the net: track segments of one net on one layer joined end to end,
ending wherever a segment end sits on a via or a pad of that net (or is left
open). Where a run branches, its length is the longest way through it. Chains of
short pin-to-via stubs that only meet at pads or vias are therefore separate
runs; a rail drawn as a trace is one long run.

A filled zone island of a power net on a signal layer counts whole, with the
longer side of its bounding box: a pour is rail copper wherever its vias are.

Ground is not a rail here and is not checked. The power layer (In3) and the
ground planes are not signal layers.

Exceptions are listed by name only, net and layer, in ALLOWED.

Usage: tools/check_power_layers.py [board]     exit 1 on any failure
"""
import collections, re, sys
import pcbnew

LIMIT_MM = 10.0
ALLOWED = {
    ('AUX_RAIL', 'B.Cu'): 'AUX trunk in its reserved lane beside the east 1.8 V strip',
    ('+1V0', 'In2_signal'): 'core regulator sense line from ball V10 (no load current)',
}
POWER_CLASSES = {'PWR_3A', 'AUX_5A', 'EXT_2A'}
POWER_NAME = re.compile(r'^(\+.*|VBUS|VSYS|VIN_EXT|AUX_RAIL|PHY_1V0|VCCIO_\d(_EXT)?|SLOT_[A-Z]_(5V|3V3|AUX|PIN_VOLTAGE))$')


def is_power(net):
    name = net.GetNetname()
    if not name or name == 'GND':
        return False
    return bool(POWER_NAME.match(name)) or bool(POWER_CLASSES & set(net.GetNetClassName().split(',')))


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else 'kicad/odin.kicad_pcb'
    b = pcbnew.LoadBoard(path)
    signal = [l for l in b.GetEnabledLayers().CuStack()
              if not re.search(r'GND|power', b.GetLayerName(l), re.I)]
    power = {n.GetNetname() for n in b.GetNetInfo().NetsByNetcode().values() if is_power(n)}

    chains = []                                   # (net, layer name, length, widths, where, what)
    vias = collections.defaultdict(list)
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() in power:
            vias[t.GetNetname()].append((t.GetPosition(), t.GetWidth(pcbnew.F_Cu) // 2))
    pads = collections.defaultdict(list)
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() in power:
                pads[p.GetNetname()].append(p)
    for layer in signal:
        lname = b.GetLayerName(layer)
        tracks = collections.defaultdict(list)
        for t in b.GetTracks():
            if t.Type() != pcbnew.PCB_VIA_T and t.GetLayer() == layer and t.GetNetname() in power:
                tracks[t.GetNetname()].append(t)
        for net, ts in sorted(tracks.items()):
            # graph: nodes are segment end points, edges are segments
            edges = collections.defaultdict(list)          # node -> [(other node, length mm, segment index)]
            for i, t in enumerate(ts):
                a, c = (t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)
                edges[a].append((c, t.GetLength() / 1e6, i)); edges[c].append((a, t.GetLength() / 1e6, i))

            def terminal(n):
                pt = pcbnew.VECTOR2I(n[0], n[1])
                if any((pt.x - v.x) ** 2 + (pt.y - v.y) ** 2 <= r * r for v, r in vias[net]):
                    return True
                return any(p.IsOnLayer(layer) and p.HitTest(pt) for p in pads[net])
            term = {n: terminal(n) for n in edges}
            seen = set()
            for i0, t0 in enumerate(ts):
                if i0 in seen:
                    continue
                # one run: the segments reachable from this one without passing through a via or pad
                run, nodes, todo = set(), set(), [i0]
                while todo:
                    i = todo.pop()
                    if i in run:
                        continue
                    run.add(i); t = ts[i]
                    for n in ((t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)):
                        nodes.add(n)
                        if not term[n]:
                            todo += [j for _, _, j in edges[n] if j not in run]
                seen |= run
                best = (0.0, None, None)                   # longest way through the run
                for src in nodes:
                    dist = {src: 0.0}; todo = [src]
                    while todo:
                        n = todo.pop()
                        if n != src and term[n]:
                            continue
                        for m, l, j in edges[n]:
                            if j in run and dist[n] + l < dist.get(m, 1e18):
                                dist[m] = dist[n] + l; todo.append(m)
                    far = max(dist, key=dist.get)
                    if dist[far] > best[0]:
                        best = (dist[far], src, far)
                widths = sorted({ts[i].GetWidth() / 1e6 for i in run})
                where = '(%.1f, %.1f) to (%.1f, %.1f)' % (best[1][0] / 1e6, best[1][1] / 1e6, best[2][0] / 1e6, best[2][1] / 1e6)
                chains.append((net, lname, best[0], widths, where, f'run of {len(run)} segment' + ('s' if len(run) > 1 else '')))
        for z in b.Zones():
            if z.GetIsRuleArea() or z.GetNetname() not in power or not z.GetLayerSet().Contains(layer):
                continue
            fill = z.GetFilledPolysList(layer)
            for i in range(fill.OutlineCount()):
                bb = fill.Outline(i).BBox()
                chains.append((z.GetNetname(), lname, max(bb.GetWidth(), bb.GetHeight()) / 1e6,
                               [round(min(bb.GetWidth(), bb.GetHeight()) / 1e6, 1)],
                               'x %.1f-%.1f y %.1f-%.1f' % (bb.GetX() / 1e6, bb.GetRight() / 1e6, bb.GetY() / 1e6, bb.GetBottom() / 1e6),
                               f"zone '{z.GetZoneName() or 'unnamed zone'}'"))

    long_ = sorted((c for c in chains if c[2] > LIMIT_MM), key=lambda c: -c[2])
    fails = [c for c in long_ if (c[0], c[1]) not in ALLOWED]
    for c in long_:
        tag = 'allowed' if (c[0], c[1]) in ALLOWED else 'FAIL   '
        why = f"  [{ALLOWED[(c[0], c[1])]}]" if tag == 'allowed' else ''
        print(f"{tag} {c[0]:10s} {c[1]:11s} {c[2]:6.1f} mm  width {'/'.join(f'{w:g}' for w in c[3])} mm  {c[4]}  {c[5]}{why}")
    print(f'power on signal layers: {len(fails)} runs over {LIMIT_MM:g} mm'
          f' ({len(long_) - len(fails)} allowed by name), {len(power)} power nets, layers '
          + ' '.join(b.GetLayerName(l) for l in signal))
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
