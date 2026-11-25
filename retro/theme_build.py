#!/usr/bin/env python3
"""Retro tracker theme ("always-current clone"): BBP's published page = Classic's BUILT page with the DynastyCast theme.

    python3 retro/theme_build.py            (after Classic has built site/, after retro/build.py; re-runnable)

Since 2026-11-24 (brief FR-1) the themed page IS the site: it is written to site/index.html (the root) and uses Classic's
site/p/ and site/build.json in place (no copy). Classic's built index.html is kept outside site/ as a build intermediate,
site-classic/ at the repo root (git-ignored; never published): site-classic/index.html + a symlink to every other entry of
site/, so `python3 -m http.server` in site-classic/ serves Classic with its chunks (tools/tilechk.py, tools/shots.py,
retro/qa h.CL). A run finds Classic in site/index.html when that page is not themed yet (no class="retro" on <html>) and saves
it to site-classic/index.html; when site/index.html is already themed (a second run) it reads the saved site-classic/index.html.

Reads: site/index.html (or site-classic/index.html, see above), site/p/*, site/build.json, retro/theme.css, retro/theme.js
(optional), retro/wordmark.svg, retro/favicon.html, retro/fonts/.
Writes: site/index.html (themed), site/fonts/ (Martian Mono), site/retro/tracker/index.html (a redirect to the root that keeps
location.hash: the old address of the themed copy; retro/build.py replaces the whole site/retro/ folder, so this runs after it),
site-classic/; removes site/DynastyStandings.html (moved to site-classic/: BBP no longer publishes it).
Any missing input or any marker that is not found exactly as expected: message on stderr, exit 1, and nothing under site/ is
changed (site/index.html stays the Classic build, which is NOT fit to publish: the workflow step "Retro tracker theme" has no
continue-on-error and sits before configure-pages / upload / deploy, so the last good deploy stays live). The themed page is
written last, with a temp file + rename.

It edits nothing under pipeline/. The themed page differs from Classic's index.html only by the patches listed in PATCHES below
(each one is checked). See retro/RETRO.md, "Tracker theme".
"""
import base64, hashlib, os, re, shutil, struct, sys, tempfile, zlib

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, '..', 'site')
CLASSIC = os.path.join(HERE, '..', 'site-classic')     # build intermediate: Classic's page (git-ignored, never published)
OLD = os.path.join(SITE, 'retro', 'tracker')            # old address of the themed copy: a redirect to the root
THEMED = '<html lang="en" class="retro">'
# Martian Mono, self-hosted (retro/fonts/, SIL OFL 1.1, the unmodified @fontsource-variable/martian-mono 5.x files:
# axes wdth 75-112.5 and wght 100-800). Declared in <head>, before any script asks document.fonts for it.
#   font-stretch:75%   the face is declared as the condensed width only, so the family IS condensed: Classic's fitters
#                      measure on a canvas with family + weight + size and never pass font-stretch.
#   size-adjust:87.5%  Martian Mono's capitals are .80em (Barlow Condensed / IBM Plex Sans: .70em). Scaling the face
#                      keeps every Classic font size at the cap height it was designed for, in layout AND on canvas.
UR = {'latin': 'U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD',
      'latin-ext': 'U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF'}
FONT_FILES = {k: f'martian-mono-{k}-wdth-normal.woff2' for k in UR}
FONT = ('<link rel="preload" href="fonts/' + FONT_FILES['latin'] + '" as="font" type="font/woff2" crossorigin>\n<style id="retro-font">'
        + ''.join('@font-face{font-family:"Martian Mono";font-style:normal;font-weight:100 800;font-stretch:75%;size-adjust:87.5%;font-display:swap;'
                  f'src:url(fonts/{f}) format("woff2");unicode-range:{UR[k]}}}' for k, f in FONT_FILES.items()) + '</style>')
CLASSIC_FONT = re.compile(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com/css2\?family=Barlow\+Condensed[^"]*">')


class Bad(Exception):
    pass


def need(ok, msg):
    if not ok:
        raise Bad(msg)


def once(s, old, new, what):
    """replace exactly one occurrence, or fail"""
    need(s.count(old) == 1, f'{what}: expected 1 match, found {s.count(old)}')
    return s.replace(old, new, 1)


def grain_png(n=96, seed=1977, amax=40):
    """n x n grain tile as a PNG data URI: black pixels with a random alpha of 0..amax/255, so it can only darken the
    surface it is printed on (contrast of light text never drops). No Pillow needed; fixed seed, reproducible."""
    x = seed
    rows = bytearray()
    for _ in range(n):
        rows.append(0)
        for _ in range(n):
            x = (x * 1103515245 + 12345) & 0x7fffffff
            rows += bytes((0, 0, 0, ((x >> 16) & 0xff) * amax // 255))

    def chunk(t, d):
        c = struct.pack('>I', len(d)) + t + d
        return c + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    png = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', n, n, 8, 6, 0, 0, 0))
           + chunk(b'IDAT', zlib.compress(bytes(rows), 9)) + chunk(b'IEND', b''))
    return 'data:image/png;base64,' + base64.b64encode(png).decode()


def classic_page():
    """Classic's built page: site/index.html while it is not themed yet, else the copy saved by an earlier run"""
    src = os.path.join(SITE, 'index.html')
    need(os.path.isfile(src), 'missing site/index.html (build Classic first)')
    s = open(src, encoding='utf-8').read()
    if THEMED not in s:
        return s, True
    sv = os.path.join(CLASSIC, 'index.html')
    need(os.path.isfile(sv), 'site/index.html is already themed and site-classic/index.html is missing (rebuild Classic)')
    s = open(sv, encoding='utf-8').read()
    need(THEMED not in s, 'site-classic/index.html is themed (rebuild Classic)')
    return s, False


def build(s):
    need(os.path.isfile(os.path.join(SITE, 'build.json')), 'missing site/build.json')
    css_p = os.path.join(HERE, 'theme.css')
    need(os.path.isfile(css_p), 'missing retro/theme.css')
    css = open(css_p, encoding='utf-8').read()
    need('</style' not in css and '<' not in re.sub(r'/\*.*?\*/', '', css, flags=re.S), 'retro/theme.css: "<" outside a comment')
    css = once(css, '/*__GRAIN__*/', f'--grain:url({grain_png()});', 'theme.css grain marker')
    js_p = os.path.join(HERE, 'theme.js')
    js = open(js_p, encoding='utf-8').read() if os.path.isfile(js_p) else ''
    need('</script' not in js, 'retro/theme.js: closing script tag')

    # ---- PATCHES (the only differences between the copy and Classic's index.html) ----
    # 1. marker class on <html>
    s = once(s, '<html lang="en">', '<html lang="en" class="retro">', '<html> tag')
    # 2. fonts: Classic's Google Fonts link is replaced by the self-hosted Martian Mono face (see FONT). The theme
    #    points Classic's --display / --body at it, so Barlow Condensed / IBM Plex Sans are never used in the copy
    #    and the copy makes no request to Google Fonts.
    m = CLASSIC_FONT.findall(s)
    need(len(m) == 1, f'Classic font link: expected 1, found {len(m)}')
    s = s.replace(m[0], FONT, 1)
    # 3. the reveal script waits for the fonts the fitters measure with: same script, Martian Mono instead
    for fam in ('Barlow Condensed', 'IBM Plex Sans'):
        k = f'px "{fam}"\')'
        need(s.count(k) == 2, f'reveal script font loads for {fam}: expected 2, found {s.count(k)}')
        s = s.replace(k, 'px "Martian Mono"\')')
    # 4. robots: Classic already carries noindex; make sure exactly one is there
    n = s.count('<meta name="robots" content="noindex">')
    need(n <= 1, 'more than one robots meta')
    if n == 0:
        s = once(s, '<meta charset="utf-8">', '<meta charset="utf-8">\n<meta name="robots" content="noindex">', 'charset meta')
    # 5. (dropped 2026-11-24, FR-1: at the root Classic's own year-button hrefs are right)
    # 6. (dropped 2026-11-24, FR-1: the title stays Classic's)
    need(re.search(r'<title>(.*?)</title>', s, re.S) is not None, 'no <title>')
    # 8. header wordmark: Classic's bitmap script art ("League") is replaced by the theme's own vector lockup (retro/wordmark.svg,
    #    THE + LEAGUE drawn as paths). The h1 keeps its accessible name as visually hidden text; the svg keeps the class .lgs so
    #    Classic's height rules size it and the header rows stay where they are. Classic's page is not touched.
    wm_p = os.path.join(HERE, 'wordmark.svg')
    need(os.path.isfile(wm_p), 'missing retro/wordmark.svg')
    wm = open(wm_p, encoding='utf-8').read().strip()
    need(wm.startswith('<svg ') and wm.endswith('</svg>') and '<script' not in wm and 'class="lgs wm ' in wm, 'retro/wordmark.svg: not the expected inline svg')
    h1 = re.findall(r'<h1 style="white-space:nowrap">The <img class="lgs"[^>]*></h1>', s)
    need(len(h1) == 1, f'header title with the League art: expected 1, found {len(h1)}')
    s = s.replace(h1[0], '<h1 style="white-space:nowrap"><span class="wm-tx">The League</span>' + wm + '</h1>', 1)
    # 9. favicon (pass 5; TL since 2026-11-12, cleanup job 1): the TL mark, the same three self-contained <link> tags as the loop page
    #    (retro/favicon.html, written by "wordmark_gen.py apply" from favicon-16.png / favicon-32.png / favicon-180.png). Classic has
    #    no icon; if it gains one, its links are dropped from the copy so exactly the theme's three remain.
    ic_p = os.path.join(HERE, 'favicon.html')
    need(os.path.isfile(ic_p), 'missing retro/favicon.html')
    ic = open(ic_p, encoding='utf-8').read().strip()
    ICON = r'<link\b[^>]*\brel="(?:shortcut icon|icon|apple-touch-icon|mask-icon)"[^>]*>'
    need(len(re.findall(ICON, ic)) == 3 and re.sub(ICON, '', ic).strip() == '' and 'http' not in ic, 'retro/favicon.html: expected exactly three self-contained icon links')
    s = re.sub(ICON + r'\n?', '', s)
    s = once(s, '<meta charset="utf-8">', '<meta charset="utf-8">\n' + ic, 'charset meta (favicon)')
    need(len(re.findall(ICON, s)) == 3, 'favicon: expected exactly three icon links in the copy')
    # 7. the theme, last in the document: after every <style> of the page, including the chunk styles lazy.py moves
    #    to just after the last pane (the chunks themselves carry no <style>: checked below)
    need(s.count('</body>') == 1, '</body>: expected 1')
    tail = f'<style id="retro-theme">\n{css}\n</style>\n' + (f'<script id="retro-theme-js">\n{js}\n</script>\n' if js.strip() else '')
    s = s.replace('</body>', tail + '</body>', 1)
    last_style = [m.start() for m in re.finditer(r'<style\b', s)][-1]
    need(s[last_style:].startswith('<style id="retro-theme">'), 'the theme is not the last <style> in the document')

    for f in list(FONT_FILES.values()) + ['OFL.txt']:
        need(os.path.isfile(os.path.join(HERE, 'fonts', f)), f'missing retro/fonts/{f}')
    pd = os.path.join(SITE, 'p')
    names = sorted(os.listdir(pd)) if os.path.isdir(pd) else []
    want = set(re.findall(r'"(p/[\w.-]+\.html)"', s))    # window.LZ manifest
    need(all(os.path.isfile(os.path.join(SITE, w)) for w in want), 'a chunk named in the page is missing from site/p/')
    styled = []
    for nme in names:
        a = os.path.join(pd, nme)
        if os.path.isfile(a) and b'<style' in re.sub(rb'<script\b.*?</script>', b'', open(a, 'rb').read(), flags=re.S):
            styled.append(nme)
    need(not styled, 'chunks carry their own <style> (would load after the theme): ' + ', '.join(styled[:5]))
    return s, len(names), hashlib.sha256(css.encode()).hexdigest()[:12]


# the old address /retro/tracker/ (2026-11-09 .. 2026-11-24): same hash, at the root. Page colour = the theme's --purple.
REDIRECT = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">\n<meta name="robots" content="noindex">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1">\n<title>The League</title>\n'
            '<script>location.replace("../../"+location.hash)</script>\n'
            '<noscript><meta http-equiv="refresh" content="0;url=../../"></noscript>\n'
            '<style>html,body{background:#332370;color:#fff}</style>\n</head><body><p><a href="../../" style="color:inherit">The League</a></p></body></html>\n')


def write_atomic(path, data, mode='w'):
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    fd, tp = tempfile.mkstemp(prefix='.tmp-', dir=d)
    try:
        with os.fdopen(fd, mode, **({'encoding': 'utf-8'} if 'b' not in mode else {})) as f:
            f.write(data)
        os.chmod(tp, 0o644)
        os.replace(tp, path)
    except BaseException:
        if os.path.exists(tp):
            os.remove(tp)
        raise


def publish(s, classic, fresh):
    """everything is checked; write the outputs, the themed root page last"""
    os.makedirs(CLASSIC, exist_ok=True)
    if fresh:
        write_atomic(os.path.join(CLASSIC, 'index.html'), classic)
    # Martian Mono: site/fonts/ (assembled beside it, then renamed)
    fd = os.path.join(SITE, 'fonts')
    tmp = tempfile.mkdtemp(prefix='.fonts-', dir=SITE)
    try:
        for f in list(FONT_FILES.values()) + ['OFL.txt']:
            shutil.copyfile(os.path.join(HERE, 'fonts', f), os.path.join(tmp, f))
        os.chmod(tmp, 0o755)
        if os.path.isdir(fd):
            shutil.rmtree(fd)
        os.rename(tmp, fd)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    # the old address
    shutil.rmtree(OLD, ignore_errors=True)
    write_atomic(os.path.join(OLD, 'index.html'), REDIRECT)
    # DynastyStandings.html: BBP no longer publishes it (pipeline/build_site.py still writes it; kept beside Classic)
    ds = os.path.join(SITE, 'DynastyStandings.html')
    if os.path.isfile(ds):
        os.replace(ds, os.path.join(CLASSIC, 'DynastyStandings.html'))
    # site-classic/: a symlink to every other entry of site/ (QA serves Classic from there over http)
    for n in os.listdir(CLASSIC):
        q = os.path.join(CLASSIC, n)
        if os.path.islink(q):
            os.remove(q)
    for n in sorted(os.listdir(SITE)):
        if n in ('index.html', 'DynastyStandings.html') or n.startswith('.'):
            continue
        if not os.path.exists(os.path.join(CLASSIC, n)):
            os.symlink(os.path.join('..', 'site', n), os.path.join(CLASSIC, n))
    write_atomic(os.path.join(SITE, 'index.html'), s)


def main():
    try:
        classic, fresh = classic_page()
        s, n, v = build(classic)
        publish(s, classic, fresh)
        print(f'retro tracker: wrote site/index.html ({len(s.encode())} bytes, {n} chunks, theme {v}); Classic in site-classic/ '
              f'({"saved from this build" if fresh else "kept from the earlier run"}); site/retro/tracker/ = redirect')
    except BaseException as e:
        if isinstance(e, (KeyboardInterrupt, SystemExit)):
            raise
        print(f'retro tracker: build failed, site/index.html not themed (not fit to publish): {e if isinstance(e, Bad) else repr(e)}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
