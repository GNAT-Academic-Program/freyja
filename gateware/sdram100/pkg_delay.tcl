# Writes every package pin's trace delay for the exact part. mkprofile.py keeps only the SDRAM balls.
#   vivado -mode batch -nojournal -nolog -source pkg_delay.tcl -tclargs <out.csv>
create_project -in_memory -part xc7a100tfgg676-2
link_design -part xc7a100tfgg676-2 -name x
write_csv -force [lindex $argv 0]
exit 0
