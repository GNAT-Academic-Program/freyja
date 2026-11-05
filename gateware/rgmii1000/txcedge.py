#!/usr/bin/env python3
"""TXC rise and fall time at U30's pin, between 0.2 and 0.8 of U30's own DVDD_RG. Thresholds are never taken from the waveform.

    python3 gateware/rgmii1000/txcedge.py board.kicad_pcb [ohms ...] > gateware/rgmii1000/results/txcedge.txt

Bank 16's VCCO balls and U30 pin 28, DVDD_RG, are the same net, +2V5 (kicad/odin.net), so the two supplies cannot differ by
more than the copper between them. VCCO in each corner is the IBIS [Voltage Range] of the driver: the tables exist at those
voltages only. DVDD_RG is that VCCO plus the DC offset of the routed +2V5, which is the only difference modelled.

Same engine and sweep as txsi.py, plus the IBIS Typ corner: single edge from a settled line, and a 125 MHz square wave,
last of four cycles. Unclamped at U30, lossless lines, a lumped C, all as in txsi.py. Reads a board, never writes one.
"""
import importlib.util
import math
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('txsi', os.path.join(HERE, 'txsi.py'))
x = importlib.util.module_from_spec(spec)
spec.loader.exec_module(x)
r, fl = x.r, x.fl

LIMIT = 0.75    # ns, Table 60, tR and tF, RTL8211F rev 1.7
CORNERS = ((1, 'slow', 1.05, 1.03), (0, 'typ', 1., 1.), (2, 'fast', .95, .97))
# mV from C198.1 on the committed +2V5 copper, 25 C. Bank 16 at 0.12 A and DVDD_RG at 0.02 A are budget estimates; a selector is
# 0.6 A. Load, lowest and highest VCCO ball, U30 pin 28. Findings, "+2V5 distribution routed".
DROPS = (('board only, 0.14 A', 6.7, 8.5, 7.7), ('J19 at 2.5 V, 0.74 A', 12.2, 14.0, 13.2),
         ('J20 at 2.5 V, 0.74 A', 14.0, 21.9, 15.0), ('both selectors, 1.34 A', 19.5, 27.4, 20.5))
# DVDD_RG minus VCCO is the ball's drop minus U30's drop: U30 sits higher than a ball that has dropped more.
HIGHEST = max(hi - u for _, _, hi, u in DROPS) / 1000
TOL = 0.05      # C25105, 0402WGF330JTCE, the J code


def edges(t, v, e, phy):
    """Rise or fall between the fixed levels, by two independent routines: the one txsi.py reports and a plain first crossing."""
    a = x.analyse(t, v, e, phy)
    lo, hi = .2 * phy, .8 * phy
    p, q = (lo, hi) if e == 'r' else (hi, lo)
    return a, (fl.cross(t, v, q, e) - fl.cross(t, v, p, e)) * 1e9


def case(m, c, kd, kz, secs, idx, ohms, Zp, tp, Cl, e, off):
    d = fl.Driver(m, c)
    t, v, _ = fl.sim(d, e, [(Zp, tp)] + r.sections(secs, kz, kd), Cl, tend=8e-9, Rseries=(idx, ohms))
    return d, t, v, edges(t, v, e, d.Vcc + off)


def settled(d, ss, Cl, ohms, e):
    """Level at the end of 60 ns from one edge, and the peak-to-peak of the last 5 ns: the settled level, shown to be settled."""
    t, v, _ = fl.sim(d, e, ss, Cl, tend=60e-9, Rseries=ohms)
    tail = v[t >= t[-1] - 5e-9]
    return float(tail.mean()), float(tail.max() - tail.min())


def periodic(d, ss, Cl, rs, phy):
    """One period of a settled 125 MHz clock, in txsi.pin_windows, with the same half period a cycle earlier as a check."""
    out = {}
    t, v, win = x.pin_windows(d, ss, Cl, rs)
    for e, (i, j) in win.items():
        a = x.analyse(t[i], v[i], e, phy)
        out[e] = dict(a, before=float(v[i][-1]), peak=float(v[i].max() if e == 'r' else v[i].min()), drift=float(abs(v[i][:j.sum()] - v[j][:i.sum()]).max()))
    return out


def main():
    b = pcbnew.LoadBoard(sys.argv[1])
    values = [float(a) for a in sys.argv[2:]] or [33.]
    fp = {f.GetReference(): f for f in b.GetFootprints()}
    secs, idx, placed, ref, near, bp, pp = r.leg(b, fp, 'PHY_TXC')
    Lp, Cp = fl.pkg()
    L, C = Lp[bp.GetNumber()], Cp[bp.GetNumber()]
    Zp, tp = math.sqrt(L / C), math.sqrt(L * C)
    m = fl.model(x.DRIVER)

    fb, top, bot = (.588, .6, .612), 100e3, 31.6e3
    print('Supplies')
    print(f'  U13 setpoint at C198.1: {fb[1] * (1 + top / bot):.4f} V; bound with VFB 0.588-0.612 V (SLVSDG1C) and 1 % R59, R60: '
          f'{fb[0] * (1 + top * .99 / (bot * 1.01)):.3f} to {fb[2] * (1 + top * 1.01 / (bot * .99)):.3f} V')
    print('  Realtek rev 1.7 Table 55 and 58, 2.5 V RGMII supply: 2.25 to 2.75 V. Slow and Fast below are 2.375 and 2.625 V, IBIS.')
    print('  DC, mV below C198.1, and DVDD_RG minus VCCO:')
    for name, lo, hi, u in DROPS:
        print(f'    {name:24s} VCCO balls {lo:5.1f} to {hi:5.1f}, U30.28 {u:5.1f}, offset {lo - u:+.1f} to {hi - u:+.1f}')
    print(f'  TXC: ball {bp.GetNumber()}, {ref} centre {near:.2f} mm from pin {pp.GetNumber()}. No DC load on PHY_TXC or PHY_TXC_U30, so nothing but the driver sets the settled levels.')
    print()

    for ohms in values:
        print(f'== {ohms:g} ohm in {ref}. Limit {LIMIT} ns. One edge from a settled line, 8 ns window.')
        print('settled: mean of the last 5 ns of a 60 ns window, with its peak-to-peak in brackets.')
        print('corner load | VCCO   DVDD_RG  0.2x   0.8x  | settled hi (pp)     lo (pp)      | rise_ns (check) fall_ns (check) | margin_ps')
        worst = None
        for c, name, kd, kz in CORNERS:
            for Cl in r.CASES:
                for off in (0., HIGHEST):
                    d, tr, vr, (ar, cr) = case(m, c, kd, kz, secs, idx, ohms, Zp, tp, Cl, 'r', off)
                    d, tf, vf, (af, cf) = case(m, c, kd, kz, secs, idx, ohms, Zp, tp, Cl, 'f', off)
                    phy = d.Vcc + off
                    ss = [(Zp, tp)] + r.sections(secs, kz, kd)
                    hi, hp = settled(d, ss, Cl, (idx, ohms), 'r')
                    lo, lp = settled(d, ss, Cl, (idx, ohms), 'f')
                    margin = (LIMIT - max(ar['edge'], af['edge'])) * 1000
                    print(f"{name:4s} {int(Cl * 1e12)}pF | {d.Vcc:.3f}  {phy:.4f}  {.2 * phy:.4f} {.8 * phy:.4f} | {hi:6.3f} ({hp:.3f}) {lo:6.3f} ({lp:.3f}) | "
                          f"{ar['edge']:.3f} ({cr:.3f})   {af['edge']:.3f} ({cf:.3f})   | {margin:+.1f}", flush=True)
                    if worst is None or margin < worst[0]:
                        worst = (margin, name, Cl, off)
        print(f'Least margin: {worst[0]:+.1f} ps, {worst[1]}, {int(worst[2] * 1e12)} pF, DVDD_RG = VCCO {worst[3] * 1000:+.1f} mV')
        print()

        print(f'== {ohms:g} ohm. 125 MHz clock, a settled cycle, windows cut at the pin. end: level 1 ns before the next edge crosses 1.25 V; not a settled level.')
        print('corner load | DVDD_RG | rise_ns fall_ns | inside VIH VIL, V | when, ns after first crossing | long, ns | settled, ns after 1.25 V | end hi lo | peaks | cycle drift V | 1.25V recross')
        for c, name, kd, kz in CORNERS:
            d = fl.Driver(m, c)
            ss = [(Zp, tp)] + r.sections(secs, kz, kd)
            phy = d.Vcc + HIGHEST
            for Cl in r.CASES:
                p = periodic(d, ss, Cl, (idx, ohms), phy)
                a, f = p['r'], p['f']
                print(f"{name:4s} {int(Cl * 1e12)}pF | {phy:.4f} | {a['edge']:.3f}   {f['edge']:.3f} | {a['depth']:.3f} {f['depth']:.3f} | {a['when']:.3f} {f['when']:.3f} | {a['dur']:.3f} {f['dur']:.3f} | "
                      f"{a['settle_mid']:.3f} {f['settle_mid']:.3f} | {a['before']:.3f} {f['before']:.3f} | {a['peak']:.2f} {f['peak']:.2f} | {max(a['drift'], f['drift']):.3f} | {a['recross']} {f['recross']}", flush=True)
        print()

        # What the margin depends on, Slow corner and rising edge, the limiting case.
        print(f'== {ohms:g} ohm. Sensitivity of the limiting case, Slow, 5 pF.')
        c, name, kd, kz = CORNERS[0]
        print('R ohm   DVDD_RG-VCCO mV | one edge: rise_ns fall_ns margin_ps | 125 MHz: rise_ns fall_ns margin_ps')
        d = fl.Driver(m, c)
        for R, off in ((ohms, 0.), (ohms, HIGHEST), (ohms * 1.01, HIGHEST), (ohms * (1 + TOL), 0.), (ohms * (1 + TOL), HIGHEST)):
            _, _, _, (ar, _) = case(m, c, kd, kz, secs, idx, R, Zp, tp, 5e-12, 'r', off)
            _, _, _, (af, _) = case(m, c, kd, kz, secs, idx, R, Zp, tp, 5e-12, 'f', off)
            p = periodic(d, [(Zp, tp)] + r.sections(secs, kz, kd), 5e-12, (idx, R), d.Vcc + off)
            print(f"{R:6.2f}  {off * 1000:+6.1f}          | {ar['edge']:.4f} {af['edge']:.4f} {(LIMIT - max(ar['edge'], af['edge'])) * 1000:+5.1f}    "
                  f"| {p['r']['edge']:.4f} {p['f']['edge']:.4f} {(LIMIT - max(p['r']['edge'], p['f']['edge'])) * 1000:+5.1f}", flush=True)

        def bisect(fn, lo, hi):
            for _ in range(14):
                mid = (lo + hi) / 2
                lo, hi = (mid, hi) if fn(mid) < LIMIT else (lo, mid)
            return (lo + hi) / 2

        worst_edge = lambda R, Cl, off: max(case(m, c, kd, kz, secs, idx, R, Zp, tp, Cl, e, off)[3][0]['edge'] for e in 'rf')
        print(f"Load reaching {LIMIT} ns: {bisect(lambda q: worst_edge(ohms, q * 1e-12, 0.), 2, 12):.2f} pF at nominal R, equal supplies; "
              f"{bisect(lambda q: worst_edge(ohms * (1 + TOL), q * 1e-12, HIGHEST), 2, 12):.2f} pF at R +5 %, offset {HIGHEST * 1000:+.1f} mV")
        print(f"DVDD_RG above VCCO reaching {LIMIT} ns at 5 pF, nominal R: {bisect(lambda q: worst_edge(ohms, 5e-12, q / 1000), 0, 200):.1f} mV")
        print()
    print('Fixed 0.5 and 2.0 V against this Slow corner would need DVDD_RG 125 mV above VCCO on one net: not a state of this board, so not evaluated.')
    sys.stdout.flush()


if __name__ == '__main__':
    main()
    sys.stdout.flush()
    os._exit(0)
