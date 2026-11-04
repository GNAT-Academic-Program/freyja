#!/usr/bin/env python3
"""2D electrostatic cross-section solver: finite differences, numpy conjugate gradient. C with dielectrics and C0 in air give Z0 = 1/(c sqrt(C C0)), Dk_eff = C/C0.
Geometry from ref/jlc08161h-1080a-stackup.json values quoted in ref/pcb-impedance.md. Validated against the saved JLC 100 ohm differential result."""
import numpy as np, json, sys, math
C0=299.792458  # mm/ns
EPS0=8.854e-12
def solve(layers,traces,width=4.0,dx=.0025,dy=.0025,tol=1e-7):
    """layers: list top to bottom of (thickness, er). Walls: conductors at given y indices come via traces of kind 'plane'. traces: dict with planes y, signal rects (x0,x1,y0,y1,volt)."""
    H=sum(t for t,_ in layers); nx=int(width/dx)+1; ny=int(round(H/dy))+1
    er=np.ones((ny-1,nx-1))
    y=0.
    for t,e in layers:
        j0=int(round(y/dy)); j1=int(round((y+t)/dy)); er[j0:j1,:]=e; y+=t
    fix=np.zeros((ny,nx),bool); V=np.zeros((ny,nx))
    for yy in traces['planes']:
        j=int(round(yy/dy)); fix[j,:]=True; V[j,:]=0
    fix[0,:]=True; fix[-1,:]=True; fix[:,0]=True; fix[:,-1]=True
    for (x0,x1,y0,y1,v) in traces['rects']:
        i0,i1=int(round(x0/dx)),int(round(x1/dx)); j0,j1=int(round(y0/dy)),int(round(y1/dy))
        fix[j0:j1+1,i0:i1+1]=True; V[j0:j1+1,i0:i1+1]=v
    def cap(er_):
        # edge conductances from cell permittivity
        ax=np.zeros((ny,nx-1)); ay=np.zeros((ny-1,nx))
        ax[1:-1,:]=.5*(er_[:-1,:]+er_[1:,:])*(dy/dx); ax[0,:]=.5*er_[0,:]*(dy/dx); ax[-1,:]=.5*er_[-1,:]*(dy/dx)
        ay[:,1:-1]=.5*(er_[:,:-1]+er_[:,1:])*(dx/dy); ay[:,0]=.5*er_[:,0]*(dx/dy); ay[:,-1]=.5*er_[:,-1]*(dx/dy)
        def A(u):
            r=np.zeros_like(u)
            fx=ax*(u[:,1:]-u[:,:-1]); fy=ay*(u[1:,:]-u[:-1,:])
            r[:,:-1]-=fx; r[:,1:]+=fx; r[:-1,:]-=fy; r[1:,:]+=fy
            return r
        d=np.zeros((ny,nx)); d[:,:-1]+=ax; d[:,1:]+=ax; d[:-1,:]+=ay; d[1:,:]+=ay; d[d==0]=1
        u=V.copy(); r=-A(u); r[fix]=0; z=r/d; p=z.copy(); rz=(r*z).sum(); r0=np.sqrt((r*r).sum())
        for it in range(40000):
            q=A(p); q[fix]=0; a=rz/(p*q).sum(); u+=a*p; r-=a*q
            if np.sqrt((r*r).sum())<tol*r0: break
            z=r/d; rz2=(r*z).sum(); p=z+(rz2/rz)*p; rz=rz2
        E=(ax*(u[:,1:]-u[:,:-1])**2).sum()+(ay*(u[1:,:]-u[:-1,:])**2).sum()   # energy
        return E
    return cap(er),cap(np.ones_like(er))
def line(E,E0,vs=1.0):
    # C = E*eps0/V^2 per metre for total excitation; Z from C and C0
    c=E*EPS0; c0=E0*EPS0; v=299792458.
    return 1/(v*math.sqrt(c*c0)), E/E0
Tout,Tin=.04064,.0152
def stack_outer(mask=True):
    # mask above trace modelled as a uniform coat: 1.0 mil over the plane side, trace top coat 0.6 mil
    return
def outer(w_top,w_bot,pitch=None,odd=None,H=.0764,er=3.91,mask=(.0254,.01524,3.8),T=Tout,core=(.1,4.36)):
    # from top: air, mask, prepreg H, In1 plane. Modelled as stacked cells with the mask following the trace.
    air=.5; m1,m2,me=mask
    width=4.0; dx=dy=.0025
    tot=air+max(T+m2,m1)+H
    yp=air+max(T+m2,m1)+H   # plane
    nx=int(width/dx)+1; ny=int(round(tot/dy))+1
    er_=np.ones((ny-1,nx-1)); jp=int(round(yp/dy)); jt=int(round((yp-H)/dy))
    er_[jt:jp,:]=er
    # mask: 1 mil over the dielectric, plus a 0.6 mil coat over the trace
    jm=int(round((yp-H-m1)/dy)); er_[jm:jt,:]=me
    cx=width/2; xs=[cx] if pitch is None else [cx-pitch/2,cx+pitch/2]
    jtt=int(round((yp-H-T)/dy)); jc=int(round((yp-H-T-m2)/dy))
    for x in xs:
        i0=int(round((x-w_bot/2-m2)/dx)); i1=int(round((x+w_bot/2+m2)/dx)); er_[jc:jt,i0:i1]=me
    fix=np.zeros((ny,nx),bool); V=np.zeros((ny,nx)); fix[jp:,:]=True; fix[0,:]=True; fix[:,0]=True; fix[:,-1]=True
    for k,x in enumerate(xs):
        v=1. if (pitch is None or k==0 or odd is None) else (-1. if odd else 1.)
        for j in range(jtt,jt+1):
            f=(j-jtt)/max(1,jt-jtt); ww=w_top+(w_bot-w_top)*f
            i0=int(round((x-ww/2)/dx)); i1=int(round((x+ww/2)/dx)); fix[j,i0:i1+1]=True; V[j,i0:i1+1]=v
    return _solve(er_,fix,V,dx,dy,len(xs))
def _solve(er_,fix,V,dx,dy,n,tol=1e-6):
    ny,nx=V.shape
    def en(e):
        ax=np.zeros((ny,nx-1)); ay=np.zeros((ny-1,nx))
        ax[1:-1,:]=.5*(e[:-1,:]+e[1:,:])*(dy/dx); ax[0,:]=.5*e[0,:]*(dy/dx); ax[-1,:]=.5*e[-1,:]*(dy/dx)
        ay[:,1:-1]=.5*(e[:,:-1]+e[:,1:])*(dx/dy); ay[:,0]=.5*e[:,0]*(dx/dy); ay[:,-1]=.5*e[:,-1]*(dx/dy)
        def A(u):
            r=np.zeros_like(u); fx=ax*(u[:,1:]-u[:,:-1]); fy=ay*(u[1:,:]-u[:-1,:])
            r[:,:-1]-=fx; r[:,1:]+=fx; r[:-1,:]-=fy; r[1:,:]+=fy; return r
        d=np.zeros((ny,nx)); d[:,:-1]+=ax; d[:,1:]+=ax; d[:-1,:]+=ay; d[1:,:]+=ay; d[d==0]=1
        u=V.copy(); r=A(u); r=-r; r[fix]=0; z=r/d; p=z.copy(); rz=(r*z).sum(); r0=math.sqrt((r*r).sum())
        for it in range(60000):
            q=A(p); q[fix]=0; a=rz/(p*q).sum(); u+=a*p; r-=a*q
            if math.sqrt((r*r).sum())<tol*r0: break
            z=r/d; rz2=(r*z).sum(); p=z+(rz2/rz)*p; rz=rz2
        return (ax*(u[:,1:]-u[:,:-1])**2).sum()+(ay*(u[1:,:]-u[:-1,:])**2).sum()
    E=en(er_); E0=en(np.ones_like(er_))
    # for n lines at +/-1 volt, charge energy is shared: per-line C = E/n
    Z=1/(299792458.*EPS0*math.sqrt(E/n*E0/n)); return Z,E/E0
def inner(w,w_bot=None,h_near=.1,er_near=4.36,h_far=(.2104,.084,.2104),er_far=(4.40,3.91,4.40),T=Tin,far_plane=True,pitch=None,odd=None,dy=.0025,dx=.0025):
    # near plane above y=0, trace on the core, prepreg stack below to the far plane (or 0.5 mm prepreg and open if far_plane False)
    width=4.0; w_bot=w if w_bot is None else w_bot
    Hf=sum(h_far); tot=h_near+Hf+(0 if far_plane else 1.0)
    ny=int(round(tot/dy))+1; nx=int(width/dx)+1; er_=np.ones((ny-1,nx-1))*er_far[-1]
    jt=int(round(h_near/dy)); er_[:jt,:]=er_near
    y=h_near
    for h,e in zip(h_far,er_far):
        j0=int(round(y/dy)); j1=int(round((y+h)/dy)); er_[j0:j1,:]=e; y+=h
    fix=np.zeros((ny,nx),bool); V=np.zeros((ny,nx)); fix[0,:]=True; fix[-1,:]=True; fix[:,0]=True; fix[:,-1]=True
    cx=width/2; xs=[cx] if pitch is None else [cx-pitch/2,cx+pitch/2]; jb=int(round((h_near+T)/dy))
    for k,x in enumerate(xs):
        v=1. if (pitch is None or k==0 or odd is None) else (-1. if odd else 1.)
        for j in range(jt,jb+1):
            f=(j-jt)/max(1,jb-jt); ww=w_bot+(w-w_bot)*f
            i0=int(round((x-ww/2)/dx)); i1=int(round((x+ww/2)/dx)); fix[j,i0:i1+1]=True; V[j,i0:i1+1]=v
    return _solve(er_,fix,V,dx,dy,len(xs))
if __name__=='__main__':
    out={}
    tp=lambda ek:ek**.5/C0*1000
    # validation: the saved JLC result, 0.0986 mm, gap 0.200, 100.0 ohm differential
    z,ek=outer(.0986-.0127,.0986,pitch=.0986+.2,odd=True); print(f'validation JLC 100 ohm pair: solver Zodd {z:.1f} ohm, Zdiff {2*z:.1f} ohm (JLC 100.0)'); out['validation_Zdiff']=2*z
    rows={}
    for nm,f in (('F.Cu / B.Cu 0.125 mm',lambda **k:outer(.125-.0127,.125,**k)),('In2 / In5 0.125 mm',lambda **k:inner(.125,**k))):
        z,ek=f(); rows[nm]=(z,ek,tp(ek)); print(f'{nm:24s} Z0 {z:5.1f} ohm  Dk_eff {ek:.3f}  {tp(ek):.2f} ps/mm')
    # sensitivity
    for w in (.1125,.1375,.15,.2,.25,.3):
        z,ek=inner(w); print(f'  inner width {w:.4f}: Z0 {z:5.1f}, {tp(ek):.2f} ps/mm')
    z,ek=inner(.125,far_plane=False); print(f'  inner 0.125, far plane absent: Z0 {z:.1f}, {tp(ek):.2f} ps/mm')
    z,ek=inner(.125,h_near=.09); print(f'  inner 0.125, core 0.09: Z0 {z:.1f}'); z,ek=inner(.125,h_near=.11); print(f'  inner 0.125, core 0.11: Z0 {z:.1f}')
    z,ek=inner(.125,er_near=4.36*1.05,er_far=(4.4*1.05,3.91*1.05,4.4*1.05)); print(f'  inner 0.125, Dk +5%: Z0 {z:.1f}, {tp(ek):.2f} ps/mm'); z,ek=inner(.125,er_near=4.36*.95,er_far=(4.4*.95,3.91*.95,4.4*.95)); print(f'  inner 0.125, Dk -5%: Z0 {z:.1f}, {tp(ek):.2f} ps/mm')
    z,ek=outer(.1125-.0127,.1125); print(f'  outer width 0.1125: Z0 {z:.1f}, {tp(ek):.2f}'); z,ek=outer(.1375-.0127,.1375); print(f'  outer width 0.1375: Z0 {z:.1f}, {tp(ek):.2f}')
    z,ek=outer(.125-.0127,.125,mask=(0.0001,0.0001,1.0)); print(f'  outer 0.125, no mask: Z0 {z:.1f}, {tp(ek):.2f} ps/mm')
    # adjacent lane at the routed pitch, 0.3 mm centre to centre: mode delay spread
    for nm,f,p in (('inner',lambda **k:inner(.125,**k),.3),('outer',lambda **k:outer(.125-.0127,.125,**k),.3)):
        ze,ee=f(pitch=p,odd=False); zo,eo=f(pitch=p,odd=True); print(f'  {nm} pair at pitch {p}: even Z {ze:.1f}, {tp(ee):.2f} ps/mm; odd Z {zo:.1f}, {tp(eo):.2f} ps/mm')
    # widths for a 50 ohm-ish inner line, for reference
