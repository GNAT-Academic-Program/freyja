# The two fast ports

The `XC7A100T-FGG676` has two four-lane GTP quads. This revision wires two
lanes in quad 216, up to ~6.6 Gb/s each. The other lanes remain unconnected. Ordinary pins
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
Wire that to the supervisor and the whole thing becomes self-describing —
exactly like the board-ID pins on the extension slots:

- **It tells you what is plugged in.** Over the USB console: `SFP0: FS
  1000BASE-T copper, s/n …` / `SFP1: empty`. No guessing, no label squinting.
- **It knows when something is inserted or removed.** Each cage has presence,
  transmit-fault and rate-select pins. All go to the supervisor.
- **The supervisor controls power to both ports together.** A faulty module can
  be shut down. Same rule as the extension rails —
  a bad thing gets cut by software, not by smoke.
- **A status LED per cage**, driven by the fabric so your own link logic can
  own it.

Cost: about 6 supervisor pins for two cages, and the supervisor has spare.

## The honest limits

- **6.6 Gb/s is the ceiling.** 1 Gb and 2.5 Gb modules work. 10 Gb does not.
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
| `J60`, `J61` | SFP electrical connector | lanes 0 and 1 |
| `X2` | 125 MHz differential oscillator | the reference clock the lanes need |
| `Q1` | P-channel high-side switch | gate pulled high, so cages are **off until the supervisor turns them on** |
| `U17` | SFP power controller | gives the two ports a safe default-off power control |
| `R30` | `MGTRREF` precision resistor | value to confirm, see `findings.md` |

Coupling capacitors sit in series on all eight high-speed lines. Both status
buses and the two-wire identification bus run to the supervisor, with pull-ups.
The unused lanes and second reference-clock input are explicit no-connects.

The oscillator is selected and pin-checked. The `MGTRREF` resistor value still
needs confirmation against UG482.
