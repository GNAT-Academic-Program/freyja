#!/usr/bin/env python3
"""Drive and slew comparison on the routed PHY_TXC, the net Table 60's 0.75 ns edge limit applies to.

    python3 gateware/rgmii1000/drive.py board.kicad_pcb > gateware/rgmii1000/results/drive.txt

Lumped C at the pin, no PHY clamp model, so overshoot and ringback are upper estimates. Reads a board, never writes one.
"""
import importlib.util
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('route', os.path.join(HERE, 'route.py'))
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
b = pcbnew.LoadBoard(sys.argv[1])
fp = {f.GetReference(): f for f in b.GetFootprints()}
xy = lambda p: (round(p.GetPosition().x / 1e6, 3), round(p.GetPosition().y / 1e6, 3))
n = 'PHY_TXC'
u1 = next(p for p in fp['U1'].Pads() if p.GetNetname() == n)
u30 = next(p for p in fp['U30'].Pads() if p.GetNetname() == n)
secs, _ = r.fl.walk(b, n, xy(u1), xy(u30))
print('driver            corner_load  tr_20_80 tf_20_80  Vmax  Vmin  ringback_r ringback_f  (ns, V; ringback negative re-enters VIH 1.7 / VIL 0.7)')
for slew in 'FS':
    for mA in (4, 8, 12, 16):
        name = f'LVCMOS25_{slew}_{mA}_HR'
        s = r.tx_flight(secs, u1.GetNumber(), name)
        for k, row in s.items():
            print(f"{name:17s} {k:11s} {row['r']['edge_20_80']:8.2f} {row['f']['edge_20_80']:8.2f} {row['r']['vmax']:5.2f} {row['f']['vmin']:5.2f} {row['r']['ringback']:10.2f} {row['f']['ringback']:10.2f}", flush=True)
sys.stdout.flush()
os._exit(0)
