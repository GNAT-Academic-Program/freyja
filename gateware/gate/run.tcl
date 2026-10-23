# Vivado gate: synthesise, place, route and write a bitstream for the
# throwaway top in this directory against ref/freya.xdc, so the ball
# allocation is proven legal on the real part.
#
#   cd <repo>
#   python3 tools/gen_xdc.py
#   source /tools/Xilinx/2026.1/Vivado/settings64.sh
#   vivado -mode batch -nojournal -nolog -source gateware/gate/run.tcl
#
# Products go to gateware/gate/build/ (ignored by git). Exit code is non-zero
# on any failure, so tools/gate.py could call this if it ever grows a long
# mode; today it is run by hand because it takes minutes.
set root [file normalize [file join [file dirname [info script]] .. ..]]
set build [file join $root gateware gate build]
file mkdir $build
set part xc7a100tfgg676-2

set found [get_parts $part]
if {[llength $found] == 0} { puts "ERROR: part $part not installed"; exit 1 }
puts "part: $found"

create_project -in_memory -part $part
read_verilog [file join $root gateware gate top.v]
read_xdc [file join $root ref freya.xdc]
read_xdc [file join $root gateware gate gate.xdc]
synth_design -top top -part $part
# Unconstrained-port and I/O-standard problems surface here, before P&R.
report_drc -file [file join $build drc_synth.rpt]
opt_design
place_design
route_design
report_drc -file [file join $build drc_routed.rpt]
report_io -file [file join $build io.rpt]
report_clock_utilization -file [file join $build clocks.rpt]
report_timing_summary -file [file join $build timing.rpt]
report_utilization -file [file join $build util.rpt]
write_checkpoint -force [file join $build top_routed.dcp]
write_bitstream -force [file join $build top.bit]
puts "GATE BITSTREAM OK: [file join $build top.bit]"
exit 0
