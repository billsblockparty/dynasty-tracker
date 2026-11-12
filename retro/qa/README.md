# retro/qa: the audits behind the retro tracker theme's gate

Development tools only. Nothing here is run by the workflow or read by a build step (`retro/build.py` and `retro/theme_build.py`
read named files in `retro/` and never this folder; `retro/**` is not in the workflow's push paths). The rules they check are in
`retro/RETRO.md` (rules 2, 3, 9, 11; "Checks before shipping a change to the theme").

## Set-up

1. Build: `cd pipeline && python3 run.py build` (the Team Hub's Sleeper 403 offline is expected), `python3 retro/build.py`,
   `python3 retro/theme_build.py`.
2. For WebKitGTK: `cp tools/mem/frame.html site/__frame.html && cp tools/mem/frame.html site/retro/tracker/__frame.html`
   (again after every `theme_build.py`: it replaces the folder). The page is loaded in an iframe of the exact width.
3. Serve `site/` over http: `cd site && python3 -m http.server 8830 --bind 127.0.0.1`. Other address: `QA_BASE=http://host:port`.
   For the box comparison serve a copy of `site/retro/tracker/` built from the commit before your change on a second port (8832).
   For `loop.py` serve a folder that holds `build.json` and `retro/index.html` + `retro/data.json` (a copy: `swap` rewrites the two
   json files and restores them).
4. Run from a scratch folder that has `out/` and `s/` (results are written to `./out`): `mkdir -p out s`.
5. Needs Playwright with Chromium, Pillow, numpy; `tools/realfonts.py` (see its header) and `tools/device.py`. Martian Mono comes from
   `retro/fonts/`. WebKitGTK: `webkit2gtk-4.1` MiniBrowser + `WebKitWebDriver` + selenium, an X display `:97`
   (`Xvfb :97 -screen 0 2400x3600x24`; remove a stale `/tmp/.X97-lock` if Xvfb will not start).

Width tokens: `360P 402P 440P 874L 956L` = iPhone emulation (`tools/device.py`; page scale 0.85, so 440P lays out at 518 CSS px and
956L at 1124 = the desktop layout); plain numbers = desktop viewports. WebKitGTK ignores the viewport meta: `eng.py` maps the phone
tokens to the layout widths (360P 424, 402P 473, 440P 518) and uses `GDK_SCALE` 3 (phones) or 2; `darkink.py wk` takes the plain
layout widths (`518 473 1440`). One WebKitGTK run at a time; run them one after another (a width takes 5 to 25 minutes).

## Scripts (engine `ch` = Chromium, `wk` = WebKitGTK; every count must be 0 unless noted)

| Script | Checks | Run |
|---|---|---|
| `darkink.py` | Rule 2 and rule 3 on every tab and state (133 states): each text node's ink, the surface under it (from a screenshot with text off), its shadow / outline. `FAIL` = dark ink with a dark shadow or outline; `low-contrast` = under 4.5:1 (3:1 large) | `darkink.py ch <label> $U 440P 1440`; one tab: `TABS=standings darkink.py ...`; summary `gsum.py out/di-*.json`, detail `sumdi.py -v` |
| `gapf.py` `gapf2.py` `gapf3.py` `gapf4.py` `gapf5.py` | Rule 11 for every framed element holding text (Matchups + Playoffs; pass 2; pass 3; Stats + Team Hub; Standings): ink incl. shadow to the frame, >= 3px beside (equal within 0.5px), >= 2px above / below, from pixels | `gapf5.py ch <label> $U 1440 1100`; one state: `ONLY=...` |
| `chipm.py` `chipm5.py` | The same for rank chips whose tile is a pseudo-element (`.ct::before`), which `gapf` cannot see: Stats + Team Hub; Standings on desktop | `chipm5.py wk $U 1440` |
| `chipph.py` `svgm.py` | Standings rank chips on every layout, both builds (cleanup job 2): drawn chips, chips on their own box (dropped points, week strip with `OPEN=1`), streak tiles, Proj finish tile: ink to tile edge and the nearest ink above / below / beside; `svgm.py` = the season chart's SVG chips | `OPEN=1 chipph.py wk $U after 402P 1440`; `svgm.py ch $U after 402P 1440` |
| `rkm5.py` | The CSS rank tiles of Standings on desktop (table and cards): the same gaps; the digit's centring is printed, not counted | `rkm5.py ch $U 1440` |
| `ptm3.py` | Paper Trail > Picks ink: tile digits, heads, coach names, NFL slot (figures, no pass / fail) | `ptm3.py wk $U 440P` |
| `ovf.py` `ovf2.py` `ovf3.py` `ovf4.py` `ovf5.py` | Against Classic, same states: new clipped text, new ellipsis, more lines, sideways scroll, text smaller than Classic's (same tab split as `gapf`) | `ovf5.py 360P 402P 440P 874L 956L 1100 1240 1440 1920` |
| `boxes.py` (+ `boxes_states.py`) | Every element's box in a tab's states: `dump` writes json, `cmp a.json b.json [-v]` lists what moved or changed size. Proof that a pass moved nothing elsewhere | `boxes.py dump $U 440P matchups out/bx-new --pane`; `boxes.py cmp out/bx-base-matchups-440P.json out/bx-new-matchups-440P.json` |
| `tilechk_r.py` | `tools/tilechk.py`'s own check against the copy over http (`r`) or Classic (`c`) | `tilechk_r.py r 360P 402P 440P 874L 956L 402 440 360 1440` |
| `loop.py` | The loop page: `shots` (six screens after the wipe, no sideways scroll, no page errors), `badge` (8x crop of the TL badge, box, icon links), `swap` (new `data.json` shown with 0 navigations) | `loop.py shots http://127.0.0.1:8834/lsrv out/loop` |
| `icons_png.py` | Not an audit: renders `retro/favicon-16.png` (from `favicon-16.svg`), `favicon-32.png` (from `favicon.svg`) and `favicon-180.png` (then `python3 retro/wordmark_gen.py apply`) | `icons_png.py` |
| `h.py` `eng.py` `mmfont.py` | Harness: fonts, the two engines behind one interface, the text-on / text-off ink scan | imported |

`$U` = `http://127.0.0.1:8830/retro/tracker/index.html`.

## Reading the results

- Headless Chromium places text on whole CSS px with the phones' page scale: left / right balance readings of 0.5 to 0.9px there are
  the engine, not the page (RETRO.md, "Known issues"). WebKitGTK is the reference for rule 11's balance; Chromium for the minimum gaps
  at all widths.
- WebKitGTK rounds glyph advances to whole pixels (Safari does not) and reports boxes for SVG text it does not paint: `PAINT=1
  darkink.py wk ...` leaves unpainted nodes out.
- `ovf5.py` counts the fitter-sized rank chips' digits as "smaller than Classic's" on desktop (10px against 10.25px nominal): Classic's
  tile fitter sizes them from the digits' ink, which is the same height in both (RETRO.md, "Pass 5").
- A run that prints "unstable screenshots" or "page moved during capture" skipped a view: run that width again by itself.
