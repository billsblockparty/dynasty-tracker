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
| Leaderboards, Players, The Wire, Compare | NOT STARTED | small each (token-driven tables and pills) |
| Stats, Rosters, Team Hub, Playoffs, Drafts list | NOT STARTED | medium each (pastel pills with dark text, matrices and bars, SVG charts, bracket and schedule cells) |
| Matchups | NOT STARTED, except the lineup score cells (rule 11, 2026-11-10; also in Playoffs lineups) | large (cards fall to black, win-probability bars, live states) |
| Paper Trail | NOT STARTED | large (`BC7` digit outlines and `tileSnap` are Barlow-specific) |
| Drafts desktop board | NOT STARTED | large (pastel position cells) |

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

## Mechanism ("always-current clone")

- `python3 retro/theme_build.py`: workflow step "Retro tracker theme", directly after "Retro edition",
  `continue-on-error: true`, every mode. `retro/**` is not in the workflow's push paths.
- **Build order:** `retro/build.py` replaces the whole `site/retro/` folder on every run (and removes it when it
  fails), so the theme step must come after it. Loop build fails: `site/retro/` is gone, then this step creates
  `site/retro/tracker/` again, so the tracker is published without the loop. Theme build fails: only
  `site/retro/tracker/` is removed; the loop page and Classic are untouched.
- Reads (never writes): `site/index.html`, `site/p/*`, `site/build.json`, `retro/theme.css`, `retro/theme.js`,
  `retro/fonts/`. Writes `site/retro/tracker/` only: `index.html`, `p/` (byte-for-byte copies of the chunks),
  `fonts/`, `build.json` (copy). Atomic: built in a temp folder beside the target, then renamed. Any missing input or
  marker: message on stderr, exit 1, and `site/retro/tracker/` does not exist.
- This relaxes hard rule 2 above for this one script: `theme_build.py` reads `site/` (read-only). It edits nothing
  under `pipeline/` and nothing of Classic's.
- **The 7 patches** (the only differences from Classic's `index.html`; each is checked and the build fails if one does
  not apply): (1) `class="retro"` on `<html>`; (2) Classic's Google Fonts link replaced by the self-hosted Martian
  Mono face (`<head>`); (3) the reveal script's four `document.fonts.load()` calls ask for Martian Mono; (4) one
  `noindex` robots meta (Classic already has it); (5) past-season buttons point at Classic's pages (`../../2025/`);
  (6) title gets " · Retro"; (7) `<style id="retro-theme">` + `<script id="retro-theme-js">` as the last things in
  `<body>`, after every `<style>` of the page including the ones `lazy.py` moves out of the chunks (the build checks
  that the theme is the last `<style>` and that no chunk carries one). After any change to Classic's page shell
  (head, reveal script, year buttons, style order) run the script and check that all seven still apply.
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
     off themselves (block "dark-ink rule, layer 2" at the end of theme.css; today the dropdown menus `.ddm`).
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
    text alone, no layout reads, at load and for nodes added later (`MutationObserver`).
11. **Text never touches a frame (2026-11-10).** Inside any framed cell or tile, the visible ink INCLUDING its shadow
    or outline keeps at least 3 CSS px from the inner edge of the frame on the left and right, the left and right
    gaps equal within 0.5px (ink-centred), and at least 2px top and bottom, at every width. Measured from
    screenshots (text switched off and on, the difference is the ink), not from layout boxes.
    Done for the **lineup score cells** (Matchups and Playoffs lineups, `.cr.lu .cv .fs`: delta, points figure,
    FINAL / LIVE / PROJ). The cell is Classic's (38px, 36px inside its frame lines) and Martian Mono is monospaced
    (the decimal point takes a full .525em), so the figure is 14.5px instead of Classic's 18.375px: the widest
    four-character figure is 27.7px of ink + 1px of shadow. A lineup that holds a five-character figure ("100.0",
    "-10.4") shows every figure at 11.5px (`fs5`): one size per lineup, never per cell. The label's tracking is 0.
    Ink centring by `text-indent` (half of it moves the line): figure from the first and last glyph's bearings
    (theme.js), delta and label by constants per state. Not chosen: tighter tracking (at -.05em the bearings of "00"
    already leave 0.01px, and keeping 18.375px would need -.16em; the face has no narrower width than 75 and no
    proportional figures) and wider cells (44px instead of 38px would keep 18.375px, but takes 6px from each name
    column and moves every name and logo beside them).
    Every other framed element on Matchups is listed, not fixed, under Known issues.

## Known issues

- **Rule 11 is met by the lineup score cells only.** Other framed elements on Matchups whose ink (with shadow) comes
  within 2px of the frame, measured 2026-11-10 (440P and 1920; to do with that tab): road "@" tiles `.gha.ht.r` (23 in a final week, 14 in a projected one: 0.5 to 1.3px above the glyph, 1.2 to 2.0px
  below), home "vs" tiles `.gha.ht.h` (1 of 12: 1.96px above), FK / FL chips `.flg` (7: 1.0 to 1.7px above),
  matchup-card rank chips `.hrk .ch` (2: 0.4 to 1.6px above and below), injury tags `.inj` Q / O (2: 1.5px above),
  "N on bye" chips `.mby` (3: 0.8 to 1.5px below), card streak tiles `.gb .stk` at 1920 only (up to 4 of 10 read 0px
  to the right or below: check when theming), the open week menu's own row `.ddm label` (0px left). All of these are
  top / bottom except the last two; left and right are >= 2.3px everywhere else. Position tiles `.pq`, the toggles and
  the score cells have every gap >= 2px.
- **Score cells, limits.** A figure of six characters or more would not keep 3px (none can occur: a player's points).
  On engines where `theme.js` does not run the figure uses a mean bearing (up to 0.65px off centre). The cell's own
  position on the device-pixel grid is not corrected (as rule 7 does for the FAAB and rank tiles): up to 1 device pixel,
  0.33px at 3x. WebKitGTK rounds glyph advances to whole pixels (Safari does not); `theme.js` measures the advance
  once and compensates.
- **Not themed yet, contrast.** The dark-ink audit also lists text under 4.5:1 (3:1 large) on the tabs that are NOT
  STARTED: per tab, worst state at 440P: Players 123 (past bye
  weeks `.by.past` #4b5262 on `--blue-2` 1.34:1, age flags, team-colour position tiles), Stats 91 (matrix cells
  4.3 to 4.4:1), Playoffs 75 (schedule view chips and times 1.9 to 2.4:1, projected figures 3.08:1), Matchups 58
  (projected figures `.fs.pj` #8f98ab 3.08:1, delta 4.11:1, REC label 4.12:1, FL chip 3.81:1), Team Hub 53, Standings
  45 (only with the Glossary open: the legend sits on the orange end of the ground, see "Short pages"), Rosters 43,
  Compare 41, Paper Trail 27, The Wire 4, Drafts 0, Leaderboards 0. Light ink on a light surface: the dropdown menus
  `.ddm` (white panel; `--peri-lt` rank figures 1.7:1 and the yellow selected name 1.06:1), Compare and Playoffs.
- **Hard-coded Classic font metrics.** `SGD` / `SGR` (shotgun tally bearings) are Barlow Condensed / IBM Plex Sans
  values: the mug-to-count and label-to-mug gaps are off by a fraction of a pixel here. `BC7` (Paper Trail digit
  outlines) is Barlow Condensed 700: Paper Trail's TIMES TRADED tiles will be wrong until that tab is themed.
- **Streak tile in WebKitGTK:** "L" streaks sit up to 1.6px right of centre (Classic there: 0.6px); "W" streaks are
  fine. Cause: Classic's tile fitter centres by canvas ink, and WebKitGTK's canvas reports the advance box, not the
  ink (CLAUDE.md, Gotchas). Chromium: ≤ 0.5px. Safari unverified.
- **Headless Chromium** places text on whole CSS px, so its FAAB and rank-tile gaps differ by up to 0.8px and 1.5px
  (rule 7 is met in WebKit only). Same limit as DESIGN.md §8 notes for Classic's tiles.
- **Phones' page scale 0.85:** rule 7's grid is 1 / devicePixelRatio CSS px (the engine's own snapping grid); the
  scale is applied to the raster afterwards. Not measurable in the sandbox; real iPhone Safari is checked by Nicklaus.
- **Past-season buttons** open Classic's (unthemed) pages, and those pages' 2026 button returns to Classic.
- **Short pages:** the ground reaches its orange end under free-standing text (e.g. Stats' Glossary label). Fix with
  that tab.
- **Header title art** ("League") is Classic's bitmap.
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
- Real iPhone Safari is checked by Nicklaus.
- Classic byte-identical before / after `retro/build.py` + `retro/theme_build.py`; `git status` shows only `retro/`
  (plus the documented one-liners).
