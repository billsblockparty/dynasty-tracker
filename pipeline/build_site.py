# Wrap standings.html (scripts kept, for the live site) as site/index.html, and copy the no-script file for download.
import os,shutil,datetime,zoneinfo
P=os.path.dirname(os.path.abspath(__file__))+'/';OUT=os.path.join(P,'..','site')
os.makedirs(OUT,exist_ok=True)
s=open(P+'standings.html',encoding='utf-8').read()
now=datetime.datetime.now(zoneinfo.ZoneInfo('America/New_York'));stamp=now.strftime('%a %b %-d, %-I:%M %p ET');ver=now.strftime('%Y%m%d%H%M%S')
UPD=('<div id="upd" role="status" hidden><span>New scores</span><button type="button" onclick="location.reload()">Refresh</button></div>'
 '<style>#upd{position:fixed;left:50%;bottom:calc(16px + env(safe-area-inset-bottom));transform:translateX(-50%);z-index:50;display:flex;align-items:center;gap:12px;'
 'padding:8px 8px 8px 16px;border-radius:999px;background:var(--chalk);color:var(--ink);font:500 14px var(--body);box-shadow:0 6px 24px rgba(0,0,0,.45)}#upd[hidden]{display:none}'
 '#upd button{border:0;border-radius:999px;padding:6px 14px;background:var(--ink);color:var(--chalk);font:600 13px var(--body);cursor:pointer}</style>'
 '<script>(function(){var V="'+ver+'",el=document.getElementById("upd");function chk(){if(document.visibilityState!=="visible"||!el.hidden)return;'
 'fetch("build.json?"+Date.now(),{cache:"no-store"}).then(function(r){return r.json()}).then(function(j){if(j.v&&j.v!==V)el.hidden=false}).catch(function(){})}'
 'setInterval(chk,120000);document.addEventListener("visibilitychange",chk)})()</script>')
head=('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
      '<meta name="robots" content="noindex">\n')
s=head+s.replace('<meta charset="utf-8">\n','',1)
j=s.index('</style>')+len('</style>');s=s[:j]+'\n</head>\n<body>'+s[j:]+UPD+f'\n<!-- built {stamp} -->\n</body>\n</html>\n'
s=s.replace('</style>','body{margin:0}</style>',1)
open(os.path.join(OUT,'index.html'),'w',encoding='utf-8').write(s)
shutil.copy(P+'DynastyStandings.html',os.path.join(OUT,'DynastyStandings.html'))
open(os.path.join(OUT,'.nojekyll'),'w').close()
import json;json.dump({'v':ver,'built':stamp},open(os.path.join(OUT,'build.json'),'w'))
print('site built',stamp,round(len(s)/1e6,1),'MB')
