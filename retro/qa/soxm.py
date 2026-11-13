# soxm.py <ch|wk> <url> <label> <token...> : Remaining schedule cells (.sox; Stats > Schedules, Team Hub): the row left between the picture's
# paint (ring and hard shadow) and the rank tile, from pixels (job 3, item 2). Pictures: A against (picture off) and (chip off).
# TAB=stats|team-hub, IDS=comma list of label ids (stats needs sx-sch), CSSX = extra css (to mock a variant). json in ./out/soxm-...
import sys,json,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));import eng,numpy as np
eng.PHONE.update({"874L":0,"956L":0})
ENG,URL,LABEL=sys.argv[1:4];TOKS=sys.argv[4:];TAB=os.environ.get('TAB','stats');IDS=[i for i in os.environ.get('IDS','sx-sch' if TAB=='stats' else '').split(',') if i];CSSX=os.environ.get('CSSX','')
JS=r"""()=>{const o=[];const B=e=>{const r=e.getBoundingClientRect();return [r.left+scrollX,r.top+scrollY,r.right+scrollX,r.bottom+scrollY]};
for(const s of document.querySelectorAll('.sox')){if(!s.getClientRects().length||(s.checkVisibility&&!s.checkVisibility()))continue;const a=s.querySelector('.pav'),c=s.querySelector('.ch'),v=s.querySelector('.soa');if(!a||!c)continue;
 const k=[...s.children].map(B);o.push({sox:B(s),av:B(a),ch:B(c),soa:v?B(v):null,sw:s.scrollWidth,cw:s.clientWidth,lines:new Set(k.map(b=>Math.round((b[1]+b[3])/2/6))).size,tx:c.textContent.trim(),cls:c.className.trim(),avw:a.getBoundingClientRect().width,
  cellR:s.parentElement.getBoundingClientRect().right+scrollX,next:s.nextElementSibling?B(s.nextElementSibling):null})}return o}"""
ADD="(a)=>{const s=document.createElement('style');s.id=a[0];s.textContent=a[1];document.head.appendChild(s)}";DEL="(i)=>{const s=document.getElementById(i);if(s)s.remove()}"
X=':not(#_):not(#_):not(#_)';PARTS=[('av','.sox .pav'+X+'{visibility:hidden!important}'),('ch','.sox .ch'+X+'{visibility:hidden!important}')]
CK="(id)=>{if(id[0]=='#'){document.querySelector(id).click();return}const l=document.querySelector('label[for=\"'+id+'\"]');(l||document.getElementById(id)).click()}"
def stat(v):
    v=[x for x in v if x is not None];return 'n=0' if not v else 'min %.2f mean %.2f max %.2f (n=%d)'%(min(v),sum(v)/len(v),max(v),len(v))
for tok in TOKS:
    E=(eng.Ch if ENG=='ch' else eng.Wk)(tok);E.open(URL+'#'+TAB,2600);E.ev(eng.PREP)
    if CSSX:E.ev(ADD,['__x',CSSX])
    for i in IDS:E.ev(CK,i);E.wait(1200)
    E.ev("()=>window.__fitAll&&window.__fitAll()");E.wait(900);rows=E.ev(JS)
    if not rows:print(tok,'no cells');E.close();continue
    y0=min(r['sox'][1] for r in rows);vh=E.ev("()=>innerHeight");OUT=[]
    for vi in range(int(os.environ.get('VIEWS','1'))):
        E.ev("(y)=>scrollTo(0,y)",max(0,y0-80+vi*(vh-200)));E.wait(500);sy=E.ev("()=>scrollY");sx=E.ev("()=>scrollX")
        for attempt in range(4):
            E.wait(500*attempt);A,sc=E.view();P={}
            for k,css in PARTS:E.ev(ADD,['__p',css]);E.wait(260+150*attempt);P[k],_=E.view();E.ev(DEL,'__p');E.wait(120+150*attempt)
            A2,_=E.view();bad=1 if A.shape!=A2.shape else float((np.abs(A-A2).max(axis=2)>30).mean())
            if bad<2e-5:break
        else:print('   unstable, view',vi,'skipped');continue
        H=A.shape[0]/sc
        for r in rows:
            if r.get('done') or r['sox'][1]-sy<8 or r['sox'][3]-sy>H-8:continue
            r['done']=1;a,c=r['av'],r['ch'];t=int((min(a[1],c[1])-sy-6)*sc);u=int((max(a[3],c[3])-sy+6)*sc);x0=int((a[0]-sx-6)*sc);x1=int((c[2]-sx+6)*sc)
            ma=(np.abs(A[t:u,x0:x1]-P['av'][t:u,x0:x1]).max(axis=2)>24);mc=(np.abs(A[t:u,x0:x1]-P['ch'][t:u,x0:x1]).max(axis=2)>24)
            ma[:,int((c[0]-sx+1.5)*sc)-x0:]=False;mc[:,:max(0,int((a[2]-sx-1.5)*sc)-x0)]=False   # a neighbouring cell's picture or chip inside the crop is not this cell's
            if not ma.any() or not mc.any():continue
            # only the rows of pixels the tile occupies: the gap is read where the two stand side by side
            rc=np.nonzero(mc.any(axis=1))[0];band=slice(rc[0],rc[-1]+1);ca=np.nonzero(ma[band].any(axis=0))[0];cc=np.nonzero(mc[band].any(axis=0))[0]
            if not len(ca):continue
            d=dict(tx=r['tx'],cls=r['cls'],avw=r['avw'],lines=r['lines'],gap=(cc[0]-ca[-1]-1)/sc,av_past=(x0+ca[-1]+1)/sc+sx-a[2],tile_before=c[0]-((x0+cc[0])/sc+sx),boxgap=c[0]-a[2],over=r['sw']-r['cw'],
                   soa_gap=(r['soa'][0]-((x0+cc[-1]+1)/sc+sx)) if r['soa'] and r['lines']==1 else None,soa_x=r['soa'][0]-r['sox'][0] if r['soa'] else None,chx=c[0]-r['sox'][0],col=round(r['sox'][0]),sox_w=r['sox'][2]-r['sox'][0]);OUT.append(d)
    json.dump(OUT,open(f'out/soxm-{LABEL}-{ENG}-{tok}-{TAB}.json','w'))
    print(f'== {LABEL} {E.name} {tok} {TAB} cells {len(OUT)} of {len(rows)}; picture widths {sorted(set(round(d["avw"],1) for d in OUT))}; lines per cell {sorted(set(d["lines"] for d in OUT))}; cell width %.1f to %.1f'%(min(d['sox_w'] for d in OUT),max(d['sox_w'] for d in OUT)) if OUT else f'== {LABEL} {tok} nothing read')
    for k,lab in [('boxgap','picture box -> chip box'),('av_past','picture paint past its box (right)'),('tile_before','tile starts left of the chip box'),('gap','ROW between picture paint and tile'),('soa_gap','tile -> AVG figure box (one-line cells)'),('over','cell scrollWidth - clientWidth')]:
        print('   %-42s'%lab,stat([d[k] for d in OUT]))
    cols={}
    for d in OUT:cols.setdefault(d['col'],[]).append(d['chx'])
    print('   chip left edge within its cell, per column: %d columns, largest spread %.2f'%(len(cols),max(max(v)-min(v) for v in cols.values())) if cols else '')
    E.close()
