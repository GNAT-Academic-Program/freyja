#!/usr/bin/env python3
"""Single source of truth for XC7A100T-FGG676 ball allocation.
Both ref/ballmap.md and the KiCad schematic are generated from assign()."""
import re
from collections import defaultdict, OrderedDict
from identity import FPGA_PART

PKG = 'easyeda/EasyEDA.kicad_sym'
PART = FPGA_PART

def part_block():
    text = open(PKG, encoding='utf-8').read()
    start = text.index(f'(symbol "{PART}"')
    depth, pos = 1, start + len(f'(symbol "{PART}"')
    while depth:
        depth += (text[pos] == '(') - (text[pos] == ')')
        pos += 1
    return text[start:pos]

CONFIG_USE = OrderedDict([
    ('R14', 'FLASH_D0_MOSI'), ('R15', 'FLASH_D1_MISO'),
    ('P14', 'FLASH_D2_WP'),   ('N14', 'FLASH_D3_HOLD'),
    ('P18', 'FLASH_CS_B'),    ('P15', 'PUDC_B'),
])
SIDEBAND = ['DBG_TCK', 'DBG_TMS', 'DBG_TDI', 'DBG_TDO', 'SB_UART_RX', 'SB_UART_TX']
SLOT_BANK = OrderedDict([('L', '14'), ('M', '13'),
                         ('A', '15'), ('B', '15'), ('C', '15'), ('D', '15'),
                         ('E', '34'), ('F', '34'), ('G', '34'), ('H', '34')])

def load():
    io, other = defaultdict(list), defaultdict(list)
    text = part_block()
    for m in re.finditer(r'\(pin [\s\S]*?\(name "([^"]*)"[\s\S]*?'
                         r'\(number "([^"]*)"', text):
        name, ball = m.group(1), m.group(2)
        suffix = re.search(r'_(\d+)$', name)
        bank = suffix.group(1) if suffix else 'NA'
        # A bank suffix does not make a ball user I/O: VCCO_15, for example,
        # is a supply pin. Count and allocate only names that actually begin
        # IO_. This prevents a seductive but dangerous 56-versus-50 error.
        (io if name.startswith('IO_') and bank in {'13','14','15','16','34','35'}
         else other)[bank].append((ball, name))
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

    pools = {'14': fp14}
    for bk in ('13', '15', '34'):
        fp, _ = pairs_and_singles(io[bk])
        pools[bk] = fp

    slots = OrderedDict()
    for s, bk in SLOT_BANK.items():
        # L and M are complete eight-bit 5V buses. Direct slots get twelve IO.
        prs = _take(pools[bk], used, 4 if s in ('L', 'M') else 6)
        slots[s] = (bk, prs)
        for i, ball in enumerate(b for group in prs for b in group):
            if s in ('L', 'M'):
                bus = 0 if s == 'L' else 1
                net[ball] = f'BUS5V{bus}_IO{i}'
            else:
                net[ball] = f'SLOT{s}_IO{i}'

    # One direction control per complete 8-bit bus, kept in the same fixed
    # 3.3V bank as that bus. These are low-speed controls, so an otherwise
    # unallocated ordinary IO is appropriate.
    for bus, bk in ((0, '14'), (1, '13')):
        candidates = [b for b, _ in io[bk] if b not in used]
        if not candidates: raise RuntimeError(f'bank {bk}: no IO for BUS5V{bus}_DIR')
        b = candidates[0]; used.add(b); net[b] = f'BUS5V{bus}_DIR'
    # Allocate OE after DIR to preserve every existing ball assignment.
    # These active-low enables stay in the buses' fixed 3.3V banks.
    for bus, bk in ((0, '14'), (1, '13')):
        candidates = [b for b, _ in io[bk] if b not in used]
        if not candidates: raise RuntimeError(f'bank {bk}: no IO for BUS5V{bus}_OE_N')
        b = candidates[0]; used.add(b); net[b] = f'BUS5V{bus}_OE_N'
    return net, psram, sb, slots, io, other
