# QA harness for the themed tracker copy: real Classic fonts + Martian Mono (condensed-only face, as the theme requests it)
import sys,os
sys.path.insert(0,os.path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)),'..','..','tools'));import realfonts,device
D=os.path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)),'..','fonts','')   # retro/fonts: the unmodified @fontsource-variable/martian-mono files
UR={'latin':'U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD',
    'latin-ext':'U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF'}
# what Google Fonts returns for  family=Martian+Mono:wdth,wght@75,100..800 : one width only (font-stretch:75%)
MM=''.join("@font-face{font-family:'Martian Mono';font-style:normal;font-weight:100 800;font-stretch:75%;font-display:swap;"
            f"src:url(https://fonts.local/martian-mono-{k}-wdth-normal.woff2) format('woff2');unicode-range:{u}}}" for k,u in UR.items())
def setup(pg):
    realfonts.setup(pg)
    def css(r):
        if 'Martian' in r.request.url: r.fulfill(status=200,content_type='text/css',body=MM,headers={'access-control-allow-origin':'*'})
        else: r.fallback()
    pg.route('https://fonts.googleapis.com/**',css)
    def font(r):
        n=r.request.url.rsplit('/',1)[1]
        if n.startswith('martian'): r.fulfill(status=200,content_type='font/woff2',body=open(D+n,'rb').read(),headers={'access-control-allow-origin':'*'})
        else: r.fallback()
    pg.route('https://fonts.local/**',font)
_B=os.environ.get('QA_BASE','http://127.0.0.1:8830');CL=_B+'/index.html';RT=_B+'/retro/tracker/index.html'
def open_page(b,tok,url,h=1000,wait=1800):
    pg,d=device.new_page(b,tok,h);pg.route('**/api.sleeper.app/**',lambda r:r.abort());setup(pg)
    pg.goto(url);pg.evaluate('()=>document.fonts.ready');pg.wait_for_timeout(wait);return pg,d
