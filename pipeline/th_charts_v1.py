import os as _dt_os;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'
# Team Hub charts: inline SVG built at build time (no script needed; works in the download file).
# Every mark carries a <title>, so hovering (desktop) or long-pressing (phone) shows its value.
# Colour: one accent (the team on the page), neutral grey for the other nine teams, position colours for positions
# (stack order QB, WR, TE, K, RB, DEF - the order that clears the palette validator's adjacent-pair checks on the
# dark surface), win green / loss red only for above / below.
import json,html,statistics as stt
import numpy as np
import assess as A
import sx_data as D
e=html.escape
T,WK,FUT,G=A.T,A.WK,A.FUT,A.G
TEAMS=list(T)
HI=json.load(open(__DTP__+'hist.json'));HM=HI['m']
ACC='#7fa6ff';NEU='#596278';GRID='#262c38';TXT='#9aa3b5';DIM='#626b7c';INK='#eef0f4'
def _mix(h,t=0.82,b='#0b0e14'):
    a=[int(h[i:i+2],16) for i in (1,3,5)];c=[int(b[i:i+2],16) for i in (1,3,5)]
    return '#'+''.join(f'{round(x*t+y*(1-t)):02x}' for x,y in zip(a,c))
PC={k:_mix(v) for k,v in {'QB':'#f7739c','RB':'#3ddcc1','WR':'#5ec6f4','TE':'#fca95c','K':'#c491ff','DEF':'#c98a72'}.items()}
STACK=['QB','WR','TE','K','RB','DEF']   # validated adjacent order
POS=['QB','RB','WR','TE','K','DEF']
WIN='#3fd69b';LOSS='#ff5d73'

# ---------- data
def starters(t,w):
    v=HI['w'][str(w)][str(A.RID[t])];o=[]
    for x in v[2].split(','):
        if not x:continue
        f=x.split('|');o.append(dict(pid=f[0],pos=HM.get(f[0],['DEF'])[0],proj=float(f[2]),pts=float(f[3])))
    return o
POSPTS={t:[{p:sum(q['pts'] for q in starters(t,w) if q['pos']==p) for p in POS} for w in range(1,G+1)] for t in TEAMS}
PROJ={t:[sum(q['proj'] for q in starters(t,w)) for w in range(1,G+1)] for t in TEAMS}
SC={t:[x[2] for x in WK[t]] for t in TEAMS}
for t in TEAMS:  # starter sums must reconcile with the weekly team scores
    for w in range(G):assert abs(sum(POSPTS[t][w].values())-SC[t][w])<0.02,(t,w+1,sum(POSPTS[t][w].values()),SC[t][w])
LGPOS=[{p:sum(POSPTS[t][w][p] for t in TEAMS)/10 for p in POS} for w in range(G)]

def odds_path(n=6000,seed=11):
    """playoff chance as of the end of each week 1..G, the Stats-tab model; early weeks lean harder on the league average"""
    sched={}
    for t in TEAMS:
        for x in WK[t]:sched[(x[0],t)]=A.FN(x[1])
        for x in FUT[t]:sched[(x[0],t)]=A.FN(x[1])
    idx={t:i for i,t in enumerate(TEAMS)};out={t:[] for t in TEAMS}
    for k in range(1,G+1):
        rng=np.random.default_rng(seed+k)
        sc={t:np.array(SC[t][:k]) for t in TEAMS};allsc=np.concatenate(list(sc.values()))
        lg=allsc.mean();pooled=np.mean([np.var(sc[t]) for t in TEAMS]) if k>=3 else np.var(allsc)
        wt=k/(k+3.77)  # weight on the team's own average grows with games played; 0.65 at 7 games, as on the Stats tab
        mu={t:wt*sc[t].mean()+(1-wt)*lg for t in TEAMS}
        sd={t:float(np.sqrt(0.5*(np.var(sc[t]) if k>=3 else pooled)+0.5*pooled)) for t in TEAMS}
        Wn=np.tile(np.array([sum(1 for w in range(k) if WK[t][w][2]>WK[t][w][3]) for t in TEAMS],float),(n,1))
        PF=np.tile(np.array([sum(SC[t][:k]) for t in TEAMS]),(n,1))
        for wk in range(k+1,15):
            S=np.stack([rng.normal(mu[t],sd[t],n) for t in TEAMS],axis=1);PF+=S;seen=set()
            for t in TEAMS:
                if t in seen:continue
                o=sched[(wk,t)];seen|={t,o};a,b=idx[t],idx[o];Wn[:,a]+=S[:,a]>S[:,b];Wn[:,b]+=S[:,b]>S[:,a]
        order=np.argsort(-(Wn*10000+PF),axis=1);seed_of=np.empty_like(order);seed_of[np.arange(n)[:,None],order]=np.arange(10)[None,:]
        for t in TEAMS:out[t].append(float((seed_of[:,idx[t]]<6).mean()*100))
    return out
ODDS=odds_path()

# ---------- svg helpers
def _svg(w,h,body,label):
    return f'<svg class="thsvg" viewBox="0 0 {w} {h}" role="img" aria-label="{e(label)}">{body}</svg>'
def _t(x,y,s,cls='ax',anchor='middle',extra=''):return f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}" text-anchor="{anchor}"{extra}>{s}</text>'
def _title(s):return f'<title>{e(s)}</title>'
def _nice(lo,hi,n=4):
    span=hi-lo;step=10**int(np.floor(np.log10(span/n)));
    for m in (1,2,2.5,5,10):
        if span/(step*m)<=n:step*=m;break
    a=np.floor(lo/step)*step;b=np.ceil(hi/step)*step
    return [a+i*step for i in range(int(round((b-a)/step))+1)]
def legend(items):
    """legend row (HTML, outside the svg): [(colour, label, kind)] kind: dot / line / band"""
    return '<div class="thlg">'+''.join(f'<span><i class="{k}" style="--c:{c}"></i>{e(l)}</span>' for c,l,k in items)+'</div>'

# ---------- 1. PF vs PA scatter (all teams)
def scatter_pfpa(t):
    W,Hh,L,R,Tp,B=360,250,40,12,14,34
    xs={k:T[k][5] for k in TEAMS};ys={k:T[k][8] for k in TEAMS}
    xt=_nice(min(xs.values())-2,max(xs.values())+2);yt=_nice(min(ys.values())-2,max(ys.values())+2)
    X=lambda v:L+(v-xt[0])/(xt[-1]-xt[0])*(W-L-R);Y=lambda v:Hh-B-(v-yt[0])/(yt[-1]-yt[0])*(Hh-B-Tp)
    mx,my=stt.mean(xs.values()),stt.mean(ys.values())
    g=''.join(f'<line x1="{X(v):.1f}" x2="{X(v):.1f}" y1="{Tp}" y2="{Hh-B}" class="gl"/>'+_t(X(v),Hh-B+14,f'{v:.0f}') for v in xt)
    g+=''.join(f'<line x1="{L}" x2="{W-R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" class="gl"/>'+_t(L-6,Y(v)+3.5,f'{v:.0f}','ax','end') for v in yt)
    g+=f'<line x1="{X(mx):.1f}" x2="{X(mx):.1f}" y1="{Tp}" y2="{Hh-B}" class="avg"/><line x1="{L}" x2="{W-R}" y1="{Y(my):.1f}" y2="{Y(my):.1f}" class="avg"/>'
    # quadrant captions (corners): high PF + low PA = strong; low PF + high PA = struggling
    g+=_t(W-R-3,Hh-B-6,'scores high · faces low','qd','end')+_t(L+4,Tp+10,'scores low · faces high','qd','start')
    g+=_t(L+(W-L-R)/2,Hh-4,'Points for per week','axt')+f'<text class="axt" transform="translate(10,{Tp+(Hh-B-Tp)/2:.0f}) rotate(-90)" text-anchor="middle">Points against per week</text>'
    dots=''
    for k in sorted(TEAMS,key=lambda k:k==t):
        c=ACC if k==t else NEU;r=6 if k==t else 4.5
        dots+=f'<circle cx="{X(xs[k]):.1f}" cy="{Y(ys[k]):.1f}" r="{r}" fill="{c}" class="dot">{_title(f"{k}: {xs[k]:.1f} for, {ys[k]:.1f} against per week")}</circle>'
    lx,ly=X(xs[t]),Y(ys[t]);anc='end' if lx>W*0.62 else 'start';dx=-9 if anc=='end' else 9
    dots+=_t(lx+dx,ly-8,e(t),'dl',anc)
    return _svg(W,Hh,g+dots,f'Points for vs points against per week, all teams; {t} at {xs[t]:.1f} for, {ys[t]:.1f} against')

# ---------- 2. playoff chance by week
def odds_line(t):
    W,Hh,L,R,Tp,B=360,190,34,40,12,26
    X=lambda w:L+14+(w-1)/(max(1,G-1))*(W-L-R-14);Y=lambda v:Hh-B-v/100*(Hh-B-Tp)
    g=''.join(f'<line x1="{L}" x2="{W-R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" class="gl"/>'+_t(L-6,Y(v)+3.5,f'{v}%','ax','end') for v in (0,25,50,75,100))
    g+=''.join(_t(X(w),Hh-B+15,f'Wk {w}' if w==1 else str(w)) for w in range(1,G+1))
    oth=''.join(f'<polyline points="{" ".join(f"{X(w+1):.1f},{Y(v):.1f}" for w,v in enumerate(ODDS[k]))}" class="ln0"/>' for k in TEAMS if k!=t)
    pts=ODDS[t];line=f'<polyline points="{" ".join(f"{X(w+1):.1f},{Y(v):.1f}" for w,v in enumerate(pts))}" class="ln1" style="stroke:{ACC}"/>'
    mk=''.join(f'<circle cx="{X(w+1):.1f}" cy="{Y(v):.1f}" r="{5 if w==G-1 else 3.5}" fill="{ACC}" class="dot">{_title(f"After week {w+1}: {v:.0f}% playoff chance")}</circle>' for w,v in enumerate(pts))
    end=_t(X(G)+8,Y(pts[-1])+4,f'{pts[-1]:.0f}%','dv','start')
    return _svg(W,Hh,g+oth+line+mk+end,f'{t} playoff chance after each week: '+', '.join(f'week {w+1} {v:.0f}%' for w,v in enumerate(pts)))

# ---------- 3. weekly score vs the league
def weekly_vs_league(t):
    W,Hh,L,R,Tp,B=360,200,34,14,12,26
    allv=[SC[k][w] for k in TEAMS for w in range(G)]
    yt=_nice(min(allv)-3,max(allv)+3)
    X=lambda w:L+(w-0.5)/G*(W-L-R);Y=lambda v:Hh-B-(v-yt[0])/(yt[-1]-yt[0])*(Hh-B-Tp)
    g=''.join(f'<line x1="{L}" x2="{W-R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" class="gl"/>'+_t(L-6,Y(v)+3.5,f'{v:.0f}','ax','end') for v in yt)
    bw=min(14,(W-L-R)/G*0.42);body=''
    for w in range(G):
        col=[SC[k][w] for k in TEAMS];lo,hi,md=min(col),max(col),stt.median(col)
        body+=f'<rect x="{X(w+1)-bw/2:.1f}" y="{Y(hi):.1f}" width="{bw:.1f}" height="{Y(lo)-Y(hi):.1f}" rx="4" class="rng">{_title(f"Week {w+1}: league range {lo:.1f}–{hi:.1f}, median {md:.1f}")}</rect>'
        body+=f'<line x1="{X(w+1)-bw/2-2:.1f}" x2="{X(w+1)+bw/2+2:.1f}" y1="{Y(md):.1f}" y2="{Y(md):.1f}" class="med"/>'
        body+=_t(X(w+1),Hh-B+15,f'Wk {w+1}' if w==0 else str(w+1))
    pts=SC[t]
    body+=f'<polyline points="{" ".join(f"{X(w+1):.1f},{Y(v):.1f}" for w,v in enumerate(pts))}" class="ln1" style="stroke:{ACC}"/>'
    for w,v in enumerate(pts):
        won=WK[t][w][2]>WK[t][w][3]
        body+=f'<circle cx="{X(w+1):.1f}" cy="{Y(v):.1f}" r="4.5" fill="{ACC}" class="dot">{_title(f"Week {w+1}: {v:.1f} ({"W" if won else "L"} {WK[t][w][2]:.1f}–{WK[t][w][3]:.1f}), rank {WK[t][w][4]} of 10")}</circle>'
    return _svg(W,Hh,g+body,f'{t} weekly scores against the league range and median')

# ---------- 4. points by position per week (stacked)
def pos_stack(t):
    W,Hh,L,R,Tp,B=360,210,34,10,16,26
    tot=[sum(POSPTS[t][w].values()) for w in range(G)];yt=_nice(0,max(tot)+5)
    X=lambda w:L+(w-0.5)/G*(W-L-R);Y=lambda v:Hh-B-v/yt[-1]*(Hh-B-Tp)
    g=''.join(f'<line x1="{L}" x2="{W-R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" class="gl"/>'+_t(L-6,Y(v)+3.5,f'{v:.0f}','ax','end') for v in yt)
    bw=min(24,(W-L-R)/G*0.6);body=''
    for w in range(G):
        y0=0;segs=[(p,POSPTS[t][w][p]) for p in STACK if POSPTS[t][w][p]>0]
        for j,(p,v) in enumerate(segs):
            top=j==len(segs)-1;ya,yb=Y(y0+v),Y(y0)
            h=max(0,yb-ya-(2 if not top else 0))  # 2px surface gap between segments
            if top:  # rounded data end only on the top segment
                r=min(4,h/2);d=f'M{X(w+1)-bw/2:.1f},{yb:.1f}V{ya+r:.1f}Q{X(w+1)-bw/2:.1f},{ya:.1f} {X(w+1)-bw/2+r:.1f},{ya:.1f}H{X(w+1)+bw/2-r:.1f}Q{X(w+1)+bw/2:.1f},{ya:.1f} {X(w+1)+bw/2:.1f},{ya+r:.1f}V{yb:.1f}Z'
                body+=f'<path d="{d}" fill="{PC[p]}">{_title(f"Week {w+1} {p}: {v:.1f}")}</path>'
            else:body+=f'<rect x="{X(w+1)-bw/2:.1f}" y="{ya+2:.1f}" width="{bw:.1f}" height="{h:.1f}" fill="{PC[p]}">{_title(f"Week {w+1} {p}: {v:.1f}")}</rect>'
            y0+=v
        body+=_t(X(w+1),Y(tot[w])-5,f'{tot[w]:.0f}','dvs')+_t(X(w+1),Hh-B+15,f'Wk {w+1}' if w==0 else str(w+1))
    return _svg(W,Hh,g+body,f'{t} points by position each week')+legend([(PC[p],p,'sq') for p in STACK])

# ---------- 5. position per week vs league average (dot + bar)
def pos_vs_league(t):
    W,L,R=360,40,58;rows=len(POS);rh=30;Hh=rows*rh+26
    tv={p:sum(POSPTS[t][w][p] for w in range(G))/G for p in POS};lv={p:sum(LGPOS[w][p] for w in range(G))/G for p in POS}
    mx=max(max(tv.values()),max(lv.values()))*1.08;X=lambda v:L+v/mx*(W-L-R)
    ticks=_nice(0,mx,4);g=''.join(f'<line x1="{X(v):.1f}" x2="{X(v):.1f}" y1="4" y2="{Hh-22}" class="gl"/>'+_t(X(v),Hh-8,f'{v:.0f}') for v in ticks if v<=mx)
    body=''
    for i,p in enumerate(POS):
        y=8+i*rh+rh/2;d=tv[p]-lv[p]
        body+=_t(L-8,y+4,p,'yl','end')
        body+=f'<rect x="{L}" y="{y-7:.1f}" width="{max(0,X(tv[p])-L):.1f}" height="14" rx="4" fill="{PC[p]}">{_title(f"{p}: {tv[p]:.1f} per week (league average {lv[p]:.1f})")}</rect>'
        body+=f'<line x1="{X(lv[p]):.1f}" x2="{X(lv[p]):.1f}" y1="{y-11:.1f}" y2="{y+11:.1f}" class="lgavg"/>'
        body+=_t(W-R+8,y+4,f'{tv[p]:.1f}','dv','start')+_t(W-2,y+4,f'{d:+.1f}','dl2 '+('up' if d>=0.05 else 'dn' if d<=-0.05 else ''),'end')
    return _svg(W,Hh,g+body,f'{t} points per week by position against the league average')+legend([(TXT,'League average','tick')])

# ---------- 6. position heatmap: vs league average each week
def pos_heat(t):
    W,L,R,Tp=360,40,4,20;rh=26;Hh=Tp+len(POS)*rh+4;cw=(W-L-R)/G
    vals=[[POSPTS[t][w][p]-LGPOS[w][p] for w in range(G)] for p in POS];m=max(abs(v) for r in vals for v in r) or 1
    body=''.join(_t(L+cw*(w+0.5),13,f'Wk {w+1}' if w==0 else str(w+1)) for w in range(G))
    for i,p in enumerate(POS):
        y=Tp+i*rh;body+=_t(L-8,y+rh/2+4,p,'yl','end')
        for w in range(G):
            v=vals[i][w];a=min(1,abs(v)/m)*0.62+0.06;c=WIN if v>=0 else LOSS
            body+=(f'<rect x="{L+cw*w+1:.1f}" y="{y+1:.1f}" width="{cw-2:.1f}" height="{rh-2}" rx="4" fill="{c}" fill-opacity="{a:.2f}">{_title(f"Week {w+1} {p}: {POSPTS[t][w][p]:.1f} vs league {LGPOS[w][p]:.1f} ({v:+.1f})")}</rect>'
                   +_t(L+cw*(w+0.5),y+rh/2+4,f'{v:+.0f}','hv'))
    return _svg(W,Hh,body,f'{t} position points each week minus the league average')+legend([(WIN,'Above league average','sq'),(LOSS,'Below','sq')])

# ---------- 7. actual vs projected
def vs_proj(t):
    W,Hh,L,R,Tp,B=360,170,34,10,16,26
    d=[SC[t][w]-PROJ[t][w] for w in range(G)];m=max(abs(x) for x in d)*1.15 or 1
    yt=[v for v in _nice(-m,m,6)];X=lambda w:L+(w-0.5)/G*(W-L-R);Y=lambda v:Tp+(yt[-1]-v)/(yt[-1]-yt[0])*(Hh-B-Tp)
    g=''.join(f'<line x1="{L}" x2="{W-R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" class="{"zl" if v==0 else "gl"}"/>'+_t(L-6,Y(v)+3.5,f'{v:+.0f}' if v else '0','ax','end') for v in yt)
    bw=min(24,(W-L-R)/G*0.55);body=''
    for w,v in enumerate(d):
        c=WIN if v>=0 else LOSS;y0,y1=(Y(v),Y(0)) if v>=0 else (Y(0),Y(v));h=max(1,y1-y0);r=min(4,h)
        x0=X(w+1)-bw/2;x1=X(w+1)+bw/2
        path=(f'M{x0:.1f},{y1:.1f}V{y0+r:.1f}Q{x0:.1f},{y0:.1f} {x0+r:.1f},{y0:.1f}H{x1-r:.1f}Q{x1:.1f},{y0:.1f} {x1:.1f},{y0+r:.1f}V{y1:.1f}Z' if v>=0 else
              f'M{x0:.1f},{y0:.1f}V{y1-r:.1f}Q{x0:.1f},{y1:.1f} {x0+r:.1f},{y1:.1f}H{x1-r:.1f}Q{x1:.1f},{y1:.1f} {x1:.1f},{y1-r:.1f}V{y0:.1f}Z')
        body+=f'<path d="{path}" fill="{c}" fill-opacity=".85">{_title(f"Week {w+1}: scored {SC[t][w]:.1f}, starters projected {PROJ[t][w]:.1f} ({v:+.1f})")}</path>'
        body+=_t(X(w+1),(y0-5) if v>=0 else (y1+12),f'{v:+.0f}','dvs')+_t(X(w+1),Hh-B+15,f'Wk {w+1}' if w==0 else str(w+1))
    return _svg(W,Hh,g+body,f'{t} score minus starters\' projection each week')

# ---------- 8. floor and ceiling: every team's weekly scores
def spread(t):
    order=sorted(TEAMS,key=lambda k:-stt.median(SC[k]));W,L,R=360,128,10;rh=22;Tp=6;Hh=Tp+len(order)*rh+24
    allv=[v for k in TEAMS for v in SC[k]];xt=_nice(min(allv)-3,max(allv)+3,5)
    X=lambda v:L+(v-xt[0])/(xt[-1]-xt[0])*(W-L-R)
    g=''.join(f'<line x1="{X(v):.1f}" x2="{X(v):.1f}" y1="{Tp}" y2="{Hh-22}" class="gl"/>'+_t(X(v),Hh-8,f'{v:.0f}') for v in xt)
    body=''
    for i,k in enumerate(order):
        y=Tp+i*rh+rh/2;c=ACC if k==t else NEU;sel=k==t;s=SC[k];md=stt.median(s)
        body+=_t(L-8,y+4,e(k),'yl tn'+(' sel' if sel else ''),'end')
        body+=f'<line x1="{X(min(s)):.1f}" x2="{X(max(s)):.1f}" y1="{y:.1f}" y2="{y:.1f}" stroke="{c}" stroke-width="2" stroke-linecap="round" opacity="{1 if sel else .55}"/>'
        body+=''.join(f'<circle cx="{X(v):.1f}" cy="{y:.1f}" r="{4 if sel else 3.2}" fill="{c}" class="dot">{_title(f"{k} week {w+1}: {v:.1f}")}</circle>' for w,v in enumerate(s))
        body+=f'<line x1="{X(md):.1f}" x2="{X(md):.1f}" y1="{y-7:.1f}" y2="{y+7:.1f}" class="medt"><title>{e(k)} median {md:.1f}</title></line>'
    return _svg(W,Hh,g+body,f'Weekly scores of every team, lowest to highest, with the median; sorted by median')+legend([(ACC,t,'dot'),(NEU,'Other teams','dot'),(INK,'Median','tick')])

def card(title,sub,body,cls=''):
    return f'<div class="thk{(" "+cls) if cls else ""}"><div class="thkh"><b>{title}</b>{f"<small>{sub}</small>" if sub else ""}</div>{body}</div>'
def overview(t):
    return ('<div class="thkg">'+
            card('Points for vs against','per week · all teams · lines = league average',scatter_pfpa(t))+
            card('Playoff chance','after each week · grey = other teams',odds_line(t))+
            card('Weekly score vs league','bar = league range · tick = median',weekly_vs_league(t),'wide')+
            '</div>')
def scoring(t):
    return ('<div class="thkg">'+
            card('Points by position','starters each week',pos_stack(t))+
            card('Position output vs league','points per week',pos_vs_league(t))+
            card('Position vs league, week by week','points above or below the league average',pos_heat(t),'wide')+
            card('Beat the projection?','score minus starters\' projection',vs_proj(t))+
            card('Floor and ceiling','every weekly score · sorted by median',spread(t))+
            '</div>')
if __name__=='__main__':
    print({k:[round(v) for v in ODDS[k]] for k in TEAMS})
    print({k:round(D.odds()[0][k]['po']) for k in TEAMS})
