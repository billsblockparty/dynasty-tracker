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

def page(i,t):
    w,l=T[t][0],T[t][1];pf=T[t][3];apw,apl,luck=T[t][10],T[t][11],T[t][12]
    pfv={k:T[k][5] for k in T};apv={k:T[k][10] for k in T};lkv={k:T[k][12] for k in T}
    al=HS['all'].get(t,{});titles=al.get('titles',[]);finals=al.get('finals',[])
    od=ODDS[t]
    # 1. header
    tb=[]
    if titles:tb.append(f'<span class="thb t1">{len(titles)}× Champion · {", ".join(map(str,titles))}</span>')
    ru=[y for y in finals if y not in titles]
    if ru:tb.append(f'<span class="thb t2">Runner-up · {", ".join(map(str,ru))}</span>')
    hdr=(f'<div class="thh"><b class="thn">{e(t)}</b><span class="tho">{e(owner(t))}</span>{"".join(tb) and f"<span class=thbs>{"".join(tb)}</span>"}</div>'
         '<div class="tht">'+''.join(f'<span><em>{a}</em><b>{b}</b>{c}</span>' for a,b,c in (
            ('Record',f'{w}-{l}',f'<small>{ordn(i+1)} seed</small>'),
            ('PF / wk',f'{T[t][5]:.1f}',chip(*rk(pfv,t))),
            ('All-play',f'{apw}-{apl}',chip(*rk(apv,t))),
            ('Luck',f'{luck:+.2f}',f'<small>wins vs expected</small>'),
            ('Playoffs',f'{od["po"]:.0f}%',f'<small>bye {od["bye"]:.0f}%</small>'),
            ('Proj wins',f'{od["w"]:.1f}',f'<small>of {G+len(FUT[t])}</small>')))+'</div>')
    # 2. this season
    rows=''.join(f'<div class="thw"><span class="xwk">Wk {wk}</span><span class="xres {"w" if a>b else "l"}">{"W" if a>b else "L"}</span>'
                 f'<span class="xsc"><b>{a:.1f}</b>–{b:.1f}</span><span class="xop">{e(o)}</span>{chip(r)}</div>'
                 for (wk,o,a,b),r in zip(CUR[t],[x[4] for x in WK[t]]))
    season=sec('This season',f'<div class="thl">{rows}</div>','score · rank of the week')
    # 3. remaining schedule
    fr=''.join(f'<div class="thw thf"><span class="xwk">Wk {x[0]}</span><span class="xop">{e(A.FN(x[1]))}</span><span class="xbar"><i style="width:{x[4]}%"></i></span><b class="xpct">{x[4]}%</b></div>' for x in FUT[t])
    rest=sec('Remaining schedule',f'<div class="thl">{fr}</div>',f'win chance · Wk {NOW} from projections') if FUT[t] else ''
    # 4. position strength
    pv={p:{k:ps(k,p) for k in T} for p in POS}
    pos=sec('Position strength','<div class="thp">'+''.join(f'<span>{pz(p)}<b>{ps(t,p):.1f}</b>{chip(*rk(pv[p],t))}</span>' for p in POS)+'</div>','points per start · league rank')
    # 5. roster core
    core=sorted([p for p in R[t] if p[7]!='TX'],key=lambda p:-p[4])[:8]
    cr=''.join(f'<div class="thr">{pz(p[2])}<span class="xnm"><b>{e(p[1] if p[2]!="DEF" else p[1])}</b>{badge(p[3])}</span><span class="xag">{(lambda a:f"{a:.1f}" if a else "")(A.age(p[0]))}</span><b class="xpt">{p[4]:.1f}</b><span class="xpg">{(p[4]/p[6] if p[6] else 0):.1f}</span></div>' for p in core)
    roster=sec('Roster core','<div class="thr thrh"><span></span><span class="xnm"></span><span class="xag">Age</span><b class="xpt">Pts</b><span class="xpg">/ Gm</span></div>'+cr,'top 8 by points this season')
    # 6. lineup calls
    ef=A.EF[t];efv={k:A.EF[k][0] for k in T};lost=PER[t]['lost'];flips=PER[t]['flip']
    top=[r for r in RW if r['team']==t][:1]
    call=(f'<div class="thc"><em>Costliest call</em><span>Wk {top[0]["w"]}: started {e(top[0]["start"]["name"])} ({top[0]["start"]["pts"]:.1f}) over {e(top[0]["bench"]["name"])} ({top[0]["bench"]["pts"]:.1f}), −{top[0]["swing"]:.1f}{" · cost the game" if top[0]["flip"] else ""}</span></div>') if top else ''
    lineup=sec('Lineup calls',f'<div class="tht tht3"><span><em>Efficiency</em><b>{ef[0]:.1f}%</b>{chip(*rk(efv,t))}</span><span><em>Left on bench</em><b>{lost/G:.1f}</b><small>pts / wk</small></span><span><em>Games lost to it</em><b>{flips}</b><small>best lineup wins</small></span></div>'+call)
    # 7. draft capital
    rid=A.RID[t];dc=''
    for y in ('2027','2028','2029'):
        mine=sorted([k for k,v in A.own.items() if v==rid and k[0]==y],key=lambda k:(k[1],k[2]))
        out=sorted([k for k,v in A.own.items() if k[2]==rid and v!=rid and k[0]==y],key=lambda k:k[1])
        it=''.join(f'<span class="xpk r{k[1]}{" in" if k[2]!=rid else ""}">R{k[1]}{f"<small>{e(D.RN[k[2]])}</small>" if k[2]!=rid else ""}</span>' for k in mine)
        gone=''.join(f'<span class="xpk gone">R{k[1]}<small>to {e(D.RN[A.own[k]])}</small></span>' for k in out)
        dc+=f'<div class="thd"><span class="xyr">{y}</span><span class="xpks">{it}{gone}</span></div>'
    draft=sec('Draft capital',dc,'acquired: original team · traded: dashed')
    # 8. history
    hr=''
    for y in sorted(HS['seasons']):
        s_=HS['seasons'][y][t];hr+=f'<div class="thy"><span class="xyr">{y}</span><b>{s_["w"]}-{s_["l"]}{"-"+str(s_["t"]) if s_["t"] else ""}</b><span class="xpf">{s_["pf"]:.0f}</span><span class="xsd">{ordn(s_["seed"])}</span><span class="xfn {FIN[s_["finish"]]}">{s_["finish"]}</span></div>'
    hr+=f'<div class="thy now"><span class="xyr">2026</span><b>{w}-{l}</b><span class="xpf">{pf:.0f}</span><span class="xsd">{ordn(i+1)}</span><span class="xfn f0">Week {G} of 14</span></div>'
    aw,alw=al.get('w',0)+w,al.get('l',0)+l
    hr+=f'<div class="thy all"><span class="xyr">All</span><b>{aw}-{alw}</b><span class="xpf">{aw/(aw+alw)*100:.0f}%</span><span class="xsd">{len(al.get("po",[]))}× PO</span><span class="xfn">{len(titles)} title{"s" if len(titles)!=1 else ""}</span></div>'
    hist=sec('League history','<div class="thy thyh"><span class="xyr">Season</span><b>W-L</b><span class="xpf">PF</span><span class="xsd">Seed</span><span class="xfn">Finish</span></div>'+hr,'regular season · 2021–24 on MFL')
    # 9. head-to-head (all time, incl. this season)
    hh=''
    for o in [x for x in H if x!=t]:
        h=dict(HS['h2h'].get(t,{}).get(o,{'w':0,'l':0,'t':0,'po_w':0,'po_l':0,'last':None}))
        last=h['last']
        for wk,op,a,b in CUR[t]:
            if op==o:
                h['w']+=a>b;h['l']+=a<b;last=[2026,wk,'W' if a>b else 'L',a,b]
        po=f' · playoffs {h["po_w"]}-{h["po_l"]}' if h['po_w'] or h['po_l'] else ''
        ls=f'<span class="xls">Last: {last[0]} Wk {last[1]} · <i class="{last[2].lower()}">{last[2]}</i> {last[3]:.1f}–{last[4]:.1f}{po}</span>' if last else ''
        lead='up' if h['w']>h['l'] else 'dn' if h['w']<h['l'] else ''
        hh+=f'<div class="thx"><span class="xop">{e(o)}</span><b class="{lead}">{h["w"]}-{h["l"]}{"-"+str(h["t"]) if h["t"] else ""}</b>{ls}</div>'
    h2h=sec('Head-to-head',hh,'all time, 2021–2026')
    asx=f'<div class="ths">{A.assess_html(t)}</div>'
    return f'<div class="thpg thpg-{i}">{hdr}{season}{rest}{pos}{roster}{lineup}{draft}{hist}{h2h}{asx}</div>'

radios=''.join(f'<input type="radio" name="thub" id="th-{i}" class="lr"{" checked" if i==0 else ""}>' for i in range(len(H)))
chips='<div class="lbc thc0" role="tablist" aria-label="Team">'+''.join(f'<label for="th-{i}">{e(t)}</label>' for i,t in enumerate(H))+'</div>'
sec_=f'<section class="thx0" aria-labelledby="thh0">{radios}<div class="posh"><b id="thh0">Team Hub</b></div>{chips}'+''.join(page(i,t) for i,t in enumerate(H))+'</section>'
css=''.join(f'#th-{i}:checked~.thc0 label[for="th-{i}"]{{background:var(--chalk);color:var(--ink);border-color:var(--chalk)}}#th-{i}:checked~.thpg-{i}{{display:block}}' for i in range(len(H)))
open(P+'th_section.html','w',encoding='utf-8').write(sec_);open(P+'th_css.css','w',encoding='utf-8').write(css)
if __name__=='__main__':print('team hub',len(sec_)//1000,'KB')
