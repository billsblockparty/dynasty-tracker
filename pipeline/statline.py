import os as _dt_os;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'

import json
S=json.load(open(__DTP__+'stats.json'))
def _u(n,l):return f'{n}<u>{l}</u>'
def statline(w,pid,pos):
    s=S.get(str(w),{}).get(pid)
    if s is None:return ''
    if s.endswith('x'):return 'Did not play'
    a=[int(x) for x in s.split('.')]+[0]*10
    o=[]
    def rush(c,y,t):
        r=[]
        if c:r+= [_u(c,'CAR'),_u(y,'YD')]
        if t:r.append(_u(t,'TD'))
        return r
    if pos=='QB':
        o=[f'{a[0]}/{a[1]}<u>CMP</u>',_u(a[2],'YD')]
        if a[3]:o.append(_u(a[3],'TD'))
        if a[4]:o.append(_u(a[4],'INT'))
        o+=rush(a[5],a[6],a[7])
        if a[8]:o.append(_u(a[8],'FL'))
    elif pos=='RB':
        o=[_u(a[0],'CAR'),_u(a[1],'YD')]+([_u(a[2],'TD')] if a[2] else [])
        if a[3] or a[4]:o+=[_u(a[3],'REC'),_u(a[5],'YD')]+([_u(a[6],'TD')] if a[6] else [])
        if a[7]:o.append(_u(a[7],'FL'))
    elif pos in('WR','TE'):
        o=[f'{a[0]}/{a[1]}<u>REC</u>',_u(a[2],'YD')]+([_u(a[3],'TD')] if a[3] else [])
        o+=rush(a[4],a[5],a[6])
        if a[7]:o.append(_u(a[7],'FL'))
    elif pos=='K':
        o=[f'{a[0]}/{a[1]}<u>FG</u>',f'{a[2]}/{a[3]}<u>XP</u>']
    elif pos=='DEF':
        o=[_u(a[0],'SACK')]+([_u(a[1],'INT')] if a[1] else [])+([_u(a[2],'FR')] if a[2] else [])+([_u(a[3],'TD')] if a[3] else [])+[_u(a[4],'PA')]
    return ', '.join(o)
