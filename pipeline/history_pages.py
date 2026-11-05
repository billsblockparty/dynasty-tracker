import os as _dt_os;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'
# Archive pages for the MyFantasyLeague seasons (2021-2024): site/<year>/index.html, linked from the season buttons.
# Built from history/mfl_<year>.json (weekly scores, standings, playoffs), history/summary.json (seeds, finishes) and
# history/drafts.json, with the live site's stylesheet (site/index.html) so they look the same.
# Sections: champion, final standings, playoffs, weekly results (week picker), that year's draft.
import json,html,re,os,statistics as st
P=__DTP__;SITE=os.path.join(P,'..','site')
e=html.escape
H=P+'history/'
if not os.path.exists(os.path.join(SITE,'index.html')):raise SystemExit('history pages: no site/index.html yet')
TM=json.load(open(H+'teams.json',encoding='utf-8'))['mfl']
SUM=json.load(open(H+'summary.json',encoding='utf-8'))['seasons']
try:CH=json.load(open(P+'champions.json',encoding='utf-8'))
except Exception:CH={}
try:OWN=json.load(open(P+'owners.json',encoding='utf-8'))
except Exception:OWN={}
import sys;sys.path.insert(0,P)
import draft_build as DB
idx=open(os.path.join(SITE,'index.html'),encoding='utf-8').read()
STY=''.join(re.findall(r'<style>.*?</style>',idx,flags=re.S))
LINKS=''.join(re.findall(r'<link [^>]*>',idx.split('</head>')[0]))
m=re.search(r'const AVR=(\{.*?\});',idx);AVR=json.loads(m.group(1)) if m else {}
LGS=re.search(r'<img class="lgs"[^>]*>',idx);LGS=LGS.group(0) if LGS else ''
YRS=sorted({y for y in CH}|{'2025','2026'}|{y for y in ('2021','2022','2023','2024') if os.path.exists(H+f'mfl_{y}.json')})
CUR='2026'
def nav(Y):
    def yb(y):
        t=CH.get(y);o=OWN.get(t) if t else None
        cap=(f'<small><span class="cf">{e(t)}</span><span class="cs">{e(o or t)}</span></small>' if t else (f'<small><span class="cf">In progress</span><span class="cs">Now</span></small>' if y==CUR else '<small></small>'))
        href='../' if y==CUR else f'../{y}/'
        return f'<a class="yb{" on" if y==Y else ""}" href="{href}"'+(' aria-current="page"' if y==Y else '')+f'><b>{y}</b>{cap}</a>'
    return f'<nav class="yrs n{len(YRS)}" aria-label="Season">'+''.join(yb(y) for y in YRS)+'</nav>'
def av(t):r=AVR.get(t);return f'<i class="av hav av-{r}" aria-hidden="true"></i>' if r else '<i class="av hav nl" aria-hidden="true"></i>'
def ordn(n):return f'{n}{"th" if 10<=n%100<=20 else {1:"st",2:"nd",3:"rd"}.get(n%10,"th")}'
CSS="""
.hxp{display:flex;flex-direction:column;gap:16px;margin-top:6px}
.hxc{background:var(--deck);border:1px solid var(--line);border-radius:14px;box-shadow:var(--sh-hard);padding:12px 14px}
.hxh{display:flex;align-items:baseline;justify-content:space-between;gap:10px;margin:0 0 10px}
.hxh b{font:700 17px/1.1 var(--display);letter-spacing:.06em;text-transform:uppercase;color:var(--chalk)}
.hxh span{font-size:12px;color:var(--steel)}
.hav{display:inline-block;flex:none;width:30px;height:30px;border-radius:50%;background-color:var(--deck-2);background-position:center;background-size:cover;background-repeat:no-repeat;box-shadow:0 0 0 1px var(--line-strong)}
.hav.nl{visibility:hidden}
.hxw{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}
.hxw>div{display:flex;flex-direction:column;align-items:center;gap:6px;text-align:center;padding:10px 4px;border-radius:10px;background:var(--deck-2);box-shadow:var(--sh-hard)}
.hxw .hav{width:46px;height:46px}
.hxw em{font:700 11px/1 var(--display);font-style:normal;letter-spacing:.1em;text-transform:uppercase;color:var(--label)}
.hxw .w1 em{color:#c9a15a}
.hxw b{font:700 14px/1.1 var(--display);letter-spacing:.02em;color:var(--chalk)}
.hxw small{font-size:11.5px;color:var(--steel)}
.hxs{display:grid;grid-template-columns:24px 30px minmax(0,1fr) 40px 50px 50px;column-gap:8px;align-items:center;min-height:44px;padding:5px 0;border-top:1px solid var(--line)}
.hxs.hd{min-height:0;padding-bottom:6px;border-top:0;font:700 10.5px/1 var(--display);letter-spacing:.08em;text-transform:uppercase;color:var(--label)}
.hxs.hd span:nth-child(n+4){text-align:right}
.hxs .sd{font:700 18px/1 var(--display);color:var(--steel);text-align:center}
.hxs.po .sd{color:#c9a15a}
.hxs .tn{min-width:0;display:flex;flex-direction:column;gap:2px}
.hxs .tn b{overflow-wrap:normal;font:600 14.5px/1.15 var(--body);color:var(--chalk)}
.hxs .tn small{overflow:hidden;white-space:nowrap;font-size:11.5px;color:var(--steel)}
.hxs .v{text-align:right;font:600 14px/1 var(--body);color:var(--label);font-variant-numeric:tabular-nums}
.hxs .v.rec{color:var(--chalk)}
.hxf{display:inline-block;margin-top:2px;font:700 10px/1 var(--display);letter-spacing:.08em;text-transform:uppercase;color:#c9a15a}
.hxg{display:grid;grid-template-columns:minmax(0,1fr) auto minmax(0,1fr);gap:8px;align-items:center;padding:9px 0;border-top:1px solid var(--line)}
.hxg:first-of-type{border-top:0}
.hxg .t{display:flex;align-items:center;gap:7px;min-width:0}
.hxg .t.b{flex-direction:row-reverse;text-align:right}
.hxg .t span{display:flex;flex-direction:column;min-width:0}
.hxg .t span b{overflow-wrap:normal;font:600 14px/1.15 var(--body);color:var(--label)}
.hxg .t span small{font-size:11px;color:var(--steel)}
.hxg .t.win span b{color:var(--chalk)}
.hxg .sc{font:700 16px/1 var(--display);color:var(--label);font-variant-numeric:tabular-nums;white-space:nowrap}
.hxg .sc i{font-style:normal;color:var(--steel);margin:0 5px}
.hxg .sc .win{color:var(--chalk)}
.hxr{font:700 11.5px/1 var(--display);letter-spacing:.1em;text-transform:uppercase;color:var(--label);margin:12px 0 2px}
.hxr:first-child{margin-top:0}
.clock.fin b{font-size:34px;letter-spacing:.02em}
header .eyebrow{white-space:normal}
.hxwk{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:6px;margin:0 0 10px}
.hxwk label{display:flex;align-items:center;justify-content:center;height:32px;border-radius:8px;border:1px solid var(--line);background:var(--deck-2);box-shadow:var(--sh-hard);cursor:pointer;font:700 13px/1 var(--display);color:var(--label)}
.hxwp{display:none}
@media(max-width:380px){.hxs{grid-template-columns:20px 26px minmax(0,1fr) 38px 46px 46px;column-gap:6px}.hxs .tn b{font-size:13.5px}.hxs .v{font-size:13px}}
"""
def page(Y):
    d=json.load(open(H+f'mfl_{Y}.json',encoding='utf-8'));S=SUM[Y]
    FR={fid:nm.replace('’',"'") for fid,nm in d['fr']}
    cur=lambda fid:TM.get(fid,fid)
    def who(fid,small=True):
        t=cur(fid);o=OWN.get(t,'')
        return f'<span><b>{e(FR.get(fid,t))}</b>'+(f'<small>{e(o)}</small>' if small and o else '')+'</span>'
    id_by_cur={TM[k]:k for k in TM}
    # champion, runner-up, 3rd
    fin={v['finish']:k for k,v in S.items()}
    pod=''.join(f'<div class="w{i}">{av(fin[f])}<em>{lab}</em><b>{e(FR.get(id_by_cur.get(fin[f]),fin[f]))}</b><small>{e(OWN.get(fin[f],""))}</small></div>'
                for i,(f,lab) in enumerate((('Champion','Champion'),('Runner-up','Runner-up'),('3rd','3rd place')),1) if f in fin)
    # final standings: seed order, with the playoff finish
    PFR={k:1+sum(1 for o in S if S[o]['pf']>S[k]['pf']) for k in S}
    rows=''.join(f'<div class="hxs{" po" if v["po"] else ""}"><span class="sd">{v["seed"]}</span>{av(k)}<span class="tn"><b>{e(FR.get(id_by_cur.get(k),k))}</b><small>{e(OWN.get(k,""))}'
                 +(f' · <i class="hxf">{e(v["finish"])}</i>' if v['finish'] not in ('Missed','Playoffs') else '')+f'</small></span>'
                 f'<span class="v rec">{v["w"]}-{v["l"]}{"-"+str(v["t"]) if v["t"] else ""}</span><span class="v">{v["pf"]:.0f}</span><span class="v">{v["pa"]:.0f}</span></div>'
                 for k,v in sorted(S.items(),key=lambda kv:kv[1]['seed']))
    stand=('<div class="hxs hd"><span></span><span></span><span>Team · seed</span><span>W-L</span><span>PF</span><span>PA</span></div>'+rows)
    def game(m):
        a,b=m['f'][0],m['f'][1];wa=a['score']>b['score'];wb=b['score']>a['score']
        n=lambda x:f'{x:.2f}'.rstrip('0').rstrip('.') if isinstance(x,float) else str(x)
        return (f'<div class="hxg"><span class="t{" win" if wa else ""}">{av(cur(a["id"]))}{who(a["id"])}</span>'
                f'<span class="sc"><span class="{"win" if wa else ""}">{n(a["score"])}</span><i>–</i><span class="{"win" if wb else ""}">{n(b["score"])}</span></span>'
                f'<span class="t b{" win" if wb else ""}">{av(cur(b["id"]))}{who(b["id"])}</span></div>')
    lr=d['lastRegular']
    po=''
    names={1:'Wild card',2:'Semifinals',3:'Final & 3rd place'}
    pot={cur(k) for k in TM}  # all teams
    pos_=[k for k,v in S.items() if v['po']]
    for r in (1,2,3):
        G=[m for m in d['weeks'].get(str(lr+r),[]) if not m['reg'] and all(cur(f['id']) in pos_ for f in m['f'])]
        if G:po+=f'<div class="hxr">Week {lr+r} · {names[r]}</div>'+''.join(game(m) for m in G)
    wks=[w for w in range(1,lr+1) if d['weeks'].get(str(w))]
    radios=''.join(f'<input type="radio" name="hw" id="hw-{w}" class="lr"{" checked" if w==wks[-1] else ""}>' for w in wks)
    wsel='<div class="hxwk" role="group" aria-label="Week">'+''.join(f'<label for="hw-{w}">{w}</label>' for w in wks)+'</div>'
    wp=''.join(f'<div class="hxwp hxwp-{w}">'+''.join(game(m) for m in d['weeks'][str(w)] if m['reg'])+'</div>' for w in wks)
    wcss=''.join(f'#hw-{w}:checked~.hxwk label[for="hw-{w}"]{{background:var(--chalk);color:var(--ink);border-color:var(--chalk)}}#hw-{w}:checked~.hxwp-{w}{{display:block}}' for w in wks)
    ds=DB.section(years=[Y],idp='hd')
    dsec=(ds[0] if ds else '');dcss=(DB.CSS+ds[1] if ds else '')
    body=(f'<div class="wrap">{nav(Y)}<header><div class="eyebrow">Official · {Y} season · MyFantasyLeague</div>'
          f'<h1 style="white-space:nowrap">The {LGS}</h1><div class="clock fin"><b>Final</b></div></header>'
          f'<div class="hxp">'
          f'<div class="hxc"><div class="hxh"><b>{Y} champion</b><span>{e(CH.get(Y,""))}</span></div><div class="hxw">{pod}</div></div>'
          f'<div class="hxc"><div class="hxh"><b>Final standings</b><span>regular-season seed · gold = playoff team</span></div>{stand}</div>'
          f'<div class="hxc"><div class="hxh"><b>Playoffs</b><span>championship bracket</span></div>{po}</div>'
          f'<div class="hxc">{radios}<div class="hxh"><b>Weekly results</b><span>regular season · Weeks 1–{lr}</span></div>{wsel}{wp}</div>'
          f'<div class="hxc">{dsec}</div>'
          f'<div class="key"><div><b>{Y} archive</b> the season as it was played on MyFantasyLeague: team names are that season\'s, with today\'s owners underneath. '
          'Scores and standings come from MFL\'s own records.</div></div></div></div>')
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=0.85, viewport-fit=cover">\n'
            f'<meta name="robots" content="noindex">\n<title>The League · {Y}</title>\n{LINKS}{STY}<style>{CSS}{wcss}{dcss}.yrs a.yb{{cursor:pointer}}</style>\n</head>\n<body>{body}'
            '<script>var AVR='+json.dumps(AVR)+';document.querySelectorAll(".pav[data-avt]").forEach(function(e){var r=AVR[e.dataset.avt];if(r)e.classList.add("av","av-"+r);else e.classList.add("nl")})</script>'
            '<script>(function(){function f(){document.querySelectorAll(".dfpl b").forEach(function(b){b.style.fontSize="";var p=b.parentElement,s=parseFloat(getComputedStyle(b).fontSize);while(p.scrollWidth>p.clientWidth+.5&&s>11){s-=.5;b.style.fontSize=s+"px"}});document.querySelectorAll(".hxg .t span b,.hxs .tn b").forEach(function(b){b.style.fontSize="";var s=parseFloat(getComputedStyle(b).fontSize);while(b.scrollWidth>b.clientWidth+.5&&s>10){s-=.5;b.style.fontSize=s+"px"}})}f();addEventListener("resize",function(){requestAnimationFrame(f)});document.addEventListener("change",function(){requestAnimationFrame(f)});document.fonts&&document.fonts.ready.then(f)})()</script>'
            '</body>\n</html>\n')
n=0
for Y in ('2021','2022','2023','2024'):
    if Y not in SUM or not os.path.exists(H+f'mfl_{Y}.json'):continue
    os.makedirs(os.path.join(SITE,Y),exist_ok=True)
    open(os.path.join(SITE,Y,'index.html'),'w',encoding='utf-8').write(page(Y));n+=1
print('history pages:',n)
