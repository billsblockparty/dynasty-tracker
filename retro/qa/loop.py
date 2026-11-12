# loop.py : the loop page ("DynastyCast", site/retro/index.html) checks. Serve a folder holding build.json + retro/{index.html,data.json}.
#   loop.py shots <base url of that folder> <out prefix> [WxH ...]   the six screens, captured after the wipe (default 402x874 and 1280x800)
#   loop.py badge <base url> <out.png>                              the TL badge at 8x (402 wide) + its box and the favicon links
#   loop.py swap  <base url> <folder on disk>                       data.json swapped in place: new scores appear with no navigation; files restored
import sys,json,copy,os,io
sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)));import mmfont
from playwright.sync_api import sync_playwright
mode,U=sys.argv[1],sys.argv[2].rstrip('/')
def start(b,w,h,dpr=2):
    pg=b.new_context(viewport={'width':w,'height':h},device_scale_factor=dpr).new_page();mmfont.setup(pg);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None)
    pg.goto(U+'/retro/index.html');pg.evaluate("document.fonts.ready");pg.wait_for_timeout(500);pg.click('#go');pg.wait_for_timeout(2100);return pg,errs
with sync_playwright() as p:
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    if mode=='shots':
        pre=sys.argv[3];sizes=[tuple(int(v) for v in s.split('x')) for s in sys.argv[4:]] or [(402,874),(1280,800)]
        for w,h in sizes:
            pg,errs=start(b,w,h,2 if w<800 else 1);N=pg.evaluate("SCREENS.length");names=pg.evaluate("SCREENS.map(s=>s.t.join(' '))")
            for i in range(N):
                pg.evaluate("(i)=>go(i-cur)",i);pg.wait_for_timeout(1300);pg.screenshot(path=f'{pre}-{w}-{i+1}.png')
                st=pg.evaluate("()=>({act:document.querySelectorAll('.scr.act').length,rows:document.querySelectorAll('.scr.act .row,.scr.act .card').length,sw:document.documentElement.scrollWidth,vw:innerWidth,mk:(()=>{const r=document.querySelector('.mk').getBoundingClientRect();return [r.x,r.y,r.width,r.height].map(v=>+v.toFixed(2))})(),h1:document.querySelector('h1').getBoundingClientRect().x})")
                print(w,'screen',i+1,names[i],st)
            print(w,'page errors:',errs);pg.close()
    elif mode=='badge':
        pg,errs=start(b,402,874,8);r=pg.evaluate("()=>{const r=document.querySelector('.mk').getBoundingClientRect();return [r.x,r.y,r.width,r.height]}")
        pg.screenshot(path=sys.argv[3],clip={'x':r[0]-8,'y':r[1]-8,'width':r[2]+20,'height':r[3]+20})
        print('badge box',[round(v,2) for v in r],'| icon links',pg.evaluate("()=>[...document.querySelectorAll('link[rel*=icon]')].map(l=>l.rel+' '+(l.sizes||'')+' '+l.type+' '+l.href.slice(0,30)+'… '+l.href.length)"),'| errors',errs);pg.close()
    elif mode=='swap':
        R=sys.argv[3].rstrip('/');DJ=R+'/retro/data.json';BJ=R+'/build.json';orig=json.load(open(DJ));ob=open(BJ).read()
        try:
            pg,errs=start(b,402,874);navs=[];pg.on('framenavigated',lambda f:navs.append(f.url));pg.evaluate("window.__mark=1")
            d=copy.deepcopy(orig);d['v']='swaptest0001'
            if d.get('mus'):d['mus'][0]['ap']=151.51
            else:d['stand'][0]['pf']=1999.9
            json.dump(d,open(DJ,'w'),ensure_ascii=False);json.dump({'v':'2099000000001','built':'t'},open(BJ,'w'))
            v0=pg.evaluate("D.v");pg.evaluate("chk()");pg.wait_for_timeout(600);pend=pg.evaluate("pend&&pend.v");pg.keyboard.press('ArrowRight');pg.wait_for_timeout(900)
            txt=pg.evaluate("document.querySelector('#stage').textContent");pg.evaluate("go(1-cur)");pg.wait_for_timeout(900);txt+=pg.evaluate("document.querySelector('#stage').textContent")
            print('swap: D.v',v0,'->',pg.evaluate("D.v"),'| held until screen change:',pend,'| navigations',len(navs),'| page state kept',pg.evaluate("window.__mark===1"),'| new figure shown',('151.5' in txt) or ('1999.9' in txt),'| errors',errs)
        finally:
            json.dump(orig,open(DJ,'w'),ensure_ascii=False);open(BJ,'w').write(ob)
    b.close()
