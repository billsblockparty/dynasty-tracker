# gapframed.py <ch|wk> <label> <baseurl> <token...> : Matchups, every framed element (own fill, border or inset ring; up to 240 x 70px)
# that holds text: gap between the text ink INCLUDING shadow / outline and the inner edge of the frame, from screenshots.
import sys,json,collections;sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)));import eng
ENG,LABEL,BASE=sys.argv[1],sys.argv[2],sys.argv[3];TOKS=sys.argv[4:]
JS=r"""(pane)=>{const sx=scrollX,sy=scrollY;const P=s=>{const m=(s||'').match(/rgba?\(([^)]+)\)/);if(!m)return 0;const a=m[1].split(/[, /]+/).filter(x=>x!=='').map(Number);return a[3]===undefined?1:a[3]};
const strip=c=>(c||'').toString().split(/\s+/).filter(x=>x&&!/^(t|n|p)-[A-Za-z0-9]+$/.test(x)&&!/^(a|b|act|wa|wb|fin|g|w|l)$/.test(x)).slice(0,3).join('.');
const lab=e=>e.tagName.toLowerCase()+(strip(e.className)?'.'+strip(e.className):'');
const fr=c=>{let f=[parseFloat(c.borderLeftWidth)||0,parseFloat(c.borderTopWidth)||0,parseFloat(c.borderRightWidth)||0,parseFloat(c.borderBottomWidth)||0];
  if(c.boxShadow&&c.boxShadow!=='none'){c.boxShadow.split(/,(?![^(]*\))/).forEach(sh=>{if(!sh.includes('inset'))return;const n=(sh.replace(/rgba?\([^)]*\)|color\([^)]*\)/g,'').match(/-?[\d.]+px/g)||[]).map(parseFloat);const x=n[0]||0,y=n[1]||0,sp=n[3]||0;
    f=[Math.max(f[0],sp+Math.max(x,0)),Math.max(f[1],sp+Math.max(y,0)),Math.max(f[2],sp+Math.max(-x,0)),Math.max(f[3],sp+Math.max(-y,0))]})}return f};
const M=new Map();const tw=document.createTreeWalker(document.querySelector(pane),NodeFilter.SHOW_TEXT);let n;
while(n=tw.nextNode()){if(!n.textContent.trim())continue;const pe=n.parentElement;if(!pe||!pe.getClientRects().length)continue;if(pe.checkVisibility&&!pe.checkVisibility({contentVisibilityAuto:true,visibilityProperty:true}))continue;const dm=document.querySelector('details[open] .ddm');if(dm&&!dm.contains(pe)){const q=pe.getBoundingClientRect(),m=dm.getBoundingClientRect();if(q.right>m.left-6&&q.left<m.right+6&&q.bottom>m.top-6&&q.top<m.bottom+6)continue}if(getComputedStyle(pe).visibility==='hidden')continue;
  for(let a=pe;a&&!a.matches(pane);a=a.parentElement){const c=getComputedStyle(a);const f=fr(c);const framed=P(c.backgroundColor)>.05||(c.backgroundImage&&c.backgroundImage!=='none')||f[0]>0||f[2]>0||(f[1]>0&&f[3]>0);
    if(!framed)continue;const r=a.getBoundingClientRect();if(r.width<=240&&r.height<=70&&r.width>3&&r.height>3){if(!M.has(a))M.set(a,{k:lab(a)+' < '+lab(a.parentElement),x:r.left+sx,y:r.top+sy,w:r.width,h:r.height,f:f.map(v=>Math.min(v,4)),t:a.textContent.trim().replace(/\s+/g,' ').slice(0,14)})}break}}
return [...M.values()]}"""

import os
ST=[('matchups','week 9 final','.pane-mu',['mw-9']),('matchups','week 9 detailed','.pane-mu',['mw-9','ld-d']),('matchups','current week','.pane-mu',[]),('matchups','current slate+team+optimal','.pane-mu',['lv-s','lc-t','lo-o']),('matchups','week menu open','.pane-mu',['@wdd']),
    ('playoffs','bracket','.pane-po',[]),('playoffs','builder + menu','.pane-po',['pv-c','@dd-a']),('playoffs','schedule','.pane-po',['pv-s']),('playoffs','final + slate','.pane-po',['bk-fin','blv-s'])]
ONLY=os.environ.get('ONLY','')
CK="(id)=>{if(id[0]=='@'){document.querySelector('.'+id.slice(1)).open=true;return}const l=document.querySelector('label[for=\"'+id+'\"]');(l||document.getElementById(id)).click()}"
LIVE=r"""()=>{let n=0;document.querySelectorAll('.pane-mu .cr.lu .cv.pjc').forEach((c,i)=>{if(!c.getClientRects().length||i%3==2)return;const f=c.querySelector('.fs');const v=(f.firstChild&&f.firstChild.nodeType==3?f.firstChild.nodeValue:(f.textContent.match(/[\d.]+/)||['0.0'])[0]);c.classList.remove('pjc');c.classList.add('act');c.innerHTML='<span class="fs lv" title="Projected 1.0"><em class="fdf"></em>'+v.trim()+'<small>LIVE</small></span>';n++});return n}"""
for tok in TOKS:
    E=(eng.Ch if ENG=='ch' else eng.Wk)(tok);out={};tot=0
    for tab,name,pane,ids in ST+[('matchups','current week LIVE (simulated)','.pane-mu',['!live'])]:
        if ONLY and ONLY not in tab+'/'+name:continue
        E.open(BASE+'#'+tab)
        if ENG=='wk':
            E.ev("()=>{try{localStorage.clear();sessionStorage.clear()}catch(e){}}");E.open(BASE+'#'+tab)
        for i in ids:
            if i=='!live':print('   live cells injected:',E.ev(LIVE))
            else:E.ev(CK,i)
            E.wait(1300)
        E.ev(eng.PREP);E.ev("()=>{const s=document.createElement('style');s.textContent='html::-webkit-scrollbar,body::-webkit-scrollbar{display:none!important}html{scrollbar-width:none!important}';document.head.appendChild(s)}");E.ev("()=>{document.querySelectorAll('body *').forEach(e=>{if(e.getClientRects().length&&getComputedStyle(e).position==='sticky')e.style.setProperty('position','static','important')})}");E.wait(300);items=E.ev(JS,pane);eng.inkscan(E,items,thr=12);C=collections.OrderedDict()
        for it in items:
            if not it.get('ink'):continue
            g=eng.gaps(it);C.setdefault(it['k'],[]).append((g,it['t'],it['w'],it['h']))
        out[tab+'/'+name]={k:[[round(x,2) for x in g]+[t,w,h] for g,t,w,h in v] for k,v in C.items()}
        print(f'===== {E.name} {tok} {tab} / {name}: {len(items)} framed elements with text, {sum(len(v) for v in C.values())} measured')
        print(f"{'component':60s}    n  L/R<3  T/B<2 |L-R|>.5   min L  min R  min T  min B  maxdLR example")
        bad=0
        for k,v in sorted(C.items(),key=lambda kv:min(min(g) for g,_,_,_ in kv[1])):
            lr=sum(1 for g,_,_,_ in v if min(g[0],g[1])<2.95);tb=sum(1 for g,_,_,_ in v if min(g[2],g[3])<1.95)
            cen=[] if any(x in k for x in ('span.fs','span.cv','span.stc','i.pq')) else [abs(g[0]-g[1]) for g,_,_,_ in v if max(g[0],g[1])<=9];dc=sum(1 for d in cen if d>.55)
            if not lr and not tb and not dc:continue
            bad+=lr+tb+dc;w=min(v,key=lambda x:min(x[0]));print(f"{k[:60]:60s} {len(v):4d} {lr:6d} {tb:6d} {dc:8d}  {min(g[0] for g,_,_,_ in v):6.2f} {min(g[1] for g,_,_,_ in v):6.2f} {min(g[2] for g,_,_,_ in v):6.2f} {min(g[3] for g,_,_,_ in v):6.2f} {max(cen) if cen else 0:6.2f}  '{w[1]}'")
        tot+=bad;print('   violations in this state:',bad,flush=True)
    print(f'##### {E.name} {tok} TOTAL violations: {tot}',flush=True)
    json.dump(out,open(f'gf-{LABEL}-{ENG}-{tok}.json','w'));E.close()
