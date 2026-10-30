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

def normalize_imported_pin_types():
    """Replace importer 'unspecified' types with reviewed electrical roles.

    Connectors/LEDs are passive; J51 models the attached SWD debugger at
    pins 1 and 3. Mechanical shield pins remain passive.
    This edits the source library, so embedded symbols and library ERC agree.
    """
    import symlib
    passive = {
        'F.0603.00025_P2-0603G1TS2-06T-002', 'PZ254V-11-02P',
        'HDR-IDC-2.54-2X5P', 'PM254-2-16-S-8.5', 'ZX-PM2.54-1-16PY',
        'PM254-2-08-S-8.5', 'Header-Female-2.54_1x8',
        'PH2.54-1X1P-H25', 'KF301-5.0-2P',
        'PM254-2-16-Z-8.5', 'PM254-2-08-Z-8.5',
        'PM254V-11-07-H85', '2.54mmlength21mm', '2044-2X32G00SA',
        'PMEG060V100EPDZ',
        # network: the two jacks, the PHY crystal and the link TVS arrays
        'HR911130A', 'KH-RJ45-58-8P8C', 'X322525MOB4SI', 'TPD4E1U06DBVR',
        'TF-01A_C91145',   # microSD socket
    }
    overrides = {
        'BM03B-SRSS-TB': {'1': 'bidirectional', '2': 'passive',
                          '3': 'bidirectional', '4': 'passive', '5': 'passive'},
        # RTL8211F(D) datasheet rev 1.7, Tables 1-9. RXD/RXC/RXCTL and the
        # LED pins are outputs that double as strap inputs during reset; a
        # pull resistor on an output is fine for ERC. Pin 30 is the LDO
        # output that feeds the 1.0 V pins, so it drives them.
        'RTL8211FD-CG': {
            **{str(n): 'bidirectional' for n in (1, 2, 4, 5, 6, 7, 9, 10, 14)},
            **{str(n): 'power_in' for n in (3, 8, 11, 21, 28, 29, 38, 40, 41)},
            **{str(n): 'input' for n in (12, 13, 15, 16, 17, 18, 19, 20, 36)},
            **{str(n): 'output' for n in (22, 23, 24, 25, 26, 27, 32, 33, 34, 35, 37)},
            '30': 'power_out', '31': 'open_collector', '39': 'passive'},
        # YXC OT3225 CMOS oscillator: 1 tri-state in, 2 GND, 3 out, 4 VDD
        'OT322550MJBA4SL': {'1': 'input', '2': 'power_in', '3': 'output', '4': 'power_in'},
        # Everspin MR25H10CDF, datasheet rev 9.5 Table 1.1: CS, WP, SI, SCK,
        # HOLD inputs; SO output; VDD, VSS supplies; the exposed pad is VSS.
        'MR25H10CDF': {'1': 'input', '2': 'output', '3': 'input', '4': 'power_in',
                       '5': 'input', '6': 'input', '7': 'input', '8': 'power_in',
                       '9': 'passive'},
    }
    text = open(PKG).read()
    for name in sorted(passive | overrides.keys()):
        block = symlib._block(text, name)
        found = set()
        def typed(m):
            number = m.group(3); found.add(number)
            et = 'passive' if name in passive else overrides[name][number]
            return '(pin ' + et + m.group(2) + number + '"'
        updated = re.sub(r'\(pin (\w+)( line[\s\S]*?\(number ")([^"]+)"', typed, block)
        assert found, name
        if name in overrides: assert found == set(overrides[name]), (name, found)
        text = text.replace(block, updated, 1)
    open(PKG, 'w').write(text)

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
CUSTOM_RAILS = ['VCCIO_1', 'VCCIO_2', '+1V0_MGT', '+1V2_MGT', '+1V8_IO', 'VSYS',
                'PD_VDD', 'SUP_VREG_AVDD', '+5V_EXT', '+3V3_EXT',
                'VCCIO_1_EXT', 'VCCIO_2_EXT', 'AUX_RAIL', '+5V_BUCK']

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
    # TPS2121 RUX (SLVSEA3F Figure 6-2 / Pin Functions): the +5V source mux
    mux = [('7','IN1','power_in','L'), ('2','IN2','power_in','L'),
           ('6','PR1','input','L'), ('3','CP2','input','L'),
           ('5','OV1','input','L'), ('4','OV2','input','L'),
           ('1','OUT','passive','R'), ('8','OUT','passive','R'),
           ('9','ST','open_collector','R'), ('10','ILIM','passive','R'),
           ('11','SS','passive','R'), ('12','GND','power_in','R')]
    # TPS22953 DSQ (SLVSCT5D section 6, DQC/DSQ top view): pins 1-2 IN, 3 BIAS,
    # 4 EN, 5 GND, 6 CT, 7 PG, 8 SNS, 9-10 OUT, 11 the exposed pad (GND).
    # PG is an open-drain output that the board ties to ground, as 9.3.3
    # requires of an unused PG (findings item 56); typed passive so ERC does
    # not call the ground tie a driver conflict.
    sw53 = [('1','IN','power_in','L'), ('2','IN','passive','L'),
            ('3','BIAS','power_in','L'), ('4','EN','input','L'),
            ('5','GND','power_in','L'), ('11','EP','passive','L'),
            ('9','OUT','passive','R'), ('10','OUT','passive','R'),
            ('8','SNS','input','R'), ('7','PG','passive','R'),
            ('6','CT','passive','R')]
    return (gen_box_symbol('TPS22953DSQ', sw53,
            'Package_DFN_QFN:Texas_DSQ0010A_WSON-10-1EP_2x2mm_P0.4mm_EP0.9x1.5mm',
            'https://www.ti.com/lit/ds/symlink/tps22953.pdf',
            '0.7V-to-VBIAS 5A load switch, separate 2.5-5.7V bias, reverse blocking when off, adjustable rise time') +
            gen_box_symbol('TPS2121RUX', mux,
            'Package_DFN_QFN:Texas_VQFN-HR-12_2x2.5mm_P0.5mm',
            'https://www.ti.com/lit/ds/symlink/tps2121.pdf',
            '2.8-22V 4.5A priority power mux, reverse blocking both inputs, current limit, fast switchover') +
            gen_box_symbol('TPS22950CDDC', low,
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

def gen_hdmi():
    """TPD12S016PW, the HDMI companion chip (ESD on the four TMDS pairs, DDC
    and CEC level shifting, current-limited 5 V to the connector). KiCad
    ships only the TPD12S520. Pin numbers are the PW (TSSOP-24) column of
    the Pin Functions table and the PW top view, TI SLLSE96F."""
    pins = [('1', 'CEC_A', 'bidirectional', 'L'), ('2', 'SCL_A', 'bidirectional', 'L'),
            ('3', 'SDA_A', 'bidirectional', 'L'), ('4', 'HPD_A', 'output', 'L'),
            ('5', 'LS_OE', 'input', 'L'), ('12', 'CT_HPD', 'input', 'L'),
            ('24', 'VCCA', 'power_in', 'L'), ('11', 'VCC5V', 'power_in', 'L'),
            ('6', 'GND', 'power_in', 'L'), ('14', 'GND', 'power_in', 'L'),
            ('19', 'GND', 'power_in', 'L'),
            ('23', 'D2+', 'passive', 'R'), ('22', 'D2-', 'passive', 'R'),
            ('21', 'D1+', 'passive', 'R'), ('20', 'D1-', 'passive', 'R'),
            ('18', 'D0+', 'passive', 'R'), ('17', 'D0-', 'passive', 'R'),
            ('16', 'CLK+', 'passive', 'R'), ('15', 'CLK-', 'passive', 'R'),
            ('7', 'CEC_B', 'bidirectional', 'R'), ('8', 'SCL_B', 'bidirectional', 'R'),
            ('9', 'SDA_B', 'bidirectional', 'R'), ('10', 'HPD_B', 'input', 'R'),
            ('13', '5V_OUT', 'power_out', 'R')]
    return gen_box_symbol('TPD12S016PW', pins,
                          'Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm',
                          'https://www.ti.com/lit/ds/symlink/tpd12s016.pdf',
                          'HDMI companion: 12-channel ESD, DDC/CEC level shifting, '
                          '55 mA current-limited 5 V load switch, TSSOP-24')

def gen_sdram():
    """W9825G6KH-6, 4M x 4 banks x 16 bit SDR SDRAM, TSOP II 54. KiCad ships
    no W9825; pin numbers and names are the datasheet's PIN CONFIGURATION
    (rev A03, section 4, page 4). Power and control left, data and address
    right."""
    pins = [('1', 'VDD', 'power_in', 'L'), ('14', 'VDD', 'power_in', 'L'),
            ('27', 'VDD', 'power_in', 'L'),
            ('3', 'VDDQ', 'power_in', 'L'), ('9', 'VDDQ', 'power_in', 'L'),
            ('43', 'VDDQ', 'power_in', 'L'), ('49', 'VDDQ', 'power_in', 'L'),
            ('28', 'VSS', 'power_in', 'L'), ('41', 'VSS', 'power_in', 'L'),
            ('54', 'VSS', 'power_in', 'L'),
            ('6', 'VSSQ', 'power_in', 'L'), ('12', 'VSSQ', 'power_in', 'L'),
            ('46', 'VSSQ', 'power_in', 'L'), ('52', 'VSSQ', 'power_in', 'L'),
            ('38', 'CLK', 'input', 'L'), ('37', 'CKE', 'input', 'L'),
            ('19', '~{CS}', 'input', 'L'), ('18', '~{RAS}', 'input', 'L'),
            ('17', '~{CAS}', 'input', 'L'), ('16', '~{WE}', 'input', 'L'),
            ('15', 'LDQM', 'input', 'L'), ('39', 'UDQM', 'input', 'L'),
            ('20', 'BS0', 'input', 'L'), ('21', 'BS1', 'input', 'L'),
            ('40', 'NC', 'no_connect', 'L')]
    dq = {0: '2', 1: '4', 2: '5', 3: '7', 4: '8', 5: '10', 6: '11', 7: '13',
          8: '42', 9: '44', 10: '45', 11: '47', 12: '48', 13: '50', 14: '51', 15: '53'}
    pins += [(num, f'DQ{i}', 'bidirectional', 'R') for i, num in dq.items()]
    addr = {0: '23', 1: '24', 2: '25', 3: '26', 4: '29', 5: '30', 6: '31',
            7: '32', 8: '33', 9: '34', 10: '22', 11: '35', 12: '36'}
    pins += [(num, f'A{i}', 'input', 'R') for i, num in addr.items()]
    return gen_box_symbol('W9825G6KH', pins,
                          'Package_SO:TSOP-II-54_22.2x10.16mm_P0.8mm',
                          'https://www.lcsc.com/datasheet/C62246.pdf',
                          '256 Mbit SDR SDRAM, 4M x 16 x 4 banks, 3.3 V, '
                          '166 MHz (-6), TSOP II 54')

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

MRAM_FP = 'DFN-8_L5.0-W6.0-P1.27-EP2.0-2VIA'

def gen_mram_fp():
    """MR25H10CDF land pattern: the imported EasyEDA DFN-8 (C246234) with two
    0.3 mm ground vias through the 2.0 x 2.0 mm exposed pad. The pad keeps
    its paste; the via pads carry none. Everspin MR25H10 rev 9.5 Figure 6.2
    (p. 18): body 5 x 6 mm, pitch 1.27, pad I/J 1.90-2.10, nothing but VSS
    on the exposed pad."""
    os.makedirs(PRET, exist_ok=True)
    t = open('easyeda/EasyEDA.pretty/DFN-8_L5.0-W6.0-P1.27-BL-EP.kicad_mod').read()
    t = t.replace('(module easyeda2kicad:DFN-8_L5.0-W6.0-P1.27-BL-EP', f'(module {MRAM_FP}', 1)
    t = t.replace('(fp_text value DFN-8_L5.0-W6.0-P1.27-BL-EP', f'(fp_text value {MRAM_FP}', 1)
    vias = ''.join(f'\t(pad 9 thru_hole circle (at {x:.2f} 0.00) (size 0.600 0.600) '
                   '(drill 0.300) (layers *.Cu *.Mask))\n' for x in (-0.6, 0.6))
    anchor = '\t(fp_circle'
    t = t.replace(anchor, vias + anchor, 1)
    open(f'{PRET}/{MRAM_FP}.kicad_mod', 'w').write(t)
    return t.count('(pad ')

USBC_SRC = '/usr/share/kicad/footprints/Connector_USB.pretty/USB_C_Receptacle_HCTL_HC-TYPE-C-16P-01A.kicad_mod'
USBC_FP = 'USB_C_Receptacle_HCTL_HC-TYPE-C-16P-01A_Odin'

def gen_usbc_fp():
    """KiCad's HCTL USB-C land pattern with the four outer ground pads
    (A1, A12, B1, B12) shortened on the side of the 0.65 mm locating holes.
    As shipped they are 0.6 x 1.3 mm at y -3.745 and come within 0.185 mm of
    the hole (DRC hole_clearance 0.25; JLC NPTH to copper 0.20). The pads
    keep their outer end (y -4.395) and lose 0.15 mm at the hole end: 0.6 x
    1.15 mm at y -3.82, 0.31 mm from the hole. [verify] the contact tail
    position against the HCTL drawing before ordering (findings item 49)."""
    import re
    s = open(USBC_SRC).read()
    n = 0
    def fix(m):
        nonlocal n; n += 1
        return m.group(1) + '(at ' + m.group(2) + ' -3.82)' + m.group(3) + '(size 0.6 1.15)'
    s = re.sub(r'(\(pad "(?:A1|A12|B1|B12)" smd roundrect\s*)\(at (-?3\.2) -3\.745\)(\s*)\(size 0\.6 1\.3\)',
               fix, s)
    assert n == 4, n
    s = s.replace('(footprint "USB_C_Receptacle_HCTL_HC-TYPE-C-16P-01A"',
                  f'(footprint "{USBC_FP}"', 1)
    s = s.replace('(descr "', '(descr "Odin copy: A1/A12/B1/B12 pads shortened to 1.15 mm, 0.31 mm '
                  'from the locating holes (tools/gen_kicad.py gen_usbc_fp, findings 49); ', 1)
    os.makedirs(PRET, exist_ok=True)
    open(f'{PRET}/{USBC_FP}.kicad_mod', 'w').write(s)
    return n

def gen_aux_footprints():
    """Datasheet land pattern for the AUX branch PTC."""
    os.makedirs(PRET, exist_ok=True)
    ptc = '''(footprint "Fuse_TECHFUSE_SMD2018"
\t(version 20241229)\n\t(generator "odin-tools")\n\t(layer "F.Cu")
\t(descr "TECHFUSE SMD2018, manufacturer recommended 1.5x4.6mm pads, 3.4mm gap")
\t(tags "PTC 2018 5045metric")\n\t(attr smd)
\t(property "Reference" "F**" (at 0 -3.4 0) (layer "F.SilkS")
\t\t(effects (font (size 1 1) (thickness 0.15))))
\t(property "Value" "Fuse_TECHFUSE_SMD2018" (at 0 3.4 0) (layer "F.Fab")
\t\t(effects (font (size 1 1) (thickness 0.15))))
\t(fp_rect (start -3.2 -2.55) (end 3.2 2.55)
\t\t(stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd"))
\t(fp_rect (start -2.72 -2.47) (end 2.72 2.47)
\t\t(stroke (width 0.1) (type solid)) (fill none) (layer "F.Fab"))
\t(fp_line (start -2.8 -2.55) (end 2.8 -2.55)
\t\t(stroke (width 0.12) (type solid)) (layer "F.SilkS"))
\t(fp_line (start -2.8 2.55) (end 2.8 2.55)
\t\t(stroke (width 0.12) (type solid)) (layer "F.SilkS"))
\t(pad "1" smd roundrect (at -2.45 0) (size 1.5 4.6)
\t\t(layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.15))
\t(pad "2" smd roundrect (at 2.45 0) (size 1.5 4.6)
\t\t(layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.15))
)\n'''
    open(f'{PRET}/Fuse_TECHFUSE_SMD2018.kicad_mod', 'w').write(ptc)
    return 2

if __name__ == '__main__':
    normalize_imported_pin_types()
    pins = load()
    units = gen_symbol(pins)
    t = open(SYM).read()
    open(SYM, 'w').write(t[:t.rindex(')')] + gen_flash() + gen_osc() + gen_rails() +
                         gen_lxc() + gen_extension_protection() + gen_hdmi() +
                         gen_sdram() + ')\n')
    npads = gen_footprint()
    nlp = gen_inductor_fp()
    nap = gen_aux_footprints()
    print(f'footprint {PRET}/{USBC_FP}.kicad_mod: {gen_usbc_fp()} pads shortened')
    print(f'footprint {PRET}/{MRAM_FP}.kicad_mod: {gen_mram_fp()} pads')
    print(f"symbol  {SYM}: {len(pins)} pins in {len(units)} units")
    for k, v in units.items(): print(f"   unit {k:18s} {len(v):3d} pins")
    print(f"footprint easyeda/EasyEDA.pretty/{FPNAME}.kicad_mod: {npads} pads")
    print(f"AUX PTC footprint: {nap} pads")
    print(f"footprint {PRET}/{LFP}.kicad_mod: {nlp} pads")
    assert npads == len(pins) == 676, (npads, len(pins))
    print("pad count matches ball count")
