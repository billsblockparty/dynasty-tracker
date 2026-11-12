# icons_png.py : development rasteriser (Chromium + Pillow) for the committed favicon PNGs. retro/favicon.svg -> retro/favicon-32.png
# (transparent corners) and retro/favicon-180.png (apple-touch-icon: opaque, the icon on the ground's purple with a 14px margin).
# Not run by any build: the builds read the committed files.
import io,os,sys
from PIL import Image
from playwright.sync_api import sync_playwright
R=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','')if os.path.basename(os.path.dirname(os.path.abspath(__file__)))=='qa' else sys.argv[1]
svg=open(os.path.join(R,'favicon.svg')).read().strip()
with sync_playwright() as p:
    br=p.chromium.launch()
    for name,px,bg,pad in (('favicon-32.png',32,'transparent',0),('favicon-180.png',180,'#332370',14)):
        pg=br.new_context(viewport={'width':px,'height':px},device_scale_factor=1).new_page()
        pg.set_content('<html><body style="margin:0;background:%s"><div style="width:%dpx;height:%dpx;box-sizing:border-box;padding:%dpx">%s</div></body></html>'%(bg,px,px,pad,svg.replace('<svg ','<svg style="display:block;width:100%;height:100%" ',1)))
        pg.wait_for_timeout(200);png=pg.screenshot(omit_background=(bg=='transparent'));im=Image.open(io.BytesIO(png))
        if bg!='transparent':im=im.convert('RGB')
        im.save(os.path.join(R,name),optimize=True);print(name,im.size,im.mode,os.path.getsize(os.path.join(R,name)),'bytes')
    br.close()
