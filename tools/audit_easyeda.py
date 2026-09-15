#!/usr/bin/env python3
"""Fail if a selected EasyEDA/LCSC part drifts from the textual design.

Checks the actual generated design, not the checklist: LCSC identity, selected
footprint, symbol pin numbers, footprint pad numbers, and connected pad names.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from design import build

LIB = 'easyeda/EasyEDA.kicad_sym'
PRETTY = 'easyeda/EasyEDA.pretty'

def sexpr_block(text, start):
    depth = 0
    for pos in range(start, len(text)):
        depth += (text[pos] == '(') - (text[pos] == ')')
        if depth == 0:
            return text[start:pos + 1]
    raise ValueError('unterminated s-expression')

def imported():
    text = open(LIB, encoding='utf-8').read(); out = {}
    for m in re.finditer(r'^  \(symbol "([^"]+)"', text, re.M):
        block = sexpr_block(text, m.start() + 2)
        prop = {x.group(1): x.group(2) for x in re.finditer(
            r'\(property\s+"([^"]+)"\s+"([^"]*)"', block, re.S)}
        lcsc = prop.get('LCSC Part')
        if lcsc:
            out[lcsc] = dict(name=m.group(1), mpn=prop.get('MPN', ''),
                             fp=prop.get('Footprint', ''),
                             pins=set(re.findall(r'\(number "([^"]+)"', block)))
    return out

def pads(fp):
    path = os.path.join(PRETTY, fp.split(':', 1)[1] + '.kicad_mod')
    text = open(path, encoding='utf-8').read()
    nums = set(re.findall(r'^\s*\(pad "?([^"\s]+)"?', text, re.M))
    props = {x.group(1): x.group(2) for x in re.finditer(
        r'\(property\s+"([^"]+)"\s+"([^"]*)"', text, re.S)}
    return path, nums, props

def main():
    imp = imported(); failures = []; checked = 0
    for part in build().parts:
        if not part['fp'].startswith('EasyEDA:'): continue
        checked += 1
        path, padnums, fprop = pads(part['fp'])
        used = set(part['pins'])
        if not used <= padnums:
            failures.append(f"{part['ref']}: connected symbol pins absent from footprint: {sorted(used-padnums)}")
        if part['lcsc']:
            if fprop.get('LCSC Part') not in (None, part['lcsc']):
                failures.append(f"{part['ref']}: footprint says {fprop.get('LCSC Part')}, design says {part['lcsc']}")
            sym = imp.get(part['lcsc'])
            if not sym:
                failures.append(f"{part['ref']}: no imported symbol for {part['lcsc']}")
            else:
                if sym['fp'] != part['fp']:
                    failures.append(f"{part['ref']}: imported symbol selects {sym['fp']}, design selects {part['fp']}")
                if sym['pins'] != padnums:
                    failures.append(f"{part['ref']}: imported symbol pins and footprint pads differ")
                if not used <= sym['pins']:
                    failures.append(f"{part['ref']}: design uses pins absent from imported symbol")
    if failures:
        raise SystemExit('EasyEDA audit FAILED:\n  ' + '\n  '.join(failures))
    print(f'EasyEDA audit passed: {checked} fitted instances; symbol pins, footprint pads and LCSC identities agree')

if __name__ == '__main__': main()
