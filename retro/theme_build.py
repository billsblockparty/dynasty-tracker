#!/usr/bin/env python3
"""Retro tracker theme ("always-current clone"): a themed copy of Classic's BUILT page.

    python3 retro/theme_build.py            (after Classic has built site/, and after retro/build.py)

Reads (never writes): site/index.html, site/p/*, site/build.json, retro/theme.css, retro/theme.js (optional), retro/wordmark.svg,
retro/favicon.html, retro/fonts/.
Writes: site/retro/tracker/ only (index.html, p/, fonts/, build.json), atomically: everything is assembled in a temp directory
next to the target and moved into place at the end. Any missing input or any marker that is not found exactly as
expected: message on stderr, exit 1, and site/retro/tracker/ does not exist (a stale one is removed).

It edits nothing under pipeline/ and nothing of Classic's. The copy differs from Classic's index.html only by the
patches listed in PATCHES below (each one is checked); the chunks and build.json are byte-for-byte copies.
Workflow step "Retro tracker theme" (after "Retro edition", continue-on-error). See retro/RETRO.md, "Tracker theme".
"""
import base64, hashlib, os, re, shutil, struct, sys, tempfile, zlib

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, '..', 'site')
OUT = os.path.join(SITE, 'retro', 'tracker')
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


def build(tmp):
    src = os.path.join(SITE, 'index.html')
    need(os.path.isfile(src), 'missing site/index.html (build Classic first)')
    need(os.path.isfile(os.path.join(SITE, 'build.json')), 'missing site/build.json')
    css_p = os.path.join(HERE, 'theme.css')
    need(os.path.isfile(css_p), 'missing retro/theme.css')
    s = open(src, encoding='utf-8').read()
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
    # 5. past-season buttons: the copy has no past seasons of its own, they are Classic's (two levels up)
    yrs = re.search(r'<nav class="yrs[^"]*"[^>]*>.*?</nav>', s, re.S)
    if yrs:   # (no year strip when there is one season only)
        fixed = re.sub(r'href="(\d{4}/)"', r'href="../../\1"', yrs.group(0))
        s = s.replace(yrs.group(0), fixed, 1)
    # 6. title
    t = re.search(r'<title>(.*?)</title>', s, re.S)
    need(t is not None, 'no <title>')
    s = s.replace(t.group(0), f'<title>{t.group(1).strip()} · Retro</title>', 1)
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
    # 9. favicon (pass 5): the ODL mark in the wordmark's letterforms, the same three self-contained <link> tags as the loop page
    #    (retro/favicon.html, written by "wordmark_gen.py apply" from favicon.svg / favicon-32.png / favicon-180.png). Classic has
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

    os.makedirs(os.path.join(tmp, 'p'))
    os.makedirs(os.path.join(tmp, 'fonts'))
    for f in list(FONT_FILES.values()) + ['OFL.txt']:
        need(os.path.isfile(os.path.join(HERE, 'fonts', f)), f'missing retro/fonts/{f}')
        shutil.copyfile(os.path.join(HERE, 'fonts', f), os.path.join(tmp, 'fonts', f))
    with open(os.path.join(tmp, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(s)
    shutil.copyfile(os.path.join(SITE, 'build.json'), os.path.join(tmp, 'build.json'))   # the refresh pill polls ./build.json
    pd = os.path.join(SITE, 'p')
    names = sorted(os.listdir(pd)) if os.path.isdir(pd) else []
    want = set(re.findall(r'"(p/[\w.-]+\.html)"', s))    # window.LZ manifest
    need(all(os.path.isfile(os.path.join(SITE, w)) for w in want), 'a chunk named in the page is missing from site/p/')
    styled = []
    for nme in names:
        a = os.path.join(pd, nme)
        if not os.path.isfile(a):
            continue
        shutil.copyfile(a, os.path.join(tmp, 'p', nme))
        if b'<style' in re.sub(rb'<script\b.*?</script>', b'', open(a, 'rb').read(), flags=re.S):
            styled.append(nme)
    need(not styled, 'chunks carry their own <style> (would load after the theme): ' + ', '.join(styled[:5]))
    return len(s.encode()), len(names), hashlib.sha256(css.encode()).hexdigest()[:12]


def main():
    tmp = None
    try:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        tmp = tempfile.mkdtemp(prefix='.tracker-', dir=os.path.dirname(OUT))
        size, n, v = build(tmp)
        old = None
        if os.path.exists(OUT):
            old = OUT + '.old'
            shutil.rmtree(old, ignore_errors=True)
            os.rename(OUT, old)
        os.rename(tmp, OUT)
        os.chmod(OUT, 0o755)
        tmp = None
        if old:
            shutil.rmtree(old, ignore_errors=True)
        print(f'retro tracker: wrote site/retro/tracker/ (index.html {size} bytes, {n} chunks, theme {v})')
    except BaseException as e:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(OUT, ignore_errors=True)          # never leave a stale or partial copy
        shutil.rmtree(OUT + '.old', ignore_errors=True)
        if isinstance(e, (KeyboardInterrupt, SystemExit)):
            raise
        print(f'retro tracker: build failed, site/retro/tracker/ not written: {e if isinstance(e, Bad) else repr(e)}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
