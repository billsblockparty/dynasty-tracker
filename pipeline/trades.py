import os as _dt_os;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'
# League trades for Compare and Stats > Trades: python3 trades.py  (weekly runs, after history/paper_pull.mjs)
# cmp_extra.json 'tx' (one entry per completed trade, same shape as season_replay.py builds it), 'txp' (name, position,
# NFL team of every player in a trade), 'txw' (his weekly points, weeks 1..G) and 'tp' (traded picks) were written once and
# never updated by any run before 2026-11-12, so a new trade would not have reached either list. Source: Sleeper's
# transactions in history/paper/sleeper_<season>.json (re-pulled by every weekly run) and pull_m7.json TP. Existing entries
# are kept as they are (txp teams stay the team at the time of the trade); only new trades and players are added.
# Never fatal: any error prints and exits 0.
import json,re,sys
P=__DTP__
def main():
    S=_dt_os.environ.get('DT_SEASON','2026');f=P+f'history/paper/sleeper_{S}.json'
    if not _dt_os.path.exists(f):print('trades.py: no',f,'; nothing changed');return
    d=json.load(open(f,encoding='utf-8'));X=json.load(open(P+'cmp_extra.json',encoding='utf-8'))
    G=int(re.search(r'const G=(\d+);',open(P+'data_block.js',encoding='utf-8').read()).group(1))
    have={t['ts']:t for t in X['tx']};new=[]
    for w,L_ in sorted(d.get('transactions',{}).items(),key=lambda x:int(x[0])):
        for t in L_:
            if t.get('type')!='trade' or t.get('status')!='complete' or t['status_updated'] in have:continue
            e={'w':int(w),'ts':t['status_updated'],'rids':t['roster_ids'],'adds':t.get('adds'),
               'picks':[[p['season'],p['round'],p['roster_id'],p['owner_id'],p['previous_owner_id']] for p in t.get('draft_picks') or []],
               'faab':[{'amount':x['amount'],'sender':x['sender'],'receiver':x['receiver']} for x in t.get('waiver_budget') or []]}
            new.append(e);have[e['ts']]=e
    A=json.load(open(P+'pull_pts.json',encoding='utf-8'));META=json.load(open(P+'pull8.json',encoding='utf-8')).get('META',{})
    HM=json.load(open(P+'hist.json',encoding='utf-8'))['m']
    np_=0
    for e in new:
        for pid in (e['adds'] or {}):
            if pid in X['txp']:continue
            m=META.get(pid);a=A.get(pid)
            X['txp'][pid]=[m[0] if m else (HM.get(pid,[None,pid])[1]),(m[1] if m else (a[0] if a else HM.get(pid,['?'])[0])),(m[2] if m else (a[1] if a else None))]
            X['txw'][pid]=[(v if v is not None else 0) for v in a[2][:G]] if a else [0]*G;np_+=1
    X['tx']=sorted(have.values(),key=lambda t:t['ts'])
    TP=json.load(open(P+'pull_m7.json',encoding='utf-8')).get('TP')
    tp=[[p['season'],p['round'],p['roster_id'],p['owner_id']] for p in TP] if TP is not None else X['tp']
    ch=bool(new) or sorted(map(json.dumps,tp))!=sorted(map(json.dumps,X['tp']))
    X['tp']=tp
    if ch:json.dump(X,open(P+'cmp_extra.json','w'),ensure_ascii=False)
    print('trades.py:',len(X['tx']),'trades (',len(new),'new,',np_,'new players ),',len(tp),'traded picks',('; cmp_extra.json written' if ch else '; unchanged'))
try:main()
except Exception as e:print('WARNING trades.py (ignored):',repr(e),file=sys.stderr)
