# Wrap standings.html (scripts kept, for the live site) as site/index.html, and copy the no-script file for download.
import os,shutil,datetime,zoneinfo
P=os.path.dirname(os.path.abspath(__file__))+'/';OUT=os.path.join(P,'..','site')
os.makedirs(OUT,exist_ok=True)
s=open(P+'standings.html',encoding='utf-8').read()
stamp=datetime.datetime.now(zoneinfo.ZoneInfo('America/New_York')).strftime('%a %b %-d, %-I:%M %p ET')
head=('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
      '<meta name="robots" content="noindex">\n')
s=head+s.replace('<meta charset="utf-8">\n','',1)
j=s.index('</style>')+len('</style>');s=s[:j]+'\n</head>\n<body>'+s[j:]+f'\n<!-- built {stamp} -->\n</body>\n</html>\n'
s=s.replace('</style>','body{margin:0}</style>',1)
open(os.path.join(OUT,'index.html'),'w',encoding='utf-8').write(s)
shutil.copy(P+'DynastyStandings.html',os.path.join(OUT,'DynastyStandings.html'))
open(os.path.join(OUT,'.nojekyll'),'w').close()
print('site built',stamp,round(len(s)/1e6,1),'MB')
