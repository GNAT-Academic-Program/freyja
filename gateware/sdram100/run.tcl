# SDRAM timing fixture, 100 MHz CL3. Separate from gateware/gate, which stays
# the allocation gate. Takes about a minute. Run from anywhere:
#
#   source /tools/Xilinx/2026.1/Vivado/settings64.sh
#   vivado -mode batch -nojournal -nolog -source gateware/sdram100/run.tcl
#
# Products go to gateware/sdram100/build/ (ignored by git). Pass a directory
# after -tclargs to build a generated variant from there instead.
set here [file normalize [file dirname [info script]]]
set src [expr {[llength $argv] ? [file normalize [lindex $argv 0]] : $here}]
set build [expr {[llength $argv] ? $src : [file join $here build]}]
file mkdir $build
cd $build
set part xc7a100tfgg676-2

create_project -in_memory -part $part
read_verilog [file join $src top.v]
read_xdc [file join $src sdram100_pins.xdc]
read_xdc [file join $src sdram100_timing.xdc]
synth_design -top top -part $part
opt_design
place_design
route_design
report_timing_summary -delay_type min_max -report_unconstrained -file summary.rpt
report_exceptions -file exceptions.rpt
report_clocks -file clocks.rpt
report_io -file io.rpt
check_timing -file check.rpt
report_drc -file drc.rpt

proc slack {paths} {
    if {[llength $paths] == 0} { return NA }
    return [get_property SLACK [lindex $paths 0]]
}
set f [open slacks.csv w]
puts $f "port,dir,setup,hold"
foreach q [lsort [get_ports SDRAM_*]] {
    set n [get_property NAME $q]
    if {$n eq "SDRAM_CLK"} continue
    if {[string match SDRAM_DQ* $n]} {
        set i [string range $n 8 end]
        set out [get_pins io$i/OBUFT/I]
        puts $f "$n,out,[slack [get_timing_paths -setup -through $out]],[slack [get_timing_paths -hold -through $out]]"
        set t [get_pins io$i/OBUFT/T]
        puts $f "$n,t,[slack [get_timing_paths -setup -through $t]],[slack [get_timing_paths -hold -through $t]]"
        puts $f "$n,in,[slack [get_timing_paths -setup -from $q]],[slack [get_timing_paths -hold -from $q]]"
    } else {
        puts $f "$n,out,[slack [get_timing_paths -setup -to $q]],[slack [get_timing_paths -hold -to $q]]"
    }
}
close $f

# Refuse results from flops that fell out of the IOBs.
set ologic [llength [get_cells -hier -filter {REF_NAME=~FD* && BEL=~OLOGIC*}]]
set ilogic [llength [get_cells -hier -filter {REF_NAME=~FD* && BEL=~ILOGIC*}]]
puts "IOB flops: OLOGIC $ologic ILOGIC $ilogic"
if {$ologic != 54 || $ilogic != 16} { puts "ERROR: expected 54 OLOGIC and 16 ILOGIC flops"; exit 1 }
write_checkpoint -force routed.dcp
exit 0
