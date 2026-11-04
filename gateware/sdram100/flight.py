#!/usr/bin/env python3
"""Board flight time per SDRAM net: AMD IBIS driver (two-waveform switching), package RLC, the net's own routed sections, U32 input C.
Flight = crossing of 1.4 V at U32 (datasheet timing reference) minus crossing of Vmeas into Rref/Cref (IBIS test load, the condition of the tool's OBUF delay).
Models are read from the installed Vivado, never copied; see README.md. DRIVE=8 python3 flight.py board.kicad_pcb data/flight_8.json"""
import sys,re,math,json,collections
import numpy as np, pcbnew
import os
VIV=os.environ.get('XILINX_VIVADO','/tools/Xilinx/2026.1/Vivado'); IB=VIV+'/data/parts/xilinx/artix7/public/ibis/artix7.ibs'; PK=VIV+'/data/parts/xilinx/artix7/public/ibis/pkg/xc7a100t_fgg676.pkg'
UNIT={'m':1e-3,'u':1e-6,'n':1e-9,'p':1e-12,'f':1e-15,'k':1e3,'M':1e6}
def val(s):
    m=re.match(r'^([-+\d.eE]+)([munpfkM]?)',s)
    return float(m.group(1))*UNIT.get(m.group(2),1)
def model(name):
    txt=open(IB).read(); i=txt.index('[Model]  '+name); j=txt.index('[Model]',i+10); M=txt[i:j]; out={'wave':{'r':[],'f':[]}}
    out['C_comp']=[val(x) for x in re.search(r'C_comp\s+(\S+)\s+(\S+)\s+(\S+)',M).groups()]
    out['Vcc']=[val(x) for x in re.search(r'\[Voltage Range\]\s+(\S+)\s+(\S+)\s+(\S+)',M).groups()]
    out['Vmeas']=val(re.search(r'Vmeas\s*=\s*(\S+)',M).group(1))
    def tab(kw,end):
        a=M.index(kw); b=M.index(end,a+1); rows=[]
        for ln in M[a:b].splitlines()[1:]:
            ln=ln.strip()
            if not ln or ln[0] in'|[': continue
            p=ln.split()
            if len(p)<4 or p[1]=='NA' : continue
            try: rows.append([val(x) for x in p[:4]])
            except Exception: pass
        return np.array(rows)
    out['pd']=tab('[Pulldown]','[Pullup]'); out['pu']=tab('[Pullup]','[GND_clamp]'); out['gc']=tab('[GND_clamp]','[POWER_clamp]'); out['pc']=tab('[POWER_clamp]','[Ramp]')
    for m in re.finditer(r'\[(Rising|Falling) Waveform\][^\n]*\n(.*?)(?=\n\[|\Z)',M,re.S):
        k='r' if m.group(1)=='Rising' else 'f'; body=m.group(2); R=val(re.search(r'R_fixture\s*=\s*(\S+)',body).group(1)); V=val(re.search(r'V_fixture\s*=\s*(\S+)',body).group(1))
        rows=[]
        for ln in body.splitlines():
            ln=ln.strip()
            if not ln or ln[0]=='|' or '=' in ln: continue
            p=ln.split()
            if len(p)>=4:
                try: rows.append([val(x) for x in p[:4]])
                except Exception: pass
        out['wave'][k].append((R,V,np.array(rows)))
    return out
def pkg():
    L=collections.defaultdict(float); C=collections.defaultdict(float); t=open(PK).read()
    def sect(a,b):
        i=t.index(a); j=t.index(b,i+5) if b else len(t); return t[i:j]
    for name,store,a,b in (('L',L,'[Inductance Matrix]','[Capacitance Matrix]'),('C',C,'[Capacitance Matrix]','[End')):
        cur=None
        for ln in sect(a,b).splitlines():
            ln=ln.strip()
            if ln.startswith('[Row]'): cur=ln.split()[1]; first=True; continue
            p=ln.split()
            if cur and len(p)==2 and p[0]==cur:
                try: store[cur]=float(p[1])
                except Exception: pass
    return L,C
class Driver:
    """corner: 0 typ, 1 min (slow), 2 max (fast)."""
    def __init__(s,m,corner):
        s.c=corner; col=corner+1; s.Vcc=m['Vcc'][corner]; s.Cc=m['C_comp'][corner]; s.Vmeas=m['Vmeas']
        s.pd=(m['pd'][:,0],m['pd'][:,col]); s.pu=(m['pu'][:,0],m['pu'][:,col]); s.gc=(m['gc'][:,0],m['gc'][:,col]); s.pc=(m['pc'][:,0],m['pc'][:,col]); s.k={}
        for e in 'rf':
            w=m['wave'][e]; t=w[0][2][:,0]; V=[np.interp(t,x[2][:,0],x[2][:,col]) for x in w]; Rf=[x[0] for x in w]; Vf=[(s.Vcc if x[1]>0 else 0.) for x in w]; dt=t[1]-t[0]
            ku=np.zeros_like(t); kd=np.zeros_like(t)
            dv=[np.gradient(v,t) for v in V]
            for n in range(len(t)):
                A=np.zeros((2,2)); b=np.zeros(2)
                for j in (0,1):
                    v=V[j][n]; A[j,0]=s.isrc(v); A[j,1]=-s.isink(v); b[j]=(v-Vf[j])/Rf[j]+s.Cc*dv[j][n]+s.iclamp(v)
                try: x=np.linalg.solve(A,b)
                except Exception: x=np.array([0,0])
                ku[n],kd[n]=np.clip(x,0,1.3)
            s.k[e]=(t,ku,kd)
    def isrc(s,v):
        return -np.interp(s.Vcc-v,*s.pu)
    def isink(s,v): return np.interp(v,*s.pd)
    def iclamp(s,v): # current into the pad node's clamps
        return np.interp(v,*s.gc)+np.interp(s.Vcc-v,*s.pc)
    def koft(s,e,t):
        T,ku,kd=s.k[e]; return np.interp(t,T,ku),np.interp(t,T,kd)
def sim(d,e,sections,Cload,dt=2e-12,tend=9e-9,Rseries=None):
    """sections: list of (Z,td s). Series resistor R after section index Rseries[0]. Lossless. Returns time, load V, die V."""
    N=len(sections); st=[max(1,int(round(td/dt))) for Z,td in sections]; Z=[z for z,_ in sections]; steps=int(tend/dt)
    v0=0. if e=='r' else d.Vcc
    fw=[np.full(n,v0/2.) for n in st]; bw=[np.full(n,v0/2.) for n in st]  # waves: fw travels to the load
    ptrf=[0]*N; Vd=v0; Vl=v0; out=np.zeros(steps); die=np.zeros(steps); t0=.5e-9
    for n in range(steps):
        t=n*dt-t0+0.0
        ku,kd=d.koft(e,max(t,0)) if t>=0 else d.koft(e,0)
        # arriving waves
        arr_f=[fw[i][(n)%st[i]] for i in range(N)]; arr_b=[bw[i][(n)%st[i]] for i in range(N)]
        # driver node with line 0: (2*arr_b0 - V)/Z0 + Ibuf(V) = Cc dV/dt, Newton
        V=Vd
        for _ in range(3):
            I=ku*d.isrc(V)-kd*d.isink(V)-d.iclamp(V)+(2*arr_b[0]-V)/Z[0]-d.Cc*(V-Vd)/dt
            h=1e-3; I2=ku*d.isrc(V+h)-kd*d.isink(V+h)-d.iclamp(V+h)+(2*arr_b[0]-V-h)/Z[0]-d.Cc*(V+h-Vd)/dt
            g=(I2-I)/h
            if g==0: break
            V-=I/g
        Vd=V; new_fw0=V-arr_b[0]
        new_bw=[0.]*N; new_fw=[0.]*N; new_fw[0]=new_fw0
        for i in range(N-1):
            if Rseries is not None and i==Rseries[0]:
                R=Rseries[1]; Is=(2*arr_f[i]-2*arr_b[i+1])/(Z[i]+R+Z[i+1]); Vl_=2*arr_f[i]-Is*Z[i]; Vr_=2*arr_b[i+1]+Is*Z[i+1]
                new_bw[i]=Vl_-arr_f[i]; new_fw[i+1]=Vr_-arr_b[i+1]
            else:
                Vj=2*(arr_f[i]/Z[i]+arr_b[i+1]/Z[i+1])/(1/Z[i]+1/Z[i+1]); new_bw[i]=Vj-arr_f[i]; new_fw[i+1]=Vj-arr_b[i+1]
        Ca=Cload/dt; Vl=(2*arr_f[-1]/Z[-1]+Ca*Vl)/(1/Z[-1]+Ca); new_bw[-1]=Vl-arr_f[-1]
        for i in range(N): fw[i][n%st[i]]=new_fw[i]; bw[i][n%st[i]]=new_bw[i]
        out[n]=Vl; die[n]=Vd
    return (np.arange(steps)*dt-t0),out,die
def cross(t,v,lv,e):
    if e=='r': idx=np.where(v>=lv)[0]
    else: idx=np.where(v<=lv)[0]
    if len(idx)==0: return None
    i=idx[0]
    if i==0: return t[0]
    return t[i-1]+(lv-v[i-1])/(v[i]-v[i-1])*(t[i]-t[i-1])
def refcross(d,e):
    t=np.arange(0,14e-9,2e-12); V=0. if e=='r' else d.Vcc; out=[]
    # open test load: Rref 1 Mohm, Cref 0, so the die node with Cc only
    for tt in t:
        ku,kd=d.koft(e,tt)
        for _ in range(6):
            f=ku*d.isrc(V)-kd*d.isink(V)-d.iclamp(V)-V/1e6-d.Cc*(V-out[-1] if out else 0)/2e-12
            h=1e-3; f2=ku*d.isrc(V+h)-kd*d.isink(V+h)-d.iclamp(V+h)-(V+h)/1e6-d.Cc*(V+h-(out[-1] if out else V))/2e-12
            g=(f2-f)/h
            if g==0: break
            V-=f/g
        out.append(V)
    return cross(t,np.array(out),d.Vmeas,e)
# ---- routed sections
def walk(b,net,startxy,endxy):
    tr=[t for t in b.GetTracks() if t.GetNetname()==net]; adj=collections.defaultdict(list); R=lambda p:(round(p.x/1e6,3),round(p.y/1e6,3))
    L={pcbnew.F_Cu:'F.Cu',pcbnew.In2_Cu:'In2',pcbnew.In5_Cu:'In5',pcbnew.B_Cu:'B.Cu'}
    for t in tr:
        if t.GetClass()=='PCB_VIA':
            q=R(t.GetPosition())
            for a in L.values():
                for c in L.values():
                    if a!=c: adj[(a,q)].append(((c,q),0.,'via'))
        else:
            ly=L[t.GetLayer()]; a,c=R(t.GetStart()),R(t.GetEnd()); d=math.dist(a,c); adj[(ly,a)].append(((ly,c),d,ly)); adj[(ly,c)].append(((ly,a),d,ly))
    # pads sit on F.Cu tracks; the run ends at a track end at the pad centre
    start=('F.Cu',startxy); end=('F.Cu',endxy); best={start:0}; prev={}; todo=[start]
    while todo:
        u=todo.pop(0)
        for v,d,k in adj[u]:
            if best[u]+d<best.get(v,1e9): best[v]=best[u]+d; prev[v]=(u,k,d); todo.append(v)
    path=[]; u=end
    if end not in prev: raise SystemExit(f'no walk {net} {startxy} {endxy}')
    while u!=start: p,k,d=prev[u]; path.append((k,d,u,p)); u=p
    path.reverse(); secs=[]
    for k,d,u,p in path:
        if k=='via':
            pair=frozenset((u[0],p[0]))
            secs.append(('via',pair))
        elif secs and secs[-1][0]==k: secs[-1]=(k,secs[-1][1]+d)
        else: secs.append((k,d))
    return secs,best[end]
LY=['F.Cu','In2','In5','B.Cu']; DEPTH={'F.Cu':0,'In2':.23,'In5':1.33,'B.Cu':1.57}
def build(secs,ps,kz=1.,kd=1.):
    out=[]
    for k,d in secs:
        if k=='via':
            a,c=sorted(d,key=lambda x:DEPTH[x]) if len(d)==2 else (list(d)[0],list(d)[0]); bar=abs(DEPTH[c]-DEPTH[a])
            out.append((60.,max(1e-12,bar*6.97e-12)*kd))
        else:
            pp=ps[k]; out.append((pp['Z']*kz,d*pp['td']*1e-12*kd))
    return out
_RUN=None
def _call(j): return _RUN(j)
if __name__=='__main__':
    path,oj=sys.argv[1:3]; b=pcbnew.LoadBoard(path); FP={f.GetReference():f for f in b.GetFootprints()}
    PS={'F.Cu':dict(Z=48.4,td=5.88),'B.Cu':dict(Z=48.4,td=5.88),'In2':dict(Z=49.1,td=6.97),'In5':dict(Z=49.1,td=6.97)}
    Lp,Cp=pkg(); import os; DR=os.environ.get('DRIVE','12'); ms=model(f'LVCMOS33_S_{DR}_HR'); mf=model('LVCMOS33_F_12_HR')
    C=[(0,'typ'),(1,'slow'),(2,'fast')]; DS={c:Driver(ms,c) for c,_ in C}; DF={c:Driver(mf,c) for c,_ in C}
    # refs and pins
    U1={p.GetNetname():p for p in FP['U1'].Pads()}; U32={p.GetNetname():p for p in FP['U32'].Pads()}
    xy=lambda p:(round(p.GetPosition().x/1e6,3),round(p.GetPosition().y/1e6,3))
    res={}; PINS=[n for n in U1 if (n or '').startswith('SDRAM_') and n in U32]
    stub={'SDRAM_CS_N':('R152',2),'SDRAM_CKE':('R153',1)}
    REFC={c:{e:refcross(DS[c],e) for e in 'rf'} for c,_ in C}; REFF={c:{e:refcross(DF[c],e) for e in 'rf'} for c,_ in C}
    print('tool test-load crossing (ns) slow-slew',{n:{e:round(REFC[c][e]*1e9,3) for e in 'rf'} for c,n in C}); print('fast-slew',{n:{e:round(REFF[c][e]*1e9,3) for e in 'rf'} for c,n in C})
    def run(net,secs,ball,drv,refs,Cl,Rs=None):
        L=Lp[ball]; Cc=Cp[ball]; Zp=math.sqrt(L/Cc) if Cc else 60.; tp=math.sqrt(L*Cc)
        row={}
        for c,nm in C:
            kd={0:1.,1:1.05,2:.95}[c]; kz={0:1.,1:1.03,2:.97}[c]
            ss=[(Zp,tp)]+build(secs,PS,kz,kd)
            row[nm]={}
            for e in 'rf':
                rs=(Rs[0]+1,Rs[1]) if Rs else None
                t,v,dv=sim(drv[c],e,ss,Cl,Rseries=rs)
                t14=cross(t,v,1.4,e); fl=t14-refs[c][e]
                lo,hi=.4,2.4; ta=cross(t,v,lo if e=='r' else hi,e); tb=cross(t,v,hi if e=='r' else lo,e)
                # ringback across the input thresholds after the first crossing
                i=np.searchsorted(t,(cross(t,v,2.0,e) if e=='r' else cross(t,v,.8,e)))
                after=v[i:]; rb=(after.min()<2.0) if e=='r' else (after.max()>.8)
                # earliest departure from the old valid level; last moment before the new level is held
                tl=cross(t,v,.8 if e=='r' else 2.0,e)
                bad=np.where(v<2.0)[0] if e=='r' else np.where(v>.8)[0]; ts=t[bad[-1]+1] if len(bad) and bad[-1]+1<len(t) else None
                row[nm][e]=dict(leave=round((tl-refs[c][e])*1e9,4),settle=round((ts-refs[c][e])*1e9,4) if ts is not None else None,flight=round(fl*1e9,4),edge=round((tb-ta)*1e9,3) if tb and ta else None,vmax=round(float(v.max()),2),vmin=round(float(v.min()),2),ringback=bool(rb),margin=round(float(after.min()-2.0 if e=='r' else .8-after.max()),2))
        return row
    jobs=[]
    for net in sorted(PINS):
        secs,L=walk(b,net,xy(U1[net]),xy(U32[net])); ball=U1[net].GetNumber()
        Cl=3.8e-12; st=0.
        if net in stub:
            r,k=stub[net]; p=next(x for x in FP[r].Pads() if x.GetNumber()==str(k)); _,st=walk(b,net,xy(U32[net]),xy(p)); Cl+=st*(1/(48.4*5.88e-12/1e-12*1e-0))*1e-12*0+st*5.88e-12/48.4
        if net.startswith('SDRAM_DQ') or net.endswith('DQM'): Cl=6.5e-12 if net.startswith('SDRAM_DQ') else 3.8e-12
        jobs.append((net,secs,ball,'S',Cl,None,L,st))
    # clock through R151
    ball=U1['SDRAM_CLK'].GetNumber(); R1=next(p for p in FP['R151'].Pads() if p.GetNumber()=='1'); R2=next(p for p in FP['R151'].Pads() if p.GetNumber()=='2')
    s1,l1=walk(b,'SDRAM_CLK',xy(U1['SDRAM_CLK']),xy(R1)); s2,l2=walk(b,'SDRAM_CLK_MEM',xy(R2),xy(U32['SDRAM_CLK_MEM']))
    nsec=len(s1)
    jobs.append(('SDRAM_CLK',s1+s2,ball,'F',3.5e-12,(nsec-1,22.),l1+l2,0))
    import multiprocessing as mp
    def work(j):
        net,secs,ball,kind,Cl,Rs,L,st=j
        return net,dict(sections=[(k,round(d,2)) if k!='via' else ('via','-'.join(sorted(d))) for k,d in secs],ball=ball,len=round(L,2),stub=round(st,2),cload=Cl,sim=run(net,secs,ball,DS if kind=='S' else DF,REFC if kind=='S' else REFF,Cl,Rs))
    _RUN=work
    with mp.get_context('fork').Pool(11) as pool:
        for net,r in pool.imap_unordered(_call,jobs):
            res[net]=r; print(net,r['len'],{n:{e:r['sim'][n][e]['flight'] for e in 'rf'} for n in ('slow','typ','fast')},flush=True)
    json.dump(res,open(oj,'w'),indent=0)
