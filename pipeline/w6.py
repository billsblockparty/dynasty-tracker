exec(open("w5.py").read().split("teams=list(season); S=")[0])
import json
act[6]={B:123.30,W:83.64,C:90.62,M:107.06,H:90.60,N:123.04,R:117.48,A:84.70,P:99.66,T:114.02}
sched[6]=[(B,W),(C,M),(H,N),(R,A),(P,T)]
teams=list(season)
def table(weeks):
    S={t:dict(w=0,l=0,mw=0,pf=0,pa=0,orr=[],apw=0,apl=0) for t in teams}
    for w in weeks:
        rk={t:i+1 for i,t in enumerate(sorted(act[w],key=lambda t:-act[w][t]))}
        cut=sorted(act[w].values(),reverse=True)[4]
        for t in teams:
            S[t]['mw']+=act[w][t]>=cut
            S[t]['apw']+=sum(act[w][t]>act[w][o] for o in teams if o!=t); S[t]['apl']+=sum(act[w][t]<act[w][o] for o in teams if o!=t)
        for a,b in sched[w]:
            for x,y in((a,b),(b,a)):
                S[x]['pf']+=act[w][x];S[x]['pa']+=act[w][y];S[x]['orr'].append(rk[y])
                if act[w][x]>act[w][y]:S[x]['w']+=1
                else:S[x]['l']+=1
    return S
def orders(S):
    h=sorted(teams,key=lambda t:(-S[t]['w'],-S[t]['pf'])); m=sorted(teams,key=lambda t:(-(S[t]['w']+S[t]['mw']),-S[t]['pf'])); return h,m
S5=table(range(1,6)); S6=table(range(1,7)); G=6
ph,pm=orders(S5); h,m=orders(S6)
pfr={t:i+1 for i,t in enumerate(sorted(teams,key=lambda t:-S6[t]['pf']))}
par={t:i+1 for i,t in enumerate(sorted(teams,key=lambda t:-S6[t]['pa']))}
T={}
for t in teams:
    s=S6[t]; ap=s['apw']/(s['apw']+s['apl']); luck=round(s['w']-ap*G,2)
    T[t]=[s['w'],s['l'],s['mw'],round(s['pf'],2),pfr[t],round(s['pf']/G,2),round(s['pa'],2),par[t],round(s['pa']/G,2),round(sum(s['orr'])/G,1),s['apw'],s['apl'],luck]
for i,t in enumerate(h,1): print(i,t,T[t],'prev',ph.index(t)+1)
print('MED',m)
json.dump(dict(T=T,H=h,M=m,PH=ph,PM=pm),open('w6.json','w'))
