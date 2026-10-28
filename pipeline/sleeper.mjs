// Sleeper data pulls for the tracker. Pure functions over `get(url) -> JSON`, so the same code runs in Node
// (GitHub Actions) and in a browser for checking. Output shapes match the files the Python build reads.
export const LEAGUE = '1335450123487961088', SEASON = '2026';
const A = 'https://api.sleeper.app/v1', S = 'https://api.sleeper.com';
const FPOS = new Set(['QB', 'RB', 'WR', 'TE', 'K', 'DEF']);
const r2 = x => Math.round(x * 100) / 100;
const KST = { pre_game: 'pre', in_game: 'in', complete: 'post' };

export const leagueScore = (stats, ss) => {
  let s = 0;
  for (const [k, v] of Object.entries(stats || {})) if (ss[k] != null && typeof v === 'number') s += v * ss[k];
  return r2(s);
};

// last regular-season week whose games are all complete (0 if none)
export async function lastCompleteWeek(get) {
  const sch = await get(`${S}/schedule/nfl/regular/${SEASON}`);
  let done = 0;
  for (let w = 1; w <= 18; w++) {
    const g = sch.filter(x => x.week == w);
    if (g.length && g.every(x => x.status == 'complete')) done = w; else break;
  }
  return { done, sch };
}

async function kickoffs(get, w) {
  const sc = await get(`${S}/scores/nfl/regular/${SEASON}/${w}`);
  const k = {};
  for (const x of sc) {
    const m = x.metadata || {};
    for (const tm of [m.home_team, m.away_team]) if (tm) k[tm] = [m.date_time, KST[x.status] || x.status];
  }
  return k;
}

const projURL = w => `${S}/projections/nfl/${SEASON}/${w}?season_type=regular` + ['QB', 'RB', 'WR', 'TE', 'K', 'DEF'].map(p => `&position[]=${p}`).join('');

// Weekly full refresh inputs: completes week D, prepares week N = D + 1.
export async function pullWeekly(get, D) {
  const N = D + 1, L = `${A}/league/${LEAGUE}`;
  const [lg, ro, us, mD, mN, tD, tN, tp, state, sch] = await Promise.all([
    get(L), get(`${L}/rosters`), get(`${L}/users`), get(`${L}/matchups/${D}`), get(`${L}/matchups/${N}`),
    get(`${L}/transactions/${D}`), get(`${L}/transactions/${N}`), get(`${L}/traded_picks`), get(`${A}/state/nfl`),
    get(`${S}/schedule/nfl/regular/${SEASON}`)]);
  const ss = lg.scoring_settings;
  const pull_m7 = {
    M7: mD.map(x => ({ rid: x.roster_id, mid: x.matchup_id, pts: x.points, st: x.starters, pp: x.players_points })),
    RO: ro.map(r => ({ rid: r.roster_id, pl: r.players || [], res: r.reserve, taxi: r.taxi, own: r.owner_id })),
    TP: tp,
  };
  // weekly league points for every fantasy-position player who played in weeks 1..D
  const weeks = await Promise.all(Array.from({ length: D }, (_, i) => get(`${S}/stats/nfl/${SEASON}/${i + 1}?season_type=regular`)));
  const P = {};
  weeks.forEach((rows, i) => {
    for (const r of rows) {
      const pos = r.player && r.player.position;
      if (!FPOS.has(pos)) continue;
      const s = r.stats || {};
      if (!(s.gp > 0)) continue;
      const e = P[r.player_id] || (P[r.player_id] = [pos, r.team, Array(D).fill(null), '0'.repeat(D)]);
      e[1] = r.team || e[1];
      e[2][i] = leagueScore(s, ss);
      e[3] = e[3].slice(0, i) + '1' + e[3].slice(i + 1);
    }
  });
  // projections (week N), player meta for rostered players, schedule N..14, kickoffs N
  const ids = new Set(ro.flatMap(r => r.players || []));
  const [pj, players, K8] = await Promise.all([get(projURL(N)), get(`${A}/players/nfl`), kickoffs(get, N)]);
  const PJ = {};
  for (const r of pj) if (ids.has(r.player_id)) PJ[r.player_id] = [leagueScore(r.stats, ss), r.opponent || null];
  for (const id of ids) if (!(id in PJ)) PJ[id] = [0, null];
  const META = {};
  for (const id of ids) {
    const p = players[id];
    META[id] = p ? [p.full_name || `${p.first_name} ${p.last_name}`, p.position, p.team || null, p.injury_status || null, p.birth_date || null] : null;
  }
  const S8 = sch.filter(x => x.week >= N && x.week <= 14).map(x => [x.week, x.away, x.home]);
  const pull8 = { PJ, META, S8, K8 };
  const tr = t => ({ ts: t.status_updated, rids: t.roster_ids, adds: t.adds, picks: t.draft_picks, faab: t.waiver_budget, st: t.status });
  const pull8a = {
    state, ss, pos: lg.roster_positions,
    ro: ro.map(r => ({ rid: r.roster_id, own: r.owner_id, n: (r.players || []).length, res: r.reserve, taxi: r.taxi })),
    us: us.map(u => [u.user_id, u.display_name, (u.metadata || {}).team_name]),
    m8: mN.map(x => [x.roster_id, x.matchup_id, x.starters]),
    t7: tD.filter(t => t.type == 'trade').map(tr), t8: tN.filter(t => t.type == 'trade').map(tr), ntp: tp.length,
  };
  return { pull_m7, pull_pts: P, pull8, pull8a };
}

// Playoff weeks 15-17: league-scored projections, home teams, kickoffs (same shape as po_pull.js)
export async function pullPlayoffs(get) {
  const L = `${A}/league/${LEAGUE}`;
  const [lg, ro, sch] = await Promise.all([get(L), get(`${L}/rosters`), get(`${S}/schedule/nfl/regular/${SEASON}`)]);
  const ss = lg.scoring_settings, ids = new Set(ro.flatMap(r => r.players || []));
  const out = { PO: {}, HOME: {}, KICK: {}, SCH: {} };
  for (const w of [15, 16, 17]) {
    const g = sch.filter(x => x.week == w);
    out.SCH[w] = g.map(x => [x.home, x.away, x.status, x.date]); out.HOME[w] = g.map(x => x.home);
    const pr = await get(projURL(w)), m = {};
    for (const r of pr) if (ids.has(r.player_id)) m[r.player_id] = [leagueScore(r.stats, ss), r.opponent || null, r.team || null];
    out.PO[w] = m;
    const sc = await get(`${S}/scores/nfl/regular/${SEASON}/${w}`), k = {};
    for (const x of sc) { const t = x.metadata && x.metadata.date_time; for (const tm of [x.metadata?.home_team, x.metadata?.away_team]) if (tm) k[tm] = [t, x.status]; }
    out.KICK[w] = k;
  }
  out.n = ids.size;
  return out;
}

// In-week scores for week W (same shape as score_pull.js, plus rows for newly started players)
const STATK = { QB: ['pass_cmp', 'pass_att', 'pass_yd', 'pass_td', 'pass_int', 'rush_att', 'rush_yd', 'rush_td', 'fum_lost'], RB: ['rush_att', 'rush_yd', 'rush_td', 'rec', 'rec_tgt', 'rec_yd', 'rec_td', 'fum_lost'], WR: ['rec', 'rec_tgt', 'rec_yd', 'rec_td', 'rush_att', 'rush_yd', 'rush_td', 'fum_lost'], K: ['fgm', 'fga', 'xpm', 'xpa'], DEF: ['sack', 'int', 'fum_rec', 'def_td', 'pts_allow'] };
STATK.TE = STATK.WR;
export async function pullLive(get, W, known) {
  const L = `${A}/league/${LEAGUE}`;
  const [sc, m, st] = await Promise.all([get(`${S}/schedule/nfl/regular/${SEASON}`), get(`${L}/matchups/${W}`), get(`${S}/stats/nfl/${SEASON}/${W}?season_type=regular`)]);
  const done = sc.filter(g => g.week == W && g.status == 'complete').flatMap(g => [g.home, g.away]);
  const live = sc.filter(g => g.week == W && g.status == 'in_game').flatMap(g => [g.home, g.away]);
  const pp = {}, tp = {}, sts = {};
  m.forEach(x => { tp[x.roster_id] = x.points; sts[x.roster_id] = x.starters; Object.assign(pp, x.players_points); });
  const S_ = {};
  for (const r of st) {
    const pid = r.player_id; if (!(pid in pp)) continue;
    const pos = r.player?.position || ''; const k = STATK[pos]; if (!k) continue;
    const s = r.stats || {}; if (!s.gp && !s.gms_active && pos != 'DEF') continue;
    const a = k.map(x => Math.round(s[x] || 0)); while (a.length > 1 && a[a.length - 1] === 0) a.pop();
    S_[pid] = a.join('.');
  }
  const pz = {}; for (const [k, v] of Object.entries(pp)) if (v) pz[k] = v;
  // starters the build has never seen (added after the weekly refresh): give score.py a full row
  const extra = {}, need = Object.values(sts).flat().filter(id => id && id != '0' && !known.has(id));
  if (need.length) {
    const [lg, players, pj] = await Promise.all([get(L), get(`${A}/players/nfl`), get(projURL(W))]);
    const ss = lg.scoring_settings, P = Object.fromEntries(pj.map(r => [r.player_id, r]));
    const INJ = new Set(['Questionable', 'Doubtful', 'Out', 'IR', 'PUP', 'Sus']);
    for (const id of need) {
      const p = players[id] || {}, q = P[id];
      const inj = p.injury_status && INJ.has(p.injury_status) ? p.injury_status : null;
      extra[id] = [id, p.position || '', p.full_name || `${p.first_name || ''} ${p.last_name || ''}`.trim() || id, p.team || '', q ? leagueScore(q.stats, ss) : 0, 0, q ? q.opponent || null : null, inj];
    }
  }
  return { w: W, done, live, tp, pp: pz, S: S_, starters: sts, extra };
}
