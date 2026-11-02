#!/usr/bin/env python3
"""Check ref/bom-jlcpcb.csv against a snapshot of the JLCPCB parts library.

    python3 tools/jlc_stock.py DB.sqlite3            # print the report
    python3 tools/jlc_stock.py DB.sqlite3 --write    # ref/jlc-stock.md

DB.sqlite3 is the in-stock database that CDFER/jlcpcb-parts-database
builds daily from yaqwsx/jlcparts (about 400 MB; components with fewer
than five pieces in stock are dropped, so a missing row means out of
stock or not in the library):

    https://cdfer.github.io/jlcpcb-parts-database/jlcpcb-components.sqlite3

For every line with an LCSC number: library type (basic, preferred or
extended, the last one paying JLCPCB's per-line fee), stock against the
need for BOARDS boards, the assembly process. For every line without
one: the basic or preferred part with the same value and package, if
any, so the matcher's choice at order time can be pinned instead.
"""
import csv, datetime, json, os, re, sqlite3, sys

HERE = os.path.dirname(os.path.abspath(__file__))
BOM = os.path.join(HERE, '..', 'ref', 'bom-jlcpcb.csv')
OUT = os.path.join(HERE, '..', 'ref', 'jlc-stock.md')
BOARDS = 10
MARGIN = 3     # flag stock below MARGIN x the need

MLCC = "subcategory='Multilayer Ceramic Capacitors MLCC - SMD/SMT'"
CHIP_R = "subcategory='Chip Resistor - Surface Mount'"


def tag(lib, pref):
    return 'basic' if lib == 'base' else ('preferred' if pref else 'extended')


def package(fp):
    m = re.search(r'_(0402|0603|0805|1206|1210)_', fp)
    return m.group(1) if m else None


def resistance(value):
    v = value.split()[0]
    if v.endswith('k'):
        return v[:-1] + 'kΩ'
    if v.endswith('M'):
        return v[:-1] + 'MΩ'
    return v + 'Ω'


def capacitance(value):
    m = re.match(r'([\d.]+)(pF|nF|uF)(?:\s+([\d.]+)V)?', value)
    if not m:
        return None, None
    num, unit = float(m.group(1)), m.group(2)
    if unit == 'uF' and num < 1:            # JLCPCB writes 0.47uF as 470nF
        num, unit = round(num * 1000), 'nF'
    text = ('%g' % num) + unit
    return text, (float(m.group(3)) if m.group(3) else None)


def generic_candidate(cur, line):
    """Basic/preferred part for a line without an LCSC number; failing that
    the best-stocked extended part; None when the library has no such value."""
    pkg = package(line['Footprint'])
    if not pkg:
        return None
    return (_candidate(cur, line, pkg, "(library_type='base' or preferred=1)")
            or _candidate(cur, line, pkg, "1"))


def _candidate(cur, line, pkg, lib):
    if line['Footprint'].startswith('R_'):
        q = cur.execute(
            f"select lcsc, mfr, library_type, preferred, stock from jlc_components "
            f"where {CHIP_R} and package=? and {lib} and json_extract(attributes,'$.Resistance')=? "
            "and json_extract(attributes,'$.Tolerance') in ('±1%','±0.5%','±0.1%') "
            "order by library_type, stock desc limit 1", (pkg, resistance(line['Comment']))).fetchone()
        return q and dict(lcsc=q[0], mfr=q[1], lib=tag(q[2], q[3]), stock=q[4], note='1%')
    if line['Footprint'].startswith('C_'):
        text, volt = capacitance(line['Comment'])
        if not text:
            return None
        for q in cur.execute(
                f"select lcsc, mfr, library_type, preferred, stock, "
                "json_extract(attributes,'$.\"Voltage Rating\"'), json_extract(attributes,'$.\"Temperature Coefficient\"') "
                f"from jlc_components where {MLCC} and package=? and {lib} "
                "and json_extract(attributes,'$.Capacitance')=? order by library_type, stock desc", (pkg, text)):
            v = float(q[5].rstrip('V')) if q[5] else 0
            if volt and v < volt:
                continue
            if q[6] not in ('C0G', 'NP0', 'X7R', 'X5R', 'X6S', 'X7S'):
                continue
            return dict(lcsc=q[0], mfr=q[1], lib=tag(q[2], q[3]), stock=q[4], note=f'{q[5]} {q[6]}')
    return None


def check(db_path, bom_path=BOM, boards=BOARDS):
    cur = sqlite3.connect(db_path).cursor()
    stamp = cur.execute('select max(fetched_at) from jlc_components').fetchone()[0]
    snapshot = datetime.datetime.fromtimestamp(stamp, datetime.timezone.utc).strftime('%Y-%m-%d')
    numbered, generic = [], []
    for line in csv.DictReader(open(bom_path, encoding='utf-8')):
        n = len(line['Designator'].split(','))
        need = n * boards
        if line['LCSC Part']:
            row = cur.execute(
                'select library_type, preferred, stock, assembly_process, attrition, price, mfr, package '
                'from jlc_components where lcsc=?', (int(line['LCSC Part'][1:]),)).fetchone()
            if row:
                attr = json.loads(row[4]) if row[4] else {}
                numbered.append(dict(line=line, need=need, lib=tag(row[0], row[1]), stock=row[2],
                                     process=row[3] or '?', moq=attr.get('leastNumber', 1),
                                     price=row[5].split(',')[0].split(':')[1] if row[5] else '?',
                                     mfr=row[6], pkg=row[7]))
            else:
                numbered.append(dict(line=line, need=need, lib='absent', stock=0, process='?',
                                     moq=0, price='?', mfr='', pkg=''))
        else:
            generic.append(dict(line=line, need=need, cand=generic_candidate(cur, line)))
    return snapshot, numbered, generic


def report(snapshot, numbered, generic, boards=BOARDS):
    out = []
    w = out.append
    w(f'# JLCPCB library check of ref/bom-jlcpcb.csv\n')
    w(f'Library snapshot {snapshot} (CDFER/jlcpcb-parts-database from yaqwsx/jlcparts, '
      f'in-stock rows only). Need is for {boards} boards. Generated by `tools/jlc_stock.py`.\n')
    absent = [x for x in numbered if x['lib'] == 'absent']
    thin = [x for x in numbered if x['lib'] != 'absent' and x['stock'] < MARGIN * x['need']]
    ext = sum(1 for x in numbered if x['lib'] == 'extended')
    unmatched = [x for x in generic if not x['cand']]
    w('## Summary\n')
    w(f'- Numbered lines: {len(numbered)}; absent from the library snapshot: {len(absent)} '
      f'({", ".join(x["line"]["LCSC Part"] + " " + x["line"]["Designator"] for x in absent) or "none"}).')
    w(f'- Stock below {MARGIN} x need: {len(thin)} '
      f'({", ".join(x["line"]["LCSC Part"] + " " + x["line"]["Designator"] for x in thin) or "none"}).')
    w(f'- Extended (fee) lines among the numbered: {ext}; basic: '
      f'{sum(1 for x in numbered if x["lib"] == "basic")}; preferred: '
      f'{sum(1 for x in numbered if x["lib"] == "preferred")}.')
    w(f'- Generic lines: {len(generic)}; with a library part of the same value and package: '
      f'{len(generic) - len(unmatched)}; without any: {len(unmatched)} '
      f'({", ".join(x["line"]["Comment"] + " " + x["line"]["Designator"] for x in unmatched) or "none"}).\n')
    w('## Numbered lines\n')
    w('| LCSC | Library | Process | Stock | Need | MOQ | Unit price | Part | Designators |')
    w('|---|---|---|---:|---:|---:|---:|---|---|')
    for x in numbered:
        l = x['line']
        flag = ' **absent**' if x['lib'] == 'absent' else (' (thin)' if x in thin else '')
        w(f"| {l['LCSC Part']} | {x['lib']}{flag} | {x['process']} | {x['stock']} | {x['need']} | {x['moq']} | "
          f"{x['price']} | {x['mfr']} {x['pkg']} | {l['Designator']} |")
    w('\n## Generic lines and a library candidate (basic or preferred first, else extended)\n')
    w('| Value | Footprint | Need | Candidate | Library | Stock | Rating | Designators |')
    w('|---|---|---:|---|---|---:|---|---|')
    for x in generic:
        l, c = x['line'], x['cand']
        if c:
            w(f"| {l['Comment']} | {l['Footprint']} | {x['need']} | C{c['lcsc']} {c['mfr']} | {c['lib']} | "
              f"{c['stock']} | {c['note']} | {l['Designator']} |")
        else:
            w(f"| {l['Comment']} | {l['Footprint']} | {x['need']} | none | | | | {l['Designator']} |")
    return '\n'.join(out) + '\n'


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        sys.exit(__doc__)
    text = report(*check(args[0]))
    if '--write' in sys.argv:
        open(OUT, 'w', encoding='utf-8').write(text)
        print('wrote', os.path.relpath(OUT))
    else:
        print(text)
