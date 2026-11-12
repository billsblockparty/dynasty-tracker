# ovf.py <tok...> : Matchups + Playoffs states, Classic vs Retro: clipped / ellipsised text, wrapped lines, sideways scroll, text under 11px
import sys;sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import json,collections,h
SHT="js:(()=>{const b=[...document.querySelectorAll('.pane-pt .ptv-k .ptk')].filter(e=>e.getClientRects().length&&e.querySelector('.ptxn'));const c=b.find(e=>+e.querySelector('.ptxn').textContent.trim()>=2)||b[0];c.click()})()"
PLY="js:document.querySelectorAll('.pane-pt .ptb')[1].click()"
PSH="js:(()=>{const b=[...document.querySelectorAll('.pane-pt .ptv-p .ptk')].filter(e=>e.getClientRects().length);(b.find(e=>/Traded/.test(e.textContent))||b[0]).click()})()"
CLS="js:(()=>{const x=document.querySelector('.pts .ptsx');if(x&&!document.querySelector('.pts').hidden)x.click()})()"
class BS:
    ROOT={'stats':'.pane-sx','team-hub':'.pane-th'}
    ST={'stats':[('pos',['sx-pos']),('odds',['sx-odds']),('drf',['sx-drf']),('frm',['sx-frm']),('sch',['sx-sch']),('ew',['sx-ew']),('trd',['sx-trd']),('lu',['sx-lu']),('prj',['sx-prj']),('mg',['sx-mg']),('pt',['sx-pt']),('cs',['sx-cs']),('st',['sx-st']),('yo',['sx-yo']),('rk',['sx-rk']),('by',['sx-by']),('hr',['sx-hr']),('pos-wk',['sx-pos','pm-wk']),('pos-tot',['pm-tot']),('odds-team',['sx-odds','odm-t']),('ew-cell-glossary',['sx-ew','js:document.querySelectorAll(".pane-sx .ewm .mx[data-w]")[7].click()','gl-s'])],
        'team-hub':[('team1',[]),('team2',['thx-1']),('team5',['thx-4']),('team8',['thx-7']),('team10',['thx-9']),('team1-again',['thx-0']),('trends',['thv-t']),('trends-wk3',['thw-3']),('trends-team6',['thx-5']),('team6-glossary',['thv-d','gl-s'])]}
from playwright.sync_api import sync_playwright
JS=r"""(root)=>{const R=document.querySelector(root);const out=[];const g=document.createRange();let i=0;
for(const e of R.querySelectorAll('*')){i++;if(!e.getClientRects().length)continue;if(e.checkVisibility&&!e.checkVisibility({contentVisibilityAuto:true,visibilityProperty:true}))continue;
 const own=[...e.childNodes].filter(n=>n.nodeType===3&&n.nodeValue.trim());if(!own.length)continue;const c=getComputedStyle(e);const z=e.currentCSSZoom||1;
 let lines=0,tw=0;const tops=new Set();for(const n of own){g.selectNodeContents(n);for(const r of g.getClientRects()){if(r.width>.5){tops.add(Math.round(r.top/3));tw=Math.max(tw,r.right)}}}lines=tops.size;
 // clipped: the text's own ink box runs past a clipping ancestor's box
 let clip=0,el=e;const tr=(()=>{let l=1e9,rr=-1e9;for(const n of own){g.selectNodeContents(n);for(const r of g.getClientRects()){l=Math.min(l,r.left);rr=Math.max(rr,r.right)}}return [l,rr]})();
 for(let a=e;a&&a!==R;a=a.parentElement){const ac=getComputedStyle(a);if(ac.overflowX!=='visible'){const b=a.getBoundingClientRect();if(tr[1]>b.right+1||tr[0]<b.left-1){clip=Math.max(clip,+(Math.max(tr[1]-b.right,b.left-tr[0])).toFixed(1))}}}
 const ell=c.textOverflow==='ellipsis'&&e.scrollWidth>e.clientWidth+1;
 const cn=(e.className&&e.className.baseVal!==undefined?e.className.baseVal:e.className)||'';
 out.push([i,e.tagName.toLowerCase()+(cn?'.'+String(cn).trim().split(/\s+/).slice(0,3).join('.'):'')+' < '+((e.parentElement.className||'')+'').split(/\s+/).slice(0,2).join('.'),own.map(n=>n.nodeValue.trim()).join(' ').slice(0,24),lines,clip,ell?1:0,+(parseFloat(c.fontSize)*z).toFixed(2)])}
return {sw:document.documentElement.scrollWidth,vw:innerWidth,n:document.querySelectorAll('*').length,t:out}}"""
def grab(b,url,tok,tab):
    pg,d=h.open_page(b,tok,url+'#'+tab,1000,2600);R={}
    for name,ids in BS.ST[tab]:
        for i in ids:
            if i.startswith('js:'):pg.evaluate('()=>{'+i[3:]+'}')
            elif i[0]=='@':pg.evaluate("(s)=>{document.querySelector('.'+s).open=true}",i[1:])
            else:pg.evaluate("(id)=>{const l=document.querySelector('label[for=\"'+id+'\"]');(l||document.getElementById(id)).click()}",i)
            pg.wait_for_timeout(1200)
        pg.evaluate("()=>window.__fitAll&&window.__fitAll()");pg.wait_for_timeout(600);R[name]=pg.evaluate(JS,BS.ROOT[tab])
    pg.close();return R
tot=collections.Counter()
with sync_playwright() as p:
    b=p.chromium.launch()
    for tok in [a for a in sys.argv[1:] if not a.startswith('--')]:
        for tab in ('stats','team-hub'):
            C=grab(b,h.CL,tok,tab);Rr=grab(b,h.RT,tok,tab)
            for st in C:
                c,r=C[st],Rr[st];cm={x[0]:x for x in c['t']};nc=[];nw=[];ne=[];small=collections.Counter();csmall=collections.Counter()
                for x in r['t']:
                    y=cm.get(x[0])
                    if x[4]>0 and not (y and y[4]>0):nc.append(x)
                    if x[5] and not (y and y[5]):ne.append(x)
                    if y and x[3]>y[3]:nw.append((x,y[3]))
                    if x[6]<10.95:small[(x[1],x[6])]+=1
                for y in c['t']:
                    if y[6]<10.95:csmall[(y[1],y[6])]+=1
                newsmall={k:v for k,v in small.items() if not any(ck[0]==k[0] and ck[1]<=k[1]+.01 for ck in csmall)}
                side=r['sw']>r['vw']
                tot['clip']+=len(nc);tot['ell']+=len(ne);tot['wrap']+=len(nw);tot['side']+=side;tot['small']+=len(newsmall)
                print(f"{tok} {tab}/{st}: elements {c['n']}/{r['n']}; sideways scroll {'YES' if side else 'no'} ({r['sw']}/{r['vw']}); new clipped {len(nc)}, new ellipsis {len(ne)}, more lines than Classic {len(nw)}; text <11px: Classic {sum(csmall.values())} nodes, Retro {sum(small.values())}, smaller than Classic's {len(newsmall)}")
                for x in nc[:6]:print('     CLIP',x)
                for x in ne[:6]:print('     ELLIPSIS',x)
                for x,l in nw[:8]:print('     WRAP',x,'classic lines',l)
                for k,v in list(newsmall.items())[:8]:print('     SMALL',k,v)
                if '--small' in sys.argv and st in ('w9-detailed','schedule','now'):
                    print('     retro <11px:',sorted(((k[0][:40],k[1],v) for k,v in small.items()),key=lambda x:-x[2])[:14])
    b.close()
print('TOTAL',dict(tot))
