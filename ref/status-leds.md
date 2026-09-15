# Board status LEDs and core power-good

U17 remains on upstream I2C at 7-bit address **0x24**. No RP2350 or FPGA
GPIO assignments change. Three green LEDs reuse the qualified 0603 part
C7496818, each fed from always-on +3V3 through 1k (R128–R130, C11702).
U17 sinks their cathode current: **0 lights an LED, 1 turns it off**.
Expected current is approximately 0.7–1.3mA per LED before output-voltage
loss; under 4mA total. All LEDs default off at expander power-on.

| U17 bit (physical pin) | Function | Board label |
|---|---|---|
| P0 (4) | D9 supervisor heartbeat | CTRL HB |
| P1 (5) | D10 software-controlled user indicator | USER 1 |
| P2 (6) | D11 software-controlled user indicator | USER 2 |
| P3 (7) | CORE_1V0_GOOD from U15 PG | input; retain existing 100k pull-up |
| P4–P6 | spare | keep output latches high |
| P7 (12) | EN_SFP_N | existing shared SFP power control |

The PCF8574 has quasi-bidirectional pins. **Always write P3=1** to release
that pin for input; writing zero would pull down the regulator's PG signal.
Read bit 3 to sample power-good. A high reading is meaningful only after
core power is enabled and its startup interval has elapsed; combine it with
MON_1V0 for a voltage check. No automatic firmware interpretation exists yet.

## Firmware write contract

Maintain a software shadow of U17's **output latch**, initialized to 0xFF.
Serialize all U17 writes with the same bus lock used for SFP management.
Never use a port read as the writeback value: a low PG input must not become
a latched-low output, and LED pin readback need not equal its output latch.

- To change LEDs, modify only bits 0–2; preserve bit 7.
- To change SFP power, modify only bit 7; preserve bits 0–2.
- Before every write, OR the shadow with **0x78**, keeping P3–P6 high.
- Read `port & 0x08` for core PG; do not merge that read into the shadow.
- `0x7F` enables SFP power with all LEDs off; `0xFF` disables it with all
  LEDs off. These full-byte constants are startup states, not general runtime
  updates. Deselect U27 before turning SFP power off.

For the reference firmware, toggle heartbeat at a visible cadence (for
example, once every 500ms) from the main service loop after successful status
polling. A stuck-on light is not proof of a healthy supervisor. USER 1/2
are available to supervisor software or fabric applications via supervisor
commands; they are not directly wired FPGA LEDs. The firmware is not yet
implemented, so these behaviors remain a firmware contract.

If a selected SFP module holds the upstream I2C bus low, LED updates and PG
reads stop too. The heartbeat stopping exposes that failure; recovery follows
[the SFP bus contract](sfp-i2c.md). Place the three labeled LEDs where they
remain visible, using the board-status group in the placement tools.

The sinking connection and input-latch rule follow the
[NXP PCF8574 datasheet](https://www.nxp.com/docs/en/data-sheet/PCF8574_PCF8574A.pdf).
