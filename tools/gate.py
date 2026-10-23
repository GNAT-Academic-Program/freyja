#!/usr/bin/env python3
"""Run every rev A phase gate and print the numbers for ref/rev-a-report.md.

    python3 tools/gate.py

Read-only. Runs, in order: design.py / budget.py / qualified.py build checks,
check_erc.py, netlist export to a scratch file compared with kicad/odin.net,
DRC with schematic parity, place.py --check, depth.py. Exits non-zero if a
blocking check fails (build errors, ERC, parity, netlist drift). DRC
violations and unrouted counts are reported, not gated: the board is not
routed yet.
"""
import collections, json, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
PY = sys.executable


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def parts_and_sheets():
    s = open('kicad/odin.net').read()
    comps = re.findall(r'\(comp \(ref "([^"]+)"\)[\s\S]*?\(sheetpath \(names "([^"]*)"', s)
    by = collections.Counter(n.strip('/') or 'root' for _, n in comps)
    return len(comps), dict(sorted(by.items()))


def pcb_counts():
    s = open('kicad/odin.kicad_pcb', encoding='utf-8').read()
    fps = re.split(r'\n\t\(footprint ', s)[1:]
    inside = bcu = 0
    for f in fps:
        m = re.search(r'\(at ([-\d.]+) ([-\d.]+)', f)
        x, y = float(m.group(1)), float(m.group(2))
        if 30 <= x <= 130 and 30 <= y <= 130: inside += 1
        if '(layer "B.Cu")' in f[:400]: bcu += 1
    return dict(footprints=len(fps), inside=inside, outside=len(fps) - inside,
                bcu=bcu, tracks=len(re.findall(r'\n\t\(segment ', s)),
                vias=len(re.findall(r'\n\t\(via ', s)))


def main():
    ok = True
    for tool in ('design.py', 'budget.py', 'qualified.py'):
        r = run([PY, f'tools/{tool}'])
        print(f'{tool:14s} exit {r.returncode}')
        if r.returncode: ok = False; print(r.stdout[-800:], r.stderr[-800:])

    with tempfile.TemporaryDirectory() as tmp:
        net = os.path.join(tmp, 'odin.net')
        r = run(['kicad-cli', 'sch', 'export', 'netlist', '--format', 'kicadsexpr',
                 '-o', net, 'kicad/odin.kicad_sch'])
        if r.returncode: ok = False; print('netlist export failed', r.stderr[-500:])
        else:
            strip = lambda t: re.sub(r'\(date "[^"]*"\)|\(tool "[^"]*"\)', '', t)
            if strip(open(net).read()) != strip(open('kicad/odin.net').read()):
                ok = False; print('NETLIST DRIFT: kicad/odin.net is not the export of the schematic')
            else: print('netlist        matches kicad/odin.net')

        r = run([PY, 'tools/check_erc.py'])
        print('check_erc.py   exit', r.returncode, '|', r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr.strip()[-200:])
        if r.returncode: ok = False

        drc = os.path.join(tmp, 'drc.json')
        r = run(['kicad-cli', 'pcb', 'drc', '--schematic-parity', '--severity-all',
                 '--format', 'json', '-o', drc, 'kicad/odin.kicad_pcb'])
        d = json.load(open(drc))
        v = d['violations']
        sev = collections.Counter(x['severity'] for x in v)
        parity = d.get('schematic_parity', [])
        print(f"DRC            {sev.get('error',0)} errors, {sev.get('warning',0)} warnings, "
              f"{len(d.get('unconnected_items', []))} unrouted, {len(parity)} parity")
        for x in parity[:10]:
            print('   parity:', x['description'], [i['description'] for i in x['items']])
        if parity: ok = False
        types = collections.Counter(x['type'] for x in v if x['severity'] == 'error')
        if types: print('   error types:', dict(types))

    r = run([PY, 'tools/place.py', '--check'])
    print('place.py --check exit', r.returncode, '|', (r.stdout.strip().splitlines() or [''])[-1])

    n, by = parts_and_sheets()
    print(f'parts          {n}  {by}')
    print('pcb            ', pcb_counts())
    r = run([PY, 'tools/depth.py', '--pcb'])
    print('depth          ', [l for l in r.stdout.splitlines() if l.startswith('depth >=')][0])
    print('GATE', 'PASS' if ok else 'FAIL')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
