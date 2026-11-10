#!/usr/bin/env python3
"""Board stackup, net classes and design rules for kicad/odin.kicad_pcb.

    python3 tools/gen_pcb.py --rules-only   # the only form to use on the live board

8 layers, JLC08161H-1080A (ref/jlc08161h-1080a-stackup.json): S-G-S-P-G-S-G-S.
Without --rules-only it emits an empty board, which destroys placement."""
import argparse
import json
from pathlib import Path

from identity import PRODUCT, HW_VERSION, FPGA_PART, CONTROLLER_PART
W, H, C = 100.0, 140.0, 2.0        # board size and 45 degree corner chamfer
X0, Y0 = 156.882, 84.805           # top-left corner: slot axis - W/2; bottom edge on the jack faces
OUT = 'kicad/odin.kicad_pcb'

# JLC08161H-1080A keeps the JLC06161H-1080B outer prepreg (1080, 0.0764 mm,
# Dk 3.91), so the saved coated-microstrip solver result for 100 ohm on
# L1/L2 and L8/L7 still holds: W1 = 3.8828 mil at S1 = 0.200 mm, rounded to
# 0.099 mm. Inputs and response: ref/pcb-impedance.md.
DIFF_WIDTH = 0.099
DIFF_GAP = 0.200
# 50 ohm single-ended on the same outer prepreg: Hammerstad-Jensen with the
# 1.6 mil finished copper gives 50.6 ohm at 0.13 mm bare; solder mask takes
# a few ohm off, so 0.125 mm. Estimate, to be confirmed with JLC's
# calculator at order time (ref/pcb-impedance.md).
RGMII_WIDTH = 0.125
# The HDMI TMDS_33 pairs are 100 ohm differential too and share the class's
# outer-layer geometry and rules (HDMI 1.4: 100 ohm +/-15 %).
LVDS_PATTERNS = ('LINK_*', 'HDMI_CLK_*', 'HDMI_D0_*', 'HDMI_D1_*', 'HDMI_D2_*')
# J73's pads are 0.5 mm pitch with a GND pad between P and N. A 0.099 mm track on
# a pad centre is 0.3005 mm from its neighbours, under the 0.31 mm pair rule, and
# 2 x 0.5 - 0.099 = 0.901 mm from its partner, over the 0.200 mm pair gap. The
# exceptions are limited to these nets and to tracks wholly inside a rule area
# the board owns: F.Cu x 234.95-240.85, y 214.19-215.40. Foreign copper at 0.300 mm
# is allowed against J73's pads only; the pair may open from the coupled 0.200 mm
# to the pad-centre 0.901 mm. If the area is missing the conditions are false and
# the normal rules apply, so the entries fail loudly.
HDMI_TMDS_PATTERNS = ('HDMI_CLK_*', 'HDMI_D0_*', 'HDMI_D1_*', 'HDMI_D2_*')
HDMI_ENTRY_AREA = 'J73_TMDS_ENTRY'
HDMI_ENTRY_CLEARANCE = 0.3
HDMI_ENTRY_PAIR_PITCH = 2 * 0.5
HDMI_ENTRY_GAP_MAX = round(HDMI_ENTRY_PAIR_PITCH - DIFF_WIDTH, 3)
# J71 and J72 contacts are 1.02 mm apart along the rows, staggered 1.78 mm, 1.524 mm
# across. A 0.099 mm track on a south-row contact's axis passes between two north-row
# contacts with 1.02 - 0.762 - 0.0495 = 0.2085 mm a side, so 0.31 mm cannot be met; the
# limit here is 0.200 mm, on LINK tracks wholly inside the rule areas the board owns and
# against those two jacks' pads only. If an area is missing the conditions are false and
# the normal rule applies, so the entries fail loudly. No local pair-gap rule: the part of
# an entry beside its partner lies inside the north-row pad, which the gap check skips.
LINK_ENTRY_AREAS = ('J71_LINK_ENTRY', 'J72_LINK_ENTRY')
LINK_ENTRY_CLEARANCE = 0.2
MDI_PATTERNS = ('ETH_MDI*',)
# U30 launch: pads 0.2 mm wide on 0.4 mm pitch, so a 0.099 mm track on a pad centre is
# 0.4 - 0.1 - 0.0495 = 0.2505 mm from the next pad; MDI1_N then threads about 0.17 mm between
# pad 6's corner and MDI1_P's via, because parts sit 0.74 mm under the toes. MDI tracks
# wholly inside the rule area the board owns, against U30's pads only. If the area is
# missing the condition is false and the normal rule applies, so the launch fails loudly.
MDI_LAUNCH_AREA = 'U30_MDI_LAUNCH'
MDI_LAUNCH_CLEARANCE = 0.17
# Pads 4-7 leave one pair's N beside the next pair's P at the same 0.4 mm pitch, then round
# MDI1_N's via: 0.168 mm at worst, measured. Other pairs only, tracks and vias, in the same area.
MDI_LAUNCH_PAIR_CLEARANCE = 0.16
# Supply pins 3 and 8 sit between MDI pads, so their PHY_1V0 exits cannot keep 0.31 mm from the
# MDI tracks beside them: 0.2786 mm at worst, measured. Both tracks wholly inside the area, on
# PHY_1V0 only; a via keeps 0.31.
MDI_LAUNCH_SUPPLY_CLEARANCE = 0.27
RGMII_PATTERNS = ('PHY_TXC', 'PHY_TXD?', 'PHY_TX_CTL', 'PHY_RXC', 'PHY_RXD?', 'PHY_RX_CTL',
                  'PHY_TXC_U30', 'PHY_TXD?_U30', 'PHY_TX_CTL_U30')
# The SDR SDRAM bus (W9825G6KH-6, 3.3 V single-ended, target 100 MHz CL3) uses
# 0.125 mm, about 50 ohm on all four signal layers; CLK has its 22 ohm at the
# FPGA. Delay limits, not equal lengths: see ref/pcb-impedance.md.
SDRAM_PATTERNS = ('SDRAM_*',)
# +5V_BUCK is in PWR_3A, 1.5 mm or wider, and that holds for its load path: L2, the
# output capacitors and the way on to U34. U11's feedback sense branch is on the same
# net and carries the divider's 40 uA. On F.Cu it runs from C189.1 between pin 1 and
# L2, under the package between the exposed pad and the tips of pins 1 to 4, and round
# the pad's north vias to R55.1; 0.8 mm is all the package leaves, so the branch is
# 0.2 mm. The exception is limited to this net, to F.Cu, and to tracks wholly inside a
# rule area the board owns: a strip 0.5 mm wide along that route, in which nothing
# 1.5 mm wide fits, so the load path cannot use it. Clearances are not changed. The
# rule stands after "input path 3A" because KiCad lets the later rule win. If the area
# is missing the condition is false and 1.5 mm applies, so the branch fails loudly.
U11_SENSE_NET = '+5V_BUCK'
U11_SENSE_AREA = 'U11_SENSE'
U11_SENSE_WIDTH = 0.2
# U34 (TPS2121, VQFN-HR 12): IN2 (+5V_BUCK) and IN1 (VBUS) are 0.40 x 1.05 mm pins with a
# pin of another net 0.30 mm away on both sides (OUT above, CP2 or PR1 below), so no 1.5 mm
# copper can touch them: 0.15 mm clearance leaves 0.70 mm. Each pin gets a 0.5 mm neck,
# shorter than 2 mm, wholly inside its own rule area, into the 1.5 mm copper and the 0.8 mm
# vias beside the pin. The two 100k divider taps of VBUS (R162, R164, PR1 and OV1) carry
# 50 uA each: 0.25 mm inside U34_VBUS_TAPS (F.Cu stubs into the pads) and U34_VBUS_TAPS_IN2
# (the In2 hop from the IN1 via). Q7's gate divider (R201, 100k) reads VIN_EXT before D4:
# its tap is 0.2 mm inside VIN_EXT_TAP, a 0.5 mm strip along that route and nothing else.
U34_NECK_NETS = ('+5V_BUCK', 'VBUS')
U34_NECK_AREAS = ('U34_NECK_IN2', 'U34_NECK_IN1')
U34_NECK_WIDTH = 0.5
U34_TAP_AREAS = ('U34_VBUS_TAPS', 'U34_VBUS_TAPS_IN2')
U34_TAP_WIDTH = 0.25
VIN_EXT_TAP_AREA = 'VIN_EXT_TAP'
VIN_EXT_TAP_WIDTH = 0.2
# Input tree (2026-11-09). J1's VBUS pads are 0.60 x 1.45 mm with GND 0.20 mm and a CC pad 0.25 mm away: a 0.6 mm
# neck of at most 0.9 mm inside J1_VBUS_NECK_W / J1_VBUS_NECK_E joins each pair to 1.5 mm copper. U18's VIN pin is
# 0.28 x 0.67 mm on 0.5 mm pitch: a 0.28 mm neck of at most 1.0 mm inside U18_VIN_NECK. U26's IN pins 9 and 10 (north
# face, 0.28 x 0.67 mm on 0.5 mm pitch) reach the IN bar and C187's pad by 0.28 mm necks of at most 0.8 mm inside
# U26_IN_NECKS; its OUT pins 7 and 8 (north face) reach the OUT bar by one 0.28 mm track inside U26_OUT_NECKS, 0.22 mm
# of it beyond pin 7. R50 (110k, the UVLO/OVP divider, 33 uA) reads VBUS by a 0.2 mm tap inside U26_VBUS_TAP. R81 (100k,
# the VSYS monitor divider, 80 uA) reads VSYS by a 0.2 mm tap on In2 and F.Cu inside VSYS_MON_TAP.
J1_NECK_AREAS = ('J1_VBUS_NECK_W', 'J1_VBUS_NECK_E')
J1_NECK_WIDTH = 0.6
U18_VIN_NECK_AREA = 'U18_VIN_NECK'
U18_VIN_NECK_WIDTH = 0.28
U26_IN_NECK_AREA = 'U26_IN_NECKS'
U26_IN_NECK_WIDTH = 0.28
U26_OUT_NECK_AREA = 'U26_OUT_NECKS'
U26_OUT_NECK_WIDTH = 0.28
U26_VBUS_TAP_AREA = 'U26_VBUS_TAP'
U26_VBUS_TAP_WIDTH = 0.2
VSYS_MON_TAP_AREA = 'VSYS_MON_TAP'
VSYS_MON_TAP_WIDTH = 0.2
GENERATED = ('MGT_100R', 'LVDS_100R', 'MDI_100R', 'RGMII', 'SDRAM', 'PSRAM', 'AUX_5A', 'PWR_3A', 'EXT_2A')


TMDS_NETS = ' || '.join(f"A.NetName == '{p}'" for p in HDMI_TMDS_PATTERNS)
LINK_IN_ENTRY = ("A.Type == 'Track' && A.NetName == 'LINK_*' && ("
                 + ' || '.join(f"A.enclosedByArea('{a}')" for a in LINK_ENTRY_AREAS) + ')')
POWER_HEADERS = ' || '.join(f"B.Reference == '{r}'" for r in
                          ('J53', 'J62', 'J54', 'J63', 'J55', 'J64', 'J56', 'J65', 'J57', 'J58'))

def emit_rules():
    """Merge generated classes into the project; preserve unrelated settings."""
    path = Path(OUT).with_suffix('.kicad_pro')
    project = json.loads(path.read_text())
    settings = project['net_settings']
    default = next(c for c in settings['classes'] if c['name'] == 'Default')
    default.update(clearance=0.15, via_diameter=0.45, via_drill=0.2)
    settings['classes'] = [c for c in settings['classes'] if c['name'] not in GENERATED]
    diff = dict(default, track_width=DIFF_WIDTH, diff_pair_width=DIFF_WIDTH,
                diff_pair_gap=DIFF_GAP)
    settings['classes'] += [
        dict(diff, name='LVDS_100R', priority=0),
        dict(diff, name='MDI_100R', priority=0),
        dict(default, name='RGMII', priority=1, track_width=RGMII_WIDTH),
        dict(default, name='SDRAM', priority=1, track_width=RGMII_WIDTH),
        dict(default, name='PSRAM', priority=1, track_width=0.1),
        dict(default, name='AUX_5A', priority=2, track_width=2.0,
             via_diameter=1.0, via_drill=0.5),
        # input path at the 3 A planning current (U26 at 29.4k, J50 3 A):
        # 1.5 mm on 1 oz outer copper is about 3 A at 10 C rise (IPC-2221)
        dict(default, name='PWR_3A', priority=2, track_width=1.5,
             via_diameter=0.8, via_drill=0.4),
        # the four switched extension buses: 2 A on +5V_EXT, 1 A on the rest
        dict(default, name='EXT_2A', priority=2, track_width=1.0,
             via_diameter=0.8, via_drill=0.4),
    ]
    settings['netclass_patterns'] = [p for p in settings['netclass_patterns']
                                    if p['netclass'] not in GENERATED]
    settings['netclass_patterns'] += [dict(netclass='LVDS_100R', pattern=p) for p in LVDS_PATTERNS]
    settings['netclass_patterns'] += [dict(netclass='MDI_100R', pattern=p) for p in MDI_PATTERNS]
    settings['netclass_patterns'] += [dict(netclass='RGMII', pattern=p) for p in RGMII_PATTERNS]
    settings['netclass_patterns'] += [dict(netclass='SDRAM', pattern=p) for p in SDRAM_PATTERNS]
    settings['netclass_patterns'].append(dict(netclass='PSRAM', pattern='PSRAM*'))
    settings['netclass_patterns'].append(dict(netclass='AUX_5A', pattern='AUX_RAIL'))
    settings['netclass_patterns'] += [dict(netclass='PWR_3A', pattern=p)
                                      for p in ('VBUS', 'VBUS_SS', 'VSYS', 'VIN_EXT', '+5V_BUCK')]
    settings['netclass_patterns'] += [dict(netclass='EXT_2A', pattern=p)
                                      for p in ('+5V_EXT', '+3V3_EXT', 'VCCIO_1_EXT', 'VCCIO_2_EXT')]
    project['board']['design_settings']['rules'].update(
        min_clearance=0.15, min_track_width=0.0889,
        min_via_diameter=0.45, min_through_hole_diameter=0.2)
    path.write_text(json.dumps(project, indent=2) + '\n')
    rules = f'''# Generated by tools/gen_pcb.py; see ref/pcb-impedance.md.
(version 1)
(rule "Default clearance"
  (constraint clearance (min 0.15mm)))
(rule "PSRAM minimum width"
  (condition "A.hasNetclass('PSRAM')")
  (constraint track_width (min 0.1mm) (opt 0.1mm)))
(rule "AUX_RAIL 5A aggregate"
  (condition "A.hasNetclass('AUX_5A')")
  (constraint track_width (min 2.0mm) (opt 2.0mm)))
(rule "input path 3A"
  (condition "A.hasNetclass('PWR_3A')")
  (constraint track_width (min 1.5mm) (opt 1.5mm)))
(rule "extension buses 2A"
  (condition "A.hasNetclass('EXT_2A')")
  (constraint track_width (min 1.0mm) (opt 1.0mm)))
# U11's output sense: a {U11_SENSE_NET} track on F.Cu wholly inside the {U11_SENSE_AREA} rule area, the
# 0.5 mm strip from C189.1 under U11 to R55.1, may be {U11_SENSE_WIDTH} mm. It carries the divider's
# 40 uA. Every other {U11_SENSE_NET} track keeps "input path 3A". Later rules win, so this follows it.
(rule "U11 output sense branch"
  (layer "F.Cu")
  (condition "A.Type == 'Track' && A.NetName == '{U11_SENSE_NET}' && A.enclosedByArea('{U11_SENSE_AREA}')")
  (constraint track_width (min {U11_SENSE_WIDTH}mm) (opt {U11_SENSE_WIDTH}mm)))
# U34's input pins: a {U34_NECK_NETS[0]} or {U34_NECK_NETS[1]} track on F.Cu wholly inside {U34_NECK_AREAS[0]} or
# {U34_NECK_AREAS[1]}, the pin's own neck, may be {U34_NECK_WIDTH} mm: the 0.40 mm pin has another net 0.30 mm
# away on both sides, so the class width cannot reach it. Everything beyond the neck keeps "input path 3A".
(rule "U34 input pin necks"
  (layer "F.Cu")
  (condition "A.Type == 'Track' && (A.NetName == '{U34_NECK_NETS[0]}' || A.NetName == '{U34_NECK_NETS[1]}') && (A.enclosedByArea('{U34_NECK_AREAS[0]}') || A.enclosedByArea('{U34_NECK_AREAS[1]}'))")
  (constraint track_width (min {U34_NECK_WIDTH}mm) (opt {U34_NECK_WIDTH}mm)))
# U34's VBUS divider taps (R162.1, R164.1, 50 uA each): VBUS tracks wholly inside {U34_TAP_AREAS[0]} (F.Cu) or
# {U34_TAP_AREAS[1]} (In2) may be {U34_TAP_WIDTH} mm. The areas hold nothing but the taps.
(rule "U34 VBUS divider taps"
  (condition "A.Type == 'Track' && A.NetName == 'VBUS' && (A.enclosedByArea('{U34_TAP_AREAS[0]}') || A.enclosedByArea('{U34_TAP_AREAS[1]}'))")
  (constraint track_width (min {U34_TAP_WIDTH}mm) (opt {U34_TAP_WIDTH}mm)))
# Q7's gate divider reads VIN_EXT through R201 (100k, 0.2 mA at 21 V): a VIN_EXT track wholly inside {VIN_EXT_TAP_AREA},
# the 0.5 mm strip along that one route, may be {VIN_EXT_TAP_WIDTH} mm. The input path from J50 keeps "input path 3A".
(rule "VIN_EXT tap to Q7's divider"
  (condition "A.Type == 'Track' && A.NetName == 'VIN_EXT' && A.enclosedByArea('{VIN_EXT_TAP_AREA}')")
  (constraint track_width (min {VIN_EXT_TAP_WIDTH}mm) (opt {VIN_EXT_TAP_WIDTH}mm)))
# J1's VBUS pad pairs: a VBUS track on F.Cu wholly inside {J1_NECK_AREAS[0]} or {J1_NECK_AREAS[1]} may be {J1_NECK_WIDTH} mm,
# the 0.60 mm pad's own neck into the 1.5 mm copper below it (GND 0.20 mm and a CC pad 0.25 mm beside the pad).
(rule "J1 VBUS pin necks"
  (layer "F.Cu")
  (condition "A.Type == 'Track' && A.NetName == 'VBUS' && (A.enclosedByArea('{J1_NECK_AREAS[0]}') || A.enclosedByArea('{J1_NECK_AREAS[1]}'))")
  (constraint track_width (min {J1_NECK_WIDTH}mm) (opt {J1_NECK_WIDTH}mm)))
# U18's VIN pin (0.28 x 0.67 mm, 0.5 mm pitch): a VBUS track on F.Cu wholly inside {U18_VIN_NECK_AREA} may be {U18_VIN_NECK_WIDTH} mm.
(rule "U18 VIN pin neck"
  (layer "F.Cu")
  (condition "A.Type == 'Track' && A.NetName == 'VBUS' && A.enclosedByArea('{U18_VIN_NECK_AREA}')")
  (constraint track_width (min {U18_VIN_NECK_WIDTH}mm) (opt {U18_VIN_NECK_WIDTH}mm)))
# U26's IN pins 9 and 10 (0.28 x 0.67 mm, 0.5 mm pitch, OUT pin 8 beside pin 9): a VBUS track on F.Cu wholly inside
# {U26_IN_NECK_AREA} may be {U26_IN_NECK_WIDTH} mm. Pins 11 to 13 are covered by the 1.5 mm bar.
(rule "U26 IN pin necks"
  (layer "F.Cu")
  (condition "A.Type == 'Track' && A.NetName == 'VBUS' && A.enclosedByArea('{U26_IN_NECK_AREA}')")
  (constraint track_width (min {U26_IN_NECK_WIDTH}mm) (opt {U26_IN_NECK_WIDTH}mm)))
# U26's OUT pins 7 and 8 (north face): a VBUS_SS track on F.Cu wholly inside {U26_OUT_NECK_AREA} may be {U26_OUT_NECK_WIDTH} mm.
(rule "U26 OUT pin necks"
  (layer "F.Cu")
  (condition "A.Type == 'Track' && A.NetName == 'VBUS_SS' && A.enclosedByArea('{U26_OUT_NECK_AREA}')")
  (constraint track_width (min {U26_OUT_NECK_WIDTH}mm) (opt {U26_OUT_NECK_WIDTH}mm)))
# R50 (110k) reads VBUS for U26's UVLO and OVP thresholds, 33 uA: a VBUS track on F.Cu wholly inside {U26_VBUS_TAP_AREA} may be {U26_VBUS_TAP_WIDTH} mm.
(rule "U26 VBUS divider tap"
  (layer "F.Cu")
  (condition "A.Type == 'Track' && A.NetName == 'VBUS' && A.enclosedByArea('{U26_VBUS_TAP_AREA}')")
  (constraint track_width (min {U26_VBUS_TAP_WIDTH}mm) (opt {U26_VBUS_TAP_WIDTH}mm)))
# R81 (100k) reads VSYS for the controller's monitor, 80 uA: a VSYS track wholly inside {VSYS_MON_TAP_AREA} (F.Cu and In2) may be {VSYS_MON_TAP_WIDTH} mm.
(rule "VSYS monitor tap"
  (condition "A.Type == 'Track' && A.NetName == 'VSYS' && A.enclosedByArea('{VSYS_MON_TAP_AREA}')")
  (constraint track_width (min {VSYS_MON_TAP_WIDTH}mm) (opt {VSYS_MON_TAP_WIDTH}mm)))
# RGMII: about 50 ohm on all four signal layers. Timing is set by the derived
# delay limits in gateware/rgmii1000, not by equal lengths. The U30 side of each
# TX resistor is in this class too.
(rule "RGMII width"
  (condition "A.hasNetclass('RGMII')")
  (constraint track_width (min {RGMII_WIDTH}mm) (opt {RGMII_WIDTH}mm)))
# SDRAM: 0.125 mm is about 50 ohm on all four signal layers (48.4 outer, 49.1
# inner, field solve). Target 100 MHz, CL3. Equal lengths are not required: use
# the derived delay limits in ref/pcb-impedance.md. Above 100 MHz, reassess.
(rule "SDRAM width"
  (condition "A.hasNetclass('SDRAM')")
  (constraint track_width (min {RGMII_WIDTH}mm) (opt {RGMII_WIDTH}mm)))
# 100 ohm differential pairs: the LVDS_25 link pairs and the PHY's MDI pairs.
# Geometry is calculated only for L1 over In1 and B.Cu over In6.
(rule "100R outer geometry"
  (layer outer)
  (condition "A.hasNetclass('LVDS_100R') || A.hasNetclass('MDI_100R')")
  (constraint track_width (min {DIFF_WIDTH}mm) (opt {DIFF_WIDTH}mm) (max {DIFF_WIDTH}mm))
  (constraint diff_pair_gap (min {DIFF_GAP}mm) (opt {DIFF_GAP}mm) (max {DIFF_GAP}mm)))
(rule "100R outer routing only"
  (layer inner)
  (condition "A.hasNetclass('LVDS_100R') || A.hasNetclass('MDI_100R')")
  (constraint disallow track))
# Keep other copper >= ~4 dielectric heights away from the pair tracks for
# the non-coplanar model. Pads are not held to it as the first item, but a pair
# track is held to it against any pad.
(rule "100R clearance to other copper"
  (condition "A.Type == 'Track' && (A.hasNetclass('LVDS_100R') || A.hasNetclass('MDI_100R')) && !AB.isCoupledDiffPair()")
  (constraint clearance (min 0.31mm)))
# J73 pad entry: at 0.5 mm pitch a 0.099 mm track on a pad centre is 0.3005 mm
# from the next pad, so 0.31 mm cannot be met, and P and N run {HDMI_ENTRY_PAIR_PITCH:.1f} mm apart
# with a GND pad between, so the gap is {HDMI_ENTRY_GAP_MAX} mm. HDMI TMDS tracks wholly inside the
# {HDMI_ENTRY_AREA} rule area only. These must follow the rules above.
(rule "HDMI TMDS entry to J73 pads"
  (layer "F.Cu")
  (condition "A.Type == 'Track' && ({TMDS_NETS}) && A.enclosedByArea('{HDMI_ENTRY_AREA}') && B.Type == 'Pad' && B.memberOfFootprint('J73') && !AB.isCoupledDiffPair()")
  (constraint clearance (min {HDMI_ENTRY_CLEARANCE}mm)))
(rule "HDMI TMDS entry pair gap at J73"
  (layer "F.Cu")
  (condition "A.Type == 'Track' && ({TMDS_NETS}) && A.enclosedByArea('{HDMI_ENTRY_AREA}')")
  (constraint diff_pair_gap (min {DIFF_GAP}mm) (opt {DIFF_GAP}mm) (max {HDMI_ENTRY_GAP_MAX}mm)))
# J71/J72 contact entries: a 0.099 mm track between 1.524 mm contacts on 2.04 mm pitch has
# 0.2085 mm a side. LINK tracks wholly inside {LINK_ENTRY_AREAS[0]} or {LINK_ENTRY_AREAS[1]}, against those jacks' pads only.
(rule "LINK entry to J71 J72 pads"
  (layer outer)
  (condition "{LINK_IN_ENTRY} && B.Type == 'Pad' && (B.memberOfFootprint('J71') || B.memberOfFootprint('J72')) && !AB.isCoupledDiffPair()")
  (constraint clearance (min {LINK_ENTRY_CLEARANCE}mm)))
# U30 MDI launch: on a 0.4 mm pitch pad centre a 0.099 mm track is 0.2505 mm from the next
# pad, and one lane has about 0.17 mm at a pad corner. MDI tracks wholly inside {MDI_LAUNCH_AREA}, against U30 pads only.
(rule "MDI launch to U30 pads"
  (layer "F.Cu")
  (condition "A.Type == 'Track' && A.NetName == 'ETH_MDI*' && A.enclosedByArea('{MDI_LAUNCH_AREA}') && B.Type == 'Pad' && B.memberOfFootprint('U30') && !AB.isCoupledDiffPair()")
  (constraint clearance (min {MDI_LAUNCH_CLEARANCE}mm)))
# MDI to another MDI pair in {MDI_LAUNCH_AREA}, tracks and vias: not between coupled partners, which keep the 0.200 mm gap.
(rule "MDI launch to other MDI pairs"
  (layer "F.Cu")
  (condition "A.Type == 'Track' && A.NetName == 'ETH_MDI*' && A.enclosedByArea('{MDI_LAUNCH_AREA}') && (B.Type == 'Track' || B.Type == 'Via') && B.NetName == 'ETH_MDI*' && !AB.isCoupledDiffPair()")
  (constraint clearance (min {MDI_LAUNCH_PAIR_CLEARANCE}mm)))
# PHY_1V0 exits of U30 pins 3 and 8 between MDI tracks in {MDI_LAUNCH_AREA}: both tracks wholly inside it. A PHY_1V0 via keeps 0.31 mm.
(rule "MDI launch to PHY_1V0 exits"
  (layer "F.Cu")
  (condition "A.Type == 'Track' && A.NetName == 'ETH_MDI*' && A.enclosedByArea('{MDI_LAUNCH_AREA}') && B.Type == 'Track' && B.NetName == 'PHY_1V0' && B.enclosedByArea('{MDI_LAUNCH_AREA}')")
  (constraint clearance (min {MDI_LAUNCH_SUPPLY_CLEARANCE}mm)))
(rule "100R intra-pair skew"
  (condition "A.hasNetclass('LVDS_100R') || A.hasNetclass('MDI_100R')")
  (constraint skew (max 0.1mm) (within_diff_pairs)))
# The key post stands one pitch off its power header's line: the plastic clears
# by 0.07 mm, only the courtyards meet. The two 2x16 signal bodies of an edge
# stand end to end on the pitch (design.py). Named pairs only.
(rule "key post beside its power header"
  (condition "(A.Reference == 'MK*' && ({POWER_HEADERS})) || (B.Reference == 'MK*' && ({POWER_HEADERS.replace('B.Ref', 'A.Ref')}))")
  (constraint courtyard_clearance (min -1mm)))
(rule "signal bodies end to end"
  (condition "(A.Reference == 'J3A' && B.Reference == 'J3B') || (A.Reference == 'J3B' && B.Reference == 'J3A') || (A.Reference == 'J5A' && B.Reference == 'J5B') || (A.Reference == 'J5B' && B.Reference == 'J5A')")
  (constraint courtyard_clearance (min -1mm)))
'''
    Path(OUT).with_suffix('.kicad_dru').write_text(rules)
    print(f'wrote {path} net classes and {Path(OUT).with_suffix(".kicad_dru")}')


def sexpr_block(text, marker):
    """Locate one balanced block, ignoring parentheses in quoted strings."""
    start = text.index(marker)
    depth, quoted, escaped = 0, False, False
    # scan from the block's own '(' : a marker may begin with whitespace
    # ('\n\t(layers'), and a scan from there ends at once at depth 0, which
    # made update_stackup insert the 8-layer list in front of the old one
    # instead of replacing it (KiCad reads the last list: 6 layers)
    for i in range(text.index('(', start), len(text)):
        c = text[i]
        if escaped:
            escaped = False
        elif c == '\\' and quoted:
            escaped = True
        elif c == '"':
            quoted = not quoted
        elif not quoted:
            depth += (c == '(') - (c == ')')
            if depth == 0:
                return start, i + 1
    raise ValueError(f'Unterminated block: {marker}')


def update_stackup():
    """Replace only the stackup block; placement, tracks and zones stay intact."""
    path = Path(OUT)
    board = path.read_text()
    start, end = sexpr_block(board, '(stackup')
    a, b = sexpr_block(SETUP, '(stackup')
    board = board[:start] + SETUP[a:b] + board[end:]
    # The copper layer list goes with the stackup. Nothing is routed yet, so
    # adding inner layers touches no track or zone.
    start, end = sexpr_block(board, '\n\t(layers')
    board = board[:start] + '\n' + layers_block() + board[end:]
    path.write_text(board)
    print(f'updated {path}: JLC08161H-1080A 8-layer stackup and layer list; placement preserved')

LAYERS = [(0,'F.Cu','signal'), (4,'In1.Cu','signal','In1_GND'),
          (6,'In2.Cu','signal','In2_signal'), (8,'In3.Cu','signal','In3_power'),
          (10,'In4.Cu','signal','In4_GND'), (12,'In5.Cu','signal','In5_signal'),
          (14,'In6.Cu','signal','In6_GND'), (2,'B.Cu','signal'),
          (9,'F.Adhes','user','F.Adhesive'), (11,'B.Adhes','user','B.Adhesive'),
          (13,'F.Paste','user'), (15,'B.Paste','user'),
          (5,'F.SilkS','user','F.Silkscreen'), (7,'B.SilkS','user','B.Silkscreen'),
          (1,'F.Mask','user'), (3,'B.Mask','user'),
          (17,'Dwgs.User','user','User.Drawings'), (19,'Cmts.User','user','User.Comments'),
          (21,'Eco1.User','user','User.Eco1'), (23,'Eco2.User','user','User.Eco2'),
          (25,'Edge.Cuts','user'), (27,'Margin','user'),
          (31,'F.CrtYd','user','F.Courtyard'), (29,'B.CrtYd','user','B.Courtyard'),
          (35,'F.Fab','user'), (33,'B.Fab','user')]

def layers_block():
    o = ['\t(layers']
    for l in LAYERS:
        o.append(f'\t\t({l[0]} "{l[1]}" {l[2]}' + (f' "{l[3]}"' if len(l) > 3 else '') + ')')
    o.append('\t)')
    return '\n'.join(o)

# KiCad's sublayer separator is the bare word addsublayer. Written in parentheses
# it loads without complaint and keeps only the last sublayer's values, which is
# how the board lost 0.589 mm of dielectric: tools/check_stackup.py guards this.
SETUP = '''\t(setup
\t\t(pad_to_mask_clearance 0)
\t\t(allow_soldermask_bridges_in_footprints no)
\t\t(tenting front back)
\t\t(stackup
\t\t\t(layer "F.SilkS" (type "Top Silk Screen"))
\t\t\t(layer "F.Paste" (type "Top Solder Paste"))
\t\t\t(layer "F.Mask" (type "Top Solder Mask") (thickness 0.0254) (epsilon_r 3.8))
\t\t\t(layer "F.Cu" (type "copper") (thickness 0.035))
\t\t\t(layer "dielectric 1" (type "prepreg") (thickness 0.0764) (material "NP-155F 1080 RC67%") (epsilon_r 3.91) (loss_tangent 0.02))
\t\t\t(layer "In1.Cu" (type "copper") (thickness 0.0152))
\t\t\t(layer "dielectric 2" (type "core") (thickness 0.1) (material "NP-155F core") (epsilon_r 4.36) (loss_tangent 0.02))
\t\t\t(layer "In2.Cu" (type "copper") (thickness 0.0152))
\t\t\t(layer "dielectric 3" (type "prepreg") (thickness 0.2104) (material "NP-155F 7628 RC49%") (epsilon_r 4.4) (loss_tangent 0.02)
                addsublayer (thickness 0.084) (material "NP-155F 1080 RC67%") (epsilon_r 3.91) (loss_tangent 0.02)
                addsublayer (thickness 0.2104) (material "NP-155F 7628 RC49%") (epsilon_r 4.4) (loss_tangent 0.02))
\t\t\t(layer "In3.Cu" (type "copper") (thickness 0.0152))
\t\t\t(layer "dielectric 4" (type "core") (thickness 0.1) (material "NP-155F core") (epsilon_r 4.36) (loss_tangent 0.02))
\t\t\t(layer "In4.Cu" (type "copper") (thickness 0.0152))
\t\t\t(layer "dielectric 5" (type "prepreg") (thickness 0.2104) (material "NP-155F 7628 RC49%") (epsilon_r 4.4) (loss_tangent 0.02)
                addsublayer (thickness 0.084) (material "NP-155F 1080 RC67%") (epsilon_r 3.91) (loss_tangent 0.02)
                addsublayer (thickness 0.2104) (material "NP-155F 7628 RC49%") (epsilon_r 4.4) (loss_tangent 0.02))
\t\t\t(layer "In5.Cu" (type "copper") (thickness 0.0152))
\t\t\t(layer "dielectric 6" (type "core") (thickness 0.1) (material "NP-155F core") (epsilon_r 4.36) (loss_tangent 0.02))
\t\t\t(layer "In6.Cu" (type "copper") (thickness 0.0152))
\t\t\t(layer "dielectric 7" (type "prepreg") (thickness 0.0764) (material "NP-155F 1080 RC67%") (epsilon_r 3.91) (loss_tangent 0.02))
\t\t\t(layer "B.Cu" (type "copper") (thickness 0.035))
\t\t\t(layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.0254) (epsilon_r 3.8))
\t\t\t(layer "B.Paste" (type "Bottom Solder Paste"))
\t\t\t(layer "B.SilkS" (type "Bottom Silk Screen"))
\t\t\t(copper_finish "ENIG")
\t\t\t(dielectric_constraints no)
\t\t)
\t\t(pcbplotparams
\t\t\t(layerselection 0x00010fc_ffffffff)
\t\t\t(plot_on_all_layers_selection 0x0000000_00000000)
\t\t\t(disableapertmacros no) (usegerberextensions no) (usegerberattributes yes)
\t\t\t(usegerberadvancedattributes yes) (creategerberjobfile yes)
\t\t\t(dashed_line_dash_ratio 12.000000) (dashed_line_gap_ratio 3.000000)
\t\t\t(svgprecision 4) (plotframeref no) (mode 1) (useauxorigin no)
\t\t\t(dxfpolygonmode yes) (dxfimperialunits yes) (dxfusepcbnewfont yes)
\t\t\t(psnegative no) (psa4output no) (plot_black_and_white yes)
\t\t\t(sketchpadsonfab no) (plotpadnumbers no) (hidednponfab no)
\t\t\t(sketchdnponfab yes) (crossoutdnponfab yes) (subtractmaskfromsilk no)
\t\t\t(outputformat 1) (mirror no) (drillshape 1) (scaleselection 1)
\t\t\t(outputdirectory "")
\t\t)
\t)'''

def emit_board():
    o = ['(kicad_pcb', '\t(version 20241229)', '\t(generator "odin-tools")',
         '\t(generator_version "9.0")',
         '\t(general\n\t\t(thickness 1.6)\n\t\t(legacy_teardrops no)\n\t)',
         '\t(paper "A3")', layers_block()]
    # S / GND / S / PWR / GND / S / GND / S, nominal 1.6 mm ENIG.
    # JLC08161H-1080A: ref/jlc08161h-1080a-stackup.json, ref/pcb-impedance.md.
    o.append(SETUP)
    o.append('\t(net 0 "")')
    # chamfered rectangular outline
    x1, y1, x2, y2 = X0, Y0, X0 + W, Y0 + H
    seg = lambda ax, ay, bx, by: (f'\t(gr_line (start {ax} {ay}) (end {bx} {by}) '
                                  f'(stroke (width 0.1) (type default)) (layer "Edge.Cuts"))')
    o += [seg(x1+C, y1, x2-C, y1), seg(x2-C, y1, x2, y1+C),
          seg(x2, y1+C, x2, y2-C), seg(x2, y2-C, x2-C, y2),
          seg(x2-C, y2, x1+C, y2), seg(x1+C, y2, x1, y2-C),
          seg(x1, y2-C, x1, y1+C), seg(x1, y1+C, x1+C, y1)]
    # The version stamp is on the back, the assembled side has no room for it,
    # below U1's escape field and clear of the through-hole pins.
    for tx, ty, txt, sz, layer, just in (
            (x1+W/2, y1+87, f'{PRODUCT} HW {HW_VERSION}', 3.0, 'B.SilkS', 'mirror'),
            (x1+3, y1+3, f'{FPGA_PART} + {CONTROLLER_PART}  |  8 layer', 1.5, 'F.Fab', 'left')):
        o.append(f'\t(gr_text "{txt}" (at {tx} {ty}) (layer "{layer}") '
                 f'(effects (font (size {sz} {sz}) (thickness {sz/6:.2f})) (justify {just})))')
    o.append(')')
    open(OUT, 'w').write('\n'.join(o) + '\n')
    print(f"wrote {OUT}: {W}x{H}mm, 8 layers, ENIG")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rules-only', action='store_true',
                        help='update stackup and project rules, preserving board contents')
    args = parser.parse_args()
    if args.rules_only:
        update_stackup()
    else:
        emit_board()
    emit_rules()


if __name__ == '__main__':
    main()
