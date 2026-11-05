#!/usr/bin/env python3
"""Routed delays of the RGMII nets, for mkprofile.py and the review.

    python3 gateware/rgmii1000/route.py board.kicad_pcb [gateware/rgmii1000/data/route.json]

Walks each net from ball to pin on the saved board, so the numbers are of the copper, not of a plan.
TX: AMD IBIS driver through the package and the routed sections into a lumped C at the pin, using the
engine in ../sdram100/flight.py. Flight is the 1.25 V crossing at U30 minus the driver's own crossing
into its IBIS test load, the condition of Vivado's OBUF delay, so the package is inside it.
RX: no RTL8211F IBIS model exists, so line delay only, plus the FPGA package from data/pkg_delay.csv.
Per-layer delay from ../sdram100/results/fieldsolve.txt; barrels at 6.97 ps/mm, assumed, not a via solve.
Reads a board, never writes one.
"""
import hashlib
import importlib.util
import json
import math
import os
import sys

import numpy as np
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('flight', os.path.join(HERE, '..', 'sdram100', 'flight.py'))
fl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fl)

CLK = {'tx': 'PHY_TXC', 'rx': 'PHY_RXC'}
TX = ['PHY_TXD0', 'PHY_TXD1', 'PHY_TXD2', 'PHY_TXD3', 'PHY_TX_CTL']
RX = ['PHY_RXD0', 'PHY_RXD1', 'PHY_RXD2', 'PHY_RXD3', 'PHY_RX_CTL']
MGMT = ['PHY_MDC', 'PHY_MDIO', 'PHY_RESET_N', 'PHY_INT_N']
# ps/mm: nominal and the spread from the field solve. Outer lanes 5.74-6.00 with a neighbour at 0.3 mm.
OUTER = (5.74, 5.88, 6.00)
INNER = (6.79, 6.97, 7.14)
BARREL_PS_MM = 6.97
# mid-plane depth of each routing layer, from ref/pcb-impedance.md, F.Cu to B.Cu 1.5886 mm
DEPTH = {'F.Cu': 0., 'In2': .2167, 'In5': 1.3719, 'B.Cu': 1.5886}
ZL = {'F.Cu': 48.4, 'B.Cu': 48.4, 'In2': 49.1, 'In5': 49.1}
CASES = [2e-12, 5e-12]      # U30 input capacitance is not published: a range, assumed


def barrel(pair):
    a, c = sorted(pair, key=lambda k: DEPTH[k]) if len(pair) == 2 else (list(pair)[0], list(pair)[0])
    return abs(DEPTH[c] - DEPTH[a])


def describe(secs):
    """mm per layer, vias, nominal ps, and the ps for each of the four spread corners."""
    mm = {}
    vias = []
    for k, d in secs:
        if k == 'via':
            vias.append(barrel(d))
        else:
            mm[k] = mm.get(k, 0.) + d
    outer = mm.get('F.Cu', 0.) + mm.get('B.Cu', 0.)
    inner = mm.get('In2', 0.) + mm.get('In5', 0.)
    bar = sum(vias) * BARREL_PS_MM
    corners = {(a, b): outer * OUTER[a] + inner * INNER[b] + bar for a in (0, 2) for b in (0, 2)}
    return dict(mm={k: round(v, 3) for k, v in mm.items()}, length=round(outer + inner, 3), vias=len(vias),
                barrel_mm=round(sum(vias), 4), nominal_ps=round(outer * OUTER[1] + inner * INNER[1] + bar, 2)), corners


def sections(secs, kz, kd):
    out = []
    for k, d in secs:
        if k == 'via':
            out.append((60., max(1e-12, barrel(d) * BARREL_PS_MM * 1e-12) * kd))
        else:
            td = (OUTER[1] if k in ('F.Cu', 'B.Cu') else INNER[1]) * 1e-12
            out.append((ZL[k] * kz, d * td * kd))
    return out


def tx_flight(secs, ball, driver_name):
    """Per corner and load: flight, edge rate, overshoot and ringback at U30."""
    Lp, Cp = fl.pkg()
    L, C = Lp[ball], Cp[ball]
    Zp, tp = math.sqrt(L / C), math.sqrt(L * C)
    m = fl.model(driver_name)
    out = {}
    for c, name, kd, kz in ((1, 'slow', 1.05, 1.03), (2, 'fast', .95, .97)):
        d = fl.Driver(m, c)
        ref = {e: fl.refcross(d, e) for e in 'rf'}
        for Cl in CASES:
            key = f'{name}_{int(Cl * 1e12)}pF'
            row = {}
            for e in 'rf':
                t, v, _ = fl.sim(d, e, [(Zp, tp)] + sections(secs, kz, kd), Cl, tend=8e-9)
                a = fl.cross(t, v, .2 * d.Vcc if e == 'r' else .8 * d.Vcc, e)
                b = fl.cross(t, v, .8 * d.Vcc if e == 'r' else .2 * d.Vcc, e)
                first = fl.cross(t, v, 1.7 if e == 'r' else .7, e)
                after = v[np.searchsorted(t, first):]
                bad = np.where(v < 1.7)[0] if e == 'r' else np.where(v > .7)[0]
                settle = t[bad[-1] + 1] if len(bad) and bad[-1] + 1 < len(t) else None
                row[e] = dict(flight=round((fl.cross(t, v, 1.25, e) - ref[e]) * 1e9, 4),
                              settle=round((settle - ref[e]) * 1e9, 4) if settle is not None else None,
                              edge_20_80=round((b - a) * 1e9, 3), vmax=round(float(v.max()), 2), vmin=round(float(v.min()), 2),
                              ringback=round(float(after.min() - 1.7 if e == 'r' else .7 - after.max()), 3))
            out[key] = row
    return out


def main():
    board = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'data', 'route.json')
    driver = os.environ.get('DRIVER', 'LVCMOS25_F_8_HR')
    b = pcbnew.LoadBoard(board)
    fp = {f.GetReference(): f for f in b.GetFootprints()}
    xy = lambda p: (round(p.GetPosition().x / 1e6, 3), round(p.GetPosition().y / 1e6, 3))
    u1 = {p.GetNetname(): p for p in fp['U1'].Pads()}
    u30 = {p.GetNetname(): p for p in fp['U30'].Pads()}
    pkg = {}
    for line in open(os.path.join(HERE, 'data', 'pkg_delay.csv')):
        if not line.startswith('#'):
            ball, lo, hi = line.strip().split(',')
            pkg[ball] = (float(lo) / 1000, float(hi) / 1000)
    nets = {}
    for n in [CLK['tx']] + TX + [CLK['rx']] + RX + MGMT:
        # flight.walk expects F.Cu ends at the pads; every net here starts and ends on F.Cu
        secs, _ = fl.walk(b, n, xy(u1[n]), xy(u30[n]))
        row, corners = describe(secs)
        ball = u1[n].GetNumber()
        row.update(ball=ball, pin=u30[n].GetNumber(), pkg_ps=[round(v * 1000, 1) for v in pkg[ball]],
                   sections=[(k, round(d, 3)) if k != 'via' else ('via', '-'.join(sorted(d))) for k, d in secs])
        row['_corners'] = {f'{a}{c}': v for (a, c), v in corners.items()}
        if n in TX or n == CLK['tx']:
            row['sim'] = tx_flight(secs, ball, driver)
        nets[n] = row
        print(n, ball, 'pin', row['pin'], row['length'], 'mm', row['mm'], 'vias', row['vias'], 'ps', row['nominal_ps'], flush=True)
    res = dict(board_sha256=hashlib.sha256(open(board, 'rb').read()).hexdigest(), driver=driver, nets=nets, tx={}, rx={})
    # TX: data minus clock at U30, from the simulation, each load case on both, all edge pairs.
    clk = nets[CLK['tx']]['sim']
    for n in TX:
        s = nets[n]['sim']
        d = [s[k][e]['flight'] - clk[k][g]['flight'] for k in s for e in 'rf' for g in 'rf']
        res['tx'][n] = dict(lo=round(min(d), 4), hi=round(max(d), 4), nominal_line_ps=round(nets[n]['nominal_ps'] - nets[CLK['tx']]['nominal_ps'], 2))
    # RX: data minus clock at the FPGA balls: line at the four spread corners, plus package min and max.
    ck = nets[CLK['rx']]
    for n in RX:
        r = nets[n]
        line = [r['_corners'][k] - ck['_corners'][k] for k in r['_corners']]
        res['rx'][n] = dict(lo=round((min(line) + r['pkg_ps'][0] - ck['pkg_ps'][1]) / 1000, 4),
                            hi=round((max(line) + r['pkg_ps'][1] - ck['pkg_ps'][0]) / 1000, 4),
                            line_ps=[round(min(line), 2), round(max(line), 2)])
    for r in nets.values():
        del r['_corners']
    json.dump(res, open(out, 'w'), indent=1)
    print('tx', json.dumps(res['tx']))
    print('rx', json.dumps(res['rx']))


if __name__ == '__main__':
    main()
    sys.stdout.flush()
    os._exit(0)
