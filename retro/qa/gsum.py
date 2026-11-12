# gsum.py <di json...> : per file, per tab: states, FAIL total, low total, worst-state low
import sys,json,collections
for f in sys.argv[1:]:
    R=json.load(open(f));T=collections.OrderedDict()
    for st,ns in R.items():
        t=st.split('/')[0];d=T.setdefault(t,[0,0,0,0]);F=sum(1 for n in ns if n['fail']);L=sum(1 for n in ns if n['low']);d[0]+=1;d[1]+=F;d[2]+=L;d[3]=max(d[3],L)
    print(f.split('/')[-1],'| FAIL total',sum(d[1] for d in T.values()),'|',', '.join(f"{t}: {d[0]} st, fail {d[1]}, low {d[2]} (worst {d[3]})" for t,d in T.items()))
