#!/usr/bin/env python3
"""The Odin placement contract, as data.

Pure geometry: no pcbnew, no KiCad. Every position here is in BOARD-LOCAL
millimetres, origin at the top-left board corner, x rightward, y downward,
board 100 x 100 (gen_pcb.py puts that corner at absolute (30, 30)).
tools/place.py converts and applies; this module only decides and checks.

Three tiers, in order of authority:

  1. CONTRACT      the mechanical promises extensions rely on: slot bodies,
                   power rows, key posts, cages, USB, BGA. Computed, asserted.
  2. ANCHORS       one coordinate per schematic group (regulators, memories,
                   supervisor...). Members are laid out by place.py relative
                   to these. Tune freely; the contract does not move.
  3. RULES         parametric placement (PSRAM series resistors at the FPGA
                   escape edge). Implemented in place.py where pad data exists.
                   The board is assembled on one side: nothing goes on B.Cu.

Run standalone to print the table and check courtyard collisions:
    python3 tools/placement.py
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))

BOARD_W, BOARD_H = 100.0, 100.0
ORIGIN_X, ORIGIN_Y = 30.0, 30.0          # must match tools/gen_pcb.py X0, Y0

# ---------------------------------------------------------------- helpers
def grid(v, pitch=0.01):
    return round(round(v / pitch) * pitch, 3)

class P:
    """One placed footprint: board-local origin, rotation, side."""
    def __init__(self, ref, x, y, rot=0, side='F', why=''):
        self.ref, self.x, self.y = ref, grid(x), grid(y)
        self.rot, self.side, self.why = rot % 360, side, why
    def abs_at(self):
        return (round(self.x + ORIGIN_X, 3), round(self.y + ORIGIN_Y, 3), self.rot)
    def __repr__(self):
        return f"{self.ref:5s} ({self.x:6.2f},{self.y:6.2f}) r{self.rot:<3d} {self.side}  {self.why}"

# ------------------------------------------------------ the numbers that rule
# 2x32 signal socket body (courtyard): 81.90 x 4.90, pads centred on origin.
# Per-zone keyed power row: one post plus a 1x7 female body.
# RJ45 jacks on the top edge: HR911130A 16.04 x 21.30, KH-RJ45-58 15.70 x 18.20.
# FBGA-676:                            27.4 x 27.7 courtyard.
SIG_LEN   = 81.90       # 2x32 body length
SIG_W     = 4.90
PWR_W     = 2.54
# THE LATTICE. A shield bridges signal rows, power row and key post, so all
# of them must sit on one 2.54mm grid RELATIVE to each other. The absolute
# inset from the board edge is free; the relative spacings are the contract.
EDGE_SIG  = 4.70                     # signal 2x32 centreline; rows at +/-1.27
EDGE_PWR  = EDGE_SIG + 1.27 + 3 * 2.54   # 13.59: inner sig row + 3 pitches
BODY_CTR  = 50.0                    # one continuous body per left/right edge

# Slot letters per edge. Package geometry decides this, not taste: bank 34
# balls (E-H) live on package columns 1..8 (left half of U1), banks 15/13/14
# (A-D, bus M, PSRAM, flash) on columns 14..26 (right half). Crossing the die
# with 96 escapes would be self-sabotage.
LEFT_SLOTS  = ('E', 'F', 'G', 'H')   # J5 = E-H
RIGHT_SLOTS = ('A', 'B', 'C', 'D')   # J3 = A-D
POWER_REFS = {'A':'J53', 'B':'J62', 'C':'J54', 'D':'J63',
              'E':'J55', 'F':'J64', 'G':'J56', 'H':'J65',
              'L':'J57', 'M':'J58'}

# The FPGA. Bank 16 (network) is the top-left quadrant of the package and
# faces the top edge, where the three jacks and the PHY sit; the GTP corner
# is unused in rev A. The die stays below centre to leave the network strip.
FPGA = (50.0, 62.0)

# Three RJ45 jacks along the top edge, 17.8 mm pitch, mouths overhanging the
# edge by about 3 mm like any tab-down jack. The imported footprints put the
# mouth at -y for the HanRun magjack (its LED pins sit at the front) and at
# +y for the Kinghelm plain jack (shield tabs at the front), hence the two
# rotations. Verify both in the 3D view before ordering; the STEP models are
# imported. Left to right: LINK P, LINK Q, ETH; the PHY goes between ETH and
# the FPGA. J50 moves to the top-left corner to make room.
JACK_PITCH = 17.8
JACK_X = {'J71': 25.0, 'J72': 25.0 + JACK_PITCH, 'J70': 25.0 + 2 * JACK_PITCH}
JACK_Y = {'J71': 7.7, 'J72': 7.7, 'J70': 10.0}   # origin so the mouth sits ~3 mm past y=0
JACK_ROT = {'J71': 180, 'J72': 180, 'J70': 0}

def contract():
    """Tier 1: every promised position, computed."""
    out = []

    # --- extension edges -------------------------------------------------
    # Left edge (x small): E-H. Right edge: A-D. Signal bodies vertical.
    # One continuous 2x32 body serves all four zones on each edge. Opposite
    # rotations face the sockets across the shield; design.py reverses J5's
    # physical-column map so the electrical pattern itself is not mirrored.
    # tools/place.py compares all 64 real pad coordinates directly.
    for jsig, edge in (('J5', 'L'), ('J3', 'R')):
        xs = EDGE_SIG if edge == 'L' else BOARD_W - EDGE_SIG
        r = 90 if edge == 'L' else 270
        out.append(P(jsig, xs, BODY_CTR, r, why=f'{edge} edge signal 2x32'))

    # Keyed power rows: position 1 is the post; the 1x7 body covers positions
    # 2..8. Four eight-column sections occupy the body's uninterrupted pitch;
    # their centres are 20.32 mm apart around the y=50 body centre.
    zone_y = {s: BODY_CTR + (i - 1.5) * 8 * 2.54
              for slots in (LEFT_SLOTS, RIGHT_SLOTS)
              for i, s in enumerate(slots)}
    for s in LEFT_SLOTS:
        out.append(P(f'MK{ord(s)}', EDGE_PWR, zone_y[s] - 8.89, 0, why=f'{s} power position 1'))
        out.append(P(POWER_REFS[s], EDGE_PWR, zone_y[s] + 1.27, 270,
                     why=f'{s} power positions 2..8'))
    for s in RIGHT_SLOTS:
        x = BOARD_W - EDGE_PWR
        out.append(P(f'MK{ord(s)}', x, zone_y[s] - 8.89, 0, why=f'{s} power position 1'))
        out.append(P(POWER_REFS[s], x, zone_y[s] + 1.27, 270,
                     why=f'{s} power positions 2..8'))

    # --- 5V buses on the bottom edge ------------------------------------
    # Both buses are in bank 13 (1.8 V, rows U..AC, lower/right-most on the
    # die): M outermost right, L inboard.
    # J8 sits 25.4 (10 pitches) from J7 so both buses share one lattice.
    for jsig, s, x in (('J7', 'L', 48.0), ('J8', 'M', 73.4)):
        out.append(P(jsig, x, BOARD_H - EDGE_SIG, 0, why='5V bus signal 2x8'))
        out.append(P(f'MK{ord(s)}', x - 8.89, BOARD_H - EDGE_PWR, 0,
                     why=f'{s} power position 1'))
        out.append(P(POWER_REFS[s], x + 1.27, BOARD_H - EDGE_PWR, 0,
                     why=f'{s} power positions 2..8'))

    # --- FPGA ------------------------------------------------------------
    out.append(P('U1', *FPGA, 0, why='FBGA-676, bank 16 toward the top edge'))

    # --- network, top edge ----------------------------------------------
    for ref, what in (('J71', 'LINK P plain RJ45'), ('J72', 'LINK Q plain RJ45'),
                      ('J70', 'ETH 1000Base-T magjack')):
        out.append(P(ref, JACK_X[ref], JACK_Y[ref], JACK_ROT[ref], why=what))

    # --- input corners ---------------------------------------------------
    out.append(P('J1', 79.0, 2.6, 0, why='USB-C, mid-mount on top edge'))
    out.append(P('J50', 9.5, 4.2, 0, why='9-21V screw terminal, top-left corner'))

    # --- service row (bottom left) ---------------------------------------
    out.append(P('J2', 26.0, BOARD_H - 5.5, 0, why='FPGA JTAG 2x5'))
    out.append(P('J51', 35.5, BOARD_H - 4.0, 0, why='controller SWD'))
    out.append(P('J52', 39.5, BOARD_H - 5.0, 90, why='EXT JTAG select'))
    out.append(P('SW1', 43.5, BOARD_H - 4.5, 0, why='CTRL BOOT'))
    return out

# ---------------------------------------------------------------- tier 2
# One anchor per schematic group. place.py lays group members on a compact
# grid growing from the anchor in the stated direction. These are starting
# values meant to be tuned by eye; nothing else references them.
ANCHORS = {
    'U7  board controller':        (50.0, 88.0, 'up'),
    'board controller startup memory': (58.5, 92.0, 'right'),
    'crystal (RP-008280 s4)':      (43.5, 92.0, 'left'),
    'U7 core regulator (RP-008280 s2.1)': (56.0, 84.0, 'right'),
    'PSRAM0': (69.0, 50.0, 'down'), 'PSRAM1': (69.0, 58.0, 'down'),
    'PSRAM2': (69.0, 66.0, 'down'), 'PSRAM3': (69.0, 74.0, 'down'),
    'config flash':                (69.0, 42.0, 'down'),
    'U15  5V to +1V0  (4A FPGA core supply)': (30.0, 55.0, 'left'),
    'MGTAVCC filter':              (36.0, 44.0, 'up'),
    'U16  5V to +1V2_MGT':         (30.0, 44.0, 'left'),
    'U14  5V to +1V8':             (30.0, 66.0, 'left'),
    'U13  5V to +2V5':             (30.0, 72.0, 'left'),
    'U11  VSYS to +5V':            (80.0, 14.0, 'down'),
    'U12  VSYS to +3V3  (always-on AP63300 reference circuit)': (70.0, 14.0, 'down'),
    'AUX IN':                      (60.0, 14.0, 'down'),
    'VBUS pass switch to +5V':     (90.0, 12.0, 'down'),
    'input OR-ing':                (75.0, 8.0, 'right'),
    'USB protection':              (85.0, 8.0, 'down'),
    'USB-PD sink':                 (93.0, 16.0, 'down'),
    'board status LEDs':          (24.0, 82.0, 'right'),
    'U30  gigabit PHY':            (60.0, 26.0, 'down'),
    'PHY clock':                   (66.0, 30.0, 'down'),
    'PHY straps and LEDs':         (52.0, 30.0, 'down'),
    'ETH jack':                    (60.0, 20.0, 'right'),
    'LINK P':                      (25.0, 22.0, 'down'),
    'LINK Q':                      (42.8, 22.0, 'down'),
    'GTP calibration':             (36.0, 48.0, 'right'),
    'system clock':                (50.0, 46.0, 'right'),
    'JTAG owner selection':        (24.0, 88.0, 'right'),
    'series resistors to FPGA':    (38.0, 80.0, 'right'),
    'config straps (UG470)':       (56.0, 74.0, 'right'),
    'extension power protection control': (50.0, 24.0, 'right'),
    'U21  +5V to +5V_EXT':         (14.0, 20.0, 'down'),
    'U22  +3V3 to +3V3_EXT':       (14.0, 26.0, 'down'),
    'U23  VCCIO_1 to VCCIO_1_EXT': (86.0, 26.0, 'down'),
    'U24  VCCIO_2 to VCCIO_2_EXT': (14.0, 32.0, 'down'),
    'VCCIO_1 selector':            (86.0, 40.0, 'down'),
    'VCCIO_2 selector':            (14.0, 40.0, 'down'),
    'rail monitors':               (58.0, 88.0, 'right'),
    'BOOTSEL':                     (44.0, 92.0, 'down'),
    'RUN':                         (46.0, 84.0, 'left'),
    'USB-C':                       (88.0, 6.0, 'down'),
}
# Slot branch groups (fuses + selector + caps): a strip inboard of each key.
for i, s in enumerate(LEFT_SLOTS):
    ANCHORS[f'SLOT {s} branches'] = (21.0, 18.0 + 21.0 * i, 'down')
for i, s in enumerate(RIGHT_SLOTS):
    ANCHORS[f'SLOT {s} branches'] = (79.0, 18.0 + 21.0 * i, 'down')
ANCHORS['SLOT L branches'] = (56.0, 80.0, 'right')
ANCHORS['SLOT M branches'] = (82.0, 80.0, 'right')
ANCHORS['5V BUS 0 converter'] = (56.0, 74.0, 'right')
ANCHORS['5V BUS 1 converter'] = (82.0, 74.0, 'right')

# ---------------------------------------------------------------- checks
FP_DIRS = ('easyeda/EasyEDA.pretty', 'kicad/odin.pretty')

def _fp_bbox(fpname):
    for d in FP_DIRS:
        p = os.path.join(d, fpname + '.kicad_mod')
        if os.path.isfile(p):
            t = open(p).read()
            xs, ys = [], []
            crt = re.findall(r'\(fp_line[^(]*\(start ([-\d.]+) ([-\d.]+)\)\s*'
                             r'\(end ([-\d.]+) ([-\d.]+)\)[^)]*?F\.CrtYd', t) or \
                  re.findall(r'\(fp_line(.*?F\.CrtYd.*?)\)\)', t, re.S)
            if crt and isinstance(crt[0], tuple):
                for a, b, c, d in crt:
                    xs += [float(a), float(c)]; ys += [float(b), float(d)]
            else:
                scope = crt if crt else [t]
                for s in scope:
                    for m in re.finditer(r'\((?:start|end|at|xy) ([-\d.]+) ([-\d.]+)', s):
                        xs.append(float(m.group(1))); ys.append(float(m.group(2)))
            return min(xs), max(xs), min(ys), max(ys)
    return None

CONTRACT_FP = {         # ref prefix -> footprint file stem, for the checker
    'J3': 'HDR-TH_64P-P2.54-V-F-R2-C32-S2.54-1',
    'J5': 'HDR-TH_64P-P2.54-V-F-R2-C32-S2.54-1',
    'J7': 'HDR-TH_16P-P2.54-V-F-R2-C8-S2.54', 'J8': 'HDR-TH_16P-P2.54-V-F-R2-C8-S2.54',
    **{r: 'HDR-TH_7P-P2.54-V-F' for r in POWER_REFS.values()},
    'J70': 'RJ45-TH_HR911130A', 'J71': 'RJ45-TH_KH-RJ45-58-8P8C',
    'J72': 'RJ45-TH_KH-RJ45-58-8P8C',
    'U1': 'FBGA-676_L27.0-W27.0-R26-C26-P1.00-BL',
    'J1': 'USB-C-SMD_HC-TYPE-C-16P-01A', 'J50': 'CONN-TH_P5.00_KF301-5.0-2P',
    'J2': 'IDC-TH_10P-P2.54_C5665',
    **{f'MK{ord(s)}': 'HDR-TH_1P-P2.54-V-M-21MM-C51353' for s in 'ABCDEFGHLM'},
}

def _rot_bbox(b, rot):
    import math
    x0, x1, y0, y1 = b
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    pts = [(x * c + y * s, -x * s + y * c)
           for x in (x0, x1) for y in (y0, y1)]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return min(xs), max(xs), min(ys), max(ys)

def check(placed):
    """Courtyard-level sanity: on board, no contract-vs-contract overlap."""
    boxes, errs = [], []
    for p in placed:
        stem = CONTRACT_FP.get(p.ref)
        if not stem:
            continue
        b = _fp_bbox(stem)
        if not b:
            errs.append(f'{p.ref}: footprint {stem} not found'); continue
        x0, x1, y0, y1 = _rot_bbox(b, p.rot)
        box = (p.ref, p.x + x0, p.x + x1, p.y + y0, p.y + y1)
        # jacks and USB may legitimately overhang the edge
        overhang_ok = p.ref in ('J70', 'J71', 'J72', 'J1', 'J50')
        if not overhang_ok and (box[1] < 0 or box[2] > BOARD_W or
                                box[3] < 0 or box[4] > BOARD_H):
            errs.append(f'{p.ref}: outside the board: {box[1:]}')
        boxes.append(box)
    inside = set()
    # Adjacent cut-strip post and female socket plastics share their nominal
    # courtyard boundary; this is the intended keyed compound row.
    inside.update(frozenset((f'MK{ord(s)}', POWER_REFS[t]))
                  for s in 'ABCDEFGHLM' for t in 'ABCDEFGHLM')
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            if frozenset((a[0], b[0])) in inside:
                continue
            if a[1] < b[2] and b[1] < a[2] and a[3] < b[4] and b[3] < a[4]:
                errs.append(f'contract overlap: {a[0]} x {b[0]}')
    return errs

def shield_keepouts():
    """Read the authoritative PCB; print tall-part envelopes without moving it."""
    import pcbnew
    board = pcbnew.LoadBoard('kicad/odin.kicad_pcb')
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    rows = ['| Ref | Board-local X interval (mm) | Y interval (mm) | Shield obligation |',
            '|---|---:|---:|---|']
    for ref in ('J70','J71','J72','J50','J68'):
        fp = fps[ref]
        graphics = [g.GetBoundingBox() for g in fp.GraphicalItems()
                    if g.GetLayer() == pcbnew.F_CrtYd]
        if not graphics: graphics = [fp.GetBoundingBox(False)]
        x0 = min(pcbnew.ToMM(g.GetLeft()) for g in graphics) - ORIGIN_X
        x1 = max(pcbnew.ToMM(g.GetRight()) for g in graphics) - ORIGIN_X
        y0 = min(pcbnew.ToMM(g.GetTop()) for g in graphics) - ORIGIN_Y
        y1 = max(pcbnew.ToMM(g.GetBottom()) for g in graphics) - ORIGIN_Y
        what = 'jack cutout and cable access' if ref in ('J70','J71','J72') else 'terminal cutout and screwdriver access'
        if not (0 <= fp.GetPosition().x/1e6-ORIGIN_X <= BOARD_W and
                0 <= fp.GetPosition().y/1e6-ORIGIN_Y <= BOARD_H):
            what += '; currently outside board, human placement pending'
        rows.append(f'| {ref} | {x0:.2f} to {x1:.2f} | {y0:.2f} to {y1:.2f} | {what} |')
    for s in 'ABCDEFGHLM':
        fp = fps[f'MK{ord(s)}']
        x = pcbnew.ToMM(fp.GetPosition().x)-ORIGIN_X
        y = pcbnew.ToMM(fp.GetPosition().y)-ORIGIN_Y
        rows.append(f'| MK{ord(s)} | centre {x:.2f} | centre {y:.2f} | >=1.6 mm bare NPTH; post tip >=18.5 mm |')
    return '\n'.join(rows)


if __name__ == '__main__' and '--keepouts' in sys.argv:
    print(shield_keepouts())
    raise SystemExit(0)

if __name__ == '__main__':
    placed = contract()
    for p in placed:
        print(p)
    errs = check(placed)
    print(f'\n{len(placed)} contract placements, {len(ANCHORS)} group anchors')
    if errs:
        print('CONTRACT VIOLATIONS:')
        for e in errs: print(' ', e)
        raise SystemExit(1)
    print('contract check: clean')
