#!/usr/bin/env python3
"""One-off (BBP, 2026-11-17, brief irtaxi): apply pipeline/irtx.json to completed weeks already written by full_update.py.
  python3 tools/irtx_apply.py 8 9 10
For each week: weeks.json 'mx' (best lineup without the players irtx leaves out), cmp_extra.json 'bench' (Bench points
without them); then skill_opt.json (as full_update.py section 3), data_block.js CH and eff.json (season.build) for all
completed weeks. Prints every change. Other data_block constants are checked unchanged. Never fatal for a missing file."""
import sys,os,json,re,io,contextlib
P=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'pipeline')+'/'
sys.path.insert(0,P);os.chdir(P)
import irtx
WEEKS=[int(x) for x in sys.argv[1:]]
L=lambda f:json.load(open(P+f,encoding='utf-8'))
HI=L('hist.json');WJ=L('weeks.json');X=L('cmp_extra.json')
with contextlib.redirect_stdout(io.StringIO()):import season
RN=season.RN
def optimal(pool):   # = full_update.py section 1
    by={}
    for q in pool:by.setdefault(q['pos'],[]).append(q)
    for k in by:by[k].sort(key=lambda q:-q['pts'])
    g=lambda p_,n:by.get(p_,[])[:n]
    fl=sorted(by.get('RB',[])[2:]+by.get('WR',[])[2:]+by.get('TE',[])[1:],key=lambda q:-q['pts'])[:1]
    return g('QB',1)+g('RB',2)+g('WR',2)+g('TE',1)+fl+g('K',1)+g('DEF',1)
def par(sx):
    o=[]
    for x in sx.split(','):
        if not x:continue
        f=x.split('|');o.append({'pid':f[0],'pos':HI['m'][f[0]][0],'pts':float(f[3]),'nfl':f[1]})
    return o
for w in WEEKS:
    for rid,v in HI['w'][str(w)].items():
        st,bn=par(v[2]),par(v[3]);xo=irtx.out(w,rid,[(q['pid'],q['nfl']) for q in bn],{q['pid'] for q in st})
        mx=round(sum(q['pts'] for q in optimal([q for q in st+bn if q['pid'] not in xo and q['pid'] not in ('0','')])),2)
        old=WJ[str(w)]['mx'][rid]
        assert mx>=WJ[str(w)]['act'][rid]-1e-9
        b=round(sum(q['pts'] for q in bn if q['pid'] not in xo),2);t=RN[int(rid)];ob=X['bench'][t][w-1]
        if mx!=old or b!=ob:print(f'W{w} {t:24} Max PF {old:.2f} -> {mx:.2f}   Bench {ob:.2f} -> {b:.2f}   out {sorted(xo.items())}')
        WJ[str(w)]['mx'][rid]=mx;X['bench'][t][w-1]=b
json.dump(WJ,open(P+'weeks.json','w'))
json.dump(X,open(P+'cmp_extra.json','w'),ensure_ascii=False)
# skill_opt.json, as full_update.py section 3
G=int(re.search(r'const G=(\d+);',open(P+'data_block.js',encoding='utf-8').read()).group(1))
F={'RB','WR','TE'};sk={}
for w in range(1,G+1):
    for rid,v in HI['w'][str(w)].items():
        st_,bn_=par(v[2]),par(v[3])
        _x=irtx.out(w,rid,[(q['pid'],q['nfl']) for q in bn_],{q['pid'] for q in st_});bn_=[q for q in bn_ if q['pid'] not in _x]
        pool=[q for q in st_+bn_ if q['pos'] in F];by={}
        for q in pool:by.setdefault(q['pos'],[]).append(q['pts'])
        for k in by:by[k].sort(reverse=True)
        best=sum(by.get('RB',[])[:2])+sum(by.get('WR',[])[:2])+sum(by.get('TE',[])[:1])+max(by.get('RB',[])[2:3]+by.get('WR',[])[2:3]+by.get('TE',[])[1:2]+[0])
        actv=sum(q['pts'] for q in st_ if q['pos'] in F)
        e=sk.setdefault(rid,{'act':0,'opt':0,'hits':0,'wk':[]});e['act']+=actv;e['opt']+=best;e['wk'].append(round(best-actv,2));e['hits']+=abs(best-actv)<0.005
SK0=L('skill_opt.json');SK={'_note':SK0['_note']}
for rid,e in sk.items():SK[RN[int(rid)]]={'act':round(e['act'],2),'opt':round(e['opt'],2),'hits':e['hits'],'wk':e['wk']}
for t in SK:
    if t!='_note' and SK[t]!=SK0.get(t):print('skill_opt',t,SK0[t]['opt'],'->',SK[t]['opt'],'hits',SK0[t]['hits'],'->',SK[t]['hits'])
json.dump(SK,open(P+'skill_opt.json','w'))
# data_block.js CH, eff.json
import importlib;importlib.reload(season)
D=season.build(G);s=open(P+'data_block.js',encoding='utf-8').read()
def C(k,v):return f'const {k}='+json.dumps(v,ensure_ascii=False,separators=(',',':'))+';\n'
for k in ('T','H','M','WK','PH','PM','POS'):
    old=json.loads(re.search(r'const '+k+r'=(.*?);\n',s).group(1))
    if old!=json.loads(json.dumps(D[k])):print('WARNING irtx_apply: data_block',k,'differs; left as it was',file=sys.stderr)
oc=json.loads(re.search(r'const CH=(.*?);\n',s).group(1))
for t in D['CH']:
    if list(D['CH'][t])!=list(oc[t]):print('CH',t,oc[t],'->',D['CH'][t])
s=re.sub(r'const CH=.*?;\n',lambda m:C('CH',D['CH']),s,count=1)
open(P+'data_block.js','w',encoding='utf-8').write(s)
oe=L('eff.json')
for t in D['EFF']:
    if list(D['EFF'][t])!=list(oe[t]):print('EFF',t,oe[t],'->',D['EFF'][t])
json.dump(D['EFF'],open(P+'eff.json','w'),indent=0)
print('done')
