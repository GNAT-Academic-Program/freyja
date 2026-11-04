#!/usr/bin/env python3
"""Turns the fixture's slacks and arcs into the numbers quoted in README.md.

    python3 gateware/sdram100/margins.py

Reads build/slacks.csv and build/arcs.txt, data/flight_8.json. Writes
results/margins.csv and results/summary.txt.
"""
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from mkprofile import budget, T_AC

T_HZ, T_LZ = 5.0, 0.0   # W9825G6KH rev A03, section 9.5, -6, CL3
T = 10.0
FWD = 7.5               # +270 degrees


def note8(sim):
    """Datasheet note 8: (tr + tf)/2 - 1 ns on setup and hold when edges are slower than 1 ns."""
    return max(0., max((sim[c]['r']['edge'] + sim[c]['f']['edge']) / 2 - 1 for c in sim))


def worst(rows, key):
    return min(rows, key=lambda r: r[key])


def main():
    b = budget()
    flight = json.load(open(os.path.join(HERE, 'data', 'flight_8.json')))
    by = {r['net']: r for r in b['rows']}
    slacks = list(csv.DictReader(open(os.path.join(HERE, 'build', 'slacks.csv'))))
    rows = []
    for s in slacks:
        n, d = s['port'], s['dir']
        is_dq = re.fullmatch(r'SDRAM_DQ\d+', n)
        group = 'read' if d == 'in' else 'release' if d == 't' else 'write' if is_dq else 'command'
        rows.append(dict(group=group, net=n, setup=float(s['setup']), hold=float(s['hold']),
                         note8=note8(flight[n]['sim']) if group in ('command', 'write') else 0.))
    with open(os.path.join(HERE, 'results', 'margins.csv'), 'w', newline='') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(['group', 'net', 'setup_ns', 'hold_ns', 'note8_addition_ns'])
        for r in rows:
            w.writerow([r['group'], r['net'], f"{r['setup']:.3f}", f"{r['hold']:.3f}", f"{r['note8']:.3f}"])

    out = []
    dc_min, dc_max = b['dc_min'], b['dc_max']
    for g in ('command', 'write'):
        rr = [r for r in rows if r['group'] == g]
        for r in rr:
            r['setup8'], r['hold8'] = r['setup'] - r['note8'], r['hold'] - r['note8']
        settle = [by[r['net']]['settle'] - dc_min for r in rr]
        leave = [by[r['net']]['leave'] - dc_max for r in rr]
        su, hd = worst(rr, 'setup'), worst(rr, 'hold')
        su8, hd8 = worst(rr, 'setup8'), worst(rr, 'hold8')
        lim_su = min(r['setup'] + by[r['net']]['settle'] - dc_min for r in rr)
        lim_hd = max(by[r['net']]['leave'] - dc_max - r['hold'] for r in rr)
        out.append(f"{g}: setup {su['setup']:+.2f} ({su['net']}) hold {hd['hold']:+.2f} ({hd['net']}); "
                   f"with note 8 setup {su8['setup8']:+.2f} ({su8['net']}) hold {hd8['hold8']:+.2f} ({hd8['net']}); "
                   f"limits settle-clock <= {lim_su:+.2f} leave-clock >= {lim_hd:+.2f}; now {max(settle):+.2f} {min(leave):+.2f}")
    rd = [r for r in rows if r['group'] == 'read']
    su, hd = worst(rd, 'setup'), worst(rd, 'hold')
    lim = min(r['setup'] + dc_max + by[r['net']]['q_max'] for r in rd)
    now = [dc_min + by[r['net']]['q_min'] for r in rd] + [dc_max + by[r['net']]['q_max'] for r in rd]
    out.append(f"read: setup {su['setup']:+.2f} ({su['net']}) hold {hd['hold']:+.2f} ({hd['net']}); "
               f"limit clock+DQ <= {lim:.2f}; now {min(now):.2f}-{max(now):.2f}")
    rl = [r for r in rows if r['group'] == 'release']
    su, hd = worst(rl, 'setup'), worst(rl, 'hold')
    out.append(f"T arc, either direction: setup {su['setup']:+.3f} ({su['net']}) hold {hd['hold']:+.3f} ({hd['net']})")

    # Turnaround. c0 edges are numbered from the edge launching READ. U32 edge n follows c0 edge n by FWD.
    arcs = {}
    for line in open(os.path.join(HERE, 'build', 'arcs.txt')):
        p = line.split()
        if p[1] == 'fwd':
            arcs[p[0], 'fwd'] = (float(p[2]), float(p[3]))
        else:
            arcs[p[0], p[1], p[2]] = (float(p[3]), float(p[4]))
    q = [(by[f'SDRAM_DQ{i}']['q_min'], by[f'SDRAM_DQ{i}']['q_max']) for i in range(16)]
    q_min, q_max = min(a for a, _ in q), max(a for _, a in q)
    for c in ('Slow', 'Fast'):
        early, late = arcs[c, 'fwd']
        on_min = min(arcs[c, 'enable', 'setup'][0], arcs[c, 'enable', 'hold'][0])
        off_max = max(arcs[c, 'disable', 'setup'][1], arcs[c, 'disable', 'hold'][1])
        # BL4: last word launched by U32 edge 5, tHZ runs from U32 edge 6.
        off_at_u32 = 6 * T + FWD + late + dc_max + T_HZ
        for edge in (7, 8):
            on = edge * T + on_min
            out.append(f"{c} BL4 read to write, FPGA drives from c0 edge {edge}: "
                       f"margin at U32 {on + q_min - off_at_u32:+.2f}, at FPGA pad {on - off_at_u32 - q_max:+.2f}")
        # U32 may start driving at U32 edge 2 + tLZ.
        u32_on = 2 * T + FWD + early + dc_min + T_LZ
        for k in (0, 1, 2):
            out.append(f"{c} write to read, FPGA release launched {k} cycles after READ: "
                       f"{u32_on - (k * T + off_max + q_max):.2f} ns before U32 can drive")
    text = '\n'.join(out) + '\n'
    open(os.path.join(HERE, 'results', 'summary.txt'), 'w').write(text)
    print(text, end='')


if __name__ == '__main__':
    main()
