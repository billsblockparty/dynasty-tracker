#!/usr/bin/env python3
"""TeamHub 1.5: standalone page published at <site>/teamhub/ (separate from the tabbed tracker).
Pulls Sleeper data, computes per-team stats for all FINAL weeks, Monte Carlo playoff odds, week-by-week
snapshots and a live strip for the in-progress week (matchups + projections fetched fresh every run).
Writes site/teamhub/index.html (self-contained: template.html + baked JSON + inlined fonts) and
site/teamhub/data.json. Called by pipeline/run.py in every mode (never fatal). --refresh-players refetches
the 14 MB Sleeper players file (weekly mode) and rewrites players_slim.json, the committed name/position/
injury map for rostered players; live runs use the small committed file.
"""
import json, os, sys, time, base64, re, math, statistics, urllib.request, itertools
from datetime import datetime, timezone

LEAGUE = "1335450123487961088"
DEFAULT_ROSTER = 8
ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(ROOT, "..", ".."))
CACHE = os.path.join(REPO, ".cache", "teamhub")   # not committed
OUT = os.path.join(REPO, "site", "teamhub")
SLIM = os.path.join(ROOT, "players_slim.json")
SLIM_FIELDS = ("full_name", "first_name", "last_name", "position", "fantasy_positions", "team", "injury_status")
API = "https://api.sleeper.app/v1"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
os.makedirs(CACHE, exist_ok=True)

def get(url, ua=None, raw=False):
    req = urllib.request.Request(url, headers={"User-Agent": ua or "teamhub/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        b = r.read()
    return b if raw else json.loads(b)

def cached(name, url, max_age=None, force=False):
    p = os.path.join(CACHE, name)
    if not force and os.path.exists(p) and (max_age is None or time.time() - os.path.getmtime(p) < max_age):
        return json.load(open(p))
    d = get(url)
    json.dump(d, open(p, "w"))
    return d

def main():
    refresh_players = "--refresh-players" in sys.argv
    state = get(f"{API}/state/nfl"); json.dump(state, open(os.path.join(CACHE, "state.json"), "w"))
    league = cached("league.json", f"{API}/league/{LEAGUE}", force=True)
    rosters = cached("rosters.json", f"{API}/league/{LEAGUE}/rosters", force=True)
    users = cached("users.json", f"{API}/league/{LEAGUE}/users", force=True)

    # ---- final weeks: league's last scored leg, capped below the NFL state's current week
    last_scored = int(league["settings"].get("last_scored_leg") or 0)
    cur = int(state["week"]) if state.get("season") == league["season"] and state.get("season_type") == "regular" else 99
    last_final = min(last_scored, cur - 1)
    weeks = list(range(1, last_final + 1))
    mus = {w: cached(f"matchups_{w}.json", f"{API}/league/{LEAGUE}/matchups/{w}", force=True) for w in weeks}
    nxt = last_final + 1
    live_m = cached(f"matchups_{nxt}.json", f"{API}/league/{LEAGUE}/matchups/{nxt}", force=True) if nxt < int(league["settings"].get("playoff_week_start") or 15) else []
    need = {p for w in weeks for a in mus[w] for p in (a.get("players") or [])} | {p for r in rosters for p in (r.get("players") or [])} \
         | {p for a in live_m for p in (a.get("starters") or []) if p not in (None, "0")}
    players = json.load(open(SLIM)) if os.path.exists(SLIM) else {}
    stale_schema = bool(players) and "injury_status" not in next(iter(players.values()))
    if refresh_players or stale_schema or not need <= set(players):
        full = cached("players_nfl.json", f"{API}/players/nfl", max_age=86400, force=refresh_players)
        keep = need | set(players)
        players = {k: {f: full[k].get(f) for f in SLIM_FIELDS} for k in sorted(keep) if k in full}
        json.dump(players, open(SLIM, "w"), separators=(",", ":"), sort_keys=True)

    slots = [s for s in league["roster_positions"] if s not in ("BN", "IR", "TAXI")]
    FLEXMAP = {"FLEX": {"RB", "WR", "TE"}, "SUPER_FLEX": {"QB", "RB", "WR", "TE"}, "REC_FLEX": {"WR", "TE"}, "WRRB_FLEX": {"RB", "WR"}}
    POS_ORDER = ["QB", "RB", "WR", "TE", "K", "DEF"]

    def ppos(pid):
        p = players.get(pid)
        if p is None:
            return "DEF" if not pid.isdigit() else None
        return p.get("position") or (p.get("fantasy_positions") or [None])[0]
    def elig(pid):
        p = players.get(pid)
        if p is None: return {"DEF"} if not pid.isdigit() else set()
        return set(p.get("fantasy_positions") or [p.get("position")])
    def pname(pid):
        p = players.get(pid) or {}
        if not pid.isdigit(): return f"{p.get('first_name', pid)} {p.get('last_name', 'D/ST')}".strip()
        return p.get("full_name") or f"{p.get('first_name','')} {p.get('last_name','')}".strip() or pid
    def slot_ok(slot, pid):
        e = elig(pid)
        return bool(e & FLEXMAP[slot]) if slot in FLEXMAP else slot in e

    def optimal(pp, pool):
        """Exact max-points legal lineup over `slots` using players in pool (dict pid->pts)."""
        # candidate pruning: per slot keep top N eligible players (N = slots of that kind + flex slots + 1)
        cands = []
        for s in slots:
            el = sorted([p for p in pool if slot_ok(s, p)], key=lambda p: -pool[p])[:len(slots)]
            cands.append(el)
        order = sorted(range(len(slots)), key=lambda i: (slots[i] in FLEXMAP, len(cands[i])))
        best = [-1.0, None]
        def rec(k, used, tot, pick):
            if k == len(order):
                if tot > best[0]: best[0], best[1] = tot, dict(pick)
                return
            # upper bound prune
            ub = tot + sum(max([pool[p] for p in cands[order[j]] if p not in used] or [0]) for j in range(k, len(order)))
            if ub <= best[0] + 1e-9: return
            i = order[k]; any_ = False
            for p in cands[i]:
                if p in used: continue
                any_ = True; used.add(p); pick[i] = p
                rec(k + 1, used, tot + pool[p], pick)
                used.discard(p); del pick[i]
            if not any_: rec(k + 1, used, tot, pick)
        rec(0, set(), 0.0, {})
        return round(best[0], 2), best[1]

    umap = {u["user_id"]: u for u in users}
    teams = {}
    for r in rosters:
        u = umap.get(r.get("owner_id"), {})
        md = u.get("metadata") or {}
        rid = r["roster_id"]
        teams[rid] = dict(rid=rid, name=(md.get("team_name") or u.get("display_name") or f"Team {rid}").strip(),
                          owner=u.get("display_name", ""), avatar=md.get("avatar") if (md.get("avatar") or "").startswith("http") else (f"https://sleepercdn.com/avatars/thumbs/{u['avatar']}" if u.get("avatar") else None),
                          sleeper=dict(w=r["settings"].get("wins", 0), l=r["settings"].get("losses", 0), t=r["settings"].get("ties", 0),
                                       fpts=round(r["settings"].get("fpts", 0) + r["settings"].get("fpts_decimal", 0) / 100, 2)),
                          taxi=set(r.get("taxi") or []))
    rids = sorted(teams)
    N = len(rids)

    W = {rid: [] for rid in rids}
    league_wk = []
    caveats = []
    for w in weeks:
        m = mus[w]
        by = {a["roster_id"]: a for a in m}
        sc = {rid: round(by[rid]["points"] or 0, 2) for rid in rids}
        vals = sorted(sc.values())
        q = statistics.quantiles(vals, n=4, method="inclusive")
        league_wk.append(dict(w=w, med=round(statistics.median(vals), 2), p25=round(q[0], 2), p75=round(q[2], 2),
                              hi=max(vals), lo=min(vals), scores={str(k): v for k, v in sc.items()}))
        groups = {}
        for a in m:
            if a.get("matchup_id") is not None: groups.setdefault(a["matchup_id"], []).append(a["roster_id"])
        rank_sorted = sorted(rids, key=lambda r: -sc[r])
        for rid in rids:
            a = by[rid]
            opp = next((o for o in groups.get(a.get("matchup_id"), []) if o != rid), None)
            me = sc[rid]; op = sc[opp] if opp else None
            res = None if op is None else ("W" if me > op else "L" if me < op else "T")
            apw = sum(1 for o in rids if o != rid and sc[o] < me); apl = sum(1 for o in rids if o != rid and sc[o] > me)
            apt = N - 1 - apw - apl
            pp = {k: (v or 0) for k, v in (a.get("players_points") or {}).items()}
            pool = {p: pp[p] for p in (a.get("players") or []) if p in pp and p not in teams[rid]["taxi"]}
            opt, pick = optimal(pp, pool)
            starters = a.get("starters") or []; spts = a.get("starters_points") or []
            st = []
            for i, pid in enumerate(starters):
                if pid in (None, "0", 0): st.append(dict(slot=slots[i] if i < len(slots) else "?", pos=None, pts=0.0, pid=None)); continue
                st.append(dict(slot=slots[i] if i < len(slots) else "?", pid=pid, pos=ppos(pid), pts=round(spts[i] if i < len(spts) else pp.get(pid, 0), 2)))
            actual = round(sum(s["pts"] for s in st), 2)
            if abs(actual - me) > 0.02: caveats.append(f"W{w} roster {rid}: starter sum {actual} != points {me}")
            # biggest missed swap: best bench player not in actual starters but in optimal
            missed = [p for p in (pick or {}).values() if p not in starters]
            W[rid].append(dict(w=w, pts=me, opp=opp, opp_pts=op, res=res, wk_rank=rank_sorted.index(rid) + 1,
                               apw=apw, apl=apl, apt=apt, xw=round((apw + 0.5 * apt) / (N - 1), 4),
                               opt=opt, left=round(max(opt - me, 0), 2), eff=round(me / opt, 4) if opt else 1,
                               missed=[dict(n=pname(p), pos=ppos(p), pts=round(pool[p], 2)) for p in missed][:3],
                               starters=st))

    def standings_after(k):
        rows = []
        for rid in rids:
            g = W[rid][:k]
            wn = sum(x["res"] == "W" for x in g); ls = sum(x["res"] == "L" for x in g); t = sum(x["res"] == "T" for x in g)
            rows.append((rid, wn + 0.5 * t, sum(x["pts"] for x in g)))
        rows.sort(key=lambda x: (-x[1], -x[2]))
        return {r[0]: i + 1 for i, r in enumerate(rows)}
    rank_hist = [standings_after(k) for k in range(1, len(weeks) + 1)]

    T = {}
    for rid in rids:
        g = W[rid]
        wn = sum(x["res"] == "W" for x in g); ls = sum(x["res"] == "L" for x in g); t = sum(x["res"] == "T" for x in g)
        pf = round(sum(x["pts"] for x in g), 2); pa = round(sum(x["opp_pts"] or 0 for x in g), 2)
        apw = sum(x["apw"] for x in g); apl = sum(x["apl"] for x in g); apt = sum(x["apt"] for x in g)
        xw = round(sum(x["xw"] for x in g), 2)
        streak = ""
        if g:
            last = g[-1]["res"]; n = 0
            for x in reversed(g):
                if x["res"] == last: n += 1
                else: break
            streak = f"{last}{n}"
        # position strength
        pos = {p: dict(pts=0.0, starts=0) for p in POS_ORDER}
        for x in g:
            for s in x["starters"]:
                if s["pos"] in pos: pos[s["pos"]]["pts"] += s["pts"]; pos[s["pos"]]["starts"] += 1
        for p in pos.values(): p["pts"] = round(p["pts"], 2); p["pps"] = round(p["pts"] / p["starts"], 2) if p["starts"] else 0
        T[rid] = dict(**{k: v for k, v in teams[rid].items() if k not in ("taxi",)}, w=wn, l=ls, t=t, pf=pf, pa=pa,
                      apw=apw, apl=apl, apt=apt, xw=xw, luck=round(wn + 0.5 * t - xw, 2), streak=streak,
                      left=round(sum(x["left"] for x in g), 2), opt=round(sum(x["opt"] for x in g), 2),
                      rank=rank_hist[-1][rid] if rank_hist else None, rank_hist=[h[rid] for h in rank_hist],
                      weeks=g, pos=pos)
        T[rid]["eff"] = round(pf / T[rid]["opt"], 4) if T[rid]["opt"] else 1
    def rank_by(key, rev=True):
        s = sorted(rids, key=lambda r: key(T[r]), reverse=rev)
        return {r: s.index(r) + 1 for r in rids}  # ties share index order; good enough for display
    for k, fn, rev in [("pf_rank", lambda t: t["pf"], True), ("ap_rank", lambda t: t["apw"] + .5 * t["apt"], True),
                       ("luck_rank", lambda t: t["luck"], True), ("left_rank", lambda t: t["left"], False),
                       ("pa_rank", lambda t: t["pa"], True)]:
        rk = rank_by(fn, rev)
        for r in rids: T[r][k] = rk[r]
    for p in POS_ORDER:
        rk = rank_by(lambda t: t["pos"][p]["pps"], True)
        for r in rids: T[r]["pos"][p]["rank"] = rk[r]
    # league per-position avg for context
    pos_league = {p: dict(avg=round(statistics.mean(T[r]["pos"][p]["pps"] for r in rids), 2),
                          max=max(T[r]["pos"][p]["pps"] for r in rids)) for p in POS_ORDER}

    # ---- self-checks against Sleeper's own roster settings
    checks = []
    for r in rids:
        s = T[r]["sleeper"]
        ok_rec = (s["w"], s["l"], s["t"]) == (T[r]["w"], T[r]["l"], T[r]["t"])
        ok_pf = abs(s["fpts"] - T[r]["pf"]) < 0.05
        checks.append(dict(rid=r, record_ok=ok_rec, pf_ok=ok_pf, sleeper=s, ours=dict(w=T[r]["w"], l=T[r]["l"], t=T[r]["t"], pf=T[r]["pf"])))
        if not ok_rec: caveats.append(f"roster {r}: record from matchups {T[r]['w']}-{T[r]['l']} vs Sleeper {s['w']}-{s['l']}")
        if not ok_pf: caveats.append(f"roster {r}: PF {T[r]['pf']} vs Sleeper fpts {s['fpts']}")

    # ================= TeamHub 1.5 additions =================
    import ext15
    st = league["settings"]
    PO_TEAMS = int(st.get("playoff_teams") or 6); PO_START = int(st.get("playoff_week_start") or 15)
    REG_END = PO_START - 1
    live_wk = last_final + 1
    fut = {w: cached(f"matchups_{w}.json", f"{API}/league/{LEAGUE}/matchups/{w}", force=True) for w in range(live_wk, REG_END + 1)}
    sched = {}
    for w, m in list(mus.items()) + list(fut.items()):
        g = {}
        for a in m:
            if a.get("matchup_id") is not None: g.setdefault(a["matchup_id"], []).append(a["roster_id"])
        sched[w] = [sorted(v) for v in g.values() if len(v) == 2]

    # accents
    acc, acc_notes = ext15.accents(teams)
    for r in rids: T[r].update(acc[r])
    for r, n in acc_notes.items(): caveats.append(f"accent roster {r}: {n}")

    # per-week snapshots (state through week k)
    def snap(k):
        out = {}
        for rid in rids:
            g = W[rid][:k]
            wn = sum(x["res"] == "W" for x in g); ls = sum(x["res"] == "L" for x in g); t = sum(x["res"] == "T" for x in g)
            apw = sum(x["apw"] for x in g); apl = sum(x["apl"] for x in g); apt = sum(x["apt"] for x in g)
            xw = sum(x["xw"] for x in g); last = g[-1]["res"]; n = 0
            for x in reversed(g):
                if x["res"] == last: n += 1
                else: break
            pos = {p: [0.0, 0] for p in POS_ORDER}
            for x in g:
                for s in x["starters"]:
                    if s["pos"] in pos: pos[s["pos"]][0] += s["pts"]; pos[s["pos"]][1] += 1
            out[rid] = dict(w=wn, l=ls, t=t, pf=round(sum(x["pts"] for x in g), 2), pa=round(sum(x["opp_pts"] or 0 for x in g), 2),
                            apw=apw, apl=apl, apt=apt, xw=round(xw, 2), luck=round(wn + .5 * t - xw, 2), streak=f"{last}{n}",
                            left=round(sum(x["left"] for x in g), 2), opt=round(sum(x["opt"] for x in g), 2),
                            pos={p: dict(pps=round(v[0] / v[1], 2) if v[1] else 0, starts=v[1], pts=round(v[0], 2)) for p, v in pos.items()})
        def rk(fn, rev=True):
            s = sorted(rids, key=lambda r: fn(out[r]), reverse=rev); return {r: s.index(r) + 1 for r in rids}
        stand = sorted(rids, key=lambda r: (-(out[r]["w"] + .5 * out[r]["t"]), -out[r]["pf"]))
        for r in rids: out[r]["rank"] = stand.index(r) + 1
        for key, fn, rev in [("pf_rank", lambda o: o["pf"], True), ("ap_rank", lambda o: o["apw"] + .5 * o["apt"], True),
                             ("luck_rank", lambda o: o["luck"], True), ("left_rank", lambda o: o["left"], False)]:
            m = rk(fn, rev)
            for r in rids: out[r][key] = m[r]
        for p in POS_ORDER:
            m = rk(lambda o: o["pos"][p]["pps"])
            for r in rids: out[r]["pos"][p]["rank"] = m[r]
        # Monte Carlo as of week k
        hist = {r: [x["pts"] for x in W[r][:k]] for r in rids}
        allsc = [v for r in rids for v in hist[r]]
        pooled = statistics.stdev(allsc) if len(allsc) > 2 else 20.0
        remaining = [(w, a, b) for w in range(k + 1, REG_END + 1) for a, b in sched.get(w, [])]
        odds = ext15.simulate(rids, {r: (out[r]["w"] + .5 * out[r]["t"], out[r]["pf"]) for r in rids}, remaining,
                              REG_END, PO_START, PO_TEAMS, n=10000, seed=1000 + k, pooled_sd=pooled, score_hist=hist)
        for r in rids: out[r]["odds"] = odds[r]
        return {str(r): v for r, v in out.items()}
    snaps = {str(k): snap(k) for k in weeks}
    final_odds = {r: snaps[str(last_final)][str(r)]["odds"] for r in rids}
    for r in rids: T[r]["odds"] = final_odds[r]

    # compact starters per week (for contribution share) + names / injury
    names = {}
    for r in rids:
        for x in T[r]["weeks"]:
            x["st"] = [[s["pid"], s["pts"], s["pos"]] for s in x["starters"] if s["pid"]]
            for s in x["starters"]:
                if s["pid"] and s["pid"] not in names:
                    p = players.get(s["pid"]) or {}
                    names[s["pid"]] = dict(n=pname(s["pid"]), pos=ppos(s["pid"]), team=p.get("team"), inj=p.get("injury_status"))

    # live week (in progress): Sleeper matchups + Sleeper projections
    live = None
    if live_wk <= REG_END:
        m = fut[live_wk]; by = {a["roster_id"]: a for a in m}
        try:
            proj = get(f"https://api.sleeper.app/projections/nfl/{league['season']}/{live_wk}?season_type=regular&position[]=QB&position[]=RB&position[]=WR&position[]=TE&position[]=K&position[]=DEF&order_by=pts_half_ppr", ua=UA)
            json.dump(proj, open(os.path.join(CACHE, f"proj_{live_wk}.json"), "w"))
        except Exception as e:
            caveats.append(f"projections fetch failed: {e}"); proj = json.load(open(os.path.join(CACHE, f"proj_{live_wk}.json")))
        PK = "pts_half_ppr" if league["scoring_settings"].get("rec") == 0.5 else ("pts_ppr" if league["scoring_settings"].get("rec") == 1 else "pts_std")
        pj = {str(x["player_id"]): float((x.get("stats") or {}).get(PK) or 0) for x in proj}
        dates = sorted({x.get("date") for x in proj if x.get("date")})
        sd7 = {r: final_odds[r]["sd"] for r in rids}
        any_pts = any((a.get("points") or 0) > 0 for a in m)
        teamrow = {}
        for r in rids:
            a = by[r]; pp = a.get("players_points") or {}
            sts = [p for p in (a.get("starters") or []) if p not in (None, "0")]
            noproj = [pname(p) for p in sts if p not in pj and not (pp.get(p) or 0)]
            # played player (non-zero points) -> actual; otherwise projection
            tot = sum((pp.get(p) or 0) if (pp.get(p) or 0) != 0 else pj.get(p, 0) for p in sts)
            teamrow[r] = dict(pts=round(a.get("points") or 0, 2), proj=round(tot, 2), noproj=noproj,
                              pure_proj=round(sum(pj.get(p, 0) for p in sts), 2))
        games = []
        for a, b in sched[live_wk]:
            ta, tb = teamrow[a], teamrow[b]
            z = (ta["proj"] - tb["proj"]) / math.sqrt(sd7[a] ** 2 + sd7[b] ** 2)
            games.append(dict(a=a, b=b, pa=ta["pts"], pb=tb["pts"], ja=ta["proj"], jb=tb["proj"], wa=round(100 * ext15.norm_cdf(z), 1)))
        live = dict(week=live_wk, in_progress=bool(any_pts), dates=dates, games=games, teams={str(r): v for r, v in teamrow.items()}, key=PK)
        for r, v in teamrow.items():
            if v["noproj"]: caveats.append(f"W{live_wk} roster {r}: no Sleeper projection for starter(s) {', '.join(v['noproj'])} (counted as 0)")

    ext = dict(playoff=dict(teams=PO_TEAMS, week_start=PO_START, reg_end=REG_END, round_type=st.get("playoff_round_type"),
                            seed_type=st.get("playoff_seed_type"), byes=2 if PO_TEAMS == 6 else 0),
               sched={str(w): v for w, v in sched.items()}, snaps=snaps, live=live, names=names, sims=10000)

    data = dict(league=dict(id=LEAGUE, name=league["name"], season=league["season"], slots=slots, teams=N,
                            ppr=league["scoring_settings"].get("rec")),
                weeks=weeks, through=last_final, nfl_week=state.get("week"), built=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                default=DEFAULT_ROSTER, league_wk=league_wk, pos_league=pos_league, pos_order=POS_ORDER,
                teams={str(r): T[r] for r in rids}, checks=checks, caveats=caveats, **ext)
    os.makedirs(OUT, exist_ok=True)
    json.dump(data, open(os.path.join(OUT, "data.json"), "w"), indent=1, ensure_ascii=False)

    # ---- page: slim data (drop starters detail) + inline fonts
    slim = json.loads(json.dumps(data))
    for t in slim["teams"].values():
        for x in t["weeks"]: x.pop("starters", None)
    for k in slim["snaps"].values():
        for o in k.values(): o.pop("opt", None)
    slim.pop("checks"); slim.pop("caveats")
    html = open(os.path.join(ROOT, "template.html"), encoding="utf-8").read()
    html = html.replace("/*__FONTS__*/", fonts_css()).replace("__DATA__", json.dumps(slim, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"))
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(html)
    print(f"teamhub 1.5: weeks {weeks[0]}-{weeks[-1]} | site/teamhub/index.html + data.json written | caveats: {len(caveats)}")
    for c in caveats: print("  !", c)

def fonts_css():
    """Download the latin subsets of the live site's fonts and inline them as base64 (cached)."""
    p = os.path.join(ROOT, "fonts_inline.css")  # committed; regenerated only if missing
    if os.path.exists(p): return open(p).read()
    try:
        css = get("https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap", ua=UA, raw=True).decode()
        out = []
        for block in re.findall(r"/\* latin \*/\s*(@font-face\s*{[^}]*})", css):
            url = re.search(r"url\((https://[^)]+)\)", block).group(1)
            b64 = base64.b64encode(get(url, ua=UA, raw=True)).decode()
            out.append(block.replace(url, "data:font/woff2;base64," + b64))
        s = "\n".join(out); open(p, "w").write(s); return s
    except Exception as e:
        print("font inline failed:", e); return ""

if __name__ == "__main__":
    main()
