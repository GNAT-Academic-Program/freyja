# Odin user manual

Odin is an FPGA board for building the thing you meant to build.

One USB-C cable powers it and programs it. Four PSRAM chips give the FPGA
32 MB of working memory on four private ports, and a 32 MB SDRAM sits beside
them. Ten extension ports carry signals and useful power.
A gigabit Ethernet jack and two raw link ports sit on the bottom edge,
opposite the two extension bus headers.

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
      32 MB PSRAM <---> four separate memory links   |
      32 MB SDRAM <---> one 16-bit bus                |
     microSD, MRAM <---> SPI                          |
                    |                                |
      slots A-D  <----> 48 direct pins, one voltage  |
      slots E-H  <----> 48 direct pins, one voltage  |
      5V BUS 0/1 <----> two complete 8-bit buses     |
                    |                                |
      ETH         <----> 1000Base-T PHY, RGMII     |
      LINK P / Q  <----> raw LVDS pairs, board to board |
                    +--------------------------------+
```

## Start here

1. Leave all extensions unplugged.
2. Set both **A–D PIN VOLTAGE** and **E–H PIN VOLTAGE** to **3.3 V**.
3. Leave **AUX IN** unconnected.
4. Plug USB-C into Odin.
5. Wait for the board controller to start.
6. Plug in one simple extension and test it before adding the next.

Use a USB-PD charger when the board carries displays, speakers or motors. A computer port is fine for programming and light work, but it may
not have enough power for everything at once.

Odin asks USB-C for 5 V by default and for 9 V only once the board controller
is running and has decided to; its pins cannot form any higher request.
While it asks, the board's 5 V runs a little low for under a second;
extension power stays off until the request is settled. A 9 V charger is
good for at least 15 W. A computer port is treated as 500 mA unless you
tell the board controller otherwise: it cannot measure what a 5 V port
offers.

### Optional power input

`OPTIONAL POWER IN` is not required for normal use. It is a second way to
power Odin from a regulated bench supply when USB-C cannot provide enough
power. Connect **9–21 V** to the pin marked `+` and supply ground to `GND`.
USB-C may remain connected; while the optional input is powered, Odin runs
from it and uses USB only to talk to the computer. Never exceed 21 V.
Full extension power (every connector rail loaded at once) needs this
input; a 9 V USB-PD charger carries the board and part of the extensions.
See [power-budget.md](power-budget.md).

## The extension idea, from zero

Odin has eight shield sections on the left and right edges of the 100 x 100 mm
board (A–D on the left, E–H on the right). Each section has a 16-position
signal block and a separate keyed power row: a grounded post at position 1
and a seven-contact socket. Two additional ports are complete 5 V-compatible
eight-bit buses. The authoritative pin map is
[extension-ux.md](extension-ux.md); the tables below repeat it.

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

Twelve pins are signals. Four grounds complete the signal block, in columns
3 and 6 of both rows. Power gets its own unmistakable row: a key post, then
PIN V, 3V3, 5V and AUX, each beside a ground.

### Where are the I/Os?

Here. `IO` means a signal you can use as an input or an output.

```text
              1     2     3     4     5     6     7     8
signal row 1  IO0   IO2   GND   IO4   IO6   GND   IO8   IO10
signal row 2  IO1   IO3   GND   IO5   IO7   GND   IO9   IO11
power row     POST  PIN V GND   3V3   GND   5V    GND   AUX
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
physical arrangement: **one continuous 2x32 female signal body per edge, and
per zone one 1x7 female power socket with a grounded key post in front of
it**. A 16 shield uses one zone on each edge, a 32 two, and a 64 all four. The
key posts and outlines must make those partial positions unambiguous.

The bridge gives the extension support at both ends, almost the full board
area above Odin, and matching connectors on top so another shield can stack.
The extension PCB and its fitted headers determine its size; there is no size
switch.

### Where are the slots on Odin?

The required arrangement is:

```text
                       100 mm
          +----------------------------+
      A   |  [ L ]            [ M ]    |   E        top: the two 5 V buses
      B   |                            |   F
          |           ODIN             |            left: A-D (bank 15)
      C   |                            |   G        right: E-H (bank 34)
      D   |                            |   H
          +----------------------------+
```

Matching pairs are A/E, B/F, C/G and D/H, directly opposite each other across
the board on one 2.54 mm lattice. All eight zones have the same pitch,
orientation and distance from the board edge; `tools/place.py --check`
verifies that from the real pad coordinates.

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
 signal row 1        IO0   IO2   GND   IO4   IO6   GND   IO8   IO10
 signal row 2        IO1   IO3   GND   IO5   IO7   GND   IO9   IO11
 power row           POST  PIN V GND   3V3   GND   5V    GND   AUX
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
| `AUX` | Whatever you wire to **AUX IN** (9–28 V, unregulated), through that slot's own fuse. Nothing when AUX IN is empty |

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
turn around together. Each bus also has an independent active-low enable,
`BUS5V0_OE_N` or `BUS5V1_OE_N`, pulled up to +3V3 through 10k. The translators
remain disabled during FPGA configuration. Use them for old 5 V buses,
parallel displays and similar parts.
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

In the FPGA design, keep `BUS5V0_OE_N` high while setting direction and
initial data. `BUS5V0_DIR=1` sends FPGA data to the connector; `DIR=0` receives
connector data (release the FPGA data outputs first). Drive `OE_N` low only
when ready. Raise it before changing direction and allow the translator's
disable/enable timing when handing the bus over. Initialize both enables
high in the bitstream's reset logic. BUS 1 has independent DIR and OE_N
controls and follows the same sequence. See the
[SN74LXC8T245 datasheet](https://www.ti.com/lit/ds/symlink/sn74lxc8t245.pdf).

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
AUX 12 V        backlight driver, if required (12 V wired to AUX IN)
```

The framebuffer belongs in PSRAM. A 320 x 240 RGB565 frame is about 150 KB;
the board has 32 MB of PSRAM and another 32 MB of SDRAM.

## Memory without ceremony

Odin has four 8 MB PSRAM chips. Each has its own connection to the FPGA.

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
**J2 is a custom 2.54mm 2×5 header, incompatible with direct Xilinx 2mm 2×7
or Digilent 1×6 cables:** use an adapter; pins 1/3/5/7/9 are +3V3 reference,
TMS, TCK, TDO and TDI, and all even pins are GND. Pin 1 is marked `1` on
silkscreen; +3V3 is the adapter voltage reference, not an external power input.
Fit **EXT JTAG** (`J52`) before attaching an external programmer.
That disconnects the board controller from the same four wires. Remove the
jumper for normal board-controlled programming.

The FPGA loads itself from its flash (master SPI) at power-on. The board
controller writes that flash while it holds the FPGA in reset, and loads a
design directly into the FPGA over the same JTAG wires. There is no
slave-serial path: the mode pins are fixed in copper.

## Network and link ports

**ETH** is a 1000Base-T jack behind an RTL8211FD-CG PHY on RGMII. The FPGA
design still needs a MAC (and a stack): the PHY gives you a link, not an
Ethernet controller. Green is link/activity, yellow is a 1000 Mb/s link.

**LINK P** and **LINK Q** are not Ethernet. They carry eight LVDS pairs
straight from FPGA pins to a shielded twisted-pair cable, for board-to-board
links between two of these boards. Cable **P to Q**, use STP cable, and
**power both boards before connecting the cable**: the pins are DC coupled
and the receiving board must be powered first. See
[link-ports.md](link-ports.md) for the pinout and [network.md](network.md)
for the PHY.

## If something goes wrong

### The board resets when an extension starts

The power source is probably too small, or the extension has too much startup
current.

- Remove the extension and try again.
- Use a USB-PD charger instead of a computer port.
- Check the extension for a short.
- Start with AUX IN unconnected.

### An extension does nothing

- Check the guide pin and header alignment.
- Check PIN VOLTAGE for the whole group.
- Check whether it needs AUX, and what AUX IN is wired to.
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
7. Start a new extension at 3.3 V with AUX IN unconnected.
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
- PHY bring-up register sequence and link-port data rate
- Board revision and matching schematic commit

Until those are fixed, this is the user contract for the design—not permission
to fabricate an unchecked revision.

## FPGA DONE indicator

The green **FPGA DONE** LED lights when the FPGA releases DONE high after
configuration. A BSS138 buffer supplies its current independently of the
configuration pin, and an external 4.7k pull-up defines the high level.
Reference bitstreams do **not** need `DriveDone=Yes` for this indicator.
The supervisor reads the same DONE signal through its existing input path.

A lit LED indicates DONE is high; it does not prove that the user application
is running correctly. Ignore the indicator while supplies are ramping.

## Controller heartbeat and user indicators

Three additional green indicators are fitted: **CTRL HB**, **USER 1** and
**USER 2**. They default off. Supervisor firmware can blink CTRL HB from its
main service loop and expose USER 1/2 to applications; that firmware remains
to be implemented. A frozen heartbeat indicates lost progress, while a
steady lit LED alone does not establish health. The three LEDs hang
directly off supervisor GPIO35-37 (low lights them).

The supervisor also reads the core regulator's **CORE_1V0_GOOD** on GPIO38,
alongside its existing MON_1V0 voltage measurement.
See [status indicators and firmware rules](status-leds.md).

## Memory

| Part | LCSC | Capacity | Bus | Voltage | FPGA bank | Populated by default |
|---|---|---|---|---|---|---|
| APS6404L-SQN-SN PSRAM, x4 (U2-U5) | C5360304 | 4 x 8 MB | QSPI, one private 6-line port per chip | 1.8 V | 13 | yes |
| W9825G6KH-6 SDRAM (U32) | C62246 | 32 MB | 16-bit SDR, 39 lines | 3.3 V | 35 (data, control), 14 (address) | yes |
| MR25H10CDF MRAM (U33) | C246234 | 128 KB | SPI, 4 lines | 3.3 V | 14 | yes |
| microSD socket TF-01A (J74) | C91145 | card | SPI mode, 5 lines incl. card detect | 3.3 V | 14 | yes |
| W25Q256JVEIQ configuration flash (U6) | C97522 | 32 MB | QSPI, master SPI boot | 3.3 V | 14 and bank 0 | yes |

Ball-by-ball list: `ref/ballmap.md`; constraints: `ref/freya.xdc`.
