"""TeamHub 1.5 extensions: accents, schedule, Monte Carlo odds, week snapshots, live Week strip."""
import json, os, io, math, colorsys, statistics, urllib.request
import numpy as np

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
BG = (0x0f, 0x12, 0x18)
FALLBACK = {8: "#ff7a1a", 3: "#7fa6ff", 1: "#3fd69b", 2: "#f7739c", 4: "#5ec6f4", 5: "#c491ff", 6: "#e8c15a", 7: "#3ddcc1", 9: "#fca95c", 10: "#ff5d73"}
PINNED = {8: "#ff7a1a", 3: "#7fa6ff"}  # Bill's keeps live-site orange, Ram Rod stays blue

def _get(url, raw=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        b = r.read()
    return b if raw else json.loads(b)

# ---------------------------------------------------------------- colour
def _lum(rgb):
    def c(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (c(x) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b
def contrast(a, b=BG):
    la, lb = _lum(a), _lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)
def hx(rgb): return "#%02x%02x%02x" % tuple(int(round(x)) for x in rgb)
def rgb_of(h): return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))

def dominant(img_bytes):
    from PIL import Image
    im = Image.open(io.BytesIO(img_bytes)).convert("RGB").resize((64, 64))
    px = np.asarray(im, dtype=float).reshape(-1, 3) / 255
    hsv = np.array([colorsys.rgb_to_hsv(*p) for p in px])
    keep = (hsv[:, 1] > 0.28) & (hsv[:, 2] > 0.22)
    if keep.sum() < 64 * 64 * 0.04:
        return None, float(keep.mean())
    bins = (hsv[keep, 0] * 24).astype(int) % 24
    w = hsv[keep, 1] * hsv[keep, 2]
    score = np.bincount(bins, weights=w, minlength=24)
    score = score + np.roll(score, 1) * .5 + np.roll(score, -1) * .5
    b = int(score.argmax())
    sel = np.isin(bins, [(b - 1) % 24, b, (b + 1) % 24])
    rgb = (px[keep][sel] * w[sel, None]).sum(0) / w[sel].sum()
    return tuple(rgb * 255), float(keep.mean())

def legible(rgb, target=4.5):
    """Raise lightness/saturation in HLS until contrast vs dark bg >= target (keeps hue)."""
    h, l, s = colorsys.rgb_to_hls(*(x / 255 for x in rgb))
    s = max(s, 0.55)
    l = max(l, 0.45)
    for _ in range(60):
        out = tuple(v * 255 for v in colorsys.hls_to_rgb(h, l, s))
        if contrast(out) >= target: return out
        l = min(0.85, l + 0.01)
    return out

# Hand-picked colour map: Bill's keeps the live-site orange, Ram Rod its blue; the other 8 are spread across hues
# away from both (min CIELAB dE76 between any two = 32). Every colour is >= 6.6:1 on the #0f1218 navy, so it is
# safe for text (4.5:1) as well as chart lines (3:1). accents_from_avatars() is kept for reference only.
ACCENTS = {8: "#ff7a1a", 3: "#7fa6ff", 1: "#e663f0", 2: "#f2d14a", 4: "#a6e35a", 5: "#ff7ab8", 6: "#e9edf3", 7: "#3ccf74", 9: "#c9b48a", 10: "#2fd8d0"}

def accents(teams):
    out = {}
    for rid in teams:
        col = ACCENTS.get(rid, FALLBACK.get(rid, "#7fa6ff"))
        how = "pinned (live-site colour)" if rid in PINNED else ("hand-picked map" if rid in ACCENTS else "fallback")
        out[rid] = dict(accent=col, accent_src=how, contrast=round(contrast(rgb_of(col)), 2))
    return out, {}

def accents_from_avatars(teams, cache):
    os.makedirs(os.path.join(cache, "avatars"), exist_ok=True)
    out, notes = {}, {}
    for rid, t in teams.items():
        src = None
        try:
            p = os.path.join(cache, "avatars", f"{rid}.img")
            if not os.path.exists(p) and t.get("avatar"):
                open(p, "wb").write(_get(t["avatar"], raw=True))
            if os.path.exists(p):
                rgb, frac = dominant(open(p, "rb").read())
                if rgb:
                    src = rgb
        except Exception as e:
            notes[rid] = f"avatar fetch/parse failed: {e}"
        if src is None:
            col = PINNED.get(rid, FALLBACK.get(rid, "#7fa6ff")); how = "fallback (avatar has no dominant colour)"
            raw = None
        else:
            raw = hx(src); col = hx(legible(src)); how = "avatar dominant hue"
        if rid in PINNED:
            col = PINNED[rid]; how = "pinned (live-site colour)" + (f"; avatar hue was {raw}" if raw else "")
        out[rid] = dict(accent=col, accent_src=how, avatar_rgb=raw, contrast=round(contrast(rgb_of(col)), 2))
    return out, notes

# ---------------------------------------------------------------- Monte Carlo
def simulate(rids, played, schedule, reg_end, po_start, po_teams, n=10000, seed=7, pooled_sd=None, score_hist=None):
    """played: rid -> (wins_float, pf) after the last final week.
    schedule: list of (week, a, b) unplayed regular-season games.
    score_hist: rid -> list of weekly scores used for mean/sd (normal model)."""
    rng = np.random.default_rng(seed)
    idx = {r: i for i, r in enumerate(rids)}
    R = len(rids)
    mu = np.array([np.mean(score_hist[r]) for r in rids])
    sd = np.array([(np.std(score_hist[r], ddof=1) if len(score_hist[r]) >= 3 else pooled_sd) for r in rids])
    wins = np.tile(np.array([played[r][0] for r in rids], float), (n, 1))
    pf = np.tile(np.array([played[r][1] for r in rids], float), (n, 1))
    weeks = sorted({w for w, _, _ in schedule})
    for w in weeks:
        s = rng.normal(mu, sd, size=(n, R))
        pf += s
        for ww, a, b in schedule:
            if ww != w: continue
            ia, ib = idx[a], idx[b]
            aw = s[:, ia] > s[:, ib]
            wins[:, ia] += aw; wins[:, ib] += ~aw
    # seeding: wins desc, then PF desc
    key = wins * 1e6 + pf
    order = np.argsort(-key, axis=1)            # (n, R) seeds 1..R
    seeds = order[:, :po_teams]
    playoff = np.zeros(R); bye = np.zeros(R); title = np.zeros(R)
    rows = np.arange(n)
    for k in range(po_teams):
        np.add.at(playoff, seeds[:, k], 1)
    nbye = {6: 2, 4: 0, 8: 0}.get(po_teams, 0)
    for k in range(nbye):
        np.add.at(bye, seeds[:, k], 1)
    def game(a, b):
        sa = rng.normal(mu[a], sd[a]); sb = rng.normal(mu[b], sd[b])
        return np.where(sa > sb, a, b)
    if po_teams == 6:
        w45 = game(seeds[:, 3], seeds[:, 4]); w36 = game(seeds[:, 2], seeds[:, 5])
        f1 = game(seeds[:, 0], w45); f2 = game(seeds[:, 1], w36)
        champ = game(f1, f2)
    elif po_teams == 4:
        champ = game(game(seeds[:, 0], seeds[:, 3]), game(seeds[:, 1], seeds[:, 2]))
    else:
        a = [game(seeds[:, i], seeds[:, po_teams - 1 - i]) for i in range(po_teams // 2)]
        while len(a) > 1: a = [game(a[i], a[len(a) - 1 - i]) for i in range(len(a) // 2)]
        champ = a[0]
    np.add.at(title, champ, 1)
    mean_seed = np.zeros(R)
    for k in range(R): np.add.at(mean_seed, order[:, k], k + 1)
    return {r: dict(title=round(100 * title[idx[r]] / n, 2), bye=round(100 * bye[idx[r]] / n, 2),
                    playoff=round(100 * playoff[idx[r]] / n, 2), seed=round(mean_seed[idx[r]] / n, 2),
                    mu=round(float(mu[idx[r]]), 2), sd=round(float(sd[idx[r]]), 2)) for r in rids}

def norm_cdf(x): return 0.5 * (1 + math.erf(x / math.sqrt(2)))
