import os as _dt_os;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'
# Assemble standings.html from head + data + script, inserting the timeline and position section.
import subprocess,json
P=__DTP__+''
subprocess.run(['python3',P+'pos/build_pos.py'],check=True,stdout=subprocess.DEVNULL)
h=open(P+'new_head.html',encoding='utf-8').read();t=open(P+'new_tail.js',encoding='utf-8').read()
import re as _r0
DONE=int(_r0.search(r'const G=(\d+);',open(P+'data_block.js',encoding='utf-8').read()).group(1))  # last completed week (from data_block)
BYES={5,6,7,8,9,10,11,13,14}  # 2026 NFL weeks with teams on bye (NFL.com schedule release)
import re as _re
_WK=json.loads(_re.search(r'const WK=(\{.*?\});\n',open(P+'data_block.js',encoding='utf-8').read()).group(1))
LTOT=[sum(_WK[t][w][2] for t in _WK) for w in range(DONE)]
_lo,_hi=800,max(LTOT)
# weekly rank of each played week's league total (1 = highest-scoring week so far), shown inside the bar
_WRK={k:1+sum(1 for x in LTOT if x>LTOT[k-1]) for k in range(1,DONE+1)}
# playoff weeks: total points in the championship-bracket games of each round (week 15 wild cards, week 16 semifinals,
# week 17 final + 3rd-place game; two games a round). A finished season's own page shows that season; the current season
# shows the average of past seasons
# (history/raw/<year>/core.json.gz from Sleeper; history/po_extra.json = {"year": {"15": [scores...], ...}} for MFL seasons);
# the highest of the three averages fills its bar, the others fill relative to it
def _po_ref():
    import gzip as _gz,glob as _gl
    acc={}
    _cur=_dt_os.environ.get('DT_SEASON','2026');_seen=set()
    for fz in sorted(_gl.glob(P+'history/raw/*/core.json.gz')+_gl.glob(P+'../../../pipeline/history/raw/*/core.json.gz')):
        yr=fz.split('/')[-2]
        if yr in _seen or (yr==_cur)!=(_dt_os.environ.get('DT_PAST')=='1'):continue
        _seen.add(yr)
        try:
            dd=json.load(_gz.open(fz));base=[q for q in dd if q.endswith('/winners_bracket')][0][:-len('/winners_bracket')]
            ps=dd[base]['settings'].get('playoff_week_start',15)
            for g in dd[base+'/winners_bracket']:
                if g.get('p') not in (None,1,3):continue
                M=dd.get(f"{base}/matchups/{ps+g['r']-1}") or []
                pts={m['roster_id']:m.get('points') for m in M}
                for tt in (g.get('t1'),g.get('t2')):
                    if isinstance(tt,int) and pts.get(tt) is not None:acc.setdefault(14+g['r'],{}).setdefault(yr,[]).append(pts[tt])
        except Exception as ex:print('po ref',fz,ex)
    if _dt_os.path.exists(P+'history/po_extra.json') and _dt_os.environ.get('DT_PAST')!='1':
        for yr,wk in json.load(open(P+'history/po_extra.json')).items():
            for w,v in wk.items():acc.setdefault(int(w),{})[yr]=v
    return {w:(sum(sum(v) for v in ys.values())/len(ys),sorted(ys)) for w,ys in acc.items() if ys}
_POR=_po_ref();_pomx=max([v[0] for v in _POR.values()] or [1])
def _seg(k):
    if k<=DONE:
        v=LTOT[k-1];hp=12+88*(v-_lo)/(_hi-_lo)
        bar=f'<i class="done" style="height:{hp:.1f}%" title="Week {k}: {v:.1f} league points, #{_WRK[k]} of {DONE} weeks"><em class="wrk">{_WRK[k]}</em></i>'
    elif k>=15 and k in _POR:
        av,yrs=_POR[k];hp=100*av/_pomx
        bar=f'<i class="po"></i><i class="por" style="height:{hp:.1f}%" title="Week {k}: {av:.1f} points across the two championship-bracket games{" in "+yrs[0] if _dt_os.environ.get('DT_PAST')=='1' else ", average of "+", ".join(yrs)}"></i>'
    else:
        bar=f'<i class="{"po" if k>=15 else "fut"}"></i>'
    lab=f'<b class="wv">{LTOT[k-1]:.0f}<small>pts</small></b>' if k<=DONE else (f'<b class="wv pov">{_POR[k][0]:.0f}<small>pts</small></b>' if k>=15 and k in _POR else '<b class="wv"></b>')
    return f'<div class="wkc{" bye" if k in BYES else ""}">{lab}<span class="wb">{bar}</span><span>{k}</span></div>'
segs=''.join(_seg(k) for k in range(1,18))
d=open(P+'data_block.js',encoding='utf-8').read().replace('// remaining schedule: [week, opp, projScore, oppProj, winPct] (app projections as of Oct 15)','// remaining schedule: [week, opp, ...] (only week and opponent are shown)')
import json;sp0=__import__('subprocess');sp0.run(['python3',P+'lb_build.py'],check=True,stdout=sp0.DEVNULL)
h=h.replace('LB_SECTION',open(P+'lb_section.html',encoding='utf-8').read()).replace('LB_CSS',open(P+'lb_css.css',encoding='utf-8').read())
sp0.run(['python3',P+'cmp_build.py'],check=True,stdout=sp0.DEVNULL)
h=h.replace('CMP_SECTION',open(P+'cmp_section.html',encoding='utf-8').read()).replace('CMP_CSS',open(P+'cmp_css.css',encoding='utf-8').read())
sp0.run(['python3',P+'mu_build.py'],check=True,stdout=sp0.DEVNULL)
h=h.replace('MU_SECTION',open(P+'mu_section.html',encoding='utf-8').read()).replace('MU_CSS',open(P+'mu_css.css',encoding='utf-8').read())
sp0.run(['python3',P+'ro_build.py'],check=True,stdout=sp0.DEVNULL)
h=h.replace('RO_SECTION',open(P+'ro_section.html',encoding='utf-8').read()).replace('RO_CSS',open(P+'ro_css.css',encoding='utf-8').read())
sp0.run(['python3',P+'sx_build.py'],check=True,stdout=sp0.DEVNULL)
sp0.run(['python3',P+'po_build.py'],check=True,stdout=sp0.DEVNULL)
h=h.replace('PO_SECTION',open(P+'po_section.html',encoding='utf-8').read()).replace('PO_CSS',open(P+'po_css.css',encoding='utf-8').read())
h=h.replace('SX_SECTION',open(P+'sx_section.html',encoding='utf-8').read()).replace('SX_CSS',open(P+'sx_css.css',encoding='utf-8').read())
# Team Hub is switched by pipeline/features.json ("teamhub": true/false). Off = not built and not on the page
# (tab, pane and glossary removed); the code stays in th_build.py / th_charts.py, ready to switch back on.
_TH_OFF=False
_FT=json.load(open(P+'features.json')) if _dt_os.path.exists(P+'features.json') else {}
if _FT.get('teamhub',True):
    sp0.run(['python3',P+'th_build.py'],check=True,stdout=sp0.DEVNULL)
    h=h.replace('TH_SECTION',open(P+'th_section.html',encoding='utf-8').read()).replace('TH_CSS',open(P+'th_css.css',encoding='utf-8').read())
else:
    _TH_OFF=True
    import re as _re_th
    h=_re_th.sub(r'  <div class="pane pane-th">.*?\n  </div>\n(?=  <div class="pane pane-po">)','',h,flags=_re_th.S)
    h=h.replace('<label for="tab-th" class="tpo">Team Hub</label>','').replace('<input type="radio" name="tab" id="tab-th" class="lr tabr">','').replace('TH_CSS','')
# Players tab: top 50 NFL players by position (pull_top.json). Inserted beside Playoffs; skipped if the pull is missing.
_PL=_dt_os.path.exists(P+'pull_top.json')
if _PL:
    sp0.run(['python3',P+'pl_build.py'],check=True,stdout=sp0.DEVNULL)
    _GL='<div class="glw"><span>Glossary</span><div class="pseg glc" role="group" aria-label="Glossary"><label for="gl-h">Hide</label><label for="gl-s">Show</label></div></div>'
    _KEY=('<div class="key"><div><b>Players</b> every NFL player, rostered or not, ranked at his position by season points (half-PPR, league scoring) '
          'or by points per game. Per game needs at least half the completed weeks played. <b>Tile</b> = position rank for the chosen sort. '
          '<b>GP</b> games played, (bye week), then the fantasy team that rosters him or Free agent.</div>'
          '<div><b>Stat line</b> season totals. PA yards-TD-INT, RU carries-yards-TD, REC catches-yards-TD; K FG made/attempted, LNG longest FG, XP made/attempted; '
          'DEF SK sacks, TO takeaways (interceptions + fumble recoveries), TD defensive and return touchdowns, PA points allowed per game.</div></div>')
    h=h.replace('<input type="radio" name="tab" id="tab-po" class="lr tabr">','<input type="radio" name="tab" id="tab-po" class="lr tabr"><input type="radio" name="tab" id="tab-pl" class="lr tabr">',1)
    h=h.replace('<label for="tab-po" class="tpo">Playoffs</label>','<label for="tab-po" class="tpo">Playoffs</label><label for="tab-pl" class="tpo">Players</label>',1)
    h=h.replace('  <div class="pane pane-po">','  <div class="pane pane-pl">\n  '+open(P+'pl_section.html',encoding='utf-8').read()+'\n  '+_GL+'\n  '+_KEY+'\n  </div>\n  <div class="pane pane-po">',1)
    _PLCSS=open(P+'pl_css.css',encoding='utf-8').read()+'#tab-pl:checked~.tabs label[for="tab-pl"]{background:var(--chalk);color:var(--ink);border-color:var(--chalk)}#tab-pl:checked~.pane-pl{display:block}'
if _dt_os.environ.get('DT_PAST')=='1':  # a finished past season: "Final" in place of the countdown
    h=h.replace('<div class="clock"><b>__LEFT__</b><span>weeks left</span></div>','<div class="clock fin"><b>Final</b></div>',1)
    h=h.replace('</style>','.clock.fin b{font-size:34px;letter-spacing:.02em;transform:translateY(1.5px)}</style>',1)
h=h.replace('__LEFT__',str(14-DONE)).replace('__G__',str(DONE))
# title: the gold-and-teal script 'League' artwork in place of the typed word
import base64 as _b64l
if _dt_os.path.exists(P+'league_script.webp'):
    h=h.replace('<h1>The <span class="lgi">League</span>','<h1 style="white-space:nowrap">The <span class="lgi">League</span>',1)
    # sizing lives in the head too: the main stylesheet sits after the 10 MB body, so without this the art paints full-size first
    h=h.replace('<h1 style="white-space:nowrap">','<style>h1 .lgs{height:1.4em;vertical-align:-.448em}@media(max-width:380px){h1 .lgs{height:1.38em!important;vertical-align:-.442em!important}}@media(min-width:430px){h1 .lgs{height:1.65em!important;vertical-align:-.528em!important}}@media(min-width:1100px){h1 .lgs{height:1.85em!important;vertical-align:-.592em!important}}</style><h1 style="white-space:nowrap">',1)
    h=h.replace('<span class="lgi">League</span>','<img class="lgs" alt="League" width="736" height="322" style="display:inline-block;width:auto;height:1.4em;vertical-align:-.448em;margin-left:.06em" src="data:image/webp;base64,'+_b64l.b64encode(open(P+'league_script.webp','rb').read()).decode()+'">',1)
h=h.replace('SEGMENTS',segs).replace('POS_SECTION',open(P+'pos/pos_section.html',encoding='utf-8').read())
import json,subprocess as sp
EF={t:v[:2] for t,v in json.load(open(P+'eff.json')).items()}
d+='// lineup efficiency: [actual PF as % of Max PF (best possible lineup), points left on the bench per week]\nconst EF='+json.dumps(EF)+';\n'
_sk=json.load(open(P+'skill_opt.json'));_sk.pop('_note',None)
SK={t:[round(v['act']/v['opt']*100,2),round((v['opt']-v['act'])/DONE,2)] for t,v in _sk.items()}
d+='// skill-position efficiency: [actual RB/WR/TE/FLEX points as % of the best legal 2RB+2WR+1TE+1FLEX combo from the roster, points per week left on the bench] (Sleeper lineups)\nconst SK='+json.dumps(SK)+';\n'
import importlib,sys as _sy;_sy.path.insert(0,P);import sx_data as _D
_DP={}
for _t in _D.TEAMS:
    _a={k:0.0 for k in ['QB','RB','WR','TE','K','DEF']}
    for _w in range(1,_D.G+1):
        _st,_bn=_D.lineup(_t,_w);_op=_D.optimal(_st+_bn);_ids={q['pid'] for q in _st};_oi={q['pid'] for q in _op}
        _ins=sorted([q for q in _op if q['pid'] not in _ids],key=lambda q:-q['pts']);_outs=sorted([q for q in _st if q['pid'] not in _oi],key=lambda q:q['pts'])
        for _i in _ins:
            _c=[o for o in _outs if o['pos']==_i['pos']] or [o for o in _outs if _i['pos'] in('RB','WR','TE') and o['pos'] in('RB','WR','TE')]
            _o=_c[0];_outs.remove(_o);_a[_i['pos']]+=_i['pts']-_o['pts']
    _DP[_t]=[round(_a[k]/_D.G,2) for k in ['QB','RB','WR','TE','K','DEF']]
d+='// dropped points per week by position [QB,RB,WR,TE,K,DEF]: bench player who should have started minus the starter he replaces, credited to the bench player\'s position\nconst DP='+json.dumps(_DP)+';\n'
import psim as _PSM
_SO0=_PSM.run()['teams']
_SO={_t:[round(sum((k+1)*q for k,q in enumerate(_o['dist']))/100,1),_o['top'],_o['bye'],_o['po']] for _t,_o in _SO0.items()}
_X0=json.load(open(P+'cmp_extra.json',encoding='utf-8'))
_AVR={v:int(k) for k,v in _X0['rn'].items() if _dt_os.path.exists(P+f'avatars/{k}.webp')}
d+='// team logo ids (Sleeper team avatars, .av-N)\nconst AVR='+json.dumps(_AVR,ensure_ascii=False)+';\n'
# FAAB balances (standings card tiles): pull_faab.json from node pull.mjs faab; current season only (the page refreshes them from Sleeper on load)
try:
    _FB=json.load(open(P+'pull_faab.json',encoding='utf-8')) if _dt_os.path.exists(P+'pull_faab.json') and _dt_os.environ.get('DT_PAST')!='1' else None
    try:_RNF={int(k):v for k,v in json.load(open(P+'cmp_extra.json',encoding='utf-8'))['rn'].items()}
    except Exception:import lg as _lgf;_RNF=dict(_lgf.RN)
    if _FB and _FB.get('budget'):
        d+='// FAAB: budget, league id, roster id -> team, dollars left per team\nconst FAABB='+str(int(_FB['budget']))+',FAABL='+json.dumps(str(_FB['league']))+',FAABR='+json.dumps({k:v for k,v in _RNF.items()},ensure_ascii=False)+',FAAB='+json.dumps({_RNF[int(k)]:int(v) for k,v in _FB['left'].items() if int(k) in _RNF},ensure_ascii=False)+';\n'
except Exception as _e:print('faab skipped:',_e)
# standings seed numerals (Jaguars Rivalries art): 1-2 alabaster patch (bye), 3-6 gold glow (playoffs), 7+ white shadow
import base64 as _b64r
_RNI={r:'data:image/webp;base64,'+_b64r.b64encode(open(P+f'ranknum/r{r}.webp','rb').read()).decode() for r in range(1,13) if _dt_os.path.exists(P+f'ranknum/r{r}.webp')}
d+='const RNI='+json.dumps(_RNI)+';\n'

d+='// season-end sim (player-level sim, 20,000 runs): [average finishing seed, % 1st, % bye, % playoffs]\nconst SO='+json.dumps({_t:[round(x,2) for x in v] for _t,v in _SO.items()})+';\n'
import os as _os,base64 as _b64
_LG='';_MIME={'svg':'image/svg+xml','png':'image/png','webp':'image/webp'}
if _os.path.isdir(P+'logos'):
    for _f in sorted(_os.listdir(P+'logos')):
        _t,_,_x=_f.rpartition('.');_x=_x.lower()
        if _x in _MIME and _t.isalpha() and _t.isupper() and 2<=len(_t)<=3:
            _u='data:'+_MIME[_x]+';base64,'+_b64.b64encode(open(P+'logos/'+_f,'rb').read()).decode()
            try:  # shown at about 23x21 CSS px: embed a 72x64 WebP (sharp on 3x screens) instead of the full upload
                from PIL import Image as _Im;import io as _io
                _im=_Im.open(P+'logos/'+_f).convert('RGBA');_im.thumbnail((72,64),_Im.LANCZOS)
                _bb=_io.BytesIO();_im.save(_bb,format='WEBP',quality=90,method=6)
                _u='data:image/webp;base64,'+_b64.b64encode(_bb.getvalue()).decode()
            except Exception:pass
            _LG+=f'.thr .nfl.tm.n-{_t},.cnm b .nfl.tm.n-{_t},.rn>b .nfl.tm.n-{_t},.cnm small .nfl.opp.n-{_t},.tpb .nfl.n-{_t},.ppl .nfl.n-{_t},.wrx .nfl.n-{_t},.dfs .nfl.n-{_t},.ptx .nfl.n-{_t},.pts .nfl.n-{_t}{{background:url("{_u}") center/contain no-repeat!important;box-shadow:none!important;border-radius:0!important;width:22px!important;height:20px!important}}.nfl.tm.n-{_t} .ct,.nfl.opp.n-{_t} .ct,.tpb .nfl.n-{_t} .ct,.ppl .nfl.n-{_t} .ct,.wrx .nfl.n-{_t} .ct,.dfs .nfl.n-{_t} .ct,.ptx .nfl.n-{_t} .ct,.pts .nfl.n-{_t} .ct{{visibility:hidden}}'
# THE WIRE tab (best available players), after Players; needs pull_wire.json
_WR=_dt_os.path.exists(P+'pull_wire.json') and _PL
_WRCSS=''
if _WR:
    sp0.run(['python3',P+'wire_build.py'],check=True,stdout=sp0.DEVNULL)
    h=h.replace('<input type="radio" name="tab" id="tab-pl" class="lr tabr">','<input type="radio" name="tab" id="tab-pl" class="lr tabr"><input type="radio" name="tab" id="tab-wr" class="lr tabr">',1)
    h=h.replace('<label for="tab-pl" class="tpo">Players</label>','<label for="tab-pl" class="tpo">Players</label><label for="tab-wr" class="tpo">The Wire</label>',1)
    h=h.replace('  <div class="pane pane-pl">','  <div class="pane pane-wr">\n  '+open(P+'wire_section.html',encoding='utf-8').read()+'\n  </div>\n  <div class="pane pane-pl">',1)
    # 10 tabs: phones 3 + 3 + 2 + 2 (the last four span half the row), desktop one row of 10
    _WRCSS=(open(P+'wire_css.css',encoding='utf-8').read()+'#tab-wr:checked~.tabs label[for="tab-wr"]{background:var(--chalk);color:var(--ink);border-color:var(--chalk)}#tab-wr:checked~.pane-wr{display:block}'
      '@media(max-width:1099px){nav.tabs>label.tpo{grid-column:span 3!important}}@media(min-width:1100px){nav.tabs{grid-template-columns:repeat(10,minmax(0,1fr))!important}nav.tabs>label,nav.tabs>label.tpo{grid-column:auto / span 1!important}}')
# Drafts tab (every draft since the startup), after The Wire; needs history/drafts.json
_DF=_dt_os.path.exists(P+'history/drafts.json') and _WR
_DFCSS=''
if _DF:
    sp0.run(['python3',P+'draft_build.py'],check=True,stdout=sp0.DEVNULL)
    if _dt_os.path.exists(P+'draft_section.html'):
        h=h.replace('<input type="radio" name="tab" id="tab-wr" class="lr tabr">','<input type="radio" name="tab" id="tab-wr" class="lr tabr"><input type="radio" name="tab" id="tab-df" class="lr tabr">',1)
        h=h.replace('<label for="tab-wr" class="tpo">The Wire</label>','<label for="tab-wr" class="tpo">The Wire</label><label for="tab-df" class="tpo">Drafts</label>',1)
        h=h.replace('  <div class="pane pane-wr">','  <div class="pane pane-df">\n  '+open(P+'draft_section.html',encoding='utf-8').read()+'\n  </div>\n  <div class="pane pane-wr">',1)
        # 11 tabs: phones 3 + 3 + 3 + 2 (Drafts and Team Hub share the last row), desktop one row of 11
        _DFCSS=(open(P+'draft_css.css',encoding='utf-8').read()+'#tab-df:checked~.tabs label[for="tab-df"]{background:var(--chalk);color:var(--ink);border-color:var(--chalk)}#tab-df:checked~.pane-df{display:block}'
          '@media(max-width:1099px){nav.tabs>label.tpo{grid-column:span 2!important}nav.tabs>label[for="tab-df"],nav.tabs>label[for="tab-th"]{grid-column:span 3!important}}'
          '@media(min-width:1100px){nav.tabs{grid-template-columns:repeat(11,minmax(0,1fr))!important}}')
# Paper Trail tab (pick chains + player moves), after Drafts; needs paper_build.py data (BBP history/paper, YILM captures)
_PTCSS=''
_PTA=next((a for a in (('tab-df','Drafts','df'),('tab-wr','The Wire','wr'),('tab-pl','Players','pl')) if f'<label for="{a[0]}" class="tpo">{a[1]}</label>' in h),None)  # after Drafts, else the last Front Office tab built
if _dt_os.path.exists(P+'paper_build.py') and _PTA:
    if sp0.run(['python3',P+'paper_build.py'],stdout=sp0.DEVNULL).returncode==0 and _dt_os.path.exists(P+'paper_section.html'):
        _t,_l,_c=_PTA
        h=h.replace(f'<input type="radio" name="tab" id="{_t}" class="lr tabr">',f'<input type="radio" name="tab" id="{_t}" class="lr tabr"><input type="radio" name="tab" id="tab-pt" class="lr tabr">',1)
        h=h.replace(f'<label for="{_t}" class="tpo">{_l}</label>',f'<label for="{_t}" class="tpo">{_l}</label><label for="tab-pt" class="tpo">Paper Trail</label>',1)
        h=h.replace(f'  <div class="pane pane-{_c}">','  <div class="pane pane-pt">\n  '+open(P+'paper_section.html',encoding='utf-8').read()+f'\n  </div>\n  <div class="pane pane-{_c}">',1)
        _PTCSS=open(P+'paper_css.css',encoding='utf-8').read()+'#tab-pt:checked~.pane-pt{display:block}'
# ---------- navigation groups (Nicklaus, 2026-11-03): the 11 tab buttons become 3 groups (nav.tabs, existing button
# component) + a sub-tab row of the active group's tabs (.lbc pills, as in Stats). Group radios sit just before the
# sticky .tnav band so CSS can show the right sub-tabs; new_tail.js keeps group and tab in step (and handles #hash links).
def _navgroups(h):
    import re as _re
    m=_re.search(r'<nav class="tabs" aria-label="Sections">(.*?)</nav>',h,_re.S)
    if not m:return h
    labs=dict((a,b) for a,b in _re.findall(r'<label for="(tab-[a-z]+)"[^>]*>([^<]+)</label>',m.group(1)))
    GR=[('gd','Game Day',['tab-st','tab-mu','tab-po']),('fo','Front Office',['tab-ro','tab-pl','tab-wr','tab-df','tab-pt']),('lab','The Lab',['tab-sx','tab-lb','tab-cm','tab-th'])]  # order 2026-11-05
    GR=[(g,n,[t for t in ts if t in labs]) for g,n,ts in GR];GR=[x for x in GR if x[2]]
    po=1 if (DONE>=14 and _dt_os.environ.get('DT_PAST')!='1') else 0
    rad=''.join(f'<input type="radio" name="tgrp" id="grp-{g}" class="lr tgr"{" checked" if i==0 else ""}>' for i,(g,n,ts) in enumerate(GR))
    top='<nav class="tabs" role="tablist" aria-label="Sections">'+''.join(f'<label for="grp-{g}" role="tab" id="gtab-{g}">{n}</label>' for g,n,ts in GR)+'</nav>'
    sub='<div class="lbc tsub" role="tablist" aria-label="Pages">'+''.join(f'<label for="{t}" role="tab" class="g-{g}">{labs[t]}</label>' for g,n,ts in GR for t in ts)+'</div>'
    return h[:m.start()]+rad+f'<div class="tnav" data-po="{po}">'+top+sub+'</div>'+h[m.end():]
h=_navgroups(h)
_i=h.rindex('</style>');h=h[:_i]+open(P+'readability.css',encoding='utf-8').read()+_LG+(_PLCSS if _PL else '')+_WRCSS+_DFCSS+_PTCSS+('.tabs label.tpo{grid-column:1 / -1!important}' if _TH_OFF and not _PL else '.tabs label.tpo{grid-column:span 2!important}' if not _TH_OFF and _PL else '')+h[_i:]
open(P+'standings.html','w',encoding='utf-8').write(h+d+t)
