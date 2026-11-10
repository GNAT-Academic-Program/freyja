#!/usr/bin/env python3
"""Check the stackup pcbnew really holds against the selected JLC template.

    python3 tools/check_stackup.py [board]

Read-only for the board: pcbnew loads it and saves a copy to a temporary
directory, and the copy's stackup is compared, sublayer by sublayer, with
ref/jlc08161h-1080a-stackup.json. The Python bindings do not expose the stackup,
and reading the board file alone would miss text that KiCad accepts and then
drops. The generator's own block must say the same. Exit 1 on any difference.
"""
import json
import os
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from gen_pcb import SETUP, OUT, sexpr_block

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / 'ref' / 'jlc08161h-1080a-stackup.json'
FIELDS = ('thickness', 'material', 'epsilon_r', 'loss_tangent')
FINE_LAYERS = ('F.Cu', 'In2.Cu', 'In5.Cu', 'B.Cu')    # the signal layers that carry U1's ball-field routing


def parse(text):
    """Nested lists from one s-expression; a bare word stays a string."""
    stack = [[]]
    for tok in re.findall(r'"(?:[^"\\]|\\.)*"|[()]|[^\s()"]+', text):
        if tok == '(':
            stack.append([])
        elif tok == ')':
            done = stack.pop()
            stack[-1].append(done)
        else:
            stack[-1].append(tok.strip('"'))
    return stack[0][0]


def stackup(text):
    """[(layer, type, [sublayer dict, ...]), ...] from a text holding a stackup block."""
    a, b = sexpr_block(text, '(stackup')
    layers = []
    for entry in parse(text[a:b])[1:]:
        if not isinstance(entry, list) or entry[0] != 'layer':
            continue
        kind, subs = None, [{}]
        for item in entry[2:]:
            if item == 'addsublayer':
                subs.append({})
            elif not isinstance(item, list):
                raise ValueError(f'{entry[1]}: unexpected word {item}')
            elif item[0] == 'type':
                kind = item[1]
            elif item[0] in FIELDS:
                subs[-1][item[0]] = float(item[1]) if item[0] != 'material' else item[1]
            else:
                raise ValueError(f'{entry[1]}: unexpected item {item[0]}, a sublayer written in parentheses?')
        layers.append((entry[1], kind, subs))
    return layers


def template():
    """The JLC template as the same structure, adjoining dielectrics forming one section."""
    want = []
    for layer in json.loads(TEMPLATE.read_text())['layers']:
        if layer['Type'] == 'Copper':
            want.append(('copper', [{'thickness': layer['Thickness']}]))
            continue
        m = layer['Material']
        material = f"{m['Model']} core" if m['IsCore'] else f"{m['Model']} {m['Construction']} RC{m['ResinContent']}%"
        sub = dict(thickness=layer['Thickness'], material=material,
                   epsilon_r=m['DielectricConstant'], loss_tangent=m['LossTangent'])
        kind = 'core' if m['IsCore'] else 'prepreg'
        if want[-1][0] == kind:
            want[-1][1].append(sub)
        else:
            want.append((kind, [sub]))
    return want


def compare(name, layers, want, problems):
    """Copper and dielectric sections only: the template holds no solder mask."""
    have = [l for l in layers if l[1] in ('copper', 'core', 'prepreg')]
    if [(k, s) for _, k, s in have] != want:
        problems.append(f'{name} differs from {TEMPLATE.name}')
        for (n, k, s), (wk, ws) in zip(have, want):
            if (k, s) != (wk, ws):
                problems.append(f'  {n}: {k} {s}, template {wk} {ws}')
    return have


def elevations(have):
    """Copper mid-plane depths from F.Cu's mid-plane: KiCad's layer distance."""
    depth, out, half = 0., {}, None
    for name, kind, subs in have:
        t = sum(s['thickness'] for s in subs)
        if kind == 'copper':
            depth += t / 2 if half is not None else 0
            out[name] = depth
            depth += t / 2
            half = True
        else:
            depth += t
    return out


def main():
    board = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / OUT).resolve()
    import pcbnew
    with tempfile.TemporaryDirectory() as tmp:
        copy = os.path.join(tmp, 'roundtrip.kicad_pcb')
        pcbnew.SaveBoard(copy, pcbnew.LoadBoard(str(board)))
        saved = stackup(open(copy, encoding='utf-8').read())
    problems = []
    want = template()
    have = compare('board after a pcbnew load and save', saved, want, problems)
    compare('tools/gen_pcb.py SETUP', stackup(SETUP), want, problems)
    # Ball-field fine routing (0.09 mm tracks, 0.0889 mm inside U1_BALL_FIELD) is etched on the four signal
    # layers; none of them may be specified as 2 oz (0.070 mm) copper. All four are 1 oz or lighter.
    for name, kind, subs in have:
        if kind == 'copper' and name in FINE_LAYERS and sum(x['thickness'] for x in subs) >= .070 - 1e-6:
            problems.append(f'{name}: {sum(x["thickness"] for x in subs):.4f} mm copper (2 oz) on a ball-field routing layer')
    fine = ', '.join(f'{n} {sum(x["thickness"] for x in subs):.4f}' for n, k, subs in have if k == 'copper' and n in FINE_LAYERS)
    print(f'ball-field routing layers, copper mm: {fine}')
    copper = sum(s['thickness'] for _, k, subs in have if k == 'copper' for s in subs)
    dielectric = sum(s['thickness'] for _, k, subs in have if k != 'copper' for s in subs)
    mask = sum(s.get('thickness', 0) for _, k, subs in saved if 'Mask' in k for s in subs)
    for p in problems:
        print(p)
    print(f'copper {copper:.4f} + dielectric {dielectric:.4f} = {copper + dielectric:.4f} mm, mask {mask:.4f} mm apart; '
          f'F.Cu to B.Cu {elevations(have)["B.Cu"]:.4f} mm; ' + ('FAIL' if problems else 'matches the template'))
    sys.stdout.flush()
    os._exit(1 if problems else 0)     # pcbnew can crash tearing down at exit


if __name__ == '__main__':
    main()
