#!/usr/bin/env python3
"""Read symbols out of any KiCad symbol library: pin name->numbers, units, and the
raw s-expression block so it can be embedded in a generated schematic."""
import os, re, glob
SYSDIRS = ['/usr/share/kicad/symbols', '/usr/local/share/kicad/symbols']

def libpath(lib):
    if os.path.exists(f'kicad/{lib}.kicad_sym'): return f'kicad/{lib}.kicad_sym'
    for d in SYSDIRS:
        p = os.path.join(d, f'{lib}.kicad_sym')
        if os.path.exists(p): return p
    raise FileNotFoundError(lib)

def _block(text, name):
    key = f'(symbol "{name}"'
    i = text.index(key)
    d, j = 1, i + len(key)
    while d > 0:
        if text[j] == '(': d += 1
        elif text[j] == ')': d -= 1
        j += 1
    return text[i:j]

def get(lib_id):
    lib, name = lib_id.split(':', 1)
    text = open(libpath(lib)).read()
    blk = _block(text, name)
    ext = re.search(r'\(extends "([^"]+)"\)', blk)
    base = _block(text, ext.group(1)) if ext else blk
    pins = {}                       # name -> [numbers]
    units = set()
    for m in re.finditer(r'\(symbol "[^"]*_(\d+)_(\d+)"(.*?)(?=\n\t\t\(symbol "|\Z)', base, re.S):
        u = int(m.group(1)); units.add(u)
        for pm in re.finditer(r'\(pin \w+ line.*?\(name "([^"]*)".*?\(number "([^"]*)"', m.group(3), re.S):
            pins.setdefault(pm.group(1), []).append((pm.group(2), u))
    return {'name': name, 'lib': lib, 'block': blk, 'base': base,
            'pins': pins, 'units': sorted(u for u in units if u > 0) or [1]}

if __name__ == '__main__':
    import sys
    for lid in sys.argv[1:]:
        s = get(lid)
        print(f"=== {lid}  units={s['units']}")
        for n, v in sorted(s['pins'].items()):
            print(f"    {n:22s} {','.join(f'{num}(u{u})' for num,u in v)}")
