import os as _dt_os;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'
# Team Hub: one page per team, switched by CSS-only radios (no script needed, works in the download file too).
# Sections: header + key numbers, this season, remaining schedule, position strength, roster core, lineup calls,
# draft capital, league history 2021-2026, head-to-head (all time), assessment. Writes th_section.html + th_css.css.
import json,re,html,subprocess
P=__DTP__
subprocess.run(['python3',P+'history_summary.py'],check=True,stdout=subprocess.DEVNULL)
import assess as A
import sx_data as D
import csv
import th_charts as C
e=html.escape
T,WK,FUT,R,G,NOW=A.T,A.WK,A.FUT,A.R,A.G,A.NOW
H=json.loads(re.search(r'const H=(\[.*?\]);',A._s).group(1))   # standings order
HS=json.load(open(P+'history/summary.json'))
P8=json.load(open(P+'pull8a.json'))
OWN={r['rid']:r['own'] for r in P8['ro']};UN={u[0]:u[1] for u in P8['us']}
owner=lambda t:UN.get(OWN.get(A.RID[t]),'')
ODDS,_=D.odds()
RW,PER=D.decisions()
POSR={A._norm(r['team']):r for r in csv.DictReader(open(P+'pos/pos.csv',encoding='utf-8'))}
POS=['QB','RB','WR','TE','K','DEF']
def ps(t,p):r=POSR[t];return float(r[p])/max(1,int(r['starts_'+p])-int(r.get('nogame_'+p) or 0))
def rk(vals,t,desc=True):
    v=vals[t];return 1+sum((x>v+1e-9) if desc else (x<v-1e-9) for x in vals.values()),sum(abs(x-v)<1e-9 for x in vals.values())>1
tone=lambda r:'gold' if r==1 else 'g' if r<=3 else 'b last' if r==10 else 'b' if r>=8 else ''
def chip(r,tie=False):return f'<i class="ch {tone(r)}"><span class="ct">{"T" if tie else "#"}{r}</span></i>'
ordn=A.ordn
def badge(tm):return f'<em class="nfl tm n-{tm}"><span class="ct">{tm}</span></em>' if tm else ''
def pz(pos):return f'<i class="pp p-{pos.lower()}"><span class="ct">{pos}</span></i>'
def sec(title,body,sub=''):return f'<div class="ths"><div class="msh thsh">{title}{f"<small>{sub}</small>" if sub else ""}</div>{body}</div>'
# current-season games into the all-time head-to-head
CUR={t:[(w[0],A.FN(w[1]),w[2],w[3]) for w in WK[t]] for t in T}
FIN={'Champion':'f1','Runner-up':'f2','3rd':'f3','4th':'f4','Playoffs':'f5','Missed':'f6'}

def band(pid,pos,pts,gp):
    """position band like every other player row: season points rank, or points-per-game rank under / Gm"""
    rk=(A.K.get(pid) or [None])[0] if pts>0 else None;pr=(A.PG.get(pid) or [None])[0] if pts>0 else None
    b3=lambda x:x and (x>=100 or (pos=='DEF' and x>=10))
    return (f'<i class="pq p-{pos.lower()}"><span class="pqi"><span>{pos}</span>'
            f'<b class="rkt{" b3" if b3(rk) else ""}">{rk or ""}</b><b class="rkg{" b3" if b3(pr) else ""}">{pr or ""}</b></span></i>')
def acl(a):return 'ay' if a<27 else 'ap' if a<31 else 'ao'
def prow(p):
    pid,name,pos,nfl,pts,_,gp,tag=p[:8]
    a=A.age(pid);ag=f'<em class="pag {acl(a)}">{a:.1f}</em>' if a else ''
    by=A.BYE.get(nfl);byh=f' · bye {by}' if by and by>=NOW else ''
    return (f'<div class="rr2">{band(pid,pos,pts,gp)}<span class="rn"><b><span class="nmx">{e(name)}</span>{badge(nfl)}{ag}</b>'
            f'<small><span class="gp">{gp} GP{byh}</span></small></span><span class="rv">{pts:.1f}</span><span class="rg2">{(pts/gp if gp else 0):.1f}</span></div>')
def page(i,t):
    w,l=T[t][0],T[t][1];pf=T[t][3];apw,apl,luck=T[t][10],T[t][11],T[t][12]
    pfv={k:T[k][5] for k in T};apv={k:T[k][10] for k in T}
    al=HS['all'].get(t,{});titles=al.get('titles',[]);finals=al.get('finals',[])
    od=ODDS[t]
    tb=[]
    if titles:tb.append(f'<span class="thb t1">{len(titles)}× Champion · {", ".join(map(str,titles))}</span>')
    ru=[y for y in finals if y not in titles]
    if ru:tb.append(f'<span class="thb t2">Runner-up · {", ".join(map(str,ru))}</span>')
    AS=A.assess(t)
    hdr=f'<div class="thh"><span class="thnr"><b class="thn">{e(t)}</b><i class="rat {AS["tc"]}">{AS["tier"]}</i></span><span class="tho">{e(owner(t))}</span>{"".join(tb) and f"<span class=thbs>{"".join(tb)}</span>"}</div>'
    tiles=('<div class="tht">'+''.join(f'<span><em>{a}</em><b>{b}</b>{c}</span>' for a,b,c in (
            ('Record',f'{w}-{l}',chip(i+1)),
            ('PF / wk',f'{T[t][5]:.1f}',chip(*rk(pfv,t))),
            ('All-play',f'{apw}-{apl}',chip(*rk(apv,t))),
            ('Luck',f'{luck:+.2f}',f'<small>wins vs expected</small>'),
            ('Playoffs',f'{od["po"]:.0f}%',f'<small>bye {od["bye"]:.0f}%</small>'),
            ('Proj wins',f'{od["w"]:.1f}',f'<small>of {G+len(FUT[t])}</small>')))+'</div>')
    # ---- NOW: key numbers, one 14-week timeline, lineup calls, assessment
    tl=''.join(f'<div class="thw"><span class="xwk">{wk}</span><span class="xres {"w" if a>b else "l"}">{"W" if a>b else "L"}</span>'
               f'<span class="xop">{e(o)}</span><span class="xsc"><b>{a:.1f}</b><i>–</i>{b:.1f}</span>{chip(r)}</div>'
               for (wk,o,a,b),r in zip(CUR[t],[x[4] for x in WK[t]]))
    tl+=''.join(f'<div class="thw thf{" nx" if x[0]==NOW else ""}"><span class="xwk">{x[0]}</span><span class="xres u">{"NEXT" if x[0]==NOW else ""}</span><span class="xop">{e(A.FN(x[1]))}</span>'
                f'<span class="xbar {"xg" if x[4]>=60 else "xr" if x[4]<40 else "xn"}"><i style="width:{x[4]}%"></i></span><b class="xpct">{x[4]}%</b></div>' for x in FUT[t])
    season=sec('Season',f'<div class="thl">{tl}</div>','played: score · week rank &nbsp;|&nbsp; ahead: win chance')
    ef=A.EF[t];efv={k:A.EF[k][0] for k in T};lost=PER[t]['lost'];flips=PER[t]['flip']
    top=[r for r in RW if r['team']==t][:1]
    call=''
    if top:
        c=top[0]
        call=(f'<div class="thc"><em>Costliest call · Wk {c["w"]}{" · cost the game" if c["flip"] else ""}</em>'
              f'<span class="cc"><span>Started <b>{e(c["start"]["name"])}</b></span><b class="v dn">{c["start"]["pts"]:.1f}</b></span>'
              f'<span class="cc"><span>Benched <b>{e(c["bench"]["name"])}</b></span><b class="v up">{c["bench"]["pts"]:.1f}</b></span>'
              f'<span class="cc sw"><span>Points lost</span><b class="v">−{c["swing"]:.1f}</b></span></div>')
    lineup=sec('Lineup calls',f'<div class="tht tht3"><span><em>Efficiency</em><b>{ef[0]:.1f}%</b>{chip(*rk(efv,t))}</span><span><em>Left on bench</em><b>{lost/G:.1f}</b><small>pts / wk</small></span><span><em>Lineup losses</em><b>{flips}</b><small>games lost on the bench</small></span></div>'+call)
    li=lambda xs,c:''.join(f'<div class="tha {c}"><i></i><span>{x}</span></div>' for x in xs) or f'<div class="tha {c}"><i></i><span>Nothing stands out.</span></div>'
    asx=sec('Strengths',li(AS['good'],'up'))+sec('Concerns',li(AS['bad'],'dn'))
    now=f'<div class="thv thv-n">{tiles}<div class="ths">{C.overview(t)}</div>{season}{asx}</div>'+f'<div class="thv thv-s"><div class="ths">{C.scoring(t)}</div>{lineup}</div>'
    # ---- ROSTER: core players (bands), position strength, draft capital
    core=sorted([p for p in R[t] if p[7]!='TX'],key=lambda p:-p[4])[:8]
    roster=f'<div class="ths"><div class="msh thsh">Roster core<span class="thrk"><i class="lt">Rank</i>{RKW}</span></div><div class="rcol thrc"><span>Player</span><span>Pts</span><span>/g</span></div>'+''.join(prow(p) for p in core)+'</div>'
    pv={p:{k:ps(k,p) for k in T} for p in POS}
    pos=sec('Position strength','<div class="thp">'+''.join(f'<span class="p-{p.lower()}"><i>{p}</i><b>{ps(t,p):.1f}</b>{chip(*rk(pv[p],t))}</span>' for p in POS)+'</div>','points per start · league rank')
    rid=A.RID[t]
    cells=''
    for y in ('2027','2028','2029'):
        cells+=f'<span class="dy">{y}</span>'
        for r_ in (1,2,3,4):
            mine=[k for k,v in A.own.items() if v==rid and k[0]==y and k[1]==r_]
            out=[k for k,v in A.own.items() if k[2]==rid and v!=rid and k[0]==y and k[1]==r_]
            it=''.join(f'<i class="in">+ {e(D.RN[k[2]])}</i>' for k in mine if k[2]!=rid)
            it+=''.join(f'<i class="out">to {e(D.RN[A.own[k]])}</i>' for k in out)
            n=len(mine)
            cells+=f'<span class="dc{" r1" if r_==1 else ""}{" none" if not n else ""}"><b>{n}</b>{it}</span>'
    draft=sec('Draft capital',f'<div class="thdg"><span></span>'+''.join(f'<span class="dh">R{r_}</span>' for r_ in (1,2,3,4))+cells+'</div>','picks held · + acquired from · traded away struck')
    ro=f'<div class="thv thv-r">{roster}{pos}{draft}</div>'
    # ---- HISTORY: seasons + head-to-head
    hr=''
    for y in sorted(HS['seasons']):
        s_=HS['seasons'][y][t];hr+=f'<div class="thy"><span class="xyr">{y}</span><b>{s_["w"]}-{s_["l"]}{"-"+str(s_["t"]) if s_["t"] else ""}</b><span class="xpf">{s_["pf"]/max(1,s_["w"]+s_["l"]+s_["t"]):.1f}</span><span class="xsd">{s_["seed"]}</span><span class="xfn {FIN[s_["finish"]]}">{s_["finish"]}</span></div>'
    hr+=f'<div class="thy now"><span class="xyr">2026</span><b>{w}-{l}</b><span class="xpf">{pf/G:.1f}</span><span class="xsd">{i+1}</span><span class="xfn f0">Wk {G} of 14</span></div>'
    aw,alw=al.get('w',0)+w,al.get('l',0)+l
    tots=(f'<div class="tht tht4"><span><em>All-time</em><b>{aw}-{alw}</b><small>{aw/(aw+alw)*100:.0f}% wins</small></span>'
          f'<span><em>Playoffs</em><b>{len(al.get("po",[]))}</b><small>of 5 seasons</small></span>'
          f'<span><em>Finals</em><b>{len(finals)}</b><small>{len(titles)} won</small></span></div>')
    hist=sec('League history',tots+'<div class="thy thyh"><span class="xyr">Season</span><b>W-L</b><span class="xpf">PF/wk</span><span class="xsd">Seed</span><span class="xfn">Finish</span></div>'+hr,'regular season · 2021–24 on MFL')
    hh='<div class="thx thxh"><span class="xop">Opponent</span><b>W-L</b><span class="xpo">Playoffs</span></div>'
    for o in [x for x in H if x!=t]:
        h=dict(HS['h2h'].get(t,{}).get(o,{'w':0,'l':0,'t':0,'po_w':0,'po_l':0,'pf':0.0,'pa':0.0,'last':None}))
        last=h['last']
        for wk,op,a,b in CUR[t]:
            if op==o:h['w']+=a>b;h['l']+=a<b;h['pf']+=a;h['pa']+=b;last=[2026,wk,'W' if a>b else 'L',a,b]
        n=h['w']+h['l']+h['t'];d=h['w']-h['l'];lead='up' if d>=3 else 'dn' if d<=-3 else ''
        po=f'{h["po_w"]}-{h["po_l"]}' if h['po_w'] or h['po_l'] else '–'
        ls=f'Last Wk {last[1]} ’{str(last[0])[2:]} <i class="{last[2].lower()}">{last[2]}</i> {last[3]:.1f}–{last[4]:.1f}' if last else ''
        av=f'Avg {h["pf"]/n:.1f}–{h["pa"]/n:.1f}' if n else ''
        hh+=f'<div class="thx"><span class="xop">{e(o)}</span><b class="{lead}">{h["w"]}-{h["l"]}{"-"+str(h["t"]) if h["t"] else ""}</b><span class="xpo">{po}</span><span class="xls">{av}<i class="sep">·</i>{ls}</span></div>'
    h2h=sec('Head-to-head',hh,'all time · standings order · colour = lead of 3+')
    hi=f'<div class="thv thv-h">{hist}{h2h}</div>'
    return f'<div class="thpg thpg-{i}">{hdr}{now}{ro}{hi}</div>'

radios=''.join(f'<input type="radio" name="thub" id="th-{i}" class="lr"{" checked" if i==0 else ""}>' for i in range(len(H)))+\
  '<input type="radio" name="thv" id="thv-n" class="lr" checked><input type="radio" name="thv" id="thv-s" class="lr"><input type="radio" name="thv" id="thv-r" class="lr"><input type="radio" name="thv" id="thv-h" class="lr">'+\
  '<input type="radio" name="thk" id="thk-t" class="lr" checked><input type="radio" name="thk" id="thk-g" class="lr">'
VSW='<div class="thctl"><div class="thvw pseg" role="group" aria-label="Team Hub view"><label for="thv-n">Overview</label><label for="thv-s">Scoring</label><label for="thv-r">Roster</label><label for="thv-h">History</label></div></div>'
RKW='<div class="thkw pseg" role="group" aria-label="Position rank by"><label for="thk-t">Pts</label><label for="thk-g">/ Gm</label></div>'
dd=('<details class="dd tdd"><summary>'+''.join(f'<span class="sv tsv-{i}">{e(t)}</span>' for i,t in enumerate(H))+
    '<svg viewBox="0 0 10 6" aria-hidden="true"><path d="M1 1l4 4 4-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg></summary>'
    '<div class="ddm">'+''.join(f'<label for="th-{i}"><i>{i+1}</i>{e(t)}</label>' for i,t in enumerate(H))+'</div></details>')
sec_=f'<section class="thx0" aria-labelledby="thh0">{radios}<div class="posh"><b id="thh0">Team Hub</b>{dd}</div>{VSW}'+''.join(page(i,t) for i,t in enumerate(H))+'</section>'
css=''.join(f'#th-{i}:checked~.posh .tsv-{i}{{display:inline}}#th-{i}:checked~.posh label[for="th-{i}"]{{background:var(--chalk);color:var(--ink)}}#th-{i}:checked~.thpg-{i}{{display:block}}' for i in range(len(H)))
open(P+'th_section.html','w',encoding='utf-8').write(sec_);open(P+'th_css.css','w',encoding='utf-8').write(css)
if __name__=='__main__':print('team hub',len(sec_)//1000,'KB')
