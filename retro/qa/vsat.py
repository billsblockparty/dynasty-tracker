# vsat.py <ch|wk> <url> <label> <token...> : the game line of the lineups ("vs" / "at", logo, dot, kickoff) from pixels (job 3, item 1).
# Works on both builds. Per row of the first views of a state: glyph ink of the word (fill only) and with its shadow, the name's glyph ink,
# the logo's own ink and box, the dot's and the kickoff's glyph ink. Pictures: A (all on) against one picture per part switched off.
# TAB / IDS (comma list of label ids) choose the state: default Matchups as loaded. Prints the gaps; json in ./out/vsat-<label>-<eng>-<tok>.json
import sys,json,os,collections;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));import eng,numpy as np
eng.PHONE.update({"874L":0,"956L":0})
ENG,URL,LABEL=sys.argv[1:4];TOKS=sys.argv[4:];TAB=os.environ.get('TAB','matchups');IDS=[i for i in os.environ.get('IDS','').split(',') if i]
PANE={'matchups':'.pane-mu','playoffs':'.pane-po'}[TAB]
JS=r"""(P)=>{const o=[];const B=e=>{if(!e)return null;const r=e.getBoundingClientRect();return [r.left+scrollX,r.top+scrollY,r.right+scrollX,r.bottom+scrollY]};
for(const g of document.querySelectorAll(P+' .cnm:not(.psg) .gp')){if(!g.getClientRects().length||(g.checkVisibility&&!g.checkVisibility()))continue;const a=g.querySelector('.gha.ht');if(!a)continue;const cn=g.closest('.cn'),m=g.closest('.cnm'),nm=m.querySelector('b>span');
 o.push({side:cn&&cn.classList.contains('b')?'b':'a',w:a.classList.contains('h')?'vs':'at',word:B(a),name:B(nm),ntx:nm?nm.textContent:'',logo:B(g.querySelector('em.nfl.opp')),tm:(g.querySelector('em.nfl.opp')||{}).className,sep:B(g.querySelector('.gsep')),when:B(g.querySelector('.gwhen')),wtx:(g.querySelector('.gwhen')||{}).textContent,cnm:B(m),row:B(g.closest('.cr'))})}
return o}"""
ADD="(a)=>{const s=document.createElement('style');s.id=a[0];s.textContent=a[1];document.head.appendChild(s)}";DEL="(i)=>{const s=document.getElementById(i);if(s)s.remove()}"
X=':not(#_):not(#_):not(#_)';F='{-webkit-text-fill-color:transparent!important}';FS='{-webkit-text-fill-color:transparent!important;text-shadow:none!important}'
G=PANE+' .cnm .gp .gha.ht'
PARTS=[('wg',G+X+','+G+X+'::after'+F),('ws',G+X+','+G+X+'::after'+FS),('ng',PANE+' .cnm b>span'+X+F),('lg',PANE+' .cnm .gp em.nfl.opp'+X+'{background-image:none!important}'),
       ('sg',PANE+' .cnm .gp .gsep'+X+F),('ss',PANE+' .cnm .gp .gsep'+X+FS),('kg',PANE+' .cnm .gp .gwhen'+X+F)]
CK="(id)=>{if(id[0]=='#'){document.querySelector(id).click();return}const l=document.querySelector('label[for=\"'+id+'\"]');(l||document.getElementById(id)).click()}"
def edges(D,thr=24):
    m=D.max()
    if m<thr:return None
    cov=np.clip(D/m,0,1);cov[cov<.15]=0;c=cov.max(axis=0);r=cov.max(axis=1);nz=np.nonzero(c)[0];nr=np.nonzero(r)[0]
    if not len(nz):return None
    return [nz[0]+(1-c[nz[0]]),nr[0]+(1-r[nr[0]]),nz[-1]+c[nz[-1]],nr[-1]+r[nr[-1]]]
def stat(v):
    v=[x for x in v if x is not None]
    return 'n=0' if not v else 'min %.2f mean %.2f max %.2f (n=%d)'%(min(v),sum(v)/len(v),max(v),len(v))
for tok in TOKS:
    E=(eng.Ch if ENG=='ch' else eng.Wk)(tok);E.open(URL+'#'+TAB,2600);E.ev(eng.PREP)
    for i in IDS:E.ev(CK,i);E.wait(1200)
    E.ev("()=>window.__fitAll&&window.__fitAll()");E.wait(900);rows=E.ev(JS,PANE)
    if not rows:print(tok,'no rows');E.close();continue
    y0=min(r['row'][1] for r in rows);vh=E.ev("()=>innerHeight");OUT=[]
    for vi in range(int(os.environ.get('VIEWS','2'))):
        E.ev("(y)=>scrollTo(0,y)",max(0,y0-60+vi*(vh-260)));E.wait(500);sy=E.ev("()=>scrollY");sx=E.ev("()=>scrollX")
        for attempt in range(4):
            E.wait(600*attempt);A,sc=E.view();P={}
            for k,css in PARTS:
                E.ev(ADD,['__p',css]);E.wait(260+150*attempt);P[k],_=E.view();E.ev(DEL,'__p');E.wait(120+150*attempt)
            A2,_=E.view();bad=1 if A.shape!=A2.shape else float((np.abs(A-A2).max(axis=2)>30).mean())
            if bad<2e-5:break
        else:print('   unstable screenshots, view',vi,'skipped',bad);continue
        H=A.shape[0]/sc
        def ink(k,b,pad=3):
            if not b:return None
            x0=int((b[0]-sx-pad)*sc);x1=int((b[2]-sx+pad)*sc)+1;t=int((b[1]-sy-pad)*sc);u=int((b[3]-sy+pad)*sc)+1
            e=edges(np.abs(A[t:u,x0:x1]-P[k][t:u,x0:x1]).max(axis=2).astype(float))
            return None if not e else [(x0+e[0])/sc+sx,(t+e[1])/sc+sy,(x0+e[2])/sc+sx,(t+e[3])/sc+sy]
        for r in rows:
            if r.get('done') or r['row'][1]-sy<2 or r['row'][3]-sy>H-2:continue
            r['done']=1;wg=ink('wg',r['word']);ws=ink('ws',r['word']);ng=ink('ng',r['name'],1);lg=ink('lg',r['logo'],0);sg=ink('sg',r['sep']);ss=ink('ss',r['sep']);kg=ink('kg',r['when'],1)
            if not wg or not lg:continue
            L=r['logo'];d=dict(side=r['side'],w=r['w'],name=r['ntx'],tm=r['tm'],when=r['wtx'],wordw=wg[2]-wg[0],
              name_l=(wg[0]-ng[0]) if ng and r['side']=='a' else None,namebox_l=wg[0]-r['name'][0] if r['side']=='a' else None,
              w_logo=L[0]-wg[2],ws_logo=L[0]-ws[2],w_logoink=lg[0]-wg[2],logo_l=lg[0]-L[0],logo_r=L[2]-lg[2],
              logo_sep=(sg[0]-L[2]) if sg else None,logoink_sep=(sg[0]-lg[2]) if sg else None,sep_when=(kg[0]-sg[2]) if sg and kg else None,sepsh_when=(kg[0]-ss[2]) if ss and kg else None,
              vc=(wg[1]+wg[3])/2-(L[1]+L[3])/2,vcs=(ws[1]+ws[3])/2-(L[1]+L[3])/2,vcl=(wg[1]+wg[3])/2-(lg[1]+lg[3])/2,
              when_r=(ng[2]-kg[2]) if ng and kg and r['side']=='b' else None,line=(kg[2] if kg else lg[2])-wg[0],wl=wg[0]-r['cnm'][0],lx=L[0]-r['cnm'][0],lxr=r['cnm'][2]-L[0])
            OUT.append(d)
    json.dump(OUT,open(f'out/vsat-{LABEL}-{ENG}-{tok}.json','w'))
    print(f'== {LABEL} {E.name} {tok} {TAB} {IDS} rows {len(OUT)} of {len(rows)}')
    for w in ('vs','at'):
        S=[d for d in OUT if d['w']==w]
        if not S:continue
        print(f' "{w}" ink width',stat([d['wordw'] for d in S]))
        for k,lab in [('name_l','word ink left - name ink left (left side)'),('namebox_l','word ink left - name box left (left side)'),('w_logo','word ink -> logo box'),('ws_logo','word ink+shadow -> logo box'),('w_logoink','word ink -> logo ink'),
                      ('vc','word ink centre - logo box centre (down +)'),('vcs','same, ink + shadow')]:print('   %-46s'%lab,stat([d[k] for d in S]))
    for k,lab in [('logo_sep','logo box -> dot ink'),('logoink_sep','logo ink -> dot ink'),('sep_when','dot ink -> kickoff ink'),('sepsh_when','dot ink+shadow -> kickoff ink'),('when_r','name ink right - kickoff ink right (right side)'),('line','line: word ink left to kickoff ink right')]:
        print('   %-46s'%lab,stat([d[k] for d in OUT]))
    for s,k in (('a','lx'),('b','lxr')):
        v=[d[k] for d in OUT if d['side']==s];print(f'   logo box left x within the name cell, side {s}: spread %.2f'%((max(v)-min(v)) if v else 0), '(right-aligned line: by content)' if s=='b' else '')
    E.close()
