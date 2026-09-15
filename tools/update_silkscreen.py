#!/usr/bin/env python3
"""Give user-facing parts plain top-silk labels without moving footprints.

References such as J52 and SW1 belong on the fabrication drawing. The top
silk says what a human can plug in, press or select. Extra jumper-choice
labels are footprint fields, so they move and rotate with the footprint.
"""
import re
import pcbnew
from identity import PRODUCT, HW_VERSION

BOARD = 'kicad/odin.kicad_pcb'
NETLIST = 'kicad/odin.net'

USER_LABELS = {
    'D9': 'CTRL HB', 'D10': 'USER 1', 'D11': 'USER 2',
    'D1': 'FPGA DONE', 'SW1': 'CTRL BOOT',
    'J1': 'USB-C', 'J2': 'FPGA JTAG',
    'J3': 'A | B', 'J4': 'C | D', 'J5': 'E | F', 'J6': 'G | H',
    'J53': 'A | B POWER', 'J54': 'C | D POWER',
    'J55': 'E | F POWER', 'J56': 'G | H POWER',
    'J7': '5V BUS 0', 'J8': '5V BUS 1',
    'J57': '5V BUS 0 POWER', 'J58': '5V BUS 1 POWER',
    **{f'J{10+i}': f'SLOT {s} POWER' for i, s in enumerate('LABCDEFGH')},
    'J21': '5V BUS 1 POWER SELECT',
    'J19': 'A-D PIN VOLTAGE', 'J20': 'E-H PIN VOLTAGE',
    'J50': 'OPTIONAL POWER IN', 'J51': 'CTRL SWD', 'J52': 'EXT JTAG',
    'J60': 'SFP 0', 'J61': 'SFP 1',
    **{f'MK{ord(s)}': f'GUIDE {s}' for s in 'ABCDEFGHLM'},
}

ROLE_LABELS = {
    'U1': 'PROGRAMMABLE LOGIC',
    'U2': 'WORK MEMORY 0', 'U3': 'WORK MEMORY 1',
    'U4': 'WORK MEMORY 2', 'U5': 'WORK MEMORY 3',
    'U6': 'FPGA STARTUP MEMORY',
    'U7': 'BOARD CONTROLLER',
    'U8': 'CONTROLLER MEMORY',
    'U9': '5V BUS 0 CONVERTER', 'U10': '5V BUS 1 CONVERTER',
    'U11': '5V SUPPLY', 'U12': '3V3 SUPPLY\nALWAYS ON',
    'U13': '2V5 SUPPLY', 'U14': '1V8 SUPPLY',
    'U15': '1V0 SUPPLY\nFPGA CORE', 'U16': '1V2 SUPPLY\nFAST LINKS',
    'U17': 'OPTIONAL SFP CONTROL', 'U18': 'USB POWER REQUEST',
    'U19': '12V SUPPLY\nSLOT POWER', 'U20': 'JTAG OWNER',
    'U21': 'SLOT 5V PROTECTION', 'U22': 'SLOT 3V3 PROTECTION',
    'U23': 'A-D PIN PROTECTION', 'U24': 'E-H PIN PROTECTION',
    'U25': '12V SLOT PROTECTION', 'U26': 'USB INPUT PROTECTION',
    'X2': 'LINK CLOCK\n125MHz',
}

# These are populated from the schematic value instead of duplicated here.
# If a later cost-driven revision changes either device, regenerating the PCB
# changes the printed identity as well.  Put the text outside the package so it
# remains readable after assembly.
PART_ID_OFFSETS = {
    'U1': (0.0, 16.0),
    'U7': (0.0, 7.0),
}

def add_field(fp, name, text, x_mm, y_mm, size_mm=0.8):
    if fp.HasFieldByName(name):
        fp.RemoveField(name)
    field = pcbnew.PCB_FIELD(fp, fp.GetNextFieldId(), name)
    field.SetText(text)
    field.SetLayer(pcbnew.F_SilkS)
    field.SetVisible(True)
    field.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(size_mm), pcbnew.FromMM(size_mm)))
    field.SetTextThickness(pcbnew.FromMM(0.15))
    field.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
    field.SetFPRelativePosition(pcbnew.VECTOR2I(pcbnew.FromMM(x_mm), pcbnew.FromMM(y_mm)))
    fp.AddField(field)

def main():
    board = pcbnew.LoadBoard(BOARD)
    netlist = open(NETLIST).read()
    schematic_values = {}
    section = netlist[netlist.index('(components'):netlist.index('(libparts')]
    for chunk in section.split('(comp (ref "')[1:]:
        ref = chunk[:chunk.index('"')]
        value = re.search(r'\(value "([^"]*)"\)', chunk)
        if value:
            schematic_values[ref] = value.group(1)

    # Keep the current laid-out board stamped as well as fresh boards emitted
    # by gen_pcb.py. This is the permanent identity when flash is rewritten.
    version_text = f'{PRODUCT} HW {HW_VERSION}'
    version_found = False
    for drawing in board.GetDrawings():
        if not hasattr(drawing, 'GetText'):
            continue
        if re.fullmatch(r'ODIN(?: HW .*)?', drawing.GetText()):
            drawing.SetText(version_text)
            drawing.SetLayer(pcbnew.F_SilkS)
            version_found = True
    if not version_found:
        raise SystemExit('missing managed ODIN hardware-version silkscreen text')
    found = set()
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref in schematic_values:
            fp.SetValue(schematic_values[ref])
        # Manufacturing identifiers remain available, but do not clutter the
        # interface a person sees while using the board.
        fp.Reference().SetLayer(pcbnew.F_Fab)
        fp.Reference().SetVisible(True)
        if ref not in USER_LABELS:
            continue
        found.add(ref)
        # Keep the schematic value for BOM/parity; UI text is a separate field.
        label_pos = fp.Value().GetFPRelativePosition()
        add_field(fp, 'UI_LABEL', USER_LABELS[ref],
                  pcbnew.ToMM(label_pos.x), pcbnew.ToMM(label_pos.y), 1.0)
        fp.Value().SetLayer(pcbnew.F_Fab)
        fp.Value().SetVisible(False)

        if ref in {f'J{i}' for i in range(10, 19)} | {'J21'}:
            add_field(fp, 'UI_CHOICES', '12V\n5V\n3V3', -4.0, 0.0)
            add_field(fp, 'UI_RULE', 'ONE ROW ONLY', -4.0, 7.0, 0.7)
        elif ref in {'J19', 'J20'}:
            add_field(fp, 'UI_CHOICES', '3V3\n2V5\n1V8', -4.0, 0.0)
            add_field(fp, 'UI_RULE', 'ONE ROW ONLY', -4.0, 7.0, 0.7)
        elif ref == 'J50':
            add_field(fp, 'UI_PINS', '9-14V +\nGND', -4.0, 0.0)
        elif ref == 'J52':
            add_field(fp, 'UI_STATES', 'OPEN: CTRL\nFIT: EXT', -4.0, 0.0)

    # Role labels explain the board at a glance without replacing exact part
    # identities on F.Fab.
    role_found = set()
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref not in ROLE_LABELS:
            continue
        role_found.add(ref)
        add_field(fp, 'UI_ROLE', ROLE_LABELS[ref], 0.0, 4.0)

    part_ids_found = set()
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref not in PART_ID_OFFSETS:
            continue
        exact_part = schematic_values.get(ref)
        if not exact_part:
            raise SystemExit(f'missing exact schematic part identity for {ref}')
        part_ids_found.add(ref)
        x, y = PART_ID_OFFSETS[ref]
        add_field(fp, 'PART_ID', exact_part, x, y, 0.8)

    missing = set(USER_LABELS) - found
    if missing:
        raise SystemExit('missing user-facing footprints: ' + ', '.join(sorted(missing)))
    missing_roles = set(ROLE_LABELS) - role_found
    if missing_roles:
        raise SystemExit('missing role-labelled footprints: ' + ', '.join(sorted(missing_roles)))
    missing_part_ids = set(PART_ID_OFFSETS) - part_ids_found
    if missing_part_ids:
        raise SystemExit('missing silk part identities: ' + ', '.join(sorted(missing_part_ids)))
    pcbnew.SaveBoard(BOARD, board)
    print(f'updated {len(found)} controls/connectors and {len(role_found)} role labels; '
          f'HW {HW_VERSION} and {len(part_ids_found)} exact part identities on F.SilkS; '
          'all references moved to F.Fab')

if __name__ == '__main__':
    main()
