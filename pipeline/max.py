B,R,M,C,P,N,H,T,A,W="Bill's Block Party","Team Ram Rod","Mandingoes","Convicts","Team RIPMFL","Nuts in the Face","Homer's Heroes","Cheating is Trying","Reverse Apache Master","Canton waitlist"
act={1:{B:186.56,R:131.86,M:114.70,T:112.94,W:110.30,A:107.46,N:105.04,C:100.70,P:91.22,H:89.36},
2:{C:148.36,M:138.18,P:133.26,H:125.72,N:121.58,R:118.64,B:101.32,T:79.38,A:66.90,W:56.40},
3:{B:170.90,R:131.98,H:121.06,W:120.28,P:115.78,M:107.76,C:102.34,A:97.64,N:97.32,T:71.48},
4:{B:147.64,R:147.32,C:123.10,T:109.92,H:98.92,P:96.22,M:95.84,A:83.78,N:75.28,W:61.58}}
mx={1:{B:189.36,R:155.56,M:144.70,T:132.34,W:122.90,A:119.56,N:118.20,C:120.16,P:112.22,H:119.46},
2:{C:158.16,M:151.28,P:158.88,H:125.72,N:131.38,R:160.88,B:124.88,T:102.32,A:80.80,W:81.12},
3:{B:188.70,R:145.06,H:123.16,W:134.58,P:125.08,M:118.96,C:113.44,A:114.44,N:132.58,T:96.24},
4:{B:184.04,R:169.02,C:149.90,T:121.96,H:115.22,P:121.38,M:129.96,A:103.66,N:113.68,W:77.08}}
season={B:686.98,R:630.52,M:544.90,C:541.66,P:517.56,N:495.84,H:483.56,T:452.86,A:418.46,W:415.68}
sched={1:[(B,M),(C,T),(H,A),(R,N),(P,W)],2:[(B,R),(C,W),(H,P),(A,T),(N,M)],3:[(B,N),(C,P),(H,T),(R,M),(A,W)],4:[(B,A),(C,N),(H,W),(R,T),(P,M)]}
teams=list(season)
for t in teams: assert abs(sum(mx[w][t] for w in mx)-season[t])<0.01,(t,sum(mx[w][t] for w in mx))
def rec(sc):
    S={t:[0,0,0,0,0] for t in teams}  # w,l,mw,ml,pf
    for w,ms in sched.items():
        for a,b in ms:
            x,y=sc[w][a],sc[w][b]; S[a if x>y else b][0]+=1; S[b if x>y else a][1]+=1
        r=sorted(sc[w].values(),reverse=True); assert r[4]!=r[5]
        for t in teams:
            S[t][2 if sc[w][t]>=r[4] else 3]+=1; S[t][4]+=sc[w][t]
    return S
a,o=rec(act),rec(mx)
order=sorted(teams,key=lambda t:(-(o[t][0]+o[t][2]),-o[t][4]))
for t in order:
    print(f"{t:22} max H2H {o[t][0]}-{o[t][1]} med {o[t][0]+o[t][2]}-{o[t][1]+o[t][3]} | act H2H {a[t][0]}-{a[t][1]} med {a[t][0]+a[t][2]}-{a[t][1]+a[t][3]} | maxPF {o[t][4]:.2f}")
print()
for w in sched:
    for x,y in sched[w]:
        fa=act[w][x]>act[w][y]; fm=mx[w][x]>mx[w][y]
        if fa!=fm: print("FLIP wk",w,x,act[w][x],mx[w][x],"vs",y,act[w][y],mx[w][y])
