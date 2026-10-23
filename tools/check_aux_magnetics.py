#!/usr/bin/env python3
"""Read-only checks of the drawing-derived C54563336 library assets."""
from pathlib import Path
import sys

import pcbnew

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import symlib


def main():
    fp = pcbnew.FootprintLoad(str(ROOT / 'kicad/odin.pretty'), 'L_PROD_PSSCAQ1285')
    assert fp is not None, 'C54563336 footprint could not be loaded'
    pads = {p.GetNumber(): p for p in fp.Pads()}
    expected = {'1': (-1.75, -4.975), '2': (1.75, -4.975),
                '3': (1.75, 4.975), '4': (-1.75, 4.975)}
    assert set(pads) == set(expected), 'Expected exactly four separate lands'
    for num, (x, y) in expected.items():
        p = pads[num]
        assert (p.GetPosition().x, p.GetPosition().y) == (
            pcbnew.FromMM(x), pcbnew.FromMM(y)), f'Pad {num}: incorrect centre'
        assert (p.GetSize().x, p.GetSize().y) == (
            pcbnew.FromMM(2.5), pcbnew.FromMM(3.85)), f'Pad {num}: incorrect size'
        assert p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD, f'Pad {num}: not SMD'
    sym = symlib.get('odin:PSSCAQ1285_4R7MP')
    actual = {name: {n for n, _ in nums} for name, nums in sym['pins'].items()}
    assert actual == {'PRI_DOT': {'1'}, 'PRI': {'3'},
                      'SEC_DOT': {'2'}, 'SEC': {'4'}}, actual
    print('C54563336 PASS: four 2.50x3.85 mm lands; 3.50x9.95 mm centre pitches; '
          'windings 1-3/2-4; dots 1/2')


if __name__ == '__main__':
    main()
