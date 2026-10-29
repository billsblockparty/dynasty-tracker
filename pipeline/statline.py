import os as _dt_os;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'

import json,re
S=json.load(open(__DTP__+'stats.json'))
def _u(n,l):return f'{n}<u>{l}</u>'
# Top three scoring stats (by fantasy points, either sign), shown in natural order. Attempts, carries and targets are left
# out: they score nothing. Kickers keep FG/XP; defenses keep their top two plays plus points allowed.
SS=json.load(open(__DTP__+'pull8a.json'))['ss']
KEYS={'QB':['pass_cmp','pass_att','pass_yd','pass_td','pass_int','rush_att','rush_yd','rush_td','fum_lost'],
      'RB':['rush_att','rush_yd','rush_td','rec','rec_tgt','rec_yd','rec_td','fum_lost'],
      'WR':['rec','rec_tgt','rec_yd','rec_td','rush_att','rush_yd','rush_td','fum_lost']}
KEYS['TE']=KEYS['WR']
LAB={'pass_yd':'PA YD','pass_td':'PA TD','pass_int':'INT','rush_yd':'RU YD','rush_td':'RU TD','rec':'REC','rec_yd':'RE YD','rec_td':'RE TD','fum_lost':'FL'}
def items(pos,a):
    v=dict(zip(KEYS[pos],a))
    it=[(k,v[k],v[k]*SS.get(k,0)) for k in KEYS[pos] if k in LAB and v.get(k)]
    it=[x for x in it if abs(x[2])>=0.5] or it[:1]  # drop trivia like -1 rushing yard
    top=sorted(range(len(it)),key=lambda i:(-abs(it[i][2]),i))[:3]
    return [it[i] for i in sorted(top)]
def _grp(lab,nums):return f'<span class="sit"><u>{lab}</u> {"-".join(f"({n})".replace("(-","(−") if isinstance(n,int) and n<0 else str(n) for n in nums)}</span>'
def statline(w,pid,pos):
    """Compact category lines: QB 'PA 292-4' (yds-TD[-INT]), 'RU 14-67-1' (car-yds[-TD]),
    'REC 7-24-1' (rec-yds[-TD]), 'FL 1'. Categories split by a dot; only categories with something in them."""
    s=S.get(str(w),{}).get(pid)
    if s is None:return ''
    if s.endswith('x'):return 'Did not play'
    a=[int(x) for x in s.split('.')]+[0]*10
    td=lambda c,y,t:[c,y]+([t] if t else [])
    if pos=='QB':
        pa=[a[2]]+([a[3],a[4]] if a[4] else [a[3]] if a[3] else [])
        o=[_grp('PA',pa)]+([_grp('RU',td(a[5],a[6],a[7]))] if a[5] else [])+([_grp('FL',[a[8]])] if a[8] else [])
    elif pos=='RB':
        o=([_grp('RU',td(a[0],a[1],a[2]))] if a[0] else [])+([_grp('REC',td(a[3],a[5],a[6]))] if a[3] else [])+([_grp('FL',[a[7]])] if a[7] else [])
    elif pos in('WR','TE'):
        o=([_grp('REC',td(a[0],a[2],a[3]))] if a[0] or a[1] else [])+([_grp('RU',td(a[4],a[5],a[6]))] if a[4] else [])+([_grp('FL',[a[7]])] if a[7] else [])
        if not o:o=[_grp('REC',[0,0])]
    elif pos=='K':
        o=[_grp('FG',[f'{a[0]}/{a[1]}']),_grp('XP',[f'{a[2]}/{a[3]}'])]
    elif pos=='DEF':
        o=[_grp(l,[n]) for n,l in ((a[0],'SK'),(a[1],'INT'),(a[2],'FR'),(a[3],'TD')) if n]+[_grp('PA',[a[4]])]
    else:o=[]
    if pos in('RB',) and not o:o=[_grp('RU',[0,0])]
    h='<i class="sdt">•</i>'.join(o)
    return h
def tight(h):
    """'' / ' stg1' / ' stg2': smaller type for long lines so every stat line stays on one line"""
    n=len(re.sub(r'<[^>]+>','',h))+h.count('class="sit"')
    return '' if n<=T1 else ' stg1' if n<=T2 else ' stg2' if n<=T3 else ' stg3'
T1,T2,T3=19,23,26
