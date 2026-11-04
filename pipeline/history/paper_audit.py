"""Paper Trail, phase 1: audit of the raw transaction data in history/paper/ (pulled by paper_pull.mjs).
Normalises MFL 2021-24(+25) and Sleeper 2025+ into one event list, maps players to Sleeper ids and picks to
season + round + ORIGINAL team, replays every pick's ownership and reports coverage, unmatched players, chain gaps
and the MFL -> Sleeper hand-over. Writes paper/audit.json and prints the report. No guessing: anything that does not
line up is reported, not repaired."""
import json,os,re,collections,datetime as dt
P=os.path.dirname(os.path.abspath(__file__))+'/paper/'
J=lambda f:json.load(open(P+f,encoding='utf-8')) if os.path.exists(P+f) else None
A=lambda x:x if isinstance(x,list) else ([x] if x else [])
TEAMS=json.load(open(os.path.dirname(P[:-1])+'/teams.json'))
MT=TEAMS['mfl'];ST={int(k):v for k,v in TEAMS['sleeper_roster'].items()}
day=lambda ms:dt.datetime.fromtimestamp(ms/1000,dt.timezone.utc).strftime('%Y-%m-%d')
SP=J('sleeper_players.json') or {};DP=J('dp_ids.json') or {}
def nk(n):
    n=str(n or '')
    if ',' in n:l,f=n.split(',',1);n=f.strip()+' '+l.strip()
    n=re.sub(r"[.'’`,]",'',n.lower()).replace('-',' ');n=re.sub(r'\b(jr|sr|ii|iii|iv|v)\b','',n);return re.sub(r'\s+',' ',n).strip()
POS={'PK':'K','Def':'DEF','DEF':'DEF'}
SBY=collections.defaultdict(list)
for sid,(nm,pos,tm,ye,bd) in SP.items():SBY[(nk(nm),pos)].append(sid)
DEFT={}  # MFL defense ids -> Sleeper team abbreviation (DEF ids are the abbreviation)
REP={'unmatched':{},'via':collections.Counter()}
MFLP={}
def mflplayer(pid,y):
    """MFL player id -> Sleeper id (DynastyProcess map, then name + position), or 'mfl:<id>'"""
    if pid in MFLP:return MFLP[pid]
    info=None
    for yy in range(2025,2020,-1):
        d=MY.get(yy)
        if d and pid in d['players']:info=d['players'][pid];break
    sid=None
    if pid in DP and DP[pid][0]:sid=DP[pid][0];REP['via']['dynastyprocess']+=1
    elif info:
        nm,pos,tm=info[0],POS.get(info[1],info[1]),info[2]
        if pos=='DEF':
            ab={'JAC':'JAX','GBP':'GB','KCC':'KC','LVR':'LV','NEP':'NE','NOS':'NO','SFO':'SF','TBB':'TB'}.get(tm,tm)
            if ab in SP:sid=ab;REP['via']['defense']+=1
        else:
            c=SBY.get((nk(nm),pos)) or []
            if len(c)==1:sid=c[0];REP['via']['name+position']+=1
            elif len(c)>1:REP['unmatched'][pid]=[nm,pos,tm,'ambiguous: '+','.join(c)]
    if not sid:
        REP['via']['unmatched']+=1
        if pid not in REP['unmatched']:REP['unmatched'][pid]=[*(info[:3] if info else ['?','?','?']),'no match' if info else 'not in MFL players export']
        sid='mfl:'+pid
    MFLP[pid]=sid;return sid
MY={y:J(f'mfl_{y}.json') for y in range(2021,2026)};MY={y:d for y,d in MY.items() if d}
SY={y:J(f'sleeper_{y}.json') for y in range(2025,2031)};SY={y:d for y,d in SY.items() if d}

EV=[];COV=collections.defaultdict(collections.Counter);ISSUES=[]
def pick(y,r,orig):return f'{y} R{r} ({orig})'
# ---------- MFL
SLOT={}  # (year, round, slot) -> original team, reconstructed below
for y,d in sorted(MY.items()):
    tx=A((d.get('transactions') or {}).get('transaction'))
    for t in tx:
        ty=t['type'];COV[f'MFL {y}'][ty]+=1;ts=int(t['timestamp'])*1000
        if ty=='TRADE':
            f1,f2=MT.get(t['franchise'],t['franchise']),MT.get(t['franchise2'],t['franchise2'])
            sides=[]
            for frm,to,key in ((f1,f2,'franchise1_gave_up'),(f2,f1,'franchise2_gave_up')):
                for c in [c for c in t[key].split(',') if c]:
                    if c.startswith('FP_'):_,o,yy,r=c.split('_');sides.append(('pick',pick(int(yy),int(r),MT.get(o,o)),frm,to))
                    elif c.startswith('DP_'):_,r,p=c.split('_');sides.append(('dpick',(y,int(r)+1,int(p)+1),frm,to))
                    elif c.startswith('BB_'):sides.append(('faab',float(c[3:]),frm,to))
                    else:sides.append(('player',mflplayer(c,y),frm,to))
            EV.append(dict(src='MFL',season=y,ts=ts,type='trade',teams=[f1,f2],moves=sides,by_commish=t.get('by_commish')=='1'))
        elif ty in('BBID_WAIVER','FREE_AGENT','WAIVER'):
            tm=MT.get(t['franchise'],t['franchise']);parts=t['transaction'].split('|')
            adds=[c for c in parts[0].split(',') if c];drops=[c for c in parts[-1].split(',') if c] if len(parts)>1 else []
            bid=float(parts[1]) if ty=='BBID_WAIVER' and len(parts)>2 else None
            EV.append(dict(src='MFL',season=y,ts=ts,type='waiver' if ty!='FREE_AGENT' else 'free_agent',teams=[tm],
                moves=[('player',mflplayer(a,y),None,tm) for a in adds]+[('player',mflplayer(x,y),tm,None) for x in drops],bid=bid))
    for u in A((d.get('draftResults') or {}).get('draftUnit')):
        for p in A(u.get('draftPick')):
            if not p.get('player'):continue
            tm=MT.get(p['franchise'],p['franchise']);r,s=int(p['round']),int(p['pick'])
            EV.append(dict(src='MFL',season=y,ts=int(p['timestamp'])*1000,type='draft',teams=[tm],kind='startup' if u.get('draftType')=='SDRAFT' else 'rookie',
                slot=(y,r,s),moves=[('player',mflplayer(p['player'],y),None,tm)],comment=p.get('comments','')))
            COV[f'MFL {y}']['DRAFT_PICK']+=1
# ---------- Sleeper
for y,d in sorted(SY.items()):
    ros={r['roster_id']:ST.get(r['roster_id'],r['roster_id']) for r in d['rosters']}
    for t in [t for r in d['transactions'].values() for t in r]:
        COV[f'Sleeper {y}'][f"{t['type']}:{t['status']}"]+=1
        if t['status']!='complete':continue
        T=lambda rid:ST.get(rid,rid)
        mv=[]
        if t['type']=='trade':
            for pid,rid in (t.get('adds') or {}).items():
                frm=(t.get('drops') or {}).get(pid);mv.append(('player',pid,T(frm) if frm else None,T(rid)))
            for dp in t.get('draft_picks') or []:mv.append(('pick',pick(int(dp['season']),dp['round'],T(dp['roster_id'])),T(dp['previous_owner_id']),T(dp['owner_id'])))
            for wb in t.get('waiver_budget') or []:mv.append(('faab',wb['amount'],T(wb['sender']),T(wb['receiver'])))
        else:
            for pid,rid in (t.get('adds') or {}).items():mv.append(('player',pid,None,T(rid)))
            for pid,rid in (t.get('drops') or {}).items():mv.append(('player',pid,T(rid),None))
        EV.append(dict(src='Sleeper',season=y,ts=t['status_updated'] or t['created'],type=t['type'],teams=[T(r) for r in t.get('roster_ids') or []],moves=mv,
            bid=(t.get('settings') or {}).get('waiver_bid')))
    for dd in d['drafts']:
        dr=dd['draft'];kind='rookie' if dr['type']=='linear' else ('import' if dr['settings'].get('rounds',0)>=10 else 'supplemental')
        for p in dd['picks'] or []:
            EV.append(dict(src='Sleeper',season=int(dr['season']),ts=dr.get('last_picked') or dr.get('start_time') or 0,type='draft',kind=kind,teams=[ST.get(p['roster_id'])],
                slot=(int(dr['season']),p['round'],p['draft_slot']),pick_no=p['pick_no'],moves=[('player',p['player_id'],None,ST.get(p['roster_id']))]))
            COV[f'Sleeper {y}'][f'draft:{kind}']+=1
EV.sort(key=lambda e:e['ts'])

# ---------- MFL current-year slots (DP_r_p): original owner of each slot, solved from the pick chains (never assumed)
def chain_owner(fp,until):
    """owner of a future pick (as named FP) after all FP trades before `until` (ms)"""
    y,r,o=fp;own=o
    for e in EV:
        if e['ts']>=until:break
        for m in e.get('moves',[]):
            if m[0]=='pick' and m[1]==pick(y,r,o):own=m[3]
    return own
for y in sorted(MY):
    rk=[e for e in EV if e['src']=='MFL' and e['type']=='draft' and e['kind']=='rookie' and e['season']==y]
    if not rk:continue
    t0=min(e['ts'] for e in rk);final={e['slot'][1:]:e['teams'][0] for e in rk}
    dpt=[e for e in EV if e['src']=='MFL' and e['season']==y and e['type']=='trade' and any(m[0]=='dpick' for m in e['moves'])]
    first_dp=min([e['ts'] for e in dpt]+[t0])
    rounds=sorted({k[0] for k in final});slots=sorted({k[1] for k in final});teams=sorted(set(MT.values()))
    for s in slots:
        ok=[]
        for o in teams:
            good=True
            for r in rounds:
                own=chain_owner((y,r,o),first_dp)
                for e in dpt:
                    for m in e['moves']:
                        if m[0]=='dpick' and m[1]==(y,r,s):
                            if m[2]!=own:good=False
                            own=m[3]
                if own!=final.get((r,s)):good=False
            if good:ok.append(o)
        if len(ok)==1:SLOT[(y,s)]=ok[0]
        else:ISSUES.append(dict(kind='mfl slot unresolved',season=y,slot=s,candidates=ok))
for e in EV:  # rewrite DP picks as canonical picks
    e['moves']=[('pick',pick(m[1][0],m[1][1],SLOT.get((m[1][0],m[1][2]),'?slot'+str(m[1][2]))),m[2],m[3]) if m[0]=='dpick' else m for m in e['moves']]
    if e['type']=='draft' and e['src']=='MFL' and e['kind']=='rookie':e['pick']=pick(e['slot'][0],e['slot'][1],SLOT.get((e['slot'][0],e['slot'][2]),'?'))

# ---------- Sleeper rookie-draft slots: original owner from the draft's slot order
for y,d in SY.items():
    for dd in d['drafts']:
        dr=dd['draft']
        if dr['type']!='linear':continue
        s2r={int(k):v for k,v in (dr.get('slot_to_roster_id') or {}).items()}
        if not s2r and dr.get('draft_order'):
            u2r={r['owner_id']:r['roster_id'] for r in d['rosters']};s2r={v:u2r.get(k) for k,v in dr['draft_order'].items()}
        for e in EV:
            if e['src']=='Sleeper' and e['type']=='draft' and e.get('kind')=='rookie' and e['slot'][0]==int(dr['season']):
                e['pick']=pick(e['slot'][0],e['slot'][1],ST.get(s2r.get(e['slot'][2]),'?'))

# ---------- replay every pick: owner chain, gaps, final use
CH=collections.defaultdict(list)
for e in EV:
    for m in e['moves']:
        if m[0]=='pick':CH[m[1]].append(dict(ts=e['ts'],src=e['src'],frm=m[2],to=m[3],date=day(e['ts'])))
    if e['type']=='draft' and e.get('pick'):CH[e['pick']].append(dict(ts=e['ts'],src=e['src'],drafted=e['moves'][0][1],by=e['teams'][0],date=day(e['ts'])))
GAPS=[];FINAL={}
for k,steps in CH.items():
    m=re.match(r'(\d+) R(\d) \((.*)\)',k)
    if not m:continue
    own=m.group(3)
    for s in sorted(steps,key=lambda s:s['ts']):
        if 'drafted' in s:
            if s['by']!=own:GAPS.append(dict(pick=k,kind='used by a team that did not hold it',holder=own,used_by=s['by'],date=s['date']))
            continue
        if s['frm']!=own:GAPS.append(dict(pick=k,kind='moved from a team that did not hold it',holder=own,moved_from=s['frm'],to=s['to'],date=s['date'],src=s['src']))
        own=s['to']
    FINAL[k]=own

# ---------- the hand-over: MFL end state vs Sleeper start state, for every pick of 2025 on
mfl_end={}
fd=MY.get(2025) or MY.get(2024)
for f in A((fd.get('futureDraftPicks') or {}).get('franchise')):
    for p in A(f.get('futureDraftPick')):mfl_end[pick(int(p['year']),int(p['round']),MT.get(p['originalPickFor']))]=MT.get(f['id'])
replay_end={}
for k,steps in CH.items():
    own=re.match(r'.*\((.*)\)',k).group(1)
    for s in sorted(steps,key=lambda s:s['ts']):
        if s['src']=='MFL' and 'to' in s:own=s['to']
    replay_end[k]=own
sl_first={};
for k,steps in CH.items():
    sl=[s for s in sorted(steps,key=lambda s:s['ts']) if s['src']=='Sleeper' and 'frm' in s]
    if sl:sl_first[k]=sl[0]['frm']
sl_now={}
last=SY[max(SY)];prev=SY.get(min(SY))
for tp in (prev or {}).get('traded_picks',[])+last.get('traded_picks',[]):
    sl_now[pick(int(tp['season']),tp['round'],ST.get(tp['roster_id']))]=ST.get(tp['owner_id'])
HAND=[]
for k in sorted(set(mfl_end)|{kk for kk in CH if int(kk[:4])>=2025}):
    y=int(k[:4])
    if y<2025:continue
    a=mfl_end.get(k);b=replay_end.get(k,re.match(r'.*\((.*)\)',k).group(1))
    start=sl_first.get(k)
    if start is None:  # never traded on Sleeper: whoever used it in a Sleeper draft, else Sleeper's current owner, else the original team
        used=[x for x in CH.get(k,[]) if x['src']=='Sleeper' and 'drafted' in x]
        start=used[0]['by'] if used else sl_now.get(k,re.match(r'.*\((.*)\)',k).group(1))
    row=dict(pick=k,mfl_snapshot=a,mfl_replay=b,sleeper_start=start)
    if a and b and a!=b:row['issue']='MFL snapshot and MFL trade replay disagree'
    if a and start and a!=start:row['issue']=(row.get('issue','')+'; ' if row.get('issue') else '')+'Sleeper start owner differs from MFL end owner'
    HAND.append(row)

# ---------- players across the move: MFL rosters replayed to the end vs the Sleeper import drafts
ROS=collections.defaultdict(set);WHO={}
for e in EV:
    if e['src']!='MFL':continue
    for m in e['moves']:
        if m[0]!='player':continue
        pid=m[1]
        if m[2] and pid in ROS[m[2]]:ROS[m[2]].discard(pid)
        elif m[2] and e['type']!='draft':ISSUES.append(dict(kind='MFL player left a team that did not hold it',player=pid,team=m[2],date=day(e['ts']),type=e['type']))
        if m[3]:
            if pid in WHO and WHO[pid]!=m[2] and WHO[pid] is not None and pid in ROS[WHO[pid]] and m[2] is None:
                ISSUES.append(dict(kind='MFL player added while on another roster',player=pid,team=m[3],other=WHO[pid],date=day(e['ts'])))
            ROS[m[3]].add(pid);WHO[pid]=m[3]
        elif m[2]:WHO[pid]=None
IMP=collections.defaultdict(set)
for e in EV:
    if e['src']=='Sleeper' and e['type']=='draft' and e.get('kind') in ('import','supplemental'):IMP[e['teams'][0]].add(e['moves'][0][1])
STITCH={}
for tm in sorted(set(ROS)|set(IMP)):
    a_,b_=ROS.get(tm,set()),IMP.get(tm,set())
    STITCH[tm]=dict(mfl_end=len(a_),sleeper_import=len(b_),missing_in_sleeper=sorted(a_-b_),new_in_sleeper=sorted(b_-a_))
nm=lambda i:(SP.get(i) or ['?'])[0]
# ---------- report
out=dict(coverage={k:dict(v) for k,v in COV.items()},events=len(EV),player_map=dict(REP['via']),unmatched=REP['unmatched'],
         slots={f'{y} slot {s}':o for (y,s),o in sorted(SLOT.items())},issues=ISSUES,chain_gaps=GAPS,handover=HAND,
         picks=len(CH),roster_stitch=STITCH)
json.dump(out,open(P+'audit.json','w'),indent=1,default=str)
json.dump([dict(e,moves=[list(m) for m in e['moves']]) for e in EV],open(P+'events.json','w'),default=str)
if __name__=='__main__':
    for k,v in out['coverage'].items():print(k,v)
    print('events',len(EV),'picks tracked',len(CH));print('player map',out['player_map']);print('unmatched',len(out['unmatched']))
    for k,v in list(out['unmatched'].items())[:40]:print('  ',k,v)
    print('slot issues',ISSUES);print('slots',out['slots'])
    print('chain gaps',len(GAPS))
    for g in GAPS:print('  ',g)
    bad=[h for h in HAND if h.get('issue')];print('handover rows',len(HAND),'issues',len(bad))
    for h in bad:print('  ',h)
    print('handover start sources',collections.Counter((h['mfl_snapshot'] is not None,h['sleeper_start'] is not None) for h in HAND))
    for tm,v in STITCH.items():print('STITCH',tm,v['mfl_end'],v['sleeper_import'],'missing',[nm(x) for x in v['missing_in_sleeper']],'new',[nm(x) for x in v['new_in_sleeper']])
    print('other issues',collections.Counter(i['kind'] for i in ISSUES))
