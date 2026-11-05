// TEMPORARY (2026-11-05, Nicklaus): Safari memory test pages at site/debug/mem/. Remove this file and its line in run.py
// once the Safari figures are in (DESIGN.md §8). BBP only. Never fatal for the build.
// Builds variants of the freshly built site/index.html, each with one thing removed, so Safari's memory can be read per
// variant in Activity Monitor. Same variants as the WebKitGTK bisect of 2026-11-04 (tools/mem/README.md).
// Needs Playwright + Chromium (CI installs them) only to find which CSS rules the Standings page uses (variant b).
const fs = require('fs'), path = require('path');
const OUT = path.resolve(__dirname, '..', 'site'), DIR = path.join(OUT, 'debug', 'mem');
const S = fs.readFileSync(path.join(OUT, 'index.html'), 'utf8');
const STYLE = /(<style[^>]*>)([\s\S]*?)(<\/style>)/g;
const esc = t => t.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

// rules of each <style> block, with: used on the Standings page (402 or 1440), is a cleanup override (body * / :not(#z))
const RULES_JS = `()=>{const DYN=/::?(-webkit-[a-z-]+|before|after|placeholder|selection|marker|first-line|first-letter|backdrop|hover|focus-visible|focus-within|focus|active|visited|link|target|disabled|enabled|checked|indeterminate|default|placeholder-shown|autofill|invalid|valid|empty|scrollbar[a-z-]*)(\\([^)]*\\))?/g;
 const used=sel=>{for(const part of sel.split(/,(?![^(]*\\))/)){let s=part.replace(DYN,'').trim();if(!s||/^[>+~]/.test(s)||/[>+~]$/.test(s))s=s.replace(/[>+~]\\s*$/,'')||'*';try{if(document.querySelector(s))return true}catch(e){return true}}return false};
 const walk=r=>{if(r.type===1)return used(r.selectorText);if(r.cssRules){for(const x of r.cssRules)if(walk(x))return true;return false}return true};
 const ov=r=>r.type===1&&(/body \\*/.test(r.selectorText)||/:not\\(#z\\)/.test(r.selectorText));
 return [...document.querySelectorAll('style')].map(st=>[...st.sheet.cssRules].map(r=>({t:r.cssText,u:walk(r),o:ov(r)})))}`;

async function sheets() {
  const { chromium } = require('playwright');
  const b = await chromium.launch(); let all = null;
  try {
    for (const w of [402, 1440]) {
      const pg = await b.newPage({ viewport: { width: w, height: 1000 } });
      await pg.goto('file://' + path.join(OUT, 'index.html')); await pg.waitForTimeout(2500);
      const sh = await pg.evaluate(`(${RULES_JS})()`); await pg.close(); if (!Array.isArray(sh)) throw new Error("no rule list");
      if (!all) all = sh; else all.forEach((a, i) => a.forEach((x, j) => { x.u = x.u || sh[i][j].u }));
    }
  } finally { await b.close() }
  return all;
}

function cssVariant(SH, keep) { let i = -1; return S.replace(STYLE, (m, a, body, c) => { i++; return a + SH[i].map(keep).filter(Boolean).join('\n') + c }) }
function emptyTag(s, openRe) {  // remove the contents of the first element matching openRe (balanced on its tag name)
  const m = openRe.exec(s); if (!m) throw new Error('not found: ' + openRe);
  const name = /^<(\w+)/.exec(m[0])[1], start = m.index + m[0].length, re = new RegExp(`<(/?)${name}\\b[^>]*>`, 'g');
  re.lastIndex = start; let d = 1, t;
  while ((t = re.exec(s))) { d += t[1] ? -1 : 1; if (!d) return s.slice(0, start) + s.slice(t.index) }
  throw new Error('unbalanced ' + openRe);
}
function noop(s, names) { for (const n of names) { const re = new RegExp(`(\\bfunction ${n}\\s*\\([^)]*\\)\\s*\\{)`, 'g'); if (!re.test(s)) throw new Error('no function ' + n); s = s.replace(re, '$1return;') } return s }
const TINY = { 'image/webp': 'UklGRhoAAABXRUJQVlA4TA0AAAAvAAAAEAcQERGIiP4HAA==', 'image/png': 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=' };
const DU = /data:([a-z/+]+);base64,[A-Za-z0-9+/=]+/g, tiny = (m, t) => 'data:' + t + ';base64,' + (TINY[t] || TINY['image/png']);
const FIT = ['fit', 'inkTile', 'tnFit', 'mvAl', 'sbFit', 's2Fit', 'rrFit', 'nrdFit', 'rniSnap', 'finFit', 'simGap', 'pfit', 'tabFit', 'ddFit', 'subFit', 'pcnFit', 'rslFit', 'ravFit'];

(async () => {
  let SH = null; try { SH = await sheets() } catch (e) { console.log('memdebug: CSS usage not available (' + e.message.split('\n')[0] + '); variant b skipped') }
  const big = [...S.matchAll(/<script>([\s\S]*?)<\/script>/g)].sort((x, y) => y[1].length - x[1].length)[0];
  const nRules = SH ? SH.flat().length : 0, nUnused = SH ? SH.flat().filter(r => !r.u).length : 0;
  const V = [
    ['blank', 'Blank page', "Safari's own cost for one tab. Subtract it from the others.", null],
    ['full', 'Full page', 'The Standings page as it is live.', S],
    ['a-nocss', 'a) All CSS removed', 'Every <style> block emptied.', S.replace(STYLE, (m, a, b, c) => a + c)],
    ['b-unusedcss', 'b) CSS not used on Standings removed', SH ? `${nUnused} of ${nRules} rules removed (they match nothing on the loaded Standings page).` : 'Not built: Chromium was not available.', SH ? cssVariant(SH, r => r.u ? r.t : null) : null],
    ['b0-csscontrol', 'b/c control: CSS rewritten, nothing removed', 'Variants b and c rewrite the CSS through the browser; this one does the same and removes nothing.', SH ? cssVariant(SH, r => r.t) : null],
    ['c-overrides', 'c) Cleanup override rules removed', 'The body * border rule and the :not(#z) data-bar rules.', SH ? cssVariant(SH, r => (r.o && !r.t.startsWith('@')) ? null : r.t) : null],
    ['d-nofonts', 'd) Web fonts removed', 'Google Fonts link removed: system fonts instead.', S.replace(/<link rel="stylesheet" href="https:\/\/fonts\.googleapis\.com[^>]*>/, '')],
    ['e-noscript', 'e) Data and page script removed', 'No board is drawn and no fitter runs (the data and the page script are one block).', S.slice(0, big.index) + S.slice(big.index + big[0].length)],
    ['e-noimages', 'e) Inline images in the data replaced', 'Rank tiles and logos in the data become 1px images.', S.slice(0, big.index) + big[0].replace(DU, tiny) + S.slice(big.index + big[0].length)],
    ['e-nocssimages', 'e) Inline images in CSS replaced', 'Images embedded in the stylesheets become 1px images.', S.replace(STYLE, (m, a, b, c) => a + b.replace(DU, tiny) + c)],
    ['f-noreveal', 'f) Hidden-until-fitted reveal removed', 'The page shows at once instead of after the fitters.', S.replace('body>*{visibility:hidden}', '')],
    ['g-seasons', 'g) Season strip emptied', 'The year buttons at the top.', emptyTag(S, /<nav class="yrs[^"]*"[^>]*>/)],
    ['g-header', 'g) Header emptied', 'Title and season timeline.', emptyTag(S, /<header[^>]*>/)],
    ['g-tabbar', 'g) Tab bar emptied', 'Game Day / The Lab / Front Office and the tab pills.', emptyTag(S, /<div class="tnav"[^>]*>/)],
    ['g-standings', 'g) Standings pane emptied', 'No board (the page script stops where it needs it).', emptyTag(S, /<div class="pane pane-st"[^>]*>/)],
    ['h-nofitters', 'Fitters off (all)', 'Every fitting function returns at once.', noop(S, FIT)],
    ['h-nodraw', 'Board not drawn', 'draw() returns at once; fitters still run on nothing.', noop(S, ['draw'])],
    ['h-nodtab', 'Desktop table off', 'dtab() returns at once (only matters at desktop widths).', noop(S, ['dtab'])],
    ['h-noseason', 'Season charts off', 'season() returns at once.', noop(S, ['season'])],
    ['h-nofit', 'Rank-tile fitter off', 'fit() returns at once.', noop(S, ['fit'])],
    ['h-nosbfit', 'Stat-line fitter off', 'sbFit() returns at once.', noop(S, ['sbFit'])],
    ['h-nos2fit', 'Opp / All-play / Luck fitter off', 's2Fit() returns at once.', noop(S, ['s2Fit'])],
    ['h-notnfit', 'Name fitter off', 'tnFit() returns at once.', noop(S, ['tnFit'])],
    ['h-norrfit', 'Right-column fitter off', 'rrFit() returns at once.', noop(S, ['rrFit'])],
  ];
  fs.mkdirSync(DIR, { recursive: true });
  const label = (t, d) => `<div style="all:initial;display:block!important;visibility:visible!important;position:relative;z-index:2147483647;box-sizing:border-box;width:100%;padding:8px 16px;background:#FFD400;color:#000;font:600 14px/1.35 -apple-system,system-ui,sans-serif">MEMORY TEST · ${esc(t)}<br><span style="font-weight:400">${esc(d)}</span></div>`;
  const rows = [];
  for (const [id, t, d, html] of V) {
    if (id !== 'blank' && !html) { rows.push([id, t, d, false]); continue }
    let s = id === 'blank'
      ? `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex, nofollow"><title>MEM ${esc(t)}</title></head><body style="margin:0;background:#fff">${label(t, d)}</body></html>`
      : html.replace('<meta charset="utf-8">\n', '<meta charset="utf-8">\n<base href="../../">\n<meta name="robots" content="noindex, nofollow">\n')
            .replace(/<title>/, '<title>MEM ' + esc(t) + ' · ').replace(/<body([^>]*)>/, (m) => m + label(t, d));
    if (id !== 'blank' && !s.includes('<base href="../../">')) throw new Error('head marker not found');
    fs.writeFileSync(path.join(DIR, id + '.html'), s); rows.push([id, t, d, true]);
  }
  const built = (/<!-- built ([^-]+) -->/.exec(S) || [, ''])[1].trim();
  const list = rows.map(([id, t, d, ok]) => `<tr><td>${ok ? `<a href="${id}.html" target="_blank" rel="noopener">${esc(t)}</a>` : esc(t) + ' (not built)'}<div class="d">${esc(d)}</div></td><td><input inputmode="decimal" data-k="${id}" aria-label="MB for ${esc(t)}" placeholder="MB"></td></tr>`).join('');
  const idx = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex, nofollow"><title>Memory test pages</title>
<style>body{margin:0;background:#0C1215;color:#ECE6DA;font:15px/1.45 -apple-system,system-ui,sans-serif}main{max-width:760px;margin:0 auto;padding:16px}h1{font-size:20px;margin:8px 0}
ol{padding-left:20px}li{margin:4px 0}table{width:100%;border-collapse:collapse;margin:12px 0}td{padding:8px;border-top:1px solid #24444D;vertical-align:top}td:last-child{width:90px}
a{color:#7FA6FF}.d{color:#A0A8B8;font-size:13px}input{width:80px;box-sizing:border-box;padding:6px;font:inherit;background:#1A2C33;color:#ECE6DA;border:1px solid #2F5761;border-radius:4px}
button{font:inherit;padding:8px 14px;border-radius:6px;border:0;background:#ECE6DA;color:#0F1C20;font-weight:600}textarea{width:100%;height:120px;margin-top:8px;background:#1A2C33;color:#ECE6DA;border:1px solid #2F5761}</style></head>
<body><main><h1>Memory test pages (temporary)</h1><p class="d">Built ${esc(built)} from the live page. Not linked from the site; removed once the figures are in.</p>
<ol><li>Quit Safari, reopen it with only this page, open Activity Monitor › Memory.</li>
<li>Tap a test: it opens in its own tab. Wait 10 seconds on it without scrolling.</li>
<li>Read the Memory figure of that tab's process (it is listed under the site's name; this list page is the small one). If only one process for the site is listed, close this tab before reading and reopen it from History after.</li>
<li>Type the figure in MB in its box, close the test tab, next test.</li>
<li>Also once: open <b>Full page</b>, tap every tab in turn, come back to Standings, wait 10 seconds, read it, and put that figure in the last box.</li></ol>
<table>${list}<tr><td>Full page, after visiting every tab<div class="d">Open Full page, tap every tab, back to Standings, wait 10 s.</div></td><td><input inputmode="decimal" data-k="full-every-tab" placeholder="MB"></td></tr></table>
<button type="button" id="cp">Copy results</button><textarea id="tx" readonly aria-label="Results"></textarea>
<script>(function(){var K="memtest",I=[].slice.call(document.querySelectorAll("input[data-k]")),v={};try{v=JSON.parse(localStorage.getItem(K)||"{}")}catch(e){}
I.forEach(function(i){if(v[i.dataset.k])i.value=v[i.dataset.k];i.addEventListener("input",function(){v[i.dataset.k]=i.value;try{localStorage.setItem(K,JSON.stringify(v))}catch(e){};out()})});
function out(){document.getElementById("tx").value="Safari memory, Activity Monitor (MB)\\n"+I.map(function(i){return i.getAttribute("aria-label")?i.getAttribute("aria-label").replace("MB for ",""):"Full page, after every tab"}).map(function(n,k){return n+"\\t"+(I[k].value||"-")}).join("\\n")}
out();document.getElementById("cp").onclick=function(){var t=document.getElementById("tx");t.select();try{navigator.clipboard.writeText(t.value)}catch(e){try{document.execCommand("copy")}catch(_){}}}})()</script></main></body></html>`;
  fs.writeFileSync(path.join(DIR, 'index.html'), idx);
  fs.writeFileSync(path.join(OUT, 'robots.txt'), 'User-agent: *\nDisallow: /dynasty-tracker/debug/\n');
  console.log(`memdebug: ${rows.filter(r => r[3]).length} test pages in site/debug/mem/`);
})().catch(e => console.log('memdebug: skipped (' + e.message + ')'));
