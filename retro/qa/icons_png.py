# icons_png.py : development rasteriser (Chromium + Pillow) for the committed favicon PNGs.
#   retro/favicon-16.svg -> retro/favicon-16.png   (the hand-hinted 16px drawing, 1 unit = 1 pixel; transparent corners)
#   retro/favicon.svg    -> retro/favicon-32.png   (transparent corners)
#   wordmark_gen.icon180() -> retro/favicon-180.png (apple-touch-icon: opaque, the 32px artwork on the ground's purple, 14px margin)
# Not run by any build: the builds read the committed files. Afterwards: python3 retro/wordmark_gen.py apply
import io,os,sys
from PIL import Image
from playwright.sync_api import sync_playwright
R=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','')if os.path.basename(os.path.dirname(os.path.abspath(__file__)))=='qa' else sys.argv[1]
sys.path.insert(0,R);import wordmark_gen
rd=lambda f:open(os.path.join(R,f)).read().strip()
with sync_playwright() as p:
    br=p.chromium.launch()
    for name,px,svg,opaque in (('favicon-16.png',16,rd('favicon-16.svg'),0),('favicon-32.png',32,rd('favicon.svg'),0),('favicon-180.png',180,wordmark_gen.icon180(),1)):
        pg=br.new_context(viewport={'width':px,'height':px},device_scale_factor=1).new_page()
        pg.set_content('<html><body style="margin:0;background:transparent"><div style="width:%dpx;height:%dpx">%s</div></body></html>'%(px,px,svg.replace('<svg ','<svg style="display:block;width:100%;height:100%" ',1)))
        pg.wait_for_timeout(200);png=pg.screenshot(omit_background=not opaque);im=Image.open(io.BytesIO(png))
        if opaque:im=im.convert('RGB')
        im.save(os.path.join(R,name),optimize=True);print(name,im.size,im.mode,os.path.getsize(os.path.join(R,name)),'bytes')
    br.close()
