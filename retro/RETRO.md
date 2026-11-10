# RETRO.md: the Retro edition ("DynastyCast")

Retro's own design source of truth. `DESIGN.md` governs Classic only and none of its rules apply here; nothing in
this file applies to Classic. Gradients and glow are allowed here and only here.

Page: `/dynasty-tracker/retro/` (`site/retro/index.html`, self-contained, plus `site/retro/data.json` for in-place
updates). BBP only; not ported to YILM.

## Isolation (hard rules)

1. All Retro code lives in `retro/`: `build.py`, `template.html`, this file.
2. `retro/build.py` only reads `pipeline/` (as text / JSON; it never imports or runs a pipeline script) and only
   writes `site/retro/`. It shares no CSS, JS or fitting code with Classic.
3. Nothing under `pipeline/` and nothing in Classic's HTML/CSS/JS is edited for Retro. Classic has no link to Retro.
4. The page reads Classic's `../build.json` (read-only) to notice a new deploy. That is its only runtime dependency
   on Classic; `build.py` itself never reads `site/`.

## Build

- `python3 retro/build.py` (workflow step "Retro edition", directly after "Past seasons (year switch)",
  `continue-on-error: true`; runs in every mode, so it refreshes with the Tuesday update and the 10-minute live runs).
- Atomic: `index.html` and `data.json` are written to a temp directory and moved to `site/retro/` together, only after
  everything succeeded. Any
  missing or malformed input: message on stderr, exit 1, and `site/retro/` does not exist (a stale one is removed).
  Classic still deploys.
- `retro/**` is not in the workflow's push paths. Test with Actions > Run workflow > build.
- Needs Pillow (already installed by the workflow's Install step).
- `template.html` is the page; `build.py` replaces the single marker `/*__RETRO_DATA__*/` with
  `const TV="<template version>";let D={...};`.
- `data.json` = the same `D` plus `tv`. `D.v` is the data version (first 12 hex of the SHA-256 of the data);
  `tv` / `TV` is the template version (first 12 hex of the SHA-256 of `template.html`). Neither is Classic's
  `build.json` `v`: `build.py` reads nothing outside `pipeline/`.

## Screens and data sources

| # | Screen | Source (read-only) | Fields of `D` |
|---|---|---|---|
| 1 | League Standings | `data_block.js`: `G`, `T` (w, l, pf), `H` (order), `PH` (movement, computed, not shown) | `stand` |
| 2 | Current Scoreboard | `wk{G+1}.json` `out[rid].mid / .pts` + `FUT` win % (pre-game figure, does not move in-game); `done` / `live` / `home` for the label | `mus`, `wk` |
| 3 | Week G+1 Forecast | `data_block.js`: `FUT` week G+1 projected score and win % | `mus` |
| 4 | Week G Results | `data_block.js`: `WK` week G; winner first, highest winning score first | `res` |
| 5 | League Almanac | `WK` (highest / lowest single week), `T` (PF, PA, all-play, luck high / low); ties go to the higher seed | `alm` |
| 6 | Hall of Champions | `champions.json` | `champs` |
| - | Team pictures | `avatars/{roster id}.webp` via `history/teams.json` `sleeper_roster`, shrunk to 20x20 PNG (bilinear), inlined | `av` |
| - | Short names | first `FN` key in `new_tail.js` naming the team; a team `FN` does not list takes `SH[roster id]` from `full_update.py` | `sh` |

- H2H standings only. Bye line under seed 2, playoff line under seed 6 (fixed in the template, BBP's format).
- Matchups are ordered by Sleeper matchup id, the favourite (higher win %) on top.
- No `wk{G+1}.json` (after the last regular-season week): screens 2 and 3 and the score lines of the ticker are left
  out; the build succeeds.
- Screen 2's panel header has three states (`D.wk`), decided from the week file's own fields: `done` (NFL teams
  whose game is final), `live` (NFL teams playing now), `home` (the week's home teams, one per game, so
  2 x `len(home)` teams play that week):
  - `Week N · Final` (`final`): `home` is not empty, `live` is empty, every `home` team is in `done`, and `done`
    holds at least 2 x `len(home)` teams. Stays until the next weekly build moves `G` on.
  - `Week N · Live` (`live`): not final, and `done` or `live` is not empty or any fantasy score is above 0.
  - `Week N · Pre-game` (`pre`): everything else (what `full_update.py` writes on Tuesday: `done` empty, all `pts` 0).
- Never highlight Bill's Block Party (DESIGN.md rule 13 applies here too). Champions and records show whoever the
  data says.
- `<meta name="robots" content="noindex">`. Start screen has a small CLASSIC link to `../`.

## Tokens (`:root` in template.html)

| Token | Value | Job |
|---|---|---|
| `--purple` | `#332370` | frame background, gradient end |
| `--orange` | `#e28144` | gradient end (header bar, stage) |
| `--blue` | `#354e84` | panels, lower display line |
| `--gray` | `#545658` | spare |
| `--yellow` | `#ffff6f` | titles, column heads, rank numbers, playoff line |
| `--peri` | `#8b9df8` | dimmed text (losers, win %), bye line, badge ring |
| `--white` / `--black` | `#fff` / `#000` | text fill / outline and hard shadow |
| `--win` / `--loss` | `#7dffa0` / `#ff8f8f` | spare |
| `--line` | `#8da4e8` | rule above the lower display line |
| `--badge-hi` / `--badge-lo` | `#5f6def` / `#2040fa` | ODL badge fill (gradient) |
| `--glow` | `rgba(255,255,255,.25)` | panel inner glow |
| `--drift` | `#222` | luminance drift layer |
| `--halo` | `rgba(255,255,255,.35)` | soft-focus text glow |
| `--wash` | `#808080` | desaturation overlay |
| `--card` | 8-step blue gradient | champion cards |

## Type treatment

- Martian Mono (Google Fonts, variable: wdth 75-112.5, wght 100-800), `font-stretch:75%`, `letter-spacing:-.05em`;
  the clock uses 112.5%.
- Every text in the frame: black outline under the fill (`-webkit-text-stroke:2px #000; paint-order:stroke`, `.375cqw`
  on the 4:3 layout), hard offset shadow `.375cqw .375cqw #000`, plus a faint halo `0 0 .06em var(--halo)`.
- Phones: full-bleed frame, `font-size:clamp(.875rem,4vw,1.125rem)`, side margin 24px. Wide screens (>=768px and
  landscape): a 4:3 frame, `font-size:min(4vh,3vw)`, side margin 7.8125%.
- Standings columns: rank `1.6em`, picture, name `1fr`, W-L `3.1em`, PF `4.6em`; on phones rank `1.4em`, W-L `2.6em`,
  PF `4.2em` (holds 1999.9). PF was 4.6em on phones until 2026-11-09: at 360 the longest short name ("Block Party")
  had 0.6px to spare in Chromium and overran its box by 3.4px in WebKitGTK; now 6.4px / 2.4px to spare.

## Team names (fit rule)

- Every team name, on every screen and in the ticker, starts as the full name. `fitNames()` keeps it when it fits its
  own box on one line; otherwise that one element shows the short form (so one screen can mix full and short names).
  Ticker: per message, full names if the whole message fits, else short names.
- The test is the text width (a Range, to a fraction of a pixel) against the box's content width. Type size, column
  widths and layout are never changed to make a name fit.
- Runs after every screen change, on resize, when fonts finish loading, and after the turn-on.
- Name boxes (`.nm`) and the title (`h1`) do not clip (`overflow:visible`): a clip box there shaved the outline and
  hard shadow at its edges. The ticker keeps its clip box, widened by `.25em` side padding that only the outline and
  shadow may enter.

## Overlays and motion

- `.desat`: `--wash` with `mix-blend-mode:saturation`, opacity .1 (10% desaturation).
- `.drift`: vertical black / `--drift` gradient, `mix-blend-mode:screen`, opacity .06, 8s alternate.
- `canvas.grain`: half-resolution noise redrawn every 83ms, `mix-blend-mode:overlay`, opacity .18.
- `.flash` + `tvon`: 1.6s TV turn-on when Start is pressed.
- Wipe: each screen and each ticker message is revealed left to right with `clip-path` in steps (0.55s / 0.45s).
- Screens advance every 10s on the wall clock; tap the left / right half or use the arrow keys (Space = next), the
  chosen screen gets its full 10s. Page bars show the position.
- Music: Web Audio synthesis only (no audio file); Sound button toggles it.

## The no-container-filter lesson

No `filter` on any container. iOS Safari re-rasterises a filtered ancestor at low resolution after each animation,
so everything inside goes blurry. Soft focus therefore comes from the text halo, and the wash from the
saturation-blend overlay. The only `filter` on the page is the `drop-shadow` on the ODL badge (`.mk`), which holds
nothing but its own two lines of text. Keep it that way.

## Auto-update (no reload)

- Every 2 minutes the page fetches `../build.json` (`no-store`). When its `v` is one the page has not handled yet
  (the first poll after load included), it fetches `./data.json` (`no-store`).
- New data (`data.json` `v` differs from the page's `D.v`): held until the next screen change, then swapped in place.
  The screen list, the stage and the ticker are rebuilt (screens 2 and 3 appear or disappear with `mus`); pictures
  already on the page are kept. No reload: the music keeps playing and the clock sync (`offset`) is untouched.
- `data.json` missing, not JSON or the wrong shape: the current data stays and the next poll tries again.
- Template changed (`data.json` `tv` differs from the page's `TV`): the page reloads at the next screen change. That
  reload skips the start screen (no turn-on, sound off: browsers do not start audio without a tap) so an unattended
  screen keeps running. A manual reload shows the start screen as usual.

## Checks before shipping a change

- 360, 402, 440 wide and 1280x800, every screen, captured after the wipe: nothing clipped, wrapped or ellipsised;
  every team name on one line; panels full width between the side margins (measured).
- Measure with Martian Mono actually loaded (it does not load in the sandbox without a local copy).
- Real iPhone Safari is checked by Nicklaus.
- Classic unchanged: `git status` shows changes only in `retro/` (plus the documented one-liners).
