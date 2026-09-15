# SFP identity bus and firmware contract

## Hardware

U27 is **NXP PCA9543APW,118 / C2652904**, using the standard TSSOP-14
4.4 × 5 mm, 0.65 mm-pitch footprint and a drawing-based symbol. Its pin map
is from NXP PCA9543A/43B Table 3. A0/A1 are grounded, selecting address
**0x70**. U17 remains upstream at **0x24**, with P7 controlling shared Q1.

```text
RP2350 GPIO14 SCL / GPIO31 SDA
  +-- U17 PCF8574 (0x24) -- P7 --> Q1 shared SFP power
  +-- U27 PCA9543A (0x70)
        +-- channel 0 --> J60 / SFP0 EEPROM (0x50)
        +-- channel 1 --> J61 / SFP1 EEPROM (0x50)
```

U27 is powered from always-on +3V3 with C231 (100nF). R99–R102 provide
4.7k pull-ups on the four downstream lines to switched SFP_VCC. Existing
upstream 4.7k pull-ups remain on +3V3. R103 pulls both unused interrupt
inputs high; the interrupt output floats. RESET uses SUP_RUN and its existing
1k pull-up/100nF capacitor. Pulling SUP_RUN low resets both controller and mux.
A controller software/watchdog reset alone does **not** necessarily pulse RUN.

Q1 still powers both ports together. A module power fault therefore requires
shutting down both ports; the mux provides separate identity access, not
per-port power protection. Both serial links can stay powered during identity
reads. Per-port TX_DISABLE remains available to suppress a transmitter.

## Required firmware sequence

There is no supervisor firmware implementation in this repository yet. The
following is the required behavior, not a claim of a tested console feature.

1. Use 100 kHz on the shared upstream bus (U17 is a PCF8574).
2. At each firmware startup, write the single control byte **0x00** to U27
   at 7-bit address **0x70**, ending with STOP. This also clears a selection
   that might have survived a controller-only reset.
3. Keep U17 P3–P6 latches high. Clear P7 in the software output shadow
   to power both cages, preserving the P0–P2 LED states. **0x7F** is the
   initial all-LEDs-off, SFP-power-on value at **0x24**. Wait for the selected modules' specified
   management-interface startup time; use bounded retries and presence checks.
4. Hold one shared-bus software lock across selection, EEPROM access and
   deselection. Write **0x01** for SFP0 or **0x02** for SFP1 to 0x70, with
   STOP before addressing the EEPROM. Read its identity at **0x50**; use
   **0x51** only for modules supporting that diagnostics address.
5. Write **0x00** with STOP when finished, including on a recoverable read
   error. Never write **0x03**: selecting both channels recreates the conflict.
6. Deselect both channels before setting P7 in the U17 output shadow to
   remove shared power. Preserve P0–P2 and force P3–P6 high; **0xFF** is
   the all-LEDs-off, SFP-power-off state. Do not select a channel while SFP_VCC is off: upstream pull-ups
   could otherwise feed an unpowered module through the selected switch.

Treat each module's MOD_ABS independently. A failed read on one channel must
not reuse the other channel's cached identity. Switching channels does not
power-cycle the modules or interrupt the FPGA serial lanes.

If a selected module holds the bus low, a mux command and U17 power-off
command may both be inaccessible. Try bounded bus recovery, then assert
SUP_RUN externally or cycle board power to force mux deselection. Do not
claim that an I2C command to U17 can always recover a stuck upstream bus.

## Sources and qualification

- [NXP PCA9543A/43B datasheet](https://www.nxp.com/docs/en/data-sheet/PCA9543A_43B.pdf):
  pinout, address map, control register and reset behavior. Selection takes
  effect after STOP; POR/reset disconnects both channels.
- [LCSC C2652904](https://www.lcsc.com/product-detail/interface-specialized_nxp-pca9543apw-118_C2652904.html):
  exact orderable suffix and TSSOP-14 package.
- [JLC part listing](https://jlcpcb.com/partdetail/NXP-PCA9543APW_118/C2652904):
  listed for Economic and Standard PCBA, checked 2026-09-15. Refresh stock
  at assembly order time. This uses a generated symbol and standard KiCad
  footprint, not an EasyEDA import.

U17 now also provides three LEDs and the core PG input. Follow the
[shared-output-latch rules](status-leds.md) for every U17 write.
