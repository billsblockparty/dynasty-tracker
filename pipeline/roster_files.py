import os as _dt_os;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'
# Current-roster files, shared by full_update.py (completed-week pull) and midweek.py (daily / mid-week weekly runs):
#   rosters(): rosters.json, ro_ranks.json, ro_pg.json  (section 4 of full_update.py until 2026-11-12)
#   lineups(): wk<NOW>.json + kick.json[NOW]            (section 6 of full_update.py until 2026-11-12)
# Inputs are the pull files of `node pull.mjs weekly D` (RO = pull_m7 RO, A = pull_pts, META/PJ/S8/K8 = pull8, m8 from pull8a).
import json
P=__DTP__
L=lambda f:json.load(open(P+f,encoding='utf-8'))
INJ={'Questionable','Doubtful','Out','IR','PUP','Sus'}

def rosters(RO,A,META,nm,pos,DONE,RID):
    tot={p:round(sum(v for v in a[2][:DONE] if v is not None),2) for p,a in A.items()}
    gp={p:a[3][:DONE].count('1') for p,a in A.items()};ap={p:a[0] for p,a in A.items()}
    K={};PG={}
    pgv=lambda q:tot[q]/gp[q] if gp[q] else 0
    OLDR=L('rosters.json');keys={}
    for k in OLDR:
        n=k.replace('’',"'").replace(' 👑','').strip();n={'RIPMFL':'Team RIPMFL'}.get(n,n);keys[RID[n]]=k
    R={}
    for rid,r in RO.items():
        pl=[]
        for pid in r['pl']:
            p_=pos(pid);pts=tot.get(pid,0.0);g=gp.get(pid,0)
            same=[q for q in tot if ap[q]==p_]
            rk=1+sum(1 for q in same if tot[q]>pts+1e-9) if pid in tot else len(same)+1
            tie=int(sum(1 for q in same if abs(tot[q]-pts)<1e-9)>1) if pid in tot else 0
            ordn=1+sum(1 for q in same if tot[q]>pts+1e-9 or (abs(tot[q]-pts)<1e-9 and q<pid)) if pid in tot else len(same)+1
            if pid in tot:K[pid]=[rk,tie,pts]
            if g:PG[pid]=[1+sum(1 for q in same if gp[q]>=3 and pgv(q)>pgv(pid)+1e-9),g]
            else:PG[pid]=None
            tag='IR' if pid in (r['res'] or []) else 'TX' if pid in (r['taxi'] or []) else ''
            tm=(META.get(pid) or [None,None,None])[2] or (A[pid][1] if pid in A else '')
            pl.append([pid,nm(pid),p_,tm,pts,ordn,g,tag])
        R[keys[rid]]=pl
    json.dump(R,open(P+'rosters.json','w'),ensure_ascii=False)
    OK=L('ro_ranks.json');K['_bye']=OK['_bye']
    json.dump(K,open(P+'ro_ranks.json','w'));json.dump(PG,open(P+'ro_pg.json','w'))
    return R

def lineups(m8,RO,PJ,META,S8,K8,nm,pos,NOW,old=None,played=()):
    """wk<NOW>.json from Sleeper's week-NOW matchups (starters) and the current rosters (bench).
    old = the existing wk<NOW>.json (mid-week refresh): its scores (team totals, player points, done / live / left) are
    kept, and a player who already has points or a stat line this week (played = ids with a week-NOW stat line) keeps the
    NFL team and opponent of his row, as teams.py does. old=None (completed-week pull) writes a fresh week."""
    home8={h for w_,a_,h in S8 if w_==NOW}
    prev={p[0]:p for X in (old or {}).get('out',{}).values() for p in X['st']+X['bn']}
    out={}
    for rid,(mid,st) in m8.items():
        r=RO[rid]
        def row(pid):
            pj=PJ.get(pid,[0,None]);inj=(META.get(pid) or [None]*4)[3]
            if pid in (r['res'] or []):inj=inj or 'IR'
            tm=(META.get(pid) or [None,None,None])[2] or ''
            x=[pid,pos(pid),nm(pid),tm,pj[0],0,pj[1],inj if inj in INJ else None]
            o=prev.get(pid)
            if o:
                x[5]=o[5]
                if o[5] or pid in played:x[3],x[6]=o[3],o[6]
            return x
        X={'mid':mid,'pts':0,'st':[row(p) for p in st],'bn':[row(p) for p in r['pl'] if p not in st]}
        if old and str(rid) in old.get('out',{}):X['pts']=old['out'][str(rid)].get('pts',0)
        out[str(rid)]=X
    w={'done':[],'out':out,'home':sorted(home8),'done_note':'final + vs/@ for completed games too'}
    if old:
        for k in ('done','live','left'):
            if k in old:w[k]=old[k]
    json.dump(w,open(P+f'wk{NOW}.json','w'))
    KI=L('kick.json');KI[str(NOW)]=K8;json.dump(KI,open(P+'kick.json','w'))
    return w
