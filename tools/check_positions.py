#!/usr/bin/env python3
"""Snapshot/compare the hand-placed PCB. Never writes a PCB or runs placement."""
import argparse
import json
from pathlib import Path
import pcbnew


def positions():
    board = pcbnew.LoadBoard('kicad/odin.kicad_pcb')
    return {f.GetReference(): dict(x_nm=f.GetPosition().x, y_nm=f.GetPosition().y,
            rot_deg=f.GetOrientationDegrees(), layer=board.GetLayerName(f.GetLayer()))
            for f in board.GetFootprints()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path)
    parser.add_argument('--compare', type=Path)
    args = parser.parse_args()
    now = positions()
    if args.snapshot:
        # Never silently overwrite the authoritative opening snapshot.
        mode = 'w' if args.snapshot.name == 'pos_after.json' else 'x'
        with args.snapshot.open(mode) as stream:
            json.dump(now, stream, indent=2, sort_keys=True)
        print(f'Snapshot: {len(now)} footprints -> {args.snapshot}')
    if args.compare:
        before = json.loads(args.compare.read_text())
        common = before.keys() & now.keys()
        moved = sorted(r for r in common if before[r] != now[r])
        print(f'{len(moved)} moved — {len(common)} common refs; x/y/rotation/side compared')
        print('Added:', ', '.join(sorted(now.keys() - before.keys())) or '(none)')
        print('Removed:', ', '.join(sorted(before.keys() - now.keys())) or '(none)')
        if moved:
            for r in moved:
                print(r, before[r], '->', now[r])
            raise SystemExit(1)


if __name__ == '__main__':
    main()
