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
                               pins=pins, lcsc=lcsc, dnp=dnp, sym=sym))
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
V12, V5, V33, V25, V18, V10, V12MGT = '+12V', '+5V', '+3V3', '+2V5', '+1V8', '+1V0', '+1V2_MGT'
V10MGT, GND = '+1V0_MGT', 'GND'
VCCIO = {'14': V33, '15': 'VCCIO_1', '34': 'VCCIO_2'}

RAIL_CHECK = []

def build():
    RAIL_CHECK.clear()
    d = Design()
    assigned, psram, sb, slots, io, other = assign()

    # ------------------------------------------------ U1 : the FPGA
    from gen_sch import net_for            # reuse the ball->net policy
    fpga_pins = {}
    for bank, lst in list(io.items()) + list(other.items()):
        for ball, name in lst:
            n = net_for(ball, name, assigned)
            if n: fpga_pins[ball] = n
    d.add('U1', 'odin:XC7A50T-2CSG325I', 'XC7A50T-2CSG325I', FP_FPGA, fpga_pins)

    # FPGA decoupling: one 100nF per supply ball, plus bulk per rail
    supply_balls = [(b, net_for(b, n, assigned)) for bank, lst in
                    list(io.items()) + list(other.items()) for b, n in lst
                    if net_for(b, n, assigned) in
                    (V10, V18, V33, 'VCCIO_1', 'VCCIO_2', V10MGT, V12MGT)]
    for ball, rail in supply_balls: d.C('100nF', rail, GND)
    for rail, n in ((V10, 4), (V18, 2), (V33, 2), ('VCCIO_1', 2), ('VCCIO_2', 2),
                    (V10MGT, 1), (V12MGT, 1)):
        for _ in range(n): d.C('4.7uF', rail, GND, C0603)

    # config straps (UG470)
    d.R('4.7k', 'CFG_M0', V33); d.R('4.7k', 'CFG_M1', GND); d.R('4.7k', 'CFG_M2', GND)
    d.R('4.7k', 'CFG_PROG_B', V33); d.R('4.7k', 'CFG_INIT_B', V33)
    d.R('4.7k', 'PUDC_B', GND)                    # pull-ups enabled during config
    d.R('330', 'CFG_DONE', 'DONE_LED_A')
    d.add('D1', 'Device:LED', 'green', LED0603, {'K': GND, 'A': 'DONE_LED_A'})

    # ------------------------------------------------ PSRAM x4
    for c in range(4):
        p = f'PSRAM{c}_'
        d.add(f'U{2+c}', 'Memory_RAM:APS1604M-3SQRx-SN', 'APS1604M-3SQR-SN', SOIC8W,
              {'~{CE}': p+'CE_B', 'SCLK': p+'SCK', 'SI/SIO0': p+'IO0', 'SO/SIO1': p+'IO1',
               'SIO2': p+'IO2', 'SIO3': p+'IO3', 'VDD': V33, 'VSS': GND}, LCSC['APS1604M-3SQRx-SN'])
        d.C('100nF', V33, GND)

    # ------------------------------------------------ config flash (FPGA master SPI)
    d.add('U6', 'odin:W25Q256JVEIQ', 'W25Q256JVEIQ', SOIC8W,
          {'~{CS}': 'FLASH_CS_B', 'CLK': 'CFG_CCLK', 'DI/IO0': 'FLASH_D0_MOSI',
           'DO/IO1': 'FLASH_D1_MISO', '~{WP}/IO2': 'FLASH_D2_WP',
           '~{HOLD}/IO3': 'FLASH_D3_HOLD', 'VCC': V33, 'GND': GND}, 'C97522')
    d.C('100nF', V33, GND)

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
          27:'BOARDID_0', 28:'BOARDID_1', 29:'BOARDID_2', 30:'BOARDID_3'}
    for g, n in gp.items(): sup[f'GPIO{g}'] = n
    for a, n in enumerate(['MON_12V','MON_5V','MON_3V3','MON_2V5','MON_1V8','MON_1V0','MON_1V2','MON_VCCIO1']):
        sup[f'GPIO{40+a}/ADC{a}'] = n
    d.add('U7', 'MCU_RaspberryPi:RP2350B', 'RP2350B', QFN80, sup)
    for _ in range(8): d.C('100nF', V33, GND)
    for _ in range(4): d.C('100nF', '+1V1', GND)
    d.C('4.7uF', '+1V1', GND, C0603); d.C('10uF', V33, GND, C0805)
    d.L('3.3uH', 'SUP_LX', '+1V1')
    d.add('Y1', 'Device:Crystal_GND24', '12MHz', XTAL,
          {'1': 'SUP_XIN', '3': 'SUP_XOUT', 'G': GND})
    d.C('15pF', 'SUP_XIN', GND); d.C('15pF', 'SUP_XOUT', GND)
    d.R('1k', 'SUP_RUN', V33); d.C('100nF', 'SUP_RUN', GND)
    d.add('U8', 'Memory_Flash:W25Q32JVZP', 'W25Q32JVZP', USON8,
          {'~{CS}': 'SUPF_CS', 'CLK': 'SUPF_CLK', 'DI/IO_{0}': 'SUPF_D0',
           'DO/IO_{1}': 'SUPF_D1', '~{WP}/IO_{2}': 'SUPF_D2',
           '~{HOLD}/~{RESET}/IO_{3}': 'SUPF_D3', 'VCC': V33, 'GND': GND, 'EP': GND},
          LCSC['W25Q32JVZP'])
    d.C('100nF', V33, GND)
    d.add('J1', 'Connector:USB_C_Receptacle_USB2.0_16P', 'USB-C', USBC,
          {'VBUS': 'VBUS', 'GND': GND, 'SHIELD': GND, 'CC1': 'USB_CC1', 'CC2': 'USB_CC2',
           'D+': 'USB_DP', 'D-': 'USB_DM'})
    d.R('5.1k', 'USB_CC1', GND); d.R('5.1k', 'USB_CC2', GND)
    d.add('SW1', 'Switch:SW_Push', 'BOOTSEL', 'Button_Switch_SMD:SW_SPST_B3U-1000P',
          {'1': 'SUPF_CS', '2': GND})

    d.add('J51', 'Connector_Generic:Conn_01x03', 'SUP_SWD',
          'Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical',
          {'Pin_1': 'SUP_SWCLK', 'Pin_2': GND, 'Pin_3': 'SUP_SWDIO'})

    # series resistors on every supervisor<->FPGA shared line (33R)
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
    d.add('J2', 'Connector_Generic:Conn_02x05_Odd_Even', 'JTAG', HDR2x5,
          {'Pin_1': V33, 'Pin_2': GND, 'Pin_3': 'JTAG_TMS', 'Pin_4': GND,
           'Pin_5': 'JTAG_TCK', 'Pin_6': GND, 'Pin_7': 'JTAG_TDO', 'Pin_8': GND,
           'Pin_9': 'JTAG_TDI', 'Pin_10': GND})

    # ------------------------------------------------ slot L level shifters
    lsl = [f'SLOTL_P{i}_{s}' for i in range(5) for s in ('P', 'N')]
    for k in range(2):
        conn = {'VCCA': V33, 'VCCB': V5, 'GND': GND,
                'DIR': f'SLOTL_DIR{k}', '~{OE}': GND}
        for i in range(8):
            idx = k*8 + i
            conn[f'A{i+1}'] = lsl[idx] if idx < 10 else ''
            conn[f'B{i+1}'] = f'SLOTL_IO{idx}' if idx < 10 else ''
        d.add(f'U{9+k}', 'Logic_LevelTranslator:SN74AVC8T245PW', 'SN74AVC8T245PW',
              TSSOP24, {k_: v for k_, v in conn.items() if v})
        d.C('100nF', V33, GND); d.C('100nF', V5, GND)

    # ------------------------------------------------ nine slots
    jn = 3
    for s, (bank, prs) in slots.items():
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
        d.add(f'J{jn}', 'Connector_Generic:Conn_02x03_Odd_Even', f'VCCIO{dom}_SEL', HDR2x3,
              {'Pin_1': V33, 'Pin_2': net, 'Pin_3': V25, 'Pin_4': net,
               'Pin_5': V18, 'Pin_6': net})
        jn += 1
        for _ in range(2): d.C('22uF', net, GND, C0805)

    # ------------------------------------------------ power tree
    d.add('J50', 'Connector_Generic:Conn_01x02', 'VIN 12V', HDR1x2,
          {'Pin_1': V12, 'Pin_2': GND})
    d.C('22uF', V12, GND, C0805); d.C('22uF', V12, GND, C0805)
    d.add('D2', 'Device:D_Schottky', 'SS34', 'Diode_SMD:D_SMA',
          {'A': 'VBUS', 'K': V5})          # USB can power the board when VIN is absent
    d.C('10uF', 'VBUS', GND, C0805)
    # 12V -> 5V
    d.add('U11', 'Regulator_Switching:TPS54202DDC', 'TPS54202DDC', SOT236,
          {'VIN': V12, 'GND': GND, 'EN': 'EN_5V', 'FB': 'FB_5V',
           'SW': 'SW_5V', 'BOOT': 'BOOT_5V'}, LCSC['TPS54202DDC'])
    d.C('100nF', 'BOOT_5V', 'SW_5V'); d.L('4.7uH', 'SW_5V', V5)
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
        fb = f'FB{rail}'; sw = f'SW{rail}'
        d.add(ref, 'Regulator_Switching:TLV62569DRL', 'TLV62569DRL', SOT236,
              {'VIN': V5, 'GND': GND, 'EN': en, 'FB': fb, 'SW': sw},
              LCSC['TLV62569DRL'])
        d.L('1.5uH', sw, rail)
        d.R(top, rail, fb, R0603); d.R(bot, fb, GND, R0603)
        for _ in range(2): d.C('22uF', rail, GND, C0805)
        d.C('100nF', V5, GND)
    # MGTAVCC 1.0V filtered off +1V0
    d.L('1uH', V10, V10MGT); d.C('4.7uF', V10MGT, GND, C0603)
    # rail monitors into the supervisor ADC (divide the ones above 3.3V)
    d.R('100k', V12, 'MON_12V', R0603); d.R('33k', 'MON_12V', GND, R0603)
    d.R('100k', V5,  'MON_5V',  R0603); d.R('100k', 'MON_5V', GND, R0603)
    for rail, mon in ((V33,'MON_3V3'), (V25,'MON_2V5'), (V18,'MON_1V8'),
                      (V10,'MON_1V0'), (V12MGT,'MON_1V2'), ('VCCIO_1','MON_VCCIO1')):
        d.R('1k', rail, mon, R0603)
    # board-ID pull-downs
    for i in range(4): d.R('10k', f'BOARDID_{i}', GND)
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
