# RGMII timing fixture, 125 MHz DDR. Separate from gateware/gate, which stays
# the allocation gate. Takes about a minute. Run from anywhere:
#
#   source /tools/Xilinx/2026.1/Vivado/settings64.sh
#   vivado -mode batch -nojournal -nolog -source gateware/rgmii1000/run.tcl
#
# Products go to gateware/rgmii1000/build/ (ignored by git). Pass a directory
# after -tclargs to build a generated variant from there instead.
set here [file normalize [file dirname [info script]]]
set src [expr {[llength $argv] ? [file normalize [lindex $argv 0]] : $here}]
set build [expr {[llength $argv] ? $src : [file join $here build]}]
file mkdir $build
cd $build
set part xc7a100tfgg676-2

create_project -in_memory -part $part
read_verilog [file join $src top.v]
read_xdc [file join $src rgmii1000_pins.xdc]
read_xdc [file join $src rgmii1000_timing.xdc]
synth_design -top top -part $part
opt_design
place_design
route_design
report_timing_summary -delay_type min_max -report_unconstrained -file summary.rpt
report_clocks -file clocks.rpt
report_io -file io.rpt
check_timing -file check.rpt
report_drc -file drc.rpt

proc row {f tag paths} {
    if {[llength $paths] == 0} { puts $f "$tag: no path"; return }
    set p [lindex $paths 0]
    regexp {([a-z0-9_]+ (?:rise|fall)@[-0-9.]+ns) - ([a-z0-9_]+ (?:rise|fall)@[-0-9.]+ns)} \
        [report_timing -of_objects $p -return_string] -> capture launch
    puts $f [format "%-22s %-26s launch %-20s capture %-18s req %7s slack %7s" \
        $tag [get_property ENDPOINT_PIN $p] $launch $capture [get_property REQUIREMENT $p] [get_property SLACK $p]]
}

# Worst path per port and corner, then every launch and capture edge pair.
proc slack {paths} {
    if {[llength $paths] == 0} { return NA }
    return [get_property SLACK [lindex $paths 0]]
}
set txp [get_ports {PHY_TXD* PHY_TX_CTL}]
set rxp [get_ports {PHY_RXD* PHY_RX_CTL}]
set f [open slacks.csv w]
puts $f "port,dir,corner,setup,hold"
foreach c {Slow Fast} {
    foreach q [lsort $txp] { puts $f "$q,tx,$c,[slack [get_timing_paths -setup -corner $c -to $q]],[slack [get_timing_paths -hold -corner $c -to $q]]" }
    foreach q [lsort $rxp] { puts $f "$q,rx,$c,[slack [get_timing_paths -setup -corner $c -from $q]],[slack [get_timing_paths -hold -corner $c -from $q]]" }
}
close $f
# Both DDR edges: worst path launched by each c125 edge on TX, captured by each RXC edge on RX.
set f [open edges.txt w]
foreach c {Slow Fast} {
    row $f "tx setup $c launch rise" [get_timing_paths -setup -corner $c -rise_from [get_clocks c125*] -to $txp]
    row $f "tx setup $c launch fall" [get_timing_paths -setup -corner $c -fall_from [get_clocks c125*] -to $txp]
    row $f "tx hold  $c launch rise" [get_timing_paths -hold  -corner $c -rise_from [get_clocks c125*] -to $txp]
    row $f "tx hold  $c launch fall" [get_timing_paths -hold  -corner $c -fall_from [get_clocks c125*] -to $txp]
    row $f "rx setup $c capture rise" [get_timing_paths -setup -corner $c -from $rxp -rise_to [get_clocks phy_rxc]]
    row $f "rx setup $c capture fall" [get_timing_paths -setup -corner $c -from $rxp -fall_to [get_clocks phy_rxc]]
    row $f "rx hold  $c capture rise" [get_timing_paths -hold  -corner $c -from $rxp -rise_to [get_clocks phy_rxc]]
    row $f "rx hold  $c capture fall" [get_timing_paths -hold  -corner $c -from $rxp -fall_to [get_clocks phy_rxc]]
}
close $f
report_timing -setup -corner Slow -from [lindex [lsort $rxp] 0] -file rx_setup_path.txt
report_timing -hold -corner Fast -from [lindex [lsort $rxp] 0] -file rx_hold_path.txt
report_timing -setup -corner Slow -to [lindex [lsort $txp] 0] -file tx_setup_path.txt
report_timing -hold -corner Fast -to [lindex [lsort $txp] 0] -file tx_hold_path.txt

# Refuse results from registers outside the IOBs.
set o [llength [get_cells -hier -filter {REF_NAME=~ODDR* && BEL=~OLOGIC*}]]
set i [llength [get_cells -hier -filter {REF_NAME=~IDDR* && BEL=~ILOGIC*}]]
puts "IOB: ODDR in OLOGIC $o, IDDR in ILOGIC $i"
if {$o != 6 || $i != 5} { puts "ERROR: expected 6 ODDR and 5 IDDR in the IOBs"; exit 1 }
write_checkpoint -force routed.dcp
exit 0
