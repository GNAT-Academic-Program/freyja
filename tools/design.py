#!/usr/bin/env python3
"""Declarative netlist for Odin. Parts connect by PIN NAME; numbers are resolved
from the KiCad symbol libraries so nothing is hand-typed and nothing is guessed."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import symlib
from alloc import assign, load
from collections import OrderedDict

FP_FPGA = 'odin:BGA-324_15x15mm_Layout18x18_P0.8mm'
C0402   = 'Capacitor_SMD:C_0402_1005Metric'
C0603   = 'Capacitor_SMD:C_0603_1608Metric'
C0805   = 'Capacitor_SMD:C_0805_2012Metric'
R0402   = 'Resistor_SMD:R_0402_1005Metric'
R0603   = 'Resistor_SMD:R_0603_1608Metric'
L_IND   = 'Inductor_SMD:L_Bourns-SRN4018'
SOT236  = 'Package_TO_SOT_SMD:SOT-23-6'
SOIC8W  = 'Package_SO:SOIC-8_5.3x5.3mm_P1.27mm'
USON8   = 'Package_SON:Winbond_USON-8-1EP_3x2mm_P0.5mm_EP0.2x1.6mm'
QFN80   = 'Package_DFN_QFN:QFN-80-1EP_10x10mm_P0.4mm_EP3.4x3.4mm_ThermalVias'
TSSOP24 = 'Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm'
HDR2x8  = 'Connector_PinHeader_2.54mm:PinHeader_2x08_P2.54mm_Vertical_SMD'
HDR2x3  = 'Connector_PinHeader_2.54mm:PinHeader_2x03_P2.54mm_Vertical'
HDR2x5  = 'Connector_PinHeader_2.54mm:PinHeader_2x05_P2.54mm_Vertical'
HDR1x2  = 'Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical'
XTAL    = 'Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm'
USBC    = 'Connector_USB:USB_C_Receptacle_HCTL_HC-TYPE-C-16P-01A'
LED0603 = 'LED_SMD:LED_0603_1608Metric'

LCSC = {'APS1604M-3SQRx-SN':'C18214056', 'W25Q32JVZP':'C82317',
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
    def add(self, ref, lib_id, value, fp, conn, lcsc='', dnp=False):
        if any(q['ref'] == ref for q in self.parts):
            raise ValueError(f"duplicate designator {ref}")
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
    def seq(self, pre):
        self._n[pre] = self._n.get(pre, 0) + 1
        return f'{pre}{self._n[pre]}'
    def C(self, val, a, b, fp=C0402):
        return self.add(self.seq('C'), 'Device:C', val, fp, {'1': a, '2': b})
    def R(self, val, a, b, fp=R0402):
        return self.add(self.seq('R'), 'Device:R', val, fp, {'1': a, '2': b})
    def L(self, val, a, b):
        return self.add(self.seq('L'), 'Device:L', val, L_IND, {'1': a, '2': b})
    def F(self, val, a, b):
        return self.add(self.seq('F'), 'Device:Polyfuse', val, R0603, {'1': a, '2': b})

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

# ---------------------------------------------------------------- rails
V12, V5, V33, V25, V18, V10, V12MGT = 'VSYS', '+5V', '+3V3', '+2V5', '+1V8', '+1V0', '+1V2_MGT'
V10MGT, GND = '+1V0_MGT', 'GND'
VCCIO = {'14': V33, '15': 'VCCIO_1', '34': 'VCCIO_2'}

RAIL_CHECK = []

def build():
    RAIL_CHECK.clear()
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
    d.add('U1', 'odin:XC7A50T-2CSG325I', 'XC7A50T-2CSG325I', FP_FPGA, fpga_pins)

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
    d.add('D1', 'Device:LED', 'green', LED0603, {'K': GND, 'A': 'DONE_LED_A'})

    d.sheet('Memory')
    # ------------------------------------------------ PSRAM x4
    for c in range(4):
        p = f'PSRAM{c}_'
        d.group(f'PSRAM{c}')
        d.add(f'U{2+c}', 'Memory_RAM:APS1604M-3SQRx-SN', 'APS1604M-3SQR-SN', SOIC8W,
              {'~{CE}': p+'CE_B', 'SCLK': p+'SCK', 'SI/SIO0': p+'IO0', 'SO/SIO1': p+'IO1',
               'SIO2': p+'IO2', 'SIO3': p+'IO3', 'VDD': V33, 'VSS': GND}, LCSC['APS1604M-3SQRx-SN'])
        d.C('100nF', V33, GND)

    d.sheet('Memory')
    # ------------------------------------------------ config flash (FPGA master SPI)
    d.group('config flash')
    d.add('U6', 'odin:W25Q256JVEIQ', 'W25Q256JVEIQ', SOIC8W,
          {'~{CS}': 'FLASH_CS_B', 'CLK': 'CFG_CCLK', 'DI/IO0': 'FLASH_D0_MOSI',
           'DO/IO1': 'FLASH_D1_MISO', '~{WP}/IO2': 'FLASH_D2_WP',
           '~{HOLD}/IO3': 'FLASH_D3_HOLD', 'VCC': V33, 'GND': GND}, 'C97522')
    d.C('100nF', V33, GND)

    d.sheet('Supervisor')
    # ------------------------------------------------ U7 : RP2350B supervisor
    sup = {'GND': GND, 'IOVDD': V33, 'DVDD': '+1V1', 'ADC_AVDD': V33,
           'QSPI_IOVDD': V33, 'USB_OTP_VDD': V33,
           'VREG_VIN': V33, 'VREG_AVDD': V33, 'VREG_PGND': GND,
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
          21:'EN_3V3', 22:'EN_2V5', 23:'EN_1V8', 24:'EN_1V0', 25:'EN_1V2', 26:'EN_5V',
          27:'PD_CFG1', 28:'PD_CFG2', 29:'PD_CFG3', 30:'PD_PG',
          14:'SFP_SCL', 31:'SFP_SDA',
          32:'SFP0_MOD_ABS', 33:'SFP0_TX_DIS', 34:'SFP0_TX_FAULT', 35:'SFP0_LOS',
          36:'SFP1_MOD_ABS', 37:'SFP1_TX_DIS', 38:'SFP1_TX_FAULT', 39:'SFP1_LOS'}
    for g, n in gp.items(): sup[f'GPIO{g}'] = n
    sup['GPIO47/ADC7'] = 'EN_SFP_N'
    for a, n in enumerate(['MON_VSYS','MON_5V','MON_3V3','MON_2V5','MON_1V8','MON_1V0','MON_1V2']):
        sup[f'GPIO{40+a}/ADC{a}'] = n
    d.group('U7  supervisor')
    d.add('U7', 'MCU_RaspberryPi:RP2350B', 'RP2350B', QFN80, sup)
    for _ in range(8): d.C('100nF', V33, GND)
    for _ in range(4): d.C('100nF', '+1V1', GND)
    d.C('4.7uF', '+1V1', GND, C0603); d.C('10uF', V33, GND, C0805)
    d.L('3.3uH', '+1V1', 'SUP_LX')
    d.group('crystal')
    d.add('Y1', 'Device:Crystal_GND24', '12MHz', XTAL,
          {'1': 'SUP_XIN', '3': 'SUP_XOUT', 'G': GND})
    d.C('15pF', 'SUP_XIN', GND); d.C('15pF', 'SUP_XOUT', GND)
    d.R('1k', V33, 'SUP_RUN'); d.C('100nF', 'SUP_RUN', GND)
    d.group('supervisor boot flash')
    d.add('U8', 'Memory_Flash:W25Q32JVZP', 'W25Q32JVZP', USON8,
          {'~{CS}': 'SUPF_CS', 'CLK': 'SUPF_CLK', 'DI/IO_{0}': 'SUPF_D0',
           'DO/IO_{1}': 'SUPF_D1', '~{WP}/IO_{2}': 'SUPF_D2',
           '~{HOLD}/~{RESET}/IO_{3}': 'SUPF_D3', 'VCC': V33, 'GND': GND, 'EP': GND},
          LCSC['W25Q32JVZP'])
    d.C('100nF', V33, GND)
    d.group('USB-C')
    d.add('J1', 'Connector:USB_C_Receptacle_USB2.0_16P', 'USB-C', USBC,
          {'VBUS': 'VBUS', 'GND': GND, 'SHIELD': GND, 'CC1': 'USB_CC1', 'CC2': 'USB_CC2',
           'D+': 'USB_DP', 'D-': 'USB_DM'})
    # CH224K owns the CC lines and negotiates; no plain 5.1k pull-downs here.
    # The supervisor drives CFG1..3, so the requested voltage is firmware, not
    # a strap, and it reads PG to know whether the request succeeded.
    d.group('USB-PD sink')
    d.add('U18', 'Interface_USB:CH224K', 'CH224K', 'Package_DFN_QFN:QFN-12-1EP_3x3mm_P0.5mm_EP1.45x1.45mm',
          {'VDD': 'PD_VDD', 'VBUS': 'VBUS', 'GND': GND,
           'CC1': 'USB_CC1', 'CC2': 'USB_CC2',
           'CFG1': 'PD_CFG1', 'CFG2': 'PD_CFG2', 'CFG3': 'PD_CFG3',
           'PG': 'PD_PG', 'DP': '', 'DM': ''})
    d.C('1uF', 'PD_VDD', GND)      # VDD is the chip's own LDO output, decouple only
    d.R('10k', V33, 'PD_PG')
    d.add('SW1', 'Switch:SW_Push', 'BOOTSEL', 'Button_Switch_SMD:SW_SPST_B3U-1000P',
          {'1': 'SUPF_CS', '2': GND})

    d.group('supervisor SWD')
    d.add('J51', 'Connector_Generic:Conn_01x03', 'SUP_SWD',
          'Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical',
          {'Pin_1': 'SUP_SWCLK', 'Pin_2': GND, 'Pin_3': 'SUP_SWDIO'})

    # series resistors on every supervisor<->FPGA shared line (33R)
    d.group('series resistors to FPGA')
    for a, b in [('SUP_JTAG_TCK','JTAG_TCK'), ('SUP_JTAG_TMS','JTAG_TMS'),
                 ('SUP_JTAG_TDI','JTAG_TDI'), ('SUP_JTAG_TDO','JTAG_TDO'),
                 ('SUP_PROG_B','CFG_PROG_B'), ('SUP_INIT_B','CFG_INIT_B'),
                 ('SUP_DONE','CFG_DONE'), ('SUP_CCLK','CFG_CCLK'),
                 ('SUP_FCS_B','FLASH_CS_B'), ('SUP_FD0','FLASH_D0_MOSI'),
                 ('SUP_FD1','FLASH_D1_MISO'), ('SUP_FD2','FLASH_D2_WP'),
                 ('SUP_FD3','FLASH_D3_HOLD'),
                 ('SUP_DBG_TCK','DBG_TCK'), ('SUP_DBG_TMS','DBG_TMS'),
                 ('SUP_DBG_TDI','DBG_TDI'), ('SUP_DBG_TDO','DBG_TDO'),
                 ('SUP_UART_TX','SB_UART_RX'), ('SUP_UART_RX','SB_UART_TX')]:
        d.R('33', a, b)
    # manual JTAG header in parallel, jumper isolates the supervisor
    d.group('manual JTAG header')
    d.add('J2', 'Connector_Generic:Conn_02x05_Odd_Even', 'JTAG', HDR2x5,
          {'Pin_1': V33, 'Pin_2': GND, 'Pin_3': 'JTAG_TMS', 'Pin_4': GND,
           'Pin_5': 'JTAG_TCK', 'Pin_6': GND, 'Pin_7': 'JTAG_TDO', 'Pin_8': GND,
           'Pin_9': 'JTAG_TDI', 'Pin_10': GND})

    d.sheet('Slots')
    # ------------------------------------------------ slot L level shifters
    lsl = [f'SLOTL_P{i}_{s}' for i in range(5) for s in ('P', 'N')]
    for k in range(2):
        d.group(f'slot L level shifter {k}')
        conn = {'VCCA': V33, 'VCCB': V5, 'GND': GND,
                'DIR': f'SLOTL_DIR{k}', '~{OE}': GND}
        for i in range(8):
            idx = k*8 + i
            conn[f'A{i+1}'] = lsl[idx] if idx < 10 else ''
            conn[f'B{i+1}'] = f'SLOTL_IO{idx}' if idx < 10 else ''
        d.add(f'U{9+k}', 'Logic_LevelTranslator:SN74AVC8T245PW', 'SN74AVC8T245PW',
              TSSOP24, {k_: v for k_, v in conn.items() if v})
        d.C('100nF', V33, GND); d.C('100nF', V5, GND)

    d.sheet('Slots')
    # ------------------------------------------------ nine slots
    jn = 3
    for s, (bank, prs) in slots.items():
        d.group(f'SLOT {s}')
        vio = VCCIO[bank]
        aux = f'AUX_{s}'
        sig = ([f'SLOTL_IO{i}' for i in range(10)] if s == 'L'
               else [f'SLOT{s}_P{i}_{q}' for i in range(5) for q in ('P', 'N')])
        #  row A: P0+ P1+ GND P2+ P3+ P4+ VCCIO +5V   (odd pins 1,3,5,..,15)
        #  row B: P0- P1- GND P2- P3- P4- +3V3  AUX   (even pins 2,4,6,..,16)
        rowA = [sig[0], sig[2], GND, sig[4], sig[6], sig[8], f'VIO_{s}', f'V5_{s}']
        rowB = [sig[1], sig[3], GND, sig[5], sig[7], sig[9], f'V33_{s}', aux]
        pins = {}
        for i in range(8):
            pins[f'Pin_{2*i+1}'] = rowA[i]
            pins[f'Pin_{2*i+2}'] = rowB[i]
        d.add(f'J{jn}', 'Connector_Generic:Conn_02x08_Odd_Even', f'SLOT_{s}', HDR2x8, pins)
        jn += 1
        # per-module resettable fuse on every exported rail
        d.F('500mA', vio, f'VIO_{s}'); d.F('1A', V5, f'V5_{s}')
        d.F('500mA', V33, f'V33_{s}'); d.F('500mA', f'AUXSEL_{s}', aux)
        # AUX selector: 2x3, jumper picks VIN / +5V / +3V3
        d.add(f'J{jn}', 'Connector_Generic:Conn_02x03_Odd_Even', f'AUX_SEL_{s}', HDR2x3,
              {'Pin_1': V12, 'Pin_2': f'AUXSEL_{s}', 'Pin_3': V5,
               'Pin_4': f'AUXSEL_{s}', 'Pin_5': V33, 'Pin_6': f'AUXSEL_{s}'})
        jn += 1
        d.C('10uF', f'VIO_{s}', GND, C0805); d.C('100nF', f'V33_{s}', GND)

    # VCCIO domain selectors (bank 15 and bank 34)
    for dom, net in (('1', 'VCCIO_1'), ('2', 'VCCIO_2')):
        d.group(f'VCCIO_{dom} selector')
        d.add(f'J{jn}', 'Connector_Generic:Conn_02x03_Odd_Even', f'VCCIO{dom}_SEL', HDR2x3,
              {'Pin_1': V33, 'Pin_2': net, 'Pin_3': V25, 'Pin_4': net,
               'Pin_5': V18, 'Pin_6': net})
        jn += 1
        for _ in range(2): d.C('22uF', net, GND, C0805)

    d.sheet('HighSpeed')
    # ------------------------------------------------ four fast serial lanes
    # Lanes 0/1 get populated SFP cages; 2/3 get identical footprints left
    # empty, so filling them later is a soldering iron, not a respin.
    d.group('125MHz reference clock')
    d.add('X2', 'odin:OSC_DIFF_6P_3225', '125MHz LVDS',
          'Oscillator:Oscillator_SMD_SiTime_SiT9121-6Pin_3.2x2.5mm',
          {'VDD': V33, 'GND': GND, 'OE': V33, 'OUT+': 'REFCLK_OSC_P',
           'OUT-': 'REFCLK_OSC_N'})
    d.C('100nF', V33, GND); d.C('4.7uF', V33, GND, C0603)
    d.C('100nF', 'REFCLK_OSC_P', 'MGTREFCLK0P')      # AC-couple the reference clock
    d.C('100nF', 'REFCLK_OSC_N', 'MGTREFCLK0N')
    d.R('100', 'MGTRREF', GND, R0603)                # value to confirm vs UG482
    # high-side switch: gate pulled to +3V3 so the cages are OFF until the
    # supervisor has booted and decided a module is safe to power
    d.group('SFP power gate')
    d.add('Q1', 'Device:Q_PMOS', 'SFP power gate', 'Package_TO_SOT_SMD:SOT-23',
          {'S': V33, 'D': 'SFP_VCC', 'G': 'EN_SFP_N'})
    d.R('100k', V33, 'EN_SFP_N')
    d.C('10uF', 'SFP_VCC', GND, C0805)
    d.group('SFP I2C bus')
    for n in ('SFP_SCL', 'SFP_SDA'): d.R('4.7k', V33, n)
    for c in range(4):
        d.group(f'SFP cage {c}' + ('' if c < 2 else ' (not fitted)'))
        pop = c < 2
        p = f'SFP{c}_'
        ctl = (lambda k: p + k) if pop else (lambda k: f'SFP{c}_{k}_NP')
        d.add(f'J{60+c}', 'Interface_Optical:SFP', f'SFP cage {c}',
              'Connector:Connector_SFP_and_Cage',
              {'TD+': p+'TD_P', 'TD-': p+'TD_N', 'RD+': p+'RD_P', 'RD-': p+'RD_N',
               'MOD_DEF1': 'SFP_SCL', 'MOD_DEF2': 'SFP_SDA',
               'MOD_DEF0': ctl('MOD_ABS'), 'TX_DISABLE': ctl('TX_DIS'),
               'TX_FAULT': ctl('TX_FAULT'), 'RX_LOS': ctl('LOS'),
               'RATE_SELECT': GND, 'VccT': 'SFP_VCC', 'VccR': 'SFP_VCC',
               'VeeT': GND, 'VeeR': GND, 'CAGE': GND}, dnp=not pop)
        # AC coupling: 100nF in series on all four high-speed lines
        d.C('100nF', f'MGTPTXP{c}', p+'TD_P'); d.C('100nF', f'MGTPTXN{c}', p+'TD_N')
        d.C('100nF', p+'RD_P', f'MGTPRXP{c}'); d.C('100nF', p+'RD_N', f'MGTPRXN{c}')
        d.C('100nF', 'SFP_VCC', GND)
        if pop:                                       # open-collector status lines
            for k in ('MOD_ABS', 'TX_FAULT', 'LOS'): d.R('4.7k', V33, p+k)

    # Cages 2/3 are unpopulated, so their control lines have no supervisor pin
    # left. An I2C expander footprint (also unpopulated) sits on the SFP bus:
    # fit it together with the cages and all four are fully controllable.
    d.group('SFP port expander (not fitted)')
    d.add('U17', 'Interface_Expansion:PCF8574T', 'PCF8574T',
          'Package_SO:SOIC-16_3.9x9.9mm_P1.27mm',
          {'VDD': V33, 'GND': GND, 'SCL': 'SFP_SCL', 'SDA': 'SFP_SDA',
           'A0': GND, 'A1': GND, 'A2': V33, '~{INT}': 'SFP_EXP_INT',
           'P0': 'SFP2_MOD_ABS_NP', 'P1': 'SFP2_TX_DIS_NP',
           'P2': 'SFP2_TX_FAULT_NP', 'P3': 'SFP2_LOS_NP',
           'P4': 'SFP3_MOD_ABS_NP', 'P5': 'SFP3_TX_DIS_NP',
           'P6': 'SFP3_TX_FAULT_NP', 'P7': 'SFP3_LOS_NP'}, dnp=True)
    d.C('100nF', V33, GND)
    d.R('4.7k', V33, 'SFP_EXP_INT')

    d.sheet('Power')
    # ------------------------------------------------ power tree
    d.group('input OR-ing')
    d.add('J50', 'Connector_Generic:Conn_01x02', 'VIN (optional)', HDR1x2,
          {'Pin_1': 'VIN_EXT', 'Pin_2': GND})
    d.add('D3', 'Device:D_Schottky', 'SS34', 'Diode_SMD:D_SMA',
          {'A': 'VBUS', 'K': V12})          # USB-C, normally 9V after negotiation
    d.add('D4', 'Device:D_Schottky', 'SS34', 'Diode_SMD:D_SMA',
          {'A': 'VIN_EXT', 'K': V12})       # optional external supply, higher wins
    d.C('22uF', V12, GND, C0805); d.C('22uF', V12, GND, C0805)
    d.add('D2', 'Device:D_Schottky', 'SS34', 'Diode_SMD:D_SMA',
          {'A': 'VBUS', 'K': V5})          # USB can power the board when VIN is absent
    d.C('10uF', 'VBUS', GND, C0805)
    # 12V -> 5V
    d.group('U11  12V to 5V')
    d.add('U11', 'Regulator_Switching:TPS54202DDC', 'TPS54202DDC', SOT236,
          {'VIN': V12, 'GND': GND, 'EN': 'EN_5V', 'FB': 'FB_5V',
           'SW': 'SW_5V', 'BOOT': 'BOOT_5V'}, LCSC['TPS54202DDC'])
    d.C('100nF', 'BOOT_5V', 'SW_5V'); d.L('4.7uH', V5, 'SW_5V')
    rt, rb, act = fb_divider(5.0, 0.596)          # TPS54202 Vref = 0.596 V
    d.R(rt, V5, 'FB_5V', R0603); d.R(rb, 'FB_5V', GND, R0603)
    RAIL_CHECK.append(('+5V', 5.0, act, rt, rb))
    for _ in range(3): d.C('22uF', V5, GND, C0805)
    # 5V -> the low rails
    for ref, rail, en, vtgt in (('U12', V33, 'EN_3V3', 3.3),
                                ('U13', V25, 'EN_2V5', 2.5),
                                ('U14', V18, 'EN_1V8', 1.8),
                                ('U15', V10, 'EN_1V0', 1.0),
                                ('U16', V12MGT, 'EN_1V2', 1.2)):
        top, bot, act = fb_divider(vtgt, 0.600)   # TLV62569 Vfb = 0.600 V
        RAIL_CHECK.append((rail, vtgt, act, top, bot))
        d.group(f'{ref}  5V to {rail}')
        fb = f'FB{rail}'; sw = f'SW{rail}'
        d.add(ref, 'Regulator_Switching:TLV62569DRL', 'TLV62569DRL', SOT236,
              {'VIN': V5, 'GND': GND, 'EN': en, 'FB': fb, 'SW': sw},
              LCSC['TLV62569DRL'])
        d.L('1.5uH', rail, sw)
        d.R(top, rail, fb, R0603); d.R(bot, fb, GND, R0603)
        for _ in range(2): d.C('22uF', rail, GND, C0805)
        d.C('100nF', V5, GND)
    d.group('MGTAVCC filter')
    # MGTAVCC 1.0V filtered off +1V0
    d.L('1uH', V10MGT, V10); d.C('4.7uF', V10MGT, GND, C0603)
    d.group('rail monitors')
    # rail monitors into the supervisor ADC (divide the ones above 3.3V)
    d.R('100k', V12, 'MON_VSYS', R0603); d.R('33k', 'MON_VSYS', GND, R0603)
    d.R('100k', V5,  'MON_5V',  R0603); d.R('100k', 'MON_5V', GND, R0603)
    for rail, mon in ((V33,'MON_3V3'), (V25,'MON_2V5'), (V18,'MON_1V8'),
                      (V10,'MON_1V0'), (V12MGT,'MON_1V2')):
        d.R('1k', rail, mon, R0603)

    return d

if __name__ == '__main__':
    d = build()
    print("rail  target  actual   Rtop/Rbot")
    for rail, tgt, act, rt, rb in RAIL_CHECK:
        flag = 'OK' if abs(act-tgt)/tgt < 0.02 else 'FAIL'
        print(f"  {rail:9s} {tgt:5.2f}V {act:6.3f}V  {rt}/{rb}  {flag}")
    print(f"parts: {len(d.parts)}")
    nets = {}
    for p in d.parts:
        for pin, n in p['pins'].items(): nets.setdefault(n, []).append(f"{p['ref']}.{pin}")
    print(f"nets:  {len(nets)}")
    single = [n for n, v in nets.items() if len(v) == 1]
    print(f"single-node nets: {len(single)}  {sorted(single)[:12]}")
