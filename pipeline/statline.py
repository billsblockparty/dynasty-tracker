import os as _dt_os;__DTP__=_dt_os.path.dirname(_dt_os.path.abspath(__file__)).removesuffix('/pos')+'/'

import json
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
def statline(w,pid,pos):
    s=S.get(str(w),{}).get(pid)
    if s is None:return ''
    if s.endswith('x'):return 'Did not play'
    a=[int(x) for x in s.split('.')]+[0]*10
    if pos in KEYS:
        o=[_u(n,LAB[k]) for k,n,_ in items(pos,a)] or [_u(0,'RE YD' if pos in('WR','TE') else 'PA YD' if pos=='QB' else 'RU YD')]
    elif pos=='K':
        o=[f'{a[0]}/{a[1]}<u>FG</u>',f'{a[2]}/{a[3]}<u>XP</u>']
    elif pos=='DEF':
        pl=[(a[3],'TD',6),(a[1],'INT',2),(a[2],'FR',2),(a[0],'SACK',1)]
        o=[_u(n,l) for n,l,_ in sorted([x for x in pl if x[0]],key=lambda x:-x[0]*x[2])[:2]]+[_u(a[4],'PA')]
    else:o=[]
    return '<i class="sdt"> · </i>'.join(f'<span class="sit">{x}</span>' for x in o)
