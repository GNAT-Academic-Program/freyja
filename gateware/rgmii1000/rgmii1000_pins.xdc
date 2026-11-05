# Excerpt of ref/freya.xdc for this fixture only. A real design reads ref/freya.xdc instead.
set_property -dict {PACKAGE_PIN D19 IOSTANDARD LVCMOS25} [get_ports {PHY_RXC}]   ;# bank 16 IO_L13P_T2_MRCC_16
set_property -dict {PACKAGE_PIN C19 IOSTANDARD LVCMOS25} [get_ports {PHY_RXD0}]   ;# bank 16 IO_L13N_T2_MRCC_16
set_property -dict {PACKAGE_PIN H17 IOSTANDARD LVCMOS25} [get_ports {PHY_RXD1}]   ;# bank 16 IO_0_16
set_property -dict {PACKAGE_PIN E22 IOSTANDARD LVCMOS25} [get_ports {PHY_RXD2}]   ;# bank 16 IO_25_16
set_property -dict {PACKAGE_PIN B19 IOSTANDARD LVCMOS25} [get_ports {PHY_RXD3}]   ;# bank 16 IO_L10P_T1_16
set_property -dict {PACKAGE_PIN A19 IOSTANDARD LVCMOS25} [get_ports {PHY_RX_CTL}]   ;# bank 16 IO_L10N_T1_16
set_property -dict {PACKAGE_PIN C24 IOSTANDARD LVCMOS25} [get_ports {PHY_TXC}]   ;# bank 16 IO_L23P_T3_16
set_property -dict {PACKAGE_PIN B24 IOSTANDARD LVCMOS25} [get_ports {PHY_TXD0}]   ;# bank 16 IO_L23N_T3_16
set_property -dict {PACKAGE_PIN C22 IOSTANDARD LVCMOS25} [get_ports {PHY_TXD1}]   ;# bank 16 IO_L19P_T3_16
set_property -dict {PACKAGE_PIN C23 IOSTANDARD LVCMOS25} [get_ports {PHY_TXD2}]   ;# bank 16 IO_L19N_T3_VREF_16
set_property -dict {PACKAGE_PIN C21 IOSTANDARD LVCMOS25} [get_ports {PHY_TXD3}]   ;# bank 16 IO_L16P_T2_16
set_property -dict {PACKAGE_PIN B21 IOSTANDARD LVCMOS25} [get_ports {PHY_TX_CTL}]   ;# bank 16 IO_L16N_T2_16
set_property -dict {PACKAGE_PIN M21 IOSTANDARD LVCMOS33} [get_ports {SYS_CLK}]   ;# bank 14 IO_L12P_T1_MRCC_14
