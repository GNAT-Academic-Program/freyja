# The four fast lanes

The `XC7A50T` has four built-in serial lanes, ~6.6 Gb/s each. Ordinary pins
are roughly a hundred times slower. These are the only thing on Odin an
extension board can never add later, because a signal that fast dies in a
0.1" pin header — it needs a real connector and controlled-impedance copper on
the base board.

## Don't spend them on video

Tempting, but wrong. The Artix-7 drives HDMI at 1080p60 from **ordinary I/O**
using TMDS — no fast lane required. Video belongs on an extension board or on
spare base-board I/O. Spend the fast lanes on what ordinary pins genuinely
cannot do: multi-gigabit serial.

## The recommendation: SFP cages

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

**Four cage positions, two populated by default.** Lanes 0 and 1 get real
cages; lanes 2 and 3 get identical footprints left empty. Populating them
later costs a soldering iron, not a respin.

## What makes it UX-smart

Every SFP module carries an identification chip you read over a two-wire bus.
Wire that to the supervisor and the whole thing becomes self-describing —
exactly like the board-ID pins on the extension slots:

- **It tells you what is plugged in.** Over the USB console: `SFP0: FS
  1000BASE-T copper, s/n …` / `SFP1: empty`. No guessing, no label squinting.
- **It knows when something is inserted or removed.** Each cage has presence,
  transmit-fault and rate-select pins. All go to the supervisor.
- **The supervisor powers each cage independently.** A module can draw a watt;
  a faulty or absent one gets no power. Same rule as the extension rails —
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
- **Board area.** A cage is roughly 14 mm wide and 47 mm deep. Two side by
  side take 28 mm of one edge. Four take 56 mm, which is most of a 100 mm
  edge — a real reason to populate two and leave two as footprints.

## If you would rather not

The alternative is to accept the lanes are dead and save the connectors, the
area and the routing care. That is a legitimate call for a first revision.
What is *not* legitimate is leaving it undecided — the pads have to be routed
before layout, or the option is gone for the life of the board.
