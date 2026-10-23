#!/usr/bin/env python3
"""Read-only PCB/netlist and connector-accounting gates; no placement import."""
import re
import pcbnew
from load_pcb import parse
from placement import POWER_REFS


def main():
    comps, nets = parse()
    board = pcbnew.LoadBoard('kicad/odin.kicad_pcb')
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    expected = {r: c for r, c in comps.items() if not r.startswith('#')}
    assert set(fps) == set(expected), 'PCB and netlist references differ'
    pin_net = {(r, p): n for n, nodes in nets.items() for r, p in nodes}
    for ref, f in fps.items():
        identity = str(f.GetFPID().GetLibNickname()) + ':' + str(f.GetFPID().GetLibItemName())
        assert identity == expected[ref]['fp'], (ref, identity, expected[ref]['fp'])
        assert f.GetValue() == expected[ref]['value'], ref
        for pad in f.Pads():
            assert pad.GetNetname() == pin_net.get((ref, pad.GetNumber()), ''), (ref, pad.GetNumber())
    assert not any('POWER_SELECTED' in n or n in ('+12V', '+12V_EXT') for n in nets)
    assert not (set(f'J{i}' for i in range(10,19)) | {'J21','J4','J6','U19','U25'}) & fps.keys()
    assert {'J19','J20','J68'} <= fps.keys()
    assert not ({'J66','J67','U28','U29','L10','D12'} & fps.keys())
    aux_fuses = set()
    for ref, slots in (('J3','ABCD'), ('J5','EFGH')):
        pads = sorted(fps[ref].Pads(), key=lambda p:(p.GetPosition().y,p.GetPosition().x))
        assert len(pads) == 64, ref
        for i, slot in enumerate(slots):
            actual = [p.GetNetname() for p in pads[16*i:16*(i+1)]]
            wanted = [f'SLOT{slot}_IO{j}' for j in range(12)]
            wanted[4:4] = ['GND','GND']
            wanted[10:10] = ['GND','GND']
            assert actual == wanted, (ref, slot, actual)
    for ref in ('J7','J8'):
        assert sum(p.GetNetname() == 'GND' for p in fps[ref].Pads()) == 4, ref
        assert sum(p.GetNetname().startswith('unconnected-') for p in fps[ref].Pads()) == 4, ref
    for slot, ref in POWER_REFS.items():
        bynum = {p.GetNumber(): p.GetNetname() for p in fps[ref].Pads()}
        wanted = [f'SLOT_{slot}_PIN_VOLTAGE', 'GND', f'SLOT_{slot}_3V3',
                  'GND', f'SLOT_{slot}_5V', 'GND', f'SLOT_{slot}_AUX']
        assert bynum == {str(i+1): n for i,n in enumerate(wanted)}, (slot,bynum)
        post = list(fps[f'MK{ord(slot)}'].Pads())
        assert len(post) == 1 and post[0].GetNetname() == 'GND', slot
        for i, n in enumerate(wanted):
            if n != 'GND':
                assert (i > 0 and wanted[i-1] == 'GND') or (i < 6 and wanted[i+1] == 'GND'), slot
        aux = f'SLOT_{slot}_AUX'
        fuses = [r for r in fps if r.startswith('F') and not r.startswith('FB')
                 and set(p.GetNetname() for p in fps[r].Pads()) == {'AUX_RAIL',aux}]
        assert len(fuses) == 1, (slot, fuses)
        aux_fuses.update(fuses)
    assert not {'AUX_RAW', 'AUX_REG', 'AUX_SEPIC'} & nets.keys()
    rail_users = {r for r,_ in nets['AUX_RAIL']}
    assert rail_users == {'J68'} | aux_fuses, rail_users
    assert {p.GetNumber():p.GetNetname() for p in fps['J68'].Pads()} == {
        '1':'AUX_RAIL','2':'GND'}
    assert not ({'J60','J61','SH1','SH2','X2','U27','Q1','FB1','FB2'} & fps.keys())
    assert {'J70','J71','J72','U30','X3'} <= fps.keys()
    for ref in ('J71','J72'):
        assert {p.GetNumber() for p in fps[ref].Pads() if p.GetNumber()} == {str(i) for i in range(1,11)}, ref
        assert all(fps[ref].FindPadByNumber(str(i)).GetNetname() == 'GND' for i in (9, 10)), ref
    print(f'PCB/netlist PASS: {len(fps)} references, values, footprint assignments and pad nets')
    print('Ground accounting PASS: 10 sections x (4 signal GND + 3 power GND + 1 GND post); all rail neighbors GND')
    print('AUX topology PASS: no converter, J19/J20 retained, J68 feeds AUX_RAIL and only the ten branch PTCs')
    print('Mechanical placement contract NOT applied or certified by this electrical check')


if __name__ == '__main__':
    main()
