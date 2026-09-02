#!/usr/bin/env python3
"""Single source of truth for XC7A50T-CSG325 ball allocation.
Both ref/ballmap.md and the KiCad schematic are generated from assign()."""
import re
from collections import defaultdict, OrderedDict

PKG = 'ref/xc7a50tcsg325pkg.txt'

CONFIG_USE = OrderedDict([
    ('K16', 'FLASH_D0_MOSI'), ('L17', 'FLASH_D1_MISO'),
    ('J15', 'FLASH_D2_WP'),   ('J16', 'FLASH_D3_HOLD'),
    ('L15', 'FLASH_CS_B'),    ('J18', 'PUDC_B'),
])
SIDEBAND = ['DBG_TCK', 'DBG_TMS', 'DBG_TDI', 'DBG_TDO', 'SB_UART_RX', 'SB_UART_TX']
SLOT_BANK = OrderedDict([('L', '14'),
                         ('A', '15'), ('B', '15'), ('C', '15'), ('D', '15'),
                         ('E', '34'), ('F', '34'), ('G', '34'), ('H', '34')])

def load():
    io, other = defaultdict(list), defaultdict(list)
    for l in open(PKG, encoding='utf-8', errors='replace'):
        l = l.replace('\r', '').rstrip()
        if not l.strip() or l.startswith(('Device/Package', 'Pin ', 'Total Number')): continue
        f = re.split(r'\s{2,}', l.strip())
        if len(f) < 7: continue
        ball, name, _, bank, _, _, iot = f[:7]
        (io if iot == 'HR' else other)[bank].append((ball, name))
    return io, other

def pairs_and_singles(pins):
    p, single = defaultdict(dict), []
    for ball, name in pins:
        m = re.match(r'IO_L(\d+)([PN])_T(\d+)', name)
        if m: p[int(m.group(1))][m.group(2)] = ball
        else: single.append(ball)
    full = [(v['P'], v['N'], k) for k, v in sorted(p.items()) if len(v) == 2]
    half = [b for v in p.values() if len(v) == 1 for b in v.values()]
    return full, single + half

def _take(pool, used, n):
    got = []
    while len(got) < n and pool:
        a, b, i = pool.pop(0)
        if a in used or b in used: continue
        used.update((a, b)); got.append((a, b))
    if len(got) < n: raise RuntimeError(f"ran out of differential pairs: wanted {n}, got {len(got)}")
    return got

def assign():
    """-> (net_of_ball: dict, psram: dict, sideband: list, slots: OrderedDict, io, other)"""
    io, other = load()
    used = set(CONFIG_USE)
    net = dict(CONFIG_USE)

    fp14, _ = pairs_and_singles(io['14'])
    fp14 = [t for t in fp14 if t[0] not in used and t[1] not in used]

    psram = OrderedDict()
    lanes = ['SCK', 'CE_B', 'IO0', 'IO1', 'IO2', 'IO3']
    for c in range(4):
        balls = [b for pr in _take(fp14, used, 3) for b in pr]
        psram[c] = balls
        for b, ln in zip(balls, lanes): net[b] = f'PSRAM{c}_{ln}'

    sb = [b for pr in _take(fp14, used, 3) for b in pr]
    for b, n in zip(sb, SIDEBAND): net[b] = n

    # level-shifter direction control for slot L: bank 14 has leftover
    # single-ended balls (true singles plus the unused halves of the pairs
    # that config took), which is exactly what these low-speed pins want.
    _, sg14 = pairs_and_singles(io['14'])
    spare14 = [b for b in sg14 if b not in used]
    halves = [b for pr in pairs_and_singles(io['14'])[0]
              for b in pr[:2] if b not in used]
    for i, b in enumerate((spare14 + halves)[:2]):
        used.add(b); net[b] = f'SLOTL_DIR{i}'

    pools = {'14': fp14}
    for bk in ('15', '34'):
        fp, _ = pairs_and_singles(io[bk])
        pools[bk] = fp

    slots = OrderedDict()
    for s, bk in SLOT_BANK.items():
        prs = _take(pools[bk], used, 5)
        slots[s] = (bk, prs)
        for i, (p, n_) in enumerate(prs):
            net[p] = f'SLOT{s}_P{i}_P'
            net[n_] = f'SLOT{s}_P{i}_N'
    return net, psram, sb, slots, io, other
