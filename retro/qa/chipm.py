# chipm.py <ch|wk> <baseurl> <token...> : rank chips whose tile is drawn by .ct::before (Stats, Team Hub): gaps between digit ink and the
# painted tile, both read from pixels. Three pictures per view: text on (A), text off (B), text and tiles off (C). tile = B-C, ink = A-B.
import sys,json,collections,os;sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)));import eng,numpy as np
eng.PHONE.update({"874L":0,"956L":0})
ENG,BASE=sys.argv[1],sys.argv[2];TOKS=sys.argv[3:]
SEL=':is(.pane-sx,.thx2) :is(.ch,.tqt)[style*="padding"]'
JS="(sel)=>[...document.querySelectorAll(sel)].filter(e=>e.getClientRects().length&&(!e.checkVisibility||e.checkVisibility())).map(e=>{const r=e.getBoundingClientRect();return {x:r.left+scrollX-3,y:r.top+scrollY-3,w:r.width+6,h:r.height+6,t:e.textContent.trim(),k:e.className.trim().replace(/\\s+/g,'.')+' < '+(e.parentElement.className||'').toString().split(/\\s+/)[0]}})"
TOFF="(c)=>{const s=document.createElement('style');s.id='__toff';s.textContent=c;document.head.appendChild(s)}";TON="()=>{const s=document.getElementById('__toff');if(s)s.remove()}"
TCSS=SEL+' .ct::before{display:none!important}'
ST=[('stats','sch',['sx-sch']),('stats','cs',['sx-cs']),('team-hub','team 1',[]),('team-hub','team 10',['thx-9']),('team-hub','trends team 7',['thx-6','thv-t']),('team-hub','trends team 3 wk 3',['thx-2','thv-t','thw-3'])]
CK="(id)=>{const l=document.querySelector('label[for=\"'+id+'\"]');(l||document.getElementById(id)).click()}"
def edges(D,thr):
    m=D.max()
    if m<thr:return None
    cov=np.clip(D/m,0,1);cov[cov<.12]=0;c=cov.max(axis=0);r=cov.max(axis=1);nz=np.nonzero(c)[0];nr=np.nonzero(r)[0]
    if not len(nz):return None
    return [nz[0]+(1-c[nz[0]]),nr[0]+(1-r[nr[0]]),nz[-1]+c[nz[-1]],nr[-1]+r[nr[-1]]]
for tok in TOKS:
    E=(eng.Ch if ENG=='ch' else eng.Wk)(tok);tot=0;N=0
    for tab,name,ids in ST:
        if os.environ.get('ONLY') and os.environ['ONLY'] not in tab+'/'+name:continue
        E.open(BASE+'#'+tab)
        if ENG=='wk':
            E.ev("()=>{try{localStorage.clear();sessionStorage.clear()}catch(e){}}");E.open(BASE+'#'+tab)
        for i in ids:E.ev(CK,i);E.wait(1400)
        E.wait(1800)
        E.ev(eng.PREP);E.ev("()=>{const s=document.createElement('style');s.textContent='html,body,body *{overflow-anchor:none!important}';document.head.appendChild(s)}");E.ev("()=>{document.querySelectorAll('body *').forEach(e=>{if(e.getClientRects().length&&getComputedStyle(e).position==='sticky')e.style.setProperty('position','static','important')})}");E.wait(300)
        items=E.ev(JS,SEL);H=E.ev("()=>document.documentElement.scrollHeight");vh=E.ev("()=>innerHeight");y=0;todo=list(items);res=collections.OrderedDict()
        while y<H and todo:
            E.ev("(y)=>scrollTo(0,y)",y);E.wait(350);sy=E.ev("()=>scrollY")
            if not any(sy+1<it['y'] and it['y']+it['h']<sy+vh-1 for it in todo):y+=vh-220;continue
            W=700 if ENG=='wk' else 250
            for attempt in range(5):
                A,sc=E.view();E.ev(eng.HIDE_ON,eng.HIDE);E.wait(W);B,_=E.view();E.ev(TOFF,TCSS);E.wait(W);C,_=E.view();E.ev(TON);E.wait(W);B2,_=E.view();E.ev(eng.HIDE_OFF);E.wait(W);A2,_=E.view()
                if A.shape==B.shape==C.shape==B2.shape==A2.shape and (np.abs(B-B2).max(axis=2)>8).mean()<2e-5 and (np.abs(A-A2).max(axis=2)>8).mean()<2e-5:break
                W+=400;E.wait(600)
            else:print('   unstable pictures at',sy,flush=True)
            rest=[]
            if os.environ.get('DUMP'):
                from PIL import Image
                for nm,im in (('A',A),('B',B),('C',C)):Image.fromarray(im.astype(np.uint8)).save(f's/dump-{nm}-{int(sy)}.png')
            for it in todo:
                if it['y']-sy<1 or it['y']+it['h']-sy>A.shape[0]/sc-1:rest.append(it);continue
                x0=int(round(it['x']*sc));x1=int(round((it['x']+it['w'])*sc));y0=int(round((it['y']-sy)*sc));y1=int(round((it['y']+it['h']-sy)*sc))
                tl=edges(np.abs(B[y0:y1,x0:x1]-C[y0:y1,x0:x1]).max(axis=2).astype(float),8);ik=edges(np.abs(A[y0:y1,x0:x1]-B[y0:y1,x0:x1]).max(axis=2).astype(float),20)
                if not tl or not ik:res.setdefault(it['k'],[]).append((None,it['t']));continue
                g=[(ik[0]-tl[0])/sc,(tl[2]-ik[2])/sc,(ik[1]-tl[1])/sc,(tl[3]-ik[3])/sc];res.setdefault(it['k'],[]).append((g,it['t']))
            todo=rest;y+=vh-220
        print(f'===== {E.name} {tok} {tab} / {name}: {len(items)} chips');bad=0
        for k,v in res.items():
            ok=[x for x in v if x[0]];nm=len(v)-len(ok)
            if not ok:print(f'  {k[:40]:40s} n {len(v)} NOT MEASURED');bad+=nm;continue
            lr=sum(1 for g,_ in ok if min(g[0],g[1])<2.95);tb=sum(1 for g,_ in ok if min(g[2],g[3])<1.95);dc=sum(1 for g,_ in ok if abs(g[0]-g[1])>.55);bad+=lr+tb+dc+nm;w=max(ok,key=lambda x:abs(x[0][0]-x[0][1]))
            print(f"  {k[:40]:40s} n {len(ok):3d} unmeasured {nm} | L/R<3 {lr} T/B<2 {tb} |L-R|>.5 {dc} | min L {min(g[0] for g,_ in ok):.2f} R {min(g[1] for g,_ in ok):.2f} T {min(g[2] for g,_ in ok):.2f} B {min(g[3] for g,_ in ok):.2f} max dLR {abs(w[0][0]-w[0][1]):.2f} '{w[1]}'")
        N+=len(items);tot+=bad;print('   violations:',bad,flush=True)
    print(f'##### {E.name} {tok} chips {N} TOTAL violations: {tot}',flush=True);E.close()
