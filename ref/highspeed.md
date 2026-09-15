# The two fast ports

The `XC7A100T-FGG676` has two four-lane GTP quads. This revision wires two
lanes in quad 216. The FPGA supports up to ~6.6 Gb/s per lane, but the
selected Amphenol cage is listed at 2.5 Gb/s; higher-rate operation is
unqualified. Unused RX lanes are grounded and unused TX lanes float. Ordinary pins
are roughly a hundred times slower. These are the only thing on Odin an
extension board can never add later, because a signal that fast dies in a
0.1" pin header — it needs a real connector and controlled-impedance copper on
the base board.

## Don't spend them on video

Tempting, but wrong. The Artix-7 drives HDMI at 1080p60 from **ordinary I/O**
using TMDS — no fast lane required. Video belongs on an extension board or on
spare base-board I/O. Spend the fast lanes on what ordinary pins genuinely
cannot do: multi-gigabit serial.

## Built: SFP cages

An SFP cage is a socket you plug a **module** into — which is the same idea as
Odin's extension slots, one level up. One socket, many personalities:

| Module | What you get | Rough cost |
|---|---|---|
| Copper 1000BASE-T | An RJ45 ethernet port | ~$15 |
| Fibre (many kinds) | 550 m to 80 km, pick the module | $8–40 |
| Direct-attach copper | A fixed cable, board to board or to a switch | ~$10 |
| Loopback plug | Test your link with no other hardware | ~$5 |

You wanted two ethernet ports. This gives you two ethernet ports **and** fibre
**and** board-to-board, and the base board never has to choose which.

**There are two ports, full stop.** Lanes 0 and 1 reach them. Lanes 2 and 3 do
not create empty connectors, fake choices or assembly noise.

## What makes it UX-smart

Every SFP module carries an identification chip you read over a two-wire bus.
U27 selects one module’s two-wire bus at a time, so firmware can identify
both modules despite their shared EEPROM address, 0x50. This enables the
planned self-describing interface —
exactly like the board-ID pins on the extension slots:

- **Planned identity reporting.** Supervisor firmware can report: `SFP0: FS
  1000BASE-T copper, s/n …` / `SFP1: empty`. No guessing, no label squinting.
- **It knows when something is inserted or removed.** Each cage has presence,
  transmit-fault and rate-select pins. All go to the supervisor.
- **The supervisor controls power to both ports together.** A module fault
  requiring power removal shuts down both links. U27 isolates management
  traffic; it does not provide independent power shutdown.
- **Three board status LEDs** on U17: supervisor heartbeat and two user
  indicators, with [software control](status-leds.md). They are not dedicated
  per-cage FPGA LEDs.

Management uses the shared upstream I²C bus plus per-port control/status
pins. See [the selection and recovery contract](sfp-i2c.md).

## The honest limits

- **The selected cage is listed at 2.5 Gb/s.** The FPGA lane ceiling is
  ~6.6 Gb/s, but it does not qualify the complete port at that speed. Match
  the module line rate and FPGA design; higher-rate operation needs separate
  qualification. See [cage qualification](sfp-cage.md).
- **The socket is not the hard part.** You still need a gigabit ethernet core
  in the fabric. Open ones exist, and Xilinx ships one, but standing up a
  working link is a project measured in weeks, not an afternoon. The board's
  job is to make sure that project is *possible* — which it is not at all if
  these lanes go nowhere.
- **Board area.** A cage is roughly 14 mm wide and 47 mm deep. The two ports
  take about 28 mm of one edge.

## What is actually in the schematic

| Ref | Part | Note |
|---|---|---|
| `J60`, `J61` | TE 1888247-1 electrical connector | lanes 0 and 1 |
| `SH1`, `SH2` | Amphenol U77A11133001 solder-tail cage | C5355132, JLC wave solder |
| `X2` | 125 MHz differential oscillator | the reference clock the lanes need |
| `Q1` | P-channel high-side switch | gate pulled high, so cages are **off until the supervisor turns them on** |
| `U17` | SFP power controller | shared default-off power control, address 0x24 |
| `U27` | PCA9543APW,118 I²C switch | address 0x70; separate EEPROM channels |
| `R35` | `MGTRREF` precision resistor | 100R 1%, 0603, to `+1V2_MGT` (MGTAVTT); findings item 6 fixed |

Coupling capacitors sit in series on all eight high-speed lines. Status lines run to the supervisor. Each two-wire identification bus has
its own pull-ups and reaches the supervisor through a separate U27 channel.
Both G10 (quad 213) and G11 (quad 216) remain powered. `R89` provides quad
213 with its own 100R 1% 0603 resistor from `MGTRREF_213` to `+1V2_MGT`.
All eight RX pins in quad 213 and the four RX pins of unused lanes 2/3 in
quad 216 connect to GND. Unused TX and reference-clock pins float, per
[UG482 Tables 5-5 and 5-6](https://0x04.net/~mwk/xidocs/ug/ug482_7Series_GTP_Transceivers.pdf#page=223).

The oscillator is selected and pin-checked. `MGTRREF` uses 100 ohm, 1% to
MGTAVTT per [UG482 v1.9, Figure 5-1](https://0x04.net/~mwk/xidocs/ug/ug482_7Series_GTP_Transceivers.pdf#page=218).
