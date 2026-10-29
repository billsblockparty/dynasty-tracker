import os as _dt_os;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'
# League history 2021-2025 per team (current Sleeper names): season records, finishes, all-time totals, head-to-head.
# Sources: history/mfl_<y>.json (2021-24, league 68106) and history/sleeper_2025.json; mapping in history/teams.json.
# Regular season = MFL weeks <= lastRegularSeasonWeek / Sleeper weeks < playoff_week_start. Seeds: wins, then PF.
# Head-to-head counts regular-season games plus championship-bracket and 3rd-place games (not consolation).
import json
P=__DTP__;H=P+'history/'
TM=json.load(open(H+'teams.json'))
SEAS={}   # year -> {team: {...}}
GAMES=[]  # (year, week, a, b, pa, pb, kind) kind: reg / po
def fin_label(place,po):
    return {1:'Champion',2:'Runner-up',3:'3rd',4:'4th'}.get(place,'Playoffs' if po else 'Missed')
for y in (2021,2022,2023,2024):
    d=json.load(open(H+f'mfl_{y}.json'));N=TM['mfl'];LR=d['lastRegular']
    rec={N[f]:{'w':0,'l':0,'t':0,'pf':0.0,'pa':0.0} for f,_ in d['fr']}
    for w,ms in d['weeks'].items():
        if int(w)>LR:continue
        for m in ms:
            a,b=m['f'];A,B=N[a['id']],N[b['id']]
            for x,o,X in((a,b,A),(b,a,B)):
                r=rec[X];r['pf']+=x['score'];r['pa']+=o['score'];r['w' if x['score']>o['score'] else 'l' if x['score']<o['score'] else 't']+=1
            GAMES.append((y,int(w),A,B,a['score'],b['score'],'reg'))
    place={};po=set()
    for br in d['brackets']:
        third='3rd' in br['name']
        for rd in br['rounds']:
            for g in rd['games']:
                A,B=N[g['home']['id']],N[g['away']['id']];GAMES.append((y,rd['week'],A,B,g['home']['pts'],g['away']['pts'],'po'))
                if not third:po|={A,B}
        last=br['rounds'][-1]['games'][0];A,B=N[last['home']['id']],N[last['away']['id']]
        win,los=(A,B) if last['home']['pts']>last['away']['pts'] else (B,A)
        if third:place[win]=3;place[los]=4
        else:place[win]=1;place[los]=2
    SEAS[y]={t:{**r,'place':place.get(t),'po':t in po} for t,r in rec.items()}
# Sleeper 2025
s=json.load(open(H+'sleeper_2025.json'));N=TM['sleeper_roster'];PW=s['playoff_week_start']
rec={N[str(r['rid'])]:{'w':0,'l':0,'t':0,'pf':0.0,'pa':0.0} for r in s['rosters']}
for w,ms in s['weeks'].items():
    w=int(w);by={}
    for m in ms:by.setdefault(m['mid'],[]).append(m)
    for mid,pair in by.items():
        if mid is None or len(pair)!=2:continue
        a,b=pair;A,B=N[str(a['rid'])],N[str(b['rid'])]
        if w<PW:
            for x,o,X in((a,b,A),(b,a,B)):
                r=rec[X];r['pf']+=x['pts'];r['pa']+=o['pts'];r['w' if x['pts']>o['pts'] else 'l' if x['pts']<o['pts'] else 't']+=1
            GAMES.append((2025,w,A,B,a['pts'],b['pts'],'reg'))
place={};po=set()
for g in s['winners_bracket']:
    po|={N[str(g['t1'])],N[str(g['t2'])]} if g.get('t1') and g.get('t2') else set()
    if g.get('p') in (1,3):
        place[N[str(g['w'])]]=g['p'];place[N[str(g['l'])]]=g['p']+1
# playoff game scores: match bracket games to week matchups by roster pair
for g in s['winners_bracket']:
    if g.get('p') not in (None,1,3) or not g.get('t1'):continue
    wk=PW+g['r']-1;ms={m['rid']:m['pts'] for m in s['weeks'][str(wk)]}
    A,B=N[str(g['t1'])],N[str(g['t2'])];GAMES.append((2025,wk,A,B,ms[g['t1']],ms[g['t2']],'po'))
SEAS[2025]={t:{**r,'place':place.get(t),'po':t in po} for t,r in rec.items()}
for r in s['rosters']:  # Sleeper's own season PF/PA (includes stat corrections made after the weekly scores were saved)
    SEAS[2025][N[str(r['rid'])]].update(pf=r['pf'],pa=r['pa'])
# seeds (regular-season rank by wins, then PF) and labels
for y,S in SEAS.items():
    order=sorted(S,key=lambda t:(-S[t]['w'],-S[t]['pf']))
    for i,t in enumerate(order):S[t]['seed']=i+1;S[t]['pf']=round(S[t]['pf'],2);S[t]['pa']=round(S[t]['pa'],2);S[t]['finish']=fin_label(S[t]['place'],S[t]['po'])
TEAMS=sorted({t for S in SEAS.values() for t in S})
ALL={t:{k:sum(SEAS[y][t][k] for y in SEAS) for k in ('w','l','t')} for t in TEAMS}
for t in TEAMS:
    ALL[t].update(pf=round(sum(SEAS[y][t]['pf'] for y in SEAS),2),titles=[y for y in SEAS if SEAS[y][t]['place']==1],
                  finals=[y for y in SEAS if SEAS[y][t]['place'] in (1,2)],po=[y for y in SEAS if SEAS[y][t]['po']],
                  best_seed=min(SEAS[y][t]['seed'] for y in SEAS))
H2H={t:{} for t in TEAMS}
for y,w,A,B,pa,pb,k in GAMES:
    for X,Y,px,py in((A,B,pa,pb),(B,A,pb,pa)):
        h=H2H[X].setdefault(Y,{'w':0,'l':0,'t':0,'po_w':0,'po_l':0,'pf':0.0,'pa':0.0,'last':None})
        r='w' if px>py else 'l' if px<py else 't';h[r]+=1;h['pf']=round(h['pf']+px,2);h['pa']=round(h['pa']+py,2)
        if k=='po' and r!='t':h['po_'+r]+=1
        if h['last'] is None or (y,w)>(h['last'][0],h['last'][1]):h['last']=[y,w,r.upper(),round(px,2),round(py,2)]
out={'note':'2021-2024 MFL league 68106, 2025 Sleeper. Regular season + championship/3rd-place games in head-to-head.','seasons':{str(y):S for y,S in SEAS.items()},'all':ALL,'h2h':H2H}
json.dump(out,open(H+'summary.json','w'),indent=0)
if __name__=='__main__':
    for y,S in SEAS.items():print(y,[(t.split()[0],f"{S[t]['w']}-{S[t]['l']}",S[t]['seed'],S[t]['finish']) for t in sorted(S,key=lambda t:S[t]['seed'])])
