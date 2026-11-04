// Paper Trail, phase 1 (data audit): raw transaction log for every season, stored as-is for the audit.
//   MFL league 68106, 2021-2024: league (franchises), transactions (all types), draftResults, futureDraftPicks, players referenced
//   Sleeper 2025 + current league: league, users, rosters, transactions (rounds 0-18), traded_picks, drafts (+ picks, traded picks)
//   Sleeper players (slim: fantasy positions only) and the DynastyProcess id map (MFL id <-> Sleeper id)
// Output: pipeline/history/paper/*.json (public league data). Run in CI (network): node pipeline/history/paper_pull.mjs
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const OUT = path.join(path.dirname(fileURLToPath(import.meta.url)), 'paper');
fs.mkdirSync(OUT, { recursive: true });
const sleep = ms => new Promise(r => setTimeout(r, ms));
const UA = { 'user-agent': 'dynasty-tracker (github.com/billsblockparty/dynasty-tracker)' };
async function get(u, { text = false, tries = 6 } = {}) {
  for (let i = 1; ; i++) {
    try { const r = await fetch(u, { headers: UA });
      if (!r.ok) throw new Error(r.status + ' ' + u);
      const j = text ? await r.text() : await r.json(); await sleep(u.includes('myfantasyleague') ? 1500 : 200); return j; }
    catch (e) { if (i >= tries) { console.log('FAILED', u, String(e)); return null; } await sleep((String(e).includes(' 429') ? 30000 : 1500) * i); }
  }
}
const arr = x => x == null ? [] : [].concat(x);
const W = (f, d) => { fs.writeFileSync(path.join(OUT, f), JSON.stringify(d)); console.log('wrote', f, JSON.stringify(d).length); };
const MFL = (y, q) => `https://api.myfantasyleague.com/${y}/export?L=68106&JSON=1&${q}`;

async function mfl(y) {
  const o = { year: y };
  o.league = (await get(MFL(y, 'TYPE=league')))?.league || null;
  o.transactions = (await get(MFL(y, 'TYPE=transactions&TRANS_TYPE=*')))?.transactions || null;
  o.draftResults = (await get(MFL(y, 'TYPE=draftResults')))?.draftResults || null;
  o.futureDraftPicks = (await get(MFL(y, 'TYPE=futureDraftPicks')))?.futureDraftPicks || null;
  o.assets = (await get(MFL(y, 'TYPE=assets')))?.assets || null;
  // every player id referenced by a transaction or a draft pick
  const ids = new Set();
  const scan = s => String(s || '').split(/[,|]/).forEach(t => { if (/^\d{4,6}$/.test(t)) ids.add(t); });
  for (const t of arr(o.transactions?.transaction)) for (const k of Object.keys(t)) if (k !== 'timestamp' && k !== 'franchise' && k !== 'franchise2') scan(t[k]);
  for (const d of arr(o.draftResults?.draftUnit)) for (const p of arr(d.draftPick)) if (p.player) ids.add(p.player);
  o.players = {};
  const list = [...ids];
  for (let i = 0; i < list.length; i += 150) {
    const P = (await get(MFL(y, `TYPE=players&DETAILS=1&PLAYERS=${list.slice(i, i + 150).join(',')}`)))?.players;
    for (const p of arr(P?.player)) o.players[p.id] = [p.name, p.position, p.team, p.draft_year || null, p.draft_round || null, p.draft_pick || null];
  }
  return o;
}
const S = 'https://api.sleeper.app/v1';
async function sleeperLeague(L) {
  const o = { league_id: L };
  o.league = await get(`${S}/league/${L}`);
  o.users = await get(`${S}/league/${L}/users`);
  o.rosters = await get(`${S}/league/${L}/rosters`);
  o.traded_picks = await get(`${S}/league/${L}/traded_picks`);
  o.transactions = {};
  for (let r = 0; r <= 18; r++) { const t = await get(`${S}/league/${L}/transactions/${r}`); if (t && t.length) o.transactions[r] = t; }
  o.drafts = [];
  for (const d of arr(await get(`${S}/league/${L}/drafts`))) {
    o.drafts.push({ draft: await get(`${S}/draft/${d.draft_id}`), picks: await get(`${S}/draft/${d.draft_id}/picks`), traded_picks: await get(`${S}/draft/${d.draft_id}/traded_picks`) });
  }
  return o;
}
(async () => {
  for (const y of [2021, 2022, 2023, 2024, 2025]) W(`mfl_${y}.json`, await mfl(y));  // 2025: whatever MFL holds after the rollover (the league moved to Sleeper in March 2025)
  // Sleeper: current league and its previous_league_id chain
  let L = process.env.DT_LEAGUE || '1335450123487961088';
  const ids = new Set();
  while (L && L !== '0') {
    const o = await sleeperLeague(L);
    const y = o.league?.season || L;
    W(`sleeper_${y}.json`, o);
    for (const r of Object.values(o.transactions)) for (const t of r) { Object.keys(t.adds || {}).forEach(i => ids.add(i)); Object.keys(t.drops || {}).forEach(i => ids.add(i)); }
    for (const d of o.drafts) for (const p of arr(d.picks)) if (p.player_id) ids.add(p.player_id);
    for (const r of arr(o.rosters)) for (const p of arr(r.players)) ids.add(p);
    L = o.league?.previous_league_id;
  }
  // Sleeper players: fantasy positions (for the MFL name + position fallback) plus every referenced id
  const P = await get(`${S}/players/nfl`);
  const slim = {};
  for (const [id, p] of Object.entries(P || {})) {
    const pos = p.position || (p.fantasy_positions || [])[0];
    if (ids.has(id) || ['QB', 'RB', 'WR', 'TE', 'K', 'DEF'].includes(pos))
      slim[id] = [p.full_name || [p.first_name, p.last_name].filter(Boolean).join(' '), pos || null, p.team || null, p.years_exp ?? null, p.birth_date || null];
  }
  W('sleeper_players.json', slim);
  // DynastyProcess player id map (mfl_id <-> sleeper_id), CC-BY
  const csv = await get('https://raw.githubusercontent.com/dynastyprocess/data/master/files/db_playerids.csv', { text: true });
  if (csv) {
    const split = l => { const o = []; let c = '', q = false; for (const ch of l) { if (ch === '"') q = !q; else if (ch === ',' && !q) { o.push(c); c = ''; } else c += ch; } o.push(c); return o; };
    const [h, ...rows] = csv.trim().split(/\r?\n/); const H = split(h);
    const im = H.indexOf('mfl_id'), is = H.indexOf('sleeper_id'), inm = H.indexOf('name'), ip = H.indexOf('position');
    const map = {};
    for (const line of rows) { const c = split(line); if (c[im] && c[im] !== 'NA') map[c[im]] = [c[is] && c[is] !== 'NA' ? c[is] : null, c[inm], c[ip]]; }
    W('dp_ids.json', map);
  }
  console.log('done');
})();
