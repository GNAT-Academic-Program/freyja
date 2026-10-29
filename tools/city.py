#!/usr/bin/env python3
"""City plan: where each parked island goes relative to the others.

    python3 tools/city.py                 # plan + preview, writes nothing to the pcb
    python3 tools/islands.py --city ref/city/plan.yaml --apply   # move the groups

The islands (dashed boxes in the lot) are the neighbourhoods. This lays them
out as a city beside the sheet, inside a copy of the board outline drawn at
SCALE times real size (the boxes with their title bars take about twice the
board's area; the owner compacts them by hand afterwards):

  1. Frame: the board outline and every footprint already on the board
     (expansion headers, slot rows, key posts) drawn as ghosts at their
     scaled places. They are fixed; blocks are pulled toward the pins they
     wire to.
  2. Edges, for the user: connectors a cable plugs into sit on the edge,
     in the order of tools/placement.py's contract (network jacks, USB-C and
     the power input on the top edge; 5 V buses, their slot rows and the
     service row on the bottom). Each edge block is fixed.
  3. Wiring: every net shared by two blocks pulls the pins on that net
     together (the pins, not the block centres, so a regulator lands on the
     side of its load where the rail pins are). A net shared by k blocks
     weighs 1/(k-1): a short signal pulls hard, a rail shared by twenty
     islands barely. GND is ignored. placement.py's group anchors are a weak
     prior.
  4. Legalize: blocks in priority order go to the nearest spot that
     overlaps nothing.

Nothing here moves a footprint: the plan is a list of rigid moves per island
group, applied by tools/islands.py --city.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import islands as I  # noqa: E402

ROOT = I.ROOT
OUT_DIR = os.path.join(ROOT, 'ref', 'city')
SCALE = 2.2
ORIGIN = (650.0, 20.0)          # canvas position of the board's top-left corner
GAP = 2.0                       # between blocks on the canvas
PRIOR = 0.05                    # weak pull toward the board centre, a tie-break

# Edge layouts, board-relative x along the top and bottom edges. The slot
# rows take x < 13.4 and x > 86.2 down to y = 85, so the top edge holds
# 73 mm and the bottom edge the full 100 mm. Rows are packed in this order,
# each block as close to its x as the ones before it allow.
#
# best (default): U1 turned 90 degrees. Scored on signal balls only
#   (python3 tools/city.py --score), every interface then faces its
#   connector: A-D toward J3 (left) +0.75, E-H toward J5 (right) +0.97,
#   network toward the bottom +0.73, the 5 V buses toward the top +0.48.
#   So the network jacks take the bottom edge (bank 16 balls sit
#   bottom-left), the bus headers the top. USB-C, the DC and AUX inputs stay
#   on the top edge, the service row goes bottom-right.
# contract: tools/placement.py as written (U1 at 0, jacks on top, buses on
#   the bottom): E-H balls face nowhere (-0.02) and the bus balls face away
#   from their headers (-0.86).
VARIANTS = {
    'best': dict(
        # absolute rotations: U1 per the score; J70 and J1 so their openings
        # face out of their edge (pins at the back of the body)
        turn={'U1': 90, 'J70': 180, 'J1': 180},
        inner={'U1': (50.0, 48.0)},   # 48: room above for the top power door
        # the two bus headers sit symmetric about the board centre, 25.4 mm
        # apart (ten 2.54 pitches, the shield lattice), so a shield has legs
        # spread evenly; the DC input takes the top-left corner, USB-C the
        # top-right, the AUX input moves to the bottom-right corner
        top=[('J50', 19.0), ('J7', 37.3), ('J8', 62.7), ('J1', 81.0)],
        # the L/M power rows and their keys (MK76 / MK77: design.py names the
        # post MK{ord(slot)}, so MK71/MK72 are the G/H keys and belong to the
        # side rows, findings 51) stack inboard of the bus headers
        top_inboard={'J57': 'J7', 'J58': 'J8', 'MK76': 'J7', 'MK77': 'J8'},
        # the two LINK jacks (straight to the FPGA, experiments) and the real
        # Ethernet jack (through the PHY) are kept apart by the FPGA JTAG
        # header, so the two kinds read differently at a glance. HDMI OUT
        # (J73) sits under bank 35, the FPGA's bottom-right corner; the SWD
        # connector, the JTAG jumper and the BOOTSEL button take no cable
        # from outside the case and move inboard, pulled by their wiring
        bottom=[('J71', 15.0), ('J72', 32.8), ('J2', 50.0), ('J70', 66.0), ('J73', 83.0),
                ('J68', 97.0)],
        # J74, the microSD socket (2026-10-29): neither edge has the 14.5 mm
        # it needs (bottom: six cabled connectors in 88 mm; top: 73 mm usable,
        # 60 mm taken, J7/J8 fixed 25.4 mm apart), so it sits inboard, pulled
        # by its bank 14 lines, card opening toward the bottom edge (its
        # contacts are at the back of the footprint, rotation 0). The SDRAM
        # U32 and the MRAM U33 are plain blocks pulled by their bank 35 /
        # bank 14 lines.
        bottom_inboard={}),
    'contract': dict(
        turn={'J71': 180, 'J72': 180},
        inner={'U1': (50.0, 60.0)},
        top=[('J50', 14.0), ('J71', 31.0), ('J72', 48.8), ('J70', 66.6), ('J1', 84.0)],
        top_inboard={},
        bottom=[('J2', 22.0), ('J51', 32.0), ('J52', 38.0), ('SW1', 44.0), ('J7', 54.0),
                ('J8', 76.0), ('J68', 93.0)],
        bottom_inboard={'J57': 'J7', 'J58': 'J8', 'MK76': 'J7', 'MK77': 'J8'}),
}
# districts (owner, 2026-10-29): the owner moved the islands by hand in the
# city and asked for the board to read as a few clear neighbourhoods: the
# LEDs as one dashboard, the PSRAMs as one tiled block, the jumpers as a
# control corner, the USB story in one place, the regulators in rows, the
# JTAG parts together, the JTAG header at the far bottom-left, every cable
# jack on the bottom edge, USB-C on top. Each entry below places one block
# against a neighbour already placed (edges and doors come first):
#   x: ('right_of' | 'left_of', REF [, gap])  beside REF's box
#      ('left' | 'right' | 'centre', REF)      flush with REF's box edge
#   y: ('above' | 'below', REF [, gap]) / ('top' | 'bottom' | 'centre', REF)
# Two things the owner's hand layout could not show at 2.2x, kept here:
#   - the bottom edge is 89.6 mm at real size (the slot rows reach y 82-85
#     at both corners, so a jack 18-21 mm deep starts at x 10.4); the five
#     cable jacks take 80.1 mm of it. The JTAG header (8.8 mm standing)
#     does not fit on the edge with them unless the AUX terminal moves to
#     the right edge with 0.5 mm gaps, so it stands one row in, at the far
#     left above the LINK P jack: a ribbon cable comes from above, it needs
#     no edge. The microSD (16.7 mm) does not fit either (the previous
#     finding stands) and stays inboard, pulled by its bank lines.
#   - U11 and U12 are the two identical VSYS converters (AP63300, 21 V in):
#     they sit side by side straight under the eFuse U26 and against the
#     mux U34, so the 21 V bus never leaves the USB corner where it enters
#     (U26 under USB-C; J50's D4 at the top-left is the other source) and
#     U11 -> U34 stays short. U13 (2.5 V) stays at the PHY, its load, as the
#     bottom door. The FPGA door (U16, U15, U14, U34) is the regulator row;
#     the two VSYS cells hang one step below its right end.
VARIANTS['districts'] = dict(
    VARIANTS['best'],
    turn={'U1': 90, 'J70': 180, 'J1': 180, 'J2': 90},
    # rows: cells merged into a host island at a fixed pitch, LED centres on
    # one line (the dashboard is one island, one box, one title; the labels
    # on the silkscreen come from tools/stencil.py)
    rows={'D1': (['D9', 'D10', 'D11'], 5.0, 'LED dashboard: CTRL HB, USER 1, USER 2 at 5 mm pitch right of FPGA DONE')},
    # the owner's bottom order; x is the real-size centre so the row fits
    # 10.7..100 with 1 mm gaps (J71 17.0, J72 17.0, J70 17.6, J73 18.5, J68 10.0)
    bottom=[('J71', 19.5), ('J72', 37.5), ('J70', 55.5), ('J73', 74.5), ('J68', 94.5)],
    districts=[
        # service corner, bottom-left: JTAG header standing above the LINK P
        # jack, the JTAG switch beside it, its jumper on top; then the A-D
        # PIN V jumper with its switch on top (VCCIO_1 balls are at the
        # FPGA's bottom-left, the A-D fuses run up the left strip)
        ('J2', dict(x=('left', 'J71'), y=('above', 'J71')), 'service corner: JTAG header standing at the far bottom-left, one row in'),
        ('U20', dict(x=('right_of', 'J2'), y=('bottom', 'J2')), 'service corner: JTAG switch beside its header'),
        ('J52', dict(x=('left', 'U20'), y=('above', 'U20')), 'service corner: EXT JTAG jumper on its switch'),
        ('J19', dict(x=('right_of', 'U20'), y=('bottom', 'U20')), 'service corner: A-D PIN V jumper'),
        ('U23', dict(x=('left', 'J19'), y=('above', 'J19')), 'service corner: A-D PIN V switch on its jumper'),
        # the E-H mirror, bottom-right, above the HDMI jack
        ('J20', dict(x=('right', 'J73'), y=('above', 'J73')), 'E-H PIN V jumper above HDMI, mirror of J19'),
        ('U24', dict(x=('right', 'J20'), y=('above', 'J20')), 'E-H PIN V switch on its jumper, mirror of U23'),
        # the LED dashboard (one block, see rows) above the AUX terminal,
        # right-aligned to it, at the board's bottom-right corner
        ('D1', dict(x=('right', 'J68'), y=('above', 'J68')), 'LED dashboard above the AUX terminal, bottom-right corner'),
        # USB story, top-right: eFuse under the connector, PD negotiator
        # beside it, the two VSYS converters side by side under slot M's
        # power socket, against the door row's mux
        ('U26', dict(x=('right', 'J1'), y=('below', 'J1')), 'USB story: eFuse straight under USB-C'),
        ('U18', dict(x=('right_of', 'U26'), y=('top', 'U26')), 'USB story: PD negotiator beside the eFuse, CC lines short'),
        ('U11', dict(x=('right_of', 'U34'), y=('below', 'U26')), 'VSYS converters: 5 V cell beside the mux, straight under the eFuse'),
        ('U12', dict(x=('right_of', 'U11'), y=('top', 'U11')), 'VSYS converters: 3.3 V cell beside the 5 V cell, identical'),
        # PSRAM: four identical cells in a 2 x 2 block on the FPGA's left,
        # top-aligned with its island (PSRAM0/1 series resistors sit on the
        # north flank, PSRAM2/3 on the west flank)
        ('U3', dict(x=('left_of', 'U1'), y=('top', 'U1')), 'PSRAM block: cell 1 against the FPGA, top row'),
        ('U2', dict(x=('left_of', 'U3'), y=('top', 'U3')), 'PSRAM block: cell 0, top row'),
        ('U4', dict(x=('left', 'U3'), y=('below', 'U3')), 'PSRAM block: cell 2 against the FPGA, bottom row'),
        ('U5', dict(x=('left_of', 'U4'), y=('top', 'U4')), 'PSRAM block: cell 3, bottom row'),
        # serial memory shelf: config flash and MRAM continue the door row
        # leftwards (both on the FPGA's left half, SPI, 4-6 lines each)
        ('U6', dict(x=('left_of', 'U16'), y=('bottom', 'U16')), 'serial memory shelf: config flash at the door row left end'),
        ('U33', dict(x=('left_of', 'U6'), y=('bottom', 'U6')), 'serial memory shelf: MRAM beside the flash'),
        # the PHY straight above its jack
        ('U30', dict(x=('centre', 'J70'), y=('above', 'J70')), 'PHY above the Ethernet jack, MDI pairs straight down'),
        # the 2.5 V regulator beside the PHY, its load, under the FPGA
        ('U13', dict(x=('left_of', 'U30'), y=('below', 'U1')), '2.5 V regulator beside the PHY, under the FPGA'),
    ],
    # dashed boxes drawn round the finished districts (city frame)
    boxes={
        'SERVICE CORNER (JTAG, A-D PIN V)': ['J2', 'U20', 'J52', 'J19', 'U23'],
        'E-H PIN V': ['J20', 'U24'],
        'LED DASHBOARD': ['D1'],
        'USB POWER IN': ['J1', 'U26', 'U18', 'U34'],
        'VSYS CONVERTERS': ['U11', 'U12'],
        'FPGA POWER DOOR': ['U16', 'U15', 'U14'],
        'PSRAM': ['U2', 'U3', 'U4', 'U5'],
        'SERIAL MEMORY': ['U6', 'U33'],
        'NETWORK': ['U30', 'J70', 'U13'],
    })
V = VARIANTS['districts']

# Satellites: parts that must sit right at one chip's pins. Each joins that
# chip's island: it is attached outside the chip's parts on the side where
# the shared pins are, and the two become one block and one box.
SATELLITES = {
    'Y1': ('U7', 'RP2350 12 MHz crystal: at XIN/XOUT, short traces, no other signal between (RP2350 hardware design guide RP-008280, crystal section)'),
    'U8': ('U7', 'RP2350 QSPI flash: QSPI traces as short as possible (RP-008280, flash section)'),
    'X3': ('U30', 'PHY 25 MHz crystal at the PHY XTAL pins (RTL8211F)'),
    # a third element names the one net that decides the side: the clock
    # must sit at the SYS_CLK ball, not at the mean of every +3V3 pad the
    # two share (re-audit 2026-10-29, item 58)
    'X4': ('U1', '50 MHz fabric clock at its MRCC ball M21, 33 ohm at the source (floorplan.md)', 'SYS_CLK'),
    'U31': ('J73', 'HDMI protection chip as close to the connector as possible, no vias '
                   'between them (TI SLLSE96F 10.1)'),
    # PR1 is a 100k/36.5k node compared against CP2 inside the mux: the two
    # transistors that pull it down sit at that pin, not across the board
    'Q6': ('U34', 'pulls the mux PR1 node (9 V request hold); the divider node stays short', 'VBUS5_PR1'),
    'Q7': ('U34', 'pulls the mux PR1 node (screw input present); the divider node stays short', 'VBUS5_PR1'),
}
# Links that matter more than their wire count: the pull between the two
# blocks is multiplied by this factor.
CRITICAL = {
    frozenset(('U7', 'J1')): (6.0, 'USB D+/D- pair from the connector to the RP2350'),
    frozenset(('U26', 'J1')): (8.0, 'VBUS input path: jack, TVS, then the eFuse, as short and wide as possible'),
    frozenset(('U18', 'J1')): (6.0, 'USB-C CC lines to the USB-PD negotiator'),
    frozenset(('U1', 'U6')): (3.0, 'FPGA configuration flash, SPI at up to 100 MHz'),
    frozenset(('U1', 'U15')): (3.0, 'FPGA core supply, 4 A: short wide path'),
    frozenset(('U1', 'U2')): (3.0, 'PSRAM bus'), frozenset(('U1', 'U3')): (3.0, 'PSRAM bus'),
    frozenset(('U1', 'U4')): (3.0, 'PSRAM bus'), frozenset(('U1', 'U5')): (3.0, 'PSRAM bus'),
    frozenset(('U1', 'U30')): (3.0, 'RGMII to the PHY'),
    # every ampere of regulated +5V passes U11 -> U34 -> the rail (item 57):
    # the mux is the junction, so it is pulled to U11 first and the door
    # second; U11 is no longer pulled straight to U15
    frozenset(('U11', 'U34')): (6.0, '+5V_BUCK from U11 into the mux IN2, short and wide; U34 borrows U11 bulk'),
    frozenset(('U34', 'U15')): (4.0, 'the +5V rail from the mux OUT into the top power door, short and wide'),
    frozenset(('U34', 'J1')): (2.0, 'VBUS into the mux IN1'),
}

# Power doors: regulators lined up against one side of the FPGA so each
# drives its plane area straight in under the balls it feeds. The top and
# bottom of the middle column hold only the unused transceiver balls, so no
# signal has to leave there: power enters there without blocking an escape.
# The right side is taken on In3 by VCCIO_2 and the slot E-H escape, the
# left by VCCIO_1 and slots A-D, the bottom-left corner by bank 16 (links).
# Per side: blocks in order left to right, the block aligned on the column,
# and the net whose balls set the column (their mean x).
DOORS = {
    'top': (['U16', 'U15', 'U14', 'U34'], 'U15', '+1V0',
            '1.0 V core (U15, 4 A) straight down the middle column on In3; 1.8 V (U14) '
            'and 1.2 V (U16) beside it, fed on In5 through the same door; the +5V mux '
            'U34 closes the row on the USB side and U11, pulled to it by the CRITICAL '
            'link, sits against it, so U11 -> U34 -> the three 5 V converters is one '
            'path along the door. U11 in the row itself pushed U26 away from J1 (right '
            'end) or PSRAM U2 off the bank-13 side (left end); U34 at the left end sent '
            'U11 onto the PSRAM side too (re-audit 2026-10-29, item 57)'),
    'bottom': (['U13'], 'U13', '+1V0',
               '2.5 V up the middle column from below, then left on In3 under the bank 16 '
               'corner; the PHY beside it shares the rail'),
}
# Parts already in a chip's group that must sit at one of its pins: moved
# inside the group to the side where that pin is (key: group anchor; the
# net is the chip pin's net, followed through the series part).
RESEAT = {
    'U1': (['X4', 'R147', 'C246'], 'SYS_CLK',
           '50 MHz oscillator and its 33 ohm source resistor at the SYS_CLK MRCC ball, '
           'away from the top power door'),
}


# the 'districts' variant sets U13 beside the PHY (district entry) instead
# of the bottom door
VARIANTS['districts']['doors'] = {'top': DOORS['top']}


def canvas(p):
    o = BOARD.outline
    return (ORIGIN[0] + SCALE * (p[0] - o[0]), ORIGIN[1] + SCALE * (p[1] - o[1]))


def rel_canvas(x, y):
    return (ORIGIN[0] + SCALE * x, ORIGIN[1] + SCALE * y)


class Block:
    def __init__(self, label, refs, ext, shift=None):
        self.label, self.refs = label, refs
        self.shift = shift or {}                        # ref -> (dx, dy): satellite parts moved beside the chip
        self.anchor = label.split()[1]
        self.ext = ext                                  # marker rectangle, title bar included
        self.c0 = ((ext[0] + ext[2]) / 2, (ext[1] + ext[3]) / 2)
        # turn: the anchor's target rotation in the variant minus its current
        # one, so a rerun never turns a block twice
        cur = BOARD.fps[self.anchor].rot
        self.turn = I.norm_fp_angle(V['turn'].get(self.anchor, cur) - cur) % 360
        if True:
            # the marker as islands.py --city rebuilds it: courtyards turned
            # about c0, title bar (with the part's plain name) on top
            pts = []
            for r in refs:
                fp = BOARD.fps[r]
                sx_, sy_ = self.shift.get(r, (0.0, 0.0))
                for (px, py) in fp.polygon():
                    dx, dy = I.rot(px + sx_ - self.c0[0], py + sy_ - self.c0[1], self.turn)
                    pts.append((dx, dy))
            bb = I.bbox_of(pts)
            e = I.marker_extent(bb, label, I.make_note('generic', len(refs)))
            self.rel = e                                # marker box relative to the pivot c0
        else:
            self.rel = (ext[0] - self.c0[0], ext[1] - self.c0[1], ext[2] - self.c0[0], ext[3] - self.c0[1])
        self.w, self.h = self.rel[2] - self.rel[0], self.rel[3] - self.rel[1]
        # where the anchor part itself sits, relative to the pivot: edge rows
        # are laid out by the connectors, not by their boxes
        ab = BOARD.fps[self.anchor].bbox()
        self.aoff = I.rot((ab[0] + ab[2]) / 2 - self.c0[0], (ab[1] + ab[3]) / 2 - self.c0[1], self.turn)
        self.pos = None
        self.fixed = False
        self.prior = None
        self.pins = {}                                  # net -> list of offsets from the centre
        for r in refs:
            fp = BOARD.fps[r]
            for p in fp.pads:
                if not p.net or p.net == I.GND or p.net.startswith('unconnected'):
                    continue
                px, py = fp.pad_pos(p)
                sx_, sy_ = self.shift.get(r, (0.0, 0.0))
                ox, oy = I.rot(px + sx_ - self.c0[0], py + sy_ - self.c0[1], self.turn)
                self.pins.setdefault(p.net, []).append((ox, oy))

    def offset(self, net):
        pts = self.pins[net]
        return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))

    def box(self, pos=None):
        """Marker box on the canvas when the pivot c0 sits at pos."""
        x, y = pos or self.pos
        return (x + self.rel[0], y + self.rel[1], x + self.rel[2], y + self.rel[3])


def attach(host_refs, sat_refs, why, gap=0.8, net=None):
    """Where a satellite goes beside its chip, in the board's own frame:
    outside the chip island's parts, on the side where the chip's pins
    shared with the satellite are (only the pins on `net` when one is
    named: a supply rail shared by both must not outvote the one signal
    pin), centred on those pins. Returns ((dx, dy) to add to every
    satellite part, side letter, why)."""
    hb = I.bbox_of([p for r in host_refs for p in BOARD.fps[r].polygon()])
    sb = I.bbox_of([p for r in sat_refs for p in BOARD.fps[r].polygon()])
    sat_nets = {p.net for r in sat_refs for p in BOARD.fps[r].pads
                if p.net and p.net != I.GND and not p.net.startswith('unconnected')}
    if net:
        sat_nets = {net}
    pins = [BOARD.fps[r].pad_pos(p) for r in host_refs for p in BOARD.fps[r].pads if p.net in sat_nets]
    hc = ((hb[0] + hb[2]) / 2, (hb[1] + hb[3]) / 2)
    pc = (sum(x for x, _ in pins) / len(pins), sum(y for _, y in pins) / len(pins)) if pins else hc
    side = I.side_toward((pc[0] - hc[0], pc[1] - hc[1]))
    sw, sh = sb[2] - sb[0], sb[3] - sb[1]
    if side in 'EW':
        x0 = hb[2] + gap if side == 'E' else hb[0] - gap - sw
        y0 = min(max(pc[1] - sh / 2, hb[1]), hb[3] - sh)
    else:
        y0 = hb[3] + gap if side == 'S' else hb[1] - gap - sh
        x0 = min(max(pc[0] - sw / 2, hb[0]), hb[2] - sw)
    return ((x0 - sb[0], y0 - sb[1]), side, why)


def reseat(host_refs, sat_refs, anchor, net, gap=0.8):
    """Shift for parts of the anchor's own group: outside the rest of the
    group, on the side of the anchor's pin(s) on net, centred on them."""
    rest = [r for r in host_refs if r not in sat_refs]
    hb = I.bbox_of([p for r in rest for p in BOARD.fps[r].polygon()])
    sb = I.bbox_of([p for r in sat_refs for p in BOARD.fps[r].polygon()])
    fp = BOARD.fps[anchor]
    pins = [fp.pad_pos(p) for p in fp.pads if p.net == net]
    ac = fp.centre()
    pc = (sum(x for x, _ in pins) / len(pins), sum(y for _, y in pins) / len(pins))
    side = I.side_toward((pc[0] - ac[0], pc[1] - ac[1]))
    sw, sh = sb[2] - sb[0], sb[3] - sb[1]
    if side in 'EW':
        x0 = hb[2] + gap if side == 'E' else hb[0] - gap - sw
        y0 = pc[1] - sh / 2
    else:
        y0 = hb[3] + gap if side == 'S' else hb[1] - gap - sh
        x0 = pc[0] - sw / 2
    return (x0 - sb[0], y0 - sb[1]), side


def pad_rel(block, ref, number):
    """A pad's offset from the block pivot, after the block's turn."""
    fp = BOARD.fps[ref]
    p = next(p for p in fp.pads if p.number == number)
    px, py = fp.pad_pos(p)
    sx_, sy_ = block.shift.get(ref, (0.0, 0.0))
    return I.rot(px + sx_ - block.c0[0], py + sy_ - block.c0[1], block.turn)


def overlaps(a, b, gap=0.0):
    return not (a[2] + gap <= b[0] or b[2] + gap <= a[0] or a[3] + gap <= b[1] or b[3] + gap <= a[1])


def main():
    global BOARD, V
    import argparse
    ap = argparse.ArgumentParser(description='Plan where the parked islands go relative to each other.')
    ap.add_argument('--variant', choices=sorted(VARIANTS), default='districts')
    args = ap.parse_args()
    V = VARIANTS[args.variant]
    BOARD = I.Board(os.path.join(ROOT, 'kicad', 'odin.kicad_pcb'))
    o = BOARD.outline
    groups = {}
    for ref, label in BOARD.island_groups().items():
        groups.setdefault(label, []).append(ref)
    marks = BOARD.markers()
    sat_info = {}
    for sat, info in SATELLITES.items():
        host, why = info[0], info[1]
        net = info[2] if len(info) > 2 else None
        hl, sl = f'island {host}', f'island {sat}'
        if hl not in groups or sl not in groups:
            continue
        sat_info[sl] = attach(groups[hl], groups[sl], why, net=net) + (hl,)
    # two satellites on the same side of one host stack outward in SATELLITES
    # order (Q6 and Q7 both at U34's PR1 pin), instead of landing on each other
    taken = {}
    for sl, (dxy, side, why, hl) in list(sat_info.items()):
        sb = I.bbox_of([p for r in groups[sl] for p in BOARD.fps[r].polygon()])
        depth = (sb[3] - sb[1]) if side in 'NS' else (sb[2] - sb[0])
        used = taken.get((hl, side), 0.0)
        if used:
            step = used + 0.8
            dxy = {'N': (dxy[0], dxy[1] - step), 'S': (dxy[0], dxy[1] + step),
                   'E': (dxy[0] + step, dxy[1]), 'W': (dxy[0] - step, dxy[1])}[side]
            why = f'{why}; stacked outside the satellite before it'
            sat_info[sl] = (dxy, side, why, hl)
        taken[(hl, side)] = used + depth + (0.8 if used else 0.0)
    # rows: cells merged into their host like satellites, at a fixed pitch
    # to the right of the host's anchor, anchor centres on one line
    for host, (cells, pitch, why) in (V.get('rows') or {}).items():
        hl = f'island {host}'
        if hl not in groups:
            continue
        hc = BOARD.fps[host].centre()
        prev_right = I.bbox_of([p for r in groups[hl] for p in BOARD.fps[r].polygon()])[2]
        for i, c in enumerate(cells):
            cl = f'island {c}'
            if cl not in groups:
                continue
            cc = BOARD.fps[c].centre()
            cb = I.bbox_of([p for r in groups[cl] for p in BOARD.fps[r].polygon()])
            tx = max(hc[0] + pitch * (i + 1), prev_right + 1.0 + (cc[0] - cb[0]))
            dxy = (tx - cc[0], hc[1] - cc[1])
            sat_info[cl] = (dxy, 'E', why, hl)
            prev_right = cb[2] + dxy[0]
    reseats = {}
    for a, (srefs, net, _why) in RESEAT.items():
        lab = f'island {a}'
        if lab in groups and all(r in groups[lab] for r in srefs):
            dxy, side = reseat(groups[lab], srefs, a, net)
            reseats[lab] = ({r: dxy for r in srefs}, side)
    blocks = {}
    for lab, refs in groups.items():
        if lab not in marks or lab in sat_info:
            continue
        shift, all_refs = dict(reseats.get(lab, ({}, ''))[0]), list(refs)
        for sl, (dxy, _side, _why, hl) in sat_info.items():
            if hl == lab:
                all_refs += groups[sl]
                shift.update({r: dxy for r in groups[sl]})
        blocks[lab] = Block(lab, all_refs, marks[lab][0], shift)
    by_anchor = {b.anchor: b for b in blocks.values()}

    # fixed ghosts: everything already on the board
    on_board = [r for r, fp in BOARD.fps.items() if o[0] <= fp.x <= o[2] and o[1] <= fp.y <= o[3]]
    ghosts = []
    fixed_pins = {}                                     # net -> list of canvas points
    for r in on_board:
        fp = BOARD.fps[r]
        bb = fp.bbox()
        # only connectors and key posts are drawn: small parts blown up 2.2x
        # read as empty boxes
        if fp.prefix() in ('J', 'MK'):
            ghosts.append((r, canvas((bb[0], bb[1])) + canvas((bb[2], bb[3]))))
        for p in fp.pads:
            if p.net and p.net != I.GND and not p.net.startswith('unconnected'):
                fixed_pins.setdefault(p.net, []).append(canvas(fp.pad_pos(p)))
    ghosts = [(r, (g[0], g[1], g[2], g[3])) for r, g in ghosts]

    # edge blocks: pack each edge row in order, then the inboard partners
    top_y = ORIGIN[1]
    bot_y = ORIGIN[1] + SCALE * (o[3] - o[1])
    right_edge = ORIGIN[0] + SCALE * (o[2] - o[0]) - 1.0
    for row, at_top in ((V['top'], True), (V['bottom'], False)):
        prev_right = -1e9
        row_blocks = []
        for a, x in row:
            b = by_anchor.get(a)
            if not b:
                continue
            cx = max(rel_canvas(x, 0)[0] - b.aoff[0], prev_right + GAP - b.rel[0])
            cy = top_y - b.rel[1] + 1.0 if at_top else bot_y - b.rel[3] - 1.0
            b.pos, b.fixed = (cx, cy), True
            prev_right = cx + b.rel[2]
            row_blocks.append(b)
        # a row that runs past the right edge slides back, last block first
        limit = right_edge
        for b in reversed(row_blocks):
            if b.pos[0] + b.rel[2] > limit:
                b.pos = (limit - b.rel[2], b.pos[1])
            limit = b.pos[0] + b.rel[0] - GAP
    for inboard, at_top in ((V['top_inboard'], True), (V['bottom_inboard'], False)):
        stacked = {}
        for a, edge_ref in inboard.items():
            b, edge = by_anchor.get(a), by_anchor.get(edge_ref)
            if not (b and edge and edge.pos):
                continue
            edge_far = edge.pos[1] + (edge.rel[3] if at_top else edge.rel[1])
            depth = stacked.get(edge_ref, edge_far + (GAP if at_top else -GAP))
            cy = depth - b.rel[1] if at_top else depth - b.rel[3]
            # the inboard row's contacts sit on the edge row's 2.54 mm
            # lattice (place.py's row check, re-audit 2026-10-29): the pin
            # rows are moved apart, never closer, to the next multiple
            py_b = pad_rel(b, b.anchor, '1')[1]
            py_e = pad_rel(edge, edge.anchor, '1')[1]
            dy = (cy + py_b) - (edge.pos[1] + py_e)
            n = math.ceil(abs(dy) / 2.54 - 1e-6)
            cy += (n * 2.54 - abs(dy)) * (1.0 if dy >= 0 else -1.0)
            b.pos, b.fixed = (edge.pos[0] + edge.aoff[0] - b.aoff[0], cy), True
            depth = cy + (b.rel[1] if at_top else b.rel[3])
            stacked[edge_ref] = depth + (b.h + GAP if at_top else -(b.h + GAP))
    for a, (x, y) in V['inner'].items():
        b = by_anchor.get(a)
        if b:
            b.pos, b.fixed = rel_canvas(x, y), True
    # key posts (findings 51; owner 2026-10-29: place them). place.py's rule:
    # the post is one 2.54 pitch before pin 1 along the row, in line with it.
    #  - a post still in the lot whose row is on the board goes straight onto
    #    the board at that spot (real coordinates, `marker: none`: the island
    #    marker is dropped, the post becomes hand placement);
    #  - a post on the board whose row is a planned block (the L/M rows that
    #    moved to the top edge) joins that block at the same offset from the
    #    row's planned pin 1 (`merge_into` the row), so it rides with the row.
    import placement as pl
    POST_ON_BOARD, POST_WITH_ROW = {}, {}
    for slot in 'ABCDEFGHLM':
        key, pwr = f'MK{ord(slot)}', pl.POWER_REFS[slot]
        if key not in BOARD.fps or pwr not in BOARD.fps:
            continue
        axis = 0 if slot in 'LM' else 1
        b = by_anchor.get(key)
        row_b = by_anchor.get(pwr)
        row = BOARD.fps[pwr]
        row_on_board = o[0] <= row.x <= o[2] and o[1] <= row.y <= o[3]
        if b and not b.fixed and row_on_board and row_b is None:
            pin1 = next((p for p in row.pads if p.number == '1'), None)
            pin3 = next((p for p in row.pads if p.number == '3'), None)
            if pin1 is None or pin3 is None:
                continue
            p1, p3 = row.pad_pos(pin1), row.pad_pos(pin3)
            d = 1.0 if p3[axis] > p1[axis] else -1.0
            target = (p1[0] - 2.54 * d, p1[1]) if axis == 0 else (p1[0], p1[1] - 2.54 * d)
            b.pos, b.fixed, b.why = (target[0] - b.aoff[0], target[1] - b.aoff[1]), True, f'key at position 1 of {pwr} on the board'
            POST_ON_BOARD[key] = pwr
        elif b is None and row_b is not None:
            POST_WITH_ROW[key] = (pwr, axis)
    # power doors: rows against the FPGA box, the aligned block on the column
    u1 = by_anchor.get('U1')
    for side, (row, key, net, _why) in V.get('doors', DOORS).items():
        bs = [by_anchor[a] for a in row if a in by_anchor]
        if not (u1 and u1.pos and bs and net in u1.pins):
            continue
        pts = u1.pins[net]
        col = u1.pos[0] + sum(p[0] for p in pts) / len(pts)
        ub = u1.box()
        k = row.index(key)
        kb = by_anchor[key]
        kb.pos = (col - kb.aoff[0], 0.0)
        for i in range(k - 1, -1, -1):                 # leftwards from the key block
            nb, b = bs[i + 1], bs[i]
            b.pos = (nb.pos[0] + nb.rel[0] - GAP - b.rel[2], 0.0)
        for i in range(k + 1, len(bs)):                # rightwards
            pb, b = bs[i - 1], bs[i]
            b.pos = (pb.pos[0] + pb.rel[2] + GAP - b.rel[0], 0.0)
        for b in bs:
            y = ub[1] - GAP - b.rel[3] if side == 'top' else ub[3] + GAP - b.rel[1]
            b.pos, b.fixed, b.why = (b.pos[0], y), True, 'door'

    # districts: blocks set against a neighbour already placed (see the
    # 'districts' variant), in list order, each fixed once placed
    def edge_of(b, which):
        bx = b.box()
        return {'left': bx[0], 'right': bx[2], 'top': bx[1], 'bottom': bx[3],
                'cx': (bx[0] + bx[2]) / 2, 'cy': (bx[1] + bx[3]) / 2}[which]
    for anchor, spec, why in V.get('districts', []):
        b = by_anchor.get(anchor)
        if not b:
            print(f'  NOTE district: {anchor} has no block; skipped')
            continue
        xr, yr = spec['x'], spec['y']
        rx, ry = by_anchor.get(xr[1]), by_anchor.get(yr[1])
        if not (rx and rx.pos and rx.fixed and ry and ry.pos and ry.fixed):
            print(f'  NOTE district: {anchor} refers to {xr[1]}/{yr[1]}, not placed yet; skipped')
            continue
        gx = xr[2] if len(xr) > 2 else GAP
        gy = yr[2] if len(yr) > 2 else GAP
        x0 = {'right_of': lambda: edge_of(rx, 'right') + gx,
              'left_of': lambda: edge_of(rx, 'left') - gx - b.w,
              'left': lambda: edge_of(rx, 'left'),
              'right': lambda: edge_of(rx, 'right') - b.w,
              'centre': lambda: edge_of(rx, 'cx') - b.w / 2}[xr[0]]()
        y0 = {'below': lambda: edge_of(ry, 'bottom') + gy,
              'above': lambda: edge_of(ry, 'top') - gy - b.h,
              'top': lambda: edge_of(ry, 'top'),
              'bottom': lambda: edge_of(ry, 'bottom') - b.h,
              'centre': lambda: edge_of(ry, 'cy') - b.h / 2}[yr[0]]()
        b.pos, b.fixed, b.why = (x0 - b.rel[0], y0 - b.rel[1]), True, why

    # weak prior: the board centre (placement.py's group anchors assume the
    # contract's sides, which the board no longer follows)
    for b in blocks.values():
        b.prior = rel_canvas(50.0, 50.0)
        if b.pos is None:
            b.pos = b.prior

    # net weights over blocks and fixed footprints
    nets = {}
    for b in blocks.values():
        for n in b.pins:
            nets.setdefault(n, set()).add(b.label)
    weight = {}
    for n, labs in nets.items():
        k = len(labs) + (1 if n in fixed_pins else 0)
        if k >= 2:
            weight[n] = 1.0 / (k - 1)

    # solve: each free block moves to the weighted mean of the centres its
    # pins ask for
    free = [b for b in blocks.values() if not b.fixed]
    for _it in range(200):
        moved = 0.0
        for b in free:
            sx = sy = 0.0
            wsum = 0.0
            for n, w in weight.items():
                if n not in b.pins:
                    continue
                ox, oy = b.offset(n)
                for lab in nets[n]:
                    if lab == b.label:
                        continue
                    other = blocks[lab]
                    px, py = other.offset(n)
                    crit = CRITICAL.get(frozenset((b.anchor, other.anchor)))
                    wk = crit[0] if crit else w          # a critical link pulls at full strength
                    sx += wk * (other.pos[0] + px - ox)
                    sy += wk * (other.pos[1] + py - oy)
                    wsum += wk
                for fx, fy in fixed_pins.get(n, []):
                    sx += w * (fx - ox)
                    sy += w * (fy - oy)
                    wsum += w
            lam = PRIOR * max(wsum, 1.0)
            nx = (sx + lam * b.prior[0]) / (wsum + lam)
            ny = (sy + lam * b.prior[1]) / (wsum + lam)
            moved = max(moved, abs(nx - b.pos[0]) + abs(ny - b.pos[1]))
            b.pos = (nx, ny)
        if moved < 0.01:
            break

    # legalize: fixed first, then free blocks by how strongly they are wired
    def wired(b):
        # critical links first: those blocks claim their spot before others
        crit = sum(f for pair, (f, _w) in CRITICAL.items() if b.anchor in pair)
        return 100.0 * crit + sum(weight.get(n, 0.0) for n in b.pins)
    placed = []
    obstacles = [g for _r, g in ghosts]
    frame = (ORIGIN[0] + 1.0, ORIGIN[1] + 1.0, ORIGIN[0] + SCALE * (o[2] - o[0]) - 1.0,
             ORIGIN[1] + SCALE * (o[3] - o[1]) - 1.0)

    def inside(bx):
        return frame[0] <= bx[0] and frame[1] <= bx[1] and bx[2] <= frame[2] and bx[3] <= frame[3]
    outside = []
    for b in sorted(blocks.values(), key=lambda b: (not b.fixed, -wired(b), -(b.w * b.h))):
        target = b.pos
        best = None
        for must_be_inside in (True, False):
          r = 0.0
          while best is None and r < 400:
            k = max(1, int(2 * math.pi * r / 1.0)) if r else 1
            for i in range(k):
                a = 2 * math.pi * i / k
                if b.fixed:
                    cand = target                 # edge rows were packed already
                else:
                    cand = (target[0] + r * math.cos(a), target[1] + r * math.sin(a))
                bx = b.box(cand)
                if b.fixed:
                    best = cand
                    break
                if must_be_inside and not inside(bx):
                    continue
                if any(overlaps(bx, q.box(), GAP) for q in placed):
                    continue
                if any(overlaps(bx, g, GAP / 2) for g in obstacles):
                    continue
                best = cand
                break
            r += 1.0
          if best is not None:
            if not must_be_inside:
                outside.append(b.anchor)
            break
        if best is None:
            sys.exit(f'{b.anchor}: no free spot within 400 mm; nothing written')
        b.pos = best
        placed.append(b)
    for b in placed:                              # nothing may overlap, edge rows included
        for q in placed:
            if q is not b and overlaps(b.box(), q.box()):
                bb, qb = b.box(), q.box()
                sys.exit(f'{b.anchor} [{bb[0]:.1f},{bb[1]:.1f}..{bb[2]:.1f},{bb[3]:.1f}] ({getattr(b, "why", "")}) overlaps '
                         f'{q.anchor} [{qb[0]:.1f},{qb[1]:.1f}..{qb[2]:.1f},{qb[3]:.1f}] ({getattr(q, "why", "")}) in the plan; nothing written')
    if outside:
        print(f'  no room inside the frame for: {", ".join(outside)} (placed just outside it)')

    # plan: rigid move per group (turn about the box centre, then translate)
    os.makedirs(OUT_DIR, exist_ok=True)
    lines = ['# City plan written by tools/city.py; applied by tools/islands.py --city.',
             '# Per island group: the marker centre moves to (x, y) and the group turns by turn.',
             f'variant: {args.variant}', f'scale: {SCALE}', f'origin: [{ORIGIN[0]}, {ORIGIN[1]}]',
             f'outline: [{o[0]}, {o[1]}, {o[2]}, {o[3]}]', 'ghosts:']
    for r, g in sorted(ghosts, key=lambda t: I.natural(t[0])):
        lines.append(f'  {r}: [{g[0]:.2f}, {g[1]:.2f}, {g[2]:.2f}, {g[3]:.2f}]')
    lines.append('islands:')
    for b in sorted(blocks.values(), key=lambda b: I.natural(b.anchor)):
        why = 'centre' if b.anchor in V['inner'] else getattr(b, 'why', 'edge' if b.fixed else 'wired')
        rs = ''
        if b.label in reseats:
            rs = ', reseat: {' + ', '.join(f'{r}: [{d[0]:.3f}, {d[1]:.3f}]'
                                           for r, d in reseats[b.label][0].items()) + '}'
        if b.anchor in POST_ON_BOARD:
            rs += ', marker: none'
        lines.append(f'  {b.anchor}: {{from: [{b.c0[0]:.2f}, {b.c0[1]:.2f}], to: [{b.pos[0]:.2f}, {b.pos[1]:.2f}], '
                     f'turn: {b.turn}, why: "{why}"{rs}}}')
        for sl, (dxy, side, swhy, hl) in sat_info.items():
            if hl != b.label:
                continue
            sc0 = marks[sl][0]
            sc = ((sc0[0] + sc0[2]) / 2, (sc0[1] + sc0[3]) / 2)
            vx, vy = I.rot(sc[0] + dxy[0] - b.c0[0], sc[1] + dxy[1] - b.c0[1], b.turn)
            sa = sl.split()[1]
            lines.append(f'  {sa}: {{from: [{sc[0]:.2f}, {sc[1]:.2f}], to: [{b.pos[0] + vx:.2f}, {b.pos[1] + vy:.2f}], '
                         f'turn: {b.turn}, why: "satellite of {b.anchor}, {side} side: {swhy}", merge_into: {b.anchor}}}')
    for key, (pwr, axis) in sorted(POST_WITH_ROW.items()):
        rb = by_anchor[pwr]
        fp = BOARD.fps[key]
        row = BOARD.fps[pwr]
        pin1 = next((p for p in row.pads if p.number == '1'), None)
        pin3 = next((p for p in row.pads if p.number == '3'), None)
        if pin1 is None or pin3 is None:
            print(f'  NOTE {key}: row {pwr} has no pin 1/3; post not planned')
            continue
        # the row's own pads after the block's rigid move (turn about c0, then to)
        p1, p3 = row.pad_pos(pin1), row.pad_pos(pin3)
        o1 = I.rot(p1[0] - rb.c0[0], p1[1] - rb.c0[1], rb.turn)
        o3 = I.rot(p3[0] - rb.c0[0], p3[1] - rb.c0[1], rb.turn)
        d = 1.0 if o3[axis] > o1[axis] else -1.0
        tx, ty = rb.pos[0] + o1[0], rb.pos[1] + o1[1]
        if axis == 0:
            tx -= 2.54 * d
        else:
            ty -= 2.54 * d
        lines.append(f'  {key}: {{from: [{fp.x:.2f}, {fp.y:.2f}], to: [{tx:.2f}, {ty:.2f}], turn: 0.0, '
                     f'why: key at position 1 of {pwr} with the row, merge_into: {pwr}}}')
        print(f'  {key} (slot key) leaves the board to stand at position 1 of {pwr} in the plan')
    # district boxes: drawn round the finished neighbourhoods by islands.py
    # --city (city frame group), 1 mm outside their blocks
    dboxes = {}
    for name, anchors in (V.get('boxes') or {}).items():
        bs = [by_anchor[a] for a in anchors if a in by_anchor]
        if not bs:
            continue
        xs = [v for b in bs for v in (b.box()[0], b.box()[2])]
        ys = [v for b in bs for v in (b.box()[1], b.box()[3])]
        dboxes[name] = (min(xs) - 1.0, min(ys) - 1.0, max(xs) + 1.0, max(ys) + 1.0)
    if dboxes:
        lines.append('districts:')
        for name, d in dboxes.items():
            lines.append(f'  "{name}": [{d[0]:.2f}, {d[1]:.2f}, {d[2]:.2f}, {d[3]:.2f}]')
    path = os.path.join(OUT_DIR, 'plan.yaml')
    open(path, 'w').write('\n'.join(lines) + '\n')

    # preview
    xs = [ORIGIN[0] - 30, ORIGIN[0] + SCALE * 100 + 30]
    ys = [ORIGIN[1] - 30, ORIGIN[1] + SCALE * 100 + 30]
    for b in blocks.values():
        bx = b.box()
        xs += [bx[0], bx[2]]
        ys += [bx[1], bx[3]]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    k = 4.0
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{(x1-x0)*k:.0f}" height="{(y1-y0)*k:.0f}" '
           f'style="background:#fff;font-family:sans-serif">']

    def R(bx, fill, stroke, dash=False):
        return (f'<rect x="{(bx[0]-x0)*k:.1f}" y="{(bx[1]-y0)*k:.1f}" width="{(bx[2]-bx[0])*k:.1f}" '
                f'height="{(bx[3]-bx[1])*k:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"'
                + (' stroke-dasharray="8,4"' if dash else '') + '/>')
    ob = (ORIGIN[0], ORIGIN[1], ORIGIN[0] + SCALE * (o[2] - o[0]), ORIGIN[1] + SCALE * (o[3] - o[1]))
    svg.append(R(ob, 'none', '#333'))
    for r, g in ghosts:
        svg.append(R(g, '#e8e8e8', '#aaa'))
    for b in blocks.values():
        bx = b.box()
        col = '#cfe3ff' if b.fixed else '#fff3c4'
        svg.append(R(bx, col, '#06c', dash=True))
        svg.append(f'<text x="{(bx[0]-x0)*k+4:.1f}" y="{(bx[1]-y0)*k+16:.1f}" font-size="14" fill="#036">{b.anchor}</text>')
    for name, d in dboxes.items():
        svg.append(R(d, 'none', '#c40', dash=True))
        svg.append(f'<text x="{(d[0]-x0)*k+2:.1f}" y="{(d[1]-y0)*k-3:.1f}" font-size="12" fill="#c40">{name}</text>')
    svg.append('</svg>')
    prev = os.path.join(OUT_DIR, 'city.svg')
    open(prev, 'w').write('\n'.join(svg))
    print(f'{len(blocks)} blocks ({sum(1 for b in blocks.values() if b.fixed)} fixed on an edge or centre), '
          f'{len(ghosts)} ghosts; plan {os.path.relpath(path, ROOT)}, preview {os.path.relpath(prev, ROOT)}')


if __name__ == '__main__':
    main()
