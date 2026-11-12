# darkink.py <engine ch|wk> <label> <baseurl> <token...>   -> di-<label>-<engine>-<token>.json
# every visible text node on every tab/state: ink colour, surface under it (sampled from a screenshot taken with all text hidden),
# computed text-shadow / -webkit-text-stroke. FAIL = ink darker than its surface AND a dark shadow or a dark stroke.
import sys,json,io,time,os,re,collections
import numpy as np
from PIL import Image
sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
ENG,LABEL,BASE=sys.argv[1],sys.argv[2],sys.argv[3];TOKS=sys.argv[4:]
PAINT=os.environ.get('PAINT','')=='1';_T=os.environ.get('TABS','');WANT=lambda t:(not _T) or t in _T.split(',')
COLLECT=r"""(root)=>{
const P=s=>{if(!s)return [0,0,0,0];let m=s.match(/rgba?\(([^)]+)\)/);if(m){const a=m[1].split(/[, /]+/).filter(x=>x!=='').map(Number);return [a[0],a[1],a[2],a[3]===undefined?1:a[3]]}
  m=s.match(/color\(srgb ([\d.e-]+) ([\d.e-]+) ([\d.e-]+)(?: \/ ([\d.e-]+))?\)/);return m?[m[1]*255,m[2]*255,m[3]*255,m[4]===undefined?1:+m[4]]:[0,0,0,0]};
const CS=new Map();const cs=e=>{let c=CS.get(e);if(!c){c=getComputedStyle(e);CS.set(e,c)}return c};
const VIS=new Map();   // element -> {ok, op, clip rect}
const info=e=>{let v=VIS.get(e);if(v)return v;const c=cs(e);const p=e.parentElement?info(e.parentElement):{ok:true,op:1,clip:null};
  let ok=p.ok&&c.display!=='none'&&c.visibility!=='hidden';let op=p.op*parseFloat(c.opacity);let clip=p.clip;
  if(ok&&(c.overflowX!=='visible'||c.overflowY!=='visible'||(c.clipPath&&c.clipPath!=='none')||(c.clip&&c.clip!=='auto'))&&e!==document.documentElement&&e!==document.body){const r=e.getBoundingClientRect();const k=[r.left,r.top,r.right,r.bottom];
    clip=clip?[Math.max(clip[0],k[0]),Math.max(clip[1],k[1]),Math.min(clip[2],k[2]),Math.min(clip[3],k[3])]:k}
  v={ok,op,clip};VIS.set(e,v);return v};
const strip=c=>(c||'').toString().split(/\s+/).filter(x=>x&&!/^(t|n|p)-[A-Za-z0-9]+$/.test(x)&&!/^(on|a|b|act|wa|wb|up|dn|fin|h|r|g|gold|last|w|l|done|fut)$/.test(x)&&!/\d{2,}/.test(x)).slice(0,2).join('.');
const lab=e=>{const cn=e.className&&e.className.baseVal!==undefined?e.className.baseVal:e.className;return e.tagName.toLowerCase()+(strip(cn)?'.'+strip(cn):'')};
const comp=e=>{const a=[lab(e)];let p=e.parentElement,n=0;while(p&&p!==document.body&&n<2){const cn=p.className&&p.className.baseVal!==undefined?p.className.baseVal:p.className;if(strip(cn)){a.push(lab(p));n++}p=p.parentElement}
  const pane=e.closest('[class*="pane-"],.tnav,header,.yrs,.pts,#upd');return a.join(' < ')};
const DM=document.querySelector('details[open] .ddm');const sx=scrollX,sy=scrollY,W=document.documentElement.scrollWidth,H=document.documentElement.scrollHeight,out=[];
const push=(pe,R,txt,pseudo)=>{if(root&&!pe.closest(root))return;if(DM&&!DM.contains(pe)){const m=DM.getBoundingClientRect();if(R.right>m.left&&R.left<m.right&&R.bottom>m.top&&R.top<m.bottom)return}const v=info(pe);if(!v.ok||v.op<.02)return;if(R.width<.5||R.height<.5)return;
  if(v.clip&&(R.right<=v.clip[0]+.5||R.left>=v.clip[2]-.5||R.bottom<=v.clip[1]+.5||R.top>=v.clip[3]-.5))return;
  if(R.right+sx<1||R.left+sx>W-1||R.bottom+sy<1||R.top+sy>H-1)return;
  const c=pseudo?getComputedStyle(pe,pseudo):cs(pe);const svg=!!pe.closest('svg')&&pe.tagName.toLowerCase()!=='foreignobject'&&!pe.closest('foreignObject');
  let fg=P(svg?c.fill:c.color);const tf=c.webkitTextFillColor;if(!svg&&tf&&tf!==c.color)fg=P(tf);
  if(fg[3]<.02)return;const z=pe.currentCSSZoom||1;
  out.push({k:comp(pe)+(pseudo||''),t:txt.slice(0,16),x:+(R.left+sx).toFixed(2),y:+(R.top+sy).toFixed(2),w:+R.width.toFixed(2),h:+R.height.toFixed(2),fg:fg.map(x=>+x.toFixed(3)),op:+v.op.toFixed(3),
    sh:c.textShadow||'none',sw:parseFloat(c.webkitTextStrokeWidth)||0,sc:P(c.webkitTextStrokeColor),fs:+(parseFloat(c.fontSize)*z).toFixed(2),fw:+c.fontWeight||400,svg})};
const tw=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let n;const g=document.createRange();
while(n=tw.nextNode()){const t=n.textContent.trim();if(!t)continue;const pe=n.parentElement;if(!pe)continue;const tg=pe.tagName.toLowerCase();if(tg==='style'||tg==='script'||tg==='title'||tg==='noscript'||tg==='option'||tg==='desc')continue;
  if(!pe.getClientRects().length&&!pe.closest('svg'))continue;if(pe.checkVisibility&&!pe.checkVisibility({contentVisibilityAuto:true}))continue;g.selectNodeContents(n);const rs=[...g.getClientRects()].filter(x=>x.width>.5&&x.height>.5);if(!rs.length)continue;
  // one entry per text node, at its widest line box
  let R=rs[0];for(const x of rs)if(x.width>R.width)R=x;push(pe,R,t,null)}
document.body.querySelectorAll('*').forEach(e=>{if(!e.getClientRects().length)return;for(const ps of ['::before','::after']){const c=getComputedStyle(e,ps);const ct=c.content;
  if(!ct||ct==='none'||ct==='normal'||!/^["']/.test(ct))continue;const t=ct.replace(/^["']|["']$/g,'').trim();if(!t||c.display==='none'||c.visibility==='hidden')continue;
  const r=e.getBoundingClientRect();const w=parseFloat(c.width),hh=parseFloat(c.height);let R=r;if(c.position==='absolute'&&w>0&&hh>0){R={left:r.left+(r.width-w)/2,top:r.top+(r.height-hh)/2,width:w,height:hh,right:r.left+(r.width+w)/2,bottom:r.top+(r.height+hh)/2}}
  push(e,R,t,ps)}});
return {W,H,vw:innerWidth,n:out}}"""
HIDE="*,*::before,*::after{color:transparent!important;text-shadow:none!important;-webkit-text-stroke:0 transparent!important;-webkit-text-fill-color:transparent!important;transition:none!important;animation:none!important}svg text,svg tspan{fill:transparent!important;stroke:transparent!important}"
PREP="()=>{document.querySelectorAll('.ltot,.mpk,.mcol,.pane *').forEach(e=>{if(e.getClientRects().length&&getComputedStyle(e).position==='sticky')e.style.setProperty('position','static','important')});if(!document.getElementById('__st')){const s=document.createElement('style');s.id='__st';s.textContent='.tnav{position:static!important}*{transition:none!important;animation:none!important;scroll-behavior:auto!important}';document.head.appendChild(s)}}"
HIDE_ON="(c)=>{const s=document.createElement('style');s.id='__hide';s.textContent=c;document.head.appendChild(s)}"
HIDE_OFF="()=>{const s=document.getElementById('__hide');if(s)s.remove()}"
GROUPS=r"""(skip)=>{const G={};document.querySelectorAll('input[type=radio]').forEach(i=>{if(!i.id||!i.name||skip.includes(i.name))return;const l=document.querySelector('label[for="'+i.id+'"]');if(!l||!l.getClientRects().length)return;(G[i.name]=G[i.name]||[]).push([i.id,i.checked])});return G}"""
CLICK="(id)=>{const l=document.querySelector('label[for=\"'+id+'\"]');if(l)l.click();else{const i=document.getElementById(id);if(i)i.click()}}"
def lum(c):
    c=[x/255 for x in c[:3]];c=[x/12.92 if x<=.03928 else ((x+.055)/1.055)**2.4 for x in c];return .2126*c[0]+.7152*c[1]+.0722*c[2]
def pcol(s):
    out=[]
    for m in re.finditer(r'rgba?\(([^)]+)\)',s):
        a=[float(x) for x in re.split(r'[,\s/]+',m.group(1).strip()) if x!=''];out.append(a[:3]+[a[3] if len(a)>3 else 1.0])
    for m in re.finditer(r'color\(srgb ([\d.e-]+) ([\d.e-]+) ([\d.e-]+)(?: / ([\d.e-]+))?\)',s):
        out.append([float(m.group(1))*255,float(m.group(2))*255,float(m.group(3))*255,float(m.group(4)) if m.group(4) else 1.0])
    for m in re.finditer(r'okl(?:ch|ab)\(([\d.e-]+)%? [\d.e-]+ [\d.e-]+(?: / ([\d.e-]+))?\)',s):
        L=float(m.group(1));L=L/100 if L>1 else L;v=255*max(0,L)**3;out.append([v,v,v,float(m.group(2)) if m.group(2) is not None else 1.0])
    return out
def judge(nodes,im,sc):
    res=[]
    Hh,Ww=im.shape[:2]
    for n in nodes:
        x0=int(max(0,np.floor(n['x']*sc)));y0=int(max(0,np.floor(n['y']*sc)));x1=int(min(Ww,np.ceil((n['x']+n['w'])*sc)));y1=int(min(Hh,np.ceil((n['y']+n['h'])*sc)))
        if x1<=x0 or y1<=y0:continue
        bg=np.median(im[y0:y1,x0:x1].reshape(-1,3),axis=0)
        a=n['fg'][3]*n['op'];ink=[n['fg'][i]*a+bg[i]*(1-a) for i in range(3)]
        li,lb=lum(ink),lum(bg);cr=(max(li,lb)+.05)/(min(li,lb)+.05)
        dsh=any(c[3]>.05 and lum(c)<.2 for c in pcol(n['sh'])) if n['sh'] and n['sh']!='none' else False
        dst=n['sw']>0 and n['sc'][3]>.05 and lum(n['sc'])<.2
        large=n['fs']>=24 or (n['fs']>=18.66 and n['fw']>=700)
        n2=dict(k=n['k'],t=n['t'],ink=[round(v) for v in ink],bg=[round(float(v)) for v in bg],cr=round(float(cr),2),fs=n['fs'],fw=n['fw'],sh=n['sh'] if dsh else '',sw=n['sw'] if dst else 0,
                fail=bool(li<lb and (dsh or dst)),dark=bool(li<lb),low=bool(cr<(3 if large else 4.5)),large=large,x=n['x'],y=n['y'],w=n['w'],h=n['h'])
        res.append(n2)
    return res
class Ch:
    def __init__(s,tok):
        import h;from playwright.sync_api import sync_playwright
        s.h=h;s.pw=sync_playwright().start();s.b=s.pw.chromium.launch();s.tok=tok;s.pg=None
    def open(s,url):
        if s.pg:s.pg.close()
        s.pg,_=s.h.open_page(s.b,s.tok,url,1000,2200)
    def ev(s,js,arg=None):return s.pg.evaluate(js,arg) if arg is not None else s.pg.evaluate(js)
    def wait(s,ms):s.pg.wait_for_timeout(ms)
    def shot(s,W,H):
        im=np.asarray(Image.open(io.BytesIO(s.pg.screenshot(full_page=True,scale='css'))).convert('RGB')).astype(np.float32);return im,im.shape[1]/W
    def close(s):s.b.close();s.pw.stop()
class Wk:
    def __init__(s,tok):
        from selenium import webdriver;from selenium.webdriver.webkitgtk.options import Options;from selenium.webdriver.webkitgtk.service import Service
        os.environ['DISPLAY']=':97';os.environ.pop('GDK_SCALE',None)
        o=Options();o.binary_location='/usr/lib/x86_64-linux-gnu/webkit2gtk-4.1/MiniBrowser';o.add_argument('--automation')
        s.d=webdriver.WebKitGTK(options=o,service=Service(executable_path='/usr/bin/WebKitWebDriver',env=dict(os.environ)));s.W=int(tok);s.d.set_window_size(max(s.W+40,500),1100);s.d.set_script_timeout(120)
    def open(s,url):
        base,hsh=(url.split('#')+[''])[:2];s.d.switch_to.default_content()
        s.d.get('about:blank');s.d.get(base.rsplit('/',1)[0]+f'/__frame.html?w={s.W}&u=index.html'+('%23'+hsh if hsh else ''));time.sleep(1.5);s.d.switch_to.frame('f');time.sleep(4.5)
    def ev(s,js,arg=None):
        return s.d.execute_script('return ('+js+')(arguments[0])',arg) if arg is not None else s.d.execute_script('return ('+js+')()')
    def wait(s,ms):time.sleep(ms/1000)
    def shot(s,W,H):
        parts=[];y=0;sc=None
        # the picture is stitched from scrolled views: anything sticky would be drawn again at the top of every piece, over the page
        s.d.execute_script("document.querySelectorAll('body *').forEach(e=>{if(e.getClientRects().length&&getComputedStyle(e).position==='sticky')e.style.setProperty('position','static','important')})")
        while y<H:
            s.d.execute_script('scrollTo(0,arguments[0])',y);time.sleep(.35);yy=s.d.execute_script('return scrollY')
            s.d.switch_to.default_content();prev=None
            for k in range(6):   # the same picture twice in a row, or the page was still painting
                png=s.d.get_screenshot_as_png();im=np.asarray(Image.open(io.BytesIO(png)).convert('RGB')).astype(np.float32)
                if prev is not None and prev.shape==im.shape and (np.abs(prev-im).max(axis=2)>8).mean()<1e-5:break
                prev=im;time.sleep(.35)
            vp=s.d.execute_script('return innerWidth');s.d.switch_to.frame('f');sc=im.shape[1]/vp
            parts.append((yy,im[:int(1000*sc),:int(round(W*sc))]));y+=1000
        full=np.zeros((int(np.ceil(H*sc))+2,int(round(W*sc)),3),np.float32)
        for yy,im in parts:
            a=int(round(yy*sc));hh=min(im.shape[0],full.shape[0]-a);full[a:a+hh,:im.shape[1]]=im[:hh,:full.shape[1]]
        s.d.execute_script('scrollTo(0,0)');return full,sc
    def close(s):s.d.quit()
def run(tok):
    E=(Ch if ENG=='ch' else Wk)(tok);R=collections.OrderedDict()
    def audit(name,root=''):
        for attempt in range(4):
            # the page must not move between reading the text nodes and taking the picture: read, shoot, read again, compare
            E.ev(PREP);E.wait(120+400*attempt);c=E.ev(COLLECT,root or 0);on=E.shot(c['W'],c['H'])[0] if PAINT else None;E.ev(HIDE_ON,HIDE);E.wait(150);im,sc=E.shot(c['W'],c['H']);E.ev(HIDE_OFF);E.wait(60);c2=E.ev(COLLECT,root or 0)
            if c['H']==c2['H'] and len(c['n'])==len(c2['n']) and all(abs(a['y']-b['y'])<.6 and abs(a['x']-b['x'])<.6 for a,b in zip(c['n'],c2['n'])):break
            print(f'  {tok} {name}: page moved during capture, again',flush=True)
        if PAINT and on is not None and on.shape==im.shape:
            # PAINT=1: a text node counts only if it is painted, i.e. pixels in its box change when text is switched off
            # (WebKitGTK reports boxes for SVG axis text and readouts that are not drawn)
            d=np.abs(on-im).max(axis=2)>12;keep=[]
            for n in c['n']:
                x0=int(max(0,np.floor(n['x']*sc)));y0=int(max(0,np.floor(n['y']*sc)));x1=int(np.ceil((n['x']+n['w'])*sc));y1=int(np.ceil((n['y']+n['h'])*sc))
                if d[y0:y1,x0:x1].any():keep.append(n)
            print(f'  {tok} {name}: {len(c["n"])-len(keep)} text nodes not painted, left out',flush=True);c['n']=keep
        R[name]=judge(c['n'],im,sc);f=sum(1 for x in R[name] if x['fail']);print(f'  {tok} {name}: {len(R[name])} text nodes, {f} FAIL, {sum(1 for x in R[name] if x["low"])} low-contrast',flush=True)
    def click(i,ms=650):E.ev(CLICK,i);E.wait(ms)
    SK=['tab','tgrp','gloss','dens']
    def sweep(tab,prefix,caps,done):
        G=E.ev(GROUPS,SK)
        for name,opts in G.items():
            if name in done:continue
            done.add(name);cap=caps.get(name,caps.get('*',2));dflt=[o[0] for o in opts if o[1]];n=0
            for oid,chk in opts:
                if chk or n>=cap:continue
                click(oid);n+=1;audit(f'{tab}/{prefix}{name}={oid}')
                if name in caps.get('nest',()):sweep(tab,f'{prefix}{oid}>',{'*':caps.get('nestcap',1)},set(done))
            if dflt:click(dflt[0],400)
    def tab(t):
        E.open(BASE+'#'+t)
        if ENG=='wk':
            E.ev("()=>{try{localStorage.clear();sessionStorage.clear()}catch(e){}}");E.open(BASE+'#'+t)

    # ---- Standings
    if WANT('standings'):
        tab('standings');audit('standings/Dumb H2H');click('dn-full');audit('standings/Nerd H2H');E.ev("()=>document.getElementById('bm').click()");E.wait(1200);audit('standings/Nerd Median');click('dn-lean');audit('standings/Dumb Median');E.ev("()=>document.getElementById('bh').click()");E.wait(1200)
        click('gl-s');audit('standings/Dumb glossary');click('dn-full');audit('standings/glossary');E.ev("()=>{const u=document.getElementById('upd');if(u)u.hidden=false}");E.wait(200);audit('standings/refresh pill','#upd')
    # ---- Matchups: current week (projection states), then a final week (lineups with FINAL cells)
    if WANT('matchups'):
        tab('matchups');audit('matchups/current week');sweep('matchups','now>',{'*':1,'mwk':0,'mus':2},set())
        click('mw-9',1500);audit('matchups/week 9');sweep('matchups','w9>',{'*':1,'mwk':0,'mus':1},set())
        tab('matchups');E.ev("""()=>{let n=0;document.querySelectorAll('.pane-mu .cr.lu .cv.pjc').forEach((c,i)=>{if(!c.getClientRects().length||i%3==2)return;const f=c.querySelector('.fs');const v=(f.firstChild&&f.firstChild.nodeType==3?f.firstChild.nodeValue:'1.0');c.classList.remove('pjc');c.classList.add('act');c.innerHTML='<span class=\"fs lv\" title=\"Projected 1.0\"><em class=\"fdf\"></em>'+v.trim()+'<small>LIVE</small></span>';n++});return n}""");E.wait(600);audit('matchups/LIVE simulated')
        tab('matchups');E.ev("()=>{document.querySelector('.pane-mu .wdd').open=true}");E.wait(500);audit('matchups/week menu open')
        tab('matchups');click('gl-s');audit('matchups/glossary')
        tab('matchups');click('ld-d');click('lo-o');audit('matchups/detailed optimal');E.ev("()=>{const u=document.getElementById('upd');if(u)u.hidden=false}");E.wait(200);audit('matchups/refresh pill','#upd')
    if WANT('playoffs'):
        tab('playoffs');audit('playoffs/default');sweep('playoffs','',{'*':1,'pview':5,'bk':5},set())
        tab('playoffs');click('pv-c');E.ev("()=>{document.querySelector('.pane-po .dd-a').open=true}");E.wait(500);audit('playoffs/builder menu open');click('pw-15');audit('playoffs/builder wk15')
        tab('playoffs');click('pv-s');click('ps-3');audit('playoffs/schedule team 4');E.ev("()=>{document.querySelector('.pane-po .dd-s').open=true}");E.wait(500);audit('playoffs/schedule menu open')
        tab('playoffs');click('gl-s');audit('playoffs/glossary')
    if WANT('rosters'):
        tab('rosters');audit('rosters/default');sweep('rosters','',{'*':1,'ros':3},set());click('ro-5');click('gl-s');audit('rosters/team 6 + glossary')
    if WANT('players'):
        tab('players');audit('players/default');sweep('players','',{'*':1,'plp':6},set());click('gl-s');audit('players/glossary')
    if WANT('the-wire'):
        tab('the-wire');audit('the-wire/default')
        for i in (1,5,7):
            E.ev("(i)=>{const b=document.querySelectorAll('.pane-wr .wpb')[i];if(b)b.click()}",i);E.wait(700);audit(f'the-wire/filter {i}')
        click('gl-s');audit('the-wire/glossary')
    if WANT('drafts'):
        tab('drafts');audit('drafts/default');sweep('drafts','',{'*':1,'dfy':6},set())
    if WANT('paper-trail'):
        SHEET="()=>{const b=[...document.querySelectorAll('.pane-pt .ptv-k .ptk')].filter(e=>e.getClientRects().length&&e.querySelector('.ptxn'));const c=b.find(e=>+e.querySelector('.ptxn').textContent.trim()>=2)||b[0];if(c)c.click();return !!c}"
        tab('paper-trail');audit('paper-trail/picks');sweep('paper-trail','',{'*':1,'pty':8},set())
        tab('paper-trail');E.ev(SHEET);E.wait(1200);audit('paper-trail/pick sheet (trade steps)','.pts')
        tab('paper-trail');E.ev("()=>{document.querySelector('label[for=pty-2026]').click()}");E.wait(900);E.ev(SHEET);E.wait(1200);audit('paper-trail/drafted pick sheet','.pts')
        tab('paper-trail');E.ev("()=>{const b=document.querySelectorAll('.pane-pt .ptb')[1];if(b)b.click()}");E.wait(1200);audit('paper-trail/players')
        E.ev("()=>{const b=[...document.querySelectorAll('.pane-pt .ptv-p .ptk')].filter(e=>e.getClientRects().length);const c=b.find(e=>/Traded/.test(e.textContent))||b[0];if(c)c.click()}");E.wait(1200);audit('paper-trail/player sheet','.pts')
    if WANT('stats'):
        tab('stats');audit('stats/default');sweep('stats','',{'*':2,'sxs':20,'nest':('sxs',),'nestcap':2},set())
        tab('stats');click('sx-ew');E.ev("()=>{const c=document.querySelectorAll('.pane-sx .ewm .mx[data-w]')[7];if(c)c.click()}");E.wait(500);audit('stats/every-week cell selected')
        tab('stats');click('gl-s');audit('stats/glossary')
    if WANT('leaderboards'):
        tab('leaderboards');audit('leaderboards/default');sweep('leaderboards','',{'*':1,'lbm':4},set());click('lb-def');click('gl-s');audit('leaderboards/def + glossary')
    if WANT('compare'):
        tab('compare');audit('compare/default');sweep('compare','',{'*':0,'csub':8},set());click('ct-pl');click('cs-g');audit('compare/players per game');click('ca-9');click('cb-0');audit('compare/players swapped pair');click('ct-sc');audit('compare/scoring swapped');click('gl-s');audit('compare/glossary');E.ev("()=>{document.querySelector('.pane-cm .dd-a').open=true}");E.wait(500);audit('compare/menu open')
    if WANT('team-hub'):
        tab('team-hub');audit('team-hub/default')
        for i in ('thx-1','thx-4','thx-9','thx-0'):
            click(i,1500);audit('team-hub/team '+i)
        click('thx-6',1500);click('thv-t',900);audit('team-hub/trends team 7');click('thw-3');audit('team-hub/trends team 7 week 3');click('thx-2',1500);audit('team-hub/trends team 3')
        click('thv-d');click('gl-s');audit('team-hub/team 3 + glossary')
    json.dump(R,open(f"out/di-{LABEL}-{ENG}-{tok}.json","w"));E.close()
for t in TOKS:run(t)
