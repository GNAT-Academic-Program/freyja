#!/usr/bin/env python3
"""Apply tools/placement.py to kicad/odin.kicad_pcb.

Run under KiCad's python (pcbnew required), after load_pcb.py or after a GUI
"Update PCB from Schematic":

    python3 tools/place.py            # apply + verify
    python3 tools/place.py --check    # verify only, move nothing

What it does, in order:

  1. CONTRACT   every footprint in placement.contract() is moved to its
                computed position. These never depend on taste.
  2. ANCHORS    every other footprint is laid out on a compact grid growing
                from its schematic group's anchor (placement.ANCHORS).
                Groups come from tools/design.py, the same source that
                generated the netlist, so membership cannot drift.
  3. PSRAM RULE 24 series resistors sit at the FPGA right-hand escape edge.
  4. DECAP RULE the FPGA's per-ball 100nF decoupling flips to B.Cu and lands
                mirrored under its supply ball.
  5. VERIFY     the extension edges expose one shared 2.54mm hole lattice:
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
def layout_groups(board, fps, contract_refs):
    """Grid-pack each schematic group around its anchor."""
    d = build()
    groups = {}
    for part in d.parts:
        groups.setdefault(part['group'], []).append(part['ref'])
    missing_anchor = []
    for gname, refs in sorted(groups.items()):
        refs = [r for r in refs if r in fps and r not in contract_refs]
        if not refs:
            continue
        if gname not in pl.ANCHORS:
            missing_anchor.append(gname)
            continue
        ax, ay, direction = pl.ANCHORS[gname]
        # ICs first (they anchor the group visually), then passives by ref
        refs.sort(key=lambda r: (0 if r[0] in 'UQXY' else 1, r))
        x, y, row_h, x0 = ax, ay, 0.0, ax
        sx = -1 if direction == 'left' else 1
        sy = -1 if direction == 'up' else 1
        for r in refs:
            w, h = courtyard_wh(fps[r])
            w, h = w + 0.5, h + 0.5                     # courtyard + air
            if abs(x - x0) + w > 12.0 and x != x0:      # wrap a 12mm-wide row
                x, y = x0, y + sy * (row_h + 0.3); row_h = 0.0
            set_at(fps[r], x + sx * w / 2, y + sy * h / 2, 0)
            x += sx * w
            row_h = max(row_h, h)
    if missing_anchor:
        print('groups without an anchor (left where they are):')
        for g in missing_anchor:
            print('  ', g)

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

# ------------------------------------------------------------- tier 3
def mirror_decaps(board, fps):
    """Each 'decoupling <rail>' 100nF flips to B.Cu under a supply ball of
    that rail. Balls are consumed nearest-first so caps spread out."""
    d = build()
    u1 = fps['U1']
    rails = {}
    for part in d.parts:
        g = part['group']
        if g.startswith('decoupling ') and part['ref'].startswith('C'):
            rails.setdefault(g.split(' ', 1)[1], []).append(part['ref'])
    for rail, caps in rails.items():
        balls = [p for p in u1.Pads() if p.GetNetname() == rail]
        if not balls:
            print(f'decap rule: no U1 balls on {rail}?'); continue
        balls.sort(key=lambda p: (p.GetPosition().x, p.GetPosition().y))
        for cap, ball in zip(sorted(caps), balls):
            if cap not in fps: continue
            fp = fps[cap]
            if fp.GetLayer() != pcbnew.B_Cu:
                fp.Flip(fp.GetPosition(), False)
            fp.SetPosition(ball.GetPosition())
            fp.SetOrientationDegrees(0)
        if len(caps) > len(balls):
            print(f'decap rule: {rail}: {len(caps)} caps for {len(balls)} balls')

# ------------------------------------------------------------- verify
def pad_coords(fp, axis):
    return sorted(round(mm(p.GetPosition()[axis]), 3) for p in fp.Pads())

def lattice_ok(vals, pitch=2.54, tol=0.05):
    base = vals[0]
    return all(abs((v - base) / pitch - round((v - base) / pitch)) * pitch < tol
               for v in vals)

def verify_sfp(fps):
    """Check mechanical datums using actual KiCad pads, not bounding boxes."""
    errs = []
    for sh, j in (('SH1', 'J60'), ('SH2', 'J61')):
        if sh not in fps or j not in fps:
            errs.append(f'{sh}/{j}: missing SFP assembly'); continue
        cage, conn = fps[sh], fps[j]
        pegs = [p for p in conn.Pads() if not p.GetNumber()]
        pads = {p.GetNumber(): p for p in conn.Pads() if p.GetNumber()}
        cx, cy = mm(cage.GetPosition().x), mm(cage.GetPosition().y)
        if len(pegs) != 2 or any(
                abs(mm(p.GetPosition().y) - cy - pl.CONNECTOR_DEPTH) > .001 or
                p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH or
                abs(mm(p.GetDrillSize().x) - 1.55) > .001 for p in pegs):
            errs.append(f'{sh}/{j}: connector peg depth or NPTH geometry wrong')
        if sorted(round(mm(p.GetPosition().x) - cx, 2) for p in pegs) != [-4.8, 4.8]:
            errs.append(f'{sh}/{j}: connector peg transverse alignment wrong')
        for n in range(1, 21):
            depth = pl.CONNECTOR_DEPTH + (-4.1 if n <= 10 else 4.1)
            if str(n) not in pads or abs(mm(pads[str(n)].GetPosition().y) - cy - depth) > .001:
                errs.append(f'{sh}/{j}: contact {n} faces the wrong direction')
        if len(list(cage.Pads())) != 20 or any(p.GetNetname() != 'GND' for p in cage.Pads()):
            errs.append(f'{sh}: expected twenty grounded shield tails')
    return errs

def verify(fps):
    errs = verify_sfp(fps)
    # opposite edges share one y-lattice; bottom buses one x-lattice
    for a, b, axis in (('J5', 'J3', 1), ('J6', 'J4', 1), ('J7', 'J8', 0)):
        ca, cb = pad_coords(fps[a], axis), pad_coords(fps[b], axis)
        if [round(v, 2) for v in ca] != [round(v, 2) for v in cb]:
            errs.append(f'{a}/{b}: pad lattices differ; a shield cannot bridge')
    # signal row + power row + key post on one 2.54 grid, per edge
    for sig, pwr, key, axis in (('J5', 'J55', 'MK69', 0), ('J3', 'J53', 'MK65', 0),
                                ('J7', 'J57', 'MK76', 1)):
        vals = [pad_coords(fps[sig], axis)[0], pad_coords(fps[pwr], axis)[0],
                pad_coords(fps[key], axis)[0]]
        if not lattice_ok(vals):
            errs.append(f'{sig}/{pwr}/{key}: rows off the 2.54 lattice: {vals}')
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
    board = pcbnew.LoadBoard(BOARD)
    fps = footprints(board)
    contract = pl.contract()
    contract_refs = {p.ref for p in contract}
    geo_errs = pl.check(contract)
    if geo_errs:
        print('placement.py contract violations:'); [print(' ', e) for e in geo_errs]
        sys.exit(1)
    if not check_only:
        absent = [p.ref for p in contract if p.ref not in fps]
        if absent:
            print(f'refs missing from the board (stale board? run load_pcb): {absent}')
            sys.exit(1)
        for p in contract:
            set_at(fps[p.ref], p.x, p.y, p.rot, p.side)
        termination_refs = {p['ref'] for p in build().parts
                            if p['group'].startswith('PSRAM') and p['group'].endswith('series termination')}
        layout_groups(board, fps, contract_refs | termination_refs)
        place_psram_termination(fps)
        mirror_decaps(board, fps)
    errs = verify(fps)
    if errs:
        print('VERIFY FAILED, board not written:'); [print(' ', e) for e in errs]
        sys.exit(1)
    if not check_only:
        board.Save(BOARD)
        print(f'wrote {BOARD}: {len(contract)} contract, groups anchored, decaps mirrored')
    else:
        print('verify: clean')

if __name__ == '__main__':
    main()
