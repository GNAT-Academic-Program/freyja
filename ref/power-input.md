# Powering Odin

**One USB-C connector. That is the whole story.** Plug it into a computer, a
charger, or a USB-C power bank. There is no barrel jack you must find and no
battery to charge.

## The budget, so the numbers are not a guess

| | Peak |
|---|---|
| FPGA core (`VCCINT`, a busy design) | 1.0 W |
| `VCCAUX` + `VCCBRAM` | 0.25 W |
| `VCCO` and I/O | 1.0 W |
| PSRAM x4, active | 0.66 W |
| Supervisor + flash | 0.2 W |
| Transceiver rails, 2 lanes | 0.4 W |
| Two SFP modules | 2.0 W |
| **Base board** | **≈ 5.5 W** |
| LCD logic (Gameboy extension) | 0.5 W |
| Class-D audio amp, peak | 2.5 W |
| LCD backlight | 1.35 W |
| **With one extension** | **≈ 10 W** |

Add two-stage regulator losses and it is **12–13 W at the connector**.

That matters, because it rules something out. **Plain 5 V USB is not enough.**
A laptop port often gives 5 V at 0.9 A — 4.5 W. Even a good 5 V/3 A source is
15 W, which is the budget with nothing to spare.

## So: USB Power Delivery, negotiating 9 V

A `CH224K` sink chip owns the connector's CC lines and asks the source for a
higher voltage. At 9 V a normal 3 A source gives **27 W** — roughly twice the
budget — and the current at the connector drops to about 1.4 A.

**Why 9 V and not 12 V.** 12 V is *optional* in the USB-PD specification and
plenty of chargers skip it. Every PD source supports 5 V and 9 V. 9 V also
happens to be what the AUX rail wants for an LCD backlight, so nothing has to
be boosted back up.

The supervisor drives the sink's three configuration pins, so **the requested
voltage is firmware, not a soldered strap.** It can ask for something else if
your extension needs it, and it reads the sink's power-good pin to find out
whether the request actually succeeded.

## What happens on a dumb 5 V source

The board still runs. `VSYS` sits at 5 V instead of 9 V, and:

- the 5 V rail comes straight from USB through a Schottky instead of from the
  buck, so it lands near 4.6 V;
- the AUX rail cannot offer 9 V, only 5 V or 3.3 V;
- the supervisor **measures `VSYS` on its ADC and says so** over the USB
  console, and refuses to enable AUX for an extension that asked for 9 V.

Degraded, documented, and it tells you. Not a mystery brownout at 2am.

## Autonomy: use a USB-C power bank

**No lithium cell on the board, deliberately.** A PD power bank is
$25–40, does 9 V under load, comes in whatever capacity you want, and is
swappable. Putting a cell on the board means a charger, protection, a fuel
gauge, thermal design, a cell connector, and shipping rules for a product
containing a battery — a product-engineering project, not a dev-board feature.

At ~12 W, a 20 000 mAh (74 Wh) PD bank runs the board and a Gameboy extension
for roughly five hours. A smaller 10 000 mAh bank gives about two and a half.

One caution worth knowing: **not every power bank holds 9 V under a 1.5 A
load**, and cheap ones drop to 5 V without warning. The supervisor will tell
you when that happens, which is the point.

## The optional extra input

`J50` is a 2-pin header, Schottky-OR'd with USB-C — the higher voltage wins.
Feed it 9–20 V if you are driving something the connector cannot. Nothing
requires it. It exists so a power-hungry extension does not force a board
respin.

## In the schematic

| Ref | Part | Role |
|---|---|---|
| `J1` | USB-C receptacle | the only required input |
| `U18` | `CH224K` | PD sink; supervisor drives CFG1..3, reads PG |
| `D2` | Schottky | USB 5 V straight to the 5 V rail (degraded mode) |
| `D3`, `D4` | Schottky | OR-ing USB-C and the optional input into `VSYS` |
| `U11` | `TPS54202` | `VSYS` (9 V) down to 5 V |
| `U12`–`U16` | `TLV62569` x5 | 5 V down to 3.3 / 2.5 / 1.8 / 1.0 / 1.2 V |
