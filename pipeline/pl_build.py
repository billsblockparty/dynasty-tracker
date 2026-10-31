import os as _dt_os;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'
# Builds the "Players" tab: top 50 NFL players at each position (rostered or not) by season points or points per game,
# with games played, bye, fantasy owner and a season stat line. Data: pull_top.json (node pull.mjs top D).
# CSS-only: position radios (pl-qb..pl-def) and sort radios (pl-sp / pl-sg); rows carry both ranks and are reordered with
# CSS order, rows outside the top 50 for the active sort are hidden.
import json,html,math
from datetime import date
P=__DTP__
e=html.escape
X=json.load(open(P+'pull_top.json',encoding='utf-8'))
D,MIN,PL=X['D'],X['minGp'],X['P']
import sys;sys.path.insert(0,P);from nfl_colors import badge_c as badge
BYE=json.load(open(P+'ro_ranks.json',encoding='utf-8')).get('_bye',{})
RN={int(k):v for k,v in json.load(open(P+'cmp_extra.json',encoding='utf-8'))['rn'].items()}
SHORT0={"Team Ram Rod":"Ram Rod","Bill's Block Party":"Block Party","Homer's Heroes":"Homer's","Mandingoes":"Mandingoes","Team RIPMFL":"RIPMFL","Cheating is Trying":"Cheating","Convicts":"Convicts","Nuts in the Face":"Nuts","Reverse Apache Master":"Apache","Canton waitlist":"Canton"}
ORD=['QB','RB','WR','TE','K','DEF'];TOP=50
NAMES={'QB':'Quarterbacks','RB':'Running backs','WR':'Wide receivers','TE':'Tight ends','K':'Kickers','DEF':'Defenses'}
def nmh(name,pos):
    parts=name.split(' ',1)
    if pos=='DEF' and len(parts)==2 or pos=='DEF' and name.count(' ')>=1:
        city,nick=name.rsplit(' ',1);return f'<span class="nmx"><span class="dc">{e(city)} </span>{e(nick)}</span>'
    if len(parts)<2 or len(name)<14:return f'<span class="nmx">{e(name)}</span>'
    return f'<span class="nmx lg"><span class="fn">{e(parts[0])} </span><span class="fi">{e(parts[0][0])}. </span>{e(parts[1])}</span>'
def age(b):
    if not b:return None
    y,m,d=map(int,b.split('-'));return (date.today()-date(y,m,d)).days/365.25
def acl(a):return 'ay' if a<27 else 'ap' if a<31 else 'ao'
def n(v):v=v or 0;return str(int(v)) if float(v).is_integer() else f'{v:.1f}'
def nn(x):return f'(−{n(-x)})' if x<0 else n(x)
def grp(lab,nums):return f'<span class="sit"><u>{lab}</u> {"-".join(nn(x) for x in nums)}</span>'
def td3(a,b,c):return [a,b]+([c] if c else [])
def statline(pos,t,gp):
    g=lambda k:t.get(k,0) or 0
    if pos=='QB':o=[grp('PA',[g('pass_yd'),g('pass_td')]+([g('pass_int')] if g('pass_int') else []))]+([grp('RU',td3(g('rush_att'),g('rush_yd'),g('rush_td')))] if g('rush_att') else [])
    elif pos=='RB':o=([grp('RU',td3(g('rush_att'),g('rush_yd'),g('rush_td')))] if g('rush_att') else [])+([grp('REC',td3(g('rec'),g('rec_yd'),g('rec_td')))] if g('rec') else [])
    elif pos in('WR','TE'):o=([grp('REC',td3(g('rec'),g('rec_yd'),g('rec_td')))] if g('rec') else [])+([grp('RU',td3(g('rush_att'),g('rush_yd'),g('rush_td')))] if g('rush_att') else [])
    elif pos=='K':o=[f'<span class="sit"><u>FG</u> {n(g("fgm"))}/{n(g("fga"))}</span>']+([f'<span class="sit"><u>LNG</u> {n(g("fgm_lng"))}</span>'] if g('fgm_lng') else [])+[f'<span class="sit"><u>XP</u> {n(g("xpm"))}/{n(g("xpa"))}</span>']
    else:
        tds=g('def_td')+g('def_st_td')
        o=[f'<span class="sit"><u>SK</u> {n(g("sack"))}</span>',f'<span class="sit"><u>TO</u> {n(g("int")+g("fum_rec"))}</span>']+([f'<span class="sit"><u>TD</u> {n(tds)}</span>'] if tds else [])+[f'<span class="sit"><u>PA</u> {g("pts_allow")/gp:.1f}<u>/g</u></span>']
    return '<i class="sd">·</i>'.join(o)
def crank(vals):  # competition rank, higher value first
    s=sorted(vals,reverse=True);return lambda v:1+sum(1 for x in s if x>v+1e-9)
rows_by={};chk={}
for pos in ORD:
    L=[]
    for pid,(name,p,nfl,w,t,own,bd) in PL.items():
        if p!=pos:continue
        pl=[v for v in w if v is not None];pts=round(sum(pl),2);gp=len(pl)
        L.append(dict(pid=pid,name=name,nfl=nfl,w=w,t=t,own=own,bd=bd,pts=pts,gp=gp,ppg=pts/gp if gp else 0))
    ra=crank([o['pts'] for o in L]);q=[o for o in L if o['gp']>=MIN];rb=crank([o['ppg'] for o in q])
    for o in L:o['ra']=ra(o['pts']);o['rb']=rb(o['ppg']) if o['gp']>=MIN else None
    rows_by[pos]=sorted(L,key=lambda o:(o['ra'],o['name']))
    chk[pos]=(sum(o['ra']<=TOP and o['pts']>0 for o in L),sum(1 for o in L if o['rb'] and o['rb']<=TOP and o['ppg']>0))
def row(o,pos):
    ina=o['ra']<=TOP and o['pts']>0;inb=o['rb'] is not None and o['rb']<=TOP and o['ppg']>0
    if not(ina or inb):return ''
    by=BYE.get(o['nfl']);bc='past' if by and by<=D else 'now' if by==D+1 else ''
    byh=f'<i class="by {bc}">(<b>{by}</b>)</i>' if by else ''
    a=age(o['bd']);ag=f'<em class="pag {acl(a)}">{a:.1f}</em>' if a and pos!='DEF' else ''
    own=f'<i class="own"><span class="of">{e(RN[o["own"]])}</span><span class="os">{e(SHORT0.get(RN[o["own"]],RN[o["own"]]))}</span></i>' if o['own'] in RN else '<i class="own fa">Free agent</i>'
    cls='rr2 plr'+('' if ina else ' xa')+('' if inb else ' xb')
    sq=f'<i class="pq p-{pos.lower()}"><span class="pqi"><span>{pos}</span><b class="ka">{o["ra"]}</b><b class="kb">{o["rb"] or ""}</b></span></i>'
    nb=badge(o['nfl']).replace('<em class="nfl','<em class="nfl tm',1) if o['nfl'] else ''
    return (f'<div class="{cls}" style="--a:{o["ra"]};--b:{o["rb"] or 999}">{sq}'
            f'<span class="rn"><b>{nmh(o["name"],pos)}{nb}{ag}</b><small><span class="gp">{o["gp"]} GP</span>{byh}{own}</small>'
            f'<span class="pst">{statline(pos,o["t"],o["gp"] or 1)}</span></span>'
            f'<span class="rv">{o["pts"]:.1f}</span><span class="rg2">{o["ppg"]:.1f}</span></div>')
radios=(''.join(f'<input type="radio" name="plp" id="pl-{p.lower()}" class="lr"{" checked" if p=="QB" else ""}>' for p in ORD)
        +'<input type="radio" name="pls" id="pl-sp" class="lr" checked><input type="radio" name="pls" id="pl-sg" class="lr">')
chips='<div class="lbc roc plc" role="tablist" aria-label="Position">'+''.join(f'<label for="pl-{p.lower()}">{p}</label>' for p in ORD)+'</div>'
seg='<div class="pseg plseg" role="group" aria-label="Sort"><label for="pl-sp">Pts</label><label for="pl-sg">Pts/g</label></div>'
blocks=''.join(f'<div class="plb plb-{p.lower()}" role="tabpanel" aria-label="{NAMES[p]}"><div class="rtop"><b>{NAMES[p]}</b><span><span class="pl-pt">Top {min(TOP,chk[p][0])} by points</span><span class="pl-pg">Top {min(TOP,chk[p][1])} by points per game</span></span></div>'
               f'<div class="rcol"><span>Player</span><span class="ca">Pts</span><span class="cb">/g</span></div><div class="pll">'+''.join(row(o,p) for o in rows_by[p])+'</div></div>' for p in ORD)
sec=(f'<section class="plx" aria-labelledby="plh">{radios}<div class="posh"><b id="plh">Players</b></div>'
     f'<div class="rsub">All NFL players · tile = position rank by <span class="pl-pt">points</span><span class="pl-pg">points per game, min. {MIN} games</span> · Wk 1–{D}</div>'
     f'{chips}{seg}{blocks}</section>')
open(P+'pl_section.html','w',encoding='utf-8').write(sec)
ids=[p.lower() for p in ORD]
css=(''.join(f'#pl-{i}:checked~.plc label[for="pl-{i}"]{{background:var(--chalk);color:var(--ink);border-color:var(--chalk)}}#pl-{i}:checked~.plb-{i}{{display:block}}' for i in ids)
 +'#pl-sp:checked~.plseg label[for="pl-sp"],#pl-sg:checked~.plseg label[for="pl-sg"]{background:var(--chalk);color:var(--ink)}'
 +'.plx .plb{display:none}.plx .pll{display:flex;flex-direction:column}.plx .plr{order:var(--a)}#pl-sg:checked~.plb .plr{order:var(--b)}'
 +'#pl-sp:checked~.plb .xa,#pl-sg:checked~.plb .xb{display:none}'
 +'.plx .kb,.plx .pl-pg{display:none}#pl-sg:checked~.plb .kb,#pl-sg:checked~.rsub .pl-pg,#pl-sg:checked~.plb .pl-pg{display:inline}#pl-sg:checked~.plb .ka,#pl-sg:checked~.rsub .pl-pt,#pl-sg:checked~.plb .pl-pt{display:none}'
 +'.plx .plc{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:6px}.plx .plc label{text-align:center;padding-inline:0}'
 +'.plx .plseg{margin:10px 0 12px}'
 +'.plx .rr2{grid-template-columns:minmax(0,1fr) 54px 36px!important}'
 +'@media(max-width:429px){.plx .nmx.lg .fn,.plx .dc{display:none}.plx .nmx.lg .fi{display:inline}}'
 +'@media(max-width:374px){.plx .pag{display:none}.plx .pst{font-size:11px;letter-spacing:-.01em}.plx .pst u{font-size:9px}.plx .pst .sd{margin:0 3px}}'
 +'.plx .rcol{display:grid;grid-template-columns:minmax(0,1fr) 54px 36px;column-gap:8px;padding:0 10px 6px calc(34px + 9px)}'
 +'#pl-sp:checked~.plb .rcol .ca,#pl-sg:checked~.plb .rcol .cb{color:var(--chalk)}#pl-sp:checked~.plb .rv,#pl-sg:checked~.plb .rg2{color:var(--chalk)}#pl-sg:checked~.plb .rv{color:var(--label)}'
 +'.plx .rn small{display:flex;align-items:baseline;gap:0 6px;min-width:0;white-space:nowrap}.plx .own{font-style:normal;color:var(--label);overflow:hidden;text-overflow:ellipsis;min-width:0}.plx .own::before{content:"·";margin-right:6px;color:var(--steel)}.plx .own.fa{color:var(--steel)}'
 +'.plx .os{display:none}@media(max-width:429px){.plx .of{display:none}.plx .os{display:inline}}'
 +'.plx .rn{overflow:visible}.plx .pst{width:calc(100% + 106px);box-sizing:border-box}'
 +'.plx .pst{display:block;margin-top:3px;font-size:12px;line-height:16px;color:var(--label);white-space:nowrap}.plx .pst u{text-decoration:none;font-size:10px;color:var(--steel);margin-right:2px}.plx .pst .sd{font-style:normal;color:var(--steel);margin:0 6px}')
open(P+'pl_css.css','w',encoding='utf-8').write(css)
print('players tab:',{p:chk[p] for p in ORD},'| bytes',len(sec))
