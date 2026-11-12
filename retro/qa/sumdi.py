# sumdi.py <json...> : per tab/state counts of FAIL, low contrast, and text on the bare ground; components listed
import sys,json,collections
def ground(bg):
    import numpy as np;p=np.array([51,35,112.]);o=np.array([226,129,68.]);v=np.array(bg,float);d=o-p;t=((v-p)@d)/(d@d);return -.08<t<1.05 and np.linalg.norm(v-(p+t*d))<16   # on the purple..orange gradient
V='-v' in sys.argv
for f in [a for a in sys.argv[1:] if a.endswith('.json')]:
    R=json.load(open(f));tf=tl=tg=0;print('#####',f)
    for st,ns in R.items():
        F=[n for n in ns if n['fail']];L=[n for n in ns if n['low']];G=[n for n in ns if ground(n['bg'])]
        tf+=len(F);tl+=len(L);tg+=len(G);print(f'{st}: {len(ns)} nodes, FAIL {len(F)}, low {len(L)}, ground {len(G)}')
        if V:
            for lab,X in (('FAIL',F),('LOW',L),('GROUND',G)):
                C=collections.OrderedDict()
                for n in X:C.setdefault(n['k'],[]).append(n)
                for k,v in C.items():print(f"    {lab} x{len(v)} {k[:70]} | '{v[0]['t']}' ink {v[0]['ink']} bg {v[0]['bg']} cr {min(x['cr'] for x in v)} fs {v[0]['fs']}")
    print(f'TOTAL FAIL {tf} low {tl} ground {tg}')
