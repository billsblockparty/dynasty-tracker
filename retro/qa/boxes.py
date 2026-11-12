# boxes.py dump <url> <tok> <tab> <outprefix>   |   boxes.py cmp <a.json> <b.json> [tol]
import sys;sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import json,collections
import boxes_states as _BS
ST={'standings':[('dumb-h2h',[]),('nerd-h2h',['dn-full']),('nerd-median',['#bm']),('dumb-median',['dn-lean'])],
    'matchups':[('now',[]),('now-detailed',['ld-d']),('now-optimal',['ld-l','lo-o']),('now-slate',['lo-a','lv-s']),('now-team',['lv-p','lc-t']),('w9',['lc-p','mw-9']),('w9-detailed',['ld-d']),('w9-game3',['ld-l','hw9-2'])],
    'playoffs':[('bracket',[]),('final',['bk-fin']),('final-slate',['blv-s']),('builder',['blv-p','pv-c']),('schedule',['pv-s'])]}
JS=r"""(root)=>{const R=document.querySelector(root)||document.body;const sx=scrollX,sy=scrollY;const out=[];const all=(window.__PANE?[R]:[document.querySelector('header'),document.querySelector('.tnav'),R]).filter(Boolean);
for(const A of all)for(const e of [A,...A.querySelectorAll('*')]){const r=e.getBoundingClientRect();const cn=(e.className&&e.className.baseVal!==undefined?e.className.baseVal:e.className)||'';
 const vis=e.getClientRects().length>0&&(!e.checkVisibility||e.checkVisibility({contentVisibilityAuto:true}));
 out.push([e.tagName.toLowerCase()+(cn?'.'+String(cn).trim().split(/\s+/).join('.'):''),vis?+(r.left+sx).toFixed(2):0,vis?+(r.top+sy).toFixed(2):0,vis?+r.width.toFixed(2):0,vis?+r.height.toFixed(2):0,e.parentElement?(e.parentElement.className||'').toString().split(/\s+/)[0]:''])}
return {n:document.querySelectorAll('*').length,sw:document.documentElement.scrollWidth,vw:innerWidth,sh:document.documentElement.scrollHeight,b:out}}"""
ST.update(_BS.ST)
ST.update({'stats':[('pos',[]),('sch',['sx-sch']),('ew',['sx-ew'])],'team-hub':[('team1',[]),('trends',['thv-t'])]})
ST.update({'rosters':[('team1',[]),('team3-tc',['ro-2','rc-t'])],'drafts':[('2026',[]),('2021',['df-2021'])],'paper-trail':[('picks-2027',[]),('picks-2026',['pty-2026']),('players',['js:document.querySelectorAll(".pane-pt .ptb")[1].click()'])],'leaderboards':[('pf',[]),('luck',['lb-luck'])],'players':[('qb',[]),('rb-pos',['pl-rb','plc-p'])],'the-wire':[('all',[])],'compare':[('overview',[]),('players',['ct-pl']),('schedule',['ct-sh'])]})
if sys.argv[1]=='dump':
    import h;from playwright.sync_api import sync_playwright
    url,tok,tab,pre=sys.argv[2:6];root={'standings':'.pane-st','matchups':'.pane-mu','playoffs':'.pane-po','leaderboards':'.pane-lb','players':'.pane-pl','the-wire':'.pane-wr','compare':'.pane-cm','rosters':'.pane-ro','drafts':'.pane-df','paper-trail':'.pane-pt','stats':'.pane-sx','team-hub':'.pane-th'}.get(tab,'body');R={}
    with sync_playwright() as p:
        b=p.chromium.launch();pg,d=h.open_page(b,tok,url+'#'+tab,1000,2600)
        for name,ids in ST[tab]:
            for i in ids:
                if i.startswith('js:'):pg.evaluate('()=>{'+i[3:]+'}')
                elif i[0]=='#':pg.evaluate("(s)=>document.querySelector(s).click()",i)
                elif i[0]=='@':pg.evaluate("(s)=>{document.querySelector('.'+s).open=true}",i[1:])
                else:pg.evaluate("(id)=>{const l=document.querySelector('label[for=\"'+id+'\"]');(l||document.getElementById(id)).click()}",i)
                pg.wait_for_timeout(1300)
            pg.evaluate("()=>window.__fitAll&&window.__fitAll()");pg.wait_for_timeout(700)
            pg.evaluate('()=>{window.__PANE=%d}'%(1 if '--pane' in sys.argv else 0));R[name]=pg.evaluate(JS,root)
            if '--png' in sys.argv:pg.screenshot(path=f'{pre}-{tab}-{tok}-{name}.png',full_page=True)
        b.close()
    json.dump(R,open(f'{pre}-{tab}-{tok}.json','w'));print(pre,tab,tok,{k:(v['n'],v['sw'],v['vw'],v['sh'],len(v['b'])) for k,v in R.items()})
else:
    A=json.load(open(sys.argv[2]));B=json.load(open(sys.argv[3]));tol=float(sys.argv[4]) if len(sys.argv)>4 else .05
    for st in A:
        a,b=A[st],B[st];n=min(len(a['b']),len(b['b']));mv=collections.Counter();sz=collections.Counter();ex={}
        if len(a['b'])!=len(b['b']):print('  ',st,'element count differs',len(a['b']),len(b['b']))
        for i in range(n):
            x,y=a['b'][i],b['b'][i]
            if x[0].split('.')[0]!=y[0].split('.')[0]:print('   order mismatch at',i,x[0],y[0]);break
            dm=max(abs(x[1]-y[1]),abs(x[2]-y[2]));ds=max(abs(x[3]-y[3]),abs(x[4]-y[4]))
            if dm>tol or ds>tol:
                k=x[0].split('.')[0]+'.'+'.'.join(c for c in x[0].split('.')[1:3] if not any(ch.isdigit() for ch in c))+' < '+x[5]
                (sz if ds>tol else mv)[k]+=1;e=ex.get(k,(0,));
                if max(dm,ds)>e[0]:ex[k]=(max(dm,ds),[round(y[j]-x[j],2) for j in (1,2,3,4)])
        print(f"{st}: elements {a['n']} / {b['n']}, boxes {n}, moved only {sum(mv.values())}, resized {sum(sz.values())}; page {a['sw']}x{a['sh']} / {b['sw']}x{b['sh']} (viewport {a['vw']})")
        if '-v' in sys.argv:
            for k,v in (sz+mv).most_common(60):print(f"     {v:4d}  {k[:70]:70s} max {ex[k][0]:.2f}  d(x,y,w,h) {ex[k][1]}  {'resized' if k in sz else 'moved'}")
