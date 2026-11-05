#!/usr/bin/env python3
"""Limits and margins for the routed board, from two fixture runs.

    python3 gateware/rgmii1000/margins.py <no-board dir> <board dir>

The no-board run has no PCB or package term: its slacks are the room the board may use, data minus clock at
the receiver, for each net. Writes results/margins.csv and results/summary.txt. Reads no hardware files.
"""
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def slacks(d):
    out = {}
    for r in csv.DictReader(open(os.path.join(d, 'slacks.csv'))):
        e = out.setdefault(r['port'], dict(dir=r['dir'], setup=1e9, hold=1e9, s_c='', h_c=''))
        if float(r['setup']) < e['setup']:
            e['setup'], e['s_c'] = float(r['setup']), r['corner']
        if float(r['hold']) < e['hold']:
            e['hold'], e['h_c'] = float(r['hold']), r['corner']
    return out


def main():
    a, c = sys.argv[1:3]
    lim, now = slacks(a), slacks(c)
    route = json.load(open(os.path.join(HERE, 'data', 'route.json')))
    rows = []
    for n in sorted(lim):
        L, N = lim[n], now[n]
        d = 'tx' if L['dir'] == 'tx' else 'rx'
        t = route[d][n]
        rows.append(dict(net=n, dir=d, limit_lo=round(-L['hold'], 3), limit_hi=round(L['setup'], 3),
                         board_lo=t['lo'], board_hi=t['hi'],
                         setup_slack=N['setup'], setup_corner=N['s_c'], hold_slack=N['hold'], hold_corner=N['h_c']))
    out = os.path.join(HERE, 'results')
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, 'margins.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(out, 'summary.txt'), 'w') as f:
        print('net          dir  limit data-clock, ns   routed data-clock, ns  setup slack      hold slack', file=f)
        for r in rows:
            print(f"{r['net']:12s} {r['dir']}  {r['limit_lo']:+.3f} .. {r['limit_hi']:+.3f}    {r['board_lo']:+.3f} .. {r['board_hi']:+.3f}     "
                  f"{r['setup_slack']:+.3f} {r['setup_corner']:4s}    {r['hold_slack']:+.3f} {r['hold_corner']}", file=f)
        for d in ('tx', 'rx'):
            g = [r for r in rows if r['dir'] == d]
            print(f"{d}: worst setup {min(r['setup_slack'] for r in g):+.3f}, worst hold {min(r['hold_slack'] for r in g):+.3f}", file=f)
    print(open(os.path.join(out, 'summary.txt')).read())


if __name__ == '__main__':
    main()
