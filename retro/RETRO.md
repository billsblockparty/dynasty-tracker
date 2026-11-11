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

---

# Tracker theme (`/retro/tracker/`)

The full tracker in the DynastyCast look: a themed copy of Classic's built page at `/dynasty-tracker/retro/tracker/`.
The loop above is unchanged. These rules replace DESIGN.md's look rules inside the copy; Nicklaus's precision standards
carry over. BBP only. No link from Classic or from the loop points here yet.

## Status per tab

| Tab | Status | Effort left |
|---|---|---|
| Standings, phones (360P / 402P / 440P; Dumb, Nerd, H2H, Median) | `LIVE` 2026-11-09 | - |
| Standings, desktop (>= 1100px) | NOT STARTED (token overrides and the CSS rank tiles only) | small |
| Leaderboards, Players, The Wire, Compare, phones and desktop (360P / 402P / 440P / 874L / 956L / 1440; every stat, position, filter, Position / Team, Pts / per game, the eight Compare sections, menus, Glossary) | `LIVE` 2026-11-11 ("Pass 2" below) | - |
| Matchups, phones and desktop (360P / 402P / 440P / 1100 / 1440 / 1920; every week, Lineup / Optimal, Position / Slate, Lean / Detailed, Colors, FINAL / LIVE / PROJ, week menu) | `LIVE` 2026-11-11 ("Game Day" below) | - |
| Playoffs, phones and desktop (bracket, game panels, matchup builder, schedule, lineups) | `LIVE` 2026-11-11 ("Game Day" below) | - |
| Rosters, Drafts (list below 1100px and the board from 1100px) and Paper Trail (Picks, Players, the sheet with its two-column trade rows), phones and desktop (360P / 402P / 440P / 874L / 956L / 1440; every team, year, order, sort and colour mode, Glossary) | `LIVE` 2026-11-11 ("Pass 3" below) | - |
| Stats, Team Hub | NOT STARTED | medium each (matrices and bars, SVG charts) |

A tab that is NOT STARTED shows whatever the token overrides make of it.

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

## Mechanism ("always-current clone")

- `python3 retro/theme_build.py`: workflow step "Retro tracker theme", directly after "Retro edition",
  `continue-on-error: true`, every mode. `retro/**` is not in the workflow's push paths.
- **Build order:** `retro/build.py` replaces the whole `site/retro/` folder on every run (and removes it when it
  fails), so the theme step must come after it. Loop build fails: `site/retro/` is gone, then this step creates
  `site/retro/tracker/` again, so the tracker is published without the loop. Theme build fails: only
  `site/retro/tracker/` is removed; the loop page and Classic are untouched.
- Reads (never writes): `site/index.html`, `site/p/*`, `site/build.json`, `retro/theme.css`, `retro/theme.js`,
  `retro/wordmark.svg`, `retro/fonts/`. Writes `site/retro/tracker/` only: `index.html`, `p/` (byte-for-byte copies of the chunks),
  `fonts/`, `build.json` (copy). Atomic: built in a temp folder beside the target, then renamed. Any missing input or
  marker: message on stderr, exit 1, and `site/retro/tracker/` does not exist.
- This relaxes hard rule 2 above for this one script: `theme_build.py` reads `site/` (read-only). It edits nothing
  under `pipeline/` and nothing of Classic's.
- **The 8 patches** (the only differences from Classic's `index.html`; each is checked and the build fails if one does
  not apply): (1) `class="retro"` on `<html>`; (2) Classic's Google Fonts link replaced by the self-hosted Martian
  Mono face (`<head>`); (3) the reveal script's four `document.fonts.load()` calls ask for Martian Mono; (4) one
  `noindex` robots meta (Classic already has it); (5) past-season buttons point at Classic's pages (`../../2025/`);
  (6) title gets " · Retro"; (8) the header wordmark: `The <img class="lgs">` (Classic's script art) is replaced by visually hidden text "The League"
  (`.wm-tx`, the h1's accessible name) + the inline `retro/wordmark.svg` (`aria-hidden`), see "Wordmark"; (7) `<style id="retro-theme">` + `<script id="retro-theme-js">` as the last things in
  `<body>`, after every `<style>` of the page including the ones `lazy.py` moves out of the chunks (the build checks
  that the theme is the last `<style>` and that no chunk carries one). After any change to Classic's page shell
  (head, reveal script, year buttons, style order) run the script and check that all eight still apply.
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
   stacked tiles one width and one left edge). Only gold and worst-rank chips carry a 1px ring (as Classic); the
   streak tile is a solid result colour with black figures; empty rank dots have a periwinkle ring.
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
    property written inline on the same element; one layout read for the tiles' left edges; see "Pass 3").
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
The bench strip and Classic's `--pg` strips stay purple.

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

**Chips and tiles (rule 11).** vs / @ tiles: solid, 17px, one cap-trimmed line; "@" (10.7px tall) sits .125em and "vs"
.06em above the cap centre so each is ink-centred. Injury tags: one baseline for Q / O / D / IR placed for the tail of
"Q". FK / FL: 11px, 3.65px / 4.4px paddings. "N on bye": centred on the ink of "b" and "y", pill height as Classic.
HOME / ROAD in the card: Classic's 0.58px side difference taken out through `--ic`. Schedule chips and tiles (sized in
`cqw`) and the schedule's three week columns are rounded to whole pixels. "Week rank N": Classic's chip keeps its box (the fitter's inline `!important`
styles cannot be overridden) but loses fill and ring; its digit is made transparent and the rank is drawn by `::after`
from `data-tx` at the label's 11.5px, on the label's cap band (Classic's fitter leaves the chip 4.43px above it, in
Classic too: the label is a flex item, where a baseline marker is not on the baseline).

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
- Measured from screenshots (`ptm3.py`), {ptm}.

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

## Known issues


- **Rule 11, limits (Game Day).** (1) Rank chips that Classic's tile fitter sizes (`.ch` with inline styles) follow
  Classic's 1.75 to 3.5px window; on these two tabs the only one under 2px was "Week rank", now a figure. (2) A tile at a
  fractional position can show 1 device pixel more on one side (0.33px at 3x); 9 of 64 schedule chips and tiles read 0.67px
  in WebKitGTK at 440P before their `cqw` sizes and the week columns were rounded to whole pixels; 1 of 45 rank chips ("20")
  still does (402P and 1440: none). (3) Headless Chromium places text on
  whole CSS px: its "@" tiles read 1.6 to 4.3px above and 2.3 to 4.3px below depending on the row. (4) Engines without
  `text-box` (before Safari 18.2 / Chrome 133) keep Classic's paddings for vs / @, injury tags, FK / FL and "N on bye".
- **Score cells, limits.** A figure of six characters or more would not keep 3px (none can occur: a player's points).
  On engines where `theme.js` does not run the figure uses a mean bearing (up to 0.65px off centre). The cell's own
  position on the device-pixel grid is not corrected (as rule 7 does for the FAAB and rank tiles): up to 1 device pixel,
  0.33px at 3x. WebKitGTK rounds glyph advances to whole pixels (Safari does not); `theme.js` measures the advance
  once and compensates.
- **Not themed yet, contrast.** The dark-ink audit also lists text under 4.5:1 (3:1 large) on the tabs that are NOT
  STARTED; per tab, worst state at 440P (2026-11-11, after pass 3): Stats 91 (matrix cells 4.3 to 4.4:1), Team Hub 73, Standings 44 (only with the Glossary open: the legend sits on the orange end of the ground, see "Short pages"). Rosters, Drafts, Paper Trail, Matchups, Playoffs,
  Leaderboards, Players, The Wire, Compare 0.
- **Plates meet.** The section plate ends 2px into the Glossary plate's frame and stands flush under the navigation band (Players
  and The Wire since pass 2, the three tabs of pass 3 alike): Classic leaves 16px / 24px there and the plates need 16px / 26px.
- **Hard-coded Classic font metrics.** `SGD` / `SGR` (shotgun tally bearings) are Barlow Condensed / IBM Plex Sans
  values: the mug-to-count and label-to-mug gaps are off by a fraction of a pixel here. `BC7` (Paper Trail digit
  outlines) is Barlow Condensed 700. **Fixed for the Picks tile digits (2026-11-11):** Classic's horizontal offsets are
  switched off (`.ptxn b` inline `left`, `.ptpj b` inline transform) and the digits are centred by `--ix`; WebKitGTK at 3x,
  440P and 402P layouts, counts 1 / 2 / 3 / 4 and injected 10 / 12 / 47: left and right gaps within 0.07px (before: "1" 5.09px
  apart, "2" 1.36px, "3" 1.69px), top and bottom within 0.28px; projected pick numbers within 0.07px including their shadow
  (before up to 2.1px), drafted pick tiles 0.11px (before up to 1.6px). Tile sizes and positions are Classic's.
  **Done in pass 3 (2026-11-11):** the tile width, the two column widths, the heads, the coach names and the NFL slot's edge
  follow Martian Mono's glyph ink ("Pass 3"). Left: `slotFit`'s 12px test and `nameFit` still measure through Classic's canvas
  (a slot is judged up to 3px wider than it is, so a slot can be dropped a little early; none of the 2026 picks' slots is at
  360P / 402P / 440P today), and the
  vertical placement relies on the digits' flat height being .70em, which holds for Martian Mono with `size-adjust`.
- **Streak tile in WebKitGTK:** "L" streaks sit up to 1.6px right of centre (Classic there: 0.6px); "W" streaks are
  fine. Cause: Classic's tile fitter centres by canvas ink, and WebKitGTK's canvas reports the advance box, not the
  ink (CLAUDE.md, Gotchas). Chromium: ≤ 0.5px. Safari unverified.
- **Headless Chromium** places text on whole CSS px, so its FAAB and rank-tile gaps differ by up to 0.8px and 1.5px
  (rule 7 is met in WebKit only). Same limit as DESIGN.md §8 notes for Classic's tiles.
- **Phones' page scale 0.85:** rule 7's grid is 1 / devicePixelRatio CSS px (the engine's own snapping grid); the
  scale is applied to the raster afterwards. Not measurable in the sandbox; real iPhone Safari is checked by Nicklaus.
- **Past-season buttons** open Classic's (unthemed) pages, and those pages' 2026 button returns to Classic.
- **Short pages:** the ground reaches its orange end under free-standing text (e.g. Stats' Glossary label). Fixed on
  Matchups and Playoffs by a plate behind the Glossary switch and text; the other tabs with their own pass.
- A page left open across a deploy uses the copy's own `p/`; old chunks are published only as far as Classic keeps
  them (`DT_CHUNKS`).

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
- Real iPhone Safari is checked by Nicklaus.
- Classic byte-identical before / after `retro/build.py` + `retro/theme_build.py`; `git status` shows only `retro/`
  (plus the documented one-liners).
