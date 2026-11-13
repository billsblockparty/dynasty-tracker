# dashm.py <ch|wk> <url> <label> <token...> : the record's dash on the Standings cards (job 3, item 3), from pixels: the dash's white
# length, the white-to-white distance to the digit on each side read along the dash's own rows, and the record's box width.
# States: H2H and Median (Dumb). Pictures: A against the same with the drawn dash switched off; the dash's white = the white that goes,
# the neighbours = the nearest white left on the dash's rows (coverage-weighted edges). Needs the build with .rdash. json in ./out/dashm-...
import sys,json,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));import eng,numpy as np
eng.PHONE.update({"874L":0,"956L":0})
ENG,URL,LABEL=sys.argv[1:4];TOKS=sys.argv[4:]
JS=r"""()=>[...document.querySelectorAll('.board .r .side .rr b')].filter(e=>e.getClientRects().length).map(b=>{const r=b.getBoundingClientRect(),c=getComputedStyle(b);return {tx:b.textContent,x:r.left+scrollX,y:r.top+scrollY,w:r.width,h:r.height,fs:parseFloat(c.fontSize),z:r.height/parseFloat(c.lineHeight)}})"""
CK="(id)=>{if(id[0]=='#'){document.querySelector(id).click();return}const l=document.querySelector('label[for=\"'+id+'\"]');(l||document.getElementById(id)).click()}"
ADD="(a)=>{const s=document.createElement('style');s.id=a[0];s.textContent=a[1];document.head.appendChild(s)}";DEL="(i)=>{const s=document.getElementById(i);if(s)s.remove()}"
OFF='.board .r .rr b .rdash:not(#_):not(#_)::before{visibility:hidden!important}'
def stat(v):return 'n=0' if not v else 'min %.2f mean %.2f max %.2f (n=%d)'%(min(v),sum(v)/len(v),max(v),len(v))
for tok in TOKS:
    E=(eng.Ch if ENG=='ch' else eng.Wk)(tok);E.open(URL+'#standings',2600);E.ev(eng.PREP);OUT=[]
    for st,ids in (('h2h',[]),('median',['#bm'])):
        for i in ids:E.ev(CK,i);E.wait(1500)
        E.ev("()=>window.__fitAll&&window.__fitAll()");E.wait(2800);rows=E.ev(JS);vh=E.ev("()=>innerHeight");y=max(0,min(r['y'] for r in rows)-80)
        while any('d' not in r for r in rows):
            E.ev("(y)=>scrollTo(0,y)",y);E.wait(450);sy=E.ev("()=>scrollY");A,sc=E.view();E.ev(ADD,['__p',OFF]);E.wait(300);B,_=E.view();E.ev(DEL,'__p');E.wait(150);H=A.shape[0]/sc;n=0
            for r in rows:
                if 'd' in r or r['y']-sy<4 or r['y']+r['h']-sy>H-4:continue
                r['d']=1;n+=1;x0=int((r['x']-4)*sc);x1=int((r['x']+r['w']+6)*sc);t=int((r['y']-sy)*sc);u=int((r['y']+r['h']-sy)*sc)
                a=np.clip((A[t:u,x0:x1].min(axis=2).astype(float)-120)/110,0,1);b=np.clip((B[t:u,x0:x1].min(axis=2).astype(float)-120)/110,0,1)   # white coverage, dash on / dash off
                d=np.clip(a-b,0,1);rs=np.nonzero((d>.5).any(axis=1))[0]
                if not len(rs):continue
                band=slice(rs[0],rs[-1]+1);dc=d[band].max(axis=0);band=slice(max(0,rs[0]-int(round(1.5*sc))),rs[-1]+1+int(round(1.5*sc)));nz=np.nonzero(dc>.1)[0];l=nz[0]+(1-dc[nz[0]]);rr=nz[-1]+dc[nz[-1]]
                # neighbours: read on the dash's rows and 1.5px above and below (its 1px outline and half a pixel: where a digit's ink would meet it)
                oc=b[band].max(axis=0);le=np.nonzero(oc[:nz[0]]>.1)[0];ri=np.nonzero(oc[nz[-1]+1:]>.1)[0]
                if not len(le) or not len(ri):continue
                eL=le[-1]+oc[le[-1]];k=nz[-1]+1+ri[0];eR=k+(1-oc[k])
                OUT.append(dict(st=st,tx=r['tx'],fs=r['fs'],w=r['w'],dash=(rr-l)/sc,gl=(l-eL)/sc,gr=(eR-rr)/sc,hh=len(rs)/sc))
            y+=vh-240
            if not n and y>20000:break
    json.dump(OUT,open(f'out/dashm-{LABEL}-{ENG}-{tok}.json','w'))
    for st in ('h2h','median'):
        S=[d for d in OUT if d['st']==st]
        if not S:continue
        print(f'== {LABEL} {E.name} {tok} {st}: records {len(S)} ({S[0]["fs"]}px)');print('   dash white length          ',stat([d['dash'] for d in S]));print('   white to white, left       ',stat([d['gl'] for d in S]));print('   white to white, right      ',stat([d['gr'] for d in S]))
        print('   |left - right|             ',stat([abs(d['gl']-d['gr']) for d in S]));w=max(S,key=lambda d:abs(d['gl']-d['gr']));print('   worst pair: %s  left %.2f right %.2f dash %.2f; record box widths %.2f to %.2f'%(w['tx'],w['gl'],w['gr'],w['dash'],min(d['w'] for d in S),max(d['w'] for d in S)))
    E.close()
