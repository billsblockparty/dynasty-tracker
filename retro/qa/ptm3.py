# ptm3.py <ch|wk> <baseurl> <tok> [year ids...] : Paper Trail > Picks, from screenshots (coverage-weighted ink incl. shadow):
#   tiles (TIMES TRADED, projected, drafted pick): ink-to-tile gaps L,R,T,B;  heads / coach names: ink centre vs the column / picture centre;
#   NFL slot: ink right edge vs the name column's right edge
import sys,json,collections;sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)));import eng
eng.PHONE.update({"874L":0,"956L":0})
ENG,BASE,tok=sys.argv[1:4];YEARS=sys.argv[4:] or ['','pty-2026']
JS=r"""()=>{const sx=scrollX,sy=scrollY,o=[];const P=s=>{const m=(s||'').match(/rgba?\(([^)]+)\)/);const a=m[1].split(/[, /]+/).filter(x=>x!=='').map(Number);return a};
const vis=e=>e.getClientRects().length>0;
for(const [k,s] of [['traded','.ptv-k .ptxn'],['proj','.ptv-k .ptn.ptpj'],['pick','.ptv-k .ptn:not(.ptpj)']])document.querySelectorAll(s).forEach(e=>{if(!vis(e))return;const r=e.getBoundingClientRect();const b=e.querySelector('b')||e;const c=getComputedStyle(b);const m=P(c.color);
 o.push({k,t:b.textContent.trim(),x:r.left+sx,y:r.top+sy,w:r.width,h:r.height,f:[0,0,k==='pick'?1:0,0],bands:[['d',r.top+sy,r.bottom+sy,b.textContent.trim(),m.slice(0,3),m[3]===undefined?1:m[3]]]})});
const free=(k,e,refc,refr)=>{if(!vis(e))return;const g=document.createRange();g.selectNodeContents(e);const r=g.getBoundingClientRect();if(!r.width)return;const c=getComputedStyle(e);const m=P(c.color);
 o.push({k,t:e.textContent.trim(),x:r.left+sx-5,y:r.top+sy-3,w:r.width+10,h:r.height+6,f:[0,0,0,0],refc:refc==null?null:refc+sx,refr:refr==null?null:refr+sx,bands:[['d',r.top+sy-3,r.bottom+sy+3,'',m.slice(0,3),m[3]===undefined?1:m[3]]]})};
const cx=e=>{const r=e.getBoundingClientRect();return (r.left+r.right)/2};
document.querySelectorAll('.ptv-k .pthx i').forEach(e=>free('head TIMES/TRADED vs tile column',e,(()=>{const p=e.closest('.ptp');const t=[...p.querySelectorAll('.ptxn')].find(vis);return t?cx(t):cx(e.parentElement)})()));
document.querySelectorAll('.ptv-k .pthv').forEach(e=>free('head VIA vs picture',e,(()=>{const p=e.closest('.ptp');const t=[...p.querySelectorAll('.ptvl .pav')].find(vis);return t?cx(t):cx(e)})()));
document.querySelectorAll('.ptv-k .ptvc').forEach(e=>free('coach vs picture',e,cx(e.parentElement.querySelector('.pav'))));
document.querySelectorAll('.ptv-k .ptns').forEach(e=>{const its=[...e.querySelectorAll('i:not(.ptbl)')];const l=its[its.length-1];if(l)free('NFL slot right edge',l,null,e.parentElement.getBoundingClientRect().right)});
return o}"""
CK="(id)=>{const l=document.querySelector('label[for=\"'+id+'\"]');(l||document.getElementById(id)).click()}"
E=(eng.Ch if ENG=='ch' else eng.Wk)(tok)
for yid in YEARS:
    E.open(BASE+'#paper-trail')
    if ENG=='wk':E.ev("()=>{try{localStorage.clear();sessionStorage.clear()}catch(e){}}");E.open(BASE+'#paper-trail')
    if yid:E.ev(CK,yid);E.wait(1600)
    E.ev(eng.PREP);E.wait(300);items=E.ev(JS);eng.inkscan(E,items,thr=12);R=collections.OrderedDict()
    for it in items:
        bi=[b for b in it.get('bands_ink',[]) if len(b)>2 and b[1] is not None]
        if not bi:continue
        l,t,r,b=bi[0][1:];sc=it['sc']
        if it['k'] in ('traded','proj','pick'):
            g=eng.gaps(it,bi[0][1:]);R.setdefault(it['k'],[]).append((it['t'],[round(x,2) for x in g],round(it['w'],2)))
        elif it.get('refc') is not None:
            R.setdefault(it['k'],[]).append((it['t'],round(it['x']+(l+r)/2/sc-it['refc'],2)))
        else:
            R.setdefault(it['k'],[]).append((it['t'],round(it['x']+r/sc-it['refr'],2)))
    print(f'===== {E.name} {tok} Paper Trail picks {yid or "default year"}')
    for k,v in R.items():
        if k in ('traded','proj','pick'):
            print(f"  {k}: n={len(v)} widths {sorted(set(x[2] for x in v))} worst |L-R| {max(abs(x[1][0]-x[1][1]) for x in v):.2f} worst |T-B| {max(abs(x[1][2]-x[1][3]) for x in v):.2f} min L/R {min(min(x[1][0],x[1][1]) for x in v):.2f} min T/B {min(min(x[1][2],x[1][3]) for x in v):.2f}")
            by=collections.OrderedDict()
            for x in v:by.setdefault(x[0],x)
            if k=='traded':
                for t,x in by.items():print(f"      '{t}': L {x[1][0]:.2f} R {x[1][1]:.2f} T {x[1][2]:.2f} B {x[1][3]:.2f}")
        else:
            d=[x[1] for x in v];by=collections.OrderedDict()
            for x in v:by.setdefault(x[0],[]).append(x[1])
            print(f"  {k}: n={len(v)} offset min {min(d):+.2f} max {max(d):+.2f} | "+', '.join(f"{t} {min(a):+.2f}" for t,a in list(by.items())[:12]))
E.close()
