#!/usr/bin/env python3
"""Escape depth of every assigned U1 signal ball. Gate for routing.

Depth is the number of ball rows from the nearest package edge: 1 for the
outer ring, 13 for the centre. With 0.45 mm pads, 0.45 mm vias and 0.15 mm
clearance a dog-bone fanout escapes about two rows per routing layer, so the
histogram says how many routing layers the allocation needs.

    python3 tools/depth.py            # from tools/alloc.py (the source of truth)
    python3 tools/depth.py --pcb      # from the U1 pads in kicad/odin.kicad_pcb

Balls the package forces deep (bank 0 configuration pins, the bank 14 flash
and PUDC_B pins) are reported separately from the allocator's own choices.
"""
import collections, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROWS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N',
        'P', 'R', 'T', 'U', 'V', 'W', 'Y', 'AA', 'AB', 'AC', 'AD', 'AE', 'AF']
PCB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'kicad', 'odin.kicad_pcb')
SKIP = ('GND', '+', 'VCC', 'unconnected', 'MGTR', 'MGTA', 'MGTP')


def depth(ball):
    m = re.match(r'([A-Z]+)(\d+)$', ball)
    r, c = ROWS.index(m.group(1)) + 1, int(m.group(2))
    return min(r, 27 - r, c, 27 - c)


def from_alloc():
    from alloc import assign, CONFIG_USE
    net, *_ = assign()
    return dict(net), set(CONFIG_USE)


def from_pcb():
    s = open(PCB, encoding='utf-8').read()
    i = s.find('(property "Reference" "U1"')
    start = s.rfind('\n\t(footprint ', 0, i)
    end = s.find('\n\t(footprint ', start + 10)
    pads = re.findall(r'\(pad "([A-Z]+\d+)" smd[\s\S]*?\(net \d+ "([^"]+)"\)',
                      s[start:end])
    net = {b: n for b, n in pads if not n.startswith(SKIP)}
    inherent = {b for b, n in net.items()
                if n.startswith(('CFG_', 'JTAG_', 'FLASH_', 'PUDC_B', 'FPGA_DX'))}
    return net, inherent


def main():
    # alloc.py covers HR I/O only. The PCB view adds the bank 0 configuration
    # balls, which the package fixes and which count as inherent.
    net, inherent = from_pcb() if '--pcb' in sys.argv else from_alloc()
    hist = collections.Counter(depth(b) for b in net)
    print(f'signal balls {len(net)}')
    for d in sorted(hist):
        print(f'  depth {d:2d}: {hist[d]}')
    deep = sorted((depth(b), net[b], b) for b in net if depth(b) >= 7)
    chosen = [x for x in deep if x[2] not in inherent]
    print(f'depth >= 7: {len(deep)}  (inherent {len(deep) - len(chosen)}, '
          f'allocator choice {len(chosen)})')
    for d, n, b in deep:
        print(f'  {b:5s} {d:2d} {n}' + ('  (inherent)' if b in inherent else ''))
    return len(chosen)


if __name__ == '__main__':
    main()
