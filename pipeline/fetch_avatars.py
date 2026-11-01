# Team logos from Sleeper (the avatar each manager set for their team), saved as small square webp files under avatars/
# so the page can inline them. Only re-downloads a logo when its Sleeper URL changes. Needs the network (runs in Actions).
import os,json,io,urllib.request
from PIL import Image
P=os.path.dirname(os.path.abspath(__file__))+'/'
D=P+'avatars/';os.makedirs(D,exist_ok=True)
IX=D+'index.json';ix=json.load(open(IX)) if os.path.exists(IX) else {}
teams=json.load(open(P+'teamhub/page_data.json',encoding='utf-8'))['teams']
for rid,t in teams.items():
    u=t.get('avatar')
    if not u or (ix.get(rid)==u and os.path.exists(f'{D}{rid}.webp')):continue
    try:
        b=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=20).read()
        im=Image.open(io.BytesIO(b)).convert('RGB');w,h=im.size;s=min(w,h)
        im=im.crop(((w-s)//2,(h-s)//2,(w-s)//2+s,(h-s)//2+s)).resize((96,96),Image.LANCZOS)
        im.save(f'{D}{rid}.webp','WEBP',quality=82);ix[rid]=u;print('logo',rid,t.get('name'))
    except Exception as e:print('logo failed',rid,e)
json.dump(ix,open(IX,'w'),indent=1)
