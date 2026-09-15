# Odin user manual

Odin is an FPGA board for building the thing you meant to build.

One USB-C cable powers it and programs it. Four PSRAM chips give the FPGA
8 MB of working memory. Ten extension ports carry signals and useful power.
Two SFP sockets carry the links that ordinary FPGA pins cannot.

This manual is for using the board. If you are designing an extension, read
`ref/extension-ux.md` after this.

## The board in one picture

```text
                         +-----------------------+
 USB-C  ---------------->| BOARD CONTROLLER      |
 power + programming     | power, recovery,      |
                         | FPGA programming       |
                         +-----------+-----------+
                                     |
                    +----------------v----------------+
                    | XC7A100T FPGA                   |
                    |                                |
       8 MB PSRAM <---> four separate memory links   |
                    |                                |
      slots A-D  <----> 48 direct pins, one voltage  |
      slots E-H  <----> 48 direct pins, one voltage  |
      5V BUS 0/1 <----> two complete 8-bit buses     |
                    |                                |
      SFP 0 and 1 <----> fast serial lanes           |
                    +--------------------------------+
```

## Start here

1. Leave all extensions unplugged.
2. Set both **A–D PIN VOLTAGE** and **E–H PIN VOLTAGE** to **3.3 V**.
3. Set each **SLOT _ POWER** selector to **3.3 V**, or leave its jumper off.
4. Plug USB-C into Odin.
5. Wait for the board controller to start.
6. Plug in one simple extension and test it before adding the next.

Use a USB-PD charger when the board carries displays, speakers, motors or SFP
modules. A computer port is fine for programming and light work, but it may
not have enough power for everything at once.

Odin never asks USB-C for more than 9 V.

### Optional power input

`OPTIONAL POWER IN` is not required for normal use. It is a second way to
power Odin from a regulated bench supply when USB-C cannot provide enough
power. Connect **9–14 V** to the pin marked `+` and supply ground to `GND`.
USB-C may remain connected; Odin uses the higher source. Never exceed 14 V.

## The extension idea, from zero

Odin has eight shield sections arranged on opposite sides of the 100 x 100 mm
board. Each section has a 16-position signal block and a separate 8-pin power
row. Two additional ports are complete 5 V-compatible eight-bit buses.

```text
one direct slot

       8 columns
     +-----------------+
signal| o o o o o o o o |
signal| o o o o o o o o |
power | o o o o o o o o |
     +-----------------+
       24 pins total
```

Twelve pins are signals. Four grounds complete the signal block. Power gets
its own unmistakable row with four supplies and four grounds.

### Where are the I/Os?

Here. `IO` means a signal you can use as an input or an output.

```text
              1     2     3     4     5     6     7     8
signal row 1  IO0   IO2   IO4   IO6   IO8   IO10  GND   GND
signal row 2  IO1   IO3   IO5   IO7   IO9   IO11  GND   GND
power row     GND   PIN V GND   3V3   GND   5V    GND   SLOT PWR
```

Use `IO0..IO11` as ordinary independent signals. Some adjacent pins can also
carry a differential signal when an extension needs that. The ball map lists
those pairings; normal users do not need to learn them.

### What do 16, 32 and 64 mean?

They mean the width used on **each side** of the base board. An extension is a
bridge, not a board hanging from one edge.

```text
                 one edge of Odin             opposite edge

16 shield             [ A ]========================[ E ]
                    16 signal positions          16 signal positions
                       + power row                  + power row

32 shield         [ A ][ B ]==================[ E ][ F ]
                       32 pins     extension         32 pins

64 shield     [ A ][ B ][ C ][ D ]========[ E ][ F ][ G ][ H ]
                       64 pins     extension         64 pins
```

A 16 gets 12 I/O on each side: 24 total. A 32 gets 48 total. A 64 spans both
complete FPGA banks and gets 96 direct I/O.

The schematic names four 16-pin sections on each edge. Those are electrical
zones, not a demand for four separate plastic connectors. Odin uses the
physical arrangement: **two continuous 2x16 stack-through signal headers and
two parallel 1x16 stack-through power headers on each edge**. A 16 shield uses
half of one pair, a 32 uses one whole pair, and a 64 uses both. The guide pins
and outlines must make those partial positions unambiguous.

The bridge gives the extension support at both ends, almost the full board
area above Odin, and matching connectors on top so another shield can stack.
The extension PCB and its fitted headers determine its size; there is no size
switch.

### Where are the slots on Odin?

The required arrangement is:

```text
                    100 mm
       +----------------------------------+
       | [ A ][ B ][ C ][ D ]            |  bank 15
       |                                  |
       |             ODIN                 |  shield bridges
       |                                  |  across this space
       | [ E ][ F ][ G ][ H ]            |  bank 34
       +----------------------------------+

       [ L ]  separate 5 V-safe legacy connector
```

Matching pairs are A/E, B/F, C/G and D/H. Placement must put each pair directly
opposite its partner. All eight connectors need the same pitch, orientation
and distance from the board edges.

**Their exact coordinates do not exist yet because placement has not been
done.** Until those coordinates and a real extension outline are drawn and
measured together, the bridge and stacking fit remain an intention, not a
proven feature.

Slots A-D always share one signal voltage. Slots E-H share another. Changing
a PIN VOLTAGE jumper changes the voltage of the whole group, not one slot.

| Shield | Sections underneath | Physical pins per side | Usable I/O |
|---|---:|---:|---:|
| 16 | A+E, B+F, C+G or D+H | 24 | 24 |
| 32 | Two matching pairs | 48 | 48 |
| 64 | A-D and E-H | 96 | 96 |

A shield reaches both FPGA banks. The A-D side shares one PIN VOLTAGE setting;
the E-H side shares the other. A 64 owns both complete groups. A smaller shield
must share each side's voltage with anything using the unused connector pairs.

### Stacking

Every shield needs female sockets underneath and matching male pins on top.
The signals pass vertically through the board so another shield can plug in.

```text
          second shield
       ===================
          stacking pins
       o o o o o o o o o o
          first shield
       ===================
          female sockets
       | | | | | | | | | |
             Odin
       ===================
```

Stacking does not create more FPGA pins or more power. Stacked shields share
the same wires, voltage groups and current budget. They must not drive the
same signal at the same time.

The guide pins, stacking headers, component height and board-to-board spacing
must be designed as one mechanical system. A guide that works for one board
but blocks the next board is not a working guide.

## One direct slot

```text
             column  1     2     3     4     5     6     7     8
 signal row 1        IO0   IO2   IO4   IO6   IO8   IO10  GND   GND
 signal row 2        IO1   IO3   IO5   IO7   IO9   IO11  GND   GND
 power row           GND   PIN V GND   3V3   GND   5V    GND   SLOT PWR
```

The separate post beside the header is the **guide pin**. The extension has a
matching hole. If it does not drop onto the header and guide pin without
force, it is reversed or shifted.

Never shift the extension sideways by one column. Check the guide pin before power.

## What the four power pins mean

| Pin | Meaning |
|---|---|
| `PIN V` | The signal voltage for that FPGA group: 3.3, 2.5 or 1.8 V |
| `+5V` | Fixed supply for 5 V parts |
| `+3V3` | Fixed supply for ordinary 3.3 V parts |
| `SEL PWR` | Selected beside that slot: 12 V, 5 V or 3.3 V |

`PIN V` is both a power output and the voltage used by the FPGA pins. The
schematic calls it `VCCIO`; the board says PIN VOLTAGE because that says what
the selector changes.

The 1.0 V FPGA core rail never reaches a connector.

### Power is shared

The small fuse beside each slot is fault protection. It is not a promise that
every slot may draw the number printed on the fuse at the same time.

Odin also separates connector power from its own power. One protected switch
feeds each shared extension bus: 5 V, 3.3 V, the two PIN VOLTAGE groups, and
selected 12 V power. A short or power applied backward can shut down the affected shared bus
without shutting down the FPGA, memories or board controller. All extensions on
that bus lose power together. Unplug the bad extension before retrying.

This protects power pins only. It does not make the ordinary FPGA signals
5 V compatible. Use 5V BUS 0 or 5V BUS 1 for 5 V signals.

The selectable 12 V rail is the tightest. Treat **about 0.5 A across the whole board**
as the present design target, pending final component qualification. One LCD
backlight is sensible. Nine motors are not.

The final production manual must take its exact limits from the released
power-budget report. Do not copy preliminary figures from an old schematic.

## Which slot should I use?

```text
Is the signal 5 V?
  yes -> use 5V BUS 0 or 5V BUS 1
  no  -> continue

Does each pin need its own direction, or is it fast/LVDS?
  yes -> use A-H
  no  -> either works

Does it require 1.8 V or 2.5 V?
  yes -> give it a whole bank: A-D or E-H
  no  -> leave PIN VOLTAGE at 3.3 V
```

### The two 5V buses are different

5V BUS 0 and 5V BUS 1 protect the FPGA from 5 V signals. Each is one complete
eight-bit bus with one shared direction control. All eight pins on one bus
turn around together. Use them for old 5 V buses, parallel displays and similar parts.
Do not use it for I2C, one-wire parts, or a mixture of inputs and outputs that
must change direction independently.

Slots A-H connect directly to FPGA pins. They are flexible and fast, but they
are **not 5 V tolerant**.

## Example 1: a 3.3 V SPI sensor

Use one direct slot, for example A.

```text
Sensor VCC   -> +3V3
Sensor GND   -> GND
Sensor SCK   -> any signal pin
Sensor MOSI  -> any signal pin
Sensor MISO  -> any signal pin
Sensor CS    -> any signal pin

A-D PIN VOLTAGE -> 3.3 V
SLOT A POWER    -> no jumper needed
```

Six signal pins remain free. The sensor receives clean 3.3 V even if another
bank uses a different voltage.

## Example 2: an old 5 V parallel peripheral

Use either 5V BUS.

```text
Peripheral VCC       -> +5V
Peripheral GND       -> GND
Data D0-D7            -> 5V BUS 0 I/O 0-7
Read/write or status  -> 5V BUS 1 I/O 0 (when 5 V compatibility is required)
```

In the FPGA design, set BUS 0's direction control before driving or reading
D0-D7. BUS 1 can independently serve a second byte-wide 5 V interface.

Do not connect a 5 V signal to A-H just because its power comes from their
5 V pin. Power voltage and signal voltage are separate things.

## Example 3: a small handheld

A 64 shield bridges A-D to E-H and gets 96 direct 3.3 V signals. This
example only needs thirty-seven:

```text
16  LCD colour bits
 4  pixel clock and display timing
 8  buttons
 2  display reset and backlight control
 3  digital audio
 4  microSD SPI
---
37  used
59  spare
```

Use:

```text
PIN V   3.3 V   FPGA signal level
+3V3            display, SD card and audio logic
+5V             audio amplifier
SEL PWR 12 V    backlight driver, if required
```

The framebuffer belongs in PSRAM. A 320 x 240 RGB565 frame is about 150 KB;
the board has 8 MB.

## Memory without ceremony

Odin has four 2 MB PSRAM chips. Each has its own connection to the FPGA.

```text
PSRAM 0  video or DMA
PSRAM 1  CPU memory
PSRAM 2  CPU memory
PSRAM 3  scratch, capture or another CPU
```

That split is only an example. HDL decides what each chip does. The hardware
does not force them to share one busy connection.

One chip can move roughly 50 MB/s at a 100 MHz quad-SPI clock. Four used
together can approach 200 MB/s. VGA RGB565 fits on one. 1080p60 RGB565 does
not fit on all four. That is the honest ceiling.

## Programming and recovery

The board controller has its own startup memory. The FPGA has another. They
are not the same thing.

| Storage | Holds |
|---|---|
| Controller memory | Software that starts and manages the board |
| FPGA startup memory | FPGA images and fabric software |

A new blank board enters its built-in USB loader. Copy the board-controller firmware
to the USB drive that appears.

If a later board-controller update goes wrong:

1. Unplug power.
2. Hold **CTRL BOOT**.
3. Plug USB-C back in.
4. Release the button when the USB drive appears.
5. Copy known-good board-controller firmware to it.

The recovery loader is inside the chip. A broken flash image cannot erase it.

### Hardware identity and compatible firmware

This design is **Odin hardware `0.1.0-proto.1`**. The hardware version and exact
programmable-device identities are printed on the PCB, so rewriting or replacing
either flash chip cannot erase the board's identity.

The assembled board prints the exact fitted programmable-device part numbers
beside the devices on the top silkscreen. For this revision they are
`XC7A100T-2FGG676I` and `RP2350B`. Do not identify a board only as “Artix-7” or
“RP-class”: package, density and controller variant determine the usable
toolchain and firmware.

Board-controller firmware must read the FPGA JTAG IDCODE before erasing or
programming FPGA storage, select an explicitly supported FPGA profile, and
refuse an unknown IDCODE with a useful diagnostic. It must also report its own
build target and supported FPGA profiles over USB.

JTAG identifies the FPGA die/device family and density, but does not reliably
encode the complete orderable suffix such as package, speed grade and
temperature grade. Therefore autodetection is a compatibility guard; the
silkscreen, schematic and manufacturing BOM remain the authority for the exact
fitted part.

Odin uses Semantic Versioning independently for hardware, board-controller
firmware and FPGA gateware:

- **MAJOR:** an existing bitstream, firmware, extension or connector contract
  becomes incompatible;
- **MINOR:** a backward-compatible hardware capability is added;
- **PATCH:** layout or BOM corrections leave behavior and interfaces unchanged;
- a pre-release suffix identifies each prototype fabrication. No two different
  fabrications may reuse the same complete hardware version.

The first proven public hardware release will be `1.0.0`. Firmware and gateware
releases must carry a manifest declaring their supported hardware-version range,
exact FPGA build target, pin-map hash and toolchain version.

### External JTAG

Normal use needs no external programmer. J2 exists for low-level FPGA debug.
Fit **EXT JTAG** (`J52`) before attaching an external programmer.
That disconnects the board controller from the same four wires. Remove the
jumper for normal board-controlled programming.

## Fast links

Two SFP sockets are fitted by default. They can accept suitable copper,
fibre or direct-attach modules.

```text
SFP 0 -> FPGA fast lane 0
SFP 1 -> FPGA fast lane 1
```

The FPGA provides the physical serial lane. Your FPGA design still needs the
protocol logic. Plugging in a copper Ethernet module does not create an
Ethernet controller by itself.

The lanes top out around 6.6 Gb/s. Use them for 1 Gb/s or suitable 2.5 Gb/s
links, not 10 Gb/s modules.

There are exactly two SFP ports. The FPGA's other fast lanes are unused.

## If something goes wrong

### The board resets when an extension starts

The power source is probably too small, or the extension has too much startup
current.

- Remove the extension and try again.
- Use a USB-PD charger instead of a computer port.
- Check the extension for a short.
- Start with SLOT POWER unselected or set to 3.3 V.

### An extension does nothing

- Check the guide pin and header alignment.
- Check PIN VOLTAGE for the whole group.
- Check its SLOT POWER selector.
- Remember that each 5V BUS uses one shared direction control.
- Remember that a blown or tripped branch fuse is not fixed by HDL.

### The FPGA will not program

- Remove every extension.
- Restore both PIN VOLTAGE groups to 3.3 V.
- Remove `EXT JTAG` (`J52`) for normal programming.
- Recover the controller with **CTRL BOOT**.

### A rail reads low

Disconnect extensions one at a time. A bad extension should be treated as the
fault until it works alone on a current-limited bench supply.

## Rules worth remembering

1. Check the guide pin before power.
2. Slots in one group share one PIN VOLTAGE setting.
3. Only 5V BUS 0 and 5V BUS 1 accept 5 V signals.
4. Each 5V BUS is a complete eight-bit bus with shared direction.
5. The four connector rails share the board's total power.
6. Never feed power into an Odin power-output pin.
7. Start a new extension at 3.3 V with SLOT POWER unselected.
8. Test one extension before stacking several.
9. Use a PD charger for power-heavy projects.
10. When in doubt, unplug power first.

## Before this manual becomes a release manual

The circuit is still being qualified. Replace this section with final ratings
before shipping hardware:

- Exact shared and per-slot current limits
- Extension-rail shutdown and fault behavior
- Final connector positions and orientation drawing
- Board-controller status messages and firmware-loading names
- Qualified SFP module types
- Board revision and matching schematic commit

Until those are fixed, this is the user contract for the design—not permission
to fabricate an unchecked revision.
