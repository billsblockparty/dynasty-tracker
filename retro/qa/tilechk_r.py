# tools/tilechk.py's own check (its JS and tolerance, read from the file) run against the themed copy over http, same tokens
import sys,re,os;sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)));import h
from playwright.sync_api import sync_playwright
src=open(os.path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)),'..','..','tools','tilechk.py')).read();JS=re.search(r"JS='''(.*?)'''",src,re.S).group(1);TOL=float(os.environ.get('TOL','0.05'))
url=h.CL if sys.argv[1]=='c' else h.RT;bad=0
with sync_playwright() as p:
    b=p.chromium.launch()
    for w in sys.argv[2:]:
        pg,_=h.open_page(b,w,url,1800,1500)
        for mode in ('H2H','Median'):
            if mode=='Median':pg.click('#bm');pg.wait_for_timeout(1200)
            for st in ('Dumb','Nerd'):
                pg.click('label[for="%s"]'%('dn-lean' if st=='Dumb' else 'dn-full'));pg.wait_for_timeout(800)
                res=pg.evaluate(JS,TOL);bad+=len(res['out']);print(sys.argv[1],w,mode,st,len(res['out']),'violations of',res['n'],'tiles');[print('   ',x) for x in res['out'][:10]]
        pg.close()
    b.close()
print('TOTAL',bad,'violations (tolerance %.2fpx)'%TOL)
