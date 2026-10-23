# LINK P and LINK Q: raw LVDS link ports

Two RJ45 jacks on the top edge carry eight LVDS_25 pairs straight from FPGA
bank 16 (VCCO = 2.5 V) over ordinary twisted-pair cable. There is no PHY, no
protocol and no isolation: these are FPGA pins on a cable. The jacks are
plain shielded 8P8C (Kinghelm KH-RJ45-58-8P8C, C2683360), **not** Ethernet
jacks, and nothing on this port talks Ethernet.

## Pinout

An 8P8C carries four twisted pairs on contacts 1-2, 3-6, 4-5 and 7-8 (T568
pairing). The lower contact of each pair is the P side. The two jacks are
mirror images so that **one straight cable from a P jack to a Q jack lands
clock on clock and data on data**, in both directions.

| Pair (contacts) | LINK P | LINK Q |
|---|---|---|
| 1-2 | `LINK_P_TXC` out | `LINK_Q_RXC` in |
| 3-6 | `LINK_P_TXD` out | `LINK_Q_RXD` in |
| 4-5 | `LINK_P_RXC` in | `LINK_Q_TXC` out |
| 7-8 | `LINK_P_RXD` in | `LINK_Q_TXD` out |

Each direction is one source-synchronous lane: a clock pair and a data pair.
Both receive clocks sit on clock-capable FPGA pairs (`LINK_P_RXC` on an MRCC
pair, `LINK_Q_RXC` on an SRCC pair; both reach BUFG/BUFR) so the receiver can
run from the far end's clock. Ball numbers: `ref/ballmap.md`.

Connect P to Q. P to P or Q to Q puts two LVDS drivers on one pair; the
current-mode drivers tolerate it, but nothing works.

## Electrical

- I/O standard LVDS_25, bank 16 at 2.5 V, DC coupled. Receiver termination is
  the FPGA's internal `DIFF_TERM`; there are no resistors on the board.
- ESD: one TPD4E1U06 (0.8 pF per line, 5.5 V working) per two pairs, at the
  jack (D20-D23). The pairs sit between 0 and 2.5 V, so an array that clamps
  to ground is enough.
- Jack shells to GND.
- **STP (shielded) cable only**, so the shield carries the common-mode return
  and ESD. The silkscreen says so.

## Operating rule: power both boards before connecting the cable

The pairs are DC coupled into HR bank inputs. DS181 Table 1 limits an I/O
input to **−0.4 V to V_CCO + 0.55 V**; with the receiving board unpowered,
V_CCO is 0 V and a driven pair pushes current through the receiver's input
clamps. Rev A has no hardware for this case. Power both boards, then connect
the cable; disconnect before powering either side down. A future revision can
add AC coupling or a bus switch if the rule proves unworkable.

## What the fabric must do

- Instantiate `OBUFDS`/`IBUFDS` with `IOSTANDARD = LVDS_25`, `DIFF_TERM =
  TRUE` on the inputs.
- Treat `LINK_x_RXC` as a clock input (`IBUFDS` → `BUFG`/`BUFR`), and keep the
  bank's own clocking resources for the RGMII `PHY_RXC` (MRCC) first.
- Data rate is whatever the cable and the I/O timing allow; start at a few
  hundred Mb/s and characterise.
