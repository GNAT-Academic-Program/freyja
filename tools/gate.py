#!/usr/bin/env python3
"""Run every rev A phase gate and print the numbers for ref/rev-a-report.md.

    python3 tools/gate.py

Read-only. Runs, in order: design.py / budget.py / qualified.py build checks,
check_erc.py, netlist export to a scratch file compared with kicad/odin.net,
ref/freya.xdc compared with a fresh gen_xdc export, DRC with schematic
parity, place.py --check, depth.py.

Two verdicts, printed separately so neither hides the other:
  GATE electrical  - build, ERC, netlist/XDC/guide drift, schematic parity
  GATE mechanical  - place.py --check (the connector lattice contract)
The exit code is 1 if the electrical gate fails; with --strict also if the
mechanical one does. DRC violations and unrouted counts are reported, not
gated: the board is not routed yet.
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

        # ref/freya.xdc and the gate top must be the current export of alloc.py
        r = run([PY, '-c', 'import sys; sys.path.insert(0, "tools"); import gen_xdc; '
                 'rs = gen_xdc.rows(); print(gen_xdc.xdc(rs)); print("@@@"); print(gen_xdc.verilog(rs))'])
        if r.returncode: ok = False; print('gen_xdc failed', r.stderr[-500:])
        else:
            want_xdc, want_v = r.stdout.split('@@@\n')
            have_xdc = open('ref/freya.xdc').read(); have_v = open('gateware/gate/top.v').read()
            if want_xdc.strip() != have_xdc.strip() or want_v.strip() != have_v.strip():
                ok = False; print('XDC DRIFT: ref/freya.xdc or gateware/gate/top.v is not the export of tools/alloc.py')
            else: print('xdc            matches ref/freya.xdc and gateware/gate/top.v')

        # every covered part explained, and ref/parts-guide.md current
        r = run([PY, '-c', 'import sys, io, contextlib; sys.path.insert(0, "tools"); '
                 'import roles; from design import build\n'
                 'with contextlib.redirect_stdout(io.StringIO()): parts = roles.annotate(build().parts)\n'
                 'probs, gaps = roles.check(parts)\n'
                 'print(len(probs), len(gaps), sum(1 for p in parts if p["role"]), len(parts))\n'
                 'print("@@@" + roles.guide(parts))'])
        head, guide_text = r.stdout.split('@@@', 1)
        nprob, ngap, ndone, ntot = map(int, head.split())
        drift = guide_text.strip() != open('ref/parts-guide.md').read().strip()
        print(f'roles          {ndone}/{ntot} parts described, {nprob} problems, {ngap} gaps on uncovered sheets'
              + ('; GUIDE DRIFT: run tools/roles.py --write' if drift else ''))
        if nprob or drift: ok = False

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
    mech_ok = r.returncode == 0
    mech_lines = [l for l in r.stdout.strip().splitlines() if l.strip()]
    print('place.py --check exit', r.returncode, '|', (mech_lines or [''])[-1])

    n, by = parts_and_sheets()
    print(f'parts          {n}  {by}')
    print('pcb            ', pcb_counts())
    r = run([PY, 'tools/depth.py', '--pcb'])
    print('depth          ', [l for l in r.stdout.splitlines() if l.startswith('depth >=')][0])
    print('GATE electrical', 'PASS' if ok else 'FAIL')
    print('GATE mechanical', 'PASS' if mech_ok else
          f'FAIL ({len([l for l in mech_lines if l.startswith("  ")])} lattice findings; '
          'placement in progress, see ref/rev-a-report.md)')
    strict = '--strict' in sys.argv
    sys.exit(0 if ok and (mech_ok or not strict) else 1)


if __name__ == '__main__':
    main()
