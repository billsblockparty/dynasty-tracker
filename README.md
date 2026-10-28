# Official Dynasty League tracker

Live site: https://billsblockparty.github.io/dynasty-tracker/

Standings, leaderboards, stats, rosters, matchups, compare and playoffs for Sleeper league `1335450123487961088`
(half-PPR, 10 teams, top 6 make the playoffs, Weeks 15–17).

## How it updates

All of this runs in GitHub Actions (`.github/workflows/site.yml`); nothing needs a computer switched on.

| When (ET) | What |
|---|---|
| Tuesday ~6:17 AM (backup ~11:17 AM) | **Weekly refresh**: final scores and stat lines for the completed week, standings, ranks, efficiency, rosters, next week's lineups and projections, playoff projections. Data changes are committed back to `pipeline/`. |
| Every 10 min in game windows (Thu night, Sunday, Mon night, December Saturdays) | **Live scores** for the current week. |
| Any push to `pipeline/` or the workflow | Weekly mode (re-runs safely if nothing new). |

Run one by hand: **Actions → Build and publish site → Run workflow**, then pick `weekly`, `live` or `build`.

The page shows a "New scores · Refresh" notice when a newer build has been published.

## Layout

- `pipeline/sleeper.mjs`, `pipeline/pull.mjs` — Sleeper API pulls (league scoring computed from raw stats).
- `pipeline/run.py` — orchestrates `weekly`, `live` and `build`.
- `pipeline/full_update.py` — completes a week (hist, weeks, data_block, ranks, rosters, next week's lineups).
- `pipeline/score.py` — applies in-week scores.
- `pipeline/rebuild.py` and the `*_build.py` files — assemble the page; `build_static.py` makes the no-script download, `build_site.py` writes `site/`.

## Known limits

- Trades are not yet added to the Compare tab's trade history automatically.
- Stat corrections are picked up for a week only when that week is re-run (`weekly` with `--force`).
- Weeks 15–17 run as playoff projections; the in-week view for playoff weeks still needs checking before Week 15.
