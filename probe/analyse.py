# Summarises the probe artifact (probe/out) into the job log. Read-only; prints only.
import json, gzip, os, sys, collections, glob, re
O = sys.argv[1]
DP = json.load(open('pipeline/history/paper/dp_ids.json'))
def L(p):
    f = os.path.join(O, p + '.json.gz')
    if not os.path.exists(f): return None
    return json.loads(gzip.open(f).read())
def sz(p):
    f = os.path.join(O, p + '.json.gz')
    return (len(gzip.open(f).read()), os.path.getsize(f)) if os.path.exists(f) else None
arr = lambda x: [] if x is None else x if isinstance(x, list) else [x]
def out(k, v): print('##', k, '=', json.dumps(v, ensure_ascii=False, default=str)[:4000], flush=True)
def sec(name, fn):
    try: fn()
    except Exception as e: out(name + ' ERROR', repr(e))
# request log
lg = [json.loads(l) for l in open(os.path.join(O, 'log.ndjson'))] if os.path.exists(os.path.join(O, 'log.ndjson')) else json.load(open(os.path.join(O, 'log.json')))['log']
out('requests', {'n': len(lg), 'non200': [(x['name'], x['status'], x.get('err'), (x.get('body') or '')[:200]) for x in lg if x['status'] != 200],
                 'retries': sum(1 for x in lg if x['try'] > 1)})
by = collections.defaultdict(list)
for x in lg: by[x['name'].split('/')[0]].append(x['ms'])
out('latency_ms', {k: {'n': len(v), 'mean': round(sum(v) / len(v)), 'max': max(v)} for k, v in by.items()})
out('headers_sample', {x['name']: x['h'] for x in lg[:3]} | {'final_url_sample': lg[0].get('final')})
# every file: raw and gz sizes, top keys, error bodies
files = sorted(glob.glob(os.path.join(O, '**/*.json.gz'), recursive=True))
inv = {}
for f in files:
    n = os.path.relpath(f, O)[:-8]; d = L(n)
    k = list(d.keys())[:6] if isinstance(d, dict) else f'list[{len(d)}]'
    if isinstance(d, dict) and len(d) == 1 and isinstance(next(iter(d.values())), dict): k = {next(iter(d)): list(next(iter(d.values())).keys())[:12]}
    inv[n] = [sz(n)[0], sz(n)[1], k]
for n, v in inv.items(): print('FILE', n, v[0], v[1], json.dumps(v[2])[:300])
for y in ('2024', '2021'):
    P = f'mfl/{y}/'
    def wr():
        tot = collections.Counter(); keys = set(); mk = set(); fk = set(); per = []
        for w in range(1, 18):
            d = L(P + f'weeklyResults_W{w}')
            if not d: continue
            W = d.get('weeklyResults') or {}
            for m in arr(W.get('matchup')):
                mk |= set(m.keys())
                for fr in arr(m.get('franchise')):
                    fk |= set(fr.keys())
                    for p in arr(fr.get('player')):
                        keys |= set(p.keys()); tot[(p.get('status'), 'score' in p and p['score'] != '', p.get('shouldStart'))] += 1
            if w in (1, 14): per.append((w, {k: v for k, v in W.items() if k != 'matchup'}))
        out(y + ' weeklyResults player keys', sorted(keys)); out(y + ' matchup keys', sorted(mk)); out(y + ' franchise keys', sorted(fk))
        out(y + ' weeklyResults (status, has score, shouldStart) counts', {str(k): v for k, v in tot.items()})
        out(y + ' weeklyResults other keys', per)
        d = L(P + 'weeklyResults_W1'); m = arr(d['weeklyResults']['matchup'])[0]; fr = arr(m['franchise'])[0]
        out(y + ' weeklyResults sample franchise', {k: v for k, v in fr.items() if k != 'player'} | {'player0': arr(fr['player'])[:3], 'nplayers': len(arr(fr['player']))})
    sec(y + ' wr', wr)
    def ros():
        sets = []; st = collections.Counter(); pk = set()
        for w in range(1, 18):
            d = L(P + f'rosters_W{w}')
            if not d: continue
            fs = arr(d['rosters']['franchise']); s = {}
            for fr in fs:
                ps = arr(fr.get('player')); s[fr['id']] = sorted(p['id'] for p in ps)
                for p in ps: st[p.get('status')] += 1; pk |= set(p.keys())
            sets.append(json.dumps(s, sort_keys=True))
            if w == 1: out(y + ' rosters W1 sample', {k: v for k, v in fs[0].items() if k != 'player'} | {'p': arr(fs[0].get('player'))[:2], 'n': len(arr(fs[0].get('player')))})
        out(y + ' rosters weeks', {'weeks': len(sets), 'distinct weekly roster sets': len(set(sets)), 'status counts all weeks': st, 'player keys': sorted(pk)})
        now = L(P + 'rosters_now')
        if now:
            s = {fr['id']: sorted(p['id'] for p in arr(fr.get('player'))) for fr in arr(now['rosters']['franchise'])}
            out(y + ' rosters_now == W17', json.dumps(s, sort_keys=True) == sets[-1] if sets else None)
        # rosters W vs weeklyResults W (starters+bench)
        diff = []
        for w in (1, 8, 14):
            r = L(P + f'rosters_W{w}'); d = L(P + f'weeklyResults_W{w}')
            if not r or not d: continue
            R = {fr['id']: {p['id'] for p in arr(fr.get('player'))} for fr in arr(r['rosters']['franchise'])}
            for m in arr(d['weeklyResults'].get('matchup')):
                for fr in arr(m['franchise']):
                    Wp = {p['id'] for p in arr(fr.get('player'))}; Rp = R.get(fr['id'], set())
                    diff.append((w, fr['id'], len(Wp), len(Rp), len(Rp - Wp), len(Wp - Rp)))
        out(y + ' rosters_W vs weeklyResults_W (w, fr, nWR, nRos, onlyRos, onlyWR)', diff)
    sec(y + ' ros', ros)
    def lg_():
        d = (L(P + 'league') or {}).get('league', {})
        out(y + ' league keys', sorted(d.keys()))
        out(y + ' league fields', {k: d.get(k) for k in ('starters', 'divisions', 'conferences', 'precision', 'bestLineup', 'lastRegularSeasonWeek', 'injuredReserve', 'taxiSquad', 'rosterSize', 'currentWaiverType', 'bbidSeasonLimit', 'bbidMinimum', 'standingsSort', 'h2h', 'rosterLimits', 'history')})
        out(y + ' league playoff-ish keys', {k: d[k] for k in d if re.search('playoff|bracket|seed|tiebreak|median|allplay', k, re.I)})
    sec(y + ' league', lg_)
    def rules():
        d = L(P + 'rules'); out(y + ' rules raw', d)
    sec(y + ' rules', rules)
    def sched():
        d = L(P + 'schedule'); ws = arr((d.get('schedule') or {}).get('weeklySchedule'))
        out(y + ' schedule', {'weeks': len(ws), 'w1': ws[0] if ws else None, 'w15': ws[14] if len(ws) > 14 else None})
    sec(y + ' sched', sched)
    def stand():
        for n in ('leagueStandings_ALL_1', 'leagueStandings'):
            d = L(P + n)
            if d:
                f = arr((d.get('leagueStandings') or {}).get('franchise'))
                out(y + ' ' + n, {'n': len(f), 'keys': sorted(f[0].keys()) if f else None, 'f0': f[0] if f else None, 'other': {k: v for k, v in (d.get('leagueStandings') or {}).items() if k != 'franchise'}})
    sec(y + ' stand', stand)
    def ps():
        d1 = L(P + 'weeklyResults_W1')
        mfl = {p['id']: p.get('score') for m in arr(d1['weeklyResults']['matchup']) for fr in arr(m['franchise']) for p in arr(fr.get('player'))}
        for n in ('playerScores_W1', 'playerScores_W1_freeagent', 'playerScores_W1_rules', 'playerScores_YTD', 'playerScores_W14'):
            d = L(P + n)
            if not d: out(y + ' ' + n, None); continue
            pl = arr((d.get('playerScores') or {}).get('playerScore'))
            nz = sum(1 for p in pl if p.get('score') not in (None, '', '0', '0.0', '0.00'))
            o = {'n': len(pl), 'nonzero': nz, 'keys': sorted(set().union(*[p.keys() for p in pl])) if pl else None, 'sample': pl[:3], 'other': {k: v for k, v in d['playerScores'].items() if k != 'playerScore'}}
            if n in ('playerScores_W1', 'playerScores_W1_rules'):
                S = {p['id']: p.get('score') for p in pl}
                both = [i for i in mfl if i in S and mfl[i] not in (None, '')]
                o['rostered_in_file'] = f"{sum(1 for i in mfl if i in S)}/{len(mfl)}"
                o['equal_to_weeklyResults'] = f"{sum(1 for i in both if abs(float(S[i] or 0) - float(mfl[i])) < 0.005)}/{len(both)}"
                o['diff_samples'] = [(i, mfl[i], S[i]) for i in both if abs(float(S[i] or 0) - float(mfl[i])) >= 0.005][:8]
                o['non_rostered'] = len(set(S) - set(mfl))
            out(y + ' ' + n, o)
    sec(y + ' ps', ps)
    def proj():
        for w in (1, 14):
            d = L(P + f'projectedScores_W{w}')
            if not d: out(y + f' projectedScores_W{w}', None); continue
            pl = arr((d.get('projectedScores') or {}).get('playerScore'))
            out(y + f' projectedScores_W{w}', {'n': len(pl), 'nonzero': sum(1 for p in pl if p.get('score') not in (None, '', '0', '0.00')), 'sample': pl[:3], 'raw_head': json.dumps(d)[:300]})
    sec(y + ' proj', proj)
    def tx():
        d = L(P + 'transactions__TRANS_TYPE__'); t = arr((d.get('transactions') or {}).get('transaction'))
        c = collections.Counter(x['type'] for x in t)
        out(y + ' transactions', {'n': len(t), 'types': c, 'samples': {k: next(x for x in t if x['type'] == k) for k in c}})
    sec(y + ' tx', tx)
    def nfl():
        d = L(P + 'nflSchedule_W1'); g = arr((d.get('nflSchedule') or {}).get('matchup'))
        out(y + ' nflSchedule_W1', {'games': len(g), 'g0': g[0] if g else None, 'other': {k: v for k, v in (d.get('nflSchedule') or {}).items() if k != 'matchup'}})
        out(y + ' nflSchedule weeks with games', [w for w in range(1, 18) if L(P + f'nflSchedule_W{w}') and arr((L(P + f'nflSchedule_W{w}').get('nflSchedule') or {}).get('matchup'))])
        out(y + ' nflByeWeeks', L(P + 'nflByeWeeks'))
        d = L(P + 'injuries_W1'); out(y + ' injuries_W1', json.dumps(d)[:600] if d else None)
    sec(y + ' nfl', nfl)
    def pls():
        d = L(P + 'players_details'); pl = arr((d.get('players') or {}).get('player'))
        want = ['Wilson, Russell', 'Stafford, Matthew', 'Adams, Davante', 'Ridley, Calvin', 'Rodgers, Aaron', 'Cooper, Amari', 'McCaffrey, Christian', 'Hopkins, DeAndre']
        out(y + ' players_details', {'n': len(pl), 'keys': sorted(set().union(*[p.keys() for p in pl[:200]])) if pl else None,
                                    'probe': {p['name']: p.get('team') for p in pl if p.get('name') in want}, 'timestamp': (d.get('players') or {}).get('timestamp')})
    sec(y + ' pls', pls)
    def misc():
        for n in ('liveScoring_W1', 'topStarters_W1', 'topOwns', 'pointsAllowed', 'history', 'accounting', 'assets', 'futureDraftPicks', 'draftResults', 'playoffBrackets'):
            d = L(P + n); out(y + ' ' + n, json.dumps(d)[:700] if d is not None else None)
    sec(y + ' misc', misc)
for y in ('2020', '2025'):
    for n in ('league', 'weeklyResults_W1'):
        d = L(f'mfl/{y}/{n}'); out(f'{y} {n}', json.dumps(d)[:500] if d is not None else None)
# Sleeper
for y in ('2024', '2021'):
    P = f'sleeper/{y}/'
    def sl():
        o = {}
        for w in range(1, 19):
            s = L(P + f'stats_W{w}'); p = L(P + f'proj_W{w}')
            o[w] = [len(s) if s else None, len(p) if p else None, sum(1 for r in (p or []) if (r.get('stats') or {}).get('pts_ppr'))]
        out(y + ' sleeper stats/proj rows per week [stats, proj, proj with pts_ppr]', o)
        s = L(P + 'stats_W1'); r = next((r for r in s if (r.get('player') or {}).get('position') == 'QB' and (r.get('stats') or {}).get('pass_yd', 0) > 200), s[0])
        out(y + ' sleeper stat row keys', sorted(r.keys())); out(y + ' sleeper stat sample', {k: r[k] for k in r if k != 'stats'} | {'stats': r.get('stats')})
        p = L(P + 'proj_W1'); r2 = next((x for x in p if x.get('player_id') == r.get('player_id')), p[0])
        out(y + ' sleeper proj sample', {k: r2[k] for k in r2 if k != 'stats'} | {'stats': r2.get('stats')})
        sc = L(P + 'schedule'); out(y + ' sleeper schedule', {'n': len(sc) if sc else None, 's0': sc[0] if sc else None})
        sc = L(P + 'scores_W1'); out(y + ' sleeper scores_W1', {'n': len(sc) if sc else None, 's0': json.dumps(sc[0])[:500] if sc else None})
        # MFL weekly score vs Sleeper pts_* for mapped rostered players, week 1 and week 14
        for w in (1, 14):
            d = L(f'mfl/{y}/weeklyResults_W{w}'); st = {r['player_id']: r.get('stats') or {} for r in L(P + f'stats_W{w}')}
            res = collections.Counter(); bad = []
            for m in arr(d['weeklyResults']['matchup']):
                for fr in arr(m['franchise']):
                    for pl in arr(fr.get('player')):
                        if pl.get('score') in (None, ''): continue
                        sid = (DP.get(pl['id']) or [None])[0]
                        if not sid: res['unmapped'] += 1; continue
                        S = st.get(str(sid))
                        if S is None: res['no sleeper row'] += 1; continue
                        v = float(pl['score']); hit = [k for k in ('pts_ppr', 'pts_half_ppr', 'pts_std') if abs(S.get(k, 0) - v) < 0.015]
                        res[','.join(hit) or 'none'] += 1
                        if not hit and len(bad) < 12: bad.append((pl['id'], sid, (DP.get(pl['id']) or [0, 0, 0])[1:], v, S.get('pts_ppr'), S.get('pts_half_ppr'), S.get('pts_std')))
            out(f'{y} W{w} MFL score vs Sleeper pts', res); out(f'{y} W{w} mismatches', bad)
    sec(y + ' sleeper', sl)
