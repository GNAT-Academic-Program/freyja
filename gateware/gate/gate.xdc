# Timing exceptions for the gate design only (gateware/gate/top.v).
# ref/freya.xdc is the board file and carries none of this.
# The four input clocks are unrelated in the gate; the fold registers cross
# between them on purpose.
set_clock_groups -asynchronous \
    -group [get_clocks sys_clk] \
    -group [get_clocks phy_rxc] \
    -group [get_clocks link_p_rxc_p] \
    -group [get_clocks link_q_rxc_p]
# Every input and output is exercised, not timed: this gate checks pin
# legality and routability, not I/O timing.
set_false_path -from [all_inputs]
set_false_path -to [all_outputs]
