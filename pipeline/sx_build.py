import os as _dt_os;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'
# Renders the Stats tab: sub-tab nav + Positions (existing POS_SECTION placeholder) + 10 modules.
import html,sys
P=__DTP__+''
sys.path.insert(0,P)
import sx_data as D
from nfl_colors import badge_c as badge
e=html.escape
T,TEAMS,G,NOW,SHORT,CODE=D.T,D.TEAMS,D.G,D.NOW,D.SHORT,D.CODE
def rec(t):return f'{T[t][0]}-{T[t][1]}'
def nm(t):return f'<span class="sxn">{e(t)}</span>'
def sgn(x,d=1):return ('+' if x>=0.05 else '−' if x<=-0.05 else '')+f'{abs(x):.{d}f}'
def pct(x):
    v='0' if x==0 else '<0.1' if x<0.05 else '>99.9' if 99.95<=x<100 else f'{x:.1f}' if (x<10 or x>=99.5) and x<100 else f'{x:.0f}'
    return v+'<small>%</small>'
def pz(pos):return f'<i class="pz p-{pos.lower()}">{pos}</i>'
def dvb(v,mx):
    w=min(abs(v)/mx,1)*50 if mx else 0
    return f'<span class="dvb"><i class="{"up" if v>=0 else "dn"}" style="width:{w:.2f}%"></i></span>'
def hbar(v,mx,cls=''):return f'<span class="hbr"><i class="{cls}" style="width:{(min(v/mx,1)*100 if mx else 0):.2f}%"></i></span>'
def nmb(t,bar):return f'<span class="sxnb">{nm(t)}{bar}</span>'
def head(title,sub):return f'<div class="sxh"><b>{title}</b><span>{sub}</span></div>'
def table(cols,rows,cls=''):
    # cols: list of (label, width) ; first col is the team name (flex)
    tpl=' '.join(['minmax(0,1fr)']+[w for _,w in cols[1:]])
    hd=''.join(f'<span>{c}</span>' for c,_ in cols)
    return f'<div class="sxt {cls}" style="--cols:{tpl}"><div class="sxr sxhd">{hd}</div>'+''.join(f'<div class="sxr">{"".join(r)}</div>' for r in rows)+'</div>'
# ---------- 1 Odds
O,meta=D.odds()
def m_odds():
    rows=[]
    for t in sorted(TEAMS,key=lambda t:(-O[t]['po'],-O[t]['w'])):
        o=O[t];a,b,c=o['top'],o['bye']-o['top'],o['po']-o['bye']
        bar='<span class="obar">'+''.join(f'<i class="{k}" style="width:{v:.2f}%"></i>' for k,v in (('o1',a),('o2',b),('o3',c)) if v>=1)+'</span>'
        rows.append(f'<div class="odr"><div class="odt">{nm(t)}<span class="sxv odn">{rec(t)}</span></div>{bar}'
                    f'<div class="odv"><span class="sxv">{o["w"]:.1f}</span><span class="sxv b c3">{pct(o["po"])}</span><span class="sxv c2">{pct(o["bye"])}</span><span class="sxv c1">{pct(o["top"])}</span></div></div>')
    hd='<div class="odv sxhd"><span>Proj W</span><span class="c3">Playoffs</span><span class="c2">Bye</span><span class="c1">#1 seed</span></div>'
    lg='<div class="olg"><span class="o1">#1 seed</span><span class="o2">Bye</span><span class="o3">Playoffs</span></div>'
    return head('Playoff odds',f'{meta["n"]:,} simulations of Weeks {meta["weeks"][0]}–{meta["weeks"][-1]}')+lg+'<div class="odx">'+hd+''.join(rows)+'</div>'
# ---------- 2 Schedule swap
M=D.schedswap()
def m_sched():
    order=D.PH
    hd='<span></span>'+''.join(f'<span>{CODE[b]}</span>' for b in order)
    rows=[]
    for a in order:
        cells=''.join(f'<span class="mx{" dg" if a==b else " up" if M[a][b]>M[a][a] else " dn" if M[a][b]<M[a][a] else ""}">{M[a][b]}</span>' for b in order)
        rows.append(f'<div class="sxr"><span class="mxn">{e(SHORT[a])}</span>{cells}</div>')
    mat=f'<div class="sxm"><div class="sxr sxhd">{hd}</div>{"".join(rows)}</div>'
    av={a:sum(M[a][b] for b in TEAMS)/10 for a in TEAMS}
    lr=[[nmb(a,dvb(T[a][0]-av[a],1.2)),f'<span class="sxv">{T[a][0]}</span>',f'<span class="sxv">{av[a]:.1f}</span>',f'<span class="sxv b {"up" if T[a][0]-av[a]>=0.5 else "dn" if T[a][0]-av[a]<=-0.5 else ""}">{sgn(T[a][0]-av[a])}</span>'] for a in sorted(TEAMS,key=lambda a:-(T[a][0]-av[a]))]
    return (head('Schedule swap',f'Wins through Week {G} with each team\'s schedule')+mat+
            head('Schedule luck','Actual wins vs average across all 10 schedules')+table([('Team',''),('Wins','42px'),('Avg','42px'),('Luck','46px')],lr))
# ---------- 3 Trades
def m_trades():
    out=[head('Trade scorecard',f'Points scored since each trade · through Week {G}')]
    for x in D.trades():
        a,b=x['sides'];pend=x['eff']>G
        def side(s,other):
            win=(not pend) and s['tot']>other['tot']+0.05
            fp=lambda v:'–' if pend else f'{v:.1f}'
            pl=''.join(f'<div class="tpl"><span class="tpn">{e(p["name"])}<span class="tpb">{pz(p["pos"])}{badge(p["nfl"])}</span></span>{"" if pend else f"<b>{p['pts']:.1f}</b>"}</div>' for p in s['pl'])
            def pkh(k):
                y,rd,rest=k.split(' ',2);return f'<div class="tpk"><i class="pkc r{rd[0]}">{rd}</i><span class="pkt">{y} <em>{e(rest.strip("()"))}</em></span></div>'
            pk=''.join(pkh(k) for k in s['pk'])
            fb=f'<div class="tpk"><i class="pkc fb">${s["faab"]}</i>FAAB</div>' if s['faab'] else ''
            body=pl+pk+fb or '<div class="tpk">–</div>'
            tot='<span>No games yet</span>' if pend else ('<span>No players</span>' if not s['pl'] else f'<b>{s["tot"]:.1f}</b><span>pts since</span>')
            return f'<div class="tsd{" win" if win else ""}"><div class="tnm">{e(s["team"])}</div><div class="trc">receives</div>{body}<div class="ttot">{tot}</div></div>'
        when=f'{x["date"]} · counts from Week {x["eff"]}' if not pend else f'{x["date"]} · no games since'
        if x['eff']==1:when=f'{x["date"]} · before Week 1'
        out.append(f'<div class="trd"><div class="trw">{when}</div><div class="trg">{side(a,b)}{side(b,a)}</div></div>')
    return ''.join(out)
# ---------- 4 Lineup calls
RW,PER=D.decisions()
def m_lineups():
    top=RW[:8];li=[]
    for r in top:
        flip='<i class="dtag">Cost the win</i>' if r['flip'] and r['bench']['pts']-r['start']['pts']>=r['them']-r['me'] else ''
        mx=40
        def ln(q,lab,cls):return f'<div class="dln dln2"><span class="dlb">{lab}</span><span class="dnm">{pz(q["pos"])}<b>{e(q["name"])}</b></span><em class="{cls}">{q["pts"]:.1f}</em></div>'
        li.append(f'<div class="dcl dcl2"><div class="dch dch2"><i class="dwk">Wk {r["w"]}</i><span class="dtm">{e(r["team"])}</span><span class="dsw"><b>+{r["swing"]:.1f}</b><small>pts lost</small></span></div>'
                  +ln(r['bench'],'Bench','up')+ln(r['start'],'Started','dn')+(f'<div class="dft">{flip}</div>' if flip else '')+'</div>')
    mxl=max(v['lost'] for v in PER.values())
    rows=[[nmb(t,hbar(PER[t]['lost'],mxl,'am')),f'<span class="sxv">{PER[t]["lost"]:.1f}</span>',f'<span class="sxv">{PER[t]["lost"]/G:.1f}</span>',f'<span class="sxv b {"dn" if PER[t]["flip"] else "z"}">{PER[t]["flip"]}</span>'] for t in sorted(TEAMS,key=lambda t:(-PER[t]['flip'],-PER[t]['lost']))]
    return (head('Costliest lineup calls','Biggest single bench-for-starter swaps')+''.join(li)+
            head('Winnable losses','Losses the best lineup on the roster would have won')+
            table([('Team',''),('Dropped','56px'),('Per wk','46px'),('Winnable','58px')],rows))
# ---------- 5 Projections
TM,HI,LO=D.projections()
def m_proj():
    rows=[[nmb(t,dvb(TM[t]['avg'],20)),f'<span class="sxv b {"up" if TM[t]["avg"]>=0.05 else "dn" if TM[t]["avg"]<=-0.05 else ""}">{sgn(TM[t]["avg"])}</span>',f'<span class="sxv">{TM[t]["beat"]}/{G}</span>'] for t in sorted(TEAMS,key=lambda t:-TM[t]['avg'])]
    def pl(lst,cls):
        return ''.join(f'<div class="ppl"><span class="pnm">{pz(r["pos"])}<b>{e(r["name"])}</b>{badge(r["nfl"])}<span class="pmt">{e(SHORT[r["team"]])} · {r["n"]} starts</span></span><b class="sxv {cls}">{sgn(r["avg"])}</b></div>' for r in lst)
    return (head('Vs projection','Starters\' points minus Sleeper projection, per week')+table([('Team',''),('Per wk','54px'),('Beat','44px')],rows)+
            head('Overachievers','Per start vs projection · min. 3 starts')+pl(HI,'up')+
            head('Underachievers','Per start vs projection · min. 3 starts')+pl(LO,'dn'))
# ---------- 6 Margins
CL,CLG,BLG=D.close()
def m_close():
    rows=[[nmb(t,dvb(CL[t]['avgm'],45)),f'<span class="sxv">{CL[t]["close"][0]}-{CL[t]["close"][1]}</span>',f'<span class="sxv">{CL[t]["blow"][0]}-{CL[t]["blow"][1]}</span>',f'<span class="sxv b {"up" if CL[t]["avgm"]>=0.05 else "dn"}">{sgn(CL[t]["avgm"])}</span>'] for t in sorted(TEAMS,key=lambda t:-CL[t]['avgm'])]
    def gl(gs,cls):return ''.join(f'<div class="gml"><span class="gwk">Wk {g["w"]}</span><span class="gtm"><span><b class="gln"><i class="wl w">W</i>{e(g["win"])}</b><em>{g["ws"]:.2f}</em></span><span><span class="gln"><i class="wl l">L</i>{e(g["lose"])}</span><em>{g["ls"]:.2f}</em></span></span><b class="gmv {cls}">{g["m"]:.2f}</b></div>' for g in gs)
    return (head('Margins',f'Close = under 10 pts · blowout = 30+ pts')+table([('Team',''),('Close','46px'),('Blowout','56px'),('Avg','46px')],rows)+
            head('Closest games','Winner on top · margin on the right')+gl(CLG,'cl')+head('Biggest blowouts','Winner on top · margin on the right')+gl(BLG,'bo'))
# ---------- 7 Stars
ST=D.stars()
def m_stars():
    o=[head('Star dependence','Share of season points from the top 1 and top 3 scorers (as starters)')]
    for t in sorted(TEAMS,key=lambda t:-ST[t]['s3']):
        s=ST[t];a,b=s['s1'],s['s3']-s['s1']
        segs=''.join(f'<i class="p-{v[1].lower()}{" s1" if i==0 else ""}" style="width:{v[2]/s["tot"]*100:.2f}%"></i>' for i,v in enumerate(s['top3']))
        names=''.join(f'<span>{pz(v[1])}{e(v[0])} <em>{v[2]/s["tot"]*100:.0f}%</em></span>' for v in s['top3'])
        o.append(f'<div class="stb"><div class="stt">{nm(t)}<span><b>{s["s1"]:.0f}%</b> top 1 · <b>{s["s3"]:.0f}%</b> top 3</span></div>'
                 f'<div class="bar sbar">{segs}</div><div class="stn">{names}</div></div>')
    return ''.join(o)
# ---------- 8 Youth
YO=D.youth()
def m_youth():
    o=[head('Production by age','Share of starters\' points by player age today'),'<div class="ylg"><span class="ay">25 and under</span><span class="ap">26–29</span><span class="ao">30+</span><span class="ad">DEF</span></div>']
    for t in sorted(TEAMS,key=lambda t:-YO[t]['pct'][0]):
        p=YO[t]['pct']
        o.append(f'<div class="stb"><div class="stt">{nm(t)}<span><b class="ay">{p[0]:.0f}%</b> · <b class="ap">{p[1]:.0f}%</b> · <b class="ao">{p[2]:.0f}%</b></span></div>'
                 f'<div class="bar ybar"><i class="y0" style="width:{p[0]:.2f}%"></i><i class="y1" style="width:{p[1]:.2f}%"></i><i class="y2" style="width:{p[2]:.2f}%"></i><i class="y3" style="width:{p[3]:.2f}%"></i></div></div>')
    return ''.join(o)
# ---------- 9 Ranks heatmap
HE=D.heat()
def m_heat():
    hd='<span></span>'+''.join(f'<span>W{w}</span>' for w in range(1,G+1))+'<span>Avg</span>'
    rows=[]
    for t in sorted(TEAMS,key=lambda t:sum(HE[t])):
        cells=''.join(f'<span class="hm r{r}">{r}</span>' for r in HE[t])
        rows.append(f'<div class="sxr"><span class="mxn">{e(SHORT[t])}</span>{cells}<span class="hav">{sum(HE[t])/G:.1f}</span></div>')
    return head('Weekly score rank','1 = highest score that week')+f'<div class="sxm hmx" style="--n:{G}"><div class="sxr sxhd">{hd}</div>{"".join(rows)}</div>'
# ---------- 10 Byes
BY=D.byes()
def m_byes():
    wk=list(range(NOW,15))
    hd='<span></span>'+''.join(f'<span>W{w}</span>' for w in wk)
    rows=[];notes=[]
    for t in D.PH:
        cells=''.join(f'<span class="bx b{min(len(BY[t][w]),3)}">{len(BY[t][w]) or "–"}</span>' for w in wk)
        rows.append(f'<div class="sxr"><span class="mxn">{e(SHORT[t])}</span>{cells}</div>')
        for w in wk:
            if len(BY[t][w])>=2:notes.append((w,t,BY[t][w]))
    nl=''.join(f'<div class="bnl"><span>Wk {w}</span><b>{e(SHORT[t])}</b><i>{"".join(f'<span>{pz(p[2])}{e(p[3]+" DEF" if p[2]=="DEF" else p[1])}</span>' for p in ps)}</i></div>' for w,t,ps in sorted(notes))
    return head('Bye exposure','Core starters on bye each remaining week')+f'<div class="sxm bym" style="--n:{len(wk)}"><div class="sxr sxhd">{hd}</div>{"".join(rows)}</div>'+head('Two or more starters out','')+nl
MODS=[('pos','Positions',None),('odds','Odds',m_odds),('sch','Schedules',m_sched),('trd','Trades',m_trades),('lu','Lineups',m_lineups),('prj','Projections',m_proj),
      ('mg','Margins',m_close),('st','Stars',m_stars),('yo','Age',m_youth),('rk','Ranks',m_heat),('by','Byes',m_byes)]
def build():
    radios=''.join(f'<input type="radio" name="sxs" id="sx-{k}" class="lr"{" checked" if i==0 else ""}>' for i,(k,_,_) in enumerate(MODS))
    nav='<div class="lbc sxnav" role="tablist" aria-label="Stats">'+''.join(f'<label for="sx-{k}">{lab}</label>' for k,lab,_ in MODS)+'</div>'
    pans=''.join(f'<div class="sxp sxp-{k}">'+('POS_SECTION' if f is None else f'<section class="sxc">{f()}</section>')+'</div>' for k,_,f in MODS)
    css=''.join(f'#sx-{k}:checked~.sxnav label[for="sx-{k}"]{{background:var(--chalk);color:var(--ink);border-color:var(--chalk)}}#sx-{k}:checked~.sxp-{k}{{display:block}}' for k,_,_ in MODS)
    return radios+nav+pans,css
if __name__=='__main__':
    h,c=build();open(P+'sx_section.html','w',encoding='utf-8').write(h);open(P+'sx_css.css','w',encoding='utf-8').write(c);print(len(h))
