# Network: RTL8211FD-CG and the ETH jack

Rev A puts one gigabit PHY on the board, RGMII to FPGA bank 16, and one
1000Base-T jack with integrated magnetics. Every value below carries its
source; the three marked **[verify]** are not in the Realtek datasheet (rev
1.7 has no reference schematic) and come from public RTL8211F boards.

## Parts

| Ref | Part | LCSC | Why |
|---|---|---|---|
| U30 | RTL8211FD-CG, QFN-40 | C2687133 | decision D2: the LDO model needs no switching inductor |
| J70 | HanRun HR911130A | C54408 | IEEE 802.3ab 1000Base-T magnetics, 1500 Vrms, two LEDs, tab down |
| X3 | YXC X322525MOB4SI, 25 MHz, 12 pF | C9006 (Basic) | Table 56: 25 MHz, ±50 ppm all in, ESR ≤ 50 Ω |

## Supplies and sequencing (Table 9, Table 53, Table 55)

| Pin(s) | Supply | Decoupling |
|---|---|---|
| 11, 40 AVDD33; 29 DVDD33 | `+3V3` | 100 nF each, 10 µF bulk |
| 28 DVDD_RG | `+2V5` | 100 nF, 1 µF |
| 30 LDO_OUT → 3, 8, 38 AVDD10; 21 DVDD10 | `PHY_1V0` (internal LDO) | 100 nF each, 4.7 µF bulk **[verify]** values, NanoPi M5 practice |
| 39 RSET | 2.49 kΩ 1 % to GND | **[verify]** value from public boards, not the datasheet |

- 3.3 V must rise in more than 0.5 ms (Table 53 note 1); U12's soft start
  does that. Never put a fast load switch in front of the PHY.
- `+2V5` is enabled by the supervisor after `+3V3`. Allowed by Table 53 note 5
  **Case II** only because `PHYRSTB` is held low until `+2V5` is up: the 1 kΩ
  pull-down on `PHY_RESET_N` does that, against a floating FPGA pin (PUDC_B
  is high, so the FPGA adds no pull-up during configuration).
- Reset: ≥ 10 ms low (Table 5), then wait **≥ 72 ms** before the first MDIO
  access (§7.17, revised in rev 1.7). Gateware owns both timings.

## Pins to the FPGA

| PHY pin | Net | Bank | Level | Note |
|---|---|---|---|---|
| TXC, TXD[3:0], TXCTL | `PHY_TXC`, `PHY_TXD0..3`, `PHY_TX_CTL` | 16 | 2.5 V | fabric → PHY |
| RXC, RXD[3:0], RXCTL | `PHY_RXC`, `PHY_RXD0..3`, `PHY_RX_CTL` | 16 | 2.5 V | PHY → fabric; `PHY_RXC` on an MRCC ball |
| MDC, MDIO | `PHY_MDC`, `PHY_MDIO` | 16 | DVDD_RG = 2.5 V (Table 58) | 1.5 kΩ pull-up to `+2V5` (§7.11.2) |
| PHYRSTB | `PHY_RESET_N` | 35 | 3.3 V (Table 58 note) | 1 kΩ pull-down; LVCMOS33 output |
| INTB | `PHY_INT_N` | 35 | 3.3 V, open drain (Table 4) | 4.7 kΩ pull-up to `+3V3` |
| CLKOUT | — | — | — | floating (Table 2); outputs 125 MHz by default, clear PHYCR2 from gateware |

RGMII delays: TXDLY = 1 and RXDLY = 1 strap the PHY's 2 ns delays on (Table 6),
so the fabric drives TXC and samples RXC without its own delay. Ball numbers
are in `ref/ballmap.md`.

## Straps (Table 10, Table 11, §7.8, §7.9)

Every CONFIG pin needs a resistor, 4.7 kΩ; none may be tied directly.

| Pin | Function | Level | Pulled to | Result |
|---|---|---|---|---|
| 22 RXD3 | PHYAD0 | 1 | DVDD_RG | PHY address 1 |
| 27 RXC | PHYAD1 | 0 | GND | |
| 26 RXCTL | PHYAD2 | 0 | GND | |
| 23 RXD2 | PLLOFF | 0 | GND | PLL keeps running in ALDPS |
| 24 RXD1 | TXDLY | 1 | DVDD_RG | 2 ns TXC delay inside the PHY |
| 25 RXD0 | RXDLY | 1 | DVDD_RG | 2 ns RXC delay inside the PHY |
| 32 LED0 | CFG_EXT | 1 | `+3V3` | external I/O supply mode |
| 33 LED1 | CFG_LDO0 | 1 | `+3V3` | with CFG_LDO1 = 0: 2.5 V I/O |
| 34 LED2 | CFG_LDO1 | 0 | GND | |

The three CFG_EXT/CFG_LDO straps go to 3.3 V and GND, not to DVDD_RG
(Table 11). The six RXD/RXC/RXCTL straps go to DVDD_RG.

## LEDs (§7.9 Figure 5, Table 7)

The LED pins double as straps, so polarity follows the strap: a pin strapped
high drives active-low, strapped low active-high.

| PHY pin | Strap | Drive | Jack LED | Circuit |
|---|---|---|---|---|
| LED0 | high | active-low | green, pins 11 (+) / 12 (−) | 11 ← 510 Ω ← `+3V3`; 12 → LED0 |
| LED2 | low | active-high | yellow, pins 14 (+) / 13 (−) | LED2 → 14; 13 → 510 Ω → GND |
| LED1 | high | — | none | strap only |

Default meanings (Table 7): LED0 link at 10 Mb/s + activity, LED2 link at
1000 Mb/s + activity. Gateware sets Table 17 Mode A to make green "link/act at
any speed" and yellow "1000 Mb/s".

## MDI and the jack (§7.7, HanRun drawing rev A)

| PHY | Jack pin | Jack signal |
|---|---|---|
| MDIP0/MDIN0 (1, 2) | P2 / P3 | MDI0± |
| MDIP1/MDIN1 (4, 5) | P4 / P7 | MDI1± |
| MDIP2/MDIN2 (6, 7) | P5 / P6 | MDI2± |
| MDIP3/MDIN3 (9, 10) | P8 / P9 | MDI3± |
| — | P1 | common chip-side centre tap: 100 nF 50 V to GND **[verify]** |
| — | P10 | jack's internal Bob-Smith network (4 × 75 Ω + 1000 pF 2 kV): GND |
| — | SHIELD0/1 | GND |

The RTL8211F terminates the MDI internally (§7.7) and drives it in voltage
mode, so the centre taps carry no supply; public RTL8211F boards return them
to ground through a capacitor.

## Routing notes for phase B

- MDI pairs 100 Ω differential, short, over one unbroken ground, no vias if
  the layer stack allows; keep the 4 × 75 Ω network's ground (P10) and the
  shield tabs on the same ground as the PHY.
- RGMII: length-match TXD[3:0]/TXCTL to TXC and RXD[3:0]/RXCTL to RXC within
  a few millimetres; the PHY's internal 2 ns delays do the rest.
- The LDO output `PHY_1V0` is a local rail: keep its capacitors within a few
  millimetres of pins 30, 3, 8, 21, 38 and give the exposed pad a via field.
- Crystal: shortest possible loop between X3, its two 18 pF capacitors and
  pins 36/37, ground fill underneath; 0 Ω in series with XTAL_OUT becomes a
  real value only if the measured drive exceeds 0.5 mW (Table 56).
