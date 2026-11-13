// READ-ONLY data check (2026-11-13). Pulls what MFL (league 68106) and Sleeper still return for past seasons
// and writes raw responses + a request log to probe/out/. Commits nothing; the workflow uploads probe/out as an artifact.
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
const OUT = path.resolve('probe/out');
fs.mkdirSync(OUT, { recursive: true });
const sleep = ms => new Promise(r => setTimeout(r, ms));
const UA = { 'user-agent': 'dynasty-tracker data check (github.com/billsblockparty/dynasty-tracker)' };
const LOG = [];
async function get(name, u, { gap = 1500, tries = 4 } = {}) {
  for (let i = 1; ; i++) {
    const t0 = Date.now(); let r, txt = '', err = null;
    try { r = await fetch(u, { headers: UA }); txt = await r.text(); } catch (e) { err = String(e); }
    const ms = Date.now() - t0;
    const h = r ? Object.fromEntries([...r.headers].filter(([k]) => /rate|retry|limit|content-type|location|server/i.test(k))) : {};
    const ent = { name, u, final: r?.url, status: r?.status ?? null, bytes: txt.length, ms, try: i, h, err };
    LOG.push(ent);
    await sleep(gap);
    if (r && r.ok) {
      const f = path.join(OUT, name + '.json.gz');
      fs.mkdirSync(path.dirname(f), { recursive: true });
      fs.writeFileSync(f, zlib.gzipSync(txt));
      try { return JSON.parse(txt); } catch { ent.err = 'not json: ' + txt.slice(0, 200); return null; }
    }
    ent.body = txt.slice(0, 300);
    if (i >= tries) return null;
    await sleep((r?.status === 429 ? 30000 : 3000) * i);
  }
}
const M = (y, q) => `https://api.myfantasyleague.com/${y}/export?L=68106&JSON=1&${q}`;
const MN = (y, q) => `https://api.myfantasyleague.com/${y}/export?JSON=1&${q}`;   // league-independent exports
async function mfl(y, full) {
  const p = `mfl/${y}/`;
  for (const t of ['league', 'rules', 'schedule', 'leagueStandings&ALL=1', 'leagueStandings', 'transactions&TRANS_TYPE=*', 'playoffBrackets',
                   'pointsAllowed', 'futureDraftPicks', 'draftResults', 'assets', 'history', 'accounting'])
    await get(p + t.replace(/[&=*]/g, '_'), M(y, 'TYPE=' + t));
  const weeks = full ? Array.from({ length: 17 }, (_, i) => i + 1) : [1, 14, 16];
  for (const w of weeks) {
    await get(`${p}weeklyResults_W${w}`, M(y, `TYPE=weeklyResults&W=${w}`));
    await get(`${p}rosters_W${w}`, M(y, `TYPE=rosters&W=${w}`));
    await get(`${p}playerScores_W${w}`, M(y, `TYPE=playerScores&W=${w}&YEAR=${y}`));
    await get(`${p}nflSchedule_W${w}`, MN(y, `TYPE=nflSchedule&W=${w}`));
  }
  await get(`${p}rosters_now`, M(y, 'TYPE=rosters'));
  await get(`${p}playerScores_W1_freeagent`, M(y, `TYPE=playerScores&W=1&YEAR=${y}&STATUS=freeagent`));
  await get(`${p}playerScores_W1_rules`, M(y, `TYPE=playerScores&W=1&YEAR=${y}&RULES=1`));
  await get(`${p}playerScores_YTD`, M(y, `TYPE=playerScores&W=YTD&YEAR=${y}`));
  for (const w of [1, 14]) await get(`${p}projectedScores_W${w}`, M(y, `TYPE=projectedScores&W=${w}`));
  await get(`${p}nflByeWeeks`, MN(y, 'TYPE=nflByeWeeks'));
  await get(`${p}injuries_W1`, MN(y, 'TYPE=injuries&W=1'));
  await get(`${p}players_details`, MN(y, 'TYPE=players&DETAILS=1'));
  await get(`${p}liveScoring_W1`, M(y, 'TYPE=liveScoring&W=1&DETAILS=1'));
  await get(`${p}topStarters_W1`, M(y, 'TYPE=topStarters&W=1'));
  await get(`${p}topOwns`, M(y, 'TYPE=topOwns'));
}
// Sleeper side (for the "score it ourselves" option and for projections): stats, projections, schedule, scores
async function sleeper(y, full) {
  const p = `sleeper/${y}/`, S = 'https://api.sleeper.com';
  const weeks = full ? Array.from({ length: 18 }, (_, i) => i + 1) : [1, 14];
  for (const w of weeks) {
    await get(`${p}stats_W${w}`, `${S}/stats/nfl/${y}/${w}?season_type=regular`, { gap: 250 });
    await get(`${p}proj_W${w}`, `${S}/projections/nfl/${y}/${w}?season_type=regular&position[]=QB&position[]=RB&position[]=WR&position[]=TE&position[]=K&position[]=DEF`, { gap: 250 });
  }
  await get(`${p}schedule`, `${S}/schedule/nfl/regular/${y}`, { gap: 250 });
  await get(`${p}scores_W1`, `${S}/scores/nfl/regular/${y}/1`, { gap: 250 });
}
const t0 = Date.now();
await mfl(2024, true);
await mfl(2021, true);
for (const y of [2020, 2025]) {   // seasons outside 2021-24: do they answer?
  await get(`mfl/${y}/league`, M(y, 'TYPE=league'));
  await get(`mfl/${y}/weeklyResults_W1`, M(y, 'TYPE=weeklyResults&W=1'));
}
await sleeper(2024, true);
await sleeper(2021, true);
fs.writeFileSync(path.join(OUT, 'log.json'), JSON.stringify({ ran: new Date().toISOString(), secs: (Date.now() - t0) / 1000, log: LOG }, null, 1));
console.log('requests', LOG.length, 'non-200', LOG.filter(x => x.status !== 200).length, 'secs', (Date.now() - t0) / 1000);
