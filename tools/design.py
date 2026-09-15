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
SOT563  = 'EasyEDA:SOT-563_L1.6-W1.2-P0.50-LS1.6-BL'
SOT236_ESD = 'EasyEDA:SOT-23-6_L2.9-W1.6-P0.95-LS2.8-BR'
SOT236_BUCK = 'EasyEDA:SOT-23-6_L2.9-W1.6-P0.95-LS2.8-BL'
SOT236_LOAD = 'EasyEDA:SOT-23-6_L2.9-W1.6-P0.95-LS2.8-BL_3'
SOT236_AP = 'EasyEDA:TSOT-23-6_L2.9-W1.6-P0.95-LS2.8-BR'
SSOP10  = 'EasyEDA:ESSOP-10_L4.9-W3.9-P1.0-LS6.0-TL-EP'
SOIC16W = 'Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm'
TSSOP8  = 'EasyEDA:TSSOP-8_L4.4-W3.0-P0.65-LS6.4-BL'
QFN80   = 'EasyEDA:QFN-80_L10.0-W10.0-P0.40-TL-EP3.4'
TSSOP24_SWITCH = 'EasyEDA:TSSOP-24_L7.8-W4.4-P0.65-LS6.4-BL'
TSSOP24_XLATE = 'EasyEDA:TSSOP-24_L7.8-W4.4-P0.65-LS6.4-BL_1'
VSSOP8_LVC2T45 = 'EasyEDA:VSSOP-8_L2.1-W2.4-P0.50-LS3.2-BL'
QFN16_SY8047 = 'EasyEDA:TQFN-16_L3.0-W3.0-P0.50-TL-EP1.6'
VQFN10RPU = 'Package_DFN_QFN:Texas_RPU0010A_VQFN-HR-10_2x2mm_P0.5mm'
EXT2x8  = 'EasyEDA:HDR-SMD_16P-P2.54-V-F-R2-C8-LS7.1'
EXT2x16 = 'EasyEDA:HDR-SMD_32P-P2.54-V-F-R2-C16-LS7.1'
EXT1x16 = 'EasyEDA:HDR-TH_16P-P2.54-V-F-1'
EXT1x8  = 'EasyEDA:HDR-TH_8P-P2.54-V-F'
HDR2x3  = 'EasyEDA:HDR-TH_6P-P2.54-V-M-R2-C3-S2.54-1'
HDR2x5  = 'Connector_PinHeader_2.54mm:PinHeader_2x05_P2.54mm_Vertical'
HDR1x2  = 'Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical'
HDR1x3  = 'Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical'
XTAL    = 'EasyEDA:CRYSTAL-SMD_4P-L3.2-W2.5-BL'
USBC    = 'Connector_USB:USB_C_Receptacle_HCTL_HC-TYPE-C-16P-01A'
LED0603 = 'LED_SMD:LED_0603_1608Metric'

LCSC = {'APS1604M-3SQRx-SN':'C18214056',
        'TLV62569DRL':'C163217', 'TPS54202DDC':'C191884'}

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
    # Rails that can sit above 3.3 V, and the rating a capacitor on them needs.
    # A 22uF 6.3V part on the 12 V AUX rail fails on first power-up, and the
    # value string is the only place a schematic reader will see the
    # difference, so it is put there automatically rather than typed.
    # Everything unmarked is 16 V minimum, X5R or better -- see
    # ref/qualified-parts.md.
    HV = {'VSYS': '25V', 'VBUS': '25V', '+12V': '25V'}

    def C(self, val, a, b, fp=C0402):
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
        }.get((fp, base), '')
        return self.add(self.seq('C'), 'Device:C', val, fp, {'1': a, '2': b}, lcsc)
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
    def F(self, val, a, b):
        # KiCad ships no *polyfuse* footprint, which is what the symbol's filter
        # asks for; a 1206 chip PTC is the physically correct package.
        selected = {
            '200mA': (PTC1206_EASYEDA, 'C269111'),  # 24 V maximum
            '300mA': (PTC1206_EASYEDA, 'C22378340'), # 16 V maximum
            '500mA': (PTC1206_EASYEDA, 'C269115'),  # 6 V maximum
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
VSYS_ABSMAX = 20.0   # J50 is a bare header: assume someone feeds it 20 V
V5_ABSMAX   = 9.0    # Q2 closed on a 9 V PD contract -- a firmware fault, but
                     # a monitor that dies in that fault cannot report it

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
V12, V5, V33, V25, V18, V10, V12MGT = 'VSYS', '+5V', '+3V3', '+2V5', '+1V8', '+1V0', '+1V2_MGT'
V10MGT, GND = '+1V0_MGT', 'GND'
V12B = '+12V'          # boosted from 5V, so AUX works on any USB source
VCCIO = {'14': V33, '15': 'VCCIO_1', '34': 'VCCIO_2'}

RAIL_CHECK = []

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

    # FPGA decoupling: one 100nF per supply ball, plus bulk per rail
    supply_balls = [(b, net_for(b, n, assigned)) for bank, lst in
                    list(io.items()) + list(other.items()) for b, n in lst
                    if net_for(b, n, assigned) in
                    (V10, V18, V33, 'VCCIO_1', 'VCCIO_2', V10MGT, V12MGT)]
    for ball, rail in supply_balls:
        d.group(f'decoupling {rail}'); d.C('100nF', rail, GND)
    for rail, n in ((V10, 4), (V18, 2), (V33, 2), ('VCCIO_1', 2), ('VCCIO_2', 2),
                    (V10MGT, 1), (V12MGT, 1)):
        d.group(f'bulk {rail}')
        for _ in range(n): d.C('4.7uF', rail, GND, C0603)

    d.group('config straps (UG470)')
    # config straps (UG470)
    d.R('4.7k', V33, 'CFG_M0'); d.R('4.7k', 'CFG_M1', GND); d.R('4.7k', 'CFG_M2', GND)
    d.R('4.7k', V33, 'CFG_PROG_B'); d.R('4.7k', V33, 'CFG_INIT_B')
    d.R('4.7k', 'PUDC_B', GND)                    # pull-ups enabled during config
    d.R('330', 'CFG_DONE', 'DONE_LED_A')
    d.add('D1', 'EasyEDA:F.0603.00025_P2-0603G1TS2-06T-002',
          'F.0603.00025/P2-0603G1TS2-06T-002', 'EasyEDA:LED0603-RD_GREEN',
          {'C': GND, 'A': 'DONE_LED_A'}, 'C7496818')

    d.sheet('Memory')
    # ------------------------------------------------ PSRAM x4
    for c in range(4):
        p = f'PSRAM{c}_'
        d.group(f'PSRAM{c}')
        d.add(f'U{2+c}', 'Memory_RAM:APS1604M-3SQRx-SN', 'APS1604M-3SQR-SN', SOIC8N,
              {'~{CE}': p+'CE_B', 'SCLK': p+'SCK', 'SI/SIO0': p+'IO0', 'SO/SIO1': p+'IO1',
               'SIO2': p+'IO2', 'SIO3': p+'IO3', 'VDD': V33, 'VSS': GND}, LCSC['APS1604M-3SQRx-SN'])
        d.C('100nF', V33, GND)

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
           'USB_DM': 'USB_DM', 'USB_DP': 'USB_DP',
           'QSPI_SCLK': 'SUPF_CLK', '~{QSPI_SS}': 'SUPF_CS',
           'QSPI_SD0': 'SUPF_D0', 'QSPI_SD1': 'SUPF_D1',
           'QSPI_SD2': 'SUPF_D2', 'QSPI_SD3': 'SUPF_D3'}
    gp = {0:'SUP_JTAG_TCK', 1:'SUP_JTAG_TMS', 2:'SUP_JTAG_TDI', 3:'SUP_JTAG_TDO',
          4:'SUP_PROG_B', 5:'SUP_INIT_B', 6:'SUP_DONE', 7:'SUP_CCLK',
          9:'SUP_FCS_B', 10:'SUP_FD0', 11:'SUP_FD1', 12:'SUP_FD2', 13:'SUP_FD3',
          15:'SUP_DBG_TCK', 16:'SUP_DBG_TMS', 17:'SUP_DBG_TDI', 18:'SUP_DBG_TDO',
          19:'SUP_UART_TX', 20:'SUP_UART_RX',
          21:'EN_VBUS5', 22:'EN_2V5', 23:'EN_1V8', 24:'EN_1V0', 25:'EN_1V2', 26:'EN_5V',
          27:'PD_CFG1', 28:'PD_CFG2', 29:'PD_CFG3', 30:'PD_PG',
          8:'EXT_EN', 14:'SFP_SCL', 31:'SFP_SDA',
          32:'SFP0_MOD_ABS', 33:'SFP0_TX_DIS', 34:'SFP0_TX_FAULT', 35:'SFP0_LOS',
          36:'SFP1_MOD_ABS', 37:'SFP1_TX_DIS', 38:'SFP1_TX_FAULT', 39:'SFP1_LOS'}
    for g, n in gp.items(): sup[f'GPIO{g}'] = n
    sup['GPIO47/ADC7'] = 'EXT_FAULT'
    sup['GPIO46/ADC6'] = 'EN_12V'
    for a, n in enumerate(['MON_VSYS','MON_5V','MON_3V3','MON_2V5','MON_1V8','MON_1V0']):
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
           'D+': 'USB_DP', 'D-': 'USB_DM'}, 'C2894897')
    # CH224K owns the CC lines and negotiates; no plain 5.1k pull-downs here.
    # The supervisor drives CFG1..3, so the requested voltage is firmware, not
    # a strap, and it reads PG to know whether the request succeeded.
    d.group('USB protection')
    # A student board gets its USB cable handled constantly. Protect the data
    # and CC lines, and clamp VBUS above the highest voltage PD will negotiate.
    d.add('D6', 'Power_Protection:ESDA6V1BC6', 'ESDA6V1BC6', SOT236_ESD,
          {'COM': GND, 'TVS1': 'USB_DP', 'TVS2': 'USB_DM',
           'TVS3': 'USB_CC1', 'TVS4': 'USB_CC2'}, 'C495220')
    # SMBJ13A is UNIDIRECTIONAL: cathode to VBUS, anode to ground. Reversed, it
    # forward-conducts on ordinary VBUS and shorts the supply. KiCad's
    # Device:D_TVS is the bidirectional (SMBJ13CA) symbol and cannot express
    # that orientation, so use the polarised avalanche-diode symbol -- which is
    # what a unidirectional TVS physically is -- and name the part in the value.
    d.add('D7', 'Device:D_Zener', 'SMBJ13A-TR', 'EasyEDA:SMB_L4.6-W3.6-LS5.3-RD',
          {'K': 'VBUS', 'A': GND}, 'C133675')

    d.group('USB-PD sink')
    d.add('U18', 'Interface_USB:CH224K', 'CH224K', SSOP10,
          {'VDD': 'PD_VDD', 'VBUS': 'VBUS', 'GND': GND,
           'CC1': 'USB_CC1', 'CC2': 'USB_CC2',
           'CFG1': 'PD_CFG1', 'CFG2': 'PD_CFG2', 'CFG3': 'PD_CFG3',
           'PG': 'PD_PG', 'DP': '', 'DM': ''}, 'C970725')
    d.C('1uF', 'PD_VDD', GND)      # VDD is the chip's own LDO output, decouple only
    d.R('10k', V33, 'PD_PG')
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
    for bus, ref in enumerate(('U9', 'U10')):
        d.group(f'5V BUS {bus} converter')
        conn = {'VCCA': V33, 'VCCB': V5, 'GND': GND,
                'DIR': f'BUS5V{bus}_DIR', '~{OE}': GND}
        for i in range(8):
            conn[f'A{i+1}'] = f'BUS5V{bus}_IO{i}'
            conn[f'B{i+1}'] = f'BUS5V{bus}_PIN{i}'
        d.add(ref, 'odin:SN74LXC8T245PW', 'SN74LXC8T245PWR',
              TSSOP24_XLATE, conn, 'C4363995')
        d.C('100nF', V33, GND); d.C('100nF', V5, GND)

    d.sheet('Slots')
    # ------------------------------------------------ shield connectors
    # A-H are eight logical zones.  Each has a 2x8 signal block plus a separate
    # 1x8 power row.  Adjacent zones share continuous 2x16 + 1x16 connector
    # bodies: AB, CD, EF and GH.  Power is kept out of the signal rows so the
    # connector reads plainly and all four exported supplies get nearby ground.
    rows = {}
    for s, (bank, _prs) in slots.items():
        if s in ('L', 'M'): continue
        aux = f'SLOT_{s}_POWER'
        sig = [f'SLOT{s}_IO{i}' for i in range(12)]
        rows[s] = ([sig[i] for i in range(0, 12, 2)] + [GND, GND],
                   [sig[i] for i in range(1, 12, 2)] + [GND, GND])

    for jn, (sa, sb) in enumerate((('A','B'), ('C','D'), ('E','F'), ('G','H')), 3):
        d.group(f'SHIELD HEADER {sa}{sb}')
        pins = {}
        for zone, s in enumerate((sa, sb)):
            rowa, rowb = rows[s]
            for i in range(8):
                col = zone * 8 + i
                # C3975161 numbers one complete physical row 1..16 and the
                # return row 32..17. Map by connector position, not by the
                # odd/even numbering of the temporary KiCad header.
                pins[str(col+1)] = rowa[i]
                pins[str(32-col)] = rowb[i]
        d.add(f'J{jn}', 'EasyEDA:PM254-2-16-S-8.5',
              'PM254-2-16-S-8.5', EXT2x16, pins, 'C3975161')

        power = {}
        for zone, s in enumerate((sa, sb)):
            rail = [GND, f'SLOT_{s}_PIN_VOLTAGE', GND, f'SLOT_{s}_3V3',
                    GND, f'SLOT_{s}_5V', GND, f'SLOT_{s}_POWER']
            for i, net_name in enumerate(rail):
                power[str(zone*8+i+1)] = net_name
        d.add(f'J{50+jn}', 'EasyEDA:ZX-PM2.54-1-16PY',
              'ZX-PM2.54-1-16PY', EXT1x16, power, 'C7499334')

    # Two identical complete 8-bit, 5V-compatible buses. Signals stay on the
    # 2x8 block; all exported power stays on the adjacent 1x8 row.
    for bus, (s, jn) in enumerate((('L', 7), ('M', 8))):
        sig = [f'BUS5V{bus}_PIN{i}' for i in range(8)]
        pins = {}
        row0 = [sig[i] for i in range(0, 8, 2)] + [GND]*4
        row1 = [sig[i] for i in range(1, 8, 2)] + [GND]*4
        for i in range(8):
            pins[str(2*i+1)] = row0[i]
            pins[str(2*i+2)] = row1[i]
        d.add(f'J{jn}', 'EasyEDA:PM254-2-08-S-8.5',
              'PM254-2-08-S-8.5', EXT2x8, pins, 'C3975153')
        power = [GND, f'SLOT_{s}_PIN_VOLTAGE', GND, f'SLOT_{s}_3V3',
                 GND, f'SLOT_{s}_5V', GND, f'SLOT_{s}_POWER']
        d.add(f'J{57+bus}', 'EasyEDA:Header-Female-2.54_1x8',
              '2.54-1*8P', EXT1x8,
              {str(i+1): n for i, n in enumerate(power)}, 'C27438')

    # Each logical zone still owns independent branch fuses, AUX selection and
    # a key position even though adjacent zones share one connector body.
    selector_ref = {'L': 10, 'M': 21, **{s: 11+i for i, s in enumerate('ABCDEFGH')}}
    for s, (bank, _prs) in slots.items():
        d.group(f'SLOT {s} branches')
        vio_ext = ('+3V3_EXT' if s in ('L', 'M') else
                   ('VCCIO_1_EXT' if bank == '15' else 'VCCIO_2_EXT'))
        aux = f'SLOT_{s}_POWER'
        # A bare header cannot stop a reversed extension. Odin_0 solved this
        # with a 1x1 male post; retain one key position per logical zone.
        d.add(f'MK{ord(s)}', 'EasyEDA:PH2.54-1X1P-H25',
              'PH2.54-1X1P-H25', 'EasyEDA:HDR-TH_1P-P2.54-V-M',
              {'1': GND}, 'C42431799')
        # per-module resettable fuse on every exported rail
        # Per-slot fuses are FAULT protection, not a current allocation. The
        # shared source budgets are far smaller than 9 x these ratings; see
        # ref/extension-ux.md. Sized so one slot cannot take the whole rail.
        d.F('500mA', vio_ext, f'SLOT_{s}_PIN_VOLTAGE')
        d.F('500mA', '+5V_EXT', f'SLOT_{s}_5V')
        d.F('300mA', '+3V3_EXT', f'SLOT_{s}_3V3')
        selected_power = f'SLOT_{s}_POWER_SELECTED'
        d.F('200mA', selected_power, aux)
        # AUX selector: 2x3, jumper picks VIN / +5V / +3V3
        d.add(f'J{selector_ref[s]}', 'EasyEDA:Header-Male-2.54_2x3',
              '2.54-2*3P', HDR2x3,
              {'1': '+12V_EXT', '2': selected_power, '3': '+5V_EXT',
               '4': selected_power, '5': '+3V3_EXT', '6': selected_power}, 'C65114')
        d.C('10uF', f'SLOT_{s}_PIN_VOLTAGE', GND, C0805)
        d.C('100nF', f'SLOT_{s}_3V3', GND)

    # VCCIO domain selectors (bank 15 and bank 34)
    for jn, (dom, net) in enumerate((('1', 'VCCIO_1'), ('2', 'VCCIO_2')), 19):
        d.group(f'VCCIO_{dom} selector')
        zones = 'A-D' if dom == '1' else 'E-H'
        d.add(f'J{jn}', 'EasyEDA:Header-Male-2.54_2x3',
              '2.54-2*3P', HDR2x3,
              {'1': V33, '2': net, '3': V25, '4': net,
               '5': V18, '6': net}, 'C65114')
        for _ in range(2): d.C('22uF', net, GND, C0805)

    d.sheet('HighSpeed')
    # ------------------------------------------------ two fast serial ports
    d.group('125MHz reference clock')
    d.add('X2', 'EasyEDA:DSC1123CI2-125.0000', 'DSC1123CI2-125.0000',
          'EasyEDA:OSC-SMD_6P-L3.2-W2.5-BL',
          {'VDD': V33, 'GND': GND, 'Enable': V33,
           'Output': 'REFCLK_OSC_P', '~{Output}': 'REFCLK_OSC_N'}, 'C617173')
    d.C('100nF', V33, GND); d.C('4.7uF', V33, GND, C0603)
    d.C('100nF', 'REFCLK_OSC_P', 'MGTREFCLK0P')      # AC-couple the reference clock
    d.C('100nF', 'REFCLK_OSC_N', 'MGTREFCLK0N')
    d.R('100', 'MGTRREF', GND, R0603)                # value to confirm vs UG482
    # high-side switch: gate pulled to +3V3 so the cages are OFF until the
    # supervisor has booted and decided a module is safe to power
    d.group('SFP power gate')
    d.add('Q1', 'Transistor_FET:Q_PMOS_GSD', 'DMG2305UX-7',
          'EasyEDA:SOT-23-3_L2.9-W1.3-P1.90-LS2.4-BR',
          {'S': V33, 'D': 'SFP_VCC', 'G': 'EN_SFP_N'}, 'C5261054')
    d.R('100k', V33, 'EN_SFP_N')
    d.C('10uF', 'SFP_VCC', GND, C0805)
    d.group('SFP I2C bus')
    for n in ('SFP_SCL', 'SFP_SDA'): d.R('4.7k', V33, n)
    for c in range(2):
        d.group(f'SFP port {c}')
        p = f'SFP{c}_'
        ctl = lambda k: p + k
        sfp_label = f'SFP {c}'
        d.add(f'J{60+c}', 'Interface_Optical:SFP', sfp_label,
              'EasyEDA:CONN-SMD_20P-P0.80-S8.20_1888247-1',
              {'TD+': p+'TD_P', 'TD-': p+'TD_N', 'RD+': p+'RD_P', 'RD-': p+'RD_N',
               'MOD_DEF1': 'SFP_SCL', 'MOD_DEF2': 'SFP_SDA',
               'MOD_DEF0': ctl('MOD_ABS'), 'TX_DISABLE': ctl('TX_DIS'),
               'TX_FAULT': ctl('TX_FAULT'), 'RX_LOS': ctl('LOS'),
               'RATE_SELECT': GND, 'VccT': 'SFP_VCC', 'VccR': 'SFP_VCC',
               'VeeT': GND, 'VeeR': GND}, 'C305914')
        # Separate press-fit shield/cage, installed after reflow.  All twenty
        # mechanical shield tails bond directly to the ground plane.
        d.add(f'SH{c+1}', 'EasyEDA:2007198-1', '2007198-1',
              'EasyEDA:TH_HC-SFP-01L',
              {str(pin): GND for pin in range(1, 21)}, 'C573949')
        # AC coupling: 100nF in series on all four high-speed lines
        d.C('100nF', f'MGTPTXP{c}', p+'TD_P'); d.C('100nF', f'MGTPTXN{c}', p+'TD_N')
        d.C('100nF', p+'RD_P', f'MGTPRXP{c}'); d.C('100nF', p+'RD_N', f'MGTPRXN{c}')
        d.C('100nF', 'SFP_VCC', GND)
        for k in ('MOD_ABS', 'TX_FAULT', 'LOS'): d.R('4.7k', V33, p+k)

    # P7's power-up-high state safely keeps the active-low SFP gate off and
    # frees a supervisor pin for EXT_FAULT. The remaining expander pins are
    # intentionally spare; they are not fictional SFP ports.
    d.group('SFP port expander')
    d.add('U17', 'EasyEDA:PCF8574T_3,518', 'PCF8574T_3,518',
          'EasyEDA:SOIC-16_L10.3-W7.5-P1.27-LS10.3-BL',
          {'VDD': V33, 'VSS': GND, 'SCL': 'SFP_SCL', 'SDA': 'SFP_SDA',
           'A0': GND, 'A1': GND, 'A2': V33, '~{INT}': 'SFP_EXP_INT',
           'P7': 'EN_SFP_N'}, 'C7605')
    d.C('100nF', V33, GND)
    d.R('4.7k', V33, 'SFP_EXP_INT')

    d.sheet('Power')
    # ------------------------------------------------ power tree
    d.group('VBUS pass switch to +5V')
    # On a plain 5V source the buck cannot make 5V from 5V, so VBUS feeds the
    # rail directly -- but ONLY then. Once PD negotiates 9V this must be open
    # or 8.6V lands on regulators rated 5.5V. Hence a switch the supervisor
    # commands, default OFF, not a diode that cannot be told to stop.
    d.add('Q2', 'Transistor_FET:Q_PMOS_GSD', 'DMG2305UX-7',
          'EasyEDA:SOT-23-3_L2.9-W1.3-P1.90-LS2.4-BR',
          {'S': 'VBUS', 'D': V5, 'G': 'VBUS5_GATE'}, 'C5261054')
    d.R('100k', 'VBUS', 'VBUS5_GATE', R0603)      # default open
    d.add('Q3', 'Transistor_FET:Q_NMOS_GSD', 'BSS138LT1G',
          'EasyEDA:SOT-23-3_L2.9-W1.6-P1.90-LS2.8-BR',
          {'D': 'VBUS5_PULL', 'S': GND, 'G': 'EN_VBUS5_G'}, 'C82045')
    d.R('10k', 'EN_VBUS5', 'EN_VBUS5_G'); d.R('100k', 'EN_VBUS5_G', GND)
    # Slew the gate rather than slamming it. Closing this switch connects VBUS
    # to 66uF of +5V bulk; done in a microsecond that is an arc at the
    # connector and a droop at the source. 10k into 100nF against the 100k
    # pull-up gives roughly a 1ms ramp, so the inrush is a few hundred mA.
    d.R('10k', 'VBUS5_PULL', 'VBUS5_GATE', R0603)
    d.C('100nF', 'VBUS5_GATE', 'VBUS')

    d.group('input OR-ing')
    d.add('J50', 'EasyEDA:KF301-5.0-2P', '9-14V POWER IN',
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
    # gate ramp becomes a linear current ramp. 100k/47k enables at 3.75V;
    # 73.2k/10k cuts off above 9.98V; 1.65k sets 2.03A typical current limit.
    # 2.2nF gives 0.91V/ms, so charging the 44uF VSYS bulk draws about 40mA.
    # It is input-powered and automatic because this path creates +3V3.
    d.add('U26', 'odin:TPS259470ARPW', 'TPS259470ARPWR', VQFN10RPU,
          {'EN/UVLO':'VBUS_UVLO', 'OVLO':'VBUS_OVLO', 'FLT':'EXT_FAULT',
           'IN':'VBUS', 'OUT':'VBUS_SS', 'dVdt':'VBUS_DVDT',
           'GND':GND, 'ILM':'VBUS_ILM'}, 'C3662799')
    d.R('100k', 'VBUS', 'VBUS_UVLO', R0603); d.R('47k', 'VBUS_UVLO', GND, R0603)
    d.R('73.2k', 'VBUS', 'VBUS_OVLO', R0603); d.R('10k', 'VBUS_OVLO', GND, R0603)
    d.R('1.65k', 'VBUS_ILM', GND, R0603)
    d.C('2.2nF 25V', 'VBUS_DVDT', GND)
    d.add('D3', 'Device:D_Schottky', 'SS34', 'EasyEDA:SMA_L4.3-W2.6-LS5.2-RD',
          {'A': 'VBUS_SS', 'K': V12}, 'C8678')
    d.add('D4', 'Device:D_Schottky', 'SS34', 'EasyEDA:SMA_L4.3-W2.6-LS5.2-RD',
          {'A': 'VIN_EXT', 'K': V12}, 'C8678')
    d.C('22uF', V12, GND, C0805); d.C('22uF', V12, GND, C0805)
    d.C('10uF', 'VBUS', GND, C0805)
    # 12V -> 5V
    d.group('U11  12V to 5V')
    d.add('U11', 'Regulator_Switching:TPS54202DDC', 'TPS54202DDCR', SOT236_BUCK,
          {'VIN': V12, 'GND': GND, 'EN': 'EN_5V', 'FB': 'FB_5V',
           'SW': 'SW_5V', 'BOOT': 'BOOT_5V'}, LCSC['TPS54202DDC'])
    d.C('100nF', 'BOOT_5V', 'SW_5V'); d.L('10uH', V5, 'SW_5V')
    rt, rb, act = fb_divider(5.0, 0.596)          # TPS54202 Vref = 0.596 V
    d.R(rt, V5, 'FB_5V', R0603); d.R(rb, 'FB_5V', GND, R0603)
    RAIL_CHECK.append(('+5V', 5.0, act, rt, rb))
    for _ in range(3): d.C('22uF', V5, GND, C0805)
    # 5V -> the low rails
    # +3V3 is ALWAYS ON and powers the supervisor. AP63300 works down to 3.8V,
    # below the 4.27V weak-port worst case, and its 3A rating covers both
    # protected VCCIO domains at their maximum current-limit tolerance.
    d.group('U12  VSYS to +3V3  (always-on AP63300 reference circuit)')
    rt3, rb3 = '93.1k', '30.1k'
    act3 = 0.8 * (1 + 93.1 / 30.1)
    RAIL_CHECK.append((V33, 3.3, act3, rt3, rb3))
    d.add('U12', 'odin:AP63300WU', 'AP63300WU-7', SOT236_AP,
          {'VIN': V12, 'GND': GND, 'FB': 'FB_3V3',
           'SW': 'SW_3V3', 'BST': 'BOOT_3V3'}, 'C2158012')
    d.C('10uF', V12, GND, C0805)
    d.C('100nF', 'BOOT_3V3', 'SW_3V3'); d.L('4.7uH', V33, 'SW_3V3')
    d.R(rt3, V33, 'FB_3V3', R0603); d.R(rb3, 'FB_3V3', GND, R0603)
    d.C('56pF', V33, 'FB_3V3')
    for _ in range(3): d.C('22uF', V33, GND, C0805)

    for ref, rail, en, vtgt in (('U13', V25, 'EN_2V5', 2.5),
                                ('U14', V18, 'EN_1V8', 1.8),
                                ('U16', V12MGT, 'EN_1V2', 1.2)):
        top, bot, act = fb_divider(vtgt, 0.600)   # TLV62569 Vfb = 0.600 V
        RAIL_CHECK.append((rail, vtgt, act, top, bot))
        d.group(f'{ref}  5V to {rail}')
        fb = f'FB{rail}'; sw = f'SW{rail}'
        d.add(ref, 'Regulator_Switching:TLV62569DRL', 'TLV62569DRLR', SOT563,
              {'VIN': V5, 'GND': GND, 'EN': en, 'FB': fb, 'SW': sw},
              LCSC['TLV62569DRL'])
        d.L('2.2uH', rail, sw)
        d.R(top, rail, fb, R0603); d.R(bot, fb, GND, R0603)
        for _ in range(2): d.C('22uF', rail, GND, C0805)
        d.C('100nF', V5, GND)
    # FPGA core supply. The SY8047 is not pin-compatible with the three
    # TLV62569 rails above; implement its reference circuit explicitly.
    top, bot, act = fb_divider(1.0, 0.600)
    RAIL_CHECK.append((V10, 1.0, act, top, bot))
    d.group('U15  5V to +1V0  (4A FPGA core supply)')
    d.add('U15', 'EasyEDA:SY8047QDC', 'SY8047QDC', QFN16_SY8047,
          {'LX': 'SW+1V0', 'PG': 'CORE_1V0_GOOD', 'FB': 'FB+1V0',
           'AGND': GND, 'SS': 'CORE_1V0_SS', 'SVIN': 'CORE_1V0_SVIN',
           'PVIN': V5, 'EN': 'EN_1V0', 'PGND': GND, 'EP': GND}, 'C3018651')
    d.C('22uF', V5, GND, C0805)
    d.R('10', V5, 'CORE_1V0_SVIN', R0603)
    d.C('1uF', 'CORE_1V0_SVIN', GND, C0603)
    d.C('1nF', 'CORE_1V0_SS', GND)
    d.R('100k', V33, 'CORE_1V0_GOOD')
    d.L('1uH_core', V10, 'SW+1V0')
    d.R(top, V10, 'FB+1V0', R0603); d.R(bot, 'FB+1V0', GND, R0603)
    d.C('22pF', V10, 'FB+1V0')
    for _ in range(2): d.C('22uF', V10, GND, C0805)
    d.group('MGTAVCC filter')
    d.group('U19  5V to 12V boost (AUX)')
    # AUX must work on a plain 5V port too, so 12V is boosted from the 5V rail
    # rather than taken from VSYS. PD then buys headroom, not functionality.
    rt, rb, act = fb_divider(12.0, 1.238)         # TPS61085 Vref = 1.238 V
    RAIL_CHECK.append((V12B, 12.0, act, rt, rb))
    d.add('U19', 'Regulator_Switching:TPS61085PW', 'TPS61085PWR', TSSOP8,
          {'VIN': V5, 'GND': GND, 'EN': 'EN_12V', 'SW': 'SW_12V', 'FB': 'FB_12V',
           'COMP': 'COMP_12V', 'FREQ': GND, 'SS': 'SS_12V'}, 'C13505')
    d.L('10uH', V5, 'SW_12V')
    d.add('D5', 'Device:D_Schottky', 'SS34', 'EasyEDA:SMA_L4.3-W2.6-LS5.2-RD',
          {'A': 'SW_12V', 'K': V12B}, 'C8678')
    d.R(rt, V12B, 'FB_12V', R0603); d.R(rb, 'FB_12V', GND, R0603)
    d.R('47k', 'COMP_12V', 'COMP_12V_C'); d.C('2.2nF', 'COMP_12V_C', GND)
    d.C('10nF', 'SS_12V', GND)
    for _ in range(2): d.C('10uF', V12B, GND, C0805)
    d.C('10uF', V5, GND, C0805)

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
        ('U23', 'VCCIO_1', 'VCCIO_1_EXT', '2.21k', 0.500),
        ('U24', 'VCCIO_2', 'VCCIO_2_EXT', '2.21k', 0.500),
    ]
    for ref, vin, vout, rilim, _ilim in low_ext:
        d.group(f'{ref}  {vin} to {vout}')
        d.add(ref, 'odin:TPS22950CDDC', 'TPS22950CDDCR', SOT236_LOAD,
              {'ON':'EXT_EN', 'VIN':vin, 'GND':GND, 'ILIM':f'{ref}_ILIM',
               'VOUT':vout, 'FLT':'EXT_FAULT'}, 'C7587833')
        d.R(rilim, f'{ref}_ILIM', GND, R0603)
        d.C('1uF', vin, GND, C0603)

    # Latch-off TPS259470L protects AUX. 6.65k sets 500mA typical
    # (425..575mA), below the boost's computed 622mA capability. 121k/12.1k
    # sets 13.2V nominal OVLO. 3.3nF gives about a 20ms 12V rise. ITIMER open
    # selects the fastest response; AUXOFF is unused.
    d.group('U25  +12V to +12V_EXT')
    d.add('U25', 'odin:TPS259470LRPW', 'TPS259470LRPWR', VQFN10RPU,
          {'EN/UVLO':'EXT_EN', 'OVLO':'EXT12_OVLO', 'FLT':'EXT_FAULT',
           'IN':V12B, 'OUT':'+12V_EXT', 'dVdt':'EXT12_DVDT',
           'GND':GND, 'ILM':'EXT12_ILM'}, 'C3662793')
    d.R('121k', V12B, 'EXT12_OVLO', R0603)
    d.R('12.1k', 'EXT12_OVLO', GND, R0603)
    d.R('6.65k', 'EXT12_ILM', GND, R0603)
    d.C('3.3nF 25V', 'EXT12_DVDT', GND)
    d.C('1uF', V12B, GND, C0603)

    d.group('MGTAVCC filter')
    # MGTAVCC 1.0V filtered off +1V0
    d.L('1uH', V10MGT, V10); d.C('4.7uF', V10MGT, GND, C0603)
    d.group('rail monitors')
    # Rail monitors into the supervisor ADC. The two rails that can sit above
    # +3V3 are divided; the dividers are sized from the absolute maximum the
    # hardware can present, not from the nominal rail -- see adc_divider().
    for rail, mon, vnom, vmax in ((V12, 'MON_VSYS', 9.0, VSYS_ABSMAX),
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
