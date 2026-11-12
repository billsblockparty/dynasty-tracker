# two engines behind one interface: Chromium (Playwright; device tokens 360P/402P/440P at DPR 3, plain widths at DPR 2) and
# WebKitGTK (MiniBrowser through WebDriver, page in an iframe of the exact width; GDK_SCALE = device scale)
import sys,io,os,time
import numpy as np
from PIL import Image
sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
PHONE={'360P':424,'402P':473,'440P':518}
def _np(png):return np.asarray(Image.open(io.BytesIO(png)).convert('RGB')).astype(np.int16)
class Ch:
    name='Chromium'
    def __init__(s,tok,dpr=2):
        import h;from playwright.sync_api import sync_playwright
        s.h=h;s.pw=sync_playwright().start();s.b=s.pw.chromium.launch();s.tok=tok;s.pg=None;s.dpr=dpr
    def open(s,url,wait=2300):
        if s.pg:s.pg.close()
        if s.tok in PHONE:s.pg,_=s.h.open_page(s.b,s.tok,url,1000,wait)
        else:
            ctx=s.b.new_context(viewport={'width':int(s.tok),'height':1000},device_scale_factor=s.dpr);s.pg=ctx.new_page();s.pg.route('**/api.sleeper.app/**',lambda r:r.abort());s.h.setup(s.pg)
            s.pg.goto(url);s.pg.evaluate('()=>document.fonts.ready');s.pg.wait_for_timeout(wait)
    def ev(s,js,arg=None):return s.pg.evaluate(js,arg) if arg is not None else s.pg.evaluate(js)
    def wait(s,ms):s.pg.wait_for_timeout(ms)
    def view(s):
        im=_np(s.pg.screenshot());return im,im.shape[1]/s.pg.evaluate('innerWidth')
    def close(s):s.b.close();s.pw.stop()
class Wk:
    name='WebKitGTK'
    def __init__(s,tok,dpr=None):
        from selenium import webdriver;from selenium.webdriver.webkitgtk.options import Options;from selenium.webdriver.webkitgtk.service import Service
        s.W=PHONE.get(tok) or int(tok);dpr=dpr or (3 if s.W<1000 else 2)
        os.environ['DISPLAY']=':97';os.environ['GDK_SCALE']=str(dpr)
        o=Options();o.binary_location='/usr/lib/x86_64-linux-gnu/webkit2gtk-4.1/MiniBrowser';o.add_argument('--automation')
        s.d=webdriver.WebKitGTK(options=o,service=Service(executable_path='/usr/bin/WebKitWebDriver',env=dict(os.environ)));s.d.set_window_size(max(s.W+40,500),1100);s.d.set_script_timeout(120)
    def open(s,url,wait=2300):
        base,hsh=(url.split('#')+[''])[:2];s.d.switch_to.default_content()
        s.d.get('about:blank');s.d.get(base.rsplit('/',1)[0]+f'/__frame.html?w={s.W}&u=index.html'+('%23'+hsh if hsh else ''));time.sleep(1.5);s.d.switch_to.frame('f');time.sleep(wait/1000+2.5)
    def ev(s,js,arg=None):
        return s.d.execute_script('return ('+js+')(arguments[0])',arg) if arg is not None else s.d.execute_script('return ('+js+')()')
    def wait(s,ms):time.sleep(ms/1000)
    def view(s):
        s.d.switch_to.default_content();png=s.d.get_screenshot_as_png();vp=s.d.execute_script('return innerWidth');s.d.switch_to.frame('f')
        im=_np(png);sc=im.shape[1]/vp;return im[:int(1000*sc),:int(round(s.W*sc))],sc
    def close(s):s.d.quit()
PREP="()=>{if(!document.getElementById('__st')){const s=document.createElement('style');s.id='__st';s.textContent='.tnav{position:static!important}*{transition:none!important;animation:none!important;scroll-behavior:auto!important}#upd{display:none!important}';document.head.appendChild(s)}}"
# text off, everything else as painted: fill colour only (currentColor borders and backgrounds stay), no shadow, no outline
HIDE="*,*::before,*::after{-webkit-text-fill-color:transparent!important;text-shadow:none!important;-webkit-text-stroke:0 transparent!important}svg text,svg tspan{fill:transparent!important;stroke:transparent!important}"
HIDE_ON="(c)=>{const s=document.createElement('style');s.id='__hide';s.textContent=c;document.head.appendChild(s)}"
HIDE_OFF="()=>{const s=document.getElementById('__hide');if(s)s.remove()}"
def inkscan(E,items,thr=30,step=None):
    """items: dicts with x,y,w,h (document CSS px). Adds 'ink' = [l,t,r,b] (document CSS px, text ink incl. shadow / outline) or None.
    The ink is every pixel that differs between a screenshot and the same screenshot with all text switched off."""
    H=E.ev("()=>document.documentElement.scrollHeight");vh=E.ev("()=>innerHeight");step=step or vh-220;y=0;todo=list(items);masks=[]
    while y<H and todo:
        E.ev("(y)=>scrollTo(0,y)",y);E.wait(350);sy=E.ev("()=>scrollY")
        for attempt in range(4):
            # A (text on), B (text off), A2 (text on again): A and A2 must be the same picture, or something else was still painting
            A,sc=E.view();E.ev(HIDE_ON,HIDE);E.wait(200+150*attempt);B,_=E.view();E.ev(HIDE_OFF);E.wait(150+150*attempt);A2,_=E.view()
            if A.shape==B.shape==A2.shape and (np.abs(A-A2).max(axis=2)>thr).mean()<2e-5:break
            E.wait(500)
        else:
            print('   unstable screenshots at scroll',sy,'- skipped',flush=True);y+=step;continue
        M=(np.abs(A-B).max(axis=2)>thr);vhh=A.shape[0]/sc;rest=[]
        for it in todo:
            if it['y']-sy<1 or it['y']+it['h']-sy>vhh-1:rest.append(it);continue
            x0=int(round(it['x']*sc));x1=int(round((it['x']+it['w'])*sc));y0=int(round((it['y']-sy)*sc));y1=int(round((it['y']+it['h']-sy)*sc))
            it['dev']=[x0,y0,x1,y1];it['sc']=sc;m=M[y0:y1,x0:x1];it['ink']=None;it['bands_ink']=[]
            if m.any():
                cs=np.nonzero(m.any(axis=0))[0];rs=np.nonzero(m.any(axis=1))[0];it['ink']=[int(cs[0]),int(rs[0]),int(cs[-1])+1,int(rs[-1])+1]   # device px inside the box
            for bn in it.get('bands',[]):
                b0=max(0,int(round((bn[1]-it['y'])*sc)));b1=min(m.shape[0],int(round((bn[2]-it['y'])*sc)));mm=m[b0:b1]
                if mm.any() and len(bn)>4:
                    # coverage-weighted edges: every pixel is unmixed into text colour / black shadow / the surface (the text-off picture),
                    # so a glyph edge that covers part of a device pixel counts as that part (a plain threshold is +-1 device px)
                    a_=A[y0+b0:y0+b1,x0:x1].astype(np.float64);b_=B[y0+b0:y0+b1,x0:x1].astype(np.float64);D=a_-b_;u=np.array(bn[4],float)-b_;v=-b_
                    uu=(u*u).sum(2);vv=(v*v).sum(2);uv=(u*v).sum(2);ud=(u*D).sum(2);vd=(v*D).sum(2);det=uu*vv-uv*uv;ok=det>1e-3*uu*vv+1
                    fa=np.where(ok,(ud*vv-vd*uv)/np.where(ok,det,1),ud/np.maximum(uu,1));fb=np.where(ok,(vd*uu-ud*uv)/np.where(ok,det,1),0)
                    cov=np.clip(np.clip(fa/max(bn[5],.05),0,1)+np.clip(fb,0,1),0,1);cov[cov<.1]=0;cols=cov.max(axis=0);rws=cov.max(axis=1);nz=np.nonzero(cols)[0];nr=np.nonzero(rws)[0]
                    if len(nz):it['bands_ink'].append([bn[0],float(nz[0]+(1-cols[nz[0]])),b0+float(nr[0]+(1-rws[nr[0]])),float(nz[-1]+cols[nz[-1]]),b0+float(nr[-1]+rws[nr[-1]])])
                    else:it['bands_ink'].append([bn[0],None])
                elif mm.any():
                    cs=np.nonzero(mm.any(axis=0))[0];rs=np.nonzero(mm.any(axis=1))[0];it['bands_ink'].append([bn[0],int(cs[0]),b0+int(rs[0]),int(cs[-1])+1,b0+int(rs[-1])+1])
                else:it['bands_ink'].append([bn[0],None])
            it['shot']=(A,sy)
        todo=rest;y+=step
    for it in todo:it['ink']=None;it['sc']=None
    return items
def gaps(it,box=None):
    """gaps in CSS px between ink [l,t,r,b] (device px in the item box) and the inner edge of the frame: (L,R,T,B)"""
    if not it.get('ink') and box is None:return None
    l,t,r,b=box or it['ink'];x0,y0,x1,y1=it['dev'];sc=it['sc'];f=it.get('f',[0,0,0,0])   # frame widths L,T,R,B in CSS px
    fl,ft,fr,fb=[int(round(v*sc)) for v in f]
    return ((l-fl)/sc,((x1-x0)-fr-r)/sc,(t-ft)/sc,((y1-y0)-fb-b)/sc)
