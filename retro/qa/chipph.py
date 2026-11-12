# chipph.py <ch|wk> <baseurl> <label> <token...> : Standings rank chips and streak tiles on the phone layouts (works on both builds).
# Pictures per view: A (all on), B (own digits off), B2 (+ their box-shadows off), C (+ tiles off), T (all text off, for neighbours).
# ink = A-B, tile = B2-C (fill only: the 1px hard shadow and a ring are not the tile edge), neighbours = text ink (A-T) and other tiles.
import sys,json,collections,os;sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)));import eng,numpy as np
eng.PHONE.update({"874L":0,"956L":0})
ENG,BASE,LABEL=sys.argv[1],sys.argv[2],sys.argv[3];TOKS=sys.argv[4:]
GROUPS=[('chip-fitted','.pane-st .ch[style*="padding"]'),('chip-unfitted','.pane-st .ch:not([style*="padding"]):not(.strip *)'),('chip-strip','.board .r .strip .ch'),('streak','.board .r .sk'),('finish-tile','.pane-st .rkb')]
SEL=','.join(g[1] for g in GROUPS)
JS="(G)=>{const o=[];for(const [g,sel] of G)for(const e of document.querySelectorAll(sel)){if(!e.getClientRects().length||(e.checkVisibility&&!e.checkVisibility()))continue;const r=e.getBoundingClientRect();const sp=e.closest('.strip');if(sp){const q=sp.getBoundingClientRect();if(r.left<q.left+5||r.right>q.right-5)continue}const row=e.closest('.r');o.push({g,x:r.left+scrollX-4,y:r.top+scrollY-4,w:r.width+8,h:r.height+8,t:e.textContent.trim(),c:e.className.trim(),k:(e.parentElement.className||'').toString().split(/\\s+/)[0]+'/'+((e.closest('.st,.sb,.dps,.side,.l5r,.key')||{}).className||'').toString().trim().replace(/\\s+/g,'.'),row:row?[...row.parentElement.parentElement.querySelectorAll('.r')].indexOf(row):-1})}return o}"
ADD="(a)=>{const s=document.createElement('style');s.id=a[0];s.textContent=a[1];document.head.appendChild(s)}";DEL="(i)=>{const s=document.getElementById(i);if(s)s.remove()}"
X=':not(#_):not(#_):not(#_)'
OWN=':is('+SEL+')'+X+',:is('+SEL+') *'+X+'{-webkit-text-fill-color:transparent!important;text-shadow:none!important}'
SHD=':is('+SEL+')'+X+',:is('+SEL+') .ct'+X+'::before{box-shadow:none!important}'
TOF=':is('+SEL+') .ct'+X+'::before{display:none!important}:is('+SEL+')'+X+'{background:none!important}'
ST=[('nerd h2h',['dn-full']),('dumb median',['dn-lean','#bm'])]
if os.environ.get('ALL'):ST=[('dumb h2h',['dn-lean']),('nerd h2h',['dn-full']),('nerd median',['#bm']),('dumb median',['dn-lean'])]
CK="(id)=>{if(id[0]=='#'){document.querySelector(id).click();return}const l=document.querySelector('label[for=\"'+id+'\"]');(l||document.getElementById(id)).click()}"
CSSX=os.environ.get('CSSX','')
def edges(D,thr):
    m=D.max()
    if m<thr:return None
    cov=np.clip(D/m,0,1);cov[cov<.12]=0;c=cov.max(axis=0);r=cov.max(axis=1);nz=np.nonzero(c)[0];nr=np.nonzero(r)[0]
    if not len(nz):return None
    return [nz[0]+(1-c[nz[0]]),nr[0]+(1-r[nr[0]]),nz[-1]+c[nz[-1]],nr[-1]+r[nr[-1]]]
OUT=[]
for tok in TOKS:
    E=(eng.Ch if ENG=='ch' else eng.Wk)(tok)
    for name,ids in ST:
        if os.environ.get('ONLY') and os.environ['ONLY'] not in name:continue
        if not os.environ.get('ALL') or name==ST[0][0]:
            E.open(BASE+'#standings')
            if ENG=='wk':
                E.ev("()=>{try{localStorage.clear();sessionStorage.clear()}catch(e){}}");E.open(BASE+'#standings')
        for i in ids:E.ev(CK,i);E.wait(1400)
        E.wait(2600 if ENG=='wk' else 1800)
        if os.environ.get('OPEN'):
            E.ev("()=>{document.querySelectorAll('#list.board .tcard>.r').forEach(r=>{const s=r.querySelector('.strip');if(s&&s.hidden)r.querySelector('.nm .tn').click()})}");E.wait(1500)
        E.ev(eng.PREP);E.ev(ADD,['__oa','html,body,body *{overflow-anchor:none!important}'+CSSX]);E.ev("()=>{document.querySelectorAll('body *').forEach(e=>{if(e.getClientRects().length&&getComputedStyle(e).position==='sticky')e.style.setProperty('position','static','important')})}");E.wait(400)
        items=E.ev(JS,GROUPS);H=E.ev("()=>document.documentElement.scrollHeight");vh=E.ev("()=>innerHeight");y=0;todo=list(items)
        while y<H and todo:
            E.ev("(y)=>scrollTo(0,y)",y);E.wait(350);sy=E.ev("()=>scrollY")
            if not any(sy+13<it['y'] and it['y']+it['h']<sy+vh-13 for it in todo):y+=vh-260;continue
            W=700 if ENG=='wk' else 250
            for attempt in range(5):
                A,sc=E.view();E.ev(ADD,['__o',OWN]);E.wait(W);B,_=E.view();E.ev(ADD,['__s',SHD]);E.wait(W);B2,_=E.view();E.ev(ADD,['__t',TOF]);E.wait(W);C,_=E.view()
                E.ev(DEL,'__t');E.ev(DEL,'__s');E.wait(W);Bb,_=E.view();E.ev(DEL,'__o');E.ev(eng.HIDE_ON,eng.HIDE);E.wait(W);T,_=E.view();E.ev(eng.HIDE_OFF);E.wait(W);A2,_=E.view()
                if A.shape==B.shape==C.shape==Bb.shape==A2.shape==T.shape==B2.shape and (np.abs(B-Bb).max(axis=2)>8).mean()<2e-5 and (np.abs(A-A2).max(axis=2)>8).mean()<2e-5:break
                W+=400;E.wait(600)
            else:print('   unstable pictures at',sy,flush=True)
            TEXT=np.abs(A-T).max(axis=2)>30;TILE=np.abs(B2-C).max(axis=2)>8;rest=[]
            for it in todo:
                if it['y']-sy<13 or it['y']+it['h']-sy>A.shape[0]/sc-13:rest.append(it);continue
                x0=int(round(it['x']*sc));x1=int(round((it['x']+it['w'])*sc));y0=int(round((it['y']-sy)*sc));y1=int(round((it['y']+it['h']-sy)*sc))
                if x0<0 or x1>A.shape[1]:it['g4']=None;continue
                tl=edges(np.abs(B2[y0:y1,x0:x1]-C[y0:y1,x0:x1]).max(axis=2).astype(float),8);ik=edges(np.abs(A[y0:y1,x0:x1]-B[y0:y1,x0:x1]).max(axis=2).astype(float),20)
                if not tl or not ik:it['g4']=None;continue
                it['g4']=[(ik[0]-tl[0])/sc,(tl[2]-ik[2])/sc,(ik[1]-tl[1])/sc,(tl[3]-ik[3])/sc];it['tile']=[(tl[2]-tl[0])/sc,(tl[3]-tl[1])/sc];it['ink']=[(ik[2]-ik[0])/sc,(ik[3]-ik[1])/sc]
                # neighbours: nearest text ink or other tile above / below, in the tile's own columns
                # the tile's own painted pixels (any change at all, faint edge rows included) are taken out of the neighbour mask
                own=np.abs(B2[y0:y1,x0:x1]-C[y0:y1,x0:x1]).max(axis=2)>8;oc=np.nonzero(own.any(axis=0))[0];orow=np.nonzero(own.any(axis=1))[0]
                cx0=x0+int(oc[0]);cx1=x0+int(oc[-1])+1;ty0=y0+int(orow[0]);ty1=y0+int(orow[-1])+1;R=int(14*sc)
                NB=(TEXT|TILE).copy();NB[y0:y1,x0:x1]&=~own;NB[ty0:ty1,cx0:cx1]=False
                N=NB[:,cx0:cx1].any(axis=1)
                up=next((d for d in range(1,R) if ty0-d>=0 and N[ty0-d]),None);dn=next((d for d in range(1,R) if ty1-1+d<len(N) and N[ty1-1+d]),None)
                it['up']=None if up is None else (up-1)/sc;it['dn']=None if dn is None else (dn-1)/sc
                Nh=NB[ty0:ty1,:].any(axis=0)
                lf=next((d for d in range(1,R) if cx0-d>=0 and Nh[cx0-d]),None);rt=next((d for d in range(1,R) if cx1-1+d<len(Nh) and Nh[cx1-1+d]),None)
                it['lf']=None if lf is None else (lf-1)/sc;it['rt']=None if rt is None else (rt-1)/sc
                if os.environ.get('CROP'):
                    from PIL import Image
                    pad=int(10*sc);Image.fromarray(A[max(0,y0-pad):y1+pad,max(0,x0-pad*3):x1+pad*3].astype(np.uint8)).save(f"s/{LABEL}-{tok}-{it['g']}-{it['row']}-{it['t']}-{len(OUT)}.png")
            todo=rest;y+=vh-260
        for it in items:it['tok']=tok;it['state']=name;it['eng']=E.name
        OUT+=items
        print(f'===== {E.name} {tok} {name}: {len(items)} elements',flush=True)
        for g,_ in GROUPS:
            v=[it for it in items if it['g']==g];ok=[it for it in v if it.get('g4')]
            if not v:continue
            if not ok:print(f'  {g:14s} n {len(v)} NOT MEASURED');continue
            G=[it['g4'] for it in ok];w=max(ok,key=lambda it:abs(it['g4'][0]-it['g4'][1]))
            ups=[it['up'] for it in ok if it['up'] is not None];dns=[it['dn'] for it in ok if it['dn'] is not None]
            print(f"  {g:14s} n {len(v):3d} unmeasured {len(v)-len(ok)} gold {sum('gold' in it['c'].split() for it in v)} last {sum('last' in it['c'].split() for it in v)} | min L {min(x[0] for x in G):.2f} R {min(x[1] for x in G):.2f} T {min(x[2] for x in G):.2f} B {min(x[3] for x in G):.2f} | max|L-R| {abs(w['g4'][0]-w['g4'][1]):.2f} '{w['t']}' n>.5: {sum(abs(x[0]-x[1])>.5 for x in G)} | L/R<3: {sum(min(x[0],x[1])<2.95 for x in G)} T/B<2: {sum(min(x[2],x[3])<1.95 for x in G)} | tile h {min(it['tile'][1] for it in ok):.2f}-{max(it['tile'][1] for it in ok):.2f} | nearest above {min(ups) if ups else float('nan'):.2f} below {min(dns) if dns else float('nan'):.2f} (none within 14px: {len(ok)-len(ups)} / {len(ok)-len(dns)}) | nearest left {min([it['lf'] for it in ok if it['lf'] is not None] or [float('nan')]):.2f} right {min([it['rt'] for it in ok if it['rt'] is not None] or [float('nan')]):.2f}",flush=True)
    E.close()
json.dump([{k:v for k,v in it.items()} for it in OUT],open(f'out/chipph-{LABEL}-{ENG}-{"_".join(TOKS)}.json','w'))
