#!/usr/bin/env python3
"""JLCPCB assembly BOM from tools/design.py.

    python3 tools/bom_jlc.py            # print the table
    python3 tools/bom_jlc.py --write    # ref/bom-jlcpcb.csv

The CSV has JLCPCB's four columns (Comment, Designator, Footprint, LCSC
Part), one row per identical part (same value, footprint and LCSC
number), designators comma-separated. Parts marked DNP are left out.
Passives without an LCSC number keep an empty LCSC column, for JLCPCB's
matcher to propose a same-value part at order time (kicad/README.md).
"""
import csv, io, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from design import build

BOARDS = 10

def rows():
    parts = [p for p in build().parts if not p.get('dnp') and p.get('bom', True)]
    groups = {}
    for p in parts:
        key = (p['value'], p['fp'], p['lcsc'])
        groups.setdefault(key, []).append(p['ref'])
    def natural(r):
        import re
        m = re.match(r'([A-Z]+)(\d+)([A-Z]?)', r)
        return (m.group(1), int(m.group(2)), m.group(3))
    out = []
    for (value, fp, lcsc), refs in groups.items():
        refs = sorted(refs, key=natural)
        out.append((value, ','.join(refs), fp.split(':', 1)[-1], lcsc, len(refs)))
    out.sort(key=lambda r: natural(r[1].split(',')[0]))
    return out


def csv_text(table):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator='\n')
    w.writerow(['Comment', 'Designator', 'Footprint', 'LCSC Part'])
    for value, refs, fp, lcsc, _n in table:
        w.writerow([value, refs, fp, lcsc])
    return buf.getvalue()


def main():
    table = rows()
    text = csv_text(table)
    with_lcsc = sum(1 for r in table if r[3])
    print(f'{len(table)} BOM lines for {sum(r[4] for r in table)} fitted parts, '
          f'{with_lcsc} lines with an LCSC number')
    if '--write' in sys.argv:
        open('ref/bom-jlcpcb.csv', 'w').write(text)
        print('wrote ref/bom-jlcpcb.csv')
    else:
        print(text[:1500])


if __name__ == '__main__':
    main()
