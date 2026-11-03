#!/usr/bin/env python3
"""Put the two 2x16 halves of a former 2x32 signal body on its exact pads.

    python3 tools/split_strip.py --before OLD.kicad_pcb            # report
    python3 tools/split_strip.py --before OLD.kicad_pcb --apply    # write

The JLCPCB library has no 2x32 female header, so each edge body is two
2x16 bodies end to end (design.py, 2026-10-30): J3A/J3B on the left edge
(slots A-B / C-D), J5A/J5B on the right (E-F / G-H). load_pcb.py stages the
new references in the band below the board; this script moves each half so
that its 32 pads land exactly on the 32 pads the old body had there, with
the old body's rotation, and refuses to write unless all 64 centres agree
to 1 um. Nothing else is touched. The old pads are read from the board as
it was before the netlist reload (--before, e.g. `git show HEAD:...`).

Mapping, from design.py: J3A pad n = old J3 pad n, J3B pad n = old J3 pad
n+32 (A,B on the pad-1 end, C,D beyond); J5A pad n = old J5 pad n+32,
J5B pad n = old J5 pad n (E,F are at the far end of the old J5 numbering).
"""
import argparse, sys
import pcbnew

BOARD = 'kicad/odin.kicad_pcb'
HALVES = {'J3A': ('J3', 0), 'J3B': ('J3', 32), 'J5A': ('J5', 32), 'J5B': ('J5', 0)}


def pads(fp):
    return {p.GetNumber(): p.GetPosition() for p in fp.Pads()}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--before', required=True, help='board file holding the old 2x32 bodies J3 and J5')
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()
    old = pcbnew.LoadBoard(args.before)
    oldfp = {f.GetReference(): f for f in old.GetFootprints()}
    board = pcbnew.LoadBoard(BOARD)
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    ok = True
    for half, (whole, offset) in HALVES.items():
        if half not in fps or whole not in oldfp:
            sys.exit(f'{half} on the board and {whole} in --before are both needed')
        src, dst = oldfp[whole], fps[half]
        want = {str(n): pads(src)[str(n + offset)] for n in range(1, 33)}
        dst.SetOrientation(src.GetOrientation())
        if dst.IsFlipped() != src.IsFlipped():
            dst.Flip(dst.GetPosition(), False)
        have = pads(dst)
        dst.SetPosition(dst.GetPosition() + (want['1'] - have['1']))
        have = pads(dst)
        worst = max(max(abs(have[n].x - want[n].x), abs(have[n].y - want[n].y)) for n in want)
        p = dst.GetPosition()
        print(f'{half}: from {whole} pads {1 + offset}..{32 + offset}; at ({pcbnew.ToMM(p.x):.3f}, '
              f'{pcbnew.ToMM(p.y):.3f}) rot {dst.GetOrientationDegrees():g}; '
              f'worst pad offset {worst / 1000:.3f} um')
        if worst > 1000: ok = False
    if not ok:
        sys.exit('pads do not coincide; not written')
    if args.apply:
        pcbnew.SaveBoard(BOARD, board)
        print(f'wrote {BOARD}')
    else:
        print('dry run; --apply to write')


if __name__ == '__main__':
    main()
