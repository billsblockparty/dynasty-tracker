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
def _seg(k):
    if k<=DONE:
        v=LTOT[k-1];hp=12+88*(v-_lo)/(_hi-_lo)
        bar=f'<i class="done" style="height:{hp:.1f}%" title="Week {k}: {v:.1f} league points"></i>'
    else:
        bar=f'<i class="{"po" if k>=15 else "fut"}"></i>'
    lab=f'<b class="wv">{LTOT[k-1]:.0f}<small>pts</small></b>' if k<=DONE else '<b class="wv"></b>'
    return f'<div class="wkc{" bye" if k in BYES else ""}">{lab}<span class="wb">{bar}</span><span>{k}</span></div>'
segs=''.join(_seg(k) for k in range(1,18))
d=open(P+'data_block.js',encoding='utf-8').read().replace('// remaining schedule: [week, opp, projScore, oppProj, winPct] (app projections as of Oct 15)','// remaining schedule: [week, opp, ...] (only week and opponent are shown)')
sp0=__import__('subprocess');sp0.run(['python3',P+'lb_build.py'],check=True,stdout=sp0.DEVNULL)
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
h=h.replace('__LEFT__',str(14-DONE)).replace('__G__',str(DONE))
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
open(P+'standings.html','w',encoding='utf-8').write(h+d+t)
