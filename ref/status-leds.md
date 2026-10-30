# Board status LEDs and core power-good

Three green LEDs (the qualified 0603 part C7496818) sit on the board
controller's own GPIOs. Each anode is fed from always-on +3V3 through 1k
(R128–R130, C11702); the cathode goes to the GPIO. **Driving the pin low
lights the LED, high or high-impedance turns it off.** About 1.2 mA each,
inside the RP2350's 12 mA pad setting. All three are dark at power-on and
while the controller is in reset: the pads are then inputs with a weak
pull-down, which pulls the cathode toward ground only through the LED's
own forward drop, so no current flows.

| RP2350 GPIO | Net | Function | Board label |
|---|---|---|---|
| GPIO35 | `LED_HEARTBEAT_N` | D9 supervisor heartbeat | CTRL HB |
| GPIO36 | `LED_USER1_N` | D10 software-controlled user indicator | USER 1 |
| GPIO37 | `LED_USER2_N` | D11 software-controlled user indicator | USER 2 |
| GPIO38 | `CORE_1V0_GOOD` | U15 power-good, open drain with a 100k pull-up (R66) | input |

The I2C expander that carried these lines in earlier revisions (U17,
PCF8574, with its bus pull-ups, bypass and interrupt pull-up) is gone:
the controller has the GPIOs to spare, and the expander was an extended
JLCPCB part plus five passives for four signals.

## Firmware contract

- Configure GPIO35–37 as outputs, initial value high (LED off), before
  anything else on those pins; reconfiguring a pin while the LED is lit is
  harmless but visible.
- Configure GPIO38 as an input with no pull: R66 already pulls it up, and
  an internal pull-down would fight it.
- Toggle CTRL HB at a visible cadence (for example once every 500 ms) from
  the main service loop after successful status polling. A stuck-on light is
  not proof of a healthy supervisor; a frozen one is proof of lost progress.
- USER 1 and USER 2 are for supervisor software or for fabric applications
  through supervisor commands; they are not wired to the FPGA.
- A high CORE_1V0_GOOD is meaningful only after EN_1V0 is asserted and the
  SY8047's start-up interval has elapsed; combine it with MON_1V0 for a
  voltage check. No automatic firmware interpretation exists yet.

Place the three labelled LEDs where they stay visible: they form the LED
dashboard with the FPGA's DONE LED (tools/city.py, tools/stencil.py).
