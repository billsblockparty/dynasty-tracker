exec(open('max.py').read().split('teams=list')[0])
act[5]={B:112.48,H:167.98,C:73.74,R:177.30,P:105.46,A:125.96,W:84.70,M:112.74,N:114.24,T:95.22}
sched[5]=[(B,H),(C,R),(P,A),(W,M),(N,T)]
teams=list(season); S={t:[0,0,0,0] for t in teams}
for w,ms in sched.items():
    for a,b in ms:
        x,y=act[w][a],act[w][b]; win,lose=(a,b) if x>y else (b,a)
        S[win][0]+=1;S[lose][1]+=1
        S[a][2]+=x;S[a][3]+=y;S[b][2]+=y;S[b][3]+=x
pfr={t:i+1 for i,t in enumerate(sorted(teams,key=lambda t:-S[t][2]))}
par={t:i+1 for i,t in enumerate(sorted(teams,key=lambda t:-S[t][3]))}
for i,t in enumerate(sorted(teams,key=lambda t:(-S[t][0],-S[t][2])),1):
    s=S[t];print(i,t,f"{s[0]}-{s[1]}",f"{s[2]:.2f} ({pfr[t]}) ({s[2]/5:.2f})",f"{s[3]:.2f} ({par[t]}) ({s[3]/5:.2f})")
