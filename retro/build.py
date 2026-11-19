#!/usr/bin/env python3
# Retro edition ("DynastyCast"): python3 retro/build.py  ->  site/retro/index.html + site/retro/data.json
# Reads pipeline/ files as text/JSON only (never imports or runs a pipeline script) and writes only site/retro/.
# The page is built in a temp directory and moved into place only when everything succeeded; on any missing or
# malformed input this exits non-zero and site/retro/ does not exist. Design notes: retro/RETRO.md.
import ast, base64, hashlib, io, json, os, re, shutil, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
P = os.path.join(ROOT, 'pipeline')
OUT = os.path.join(ROOT, 'site', 'retro')
MARK = '/*__RETRO_DATA__*/'
ICON = 20  # px, the source size of a team picture (shown pixelated)


class Bad(Exception):
    pass


def need(cond, msg):
    if not cond:
        raise Bad(msg)


def text(rel):
    p = os.path.join(P, rel)
    need(os.path.isfile(p), f'missing input: pipeline/{rel}')
    return open(p, encoding='utf-8').read()


def load(rel):
    try:
        return json.loads(text(rel))
    except ValueError as e:
        raise Bad(f'pipeline/{rel} is not valid JSON: {e}')


def js_consts(src, names):
    """`const NAME=<JSON>;` values of data_block.js, parsed as JSON (the file is never executed)."""
    out, dec = {}, json.JSONDecoder()
    for n in names:
        m = re.search(r'^const ' + n + r'=', src, re.M)
        need(m, f'data_block.js: const {n} not found')
        try:
            out[n] = dec.raw_decode(src, m.end())[0]
        except ValueError as e:
            raise Bad(f'data_block.js: const {n} is not JSON: {e}')
    return out


def num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def build():
    # ---------- season data (data_block.js)
    d = js_consts(text('data_block.js'), ['G', 'T', 'H', 'PH', 'WK', 'FUT'])
    G, T, H, PH, WK, FUT = (d[k] for k in ('G', 'T', 'H', 'PH', 'WK', 'FUT'))
    need(isinstance(G, int) and G >= 1, 'G is not a week number')
    need(isinstance(T, dict) and len(T) >= 2, 'T is empty')
    teams = list(T)
    for t, v in T.items():
        need(isinstance(v, list) and len(v) >= 13 and all(num(x) for x in v[:13]), f'T[{t}]: expected 13 numbers')
    for nme, order in (('H', H), ('PH', PH)):
        need(isinstance(order, list) and sorted(order) == sorted(teams), f'{nme} is not an ordering of the teams in T')
    need(isinstance(WK, dict) and sorted(WK) == sorted(teams), 'WK teams differ from T')
    need(isinstance(FUT, dict), 'FUT is not an object')

    # ---------- team ids, pictures, short names (existing maps only, read as text)
    tj = load('history/teams.json')
    need(isinstance(tj.get('sleeper_roster'), dict), 'history/teams.json: sleeper_roster missing')
    rid_of = {}
    for rid, name in tj['sleeper_roster'].items():
        rid_of[name] = int(rid)
    need(all(t in rid_of for t in teams), 'history/teams.json: a team in T has no roster id')

    m = re.search(r'^const FN=(\{.*?\})', text('new_tail.js'), re.M)
    need(m, 'new_tail.js: const FN not found')
    try:
        FN = json.loads(m.group(1))
    except ValueError as e:
        raise Bad(f'new_tail.js: FN is not JSON: {e}')
    m = re.search(r'^SH=(\{.*?\})', text('full_update.py'), re.M)
    need(m, 'full_update.py: SH not found')
    try:
        SH = ast.literal_eval(m.group(1))  # a literal, evaluated as data; nothing is imported or run
    except (ValueError, SyntaxError) as e:
        raise Bad(f'full_update.py: SH is not a literal dict: {e}')
    need(isinstance(FN, dict) and isinstance(SH, dict), 'FN / SH are not maps')

    def full(n):  # a schedule name (short or full) -> full team name, as the page's fn() does
        f = FN.get(n, n)
        need(f in T, f'unknown team name in schedule: {n!r}')
        return f

    # short form: the first FN key that names the team (file order); teams FN does not list take SH[roster id]
    short = {}
    for t in teams:
        keys = [k for k, v in FN.items() if v == t]
        s = keys[0] if keys else SH.get(rid_of[t])
        need(isinstance(s, str) and s, f'no short name for {t}')
        short[t] = s

    try:
        from PIL import Image
    except ImportError:
        raise Bad('Pillow is not installed (needed to shrink the team pictures)')
    av = {}
    for t in teams:
        p = os.path.join(P, 'avatars', f'{rid_of[t]}.webp')
        need(os.path.isfile(p), f'missing input: pipeline/avatars/{rid_of[t]}.webp')
        try:
            im = Image.open(p).convert('RGB').resize((ICON, ICON), Image.BILINEAR)
        except Exception as e:
            raise Bad(f'pipeline/avatars/{rid_of[t]}.webp unreadable: {e}')
        b = io.BytesIO()
        im.save(b, 'PNG', optimize=True)
        av[t] = 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()

    # ---------- 1 standings (H2H order = H; mv = places moved since last week, from PH)
    stand = [{'t': t, 's': short[t], 'w': T[t][0], 'l': T[t][1], 'pf': T[t][3], 'pa': T[t][6],
              'ap': f'{T[t][10]}-{T[t][11]}', 'luck': T[t][12], 'mv': PH.index(t) - i} for i, t in enumerate(H)]

    # ---------- 4 last week's results (WK), winner first, highest winning score first
    games, seen = [], set()
    for t in H:
        rows = [r for r in WK[t] if isinstance(r, list) and len(r) >= 4 and r[0] == G]
        need(len(rows) == 1 and num(rows[0][2]) and num(rows[0][3]), f'WK[{t}]: no single week {G} row')
        o = full(rows[0][1])
        if t in seen:
            continue
        need(o not in seen and o != t, f'WK week {G}: {t} / {o} pairing is inconsistent')
        seen.update((t, o))
        a, b, sa, sb = (t, o, rows[0][2], rows[0][3]) if rows[0][2] >= rows[0][3] else (o, t, rows[0][3], rows[0][2])
        games.append({'a': a, 'b': b, 'sa': sa, 'sb': sb})
    games.sort(key=lambda g: -g['sa'])

    # ---------- 5 almanac (T and WK); ties go to the higher seed
    allw = [(r[2], t, r[0]) for t in H for r in WK[t] if isinstance(r, list) and len(r) >= 4 and num(r[2]) and r[0] <= G]
    need(allw, 'WK has no played weeks')
    hi = max(allw, key=lambda x: x[0])
    lo = min(allw, key=lambda x: x[0])
    top = lambda i: max(H, key=lambda t: T[t][i])
    pf, pa, apb, lk, ul = top(3), top(6), top(10), top(12), min(H, key=lambda t: T[t][12])
    alm = {'hi': {'v': hi[0], 't': hi[1], 'w': hi[2]}, 'lo': {'v': lo[0], 't': lo[1], 'w': lo[2]},
           'pf': [T[pf][3], pf], 'pa': [T[pa][6], pa], 'lk': [T[lk][12], lk], 'ul': [T[ul][12], ul],
           'apb': [T[apb][10], apb, f'{T[apb][10]}-{T[apb][11]}']}

    # ---------- 6 champions
    ch = load('champions.json')
    need(isinstance(ch, dict) and ch, 'champions.json is empty')
    for y, t in ch.items():
        need(re.fullmatch(r'\d{4}', str(y)) and t in T, f'champions.json: {y}: {t!r} is not a current team name')
    champs = {y: ch[y] for y in sorted(ch)}

    # ---------- 2 + 3 current week (wk{G+1}.json + FUT). No file (after the last regular-season week): both screens are skipped
    mus, state = None, None
    wp = os.path.join(P, f'wk{G + 1}.json')
    if os.path.isfile(wp):
        wk = load(f'wk{G + 1}.json')
        need(isinstance(wk, dict) and isinstance(wk.get('out'), dict), f'wk{G + 1}.json: out missing')
        name_of = {v: k for k, v in rid_of.items()}
        by = {}
        for rid, o in wk['out'].items():
            need(isinstance(o, dict) and num(o.get('pts')) and 'mid' in o and rid.isdigit() and int(rid) in name_of,
                 f'wk{G + 1}.json: out[{rid}] malformed')
            by.setdefault(o['mid'], []).append((name_of[int(rid)], o['pts']))
        need(sum(len(v) for v in by.values()) == len(teams), f'wk{G + 1}.json: not every team has a row')
        fut = {}
        for t in teams:
            r = [x for x in FUT.get(t, []) if isinstance(x, list) and len(x) >= 5 and x[0] == G + 1]
            need(len(r) == 1 and all(num(x) for x in r[0][2:5]), f'FUT[{t}]: no single week {G + 1} row')
            fut[t] = (full(r[0][1]), r[0][2], r[0][4])
        mus = []
        for mid in sorted(by, key=lambda x: (not num(x), x)):
            pr = by[mid]
            need(len(pr) == 2, f'wk{G + 1}.json: matchup {mid} does not have two teams')
            need(fut[pr[0][0]][0] == pr[1][0] and fut[pr[1][0]][0] == pr[0][0],
                 f'wk{G + 1}.json and FUT disagree on who plays {pr[0][0]}')
            pr.sort(key=lambda x: (-fut[x[0]][2], -fut[x[0]][1], H.index(x[0])))  # favourite first
            (a, ap), (b, bp) = pr
            mus.append({'a': a, 'b': b, 'ap': ap, 'bp': bp, 'aj': fut[a][1], 'bj': fut[b][1], 'wa': fut[a][2], 'wb': fut[b][2]})
        # state of the week, from the week file's own fields: done = NFL teams whose game is final, live = NFL teams
        # playing now, home = the week's home teams (one per game, so 2 x len(home) teams play this week)
        done, playing, home = (wk.get(k) or [] for k in ('done', 'live', 'home'))
        need(all(isinstance(x, list) for x in (done, playing, home)), f'wk{G + 1}.json: done / live / home are not lists')
        if home and not playing and set(home) <= set(done) and len(set(done)) >= 2 * len(set(home)):
            state = 'final'   # every game of the week is finished
        elif done or playing or any(m['ap'] or m['bp'] for m in mus):
            state = 'live'    # at least one game has started
        else:
            state = 'pre'     # nothing has started

    D = {'G': G, 'wk': state, 'stand': stand, 'mus': mus, 'res': games, 'alm': alm, 'champs': champs, 'av': av, 'sh': short}
    dump = lambda o: json.dumps(o, ensure_ascii=False, separators=(',', ':'))
    # v: version of the data (a hash of it; build.py reads nothing outside pipeline/, so it is not Classic's build.json v)
    D = {'v': hashlib.sha256(dump(D).encode()).hexdigest()[:12], **D}
    tp = os.path.join(HERE, 'template.html')
    need(os.path.isfile(tp), 'missing retro/template.html')
    tpl = open(tp, encoding='utf-8').read()
    need(tpl.count(MARK) == 1, 'retro/template.html: data marker missing')
    tv = hashlib.sha256(tpl.encode()).hexdigest()[:12]  # template version: a page built from another template reloads
    js = dump(D).replace('</', '<\\/').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    html = tpl.replace(MARK, f'const TV="{tv}";let D={js};')
    return html, dump({'tv': tv, **D}), D


def main():
    tmp = None
    try:
        html, data, D = build()
        tmp = tempfile.mkdtemp(prefix='retro-')
        with open(os.path.join(tmp, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html)
        with open(os.path.join(tmp, 'data.json'), 'w', encoding='utf-8') as f:  # same data as the page, for in-place updates
            f.write(data)
        shutil.rmtree(OUT, ignore_errors=True)
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        shutil.move(tmp, OUT)
        os.chmod(OUT, 0o755)
        tmp = None
        print(f'retro: wrote site/retro/index.html + data.json ({len(html.encode())} + {len(data.encode())} bytes; week {D["G"]}, '
              f'{"screens 2-3 skipped (no wk%d.json)" % (D["G"] + 1) if D["mus"] is None else D["wk"]}, v {D["v"]})')
    except BaseException as e:
        shutil.rmtree(OUT, ignore_errors=True)  # never leave a stale or partial page
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)
        if isinstance(e, (KeyboardInterrupt, SystemExit)):
            raise
        print(f'retro: build failed, site/retro/ not written: {e if isinstance(e, Bad) else repr(e)}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
