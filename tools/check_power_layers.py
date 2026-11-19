#!/usr/bin/env python3
"""Power rails stay on the power layer.

Fails when a power net has copper on a signal layer (F.Cu, B.Cu and the inner
signal layers) longer than LIMIT_MM, counted per connected chain: track segments
of one net on one layer that share an end point, plus every filled zone island of
that net on that layer and the tracks that end inside it. A zone island counts
with the longer side of its bounding box. Short pin-to-via stubs and short plane
bridges stay under the limit; a rail routed as a trace or poured as a strip does
not.

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

    chains = []                                   # (net, layer name, length, widths, box, what)
    for layer in signal:
        lname = b.GetLayerName(layer)
        tracks = collections.defaultdict(list)
        for t in b.GetTracks():
            if t.Type() != pcbnew.PCB_VIA_T and t.GetLayer() == layer and t.GetNetname() in power:
                tracks[t.GetNetname()].append(t)
        islands = collections.defaultdict(list)   # net -> [(zone name, island poly)]
        for z in b.Zones():
            if z.GetIsRuleArea() or z.GetNetname() not in power or not z.GetLayerSet().Contains(layer):
                continue
            fill = z.GetFilledPolysList(layer)
            for i in range(fill.OutlineCount()):
                s = pcbnew.SHAPE_POLY_SET(); s.AddOutline(fill.Outline(i))
                islands[z.GetNetname()].append((z.GetZoneName() or 'unnamed zone', s))
        for net in sorted(set(tracks) | set(islands)):
            ts, isl = tracks[net], islands[net]
            par = list(range(len(ts) + len(isl)))

            def find(i):
                while par[i] != i:
                    par[i] = par[par[i]]; i = par[i]
                return i
            ends = collections.defaultdict(list)
            for i, t in enumerate(ts):
                for e in (t.GetStart(), t.GetEnd()):
                    ends[(e.x, e.y)].append(i)
                    for j, (_, s) in enumerate(isl):
                        if s.Contains(e):
                            par[find(i)] = find(len(ts) + j)
            for v in ends.values():
                for j in v[1:]:
                    par[find(j)] = find(v[0])
            groups = collections.defaultdict(list)
            for i in range(len(par)):
                groups[find(i)].append(i)
            for members in groups.values():
                length = 0.0; widths = set(); what = []; xs = []; ys = []
                for i in members:
                    if i < len(ts):
                        t = ts[i]; length += t.GetLength() / 1e6; widths.add(t.GetWidth() / 1e6)
                        xs += [t.GetStart().x / 1e6, t.GetEnd().x / 1e6]; ys += [t.GetStart().y / 1e6, t.GetEnd().y / 1e6]
                    else:
                        name, s = isl[i - len(ts)]; bb = s.BBox()
                        length += max(bb.GetWidth(), bb.GetHeight()) / 1e6
                        widths.add(round(min(bb.GetWidth(), bb.GetHeight()) / 1e6, 1)); what.append(f"zone '{name}'")
                        xs += [bb.GetX() / 1e6, bb.GetRight() / 1e6]; ys += [bb.GetY() / 1e6, bb.GetBottom() / 1e6]
                nseg = sum(1 for i in members if i < len(ts))
                if nseg:
                    what.append(f'{nseg} track segment' + ('s' if nseg > 1 else ''))
                chains.append((net, lname, length, sorted(widths),
                               f'x {min(xs):.1f}-{max(xs):.1f} y {min(ys):.1f}-{max(ys):.1f}', ' + '.join(what)))

    long_ = sorted((c for c in chains if c[2] > LIMIT_MM), key=lambda c: -c[2])
    fails = [c for c in long_ if (c[0], c[1]) not in ALLOWED]
    for c in long_:
        tag = 'allowed' if (c[0], c[1]) in ALLOWED else 'FAIL   '
        why = f"  [{ALLOWED[(c[0], c[1])]}]" if tag == 'allowed' else ''
        print(f"{tag} {c[0]:10s} {c[1]:11s} {c[2]:6.1f} mm  width {'/'.join(f'{w:g}' for w in c[3])} mm  {c[4]}  {c[5]}{why}")
    print(f'power on signal layers: {len(fails)} chains over {LIMIT_MM:g} mm'
          f' ({len(long_) - len(fails)} allowed by name), {len(power)} power nets, layers '
          + ' '.join(b.GetLayerName(l) for l in signal))
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
