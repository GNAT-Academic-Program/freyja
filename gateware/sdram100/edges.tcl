# Reads launch and capture edges, exception scope and turnaround arcs from the
# routed fixture. Writes edges.txt and arcs.txt beside the checkpoint; margins.py
# turns arcs.txt into the turnaround table. Run after run.tcl:
#
#   vivado -mode batch -nojournal -nolog -source gateware/sdram100/edges.tcl
set here [file normalize [file dirname [info script]]]
cd [file join $here build]
open_checkpoint routed.dcp

proc row {f tag paths} {
    if {[llength $paths] == 0} { puts $f "$tag: no path"; return }
    set p [lindex $paths 0]
    regexp {([a-z0-9_]+ (?:rise|fall)@[-0-9.]+ns) - ([a-z0-9_]+ (?:rise|fall)@[-0-9.]+ns)} \
        [report_timing -of_objects $p -return_string] -> capture launch
    puts $f [format "%-28s %-14s to %-14s launch %-22s capture %-20s req %7s slack %7s %s" \
        $tag [get_property STARTPOINT_PIN $p] [get_property ENDPOINT_PIN $p] \
        $launch $capture [get_property REQUIREMENT $p] [get_property SLACK $p] [get_property CORNER $p]]
}

set f [open edges.txt w]
set dq [get_ports SDRAM_DQ*]
set all [get_timing_paths -setup -from [get_clocks sdram_clk] -to [get_clocks c0] -max_paths 500 -nworst 1]
set ends {}
foreach p $all { lappend ends [get_property ENDPOINT_PIN $p] }
puts $f "sdram_clk to c0: [llength $all] paths, [llength [lsort -unique $ends]] endpoints; all dq_i_reg: [expr {[llength [lsearch -all -inline -glob $ends dq_i_reg*]] == [llength $ends]}]"
puts $f "other paths into dq_i from c0 (pad loopback): [llength [get_timing_paths -setup -from [get_clocks c0] -to [get_cells dq_i_reg[*]]]]"
puts $f "\n== as constrained"
foreach c {Slow Fast} {
    row $f "read setup $c" [get_timing_paths -setup -corner $c -from $dq]
    row $f "read hold $c"  [get_timing_paths -hold  -corner $c -from $dq]
}
set bus [get_ports {SDRAM_A* SDRAM_BA* SDRAM_CS_N SDRAM_RAS_N SDRAM_CAS_N SDRAM_WE_N SDRAM_CKE SDRAM_?DQM}]
foreach c {Slow Fast} {
    row $f "command setup $c" [get_timing_paths -setup -corner $c -to $bus]
    row $f "command hold $c"  [get_timing_paths -hold  -corner $c -to $bus]
    row $f "write setup $c" [get_timing_paths -setup -corner $c -through [get_pins io*/OBUFT/I]]
    row $f "write hold $c"  [get_timing_paths -hold  -corner $c -through [get_pins io*/OBUFT/I]]
}

puts $f "\n== alternatives, for comparison only; a later constraint overrides the earlier one"
proc multicycle {setup hold} {
    set_multicycle_path $setup -setup -from [get_clocks sdram_clk] -to [get_cells dq_i_reg[*]]
    set_multicycle_path $hold -hold -from [get_clocks sdram_clk] -to [get_cells dq_i_reg[*]]
}
foreach {tag setup hold} {"no exception" 1 0 "-setup 2 -hold 1" 2 1 "-setup 3, one edge late" 3 0} {
    multicycle $setup $hold
    row $f "$tag: setup" [get_timing_paths -setup -from $dq]
    row $f "$tag: hold"  [get_timing_paths -hold  -from $dq]
}
multicycle 2 0
close $f

# Arrival at the pad, from the launching c0 edge, for the release and enable arcs.
proc stamps {paths} {
    set s [report_timing -of_objects [lindex $paths 0] -return_string]
    regexp {clock c0 rise edge\)\s+([-0-9.]+)} $s -> launch
    regexp {arrival time\s+(-?[0-9.]+)} $s -> arrive
    return [expr {abs($arrive) - $launch}]
}
set f [open arcs.txt w]
foreach c {Slow Fast} {
    foreach {name opt} {enable -fall_through disable -rise_through} {
        foreach {ty} {setup hold} {
            set vals {}
            for {set i 0} {$i < 16} {incr i} {
                lappend vals [stamps [get_timing_paths -$ty -corner $c $opt [get_pins io$i/OBUFT/T]]]
            }
            set vals [lsort -real $vals]
            puts $f "$c $name $ty [lindex $vals 0] [lindex $vals end]"
        }
    }
    set s [report_timing -setup -corner $c -from $dq -return_string]
    regexp {Source Clock Delay\s+\(SCD\):\s+(-?[0-9.]+)} $s -> late
    set s [report_timing -hold -corner $c -from $dq -return_string]
    regexp {Source Clock Delay\s+\(SCD\):\s+(-?[0-9.]+)} $s -> early
    puts $f "$c fwd $early $late"
}
close $f
exit 0
