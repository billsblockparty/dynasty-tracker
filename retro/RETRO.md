# RETRO.md: the Retro edition ("DynastyCast")

Retro's own design source of truth. `DESIGN.md` governs Classic only and none of its rules apply here; nothing in
this file applies to Classic. Gradients and glow are allowed here and only here.

Page: `/dynasty-tracker/retro/` (`site/retro/index.html`, self-contained, plus `site/retro/data.json` for in-place
updates). BBP only; not ported to YILM.

## Isolation (hard rules)

1. All Retro code lives in `retro/`: `build.py`, `template.html`, this file (and, for the tracker theme below, `theme_build.py`,
   `theme.css`, `theme.js`, `wordmark.svg`, `wordmark_gen.py`, the `favicon*` files, `fonts/`; `qa/` holds development audits only).
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
| `--badge-hi` / `--badge-lo` | `#5f6def` / `#2040fa` | TL badge and favicon plate fill (gradient) |
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
saturation-blend overlay. The only `filter` on the page is the `drop-shadow` on the TL badge (`.mk`), which holds
nothing but its own drawn mark (one small inline svg since 2026-11-12; two lines of text before). Keep it that way.

## TL badge and favicon (2026-11-12)

One mark everywhere (Nicklaus, 2026-11-12): **TL**, T in `--yellow` (as "THE"), L in `--white` (as "LEAGUE"), on the blue plate. It
replaces the ODL / DYNASTY badge and the ODL favicon of pass 5 (same day, earlier).

- **Badge** (`.mk` in the loop's header): the plate is unchanged CSS (gradient `--badge-hi` to `--badge-lo`, white 2px border,
  periwinkle hairline, hard shadow, the same box: 67.36 x 53.06px at 402 wide, 139.67 x 110px at 1280 x 800). On it, one inline svg
  (`.mk-g`, viewBox 127 x 100 = the plate, out of flow so the plate keeps its box; `wordmark_gen.py badge()`): TL alone, no second
  line. It is the favicon's 32px composition scaled by 5/3: cap 60 of the plate's 100, strokes 10, T 30 wide, L 20 wide, 10 apart,
  black outline 3.33, `--orange` step at 3.33 / 3.33, `--peri` step at 6.67 / 6.67; T's steps reach L's outline. Total ink 73.3 x 73.3
  units, centred. Measured from pixels (8x): ink to the plate's inner frame 13.75 / 13.5px left / right and 6.5 / 6.75px top / bottom
  at 402 wide (ink 35.75 x 35.75px), 29.1 / 28.4px and 14.25 / 14.25px at 1280 x 800 (ink 77.5px). No closed counters; the narrowest
  opening (between T's periwinkle step and L's outline, under T's bar) is 6.67 units = 3.5px at 402 wide, 7.3px at 1280 x 800. Contrast on the plate's
  gradient as the favicon's (below). Tokens only (`--white --yellow --orange --peri --black`), no new token.
- **Letters.** T and L here are the icons' grid letters (`_tl()`: square corners, whole units), not `letters()`. `letters()` still
  holds O D S N Y (pass 5, for ODL / DYNASTY) and the pair gaps `GO` / `GD`: unused by anything since this change, kept for a later
  word. `wordmark.svg` itself is unchanged (`wordmark_gen.py C` still reproduces it byte for byte).
- **Favicon** (cleanup job 1). The same mark on the same plate (gradient `--badge-hi` to `--badge-lo`, white border, hard shadow). Square letters as the wordmark's T and L, on a
  whole-unit grid. Three drawings from `wordmark_gen.py` (literal token values: a favicon cannot read the page's custom properties):
  - **16px** (`icon16()` -> `retro/favicon-16.svg` -> `favicon-16.png`): hand-hinted, 1 unit = 1 pixel, `shape-rendering:crispEdges`.
    Plain letters with 2px strokes, no outline, no steps. T 6 x 9, L 4 x 9, 1px apart; ink to the plate's inner frame 1 / 1 / 2 / 2px
    (left / right / top / bottom), read from the PNG's pixels.
  - **32px** (`icon()` -> `retro/favicon.svg`, viewBox 64 -> `favicon-32.png`): the stepped title's treatment: black outline, `--orange`
    step at 1 / 1px, `--peri` step at 2 / 2px; stems 3px. T's steps touch L's outline, as in the wordmark. Total ink (fill, outline,
    steps) 2.50px from the plate's inner frame on all four sides (measured on a 16x render).
  - **180px** (`icon180()` -> `favicon-180.png`, apple-touch-icon): the 32px artwork scaled 2.375 on `--purple`, 14px margin, opaque.
  - Contrast on the plate's gradient (3:1 required, graphics): white 4.27 (top) to 6.61:1 (bottom), yellow 4.02 to 6.23:1.
  - **Links: PNG only, three, each with its size** (`sizes="16x16"`, `"32x32"`, apple-touch `"180x180"`), so a tab at 1x takes the
    hinted 16px drawing and a tab at 2x the 32px one. No svg icon link: a browser that prefers an svg icon at any size would scale the
    32px artwork down to 16px, the unreadable case this replaces. `favicon.svg` and `favicon-16.svg` stay in the repo as the PNGs'
    sources. Desktop Safari's pinned-tab `mask-icon` is still not provided.
- **Single source:** `python3 retro/wordmark_gen.py apply` writes `retro/favicon.html` (three self-contained `<link>` tags, data URIs)
  and the marked blocks of `template.html` (`<!--ICON-->`, `<!--MK-->`, `/*MK-CSS*/`) from the committed files. The builds read the
  committed results only: `build.py` is unchanged (the links and the svg are part of the template, so `tv` changes with them);
  `theme_build.py` reads `favicon.html` (patch 9; still exactly three links). After changing a letter or an icon:
  `wordmark_gen.py icon > retro/favicon.svg`, `wordmark_gen.py icon16 > retro/favicon-16.svg`, `python3 retro/qa/icons_png.py`,
  `wordmark_gen.py apply`, rebuild, `retro/qa/loop.py badge`.
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

---

# Tracker theme (`/retro/tracker/`)

The full tracker in the DynastyCast look: a themed copy of Classic's built page at `/dynasty-tracker/retro/tracker/`.
The loop above is unchanged. These rules replace DESIGN.md's look rules inside the copy; Nicklaus's precision standards
carry over. BBP only. No link from Classic or from the loop points here yet.

## Status per tab

| Tab | Status | Effort left |
|---|---|---|
| Standings, phones (360P / 402P / 440P / 874L; Dumb, Nerd, H2H, Median) | `LIVE` 2026-11-09; Glossary 2026-11-12; rank chips and streak tile on the one solid recipe 2026-11-12 (cleanup job 2) | - |
| Standings, desktop (>= 1100px, incl. 956L: the table, the one-team-per-row cards with the Nerd column, Glossary; 1100 / 1240 / 1440 / 1920) | `LIVE` 2026-11-12 ("Pass 5" below); every rank chip on the solid recipe 2026-11-12 (cleanup job 2) | - |
| Leaderboards, Players, The Wire, Compare, phones and desktop (360P / 402P / 440P / 874L / 956L / 1440; every stat, position, filter, Position / Team, Pts / per game, the eight Compare sections, menus, Glossary) | `LIVE` 2026-11-11 ("Pass 2" below) | - |
| Matchups, phones and desktop (360P / 402P / 440P / 1100 / 1440 / 1920; every week, Lineup / Optimal, Position / Slate, Lean / Detailed, Colors, FINAL / LIVE / PROJ, week menu) | `LIVE` 2026-11-11 ("Game Day" below) | - |
| Playoffs, phones and desktop (bracket, game panels, matchup builder, schedule, lineups) | `LIVE` 2026-11-11 ("Game Day" below) | - |
| Rosters, Drafts (list below 1100px and the board from 1100px) and Paper Trail (Picks, Players, the sheet with its two-column trade rows), phones and desktop (360P / 402P / 440P / 874L / 956L / 1440; every team, year, order, sort and colour mode, Glossary) | `LIVE` 2026-11-11 ("Pass 3" below) | - |
| Stats (all 17 sections, every toggle, Glossary) and Team Hub (every team, Data and Trends, every week, Glossary), phones and desktop (360P / 402P / 440P / 874L / 956L / 1440) | `LIVE` 2026-11-11 ("Pass 4" below) | - |

**All twelve tabs are themed, phones and desktop (2026-11-12).** What is still open is listed under "Known issues / cleanup".

## Decisions (Nicklaus, 2026-11-09)

- Rank tiles: CSS-drawn (option B); Classic's bitmap art stays available with `class="rk-art"` on `<html>`.
- Type treatment per role (rule 2 below).
- Martian Mono self-hosted with `size-adjust:87.5%`.
- Static grain printed on the surfaces; no desaturation, no drift, no overlay layers.
- The chunks are copied into the copy (about 13 MB more per deploy).
- Past-season pages stay Classic's.
- Bye = yellow, playoff = periwinkle (the reverse of the loop's two line colours; it follows Classic's gold bye tier).
- `theme_build.py` runs after `retro/build.py`, `continue-on-error`.

## Decisions (2026-11-10, from Nicklaus's iPhone and desktop Safari reports)

- 2026-11-10 · Dark ink never carries the black shadow or outline (rule 2); the default shadow's colour is derived from
  the ink (`--shk`) · the blanket T1 shadow sat behind Classic's dark text on every pastel tile outside Standings
  (position tiles, pick tiles, selected white segments: 4,241 text nodes over 100 tab states at 402P), read as doubled
  letters.
- 2026-11-10 · Lineup score cells: figure 18.375px -> 14.5px (11.5px for a lineup with a five-character figure), label
  tracking .06em -> 0, ink + shadow centred (rule 11) · in Classic's 38px cell the Martian Mono figure left 1.6px to
  the frame and its shadow reached the frame line.
- 2026-11-10 · FK / FL flex chips: no shadow (chips are T0, rule 2).
- 2026-11-10 · Header wordmark: option C, the stepped title, replaces Classic's script art in the copy (Nicklaus's pick of
  three) · the script clashed with the look and its opaque black counters showed on the purple ground.

## Decisions (2026-11-11, Game Day pass)

- 2026-11-11 · Matchups and Playoffs themed, phones and desktop (section "Game Day") · the two tabs that share the lineup.
- 2026-11-11 · Position palette = six tokens `--pos-*`, tiles filled with them, black ink, no shadow · one colour set for the
  Standings position labels, lineup tiles, position pills and (later) Drafts; dark tiles with coloured ink were the alternative
  (weaker at 14px, and K / DEF as text on blue are only 3.4 / 2.9:1).
- 2026-11-11 · Lineup score cells 44px wide with an 18px figure (was 38px / 14.5px since 2026-11-10; Classic 38px / 18.375px)
  · Nicklaus wants the figures large; the 6px per side comes out of the name columns and no name gains an abbreviation or a line.
- 2026-11-11 · Home / road tiles and injury tags are solid colour with black ink, no ring · a ringed 17px tile leaves the 10.7px
  "@" under 2px top and bottom in every engine.
- 2026-11-11 · "Week rank N" is a figure, not a tile · rule 5 (tile no taller than the 8px capitals beside it) and rule 11 (2px
  above and below the digit) cannot both hold for a digit worth reading.
- 2026-11-11 · Paper Trail > Picks: tile digits centred by Martian Mono's own glyph ink (theme.css block "Paper Trail > Picks",
  theme.js item 4) · Nicklaus, iPhone: TIMES TRADED "1" sat right of centre (measured 10.4px / 5.3px in a 23px tile; "2" 8.5 / 7.2).
  Classic's `tileSnap` places the digit by `BC7`, Barlow Condensed's outlines.
- 2026-11-11 · Selected segments, team switch and menu rows are the badge everywhere those components occur (not only Game Day)
  · they are one component; rule 4.

## Decisions (2026-11-11, pass 2: Leaderboards, Players, The Wire, Compare)

- 2026-11-11 · Leaderboards, Players, The Wire and Compare themed, phones and desktop (section "Pass 2") · the four tabs built from
  token-driven tables and pills.
- 2026-11-11 · Players and The Wire stand on a `--blue-2` plate (Playoffs' recipe) · Classic has no panel there and title, pills,
  search and column heads stood on the ground.
- 2026-11-11 · Pills (`.lbc`, `.wpb`) are `--blue-3` wells with a 4px corner; selected = the badge; a position pill carries its
  `--pos-*` colour as the label and, selected, as the fill with black ink · Classic's black 999px pills used `--ink` as a fill; the
  round pill is not part of this look. K / DEF labels are 5.59 / 4.66:1 on `--blue-3` (3.43 / 2.86:1 on `--blue`).
- 2026-11-11 · Bye weeks: past = `--peri-lt`, this week = white, upcoming = yellow (Classic's token) · Classic's past bye is
  `#4b5262`, 1.34:1 on the row. The rule is not scoped to one tab (same component on Rosters: 39 -> 15 under the limit there).
- 2026-11-11 · Compare: A = `--peri`, B = `--orange` (as the Playoffs builder keys); the Players section's position heads are
  position chips, not coloured text · K / DEF as text on the panel are 4.43 / 3.69:1.
- 2026-11-11 · Compare section pills between 760 and 1099px: 11px, tracking 0, 3px between pills (Classic 12.5px, .05em, 7px)
  · eight 57.4px pills on a landscape phone: "POSITIONS" ran past the pill's edge; now 3.3px each side.
- 2026-11-11 · Compare position chips between two figures are 17px tall (Classic 15px), rows unchanged · "QB" had 1.85px under
  the tail of "Q".
- 2026-11-11 · theme.js item 5: Compare > Schedule right-hand seed chips are taken away from Classic's tile fitter · a Classic bug
  (below, "Pass 2") that CSS cannot undo.

## Decisions (2026-11-11, pass 3: Rosters, Drafts, Paper Trail)

- 2026-11-11 · Rosters, Drafts (list and desktop board) and Paper Trail (Picks, Players, sheet) themed, phones and desktop (section
  "Pass 3") · the rest of Front Office.
- 2026-11-11 · The three sections stand on a `--blue-2` plate (the Players / The Wire recipe) · Classic has no panel there: titles,
  year buttons, the Picks / Players switch and Rosters' group heads stood on the ground.
- 2026-11-11 · Head strips are `--blue-3` everywhere: Rosters' position-group heads, the round heads of Drafts and Paper Trail, the
  sheet's season strip (as The Wire's column heads) · K and DEF as label text are 4.43 / 3.69:1 on the plate and 5.59 / 4.66:1 on the
  strip; Classic's season strip is the page colour, which reads as "ground" here.
- 2026-11-11 · Year buttons and the Picks / Players switch: unselected = a raised `--blue` button, selected = the badge (rule 4)
  · they were Classic's white button with black text.
- 2026-11-11 · Rosters team picker: selected = the badge; the other teams' pictures are dimmed by opacity alone · Classic uses
  `--ink` as the selected fill and `filter:grayscale(1)` on the pictures (rule 8: no filter).
- 2026-11-11 · A traded pick's banner on the Drafts board is the white ticket with black ink (the colours of the TIMES TRADED tile
  and the FAAB tile); the VIA box of the list is a `--blue-3` chip with a yellow ring · one motif for "this changed hands"; Classic's
  gold literals have no token here. Yellow was the alternative (louder: 25 of 40 cells carry a banner in 2026).
- 2026-11-11 · Board cells: black ink at full strength · Classic dims four of the cell's lines to 70-82% ("QB" in the strip 3.83:1).
- 2026-11-11 · theme.js item 6: Paper Trail's tile width, column widths and NFL slot edge by Martian Mono's glyph ink · Classic's
  values are written inline by private fitters (below, "Pass 3").

## Decisions (2026-11-11, pass 4: Stats, Team Hub)

- 2026-11-11 · Stats and Team Hub themed, phones and desktop (section "Pass 4") · the last two tabs.
- 2026-11-11 · Better / worse cells are solid: `--win` / `--loss` with black ink, level = a `--blue-3` well, the team's own cell white
  · Classic's 17 to 20% tints carried 4.3:1 text, and a tint is not 3:1 against its row; the solid result tile is the look's
  motif already. A dark cell with a coloured ring and digit was the alternative (quieter, but the fill no longer says anything).
- 2026-11-11 · Heat scale in five fills: `--win`, `--win-2`, the well, `--loss-2`, `--loss` (two new tokens, each `--win` / `--loss`
  70% + `--blue-3`); best and worst rank carry a black 2px inner ring · every fill is 3.6:1 or more against the panel with black ink
  at 7.2:1 or more.
- 2026-11-11 · Bye exposure: 1 = the well with a yellow ring and digit, 2 = solid yellow, 3 or more = solid orange · Classic's three
  gold / orange tints were 1.9 to 2.2:1 as text on the ground.
- 2026-11-11 · Rank chips on these two tabs: rank 1 = solid yellow, last = solid `--loss`, black ink, no ring (Standings and the other
  tabs keep the ringed chip) · Classic's tile fitter leaves 1.75 to 2.75px above and below the digit; a 1px ring inside that is under
  rule 11's 2px (measured 1.0 to 1.3px in WebKitGTK).
- 2026-11-11 · Fitter-sized rank chips: the tile is drawn around the digit (`.ct::before`), not the digit centred in the tile · the
  fitter writes both side paddings inline with `!important` from a canvas that is glyph ink in one engine and the advance box in the
  other; CSS cannot override them and rule 10 forbids rewriting the fitter.
- 2026-11-11 · Bar tracks are black, not `--blue-3` · a track is read as a scale: black is 2.0 to 2.6:1 against the rows, `--blue-3`
  1.3 to 1.6:1.
- 2026-11-11 · Team Hub stands on a `--blue-2` plate (the Players recipe); its cards are `--blue`, the odds boxes and the Trends chart
  cards are `--blue-3` wells · on a well the palette's orange is 4.72:1 as a line and as text (2.90:1 on `--blue`), so the three
  series colours stay palette colours.
- 2026-11-11 · Team Hub hero: the seed tile is the Standings rank tile (rule 6), not Classic's numeral art.
- 2026-11-11 · Corners 4px on cards and wells, 2px on tiles (Classic 5 to 12px).

## Decisions (2026-11-12, pass 5: Standings on desktop, Glossary, ODL badge and favicon)

- 2026-11-12 · Standings on desktop themed (section "Pass 5") · the last layout that only had the token overrides.
- 2026-11-12 · Desktop Standings rank chips (table cells and stat lines): rank 1 = solid yellow, last = solid `--loss`, black ink, no
  ring; the tile is drawn round the digit, 1px wider on each side and 1.5px taller above and below than Classic's fitted chip · the
  recipe of pass 4; Classic's fitter leaves 1.75px above and below the digit and 2.25px beside "10" in a 10 to 11px chip, and a 1px
  ring inside that is under rule 11. **The phone layouts keep the ringed chip of 2026-11-09** (not in this pass's scope; see cleanup).
- 2026-11-12 · Table streak tile = the cards' solid result tile (black ink, 1px hard shadow) · Classic's 16% tint carried the loss
  ink at 3.68:1.
- 2026-11-12 · Table head = a `--blue-3` strip; row dividers `--blue-3`; the 4px rule before the simulation columns stays the frame
  colour (black) · rule 1; black is 1.9 to 2.6:1 against the rows, the ground's purple (Classic's stated intent: "the page colour")
  would be 1.2 to 1.5:1.
- 2026-11-12 · #1 odds are `--yellow` (Classic's literal gold), as the bye column; playoffs odds stay white (Classic's choice).
- 2026-11-12 · Table, 1100 to 1239px: the last column keeps 9px to the panel's frame (Classic 3px); the 6px come out of TEAM · the
  Playoffs figures with their shadow stood 2px from the frame.
- 2026-11-12 · Standings Glossary: the 8px plate of the other tabs behind the switch and the text, at every width; its Hide / Show
  switch selects to the badge · the label was 3.2:1 and the text 2.0 to 4.3:1 on the orange end of the ground; the switch was the one
  segment left with Classic's white selected state.
- 2026-11-12 · ODL badge and favicon drawn in the wordmark's letterforms (replaced the same day by TL: section "TL badge and favicon"); the favicon is one more
  checked patch of `theme_build.py` (patch 9) · Nicklaus's request.
- 2026-11-12 · The audits live in `retro/qa/` (README there) · they were outside the repo.

## Decisions (2026-11-12, cleanup job 1: Nicklaus's parked requests 33 to 37, TL favicon)

- 2026-11-12 · Empty rank dots (`.seg10 i:not(.on)`, Standings on phones and desktop) are dark sockets: `--blue-3` core, black ring (was
  a `--peri` ring) · Nicklaus: the empty dots were too prominent, the filled part must dominate. The brightest part of an empty dot was
  its ring, 3.21:1 against the lighter row and 4.15:1 against the darker one, close to a filled `--peri-lt` dot (4.80 / 6.19:1). Now no
  part of an empty dot is lighter than its row (ring 2.57 / 2.00:1, core 1.63 / 1.26:1, both darker), filled cores are 4.73 to 8.36:1
  lighter. Reading taken of rule 3: the dots repeat the rank chip's digit beside them, so an empty step is not a sole cue and needs no
  3:1. The same track logic as pass 4's black bar tracks. A solid `--blue-3` dot without the ring was the quieter alternative (1.26:1
  on the darker row: close to invisible).
- 2026-11-12 · Bench band (`.lbh` on Matchups and in the Playoffs lineups): 18px of panel above it (was 0), a `--blue-3` head strip (was
  the page colour `--pg`, purple) closed by a 2px black line above and below, label `--yellow` (was `--peri-lt`), inner rule `--blue`.
  Strip height 33.5px and every player row unchanged · Nicklaus: Bench was attached to the last starter (in Slate view: to the last
  slate) and read as one section with it. Purple inside a panel reads as the ground showing through (pass 3's reason for the `--blue-3`
  head strips); 18px is Classic's own `.lbh` margin, which Classic's later `margin` shorthand resets to 0.
- 2026-11-12 · Slate header (`.slg b`, day and time) stands in a framed tile: the slate day tile's recipe (`.stc`: `--blue-3` well, 1px
  ring in the slate's state colour, 1px hard shadow, 2px corner), 22px tall · Nicklaus: visibility. The tile hangs 2.5px above and below
  Classic's 17px line, so the header row keeps its 24px and nothing below moves; the starters count moves right by the two paddings.
- 2026-11-12 · Slate view surfaces (request 37): no change, already met since Game Day · the request came from the Playoffs lineups, which
  stood on the ground until Game Day gave `.pox` its plate; measured `--blue-2` behind every slate header and total line on both tabs.
- 2026-11-12 · vs / @ (request 33): the tiles are removed; the glyph takes its tile's colour, "vs" `--win` and "@" `--peri-lt`, 15px
  (Classic 11.5px), T1 shadow, in Classic's unchanged 20 x 17px slot (Nicklaus's pick of two mocks; option B was 19px with "@" in
  `--peri` and the T2 outline) · Nicklaus: the "@" tile had a black cap that "vs" did not. Cause: Classic's Standings row rule `.r`
  also matches the road tile's class `r` and gives it a 1px top border (Known issues, 38); the copy's solid tile made it visible.
  `--peri` as text is 3.21:1 on the lighter row, `--peri-lt` 4.80 / 6.19:1, `--win` 6.48 / 8.36:1. "@" shares `--peri-lt` with the
  row's dim labels (PROJ, BYE): it is told apart by its place, weight and size, and from "vs" by colour. **The HOME / ROAD word tags
  (`.hrt`, comparison card) and the card's home / road tags are unchanged: solid `--win` / `--peri` tiles with black ink.**
- 2026-11-12 · Favicon = TL (section "TL badge and favicon"): hand-hinted 16px drawing, stepped 32px and 180px; PNG links only · ODL
  was unreadable at 16px. Nicklaus's decision.
- 2026-11-12 · Loop badge = TL alone, the favicon's composition on the unchanged plate (Nicklaus's pick of two mocks; option 1 kept
  the DYNASTY line under a smaller TL) · one mark everywhere; DYNASTY's counters were 1.7px at 402 wide.
- 2026-11-12 · Phone Standings rank chips go to the solid desktop style (Nicklaus) · cleanup job 2, not touched here.
- 2026-11-12 · The Team Hub hero seed tile stays the blue CSS-drawn tile and is the retro rank-tile standard (Nicklaus).

## Decisions (2026-11-12, cleanup job 2: one rank-chip style on Standings, phone streak tile)

- 2026-11-12 · **Rank chips are to match everywhere (Nicklaus: "match the chips everywhere ... continuity is important").** The solid
  recipe is the single rank-chip style: rank 1 = solid `--yellow`, last = solid `--loss`, black ink, no ring; other ranks keep their
  digit colour on the 45% black tile. Done on Standings in this job, every layout; the other tabs' ringed chips follow in the next job.
- 2026-11-12 · Phone Standings (below 1100px): the fitter-sized stat-line chips use the drawn tile of desktop (`--ce:1px`, `--cv:1.5px`)
  · with `--cv:1px` Chromium read 1.76 to 1.94px above or below on 2 to 7 chips a state at all four phone widths (rule 11: 2px).
- 2026-11-12 · Phone streak tile: drawn round the glyph ink, at Classic's height (`--cv:0`; desktop keeps .5px) · the ink already has
  2.46px or more above and below, so rule 5 is kept; with .5px the tile stood 0.78px under the Median record at 402P and 440P.
- 2026-11-12 · Chips Classic's fitter does not size take the same two fills on their own box, every layout: the Nerd view's
  dropped-points chips (never fitter-sized: they stand under their figure), the week strip's chips (a tapped row), the desktop table's
  Proj finish tile, and any chip between a redraw and the fitter's next run · with the ring the dropped-points chips stood 1.18px
  (above) and 2.35px (beside) from it in Chromium; a ring flashing after H2H / Median would have shown the old style.
- 2026-11-12 · Season chart (SVG) chips: rank 1 and last solid with black digits, ranks 2-3 lose the green ring and keep the green
  digit; boxes unchanged (19 x 13 units); every chip digit of the chart is T0 (no shadow, rule 2) and ink-centred (`--ix`).
- 2026-11-12 · The three copies of the drawn-tile recipe are one rule set (theme.css PART 8) · proved neutral: computed geometry and
  paint of every drawn tile on Stats, Team Hub and desktop Standings identical before and after in both engines.
- 2026-11-12 · Kept as shipped, no code change (Nicklaus): empty rank dots keep the black ring; the HOME / ROAD word tags stay solid
  tiles; the favicon links stay PNG-only (no svg link).

## Mechanism ("always-current clone")

- `python3 retro/theme_build.py`: workflow step "Retro tracker theme", directly after "Retro edition",
  `continue-on-error: true`, every mode. `retro/**` is not in the workflow's push paths.
- **Build order:** `retro/build.py` replaces the whole `site/retro/` folder on every run (and removes it when it
  fails), so the theme step must come after it. Loop build fails: `site/retro/` is gone, then this step creates
  `site/retro/tracker/` again, so the tracker is published without the loop. Theme build fails: only
  `site/retro/tracker/` is removed; the loop page and Classic are untouched.
- Reads (never writes): `site/index.html`, `site/p/*`, `site/build.json`, `retro/theme.css`, `retro/theme.js`,
  `retro/wordmark.svg`, `retro/favicon.html`, `retro/fonts/`. Writes `site/retro/tracker/` only: `index.html`, `p/` (byte-for-byte copies of the chunks),
  `fonts/`, `build.json` (copy). Atomic: built in a temp folder beside the target, then renamed. Any missing input or
  marker: message on stderr, exit 1, and `site/retro/tracker/` does not exist.
- This relaxes hard rule 2 above for this one script: `theme_build.py` reads `site/` (read-only). It edits nothing
  under `pipeline/` and nothing of Classic's.
- **The 9 patches** (the only differences from Classic's `index.html`; each is checked and the build fails if one does
  not apply): (1) `class="retro"` on `<html>`; (2) Classic's Google Fonts link replaced by the self-hosted Martian
  Mono face (`<head>`); (3) the reveal script's four `document.fonts.load()` calls ask for Martian Mono; (4) one
  `noindex` robots meta (Classic already has it); (5) past-season buttons point at Classic's pages (`../../2025/`);
  (6) title gets " · Retro"; (8) the header wordmark: `The <img class="lgs">` (Classic's script art) is replaced by visually hidden text "The League"
  (`.wm-tx`, the h1's accessible name) + the inline `retro/wordmark.svg` (`aria-hidden`), see "Wordmark"; (7) `<style id="retro-theme">` + `<script id="retro-theme-js">` as the last things in
  `<body>`, after every `<style>` of the page including the ones `lazy.py` moves out of the chunks (the build checks
  that the theme is the last `<style>` and that no chunk carries one); (9) the favicon (2026-11-12): the three self-contained
  `<link>` tags of `retro/favicon.html` after the charset meta; any icon link of Classic's is dropped first and the build checks
  that exactly three remain. After any change to Classic's page shell
  (head, reveal script, year buttons, style order) run the script and check that all nine still apply.
- Verified in the copy: chunks load from its own `p/`, `#hash` deep links and the hash kept on tab change, the refresh
  pill polls its own `build.json`, live scores poll Sleeper as in Classic. Nothing is requested from Classic or from
  Google.

## Font

- Martian Mono, self-hosted: `retro/fonts/martian-mono-latin(-ext)-wdth-normal.woff2` (unmodified
  `@fontsource-variable/martian-mono` 5.3.0, SIL OFL 1.1, licence in `retro/fonts/OFL.txt`).
- `@font-face` is declared with **`font-stretch:75%`** (one width, so the family itself is the condensed face) and
  **`size-adjust:87.5%`** (Martian Mono capitals are .80em, Barlow Condensed / IBM Plex Sans .70em). Both act on the
  face, so layout AND the canvas measurements in Classic's fitters see the same glyphs (checked in Chromium and
  WebKitGTK: canvas advance = DOM advance = .525em, cap .70em). Every Classic font size keeps its cap height, and the
  fitters produce Classic's sizes without being touched.
- The theme points `--display` and `--body` at it. `letter-spacing:-.05em` on running text, `0` in tiles and chips;
  `word-spacing:-.22em`.
- Minimum text: 11 CSS px nominal, as Classic. Because of `size-adjust`, 11px Martian Mono has the cap height of
  11px Barlow Condensed (7.7px); its x-height is larger (.53em against .46em). Digits inside tiles beside figures
  follow the tile rule, as in DESIGN.md §2.16.
- Glyph ink used by the theme (rank-tile offsets in theme.css, table `G` in theme.js) is read from the font files with
  fontTools (`varLib.instancer` at wdth 75, wght 700 / 800), never from a canvas. Re-read it if the font files change.

## Tokens

Palette = the loop's (`--purple --orange --blue --yellow --peri --white --black --badge-hi --badge-lo --glow --card`).
New for the tracker (each a mix of two palette colours):

| Token | Value | Job |
|---|---|---|
| `--blue-2` | `#2a3e6a` (`--blue` 80% + black) | darker row / panel |
| `--blue-3` | `#202f4f` (`--blue` 60% + black) | row divider, toggle tracks, empty dots |
| `--peri-lt` | `#b9c4fb` (`--peri` 60% + white) | dim text on blue rows (4.80:1; `--peri` is 3.21:1 there) |
| `--loss-lt` | `#ffb1b1` (loop `--loss` 70% + white) | loss text and tiles (4.73:1; `--loss` is 3.72:1) |
| `--badge` | `linear-gradient(#4d5ff5,#2040fa)` (steps 5 and 7 of `--card`) | selected controls, rank tiles (white text ≥ 4.92:1) |
| `--grain` | generated PNG, black specks alpha 0-16% | printed on the ground and the team rows |

| `--pos-qb` `--pos-rb` `--pos-wr` `--pos-te` `--pos-k` `--pos-def` | `#fbb2c9` `#3ddcc1` `#76cff6` `#fcb674` `#c491ff` `#c98a72` | position palette (Game Day): tile and pill fills with black ink; QB / RB / WR / TE also as label text on the blue rows |
| `--seg-on` | the badge gradient inset 2px on white, as one `background` value | stands in for Classic's `--chalk` inside segmented controls and menus (Game Day, "Segments") |
| `--win-2` `--loss-2` | `#61c188` (`--win` 70% + `--blue-3`), `#bc8a94` (`--loss` 70% + `--blue-3`) | second step of the heat scale (pass 4): 4.76 / 3.61:1 on the panel, black ink 9.49 / 7.20:1 |

Classic's tokens are re-pointed in `html.retro:root` (38 overrides): `--pg` purple, `--frame` black, `--deck`
`--blue-2`, `--row-lt` `--blue`, `--row-divider` / `--line` `--blue-3`, `--chalk` white, `--label` yellow,
`--text-dim` / `--steel` `--peri-lt`, `--ink` black, `--win` `#7dffa0`, `--loss` `--loss-lt`, `--tier-bye` yellow,
`--tier-po` `--peri-lt`, `--faab` white / `--faab-ink` black, `--sh-hard` `2px 2px 0 0 #000`, `--r-panel` 2px, chart
tokens. Position labels on the cards are Classic's position colours lightened to 4.6:1 on `--blue`.

## Rules

1. **Rows:** lighter row `--blue` > darker row `--blue-2` > divider `--blue-3` > frame black; alternating shades AND
   a divider. Measured with the grain's mean: 1.27:1, 1.17:1, 1.58:1.
2. **Type treatment by role, and the dark-ink rule.** T2 (black 2px outline under the fill + 2px hard shadow): header
   title, weeks-left figure, team names, records, group buttons, rank-tile digits (18px and up). T1 (1px hard shadow,
   no outline): every other light text. T0 (nothing): dark text on a light tile, and chip digits and letters (rank
   chips, FK / FL flex chips). The outline is not used under 18px: at 11px neighbouring letters fuse.
   **Dark-ink rule (2026-11-10): the black hard shadow and the black outline are only ever applied to LIGHT ink on a
   darker surface. Dark ink (any text whose colour is darker than its own surface) gets no text-shadow and no
   text-stroke, on every tab, themed or not.** How theme.css holds it:
   - *Layer 1, automatic.* T1 is not a fixed black: its colour is computed from the ink. `--shk` =
     `oklch(from currentColor 0 0 0 / clamp(0,(l - .4)*20,1))`, black whose alpha is 0 while the element's own text
     colour has OKLCH lightness <= .40 and 1 from .45. `text-shadow` inherits as the formula, so each element resolves
     it against its own colour (checked in Chromium 153 and WebKitGTK 2.52). Classic's dark inks (`#0f1218`,
     `#0b0e14`, black, the NFL team inks: all below L .30) get no shadow wherever Classic uses them, including tabs
     that are not themed yet and components added later; light inks on the blue and purple surfaces (L >= .60) keep
     it. Engines without relative colours (before Safari 18 / Chrome 131) skip the declaration and show no T1 shadow.
   - *Layer 2, by name.* Light ink on a LIGHT surface cannot be seen by the formula: those surfaces switch the shadow
     off themselves (block "dark-ink rule, layer 2" in theme.css; none today: the dropdown menus `.ddm` were the one case
     until they became blue panels, 2026-11-11).
   - The outline (T2) is never a default: it is set on the named roles above only, all of which the theme colours
     white or yellow. Do not add a fixed `text-shadow: ... var(--black)` to a selector whose ink Classic decides.
   - Check: `darkink` audit under "Checks before shipping" = 0.
3. **Contrast, computed against the plain (lightest) surface:** ≥ 4.5:1 small text, ≥ 3:1 large text and graphics.
   Text that sits straight on the ground must stay in the purple zone (first 1100px); the orange end of the
   gradient is 2.82:1 against white and may only show behind panels.
4. **Selected = the badge** (`--badge` fill, white 2px inner ring, white text); unselected = flat blue with yellow
   (level 1) or `--peri-lt` (level 2, toggles) text. Yellow = labels and the bye tier. Never a coloured bar on a
   card edge.
5. **Tiles:** as Classic (never taller than the figure's cap height, digits never touch the frame, ink centred,
   stacked tiles one width and one left edge). **Rank chips carry no ring (2026-11-12): rank 1 is a solid `--yellow` tile, last a solid
   `--loss` tile, both with black ink; done on Standings, the other tabs' gold and worst chips still carry Classic's 1px ring until the next job.** The
   streak tile is a solid result colour with black figures; empty rank dots are dark sockets (`--blue-3` core, the black ring
   every filled dot carries; 2026-11-12, was a periwinkle ring).
6. **Rank tiles:** CSS-drawn (42 x 44px on every row, one left edge, `--badge`, white 2px border, 2px hard shadow,
   Martian Mono 800 25px on a cap-trimmed line). Bye = yellow digit, playoff = white digit, chasing = flat `--blue-3`
   with a periwinkle border and `--peri-lt` digit.
7. **Ink centring of the FAAB tile and the rank tile** (theme.js, phones): judged by glyph ink from the font's
   outlines. Across: the whole ink box ("$" to the last digit; a digit alone). Down: the whole ink box too; for
   "$NN" that is also the digits' cap band, because Martian Mono's "$" overshoots it by the same .1em above and
   below. Each tile's text origin and baseline are put on the whole device pixel that leaves the most equal gaps
   against the tile's painted edges: at most 1 device pixel of difference each way by construction. Measured in
   WebKitGTK at 3x (360P / 402P / 440P layouts): FAAB 0.22px top/bottom, ≤ 0.33px left/right; rank tiles ≤ 0.27px
   and ≤ 0.29px. The shadow and the outline are not part of the ink.
8. **No overlay layers, no `filter`.** WebKit does not blend a fixed `mix-blend-mode` layer over this page (it falls
   back to plain alpha and greys everything: white measured 200-230 in WebKitGTK). Grain is a background layer of
   the ground and the rows (darkens only, static).
9. Nothing clipped, wrapped or ellipsised that Classic does not already wrap; no sideways scroll; elements do not
   move between Dumb / Nerd or H2H / Median beyond what the data changes. Never highlight Bill's Block Party.
10. **CSS first.** `retro/theme.js` holds only what CSS cannot do, each item with its reason: (1) re-fit after
    H2H / Median (a Classic bug, DESIGN.md §8; remove when Classic re-fits by itself); (2) rule 7 (CSS cannot see a
    tile's text or where it meets the device-pixel grid). It wraps Classic's `tnFit` (runs after it and once more two
    frames later) and never rewrites a Classic fitter; (3) rule 11 for the lineup score cells (CSS cannot see which
    glyphs a figure starts and ends with, or how many it has): sets `--fx` per cell and `fs5` per lineup from the
    text alone, no layout reads, at load and for nodes added later (`MutationObserver`); (4) rule 11 for chips and
    segments (2026-11-11): per element of a selector list, `--ix` = right bearing of the last glyph minus left bearing of
    the first (table of Martian Mono's bearings for ASCII at four weights, from the font files), which theme.css uses as a
    `text-indent`; text only, no layout reads; the same item copies the "Week rank" digit into `data-tx` (CSS cannot copy a
    text node into `content`). In an engine that rounds glyph advances to whole pixels (WebKitGTK; found by one probe) it
    also reads each element's font size (style, not layout) and adds the rounding as `--iw`; (5) Compare > Schedule (2026-11-11): an
    empty comment node in front of each right-hand seed chip and the fitter's inline styles removed, so Classic's tile fitter
    leaves the chip alone (Classic bug, see "Pass 2"; no text or layout reads; remove when Classic's `ref()` skips these chips); (6) Paper Trail > Picks
    (2026-11-11): after every run of Classic's fitter (a change of `.ptv-k`'s style attribute) the tile width `--ptcw`, the column
    widths `--ptca` / `--ptva` and the NFL slot's edge `--nx` are set again from the bearing table (CSS cannot replace a custom
    property written inline on the same element; one layout read for the tiles' left edges; see "Pass 3"). Pass 4 added no item: item 4's
    list gained the chips of Stats and Team Hub, and for rank chips it also writes the character count as `--nc` (text only); where it finds that the engine rounds glyph
    advances it sets `--rnd:1` on `<html>` once (theme.css PART 8 uses it inside `round()`). Pass 5 added no item: item 4's list gained
    four entries (Standings' fitter-sized rank chips and the cards' streak tile with `--nc`, the table's streak and Proj finish tiles), and
    item 1 gained a late check on desktop: 350ms, 900ms and 2s after an H2H / Median press, a streak tile or a table rank chip that is
    still unsized gets Classic's own `window.rrFit()` / `window.tileFit()` (selector matches, no layout read; see "Pass 5"). Cleanup job 1
    (2026-11-12) added no item: item 4's list gained one entry (`.slg b`, the slate header tile). Cleanup job 2 (2026-11-12) added no
    item: item 4's list gained one entry (the season chart's SVG chip digits, `--ix` for a `translate`; text only).
11. **Text never touches a frame (2026-11-10).** Inside any framed cell or tile, the visible ink INCLUDING its shadow
    or outline keeps at least 3 CSS px from the inner edge of the frame on the left and right, the left and right
    gaps equal within 0.5px (ink-centred), and at least 2px top and bottom, at every width. Measured from
    screenshots (text switched off and on, the difference is the ink), not from layout boxes.
    Met on Matchups and Playoffs by every framed element (2026-11-11; how, per component, under "Game Day"). The general
    recipe: (a) chips are T0 (no shadow, tracking 0) so nothing but glyph ink is inside the frame; (b) across, `--ix`
    (rule 10, item 4) as a `text-indent`: a centred line moves by half of it, a shrink-to-fit box grows by it on one side,
    both equalise the two gaps; text that keeps the running tracking and the 1px shadow subtracts `.05em` and `1px`;
    (c) down, a cap-trimmed line (`text-box: trim-both cap alphabetic`) and a padding worked out from the glyphs' own
    heights; where the tile cannot give 2px (the "@" in a ringed 17px tile) the ring goes, not the type size.
    Multi-line cells (score cells, slate tiles, position tiles) are centred line by line.
12. **No synthetic italic (2026-11-11).** Martian Mono has no italic face; where Classic sets Barlow Condensed italic
    (seed chips of the Playoffs card) the theme sets `font-style:normal`.

## Wordmark (header title, 2026-11-10)

Option C, "stepped 90s title" (Nicklaus's pick of three): `retro/wordmark.svg`, put into the copy by patch 8. Classic keeps
its script art; past-season pages are Classic's.

- **Letterforms:** the theme's own drawn alphabet (T H E L A G U only), not Martian Mono and not a font: squared forms with
  rounded corners, flat-topped A, short-spur G, built from rectangles and arcs so every counter stays open under the
  outline and the steps (Martian Mono's A has a pinhole counter and the face is not condensed). No bitmap, no opaque black
  fill areas. Pair gaps, cap = 100: L-E 8, E-A 10, flat-sided pairs 12, T-H 6.
- **Lockup:** OFFICIAL stays the label above (`.eyebrow`, unchanged). THE (yellow, half the cap height) and LEAGUE (white)
  share one baseline. Units inside the svg: 1 = 1 CSS px at the 360P layout (viewBox 272.1 x 81.2).
- **Layers, bottom to top:** LEAGUE step 2 `--peri` at (5, 5); LEAGUE step 1 `--orange` at (2.5, 2.5); THE step `--orange`
  at (2, 2); black outline (fill + 2.5 stroke: 1.25 outside the letter, the same weight on the step copies); fills
  `--white` (LEAGUE) and `--yellow` (THE). Each layer is a copy of one path (`<use>`), so no text-stroke or paint-order
  is involved and both engines draw the same thing. Tokens: `--white --yellow --orange --peri --black`, nothing new.
  Contrast on `--purple`: white 13.0:1, yellow 12.25:1, orange 4.62:1, periwinkle 5.12:1.
- **Box rule:** the svg keeps Classic's class `.lgs`, so Classic's own rules size it: 1.4em / 1.65em (from 430px) / 1.85em
  (from 1100px) of the 58px h1 = 81.2 / 95.7 / 107.3px (1.38em of 50px = 69px at 380px and under); the width follows the
  viewBox. The header's rows therefore stay exactly where Classic's art put them. If Classic changes those heights or
  breakpoints, re-check the wordmark (and `--wmy` below). LEAGUE cap height 58 / 68.4 / 76.6px, lockup width
  272.1 / 320.7 / 359.6px. The svg is never wider than 278px at the 81.2px row, which keeps it inside the title column
  down to a plain 430px viewport.
- **Position:** outermost ink (the outline) on the content left edge; the white fill starts 1.25px in. Down: `--wmy` (a
  translate inside the svg, in svg units: 5.55 / 4.58 from 430px / 3.97 from 1100px) puts the ink's centre halfway
  between OFFICIAL's baseline and the cap top of the chart's values, 5.4px under the row's centre. Ink including the
  steps stays inside the row: 2.0px spare at the bottom at 360P, 3.3 to 3.5px at 402P / 440P, 4.9px on desktop. If a
  change leaves under 1px, move `--wmy`, do not shrink the lockup.
- **Accessible name:** the h1 holds the text "The League" in `.wm-tx` (visually hidden); the svg is `aria-hidden`.
- **Smallest counter opening** (ground visible between outline / steps, from screenshots): 3.9px at 360P (the small H of
  THE; its step is 2px, not 2.5px, for that reason), 4.7px at 402P / 440P, 5.0px on desktop.
- **Small sizes:** fine at half size; at about a third (row 32px) the small THE goes muddy (its counters fall to about
  1.3px). For compact uses (favicon, loop header, share image) use a stacked or THE-less variant, not this lockup scaled.
- **`retro/wordmark_gen.py` is a development tool** (not run by the build or the workflow; the build reads the committed
  svg): `python3 retro/wordmark_gen.py C > retro/wordmark.svg`. It holds the letter construction and all three options.
- **Options A and B are kept**, as patches against e4f7966, outside the repo (`/home/claude/retro-build/shots-theme/wordmark/`
  `wordmark-A.patch`, `wordmark-B.patch`, with comparison sheets), and as `wordmark_gen.py A` / `B` for the svg alone
  (their CSS blocks are in the patches only). A = broadcast title (one line, yellow, black outline and hard shadow).
  B = badge (plate in `--badge-hi` to `--badge-lo`, white 2px border, periwinkle hairline, hard shadow): suits a compact
  mark such as a favicon or the loop page's corner badge.

## Game Day: Matchups and Playoffs (2026-11-11)

theme.css PART 5, theme.js item 4. Phones and desktop. Everything is scoped to `html.retro`; Classic and the chunks are
untouched.

**Surfaces.** Matchups keeps Classic's panel `.mux` (`--deck` = `--blue-2`, black frame, hard shadow) and gains the
board's inner glow. Playoffs has no panel in Classic (it sits on the page): here `.pox` is a `--blue-2` plate drawn with
spread shadows (12px of plate, 2px black frame, 2px hard shadow, the glow), so no box moves and no text sits on the
ground. The Glossary switch and its text (`.glw`, `.key`), which stand on the orange end of the ground, get the same
kind of plate (8px) on these two tabs. Cards on a panel are `--blue` (lighter, raised): matchup cards `.g4`, the
comparison card `.mcard`, bracket games `.pbm` / `.pbyt`. Wells are `--blue-3`: toggle tracks, the team switch, the
dropdown button, the points band `.ltot.lsb` (periwinkle 1px ring), slate day tiles `.stc`, the "vs" badge.
The bench strip is a `--blue-3` head strip since 2026-11-12 (below, "Bench band" and "Slate header"); Classic's other `--pg` strips stay purple.

**Literal Classic colours overridden** (everything else arrives through the tokens):

| Classic | Where | Here |
|---|---|---|
| `var(--ink)` used as a FILL (black after the token override) | `.g4`, `.mcard`, `.msw`, `.dd summary`, `.g4vs`, `.ltot.lsb`, `.stc` | `--blue` / `--blue-3` as above |
| `#1c212b`, border `#3a4254`, blurred shadow | dropdown menu `.ddm` | `--blue-2`, periwinkle 1px ring, 4px hard shadow; rows yellow, their small labels white; selected row = the badge |
| `color-mix(--pc 82%, #0b0e14)`, ink `#0f1218`, edge `rgba(0,0,0,.25)` | position tiles `.pq` | `--pos-*` plain, black ink, 1px black edge line |
| `#8f98ab` / `#6b7385` / `#7d8597` | projected figures `.cv:not(.act)` | `--peri-lt` (5.20:1 on the projection cell) |
| `rgba(63,214,155,.16)` + `.38` lines, `#7fdcb6` | FINAL cell, beat projection | `rgba(125,255,160,.16)`, `--win` lines and delta (5.61:1), white figure and label |
| `rgba(255,93,115,.15)` + `.38` lines, `#ff8a9a` | FINAL cell, fell short | `rgba(255,143,143,.14)`, `--loss` lines and delta (4.94:1) |
| `rgba(232,193,90,.14)` + `.45` lines, `#efd38a` | LIVE cell | `rgba(255,255,111,.16)`, `--yellow` lines and label |
| `rgba(63,214,155,.14)` / `#7fdcb6` / ring | home tiles `.gha.ht.h`, `.hrt-h`, `.hab-h` | solid `--win`, black ink (16.7:1), no ring |
| `rgba(150,160,255,.13)` / `#b9c1ff` / ring | road tiles `.gha.ht.r`, `.hrt-r`, `.hab-r` | solid `--peri`, black ink (8.3:1), no ring |
| `rgba(244,196,81,.24)` / `#f4c451`; `rgba(255,93,115,.22)` / `#ff8a98` | injury tags Q; D / O / IR | solid `--yellow` / `--loss`, black ink |
| `rgba(255,93,115,.22)` / `#ff8a98`; `rgba(238,240,244,.10)` / `#c3cad8` | FL / FK chips | dark chip (45% black), `--loss` / `--peri-lt` ink and 1px ring |
| `#e8c15a`, `rgba(232,193,90,.14)`, `rgba(63,214,155,.12)`, `rgba(255,93,115,.12)`, `#ff8a9a` | card seed chips `.gsd` | the Standings rank chip: 45% black, `--yellow` (1px ring) / `--win` / `--loss` / `--peri-lt` digit |
| `rgba(63,214,155,.12)`, `rgba(255,93,115,.12)` | card streak tiles `.stk` | solid `--win` / `--loss`, black figures (the Standings streak tile) |
| `#ff8a9a` | losing win %, bar | `--loss`; bar track `--blue-3` with a black frame |
| `--win-bg` / `--loss-bg` tints | result tiles `.mres`, WON / LOST `.hres` | solid `--win` / `--loss`, black ink |
| `#cf9a2c` | HI tag `.mt.hi` | `--yellow`, black ink |
| `rgba(127,166,255,.45 / .6)`, `#3a4254` | "N on bye" pill, upcoming-week marker | `--peri` ring, `--peri-lt` text; `--blue-3` ring for later weeks |
| `#5fd3a5` `#e8c15a` `#9aa3b5` `#7fa6ff`, their tints, `#a9c3ff` `#efd38a` | slate view: heading colour `--sc`, state chips `.ss`, day tiles | `--win` (final), `--yellow` (live), `--white` (upcoming), `--peri-lt` (bye); chips 45% black |
| `#5fd3a5` / `#f08a98` | slate deltas `.dlt` | `--win` / `--loss` |
| `#f7739c` `#3ddcc1` `#5ec6f4` `#c491ff` `#c98a72` + tints | Detailed stats category chips `.dxl>u` | `--pos-*` ink on a 45% black chip |
| `#6fc9a4` `#d4af6a` `#e0838f` | schedule: points allowed `.pag` | `--win` / `--yellow` / `--loss` |
| `rgba(238,240,244,.11)`, `rgba(63,214,155,.16)`, `rgba(255,93,115,.18)`, `#7fdcb6` `#ff9aa8` + rings | schedule rank chips `.psk2`, key chips | 45% black, `--peri-lt` / `--win` / `--loss` digit, no ring |
| `opacity:.28` on the other week's column | schedule `.psg.psy` | full strength (it was 1.9:1): the darker cell and `--peri-lt` figures tell it apart |
| `--line-strong` / `--chalk` overridden by Classic's body-wide frame colour | bracket connectors `.pbc` | `--peri`; the projected path `--white` (as its legend swatch) |
| (none: `--ca` / `--cb` are undefined on Playoffs in Classic) | builder keys A / B `.ddk` | `--peri` / `--orange` tiles, black ink |
| `rgba(127,166,255,.5)` | BN tag of the Optimal view | `--peri` ring, `--peri-lt` |

**Segments (rule 4).** Classic paints every selected segment, team-switch side and menu row with
`background:var(--chalk);color:var(--ink)` through one rule per radio id. Inside `.pseg`, `.msw` and `.ddm` the theme
re-points the two tokens (`--chalk: var(--seg-on); --ink: var(--white)`), so the selected state is the badge with its
white 2px ring on every tab that uses these components, with no list of ids. Selected matchup card: white 2px inner
ring (the six `input[id$="-N"]:checked ~ .mpk label[for$="-N"]` pairs); selected bracket game: Classic's own ring.

**Position tiles.** Fill `--pos-*`, black ink (opacity 1), no shadow, tracking 0, each line ink-centred, the stack centred in
the 33px beside the 1px edge line.

| Position | Fill | Black ink on it | As label text on `--blue` |
|---|---|---|---|
| QB | `#fbb2c9` | 12.31:1 | 4.78:1 |
| RB | `#3ddcc1` | 12.21:1 | 4.74:1 |
| WR | `#76cff6` | 12.03:1 | 4.67:1 |
| TE | `#fcb674` | 12.08:1 | 4.69:1 |
| K | `#c491ff` | 8.84:1 | 3.43:1 (not used as text on blue; on a 45% black chip 6.0:1 or more) |
| DEF | `#c98a72` | 7.36:1 | 2.86:1 (same) |

**Colors: Team.** Classic's team colours and inks. Classic's own fill (82% team colour + `#0b0e14`) leaves DEN 3.43:1,
LAC 3.93:1, JAX 4.34:1, KC 4.41:1. Here: light-ink teams 75% team colour + black (worst LAC 4.65:1, NE 5.08:1); the
four dark-ink teams (CIN, DEN, NO, PIT) the plain colour (worst DEN 4.75:1). The shadow follows the ink (rule 2,
layer 1). Tiles of dark teams are close to the row (NYJ 1.03:1 against `--blue-2`); the black edge line and the ink
carry them, as in Classic. Also applied to Rosters' team mode.

**NFL logos.** Checked against `--blue-2`: Classic's art already carries light keylines (it was drawn for a dark page).
For 30 of 32 logos at least 86% of the outline pixels stand off the row by 1.5:1 or more; LAR's outline is navy but 73%
of its area (the horn) stands off, PIT's ring 64% with 93% of the area. No keyline, disc or filter added.

**Score cells (rule 11).** 44px columns (Classic 38px), figure 18px (Classic 18.375px), a lineup with a five-character
figure 14px (`.fs5`), delta 11px (Classic 10px), label 11px.

| | A: 38px cell (2026-11-10) | B: 44px cell (shipped) |
|---|---|---|
| figure / five-character lineup / delta | 14.5px / 11.5px / 10px | 18px / 14px / 11px |
| "88.8": ink + shadow, each side | 28.7px, 3.6px | 35.4px, 3.3px |
| names at 440P, 402P, 1100 to 1920 | as Classic | as Classic (no size, text or line changes) |
| names at 360P (Classic 13.75 to 15.75px) | 15.5 to 15.75px | 13.75 to 15.75px: most lineups 15.25px, one of nine checked 13.75px |
| new abbreviations / second lines | 0 | 0 |

Names and logos keep their outer edges; only the two cells and the name columns' inner edges move (6px each).
Other tabs' `.cr.lu` rows keep Classic's 38px cell with the 14.5 / 11.5px figures.

**Chips and tiles (rule 11).** vs / @: no tile since 2026-11-12 (below, "vs / @ glyphs"); until then solid 17px tiles. Injury tags: one baseline for Q / O / D / IR placed for the tail of
"Q". FK / FL: 11px, 3.65px / 4.4px paddings. "N on bye": centred on the ink of "b" and "y", pill height as Classic.
HOME / ROAD in the card: Classic's 0.58px side difference taken out through `--ic`. Schedule chips and tiles (sized in
`cqw`) and the schedule's three week columns are rounded to whole pixels. "Week rank N": Classic's chip keeps its box (the fitter's inline `!important`
styles cannot be overridden) but loses fill and ring; its digit is made transparent and the rank is drawn by `::after`
from `data-tx` at the label's 11.5px, on the label's cap band (Classic's fitter leaves the chip 4.43px above it, in
Classic too: the label is a flex item, where a baseline marker is not on the baseline).

**vs / @ glyphs (2026-11-12).** theme.css PART 10. `.cnm .gp .gha.ht.h` / `.r` on Matchups and Playoffs (week lineups, bracket-game
lineups, the builder, the schedule grid: the only places the component occurs; `.hab` does not occur in the built pages): no fill, no
ring, `border:0`, `cursor:inherit`; "vs" `--win`, "@" `--peri-lt`; `text-shadow:1px 1px 0 var(--shk)` (T1); 15px outside the schedule
grid (the schedule keeps Classic's `cqw` size). The slot is Classic's 20 x 17px inline box (schedule: its whole-pixel `cqw` box), so no
box in the row moves. Ink including the shadow: "vs" 15.5 x 10.0px, "@" 8.0 to 8.5 x 14.5px. Centred on the slot by `--gv` (.127em
"vs", .108em "@") and `translate:0 -.9px`. Ink centre against the slot's centre, mean per glyph, side and state (Matchups Week 10 and
Week 9, Playoffs final; down is +): Chromium at 360P / 402P / 440P / 1440, "vs" -0.45 to -0.08px, "@" -0.20 to +0.23px (single rows
-0.95 to +0.62px: headless Chromium's whole-pixel text, Known issues 19); WebKitGTK at the 402P / 440P layouts "vs" +0.33px, "@"
+0.50px on every row and both sides, at 1440 "vs" 0.00px, "@" +0.50px (one device pixel at 2x). Across: within 0.3px in both.
Rule 11 does not apply (no frame). Not changed: the word tags HOME / ROAD (`.hrt`) and the card's home / road tags.

**Bench band (2026-11-12).** theme.css PART 10. `.pane-mu .lbh`, `.pane-po .lbh:not(.psbh)`: `margin-top:18px`, `--blue-3` fill,
`inset 0 2px 0` and `inset 0 -2px 0` black, label `--yellow` (12.52:1), small text `--peri-lt` (7.81:1), inner rule `--blue`. Height
33.5px as Classic. Everything under the band is 18px lower than in Classic's page; nothing else moves.

**Slate header (2026-11-12).** theme.css PART 10, theme.js item 4 (`.slg b` in the list). The day and time are a tile: `--blue-3`,
`inset 0 0 0 1px` ring (`--peri` upcoming, `--win` final, `--yellow` live, `--blue-2` for the bye slate, as `.stc`), `--sh-1`, 2px
corner, 6px side padding, `height:22px` with `margin-block:-2.5px` (the row keeps 24px), a cap-trimmed line with 4.55px above the
capitals: capitals (11.9px) plus the 1px text shadow are centred between the ring lines. Text keeps its state colour, the running
tracking and the 1px shadow; across it uses the segments' `text-indent` formula. Text on the well: white 13.28:1, `--win` 10.55:1,
`--yellow` 12.52:1, `--peri-lt` 7.81:1. Engines without `text-box` get the fill, ring and side padding on Classic's 17px line.

**Comparison card names.** 17px at the 360P layout and in the desktop side column (Classic 21px Barlow Condensed):
"Nuts in the Face" wrapped to two lines there and holds one in Classic. 21px elsewhere.

**Desktop.** Three columns as Classic inside the one panel (cards, lineup, comparison + results); cards and comparison
card share one top edge, the lineup's heading sits on its own line below it as in Classic; the ground shows no orange
behind short columns because the panel spans them; nothing on these tabs stands on the ground.

**Not changed on purpose.** Row heights, the centre line, slot-group dividers, the bench strip, Classic's fitters, the
sticky points band (its compact state uses 10 / 10.5px labels, Classic's), sizes under 11px that are Classic's own
(units in stat lines 9 to 10px, Detailed stats labels 9 to 10px, card "Final" 10.5px).

## Pass 2: Leaderboards, Players, The Wire, Compare (2026-11-11)

theme.css PART 6, theme.js item 5 and five more entries in item 4's list. Phones and desktop. Scoped to the four panes
(`.lbx`, `.plx`, `.wrx`, `.cmx` and `.pane-*`); the one rule that is not scoped is the bye-week colour (`.by.past`, `.by.now`).

**Surfaces.** Leaderboards `.lbx` and Compare `.cmx` keep Classic's panel (`--blue-2`, black frame, hard shadow) and gain the inner
glow. Players `.plx` and The Wire `.wrx` have no panel in Classic: each is a `--blue-2` plate drawn with spread shadows (12px of
plate, 2px black frame, 2px hard shadow, the glow), so no box moves. The Glossary switch and text get the 8px plate on all four.
The Wire's table `.wrt` is a `--blue` panel on the plate: head strip `--blue-3`, rows `--blue` / `--blue-2` alternating over the
1px `--blue-3` divider (rule 1), counted over the rows the position filter leaves visible (`:nth-child(even of :not([hidden]))`).
Players rows and Compare's player rows are the lineup row of Game Day (`--blue-2`, black 1px frame), unchanged.

**Pills and controls.** `.lbc label` (Leaderboards stats, Compare sections, Players positions) and `.wpb` (The Wire filter):
`--blue-3`, 4px corner, `--peri-lt` label (7.81:1). Selected = the badge through `--chalk: var(--seg-on); --ink: var(--white)` on
`.lbc` (the Game Day segment mechanism; no list of radio ids). Position pills: label in `--pos-*` on `--blue-3` (QB 7.79, RB 7.72,
WR 7.61, TE 7.64, K 5.59, DEF 4.66:1); selected = the `--pos-*` fill with black ink (7.36 to 12.31:1). The Wire's ALL (yellow
label) and FLX (white) select to the badge. Search field `.wq`: `--blue-3`, 4px corner. Classic's hard shadow on the Players pill
strip (`.lbc.roc.plc`, an L-shaped black line here) is off. Segments (`.pseg`), dropdowns and menus arrive from Game Day.

**Literal Classic colours overridden** (everything else arrives through the tokens):

| Classic | Where | Here |
|---|---|---|
| `var(--ink)` used as a FILL | pills `.lbc label` | `--blue-3` |
| `#f7739c` `#3ddcc1` `#5ec6f4` `#fca95c` `#c491ff` `#c98a72` (rule per pill; inline `--pc` on The Wire) and their 82% mixes | Players pills, The Wire pills and position tiles `.wpt` | `--pos-*`; tile ink black (Classic `#0b0e14`), 1px black edge line as the lineup tiles |
| `#4b5262`; `--sky` | bye week past; this week | `--peri-lt` (6.19:1 on the row); white |
| Classic team colours with light inks (LAC 2.94:1, JAX 3.46:1) | Players, Colors: Team tiles | the Game Day recipe: 75% team colour + black, the four dark-ink teams plain |
| `--accent` (orange, 3.74:1) | The Wire sort arrow | `--yellow` |
| `--ca:#7fa6ff` / `--cb:#f59a52`, and the same two swapped by one rule with 45 id pairs | Compare keys A / B, chart lines and dots, legend | `--peri` / `--orange`; the swapped panels through `@container style(--ca:#f59a52)` (engines without style queries keep Classic's two literals on those panels) |
| `#626b7c` / `#9aa3b5`, `#262c38`, `#0f1218` | Compare weekly chart: axis text, grid lines, dot outline | `--peri-lt`, `--blue-3`, black |
| `#7d8597` | Compare player rows, the lower figure `.cv` | `--peri-lt`; the higher one white |
| `#c9a15a` | next meeting "Week N" | `--yellow` |
| `#ff5d73` | IR mark `.cir` | `--loss` |
| `rgba(127,166,255,.1)` + `--sky` ring and digit; `rgba(63,214,155,.15)` | acquired pick chip `.pk.via`; FAAB chip | `--blue-3`, `--peri` ring, `--peri-lt` digit; `rgba(125,255,160,.16)` |
| `color-mix(--pc 55%, transparent)` line, `--pc` text | Compare Players, position head `.cgh` | `--pc` line; the head is a `--pos-*` chip with black ink |
| NFL team colours (text chips, no logo in this pane: KC 3.27:1) | Compare team chips `.nfl` | 25% black over the team colour for light-ink teams, the four dark-ink teams plain |

**Chips (rule 11).** Compare's team chips, pick chips and position heads and The Wire's position tiles are T0 with tracking 0
(their inner `.ct` too: the body-wide tracking rule reaches it) and are ink-centred by `--ix` (theme.js item 4). "QB" chips in
Compare sit 1px higher and the chips between two figures are 17px tall (Classic 15px; row heights measured unchanged). Compare's
section pills are centred on ink + shadow: `--ix` + Classic's .05em tracking after the last letter - the 1px shadow.

**Classic bug found: Compare > Schedule > Week by week, right-hand seed chip** (in Classic too, every width). `ref()` in
new_tail.js finds no text before that chip and takes the cell before it, "Wk 10", as its figure (the label holds a digit); the
tile fitter then sizes the chip to that label's cap height (14 x 10px with an 8.75px digit) and moves it about 10px up, onto the
row's divider. The left-hand chip has no cell before it and keeps 20 x 17px. Here: theme.js item 5 (rule 10). To report to the
Classic builder.

**Not changed on purpose.** Row heights and grids, Classic's fitters, the horizontal scroll strip of the Leaderboards pills on
phones (Classic's: "EFF" and later pills are reached by scrolling), sizes under 11px that are
Classic's own (Compare chart axis: 10 svg units, 14.5px on a 440P screen), the Leaderboards rows (dividers only, no alternating
shade: the rows do not run edge to edge).

## Pass 3: Rosters, Drafts, Paper Trail (2026-11-11)

theme.css PART 7, theme.js item 6 and ten more entries in item 4's list. Phones and desktop. Scoped to the three sections (`.rox`,
`.dfs`, `.ptx`), their panes and the Paper Trail sheet (`.pts`).

**Surfaces.** Each section is a `--blue-2` plate drawn with spread shadows (12px of plate, 2px black frame, 2px hard shadow, the
glow), so no box moves; `.rox` has a 2px frame of its own in Classic, which becomes part of the plate. On the plate: raised cards
are `--blue` (Rosters' team picker cells and Team assessment, Drafts' Original order and the desktop board panel), round panels
keep Classic's alternating rows (`--blue` / `--blue-2` over the 1px `--blue-3` divider) under a `--blue-3` head strip, wells are
`--blue-3` (the two inner boxes of Team assessment, an empty board cell, points tiles, the search field). Rosters' player rows are
the lineup row of Game Day (`--blue-2`, black 1px frame), as on Players. The sheet is Classic's full-screen `--deck` panel
(`--blue-2`); its season strip is `--blue-3`. The Glossary switch and text get the 8px plate on the three panes.

**Controls.** Year buttons (`.dfyb`, `.ptyb`) and the Picks / Players switch (`.ptsw`): `--blue`, 4px corner, yellow label
(7.69:1); selected = the badge through `--chalk: var(--seg-on); --ink: var(--white)` (the segment mechanism, no list of radio ids).
Team picker `.rofb`: `--blue` cells on `--blue-3` grid lines, selected cell = `--badge` with the white 2px inner ring (twelve
`#ro-N` pairs listed, as Classic lists them), other pictures at 50% opacity, no filter.

**Position colours.** Drafts and Paper Trail write Classic's literals inline (`--pc:#f7739c` ...); attribute selectors re-point the
three that differ from the palette (QB, WR, TE). Pick tiles (`.dfn`, `.ptn`), the sheet's position pill (`.pz`) and the board cells
(`.dfc`) are the `--pos-*` fill with black ink; tiles carry the lineup tile's 1px black edge line and their lines are centred in
the space left of it.

**Literal Classic colours overridden** (everything else arrives through the tokens):

| Classic | Where | Here |
|---|---|---|
| `var(--ink)` used as a FILL | team picker selected cell, Team assessment boxes `.ral` / `.rak span` | the badge; `--blue-3` wells |
| `filter:grayscale(1); opacity:.55` | team picker, other teams' pictures | `opacity:.5`, no filter |
| `#6fc9a4` `#d4af6a` `#e0838f` | average age in the group heads `.ga b` | `--win` / `--yellow` / `--loss` |
| `#9aa3b5`, `#ff5d73` | Taxi squad and Injured reserve heads (`--pc`) | `--peri-lt`, `--loss` (IR was 4.47:1 on the strip) |
| `#3fd69b` `#d4af6a`, `--sky` | outlook tag `.rat` | `--win` / `--yellow` / `--peri-lt` (`--sky` was 4.15:1) |
| `rgba(63,214,155,.16)` + ring, `rgba(255,93,115,.15)` + ring | week result tile `.ralh b` | solid `--win` / `--loss`, black ink (the result tiles of Game Day) |
| `#3fd69b` / `#ff7d8e` | Strengths / Concerns heads and bullets | `--win` / `--loss` ("Concerns" was 4.30:1) |
| `#3a4254` ring | Taxi tag `.txc` | 45% black chip, `--peri-lt`, no ring (a T0 chip as FK / FL) |
| `#0b0e14`, `#0f1218` | pick tile, pill and board cell ink | black |
| `rgba(0,0,0,.12)` ring, `opacity` .70 to .82 on four lines | board cells | 1px black frame, full strength |
| `rgba(238,240,244,.035)` | empty board cell `.dfc0` | `--blue-3` |
| `--via-bar` `#e6cf96` and its three literals | traded-pick banner `.dfct` | white, black line and ink |
| `--via-bg` / `--via-line` gold tints | VIA box of the list `.dfvia` (from 760px) | `--blue-3`, `--yellow` ring |
| `rgba(0,0,0,.4)` + a blurred `rgba(0,0,0,.25)` shadow | Paper Trail pictures | white 1px ring, black 1px hard shadow (ring ink still 38px wide) |
| `--pg` as a strip fill | sheet season strip `.ptsy` | `--blue-3` |

**Paper Trail > Picks by glyph ink** (the item left by pass 1). Classic's `ptxFit` / `tileSnap` take the TIMES TRADED tile's width
from `BC7` (Barlow Condensed's digit outlines), the TIMES TRADED and VIA column widths, the centring of the two heads and of the
coach names, and the NFL slot's right edge from a canvas; the canvas reports glyph ink in Chromium and the advance box in
WebKitGTK, and knows nothing of the theme's word spacing. Here:
- *Heads and coach names* (CSS): Classic's inline transform is off; each line is centred by its first and last glyph (`--ix`,
  item 4) less the tracking after the last letter and the 1px shadow, the same in every engine.
- *Tile width, column widths* (theme.js item 6): `--ptcw` = widest count's Martian digit ink + 16px on Classic's unit grid
  (2026: "3" = 7.37px, tile 23.5px on a 440P screen, 8.1 to 8.2px each side; Classic's 22.3px left 7.5 to 7.6px); `--ptca` =
  max(tile, TIMES / TRADED ink: 34.19px, Classic's canvas gave 34.41px); `--ptva` = max(38px, widest coach ink, VIA ink). The tiles'
  left edges go back on the unit grid for the new width. Vertical placement and the digits' centring (`--ix`, pass 1) are untouched.
- *NFL slot* (`--nx`, a `translate` beside Classic's transform): + the word spacing the canvas did not see (the body's -.22em
  = 3.08px per space: Classic left "PK 3" 2.4px short of the name column's edge), + the last glyph's right bearing where the
  canvas gave the advance box, - the advance rounding of an engine that lays text out on whole pixels.
- Measured from screenshots (`ptm3.py`; WebKitGTK at 3x, the 440P layout, the default year and 2026; re-measured 2026-11-12): TIMES TRADED
  tiles (24px wide, counts 1 / 2 / 3) left and right gaps within 0.07px of each other, top and bottom within 0.28px, 8.24px or more
  beside the digit; projected and drafted pick tiles within 0.11px left / right; TIMES / TRADED heads within 0.49px of the tile column's
  centre, the VIA head 0.11px and the coach names within 0.16px of the picture's centre; the NFL slot's ink ends 0.81 to 1.14px inside
  the name column's edge.

**Chips and tiles (rule 11).** Pick tiles: tracking 0, each line centred by `--ix`. Points tile `.dftl`, outlook tag `.rat`:
`--ix` - .05em - 1px (light ink with the shadow); the outlook tag keeps its 23px height on a cap-trimmed line (7.125px above and
below). Taxi tag and position pill: T0, tracking 0, `--ix`. VIA box of the Drafts list (from 760px): a T0 chip, 17px tall (Classic 16px, rows
unchanged at 50px), `--ix` from the "V" of VIA to the name's last letter shared between its two side paddings (with the shadow
it had 0.8px under the capitals).

**Fit.** Original order between 760 and 1099px: "Anderson" (45.6px) may run 1.4px into the 8px gap on each side (Classic's name
box clips at 42.8px). Board between 1100 and 1239px: last names at tracking -.085em, so the fitter keeps "England Patriots" on
one line (11.5px; Classic 12.5px on one line, the theme's default tracking wrapped it). Glossary: a bold term does not break.

**Not changed on purpose.** Row heights and grids, Classic's fitters (`nameFit`, `holdFit`, `slotFit`, `trFit`, the board's name
fitter), the trade rows' text forms (a pick shows its full form where that fits: "2026 R2 (Reverse Apache Master)" on a 440P
screen), the plate standing flush under the navigation band and against the Glossary plate (as Players), the 3px black divider
before the GM column, sizes under 11px that are Classic's own (the Taxi tag, 10.5px).

## Pass 4: Stats, Team Hub (2026-11-11)

theme.css PART 8 and fourteen more entries in theme.js item 4's list (no new item). Phones and desktop. Scoped to the two panes
(`.pane-sx`; `.pane-th` / `.thx2`). Nothing here reaches the ten tabs shipped before.

**Surfaces.** Stats keeps Classic's panels (`.sxc`, `.posx`: `--blue-2`, black frame, hard shadow) and gains the inner glow. Team
Hub has no panel in Classic (title, picker and every block stood on the ground): `.thx2` is a `--blue-2` plate drawn with spread
shadows (12px of plate, 2px black frame, 2px hard shadow, the glow), so no box moves. On the panel / plate: raised cards are `--blue`
(Team Hub's hero, figure cards, home / road card, dropped-points cards, the Trends week card; Stats' lineup-call cards), wells are
`--blue-3` (the hero's three odds boxes, the Trends chart cards and the frame round the week card, Stats' "Tap a cell" readout and
Record by lineup lean cards, level matrix cells). Table rows keep Classic's alternating shades (`--blue` / `--blue-2` over the 1px
`--blue-3` divider); the Trades head strip is `--blue-3` through the token. The Glossary switch and text get the 8px plate.

**Controls.** Section strip `.lbc.sxnav`: the pill of pass 2 (`--blue-3` well, 4px corner, `--peri-lt` label, selected = the badge
through `--chalk: var(--seg-on); --ink: var(--white)`). Player sim / Team average (`.odsw`): a segment track. Team Hub's picker
`.tqpk.rofb`: Rosters' recipe (`--blue` cells on `--blue-3` grid lines, selected = `--badge` with the white 2px inner ring, twelve
`#thx-N` pairs listed as Classic lists them, other pictures at 50% opacity, no filter). Trends week strip `.tqwk`: raised `--blue`
buttons with a yellow label, selected = the badge; its sticky band is `--blue-2` (Classic: the page colour).

**Matrices, heat, bars** (the requirement: better / worse must stay distinguishable, 3:1 or more against the row).

| Component | Classic | Here | Against the panel `--blue-2` |
|---|---|---|---|
| Schedule swap, Every-week cells `.mx` | better 20% green tint + `#7fdcb6`, worse 17% red tint + `#f29aa6` (4.3:1), level `--ink` | `--win` / `--loss`, black ink; level `--blue-3`, white ink; own cell white | 8.36 / 6.10:1; ink 16.7 / 12.2:1 |
| selected cell `.mx.on` | 2px inner ring `--chalk` | white 2px outline outside the cell | 10.5:1 |
| Ranks, weekly score rank `.hm` | 30 / 16% green, 12 / 24% red tints; gold / red 1.5px ring on 1 and 10 | r1-2 `--win`, r3 `--win-2`, r4-7 the well, r8 `--loss-2`, r9-10 `--loss`; black 2px inner ring on 1 and 10 | 8.36, 4.76, -, 3.61, 6.10:1 |
| Bye exposure `.bx` | 12 / 26% gold tints, 30% orange tint | b1 the well + yellow ring and digit, b2 yellow, b3 orange, black ink | ring 9.91, 9.91, 3.74:1 |
| bar tracks (`.dvb .hbr .hx-bar .tqbar .tqmini`, the rest of `.obar .sbar`) | `--ink`, `--line`, 5% white | black | 2.00:1 (2.57:1 on `--blue`) |
| bar fills | `#3fd69b` `#ff6b7f` `#e8c15a` `#7fa6ff` `#6fc9a4` `#d4af6a` `#e0838f` `#4a5263`, 70 to 78% opacity on two | `--win`, `--loss`, `--yellow`, `--peri` (odds: #1 seed / bye / playoffs = yellow / `--win` / `--peri`; age: `--win` / yellow / `--loss` / `--peri`; home / road `--win` / `--peri`; form `--yellow` to `--orange`), full strength, black 1px inner line | each 3.21:1 or more on `--blue`, 4.15:1 or more on `--blue-2`; all on a black track |
| Consistency band `.cbd` | 8% white + 22% white ring | `--blue-3`, `--peri` ring | ring 4.15:1 |

**Literal Classic colours overridden** (everything else arrives through the tokens):

| Classic | Where | Here |
|---|---|---|
| `var(--ink)` used as a FILL | section pills, level cells, `.ewb`, `.hx-card`, hero odds boxes, picker's selected cell, week strip | `--blue-3` wells; the badge |
| `var(--pg)` as a fill | Trends sticky band `.tqsk` | `--blue-2` |
| `filter:grayscale(1); opacity:.55` | picker, other teams' pictures | `opacity:.5`, no filter |
| `#e8c15a` `#f4c451`; `#5fd3a5` `#7fdcb6` `#6fc9a4`; `#f08a98` `#ff8a9a` `#e0838f` `#e58f9c`; `#93b4ff` `#a9c3ff` `#b9c1ff` | figures and heads (`.c1 .c2 .c3`, `.up .dn`, `.tqr`, `.hx-d`, age shares, winners' scores) | `--yellow`; `--win`; `--loss`; `--peri-lt` |
| 14 to 20% tints with tinted text (some with a 35 to 50% ring) | W / L tiles `.wl`, home / road tags `.hx-t`, "cost the win" `.dtag`, "WON" `.txw`, streak `.stk`, close / blowout margins `.gmv` | solid `--win` / `--loss` / `--peri` / yellow, black ink, no ring (the result and home / road tiles of Game Day) |
| `#e8c15a` `#c9d2e3` `#7a8396` `#7fa6ff` | pick round chips `.pkc` | yellow, white, `--peri-lt`, `--peri`; black ink |
| `#0f1218` | position pills and heads `.pz`, `.pp` | black |
| 8% white; gold / green / red tints | opponent rank chips in the bye lists `.bop em`, `.bnt em` | the rank chip (45% black, `--peri-lt` / `--win` / `--loss`; gold with the yellow ring) |
| `#7fa6ff` `#ff8a3d` `#f4c451` `#ff8a9a` `#6fc9a4` `#e8c15a`, Classic's own position hues, `#8ec5ff`, `#efd38a` | Trends lines, dots, bands, readouts, legends, bye marker, week cursor | `--peri` (text `--peri-lt`), `--orange`, `--yellow`, `--loss`, `--win`, `--yellow`, `--pos-*`, `--peri`, `--yellow` |
| `rgba(244,196,81,.16)` + ring, `--win-bg` / `--loss-bg`, orange / blue tints | Trends header tiles `.tqt` | the rank chip; rank 1 solid yellow, last solid `--loss`, result W / L solid `--win` / `--loss`; zone chips yellow (bye) / `--peri-lt` (playoffs) |
| Classic's numeral art | hero seed tile `.tqsd.rnh` | the CSS rank tile (rule 6): 42 x 44px, `--badge`; seeds 1-2 yellow digit, 3-6 white, 7 and lower the flat chasing tile |

**Rank chips the fitter sizes** (`.ch` in Remaining schedule and Consistency, Team Hub's dropped-points chips, `.tqt`). Classic's
tile fitter writes size, both side paddings and a `translateY` inline with `!important`. Here the chip's own fill is off and
`.ct::before` paints the tile: `top:0; bottom:0; width:100%` of the chip (so Classic's fitted size), placed from the text's static
position and moved by `(advance - 100%)/2 - --ix/2`, i.e. centred on the centre of the glyph ink; advance = `--nc` characters of
`.525em` (+ `--iw` in an engine that rounds advances). The tile can sit a fraction of a pixel off the chip's layout box (the
fitter's padding difference); nothing else moves. Measured from pixels (`chipm.py`: text on / text off / tiles off): WebKitGTK at the 440P / 402P layouts and 1440, 312 chips: left and right gaps within 0.37px of each other, 3px or more beside (4.2px beside "10"), 2px or more above and below; one Consistency chip at 1440 could not be read (a neighbour's tile inside its crop). Headless Chromium, 624 chips at six widths: 3.89px or more beside, 2.15px or more above and below, the two side gaps within 0.82px (see Known issues).

**Chips and tiles the theme sizes (rule 11).** T0, tracking 0, `--ix`: W / L tiles, home / road tags (padding 0 5px 1px: Classic's
right padding allowed for its .06em tracking), "All", pick chips, position pills and heads, FAAB tile, "Wk N" and "+N pts lost"
(shadow off), close / blowout margins, "cost the win", "WON", bye-list rank chips, the unfitted rank chips of Points by position.
Hero streak tile: a cap-trimmed line with 3px above and below (Classic 1px / 0).

**Not changed on purpose.** Row heights and grids, Classic's fitters (`sosFit`, the tile fitter, `pcnFit`), the Trades side headers'
ellipsis (Classic's by design), the horizontal scroll strip of the section pills on phones, SVG axis text sizes (Classic's own: 10
svg units), "BYE" / "PLAYOFFS" zone labels crossing a line in the Standings chart (Classic's layout), the plate standing flush under
the navigation band and against the Glossary plate (as Players).

## Pass 5: Standings on desktop, Standings Glossary (2026-11-12)

theme.css PART 9, four more entries in theme.js item 4's list and a late check in item 1 (no new item). Everything except the Glossary
plate, its switch and the no-break rule for bold terms is inside `@media(min-width:1100px)`: the phone layouts keep PART 4. 956L lays
out at 1124 CSS px and is a desktop layout.

**What changed against the Standings shipped 2026-11-09** (desktop had the token overrides and the CSS rank tiles only):

| Component | Before (tokens only) | Now |
|---|---|---|
| Table panel `.dtp` | 2px hard shadow, no glow | the board's panel: 4px hard shadow, inner glow above the rows |
| Table head (group row "20k simulations" + column heads) | the panel colour (`--blue-2`) | `--blue-3` strip (as The Wire's column heads and the round heads) |
| Row dividers | black 2px (Classic's body-wide frame colour) | `--blue-3` 2px (rule 1); the 4px rule before the simulation columns stays black |
| #1 odds `td.c1` | Classic's literal `#e8c15a` | `--yellow` |
| Streak tile `.dsk` | 16% tint, `--win` / `--loss-lt` text (loss 3.68:1), 4px corner | solid `--win` / `--loss`, black ink, 2px corner, 1px hard shadow, ink centred by `--ix` |
| Proj finish tile `.rkb` | centred by its advance box | centred by its glyph ink (`--ix`) |
| Rank chips in the table and in the cards' stat lines | 45% black chip; gold and worst with a 1px ring; Classic's fitted box (1.75px above / below the digit, 2.25px beside "10") | tile drawn round the digit by `.ct::before`, 1px wider each side, 1.5px taller above and below; rank 1 solid yellow, last solid `--loss`, black ink, no ring |
| Cards' streak tile `.sk` | Classic's fitted tile, centred by the fitter's canvas (2px between the side gaps on 5 of 10 tiles in WebKitGTK) | drawn round the glyph ink (`.ct::before`), .5px taller above and below |
| Divider before the Nerd column (`.r::after`) | `--line-strong` (white here) | `--blue-3` |
| Last column, 1100 to 1239px | 3px to the panel's frame (ink + shadow 2px) | 9px (7.5px measured); TEAM gives up the 6px |
| Glossary (every width) | switch and text on the orange end of the ground; selected segment white with black text | 8px `--blue-2` plate (12 / 10px outside the boxes, as the other tabs); selected = the badge; a bold term does not break |
| After H2H / Median on desktop | theme.js item 1's `__fitAll()` makes Classic draw the table and cards again after its fitters ran: in WebKitGTK about 1 press in 3 left the table's rank chips unsized and 1 in 10 the cards' streak tiles (Classic alone: 0 of 20) | late check in theme.js item 1 (Classic's own `rrFit()` / `tileFit()`, only when a tile is unsized): 0 of 40 presses |

**Not changed on purpose.** Cutoff strips (`--pg` purple with the tier-coloured rule), the Median second line (`--peri-lt`, 11px), the
shotgun tally, column widths other than TEAM and the last column at 1100 to 1239px, `simGap()`'s 16px rule, row heights, the season
chart (its SVG chips keep their rings, as on phones), the grain (cards only; the table's rows are plain, as every other table), the
desktop rank tiles' centring (CSS default, see cleanup), Classic's fitters.

**Fitter-sized digits are nominally smaller than Classic's.** Classic's tile fitter sizes a chip's digit from the digits' ink height
on a canvas. Martian Mono's digits are taller in the em than Barlow Condensed's (.733em against about .70em with `size-adjust`), so
the same tile gets a 10px digit where Classic has 10.25px (8.75px in both at 1100px in the table). The ink is the same height; the
overflow audit counts these 24 text nodes per desktop state as "smaller than Classic's" (144 over the 54 state x width pairs). The
phone layouts have the same chips and the same 0.25px.

**Measured (2026-11-12).** WebKitGTK at 2x, 1440 and 1100: 280 fitter-sized chips, left and right gaps within 0.46px of each other,
3.55px or more beside the digit, 2.0px or more above and below (smallest reading 1.99px). Headless Chromium at 956L / 1100 / 1240 / 1440 / 1920, 850 chips: 3.19px or more
beside, 2.64px or more above and below; 132 read 0.55 to 0.92px between their side gaps (the engine's whole-pixel text placement,
see cleanup). Rank tiles (table 26 x 24px, cards 42 x 44px zoomed 1.1): ink including outline and shadow 4.2px or more from the
border beside, 4.5px or more above and below (120 tiles, both engines).

## Cleanup job 2: one rank-chip style on Standings (2026-11-12)

theme.css PART 8 (the shared drawn tile) and PART 9 (block "Standings, EVERY layout"); one more entry in theme.js item 4's list.

| Element (Standings) | Before | Now |
|---|---|---|
| Fitter-sized stat-line chips, below 1100px | Classic's fitted box, 45% black; gold and worst with a 1px ring | the desktop's drawn tile (`.ct::before`, `--ce:1px`, `--cv:1.5px`): rank 1 solid `--yellow`, last solid `--loss`, black ink, no ring |
| Streak tile, below 1100px | Classic's fitted tile, centred by the fitter's canvas | drawn round the glyph ink at Classic's height (`--cv:0`; desktop `.5px` unchanged) |
| Dropped-points chips (never fitter-sized), week-strip chips, any unsized chip; every layout | 45% black box; gold and worst ringed | same box; rank 1 solid `--yellow`, last solid `--loss`, black ink, no ring; dropped-points and week-strip digits ink-centred (`--ix`, advance rounding from `--rnd` / `--cz`) |
| Proj finish tile of the desktop table (`.rkb`) | gold and worst ringed | the same two fills, no ring |
| Season chart SVG chips (RANK / OPP) | 45% black; gold, worst and ranks 2-3 ringed; digits with the 1px shadow, centred by their advance box | rank 1 solid `--yellow`, last solid `--loss`, black digits; no ring on any chip; all digits T0 and ink-centred (`translate` by half of `--ix`); boxes unchanged |
| Drawn-tile recipe | three copies (PART 8, PART 9 x 2) | one rule set (PART 8) |

Contrast, computed: black ink on `--yellow` 19.79:1, on `--loss` 12.18:1, on `--win` 16.68:1; tile against the lighter / darker row:
`--yellow` 7.69 / 9.91, `--loss` 4.73 / 6.10, `--win` 6.48 / 8.36.

**Measured (2026-11-12; ink to tile edge from pixels, `chipph.py` / `svgm.py`; minimum left / right / above / below, CSS px).**
Chromium at 360P, 402P, 440P, 874L, 956L, 1100, 1440 (Nerd H2H and Dumb Median, week strips open): fitted chips 3.14 / 3.18 / 2.64 /
2.65; dropped-points chips 3.65 / 3.94 / 2.63 / 2.65; week-strip chips 4.61 / 4.88 / 3.33 / 3.62; streak tiles 3.78 / 4.04 / 2.46 /
2.94; Proj finish tiles 6.06 / 6.02 / 4.11 / 4.74; SVG chips rank 1 and last 3.98 or more beside and 2.26 or more above and below
(smallest chart, 1100px: 14.9 x 10.2px chips). No gap under rule 11's minimums on a solid chip. Left / right balance in Chromium: up
to about 1px (whole-pixel text placement, Known issues 44). WebKitGTK at the 402P / 440P layouts (3x): fitted chips 3.46 / 3.46 /
2.99 / 2.98, sides within 0.19px; dropped-points 4.15 / 4.23 / 3.18 / 3.18, within 0.18px (0.67px on 7 of 40 before); week strip
4.77 / 4.76 / 3.83 / 4.18, within 0.38px; streak 4.22 / 4.04 / 2.87 / 3.67, within 0.25px (1.59px on 5 of 10 before); SVG rank 1 and
last 5.45 or more beside, 3.00 or more above and below, within 0.22px. WebKitGTK at 1440 (2x): fitted 3.56 / 3.55 / 2.29 / 1.98 (as
before the job), dropped-points 4.10 / 4.16 / 3.62 / 3.32 within 0.32px, week strip 5.44 / 5.42 / 4.26 / 4.34 (7 of 180 at 0.51 to
0.63px), Proj finish 6.25 / 6.50 / 4.28 / 5.78 within 0.44px, SVG rank 1 and last within 0.37px. The drawn tile stands 1.57px
(Chromium) / 2.00px (WebKitGTK) or more from the ink of the line above (Luck line pair at 360P / 402P) and 1.17 / 1.67px from the
figure on its left.

**Limits found.** (a) Dumb + Median with a week strip open, WebKitGTK at the 402P / 440P layouts: rows that start on a fraction of
a pixel show the drawn tile snapped apart from its digit: 10 to 12 of 50 fitted chips read 0.51 to 0.76px between their side gaps and
1 or 2 read 2.90px beside (rule 11: 3px); Nerd + H2H with strips open and Dumb + Median with no strip open: none; the build before
the job read up to 1.39px on 15 of 50 chips in the same state. (b) Mid-rank SVG chips (untouched boxes) read 1.76 to
1.93px above or below the digit in Chromium where the chart is smallest: 12 chips at 1100px, 2 at 956L; rank 1 and last hold 2.26px.
(c) SVG chips were not read in WebKitGTK at 1100px (the run returned nothing); 402P / 440P layouts and 1440 were.

## Known issues / cleanup (consolidated 2026-11-12, passes 1 to 5)

Open items, most visible first. Each names where it was found.

**A. Standings**

1. **Closed 2026-11-12 (cleanup job 2): one rank-chip style on Standings, every layout.** Fitter-sized chips = the drawn tile; chips
   the fitter does not size (dropped points, week strip, Proj finish tile, the season chart's SVG chips) = the same two fills on
   their own box. Figures under "Cleanup job 2". Left: the other tabs' ringed chips (item 41).
2. **Desktop rank tiles are centred by CSS only (pass 5).** theme.js item 2 (rule 7, the device-pixel snap) runs below 1100px. On
   desktop `rkm5.py` reads the digit about 0.5 to 1px above the tile's centre in both engines (the reading is good to about 0.5px:
   the outline's and shadow's share of the ink is estimated). Gaps are far above rule 11's minimums.
3. **Closed 2026-11-12 (cleanup job 2): phone streak tile drawn round the glyph ink** (WebKitGTK: 1.59px between the side gaps on 5
   of 10 tiles before, 0.25px or less now). Safari unverified.
4. **Shotgun tally (2026-11-09):** `SGD` / `SGR` are Barlow Condensed / IBM Plex Sans bearings; the mug-to-count and label-to-mug gaps
   are off by a fraction of a pixel in Martian Mono.
5. **Season chart chips (SVG): solid recipe since 2026-11-12 (cleanup job 2)**, measured against rule 11 ("Cleanup job 2"); they keep
   Classic's 3px corners (the HTML chips have 2px). One mid-rank chip ("6") reads 0.64px between its side gaps in WebKitGTK at 1440.
6. **Rank chips' digits 10px against Classic's 10.25px nominal** (same ink height; "Pass 5").

**B. Rule 11 limits on the other tabs**

7. **Four elements in WebKitGTK (pass 4):** three pick-round chips in Stats > Trades at the 402P layout ("2nd" / "3rd": 0.67 to 1.00px
   between the side gaps) and one dropped-points rank chip in Team Hub at the 440P layout (0.67px): they start on a fraction of a pixel
   and the engine snaps glyphs and tile separately. All gaps above the minimum.
8. **One of 45 rank chips ("20") in the Playoffs schedule at 440P (Game Day)** reads 0.67px in WebKitGTK.
9. **Fitter-sized rank chips outside the drawn-tile recipe (Game Day):** chips Classic's fitter sizes on Matchups / Playoffs follow
   Classic's 1.75 to 3.5px window. The one under 2px ("Week rank") became a figure.
10. **Score cells:** a figure of six characters or more would not keep 3px (cannot occur); without `theme.js` the figure uses a mean
    bearing (up to 0.65px off centre); the cell's own position on the device-pixel grid is not corrected (up to 0.33px at 3x).
11. **Engines without `text-box`** (before Safari 18.2 / Chrome 133) keep Classic's paddings for vs / @, injury tags, FK / FL and
    "N on bye"; engines without relative colours (before Safari 18 / Chrome 131) show no T1 shadow; engines without style queries keep
    Classic's two literals on Compare's swapped panels.
12. **Paper Trail:** `slotFit`'s 12px test and `nameFit` still measure through Classic's canvas (a slot is judged up to 3px wider than
    it is; none of the 2026 picks is affected at 360P / 402P / 440P); vertical placement relies on the digits' flat height being
    .70em (holds with `size-adjust`).
13. **Original order names between 760 and 1099px (pass 3):** "Anderson" may run 1.4px into the 8px gap on each side.

**C. Layout and surfaces**

14. **Plates meet (passes 2 to 5).** The section plate ends 2px into the Glossary plate's frame and stands flush under the navigation
    band on Players, The Wire, Rosters, Drafts, Paper Trail, Team Hub (Classic leaves 16px / 24px; the plates need 16px / 26px). The
    Glossary switch's plate and the text's plate overlap by 4px on every tab (one shared frame line). Standings is clear of the board
    (10px).
15. **Short pages / orange ground:** every tab's Glossary now stands on a plate; any free-standing text added later below the first
    1100px would again sit on the orange end (2.8:1 against white).
16. **Past-season buttons** open Classic's (unthemed) pages, and those pages' 2026 button returns to Classic.
17. **No link** from Classic or from the loop to the themed tracker yet (by decision; the loop has a CLASSIC link only).
18. **Favicon:** the 16px point is closed (2026-11-12: TL, hand-hinted 16px drawing). Still open: desktop Safari's pinned-tab
    `mask-icon` is not provided; the pages link PNG icons only, so sizes above 32px (other than the 180px touch icon) scale the 32px PNG.

**D. Measurement and engines (not page defects)**

19. **Headless Chromium** places text on whole CSS px. With the phones' 0.85 page scale its FAAB and rank-tile gaps differ by up to
    0.8 / 1.5px (rule 7 is met in WebKit only); "@" tiles read 1.6 to 4.3px above and 2.3 to 4.3px below by row; 106 of 624
    fitter-sized chips on Stats / Team Hub and 132 of 850 on desktop Standings read 0.55 to 0.92px between their side gaps; one gold
    dropped-points chip on desktop Standings reads 1.0px. Minimum gaps hold in every case. WebKitGTK: 0.
20. **WebKitGTK rounds glyph advances to whole pixels** (Safari does not); `theme.js` measures the advance once and compensates
    (`--rnd`, `--iw`, `--fx*`).
21. **Phones' page scale 0.85:** rule 7's grid is 1 / devicePixelRatio CSS px; the scale is applied to the raster afterwards. Not
    measurable in the sandbox. Real iPhone Safari is checked by Nicklaus.
22. One Consistency chip at 1440 could not be read by `chipm.py` (a neighbour's tile inside its crop; pass 4). `chipm5.py` switches off
    only the chips' own digits for that reason.

**E. Classic bugs found here, to report to the Classic builder (worked round in the copy)**

23. Pressing H2H / Median does not re-run `s2Fit` (2026-11-09; theme.js item 1; DESIGN.md §8).
24. Compare > Schedule > Week by week: `ref()` takes "Wk 10" as the right-hand seed chip's figure (pass 2; theme.js item 5).
25. "Week rank" chip sits 4.43px above its label's cap band (the label is a flex item; Game Day).
26. Desktop table outer columns 3 to 9px from the panel edge (DESIGN.md §8; the copy sets the last column to 9px at 1100 to 1239px).

38. Classic's Standings row rule `.r{... border-top:1px solid var(--line); padding:12px 0; cursor:pointer; position:relative}` also
    matches the road tile `<span class="gha ht r">` on Matchups and Playoffs (the tile's own rules reset display and padding, not the
    border): every "@" tile carries a 1px top border, black through Classic's body-wide border-colour rule, and the pointer cursor.
    In Classic it hides against the dark tile; on the copy's solid periwinkle tile it was a black cap (request 33). Worked round in
    the copy since 2026-11-12 (`border:0; cursor:inherit` on the glyph); Classic still has it.

**F. Code cleanup**

27. theme.js item 1 can go when Classic re-fits after H2H / Median by itself; item 5 when `ref()` skips those chips. The late check
    added in pass 5 exists because `__fitAll()` makes Classic draw the desktop table and cards again: it goes with item 1. It runs on
    desktop only. Phones, checked 2026-11-12 (cleanup job 2): WebKitGTK, 96 presses at the 402P / 440P layouts, no tile left unsized
    (0 at 2.6s; unsized for a moment on 80 presses at 0.45s, 27 at 1.1s, 1 at 1.7s; Chromium 0 of 96 at every sample), so the late
    check was not extended. An unsized chip shows the same fills on Classic's box, so no ring appears in that moment.
28. **Closed 2026-11-12 (cleanup job 2):** the drawn-tile recipe is one rule set (PART 8; members set `--ce`, `--cv`, `--cz`).
29. `dtPanels` and Classic rules for `tr.dtb` are unused; PART 4's ringed `.ch.gold` / `.ch.last` rules remain for the tabs that still
    carry the ring (item 41) and go with them.
30. `retro/favicon.html` and the marked blocks of `template.html` are generated copies (`wordmark_gen.py apply`): after editing the
    generator, run it, or the two pages' icons drift apart.
31. A page left open across a deploy uses the copy's own `p/`; old chunks are published only as far as Classic keeps them (`DT_CHUNKS`).
32. Wordmark options A and B are kept outside the repo only (`shots-theme/wordmark/` patches).

**H. Found 2026-11-12 (cleanup job 2), not fixed there**

39. Remaining schedule (Stats) and the Team Hub schedule cells: 0px between the logo's black shadow and the drawn rank tile (logo ring
    2px + shadow 2px + the tile's 1px reach use up Classic's 5px gap).
40. The record's dash: the digits' and the dash's outlines overlap (0 to 1px of white between white).
41. The other eleven tabs' gold and worst rank chips still carry the ring; they move to the solid recipe in the next job.
42. Classic bug seen through the copy: in Safari's wide layout (>= 1100px) the per-week text of PF / PA / TOT EFF is missing and the
    dots stand where the full line would end (Classic too; Nicklaus's screenshots 2026-11-12; not reproducible in Chromium).
43. Classic bug seen through the copy: Team Hub > Trends header tiles overflow their 260px cards at viewport widths 760 to about
    900px (24.1px past the card in the copy, 103px in Classic).
44. Standings in headless Chromium only (whole-pixel text placement, as item 19): the Dumb / Nerd switch label reads 1.57px and the
    H2H button 0.78px between their side gaps at 360P (7.05px or more to the frame; the same before the job; WebKitGTK 0); drawn
    chips, dropped-points, week-strip and SVG chips read up to about 1px between their side gaps. Minimum gaps hold.
45. Desktop, WebKitGTK at 1440: two fitted "10" chips read 0.61px between their side gaps and 7 of 180 week-strip chips 0.51 to
    0.63px (102 of 180 up to 1.11px before the job); the same two fitted chips read 0.61px on the build before the job.

**G. Requests parked by Nicklaus on 2026-11-11 (rechecked against the build of pass 5 on 2026-11-12, cleanup job 1; all five closed)**

33. Matchups vs / @ tiles: **closed 2026-11-12: tiles removed, coloured glyphs (Nicklaus 2026-11-12).** The old black top band on
    "@" was the 1px top border of item 38; `border:0` on the glyph takes it off in the copy.
34. Bench band: **closed 2026-11-12** (gap 0 -> 18px, purple -> `--blue-3` head strip with black lines, label yellow; "Bench band").
35. Standings rank dots: **closed 2026-11-12** (empty dot's ring `--peri` -> black; "Decisions, cleanup job 1").
36. Slate header in a framed tile: **closed 2026-11-12** ("Slate header").
37. Slate view surfaces: **already fixed by Game Day (pass 1)**: the Playoffs lineups gained the `.pox` plate; `--blue-2` measured behind
    every slate header and total line on Matchups and Playoffs. No change in cleanup job 1.

## Checks before shipping a change to the theme

- `tools/tilechk.py`'s check against the copy at 360P 402P 440P, Dumb and Nerd, H2H and Median: 0 violations
  (Chromium and WebKitGTK).
- Clip / wrap / ellipsis / sideways-scroll scan against Classic at the same widths; no element moves against the
  previous build except what the change is about; computed contrast scan: 0 under the limits.
- Tile ink centring from screenshots: WebKitGTK with `GDK_SCALE=3` at the phone layout widths (424 / 473 / 518 CSS
  px), tile edges read from the pixels; Chromium at device scale 3 for comparison.
- **Dark-ink audit (rule 2):** on the built copy, every tab and every state a radio or button reaches (100 states), at
  402P, 440P and 1440, Chromium and WebKitGTK: for each visible text node the ink colour, the surface under it (sampled
  from a screenshot taken with all text switched off), and the computed `text-shadow` / `-webkit-text-stroke`. Fail =
  ink darker than its surface with a dark shadow or a dark stroke. Must be 0.
- **Frame gaps (rule 11):** score cells of a full lineup (starters and bench, both teams; FINAL, LIVE, PROJ; worst cases
  "88.8", "100.0", "-1.2", "+11.8", "−11.8") at 360P, 402P, 440P, 1440, 1920, Chromium and WebKitGTK (3x phones, 2x
  desktop): ink including shadow = the pixels that change when text is switched off, edges weighted by coverage.
  Left and right >= 3px and within 0.5px of each other, top and bottom >= 2px. Boxes outside the cells: none moved.
- **Game Day (Matchups, Playoffs), 2026-11-11:** dark-ink audit and contrast 0 over the states listed in `darkink` (every
  week type, Lineup / Optimal, Slate, Detailed, Colors, a simulated LIVE lineup, week / team menus open, bracket games,
  builder, schedule, Glossary); frame gaps for EVERY framed element holding text (not only the score cells), same
  limits, with sticky elements unstuck and elements under an open menu left out; score cells line by line; clip / wrap /
  ellipsis / sideways scroll and text under 11px against Classic; box comparison against Classic for rows, cells,
  tiles and cards (intended differences: the 44px cells); 360P, 402P, 440P, 1440, 1920, Chromium and WebKitGTK.
- **Pass 2 (Leaderboards, Players, The Wire, Compare), 2026-11-11:** same audits, states in `darkink2.py` / `gapf2.py` / `ovf2.py`
  (every stat, position and filter, Position / Team, Pts / per game, the eight Compare sections, a reversed team pair, menu open,
  Glossary). Chromium at 360P, 402P, 440P, 874L, 956L, 1440; WebKitGTK at the 402P / 440P layouts and 1440. Result: dark-ink 0
  (all twelve tabs at 440P and 1440), contrast 0, frame gaps 0, clip / ellipsis / extra lines / sideways scroll / text smaller
  than Classic's 0; Standings (360P / 402P / 440P / 1440), Matchups and Playoffs (440P / 1440) boxes identical to the build before
  the pass; tile check 0.
- **Pass 3 (Rosters, Drafts, Paper Trail), 2026-11-11:** same audits, states in `darkink3.py` / `gapf3.py` / `ovf3.py` (every
  team, colour mode, order and sort; every draft year, list and board; Picks of every year, Players, a pick sheet with trade
  steps, a drafted pick's sheet, a player sheet; Glossary) and `ptm3.py` (Paper Trail ink). Chromium at 360P, 402P, 440P, 874L,
  956L, 1440; WebKitGTK at the 402P / 440P layouts and 1440. Result: dark-ink 0 (all twelve tabs at 440P and 1440 in Chromium, 123 states each; the three tabs at every other width and in WebKitGTK), contrast 0, frame gaps 0 (the VIA box at the 874L layout was fixed late and re-run in both engines), clip / ellipsis / extra lines / sideways scroll / text smaller than Classic's 0; the seven shipped tabs' boxes identical to the build before the pass (76 states: Standings 360P / 402P / 440P / 1440, the other six at 440P / 1440); tile check 0 (36 runs).
- **Pass 4 (Stats, Team Hub), 2026-11-11:** same audits, states in `darkink4.py` / `gapf4.py` / `ovf4.py` (all 17 Stats sections,
  Per start / Per week / Total, Player sim / Team average, a selected Every-week cell, Glossary; Team Hub: five teams opened one after
  another, Data and Trends, two weeks, Glossary) and `chipm.py` (rank chips whose tile is a pseudo-element, which the frame audit
  cannot see). Chromium at 360P, 402P, 440P, 874L, 956L, 1440; WebKitGTK at the 402P / 440P layouts and 1440. Result: dark-ink 0 (all twelve tabs at 440P and 1440 in Chromium, 131 states each; the two tabs at every other width and in WebKitGTK, 31 states each); contrast 0 on both tabs at every width in both engines (Standings 44, Glossary only: pass 5); frame gaps, Chromium 0 at all six widths (26 states, 1,265 to 1,460 framed elements a width); WebKitGTK 1,440: 0, 402P layout: 3, 440P layout: 1 (the four elements under Known issues); fitter-sized rank chips: WebKitGTK 0 of 312, Chromium 106 of 624 on the left / right balance only (Known issues); clip / new ellipsis / extra lines / sideways scroll / text smaller than Classic's 0 (186 state x width pairs; the Trades side headers found on 360P and 402P screens were fixed and re-run); the ten shipped tabs' boxes identical to the build before the pass (90 states: Standings 360P / 402P / 440P / 1440, the other nine at 440P / 1440); tile check 0 (36 runs); Classic byte-identical (53 files outside `site/retro/`); 8 patches apply.

- **Pass 5 (Standings on desktop, Glossary), 2026-11-12:** audits in `retro/qa/` (README there): `darkink.py`, `gapf5.py`, `chipm5.py`,
  `rkm5.py`, `ovf5.py`, `boxes.py`, `tilechk_r.py`, `loop.py`. Standings states: Dumb / Nerd x H2H / Median, Glossary open in Dumb and
  Nerd, the refresh pill. Chromium at 360P, 402P, 440P, 874L, 956L, 1100, 1240, 1440, 1920; WebKitGTK at the 402P / 440P layouts,
  1100 and 1440. Result: dark-ink 0 and contrast 0 on all twelve tabs (Chromium at 440P and 1440, 133 states each) and on Standings at every other width (Chromium 9 widths, 63 states; WebKitGTK 3 widths, 21 states), Glossary open included (was 44 at 440P, 46 at 1440). Frame gaps on desktop Standings: WebKitGTK 0 at 1440 and 1100 (5 states; the two Median states at 1440 were read again with a 4.5s settle: the late re-fit moved the page during the first capture), 0 of 170 drawn chips at 1440 (0 of 280 with 1100), 0 of 20 rank tiles; Chromium at 956L / 1100 / 1240 / 1440 / 1920: no gap under the minimums (850 chips, 100 rank tiles, every framed element), left / right balance over 0.5px on 132 of 850 chips (0.55 to 0.92px) and on one gold dropped-points chip (1.0px, 3 Nerd states a width): the engine's whole-pixel text placement (Known issues, D 19). Clip / new ellipsis / extra lines / sideways scroll 0 (54 state x width pairs; "W / L chip" in the Glossary, found on a 402P screen and at 1100px, was fixed and re-run); text nominally smaller than Classic's: the fitter-sized chip digits only ("Pass 5"). Boxes identical to a copy built from the commit before the pass: the eleven other tabs at 440P / 1440 (84 states) and Standings at 360P / 402P / 440P / 874L (16 states), the phone Standings dumps repeated after each late fix. Tile check 0 (48 runs: 12 widths, H2H / Median, Dumb / Nerd). Classic byte-identical (52 files outside `site/retro/`); 9 patches apply. Loop page: six screens at 402 x 874 and 1280 x 800, no page errors, no sideways scroll, badge box unchanged, `data.json` swapped with 0 navigations.

- **Cleanup job 1 (requests 33 to 37, TL favicon and badge), 2026-11-12:** audits in `retro/qa/` against a copy built from the commit
  of pass 5. Chromium: dark-ink 0 and contrast 0 on all twelve tabs at 440P and 1440 (133 states each) and on Standings, Matchups and
  Playoffs at 402P (42 states); frame gaps (`gapf.py`, Matchups and Playoffs) 0 at 360P, 402P, 440P and 1440; clip / ellipsis / extra
  lines / sideways scroll 0 on Matchups, Playoffs and Standings at 360P, 402P, 440P, 874L, 956L and 1440, text smaller than Classic's
  109 and 96 nodes, the same nodes as before the job (none new); tile check 0 (36 runs). WebKitGTK at the 402P / 440P layouts and 1440:
  dark-ink 0 and contrast 0 on the three tabs (42 states a width); frame gaps (`gapf.py`) 0 at the 402P layout and at 1440, 1 at the 440P layout (the "20" rank chip of the Playoffs schedule, Known issues 8, not touched). The slate header tile (12 a width, Matchups and
  Playoffs): ink including shadow 3.13 to 4.00px beside (left and right within 0.40px in Chromium at 360P / 402P / 440P, 0.50px at 1440
  in both engines, 0.33px in WebKitGTK at the phone layouts) and 2.35 to 3.52px above and below (WebKitGTK 3.00 / 3.33px). vs / @
  glyphs: figures under "vs / @ glyphs". Boxes against the pass 5 build: Standings (360P / 402P / 440P / 874L / 956L / 1440, four
  states each) and the nine other tabs (440P / 1440) 0 changed; Matchups and Playoffs (the same six widths, 132 states) only what the
  job is about: everything under the bench band 18px lower and its containers 18px taller, the slate header tile (2.5px higher, 5px
  taller, 9.3 to 10.3px wider) with the starters count 9.3 to 10.3px to its right, and the vs / @ glyph's own box 0.9px up (its
  `translate`; the slot's layout box is unchanged). Loop page: six screens at 402 x 874 and 1280 x 800, no errors, no sideways
  scroll, badge box unchanged, data swap with 0 navigations; the same three icon links on both pages; all 9 patches apply; Classic
  byte-identical.
- **Cleanup job 2 (one rank-chip style on Standings), 2026-11-12:** against a copy built from origin/main before the commit (71f68eb).
  Chromium: `chipph.py` and `svgm.py` at 360P, 402P, 440P, 874L, 956L, 1100, 1440 (figures under "Cleanup job 2"): no gap under the
  minimums on any solid chip; tile check 0 (36 runs); dark-ink 0 and contrast 0 on Standings at 360P, 402P, 440P, 874L, 956L, 1440 (7
  states each); clip / ellipsis / extra lines / sideways scroll 0 at the same six widths (36 state x width pairs), text smaller than
  Classic's: the same nodes as before; boxes on Standings (six widths, 24 states): nothing moved except what the job is about, in the
  Nerd states: 13 dropped-points digit spans (`.ct`, 0.44px or less narrower, the ink centring) and 36 to 54 SVG chip digits (0.30px
  or less, the `translate`); the eleven other tabs: full-page captures at 440P and 1440 pixel-identical (22 captures) and boxes
  identical (84 states); no gold or worst ring left on Standings at 402P, 874L, 1100, 1440 (H2H and Median, strips open). The fold of
  the drawn-tile recipe: computed geometry and paint of every drawn tile identical before and after on Stats (17 sections), Team Hub
  (4 teams, Data and Trends) and desktop Standings, Chromium 440P / 1440 and WebKitGTK 440P layout / 1440. WebKitGTK: `chipph.py`
  at the 402P / 440P layouts and 1440, `svgm.py` at the 402P / 440P layouts and 1440, frame gaps (`gapf5.py`) and dark-ink /
  contrast on Standings (402P / 440P layouts and 1440, 7 states each): frame gaps 0, dark-ink 0, contrast 0; chips as under "Cleanup job 2" (its limits (a) and (c)). theme.js item 2's inline values (FAAB and seed tiles) identical before and after (phase 1 build). All
  9 patches apply; Classic identical apart from the build stamp.
- Real iPhone Safari is checked by Nicklaus.
- Classic byte-identical before / after `retro/build.py` + `retro/theme_build.py`; `git status` shows only `retro/`
  (plus the documented one-liners).
