#!/usr/bin/env python3
"""Single source of truth for XC7A100T-FGG676 ball allocation.
Both ref/ballmap.md and the KiCad schematic are generated from assign().

    python3 tools/alloc.py            # table and checks
    python3 tools/alloc.py --check    # checks only, exit 1 on failure

Inside every bank the allocator takes the shallowest balls first (escape
depth, see tools/depth.py), so the fan-out needs as few routing layers as the
package allows. Banks 15 and 34 are full either way and keep their order.
"""
import re, sys
from collections import defaultdict, OrderedDict
from identity import FPGA_PART
from depth import depth, ROWS

PKG = 'easyeda/EasyEDA.kicad_sym'
PART = FPGA_PART

def part_block():
    text = open(PKG, encoding='utf-8').read()
    start = text.index(f'(symbol "{PART}"')
    depth_, pos = 1, start + len(f'(symbol "{PART}"')
    while depth_:
        depth_ += (text[pos] == '(') - (text[pos] == ')')
        pos += 1
    return text[start:pos]

CONFIG_USE = OrderedDict([
    ('R14', 'FLASH_D0_MOSI'), ('R15', 'FLASH_D1_MISO'),
    ('P14', 'FLASH_D2_WP'),   ('N14', 'FLASH_D3_HOLD'),
    ('P18', 'FLASH_CS_B'),    ('P15', 'PUDC_B'),
])
SIDEBAND = ['DBG_TCK', 'DBG_TMS', 'DBG_TDI', 'DBG_TDO', 'SB_UART_RX', 'SB_UART_TX']
# Both 5 V buses live in bank 13 (3.3 V, the bottom-right of the package,
# facing the bottom edge where J7/J8 sit). Bank 14 keeps the PSRAM, the
# sideband and the flash. Direct slots: A-D bank 15, E-H bank 34.
SLOT_BANK = OrderedDict([('L', '13'), ('M', '13'),
                         ('A', '15'), ('B', '15'), ('C', '15'), ('D', '15'),
                         ('E', '34'), ('F', '34'), ('G', '34'), ('H', '34')])

# The fabric's own clock: 50 MHz CMOS oscillator X4 into bank 14 (3.3 V).
SYS_CLK = 'SYS_CLK'
# Bank 16 is the network bank, VCCO = +2V5 (gen_sch.RAIL). RGMII at 2.5 V
# to the RTL8211FD-CG: TXC/TXD/TX_CTL driven by the fabric, RXC/RXD/RX_CTL
# from the PHY, MDC/MDIO at the DVDD_RG level (RTL8211F Table 58). RXC is
# the only single-ended input clock and goes on an MRCC P ball.
RGMII_RXC = 'PHY_RXC'
RGMII = ['PHY_RXD0', 'PHY_RXD1', 'PHY_RXD2', 'PHY_RXD3', 'PHY_RX_CTL',
         'PHY_TXC', 'PHY_TXD0', 'PHY_TXD1', 'PHY_TXD2', 'PHY_TXD3', 'PHY_TX_CTL',
         'PHY_MDC', 'PHY_MDIO']
# Two raw LVDS_25 link ports, four pairs each: a clock and a data pair out,
# a clock and a data pair in. The incoming clock sits on a clock-capable
# pair (MRCC for P, SRCC for Q; both reach BUFG/BUFR, UG472 ch. 2).
LINK_PORTS = ('P', 'Q')
LINK_PAIRS = ['TXC', 'TXD', 'RXD']           # plus RXC on the clock-capable pair
# PHYRSTB and INTB are 3.3 V pins (RTL8211F Table 58 note): bank 13.
BANK13_SINGLES = ['PHY_RESET_N', 'PHY_INT_N']

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

def _col(ball):
    return int(re.search(r'\d+$', ball).group())

def _by_depth(pairs, toward_top=False):
    """Shallowest pair first. With toward_top, prefer the higher package
    column (column 26 faces the top board edge) among equally deep pairs."""
    return sorted(pairs, key=lambda t: (max(depth(t[0]), depth(t[1])),
                                        -_col(t[0]) if toward_top else 0, t[2]))

def _take(pool, used, n):
    got = []
    while len(got) < n and pool:
        a, b, i = pool.pop(0)
        if a in used or b in used: continue
        used.update((a, b)); got.append((a, b))
    if len(got) < n: raise RuntimeError(f"ran out of differential pairs: wanted {n}, got {len(got)}")
    return got

def _take_pair_named(pool, used, tag, names):
    """Pop the shallowest unused pair whose P ball carries `tag` (MRCC/SRCC)."""
    for i, (a, b, k) in enumerate(pool):
        if a in used or b in used: continue
        if tag in names[a]:
            pool.pop(i); used.update((a, b)); return a, b
    raise RuntimeError(f'no free {tag} pair')

def _take_singles(pool, singles, used, n):
    """n single-ended balls: leftover singles first, then whole pairs."""
    got = []
    for b in list(singles):
        if len(got) == n: break
        if b not in used: used.add(b); got.append(b); singles.remove(b)
    while len(got) < n:
        a, b = _take(pool, used, 1)[0]
        got += [a, b]
    if len(got) > n:                      # half a pair left over: keep it single
        extra = got.pop(); used.discard(extra); singles.insert(0, extra)
    return got

def assign():
    """-> (net_of_ball: dict, psram: dict, sideband: list, slots: OrderedDict, io, other)"""
    io, other = load()
    used = set(CONFIG_USE)
    net = dict(CONFIG_USE)
    names = {b: n for lst in io.values() for b, n in lst}

    # ---- bank 14: the fabric clock, PSRAM x4 (3 pairs each) and the
    # sideband, shallowest first. SYS_CLK is the 50 MHz oscillator (X4): a
    # single-ended clock on the P side of an MRCC pair (UG472 ch. 2), so it
    # reaches the MMCMs; the pair's N ball stays free.
    fp14, s14 = pairs_and_singles(io['14'])
    fp14 = _by_depth(t for t in fp14 if t[0] not in used and t[1] not in used)
    clk, _clk_n = _take_pair_named(fp14, used, 'MRCC', names)
    net[clk] = SYS_CLK
    psram = OrderedDict()
    lanes = ['SCK', 'CE_B', 'IO0', 'IO1', 'IO2', 'IO3']
    for c in range(4):
        balls = [b for pr in _take(fp14, used, 3) for b in pr]
        psram[c] = balls
        for b, ln in zip(balls, lanes): net[b] = f'PSRAM{c}_{ln}'
    sb = [b for pr in _take(fp14, used, 3) for b in pr]
    for b, n in zip(sb, SIDEBAND): net[b] = n

    # ---- slots. 15 and 34 are full, order is irrelevant; 13 is depth sorted.
    pools, singles = {}, {}
    for bk in ('13', '15', '34'):
        fp, sg = pairs_and_singles(io[bk])
        pools[bk] = _by_depth(fp) if bk == '13' else fp
        singles[bk] = sg
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
    # One direction control and one active-low enable per bus, low speed,
    # in the buses' 3.3 V bank. Then the two 3.3 V PHY control pins.
    for n in ('BUS5V0_DIR', 'BUS5V1_DIR', 'BUS5V0_OE_N', 'BUS5V1_OE_N', *BANK13_SINGLES):
        net[_take_singles(pools['13'], singles['13'], used, 1)[0]] = n

    # ---- bank 16: RGMII and the two link ports
    fp16, s16 = pairs_and_singles(io['16'])
    fp16 = _by_depth(fp16, toward_top=True)
    rxc, rxc_n = _take_pair_named(fp16, used, 'MRCC', names)
    net[rxc] = RGMII_RXC
    rgmii = list(RGMII)
    net[rxc_n] = rgmii.pop(0)
    link = OrderedDict()
    for port, tag in zip(LINK_PORTS, ('MRCC', 'SRCC')):
        p, n = _take_pair_named(fp16, used, tag, names)
        link[port] = OrderedDict([('RXC', (p, n))])
        net[p], net[n] = f'LINK_{port}_RXC_P', f'LINK_{port}_RXC_N'
    for port in LINK_PORTS:
        for name, (p, n) in zip(LINK_PAIRS, _take(fp16, used, len(LINK_PAIRS))):
            link[port][name] = (p, n)
            net[p], net[n] = f'LINK_{port}_{name}_P', f'LINK_{port}_{name}_N'
    for b, n in zip(_take_singles(fp16, s16, used, len(rgmii)), rgmii): net[b] = n

    assign.link = link                    # for ballmap.py
    return net, psram, sb, slots, io, other

def check(net, io):
    """Structural checks; returns a list of problems."""
    names = {b: n for lst in io.values() for b, n in lst}
    probs = []
    by_net = defaultdict(list)
    for b, n in net.items(): by_net[n].append(b)
    for n, balls in by_net.items():
        if len(balls) > 1: probs.append(f'{n} on {balls}')
    inv = {n: b for b, n in net.items()}
    for clk in (SYS_CLK, 'PHY_RXC'):
        if 'MRCC' not in names[inv[clk]] or not names[inv[clk]].split('_')[1].endswith('P'):
            probs.append(f'{clk} is not on an MRCC P ball')
    if not names[inv[SYS_CLK]].endswith('_14'): probs.append('SYS_CLK is not in bank 14')
    for port, tag in zip(LINK_PORTS, ('MRCC', 'SRCC')):
        p, n = inv[f'LINK_{port}_RXC_P'], inv[f'LINK_{port}_RXC_N']
        if tag not in names[p] or names[p].split('_')[1][:-1] != names[n].split('_')[1][:-1]:
            probs.append(f'LINK_{port}_RXC is not a {tag} pair')
    for pre, bank in (('PHY_', '16'), ('LINK_', '16'), ('BUS5V', '13'), ('PSRAM', '14'), ('SLOTA', '15'), ('SLOTE', '34')):
        for n, b in inv.items():
            if n.startswith(pre) and n not in BANK13_SINGLES and not names[b].endswith('_' + bank):
                probs.append(f'{n} on {b} is not in bank {bank}')
    for n in BANK13_SINGLES:
        if not names[inv[n]].endswith('_13'): probs.append(f'{n} is not in bank 13')
    return probs

if __name__ == '__main__':
    import collections
    net, psram, sb, slots, io, other = assign()
    probs = check(net, io)
    if '--check' not in sys.argv:
        for b, n in sorted(net.items(), key=lambda t: (depth(t[0]), t[0])):
            print(f'{b:5s} depth {depth(b):2d}  {n}')
    hist = collections.Counter(depth(b) for b in net)
    print('depth histogram:', dict(sorted(hist.items())))
    deep = [(b, n) for b, n in net.items() if depth(b) >= 7]
    inherent = [b for b in deep if b[0] in CONFIG_USE]
    print(f'depth >= 7: {len(deep)} ({len(inherent)} inherent flash/PUDC_B, '
          f'{len(deep) - len(inherent)} allocator choice)')
    for p in probs: print('PROBLEM', p)
    sys.exit(1 if probs else 0)
