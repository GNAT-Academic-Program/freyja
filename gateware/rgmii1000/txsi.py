#!/usr/bin/env python3
"""TX edges, ringing and settling on the laid-out copper, at U30's pins, through R208-R213.

    python3 gateware/rgmii1000/txsi.py board.kicad_pcb > gateware/rgmii1000/results/txsi.txt

Same sweep as route.py: AMD IBIS 8 mA fast, Slow and Fast corners, 2 and 5 pF, both edges. Levels are Realtek rev 1.7
Table 58 for a 2.5 V pad, VIH 1.7 V and VIL 0.7 V; edge limits are Table 60's tR and tF, 20 % to 80 %, 0.75 ns, which
the table gives only for TXC and RXC. The edge column is 0.2 and 0.8 of the corner's VCC, which is U30's DVDD_RG to within
the +2V5 DC offset; txcedge.py resolves that and is the figure to quote. The nominal column, fixed 0.5 and 2.0 V, mixes a
2.375 V signal with 2.5 V thresholds in the Slow corner, which one net cannot do; it is kept only to match earlier records.

Two stimuli. One edge from a settled line, the case route.py and the timing use. And a 125 MHz square wave, 4 ns per
level, measuring a settled cycle: this catches residue left by the previous edge. Its windows are cut at the pin, not at
the driver, because an edge takes about 1.8 ns to reach the pin and a window cut at the driver loses the end of the half
period, where the ring-back is.

Unclamped at U30, lossless lines, a lumped C: U30's clamps and capacitance are unpublished, so voltages here are model
results, not pin predictions. Reads a board, never writes one.
"""
import importlib.util
import math
import os
import sys

import numpy as np
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('route', os.path.join(HERE, 'route.py'))
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
fl = r.fl
NETS = ['PHY_TXC', 'PHY_TX_CTL', 'PHY_TXD0', 'PHY_TXD1', 'PHY_TXD2', 'PHY_TXD3']
DRIVER = 'LVCMOS25_F_8_HR'
VIH, VIL, VMID = 1.7, 0.7, 1.25
CORNERS = ((1, 'slow', 1.05, 1.03), (2, 'fast', .95, .97))
HALF = 4e-9


def span(t, v, lo, hi, e):
    """First arrival at the far level, and the last departure from the near level before it, so residue at the start of a
    window cannot stretch the edge."""
    far = hi if e == 'r' else lo
    near = lo if e == 'r' else hi
    c = fl.cross(t, v, far, e)
    if c is None:
        return None, None
    i = int(np.searchsorted(t, c))
    w = np.where(v[:i] <= near)[0] if e == 'r' else np.where(v[:i] >= near)[0]
    if not len(w) or w[-1] + 1 >= len(t):
        return None, c
    k = w[-1]
    return t[k] + (near - v[k]) / (v[k + 1] - v[k]) * (t[k + 1] - t[k]), c


def analyse(t, v, e, vcc):
    """Everything is measured from a settled start through the first arrival at the far threshold."""
    hi, lo = (VIH, VIL) if e == 'r' else (VIL, VIH)
    t_hi = fl.cross(t, v, hi, e)
    i_hi = int(np.searchsorted(t, t_hi))
    ok = (v >= VIH) if e == 'r' else (v <= VIL)
    after = v[i_hi:]
    tail = t[i_hi:]
    bad = ~ok[i_hi:]
    # runs of samples back inside the undefined band after the first crossing
    runs = []
    k = 0
    while k < len(bad):
        if bad[k]:
            j = k
            while j + 1 < len(bad) and bad[j + 1]:
                j += 1
            runs.append((tail[k], tail[j], (after[k:j + 1].min() if e == 'r' else after[k:j + 1].max())))
            k = j + 1
        else:
            k += 1
    depth = max(((VIH - x) if e == 'r' else (x - VIL) for _, _, x in runs), default=0.)
    # reversal on the way through the band, before the first arrival: the case ringback does not see
    i_lo = np.where((v <= VIL) if e == 'r' else (v >= VIH))[0]
    i_lo = i_lo[i_lo < i_hi]
    seg = v[(i_lo[-1] if len(i_lo) else 0):i_hi + 1]
    rev = float((np.maximum.accumulate(seg) - seg).max() if e == 'r' else (seg - np.minimum.accumulate(seg)).max())
    a, c = span(t, v, .2 * vcc, .8 * vcc, e)
    a2, c2 = span(t, v, .5, 2., e)
    mid = fl.cross(t, v, VMID, e)
    i_mid = int(np.searchsorted(t, mid))
    recross = bool((v[i_mid:] < VMID).any() if e == 'r' else (v[i_mid:] > VMID).any())
    return dict(edge=(c - a) * 1e9 if a is not None else float('nan'), edge_nom=(c2 - a2) * 1e9 if c2 is not None and a2 is not None else float('nan'),
                band=(t_hi - fl.cross(t, v, lo, e)) * 1e9, mid=mid, vmax=float(v.max()), vmin=float(v.min()),
                depth=depth, reentry=len(runs), when=(runs[0][0] - t_hi) * 1e9 if runs else 0.,
                dur=sum(b - a_ for a_, b, _ in runs) * 1e9, last=(runs[-1][1] - t_hi) * 1e9 if runs else 0.,
                settle_mid=((runs[-1][1] if runs else t_hi) - mid) * 1e9, rev=rev, recross=recross)


def square(d, ss, Cl, rs, cycles=4, dt=2e-12):
    """A copy of flight.sim driven by a square wave: first edge rising, then the IBIS tables alternate."""
    N = len(ss)
    st = [max(1, int(round(td / dt))) for _, td in ss]
    Z = [z for z, _ in ss]
    steps = int((2 * cycles * HALF + .5e-9) / dt)
    fw = [np.zeros(n) for n in st]
    bw = [np.zeros(n) for n in st]
    Vd = Vl = 0.
    out = np.zeros(steps)
    t0 = .5e-9
    for n in range(steps):
        tt = n * dt - t0
        if tt < 0:
            ku, kd = d.koft('r', 0)
        else:
            m = int(tt // HALF)
            ku, kd = d.koft('r' if m % 2 == 0 else 'f', tt - m * HALF)
        af = [fw[i][n % st[i]] for i in range(N)]
        ab = [bw[i][n % st[i]] for i in range(N)]
        V = Vd
        for _ in range(3):
            I = ku * d.isrc(V) - kd * d.isink(V) - d.iclamp(V) + (2 * ab[0] - V) / Z[0] - d.Cc * (V - Vd) / dt
            h = 1e-3
            I2 = ku * d.isrc(V + h) - kd * d.isink(V + h) - d.iclamp(V + h) + (2 * ab[0] - V - h) / Z[0] - d.Cc * (V + h - Vd) / dt
            g = (I2 - I) / h
            if g == 0:
                break
            V -= I / g
        Vd = V
        nb = [0.] * N
        nf = [0.] * N
        nf[0] = V - ab[0]
        for i in range(N - 1):
            if i == rs[0]:
                R = rs[1]
                Is = (2 * af[i] - 2 * ab[i + 1]) / (Z[i] + R + Z[i + 1])
                nb[i] = 2 * af[i] - Is * Z[i] - af[i]
                nf[i + 1] = 2 * ab[i + 1] + Is * Z[i + 1] - ab[i + 1]
            else:
                Vj = 2 * (af[i] / Z[i] + ab[i + 1] / Z[i + 1]) / (1 / Z[i] + 1 / Z[i + 1])
                nb[i] = Vj - af[i]
                nf[i + 1] = Vj - ab[i + 1]
        Ca = Cl / dt
        Vl = (2 * af[-1] / Z[-1] + Ca * Vl) / (1 / Z[-1] + Ca)
        nb[-1] = Vl - af[-1]
        for i in range(N):
            fw[i][n % st[i]] = nf[i]
            bw[i][n % st[i]] = nb[i]
        out[n] = Vl
    return np.arange(steps) * dt - t0, out


def pin_windows(d, ss, Cl, rs, cycles=6):
    """A square wave and, per edge, a half period as the pin sees it: from 1 ns before this edge's 1.25 V crossing to 1 ns
    before the next edge's, and the same half period one cycle earlier. The last cycle is kept out, so nothing is cut by the end
    of the simulation."""
    t, v = square(d, ss, Cl, rs, cycles=cycles)
    w = 2 * (cycles - 2) * HALF
    win = {}
    for e, k in (('r', 0), ('f', 1)):
        ti, vi, _ = fl.sim(d, e, ss, Cl, tend=8e-9, Rseries=rs)
        s = w + k * HALF + fl.cross(ti, vi, VMID, e) - 1e-9
        win[e] = ((t >= s) & (t < s + HALF), (t >= s - 2 * HALF) & (t < s - HALF))
    return t, v, win


def main():
    b = pcbnew.LoadBoard(sys.argv[1])
    fp = {f.GetReference(): f for f in b.GetFootprints()}
    Lp, Cp = fl.pkg()
    m = fl.model(DRIVER)
    print(f'{DRIVER}. Single edge from a settled line, 8 ns window. Voltages unclamped at U30.')
    print('edge: 0.2-0.8 of the corner\'s own VCC, see txcedge.py / fixed 0.5-2.0 V, not a state of this board. band: VIL to VIH. depth: deepest return inside VIH or VIL after the first crossing.')
    print('dur: total time back inside the band. settle: last moment outside the valid level, after the 1.25 V crossing. rev: reversal on the way through the band.')
    print('net         R     from pin mm | corner load edge | edge_ns  nominal  band_ns   Vmax   Vmin  depth_V  when_ns  dur_ns  settle_ns  rev_V  1.25V_recross')
    worst = {}
    per = {}
    for n in NETS:
        secs, idx, ohms, ref, near, bp, pp = r.leg(b, fp, n)
        L, C = Lp[bp.GetNumber()], Cp[bp.GetNumber()]
        Zp, tp = math.sqrt(L / C), math.sqrt(L * C)
        rs = (idx, ohms)
        rows = []
        for c, name, kd, kz in CORNERS:
            d = fl.Driver(m, c)
            ss = [(Zp, tp)] + r.sections(secs, kz, kd)
            for Cl in r.CASES:
                ref_t = {e: fl.refcross(d, e) for e in 'rf'}
                for e in 'rf':
                    t, v, _ = fl.sim(d, e, ss, Cl, tend=8e-9, Rseries=rs)
                    a = analyse(t, v, e, d.Vcc)
                    a.update(net=n, corner=name, Cl=Cl, e=e, flight=(a['mid'] - ref_t[e]) * 1e9)
                    rows.append(a)
                    print(f"{n:11s} {ref} {ohms:3.0f} {near:5.2f} | {name:4s} {int(Cl*1e12)}pF {e} | {a['edge']:6.3f} {a['edge_nom']:7.3f} {a['band']:7.3f}  {a['vmax']:5.2f}  {a['vmin']:5.2f}  "
                          f"{a['depth']:6.3f}  {a['when']:6.3f}  {a['dur']:6.3f}  {a['settle_mid']:7.3f}  {a['rev']:5.3f}  {a['recross']}", flush=True)
        worst[n] = rows
        # square wave
        pr = []
        for c, name, kd, kz in CORNERS:
            d = fl.Driver(m, c)
            ss = [(Zp, tp)] + r.sections(secs, kz, kd)
            for Cl in r.CASES:
                t, v, win = pin_windows(d, ss, Cl, rs)
                w0, w1 = 2 * 4 * HALF, 2 * 4 * HALF + HALF
                ir, ifl = win['r'][0], win['f'][0]
                ar = analyse(t[ir], v[ir], 'r', d.Vcc)
                af = analyse(t[ifl], v[ifl], 'f', d.Vcc)
                # delay of the same edge in the square wave against the isolated edge
                tr, vr, _ = fl.sim(d, 'r', ss, Cl, tend=8e-9, Rseries=rs)
                tf, vf, _ = fl.sim(d, 'f', ss, Cl, tend=8e-9, Rseries=rs)
                dr = (ar['mid'] - w0 - fl.cross(tr, vr, VMID, 'r')) * 1e9
                df = (af['mid'] - w1 - fl.cross(tf, vf, VMID, 'f')) * 1e9
                duty = (af['mid'] - ar['mid']) / (2 * HALF) * 100
                pr.append(dict(corner=name, Cl=Cl, ar=ar, af=af, dr=dr, df=df, duty=duty))
        per[n] = pr
    print()
    print('Square wave, 125 MHz, a settled cycle, half periods cut at the pin. dflight: 1.25 V crossing against the isolated edge. settle: as above; the next edge crosses 1.25 V 4 ns after this one.')
    print('net         corner load | edge_r edge_f | depth_r depth_f | settle_r settle_f | dflight_r dflight_f | duty_%  | Vmax Vmin')
    for n in NETS:
        for p in per[n]:
            a, c = p['ar'], p['af']
            print(f"{n:11s} {p['corner']:4s} {int(p['Cl']*1e12)}pF | {a['edge']:.3f} {c['edge']:.3f} | {a['depth']:.3f} {c['depth']:.3f} | {a['settle_mid']:.3f} {c['settle_mid']:.3f} | "
                  f"{p['dr']:+.4f} {p['df']:+.4f} | {p['duty']:.2f} | {max(a['vmax'],c['vmax']):.2f} {min(a['vmin'],c['vmin']):.2f}", flush=True)
    print()
    print('Worst per net, single edge')
    for n in NETS:
        w = worst[n]
        print(f"{n:11s} edge {max(x['edge'] for x in w):.3f} nominal {max(x['edge_nom'] for x in w):.3f}  peak {max(x['vmax'] for x in w):.2f} {min(x['vmin'] for x in w):.2f}  "
              f"depth {max(x['depth'] for x in w):.3f}  settle {max(x['settle_mid'] for x in w):.3f}  rev {max(x['rev'] for x in w):.3f}  recross {sum(x['recross'] for x in w)}")
    t = worst['PHY_TXC']
    x = max(t, key=lambda q: q['depth'])
    print(f"Deepest TXC return: {x['corner']} {int(x['Cl']*1e12)} pF, {'rising' if x['e']=='r' else 'falling'}, {x['depth']:.3f} V inside {'VIH 1.7' if x['e']=='r' else 'VIL 0.7'}, "
          f"{x['when']:.3f} ns after the first crossing, {x['dur']:.3f} ns long, settled {x['settle_mid']:.3f} ns after the 1.25 V crossing")
    sys.stdout.flush()


if __name__ == '__main__':
    main()
    sys.stdout.flush()
    os._exit(0)
