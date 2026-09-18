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
  3. RULES         parametric placement (BGA decoupling mirrored under supply
                   balls). Implemented in place.py where pad data exists.

Run standalone to print the table and check courtyard collisions:
    python3 tools/placement.py
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))

from sfp_cage import CONNECTOR_DEPTH, MOUTH_OVERHANG

BOARD_W, BOARD_H = 100.0, 100.0
ORIGIN_X, ORIGIN_Y = 30.0, 30.0          # must match tools/gen_pcb.py X0, Y0

# ---------------------------------------------------------------- helpers
def grid(v, pitch=0.1):
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
# 2x16 signal socket body (courtyard): 41.0 x 6.46, pads centred on origin.
# 1x16 power row:                      41.1 x 2.54.
# SFP cage: 48.98 x 15.85; origin at board-edge datum, nose at x=-7.
# FBGA-676:                            27.4 x 27.7 courtyard.
SIG_LEN   = 41.00       # 2x16 body length
SIG_W     = 6.46
PWR_W     = 2.54
# THE LATTICE. A shield bridges signal rows, power row and key post, so all
# of them must sit on one 2.54mm grid RELATIVE to each other. The absolute
# inset from the board edge is free; the relative spacings are the contract.
EDGE_SIG  = 4.70                     # signal 2x16 centreline; rows at +/-1.27
EDGE_PWR  = EDGE_SIG + 1.27 + 3 * 2.54   # 13.59: inner sig row + 3 pitches
KEY_INSET = EDGE_SIG + 1.27 + 5 * 2.54   # 18.67: same lattice, 2 past power
BODY_CTR  = (26.50, 73.50)   # the two body centres along an edge (y for L/R
                             # edges). Gap between bodies: 6.0mm; margins 6.0.

# Slot letters per edge. Package geometry decides this, not taste: bank 34
# balls (E-H) live on package columns 1..8 (left half of U1), banks 15/13/14
# (A-D, bus M, PSRAM, flash) on columns 14..26 (right half). Crossing the die
# with 96 escapes would be self-sabotage.
LEFT_SLOTS  = ('E', 'F', 'G', 'H')   # J5 = EF, J6 = GH
RIGHT_SLOTS = ('A', 'B', 'C', 'D')   # J3 = AB, J4 = CD

# The FPGA. The SFP cages intrude ~44mm from the top edge, so the die sits
# below centre. Its top rows (A..F) carry the GTP balls: they face the cages.
FPGA = (50.0, 62.0)

# SFP cage footprint +x points into the board. KiCad rotation 270 maps
# +x to board +y: mouth at y=-7, rear at y=41.98. The connector footprint
# has contact rows along y, so rotation 180 puts pins 1..10 toward the mouth.
CAGE_PITCH = 17.0
CAGE_X = (29.0, 29.0 + CAGE_PITCH)
CAGE_OVERHANG = MOUTH_OVERHANG
CAGE_Y = 0.0                         # PCB-edge datum, not shell centre
SFP_CONN_Y = CAGE_Y + CONNECTOR_DEPTH # locating peg centreline: 35.40 mm

def contract():
    """Tier 1: every promised position, computed."""
    out = []

    # --- extension edges -------------------------------------------------
    # Left edge (x small): E-H. Right edge: A-D. Signal bodies vertical.
    # The same physical body serves both zones of its pair (EF, GH / AB, CD).
    # Rotations: pad rows must face so that connector column 1 of a left body
    # and column 1 of its opposite right body share the same y. Both bodies
    # are placed at the same y-centres with rotations 90 (left) and 270
    # (right); tools/place.py verifies the resulting pad pairing from real
    # pad coordinates and refuses to write a board that breaks it.
    for (jsig, jpwr, y) , edge in (
            (('J5', 'J55', BODY_CTR[0]), 'L'), (('J6', 'J56', BODY_CTR[1]), 'L'),
            (('J3', 'J53', BODY_CTR[0]), 'R'), (('J4', 'J54', BODY_CTR[1]), 'R')):
        xs = EDGE_SIG if edge == 'L' else BOARD_W - EDGE_SIG
        xp = EDGE_PWR if edge == 'L' else BOARD_W - EDGE_PWR
        r  = 90 if edge == 'L' else 270
        out.append(P(jsig, xs, y, r, why=f'{edge} edge signal 2x16'))
        out.append(P(jpwr, xp, y, r, why=f'{edge} edge power 1x16'))

    # Key posts: one per logical zone, inboard of the power row, at the zone
    # centre. Zone centres: each 2x16 body spans two zones of 8 columns;
    # zone centre offset from body centre = +/- 8 * 2.54 / 2 = 10.16.
    zone_dy = 10.16
    zone_y = {s: BODY_CTR[i // 2] + (-zone_dy if i % 2 == 0 else zone_dy)
              for i, s in enumerate(LEFT_SLOTS)}
    zone_y.update({s: BODY_CTR[i // 2] + (-zone_dy if i % 2 == 0 else zone_dy)
                   for i, s in enumerate(RIGHT_SLOTS)})
    for s in LEFT_SLOTS:
        out.append(P(f'MK{ord(s)}', KEY_INSET, zone_y[s], 0, why=f'key {s}'))
    for s in RIGHT_SLOTS:
        out.append(P(f'MK{ord(s)}', BOARD_W - KEY_INSET, zone_y[s], 0, why=f'key {s}'))

    # --- 5V buses on the bottom edge ------------------------------------
    # L (bank 14) right of M (bank 13)? Bank 13 balls sit lower/right-most on
    # the die (rows U..AC), bank 14 mid-right: M outermost right, L inboard.
    # J8 sits 25.4 (10 pitches) from J7 so both buses share one lattice.
    for jsig, jpwr, mk, x in (('J7', 'J57', 'MK76', 48.0),
                              ('J8', 'J58', 'MK77', 73.4)):
        out.append(P(jsig, x, BOARD_H - EDGE_SIG, 180, why='5V bus signal 2x8'))
        out.append(P(jpwr, x, BOARD_H - EDGE_PWR, 180, why='5V bus power 1x8'))
        out.append(P(mk, x - 13.0, BOARD_H - KEY_INSET, 0, why='key 5V bus'))

    # --- FPGA ------------------------------------------------------------
    out.append(P('U1', *FPGA, 0, why='FBGA-676, GTP rows toward cages'))

    # --- high speed ------------------------------------------------------
    for i, (sh, j) in enumerate((('SH1', 'J60'), ('SH2', 'J61'))):
        out.append(P(sh, CAGE_X[i], CAGE_Y, 270, why='SFP cage, bezel off top'))
        out.append(P(j, CAGE_X[i], SFP_CONN_Y, 180, why='SFP 20p connector'))
    out.append(P('X2', 58.0, 44.0, 0, why='125MHz LVDS osc, short to refclk'))

    # --- input corner (top right) ---------------------------------------
    out.append(P('J1', 79.0, 2.6, 0, why='USB-C, mid-mount on top edge'))
    out.append(P('J50', 60.0, 5.0, 0, why='9-14V screw terminal'))

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
    'U11  12V to 5V':              (80.0, 14.0, 'down'),
    'U12  VSYS to +3V3  (always-on AP63300 reference circuit)': (70.0, 14.0, 'down'),
    'U19  5V to 12V boost (AUX)':  (60.0, 14.0, 'down'),
    'VBUS pass switch to +5V':     (90.0, 12.0, 'down'),
    'input OR-ing':                (75.0, 8.0, 'right'),
    'USB protection':              (85.0, 8.0, 'down'),
    'USB-PD sink':                 (93.0, 16.0, 'down'),
    'SFP power gate':              (44.0, 36.0, 'right'),
    'SFP I2C mux':                 (57.0, 36.0, 'right'),
    'SFP I2C bus':                 (50.0, 36.0, 'right'),
    'board status LEDs':          (24.0, 82.0, 'right'),
    'SFP port expander':           (56.0, 36.0, 'right'),
    'SFP port 0':                  (26.0, 44.0, 'down'),
    'SFP port 1':                  (42.5, 44.0, 'down'),
    '125MHz reference clock':      (50.0, 44.0, 'right'),
    'JTAG owner selection':        (24.0, 88.0, 'right'),
    'series resistors to FPGA':    (38.0, 80.0, 'right'),
    'config straps (UG470)':       (56.0, 74.0, 'right'),
    'extension power protection control': (50.0, 24.0, 'right'),
    'U21  +5V to +5V_EXT':         (14.0, 20.0, 'down'),
    'U22  +3V3 to +3V3_EXT':       (14.0, 26.0, 'down'),
    'U23  VCCIO_1 to VCCIO_1_EXT': (86.0, 26.0, 'down'),
    'U24  VCCIO_2 to VCCIO_2_EXT': (14.0, 32.0, 'down'),
    'U25  +12V to +12V_EXT':       (52.0, 18.0, 'right'),
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
    'J3': 'HDR-SMD_32P-P2.54-V-F-R2-C16-LS7.1', 'J4': 'HDR-SMD_32P-P2.54-V-F-R2-C16-LS7.1',
    'J5': 'HDR-SMD_32P-P2.54-V-F-R2-C16-LS7.1', 'J6': 'HDR-SMD_32P-P2.54-V-F-R2-C16-LS7.1',
    'J53': 'HDR-TH_16P-P2.54-V-F-1', 'J54': 'HDR-TH_16P-P2.54-V-F-1',
    'J55': 'HDR-TH_16P-P2.54-V-F-1', 'J56': 'HDR-TH_16P-P2.54-V-F-1',
    'J7': 'HDR-SMD_16P-P2.54-V-F-R2-C8-LS7.1', 'J8': 'HDR-SMD_16P-P2.54-V-F-R2-C8-LS7.1',
    'J57': 'HDR-TH_8P-P2.54-V-F', 'J58': 'HDR-TH_8P-P2.54-V-F',
    'SH1': 'Amphenol_U77A11133001', 'SH2': 'Amphenol_U77A11133001',
    'J60': 'CONN-SMD_20P-P0.80-S8.20_1888247-1', 'J61': 'CONN-SMD_20P-P0.80-S8.20_1888247-1',
    'U1': 'FBGA-676_L27.0-W27.0-R26-C26-P1.00-BL',
    'J1': 'USB-C-SMD_HC-TYPE-C-16P-01A', 'J50': 'CONN-TH_P5.00_KF301-5.0-2P',
    'J2': 'IDC-TH_10P-P2.54_C5665',
    'MK65': 'HDR-TH_1P-P2.54-V-M', 'MK66': 'HDR-TH_1P-P2.54-V-M',
    'MK67': 'HDR-TH_1P-P2.54-V-M', 'MK68': 'HDR-TH_1P-P2.54-V-M',
    'MK69': 'HDR-TH_1P-P2.54-V-M', 'MK70': 'HDR-TH_1P-P2.54-V-M',
    'MK71': 'HDR-TH_1P-P2.54-V-M', 'MK72': 'HDR-TH_1P-P2.54-V-M',
    'MK76': 'HDR-TH_1P-P2.54-V-M', 'MK77': 'HDR-TH_1P-P2.54-V-M',
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
        # cages and USB may legitimately overhang the edge
        overhang_ok = p.ref in ('SH1', 'SH2', 'J1', 'J50')
        if not overhang_ok and (box[1] < 0 or box[2] > BOARD_W or
                                box[3] < 0 or box[4] > BOARD_H):
            errs.append(f'{p.ref}: outside the board: {box[1:]}')
        boxes.append(box)
    inside = {frozenset(('SH1', 'J60')), frozenset(('SH2', 'J61'))}
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            if frozenset((a[0], b[0])) in inside:
                continue
            if a[1] < b[2] and b[1] < a[2] and a[3] < b[4] and b[3] < a[4]:
                errs.append(f'contract overlap: {a[0]} x {b[0]}')
    return errs

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
