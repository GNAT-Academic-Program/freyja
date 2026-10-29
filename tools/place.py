#!/usr/bin/env python3
"""Apply tools/placement.py to kicad/odin.kicad_pcb.

Run under KiCad's python (pcbnew required), after load_pcb.py or after a GUI
"Update PCB from Schematic":

    python3 tools/place.py            # apply contract/rules + verify
    python3 tools/place.py --stage    # also restage every connectivity island
    python3 tools/place.py --check    # verify only, move nothing

What it does, in order:

  1. CONTRACT   every footprint in placement.contract() is moved to its
                computed position. These never depend on taste.
  2. ISLANDS    only with explicit --stage: stage connectivity-island tiles.
  3. PSRAM RULE 24 series resistors sit at the FPGA right-hand escape edge.
  4. VERIFY     the extension edges expose one shared 2.54mm hole lattice:
                the left and right signal sockets must present identical pad
                y-sets, the bottom pair identical x-sets, and signal row,
                power row and key post must sit on one 2.54mm grid. Failure
                exits non-zero and the board is not written.

Placement is regenerable: rerun after any netlist change. Hand-move things
only after the design settles, same trade as the schematic README states.
"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
import placement as pl
from design import build

BOARD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     'kicad', 'odin.kicad_pcb')
MM = pcbnew.FromMM

def mm(v): return pcbnew.ToMM(v)

def footprints(board):
    return {fp.GetReference(): fp for fp in board.GetFootprints()}

def set_at(fp, x, y, rot, side='F'):
    if (fp.GetLayer() == pcbnew.B_Cu) != (side == 'B'):
        fp.Flip(fp.GetPosition(), False)
    fp.SetPosition(pcbnew.VECTOR2I(MM(x + pl.ORIGIN_X), MM(y + pl.ORIGIN_Y)))
    fp.SetOrientationDegrees(rot)

def courtyard_wh(fp):
    bb = fp.GetBoundingBox(False)     # no text
    return mm(bb.GetWidth()), mm(bb.GetHeight())

# ------------------------------------------------------------- tier 2
def layout_islands(fps, skip):
    """Stage every connectivity island as its own tight tile in columns to
    the right of the board, in tools/island_classes.py order, matching the ISLxx
    net classes one to one. Each tile is a box-selectable cluster: grab it
    whole, drop it on the board. Hubs not in the contract (U7) and the
    rail-only bulk groups are staged as tiles too. Parts inside a tile stay
    contiguous by schematic group."""
    import island_classes as isl
    rows, parts, local, hubs, loose = isl.compute()
    TILE_W, GAP, X0, Y0, YMAX, COL = 30.0, 4.0, 110.0, 0.0, 100.0, 36.0

    def pack(refs, x0, y0):
        x, y, row_h = x0, y0, 0.0
        for r in refs:
            w, h = courtyard_wh(fps[r])
            w, h = w + 0.5, h + 0.5
            if x - x0 + w > TILE_W and x != x0:
                x, y, row_h = x0, y + row_h + 0.3, 0.0
            set_at(fps[r], x + w / 2, y + h / 2, 0)
            x += w
            row_h = max(row_h, h)
        return y - y0 + row_h

    tiles = [[r] for r in sorted(hubs) if r in fps and r not in skip]
    for members, _ in rows:
        t = [r for r in members if r in fps and r not in skip]
        t.sort(key=lambda r: (parts[r]['group'], r[0] not in 'UQXY', r))
        if t:
            tiles.append(t)
    for g in sorted(loose):
        t = sorted(r for r in loose[g] if r in fps and r not in skip)
        if t:
            tiles.append(t)
    x, y = X0, Y0
    for t in tiles:
        h = pack(t, x, y)
        y += h + GAP
        if y > YMAX:
            x, y = x + COL, Y0
    print(f'{len(tiles)} island tiles staged right of the board')

def place_psram_termination(fps):
    """Place 24 tuning resistors just outside U1's right-hand escape edge.

    Pad 1 faces U1, pad 2 faces the memories. Sort by ball row/column to
    reduce crossings; final escape routing still determines exact placement.
    """
    parts = [p for p in build().parts if p['group'].endswith('series termination')
             and p['group'].startswith('PSRAM')]
    u1 = fps['U1']
    ball_for_net = {p.GetNetname(): p for p in u1.Pads()}
    angle = math.radians(u1.GetOrientationDegrees())
    def local_ball(part):
        v = ball_for_net[part['pins']['1']].GetPosition() - u1.GetPosition()
        x, y = mm(v.x), mm(v.y)
        return (round(x * math.sin(angle) + y * math.cos(angle), 3),
                round(x * math.cos(angle) - y * math.sin(angle), 3))
    for i, part in enumerate(sorted(parts, key=local_ball)):
        f = fps[part['ref']]
        if f.IsFlipped(): f.Flip(f.GetPosition(), False)
        x, y = 15.4, i - (len(parts)-1)/2
        dx, dy = x*math.cos(angle)+y*math.sin(angle), -x*math.sin(angle)+y*math.cos(angle)
        f.SetPosition(u1.GetPosition() + pcbnew.VECTOR2I(MM(dx), MM(dy)))
        f.SetOrientationDegrees(u1.GetOrientationDegrees())
        f.Reference().SetLayer(pcbnew.F_Fab)
        f.Value().SetLayer(pcbnew.F_Fab)
        f.Value().SetVisible(False)

def report_overlaps(fps):
    """Courtyard-collision report over the whole board, so anchor tuning is
    a directed loop, not an eyeball hunt. Pairs entirely outside the board
    area (the unanchored import pile) are skipped as noise."""
    inside = lambda fp: 30.0 <= mm(fp.GetPosition().x) <= 130.0 and \
                        30.0 <= mm(fp.GetPosition().y) <= 130.0
    items = [(r, fp.GetBoundingBox(False)) for r, fp in fps.items()]
    hits = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            (ra, ba), (rb, bb) = items[i], items[j]
            if (inside(fps[ra]) or inside(fps[rb])) and ba.Intersects(bb):
                hits.append((ra, rb))
    if hits:
        print(f'{len(hits)} courtyard overlaps:')
        for ra, rb in sorted(hits):
            pa, pb = fps[ra].GetPosition(), fps[rb].GetPosition()
            print(f'  {ra:6s} ({mm(pa.x):6.1f},{mm(pa.y):6.1f})'
                  f'  x  {rb:6s} ({mm(pb.x):6.1f},{mm(pb.y):6.1f})')
    else:
        print('no courtyard overlaps')
    return hits

# ------------------------------------------------------------- verify
def pad_coords(fp, axis):
    return sorted(round(mm(p.GetPosition()[axis]), 3) for p in fp.Pads())

def contact_coords(fp, axis):
    """Mating-contact positions on the given axis, not solder-pad centroids.

    The SMD header pads splay to +/-2.9 or +/-3.0 off the centreline; the
    contacts a shield actually bridges sit on the centreline rows at +/-1.27.
    On the cross-row axis an SMD header shows exactly two pad values, and
    there we substitute centre +/- 1.27. Along the row, and for every TH
    part, the pads are the contacts."""
    pads = pad_coords(fp, axis)
    if 'HDR-SMD' not in str(fp.GetFPID().GetLibItemName()):
        return pads
    if len(set(pads)) != 2:                      # along the row
        return pads
    c = round(mm(fp.GetPosition()[axis]), 3)     # cross axis: rows at +/-1.27
    half = len(pads) // 2
    return [round(c - 1.27, 3)] * half + [round(c + 1.27, 3)] * half

def lattice_ok(vals, pitch=2.54, tol=0.05):
    base = vals[0]
    return all(abs((v - base) / pitch - round((v - base) / pitch)) * pitch < tol
               for v in vals)

def normalized_signal_pattern(fp):
    """Nets by board-coordinate column/row, with the slot letter removed."""
    import re
    columns = {}
    for pad in fp.Pads():
        y = round(mm(pad.GetPosition().y), 3)
        columns.setdefault(y, []).append((mm(pad.GetPosition().x), pad.GetNetname()))
    return [[re.sub(r'^SLOT[A-H]_', 'SLOT_', net)
             for _x, net in sorted(columns[y])]
            for y in sorted(columns)]

def verify(fps):
    errs = []
    # opposite edges share one y-lattice; bottom buses one x-lattice
    for a, b, axis in (('J5', 'J3', 1), ('J7', 'J8', 0)):
        ca, cb = contact_coords(fps[a], axis), contact_coords(fps[b], axis)
        if a == 'J7':
            # side-by-side pair: same pattern shifted a whole number of pitches
            d = mm(fps[b].GetPosition()[axis]) - mm(fps[a].GetPosition()[axis])
            if abs(d / 2.54 - round(d / 2.54)) * 2.54 > 0.05:
                errs.append(f'{a}/{b}: centres {d:.2f}mm apart, not a 2.54 multiple')
            cb = [round(v - d, 3) for v in cb]
        if [round(v, 2) for v in ca] != [round(v, 2) for v in cb]:
            errs.append(f'{a}/{b}: pad lattices differ; a shield cannot bridge')
    if normalized_signal_pattern(fps['J5']) != normalized_signal_pattern(fps['J3']):
        errs.append('J5/J3: physical signal/net patterns differ or are mirrored')
    # Signal rows, keyed power row, and post use one 2.54 lattice per edge.
    for sig, pwr, key, axis in (('J5', 'J55', 'MK69', 0),
                                ('J3', 'J53', 'MK65', 0),
                                ('J7', 'J57', 'MK76', 1)):
        vals = [contact_coords(fps[sig], axis)[0], contact_coords(fps[pwr], axis)[0],
                contact_coords(fps[key], axis)[0]]
        if not lattice_ok(vals):
            errs.append(f'{sig}/{pwr}/{key}: rows off the 2.54 lattice: {vals}')
    # Every zone uses the same keyed sequence: post at position 1, followed
    # exactly one pitch later by female-header pin 1 (position 2).
    sig_for = {**{s:'J3' for s in 'ABCD'}, **{s:'J5' for s in 'EFGH'},
               'L':'J7', 'M':'J8'}
    for s in 'ABCDEFGHLM':
        key, pwr = fps[f'MK{ord(s)}'], fps[pl.POWER_REFS[s]]
        axis = 0 if s in 'LM' else 1
        cross = 1 - axis
        pin1 = next((p for p in pwr.Pads() if p.GetNumber() == '1'), None)
        if pin1 is None:
            errs.append(f'{pl.POWER_REFS[s]}: missing pin 1'); continue
        along = mm(pin1.GetPosition()[axis]) - mm(key.GetPosition()[axis])
        across = mm(pin1.GetPosition()[cross]) - mm(key.GetPosition()[cross])
        if abs(along - 2.54) > .05 or abs(across) > .05:
            errs.append(f'SLOT {s}: key is not uniform position 1: delta=({along:.2f},{across:.2f})')

        ordered = sorted(pwr.Pads(), key=lambda p: mm(p.GetPosition()[axis]))
        nets = [p.GetNetname() for p in ordered]
        if nets.count('GND') != 3:
            errs.append(f'SLOT {s}: power row has {nets.count("GND")} GND, expected 3')
        for i, net in enumerate(nets):
            if net != 'GND' and not ((i and nets[i-1] == 'GND') or
                                     (i+1 < len(nets) and nets[i+1] == 'GND')):
                errs.append(f'SLOT {s}: rail {net} has no adjacent GND')
        if next(iter(key.Pads())).GetNetname() != 'GND':
            errs.append(f'SLOT {s}: position-1 post is not GND')

        sig = fps[sig_for[s]]
        pads = list(sig.Pads())
        if s in 'ABCDEFGH':
            zone = 'ABCDEFGH'.index(s) % 4
            local = sorted(pads, key=lambda p: mm(p.GetPosition()[axis]))[zone*16:(zone+1)*16]
            ng = sum(p.GetNetname() == 'GND' for p in local)
            if ng != 4:
                errs.append(f'SLOT {s}: signal section has {ng} GND, expected 4')
        else:
            ng = sum(p.GetNetname() == 'GND' for p in pads)
            if ng != 4:
                errs.append(f'SLOT {s}: 5V signal section has {ng} GND, expected 4')
    # report the column convention so extension-ux can state it as fact
    ya = {round(mm(p.GetPosition()[1]), 2): p.GetNumber() for p in fps['J5'].Pads()}
    yb = {round(mm(p.GetPosition()[1]), 2): p.GetNumber() for p in fps['J3'].Pads()}
    shared = sorted(set(ya) & set(yb))
    if shared:
        k = shared[0]
        print(f'column convention: J5 pad {ya[k]} faces J3 pad {yb[k]} at y={k}')
    return errs

def main():
    check_only = '--check' in sys.argv
    stage = '--stage' in sys.argv
    board = pcbnew.LoadBoard(BOARD)
    fps = footprints(board)
    contract = pl.contract()
    contract_refs = {p.ref for p in contract}
    geo_errs = pl.check(contract)
    if geo_errs:
        print('placement.py contract violations:'); [print(' ', e) for e in geo_errs]
        sys.exit(1)
    if not check_only:
        before = {r: (fp.GetPosition().x, fp.GetPosition().y,
                      round(fp.GetOrientationDegrees(), 3), fp.GetLayer())
                  for r, fp in fps.items()}
        absent = [p.ref for p in contract if p.ref not in fps]
        if absent:
            print(f'refs missing from the board (stale board? run load_pcb): {absent}')
            sys.exit(1)
        for p in contract:
            set_at(fps[p.ref], p.x, p.y, p.rot, p.side)
        termination_refs = {p['ref'] for p in build().parts
                            if p['group'].startswith('PSRAM') and p['group'].endswith('series termination')}
        if stage:
            layout_islands(fps, contract_refs | termination_refs)
        place_psram_termination(fps)
        moved = sorted(r for r, fp in fps.items()
                       if before[r] != (fp.GetPosition().x, fp.GetPosition().y,
                                        round(fp.GetOrientationDegrees(), 3), fp.GetLayer()))
        allowed = contract_refs | termination_refs
        unexpected = sorted(set(moved) - allowed)
        print('moved refs: ' + (', '.join(moved) if moved else 'none'))
        if unexpected and not stage:
            print('UNEXPECTED MOVES, board not written: ' + ', '.join(unexpected))
            sys.exit(1)
    errs = verify(fps)
    if errs:
        print('VERIFY FAILED, board not written:'); [print(' ', e) for e in errs]
        sys.exit(1)
    report_overlaps(fps)   # informational: overlaps do not block the write
    if not check_only:
        board.Save(BOARD)
        print(f'wrote {BOARD}: {len(contract)} contract, groups anchored')
    else:
        print('verify: clean')

if __name__ == '__main__':
    main()
