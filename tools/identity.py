"""Permanent hardware identity shared by every generated Odin artifact.

Increment HW_VERSION for every distinct fabrication. Never reuse a printed
version for different copper, connectivity, or fitted programmable devices.
"""

PRODUCT = 'ODIN'
HW_VERSION = '0.1.0-proto.1'
FPGA_PART = 'XC7A100T-2FGG676I'
CONTROLLER_PART = 'RP2350B'
