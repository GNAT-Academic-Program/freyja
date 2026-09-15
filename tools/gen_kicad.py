#!/usr/bin/env python3
"""Generate the normalized KiCad symbol for the imported XC7A100T-FGG676.
The exact EasyEDA footprint remains in easyeda/EasyEDA.pretty.
Reproducible:  python3 tools/gen_kicad.py
Outputs kicad/odin.kicad_sym and kicad/odin.pretty/*.kicad_mod
"""
import re, os
from collections import defaultdict, OrderedDict
from identity import FPGA_PART

PKG   = 'easyeda/EasyEDA.kicad_sym'
SYM   = 'kicad/odin.kicad_sym'
PRET  = 'kicad/odin.pretty'
FPNAME= 'FBGA-676_L27.0-W27.0-R26-C26-P1.00-BL'
PART  = FPGA_PART
LCSC  = 'C1521803'
DS    = 'https://docs.amd.com/v/u/en-US/ds181_Artix_7_Data_Sheet'

def part_block():
    text = open(PKG, encoding='utf-8').read()
    start = text.index(f'(symbol "{PART}"')
    depth, pos = 1, start + len(f'(symbol "{PART}"')
    while depth:
        depth += (text[pos] == '(') - (text[pos] == ')')
        pos += 1
    return text[start:pos]

def load():
    out = []
    text = part_block()
    for m in re.finditer(r'\(pin [\s\S]*?\(name "([^"]*)"[\s\S]*?'
                         r'\(number "([^"]*)"', text):
        name, ball = m.group(1), m.group(2)
        suffix = re.search(r'_(\d+)$', name)
        bank = suffix.group(1) if suffix else 'NA'
        iotype = 'HR' if bank in {'13','14','15','16','34','35'} else 'NA'
        out.append((ball, name, bank, iotype))
    return out

def etype(name, iot):
    n = name.upper()
    if n.startswith('GND'):                       return 'power_in'
    if n.startswith(('VCC', 'VREFP', 'VREFN')):   return 'power_in'
    if n.startswith('NC'):                        return 'no_connect'
    if n.startswith('MGTPTX'):                    return 'output'
    if n.startswith('MGTPRX'):                    return 'input'
    if n.startswith('MGTREFCLK'):                 return 'input'
    if n.startswith('MGTRREF'):                   return 'passive'
    if n.startswith(('TCK', 'TMS', 'TDI')):       return 'input'
    if n.startswith('TDO'):                       return 'output'
    if n.startswith('DONE'):                      return 'output'
    if n.startswith(('CCLK', 'INIT_B', 'PROGRAM_B')): return 'bidirectional'
    if n.startswith(('M0_', 'M1_', 'M2_', 'CFGBVS')): return 'input'
    if n.startswith(('VP_', 'VN_', 'DXP', 'DXN')):    return 'passive'
    if iot == 'HR':                               return 'bidirectional'
    return 'passive'

def esc(s): return s.replace('\\', '\\\\').replace('"', '\\"')

def pin(x, y, rot, et, name, num, length=5.08):
    return (f'\t\t\t(pin {et} line\n'
            f'\t\t\t\t(at {x:.2f} {y:.2f} {rot})\n'
            f'\t\t\t\t(length {length})\n'
            f'\t\t\t\t(name "{esc(name)}" (effects (font (size 1.27 1.27))))\n'
            f'\t\t\t\t(number "{num}" (effects (font (size 1.27 1.27))))\n'
            f'\t\t\t)\n')

def build_units(pins):
    """-> OrderedDict unit_label -> list[(ball,name,etype)]"""
    bybank = defaultdict(list)
    for ball, name, bank, iot in pins:
        bybank[bank].append((ball, name, etype(name, iot)))
    units = OrderedDict()
    units['Bank 0 / config'] = sorted(bybank['0'])
    for bk in ('13', '14', '15', '16', '34', '35'):
        units[f'Bank {bk}'] = sorted(bybank[bk])
    units['Bank 213 / GTP'] = sorted(bybank['213'])
    units['Bank 216 / GTP'] = sorted(bybank['216'])
    na = bybank['NA']
    units['GND']    = sorted([p for p in na if p[1].upper().startswith('GND')])
    # FGG676 exposes VCCO supply balls for banks 12 and 33 even though this
    # device/package combination exposes no user I/O from those banks.
    units['Supply'] = sorted([p for p in na if not p[1].upper().startswith('GND')]
                             + bybank['12'] + bybank['33'])
    return units

def unit_body(idx, items):
    """Two columns: first half left (pointing right), second half right."""
    half = (len(items) + 1) // 2
    left, right = items[:half], items[half:]
    h = max(len(left), len(right))
    top = (h - 1) * 2.54 / 2
    W = 63.5
    s  = f'\t\t(symbol "{PART}_{idx}_1"\n'
    s += (f'\t\t\t(rectangle (start {-W/2:.2f} {top+5.08:.2f}) (end {W/2:.2f} {top-(h-1)*2.54-5.08:.2f})\n'
          f'\t\t\t\t(stroke (width 0.254) (type default)) (fill (type background))\n\t\t\t)\n')
    for i, (ball, name, et) in enumerate(left):
        s += pin(-W/2 - 5.08, top - i*2.54, 0, et, name, ball)
    for i, (ball, name, et) in enumerate(right):
        s += pin(W/2 + 5.08, top - i*2.54, 180, et, name, ball)
    return s + '\t\t)\n'

def gen_symbol(pins):
    units = build_units(pins)
    o  = '(kicad_symbol_lib\n\t(version 20241209)\n\t(generator "odin-tools")\n\t(generator_version "9.0")\n'
    o += f'\t(symbol "{PART}"\n'
    o += '\t\t(pin_names (offset 1.016))\n\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n'
    props = [('Reference','U',False), ('Value',PART,False),
             ('Footprint',f'EasyEDA:{FPNAME}',True), ('Datasheet',DS,True),
             ('Description','AMD Artix-7 XC7A100T, FGG676 27x27mm, 26x26 ball array, 676 balls',True),
             ('LCSC',LCSC,True)]
    for i,(k,v,hide) in enumerate(props):
        o += (f'\t\t(property "{k}" "{esc(v)}"\n\t\t\t(at 0 {40-i*2.54:.2f} 0)\n'
              f'\t\t\t(effects (font (size 1.27 1.27)){" (hide yes)" if hide else ""})\n\t\t)\n')
    for i, (label, items) in enumerate(units.items(), start=1):
        o += unit_body(i, items)
    o += '\t)\n)\n'
    open(SYM, 'w').write(o)
    return units

def gen_footprint():
    text = open(f'easyeda/EasyEDA.pretty/{FPNAME}.kicad_mod').read()
    return len(re.findall(r'^\s*\(pad ', text, re.M))

FLASH_PINS = [  # standard 8-pin SPI/QSPI NOR flash pinout (SOIC-8 / SOP-8)
    ('1', '~{CS}',        'input',         'L'),
    ('2', 'DO/IO1',       'bidirectional', 'R'),
    ('3', '~{WP}/IO2',    'bidirectional', 'L'),
    ('4', 'GND',          'power_in',      'L'),
    ('5', 'DI/IO0',       'bidirectional', 'L'),
    ('6', 'CLK',          'input',         'L'),
    ('7', '~{HOLD}/IO3',  'bidirectional', 'R'),
    ('8', 'VCC',          'power_in',      'R'),
    ('9', 'EP',           'power_in',      'L'),
]

def gen_flash():
    """W25Q256JVEIQ - 256Mbit QSPI NOR. KiCad ships no W25Q256; the 8-pin pinout
    is the industry-standard one shared with W25Q128JV, which KiCad does ship."""
    nm = 'W25Q256JVEIQ'
    left  = [p for p in FLASH_PINS if p[3] == 'L']
    right = [p for p in FLASH_PINS if p[3] == 'R']
    h = max(len(left), len(right)); top = (h - 1) * 2.54 / 2; Wd = 25.4
    o  = f'\t(symbol "{nm}"\n\t\t(pin_names (offset 1.016))\n'
    o += '\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n'
    for i,(k,v,hide) in enumerate([('Reference','U',False), ('Value',nm,False),
            ('Footprint','Package_SO:SOIC-8_5.3x5.3mm_P1.27mm',True),
            ('Datasheet','https://www.winbond.com/hq/product/code-storage-flash-memory/qspiflash/?__locale=en&partNo=W25Q256JV',True),
            ('Description','256Mbit QSPI NOR flash, SOIC-8',True), ('LCSC','C97522',True)]):
        o += (f'\t\t(property "{k}" "{esc(v)}"\n\t\t\t(at 0 {12-i*2.54:.2f} 0)\n'
              f'\t\t\t(effects (font (size 1.27 1.27)){" (hide yes)" if hide else ""})\n\t\t)\n')
    o += f'\t\t(symbol "{nm}_1_1"\n'
    o += (f'\t\t\t(rectangle (start {-Wd/2:.2f} {top+2.54:.2f}) (end {Wd/2:.2f} {top-(h-1)*2.54-2.54:.2f})\n'
          f'\t\t\t\t(stroke (width 0.254) (type default)) (fill (type background))\n\t\t\t)\n')
    for i,(num,name,et,_s) in enumerate(left):
        o += pin(-Wd/2 - 5.08, top - i*2.54, 0, et, name, num)
    for i,(num,name,et,_s) in enumerate(right):
        o += pin(Wd/2 + 5.08, top - i*2.54, 180, et, name, num)
    return o + '\t\t)\n\t)\n'

OSC_PINS = [('1','OE','input','L'), ('2','GND','power_in','L'), ('3','NC','no_connect','L'),
            ('4','OUT-','output','R'), ('5','OUT+','output','R'), ('6','VDD','power_in','R')]

def gen_osc():
    """Generic 6-pin differential (LVDS) oscillator, 3.2x2.5mm.
    PINOUT IS GENERIC - confirm against the chosen part before ordering."""
    nm = 'OSC_DIFF_6P_3225'
    left  = [p for p in OSC_PINS if p[3] == 'L']
    right = [p for p in OSC_PINS if p[3] == 'R']
    h = max(len(left), len(right)); top = (h - 1) * 2.54 / 2; Wd = 25.4
    o  = f'\t(symbol "{nm}"\n\t\t(pin_names (offset 1.016))\n'
    o += '\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n'
    for i,(k,v,hide) in enumerate([('Reference','X',False), ('Value',nm,False),
            ('Footprint','Oscillator:Oscillator_SMD_SiTime_SiT9121-6Pin_3.2x2.5mm',True),
            ('Datasheet','',True),
            ('Description','Generic 6-pin differential LVDS oscillator - CONFIRM PINOUT',True)]):
        o += (f'\t\t(property "{k}" "{esc(v)}"\n\t\t\t(at 0 {12-i*2.54:.2f} 0)\n'
              f'\t\t\t(effects (font (size 1.27 1.27)){" (hide yes)" if hide else ""})\n\t\t)\n')
    o += f'\t\t(symbol "{nm}_1_1"\n'
    o += (f'\t\t\t(rectangle (start {-Wd/2:.2f} {top+2.54:.2f}) (end {Wd/2:.2f} {top-(h-1)*2.54-2.54:.2f})\n'
          f'\t\t\t\t(stroke (width 0.254) (type default)) (fill (type background))\n\t\t\t)\n')
    for i,(num,name,et,_s) in enumerate(left):
        o += pin(-Wd/2 - 5.08, top - i*2.54, 0, et, name, num)
    for i,(num,name,et,_s) in enumerate(right):
        o += pin(Wd/2 + 5.08, top - i*2.54, 180, et, name, num)
    return o + '\t\t)\n\t)\n'

# SUP_VREG_AVDD is the RP2350's analogue regulator supply behind its 33R/4.7uF
# filter -- a real local rail, not a signal, so it gets a real power symbol.
CUSTOM_RAILS = ['VCCIO_1', 'VCCIO_2', '+1V0_MGT', '+1V2_MGT', 'SFP_VCC', 'VSYS',
                'PD_VDD', 'SUP_VREG_AVDD', '+5V_EXT', '+3V3_EXT',
                'VCCIO_1_EXT', 'VCCIO_2_EXT', '+12V_EXT']

def gen_rails():
    """Clone KiCad's +3V3 power symbol for the rails it does not ship."""
    t = open('/usr/share/kicad/symbols/power.kicad_sym').read()
    i = t.index('(symbol "+3V3"')
    dep, j = 1, i + len('(symbol "+3V3"')
    while dep > 0:
        if t[j] == '(': dep += 1
        elif t[j] == ')': dep -= 1
        j += 1
    proto = t[i:j]
    out = ''
    for r in CUSTOM_RAILS:
        b = proto.replace('"+3V3"', f'"{r}"').replace('"+3V3_0_1"', f'"{r}_0_1"')
        b = b.replace('"+3V3_1_1"', f'"{r}_1_1"')
        out += '\t' + b + '\n'
    return out

def gen_lxc():
    """SN74LXC8T245PW: 1.1-5.5V both rails, direction-controlled. KiCad ships
    no symbol; TI's 8-bit '245 translators are pin-compatible in TSSOP-24, so
    this is AVC8T245's symbol renamed. Pinout flagged in findings.md."""
    t = open('/usr/share/kicad/symbols/Logic_LevelTranslator.kicad_sym').read()
    i = t.index('(symbol "SN74AVC8T245PW"')
    d, j = 1, i + len('(symbol "SN74AVC8T245PW"')
    while d > 0:
        if t[j] == '(': d += 1
        elif t[j] == ')': d -= 1
        j += 1
    b = t[i:j]
    for a, c in (('"SN74AVC8T245PW"', '"SN74LXC8T245PW"'),
                 ('"SN74AVC8T245PW_0_1"', '"SN74LXC8T245PW_0_1"'),
                 ('"SN74AVC8T245PW_1_1"', '"SN74LXC8T245PW_1_1"')):
        b = b.replace(a, c)
    return '\t' + b + '\n'

def gen_box_symbol(name, pins, footprint, datasheet, description):
    """Small one-unit custom IC symbol. `pins` is (number, name, type, side)."""
    left = [p for p in pins if p[3] == 'L']
    right = [p for p in pins if p[3] == 'R']
    h = max(len(left), len(right)); top = (h - 1) * 2.54 / 2; wd = 25.4
    o = f'\t(symbol "{name}"\n\t\t(pin_names (offset 1.016))\n'
    o += '\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n'
    props = [('Reference', 'U', False), ('Value', name, False),
             ('Footprint', footprint, True), ('Datasheet', datasheet, True),
             ('Description', description, True)]
    for i, (key, value, hide) in enumerate(props):
        o += (f'\t\t(property "{key}" "{esc(value)}"\n\t\t\t(at 0 {15-i*2.54:.2f} 0)\n'
              f'\t\t\t(effects (font (size 1.27 1.27))'
              f'{" (hide yes)" if hide else ""})\n\t\t)\n')
    o += f'\t\t(symbol "{name}_1_1"\n'
    o += (f'\t\t\t(rectangle (start {-wd/2:.2f} {top+2.54:.2f}) '
          f'(end {wd/2:.2f} {top-(h-1)*2.54-2.54:.2f})\n'
          '\t\t\t\t(stroke (width 0.254) (type default)) '
          '(fill (type background))\n\t\t\t)\n')
    for i, (num, pname, et, _side) in enumerate(left):
        o += pin(-wd/2 - 5.08, top - i*2.54, 0, et, pname, num)
    for i, (num, pname, et, _side) in enumerate(right):
        o += pin(wd/2 + 5.08, top - i*2.54, 180, et, pname, num)
    return o + '\t\t)\n\t)\n'

def gen_extension_protection():
    low = [('1','ON','input','L'), ('2','VIN','power_in','L'),
           ('3','GND','power_in','L'), ('4','ILIM','passive','R'),
           ('5','VOUT','power_out','R'), ('6','FLT','open_collector','R')]
    high = [('1','EN/UVLO','input','L'), ('2','OVLO','input','L'),
            ('3','AUXOFF','open_collector','L'), ('4','FLT','open_collector','L'),
            ('5','IN','power_in','L'), ('6','OUT','power_out','R'),
            ('7','dVdt','passive','R'), ('8','GND','power_in','R'),
            ('9','ILM','passive','R'), ('10','ITIMER','passive','R')]
    ap63300 = [('1','FB','input','L'), ('2','EN','input','L'),
               ('3','VIN','power_in','L'), ('4','GND','power_in','R'),
               ('5','SW','power_out','R'), ('6','BST','passive','R')]
    return (gen_box_symbol('TPS22950CDDC', low,
            'Package_TO_SOT_SMD:SOT-23-6',
            'https://www.ti.com/lit/ds/symlink/tps22950.pdf',
            '1.8-5.5V adjustable current-limited load switch with reverse blocking') +
            gen_box_symbol('TPS259470LRPW', high,
            'Package_DFN_QFN:Texas_RPU0010A_VQFN-HR-10_2x2mm_P0.5mm',
            'https://www.ti.com/lit/ds/symlink/tps25947.pdf',
            '2.7-23V true-reverse-blocking eFuse, adjustable OVLO, latch-off') +
            gen_box_symbol('TPS259470ARPW', high,
            'Package_DFN_QFN:Texas_RPU0010A_VQFN-HR-10_2x2mm_P0.5mm',
            'https://www.ti.com/lit/ds/symlink/tps25947.pdf',
            '2.7-23V true-reverse-blocking eFuse, adjustable OVLO, auto-retry') +
            gen_box_symbol('AP63300WU', ap63300,
            'Package_TO_SOT_SMD:SOT-23-6',
            'https://www.diodes.com/datasheet/download/AP63300_AP63301.pdf',
            '3.8-32V input, 3A synchronous buck converter, TSOT26'))

LFP = 'L_Abracon_AOTA-B201610S_2.0x1.6mm'

def gen_inductor_fp():
    """The RP2350 core regulator's inductor is not a free choice: Raspberry Pi
    had Abracon make AOTA-B201610S3R3-101-T specifically for it, with a
    polarity dot so the winding direction can be controlled at assembly (see
    RP-008280 section 2.1). KiCad ships no 2016-metric inductor land, so this
    is the datasheet's Recommended Land Pattern verbatim: two 1.00 x 1.60 mm
    pads with a 1.00 mm gap, i.e. 2.00 mm pitch. Pad 1 is the dot end."""
    os.makedirs(PRET, exist_ok=True)
    pw, ph, pitch = 1.00, 1.60, 2.00
    bx, by = 1.00, 0.80                      # body 2.0 x 1.6 mm
    cx, cy = pitch/2 + pw/2 + 0.25, by + 0.45
    o  = f'(footprint "{LFP}"\n\t(version 20241229)\n\t(generator "odin-tools")\n'
    o += '\t(generator_version "9.0")\n\t(layer "F.Cu")\n'
    o += ('\t(descr "Abracon AOTA-B201610S molded power inductor, 2.0x1.6x1.0mm, '
          'recommended land pattern, pad 1 = polarity dot")\n')
    o += '\t(tags "inductor 0806 2016metric abracon polarised")\n\t(attr smd)\n'
    o += ('\t(property "Reference" "L**" (at 0 -1.9 0) (layer "F.SilkS")\n'
          '\t\t(effects (font (size 0.7 0.7) (thickness 0.12)))\n\t)\n')
    o += (f'\t(property "Value" "{LFP}" (at 0 1.9 0) (layer "F.Fab")\n'
          '\t\t(effects (font (size 0.7 0.7) (thickness 0.12)))\n\t)\n')
    # F.Fab: body plus a solid pin-1 marker, so the assembly drawing carries
    # the orientation the regulator depends on
    o += (f'\t(fp_rect (start {-bx} {-by}) (end {bx} {by}) '
          '(stroke (width 0.1) (type solid)) (fill none) (layer "F.Fab"))\n')
    o += (f'\t(fp_circle (center {-bx+0.35} {-by+0.35}) (end {-bx+0.55} {-by+0.35}) '
          '(stroke (width 0.05) (type solid)) (fill solid) (layer "F.Fab"))\n')
    # F.SilkS: dot outside the land, on the pin-1 side
    o += (f'\t(fp_circle (center {-(pitch/2+pw/2+0.35)} 0) '
          f'(end {-(pitch/2+pw/2+0.20)} 0) '
          '(stroke (width 0.15) (type solid)) (fill solid) (layer "F.SilkS"))\n')
    o += (f'\t(fp_rect (start {-cx} {-cy}) (end {cx} {cy}) '
          '(stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd"))\n')
    for num, x in (('1', -pitch/2), ('2', pitch/2)):
        o += (f'\t(pad "{num}" smd roundrect (at {x} 0) (size {pw} {ph}) '
              '(layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.15))\n')
    o += ')\n'
    open(f'{PRET}/{LFP}.kicad_mod', 'w').write(o)
    return 2

if __name__ == '__main__':
    pins = load()
    units = gen_symbol(pins)
    t = open(SYM).read()
    open(SYM, 'w').write(t[:t.rindex(')')] + gen_flash() + gen_osc() + gen_rails() +
                         gen_lxc() + gen_extension_protection() + ')\n')
    npads = gen_footprint()
    nlp = gen_inductor_fp()
    print(f"symbol  {SYM}: {len(pins)} pins in {len(units)} units")
    for k, v in units.items(): print(f"   unit {k:18s} {len(v):3d} pins")
    print(f"footprint easyeda/EasyEDA.pretty/{FPNAME}.kicad_mod: {npads} pads")
    print(f"footprint {PRET}/{LFP}.kicad_mod: {nlp} pads")
    assert npads == len(pins) == 676, (npads, len(pins))
    print("pad count matches ball count")
