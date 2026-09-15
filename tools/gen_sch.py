#!/usr/bin/env python3
"""Generate kicad/odin.kicad_sch (FPGA skeleton) from tools/alloc.py.
Every ball gets a net; unassigned I/O get no-connect flags so ERC is meaningful."""
import sys, os, re, uuid, hashlib
sys.path.insert(0, os.path.dirname(__file__))
from alloc import assign, load
from identity import FPGA_PART
from collections import OrderedDict

SYMLIB = 'kicad/odin.kicad_sym'
OUT    = 'kicad/odin.kicad_sch'
PRO    = 'kicad/odin.kicad_pro'
PART   = FPGA_PART
W      = 63.5

def snap(v):
    return round(round(v / 1.27) * 1.27, 2)

def uid(*a):
    return str(uuid.UUID(hashlib.md5(('odin'+''.join(map(str,a))).encode()).hexdigest()))

RAIL = {'VCCINT':'+1V0', 'VCCBRAM':'+1V0', 'VCCAUX':'+1V8', 'VCCADC':'+1V8',
        'MGTAVCC':'+1V0_MGT', 'MGTAVTT':'+1V2_MGT',
        'VCCO_0':'+3V3', 'VCCO_12':'+3V3', 'VCCO_13':'+3V3', 'VCCO_14':'+3V3',
        'VCCO_15':'VCCIO_1', 'VCCO_16':'+3V3', 'VCCO_34':'VCCIO_2',
        'VCCO_35':'+3V3', 'VCCO_33':'+3V3',
        'GNDADC':'GND', 'VCCBATT':'GND'}
CFG = {'CCLK_0':'CFG_CCLK', 'PROGRAM_B_0':'CFG_PROG_B', 'INIT_B_0':'CFG_INIT_B',
       'DONE_0':'CFG_DONE', 'M0_0':'CFG_M0', 'M1_0':'CFG_M1', 'M2_0':'CFG_M2',
       'CFGBVS_0':'+3V3', 'TCK_0':'JTAG_TCK', 'TMS_0':'JTAG_TMS',
       'TDI_0':'JTAG_TDI', 'TDO_0':'JTAG_TDO',
       'VP_0':'GND', 'VN_0':'GND', 'VREFP_0':'GND', 'VREFN_0':'GND',
       'DXP_0':'FPGA_DXP', 'DXN_0':'FPGA_DXN'}

def net_for(ball, name, assigned):
    if ball in assigned: return assigned[ball]
    n = name.upper()
    if n.startswith('GND'): return 'GND'
    for k, v in RAIL.items():
        if n.startswith(k): return v
    if name in CFG: return CFG[name]
    # UG482 Tables 5-5/5-6: both G10 (quad 213) and G11 (quad 216)
    # stay powered. Unused RX pins go to GND; unused TX/refclk may float.
    # Each quad has its own calibration resistor to MGTAVTT.
    if n.startswith('MGT'):
        bare, _, quad = n.rpartition('_')
        if quad == '213':
            if bare == 'MGTRREF': return 'MGTRREF_213'
            if bare.startswith(('MGTPRXP', 'MGTPRXN')): return 'GND'
            return None
        if quad == '216':
            used = ('MGTPTXP0', 'MGTPTXN0', 'MGTPRXP0', 'MGTPRXN0',
                    'MGTPTXP1', 'MGTPTXN1', 'MGTPRXP1', 'MGTPRXN1',
                    'MGTREFCLK0P', 'MGTREFCLK0N', 'MGTRREF')
            if bare in used: return bare
            if bare.startswith(('MGTPRXP', 'MGTPRXN')): return 'GND'
        return None
    return None                      # unassigned HR I/O -> no-connect

def sym_units():
    """parse odin.kicad_sym -> (full lib text block, {unit_index: [(ball,name,side,x,y)]})"""
    t = open(SYMLIB).read()
    body = t[t.index(f'\t(symbol "{PART}"'):t.rindex('\t)\n)')+3]
    units = {}
    for m in re.finditer(r'\(symbol "%s_(\d+)_1"(.*?)\n\t\t\)\n' % re.escape(PART), t, re.S):
        idx = int(m.group(1)); pins = []
        for pm in re.finditer(r'\(pin \w+ line\s*\n\s*\(at ([-\d.]+) ([-\d.]+) (\d+)\)'
                              r'.*?\(name "([^"]*)".*?\(number "([^"]*)"', m.group(2), re.S):
            x, y, rot, nm, num = float(pm.group(1)), float(pm.group(2)), int(pm.group(3)), pm.group(4), pm.group(5)
            pins.append((num, nm, 'L' if rot == 0 else 'R', x, y))
        units[idx] = pins
    return body, units

PWRLIB = '/usr/share/kicad/symbols/power.kicad_sym'

def pwr_flag_def():
    """Lift the genuine PWR_FLAG out of KiCad's own library so the embedded copy
    matches byte-for-byte and ERC reports no lib_symbol_mismatch."""
    t = open(PWRLIB).read()
    i = t.index('(symbol "PWR_FLAG"')
    d, j = 1, i + len('(symbol "PWR_FLAG"')
    while d > 0:
        if t[j] == '(': d += 1
        elif t[j] == ')': d -= 1
        j += 1
    body = t[i:j].replace('(symbol "PWR_FLAG"', '(symbol "power:PWR_FLAG"', 1)
    return '\t\t' + body

def main():
    assigned, psram, sb, slots, io, other = assign()
    libblock, units = sym_units()
    o = ['(kicad_sch',
         '\t(version 20250114)', '\t(generator "odin-tools")', '\t(generator_version "9.0")',
         f'\t(uuid "{uid("root")}")', '\t(paper "User" 1400 900)',
         '\t(lib_symbols']
    o.append(libblock.replace(f'(symbol "{PART}"', f'(symbol "odin:{PART}"', 1))
    o.append(pwr_flag_def())
    o.append('\t)')

    nets_used = set()
    ncount = 0
    for ui in sorted(units):
        col, row = (ui-1) % 4, (ui-1)//4
        ox, oy = snap(180 + col*310), snap(130 + row*380)
        o.append(f'\t(symbol (lib_id "odin:{PART}") (at {ox} {oy} 0) (unit {ui})')
        o.append('\t\t(exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)')
        o.append(f'\t\t(uuid "{uid("U1",ui)}")')
        o.append(f'\t\t(property "Reference" "U1" (at {ox} {oy-100} 0) (effects (font (size 1.27 1.27))))')
        o.append(f'\t\t(property "Value" "{PART}" (at {ox} {oy-97} 0) (effects (font (size 1.27 1.27))))')
        o.append(f'\t\t(property "Footprint" "EasyEDA:FBGA-676_L27.0-W27.0-R26-C26-P1.00-BL" (at {ox} {oy} 0) (effects (font (size 1.27 1.27)) (hide yes)))')
        o.append(f'\t\t(instances (project "odin" (path "/{uid("root")}" (reference "U1") (unit {ui}))))')
        o.append('\t)')
        for num, nm, side, px, py in units[ui]:
            sx, sy = ox + px, oy - py
            net = net_for(num, nm, assigned)
            if net is None:
                o.append(f'\t(no_connect (at {sx} {sy}) (uuid "{uid("nc",num)}"))'); ncount += 1
                continue
            ex = sx - 5.08 if side == 'L' else sx + 5.08
            o.append(f'\t(wire (pts (xy {sx} {sy}) (xy {ex} {sy})) '
                     f'(stroke (width 0) (type default)) (uuid "{uid("w",num)}"))')
            o.append(f'\t(global_label "{net}" (shape passive) (at {ex} {sy} {180 if side=="L" else 0}) '
                     f'(fields_autoplaced yes) (effects (font (size 1.27 1.27)) '
                     f'(justify {"right" if side=="L" else "left"})) (uuid "{uid("gl",num)}"))')
            nets_used.add(net)

    rails = sorted(r for r in nets_used if r in
                   ('GND','+1V0','+1V8','+3V3','VCCIO_1','VCCIO_2','+1V0_MGT','+1V2_MGT'))
    for i, r in enumerate(rails):
        fx, fy = snap(60), snap(60 + i*25)
        o.append(f'\t(symbol (lib_id "power:PWR_FLAG") (at {fx} {fy} 0) (unit 1)')
        o.append('\t\t(exclude_from_sim no) (in_bom no) (on_board yes) (dnp no)')
        o.append(f'\t\t(uuid "{uid("flg",r)}")')
        o.append(f'\t\t(property "Reference" "#FLG{i}" (at {fx} {fy-4} 0) (effects (font (size 1.27 1.27)) (hide yes)))')
        o.append(f'\t\t(property "Value" "PWR_FLAG" (at {fx} {fy-6} 0) (effects (font (size 1.27 1.27))))')
        o.append(f'\t\t(instances (project "odin" (path "/{uid("root")}" (reference "#FLG{i}") (unit 1))))')
        o.append('\t)')
        o.append(f'\t(wire (pts (xy {fx} {fy}) (xy {fx} {fy+5.08})) (stroke (width 0) (type default)) (uuid "{uid("fw",r)}"))')
        o.append(f'\t(global_label "{r}" (shape passive) (at {fx} {fy+5.08} 270) '
                 f'(fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify right)) (uuid "{uid("fgl",r)}"))')

    o.append(f'\t(sheet_instances (path "/" (page "1")))')
    o.append(')')
    open(OUT, 'w').write('\n'.join(o) + '\n')
    if not os.path.exists(PRO):
        open(PRO, 'w').write('{\n  "board": {},\n  "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},\n  "meta": {"filename": "odin.kicad_pro", "version": 3},\n  "sheets": [["%s", "Root"]],\n  "text_variables": {}\n}\n' % uid("root"))
    print(f"wrote {OUT}: {sum(len(v) for v in units.values())} pins, "
          f"{len(nets_used)} nets, {ncount} no-connects, {len(rails)} power flags")

if __name__ == '__main__':
    main()
