# svgm.py <ch|wk> <baseurl> <label> <token...> : season chart SVG chips (RANK / OPP rows, Nerd): digit ink to chip edge, from pixels.
# A (all on), B (the chips' digits off), C (chip rects off too). ink = A-B, tile = B-C (before build: the ring's outer edge).
import sys,json,os,collections;sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)));import eng,numpy as np
eng.PHONE.update({"874L":0,"956L":0})
ENG,BASE,LABEL=sys.argv[1],sys.argv[2],sys.argv[3];TOKS=sys.argv[4:]
JS="()=>[...document.querySelectorAll('.szn rect[rx=\"3\"]')].filter(e=>e.getClientRects().length&&e.nextElementSibling&&e.nextElementSibling.tagName=='text').map(e=>{const r=e.getBoundingClientRect(),t=e.nextElementSibling;const k=e.getAttribute('fill').startsWith('rgba(244')?'gold':(e.getAttribute('stroke')||'').startsWith('rgba(255,93')?'last':e.getAttribute('fill')=='var(--win-bg)'?'g':e.getAttribute('fill')=='var(--loss-bg)'?'b':'n';return {x:r.left+scrollX-3,y:r.top+scrollY-3,w:r.width+6,h:r.height+6,bw:r.width,bh:r.height,t:t.textContent.trim(),k,opp:e.hasAttribute('opacity'),fs:parseFloat(getComputedStyle(t).fontSize)*r.width/19,ts:getComputedStyle(t).textShadow,fill:getComputedStyle(t).fill,rf:getComputedStyle(e).fill,rs:getComputedStyle(e).stroke}})"
ADD="(a)=>{const s=document.createElement('style');s.id=a[0];s.textContent=a[1];document.head.appendChild(s)}";DEL="(i)=>{const s=document.getElementById(i);if(s)s.remove()}"
OWN='.szn rect[rx="3"]+text:not(#_):not(#_){fill:transparent!important;text-shadow:none!important;stroke:none!important}'
TOF='.szn rect[rx="3"]:not(#_):not(#_){fill:transparent!important;stroke:transparent!important}'
def edges(D,thr):
    m=D.max()
    if m<thr:return None
    cov=np.clip(D/m,0,1);cov[cov<.12]=0;c=cov.max(axis=0);r=cov.max(axis=1);nz=np.nonzero(c)[0];nr=np.nonzero(r)[0]
    if not len(nz):return None
    return [nz[0]+(1-c[nz[0]]),nr[0]+(1-r[nr[0]]),nz[-1]+c[nz[-1]],nr[-1]+r[nr[-1]]]
OUT=[]
for tok in TOKS:
    E=(eng.Ch if ENG=='ch' else eng.Wk)(tok);E.open(BASE+'#standings')
    if ENG=='wk':
        E.ev("()=>{try{localStorage.clear();sessionStorage.clear()}catch(e){}}");E.open(BASE+'#standings')
    E.ev("()=>document.querySelector('label[for=\"dn-full\"]').click()");E.wait(3200 if ENG=='wk' else 2200)
    E.ev(eng.PREP);E.ev(ADD,['__oa','html,body,body *{overflow-anchor:none!important}']);E.ev("()=>{document.querySelectorAll('body *').forEach(e=>{if(e.getClientRects().length&&getComputedStyle(e).position==='sticky')e.style.setProperty('position','static','important')})}");E.wait(400)
    items=E.ev(JS);H=E.ev("()=>document.documentElement.scrollHeight");vh=E.ev("()=>innerHeight");y=0;todo=list(items)
    while y<H and todo:
        E.ev("(y)=>scrollTo(0,y)",y);E.wait(350);sy=E.ev("()=>scrollY")
        if not any(sy+2<it['y'] and it['y']+it['h']<sy+vh-2 for it in todo):y+=vh-200;continue
        W=700 if ENG=='wk' else 250
        for attempt in range(5):
            A,sc=E.view();E.ev(ADD,['__o',OWN]);E.wait(W);B,_=E.view();E.ev(ADD,['__t',TOF]);E.wait(W);C,_=E.view();E.ev(DEL,'__t');E.wait(W);Bb,_=E.view();E.ev(DEL,'__o');E.wait(W);A2,_=E.view()
            if A.shape==B.shape==C.shape==Bb.shape==A2.shape and (np.abs(B-Bb).max(axis=2)>8).mean()<2e-5 and (np.abs(A-A2).max(axis=2)>8).mean()<2e-5:break
            W+=400;E.wait(600)
        else:print('   unstable pictures at',sy,flush=True)
        rest=[]
        for it in todo:
            if it['y']-sy<2 or it['y']+it['h']-sy>A.shape[0]/sc-2:rest.append(it);continue
            x0=int(round(it['x']*sc));x1=int(round((it['x']+it['w'])*sc));y0=int(round((it['y']-sy)*sc));y1=int(round((it['y']+it['h']-sy)*sc))
            tl=edges(np.abs(B[y0:y1,x0:x1]-C[y0:y1,x0:x1]).max(axis=2).astype(float),8);ik=edges(np.abs(A[y0:y1,x0:x1]-B[y0:y1,x0:x1]).max(axis=2).astype(float),20)
            it['g4']=None if not tl or not ik else [(ik[0]-tl[0])/sc,(tl[2]-ik[2])/sc,(ik[1]-tl[1])/sc,(tl[3]-ik[3])/sc]
        todo=rest;y+=vh-200
    for it in items:it['tok']=tok;it['eng']=E.name
    OUT+=items;ok=[it for it in items if it.get('g4')]
    print(f"===== {E.name} {tok}: {len(items)} SVG chips, measured {len(ok)}; box {items[0]['bw']:.2f} x {items[0]['bh']:.2f}px, digit {items[0]['fs']:.2f}px",flush=True)
    for k in ('gold','last','g','b','n'):
        v=[it for it in ok if it['k']==k]
        if not v:continue
        G=[it['g4'] for it in v];w=max(v,key=lambda it:abs(it['g4'][0]-it['g4'][1]))
        print(f"  {k:5s} n {len(v):3d} | min L {min(x[0] for x in G):.2f} R {min(x[1] for x in G):.2f} T {min(x[2] for x in G):.2f} B {min(x[3] for x in G):.2f} | max|L-R| {abs(w['g4'][0]-w['g4'][1]):.2f} '{w['t']}' n>.5: {sum(abs(x[0]-x[1])>.5 for x in G)} | L/R<3: {sum(min(x[0],x[1])<2.95 for x in G)} T/B<2: {sum(min(x[2],x[3])<1.95 for x in G)} | text fill {v[0]['fill']} shadow {v[0]['ts'][:40]} rect {v[0]['rf']} / {v[0]['rs']}",flush=True)
    E.close()
json.dump(OUT,open(f'out/svgm-{LABEL}-{ENG}-{"_".join(TOKS)}.json','w'))
