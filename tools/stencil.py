#!/usr/bin/env python3
"""Silkscreen labels for the LED dashboard (owner, 2026-10-29: the LEDs
read as one dashboard, each telling something clear on the board stencil).

    python3 tools/stencil.py            # dry run: where each label goes
    python3 tools/stencil.py --apply    # write the labels into the pcb

Each label is a user text inside the LED's own footprint (F.SilkS, 0.8 mm,
0.15 mm stroke: JLCPCB's silkscreen minimum), so it moves and turns with the
LED whatever tool moves it next. It sits 0.9 mm under the island's parts
(one baseline for the dashboard), centred on the LED, horizontal whatever
the LED's rotation. Rerunning
replaces the labels it wrote before (any F.SilkS user text in these four
footprints), nothing else: no footprint moves (check_positions.py --compare
reports 0 moved refs across a run).

Label texts: the "Board label" column of ref/status-leds.md for the three
controller LEDs; the DONE LED is "DONE" (the 5 mm cell pitch of the dashboard
holds about six characters at 0.8 mm).
"""
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import islands as I  # noqa: E402

LABELS = {'D1': 'DONE', 'D9': 'CTRL HB', 'D10': 'USER 1', 'D11': 'USER 2'}
SIZE, STROKE, DROP = 0.8, 0.15, 0.9


def main():
    import argparse
    ap = argparse.ArgumentParser(description='Write the LED dashboard silkscreen labels.')
    ap.add_argument('--apply', action='store_true', help='write the pcb (default: dry run)')
    ap.add_argument('--board', default=I.BOARD)
    args = ap.parse_args()
    board = I.Board(args.board)
    groups = board.island_groups()
    edits = []
    for ref, words in LABELS.items():
        fp = board.fps.get(ref)
        if not fp:
            print(f'  {ref}: not on the board; skipped')
            continue
        label = groups.get(ref)
        refs = [r for r, l in groups.items() if l == label] if label else [ref]
        bb = I.bbox_of([p for r in refs for p in board.fps[r].polygon()])
        # one baseline for the whole dashboard: under the island's parts (the
        # cells of a merged dashboard share one group), centred on the LED
        cell = [r for r in refs if abs(board.fps[r].x - fp.x) <= 2.5]
        ty = bb[3] + DROP
        lx, ly = I.rot(0.0, ty - fp.y, -fp.rot)
        # drop the labels written before (user texts on F.SilkS in this footprint)
        for t in fp.node.findall('fp_text'):
            at = t.atoms()
            lay = t.find('layer')
            if len(at) > 2 and at[1].value == 'user' and lay and lay.atoms()[1].value == 'F.SilkS':
                st = t.start
                while st > 0 and board.text[st - 1] in ' \t':
                    st -= 1
                if st > 0 and board.text[st - 1] == '\n':
                    st -= 1
                edits.append((st, t.end, ''))
        first_pad = fp.node.find('pad')
        body = (f'\t\t(fp_text user "{words}"\n\t\t\t(at {I.fmt(round(lx, 3))} {I.fmt(round(ly, 3))} 0)\n'
                f'\t\t\t(layer "F.SilkS")\n\t\t\t(uuid "{uuid.uuid4()}")\n'
                f'\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size {SIZE} {SIZE})\n\t\t\t\t\t(thickness {STROKE})\n'
                f'\t\t\t\t)\n\t\t\t)\n\t\t)\n')
        st = first_pad.start
        while st > 0 and board.text[st - 1] in ' \t':
            st -= 1
        edits.append((st, st, body))
        print(f'  {ref:4} "{words}" at board ({fp.x:.2f}, {ty:.2f}), local ({lx:.3f}, {ly:.3f}), '
              f'cell parts {", ".join(sorted(cell, key=I.natural))}, island box bottom {bb[3]:.2f}')
    if not args.apply:
        print('dry run: nothing written. Add --apply to write the pcb.')
        return
    text = I.apply_edits(board.text, edits)
    open(args.board, 'w', encoding='utf-8').write(text)
    check = I.Board(args.board)
    moved = [r for r, fp in check.fps.items()
             if abs(fp.x - board.fps[r].x) > 1e-6 or abs(fp.y - board.fps[r].y) > 1e-6 or fp.rot != board.fps[r].rot]
    if moved or len(check.fps) != len(board.fps):
        open(args.board, 'w', encoding='utf-8').write(board.text)
        sys.exit(f'WRITE VERIFICATION FAILED ({len(moved)} moved); the original file was restored')
    print(f'wrote {os.path.relpath(args.board, I.ROOT)}: {len(LABELS)} labels, 0 footprints moved')


if __name__ == '__main__':
    main()
