#!/usr/bin/env python3
"""Series damping comparison on the routed TX nets, at resistor sites that exist on this board.

    python3 gateware/rgmii1000/damping.py board.kicad_pcb > gateware/rgmii1000/results/damping.txt

Same engine as route.py: AMD IBIS driver and package, each net's own routed sections, a lumped C at U30's pin.
The resistor is a series element at its real distance along the route, so the length before it is simulated.
Sites:
  end   4 mm before U30's pin: F.Cu already exists there, no via added. Fixed footprints allow this for all six.
  hop   on B.Cu just after the In2-to-B via: no via added. Needs second-side assembly, which the board does not have.
Results are unclamped: U30's input clamps and capacitance are unpublished, so voltages are not predictions of a pin.
Reads a board, never writes one.

Record of the choice, run on commit f2ff108, before the resistors existed. It expects no resistor on the route, so it
does not run on later boards: results/damping.txt stays as written, and txsi.py checks the laid-out copper.
"""
import importlib.util
import json
import math
import os
import sys

import numpy as np
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('route', os.path.join(HERE, 'route.py'))
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
fl = r.fl
NETS = ['PHY_TXC', 'PHY_TXD0', 'PHY_TXD1', 'PHY_TXD2', 'PHY_TXD3', 'PHY_TX_CTL']
VALUES = (0, 10, 22, 33, 47)
DRIVER = 'LVCMOS25_F_8_HR'


def split_at(secs, at):
    """Sections with a break at distance at along the copper; returns the list and the index before the break."""
    out, acc, idx = [], 0., None
    for k, d in secs:
        if k == 'via' or idx is not None:
            out.append((k, d))
        elif acc + d >= at:
            out += [(k, at - acc), (k, acc + d - at)]
            idx = len(out) - 2
        else:
            out.append((k, d))
            acc += d
    return out, idx


def site(secs, where):
    total = sum(d for k, d in secs if k != 'via')
    if where == 'end':
        at = total - 4.0
    else:   # just after the In2-to-B via
        acc = 0.
        for k, d in secs:
            if k == 'B.Cu':
                at = acc + .5
                break
            if k != 'via':
                acc += d
    s, i = split_at(secs, at)
    return s, i, at, total


def run(secs, ball, where):
    Lp, Cp = fl.pkg()
    L, C = Lp[ball], Cp[ball]
    Zp, tp = math.sqrt(L / C), math.sqrt(L * C)
    m = fl.model(DRIVER)
    s, i, at, total = site(secs, where)
    rows = {}
    for corner, name, kd, kz in ((1, 'slow', 1.05, 1.03), (2, 'fast', .95, .97)):
        d = fl.Driver(m, corner)
        ref = {e: fl.refcross(d, e) for e in 'rf'}
        ss = [(Zp, tp)] + r.sections(s, kz, kd)
        for Rv in VALUES:
            for Cl in r.CASES:
                row = {}
                for e in 'rf':
                    t, v, _ = fl.sim(d, e, ss, Cl, tend=8e-9, Rseries=(i + 1, float(Rv)) if Rv else None)
                    a = fl.cross(t, v, .2 * d.Vcc if e == 'r' else .8 * d.Vcc, e)
                    b = fl.cross(t, v, .8 * d.Vcc if e == 'r' else .2 * d.Vcc, e)
                    first = fl.cross(t, v, 1.7 if e == 'r' else .7, e)
                    after = v[np.searchsorted(t, first):]
                    mid = fl.cross(t, v, 1.25, e)
                    back = after.min() < 1.25 if e == 'r' else after.max() > 1.25
                    row[e] = dict(flight=(mid - ref[e]) * 1e9, edge=(b - a) * 1e9, vmax=float(v.max()), vmin=float(v.min()),
                                  ringback=float(after.min() - 1.7 if e == 'r' else .7 - after.max()), midcross=bool(back))
                rows[(name, Rv, int(Cl * 1e12))] = row
    return rows, at, total


def main():
    b = pcbnew.LoadBoard(sys.argv[1])
    fp = {f.GetReference(): f for f in b.GetFootprints()}
    xy = lambda p: (round(p.GetPosition().x / 1e6, 3), round(p.GetPosition().y / 1e6, 3))
    u1 = {p.GetNetname(): p for p in fp['U1'].Pads()}
    u30 = {p.GetNetname(): p for p in fp['U30'].Pads()}
    margins = {}
    with open(os.path.join(HERE, 'results', 'margins.csv')) as f:
        for line in f.read().splitlines()[1:]:
            c = line.split(',')
            margins[c[0]] = (float(c[2]), float(c[3]))
    out = {}
    for where in ('end', 'hop'):
        print(f'== site: {where}. Worst of Slow and Fast corners, 2 and 5 pF, both edges, unclamped.')
        print('net         mm before R / total   R  edge_ns   Vmax   Vmin  ringback_V  mid_recross')
        data = {}
        for n in NETS:
            secs, _ = fl.walk(b, n, xy(u1[n]), xy(u30[n]))
            rows, at, total = run(secs, u1[n].GetNumber(), where)
            data[n] = rows
            for Rv in VALUES:
                s = [rows[k][e] for k in rows if k[1] == Rv for e in 'rf']
                print(f"{n:11s} {at:6.1f} / {total:5.1f}     {Rv:3d}  {max(x['edge'] for x in s):6.2f}  {max(x['vmax'] for x in s):5.2f}  "
                      f"{min(x['vmin'] for x in s):5.2f}  {min(x['ringback'] for x in s):9.2f}  {sum(x['midcross'] for x in s):3d}", flush=True)
        # Timing: slack = limit minus routed term, with the limits of the no-board fixture.
        print('TXC R, data R: TXC edge limit 0.75 ns; TX setup and hold slack against the same limits as the fixture, ns')
        for rc in VALUES:
            sc = [data['PHY_TXC'][k][e] for k in data['PHY_TXC'] if k[1] == rc for e in 'rf']
            for rd in VALUES:
                su, ho = 1e9, 1e9
                for n in NETS[1:]:
                    d = []
                    for k in data[n]:
                        if k[1] != rd:
                            continue
                        kc = (k[0], rc, k[2])
                        d += [data[n][k][e]['flight'] - data['PHY_TXC'][kc][g]['flight'] for e in 'rf' for g in 'rf']
                    lim = margins[n]
                    su = min(su, lim[1] - max(d))
                    ho = min(ho, min(d) - lim[0])
                print(f"  {rc:3d} {rd:3d}  edge {max(x['edge'] for x in sc):.2f}  setup {su:+.3f} hold {ho:+.3f}", flush=True)
        out[where] = None
    sys.stdout.flush()


if __name__ == '__main__':
    main()
    sys.stdout.flush()
    os._exit(0)
