# Odin

An FPGA dev board built on one idea: **remove the accidental complexity, so
what's left is the actual project.**

## Why dumb projects look complicated

Watch a student build a handheld game on a normal FPGA board. Where does the
effort go?

- Writing a memory controller, because the framebuffer doesn't fit in BRAM.
- Fighting the programming workflow, because loading a bitstream is a ritual
  involving a vendor GUI.
- Designing a power supply, because the LCD backlight needs 12V and the board
  offers 3.3V and 5V.
- Level-shifting, because half the parts are 5V.
- Reading a 400-page manual to find which pins share a bank.
- Guessing, when it doesn't work, because the board cannot tell them anything.

Roughly 80% of the effort, and **none of it is the game.** The project isn't
complicated. The scaffolding is. And because the scaffolding is where the time
goes, the finished thing looks far more impressive than the idea deserves —
which is its own kind of failure, because the student learned plumbing instead
of architecture.

## What's actually missing, and what Odin does

| Missing on normal boards | What it causes | Odin |
|---|---|---|
| **A middle rung of memory.** BRAM (KB) → cliff → DDR3 (nightmare) | Every project that outgrows BRAM becomes a memory-controller project | 4× PSRAM, 8 MB, four independent ports, predictable latency |
| **Scriptable programming.** JTAG blaster + vendor GUI | Can't run 40 variants overnight, so nobody experiments | RP-class supervisor owns config; one USB-C, no helper bitstream |
| **Self-observation.** No rail telemetry, no software power control | Superstition-driven debugging | Supervisor drives every enable, reads back every rail |
| **A real expansion standard.** Pmod is 8 pins/3.3V; FMC is a $200 connector and a 400-page spec | Every extension is bespoke, nothing composes | Keyed 16-pin modules, 16/32/64, documented in one page |
| **Rails on the connector.** 3.3V and 5V, take it or leave it | Half of every extension BOM is regulators | Four rails per module: VCCIO, +5V, fixed +3V3, selectable AUX |
| **A level-shifting story.** All-shifted (slow) or none (no 5V parts) | You find out which by burning a part | Two buffered slots, six direct. One table says which and why |
| **Docs a human reads.** 400-page reference manual | Nobody reads it; everyone guesses | One page per subsystem. Over two pages is a bug |

Each row of that table is a decision in this repo, and each one exists to
delete a category of work that was never the point.

## The legibility principle

50 MB/s per link, 2 MB per chip. That's modest. It is also **knowable** — you
can work out on paper, before writing a line of HDL, whether your design fits.

DDR3 offers "up to 12.8 GB/s," qualified by access pattern, bank conflicts,
refresh, and calibration. You cannot reason about it in advance. You build it,
measure it, and find out.

**A legible constraint teaches. An opaque abundance does not.** A student who
computes "640×480 at 60 Hz is 37 MB/s, one PSRAM link is 50, it fits" has
learned something transferable. A student who gets 12.8 GB/s from an IP core
has learned to instantiate an IP core.

This is why the numbers on this board are small and published rather than
large and asterisked.

## The honest ceiling

Odin is not fast. Some things do not fit, and pretending otherwise would
undermine the point:

- **1080p60** RGB565 needs ~249 MB/s. Four chips ganged give ~200. Doesn't fit.
- **720p60** is ~110 MB/s. Fits ganged, with headroom.
- **VGA 60 Hz** is 37 MB/s. Fits on a single link, leaving three ports free.
- Anything wanting sustained gigabytes per second wants DDR3 and a different
  board.

If you need the ceiling raised, this is the wrong board. If you need the floor
raised so you can get to the interesting part, this is the right one.

## The test for any future decision

> Does this remove work that was never the point, or does it add work that
> looks like the point?

Series resistors on shared config lines: removes work (a firmware bug can't
brick the board). Four independent PSRAM buses instead of one shared: removes
work (no arbiter to design). A 400-page pinout PDF: adds work.

Apply it to anything proposed for this board.

## Reference

- [`ref/extension-ux.md`](ref/extension-ux.md) — the extension connector spec. One page. Read this first.
- [`ref/psram.md`](ref/psram.md) — memory: four independent ports, and why four.
- [`ref/gameboy-extension.md`](ref/gameboy-extension.md) — worked example: LCD, speaker, gamepad.
- [`ref/salvage-from-odin0.md`](ref/salvage-from-odin0.md) — what survives from last year's board.
- [`ref/ide-agent-prompt.md`](ref/ide-agent-prompt.md) — the review brief for the implementation agent.
- [`findings.md`](findings.md) — open issues against the current schematic.
