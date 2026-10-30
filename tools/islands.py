#!/usr/bin/env python3
"""Island placer: lay out the unlocked passives of ONE anchor's island.

    python3 tools/islands.py --anchor U13 --island-net +2V5          # dry run
    python3 tools/islands.py --anchor U13 --island-net +2V5 --apply  # write
    python3 tools/islands.py --list-anchors                          # overview
    python3 tools/islands.py --mirror J3,J53,F9,...                  # edge strip, other side of the rail

Dry run is the default. It prints the lock table, the island membership
table, the move report and the parts left in place, renders the island
region to ref/islands/<anchor>[-<net>].svg, and writes nothing. --apply
rewrites kicad/odin.kicad_pcb, then runs `kicad-cli pcb drc` and prints the
report. One island per run, one run per commit, so any island reverts alone.

Hard rules
  - A locked footprint never moves: not its position, rotation or side.
    tools/placement.lock.yaml decides what is locked (see that file).
  - A footprint outside the island being processed never moves.
  - Single-sided assembly. Any unlocked footprint on B.Cu aborts the run.
  - The pcb is edited minimally: only the `(at ...)` lines inside the moved
    footprints change (the footprint's own, plus its pads' and texts', whose
    angles KiCad stores as absolute). Every other byte is kept.

How membership is decided (pad geometry and nets, never ref prefixes alone)
  - An anchor is a locked footprint with more than three pads, or any locked
    footprint named with --anchor.
  - A short net has at most --short-net-max-pads pads (default 3); every
    other net is wide (GND and the power rails are wide).
  - From each unlocked passive, short nets are followed outward through other
    unlocked passives until a locked footprint stops the branch; (anchor,
    anchor pad, hops) is recorded per branch. One anchor reached: that is the
    island. Several: the anchor named by the part's design.py group wins
    ('U1 PSRAM0 series termination' keeps the source damping at the driver,
    'X4 system clock' keeps R147 at the oscillator); otherwise fewest hops,
    then the anchor whose pad is closer to the passive's current position.
    The runner-up is the passive's destination (picks the side it goes on).
  - A passive reaching no anchor (rail to GND decoupling) is assigned from
    tools/design.py when its group names the chip (`U13  5V to +2V5`) or a
    pin family (`decap VCCO_16`), else to the nearest anchor with a pad on
    that rail. Within the anchor it serves the nearest unserved rail pad;
    caps beyond the pad count are flagged "extra".
  - A regulator island is a chain: a short net from an anchor pad through an
    inductor or ferrite onto a wide rail makes that rail the anchor's chain
    rail; rail-to-GND caps assigned to the anchor are chain members, ordered
    as declared in design.py, else by capacitance descending.

Placement
  - Sides N/E/S/W are the edges of the anchor's courtyard box (courtyard
    plus pad extents); a part's side is the side nearest the pad it serves.
  - Decoupling: one row per side at --ring-gap outside the anchor, sorted by
    the served pad's position along the edge, long axis perpendicular to the
    edge, rail pad toward the chip and GND pad outward (decided by pad net,
    never pad number). A row that does not fit splits into further rows
    outward, keeping the sort order. Rows never wrap around a corner.
  - Chain: axis from the regulator pad toward the consumers of the rail
    (snapped to the outward normal or to the edge direction, so passives stay
    axis-aligned), series parts on the axis with the upstream pad facing the
    previous member, caps hanging off one side with the rail pad on the axis
    and all GND pads on the outer side.
  - Signal passives: on the side facing the destination, outside that side's
    decoupling ring, pad connected to the anchor facing the anchor.
  - Collisions: against every footprint that is not moving, keepouts and the
    board outline (--edge-margin), a part is pushed outward along its side's
    normal in --part-gap steps; against another moved part it is shifted
    along the edge. A part that cannot be placed stays where it is and is
    reported with the reason. Nothing locked ever moves to make room.

Edge strips (--mirror REF,...; owner's request of 2026-10-30)
  - The listed hand-placed parts (the IO rail header first, then its slot
    power headers, fuses, caps and posts) swap sides: every position is
    mirrored across the strip's vertical centre line (or --axis X), so the
    power parts end up between the board edge and the rail header. The
    strip keeps its footprint on the board: same box, same edge margin.
  - KiCad cannot mirror a pad pattern, so rotations are kept. A part whose
    pads are symmetric about its own vertical axis (two-pad fuses and caps,
    one-row headers, posts) is mirrored exactly (a two-pad row along x by a
    half turn, pad numbers included); for the others (a two-row header) only
    the body moves and the report says so: pin 1 stays on its own corner.
  - Dry run by default, with the move report and a render; --apply writes
    only the `(at ...)` lines, verifies the file and runs DRC. One strip per
    run, one run per commit, like any island.

Slot strip lattice (--strip J3 | J5; owner's brief of 2026-10-30)
  The owner's hand placement of the A-D strip, snapped to the lattice. The
  rail header stays where the owner put it (--rail-at X,Y moves it first,
  for the second edge, whose 32 columns must share the first edge's y values
  for a shield to bridge).
  - The 2x32 rail header's 32 columns (pad y values) make four eight-column
    sections; the section's slot letter comes from its pad nets (SLOTA_...).
  - Power header line: x = the rail's inner row (the row toward the power
    side) plus two pitches toward the edge. The 1x7 female's pins sit on
    columns 1..7 of its section, pin 1 (PIN V) at column 1.
  - Key post MK<ord(letter)>: column 8 of the section, one more pitch toward
    the edge than the header line. Off the header's line on purpose: a plain
    1x8 strip cannot mate it, so the shield needs the bare hole exactly
    there. Posts of the other edge found on this side trade places with the
    incoming posts (identical GND posts; refs follow design.py).
  - AUX fuse (SMD2018): on the edge side of the header body, 0.3 mm clear of
    it, tucked above the post with 0.3 mm to its courtyard, slot pad toward
    the header.
  - Stack: the slot's caps and 1206 fuses stand in one column midway between
    the header body and the rail body, 0.3 mm apart, in pin order from the
    top (10 uF, PIN V fuse, 100 nF, 3V3 fuse, 5V fuse), the stack centred on
    the header body. Rotations are kept (the caps' GND pads point down).
"""
import argparse
import math
import json
import os
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOARD = os.path.join(ROOT, 'kicad', 'odin.kicad_pcb')
LOCKS = os.path.join(ROOT, 'tools', 'placement.lock.yaml')
RENDER_DIR = os.path.join(ROOT, 'ref', 'islands')
PROFILES = os.path.join(ROOT, 'tools', 'island_profiles.yaml')
GND = 'GND'
OPPOSITE = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}
# Parking lot for finished staged islands: a strip outside the A3 sheet, right
# of its edge (x > 420), filled like desktop icons (top-down, then next column).
# Widened from 520 to 560, then 620, on 2026-10-28: title bars, then U1 with its bulk caps.
PARK = (430.0, 10.0, 620.0, 290.0)
PARK_COL = 32.0
PARK_GAP = 3.0
MARK_LAYER = 'Cmts.User'
# Island marker: a dashed box round the parked courtyards under a solid title
# bar (label on the first line, note on the second), grouped with the parts.
MARK_MARGIN = 1.5          # box clearance round the courtyards
MARK_GAP = 1.0             # kept between one island's marker and the next
TITLE_SIZE, NOTE_SIZE = 1.2, 0.7
CHAR_W = 0.85              # stroke font advance as a fraction of the size [estimate]
BAR_H = 0.4 + TITLE_SIZE + 0.3 + NOTE_SIZE + 0.4

# ============================================================ s-expressions
_TOK = re.compile(r'\s*(?:(\()|(\))|("(?:[^"\\]|\\.)*")|([^\s()"]+))')


class Atom:
    __slots__ = ('text', 'start', 'end')

    def __init__(self, text, start, end):
        self.text, self.start, self.end = text, start, end

    @property
    def value(self):
        t = self.text
        if t.startswith('"'):
            return t[1:-1].replace('\\"', '"').replace('\\\\', '\\')
        return t

    def num(self):
        return float(self.text)


class Node:
    __slots__ = ('items', 'start', 'end')

    def __init__(self, start):
        self.items, self.start, self.end = [], start, None

    @property
    def name(self):
        if self.items and isinstance(self.items[0], Atom):
            return self.items[0].text
        return ''

    def atoms(self):
        return [i for i in self.items if isinstance(i, Atom)]

    def nodes(self):
        return [i for i in self.items if isinstance(i, Node)]

    def find(self, name):
        for i in self.items:
            if isinstance(i, Node) and i.name == name:
                return i
        return None

    def findall(self, name):
        return [i for i in self.items if isinstance(i, Node) and i.name == name]


def parse(text):
    root = Node(0)
    stack = [root]
    pos, n = 0, len(text)
    while pos < n:
        m = _TOK.match(text, pos)
        if not m or m.lastindex is None:
            break
        pos = m.end()
        if m.group(1):
            node = Node(m.start(1))
            stack[-1].items.append(node)
            stack.append(node)
        elif m.group(2):
            node = stack.pop()
            node.end = pos
            if not stack:
                raise ValueError('unbalanced s-expression')
        else:
            g = 3 if m.group(3) else 4
            stack[-1].items.append(Atom(m.group(g), m.start(g), pos))
    if len(stack) != 1:
        raise ValueError('unterminated s-expression')
    root.end = n
    return root


def fmt(v):
    s = f'{v:.6f}'.rstrip('0').rstrip('.')
    return '0' if s in ('', '-0') else s


def norm_fp_angle(a):
    a = (a + 180.0) % 360.0 - 180.0
    return 180.0 if a <= -180.0 else a


def norm_item_angle(a):
    return a % 360.0


# ============================================================ geometry
def rot(x, y, deg):
    """KiCad footprint-local to board offset (y down, as the file stores it)."""
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (x * c + y * s, -x * s + y * c)


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def bbox_of(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (min(xs), min(ys), max(xs), max(ys))


_ROLE_NAMES = None


def role_name(ref):
    """The part's short plain name from tools/roles.py ('slot L signal
    socket'), '' when unknown."""
    global _ROLE_NAMES
    if _ROLE_NAMES is None:
        import contextlib
        import io
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                import roles
            _ROLE_NAMES = {r: v[0] for r, v in roles.PART.items()}
        except Exception:                          # noqa: BLE001
            _ROLE_NAMES = {}
    return _ROLE_NAMES.get(ref, '')


def island_title(anchor_ref):
    name = role_name(anchor_ref)
    return f'island {anchor_ref}' + (f': {name}' if name else '')


def make_note(pname, nparts):
    import datetime
    return f'{pname or "generic"}, {nparts} parts, {datetime.date.today().isoformat()}'


def wrap_words(words, width_chars):
    lines, cur = [], ''
    for w in str(words).split():
        if cur and len(cur) + 1 + len(w) > width_chars:
            lines.append(cur)
            cur = w
        else:
            cur = f'{cur} {w}' if cur else w
    if cur:
        lines.append(cur)
    return lines


def marker_layout(box, label, note):
    """An island marker: the dashed box is the courtyards plus MARK_MARGIN
    (only the short label 'island U12' may widen it); above it a title bar
    with the label, then the part's plain name and the note, small and
    wrapped to the box width. Returns (x0, top, x1, y0, y1, lines) with y0
    the bar's bottom edge."""
    anchor_ref = label.split()[1] if label.startswith('island ') else ''
    x0, b0 = box[0] - MARK_MARGIN, box[1] - MARK_MARGIN
    x1 = max(box[2] + MARK_MARGIN, x0 + len(label) * TITLE_SIZE * CHAR_W + 0.8, x0 + 8.0)
    per_line = max(10, int((x1 - x0 - 0.8) / (NOTE_SIZE * CHAR_W)))
    lines = wrap_words(role_name(anchor_ref), per_line) + wrap_words(note, per_line)
    bar = 0.4 + TITLE_SIZE + 0.3 + len(lines) * NOTE_SIZE * 1.4 + 0.3
    return (x0, b0 - bar, x1, b0, box[3] + MARK_MARGIN, lines)


def marker_extent(box, label, note):
    x0, top, x1, _y0, y1, _l = marker_layout(box, label, note)
    return (x0, top, x1, y1)


def box_corners(b):
    x0, y0, x1, y1 = b
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def box_point_dist(b, p):
    x0, y0, x1, y1 = b
    dx = max(x0 - p[0], 0.0, p[0] - x1)
    dy = max(y0 - p[1], 0.0, p[1] - y1)
    return math.hypot(dx, dy)


def polys_overlap(a, b, eps=1e-6):
    """Separating-axis test for two convex polygons; touching edges pass."""
    for poly in (a, b):
        n = len(poly)
        for i in range(n):
            ex, ey = poly[(i + 1) % n][0] - poly[i][0], poly[(i + 1) % n][1] - poly[i][1]
            nx, ny = -ey, ex
            pa = [dot((nx, ny), p) for p in a]
            pb = [dot((nx, ny), p) for p in b]
            if max(pa) <= min(pb) + eps or max(pb) <= min(pa) + eps:
                return False
    return True


def poly_in_box(poly, b):
    x0, y0, x1, y1 = b
    return all(x0 <= px <= x1 and y0 <= py <= y1 for px, py in poly)


# ============================================================ board model
class Pad:
    __slots__ = ('number', 'kind', 'shape', 'lx', 'ly', 'angle', 'w', 'h',
                 'net_code', 'net', 'at_node')

    def __init__(self, node):
        atoms = node.atoms()
        self.number = atoms[1].value if len(atoms) > 1 else ''
        self.kind = atoms[2].text if len(atoms) > 2 else ''
        self.shape = atoms[3].text if len(atoms) > 3 else ''
        at = node.find('at')
        self.at_node = at
        vals = [a.num() for a in at.atoms()[1:]] if at else [0.0, 0.0]
        self.lx, self.ly = vals[0], vals[1]
        self.angle = vals[2] if len(vals) > 2 else 0.0    # absolute (board frame); absent means 0
        size = node.find('size')
        sv = [a.num() for a in size.atoms()[1:]] if size else [0.0, 0.0]
        self.w, self.h = sv[0], (sv[1] if len(sv) > 1 else sv[0])
        net = node.find('net')
        if net:
            na = net.atoms()
            self.net_code = int(na[1].text)
            self.net = na[2].value if len(na) > 2 else ''
        else:
            self.net_code, self.net = 0, ''


CRTYD_SHAPES = ('fp_line', 'fp_rect', 'fp_poly', 'fp_circle', 'fp_arc')


class Footprint:
    def __init__(self, node):
        self.node = node
        atoms = node.atoms()
        self.lib = atoms[1].value if len(atoms) > 1 else ''
        self.attr_locked = any(a.text == 'locked' for a in atoms[2:])
        lk = node.find('locked')
        if lk and len(lk.atoms()) > 1 and lk.atoms()[1].text == 'yes':
            self.attr_locked = True
        layer = node.find('layer')
        self.layer = layer.atoms()[1].value if layer else ''
        at = node.find('at')
        self.at_node = at
        vals = [a.num() for a in at.atoms()[1:]]
        self.x, self.y = vals[0], vals[1]
        self.rot = vals[2] if len(vals) > 2 else 0.0
        self.ref = self.value = ''
        self.text_at_nodes = []
        for p in node.findall('property'):
            pa = p.atoms()
            if len(pa) > 2 and pa[1].value == 'Reference':
                self.ref = pa[2].value
            elif len(pa) > 2 and pa[1].value == 'Value':
                self.value = pa[2].value
            if p.find('at'):
                self.text_at_nodes.append(p.find('at'))
        for t in node.findall('fp_text'):
            if t.find('at'):
                self.text_at_nodes.append(t.find('at'))
        self.pads = [Pad(p) for p in node.findall('pad')]
        self.crtyd = self._courtyard()
        self.box = self._effective_box()

    # -- local geometry ------------------------------------------------
    def _courtyard(self):
        """Local bbox of the F.CrtYd shapes, inflated by half their stroke
        width: KiCad's courtyard DRC uses the stroked outline."""
        pts = []
        half_w = 0.0
        for shp in self.node.nodes():
            if shp.name not in CRTYD_SHAPES:
                continue
            lay = shp.find('layer')
            if not lay or lay.atoms()[1].value not in ('F.CrtYd', 'B.CrtYd'):
                continue
            stroke = shp.find('stroke')
            if stroke and stroke.find('width'):
                half_w = max(half_w, stroke.find('width').atoms()[1].num() / 2)
            for key in ('start', 'end', 'mid'):
                k = shp.find(key)
                if k:
                    pts.append((k.atoms()[1].num(), k.atoms()[2].num()))
            ptsn = shp.find('pts')
            if ptsn:
                for xy in ptsn.findall('xy'):
                    pts.append((xy.atoms()[1].num(), xy.atoms()[2].num()))
            if shp.name == 'fp_circle':
                c, e = shp.find('center'), shp.find('end')
                if c and e:
                    cx, cy = c.atoms()[1].num(), c.atoms()[2].num()
                    r = math.hypot(e.atoms()[1].num() - cx, e.atoms()[2].num() - cy)
                    pts += [(cx - r, cy - r), (cx + r, cy + r)]
        if not pts:
            return None
        b = bbox_of(pts)
        return (b[0] - half_w, b[1] - half_w, b[2] + half_w, b[3] + half_w)

    def _pad_box(self):
        pts = []
        for p in self.pads:
            rel = (p.angle - self.rot) % 180.0
            w, h = (p.h, p.w) if abs(rel - 90.0) < 1e-6 else \
                   ((p.w, p.h) if rel < 1e-6 else (max(p.w, p.h),) * 2)
            pts += [(p.lx - w / 2, p.ly - h / 2), (p.lx + w / 2, p.ly + h / 2)]
        return bbox_of(pts) if pts else (-0.5, -0.5, 0.5, 0.5)

    def _effective_box(self):
        pb = self._pad_box()
        if self.crtyd is None:
            return (pb[0] - 0.25, pb[1] - 0.25, pb[2] + 0.25, pb[3] + 0.25)
        c = self.crtyd
        return (min(c[0], pb[0]), min(c[1], pb[1]), max(c[2], pb[2]), max(c[3], pb[3]))

    @property
    def pads_exceed_courtyard(self):
        return self.crtyd is not None and self.box != self.crtyd

    # -- board geometry ------------------------------------------------
    def pad_pos(self, pad, at=None):
        x, y, r = at if at else (self.x, self.y, self.rot)
        dx, dy = rot(pad.lx, pad.ly, r)
        return (x + dx, y + dy)

    def polygon(self, at=None):
        x, y, r = at if at else (self.x, self.y, self.rot)
        return [(x + rot(cx, cy, r)[0], y + rot(cx, cy, r)[1]) for cx, cy in box_corners(self.box)]

    def bbox(self, at=None):
        return bbox_of(self.polygon(at))

    def centre(self, at=None):
        b = self.bbox(at)
        return ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)

    def pad_by_net(self, net):
        return next((p for p in self.pads if p.net == net), None)

    def nets(self):
        return {p.net for p in self.pads if p.net and not p.net.startswith('unconnected-')}

    def prefix(self):
        m = re.match(r'[A-Za-z]+', self.ref)
        return m.group(0) if m else self.ref


class Board:
    def __init__(self, path):
        self.path = path
        self.text = open(path, encoding='utf-8').read()
        self.root = parse(self.text)
        top = self.root.items[0]
        if not isinstance(top, Node) or top.name != 'kicad_pcb':
            raise SystemExit(f'{path}: not a kicad_pcb file')
        self.top = top
        self.fps = {}
        for n in top.findall('footprint'):
            fp = Footprint(n)
            if fp.ref in self.fps:
                raise SystemExit(f'duplicate reference {fp.ref} in {path}')
            self.fps[fp.ref] = fp
        self.outline = self._outline()
        self.keepouts = self._keepouts()
        self.nets = {}
        for fp in self.fps.values():
            for p in fp.pads:
                if p.net and not p.net.startswith('unconnected-'):
                    self.nets.setdefault(p.net, []).append((fp.ref, p))

    def _outline(self):
        pts = []
        for g in self.top.nodes():
            if not g.name.startswith('gr_'):
                continue
            lay = g.find('layer')
            if not lay or lay.atoms()[1].value != 'Edge.Cuts':
                continue
            for key in ('start', 'end', 'mid'):
                k = g.find(key)
                if k:
                    pts.append((k.atoms()[1].num(), k.atoms()[2].num()))
            ptsn = g.find('pts')
            if ptsn:
                for xy in ptsn.findall('xy'):
                    pts.append((xy.atoms()[1].num(), xy.atoms()[2].num()))
            if g.name == 'gr_circle':
                c, e = g.find('center'), g.find('end')
                if c and e:
                    cx, cy = c.atoms()[1].num(), c.atoms()[2].num()
                    r = math.hypot(e.atoms()[1].num() - cx, e.atoms()[2].num() - cy)
                    pts += [(cx - r, cy - r), (cx + r, cy + r)]
        return bbox_of(pts) if pts else None

    def _keepouts(self):
        out = []
        for z in self.top.findall('zone'):
            if not z.find('keepout'):
                continue
            name = z.find('name')
            poly = z.find('polygon')
            if not poly or not poly.find('pts'):
                continue
            pts = [(xy.atoms()[1].num(), xy.atoms()[2].num())
                   for xy in poly.find('pts').findall('xy')]
            if len(pts) >= 3:
                out.append((name.atoms()[1].value if name else 'keepout', pts))
        return out

    def short(self, net, max_pads):
        return net in self.nets and len(self.nets[net]) <= max_pads

    def island_groups(self):
        """ref -> name of the 'island X' group the footprint is in."""
        by_uuid = {}
        for ref, fp in self.fps.items():
            u = fp.node.find('uuid')
            if u:
                by_uuid[u.atoms()[1].value] = ref
        out = {}
        for g in self.top.findall('group'):
            name = g.atoms()[1].value if len(g.atoms()) > 1 else ''
            mem = g.find('members')
            if name.startswith('island ') and mem:
                for a in mem.atoms()[1:]:
                    if a.value in by_uuid:
                        out[by_uuid[a.value]] = name
        return out

    def markers(self):
        """Island markers on MARK_LAYER by label ('island U13'): the outer
        rectangle and the nodes that draw it. Current markers are a group named
        after the label (box, title bar, two texts, the island's footprints);
        the first markers were a loose rectangle with the label at its
        top-left corner, and are matched by that corner (stale duplicates
        included, so a rerun clears them)."""
        by_uuid = {}
        for n in self.top.nodes():
            u = n.find('uuid')
            if u:
                by_uuid[u.atoms()[1].value] = n
        out, claimed = {}, set()
        for g in self.top.findall('group'):
            name = g.atoms()[1].value if len(g.atoms()) > 1 else ''
            if not name.startswith('island '):
                continue
            mem = g.find('members')
            nodes = [by_uuid[a.value] for a in (mem.atoms()[1:] if mem else []) if a.value in by_uuid]
            draw = [n for n in nodes if n.name in ('gr_rect', 'gr_text')]
            pts = [(k.atoms()[1].num(), k.atoms()[2].num())
                   for n in draw for key in ('start', 'end', 'at') for k in [n.find(key)] if k]
            if pts:
                out[name] = (bbox_of(pts), draw + [g])
            claimed.update(id(n) for n in draw)
        rects = [n for n in self.top.findall('gr_rect') if id(n) not in claimed
                 and n.find('layer') and n.find('layer').atoms()[1].value == MARK_LAYER]
        for t in self.top.findall('gr_text'):
            lay = t.find('layer')
            if id(t) in claimed or len(t.atoms()) < 2 or not lay or lay.atoms()[1].value != MARK_LAYER:
                continue
            label = t.atoms()[1].value.split(':')[0]
            if not label.startswith('island '):
                continue
            at = t.find('at')
            tx, ty = at.atoms()[1].num(), at.atoms()[2].num()
            mine = [r for r in rects if abs(r.find('start').atoms()[1].num() - tx) < 1e-3
                    and abs(r.find('start').atoms()[2].num() - (ty + 0.5)) < 1e-3]
            pts = [(tx, ty)] + [(k.atoms()[1].num(), k.atoms()[2].num())
                                for r in mine for key in ('start', 'end') for k in [r.find(key)]]
            prev = out.get(label)
            if prev:
                pts += [(prev[0][0], prev[0][1]), (prev[0][2], prev[0][3])]
            out[label] = (bbox_of(pts), mine + [t] + (prev[1] if prev else []))
        return out


# ============================================================ locks
def load_locks(path):
    """The anchor families from the lock file (default U J X Y SW MK)."""
    import yaml
    data = (yaml.safe_load(open(path)) or {}) if os.path.isfile(path) else {}
    return [str(f) for f in (data.get('anchor_families') or ['U', 'J', 'X', 'Y', 'SW', 'MK'])]


def load_profiles(path):
    """Layout profiles, one per IC family, each derived from the datasheet
    layout example (see ref/island-layouts.md). Keyed by a substring of the
    anchor's value."""
    import yaml
    if not os.path.isfile(path):
        return {}
    return yaml.safe_load(open(path)) or {}


def profile_for(profiles, anchor):
    for key, prof in profiles.items():
        if key in anchor.value:
            return key, prof
    return None, None


def lock_state(fp, board, island_of, anchor_ref, families, groups=None):
    """Position decides (owner, 2026-10-28): a part on the board stays where
    the owner put it; a part outside the outline may move. Parked parts
    belong to their island; ICs, connectors, crystals, switches and posts
    are anchors (they move only as the anchor of their own chunk). A part
    parked in another island whose design.py group names this run's anchor
    is reclaimed: it was parked before the group said where it belongs."""
    o = board.outline
    if o and o[0] <= fp.x <= o[2] and o[1] <= fp.y <= o[3]:
        return True, 'on the board (hand placement)'
    if fp.ref == anchor_ref:
        return True, 'anchor of this run'
    grp = island_of.get(fp.ref)
    if grp and grp != f'island {anchor_ref}':
        g = groups.get(fp.ref, ('',))[0] if groups else ''
        if anchor_ref and anchor_ref in re.findall(r'[A-Za-z]+\d+', g or ''):
            return False, f'reclaimed from {grp}: design.py group "{g.strip()}" names {anchor_ref}'
        return True, f'parked in another island\'s group'
    if fp.prefix() in families:
        return True, f'anchor family {fp.prefix()}'
    return False, 'off the board, free to move'


def print_lock_table(board, locks):
    groups = {}
    for ref, (locked, why) in sorted(locks.items(), key=lambda t: natural(t[0])):
        groups.setdefault((locked, why), []).append(ref)
    print('LOCK TABLE (position rule; anchor families from tools/placement.lock.yaml)')
    for (locked, why), refs in sorted(groups.items(), key=lambda t: (not t[0][0], t[0][1])):
        print(f'  {"locked  " if locked else "UNLOCKED"} {len(refs):3d}  {why}')
        print(wrap(refs, indent=14))
    n_unlocked = sum(1 for v in locks.values() if not v[0])
    print(f'  {len(board.fps)} footprints, {n_unlocked} unlocked, '
          f'{len(board.fps) - n_unlocked} locked')


def natural(ref):
    m = re.match(r'([A-Za-z]+)(\d+)', ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)


def wrap(words, indent=4, width=96):
    lines, cur = [], ' ' * indent
    for w in words:
        if len(cur) + len(w) + 1 > width and cur.strip():
            lines.append(cur)
            cur = ' ' * indent
        cur += w + ' '
    if cur.strip():
        lines.append(cur)
    return '\n'.join(l.rstrip() for l in lines)


# ============================================================ design.py
def load_design():
    """ref -> (group, declared index); None when design.py cannot be built."""
    try:
        from design import build
        d = build()
    except Exception as exc:                      # noqa: BLE001
        print(f'  note: tools/design.py not available ({exc}); '
              f'decoupling falls back to hand positions')
        return None, None
    groups = {p['ref']: (p['group'], i) for i, p in enumerate(d.parts)}
    syms = {p['ref']: p['sym'] for p in d.parts}
    return groups, syms


def cap_value(value):
    """'0.47uF 6.3V' -> farads; None when the value is not a capacitance."""
    m = re.match(r'\s*([\d.]+)\s*([pnumkM]?)F?\b', value or '')
    if not m:
        return None
    try:
        v = float(m.group(1))
    except ValueError:
        return None
    return v * {'p': 1e-12, 'n': 1e-9, 'u': 1e-6, 'm': 1e-3, '': 1.0,
                'k': 1e3, 'M': 1e6}[m.group(2)]


# ============================================================ membership
class Member:
    def __init__(self, fp):
        self.fp = fp
        self.ref = fp.ref
        self.anchor = None         # anchor ref
        self.pad = None            # anchor Pad served / reached
        self.hops = None
        self.via = None            # net through which the anchor is reached
        self.role = None           # 'chain' | 'decoupling' | 'signal'
        self.dest = None           # destination anchor ref, if any
        self.dest_pad = None
        self.notes = []
        self.side = None
        self.new = None            # (x, y, rot) or None
        self.reason = ''
        self.status = ''           # 'move' | 'keep' | 'fail'
        self.kind = None           # chain: 'series' | 'shunt'
        self.up_net = None         # chain series: upstream net
        self.rail = None           # decoupling/chain: the rail served
        self.extra = False

    def pos(self):
        return (self.fp.x, self.fp.y)


def follow(board, fp, locked, max_pads):
    """Hits per locked footprint reached through short nets: ref -> (hops, pad, via)."""
    hits = {}
    visited = {fp.ref}
    queue = [(fp.ref, 0)]
    while queue:
        ref, h = queue.pop(0)
        cur = board.fps[ref]
        for net in cur.nets():
            if not board.short(net, max_pads):
                continue
            for oref, opad in board.nets[net]:
                if oref == ref:
                    continue
                if locked[oref][0]:
                    cand = (h + 1, dist(fp.pos() if hasattr(fp, 'pos') else (fp.x, fp.y),
                                        board.fps[oref].pad_pos(opad)))
                    old = hits.get(oref)
                    if old is None or (old[0], old[3]) > cand:
                        hits[oref] = (h + 1, opad, net, cand[1])
                elif oref not in visited:
                    visited.add(oref)
                    queue.append((oref, h + 1))
    return hits


def group_anchor(group, board, locked):
    """The locked footprint a design.py group names, if any ('U13  5V to +2V5')."""
    for tok in re.findall(r'[A-Za-z]+\d+', group or ''):
        if tok in board.fps and locked[tok][0]:
            return tok
    return None


def extract(board, locked, anchors, design, max_pads, verbose=True):
    """Assign every unlocked footprint to an island. Returns ref -> Member."""
    groups, syms = design if design else (None, None)
    members = {}
    wide_only = []
    for ref, fp in board.fps.items():
        if locked[ref][0]:
            continue
        m = Member(fp)
        members[ref] = m
        hits = follow(board, fp, locked, max_pads)
        ahits = {a: v for a, v in hits.items() if a in anchors}
        if ahits:
            ranked = sorted(ahits.items(), key=lambda t: (t[1][0], t[1][3]))
            a, (hops, pad, via, _d) = ranked[0]
            m.anchor, m.hops, m.pad, m.via = a, hops, pad, via
            if len(ranked) > 1:
                b, (bh, bpad, bvia, _bd) = ranked[1]
                # A series part between two chips belongs where design.py
                # puts it: the group that names an anchor decides (source
                # damping sits at the driver, 'U1 PSRAM0 series termination'),
                # distance only breaks the tie when no group says anything.
                g = group_anchor(groups[ref][0], board, locked) if groups and ref in groups else None
                if g and g != a and g in ahits:
                    gh, gpad, gvia, _gd = ahits[g]
                    b, bh, bpad = a, hops, pad
                    a, hops, pad, via = g, gh, gpad, gvia
                    m.anchor, m.hops, m.pad, m.via = a, hops, pad, via
                    m.notes.append(f'design.py group says {g}')
                m.dest, m.dest_pad = b, bpad
                tie = bh == hops
                m.notes.append(f'also reaches {b} pad {bpad.number} in {bh} hop(s)'
                               + ('; tie broken by distance' if tie and not (g and g == a) else ''))
            m.role = 'signal'
        elif hits:
            stops = ', '.join(f'{a} pad {v[1].number}' for a, v in sorted(hits.items()))
            m.notes.append(f'reaches only locked non-anchor(s) {stops}; name one with --anchor')
        else:
            wide_only.append(m)

    # chain rails: anchor -> {rail: (root pad, inductor member)}
    chain_rails = {}
    for m in members.values():
        if m.anchor and m.hops == 1 and m.fp.prefix() in ('L', 'FB') and len(m.fp.pads) == 2:
            other = [n for n in m.fp.nets() if n != m.via]
            if len(other) == 1 and not board.short(other[0], max_pads) and other[0] != GND:
                chain_rails.setdefault(m.anchor, {})[other[0]] = (m.pad, m.ref)
                m.role, m.kind, m.up_net, m.rail = 'chain', 'series', m.via, other[0]

    # wide-net-only parts: design.py association first, then hand position
    served = {}                                   # (anchor, pad number) -> ref
    pending = []
    for m in wide_only:
        nets = m.fp.nets()
        rails = sorted(n for n in nets if n != GND)
        if not rails:
            m.notes.append('only GND pads; nothing to follow')
            continue
        anchor, cand_pads, how = None, None, ''
        g = groups.get(m.ref, ('', 0))[0] if groups else ''
        ga = group_anchor(g, board, locked)
        in_group = [a for a in anchors if groups and groups.get(a, ('',))[0] == g] if g else []
        if ga and ga in anchors:
            anchor, how = ga, f'design.py group "{g.strip()}"'
        elif in_group:
            anchor = min(in_group, key=lambda a: box_point_dist(board.fps[a].bbox(), m.pos()))
            how = f'design.py group "{g.strip()}" contains {anchor}'
        elif g.startswith('decap '):
            fam = g[len('decap '):].strip()
            for a in anchors:
                sym = syms.get(a) if syms else None
                if not sym:
                    continue
                nums = {num for name, lst in sym['pins'].items()
                        if name == fam or name.startswith(fam + '_')
                        for num, _unit in lst}
                if nums:
                    pads = [p for p in board.fps[a].pads if p.number in nums and p.net in rails]
                    if pads:
                        anchor, cand_pads, how = a, pads, f'design.py group "{g}" (pins {fam})'
                        break
            if anchor is None:
                # 'decap VCCO group +2V5', 'decap +1V0_MGT': the chip with most pads on the rail
                best = max(((sum(1 for p in board.fps[a].pads if p.net in rails), a) for a in anchors),
                           default=(0, None))
                if best[0]:
                    anchor, how = best[1], f'design.py group "{g}" (most pads on {"/".join(rails)})'
        if anchor is None:
            best = None
            for a in anchors:
                afp = board.fps[a]
                on_rail = any(p.net in rails for p in afp.pads) or \
                    any(r in chain_rails.get(a, {}) for r in rails)
                if not on_rail:
                    continue
                d = box_point_dist(afp.bbox(), m.pos())
                if best is None or d < best[0]:
                    best = (d, a)
            if best is None:
                m.notes.append(f'no anchor has a pad on {"/".join(rails)}; left unassigned')
                continue
            anchor, how = best[1], f'nearest anchor with a pad on {"/".join(rails)} ({best[0]:.1f} mm)'
        m.anchor, m.hops = anchor, 0
        m.notes.append(how)
        pending.append((m, rails, cand_pads))

    # pad assignment: nearest unserved rail pad, greedy by distance
    def candidates(m, rails, cand_pads):
        afp = board.fps[m.anchor]
        pads = cand_pads if cand_pads else [p for p in afp.pads if p.net in rails]
        return pads

    order = []
    for m, rails, cand_pads in pending:
        pads = candidates(m, rails, cand_pads)
        afp = board.fps[m.anchor]
        if pads:
            d = min(dist(m.pos(), afp.pad_pos(p)) for p in pads)
        else:
            d = 0.0
        order.append((d, m.ref, m, rails, cand_pads, pads))
    for _d, _r, m, rails, cand_pads, pads in sorted(order, key=lambda t: (t[0], natural(t[1]))):
        afp = board.fps[m.anchor]
        rails_here = set(rails)
        cr = chain_rails.get(m.anchor, {})
        if not pads and any(r in cr for r in rails_here):
            rail = next(r for r in rails if r in cr)
            m.role, m.kind, m.rail = 'chain', 'shunt', rail
            m.pad = cr[rail][0]
            m.notes.append(f'{rail} is the chain rail from pad {m.pad.number} via {cr[rail][1]}')
            continue
        if not pads:
            any_pads = [p for p in afp.pads if p.net in m.fp.nets()]
            if any_pads:
                m.pad = min(any_pads, key=lambda p: dist(m.pos(), afp.pad_pos(p)))
                m.role, m.rail = 'decoupling', rails[0]
                m.notes.append(f'{m.anchor} has no pad on {rails[0]}; placed at its {m.pad.net} pad {m.pad.number}')
            else:
                m.notes.append(f'{m.anchor} has no pad on {"/".join(rails)} or GND; left unassigned')
                m.anchor = None
            continue
        is_cap = m.fp.prefix() == 'C' and GND in m.fp.nets()
        if not is_cap:
            # a divider resistor or a cap between two signal nets that are just
            # above the short-net threshold: a signal part on the shared pad
            m.pad = min(pads, key=lambda p: dist(m.pos(), afp.pad_pos(p)))
            m.role, m.via = 'signal', m.pad.net
            continue
        free = [p for p in pads if (m.anchor, p.number) not in served]
        pool = free if free else pads
        m.pad = min(pool, key=lambda p: dist(m.pos(), afp.pad_pos(p)))
        m.role, m.rail = 'decoupling', m.pad.net
        if free:
            served[(m.anchor, m.pad.number)] = m.ref
        else:
            m.extra = True
            m.notes.append(f'extra: every {m.pad.net} pad of {m.anchor} already has a cap')
    return members, chain_rails


def build_chains(board, members, anchor, chain_rails, design, max_pads):
    """Ordered chain(s) for one anchor: [{root pad, rail, seq:[Member]}]."""
    groups = design[0] if design else None
    mine = [m for m in members.values() if m.anchor == anchor]
    chains, used = [], set()

    def cap_order(c):
        if groups and c.ref in groups:
            return (0, groups[c.ref][1])
        return (1, -(cap_value(c.fp.value) or 0.0))

    def stage(rail, seq):
        caps = [m for m in mine if m.ref not in used and m.role == 'chain' and m.kind == 'shunt'
                and m.rail == rail]
        caps.sort(key=cap_order)
        for c in caps:
            used.add(c.ref)
            seq.append(c)
        for f in mine:
            if f.ref in used or f.fp.prefix() not in ('L', 'FB') or len(f.fp.pads) != 2:
                continue
            if rail not in f.fp.nets():
                continue
            other = [n for n in f.fp.nets() if n != rail]
            if len(other) == 1 and other[0] != GND and not board.short(other[0], max_pads):
                used.add(f.ref)
                f.role, f.kind, f.up_net, f.rail = 'chain', 'series', rail, other[0]
                seq.append(f)
                stage(other[0], seq)

    for rail, (root_pad, lref) in sorted(chain_rails.get(anchor, {}).items()):
        if lref in used or lref not in members:
            continue
        ind = members[lref]
        used.add(lref)
        seq = [ind]
        stage(rail, seq)
        chains.append(dict(root=root_pad, rail=rail, seq=seq))
    return chains


# ============================================================ placement
SIDES = {'N': ((0.0, -1.0), (1.0, 0.0)), 'S': ((0.0, 1.0), (1.0, 0.0)),
         'W': ((-1.0, 0.0), (0.0, 1.0)), 'E': ((1.0, 0.0), (0.0, 1.0))}


def side_of(point, box):
    x0, y0, x1, y1 = box
    d = {'N': point[1] - y0, 'S': y1 - point[1], 'W': point[0] - x0, 'E': x1 - point[0]}
    return min(d, key=d.get)


def side_toward(vec):
    if abs(vec[0]) >= abs(vec[1]):
        return 'E' if vec[0] >= 0 else 'W'
    return 'S' if vec[1] >= 0 else 'N'


def value_key(value):
    """First token of a Value field, normalised: '4.7uF', '4u7', '4.7 µF' all compare equal."""
    tok = str(value).strip().split()[0] if str(value).strip() else ''
    tok = tok.lower().replace('µ', 'u').replace('μ', 'u')
    m = re.match(r'^(\d+)([a-z])(\d+)$', tok)
    if m:                                   # 4u7 -> 4.7u
        tok = f'{m.group(1)}.{m.group(3)}{m.group(2)}'
    if len(tok) > 1 and tok[-1] in 'fh' and tok[-2] in 'pnumk0123456789':
        tok = tok[:-1]                      # 4.7uF -> 4.7u, 3.3uH -> 3.3u
    return tok


def facing_rotation(fp, pad, direction):
    """Footprint rotation that makes `pad`'s offset from the origin point point
    along `direction` (board frame, y down), snapped to a multiple of 90
    degrees: a pad at a package corner (SOT-23, SOT-23-6) would otherwise
    turn the part diagonally."""
    phi_u = math.degrees(math.atan2(pad.ly, pad.lx))
    phi_v = math.degrees(math.atan2(direction[1], direction[0]))
    a = round((phi_u - phi_v) / 90.0) * 90.0
    return norm_fp_angle(a)


def extents(fp, rotation, ref_local):
    """Corner offsets of the footprint box relative to a local reference point,
    at the given rotation: list of (dx, dy)."""
    rx, ry = rot(ref_local[0], ref_local[1], rotation)
    out = []
    for cx, cy in box_corners(fp.box):
        x, y = rot(cx, cy, rotation)
        out.append((x - rx, y - ry))
    return out


def origin_from_ref(fp, rotation, ref_local, ref_board):
    rx, ry = rot(ref_local[0], ref_local[1], rotation)
    return (ref_board[0] - rx, ref_board[1] - ry)


def spread(ideals, widths, gap, lo, hi):
    """1-D packing in a fixed order: centres as close as possible to their
    ideals, spacing at least (w_i + w_j)/2 + gap, then shifted into [lo, hi].
    None when the packed row is longer than the interval."""
    n = len(ideals)
    if n == 0:
        return []

    def off(i0, i):
        return sum(widths[k] / 2 + gap + widths[k + 1] / 2 for k in range(i0, i))

    clusters = []
    for i in range(n):
        clusters.append([i, i, ideals[i]])
        while len(clusters) > 1:
            a, b = clusters[-2], clusters[-1]
            a_last = a[2] + off(a[0], a[1])
            need = widths[a[1]] / 2 + gap + widths[b[0]] / 2
            if b[2] - a_last >= need - 1e-9:
                break
            i0, i1 = a[0], b[1]
            pos = sum(ideals[i] - off(i0, i) for i in range(i0, i1 + 1)) / (i1 - i0 + 1)
            clusters[-2:] = [[i0, i1, pos]]
    centres = [0.0] * n
    for i0, i1, pos in clusters:
        for i in range(i0, i1 + 1):
            centres[i] = pos + off(i0, i)
    left, right = centres[0] - widths[0] / 2, centres[-1] + widths[-1] / 2
    if right - left > hi - lo + 1e-9:
        return None
    shift = (lo - left) if left < lo else ((hi - right) if right > hi else 0.0)
    return [c + shift for c in centres]


def grid(v, pitch=0.01):
    return round(round(v / pitch) * pitch, 3)


class Planner:
    def __init__(self, board, anchor_ref, members, chains, args, locked, profile=(None, None)):
        self.board = board
        self.profile_name, self.profile = profile
        self.anchor = board.fps[anchor_ref]
        self.abox = self.anchor.bbox()
        self.acentre = self.anchor.centre()
        self.members = members                   # island members (list)
        self.chains = chains
        self.ring_gap, self.part_gap, self.edge_margin = args.ring_gap, args.part_gap, args.edge_margin
        self.ring_depth = {s: 0.0 for s in SIDES}
        self.chain_sides, self.ring_sides = set(), set()
        moving = {m.ref for m in members}
        self.anchor_inside = board.outline is not None and poly_in_box(
            self.anchor.polygon(), board.outline)
        # Chunk mode: the anchor is still in the staging pile, so the island
        # is built as a self-contained piece to be dragged onto the board.
        # Nothing in the pile is an obstacle (its neighbours are accidents of
        # the import order); overlaps with them are only noted.
        self.chunk = not self.anchor_inside
        self.park = self.chunk and not getattr(args, 'no_park', False)
        self.lot = tuple(getattr(args, 'lot', None) or PARK)
        self.static = [(anchor_ref, self.anchor.polygon(), 'locked')] if self.chunk else [
            (ref, fp.polygon(), 'locked' if locked[ref][0] else 'stationary')
            for ref, fp in board.fps.items() if ref not in moving]
        # the anchor is not an obstacle to its own chunk: a rerun of a parked
        # island finds its own slot free again and lands back in it
        self.staged = [(ref, fp.polygon()) for ref, fp in board.fps.items()
                       if ref not in moving and ref != anchor_ref and self.chunk]
        self.placed = []                         # (ref, polygon)
        self.locks = locked
        self.inner = None
        if board.outline and self.anchor_inside:
            x0, y0, x1, y1 = board.outline
            self.inner = (x0 + self.edge_margin, y0 + self.edge_margin,
                          x1 - self.edge_margin, y1 - self.edge_margin)

    # -- helpers ---------------------------------------------------------
    def edge_interval(self, side):
        x0, y0, x1, y1 = self.abox
        return (x0, x1) if side in 'NS' else (y0, y1)

    def edge_coord(self, side):
        x0, y0, x1, y1 = self.abox
        return {'N': y0, 'S': y1, 'W': x0, 'E': x1}[side]

    def consumers(self, rail):
        pts = []
        refs = set()
        for ref, pad in self.board.nets.get(rail, []):
            if ref == self.anchor.ref or not self.locked_ref(ref):
                continue
            pts.append(self.board.fps[ref].pad_pos(pad))
            refs.add(ref)
        if not pts:
            return None, refs
        return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)), refs

    def locked_ref(self, ref):
        return self.locks[ref][0]

    # -- chain -----------------------------------------------------------
    def layout_chain(self, chain):
        """Try the chain along each allowed axis direction, most consumer-ward
        first; the first direction with no collision against a footprint that
        is not moving wins. If every direction collides, the preferred one is
        kept and resolve() reports what it could not clear."""
        root, rail = chain['root'], chain['rail']
        root_pos = self.anchor.pad_pos(root)
        side = side_of(root_pos, self.abox)
        n, e = SIDES[side]
        centroid, crefs = self.consumers(rail)
        if self.chunk:
            # no surroundings to aim at: straight out from the pad's side
            v, order = None, [n]
        elif centroid:
            v = (centroid[0] - root_pos[0], centroid[1] - root_pos[1])
            order = sorted((n, e, (-e[0], -e[1])), key=lambda c: -dot(c, v))
        else:
            v, order = None, [n, e, (-e[0], -e[1])]
        tried = []
        for d in order:
            info = self._chain_along(chain, side, d, v, crefs)
            clashes = [f'{m.ref}: {", ".join(h)}' for m in chain['seq']
                       for h in [self.collide_static(m.fp.polygon(m.new))] if h]
            if not clashes:
                if tried:
                    info['note'] = f'direction changed after collisions: {"; ".join(tried)}'
                return info
            tried.append(f'{info["direction"]} hits {"; ".join(clashes)}')
        info = self._chain_along(chain, side, order[0], v, crefs)
        info['note'] = f'every direction collides ({"; ".join(tried)}); kept {info["direction"]}'
        return info

    def _chain_along(self, chain, side, d, v, crefs):
        root, rail, seq = chain['root'], chain['rail'], chain['seq']
        root_pos = self.anchor.pad_pos(root)
        n, e = SIDES[side]
        ec = self.edge_coord(side)
        p_edge = (root_pos[0], ec) if side in 'NS' else (ec, root_pos[1])
        perp = (-d[1], d[0])
        away = (p_edge[0] - self.acentre[0], p_edge[1] - self.acentre[1])
        s_dot = dot(perp, away)
        if abs(s_dot) < 1e-6 and v is not None:
            s_dot = dot(perp, v)
        lat = perp if s_dot >= 0 else (-perp[0], -perp[1])
        dir_word = {(0.0, -1.0): 'north', (0.0, 1.0): 'south', (-1.0, 0.0): 'west', (1.0, 0.0): 'east'}
        # Series parts (inductor, ferrite) sit on the axis, upstream pad toward
        # the previous member. The rail caps sit beside the series part that
        # feeds them, as in the datasheet layout examples (TLV62569 section
        # 10, AP63300 section 12, SY8047 layout note): rail pad level with the
        # inductor's output pad, GND pad toward the chip's ground side, so the
        # block stays compact and every GND return is short.
        s = 0.0
        lat_min = 0.0
        plan = []
        series_out, lat_cursor, last_series = None, 0.0, None
        for m in seq:
            fp = m.fp
            if m.kind == 'series':
                up = fp.pad_by_net(m.up_net) or fp.pads[0]
                down = next((p for p in fp.pads if p is not up), up)
                rotation = facing_rotation(fp, up, (-d[0], -d[1]))
                ref_local = ((up.lx + down.lx) / 2, (up.ly + down.ly) / 2)
                ext = extents(fp, rotation, ref_local)
                along = [dot(c, d) for c in ext]
                lateral = [dot(c, lat) for c in ext]
                s_ref = s - min(along)
                s = s_ref + max(along) + self.part_gap
                lat_min = min(lat_min, min(lateral))
                dv = rot(down.lx - ref_local[0], down.ly - ref_local[1], rotation)
                series_out, lat_cursor, last_series = s_ref + dot(dv, d), max(lateral), m
                words = f'series {fp.prefix()} in the {rail} chain, {m.up_net} pad toward the previous member'
                plan.append((m, rotation, ref_local, s_ref, 0.0, words))
            else:
                gpad = fp.pad_by_net(GND)
                rpad = fp.pad_by_net(m.rail) or next(p for p in fp.pads if p is not gpad)
                if gpad is None:
                    gpad = next(p for p in fp.pads if p is not rpad)
                rotation = facing_rotation(fp, gpad, (-d[0], -d[1]))
                ref_local = (rpad.lx, rpad.ly)
                ext = extents(fp, rotation, ref_local)
                lateral = [dot(c, lat) for c in ext]
                lat_ref = lat_cursor + self.part_gap - min(lateral)
                lat_cursor = lat_ref + max(lateral)
                s_ref = series_out if series_out is not None else s - min(dot(c, d) for c in ext)
                beside = f'beside {last_series.ref}' if last_series else 'at the chain start'
                words = (f'{m.rail} cap {beside}, {m.rail} pad level with its output pad, '
                         f'GND pad toward {self.anchor.ref}')
                plan.append((m, rotation, ref_local, s_ref, lat_ref, words))
        offset = self.ring_gap + (-lat_min if abs(dot(d, n)) < 0.5 else 0.0)
        a0 = (p_edge[0] + n[0] * offset, p_edge[1] + n[1] * offset)
        depth = 0.0
        for i, (m, rotation, ref_local, s_ref, lat_ref, words) in enumerate(plan):
            rb = (a0[0] + d[0] * s_ref + lat[0] * lat_ref, a0[1] + d[1] * s_ref + lat[1] * lat_ref)
            ox, oy = origin_from_ref(m.fp, rotation, ref_local, rb)
            m.new = (grid(ox), grid(oy), rotation)
            m.side = side
            m.reason = (f'{words}; chain from {self.anchor.ref} pad {root.number} ({root.net}) '
                        f'runs {dir_word.get(d, "?")} along the {side} side, position {i + 1} of {len(plan)}')
            corners = m.fp.polygon(m.new)
            depth = max(depth, max(dot((cx - p_edge[0], cy - p_edge[1]), n) for cx, cy in corners))
            # a cap beside the inductor also occupies the flank it hangs over
            cx, cy = m.fp.centre(m.new)
            for fs, (fn, _fe) in SIDES.items():
                fec = self.edge_coord(fs)
                if dot((cx, cy), fn) - fec * (abs(fn[0]) + abs(fn[1])) > 0 and fs != side:
                    reach = max(dot((px, py), fn) for px, py in corners) - fec * (abs(fn[0]) + abs(fn[1]))
                    self.ring_depth[fs] = max(self.ring_depth[fs], reach)
                    self.chain_sides.add(fs)
        self.ring_depth[side] = max(self.ring_depth[side], depth)
        return dict(side=side, direction=dir_word.get(d, '?'), consumers=sorted(crefs))

    # -- rows along one side ---------------------------------------------
    def prepare(self, side, m, inward, direction=None, ideal=None):
        """Rotation and rotated extents of one part whose `inward` pad must
        face the anchor across `side` (or point along `direction`)."""
        n, e = SIDES[side]
        rotation = facing_rotation(m.fp, inward, direction or (-n[0], -n[1]))
        ext = extents(m.fp, rotation, (0.0, 0.0))
        along = [dot(c, e) for c in ext]
        depth = [dot(c, n) for c in ext]
        return dict(m=m, rot=rotation, w=max(along) - min(along),
                    d_min=min(depth), d_max=max(depth),
                    ideal=dot(self.anchor.pad_pos(m.pad), e) if ideal is None else ideal,
                    a_mid=(max(along) + min(along)) / 2)

    def split_rows(self, prepared, lo, hi):
        """Sorted parts into the fewest rows that fit between the corners,
        consecutive runs so neighbours stay neighbours. A single part wider
        than the side is centred on it and flagged."""
        nrows = 1
        while True:
            rows = []
            size = -(-len(prepared) // nrows)
            chunks = [prepared[i:i + size] for i in range(0, len(prepared), size)]
            ok = True
            for ch in chunks:
                centres = spread([p['ideal'] for p in ch], [p['w'] for p in ch], self.part_gap, lo, hi)
                overhang = False
                if centres is None:
                    if len(ch) > 1:
                        ok = False
                        break
                    overhang = True
                    centres = [(lo + hi) / 2]
                rows.append((ch, centres, overhang))
            if ok:
                return rows
            nrows += 1

    def layout_rows(self, side, prepared, label, beside_chain=False, bounded=True, start=None, overhang=0.0, gap=None):
        """Place prepared parts in rows outside everything already on `side`.
        With beside_chain, a side that only holds a chain is treated as free:
        the parts start at ring gap and the collision pass slides them along
        the edge past the chain, so a pull-down ends up next to its pin.
        `start` is an explicit depth to stack beyond (a profile rule placed
        outside another rule's parts). Unbounded rows (folded signal parts on
        a flank) may pass the corners."""
        n, e = SIDES[side]
        lo, hi = self.edge_interval(side) if bounded else (-1e9, 1e9)
        if bounded and overhang:
            lo, hi = lo - overhang, hi + overhang      # a profile rule may let a row pass the corners a little
        ec = self.edge_coord(side)
        prepared.sort(key=lambda p: (p['ideal'], natural(p['m'].ref)))
        rows = self.split_rows(prepared, lo, hi)
        depth_used = 0.0 if (beside_chain and side in self.chain_sides
                             and side not in self.ring_sides) else self.ring_depth[side]
        if start is not None:
            depth_used = start
        ring_gap = self.ring_gap if gap is None else gap
        offset = depth_used + ring_gap
        total = len(prepared)
        k = 0
        for ri, (ch, centres, overhang) in enumerate(rows):
            depth = max(p['d_max'] - p['d_min'] for p in ch)
            for p, c in zip(ch, centres):
                m = p['m']
                k += 1
                normal_c = offset + (-p['d_min'])
                centre_along = c - p['a_mid']
                ox = ec * abs(n[0]) + n[0] * normal_c + e[0] * centre_along
                oy = ec * abs(n[1]) + n[1] * normal_c + e[1] * centre_along
                m.new = (grid(ox), grid(oy), p['rot'])
                m.side = side
                m.reason = label(m, ri + 1, k, total)
                if overhang:
                    m.notes.append(f'wider than the {side} side ({hi - lo:.2f} mm); overhangs the corners')
            offset += depth + ring_gap
        self.ring_depth[side] = max(self.ring_depth[side], offset - ring_gap)

    def outer_depth(self, side, m):
        """How far the placed part reaches out from the anchor edge on `side`."""
        n, _e = SIDES[side]
        ec = self.edge_coord(side)
        base = ec * (n[0] * abs(n[0]) + n[1] * abs(n[1]))
        return max(dot(c, n) for c in m.fp.polygon(m.new)) - base

    # -- decoupling ring -------------------------------------------------
    def layout_ring(self, side, caps):
        n, e = SIDES[side]
        prepared = []
        for m in caps:
            rail_pad = m.fp.pad_by_net(m.pad.net) or m.fp.pads[0]
            gnd_near = None
            if self.chains and m.fp.pad_by_net(GND):
                # regulator input cap: a GND pin next to the rail pin on the same
                # side lets the cap lie along the edge, pad over pad (datasheet
                # layout examples put CIN across VIN and GND)
                rp = self.anchor.pad_pos(m.pad)
                cands = [p for p in self.anchor.pads if p.net == GND and p is not m.pad
                         and side_of(self.anchor.pad_pos(p), self.abox) == side
                         and dist(self.anchor.pad_pos(p), rp) <= 1.5]
                if cands:
                    gnd_near = min(cands, key=lambda p: dist(self.anchor.pad_pos(p), rp))
            if gnd_near:
                gp = self.anchor.pad_pos(gnd_near)
                rp = self.anchor.pad_pos(m.pad)
                along_dir = e if dot((rp[0] - gp[0], rp[1] - gp[1]), e) >= 0 else (-e[0], -e[1])
                prepared.append(self.prepare(side, m, rail_pad, direction=along_dir,
                                             ideal=dot(((rp[0] + gp[0]) / 2, (rp[1] + gp[1]) / 2), e)))
                m.notes.append(f'lies along the edge across pads {m.pad.number} and {gnd_near.number} (GND)')
            else:
                prepared.append(self.prepare(side, m, rail_pad))

        def label(m, row, k, total):
            return (f'decoupling cap for {self.anchor.ref} pad {m.pad.number} ({m.pad.net}), '
                    f'{side} ring row {row}, position {k} of {total}')
        # a side that already holds a chain or profile block is free for the
        # ring: the caps belong at their pins, beside the block, not outside it
        self.layout_rows(side, prepared, label, beside_chain=True)

    # -- signal passives -------------------------------------------------
    def flank_of(self, side, pad):
        """The side adjacent to the corner of `side` nearest `pad`."""
        p = self.anchor.pad_pos(pad)
        if side in 'NS':
            return 'W' if p[0] < self.acentre[0] else 'E'
        return 'N' if p[1] < self.acentre[1] else 'S'

    def layout_signals(self, side, parts):
        def label(m, row, k, total):
            toward = f', toward {m.dest}' if m.dest else ''
            return (f'signal part on {self.anchor.ref} pad {m.pad.number} ({m.pad.net}) via {m.via}, '
                    f'{m.side} side outside the ring{toward}, row {row}, position {k} of {total}')

        def inward(m):
            return (m.fp.pad_by_net(m.via) if m.via else None) or m.fp.pads[0]

        if side in self.ring_sides and side not in self.chain_sides:
            # the pins on this side already carry their caps: fold the signal
            # parts onto the flank next to their pin, like the FB divider in
            # the regulator layout examples; only while the folded row stays
            # level with the IC, a longer row belongs outside the ring instead
            by_flank = {}
            for m in parts:
                by_flank.setdefault(self.flank_of(side, m.pad), []).append(m)
            stay = []
            for flank, group in by_flank.items():
                prepared = [self.prepare(flank, m, inward(m)) for m in group]
                lo, hi = self.edge_interval(flank)
                need = sum(p['w'] for p in prepared) + self.part_gap * (len(prepared) - 1)
                if need > hi - lo:
                    for m in group:
                        m.notes.append(f'{len(group)} parts do not fit level with the IC on the {flank} flank; row outside the {side} ring')
                    stay.extend(group)
                    continue
                for m in group:
                    m.notes.append(f'folded from the {side} side onto the {flank} flank next to pad {m.pad.number}')
                # level with the IC means at ring gap whatever else the flank
                # holds further along; collisions slide the part along the edge
                self.layout_rows(flank, prepared, label, beside_chain=True, bounded=False, start=0.0)
            parts = stay
            if not parts:
                return
        prepared = [self.prepare(side, m, inward(m)) for m in parts]
        self.layout_rows(side, prepared, label, beside_chain=True)

    # -- collisions ------------------------------------------------------
    def collide_static(self, poly):
        hits = []
        for ref, spoly, kind in self.static:
            if polys_overlap(poly, spoly):
                hits.append(f'{kind} {ref}')
        for name, kpoly in self.board.keepouts:
            if polys_overlap(poly, kpoly):
                hits.append(f'keepout {name}')
        if self.inner and not poly_in_box(poly, self.inner):
            hits.append(f'board edge (margin {self.edge_margin} mm)')
        return hits

    def collide_moved(self, poly, me):
        return [ref for ref, ppoly in self.placed if ref != me and polys_overlap(poly, ppoly)]

    def resolve(self, m, max_steps=40):
        if m.new is None:
            return
        n, e = SIDES[m.side]
        x, y, r = m.new
        step = self.part_gap
        pushed = shifted = 0
        for _round in range(6):
            poly = m.fp.polygon((x, y, r))
            hits = self.collide_static(poly)
            k = 0
            while hits and k < max_steps:
                x, y = x + n[0] * step, y + n[1] * step
                k += 1
                poly = m.fp.polygon((x, y, r))
                hits = self.collide_static(poly)
            pushed += k
            if hits:
                m.status = 'fail'
                m.reason += f'; NOT PLACED: still colliding with {", ".join(hits)} after pushing {k * step:.1f} mm outward'
                m.new = None
                return
            mh = self.collide_moved(poly, m.ref)
            if not mh:
                break
            # shift along the edge, alternating sides with growing amplitude
            found = False
            for k in range(1, max_steps + 1):
                for sgn in (1, -1):
                    tx, ty = x + e[0] * step * k * sgn, y + e[1] * step * k * sgn
                    poly = m.fp.polygon((tx, ty, r))
                    if not self.collide_moved(poly, m.ref) and not self.collide_static(poly):
                        x, y, found, shifted = tx, ty, True, shifted + k
                        break
                if found:
                    break
            if not found:
                m.status = 'fail'
                m.reason += f'; NOT PLACED: overlaps moved part(s) {", ".join(mh)} and no free slot along the edge'
                m.new = None
                return
        m.new = (grid(x), grid(y), r)
        if pushed:
            m.reason += f'; pushed {pushed * step:.1f} mm outward to clear a collision'
        if shifted:
            m.reason += f'; shifted {shifted * step:.1f} mm along the edge to clear a moved part'
        self.placed.append((m.ref, m.fp.polygon(m.new)))

    def dir_side(self, spec, figure_rotation=0.0):
        """Board-frame side letter for a profile `dir`."""
        if spec in ('inboard', 'outboard'):
            x0, y0, x1, y1 = self.abox
            long_sides = 'NS' if (x1 - x0) >= (y1 - y0) else 'EW'
            o = self.board.outline
            if o and not self.chunk:
                c = ((o[0] + o[2]) / 2 - self.acentre[0], (o[1] + o[3]) / 2 - self.acentre[1])
            else:
                c = (0.0, 1.0) if long_sides == 'NS' else (1.0, 0.0)   # a chunk: S or E
            best = max(long_sides, key=lambda k: dot(SIDES[k][0], c))
            return best if spec == 'inboard' else OPPOSITE[best]
        v = {'N': (0.0, -1.0), 'S': (0.0, 1.0), 'W': (-1.0, 0.0), 'E': (1.0, 0.0)}[spec]
        v = rot(v[0], v[1], self.anchor.rot - figure_rotation)
        return side_toward(v)

    # -- datasheet profile ------------------------------------------------
    def apply_profile(self):
        """Place the members a profile rule matches. Rules run in order; a
        member takes the first rule that matches it. Returns the matched refs.
        match keys: prefix, pin ROLE (a pad on that pin's net), cap_between
        [ROLE, ROLE] (a capacitor) or between [ROLE, ROLE] (any two-net part),
        with ROLE also OUT (the chain rail) or GND.
        place keys: side ROLE (row outside the side holding that pin, the
        pad on the pin's net facing it), flank ROLE / flank opposite ROLE
        (row on the flank next to that pin's corner, level with the IC),
        face {NET: direction} (the pad on that net, NET a pin role, OUT or
        GND, points inward, outward, N, E, S or W; this also sets whether the
        part lies across or along the edge), overhang MM (a side row may pass
        the corners by that much, for small packages), at pin (a flank part
        sits at the pin's corner, not mid-flank). Profile key figure_rotation: the
        footprint rotation at which it looks like the datasheet figure, so the
        figure's N/E/S/W can be used as they are (TSOT26 at 0 is Figure 39
        turned by 180)."""
        prof = self.profile
        roles = {}
        for role, num in (prof.get('pins') or {}).items():
            pad = next((p for p in self.anchor.pads if p.number == str(num)), None)
            if pad is None:
                raise SystemExit(f'profile {self.profile_name}: pin {num} ({role}) is not a pad of {self.anchor.ref}')
            roles[role] = pad
        out_rail = self.chains[0]['rail'] if self.chains else None

        def net_of(role):
            if role == 'OUT':
                return out_rail
            if role == 'GND':
                return GND
            if role not in roles:
                raise SystemExit(f'profile {self.profile_name}: unknown pin role {role}')
            return roles[role].net

        def facing(m, side_, pl, pin):
            """(pad, direction) that orients one part under a rule."""
            n_, _e = SIDES[side_]
            for role, d in (pl.get('face') or {}).items():
                pad = m.fp.pad_by_net(net_of(role))
                if pad is None:
                    continue
                # N/E/S/W are in the chip's own frame, as drawn in the datasheet
                # figure at rotation 0; turn them with the anchor
                vec = {'inward': (-n_[0], -n_[1]), 'outward': n_,
                       'N': (0.0, -1.0), 'S': (0.0, 1.0), 'W': (-1.0, 0.0), 'E': (1.0, 0.0)}[d]
                if d in 'NESW':
                    # figure_rotation: the footprint at that rotation looks like
                    # the datasheet figure, so figure directions turn by it first
                    vec = rot(vec[0], vec[1], self.anchor.rot - float(prof.get('figure_rotation') or 0))
                return pad, vec
            return m.fp.pad_by_net(pin.net) or m.fp.pads[0], (-n_[0], -n_[1])

        matched = {}
        rules = prof.get('rules') or []
        for idx, rule in enumerate(rules):
            mt = rule.get('match') or {}
            for m in self.members:
                if m.ref in matched:
                    continue
                nets = m.fp.nets()
                ok = 'prefix' not in mt or m.fp.prefix() == mt['prefix']
                if ok and 'pin' in mt:
                    ok = net_of(mt['pin']) in nets
                if ok and 'cap_between' in mt:
                    a, b = mt['cap_between']
                    ok = m.fp.prefix() == 'C' and nets == {net_of(a), net_of(b)}
                if ok and 'between' in mt:
                    a, b = mt['between']
                    ok = nets == {net_of(a), net_of(b)}
                if ok and 'value' in mt:
                    ok = value_key(m.fp.value) == value_key(str(mt['value']))
                if ok:
                    matched[m.ref] = idx
        rule_outer = {}
        for idx, rule in enumerate(rules):
            group = [m for m in self.members if matched.get(m.ref) == idx]
            if not group:
                continue
            pl = rule.get('place') or {}
            name = rule.get('name', f'rule {idx + 1}')
            start = None
            if 'outside' in pl:
                if pl['outside'] not in rule_outer:
                    raise SystemExit(f'profile {self.profile_name}, {name}: outside: {pl["outside"]!r} '
                                     f'names no earlier rule that placed a part')
                start = rule_outer[pl['outside']]
            role_key = pl.get('side') or (str(pl['flank']).split()[-1] if 'flank' in pl else None)
            role_pad = roles.get(role_key) if role_key else None
            if role_pad is not None:
                # the rule's part owns the role pin: a ring cap that took it by
                # distance swaps pads with it so each pin keeps one cap
                for m in group:
                    if m.pad is None or m.pad is role_pad or m.pad.net != role_pad.net:
                        continue
                    other = next((o for o in self.members if o.ref not in matched
                                  and o.pad is role_pad), None)
                    if other is not None:
                        other.pad, m.pad = m.pad, role_pad
                        other.notes.append(f'pad {role_pad.number} goes to {m.ref} ({name}); takes pad {other.pad.number}')
                        m.notes.append(f'takes pad {role_pad.number} from {other.ref}')
            if 'dir' in pl:
                # dir: a chip-frame side (N E S W, as in the figure) or the long
                # side facing the board centre (inboard) or away (outboard);
                # each part sits at its own pin along that side
                side = self.dir_side(str(pl['dir']), float(prof.get('figure_rotation') or 0))
                prepared = []
                for m in group:
                    own = m.pad if m.pad is not None and m.pad in self.anchor.pads else None
                    ref_pt = self.anchor.pad_pos(own) if own else self.acentre
                    fpad, direction = facing(m, side, pl, own or self.anchor.pads[0])
                    if own is not None and not (pl.get('face')):
                        fpad = m.fp.pad_by_net(own.net) or fpad
                    if pl.get('lie') == 'along':
                        # the part lies lengthwise along the edge, its pin-net pad
                        # toward the low end of the edge
                        e_ = SIDES[side][1]
                        direction = (-e_[0], -e_[1])
                    prepared.append(self.prepare(side, m, fpad, direction=direction,
                                                 ideal=dot(ref_pt, SIDES[side][1])))
                    m.pad, m.via = m.pad or own, m.via or (own.net if own else None)
                where = f'{side} side ({pl["dir"]}), each part at its own pin'
            elif 'side' in pl:
                pad = roles[pl['side']]
                side = side_of(self.anchor.pad_pos(pad), self.abox)
                prepared = []
                for m in group:
                    fpad, direction = facing(m, side, pl, pad)
                    prepared.append(self.prepare(side, m, fpad, direction=direction,
                                                 ideal=dot(self.anchor.pad_pos(pad), SIDES[side][1])))
                    m.pad, m.via = m.pad or pad, m.via or pad.net
                where = f'{side} side at pin {pad.number} ({pad.net})'
            elif 'flank' in pl:
                spec = str(pl['flank']).split()
                pad = roles[spec[-1]]
                base = side_of(self.anchor.pad_pos(pad), self.abox)
                flank = self.flank_of(base, pad)
                if spec[0] == 'opposite':
                    flank = OPPOSITE[flank]
                side = flank
                prepared = []
                for m in group:
                    fpad, direction = facing(m, flank, pl, pad)
                    # at: pin puts the part at the pin's own corner of the flank
                    # instead of the flank's middle
                    anchor_pt = self.anchor.pad_pos(pad) if pl.get('at') == 'pin' else self.acentre
                    prepared.append(self.prepare(flank, m, fpad, direction=direction,
                                                 ideal=dot(anchor_pt, SIDES[flank][1])))
                    m.pad = m.pad or pad
                where = (f'{flank} flank at the corner of pin {pad.number} ({pad.net}), level with the IC'
                         if pl.get('at') == 'pin' else
                         f'{flank} flank next to pin {pad.number} ({pad.net}), level with the IC')
            else:
                raise SystemExit(f'profile {self.profile_name}, {name}: place needs side or flank')

            face_txt = ', '.join(f'{r} pad {d}' for r, d in (pl.get('face') or {}).items())

            def label(m, row, k, total, name=name, where=where, face_txt=face_txt):
                return (f'profile {self.profile_name}, {name}: {where}'
                        + (f', {face_txt}' if face_txt else '') + f', row {row}, position {k} of {total}')
            self.layout_rows(side, prepared, label, beside_chain=True, bounded='flank' not in pl,
                             start=start, overhang=float(pl.get('overhang') or 0.0),
                             gap=float(pl['gap']) if 'gap' in pl else None)
            self.chain_sides.add(side)          # later rules on this side slide beside, not beyond
            for m in group:
                if not m.role:
                    m.role = 'signal'
                self.resolve(m)
            placed = [m for m in group if m.new]
            if placed:
                rule_outer[name] = max(self.outer_depth(side, m) for m in placed)
        return set(matched)

    # -- drive -----------------------------------------------------------
    def run_extend(self, keep):
        """--extend: the parts already in this island's group keep their
        place (as reviewed); only the new members are laid out, outside them,
        and the whole chunk then moves as one body to a free lot slot."""
        kept = [m for m in self.members if m.ref in keep]
        new = [m for m in self.members if m.ref not in keep]
        for m in kept:
            m.new = (m.fp.x, m.fp.y, m.fp.rot)
            m.reason = 'kept as reviewed (--extend)'
            m.role = m.role or 'kept'
            self.placed.append((m.ref, m.fp.polygon(m.new)))
            c = m.fp.centre()
            side = side_of(c, self.abox)
            self.ring_depth[side] = max(self.ring_depth[side], self.outer_depth(side, m))
        everyone = self.members
        self.members = new
        self.chains = [dict(ch, seq=[m for m in ch['seq'] if m.ref not in keep]) for ch in self.chains]
        self.chains = [ch for ch in self.chains if ch['seq']]
        info = self.run(final=False)
        self.members = everyone
        if self.chunk:
            self.displace_chunk(info)
        self.verdict()
        return info

    def run(self, final=True):
        info = {'chains': []}
        in_chain = set()
        matched = self.apply_profile() if self.profile else set()
        info['profile_matched'] = sorted(matched, key=natural)
        for ch in self.chains:
            ch = dict(ch, seq=[m for m in ch['seq'] if m.ref not in matched])
            if not ch['seq']:
                continue
            chinfo = self.layout_chain(ch)
            info['chains'].append((ch, chinfo))
            self.chain_sides.add(chinfo['side'])
            in_chain.update(m.ref for m in ch['seq'])
            for m in ch['seq']:
                self.resolve(m)
        decaps = [m for m in self.members if m.role == 'decoupling' and m.pad is not None
                  and m.ref not in matched]
        by_side = {}
        for m in decaps:
            by_side.setdefault(side_of(self.anchor.pad_pos(m.pad), self.abox), []).append(m)
        for side in 'NESW':
            if side in by_side:
                self.layout_ring(side, by_side[side])
                self.ring_sides.add(side)
                for m in sorted(by_side[side], key=lambda m: natural(m.ref)):
                    self.resolve(m)
        signals = [m for m in self.members if m.role == 'signal' and m.pad is not None
                   and m.ref not in matched]
        sig_side = {}
        for m in signals:
            if m.dest and m.dest in self.board.fps and not self.chunk:
                dc = self.board.fps[m.dest].centre()
                side = side_toward((dc[0] - self.acentre[0], dc[1] - self.acentre[1]))
            else:
                side = side_of(self.anchor.pad_pos(m.pad), self.abox)
            sig_side.setdefault(side, []).append(m)
        for side in 'NESW':
            if side in sig_side:
                self.layout_signals(side, sig_side[side])
                for m in sig_side[side]:
                    self.resolve(m)
        if not final:
            return info
        if self.chunk:
            self.displace_chunk(info)        # before the keep/move verdict: a shift moves everything
        self.verdict()
        return info

    def verdict(self):
        for m in self.members:
            if m.status == 'fail':
                continue
            if m.new is None:
                m.status = 'keep'
                if not m.reason:
                    m.reason = 'no placement rule applies'
            elif (abs(m.new[0] - m.fp.x) < 0.005 and abs(m.new[1] - m.fp.y) < 0.005
                  and abs(norm_fp_angle(m.new[2] - m.fp.rot)) < 0.01):
                m.status = 'keep'
                m.reason = 'already in place; ' + m.reason
            else:
                m.status = 'move'

    def keep_layout(self, snapshot=None):
        """No layout rules at all. --repark: every member keeps its place
        relative to the anchor and the chunk moves as one body to its lot slot
        (a re-park never re-lays an island out: the reviewed layout stays).
        --revert SNAP: every member and the anchor go back to where a
        check_positions.py snapshot has them (the undo of an apply)."""
        info = {'chains': [], 'profile_matched': []}
        snap = json.load(open(snapshot)) if snapshot else None
        for m in self.members:
            if snap:
                rec = snap.get(m.ref)
                if rec is None:
                    m.status, m.reason = 'fail', f'not in the snapshot {os.path.relpath(snapshot, ROOT)}'
                    continue
                m.new = (rec['x_nm'] / 1e6, rec['y_nm'] / 1e6, rec['rot_deg'])
                m.reason = 'back where the snapshot has it'
            else:
                m.new = (m.fp.x, m.fp.y, m.fp.rot)
                m.reason = 'layout kept as reviewed'
            m.role = m.role or 'kept'
        if snap:
            rec = snap[self.anchor.ref]
            am = Member(self.anchor)
            am.anchor, am.role, am.status = self.anchor.ref, 'anchor', 'move'
            am.new = (rec['x_nm'] / 1e6, rec['y_nm'] / 1e6, rec['rot_deg'])
            am.reason = 'anchor back where the snapshot has it'
            moved = [m for m in self.members if m.new]
            self.members.append(am)
            polys = [self.anchor.polygon(am.new)] + [m.fp.polygon(m.new) for m in moved]
            info['chunk_box'] = bbox_of([p for poly in polys for p in poly])
            info['chunk_refs'] = [self.anchor.ref] + sorted((m.ref for m in moved), key=natural)
            info['chunk_overlaps'] = []
        else:
            self.displace_chunk(info)
        self.verdict()
        return info

    def displace_chunk(self, info, margin=1.0, step=1.0, reach=200.0):
        """Move the whole chunk, anchor included, to its parking slot (or,
        with --no-park, to the nearest free spot) so it overlaps nothing. The
        anchor is locked for on-board work; in the pile the owner asked for
        finished pieces to sit together, clear of the mess, which only the
        anchor moving along can give."""
        moved = [m for m in self.members if m.new]
        polys = [self.anchor.polygon()] + [m.fp.polygon(m.new) for m in moved]
        box = bbox_of([p for poly in polys for p in poly])
        others = [bb for ref, poly in self.staged for bb in [bbox_of(poly)]]
        outline = self.board.outline
        # other islands' markers (box plus title bar) are obstacles too, so a
        # small chunk cannot slip into the empty corner of a bigger island's box
        label = f'island {self.anchor.ref}'
        note = make_note(self.profile_name, 1 + len(moved))
        marks = [ext for lab, (ext, _) in self.board.markers().items() if lab != label]

        def free(dx, dy, margin=margin):
            b = (box[0] + dx - margin, box[1] + dy - margin, box[2] + dx + margin, box[3] + dy + margin)
            if outline and not (b[2] < outline[0] or b[0] > outline[2] or b[3] < outline[1] or b[1] > outline[3]):
                return False
            if not all(b[2] < o[0] or b[0] > o[2] or b[3] < o[1] or b[1] > o[3] for o in others):
                return False
            e = marker_extent((box[0] + dx, box[1] + dy, box[2] + dx, box[3] + dy), label, note)
            e = (e[0] - MARK_GAP, e[1] - MARK_GAP, e[2] + MARK_GAP, e[3] + MARK_GAP)
            return all(e[2] < o[0] or e[0] > o[2] or e[3] < o[1] or e[1] > o[3] for o in marks)

        best = None
        if self.park:
            ext = marker_extent(box, label, note)
            lead_x, lead_y = box[0] - ext[0], box[1] - ext[1]     # marker beyond the courtyards, left and top
            mw, mh = ext[2] - ext[0], ext[3] - ext[1]
            lot = self.lot
            x = lot[0] + lead_x
            while x - lead_x + mw <= lot[2] and best is None:
                y = lot[1] + lead_y
                while y - lead_y + mh <= lot[3]:
                    dx, dy = x - box[0], y - box[1]
                    if free(dx, dy, PARK_GAP):
                        best = (grid(dx), grid(dy))     # on the grid, so the chunk moves as one body
                        info['parked'] = True
                        break
                    y += step
                x += PARK_COL
            if best is None:
                info['park_full'] = True
        if best is None and not free(0.0, 0.0):
            r = step
            while r <= reach and best is None:
                k = max(1, int(round(2 * math.pi * r / step)))
                for i in range(k):
                    a = 2 * math.pi * i / k
                    dx, dy = round(r * math.cos(a)), round(r * math.sin(a))
                    if free(dx, dy):
                        best = (dx, dy)
                        break
                r += step
        if best:
            dx, dy = best
            for m in moved:
                m.new = (grid(m.new[0] + dx), grid(m.new[1] + dy), m.new[2])
                m.reason += f'; chunk shifted by ({dx:+.0f}, {dy:+.0f}) mm to clear the pile'
            am = Member(self.anchor)
            am.anchor, am.role, am.status = self.anchor.ref, 'anchor', 'move'
            am.new = (grid(self.anchor.x + dx), grid(self.anchor.y + dy), self.anchor.rot)
            am.reason = f'anchor of the chunk, shifted by ({dx:+.0f}, {dy:+.0f}) mm with it to clear the pile'
            self.members.append(am)
            info['anchor_at'] = am.new
            info['chunk_shift'] = (dx, dy)
            box = (box[0] + dx, box[1] + dy, box[2] + dx, box[3] + dy)
        info['chunk_box'] = box
        info['chunk_refs'] = [self.anchor.ref] + sorted((m.ref for m in moved), key=natural)
        info['chunk_overlaps'] = [] if best else [
            f'{m.ref} over {ref}' for m in moved for ref, spoly in self.staged
            if polys_overlap(m.fp.polygon(m.new), spoly)]
        if not best and info['chunk_overlaps']:
            info['chunk_overlaps'].append('no free spot within reach')


# ============================================================ writing
def plan_edits(board, members):
    edits = []
    for m in members:
        if m.status != 'move':
            continue
        fp = m.fp
        nx, ny, nr = m.new
        delta = nr - fp.rot
        at = fp.at_node
        atoms = at.atoms()
        had_rot = len(atoms) > 3
        rot_txt = fmt(norm_fp_angle(nr))
        body = f'(at {fmt(nx)} {fmt(ny)}' + (f' {rot_txt})' if (had_rot or rot_txt != '0') else ')')
        edits.append((at.start, at.end, body))
        if abs(delta) > 1e-9:
            for p in fp.pads:
                node = p.at_node
                if node is None:
                    continue
                pa = node.atoms()
                old = pa[3].num() if len(pa) > 3 else 0.0
                new = norm_item_angle(old + delta)
                txt = f'(at {pa[1].text} {pa[2].text}' + (f' {fmt(new)})' if (len(pa) > 3 or fmt(new) != '0') else ')')
                edits.append((node.start, node.end, txt))
            for node in fp.text_at_nodes:
                pa = node.atoms()
                old = pa[3].num() if len(pa) > 3 else 0.0
                new = norm_item_angle(old + delta)
                txt = f'(at {pa[1].text} {pa[2].text}' + (f' {fmt(new)})' if (len(pa) > 3 or fmt(new) != '0') else ')')
                edits.append((node.start, node.end, txt))
    return edits


def marker_edits(board, anchor_ref, box, note, member_refs, absorb=(), take=()):
    """Replace this island's marker: a dashed box round the parked parts under
    a solid title bar carrying the label and the note, grouped with the
    island's footprints under the label's name, so the island, its box and
    its title move as one and read as one. Old markers of the same label
    (and stale duplicates) are removed first. Refs in `take` are removed
    from the other island group that holds them (reclaimed parts)."""
    import uuid
    edits = []
    label = f'island {anchor_ref}'
    take_uuids = set()
    for r in take:
        fp = board.fps.get(r)
        u = fp.node.find('uuid') if fp else None
        if u:
            take_uuids.add(u.atoms()[1].value)
    for g in board.top.findall('group'):
        name = g.atoms()[1].value if len(g.atoms()) > 1 else ''
        mem = g.find('members')
        if not (name.startswith('island ') and name != label and mem):
            continue
        for a in mem.atoms()[1:]:
            if a.value in take_uuids:
                st = a.start
                while st > 0 and board.text[st - 1] in ' \t':
                    st -= 1
                if st > 0 and board.text[st - 1] == '\n':
                    st -= 1
                edits.append((st, a.end, ''))
    for n in board.markers().get(label, (None, []))[1]:
        st = n.start
        while st > 0 and board.text[st - 1] in ' \t':
            st -= 1
        if st > 0 and board.text[st - 1] == '\n':
            st -= 1
        edits.append((st, n.end, ''))
    x0, top, x1, y0, y1, lines = marker_layout(box, label, note)
    ids = [str(uuid.uuid4()) for _ in range(4)]

    def rect(u, a, b, c, d, kind):
        return (f'\t(gr_rect\n\t\t(start {fmt(a)} {fmt(b)})\n\t\t(end {fmt(c)} {fmt(d)})\n'
                f'\t\t(stroke\n\t\t\t(width 0.15)\n\t\t\t(type {kind})\n\t\t)\n\t\t(fill no)\n'
                f'\t\t(layer "{MARK_LAYER}")\n\t\t(uuid "{u}")\n\t)\n')

    def text(u, words, x, y, size, just='left bottom'):
        th = fmt(round(size * 0.15, 3))
        return (f'\t(gr_text "{words}"\n\t\t(at {fmt(x)} {fmt(y)} 0)\n'
                f'\t\t(layer "{MARK_LAYER}")\n\t\t(uuid "{u}")\n'
                f'\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {fmt(size)} {fmt(size)})\n\t\t\t\t(thickness {th})\n\t\t\t)\n'
                f'\t\t\t(justify {just})\n\t\t)\n\t)\n')

    body = (rect(ids[0], x0, y0, x1, y1, 'dash') + rect(ids[1], x0, top, x1, y0, 'solid')
            + text(ids[2], label, x0 + 0.4, top + 0.4 + TITLE_SIZE, TITLE_SIZE)
            + text(ids[3], '\\n'.join(lines), x0 + 0.4, top + 0.4 + TITLE_SIZE + 0.3, NOTE_SIZE, 'left top'))
    # a footprint may sit in one group only: leave alone any that another island already holds
    taken = set()
    for g in board.top.findall('group'):
        name = g.atoms()[1].value if len(g.atoms()) > 1 else ''
        mem = g.find('members')
        if name.startswith('island ') and name != label and name not in absorb and mem:
            taken.update(a.value for a in mem.atoms()[1:] if a.value not in take_uuids)
    members = list(ids)
    for r in member_refs:
        fp = board.fps.get(r)
        u = fp.node.find('uuid') if fp else None
        if u and u.atoms()[1].value not in taken:
            members.append(u.atoms()[1].value)
        elif u:
            print(f'  {r} stays in another island\'s group; not added to {label}')
    body += (f'\t(group "{label}"\n\t\t(uuid "{uuid.uuid4()}")\n\t\t(members\n'
             + ''.join(f'\t\t\t"{u}"\n' for u in members) + '\t\t)\n\t)\n')
    edits.append((board.top.end - 1, board.top.end - 1, body))
    return edits


def city_edits(board, plan):
    """--city: move every island group named in the plan as one rigid body
    (turn about the old marker centre, then translate), rebuild its marker,
    and redraw the city frame (board outline and on-board ghosts, group
    'city frame' on MARK_LAYER). Returns (edits, moved members)."""
    import uuid
    edits, members = [], []
    groups = {}
    for ref, label in board.island_groups().items():
        groups.setdefault(label, []).append(ref)
    marks = board.markers()
    entries = plan.get('islands') or {}
    final = {}                                  # host anchor -> (refs, polygons, absorbed labels)
    bare = []                                   # entries that end with no marker (a post set on the board)
    for anchor_ref, mv in entries.items():
        label = f'island {anchor_ref}'
        refs = groups.get(label)
        if not refs and anchor_ref in board.fps and mv.get('merge_into'):
            refs = [anchor_ref]                 # a lone footprint (a key post) joining a block
        if not refs:
            print(f'  city: {label} has no group; skipped')
            continue
        fx, fy = mv['from']
        tx, ty = mv['to']
        turn = float(mv.get('turn') or 0)
        host = str(mv.get('merge_into') or anchor_ref)
        if mv.get('marker') == 'none':
            bare.append(label)
            host = None
        f = final.setdefault(host, ([], [], []))
        if host != anchor_ref and host is not None:
            f[2].append(label)
        reseat = mv.get('reseat') or {}             # ref -> [dx, dy]: a member moved inside its own group first
        for r in refs:
            fp = board.fps[r]
            sx, sy = reseat.get(r, (0.0, 0.0))
            dx, dy = rot(fp.x + sx - fx, fp.y + sy - fy, turn)
            m = Member(fp)
            m.new = (grid(tx + dx), grid(ty + dy), norm_fp_angle(fp.rot + turn))
            m.status, m.anchor = 'move', host
            m.reason = f'city plan: {label} to ({tx:.1f}, {ty:.1f})' + (f', turned {turn:g}' if turn else '')
            members.append(m)
            f[0].append(r)
            f[1].append(fp.polygon(m.new))
    for label in bare:                          # the post lands on the board: its marker and group go
        # markers() lists the box, the bar, the texts and the group node itself
        for n in marks.get(label, (None, []))[1]:
            st = n.start
            while st > 0 and board.text[st - 1] in ' \t':
                st -= 1
            if st > 0 and board.text[st - 1] == '\n':
                st -= 1
            edits.append((st, n.end, ''))
    for host, (refs, polys, absorbed) in final.items():
        if host is None:
            continue
        label = f'island {host}'
        box = bbox_of([p for poly in polys for p in poly])
        note = ''
        name = role_name(host)
        for n in marks.get(label, (None, []))[1]:
            if n.name == 'gr_text' and not n.atoms()[1].value.startswith(label):
                v = n.atoms()[1].value.replace('\\n', ' ').replace('\n', ' ')
                v = ' '.join(v.split())
                note = v[len(name):].strip() if name and v.startswith(name) else v.split(': ', 1)[-1]
        if absorbed:
            sats = ', '.join(l.split()[1] for l in absorbed)
            note = (note.split(' + ')[0] + f' + {sats}') if note else f'with {sats}'
            for l in absorbed:                  # the satellite's own box goes
                for n in marks.get(l, (None, []))[1]:
                    st = n.start
                    while st > 0 and board.text[st - 1] in ' \t':
                        st -= 1
                    if st > 0 and board.text[st - 1] == '\n':
                        st -= 1
                    edits.append((st, n.end, ''))
        edits += marker_edits(board, host, box, note or 'city plan',
                              [host] + sorted((r for r in refs if r != host), key=natural), absorb=absorbed)
    # the frame: remove an old one, draw the scaled outline and ghosts
    by_uuid = {}
    for n in board.top.nodes():
        u = n.find('uuid')
        if u:
            by_uuid[u.atoms()[1].value] = n
    for g in board.top.findall('group'):
        if len(g.atoms()) > 1 and g.atoms()[1].value == 'city frame':
            mem = g.find('members')
            for n in [by_uuid[a.value] for a in (mem.atoms()[1:] if mem else []) if a.value in by_uuid] + [g]:
                st = n.start
                while st > 0 and board.text[st - 1] in ' \t':
                    st -= 1
                if st > 0 and board.text[st - 1] == '\n':
                    st -= 1
                edits.append((st, n.end, ''))
    ids, body = [], ''

    def rect(a, b_, c, d, kind, width=0.15):
        u = str(uuid.uuid4())
        ids.append(u)
        return (f'\t(gr_rect\n\t\t(start {fmt(a)} {fmt(b_)})\n\t\t(end {fmt(c)} {fmt(d)})\n'
                f'\t\t(stroke\n\t\t\t(width {fmt(width)})\n\t\t\t(type {kind})\n\t\t)\n\t\t(fill no)\n'
                f'\t\t(layer "{MARK_LAYER}")\n\t\t(uuid "{u}")\n\t)\n')

    def text(words, x, y, size):
        u = str(uuid.uuid4())
        ids.append(u)
        return (f'\t(gr_text "{words}"\n\t\t(at {fmt(x)} {fmt(y)} 0)\n\t\t(layer "{MARK_LAYER}")\n'
                f'\t\t(uuid "{u}")\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {fmt(size)} {fmt(size)})\n'
                f'\t\t\t\t(thickness {fmt(round(size * 0.15, 3))})\n\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n\t)\n')
    ox, oy = plan['origin']
    sc = float(plan['scale'])
    o = plan['outline']
    x1, y1 = ox + sc * (o[2] - o[0]), oy + sc * (o[3] - o[1])
    body += rect(ox, oy, x1, y1, 'solid', 0.3)
    body += text(f'CITY PLAN ({plan.get("variant", "")}): the board at {sc:g}x, blocks at real size; '
                 f'grey = already on the board. Compact by hand.', ox, oy - 3.0, 2.0)
    body += text('TOP EDGE', ox, oy - 0.6, 1.5)
    body += text('BOTTOM EDGE', ox, y1 + 2.2, 1.5)
    for r, g in (plan.get('ghosts') or {}).items():
        body += rect(g[0], g[1], g[2], g[3], 'dot')
        body += text(r, g[0] + 0.3, g[3] - 0.3, 1.0)
    # districts (city.py 'districts' variant): a dashed box round each
    # finished neighbourhood, its name above the box
    for name, d in (plan.get('districts') or {}).items():
        body += rect(d[0], d[1], d[2], d[3], 'dash', 0.25)
        body += text(str(name), d[0] + 0.3, d[1] - 0.4, 1.2)
    body += (f'\t(group "city frame"\n\t\t(uuid "{uuid.uuid4()}")\n\t\t(members\n'
             + ''.join(f'\t\t\t"{u}"\n' for u in ids) + '\t\t)\n\t)\n')
    edits.append((board.top.end - 1, board.top.end - 1, body))
    return edits, members


def mirror_strip(board, refs, axis=None, edge_margin=1.0):
    """Edge strip: mirror the positions of the listed parts across a vertical
    line (default the centre of their common box) and keep every rotation.
    Returns (rail header footprint, members, info)."""
    missing = [r for r in refs if r not in board.fps]
    if missing:
        sys.exit(f'--mirror: no such footprint: {", ".join(missing)}')
    if len(set(refs)) != len(refs):
        sys.exit('--mirror: a reference is listed twice')
    fps = [board.fps[r] for r in refs]
    back = [fp.ref for fp in fps if fp.layer != 'F.Cu']
    if back:
        sys.exit(f'--mirror: not on F.Cu: {", ".join(back)}')
    box = bbox_of([p for fp in fps for p in fp.polygon()])
    if axis is None:
        axis = (box[0] + box[2]) / 2
    anchor = fps[0]
    members, exact, inexact = [], [], []
    for fp in fps:
        m = Member(fp)
        m.anchor, m.role = anchor.ref, 'anchor' if fp is anchor else 'strip'
        cx, cy = fp.centre()
        dx = (2 * axis - cx) - cx
        m.new = (fp.x + dx, fp.y, fp.rot)
        # is the pad pattern (position and number) symmetric about the part's own vertical axis?
        pads = {(p.number, round(fp.pad_pos(p)[0] - cx, 4), round(fp.pad_pos(p)[1] - cy, 4)) for p in fp.pads}
        mirrored = {(n, round(-x, 4), y) for n, x, y in pads}
        turned = {(n, round(-x, 4), round(-y, 4)) for n, x, y in pads}
        if pads == mirrored:
            exact.append(fp.ref)
            m.reason = 'mirrored across the strip line'
        elif turned == mirrored:
            # two pads in a row along x: a half turn is the exact mirror, pad numbers included
            m.new = (fp.x + dx, fp.y, fp.rot + 180.0)
            exact.append(fp.ref)
            m.reason = 'mirrored across the strip line (half turn: the exact mirror of a two-pad row)'
        else:
            inexact.append(fp.ref)
            m.reason = 'body mirrored across the strip line, pad pattern kept (rotation unchanged)'
        if abs(dx) < 1e-6:
            m.status, m.reason = 'keep', 'sits on the mirror line'
        else:
            m.status = 'move'
        members.append(m)
    new_box = bbox_of([p for m in members for p in m.fp.polygon(m.new)])
    strip = set(refs)
    overlaps = []
    for ref, other in board.fps.items():
        if ref in strip:
            continue
        for m in members:
            if m.status == 'move' and polys_overlap(m.fp.polygon(m.new), other.polygon()):
                overlaps.append(f'{m.ref}/{ref}')
    ac = anchor.centre()
    o = board.outline
    margin = min(box[0] - o[0], o[2] - box[2]) if o else float('nan')
    info = {'box': box, 'new_box': new_box, 'axis': axis, 'exact': exact, 'inexact': inexact,
            'overlaps': overlaps, 'edge_margin': margin,
            'rail_was': 'left' if ac[0] < axis else 'right',
            'rail_now': 'right' if ac[0] < axis else 'left'}
    if margin < edge_margin:
        info['note'] = f'strip is {margin:.2f} mm from the board edge, under --edge-margin {edge_margin}'
    return anchor, members, info


STRIP_GAP = 0.3     # courtyard to courtyard on the strip, like --part-gap
PITCH = 2.54


def _half(fp, at):
    b = fp.bbox(at)
    return (b[2] - b[0]) / 2, (b[3] - b[1]) / 2


def strip_layout(board, rail_ref, rail_at=None):
    """Slot strip lattice; see the docstring section 'Slot strip lattice'.
    Returns (rail footprint, members, info)."""
    import placement as pl
    if rail_ref not in board.fps:
        sys.exit(f'--strip {rail_ref}: no such footprint')
    rail = board.fps[rail_ref]
    rpos = (rail_at[0], rail_at[1], rail.rot) if rail_at else (rail.x, rail.y, rail.rot)
    rows = sorted({round(rail.pad_pos(p, rpos)[0], 3) for p in rail.pads})
    cols = sorted({round(rail.pad_pos(p, rpos)[1], 3) for p in rail.pads})
    if len(rows) != 2 or len(cols) != 32:
        sys.exit(f'--strip {rail_ref}: expected a vertical 2x32 header, found {len(rows)} rows x {len(cols)} columns')
    if any(abs((c - cols[0]) - i * PITCH) > 0.01 for i, c in enumerate(cols)):
        sys.exit(f'--strip {rail_ref}: columns are not on a 2.54 mm pitch')
    slots = []
    for i in range(4):
        sec = set(cols[8 * i:8 * i + 8])
        letters = {m.group(1) for p in rail.pads if round(rail.pad_pos(p, rpos)[1], 3) in sec
                   for m in [re.match(r'SLOT([A-H])_', p.net)] if m}
        if len(letters) != 1:
            sys.exit(f'--strip {rail_ref}: section {i} carries slots {sorted(letters)}, expected exactly one')
        slots.append(letters.pop())
    headers = {s: board.fps[pl.POWER_REFS[s]] for s in slots}
    posts = {s: board.fps[f'MK{ord(s)}'] for s in slots}
    sign = 1 if sum(h.x for h in headers.values()) / 4 > rail.x else -1
    inner = rows[1] if sign > 0 else rows[0]
    x_h = inner + sign * 2 * PITCH          # header line
    x_k = x_h + sign * PITCH                # key post column
    members, notes, used = [], [], set()

    def add(fp, new, role, reason):
        m = Member(fp)
        m.anchor, m.role, m.new, m.reason = rail.ref, role, new, reason
        moved = abs(new[0] - fp.x) > 1e-6 or abs(new[1] - fp.y) > 1e-6 or abs(norm_fp_angle(new[2] - fp.rot)) > 1e-6
        m.status = 'move' if moved else 'keep'
        if not moved:
            m.reason = 'already there; ' + reason
        members.append(m)
        used.add(fp.ref)
        return m

    def upright(fp):
        rot = fp.rot
        if _half(fp, (0, 0, rot))[0] > _half(fp, (0, 0, rot))[1]:
            rot = norm_fp_angle(rot + 90)
        return rot

    add(rail, rpos, 'anchor', "rail header, the owner's position" + (' moved by --rail-at' if rail_at else ''))
    h0, p0 = headers[slots[0]], posts[slots[0]]
    hdr_hw = _half(h0, (0, 0, h0.rot))[0]
    post_hw, post_hh = _half(p0, (0, 0, p0.rot))
    rail_edge = rail.bbox(rpos)[0] if sign < 0 else rail.bbox(rpos)[2]
    x_c = ((x_h - sign * hdr_hw) + rail_edge) / 2
    x_aux = None
    sections = []
    for i, s in enumerate(slots):
        y0 = cols[8 * i]
        hdr, post = headers[s], posts[s]
        y_h = cols[8 * i + 3]
        rot_h = hdr.rot
        pins = {p.number: p for p in hdr.pads}
        if hdr.pad_pos(pins['1'], (x_h, y_h, rot_h))[1] > hdr.pad_pos(pins['7'], (x_h, y_h, rot_h))[1]:
            rot_h = norm_fp_angle(rot_h + 180)
        hpos = (x_h, y_h, rot_h)
        for p in hdr.pads:
            k = round((hdr.pad_pos(p, hpos)[1] - y0) / PITCH)
            if not (0 <= k <= 6) or abs(hdr.pad_pos(p, hpos)[1] - cols[8 * i + k]) > 0.01 or abs(hdr.pad_pos(p, hpos)[0] - x_h) > 0.01:
                sys.exit(f'{hdr.ref}: pin {p.number} would not land on columns 1..7')
        add(hdr, hpos, 'header', f'slot {s} power header, pins on columns 1..7, pin 1 (PIN V) at column 1')
        add(post, (x_k, cols[8 * i + 7], post.rot), 'post',
            f'slot {s} key post at column 8, one pitch outside the header line')
        rail_nets = [p.net for p in sorted(hdr.pads, key=lambda p: hdr.pad_pos(p, hpos)[1]) if p.net != GND]
        parts = [fp for fp in board.fps.values() if fp.prefix() in ('F', 'C')
                 and any(p.net.startswith(f'SLOT_{s}_') for p in fp.pads)]
        net_of = {fp.ref: next(p.net for p in fp.pads if p.net.startswith(f'SLOT_{s}_')) for fp in parts}
        missing = [fp.ref for fp in parts if net_of[fp.ref] not in rail_nets]
        if missing:
            sys.exit(f'slot {s}: {", ".join(missing)} are on a net with no pin on {hdr.ref}')
        # AUX fuse: edge side of the header body, above the post
        aux = [fp for fp in parts if fp.prefix() == 'F' and net_of[fp.ref].endswith('_AUX')]
        for fp in aux:
            rot = fp.rot
            if _half(fp, (0, 0, rot))[0] < _half(fp, (0, 0, rot))[1]:
                rot = norm_fp_angle(rot + 90)
            slot_pad = next(p for p in fp.pads if p.net == net_of[fp.ref])
            if sign * fp.pad_pos(slot_pad, (0, 0, rot))[0] > 0:
                rot = norm_fp_angle(rot + 180)
            hw, hh = _half(fp, (0, 0, rot))
            x_aux = x_h + sign * (hdr_hw + STRIP_GAP + hw)
            y_aux = cols[8 * i + 7] - post_hh - STRIP_GAP - hh
            add(fp, (x_aux, y_aux, rot), 'fuse', f'slot {s} AUX fuse beside the header body, above the post, slot pad toward the header')
        # the stack: caps then fuse per rail pin, top to bottom, centred on the header body
        stack = []
        for net in rail_nets:
            if net.endswith('_AUX'):
                continue
            stack += sorted((fp for fp in parts if fp.prefix() == 'C' and net_of[fp.ref] == net), key=lambda f: natural(f.ref))
            stack += sorted((fp for fp in parts if fp.prefix() == 'F' and net_of[fp.ref] == net), key=lambda f: natural(f.ref))
        rots = {fp.ref: upright(fp) for fp in stack}
        hhs = [_half(fp, (0, 0, rots[fp.ref]))[1] for fp in stack]
        length = sum(2 * h for h in hhs) + STRIP_GAP * (len(stack) - 1)
        y = y_h - length / 2
        for fp, hh in zip(stack, hhs):
            add(fp, (x_c, y + hh, rots[fp.ref]), 'stack',
                f'slot {s} {fp.value} in the stack between header and rail ({net_of[fp.ref].split("_", 2)[2]})')
            y += 2 * hh + STRIP_GAP
        sections.append({'slot': s, 'y0': y0, 'y7': cols[8 * i + 7], 'post': post.ref, 'header': hdr.ref,
                         'pins': ' '.join(f'{p.number}:{hdr.pad_pos(p, hpos)[1]:.2f}' for p in sorted(hdr.pads, key=lambda p: int(p.number))),
                         'aux': ' '.join(f.ref for f in aux), 'stack': ' '.join(f.ref for f in stack),
                         'stack_len': length, 'hdr_len': 2 * _half(hdr, (0, 0, rot_h))[1]})
    # posts of the other edge standing on this side trade places with ours
    region_x = (min(x_k, rail.x) - 20, max(x_k, rail.x) + 20)
    on_side = lambda fp: sign * (fp.x - rail.x) > 0 and region_x[0] <= fp.x <= region_x[1]
    strays = [fp for ref, fp in board.fps.items() if ref.startswith('MK') and ref not in used and len(fp.pads) == 1
              and on_side(fp) and board.outline and board.outline[1] <= fp.y <= board.outline[3]]
    incoming = [m for m in members if m.role == 'post' and not on_side(m.fp)]
    for stray, inc in zip(sorted(strays, key=lambda f: natural(f.ref)), sorted(incoming, key=lambda m: natural(m.ref))):
        add(stray, (inc.fp.x, inc.fp.y, stray.rot), 'post', f"other edge's post, takes {inc.ref}'s old place ({inc.ref} comes to this strip)")
        notes.append(f'{stray.ref} and {inc.ref} trade places: identical GND posts, refs follow design.py MK<ord(slot)>')
    for stray in strays[len(incoming):]:
        notes.append(f'NOTE {stray.ref} stands on this side but belongs to the other edge and has no incoming post to swap with')
    overlaps = []
    planned = [(m.ref, m.fp.polygon(m.new)) for m in members]
    keyed = {frozenset((a['post'], b['header'])) for a in sections for b in sections}   # own header and the next section's
    for a in range(len(planned)):
        for b in range(a + 1, len(planned)):
            if polys_overlap(planned[a][1], planned[b][1]):
                if frozenset((planned[a][0], planned[b][0])) in keyed:
                    notes.append(f'{planned[a][0]}/{planned[b][0]}: post and header courtyards touch at the corner '
                                 f'(diagonal neighbours one pitch apart; the known post-to-header DRC pair)')
                    continue
                overlaps.append(f'{planned[a][0]}/{planned[b][0]}')
    for ref, other in board.fps.items():
        if ref in used:
            continue
        for mref, poly in planned:
            if polys_overlap(poly, other.polygon()):
                overlaps.append(f'{mref}/{ref}')
    box = bbox_of([pt for _, poly in planned for pt in poly])
    o = board.outline
    margin = min(box[0] - o[0], o[2] - box[2], box[1] - o[1], o[3] - box[3]) if o else float('nan')
    gap_h = (x_c - sign * _half(stack[0], (0, 0, rots[stack[0].ref]))[0]) * sign - (x_h - sign * hdr_hw) * sign if stack else None
    info = {'rows': rows, 'cols': cols, 'sign': sign, 'inner': inner, 'x_h': x_h, 'x_k': x_k, 'x_aux': x_aux,
            'x_c': x_c, 'sections': sections, 'notes': notes, 'overlaps': overlaps, 'edge_margin': margin, 'box': box}
    return rail, members, info


def apply_edits(text, edits):
    out = text
    for start, end, new in sorted(edits, key=lambda t: t[0], reverse=True):
        out = out[:start] + new + out[end:]
    return out


def verify_written(path, moved, original):
    """Re-read the written file: moved footprints read back as planned, every
    other footprint's text is byte for byte what it was."""
    nb = Board(path)
    errs = []
    for ref, fp in original.fps.items():
        if ref not in nb.fps:
            errs.append(f'{ref} missing after write')
            continue
        nfp = nb.fps[ref]
        if ref in moved:
            m = moved[ref]
            if (abs(nfp.x - m.new[0]) > 1e-6 or abs(nfp.y - m.new[1]) > 1e-6
                    or abs(norm_fp_angle(nfp.rot - m.new[2])) > 1e-6):
                errs.append(f'{ref}: read back at {nfp.x},{nfp.y},{nfp.rot}, planned {m.new}')
            for op, np_ in zip(fp.pads, nfp.pads):
                want = fp.pad_pos(op, m.new)
                got = nfp.pad_pos(np_)
                if dist(want, got) > 1e-5:
                    errs.append(f'{ref} pad {op.number}: read back {got}, planned {want}')
                oa = op.angle - fp.rot
                na = np_.angle - nfp.rot
                if abs(norm_item_angle(oa - na)) > 1e-6 and abs(norm_item_angle(oa - na) - 360) > 1e-6:
                    errs.append(f'{ref} pad {op.number}: relative pad angle changed {oa} -> {na}')
        else:
            if original.text[fp.node.start:fp.node.end] != nb.text[nfp.node.start:nfp.node.end]:
                errs.append(f'{ref}: text changed although it did not move')
    if len(nb.fps) != len(original.fps):
        errs.append('footprint count changed')
    return errs


def run_drc(path):
    with tempfile.TemporaryDirectory() as tmp:
        rpt = os.path.join(tmp, 'drc.rpt')
        cmd = ['kicad-cli', 'pcb', 'drc', '--severity-error', '-o', rpt, path]
        print('\n$ ' + ' '.join(cmd))
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        except FileNotFoundError:
            print('  kicad-cli not found; DRC skipped')
            return
        if res.stdout.strip():
            print(res.stdout.rstrip())
        if res.stderr.strip():
            print(res.stderr.rstrip())
        if os.path.isfile(rpt):
            lines = open(rpt).read().splitlines()
            section = None
            for ln in lines:
                if ln.startswith('** '):
                    section = ln
                    print(ln)
                elif section and 'DRC violations' in section:
                    print(ln)
            # unconnected items are expected on an unrouted board: count only
            print(f'  ({len(lines)} report lines; unconnected items are listed in the file, not here)')


# ============================================================ render
def render(path, board, anchor, members, planner, title, locked):
    S = 22.0
    am = next((m for m in members if m.ref == anchor.ref), None)
    aat = am.new if am and am.new else None
    members = [m for m in members if m.ref != anchor.ref]
    polys = [anchor.polygon(aat)]
    for m in members:
        if m.new:
            polys.append(m.fp.polygon(m.new))
    region = bbox_of([p for poly in polys for p in poly])
    far_old = []
    for m in members:
        if dist(m.pos(), anchor.centre(aat)) < 25.0:
            polys.append(m.fp.polygon())
        else:
            far_old.append(m)
    region = bbox_of([p for poly in polys for p in poly])
    pad = 3.0
    x0, y0, x1, y1 = region[0] - pad, region[1] - pad, region[2] + pad, region[3] + pad
    W, H = (x1 - x0) * S, (y1 - y0) * S
    legend_h = 110

    def X(v):
        return (v - x0) * S

    def Y(v):
        return (v - y0) * S

    def poly_svg(poly, fill, stroke, extra=''):
        pts = ' '.join(f'{X(px):.1f},{Y(py):.1f}' for px, py in poly)
        return f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="1" {extra}/>'

    def pad_svg(fp, p, at, nets_of_interest):
        cx, cy = fp.pad_pos(p, at)
        ang = p.angle + (at[2] - fp.rot if at else 0.0)
        c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        hw, hh = p.w / 2, p.h / 2
        corners = [(cx + dx * c + dy * s, cy - dx * s + dy * c)
                   for dx, dy in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))]
        fill = '#333' if p.net == GND else ('#e67e22' if p.net in nets_of_interest else '#c8c8c8')
        if p.shape == 'circle':
            return f'<circle cx="{X(cx):.1f}" cy="{Y(cy):.1f}" r="{hw * S:.1f}" fill="{fill}"/>'
        return poly_svg(corners, fill, 'none')

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H + legend_h:.0f}" '
           f'viewBox="0 0 {W:.0f} {H + legend_h:.0f}" font-family="monospace">',
           f'<rect x="0" y="0" width="{W:.0f}" height="{H + legend_h:.0f}" fill="#fbfaf6"/>']
    if board.outline:
        bx0, by0, bx1, by1 = board.outline
        out.append(f'<rect x="{X(bx0):.1f}" y="{Y(by0):.1f}" width="{(bx1 - bx0) * S:.1f}" '
                   f'height="{(by1 - by0) * S:.1f}" fill="none" stroke="#000" stroke-width="2"/>')
    nets_of_interest = {m.rail for m in members if m.rail} | {m.via for m in members if m.via}
    for m in members:
        nets_of_interest |= {n for n in m.fp.nets() if n != GND}
    region_poly = box_corners((x0, y0, x1, y1))
    moving = {m.ref for m in members}
    for ref, fp in board.fps.items():
        if ref == anchor.ref or ref in moving:
            continue
        poly = fp.polygon()
        if not polys_overlap(poly, region_poly):
            continue
        fill = '#e4e4e4' if locked[ref][0] else '#eeeadf'
        out.append(poly_svg(poly, fill, '#999'))
        cx, cy = fp.centre()
        out.append(f'<text x="{X(cx):.1f}" y="{Y(cy):.1f}" font-size="9" fill="#777" '
                   f'text-anchor="middle" dominant-baseline="middle">{ref}</text>')
    # anchor
    if aat:
        out.append(poly_svg(anchor.polygon(), 'none', '#b8860b', 'stroke-dasharray="4,3"'))
    out.append(poly_svg(anchor.polygon(aat), '#fff1b8', '#b8860b'))
    served = {m.pad.number for m in members if m.pad}
    for p in anchor.pads:
        out.append(pad_svg(anchor, p, aat, nets_of_interest))
        if len(anchor.pads) <= 64 or p.number in served:
            px, py = anchor.pad_pos(p, aat)
            out.append(f'<text x="{X(px):.1f}" y="{Y(py) - 0.35 * S:.1f}" font-size="8" fill="#555" '
                       f'text-anchor="middle">{p.number}</text>')
    ac = anchor.centre(aat)
    out.append(f'<text x="{X(ac[0]):.1f}" y="{Y(ac[1]):.1f}" font-size="12" font-weight="bold" '
               f'fill="#7a5a00" text-anchor="middle" dominant-baseline="middle">{anchor.ref}</text>')
    colours = {'chain': '#9fd8a8', 'decoupling': '#a9c9f5', 'signal': '#d6b3f0'}
    for m in members:
        old_poly = m.fp.polygon()
        if m.status == 'move' and m.new:
            if m not in far_old:
                out.append(poly_svg(old_poly, 'none', '#999', 'stroke-dasharray="4,3"'))
                oc, nc = m.fp.centre(), m.fp.centre(m.new)
                out.append(f'<line x1="{X(oc[0]):.1f}" y1="{Y(oc[1]):.1f}" x2="{X(nc[0]):.1f}" '
                           f'y2="{Y(nc[1]):.1f}" stroke="#bbb" stroke-width="1"/>')
            out.append(poly_svg(m.fp.polygon(m.new), colours.get(m.role, '#ddd'), '#333'))
            for p in m.fp.pads:
                out.append(pad_svg(m.fp, p, m.new, nets_of_interest))
            c = m.fp.centre(m.new)
        else:
            stroke = '#c0392b' if m.status == 'fail' else '#333'
            out.append(poly_svg(old_poly, colours.get(m.role, '#ddd') if m.status == 'keep' else '#f5b7b1',
                                stroke, 'stroke-dasharray="3,2"' if m.status == 'fail' else ''))
            for p in m.fp.pads:
                out.append(pad_svg(m.fp, p, None, nets_of_interest))
            c = m.fp.centre()
        out.append(f'<text x="{X(c[0]):.1f}" y="{Y(c[1]) + 0.9 * S:.1f}" font-size="10" fill="#111" '
                   f'text-anchor="middle">{m.ref}</text>')
    ly = H + 16
    out.append(f'<text x="8" y="{ly:.0f}" font-size="12" font-weight="bold">{title}</text>')
    ly += 16
    for role, col in colours.items():
        out.append(f'<rect x="8" y="{ly - 10:.0f}" width="12" height="12" fill="{col}" stroke="#333"/>'
                   f'<text x="26" y="{ly:.0f}" font-size="11">{role}</text>')
        ly += 15
    out.append(f'<rect x="150" y="{H + 22:.0f}" width="12" height="12" fill="#e67e22"/>'
               f'<text x="168" y="{H + 32:.0f}" font-size="11">pad on an island net</text>')
    out.append(f'<rect x="150" y="{H + 37:.0f}" width="12" height="12" fill="#333"/>'
               f'<text x="168" y="{H + 47:.0f}" font-size="11">GND pad</text>')
    out.append(f'<rect x="150" y="{H + 52:.0f}" width="12" height="12" fill="none" stroke="#999" stroke-dasharray="4,3"/>'
               f'<text x="168" y="{H + 62:.0f}" font-size="11">previous position</text>')
    out.append(f'<rect x="150" y="{H + 67:.0f}" width="12" height="12" fill="#f5b7b1" stroke="#c0392b" stroke-dasharray="3,2"/>'
               f'<text x="168" y="{H + 77:.0f}" font-size="11">could not be placed (left where it is)</text>')
    if far_old:
        out.append(f'<text x="400" y="{H + 32:.0f}" font-size="11">previous positions out of view: '
                   f'{", ".join(m.ref for m in far_old)}</text>')
    out.append(f'<text x="400" y="{H + 47:.0f}" font-size="11">grid: {x0:.1f}..{x1:.1f} x {y0:.1f}..{y1:.1f} mm, '
               f'{S:.0f} px/mm</text>')
    out.append('</svg>')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w').write('\n'.join(out))
    return path


# ============================================================ reports
def print_membership(board, anchor, members, chains, island_net):
    print(f'\nISLAND {anchor.ref} ({anchor.value})' + (f', restricted to net {island_net}' if island_net else ''))
    print(f'  {"ref":6s} {"value":28s} {"anchor pad":22s} {"hops":4s} {"side":4s} {"role":11s} {"destination":12s} notes')
    for m in sorted(members, key=lambda m: (m.role or '', natural(m.ref))):
        padtxt = f'{m.pad.number} ({m.pad.net})' if m.pad else '-'
        role = m.role or '-'
        if m.role == 'chain' and m.kind:
            role = f'chain/{m.kind}'
        hops = 'rail' if m.hops == 0 else (str(m.hops) if m.hops is not None else '-')
        print(f'  {m.ref:6s} {m.fp.value[:28]:28s} {padtxt[:22]:22s} {hops:4s} '
              f'{m.side or "-":4s} {role:11s} {m.dest or "-":12s} {"; ".join(m.notes)}')
    for ch in chains:
        seq = ' -> '.join(f'{m.ref}' for m in ch['seq'])
        print(f'  chain on {ch["rail"]}: {anchor.ref} pad {ch["root"].number} ({ch["root"].net}) -> {seq}')


def print_moves(members):
    moves = [m for m in members if m.status == 'move']
    print(f'\nMOVE REPORT ({len(moves)} footprint(s) move)')
    for m in sorted(moves, key=lambda m: natural(m.ref)):
        print(f'  {m.ref} moves from ({m.fp.x:.2f}, {m.fp.y:.2f}) to ({m.new[0]:.2f}, {m.new[1]:.2f}), '
              f'rotation {fmt(m.fp.rot)} to {fmt(norm_fp_angle(m.new[2]))}, {m.reason}')
    kept = [m for m in members if m.status != 'move']
    print(f'\nLEFT IN PLACE ({len(kept)})')
    for m in sorted(kept, key=lambda m: natural(m.ref)):
        print(f'  {m.ref} stays at ({m.fp.x:.2f}, {m.fp.y:.2f}) rotation {fmt(m.fp.rot)}: {m.reason}'
              + (f' [{"; ".join(m.notes)}]' if m.notes and m.status != "move" else ''))


def check_geometry(board):
    """Cross-check pad positions and courtyards against pcbnew (dev aid)."""
    try:
        import pcbnew
    except ImportError:
        print('pcbnew not importable; geometry check skipped')
        return 1
    b = pcbnew.LoadBoard(board.path)
    bad = 0
    for f in b.GetFootprints():
        fp = board.fps.get(f.GetReference())
        if fp is None:
            print(f'{f.GetReference()}: not parsed'); bad += 1; continue
        for q in f.Pads():
            mine = fp.pad_by_net(q.GetNetname()) if False else next(
                (p for p in fp.pads if p.number == q.GetNumber() and
                 dist(fp.pad_pos(p), (pcbnew.ToMM(q.GetPosition().x), pcbnew.ToMM(q.GetPosition().y))) < 1e-3),
                None)
            if mine is None:
                print(f'{fp.ref} pad {q.GetNumber()}: position mismatch'); bad += 1
                break
            if abs(((mine.angle - q.GetOrientationDegrees()) + 180) % 360 - 180) > 1e-3:
                print(f'{fp.ref} pad {q.GetNumber()}: angle mine {mine.angle} pcbnew {q.GetOrientationDegrees()}'); bad += 1
                break
        if fp.crtyd is not None:
            bb = f.GetCourtyard(pcbnew.F_CrtYd).BBox()
            p = f.GetPosition()
            mine = fp.crtyd
            theirs = (pcbnew.ToMM(bb.GetLeft() - p.x), pcbnew.ToMM(bb.GetTop() - p.y),
                      pcbnew.ToMM(bb.GetRight() - p.x), pcbnew.ToMM(bb.GetBottom() - p.y))
            rmine = bbox_of([rot(x, y, fp.rot) for x, y in box_corners(mine)])
            # pcbnew's courtyard polygon is the stroked outline plus its arc
            # approximation allowance, about 0.02 mm beyond the half stroke
            if any(abs(a - c) > 0.03 for a, c in zip(rmine, theirs)):
                print(f'{fp.ref}: courtyard bbox mine {tuple(round(v, 3) for v in rmine)} pcbnew {tuple(round(v, 3) for v in theirs)}')
                bad += 1
    print(f'geometry check: {len(board.fps)} footprints, {bad} mismatch(es) '
          f'(pad positions within 0.001 mm, courtyard boxes within 0.03 mm)')
    return 1 if bad else 0


# ============================================================ main
def main():
    ap = argparse.ArgumentParser(
        description='Place the unlocked passives of one anchor island. Dry run unless --apply.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split('Hard rules', 1)[0])
    ap.add_argument('--anchor', help='reference of the locked footprint whose island is processed (U13, U1, J3...)')
    ap.add_argument('--island-net', help='restrict the island to parts with a pad on this net (+2V5)')
    ap.add_argument('--apply', action='store_true', help='write the pcb (default: dry run, print and render only)')
    ap.add_argument('--board', default=BOARD, help=f'pcb file (default {os.path.relpath(BOARD, ROOT)})')
    ap.add_argument('--locks', default=LOCKS, help=f'lock list (default {os.path.relpath(LOCKS, ROOT)})')
    ap.add_argument('--profiles', default=PROFILES,
                    help=f'datasheet layout profiles (default {os.path.relpath(PROFILES, ROOT)})')
    ap.add_argument('--render', help='SVG output path (default ref/islands/<anchor>[-<net>].svg)')
    ap.add_argument('--short-net-max-pads', type=int, default=3, help='a net with at most this many pads is short (3)')
    ap.add_argument('--ring-gap', type=float, default=0.5, help='mm from the anchor courtyard to the first ring, and between rings (0.5)')
    ap.add_argument('--part-gap', type=float, default=0.3, help='mm between neighbouring courtyards, and the collision step (0.3)')
    ap.add_argument('--edge-margin', type=float, default=1.0, help='mm kept clear inside the board outline (1.0)')
    ap.add_argument('--lot', nargs=4, type=float, metavar=('X0', 'Y0', 'X1', 'Y1'),
                    help=f'parking lot rectangle in mm (default {" ".join(fmt(v) for v in PARK)}, right of the A3 sheet)')
    ap.add_argument('--with', dest='with_', type=lambda v: v.split(','), metavar='REF,...',
                    help='pull these movable parts into this island (a TVS to its connector rather than the nearest chip)')
    ap.add_argument('--without', type=lambda v: v.split(','), metavar='REF,...',
                    help='leave these parts out of this island')
    ap.add_argument('--city', metavar='PLAN',
                    help='move every island group as one rigid body to its place in a tools/city.py plan (dry run unless --apply)')
    ap.add_argument('--extend', action='store_true',
                    help='staged islands: keep the parked parts where they are and lay out only the members that are new to the island')
    ap.add_argument('--repark', action='store_true',
                    help='staged islands: keep the layout as it is and only move the chunk, as one body, to its lot slot (no layout rules run)')
    ap.add_argument('--revert', metavar='SNAPSHOT',
                    help='staged islands: put the island (anchor included) back where a check_positions.py snapshot has it; the undo of an apply')
    ap.add_argument('--no-park', action='store_true',
                    help='staged islands: leave the chunk at the nearest free spot instead of the parking lot right of the sheet')
    ap.add_argument('--mirror', type=lambda v: v.split(','), metavar='REF,...',
                    help='edge strip: mirror the positions of these hand-placed parts across the strip\'s vertical '
                         'centre line (first ref is the IO rail header, named in the render); rotations are kept, '
                         'a pad pattern cannot be mirrored (dry run unless --apply)')
    ap.add_argument('--axis', type=float, metavar='X',
                    help='--mirror: x of the mirror line in mm (default: the centre of the strip\'s own box)')
    ap.add_argument('--strip', metavar='RAIL',
                    help='slot strip: lay the four keyed power rows, their fuses and caps on the 2.54 mm lattice of '
                         'this 2x32 rail header (J3 or J5), see the docstring (dry run unless --apply)')
    ap.add_argument('--rail-at', metavar='X,Y', type=lambda v: tuple(float(t) for t in v.split(',')),
                    help='--strip: move the rail header itself to this origin first (rotation kept)')
    ap.add_argument('--list-anchors', action='store_true', help='list every anchor with its island size and exit')
    ap.add_argument('--check-geometry', action='store_true', help='cross-check pad and courtyard geometry against pcbnew and exit')
    args = ap.parse_args()

    board = Board(args.board)
    if args.check_geometry:
        sys.exit(check_geometry(board))

    if args.strip:
        anchor, members, info = strip_layout(board, args.strip, args.rail_at)
        print(f'SLOT STRIP {anchor.ref}: rows x {info["rows"][0]:.2f} / {info["rows"][1]:.2f}, columns y '
              f'{info["cols"][0]:.2f} .. {info["cols"][-1]:.2f} step 2.54; power side {"+x" if info["sign"] > 0 else "-x"}')
        print(f'  header line x = {info["x_h"]:.2f} (inner row {info["inner"]:.2f} {"+" if info["sign"] > 0 else "-"} 2 x 2.54), '
              f'key posts x = {info["x_k"]:.2f} (one more pitch), AUX fuses x = {info["x_aux"]:.2f}, stack x = {info["x_c"]:.2f}; '
              f'edge margin {info["edge_margin"]:.2f} mm')
        for sec in info['sections']:
            print(f'  slot {sec["slot"]}: columns y {sec["y0"]:.2f}..{sec["y7"]:.2f}; header {sec["header"]} pins {sec["pins"]}; '
                  f'post {sec["post"]} at column 8; AUX {sec["aux"]}; stack {sec["stack"]} '
                  f'({sec["stack_len"]:.2f} mm on a {sec["hdr_len"]:.2f} mm header body)')
        for line in info['notes']:
            print(f'  {line}')
        if info['overlaps']:
            print(f'  OVERLAPS: {", ".join(info["overlaps"])}')
        print_moves(members)
        render_path = args.render or os.path.join(RENDER_DIR, f'{anchor.ref}-strip.svg')
        title = f'islands.py --strip {anchor.ref}' + (' --apply' if args.apply else ' (dry run)')
        locks = {ref: (True, 'hand placement') for ref in board.fps}
        render(render_path, board, anchor, members, None, title, locks)
        print(f'\nrender: {os.path.relpath(render_path, ROOT)}')
        moves = {m.ref: m for m in members if m.status == 'move'}
        if not args.apply:
            print('dry run: nothing written. Add --apply to write the pcb.')
            return
        if info['overlaps']:
            sys.exit('REFUSED: the strip layout would overlap')
        open(args.board, 'w', encoding='utf-8').write(apply_edits(board.text, plan_edits(board, members)))
        errs = verify_written(args.board, moves, board)
        if errs:
            open(args.board, 'w', encoding='utf-8').write(board.text)
            print('\n'.join('  ' + e for e in errs[:20]))
            sys.exit('WRITE VERIFICATION FAILED; the original file was restored')
        print(f'wrote {os.path.relpath(args.board, ROOT)}: {len(moves)} footprint(s) moved')
        run_drc(args.board)
        return

    if args.mirror:
        anchor, members, info = mirror_strip(board, args.mirror, args.axis, args.edge_margin)
        print(f'EDGE STRIP {anchor.ref}: {len(members)} parts, box x {info["box"][0]:.2f}..{info["box"][2]:.2f} '
              f'y {info["box"][1]:.2f}..{info["box"][3]:.2f}, mirror line x = {info["axis"]:.3f}')
        print(f'  rail header {anchor.ref} goes from the {info["rail_was"]} side of the strip to the {info["rail_now"]} side; '
              f'edge margin {info["edge_margin"]:.2f} mm (unchanged)')
        if info['inexact']:
            print(f'  body moved, pad pattern not mirrored (KiCad cannot; rotation kept): {" ".join(info["inexact"])}')
        print(f'  mirrored exactly (pads symmetric about the part\'s own vertical axis): {" ".join(info["exact"])}')
        if info['overlaps']:
            print(f'  OVERLAPS footprints outside the strip: {", ".join(info["overlaps"])}')
        print_moves(members)
        render_path = args.render or os.path.join(RENDER_DIR, f'{anchor.ref}-mirror.svg')
        title = f'islands.py --mirror {anchor.ref} strip' + (' --apply' if args.apply else ' (dry run)')
        locks = {ref: (True, 'hand placement') for ref in board.fps}
        render(render_path, board, anchor, members, None, title, locks)
        print(f'\nrender: {os.path.relpath(render_path, ROOT)}')
        moves = {m.ref: m for m in members if m.status == 'move'}
        if not args.apply:
            print('dry run: nothing written. Add --apply to write the pcb.')
            return
        if info['overlaps']:
            sys.exit('REFUSED: the mirrored strip would overlap footprints outside it')
        open(args.board, 'w', encoding='utf-8').write(apply_edits(board.text, plan_edits(board, members)))
        errs = verify_written(args.board, moves, board)
        if errs:
            open(args.board, 'w', encoding='utf-8').write(board.text)
            print('\n'.join('  ' + e for e in errs[:20]))
            sys.exit('WRITE VERIFICATION FAILED; the original file was restored')
        print(f'wrote {os.path.relpath(args.board, ROOT)}: {len(moves)} footprint(s) moved')
        run_drc(args.board)
        return

    if args.city:
        import yaml
        plan = yaml.safe_load(open(args.city))
        edits, moved = city_edits(board, plan)
        edits = plan_edits(board, moved) + edits
        print(f'CITY PLAN {os.path.relpath(args.city, ROOT)} ({plan.get("variant")}): '
              f'{len(plan.get("islands") or {})} island groups, {len(moved)} footprints move as rigid groups')
        if not args.apply:
            print('dry run: nothing written. Add --apply to write the pcb.')
            return
        open(args.board, 'w', encoding='utf-8').write(apply_edits(board.text, edits))
        moves = {m.ref: m for m in moved}
        errs = verify_written(args.board, moves, board)
        if errs:
            open(args.board, 'w', encoding='utf-8').write(board.text)
            print('\n'.join('  ' + e for e in errs[:20]))
            sys.exit('WRITE VERIFICATION FAILED; the original file was restored')
        print(f'wrote {os.path.relpath(args.board, ROOT)}: {len(moved)} footprint(s) moved')
        run_drc(args.board)
        return

    families = load_locks(args.locks)
    island_of = board.island_groups()
    design = load_design()
    locks = {ref: lock_state(fp, board, island_of, args.anchor, families, design[0])
             for ref, fp in board.fps.items()}
    reclaimed = {ref for ref, (lk, why) in locks.items() if not lk and why.startswith('reclaimed')}

    # single-sided assembly
    back = sorted(ref for ref, fp in board.fps.items() if not locks[ref][0] and fp.layer != 'F.Cu')
    if back:
        print_lock_table(board, locks)
        sys.exit(f'REFUSED: unlocked footprint(s) not on F.Cu: {", ".join(back)}. '
                 f'The board is assembled on one side; flip them in KiCad first.')
    back_locked = sorted(ref for ref, fp in board.fps.items() if fp.layer != 'F.Cu')
    if back_locked:
        print(f'  note: locked footprint(s) on the back: {", ".join(back_locked)} (pad geometry would be mirrored; '
              f'they are only used as obstacles)')
        sys.exit('REFUSED: this tool assumes every footprint is on F.Cu')

    anchors = {ref for ref, fp in board.fps.items() if locks[ref][0] and len(fp.pads) > 3}
    if args.anchor:
        if args.anchor not in board.fps:
            sys.exit(f'{args.anchor}: no such footprint')
        if not locks[args.anchor][0]:
            sys.exit(f'{args.anchor} is not locked; anchors must be locked (edit {os.path.relpath(args.locks, ROOT)})')
        anchors.add(args.anchor)

    print_lock_table(board, locks)
    print()
    members, chain_rails = extract(board, locks, anchors, design, args.short_net_max_pads)

    if args.list_anchors:
        counts = {}
        for m in members.values():
            if m.anchor:
                counts.setdefault(m.anchor, []).append(m.ref)
        print('\nANCHORS (locked, more than three pads) and their islands')
        for a in sorted(anchors, key=natural):
            refs = sorted(counts.get(a, []), key=natural)
            rails = ', '.join(sorted(chain_rails.get(a, {}))) or '-'
            print(f'  {a:6s} {board.fps[a].value[:24]:24s} {len(refs):3d} parts  chain rail: {rails:10s} {wrap(refs, indent=0, width=70).splitlines()[0] if refs else ""}')
        unassigned = sorted((m for m in members.values() if not m.anchor), key=lambda m: natural(m.ref))
        print(f'\n  unassigned ({len(unassigned)}):')
        for m in unassigned:
            print(f'    {m.ref:6s} {m.fp.value[:20]:20s} {"; ".join(m.notes)}')
        return
    if not args.anchor:
        ap.error('--anchor is required (or --list-anchors)')

    anchor = board.fps[args.anchor]
    for ref in (args.with_ or []):
        m = members.get(ref)
        if m is None:
            sys.exit(f'--with {ref}: not a movable part (locked, or no such footprint)')
        shared = [p for p in anchor.pads if p.net and p.net in m.fp.nets() and p.net != GND]
        if not shared:
            sys.exit(f'--with {ref}: shares no net with {anchor.ref} except GND')
        pad = min(shared, key=lambda p: dist(m.pos(), anchor.pad_pos(p)))
        m.anchor, m.pad, m.via, m.hops, m.role, m.dest = anchor.ref, pad, pad.net, 1, 'signal', None
        m.notes.append(f'pulled into {anchor.ref} by --with (pad {pad.number}, {pad.net})')
    island = [m for m in members.values() if m.anchor == args.anchor and m.ref not in (args.without or [])]
    if args.island_net:
        if args.island_net not in board.nets:
            sys.exit(f'net {args.island_net!r} not on the board')
        island = [m for m in island if args.island_net in m.fp.nets()]
    chains = build_chains(board, members, args.anchor, chain_rails, design, args.short_net_max_pads)
    if args.island_net:
        for ch in chains:
            ch['seq'] = [m for m in ch['seq'] if m in island]
        chains = [ch for ch in chains if ch['seq']]
    related = sorted((m.ref for m in members.values() if m.dest == args.anchor and m.anchor != args.anchor), key=natural)

    if anchor.pads_exceed_courtyard:
        print(f'  note: {anchor.ref}: pads extend beyond the F.CrtYd outline; the pad extent is used as its courtyard')
    pname, prof = profile_for(load_profiles(args.profiles), anchor)
    if prof:
        print(f'  profile {pname}: {prof.get("source", "no source given")}')
    else:
        print(f'  no layout profile matches {anchor.value!r}; generic ring/chain/signal rules apply '
              f'(add one to {os.path.relpath(args.profiles, ROOT)} after the datasheet audit)')
    planner = Planner(board, args.anchor, island, chains, args, locks, (pname, prof))
    if planner.chunk:
        print(f'  CHUNK MODE: {anchor.ref} is outside the board outline. The island is built as a '
              f'self-contained piece around it: pile neighbours are not obstacles, chains run '
              f'straight out, signal parts sit on their own pad\'s side. Box-select the chunk in KiCad '
              f'and drag it onto the board.')
    if args.repark or args.revert:
        if not planner.chunk:
            sys.exit(f'--repark/--revert act on a chunk in the pile; {anchor.ref} is inside the board outline')
        print(f'  {"REVERT" if args.revert else "RE-PARK"}: no layout rules run; '
              + (f'the island goes back to {os.path.relpath(args.revert, ROOT)}' if args.revert
                 else 'the island keeps its layout and moves as one body to its lot slot'))
        info = planner.keep_layout(args.revert)
    elif args.extend:
        keep = {r for r, g in board.island_groups().items() if g == f'island {anchor.ref}'} - {anchor.ref}
        if not keep:
            sys.exit(f'--extend: {anchor.ref} has no parked island group to extend')
        print(f'  EXTEND: {len(keep)} parked part(s) keep their place; laying out '
              f'{", ".join(sorted((m.ref for m in island if m.ref not in keep), key=natural)) or "nothing new"}')
        info = planner.run_extend(keep)
    else:
        info = planner.run()
    if prof and not (args.repark or args.revert):
        unmatched = sorted((m.ref for m in island if m.ref not in info['profile_matched']
                            and m.ref != anchor.ref), key=natural)
        print(f'  profile placed: {" ".join(info["profile_matched"]) or "nothing"}'
              + (f'; generic rules for: {" ".join(unmatched)}' if unmatched else ''))
    if planner.chunk and 'chunk_box' in info:
        b = info['chunk_box']
        print(f'  chunk box: x {b[0]:.2f}..{b[2]:.2f}, y {b[1]:.2f}..{b[3]:.2f} '
              f'({b[2] - b[0]:.1f} x {b[3] - b[1]:.1f} mm); select: {" ".join(info["chunk_refs"])}')
        if 'chunk_shift' in info:
            dx, dy = info['chunk_shift']
            where = 'its parking slot right of the sheet' if info.get('parked') else 'a free spot'
            print(f'  chunk shifted by ({dx:+.0f}, {dy:+.0f}) mm to {where}; {anchor.ref} moves with it')
        if info.get('park_full'):
            print('  parking lot full; nearest free spot used instead')
        if info['chunk_overlaps']:
            print(f'  overlaps pile neighbours: {", ".join(info["chunk_overlaps"])}')
    island = planner.members
    for ch, chinfo in info['chains']:
        cons = ', '.join(chinfo['consumers']) or 'none'
        print(f'  chain {ch["rail"]}: leaves the {chinfo["side"]} side heading {chinfo["direction"]}; '
              f'consumers of {ch["rail"]}: {cons}')
        if chinfo.get('note'):
            print(f'    {chinfo["note"]}')

    print_membership(board, anchor, island, chains, args.island_net)
    if related:
        print(f'  related (belong to another island, destination {args.anchor}): {", ".join(related)}')
    print_moves(island)

    net_slug = re.sub(r'[^A-Za-z0-9]+', '_', args.island_net).strip('_') if args.island_net else ''
    render_path = args.render or os.path.join(RENDER_DIR, f'{args.anchor}' + (f'-{net_slug}' if net_slug else '') + '.svg')
    title = f'islands.py --anchor {args.anchor}' + (f' --island-net {args.island_net}' if args.island_net else '') + \
            (' --apply' if args.apply else ' (dry run)')
    render(render_path, board, anchor, island, planner, title, locks)
    print(f'\nrender: {os.path.relpath(render_path, ROOT)}')

    moves = {m.ref: m for m in island if m.status == 'move'}
    if not args.apply:
        print('dry run: nothing written. Add --apply to write the pcb.')
        return
    if not moves:
        print('nothing to write.')
        return
    edits = plan_edits(board, island)
    if planner.chunk and 'chunk_box' in info:
        note = make_note(pname, len(info['chunk_refs']))
        took = sorted(reclaimed & set(info['chunk_refs']), key=natural)
        edits += marker_edits(board, anchor.ref, info['chunk_box'], note, info['chunk_refs'], take=took)
        print(f'  marker: dashed box with a title bar on {MARK_LAYER}, grouped with the parts as "island {anchor.ref}"'
              + (f'; taken out of their old island groups: {" ".join(took)}' if took else ''))
    new_text = apply_edits(board.text, edits)
    open(args.board, 'w', encoding='utf-8').write(new_text)
    errs = verify_written(args.board, moves, board)
    if errs:
        open(args.board, 'w', encoding='utf-8').write(board.text)
        print('\n'.join('  ' + e for e in errs))
        sys.exit('WRITE VERIFICATION FAILED; the original file was restored')
    print(f'wrote {os.path.relpath(args.board, ROOT)}: {len(moves)} footprint(s) moved, '
          f'{len(edits)} (at ...) edits, everything else byte for byte unchanged')
    run_drc(args.board)
    print(f'render: {os.path.relpath(render_path, ROOT)}  (inspect before committing; one island per commit)')


if __name__ == '__main__':
    main()
