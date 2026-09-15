# Powering Odin

**One USB-C connector. That is the whole story.** Plug it into a computer, a
charger, or a USB-C power bank. There is no barrel jack you must find and no
battery to charge.

## The budget, so the numbers are not a guess

| | Peak |
|---|---|
| FPGA core (`VCCINT`, pre-bitstream allowance) | 1.5 W |
| `VCCAUX` + `VCCBRAM` | 0.37 W |
| `VCCO` and I/O | 1.2 W |
| PSRAM x4, active | 0.66 W |
| Supervisor + flash | 0.2 W |
| Transceiver rails, 2 lanes | 0.4 W |
| Two SFP modules | 2.0 W |
| **Base board** | **≈ 6.3 W** |
| LCD logic (Gameboy extension) | 0.5 W |
| Class-D audio amp, peak | 2.5 W |
| LCD backlight | 1.35 W |
| **With one extension** | **≈ 10.7 W** |

Add two-stage regulator losses and it is **about 13–14 W at the connector**.

That matters, because it rules something out. **Plain 5 V USB is not enough.**
A laptop port often gives 5 V at 0.9 A — 4.5 W. Even a good 5 V/3 A source is
15 W, which is the budget with nothing to spare.

## How reliable is 9 V, really?

Reliable **from a charger**, and often absent **from a computer** — which is
the awkward part, because a dev board spends its life plugged into a computer.

The USB-PD Power Rules make this precise. A source's fixed voltages are
determined by its rating:

| Source rating | Must offer |
|---|---|
| up to 15 W | 5 V |
| 15–27 W | 5 V, **9 V** |
| 27–45 W | 5 V, 9 V, 15 V |
| 45–60 W | 5 V, 9 V, 15 V, 20 V |

So **9 V is mandatory on any PD source above 15 W** — every phone charger,
laptop brick and decent power bank has it. Note what is *not* in that table:
**12 V is not a PD Power Rules voltage at all.** It is an optional extra some
sources add, which is why this board does not depend on it.

The catch is the other end. Plenty of laptop and desktop USB-C ports do no PD
negotiation whatsoever and simply offer 5 V at 0.9 A or 3 A. That is the port
you are plugged into while you write HDL.

## Therefore: 5 V is the design assumption, PD is headroom

The board is built so that **everything works at 5 V**. Power Delivery changes
how much current you can draw, not what functions. Specifically, the 12 V AUX
rail is **boosted from the 5 V rail** rather than taken from the input, so an
extension's backlight or motor works whether you are on a laptop port or a
45 W charger.

What PD actually buys you: at 9 V a 3 A source delivers 27 W against a 13 W
budget, and the current through the connector drops from ~2.6 A to ~1.4 A.
Headroom and less loss — not features.

## The negotiation, in the schematic

A `CH224K` sink chip owns the connector's CC lines and asks for 9 V. If the
source cannot supply it, the board stays on 5 V and keeps working.

**Firmware must never request more than 9 V.** `D7` is an `SMBJ13A`: a
**unidirectional** 600 W TVS on `VBUS`, cathode to `VBUS`, anode to ground.
Its reverse standoff is 13 V and its breakdown is 14.4 V minimum. A 15 V
contract sits above the standoff, where leakage climbs steeply; a 20 V
contract puts it into sustained avalanche, which a 600 W transient part will
not survive as a DC condition. (It does not *forward*-conduct — that only
happens if the part is fitted backwards, which is why the schematic uses a
polarised symbol rather than the bidirectional `SMBJ13CA` one.)

9 V is the design limit, the protection is chosen for it, and the limit
belongs in the firmware as an assertion, not a comment.

The supervisor drives the sink's three configuration pins, so **the requested
voltage is firmware, not a soldered strap** (within that 9 V ceiling). It can ask for something else if
your extension needs it, and it reads the sink's power-good pin to find out
whether the request actually succeeded.

## Inrush: why there is an eFuse between the connector and everything else

USB caps how much capacitance a device may hang on `VBUS` at the moment the
cable goes in: 10 µF, or 50 µC of inrush charge. USB-PD raises that to 100 µF
only *after* a contract exists — and at plug-in there is no contract. Behind
the OR-ing diode this board has 44 µF of `VSYS` bulk, which is five times the
allowance and would show up as a drooping source, a sparking connector, and a
board that starts on one charger and not another.

So `VBUS` reaches that bulk through **`U26`, a `TPS259470A` eFuse**, not a
bare diode. Its `dVdt` capacitor sets a controlled rise of about 0.91 V/ms,
so charging the 44 µF `VSYS` bulk draws about 40 mA. It works without
firmware — this path produces +3V3, so it cannot wait for firmware that +3V3
has to boot first. It also rejects inputs below about 3.75 V or above about
9.98 V, limits current to about 2.03 A, blocks reverse current when off, and
reports a fault on `EXT_FAULT`. The 10 µF directly on `VBUS` is the USB
attach allowance, spent on purpose.

`Q2`, the 5 V pass switch, gets the same treatment for the same reason: its
gate is slewed over about a millisecond, because closing it connects `VBUS` to
66 µF of +5 V bulk.

## What actually changes on a plain 5 V source

Only two things:

- **The 5 V rail is USB `VBUS` itself**, passed through a MOSFET switch
  (`Q2`) rather than the buck, so it sits a few tens of millivolts below
  whatever the host supplies — not the ~0.4 V a diode would have cost.
- **You have less power.** 15 W at best, 4.5 W from a weak laptop port,
  against a 13 W budget. Populate two SFP modules and a loud speaker on a
  laptop port and you will run out.

Everything still *functions*, including 12 V AUX. The supervisor measures
`VSYS` on its ADC, reports the negotiated voltage over the console, and can
refuse to enable rails the source cannot sustain. Not a mystery brownout at
2am.

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
**Feed it 9–14 V.** Nothing requires it; it exists so a power-hungry extension
does not force a board respin.

The ceiling used to say 20 V and that was wrong in two ways. Nothing on the
board benefits from more than about 12 V — every rail is stepped *down* from
`VSYS`, so a higher input only buys extra heat and worse ripple — and 20 V
made the supervisor's `VSYS` monitor unsafe. That divider has since been sized
so that even 20 V on `J50` puts only 2.76 V on the ADC pin rather than
destroying it, but sizing the protection for a case is not the same as
supporting it. 14 V is the supported range; the divider is the guard rail.

`J50` has no overvoltage clamp of its own. `D4` blocks reverse polarity, and
the `VSYS` capacitors are 25 V parts, but a bench supply set to 24 V will get
past all of that. See `findings.md` item 22.

## In the schematic

| Ref | Part | Role |
|---|---|---|
| `J1` | USB-C receptacle | the only required input |
| `U18` | `CH224K` | PD sink; supervisor drives CFG1..3, reads PG |
| `D6`, `D7` | ESD array, TVS | protects D+/D-/CC and clamps `VBUS` |
| `Q2`, `Q3` | P-MOS + gate driver | passes `VBUS` to the 5 V rail, **default open**; firmware closes it only when the input really is 5 V |
| `U26` | `TPS259470A` | controlled-inrush, current-limited and overvoltage-protected path from `VBUS` to the bulk |
| `D3`, `D4` | Schottky | OR-ing USB-C and the optional input into `VSYS` |
| `U12` | `AP63300` | `VSYS` down to **3.3 V, always on** — starts from 3.8 V input |
| `U11` | `TPS54202` | `VSYS` (9 V) down to 5 V |
| `U13`–`U16` | `TLV62569` x4 | 5 V down to 2.5 / 1.8 / 1.0 / 1.2 V |
| `U19` | `TPS61085` | 5 V **up** to 12 V for AUX — works on any source |
| `U21`–`U24` | `TPS22950C` | reverse-blocking, current-limited switches for 5 V, 3.3 V and both VCCIO extension buses |
| `U25` | `TPS259470L` | 500 mA latch-off, reverse-blocking eFuse for the 12 V extension bus |

## Extension power cannot feed the base board backward

The internal rails stop at five active protection switches. Their outputs are
`+5V_EXT`, `+3V3_EXT`, `VCCIO_1_EXT`, `VCCIO_2_EXT` and `+12V_EXT`; the
per-slot PTCs come after them. FPGA, supervisor, memories, clocks and
regulators remain upstream.

`GPIO8` drives their common `EXT_EN` and a 100 kΩ resistor holds them off
during reset. Their open-drain fault outputs share `EXT_FAULT` on `GPIO47`.
The 12 V channel latches off. The low-voltage channels limit current and
thermally retry; firmware must drop `EXT_EN` after `EXT_FAULT` and require an
explicit retry.

The practical fault behavior is:

| Mistake | Result |
|---|---|
| hard short | active switch limits first; its shared bus may shut down; branch PTC remains backup |
| 5 V applied to `+3V3_EXT` | reverse current into +3V3 is blocked; the off-state discharge draws about 31 mA |
| 5 V applied to a 1.8 V VCCIO bus | reverse current into VCCIO is blocked; same discharge current applies |
| 12 V applied to AUX while Odin is off | `U25` blocks current into the boost output |
| extension powered while Odin is disconnected | `_EXT` buses do not energize the internal rails |

The low-voltage switch is rated to 6 V absolute maximum. This handles the
specified accidental 5 V application; it is not protection against someone
putting 12 V on a 3.3 V or VCCIO pin. Signal pins have separate limits.

There is no downstream ADC divider in this revision. The supervisor's six
dedicated monitor inputs are already used by the internal rails; the two
remaining ADC-capable GPIOs control +12 V and receive `EXT_FAULT`. The active
switches still enforce protection without firmware, and the combined digital
fault tells firmware to turn `EXT_EN` off.

`U12` is deliberately an `AP63300` rather than a `TLV62569`: it must run from
either a weak 5 V USB source or 9 V, because it comes up before negotiation.
Its 3.8 V minimum leaves margin at the computed 4.27 V worst-case `VSYS`.
The feedback, inductor and capacitors copy the manufacturer's 3.3 V reference
circuit, and `tools/budget.py` checks the resulting load and inductor current.
See `ref/supervisor-flash.md`.

## Every number here is computed

`ref/power-budget.md` is generated by `tools/budget.py` from a load table with
a stated basis per line and datasheet limits per regulator. If a figure in
this page and a figure there disagree, that page is right.
