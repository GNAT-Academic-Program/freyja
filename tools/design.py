#!/usr/bin/env python3
"""Declarative netlist for Odin. Parts connect by PIN NAME; numbers are resolved
from the KiCad symbol libraries so nothing is hand-typed and nothing is guessed."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import symlib
from alloc import assign, load
from budget import INDUCTOR
from identity import FPGA_PART, CONTROLLER_PART
from collections import OrderedDict

FP_FPGA = 'EasyEDA:FBGA-676_L27.0-W27.0-R26-C26-P1.00-BL'
C0402   = 'Capacitor_SMD:C_0402_1005Metric'
C0603   = 'Capacitor_SMD:C_0603_1608Metric'
C0805   = 'Capacitor_SMD:C_0805_2012Metric'
C1210   = 'Capacitor_SMD:C_1210_3225Metric'
CP_D    = 'Capacitor_Tantalum_SMD:CP_EIA-7343-31_Kemet-D'   # EIA 7343, Kemet D
R0402   = 'Resistor_SMD:R_0402_1005Metric'
R0603   = 'Resistor_SMD:R_0603_1608Metric'
# Inductors are not chosen here. tools/budget.py computes what each rail needs
# and names the part that meets it; this module only fits it.
SOT236  = 'Package_TO_SOT_SMD:SOT-23-6'
SOIC8N  = 'EasyEDA:SOIC-8_L4.9-W3.9-P1.27-LS6.0-BL'
WSON8_6 = 'EasyEDA:WSON-8_L6.0-W5.0-P1.27-BL-EP'   # Winbond ZP
WSON8_8 = 'EasyEDA:WSON-8_L8.0-W6.10-P1.27-BL-EP'
PTC1206 = 'Fuse:Fuse_1206_3216Metric'
PTC1206_EASYEDA = 'EasyEDA:F1206'
PTC2018 = 'odin:Fuse_TECHFUSE_SMD2018'
SOT563  = 'EasyEDA:SOT-563_L1.6-W1.2-P0.50-LS1.6-BL'
SOT236_ESD = 'EasyEDA:SOT-23-6_L2.9-W1.6-P0.95-LS2.8-BR'
SOT236_BUCK = 'EasyEDA:SOT-23-6_L2.9-W1.6-P0.95-LS2.8-BL'
SOT236_LOAD = 'EasyEDA:SOT-23-6_L2.9-W1.6-P0.95-LS2.8-BL_3'
HSOP8_DDA = 'EasyEDA:ESOP-8_L4.9-W3.9-P1.27-LS6.0-TL-EP'   # TI DDA PowerPAD SOIC-8, the C841384 import
DFN10_HUSB = 'EasyEDA:DFN-10_L3.0-W3.0-P0.50-BL-EP2.5'   # HUSB238 DFN-10L 3x3, the C7471904 import
SOIC16W = 'Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm'
TSSOP8  = 'EasyEDA:TSSOP-8_L4.4-W3.0-P0.65-LS6.4-BL'
QFN80   = 'EasyEDA:QFN-80_L10.0-W10.0-P0.40-TL-EP3.4'
TSSOP24_SWITCH = 'EasyEDA:TSSOP-24_L7.8-W4.4-P0.65-LS6.4-BL'
TSSOP24_XLATE = 'EasyEDA:TSSOP-24_L7.8-W4.4-P0.65-LS6.4-BL_1'
VSSOP8_LVC2T45 = 'EasyEDA:VSSOP-8_L2.1-W2.4-P0.50-LS3.2-BL'
QFN20_RVC = 'EasyEDA:QFN-20_L4.0-W3.0-P0.5-BL-EP'   # TI RVC WQFN-20 3x4, the C181295 import
VQFN12RUX = 'Package_DFN_QFN:Texas_VQFN-HR-12_2x2.5mm_P0.5mm'   # TI RUX0012A (MPQF508)
WSON8_DSG = 'EasyEDA:WSON-8_L2.0-W2.0-P0.50-TL-EP'   # TI DSG, the C524777 import
MRAM_FP = 'DFN-8_L5.0-W6.0-P1.27-EP2.0-2VIA'   # tools/gen_kicad.py gen_mram_fp
EXT2x8  = 'EasyEDA:HDR-TH_16P-P2.54-V-F-R2-C8-S2.54'
EXT2x16 = 'EasyEDA:HDR-TH_32P-P2.54-V-F-R2-C16-S2.54'   # two per edge, end to end
EXT_PWR = 'EasyEDA:HDR-TH_7P-P2.54-V-F'
EXT_KEY = 'EasyEDA:HDR-TH_1P-P2.54-V-M-21MM-C51353'
HDR2x3  = 'EasyEDA:HDR-TH_6P-P2.54-V-M-R2-C3-S2.54-1'
HDR2x5  = 'Connector_PinHeader_2.54mm:PinHeader_2x05_P2.54mm_Vertical'
HDR1x2  = 'Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical'
XTAL    = 'EasyEDA:CRYSTAL-SMD_4P-L3.2-W2.5-BL'
# Korean Hroparts TYPE-C-31-M-12 (LCSC C165948), top-mount with four
# through-hole shell legs, since 2026-10-30 (the HCTL mid-mount part is
# not in the JLCPCB library). KiCad's own footprint for this exact part,
# drawn from the HRO drawing (slots 0.6 x 1.7 / 0.6 x 1.2 on 8.65 x 4.18
# mm centres, 0.65 mm locating holes 5.78 mm apart, contacts 0.3 x 1.45 mm
# at 0.5 mm pitch ending 1.64 mm past the front slot line as the drawing's
# 5.79 - 4.18). The EasyEDA import of C165948 merges the outer contacts
# into custom pads named A1B12 etc., which cannot carry the symbol's pad
# names, so it is not used. No board cutout: the mid-mount's is gone with it.
USBC    = 'Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12'
LED0603 = 'LED_SMD:LED_0603_1608Metric'

LCSC = {'APS6404L-SQN-SN':'C5360304',
        'TLV62569PDRL':'C398364'}

class Design:
    def __init__(self):
        self.parts = []
        self._n = {}
        self.cur = 'misc'
        self.grp = ''
    def sheet(self, name):
        self.cur = name; self.grp = name
    def group(self, name):
        self.grp = name
    def add(self, ref, lib_id, value, fp, conn, lcsc='', dnp=False, fp_ok=''):
        if any(q['ref'] == ref for q in self.parts):
            raise ValueError(f"duplicate designator {ref}")
        if not fp_ok: self._check_package(ref, lib_id, fp)
        sym = symlib.get(lib_id)
        pins = {}
        conn = {k: v for k, v in conn.items() if v}
        for k, net in conn.items():
            if k in sym['pins']:
                for num, unit in sym['pins'][k]: pins[num] = net
            else:                                   # already a pin number
                pins[k] = net
        missing = [k for k in conn if k not in sym['pins'] and k not in
                   {n for v in sym['pins'].values() for n, _ in v}]
        if missing: raise KeyError(f"{ref} {lib_id}: no such pin {missing}; "
                                   f"have {sorted(sym['pins'])[:14]}")
        self.parts.append(dict(ref=ref, lib_id=lib_id, value=value, fp=fp,
                               pins=pins, lcsc=lcsc, dnp=dnp, sym=sym,
                               sheet=self.cur, group=self.grp))
        return ref
    @staticmethod
    def _check_package(ref, lib_id, fp):
        """A wrong footprint is invisible to ERC and to schematic parity, and it
        is only discovered when the board will not assemble. KiCad symbols carry
        ki_fp_filters for exactly this; hold the design to them."""
        import fnmatch
        if fp.startswith('EasyEDA:'):
            path = 'easyeda/EasyEDA.pretty/' + fp.split(':', 1)[1] + '.kicad_mod'
            if not os.path.isfile(path):
                raise FileNotFoundError(f'{ref}: imported footprint missing: {path}')
            return
        pats = symlib.get(lib_id).get('fp_filters') or []
        if not pats: return
        name = fp.split(':', 1)[-1]
        if not any(fnmatch.fnmatch(fp if ':' in p else name, p) for p in pats):
            raise ValueError(
                f"{ref} ({lib_id}): footprint {name!r} does not match the "
                f"symbol's permitted packages {pats}")

    def seq(self, pre):
        self._n[pre] = self._n.get(pre, 0) + 1
        return f'{pre}{self._n[pre]}'
    def reserve(self, pre, count=1):
        """Consume deleted sequential references without renumbering survivors."""
        for _ in range(count): self.seq(pre)
    # Rails that can sit above 3.3 V, and the rating a capacitor on them needs.
    # A 22uF 6.3V part on the 28 V AUX rail fails on first power-up, and the
    # value string is the only place a schematic reader will see the
    # difference, so it is put there automatically rather than typed.
    # Everything unmarked is 16 V minimum, X5R or better -- see
    # ref/qualified-parts.md.
    HV = {'VSYS': '50V', 'VBUS': '25V', 'AUX_RAIL': '50V'}

    def C(self, val, a, b, fp=C0402, dnp=False):
        hv = [self.HV[n] for n in (a, b) if n in self.HV]
        if hv: val = f'{val} {hv[0]}'
        # Exact JLC/LCSC choices already approved for robot assembly.  Keep
        # ordinary uncommon values generic so JLC's BOM matcher may propose
        # an in-stock same-value substitute at order time.
        base = val.split()[0]
        lcsc = {
            (C0402, '100nF'): 'C1525',
            (C0603, '1uF'):   'C29936',
            (C0603, '4.7uF'): 'C277476',
            (C0805, '10uF'):  'C15850',
            (C0805, '22uF'):  'C86816',
            (C1210, '10uF'):  'C77102',
        }.get((fp, base), '')
        return self.add(self.seq('C'), 'Device:C', val, fp, {'1': a, '2': b}, lcsc, dnp=dnp)
    def R(self, val, a, b, fp=R0402, dnp=False):
        lcsc = {
            (R0402, '1k'):   'C11702',
            (R0402, '4.7k'): 'C25900',
            (R0402, '100k'): 'C25741',
            (R0402, '33'):   'C25105',
        }.get((fp, val), '')
        return self.add(self.seq('R'), 'Device:R', val, fp, {'1': a, '2': b},
                        lcsc=lcsc, dnp=dnp)
    def L(self, key, a, b):
        """Fit the inductor tools/budget.py selected for this rail."""
        ind = INDUCTOR[key]
        return self.add(self.seq('L'), 'Device:L', f"{key} {ind['mpn']}",
                        ind['fp'], {'1': a, '2': b}, ind.get('lcsc', ''))
    def FB(self, a, b):
        """Murata BLM18PG121SN1D: 120 ohm at 100 MHz, 2 A, 50 mohm, 0603."""
        return self.add(self.seq('FB'), 'Device:FerriteBead', '120R 2A BLM18PG121SN1D',
                        'Inductor_SMD:L_0603_1608Metric', {'1': a, '2': b}, 'C14709')
    def F(self, val, a, b):
        # KiCad ships no *polyfuse* footprint, which is what the symbol's filter
        # asks for; a 1206 chip PTC is the physically correct package.
        selected = {
            '200mA': (PTC1206_EASYEDA, 'C269111'),  # 24 V maximum
            '300mA': (PTC1206_EASYEDA, 'C22378340'), # 16 V maximum
            '500mA': (PTC1206_EASYEDA, 'C269115'),  # 6 V maximum
            '1.1A 33V': (PTC2018, 'C70150'),
        }.get(val, (PTC1206, ''))
        return self.add(self.seq('F'), 'Device:Polyfuse', val, selected[0],
                        {'1': a, '2': b}, selected[1],
                        fp_ok='1206 chip PTC; no polyfuse footprint in KiCad')

# --------------------------------------------------- feedback dividers
E96 = sorted({round(10 ** (k / 96.0), 2) for k in range(96)})

def e96(x):
    """Nearest E96 value, returned as (ohms, label)."""
    import math
    best = None
    for dec in range(0, 7):
        for m in E96:
            v = m * 10 ** dec
            if best is None or abs(math.log(v / x)) < abs(math.log(best / x)): best = v
    lab = (f"{best/1e6:g}M" if best >= 1e6 else f"{best/1e3:g}k" if best >= 1e3
           else f"{best:g}")
    return best, lab

def fb_divider(vout, vref, rtop=100e3):
    """Vout = Vref * (1 + Rtop/Rbot). Solve for Rbot, snap to E96, verify."""
    rbot = rtop / (vout / vref - 1.0)
    rb, rb_lab = e96(rbot)
    rt, rt_lab = e96(rtop)
    actual = vref * (1 + rt / rb)
    err = abs(actual - vout) / vout
    if err > 0.02:
        raise ValueError(f"FB divider for {vout}V off by {err*100:.1f}% (got {actual:.3f}V)")
    return rt_lab, rb_lab, actual

# ------------------------------------------------ ADC monitor dividers
# The supervisor's "ADC pins" are ordinary RP2350 GPIOs, so nothing on them may
# exceed ADC_AVDD (+3V3) -- ever, not just nominally. Sizing a monitor divider
# for the rail's *nominal* voltage is the trap: the case where the monitor
# earns its keep is the case where the rail is wrong, and a bare 2-pin input
# header will eventually see whatever the owner's bench supply is set to. So
# every divider is sized from an absolute-maximum input, not a nominal one.
ADC_FS      = 3.3    # ADC_AVDD; also the full-scale reference
ADC_CEIL    = 3.0    # design ceiling, leaving headroom below ADC_AVDD
VSYS_ABSMAX = 21.0   # official J50 ceiling; D4 only subtracts from this
V5_ABSMAX   = 9.0    # U34 leaves VBUS before a 9 V request (Q6) and drops a
                     # VBUS above 5.3-5.9 V (OV1); 9 V on the rail would be a
                     # mux fault, and a monitor that dies in that fault cannot
                     # report it, so the divider is sized for it

# E24 for monitors, not E96: firmware calibrates a divider ratio, so precision
# buys nothing here, while being a value people actually stock buys something.
E24 = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0,
       3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1]

def e24_at_most(x):
    """Largest E24 value not exceeding x. Rounding *down* is the point: rounding
    to nearest can push the divider back over the ADC ceiling."""
    best = None
    for dec in range(0, 7):
        for m in E24:
            v = m * 10 ** dec
            if v <= x and (best is None or v > best): best = v
    if best is None: raise ValueError(f"no E24 value below {x}")
    lab = (f"{best/1e6:g}M" if best >= 1e6 else f"{best/1e3:g}k" if best >= 1e3
           else f"{best:g}")
    return best, lab

ADC_CHECK = []

def adc_divider(name, vnom, vabsmax, rtop=100e3):
    """Size a rail monitor from its absolute maximum, then report the nominal.

    Returns (rtop_label, rbot_label). Raises if the result would put more than
    ADC_CEIL on the pin at vabsmax."""
    rt, rt_lab = e96(rtop)
    rb, rb_lab = e24_at_most(rt / (vabsmax / ADC_CEIL - 1.0))
    ratio = rb / (rt + rb)
    v_max, v_nom = vabsmax * ratio, vnom * ratio
    if v_max > ADC_CEIL:
        raise ValueError(f"{name}: {vabsmax}V x {ratio:.4f} = {v_max:.2f}V "
                         f"exceeds the {ADC_CEIL}V ADC ceiling")
    ADC_CHECK.append((name, vnom, v_nom, vabsmax, v_max, rt_lab, rb_lab,
                      rt * rb / (rt + rb)))
    return rt_lab, rb_lab

# ---------------------------------------------------------------- rails
VSYS, V5, V33, V25, V18, V10, V12MGT = 'VSYS', '+5V', '+3V3', '+2V5', '+1V8', '+1V0', '+1V2_MGT'
V10MGT, GND = '+1V0_MGT', 'GND'
V5BUCK = '+5V_BUCK'     # U11's output node; U34 selects it or VBUS onto +5V
# U14's output node. +1V8 proper is only VCCAUX and VCCADC, behind a bead, so
# the FPGA's internal supplies do not share copper with 1.8 V I/O loads.
V18IO = '+1V8_IO'
VCCIO = {'13': V18IO, '14': V33, '15': 'VCCIO_1', '16': V25, '34': 'VCCIO_2', '35': V33}

RAIL_CHECK = []
MUX_CHECK = []      # U34 thresholds, printed by __main__

def build():
    RAIL_CHECK.clear(); ADC_CHECK.clear()
    d = Design()
    assigned, psram, sb, slots, io, other = assign()

    d.sheet('FPGA')
    # ------------------------------------------------ U1 : the FPGA
    from gen_sch import net_for            # reuse the ball->net policy
    fpga_pins = {}
    for bank, lst in list(io.items()) + list(other.items()):
        for ball, name in lst:
            n = net_for(ball, name, assigned)
            if n: fpga_pins[ball] = n
    d.group('U1  FPGA')
    d.add('U1', f'odin:{FPGA_PART}', FPGA_PART, FP_FPGA,
          fpga_pins, 'C1521803')

    # FPGA decoupling per UG483 v1.14 Table 2-2, row FGG676 / XC7A100T, in
    # the packages of Table 2-5. Note 2 of the table leaves MGTAVCC/MGTAVTT
    # to UG482: those stay as fitted (one 100nF per ball plus one 4.7uF).
    # Note 3: one 47uF per group of up to four VCCO banks on one voltage.
    # These parts are not the 0402s they replace, so they take explicit
    # 300-series refs and must not inherit the old positions on the board;
    # reserve() keeps every later sequential C ref where the owner put it.
    d.reserve('C', 110)     # former C1..C110, the 100nF-per-ball scheme
    decap_n = [300]
    def decap(group, rail, val, fp, lib='Device:C', lcsc=''):
        decap_n[0] += 1
        d.group(group)
        d.add(f'C{decap_n[0]}', lib, val, fp, {'1': rail, '2': GND}, lcsc)
    def decaps(group, rail, spec):
        for n, val, fp in spec:
            for _ in range(n): decap(group, rail, val, fp)
    # VCCINT: 1 x 330uF (D-case tantalum), 6 x 4.7uF 0805, 8 x 0.47uF 0603
    decap('decap VCCINT', V10, '330uF 6.3V T520V337M006ATE025', CP_D,
          'Device:C_Polarized', lcsc='C136150')
    decaps('decap VCCINT', V10, [(6, '4.7uF 6.3V', C0805), (8, '0.47uF 6.3V', C0603)])
    # VCCBRAM shares +1V0 (gen_sch.py RAIL): 1 x 100uF 1210, 2 x 0.47uF 0603
    decaps('decap VCCBRAM', V10, [(1, '100uF 2.5V', C1210), (2, '0.47uF 6.3V', C0603)])
    # VCCAUX: 1 x 47uF 1210, 3 x 4.7uF 0805, 5 x 0.47uF 0603
    decaps('decap VCCAUX', V18, [(1, '47uF 6.3V', C1210), (3, '4.7uF 6.3V', C0805),
                                 (5, '0.47uF 6.3V', C0603)])
    # VCCADC is not in Table 2-2; its existing 100nF bypass on +1V8 stays.
    decap('decap VCCADC', V18, '100nF', C0402, lcsc='C1525')
    # VCCO bank 0: 1 x 47uF 1210. Each of the six I/O banks: 2 x 4.7uF 0805
    # and 4 x 0.47uF 0603, plus one 47uF 1210 per voltage group of up to
    # four banks. Banks 12 and 33 have only VCCO balls on this device
    # (unbonded), tied to +3V3 and not counted. Grouping follows
    # gen_sch.RAIL, so moving a bank to another voltage regroups the 47uF.
    decaps('decap VCCO_0', V33, [(1, '47uF 6.3V', C1210)])
    from gen_sch import RAIL
    vcco_groups = {}
    for bank in sorted(io):
        rail = RAIL[f'VCCO_{bank}']
        vcco_groups.setdefault(rail, []).append(bank)
        decaps(f'decap VCCO_{bank}', rail,
               [(2, '4.7uF 6.3V', C0805), (4, '0.47uF 6.3V', C0603)])
    # One 47 uF per group of up to four banks on one voltage. The groups are
    # emitted in the order the rails had when U1's island was laid out, so
    # C366..C369 keep their parts; a rail that joins later (+1V8_IO, bank 13
    # since 2026-10-29) takes its 47 uF after the MGT capacitors, so no
    # placed decoupling capacitor is renumbered.
    GROUP_ORDER = [V33, 'VCCIO_1', V25, 'VCCIO_2']
    def group_caps(rails):
        for rail in rails:
            for _ in range(-(-len(vcco_groups[rail]) // 4)):
                decap(f'decap VCCO group {rail}', rail, '47uF 6.3V', C1210)
    group_caps([r for r in GROUP_ORDER if r in vcco_groups])
    # MGTAVCC / MGTAVTT, as fitted before (UG482 territory, not re-derived)
    mgt_balls = [(b, net_for(b, n, assigned)) for bank, lst in
                 list(io.items()) + list(other.items()) for b, n in lst
                 if net_for(b, n, assigned) in (V10MGT, V12MGT)]
    for ball, rail in mgt_balls:
        decap(f'decap {rail}', rail, '100nF', C0402, lcsc='C1525')
    for rail in (V10MGT, V12MGT):
        decap(f'decap {rail}', rail, '4.7uF', C0603, lcsc='C277476')
    group_caps([r for r in vcco_groups if r not in GROUP_ORDER])
    decap_refs = decap_n[0] - 300

    d.group('config straps (UG470)')
    # config straps (UG470)
    # M[2:0] = 001, master SPI. UG470 v1.17 Table 2-4: mode pins connect
    # "directly, or via a <= 1 kohm resistor" to VCCO_0 or GND.
    d.R('1k', V33, 'CFG_M0'); d.R('1k', 'CFG_M1', GND); d.R('1k', 'CFG_M2', GND)
    d.R('4.7k', V33, 'CFG_PROG_B'); d.R('4.7k', V33, 'CFG_INIT_B')
    # PUDC_B HIGH (UG470 v1.17 Table 2-4: VCCO_14 directly or via <= 1 k):
    # no internal pull-ups during configuration, so an unconfigured FPGA
    # leaves every I/O floating and the external resistors alone decide the
    # state of each line. Every line that needs a level has one: SDRAM CS
    # up / CKE down, MRAM CS/WP/HOLD up, microSD CS up, the 5 V bus OE up,
    # PHY reset down, and the PSRAM CE up / clock and data down below. With
    # PUDC_B low the pull-ups (DS181 IRPU, up to hundreds of uA) fought the
    # pull-downs and held the PSRAM clock and data high through power-up,
    # against APS6404L section 8 (findings item 39).
    d.R('1k', V33, 'PUDC_B')
    # DONE drives only Q4's gate; LED current comes from +3V3.
    d.R('330', V33, 'DONE_LED_A')
    d.add('D1', 'EasyEDA:F.0603.00025_P2-0603G1TS2-06T-002',
          'F.0603.00025/P2-0603G1TS2-06T-002', 'EasyEDA:LED0603-RD_GREEN',
          {'C': 'DONE_LED_K', 'A': 'DONE_LED_A'}, 'C7496818')

    d.sheet('Memory')
    # ------------------------------------------------ PSRAM x4
    # APS6404L-SQN-SN: 64 Mbit, VDD 1.62 to 1.98 V (datasheet rev 4.0 Table 9,
    # p. 26), SOP-8L(150) (section 4.1, p. 5). Pinout as the KiCad symbol and
    # the datasheet's top view (p. 4). VDD and the bypass are on +1V8_IO with
    # bank 13 (tools/alloc.py PSRAM_BALLS).
    for c in range(4):
        p = f'PSRAM{c}_'
        d.group(f'PSRAM{c}')
        d.add(f'U{2+c}', 'Memory_RAM:APS6404L-SQRx-SN', 'APS6404L-SQN-SN', SOIC8N,
              {'~{CE}': p+'CE_B_MEM', 'SCLK': p+'SCK_MEM',
               'SI/SIO0': p+'IO0_MEM', 'SO/SIO1': p+'IO1_MEM',
               'SIO2': p+'IO2_MEM', 'SIO3': p+'IO3_MEM', 'VDD': V18IO, 'VSS': GND}, LCSC['APS6404L-SQN-SN'])
        d.C('100nF', V18IO, GND)

    d.sheet('Memory')
    # ------------------------------------------------ config flash (FPGA master SPI)
    d.group('config flash')
    d.add('U6', 'odin:W25Q256JVEIQ', 'W25Q256JVEIQ', WSON8_8,
          {'~{CS}': 'FLASH_CS_B', 'CLK': 'CFG_CCLK', 'DI/IO0': 'FLASH_D0_MOSI',
           'DO/IO1': 'FLASH_D1_MISO', '~{WP}/IO2': 'FLASH_D2_WP',
           '~{HOLD}/IO3': 'FLASH_D3_HOLD', 'VCC': V33, 'GND': GND,
           'EP': GND}, 'C97522')
    d.C('100nF', V33, GND)

    d.sheet('Supervisor')
    # ------------------------------------------------ U7 : RP2350B board controller
    sup = {'GND': GND, 'IOVDD': V33, 'DVDD': '+1V1', 'ADC_AVDD': V33,
           'QSPI_IOVDD': V33, 'USB_OTP_VDD': V33,
           'VREG_VIN': V33, 'VREG_AVDD': 'SUP_VREG_AVDD', 'VREG_PGND': GND,
           'VREG_LX': 'SUP_LX', 'VREG_FB': '+1V1',
           'XIN': 'SUP_XIN', 'XOUT': 'SUP_XOUT', 'RUN': 'SUP_RUN',
           'SWCLK': 'SUP_SWCLK', 'SWDIO': 'SUP_SWDIO',
           'USB_DM': 'USB_DM_MCU', 'USB_DP': 'USB_DP_MCU',
           'QSPI_SCLK': 'SUPF_CLK', '~{QSPI_SS}': 'SUPF_CS',
           'QSPI_SD0': 'SUPF_D0', 'QSPI_SD1': 'SUPF_D1',
           'QSPI_SD2': 'SUPF_D2', 'QSPI_SD3': 'SUPF_D3'}
    # Every shared peripheral sits on a native RP2350 pin pair (datasheet
    # section 9.4, GPIO function table; findings item 42): the FPGA flash
    # bus is SPI1 (SCK 10, TX 11, RX 12, CSn 9; FD2/FD3 are PIO lines for
    # quad mode), the sideband UART is UART0 (TX 32, RX 33), the USB-PD
    # controller U18 is on I2C1 (SDA 14, SCL 31) since 2026-10-30. The 9 V
    # request is still one line, PD_REQ_9V (item 37): firmware raises it
    # (it drives the U34 hold, Q6) while it asks U18 for 9 V over I2C. U11
    # and U14 have no enable any more (item 34); GPIO21 reads which source
    # feeds +5V (item 35). The three status LEDs are plain GPIOs (35-37);
    # the I2C expander that used to carry them is gone (owner, 2026-10-30:
    # an extended part plus passives for four lines the RP2350 has spare).
    # U15's power-good left with the SY8047 (the TPS564201 has none; MON_1V0
    # reads the rail). Spare: 19, 20, 23, 26, 28, 29, 30, 38, 39.
    gp = {0:'SUP_JTAG_TCK', 1:'SUP_JTAG_TMS', 2:'SUP_JTAG_TDI', 3:'SUP_JTAG_TDO',
          4:'SUP_PROG_B', 5:'SUP_INIT_B', 6:'SUP_DONE', 10:'SUP_CCLK',
          9:'SUP_FCS_B', 11:'SUP_FD0', 12:'SUP_FD1', 13:'SUP_FD2', 7:'SUP_FD3',
          15:'SUP_DBG_TCK', 16:'SUP_DBG_TMS', 17:'SUP_DBG_TDI', 18:'SUP_DBG_TDO',
          32:'SUP_UART_TX', 33:'SUP_UART_RX',
          21:'VBUS5_ST', 22:'EN_2V5', 24:'EN_1V0', 25:'EN_1V2',
          27:'PD_REQ_9V', 14:'PD_SDA', 31:'PD_SCL',
          8:'EXT_EN', 34:'EXT_FAULT',
          35:'LED_HEARTBEAT_N', 36:'LED_USER1_N', 37:'LED_USER2_N'}
    for g, n in gp.items(): sup[f'GPIO{g}'] = n
    # ADC0-7 (GPIO40-47): MON_1V8 reads +1V8 itself, VCCAUX behind FB1, not
    # the regulator side of the bead (item 50); the two jumpered domains are
    # measured so firmware knows the J19/J20 setting. +1V2_MGT is not measured.
    for a, n in enumerate(['MON_VSYS','MON_5V','MON_3V3','MON_2V5','MON_1V8','MON_1V0',
                           'MON_VCCIO_1','MON_VCCIO_2']):
        sup[f'GPIO{40+a}/ADC{a}'] = n
    d.group('U7  board controller')
    d.add('U7', f'MCU_RaspberryPi:{CONTROLLER_PART}', CONTROLLER_PART,
          QFN80, sup, 'C42415655')
    # One 100nF per supply pin, per RP-008280 section 2.2.1. RP2350B has 8
    # IOVDD, 3 DVDD, and one each of ADC_AVDD, QSPI_IOVDD and USB_OTP_VDD.
    for _ in range(11): d.C('100nF', V33, GND)     # 8 IOVDD + QSPI + OTP + ADC
    for _ in range(3): d.C('100nF', '+1V1', GND)   # 3 DVDD
    # ---- the on-chip switching regulator, copied from the reference design.
    # RP-008280 section 2.1 is unusually blunt about this: the part, the values
    # and the layout are not a free choice, and "at your own risk" is their
    # phrasing, not ours. C6/C7/C9 = 4.7uF 0402, R3 = 33R, L1 = the Abracon
    # part they had made with a polarity dot so the winding direction can be
    # controlled at assembly.
    d.group('U7 core regulator (RP-008280 s2.1)')
    d.C('4.7uF', V33, GND, C0603)              # C6, at VREG_VIN
    d.C('4.7uF', '+1V1', GND, C0603)           # C7, the regulator output
    d.R('33', V33, 'SUP_VREG_AVDD', R0402)     # R3, RC filter for the
    d.C('4.7uF', 'SUP_VREG_AVDD', GND, C0603)  # C9, analogue supply
    d.L('3.3uH', '+1V1', 'SUP_LX')             # L1, mandated by RP-008280
    d.group('crystal (RP-008280 s4)')
    # Raspberry Pi "insist (well, strongly suggest)" on this exact crystal and
    # damping resistor: 12MHz ABM8-272-T3, 10pF load, 50R max ESR, with two
    # 15pF caps at the crystal terminals (7.5pF in series, +3pF of pin and
    # trace parasitics = 10.5pF) and a 1k series resistor in the XOUT leg so
    # the crystal is not over-driven.
    d.add('Y1', 'Device:Crystal_GND24', '12MHz ABM8-272-T3', XTAL,
          {'1': 'SUP_XIN', '3': 'SUP_XTAL_OUT', 'G': GND}, 'C20625731')
    d.R('1k', 'SUP_XOUT', 'SUP_XTAL_OUT', R0402)   # R2, drive-level damping
    d.C('15pF', 'SUP_XIN', GND); d.C('15pF', 'SUP_XTAL_OUT', GND)
    d.group('RUN')
    d.R('1k', V33, 'SUP_RUN'); d.C('100nF', 'SUP_RUN', GND)
    d.group('board controller startup memory')
    d.add('U8', 'Memory_Flash:W25Q32JVZP', 'W25Q32JVZP', WSON8_6,
          {'~{CS}': 'SUPF_CS', 'CLK': 'SUPF_CLK', 'DI/IO_{0}': 'SUPF_D0',
           'DO/IO_{1}': 'SUPF_D1', '~{WP}/IO_{2}': 'SUPF_D2',
           '~{HOLD}/~{RESET}/IO_{3}': 'SUPF_D3', 'VCC': V33, 'GND': GND, 'EP': GND},
          'C571260')
    d.C('100nF', V33, GND)
    d.group('USB-C')
    d.add('J1', 'Connector:USB_C_Receptacle_USB2.0_16P', 'USB-C', USBC,
          {'VBUS': 'VBUS', 'GND': GND, 'SHIELD': GND, 'CC1': 'USB_CC1', 'CC2': 'USB_CC2',
           'D+': 'USB_DP', 'D-': 'USB_DM'}, 'C165948')
    # U18 (HUSB238) owns the CC lines and negotiates; no plain 5.1k
    # pull-downs here. Its VSET strap is 0 ohm (Table 5: 5 V) and ISET
    # 4.53k (Table 6: 1.5 A), so the board asks for 5 V at 1.5 A before,
    # without and in spite of the controller; the controller asks for 9 V
    # over I2C (PDO_SELECT = 9 V, GO_COMMAND; register map rev 2.0) while
    # it raises PD_REQ_9V for the U34 hold. Unlike the CH224K's CFG pins,
    # I2C can select any PDO the charger offers: the 9 V ceiling is no
    # longer by construction. Firmware must never select above 9 V; U26's
    # 10.07 V OVP opens the path above that and D7 (13.3-14.7 V breakdown)
    # avalanches on a 12 V or higher contract, which the board must not
    # rely on (findings item 55 chose pins over I2C for this very reason;
    # the JLCPCB library left no pin-strapped PD sink, 2026-10-30).
    d.group('USB protection')
    # A student board gets its USB cable handled constantly. Protect the data
    # and CC lines, and clamp VBUS above the highest voltage PD will negotiate.
    d.add('D6', 'Power_Protection:ESDA6V1BC6', 'ESDA6V1BC6', SOT236_ESD,
          {'COM': GND, 'TVS1': 'USB_DP', 'TVS2': 'USB_DM',
           'TVS3': 'USB_CC1', 'TVS4': 'USB_CC2'}, 'C495220')
    # SMBJ12A is UNIDIRECTIONAL: cathode to VBUS, anode to ground. Reversed, it
    # forward-conducts on ordinary VBUS and shorts the supply. KiCad's
    # Device:D_TVS is the bidirectional (SMBJ12CA) symbol and cannot express
    # that orientation, so use the polarised avalanche-diode symbol -- which is
    # what a unidirectional TVS physically is -- and name the part in the value.
    # 12 V standoff (the 9 V contract plus 5 % is 9.45 V), breakdown 13.3-14.7 V,
    # clamp 19.9 V at 30.2 A: under U26's 20 V absolute maximum, which the
    # SMBJ13A's 21.5 V clamp was not (2026-10-30).
    d.add('D7', 'Device:D_Zener', 'SMBJ12A', 'EasyEDA:SMB_L4.3-W3.6-LS5.3-RD',
          {'K': 'VBUS', 'A': GND}, 'C19077565')

    d.group('USB-PD sink')
    # Hynetek HUSB238_002DD (datasheet rev 2.0, 2021; DFN-10 3x3): VIN from
    # VBUS with its 1 uF "as close as possible" (VIN PIN), no LDO output
    # pin; D+/D- unused (they are for BC1.2 / Apple detection and the USB
    # data lines belong to the RP2350); GATE open ("leave this pin open if
    # not used"): U26 is the VBUS switch, no PMOS. I2C address 0x08,
    # SDA/SCL 1.4 V VIH, 6 V absolute (not VIN-relative), pulled up to +3V3.
    # Status comes over I2C (PD_STATUS0/1), so the CH224K's PG line and
    # the Q3 request switch are gone; PD_REQ_9V stays as the U34 hold line.
    d.add('U18', 'Interface_USB:HUSB238_xxxDD', 'HUSB238_002DD', DFN10_HUSB,
          {'VIN': 'VBUS', 'GND': GND, 'CC1': 'USB_CC1', 'CC2': 'USB_CC2',
           'SDA': 'PD_SDA', 'SCL': 'PD_SCL', 'VSET': 'PD_VSET', 'ISET': 'PD_ISET',
           'D+': '', 'D-': '', 'GATE': ''}, 'C7471904')
    d.C('1uF', 'VBUS', GND, C0603) # VIN bypass (VBUS: 25 V rated by the HV rule, 0603 for the rating)
    d.reserve('R', 1)              # the former PD_PG pull-up
    d.group('BOOTSEL')
    # series resistor so pressing the button cannot fight the RP2350 actively
    # driving chip-select high; it only needs to win during the reset window
    d.add('SW1', 'Switch:SW_Push', 'CTRL BOOT', 'EasyEDA:KEY-SMD_B3U-1000PM',
          {'1': 'BOOTSEL_SW', '2': GND}, 'C231329')
    d.R('1k', 'SUPF_CS', 'BOOTSEL_SW')
    # R1 in the reference design: the flash wants chip-select at its own supply
    # level through power-up, and RP2350's QSPI_SS is briefly indeterminate
    # then. Raspberry Pi ship it Do-Not-Fit because it is unnecessary with this
    # exact flash; carry the same footprint for the same reason.
    d.R('10k', V33, 'SUPF_CS', dnp=True)

    d.group('board controller SWD')
    d.add('J51', 'EasyEDA:BM03B-SRSS-TB', 'CTRL SWD',
          'EasyEDA:CONN-SMD-3P-P1.00_BM03B-SRSS-TB-LF-SN',
          {'1': 'SUP_SWCLK', '2': GND, '3': 'SUP_SWDIO'}, 'C160389')

    # series resistors on every supervisor<->FPGA shared line (33R)
    d.group('series resistors to FPGA')
    for a, b in [('SUP_JTAG_TCK','SWJ_TCK'), ('SUP_JTAG_TMS','SWJ_TMS'),
                 ('SUP_JTAG_TDI','SWJ_TDI'), ('SUP_JTAG_TDO','SWJ_TDO'),
                 ('SUP_PROG_B','CFG_PROG_B'), ('SUP_INIT_B','CFG_INIT_B'),
                 ('SUP_DONE','CFG_DONE'), ('SUP_CCLK','CFG_CCLK'),
                 ('SUP_FCS_B','FLASH_CS_B'), ('SUP_FD0','FLASH_D0_MOSI'),
                 ('SUP_FD1','FLASH_D1_MISO'), ('SUP_FD2','FLASH_D2_WP'),
                 ('SUP_FD3','FLASH_D3_HOLD'),
                 ('SUP_DBG_TCK','DBG_TCK'), ('SUP_DBG_TMS','DBG_TMS'),
                 ('SUP_DBG_TDI','DBG_TDI'), ('SUP_DBG_TDO','DBG_TDO'),
                 ('SUP_UART_TX','SB_UART_RX'), ('SUP_UART_RX','SB_UART_TX')]:
        d.R('33', a, b)
    # ---- real isolation between the supervisor's JTAG and the FPGA's
    # J2 exists for the case where the board is broken, which is exactly when a
    # firmware contract ("the supervisor promises to tri-state GPIO0-3") is
    # worth least. So the separation is a FET bus switch, and the control is a
    # jumper a human moves, not a GPIO -- there is no spare GPIO, and more to
    # the point a debug path should not depend on the thing being debugged.
    #
    # Fit the shunt on J52 and the supervisor is electrically gone from the
    # chain. Leave it off (the shipped state) and the supervisor owns JTAG,
    # because that is the primary programming path and must work out of the box.
    d.group('JTAG owner selection')
    d.add('U20', '74xx:SN74CB3Q3384APW', 'SN74CB3Q3384APWR', TSSOP24_SWITCH,
          {'VCC': V33, 'GND': GND, '~{1OE}': 'EXTERNAL_JTAG_SELECTED', '~{2OE}': V33,
           '1A1': 'SWJ_TCK', '1B1': 'JTAG_TCK',
           '1A2': 'SWJ_TMS', '1B2': 'JTAG_TMS',
           '1A3': 'SWJ_TDI', '1B3': 'JTAG_TDI',
           '1A4': 'SWJ_TDO', '1B4': 'JTAG_TDO_SW'}, 'C469874')
    # The passive link also gives a probeable boundary and accurately tells
    # ERC that the FPGA output reaches a bidirectional bus-switch channel.
    d.R('0', 'JTAG_TDO_SW', 'JTAG_TDO')
    d.C('100nF', V33, GND)
    d.R('10k', 'EXTERNAL_JTAG_SELECTED', GND, R0603)
    d.add('J52', 'EasyEDA:PZ254V-11-02P', 'PZ254V-11-02P',
          'EasyEDA:HDR-TH_2P-P2.54-V-M',
          {'1': V33, '2': 'EXTERNAL_JTAG_SELECTED'}, 'C492401')
    # Manual JTAG header, directly on the FPGA's JTAG nets. Nothing else drives
    # them once J52 is fitted, so an external programmer has the chain alone.
    d.group('manual JTAG header')
    d.add('J2', 'EasyEDA:HDR-IDC-2.54-2X5P', 'FPGA JTAG',
          'EasyEDA:IDC-TH_10P-P2.54_C5665',
          {'1': V33, '2': GND, '3': 'JTAG_TMS', '4': GND,
           '5': 'JTAG_TCK', '6': GND, '7': 'JTAG_TDO', '8': GND,
           '9': 'JTAG_TDI', '10': GND}, 'C5665')

    d.sheet('Slots')
    # ------------------------------------------------ two complete 5V bus converters
    # The A side faces FPGA bank 13 at +1V8_IO; DIR and OE are referenced to
    # VCCA. SN74LVC8T245 SCES584D Table 4-1 and 5.3: VCCA and VCCB 1.65 to
    # 5.5 V (the bank's 1.71 V minimum is inside), OE referenced to VCCA
    # and to be pulled high (the 10k to +1V8_IO below). Same TSSOP-24
    # pinout as the LXC it replaces (1 VCCA, 2 DIR, 3-10 A, 11-13 GND,
    # 14-21 B8..B1, 22 OE, 23-24 VCCB); the KiCad symbol carries it.
    for bus, ref in enumerate(('U9', 'U10')):
        d.group(f'5V BUS {bus} converter')
        conn = {'V_{CCA}': V18IO, 'V_{CCB}': V5, 'GND': GND,
                'DIR': f'BUS5V{bus}_DIR', '~{OE}': f'BUS5V{bus}_OE_N'}
        for i in range(8):
            conn[f'A{i+1}'] = f'BUS5V{bus}_IO{i}'
            conn[f'B{i+1}'] = f'BUS5V{bus}_PIN{i}'
        d.add(ref, 'Logic_LevelTranslator:SN74LVC8T245', 'SN74LVC8T245PWR',
              TSSOP24_XLATE, conn, 'C27643')
        d.C('100nF', V18IO, GND); d.C('100nF', V5, GND)

    d.sheet('Slots')
    # ------------------------------------------------ shield connectors
    # A-H are eight logical zones.  Each has a 2x8 signal block plus a separate
    # keyed power row. All four sections on an edge share one continuous 2x32
    # signal lattice: A-D on the right, E-H on the left. Since 2026-10-30 the
    # lattice is carried by two 2x16 female bodies end to end (the JLCPCB
    # library has no 2x32 female; a 2.54 mm body is exactly n x 2.54 mm long,
    # so the pitch runs through the joint): J3A/J3B left, J5A/J5B right.
    # Each zone has its own long grounded key post on column 8, one pitch off
    # the line of its seven-contact female power socket on columns 1..7.
    rows = {}
    for s, (bank, _prs) in slots.items():
        if s in ('L', 'M'): continue
        sig = [f'SLOT{s}_IO{i}' for i in range(12)]
        rows[s] = ([sig[0], sig[2], GND, sig[4], sig[6], GND, sig[8], sig[10]],
                   [sig[1], sig[3], GND, sig[5], sig[7], GND, sig[9], sig[11]])

    for jref, edge_slots in (('J3', 'ABCD'), ('J5', 'EFGH')):
        pins = {}          # the 64 positions of the former single body
        for zone, s in enumerate(edge_slots):
            rowa, rowb = rows[s]
            for i in range(8):
                col = zone * 8 + i
                # The imported land pattern uses odd/even pad numbers by
                # column. The bodies have opposite board rotations, so J5's
                # local column and row are reversed to keep E-H in the same
                # board-coordinate directions as A-D. This is a physical-
                # position map, not an assumed serpentine numbering scheme.
                physical_col = 31 - col if jref == 'J5' else col
                if jref == 'J5':
                    pins[str(2*physical_col+1)] = rowb[i]
                    pins[str(2*physical_col+2)] = rowa[i]
                else:
                    pins[str(2*physical_col+1)] = rowa[i]
                    pins[str(2*physical_col+2)] = rowb[i]
        # Half A carries the first two slots of the edge (A,B / E,F), half
        # B the other two. On J3 pads 1-32 are A,B; on J5 the physical
        # column map above puts E,F on pads 33-64, so J5A takes those.
        halves = (((f'{jref}A', 0), (f'{jref}B', 32)) if jref == 'J3' else
                  ((f'{jref}A', 32), (f'{jref}B', 0)))
        for half, off in halves:
            d.group(f'SHIELD HEADER {edge_slots[:2] if half.endswith("A") else edge_slots[2:]}')
            d.add(half, 'EasyEDA:HC-PM254-8.5H-2X16PZ', 'HC-PM254-8.5H-2x16PZ',
                  EXT2x16, {str(n): pins[str(n + off)] for n in range(1, 33)},
                  'C22373921', fp_ok='imported symbol has no footprint filters')

    # Two identical complete 8-bit, 5V-compatible buses. Signals stay on the
    # 2x8 block; all exported power stays on the adjacent 1x8 row.
    for bus, (s, jn) in enumerate((('L', 7), ('M', 8))):
        d.group(f'SHIELD HEADER {s}')
        sig = [f'BUS5V{bus}_PIN{i}' for i in range(8)]
        pins = {}
        # L/M expose eight bus bits. Keep the same two interleaved ground
        # columns as every other 16-pin section; the final four contacts are
        # deliberately NC rather than inventing extra ground contacts.
        row0 = [sig[0], sig[2], GND, sig[4], sig[6], GND, '', '']
        row1 = [sig[1], sig[3], GND, sig[5], sig[7], GND, '', '']
        for i in range(8):
            pins[str(2*i+1)] = row0[i]
            pins[str(2*i+2)] = row1[i]
        # 2.54-2*8P female, 8.5 mm (C30734) since 2026-10-30: the HCTL
        # PM254-2-08-Z-8.5 is not in the JLCPCB library. Same 2x8 odd/even
        # column pads; the reviewed land is kept under the new number.
        d.add(f'J{jn}', 'EasyEDA:Header-Female-2.54_2x8',
              '2.54-2*8P female 8.5mm', EXT2x8, pins, 'C30734',
              fp_ok='imported symbol has no footprint filters')

    # Each logical zone owns four branch fuses and a keyed power row even
    # though adjacent zones share one signal connector body.
    # Reuse the six former power-body references so update-from-schematic can
    # swap those footprints in place. Only B/D/F/H need genuinely new refs.
    power_ref = {'A':'J53', 'B':'J62', 'C':'J54', 'D':'J63',
                 'E':'J55', 'F':'J64', 'G':'J56', 'H':'J65',
                 'L':'J57', 'M':'J58'}
    for s, (bank, _prs) in slots.items():
        d.group(f'SLOT {s} branches')
        vio_ext = ('+3V3_EXT' if s in ('L', 'M') else
                   ('VCCIO_1_EXT' if bank == '15' else 'VCCIO_2_EXT'))
        aux = f'SLOT_{s}_AUX'
        # The key is a long grounded male post, cut from a 21 mm 1x40 strip.
        # It is both the mechanical key and a probe point, not a mated contact.
        d.add(f'MK{ord(s)}', 'Connector_Generic:Conn_01x01',
              'BOOMELE 2.54-1x40P-21mm; cut to 1P; hand/wave soldered', EXT_KEY,
              {'1': GND}, 'C51353')
        power = [f'SLOT_{s}_PIN_VOLTAGE', GND, f'SLOT_{s}_3V3', GND,
                 f'SLOT_{s}_5V', GND, aux]
        if power.count(GND) != 3 or any(
                not (power[i-1] == GND if i else False) and
                not (power[i+1] == GND if i+1 < len(power) else False)
                for i, n in enumerate(power) if n != GND):
            raise ValueError(f'SLOT {s}: every power rail needs a GND neighbor')
        # Boom B254N02-0B7P51-H85C32 (C41426870) since 2026-10-30: 1x7
        # female, 8.5 mm, 3 A per contact (the slot's fused rails need
        # the 3 A class; the XFCN PM254V-11-07-H85 it replaces is not in
        # the JLCPCB library). Same 1x7 land, kept under the new number.
        d.add(power_ref[s], 'EasyEDA:B254N02-0B7P51-H85C32',
              'B254N02-0B7P51-H85C32', EXT_PWR,
              {str(i+1): n for i, n in enumerate(power)}, 'C41426870')
        # per-module resettable fuse on every exported rail
        # Per-slot fuses are FAULT protection, not a current allocation. The
        # shared source budgets are far smaller than 9 x these ratings; see
        # ref/extension-ux.md. Sized so one slot cannot take the whole rail.
        d.F('500mA', vio_ext, f'SLOT_{s}_PIN_VOLTAGE')
        d.F('500mA', '+5V_EXT', f'SLOT_{s}_5V')
        d.F('300mA', '+3V3_EXT', f'SLOT_{s}_3V3')
        # C70150 is 1.1 A hold / 2.2 A trip at 25 C and rated 33 V. The ten
        # branches protect faults independently; AUX_RAIL remains a shared
        # 5 A aggregate routing class, not ten amperes of source capacity.
        d.F('1.1A 33V', 'AUX_RAIL', aux)
        d.C('10uF', f'SLOT_{s}_PIN_VOLTAGE', GND, C0805)
        d.C('100nF', f'SLOT_{s}_3V3', GND)

    # VCCIO domain selectors (bank 15 and bank 34)
    for jn, (dom, net) in enumerate((('1', 'VCCIO_1'), ('2', 'VCCIO_2')), 19):
        d.group(f'VCCIO_{dom} selector')
        zones = 'A-D' if dom == '1' else 'E-H'
        d.add(f'J{jn}', 'EasyEDA:Header-Male-2.54_2x3',
              '2.54-2*3P', HDR2x3,
              {'1': V33, '2': net, '3': V25, '4': net,
               '5': V18IO, '6': net}, 'C65114')
        for _ in range(2): d.C('22uF', net, GND, C0805)

    # ------------------------------------------------ GTP: unused, powered
    # Rev A carries no transceiver load. UG482 Tables 5-5/5-6: MGTAVCC and
    # MGTAVTT stay powered, RX inputs are grounded (gen_sch.py), TX and
    # reference clocks float, and each quad keeps its 100 ohm 1% RCAL to
    # MGTAVTT (UG482 Figure 5-1). The former Fast Links sheet's sequential
    # refs are consumed in place so every later part keeps its designator.
    d.sheet('FPGA')
    d.group('GTP calibration')
    d.reserve('C', 4)                 # X2 decoupling and refclk AC coupling
    d.R('100 1%', 'MGTRREF', '+1V2_MGT', R0603)
    d.reserve('R', 1); d.reserve('C', 1)        # SFP power gate
    # The status expander (U17, PCF8574 on I2C1) and its passives are gone:
    # two bus pull-ups, two SFP ports' worth of parts, its 100 nF and the
    # INT pull-up. Their sequential refs (R37, R38, R45, C182 among them)
    # are consumed so every later part keeps its designator.
    d.sheet('Supervisor')
    d.reserve('R', 2)                           # SUP_SCL / SUP_SDA pull-ups
    d.reserve('C', 10); d.reserve('R', 6)       # two SFP ports
    d.reserve('C', 1); d.reserve('R', 1)        # U17 bypass and INT pull-up

    d.sheet('Power')
    # ------------------------------------------------ power tree
    # The Q2/Q3 VBUS-to-+5V pass switch is gone (findings item 35): its body
    # diode fed +5V back into VBUS and the path had no current limit. The
    # job is done by U34, a power mux appended at the end of this file. Q3
    # now drives the PD request (above); the four resistors and the gate
    # capacitor are consumed here so every later R/C keeps its designator.
    d.reserve('R', 4); d.reserve('C', 1)

    d.group('input OR-ing')
    d.add('J50', 'EasyEDA:KF301-5.0-2P', '9-21V POWER IN',
          'EasyEDA:CONN-TH_P5.00_KF301-5.0-2P',
          {'1': 'VIN_EXT', '2': GND}, 'C474881')
    # ---- inrush limiting, because VBUS is a hot-plugged connector
    # USB 2.0 caps a downstream device's VBUS bypass at 10uF (50uC of inrush
    # charge), and USB-PD only raises that to cSnkBulkPd = 100uF *after* a
    # contract exists. At the instant the cable goes in there is no contract,
    # and behind D3 sit 44uF of VSYS bulk -- five times the allowance, ~270uC.
    # The symptoms are a drooping source, a sparking connector, and a board
    # that will not start on some chargers and will on others.
    #
    # U26 gives a specified linear output slew instead of assuming a MOSFET
    # gate ramp becomes a linear current ramp. TI TPS25942A (SLVSCE9D) since
    # 2026-10-30, the TPS25947's predecessor that the JLCPCB library has:
    # reverse current blocking, auto-retry, 2.7-18 V operating, 20 V
    # absolute maximum (22 V for 10 ms), hence D7 is an SMBJ12A (19.9 V
    # clamp). One resistor string sets both thresholds (9.3.1, 9.3.2,
    # Equations 11 and 12, V(ENR) = V(OVPR) = 0.99 V): 110k / 24.9k / 14.7k
    # from VBUS to EN/UVLO to OVP to GND turns on at 3.74 V (off below
    # 0.93 x that, 3.48 V) and cuts off above 10.07 V; 33 uA through the
    # string at 5 V, far above the 100 nA pin leakage, 5.3 V on EN at 20 V
    # (20 V absolute). ILIM = 89 / R(kohm) (Equation 4): 44.2k = 2.01 A
    # typical (about 1.86-2.17 A from the 42.2k row of 7.5). dVdT: 1 uA
    # into the capacitor with a gain of 12 (Equation 1), 10 nF = 1.2 V/ms,
    # so charging the 44 uF VSYS bulk draws about 53 mA. IMON sources
    # 52 uA/A (Equation 7): 10k makes 0.52 V/A, a probe point, no ADC on it.
    # DMODE low (no diode mode), PGTH to ground and PGOOD open ("may be left
    # open or tied to ground when not used", 9.3.8); FLT to EXT_FAULT.
    # It is input-powered and automatic because this path creates +3V3.
    d.add('U26', 'odin:TPS25942ARVC', 'TPS25942ARVCR', QFN20_RVC,
          {'EN/UVLO':'VBUS_UVLO', 'OVP':'VBUS_OVLO', 'FLT':'EXT_FAULT',
           'IN':'VBUS', 'OUT':'VBUS_SS', 'dVdT':'VBUS_DVDT', 'ILIM':'VBUS_ILM',
           'IMON':'VBUS_IMON', 'DMODE':GND, 'PGTH':GND, 'PGOOD':'',
           'GND':GND, 'EP':GND}, 'C181295')
    d.R('110k', 'VBUS', 'VBUS_UVLO', R0603); d.R('24.9k', 'VBUS_UVLO', 'VBUS_OVLO', R0603)
    d.R('14.7k', 'VBUS_OVLO', GND, R0603); d.reserve('R', 1)   # the former 10k of the second divider
    d.R('44.2k', 'VBUS_ILM', GND, R0603)
    d.C('10nF 25V', 'VBUS_DVDT', GND)
    d.add('D3', 'Device:D_Schottky', 'SS34', 'EasyEDA:SMA_L4.3-W2.6-LS5.2-RD',
          {'A': 'VBUS_SS', 'K': VSYS}, 'C8678')
    d.add('D4', 'Device:D_Schottky', 'SS34', 'EasyEDA:SMA_L4.3-W2.6-LS5.2-RD',
          {'A': 'VIN_EXT', 'K': VSYS}, 'C8678')
    d.C('10uF', VSYS, GND, C1210); d.C('10uF', VSYS, GND, C1210)
    d.C('10uF', 'VBUS', GND, C0805)
    # VSYS -> 5V. TI LMR33630ADDA (SNVSAN3F) since 2026-10-30, the AP63300
    # being out of the JLCPCB library: 3.8-36 V operating, 38 V absolute
    # maximum on VIN (the SMBJ22A's 35.5 V clamp sits under it), 3 A,
    # 400 kHz, 1.0 V reference (7.5: 0.985-1.015 V), HSOIC-8 with the
    # PowerPAD as AGND. Table 6-1: EN "can be connected directly to VIN;
    # do not float", so EN is tied to VSYS and U11 and U12 keep starting by
    # themselves (item 34): +5V, and through U14 the FPGA's VCCAUX, is
    # present whenever +3V3 is, so the 3.3 V I/O banks never sit on an
    # unpowered VCCAUX for longer than the regulators' own start-up (DS181
    # Table 7). PG "can be left open when not used". 9.2.2: 100 nF CBOOT
    # (10 V or more), 1 uF 16 V on VCC, at least 10 uF ceramic at VIN
    # rated for the input (the 10 uF 50 V 1210 each has) plus a 220 nF
    # 50 V X7R as close as possible (appended below), RFBT 100 k and RFBB
    # from Equation 3 (Table 9-2: 24.9k for 5 V, 43.2k for 3.3 V, no CFF
    # at 100 k). 4.7 uH stays: Equation 5's minimum is 3.5 uH at 5 V and
    # 2.3 uH at 3.3 V; ripple is 39 % / 37 % of 3 A at the 9 V planning
    # input (the 20-40 % guidance) and 68 % / 56 % at 21 V, where
    # budget.py checks the peak against saturation. Its output node is
    # +5V_BUCK; U34 joins it to the +5V rail.
    d.group('U11  VSYS to +5V')
    d.add('U11', 'Regulator_Switching:LMR33630ADDA', 'LMR33630ADDAR', HSOP8_DDA,
          {'VIN': VSYS, 'GND': GND, 'FB': 'FB_5V', 'EN': VSYS, 'SW': 'SW_5V',
           'BOOT': 'BOOT_5V', 'VCC': 'U11_VCC', 'PG': ''}, 'C841384')
    d.C('100nF', 'BOOT_5V', 'SW_5V'); d.L('4.7uH', V5BUCK, 'SW_5V')
    rt, rb, act = fb_divider(5.0, 1.0)            # LMR33630 VREF = 1.0 V
    d.R(rt, V5BUCK, 'FB_5V', R0603); d.R(rb, 'FB_5V', GND, R0603)
    RAIL_CHECK.append(('+5V', 5.0, act, rt, rb))
    for _ in range(3): d.C('22uF', V5BUCK, GND, C0805)
    # 5V -> the low rails
    # +3V3 is ALWAYS ON and powers the supervisor. The LMR33630 works down
    # to 3.8 V, below the 4.27 V weak-port worst case, and its 3 A rating
    # covers both protected VCCIO domains at their maximum current-limit
    # tolerance.
    d.group('U12  VSYS to +3V3  (always on)')
    rt3, rb3, act3 = fb_divider(3.3, 1.0)         # Table 9-2: 100k / 43.2k
    RAIL_CHECK.append((V33, 3.3, act3, rt3, rb3))
    d.add('U12', 'Regulator_Switching:LMR33630ADDA', 'LMR33630ADDAR', HSOP8_DDA,
          {'VIN': VSYS, 'GND': GND, 'FB': 'FB_3V3', 'EN': VSYS, 'SW': 'SW_3V3',
           'BOOT': 'BOOT_3V3', 'VCC': 'U12_VCC', 'PG': ''}, 'C841384')
    d.C('10uF', VSYS, GND, C1210)
    d.C('100nF', 'BOOT_3V3', 'SW_3V3'); d.L('4.7uH', V33, 'SW_3V3')
    d.R(rt3, V33, 'FB_3V3', R0603); d.R(rb3, 'FB_3V3', GND, R0603)
    d.reserve('C', 1)                              # the AP63300's 56 pF feed-forward
    for _ in range(3): d.C('22uF', V33, GND, C0805)

    # U14's EN is tied to its VIN (SLVSDG1C: EN -0.3..6 V absolute, VIH
    # 1.2 V max): the 1.8 V rail is up whenever +5V is, see U11 above.
    # TLV62569PDRLR since 2026-10-30 (the plain DRLR is nearly out of the
    # JLCPCB library): same SOT-563 pinout, pin 6 is the open-drain PG
    # instead of NC and stays unconnected, as the datasheet's pin table
    # says for an unused PG (the rails are read by the ADC monitors).
    for ref, rail, en, vtgt in (('U13', V25, 'EN_2V5', 2.5),
                                ('U14', V18IO, V5, 1.8),
                                ('U16', V12MGT, 'EN_1V2', 1.2)):
        top, bot, act = fb_divider(vtgt, 0.600)   # TLV62569 Vfb = 0.600 V
        RAIL_CHECK.append((rail, vtgt, act, top, bot))
        d.group(f'{ref}  5V to {rail}')
        fb = f'FB{rail}'; sw = f'SW{rail}'
        d.add(ref, 'odin:TLV62569PDRL', 'TLV62569PDRLR', SOT563,
              {'VIN': V5, 'GND': GND, 'EN': en, 'FB': fb, 'SW': sw},
              LCSC['TLV62569PDRL'])
        d.L('2.2uH', rail, sw)
        d.R(top, rail, fb, R0603); d.R(bot, fb, GND, R0603)
        for _ in range(2): d.C('22uF', rail, GND, C0805)
        d.C('100nF', V5, GND)
    # FPGA core supply: TI TPS564201 (SLVSDJ7B) since 2026-10-30, the
    # 4 A D-CAP2 buck the JLCPCB library has (the SY8047 is not in it).
    # SOT-23-6 (DDC): 1 GND, 2 SW, 3 VIN, 4 VFB, 5 EN, 6 VBST. 4.5-17 V in
    # (so +5V must be at or above 4.5 V before EN_1V0: a 4.75 V USB port
    # less U34's drop is 4.69 V, and U11 in dropout during a 9 V
    # negotiation sits near 4.5 V, hence firmware enables the core only
    # once the source is settled), 560 kHz, VFB 0.760 V (0.745-0.775). No
    # PG, no SS, no SVIN: CORE_1V0_GOOD, the 10 R / 1 uF filter and the
    # 1 nF are gone (MON_1V0 reads the rail), EN "must be pulled up to
    # enable" (VENH 1.6 V, EN_1V0 from the controller with its 100k
    # pull-down). Table 2, 1 V row: R1 3.09k / R2 10k (0.995 V), L 1.5 to
    # 4.7 uH (4.7 uH taken: L7 is the 6045 part L2/L3 use, Isat 4.97 A
    # guaranteed for the 4 A class, ripple 0.31 A at 5.5 V in), COUT 20 to
    # 68 uF (2 x 22 uF here, the FPGA decoupling beyond it is the known
    # bench item). 8.2.2.4: 10 uF or more at VIN (the 22 uF) and an
    # optional 100 nF at pin 3; 8.2.2.5: 100 nF VBST to SW (both appended
    # below). The SY8047's SVIN resistor and capacitor, SS capacitor, PG
    # pull-up and the 22 pF feed-forward are consumed as designators.
    rt1, rb1 = '3.09k', '10k'
    act1 = 0.760 * (1 + 3.09 / 10.0)              # SLVSDJ7B Equation 2, Table 2
    RAIL_CHECK.append((V10, 1.0, act1, rt1, rb1))
    d.group('U15  5V to +1V0  (4A FPGA core supply)')
    d.add('U15', 'odin:TPS564201DDC', 'TPS564201DDCR', SOT236_BUCK,
          {'VIN': V5, 'GND': GND, 'SW': 'SW+1V0', 'VFB': 'FB+1V0',
           'EN': 'EN_1V0', 'VBST': 'BST+1V0'}, 'C464812')
    d.C('22uF', V5, GND, C0805)
    d.reserve('R', 1); d.reserve('C', 1)          # SVIN 10 R and 1 uF
    d.reserve('C', 1); d.reserve('R', 1)          # SS 1 nF, PG 100k
    d.L('4.7uH', V10, 'SW+1V0')
    d.R(rt1, V10, 'FB+1V0', R0603); d.R(rb1, 'FB+1V0', GND, R0603)
    d.reserve('C', 1)                             # 22 pF feed-forward
    for _ in range(2): d.C('22uF', V10, GND, C0805)
    # U19's +12V output fed only U25 and the ten per-zone AUX selectors. Those
    # consumers are gone: AUX is now the raw J68 input straight into the ten
    # branch PTCs. Consume the old sequential slots so every later
    # hand-placed L/R/C keeps its identity.
    d.reserve('L', 1)       # former L8
    d.reserve('R', 3)       # former R69..R71
    d.reserve('C', 5)       # former C213..C217

    # Extension power is a separate protected tree. Base-board loads remain
    # on the internal rails; only the connector PTC branches use these outputs.
    # One hardware pulldown makes every channel default off. All open-drain
    # fault outputs are wire-ORed into one supervisor input.
    d.group('extension power protection control')
    d.R('100k', 'EXT_EN', GND, R0603)
    d.R('10k', V33, 'EXT_FAULT', R0603)

    # TPS22950C is the orderable SOT-23-6 member with reverse blocking. The
    # +5V limit is below its qualified 1.615A shared budget. The other channels
    # use the part's minimum supported 0.5A setting. RILIM follows TI equation
    # ILIM(A)=1.18*RILIM(kohm)^-1.072. Each input gets TI's required 1uF local
    # bypass; output bulk already exists after the downstream PTCs.
    low_ext = [
        ('U21', V5,        '+5V_EXT',     '1.15k', 1.000),
        ('U22', V33,       '+3V3_EXT',    '2.21k', 0.500),
    ]
    for ref, vin, vout, rilim, _ilim in low_ext:
        d.group(f'{ref}  {vin} to {vout}')
        d.add(ref, 'odin:TPS22950CDDC', 'TPS22950CDDCR', SOT236_LOAD,
              {'ON':'EXT_EN', 'VIN':vin, 'GND':GND, 'ILIM':f'{ref}_ILIM',
               'VOUT':vout, 'FLT':'EXT_FAULT'}, 'C7587833')
        d.R(rilim, f'{ref}_ILIM', GND, R0603)
        d.C('1uF', vin, GND, C0603)
    # The two jumpered domains can be 1.8 V, below the TPS22950's 1.8 V
    # minimum input (SLVSFJ2B 7.3; findings item 41). U23/U24 are TI
    # TPS22975 (SLVSDD0B) since 2026-10-30 (the TPS22953 is not in the
    # JLCPCB library): the switch runs from a separate VBIAS pin on the
    # always-on +3V3 (2.5-5.7 V) and passes 0.6 V to VBIAS, 6 A, 16 mohm,
    # with an adjustable rise time (CT), thermal shutdown and quick output
    # discharge (230 ohm to GND while off). Unlike the TPS22953 it has no
    # PG, no SNS and no reverse current blocking: EXT_FAULT is U21, U22
    # and U26 only, and a slot that back-feeds its PIN V pin while EXT_EN
    # is low sees the switch's body diode (ref/extension-ux.md says so).
    # No programmable current limit either: the 500 mA PINV branch PTC in
    # every slot is the overload protection. ON VIH 1.05-1.2 V, so EXT_EN
    # drives it directly. The ILIM resistor each had is consumed here so
    # the later resistors keep their designators; the 1 uF input bypass
    # stays, the BIAS 100 nF, CT 1 nF and OUT 1 uF are appended below.
    for ref, vin, vout in (('U23', 'VCCIO_1', 'VCCIO_1_EXT'),
                           ('U24', 'VCCIO_2', 'VCCIO_2_EXT')):
        d.group(f'{ref}  {vin} to {vout}')
        d.add(ref, 'odin:TPS22975DSG', 'TPS22975DSGR', WSON8_DSG,
              {'VIN': vin, 'VOUT': vout, 'VBIAS': V33, 'ON': 'EXT_EN', 'GND': GND,
               'CT': f'{ref}_CT', 'EP': GND}, 'C524777')
        d.reserve('R', 1)
        d.C('1uF', vin, GND, C0603)

    # U25 was consumed only by the deleted +12V_EXT selector tree. AUX_RAIL's
    # ten 33V PTCs now provide branch isolation. Preserve later R/C numbers.
    d.reserve('R', 3)       # former R78..R80
    d.reserve('C', 2)       # former C222..C223

    d.group('MGTAVCC filter')
    # MGTAVCC 1.0V filtered off +1V0
    d.L('1uH', V10MGT, V10); d.C('4.7uF', V10MGT, GND, C0603)
    d.group('rail monitors')
    # Rail monitors into the supervisor ADC. The two rails that can sit above
    # +3V3 are divided; the dividers are sized from the absolute maximum the
    # hardware can present, not from the nominal rail -- see adc_divider().
    for rail, mon, vnom, vmax in ((VSYS, 'MON_VSYS', 9.0, VSYS_ABSMAX),
                                  (V5,  'MON_5V',   5.0, V5_ABSMAX)):
        rt, rb = adc_divider(mon, vnom, vmax)
        d.R(rt, rail, mon, R0603); d.R(rb, mon, GND, R0603)
    # The rails at or below +3V3 need no division, only a series resistor to
    # limit current into the pin's ESD structure if the rail overshoots.
    for rail, mon, vnom in ((V33,'MON_3V3',3.3), (V25,'MON_2V5',2.5),
                            (V18,'MON_1V8',1.8), (V10,'MON_1V0',1.0)):
        d.R('1k', rail, mon, R0603)
        ADC_CHECK.append((mon, vnom, vnom, ADC_FS, ADC_FS, '1k (series)', '-', 1e3))
    # One capacitor per monitor node. Two jobs: it supplies the charge the
    # ADC's sample-and-hold demands (which a 14k Thevenin divider cannot), and
    # it filters switching ripple out of a reading firmware will compare
    # against a threshold. Without it the divided rails read low and noisy.
    for mon in ('MON_VSYS', 'MON_5V', 'MON_3V3', 'MON_2V5', 'MON_1V8', 'MON_1V0'):
        d.C('100nF', mon, GND)

    # Appended to preserve existing reference designators. Quad 213 keeps
    # its own RCAL: UG482 Table 5-5.
    d.sheet('FPGA')
    d.group('GTP calibration')
    d.R('100 1%', 'MGTRREF_213', V12MGT, R0603)

    # Append to preserve existing designators; render each pulldown with its
    # regulator. Hold EN low while RP2350 GPIOs are high-Z (reset/BOOTSEL),
    # including EN_5V, whose TPS54202 has an internal enable pull-up.
    d.sheet('Power')
    for ref, en in (('U11', None), ('U13', 'EN_2V5'), ('U14', None),
                    ('U16', 'EN_1V2'), ('U15', 'EN_1V0')):
        if en is None:          # U11 and U14 are always on (item 34)
            d.reserve('R', 1); continue
        d.group(next(p['group'] for p in d.parts if p['ref'] == ref))
        d.R('100k', en, GND, R0603)
    d.reserve('R', 1)       # former R95, U19 enable pulldown

    # Default-disable the translators through FPGA configuration. OE is
    # referenced to VCCA (+1V8_IO, the bank 13 voltage; a 3.3 V pull-up
    # would exceed the bank's VIN limit); HDL must set DIR/data before OE low.
    # Append resistors to keep existing designators stable.
    d.sheet('Slots')
    for bus in range(2):
        d.group(f'5V BUS {bus} converter')
        d.R('10k', V18IO, f'BUS5V{bus}_OE_N', R0603)

    # Append to keep existing designators stable. DONE is open-drain by
    # default (UG470); no DriveDone setting is needed for this buffered LED.
    d.sheet('FPGA')
    d.group('config straps (UG470)')
    d.R('4.7k', V33, 'CFG_DONE')
    d.add('Q4', 'Transistor_FET:Q_NMOS_GSD', 'BSS138LT1G',
          'EasyEDA:SOT-23-3_L2.9-W1.6-P1.90-LS2.8-BR',
          {'G': 'CFG_DONE', 'S': GND, 'D': 'DONE_LED_K'}, 'C82045')

    # The SFP I2C switch (U27) and its pull-ups are gone; their sequential
    # refs are consumed so later designators stay put.
    d.reserve('C', 1); d.reserve('R', 5)

    # FPGA-side net names/ball assignments remain stable. The _MEM side
    # reaches only the PSRAM pin; no direct path bypasses these resistors.
    # Append to preserve all existing reference designators.
    # Grouped under U1: the resistors damp the FPGA's drive and belong at the
    # FPGA escape, not beside the memory (islands.py reads the group name).
    d.sheet('Memory')
    for c in range(4):
        d.group(f'U1 PSRAM{c} series termination')
        for lane in ('SCK', 'CE_B', 'IO0', 'IO1', 'IO2', 'IO3'):
            net = f'PSRAM{c}_{lane}'
            d.R('33', net, net+'_MEM')

    # Clamp the screw-terminal input before D4. Unidirectional TVS:
    # cathode to VIN_EXT, anode to ground; keep the surge loop at J50 short.
    d.sheet('Power')
    d.group('input OR-ing')
    d.add('D8', 'Device:D_Zener', 'SMBJ22A', 'Diode_SMD:D_SMB',
          {'K': 'VIN_EXT', 'A': GND}, 'C151920')

    # ------------------------------------------------ AUX IN
    # Rev A has no on-board AUX converter. The ten SLOT_x_AUX branches are
    # fed only from this screw terminal, each through its own 33 V PTC in
    # the slot group above. The VSYS-fed SEPIC was dropped: the SMBJ22A
    # clamp (35.5 V) on top of a charged 24 V output could exceed the
    # LM5157 SW pin's 50 V absolute maximum. See ref/power.md.
    d.group('AUX IN')
    d.add('J68', 'EasyEDA:KF301-5.0-2P', 'AUX IN 9-28V UNREGULATED',
          'EasyEDA:CONN-TH_P5.00_KF301-5.0-2P',
          {'1': 'AUX_RAIL', '2': GND}, 'C474881')

    # Cathodes on RP2350 GPIO35-37, anodes through 1k from +3V3: a GPIO
    # driven low lights the LED, about 1.2 mA each. Dark at power-on and in
    # reset, when the pads are high-impedance with a weak pull-down and the
    # anode resistor alone sets the current (none through a dark LED).
    d.sheet('Supervisor')
    d.group('board status LEDs')
    for ref, name in (('D9', 'HEARTBEAT'), ('D10', 'USER1'), ('D11', 'USER2')):
        d.R('1k', V33, f'LED_{name}_A')
        d.add(ref, 'EasyEDA:F.0603.00025_P2-0603G1TS2-06T-002',
              'F.0603.00025/P2-0603G1TS2-06T-002', 'EasyEDA:LED0603-RD_GREEN',
              {'A': f'LED_{name}_A', 'C': f'LED_{name}_N'}, 'C7496818')

    # ------------------------------------------------ Network
    # RTL8211FDI-CG (decision D2: the LDO model, no switching inductor; the
    # industrial-grade FD since 2026-10-30, the only FD in the JLCPCB
    # library). Pin names are the datasheet rev 1.7 Table 1-9 names as the
    # imported C692886 symbol carries them (identical to the C2687133 import). RGMII, MDC and MDIO run at the DVDD_RG
    # level, 2.5 V from +2V5, into bank 16 (VCCO = +2V5, tools/alloc.py).
    # PHYRSTB and INTB are 3.3 V pins (Table 58 note) and go to bank 35
    # (3.3 V; bank 13 is 1.8 V), tools/alloc.py PHY_CTL.
    # CLKOUT (pin 35) floats, Table 2; it outputs 125 MHz by default, so the
    # gateware clears it (PHYCR2) once MDIO is up.
    d.sheet('Network')
    d.group('U30  gigabit PHY')
    d.add('U30', 'EasyEDA:RTL8211FDI-CG', 'RTL8211FDI-CG',
          'EasyEDA:QFN-40_L5.0-W5.0-P0.40-BL-EP3.7',
          {'MDIP0': 'ETH_MDI0_P', 'MDIN0': 'ETH_MDI0_N',
           'MDIP1': 'ETH_MDI1_P', 'MDIN1': 'ETH_MDI1_N',
           'MDIP2': 'ETH_MDI2_P', 'MDIN2': 'ETH_MDI2_N',
           'MDIP3': 'ETH_MDI3_P', 'MDIN3': 'ETH_MDI3_N',
           'AVDD33': V33, 'DVDD33': V33, 'DVDD_RG': V25,
           'AVDD10': 'PHY_1V0', 'DVDD10': 'PHY_1V0', 'REG_OUT': 'PHY_1V0',
           'GND': GND,
           'PHYRSTB': 'PHY_RESET_N', 'INTB/PMEB': 'PHY_INT_N',
           'MDC': 'PHY_MDC', 'MDIO': 'PHY_MDIO',
           'TXC': 'PHY_TXC', 'TXCTL': 'PHY_TX_CTL',
           'TXD0': 'PHY_TXD0', 'TXD1': 'PHY_TXD1', 'TXD2': 'PHY_TXD2', 'TXD3': 'PHY_TXD3',
           'PHYAD1/RXC': 'PHY_RXC', 'PHYAD2/RXCTL': 'PHY_RX_CTL',
           'RXDLY/RXD0': 'PHY_RXD0', 'TXDLY/RXD1': 'PHY_RXD1',
           'PLLOFF/RXD2': 'PHY_RXD2', 'PHYAD0/RXD3': 'PHY_RXD3',
           'CFG_EXT/LED0': 'PHY_LED0', 'CFG_LDO0/LED1': 'PHY_LED1',
           'CFG_LDO1/LED2': 'PHY_LED2',
           'XTAL_IN': 'PHY_XI', 'XTAL_OUT/EXT_CLK': 'PHY_XO',
           'RSET': 'PHY_RSET'}, 'C692886')
    # Table 9 supplies. 3.3 V on pins 11, 29, 40: one 100nF each plus bulk.
    # Table 53 note 1: the 3.3 V rise must take more than 0.5 ms, which U12's
    # soft start provides; do not add a fast switch in front of the PHY.
    for _ in range(3): d.C('100nF', V33, GND)
    d.C('10uF', V33, GND, C0805)
    # DVDD_RG from +2V5, external I/O mode. Table 53 note 5 case II: this
    # rail may come up after 3.3 V because PHYRSTB is held low until it is.
    d.C('100nF', V25, GND); d.C('1uF', V25, GND, C0603)
    # LDO_OUT (pin 30) feeds only AVDD10 (3, 8, 38) and DVDD10 (21): one
    # 100nF per pin and 4.7uF bulk, as on public RTL8211F boards (the
    # datasheet names no value; FriendlyELEC NanoPi M5 uses 4.7uF + 100nF).
    for _ in range(4): d.C('100nF', 'PHY_1V0', GND)
    d.C('4.7uF', 'PHY_1V0', GND, C0603)
    # RSET to GND. Rev 1.7 has no reference schematic and no value; the
    # Realtek reference value, as every public RTL8211F board carries it
    # (NanoPi M5: R 2.49K/1%), is 2.49k 1%. [verify] against Realtek's own
    # reference design if it becomes available.
    d.R('2.49k 1%', 'PHY_RSET', GND)

    d.group('PHY straps and LEDs')
    # PHYRSTB: 3.3 V input, Table 58 (VIH 2.0 V), driven from bank 35. The
    # 1k pull-down holds it low while the FPGA pin floats (PUDC_B is high:
    # no configuration pull-ups) and until +2V5 is up (Table 53 note 5 case
    # II). Section 7.17: after release wait >= 72 ms before MDIO.
    d.R('1k', 'PHY_RESET_N', GND)
    # INTB is open drain (Table 4), 4.7k to 3.3 V.
    d.R('4.7k', V33, 'PHY_INT_N')
    # MDIO idles high through 1.5k to the I/O supply (Table 4, section 7.11.2).
    d.R('1.5k', V25, 'PHY_MDIO')
    # Straps, Table 10 and 11, 4.7k each. PHYAD = 001: RXD3 up, RXC and RXCTL
    # down. PLLOFF = 0 (RXD2 down), TXDLY = 1 (RXD1 up), RXDLY = 1 (RXD0 up).
    # These six pull to DVDD_RG, the RGMII pad supply.
    for net, high in (('PHY_RXD3', True), ('PHY_RXC', False), ('PHY_RX_CTL', False),
                      ('PHY_RXD2', False), ('PHY_RXD1', True), ('PHY_RXD0', True)):
        d.R('4.7k', V25 if high else GND, net)
    # CFG_EXT = 1, CFG_LDO[1:0] = 01: external 2.5 V I/O supply (section
    # 7.8). These three strap to 3.3 V and GND, not to DVDD_RG (Table 11).
    d.R('4.7k', V33, 'PHY_LED0'); d.R('4.7k', V33, 'PHY_LED1'); d.R('4.7k', 'PHY_LED2', GND)
    # LEDs live in the jack. Section 7.9 Figure 5: a pin strapped high
    # drives active-low (LED + 510 ohm from 3.3 V); strapped low, active-high
    # (LED + 510 ohm to GND). Green 11/12 on LED0, yellow 14/13 on LED2
    # (default: link at 1000 Mb/s, Table 7). LED1 is strap only.
    d.R('510', V33, 'ETH_LED_GREEN_A')
    d.R('510', 'ETH_LED_YELLOW_K', GND)

    d.group('ETH jack')
    # HanRun HR911130A, 1000Base-T magnetics and two LEDs in the jack. Pin
    # names from the HanRun drawing rev A as the imported symbol carries
    # them. P10 is the jack's internal Bob-Smith network (4 x 75 ohm, 1000 pF
    # 2 kV) and goes to ground; P1 is the common chip-side centre tap. The
    # RTL8211F drives the line in voltage mode with internal termination
    # (section 7.7), so the taps carry no bias: 100nF to ground, as on
    # public RTL8211F boards. [verify] against Realtek's reference design.
    d.add('J70', 'EasyEDA:HR911130A', 'ETH', 'EasyEDA:RJ45-TH_HR911130A',
          {'MDI0+': 'ETH_MDI0_P', 'MDI0-': 'ETH_MDI0_N',
           'MDI1+': 'ETH_MDI1_P', 'MDI1-': 'ETH_MDI1_N',
           'MDI2+': 'ETH_MDI2_P', 'MDI2-': 'ETH_MDI2_N',
           'MDI3+': 'ETH_MDI3_P', 'MDI3-': 'ETH_MDI3_N',
           'P1': 'ETH_CT', 'P10': GND, 'SHIELD0': GND, 'SHIELD1': GND,
           '11': 'ETH_LED_GREEN_A', '12': 'PHY_LED0',
           '14': 'PHY_LED2', '13': 'ETH_LED_YELLOW_K'}, 'C54408')
    d.C('100nF 50V', 'ETH_CT', GND, C0603)

    d.group('PHY clock')
    # Table 56: 25 MHz, +/-50 ppm all in, ESR <= 50 ohm, drive <= 0.5 mW.
    # X322525MOB4SI: +/-10 ppm, CL 12 pF. Load capacitors 2 x (CL - Cstray)
    # with about 3 pF stray: 18 pF. The series resistor on XTAL_OUT limits
    # drive level; 0 ohm until measured. [verify] frequency and drive.
    d.add('X3', 'EasyEDA:X322525MOB4SI', '25MHz 12pF',
          'EasyEDA:CRYSTAL-SMD_4P-L3.2-W2.5-BL_X3225',
          {'OSC1': 'PHY_XI', 'OSC2': 'PHY_XO_X', 'GND': GND}, 'C9006')
    d.R('0', 'PHY_XO', 'PHY_XO_X')
    d.C('18pF', 'PHY_XI', GND); d.C('18pF', 'PHY_XO_X', GND)

    # Two raw LVDS_25 link ports, bank 16, DC coupled, receiver termination
    # inside the FPGA (DIFF_TERM). Pair map, see ref/link-ports.md: an 8P8C
    # carries its four pairs on pins 1-2, 3-6, 4-5 and 7-8; the lower pin
    # is P. LINK P sends on 1-2 (clock) and 3-6 (data) and receives on 4-5
    # (clock) and 7-8 (data); LINK Q is the mirror, so one straight cable
    # from a P to a Q lands clock on clock and data on data.
    tvs = iter(('D20', 'D21', 'D22', 'D23'))
    for ref, port, pairs in (
            ('J71', 'P', {(1, 2): 'TXC', (3, 6): 'TXD', (4, 5): 'RXC', (7, 8): 'RXD'}),
            ('J72', 'Q', {(1, 2): 'RXC', (3, 6): 'RXD', (4, 5): 'TXC', (7, 8): 'TXD'})):
        d.group(f'LINK {port}')
        conn = {'9': GND, '10': GND}
        for (p, n), name in pairs.items():
            conn[str(p)] = f'LINK_{port}_{name}_P'
            conn[str(n)] = f'LINK_{port}_{name}_N'
        # Ckmtw R-RJ45R08P-B000 (C386756) since 2026-10-30, the plain
        # shielded 8P8C the JLCPCB library has: contacts 1-8 on the same
        # 8P8C numbering, 9/10 the shell tabs. Its drawing (2016-03-23)
        # shows the latch keyway at the top of the opening, so it is a
        # tab-up jack where the Kinghelm was tab-down; the imported land
        # (1.02 mm staggered rows, tabs 16.26 mm apart, 3.25 mm posts 12.7
        # mm apart) matches the drawing's PC board layout.
        d.add(ref, 'EasyEDA:R-RJ45R08P-B000', f'LINK {port}',
              'EasyEDA:RJ45-TH_R-RJ45R08P-B000', conn, 'C386756')
        # ESD at the jack: one TPD4E1U06 per two pairs, 0.8 pF per line.
        # The pairs sit between 0 V and 2.5 V, so a to-ground array suffices.
        for (a, b), (c, e) in (((1, 2), (3, 6)), ((4, 5), (7, 8))):
            d.add(next(tvs), 'EasyEDA:TPD4E1U06DBVR', 'TPD4E1U06DBVR',
                  'EasyEDA:SOT-23-6_L2.9-W1.6-P0.95-LS2.8-BR_TPD4E1U06',
                  {'D1+': conn[str(a)], 'D1-': conn[str(b)],
                   'D2+': conn[str(c)], 'D2-': conn[str(e)], 'GND': GND}, 'C124691')

    # ------------------------------------------------ system clock
    # The fabric had no clock of its own: X2 only fed the GTP reference input
    # and the PHY's RXC exists only with a link up. A 50 MHz 3.3 V CMOS
    # oscillator on a bank 14 MRCC ball (tools/alloc.py SYS_CLK) clocks
    # NEORV32 directly or through an MMCM. Pin 1 is the tri-state control,
    # high = running; tied to VDD. Pin names as the imported C717684 symbol.
    d.sheet('FPGA')
    d.group('X4 system clock')             # X4 is the anchor; R147 and the 100 nF stay with it
    d.add('X4', 'EasyEDA:OT322550MJBA4SL', '50MHz CMOS', 'EasyEDA:OSC-SMD_4P-L3.2-W2.5-BL',
          {'VDD': V33, 'GND': GND, 'OUTPUT': 'SYS_CLK_OSC', 'Tri-state': V33}, 'C717684')
    d.C('100nF', V33, GND)
    # 33 ohm at the source keeps the edge clean over the few centimetres to U1.
    d.R('33', 'SYS_CLK_OSC', 'SYS_CLK')

    # ------------------------------------------------ Video
    # HDMI out (DVI-compatible), straight from the fabric. Bank 35 runs at
    # 3.3 V, so its four pairs use TMDS_33: the FPGA sinks current and the
    # monitor's 50 ohm pull-ups to 3.3 V terminate each line (UG471, TMDS_33),
    # so the board adds no termination. 10:1 serialisation in OSERDESE2 makes
    # 720p60 (742.5 Mb/s per lane) comfortable on a -2 part; 1080p60 does not
    # fit an HR bank. Pairs and control lines: tools/alloc.py.
    d.sheet('Video')
    d.group('HDMI out')
    # TPD12S016PW (TI SLLSE96F), Example 2, Figure 18 and Table 3: VCCA at
    # 3.3 V, CT_HPD and LS_OE driven by the controller (here two bank 35
    # balls). The TMDS lines pass the chip's ESD pins on their way to the
    # connector; the A side of DDC/CEC/HPD is at VCCA, the B side at 5 V.
    d.add('U31', 'odin:TPD12S016PW', 'TPD12S016PWR',
          'Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm',
          {'D2+': 'HDMI_D2_P', 'D2-': 'HDMI_D2_N', 'D1+': 'HDMI_D1_P', 'D1-': 'HDMI_D1_N',
           'D0+': 'HDMI_D0_P', 'D0-': 'HDMI_D0_N', 'CLK+': 'HDMI_CLK_P', 'CLK-': 'HDMI_CLK_N',
           'HPD_A': 'HDMI_HPD', 'SCL_A': 'HDMI_SCL', 'SDA_A': 'HDMI_SDA', 'CEC_A': 'HDMI_CEC',
           'HPD_B': 'HDMI_HPD_B', 'SCL_B': 'HDMI_SCL_B', 'SDA_B': 'HDMI_SDA_B', 'CEC_B': 'HDMI_CEC_B',
           'CT_HPD': 'HDMI_CT_HPD', 'LS_OE': 'HDMI_LS_OE',
           'VCCA': V33, 'VCC5V': '+5V', '5V_OUT': 'HDMI_5V', 'GND': GND}, 'C201665')
    # Figure 18: 0.1 uF on VCCA, on VCC5V and on 5V_OUT.
    d.C('100nF', V33, GND); d.C('100nF', '+5V', GND); d.C('100nF', 'HDMI_5V', GND)
    # The two enables default on, so DDC (EDID) and hot plug work under any
    # bitstream; a design may drive them low to save about 170 uA (8.2.2).
    d.R('100k', V33, 'HDMI_CT_HPD'); d.R('100k', V33, 'HDMI_LS_OE')
    # Amphenol 10029449-111RLF, right-angle HDMI type A (the -111 since
    # 2026-10-30: the -001 is nearly out of the JLCPCB library; sheet 4 of
    # the Amphenol 10029449 drawing gives it the same contact pattern and
    # the same 1.30 mm shell holes as the -x01x sheet KiCad's footprint is
    # drawn from, gold-flash contacts, brass shell). Pin 14 (utility,
    # HDMI 1.4 HEAC) is not used: SLLSE96F Figure 19 note, "if unused, tie
    # Reserve Pin to Ground with 75 ohm resistor". The pair shields, DDC/CEC
    # ground and the shell go to ground.
    d.add('J73', 'Connector:HDMI_A', 'HDMI OUT',
          'Connector_Video:HDMI_A_Amphenol_10029449-x01xLF_Horizontal',
          {'D2+': 'HDMI_D2_P', 'D2-': 'HDMI_D2_N', 'D2S': GND,
           'D1+': 'HDMI_D1_P', 'D1-': 'HDMI_D1_N', 'D1S': GND,
           'D0+': 'HDMI_D0_P', 'D0-': 'HDMI_D0_N', 'D0S': GND,
           'CK+': 'HDMI_CLK_P', 'CK-': 'HDMI_CLK_N', 'CKS': GND,
           'CEC': 'HDMI_CEC_B', 'SCL': 'HDMI_SCL_B', 'SDA': 'HDMI_SDA_B',
           'GND': GND, '+5V': 'HDMI_5V', 'HPD': 'HDMI_HPD_B', 'SH': GND,
           'UTILITY': 'HDMI_UTILITY'}, 'C427307')
    d.R('75', 'HDMI_UTILITY', GND)

    # ------------------------------------------------ SDRAM
    # W9825G6KH-6 (datasheet rev A03): 4M x 16 x 4 banks, VDD/VDDQ 3.0 to
    # 3.6 V (section 9, p. 23), TSOP II 54 (section 12, p. 41: D 22.22,
    # E1 10.16, e 0.80 BSC, matching the fitted KiCad footprint). Pin numbers
    # from section 4, p. 4, as the generated odin:W9825G6KH symbol carries
    # them. Balls: tools/alloc.py SDRAM_BANK35 / SDRAM_BANK14. Seven
    # VDD/VDDQ pins (1, 14, 27, 3, 9, 43, 49) get one 100 nF each, plus one
    # 10 uF bulk; the datasheet gives no capacitor values. CLK leaves the
    # FPGA through 22 ohm. CS pulled up and CKE pulled down keep the chip
    # deselected and in power-down until a design drives them.
    d.sheet('Memory')
    d.group('SDRAM')
    sd = {'VDD': V33, 'VDDQ': V33, 'VSS': GND, 'VSSQ': GND, 'NC': '',
          'CLK': 'SDRAM_CLK_MEM', 'CKE': 'SDRAM_CKE', '~{CS}': 'SDRAM_CS_N',
          '~{RAS}': 'SDRAM_RAS_N', '~{CAS}': 'SDRAM_CAS_N', '~{WE}': 'SDRAM_WE_N',
          'LDQM': 'SDRAM_LDQM', 'UDQM': 'SDRAM_UDQM',
          'BS0': 'SDRAM_BA0', 'BS1': 'SDRAM_BA1'}
    for i in range(16): sd[f'DQ{i}'] = f'SDRAM_DQ{i}'
    for i in range(13): sd[f'A{i}'] = f'SDRAM_A{i}'
    d.add('U32', 'odin:W9825G6KH', 'W9825G6KH-6',
          'Package_SO:TSOP-II-54_22.2x10.16mm_P0.8mm', sd, 'C62246')
    for _ in range(7): d.C('100nF', V33, GND)
    d.C('10uF', V33, GND, C0805)
    d.group('U1 SDRAM clock source')       # 22 ohm at the FPGA ball, not at U32
    d.R('22', 'SDRAM_CLK', 'SDRAM_CLK_MEM')
    d.group('SDRAM')
    d.R('10k', V33, 'SDRAM_CS_N', R0603)
    d.R('10k', 'SDRAM_CKE', GND, R0603)

    # ------------------------------------------------ MRAM
    # Everspin MR25H10CDF (datasheet rev 9.5): 1 Mbit SPI MRAM, VDD 2.7 to
    # 3.6 V (Table 4.1, p. 10), DFN-8 Small Flag 5 x 6 mm, 1.27 mm pitch,
    # 2.0 x 2.0 mm exposed pad that connects to nothing but VSS (Figure 6.2,
    # p. 18). Pin names and numbers as the imported C246234 symbol and Table
    # 1.1 (p. 3). "The CS signal should be pulled up to VDD so that the
    # signal tracks the power supply during power-up" (section 4, p. 13):
    # 10k to +3V3. WP and HOLD are not driven by the FPGA: 10k to +3V3
    # each, so writes are allowed and the interface never pauses. Balls:
    # tools/alloc.py MRAM_BALLS. Fitted on every board (owner, 2026-10-29).
    d.sheet('Memory')
    d.group('MRAM')
    d.add('U33', 'EasyEDA:MR25H10CDF', 'MR25H10CDF', f'odin:{MRAM_FP}',
          {'~{CS}': 'MRAM_CS', 'SO': 'MRAM_SO', '~{WP}': 'MRAM_WP', 'VSS': GND,
           'SI': 'MRAM_SI', 'SCK': 'MRAM_SCK', '~{HOLD}': 'MRAM_HOLD',
           'VDD': V33, 'EP': GND}, 'C246234')
    d.C('100nF', V33, GND)
    for net in ('MRAM_CS', 'MRAM_WP', 'MRAM_HOLD'):
        d.R('10k', V33, net, R0603)

    # ------------------------------------------------ microSD socket
    # Hroparts TF-01A (LCSC C91145, JLC extended), push-push, 1.85 mm: pins
    # 1-8 are the microSD contacts in card order (DAT2, CD/DAT3, CMD, VDD,
    # CLK, VSS, DAT0, DAT1), 9 the detect switch, 10-13 the shell, as the
    # imported symbol names them; the drawing (ref/datasheets/tf-01a.pdf)
    # is mechanical only. SPI mode: CS on DAT3, MOSI on CMD, MISO on DAT0.
    # The SD specification wants CS, CMD, DAT0 and the unused DAT1/DAT2
    # pulled up in SPI mode: 10k each. The detect switch closes to the
    # shell; the FPGA reads it through its own pull-up (ref/freya.xdc).
    # The two locating pegs are plain holes (the import had them plated with
    # no annular ring). [verify] switch polarity on the prototype. Balls: tools/alloc.py
    # SD_BALLS.
    d.sheet('Memory')
    d.group('microSD socket')
    d.add('J74', 'EasyEDA:TF-01A_C91145', 'microSD', 'EasyEDA:TF-SMD_TF-01A-NPTH',
          {'DAT2(RSV)': 'SD_DAT2', 'CDDAT3(CS)': 'SD_CS', 'CMD(DI)': 'SD_MOSI',
           'VDD': V33, 'CLK(SCLK)': 'SD_SCK', 'VSS': GND, 'DAT0(D0)': 'SD_MISO',
           'DAT1(RSV)': 'SD_DAT1', 'CD': 'SD_CD', 'GND': GND}, 'C91145')
    for net in ('SD_CS', 'SD_MOSI', 'SD_MISO', 'SD_DAT1', 'SD_DAT2'):
        d.R('10k', V33, net, R0603)
    d.C('100nF', V33, GND); d.C('10uF', V33, GND, C0805)

    # ------------------------------------------------ +1V8_IO and +1V8
    # U14's output node is +1V8_IO (L5, its 2 x 22 uF and the feedback divider
    # sit on it): the 1.8 V position of J19/J20 and the MON_1V8 series
    # resistor are there, and bank 13 with its loads joins it next. VCCAUX
    # and VCCADC are the FPGA's internal supplies; they hang off the node as
    # +1V8 through one bead (50 mohm, 9 mV at the 0.18 A VCCAUX allowance,
    # inside VCCAUX's 1.71 V minimum) and keep their own UG483 decoupling.
    # The 10 uF and 100 nF are the node's own bulk (U14's 2 x 22 uF were the
    # only capacitors on it); they sit with the bead at U1's +1V8_IO balls,
    # the bead's load end (island U1).
    d.sheet('Power')
    d.group('VCCAUX filter')
    d.FB(V18IO, V18)
    d.C('10uF', V18IO, GND, C0805); d.C('100nF', V18IO, GND)

    # ================= 2026-10-29 audit corrections, appended so no earlier
    # designator moves (findings items 34-38, 42, 50). New parts are staged
    # by load_pcb.py and islanded by their anchor's group name below.

    # ---- U34: which 5 V source feeds the +5V rail (item 35)
    # TI TPS2121 priority power mux (SLVSEA3F): IN1 is VBUS, IN2 is U11's
    # output. Both channels block reverse current (9.3.6), the output is
    # current-limited on both (9.3.2) and soft-started (9.3.1), and the
    # switchover is seamless (9.3.7). The selection is wired, not firmware,
    # and it is decided by intent, not by measuring VBUS (items 52, 53):
    #   PR1 = VBUS x 36.5/136.5, CP2 = +3V3 x 56.2/156.2 = 1.19 V, so a plain
    #   5 V VBUS wins (PR1 > CP2, Table 9-3) while nothing pulls PR1 down;
    #   Q6 pulls PR1 to ground while the controller asks for 9 V and for a
    #   few seconds after it stops asking (D24/R/C hold below), so the rail
    #   is on U11 before VBUS starts toward 9 V and stays there until VBUS
    #   is back at 5 V. No comparator threshold can separate the 5.5 V the
    #   USB-PD vSafe5V range allows from the TLV62569's 5.5 V operating
    #   maximum (the OV1 reference alone is 1.01-1.10 V, 7.5 % of window),
    #   so the handoff is not left to one;
    #   Q7 pulls PR1 to ground while the screw input carries voltage, so
    #   with J50 connected the whole board runs from J50 through U11 even
    #   when a 5 V USB cable is also plugged in (item 53: before, a 500 mA
    #   computer port kept the +5V load while a bench supply sat idle);
    #   OV1 = VBUS x 23.2/123.2 crosses the 1.06 V reference at 5.63 V
    #   nominal (5.28-5.94 V over the reference and 1 % resistors): a fault
    #   backstop against a source that raises VBUS without being asked,
    #   inside the TLV62569's 6 V absolute maximum (survival, not an
    #   operating allowance), above the 5.25 V a USB 2.0 port may deliver;
    #   OV2 to GND (U11 is regulated), CP2 above the reference whenever +3V3
    #   is up enables the fast switchover (tSW 5 us typical, SLVSEA3F 7.5;
    #   100 us with CP2 low; no PD transition can happen before +3V3 exists);
    #   RILM 44.2k: 2.5 A typical (2.0-3.0 A, Table 7.5), above the 1.72 A
    #   worst-case rail load, below the 5 A connector contacts;
    #   CSS 100 nF: about 780 V/s at 5 V (Table 9-1), 80 mA into the rail's
    #   ~100 uF.
    # While Q6 or Q7 holds PR1 low on a plain 5 V VBUS, IN2 is U11 in its
    # low-dropout mode (AP63300 DS42002 section 14, near 100 % duty), about
    # VSYS minus 0.1 V: the +5V rail sits near 4.5 V for the length of the
    # negotiation (TLV62569 and SY8047 run from 2.5 V; +5V_EXT is off until
    # firmware enables it). Firmware asks for 9 V at start-up, before EXT_EN,
    # and withdraws the request if U18's PD_STATUS0 (I2C) does not confirm it.
    # ST (open drain, 10k pull-up, 6-20k allowed) tells the controller which
    # input feeds the rail: high = VBUS or none, low = U11.
    d.sheet('Power')
    d.group('U34  +5V source select')
    d.add('U34', 'odin:TPS2121RUX', 'TPS2121RUXR', VQFN12RUX,
          {'IN1': 'VBUS', 'IN2': V5BUCK, 'OUT': V5, 'GND': GND,
           'PR1': 'VBUS5_PR1', 'CP2': 'VBUS5_CP2', 'OV1': 'VBUS5_OV1', 'OV2': GND,
           'ILIM': 'VBUS5_ILIM', 'SS': 'VBUS5_SS', 'ST': 'VBUS5_ST'}, 'C485916')
    d.R('100k', 'VBUS', 'VBUS5_PR1', R0603); d.R('36.5k', 'VBUS5_PR1', GND, R0603)
    d.R('100k', 'VBUS', 'VBUS5_OV1', R0603); d.R('23.2k', 'VBUS5_OV1', GND, R0603)
    d.R('100k', V33, 'VBUS5_CP2', R0603); d.R('56.2k', 'VBUS5_CP2', GND, R0603)
    d.R('44.2k', 'VBUS5_ILIM', GND, R0603)
    d.C('100nF', 'VBUS5_SS', GND)
    d.R('10k', V33, 'VBUS5_ST', R0603)
    d.C('100nF', 'VBUS', GND)          # IN1 bypass; the 10 uF attach allowance is at U26
    for _ in range(2): d.C('22uF', V5, GND, C0805)   # OUT: the rail's bulk after the mux
    VREF_MIN, VREF_TYP, VREF_MAX = 1.01, 1.06, 1.10          # SLVSEA3F 7.5, rising
    MUX_CHECK.clear()
    MUX_CHECK.extend([('VBUS selected above (PR1 > CP2, nothing pulling PR1)', 1.19 * 136.5 / 36.5),
                      ('VBUS invalid above (OV1 rising, typical)', VREF_TYP * 123.2 / 23.2),
                      ('OV1 rising, minimum (reference and 1 % resistors)', VREF_MIN * 123.2 / 23.2 * 0.98),
                      ('OV1 rising, maximum (reference and 1 % resistors)', VREF_MAX * 123.2 / 23.2 * 1.02),
                      ('VBUS valid again below (OV1 falling, typical)', 1.04 * 123.2 / 23.2),
                      ('PR1 at 20 V', 20 * 36.5 / 136.5)])
    if MUX_CHECK[5][1] > 5.5:
        raise ValueError('TPS2121 PR1 pin would exceed 5.5 V at 20 V on VBUS')
    if MUX_CHECK[3][1] > 6.0:
        raise ValueError('OV1 worst case exceeds the TLV62569 6 V absolute maximum')
    if MUX_CHECK[2][1] < 5.25:
        raise ValueError('OV1 worst case would reject a USB 2.0 port at 5.25 V')

    # ---- local input energy storage per converter (item 38): TLV62569
    # SLVSDG1C 8.2.2.5 (4.7 uF at VIN), AP63300 DS42002 Figure 39 (10 uF
    # across VIN/GND). The 100 nF already on each TLV62569 is HF bypass only.
    d.group('U11  VSYS to +5V')
    d.C('10uF', VSYS, GND, C1210)
    for ref, rail in (('U13', V25), ('U14', V18IO), ('U16', V12MGT)):
        d.group(f'{ref}  5V to {rail}')
        d.C('4.7uF', V5, GND, C0603)

    # ---- USB D+/D- series resistors at the controller (item 36)
    # Hardware design with RP2350, section 5.1: 27 ohm in each line, close
    # to the chip. The connector side keeps the USB_DP/USB_DM names so D6
    # stays at J1; the chip side is USB_DP_MCU/USB_DM_MCU.
    d.sheet('Supervisor')
    d.group('U7  USB series resistors')
    d.R('27', 'USB_DP', 'USB_DP_MCU'); d.R('27', 'USB_DM', 'USB_DM_MCU')

    # ---- USB-PD request default (item 37): see the U18 comment above
    d.group('USB-PD sink')
    d.R('4.7k', V33, 'PD_SDA')             # I2C1 pull-up (was the CFG1 10k)
    d.R('100k', 'PD_REQ_9V', GND)          # Q6 off while the controller is dead or in reset

    # ---- PSRAM power-up pin states (item 39). APS6404L-SQN rev 4.0 section
    # 8: from the start of the VDD ramp until 150 us after it is stable, CE#
    # must be high and track VDD within 200 mV, CLK low, and SI/SO/SIO[3:0]
    # low; then a reset-enable/reset pair. The resistors sit on the memory
    # side of the 33 ohm series resistors (the _MEM nets), 10k each: against
    # a floating FPGA pin (PUDC_B high, 10 uA leakage) that is 0.1 V, far
    # below the 0.4 V VIL; CE# follows VDD through the pull-up with no FPGA
    # drive. 20 pull-downs cost 3.6 mA when every line is high. The 150 us
    # wait and the reset sequence are the memory controller's job
    # (ref/psram.md).
    d.sheet('Memory')
    for c in range(4):
        d.group(f'PSRAM{c} power-up state')
        d.R('10k', V18IO, f'PSRAM{c}_CE_B_MEM', R0603)
        for lane in ('SCK', 'IO0', 'IO1', 'IO2', 'IO3'):
            d.R('10k', f'PSRAM{c}_{lane}_MEM', GND, R0603)

    # ---- support parts for U23/U24 (item 41), now TPS22975 (SLVSDD0B
    # 12.1: input and output capacitors close to the device, the CT trace
    # as short as possible). CT: 9.3.1 wants a 30 V minimum rating on the CT
    # capacitor (the pin reaches 15 V); SR = 0.43 x CT(pF) + 26 us/V at
    # VBIAS 5 V, Table 1: 1000 pF gives 1.19 ms at 3.3 V in, 0.7 ms at
    # 1.8 V [verify at VBIAS 3.3 V, the table is taken at 5 V].
    d.sheet('Power')
    for ref, vin, vout in (('U23', 'VCCIO_1', 'VCCIO_1_EXT'),
                           ('U24', 'VCCIO_2', 'VCCIO_2_EXT')):
        d.group(f'{ref}  {vin} to {vout}')
        d.C('100nF', V33, GND)             # VBIAS
        d.C('1nF 50V', f'{ref}_CT', GND)   # about 1.2 ms rise at 3.3 V (Table 1, CT = 1000 pF)
        d.C('1uF', vout, GND, C0603)       # OUT
    d.sheet('Power')

    # ---- the two jumpered I/O domains are measured (item 50)
    d.group('rail monitors')
    for rail, mon in (('VCCIO_1', 'MON_VCCIO_1'), ('VCCIO_2', 'MON_VCCIO_2')):
        d.R('1k', rail, mon, R0603)
        d.C('100nF', mon, GND)
        ADC_CHECK.append((mon, 3.3, 3.3, ADC_FS, ADC_FS, '1k (series)', '-', 1e3))

    # ---- U34 selection by intent (items 52 and 53), appended for designators.
    # Q6 holds PR1 low while PD_REQ_9V is high and, through D24 and the
    # R/C below, for a few seconds after it falls: on the way up the rail
    # is on U11 before the charger moves VBUS; on the way down it stays
    # there until VBUS is back at 5 V (a PD source completes the 9 -> 5 V
    # step well inside a second; tSrcTransition and tSrcSettle, USB PD
    # section 7.6 [verify]). Hold: 470k x 10 uF = 4.7 s; the gate starts at
    # 3.3 V minus one 1N4148W drop (about 2.85 V) and BSS138 turns off at
    # 0.8-1.5 V: 2.4 s minimum (C -20 %), 7.2 s maximum. 1N4148W leakage is
    # 25 nA at 20 V (SOD-123 datasheets), BSS138 IGSS 100 nA at 20 V: under
    # 0.05 V on a 3 uA node. A dead or resetting controller lets PD_REQ_9V
    # fall (R173), which is the same release path. PR1 pulled to ground is
    # Table 9-3's "PR1 < VREF, CP2 >= VREF" row: IN2 whenever IN2 is valid.
    d.sheet('Power')
    d.group('Q6  mux hold: 9 V request')     # its own island, the RC at its gate
    d.add('Q6', 'Transistor_FET:Q_NMOS_GSD', 'BSS138LT1G',
          'EasyEDA:SOT-23-3_L2.9-W1.6-P1.90-LS2.8-BR',
          {'D': 'VBUS5_PR1', 'S': GND, 'G': 'SEL_IN2'}, 'C82045')
    d.add('D24', 'Device:D', '1N4148W', 'Diode_SMD:D_SOD-123',
          {'A': 'PD_REQ_9V', 'K': 'SEL_IN2'}, 'C81598')
    d.R('470k', 'SEL_IN2', GND, R0603)
    d.C('10uF', 'SEL_IN2', GND, C0805)
    # Q7 holds PR1 low while the screw input carries voltage: 100k/33k from
    # VIN_EXT (before D4, so VBUS cannot lift it) gives 2.2 V at the 9 V
    # minimum input, above BSS138's 1.5 V maximum threshold, and 5.2 V at
    # 21 V, inside its 20 V gate rating. It turns on between 3.2 and 6.0 V
    # of VIN_EXT, below the 9 V where U11 regulates, so the board is on U11
    # before J50 reaches its range. The 0603 top resistor sees 21 V.
    d.group('Q7  mux hold: screw input present')     # its own island
    d.add('Q7', 'Transistor_FET:Q_NMOS_GSD', 'BSS138LT1G',
          'EasyEDA:SOT-23-3_L2.9-W1.6-P1.90-LS2.8-BR',
          {'D': 'VBUS5_PR1', 'S': GND, 'G': 'EXT_PRESENT'}, 'C82045')
    d.R('100k', 'VIN_EXT', 'EXT_PRESENT', R0603); d.R('33k', 'EXT_PRESENT', GND, R0603)
    # IN2 bypass at U34's own pin (item 57): SLVSEA3F 11 wants each of IN1,
    # IN2 and OUT bypassed close to the device; the 3 x 22 uF at U11 are the
    # bulk and stay the planning reason for putting U34 beside U11.
    d.group('U34  +5V source select')
    d.C('1uF', V5BUCK, GND, C0603)
    MUX_CHECK.extend([('Q6 hold after PD_REQ_9V falls, minimum (s)', 0.47e6 * 10e-6 * 0.8 * 0.99 * __import__('math').log(2.85 / 1.5)),
                      ('Q6 hold after PD_REQ_9V falls, maximum (s)', 0.47e6 * 10e-6 * 1.2 * 1.01 * __import__('math').log(2.85 / 0.8)),
                      ('Q7 on above VIN_EXT, latest (Vth 1.5 V)', 1.5 * 133 / 33),
                      ('Q7 gate at 21 V on VIN_EXT', 21 * 33 / 133)])
    if MUX_CHECK[-1][1] > 20.0:
        raise ValueError('Q7 gate exceeds the BSS138 20 V rating at 21 V on J50')
    if MUX_CHECK[-2][1] > 9.0:
        raise ValueError('Q7 is not guaranteed on at the 9 V minimum screw input')

    # ---- FPGA configuration flash chip select (item 54). UG470 Table 2-4:
    # FCS_B needs an external pull-up of at most 4.7k to VCCO_14 (+3V3);
    # the internal configuration pull-ups are off (PUDC_B high, item 39)
    # and W25Q256JV 4.1/9.3 wants CS# to follow VCC through power-up and
    # power-down. The controller reaches FLASH_CS_B through R22 (33 ohm):
    # an RP2350 pad at reset has its pull-down enabled (about 50-80k,
    # RP2350 datasheet, pad control registers [verify]), which leaves CS
    # near 3.0 V through 4.7k, so neither the dead nor the resetting
    # controller can select the flash.
    d.sheet('FPGA')
    d.group('config flash')
    d.R('4.7k', V33, 'FLASH_CS_B')

    # ---- HUSB238 straps and the second I2C pull-up (2026-10-30), appended so
    # no earlier designator moves: VSET 0 ohm = 5 V (Table 5), ISET 4.53k =
    # 1.5 A (Table 6: every 5 V or 9 V PDO of a 15 W source satisfies it).
    d.sheet('Supervisor')
    d.group('USB-PD sink')
    d.R('4.7k', V33, 'PD_SCL')
    d.R('0', 'PD_VSET', GND)
    d.R('4.53k', 'PD_ISET', GND)

    # ---- LMR33630 support parts for U11/U12 (2026-10-30), appended so no
    # earlier designator moves: 9.2.2.8 the 1 uF VCC capacitor, 9.2.2.6 the
    # 220 nF high-frequency input bypass (50 V X7R by the HV rule).
    d.sheet('Power')
    for ref, grp in (('U11', 'U11  VSYS to +5V'), ('U12', 'U12  VSYS to +3V3  (always on)')):
        d.group(grp)
        d.C('1uF', f'{ref}_VCC', GND, C0603)
        d.C('220nF', VSYS, GND, C0603)

    # ---- TPS564201 support parts for U15 (2026-10-30), appended so no
    # earlier designator moves: 8.2.2.5 the 100 nF bootstrap capacitor,
    # 8.2.2.4 the optional 100 nF at VIN.
    d.sheet('Power')
    d.group('U15  5V to +1V0  (4A FPGA core supply)')
    d.C('100nF', 'BST+1V0', 'SW+1V0')
    d.C('100nF', V5, GND)

    # ---- U26 current monitor resistor (TPS25942A since 2026-10-30, 9.3.7):
    # appended so no earlier designator moves; island U26 by group name.
    d.sheet('Power')
    d.group('input OR-ing')
    d.R('10k', 'VBUS_IMON', GND, R0603)

    # Mandatory connector-accounting gate. A post is a ground probe/key, not
    # a mated contact; each section separately has four signal grounds plus
    # the three female power-row grounds.
    byref = {p['ref']: p for p in d.parts}
    for s in 'ABCDEFGH':
        if sum(n == GND for row in rows[s] for n in row) != 4:
            raise ValueError(f'SLOT {s}: signal section must have exactly 4 GND contacts')
    for s, jref in (('L', 'J7'), ('M', 'J8')):
        if sum(n == GND for n in byref[jref]['pins'].values()) != 4:
            raise ValueError(f'SLOT {s}: signal section must have exactly 4 GND contacts')
    for s, jref in power_ref.items():
        if sum(n == GND for n in byref[jref]['pins'].values()) != 3:
            raise ValueError(f'SLOT {s}: power row must have exactly 3 GND contacts')
        if set(byref[f'MK{ord(s)}']['pins'].values()) != {GND}:
            raise ValueError(f'SLOT {s}: inline post is not GND')
    print('ground sanity: 10 sections x (4 signal GND + 3 power GND + 1 GND post); rail neighbors OK')
    # Sequential C refs must never run into the explicit 300-series decaps.
    if d._n['C'] >= 300:
        raise ValueError(f"sequential C refs reached C{d._n['C']}; the FPGA decaps start at C301")
    print(f'FPGA decoupling: {decap_refs} parts, C301..C{300 + decap_refs}')

    # Nothing ships unqualified: every non-generic part must carry a real MPN,
    # package and rating in tools/qualified.py, fitted with the footprint
    # recorded there. Imported here rather than at module scope because
    # qualified.py reads this design to build its table.
    from qualified import check
    check(d.parts)
    return d

if __name__ == '__main__':
    d = build()
    print("rail  target  actual   Rtop/Rbot")
    for rail, tgt, act, rt, rb in RAIL_CHECK:
        flag = 'OK' if abs(act-tgt)/tgt < 0.02 else 'FAIL'
        print(f"  {rail:9s} {tgt:5.2f}V {act:6.3f}V  {rt}/{rb}  {flag}")
    print("\nU34 +5V source select (TPS2121)")
    for what, v in MUX_CHECK:
        print(f"  {what:56s} {v:5.2f} {'s' if '(s)' in what else 'V'}")
    print("\nmonitor        rail      reads   at max          divider   Zsrc")
    for name, vnom, vn, vmax, vm, rt, rb, z in ADC_CHECK:
        print(f"  {name:10s} {vnom:5.2f}V  {vn:5.3f}V  {vm:5.3f}V@{vmax:5.2f}V  "
              f"{rt}/{rb:8s} {z/1e3:5.1f}k")
    print(f"\nparts: {len(d.parts)}")
    nets = {}
    for p in d.parts:
        for pin, n in p['pins'].items(): nets.setdefault(n, []).append(f"{p['ref']}.{pin}")
    print(f"nets:  {len(nets)}")
    single = [n for n, v in nets.items() if len(v) == 1]
    print(f"single-node nets: {len(single)}  {sorted(single)[:12]}")
