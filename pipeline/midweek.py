import os as _dt_os;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'
# Mid-week refresh: python3 midweek.py G   (after `node pull.mjs midweek G`; G = last completed week in the files)
# A weekly-mode run with no newly completed week (the daily 8:30 AM ET run, a code push) used to skip every roster file,
# so adds, drops, trades, IR / taxi moves reached the page only at the next completed-week pull (2026-11-12). This writes,
# from the current Sleeper rosters and week G+1 matchups / projections:
#   rosters.json, ro_ranks.json, ro_pg.json (roster_files.rosters, as full_update.py section 4)
#   wk<G+1>.json (roster_files.lineups with the existing file: its live scores, done / live / left, and the team of any
#     player who has already played this week are kept), kick.json[G+1]
#   data_block.js FUT: week G+1 projected totals and win % from the current lineups (full_update.py's formula); nothing
#     else in data_block.js changes
#   cmp_extra.json age for players new to the files
# Completed weeks (hist.json, weeks.json, wk<=G>.json, pos.csv, pull_pts.json, data_block.js T/H/WK/...) are not touched.
# Prints a roster check (Sleeper rosters vs rosters.json and wk<G+1>.json); warns, never stops.
import json,re,sys,math,ast
P=__DTP__;sys.path.insert(0,P)
L=lambda f:json.load(open(P+f,encoding='utf-8'))
DONE=int(sys.argv[1]);NOW=DONE+1
G=int(re.search(r'const G=(\d+);',open(P+'data_block.js',encoding='utf-8').read()).group(1))
if G!=DONE:print('midweek.py: files are through week',G,'not',DONE,'; nothing written');sys.exit(0)
M7=L('pull_m7.json');A=L('pull_pts.json');X8=L('pull8.json');X8a=L('pull8a.json');HI=L('hist.json')
PJ,META,S8,K8=X8['PJ'],X8['META'],X8['S8'],X8['K8']
if min((s[0] for s in S8),default=NOW)!=NOW:print('midweek.py: pull8.json is not for week',NOW,'; nothing written');sys.exit(0)
RO={r['rid']:r for r in M7['RO']}
def nm(pid):
    if pid in META and META[pid]:return META[pid][0]
    if pid in HI['m']:return HI['m'][pid][1]
    return pid
def pos(pid):
    if pid in META and META[pid]:return META[pid][1]
    if pid in A:return A[pid][0]
    return HI['m'].get(pid,['?'])[0]
import season,roster_files as RF
m8={r[0]:(r[1],r[2]) for r in X8a['m8']}
R=RF.rosters(RO,A,META,nm,pos,DONE,season.RID)
f=P+f'wk{NOW}.json';old=L(f'wk{NOW}.json') if _dt_os.path.exists(f) else None
played=set((L('stats.json') if _dt_os.path.exists(P+'stats.json') else {}).get(str(NOW),{}))
wk=RF.lineups(m8,RO,PJ,META,S8,K8,nm,pos,NOW,old=old,played=played)
# ---------- FUT week NOW: projected totals for the set lineups and win % (same formula as full_update.py section 2)
s=open(P+'data_block.js',encoding='utf-8').read()
mF=re.search(r'const FUT=(\{.*?\});\n',s);FUT=json.loads(mF.group(1))
SH=ast.literal_eval(re.search(r'^SH=(\{.*\})$',open(P+'full_update.py',encoding='utf-8').read(),re.M).group(1))
def projtot(rid):return round(sum(PJ.get(p,[0])[0] for p in m8[rid][1]),2)
def opp_of(rid):return [r for r,(mid,_) in m8.items() if mid==m8[rid][0] and r!=rid][0]
nf=0
for t,F in FUT.items():
    rid=season.RID[t]
    if not F or F[0][0]!=NOW or rid not in m8:continue
    opp=opp_of(rid)
    if F[0][1]!=SH[opp]:print('midweek.py: FUT',t,'week',NOW,'opponent',F[0][1],'!= Sleeper',SH[opp],'; FUT not changed');nf=-1;break
if nf==0:
    for t,F in FUT.items():
        rid=season.RID[t]
        if not F or F[0][0]!=NOW or rid not in m8:continue
        opp=opp_of(rid);a,b=projtot(rid),projtot(opp);sd=0.215*(a+b);z=(a-b)/sd if sd else 0
        F[0]=[NOW,SH[opp],a,b,round(100*0.5*(1+math.erf(z/math.sqrt(2))))]
    for t,F in FUT.items():  # make win% pairs sum to 100
        rid=season.RID[t]
        if F and F[0][0]==NOW and rid in m8:
            opp=opp_of(rid)
            if rid>opp:F[0][4]=100-[y for y in FUT[season.RN[opp]] if y[0]==NOW][0][4]
    new='const FUT='+json.dumps(FUT,ensure_ascii=False,separators=(',',':'))+';\n'
    s=s[:mF.start()]+new+s[mF.end():];open(P+'data_block.js','w',encoding='utf-8').write(s);nf=1
# ---------- ages for players new to the files (Compare, Rosters)
X=L('cmp_extra.json');na=0
for pid,v in META.items():
    if v and v[4] and pid not in X['age']:X['age'][pid]=v[4];na+=1
if na:json.dump(X,open(P+'cmp_extra.json','w'),ensure_ascii=False)
# ---------- roster check: Sleeper's rosters (pull_m7 RO) against rosters.json and wk<NOW>.json; warn only
def _n(k):n=k.replace('’',"'").replace(' 👑','').strip();return {'RIPMFL':'Team RIPMFL'}.get(n,n)
keys={season.RID[_n(k)]:k for k in R}
bad=0
for rid,r in sorted(RO.items()):
    sl=set(r['pl'] or []);rj={p[0] for p in R[keys[rid]]};X_=wk['out'].get(str(rid),{'st':[],'bn':[]})
    wj={p[0] for p in X_['st']+X_['bn'] if p[0] and p[0]!='0'};st={p for p in m8[rid][1] if p and p!='0'}
    miss=sorted(sl-rj)+sorted((sl|st)-wj);extra=sorted(rj-sl)+sorted(wj-(sl|st))
    if miss or extra:bad+=1;print('WARNING midweek.py: roster',rid,'missing',miss,'extra',extra,file=sys.stderr)
    print(f'midweek.py: roster {rid}: Sleeper {len(sl)} players (IR {len(r["res"] or [])}, taxi {len(r["taxi"] or [])}), rosters.json {len(rj)}, wk{NOW} {len(wj)}')
print('midweek.py: week',NOW,'rosters refreshed;',('FUT projections refreshed' if nf==1 else 'FUT unchanged'),'; new ages',na,'; roster mismatches',bad)
