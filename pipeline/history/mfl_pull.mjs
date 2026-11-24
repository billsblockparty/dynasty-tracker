// Prior-season pull (brief PY-1, 2026-11-24): one MyFantasyLeague season of league 68106 plus Sleeper's public NFL data
// for the same season, saved as gzip JSON maps {request key: response} for mfl_adapt.py, which turns them into a
// Sleeper-shaped capture (history/raw/<year>/) that season_replay.py replays offline.
//   node mfl_pull.mjs 2024 [out dir]        (default out dir: ./mfl_<year>_raw)
// Resumable: every response is first written to <out>/parts/<key>.json and skipped on the next run. MFL answers 429
// even at 1.5 s spacing, so MFL requests are 3.5 s apart with backoff on 429; a request that still fails is listed in
// <out>/missing.json and never stops the run. Groups written at the end (one gz each):
//   mfl_core     league, leagueStandings, schedule, playoffBrackets + each playoffBracket, transactions, nflByeWeeks, players
//   mfl_weekly   weeklyResults W=1..17 (scores, starters, shouldStart, opt_pts)
//   mfl_rosters  rosters W=1..17 (ROSTER / INJURED_RESERVE / TAXI_SQUAD per week)
//   mfl_scores   playerScores W=1..17 (every player, free agents too)
//   mfl_proj     projectedScores W=1..17
//   mfl_nfl      nflSchedule W=1..18 (kickoffs)
//   core / stats / proj / players: Sleeper, same URLs and slimming as pull_season.mjs (no league endpoints)
import fs from 'node:fs'; import path from 'node:path'; import zlib from 'node:zlib';
const Y = process.argv[2], OUT = path.resolve(process.argv[3] || `mfl_${Y}_raw`), PARTS = path.join(OUT, 'parts');
if (!/^20\d\d$/.test(Y || '')) { console.error('usage: node mfl_pull.mjs <year> [out dir]'); process.exit(2); }
fs.mkdirSync(PARTS, { recursive: true });
const sleep = ms => new Promise(r => setTimeout(r, ms));
const MFLGAP = 3500, LID = '68106';
// league requests carry L=; NFL-wide ones (nflSchedule, nflByeWeeks) must not, or MFL refuses them
const MFL = q => /TYPE=nfl/.test(q) ? `https://api.myfantasyleague.com/${Y}/export?JSON=1&${q}` : `https://api.myfantasyleague.com/${Y}/export?L=${LID}&JSON=1&${q}`;
const A = 'https://api.sleeper.app/v1', S = 'https://api.sleeper.com';
const missing = {}, log = [];
let lastMfl = 0;
const fname = k => path.join(PARTS, k.replace(/[^A-Za-z0-9_=.-]+/g, '_') + '.json');
async function get(key, url, { mfl = false, tries = 6 } = {}) {
  const f = fname(key);
  if (fs.existsSync(f)) return JSON.parse(fs.readFileSync(f, 'utf8'));
  for (let i = 1; ; i++) {
    if (mfl) { const w = lastMfl + MFLGAP - Date.now(); if (w > 0) await sleep(w); lastMfl = Date.now(); }
    let st = 0;
    try {
      const r = await fetch(url, { headers: { 'user-agent': 'dynasty-tracker season pull' } }); st = r.status;
      if (!r.ok) throw new Error(r.status + ' ' + url);
      const j = await r.json();
      if (mfl && j && j.error) { missing[key] = 'MFL error ' + JSON.stringify(j.error).slice(0, 200); log.push(key + ': ' + missing[key]); return null; }  // a refusal is not retried
      fs.writeFileSync(f, JSON.stringify(j)); return j;
    } catch (e) {
      log.push(`${new Date().toISOString()} try ${i} ${key}: ${String(e && e.message || e).slice(0, 200)}`);
      if (i >= tries) { missing[key] = String(e && e.message || e).slice(0, 300); return null; }
      await sleep(st === 429 ? 20000 * i : 2000 * i);
    }
  }
}
const arr = x => x == null ? [] : [].concat(x);
const G = { mfl_core: {}, mfl_weekly: {}, mfl_rosters: {}, mfl_scores: {}, mfl_proj: {}, mfl_nfl: {}, core: {}, stats: {}, proj: {}, players: {} };
// ---------- MFL
const m = async (grp, q) => { const j = await get('mfl ' + q, MFL(q), { mfl: true }); if (j) G[grp][q] = j; return j; };
for (const q of ['TYPE=league', 'TYPE=leagueStandings', 'TYPE=schedule', 'TYPE=transactions', 'TYPE=nflByeWeeks', 'TYPE=players&DETAILS=1'])
  await m('mfl_core', q);
const pb = await m('mfl_core', 'TYPE=playoffBrackets');
for (const b of arr(pb && pb.playoffBrackets && pb.playoffBrackets.playoffBracket)) await m('mfl_core', `TYPE=playoffBracket&BRACKET_ID=${b.id}`);
for (let w = 1; w <= 17; w++) {
  await m('mfl_weekly', `TYPE=weeklyResults&W=${w}`);
  const ro = await m('mfl_rosters', `TYPE=rosters&W=${w}`);
  await m('mfl_scores', `TYPE=playerScores&W=${w}&YEAR=${Y}`);
  const pj = await m('mfl_proj', `TYPE=projectedScores&W=${w}`);
  // projectedScores without PLAYERS may return only a subset: ask again for every player on a roster that week
  const n = arr(pj && pj.projectedScores && pj.projectedScores.playerScore).length;
  if (ro && n < 300) {
    const ids = [...new Set(arr(ro.rosters && ro.rosters.franchise).flatMap(f => arr(f.player).map(p => p.id)))];
    for (let i = 0; i < ids.length; i += 120) await m('mfl_proj', `TYPE=projectedScores&W=${w}&PLAYERS=${ids.slice(i, i + 120).join(',')}`);
  }
  console.log('MFL week', w, 'done; projections', n);
}
for (let w = 1; w <= 18; w++) await m('mfl_nfl', `TYPE=nflSchedule&W=${w}`);
// ---------- Sleeper (public NFL data for the season; same shapes as pull_season.mjs)
const FPOS = new Set(['QB', 'RB', 'WR', 'TE', 'K', 'DEF']);
const fpos = p => p && (FPOS.has(p.position) ? p.position : (p.fantasy_positions || []).find(x => FPOS.has(x))) || null;
const sg = (u) => get('sleeper ' + u.replace(/^https:\/\/[^/]+/, ''), u, { tries: 5 });
const pl = await sg(`${A}/players/nfl`) || {}, POSOF = {};
for (const [id, p] of Object.entries(pl)) { const f = fpos(p); if (f) POSOF[id] = f; }
const slimRow = r => ({ player_id: r.player_id, team: r.team, opponent: r.opponent, player: r.player ? { position: POSOF[r.player_id] || r.player.position, first_name: r.player.first_name, last_name: r.player.last_name } : null, stats: r.stats });
const projURL = w => `${S}/projections/nfl/${Y}/${w}?season_type=regular` + ['QB', 'RB', 'WR', 'TE', 'K', 'DEF'].map(p => `&position[]=${p}`).join('');
{ const u = `${S}/schedule/nfl/regular/${Y}`, j = await sg(u); if (j) G.core[u] = j; }
for (let w = 1; w <= 18; w++) {
  const su = `${S}/scores/nfl/regular/${Y}/${w}`, sc = await sg(su);
  if (sc) G.core[su] = sc.map(x => ({ status: x.status, metadata: x.metadata ? { home_team: x.metadata.home_team, away_team: x.metadata.away_team, date_time: x.metadata.date_time } : null }));
  const tu = `${S}/stats/nfl/${Y}/${w}?season_type=regular`, st = await sg(tu);
  if (st) G.stats[tu] = st.filter(r => r.player && FPOS.has(POSOF[r.player_id] || r.player.position)).map(slimRow);
  const pr = await sg(projURL(w));
  if (pr) G.proj[projURL(w)] = pr.map(slimRow);
  console.log('Sleeper week', w, st ? st.length : 'MISSING', 'stat rows');
}
const F = ['full_name', 'first_name', 'last_name', 'position', 'fantasy_positions', 'team', 'injury_status', 'birth_date', 'years_exp'];
const keep = {};
for (const [id, p] of Object.entries(pl)) if (p && (POSOF[id] || !/^\d+$/.test(id))) keep[id] = { ...Object.fromEntries(F.map(k => [k, p[k] ?? null])), position: POSOF[id] || p.position };
G.players[`${A}/players/nfl`] = keep;
// ---------- write
const sizes = {};
for (const [k, v] of Object.entries(G)) { const f = path.join(OUT, k + '.json.gz'); fs.writeFileSync(f, zlib.gzipSync(JSON.stringify(v), { level: 9 })); sizes[k] = fs.statSync(f).size; }
fs.writeFileSync(path.join(OUT, 'missing.json'), JSON.stringify({ year: Y, missing, sizes, counts: Object.fromEntries(Object.entries(G).map(([k, v]) => [k, Object.keys(v).length])) }, null, 1));
fs.writeFileSync(path.join(OUT, 'pull.log'), log.join('\n') + '\n');
console.log('saved', sizes, 'missing', Object.keys(missing).length);
