#!/usr/bin/env python3
"""Wordmark generator (retro tracker theme). Draws THE / LEAGUE from its own letter construction (no font outlines) and
writes one inline <svg> per option. Units: 1 = 1 CSS px at the 360P layout (h1 row 81.2px); the svg scales with the row."""
import sys
def n(v):
    s=('%.3f'%v).rstrip('0').rstrip('.');return '0' if s in('-0','') else s
def rpoly(pts):
    """closed path through pts [(x,y) or (x,y,r)]; a corner with r is rounded by a circular arc (right angles only)"""
    P=[(p[0],p[1],p[2] if len(p)>2 else 0) for p in pts];N=len(P);d=[]
    def unit(a,b):
        dx,dy=b[0]-a[0],b[1]-a[1];L=(dx*dx+dy*dy)**.5;return dx/L,dy/L
    for i,(x,y,r) in enumerate(P):
        a=P[i-1];b=P[(i+1)%N]
        if r:
            u=unit((x,y),a);v=unit((x,y),b);p1=(x+u[0]*r,y+u[1]*r);p2=(x+v[0]*r,y+v[1]*r)
            cross=(x-a[0])*(b[1]-y)-(y-a[1])*(b[0]-x)
            d.append(('M' if not d else 'L')+n(p1[0])+' '+n(p1[1]));d.append('A%s %s 0 0 %d %s %s'%(n(r),n(r),1 if cross>0 else 0,n(p2[0]),n(p2[1])))
        else:d.append(('M' if not d else 'L')+n(x)+' '+n(y))
    return ''.join(d)+'Z'
WR,AB,GE,GS,GX=58,58,26,50,36   # width of H A G U; A crossbar top; G: arm end, spur top, spur left end (cap = 100)
def letters(S=16,B=14,R=15,ri=5):
    """cap height 100, y down. S = stem, B = bar, R / ri = outer / inner corner radius. returns {ch:(width, path)}"""
    G={}
    G['L']=(40,[[(0,0),(S,0),(S,100-B),(40,100-B),(40,100),(0,100)]])
    m0,m1=50-B/2,50+B/2
    G['E']=(42,[[(0,0),(42,0),(42,B),(S,B),(S,m0),(37,m0),(37,m1),(S,m1),(S,100-B),(42,100-B),(42,100),(0,100)]])
    G['T']=(46,[[(0,0),(46,0),(46,B),(23+S/2,B),(23+S/2,100),(23-S/2,100),(23-S/2,B),(0,B)]])
    G['H']=(WR,[[(0,0),(S,0),(S,m0),(WR-S,m0),(WR-S,0),(WR,0),(WR,100),(WR-S,100),(WR-S,m1),(S,m1),(S,100),(0,100)]])
    G['U']=(WR,[[(0,0),(S,0),(S,100-B,ri),(WR-S,100-B,ri),(WR-S,0),(WR,0),(WR,100,R),(0,100,R)]])
    G['A']=(WR,[[(0,100),(0,0,R),(WR,0,R),(WR,100),(WR-S,100),(WR-S,AB+B),(S,AB+B),(S,100)],[(S,AB),(WR-S,AB),(WR-S,B,ri),(S,B,ri)]])
    G['G']=(WR,[[(WR,GE),(WR,0,R),(0,0,R),(0,100,R),(WR,100,R),(WR,GS),(GX,GS),(GX,GS+B),(WR-S,GS+B),(WR-S,100-B,ri),(S,100-B,ri),(S,B,ri),(WR-S,B,ri),(WR-S,GE)]])
    return G
def word(G,txt,gaps,H,x=0,y=0):
    """-> (path data with the letters baked at x,y = top-left of the cap box, cap height H; total width)"""
    k=H/100;out=[];cx=x
    for i,ch in enumerate(txt):
        w,cs=G[ch];LOG.append((ch,cx,y,k,w))
        for c in cs:out.append(rpoly([(cx+p[0]*k,y+p[1]*k)+((p[2]*k,) if len(p)>2 else ()) for p in c]))
        cx+=w*k+(gaps[i]*k if i<len(txt)-1 else 0)
    return ''.join(out),cx-x

LOG=[]   # (letter, x, y, scale, width) of every letter placed by the last calls of word(): read by the QA scripts only
RH=81.2   # h1 row at the 360P layout (1.4 x 58px); 95.7 at 402P / 440P, 107.3 on desktop: the svg scales with it
def svg(opt,W,body,defs=''):
    return ('<svg class="lgs wm wm-%s" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %s %s" aria-hidden="true" focusable="false">'%(opt.lower(),n(W),n(RH))
            +('<defs>'+defs+'</defs>' if defs else '')+'<g class="wm-m">'+body+'</g></svg>')
GL=[8,10,12,12,12]   # LEAGUE pair gaps (cap = 100): L-E tighter (the L's open corner)
GT=[6,12]            # THE: T-H tighter (the T's overhang)
def optA(H=49.5,o=1.25,d=3,wg=.34,dy=0,p=None):
    G=letters(**(p or {}));x=o
    t,wt=word(G,'THE',GT,H,x,0);l,wl=word(G,'LEAGUE',GL,H,x+wt+wg*H,0)
    inkh=H+2*o+d;y=(RH-inkh)/2+o+dy;W=x+wt+wg*H+wl+o+d
    t,_=word(G,'THE',GT,H,x,y);l,_=word(G,'LEAGUE',GL,H,x+wt+wg*H,y)
    defs='<path id="wm-p" d="%s"/>'%(t+l)
    body=('<use href="#wm-p" class="wm-k" transform="translate(%s %s)"/><use href="#wm-p" class="wm-k"/><use href="#wm-p" class="wm-y"/>'%(n(d),n(d)))
    css='html.retro .wm-k{fill:var(--black);stroke:var(--black);stroke-width:%spx;stroke-linejoin:miter}html.retro .wm-y{fill:var(--yellow)}'%n(2*o)
    return svg('A',W,body,defs),css,dict(W=W,H=H,y=y,o=o,d=d)
def optB(H=40,o=1,d=2,wg=.34,px=12,ph=66,sh=4,dy=0,p=None):
    G=letters(**(p or {}));hl=1;bw=2
    _,wt=word(G,'THE',GT,H);_,wl=word(G,'LEAGUE',GL,H)
    PH=ph or (H+2*13+2*(hl+bw));PW=wt+wg*H+wl+2*px+2*(hl+bw)+d*.5
    y0=(RH-(PH+sh))/2+dy;xi=hl+bw+px;yi=y0+(PH-H)/2-d*.25
    t,_=word(G,'THE',GT,H,xi,yi);l,_=word(G,'LEAGUE',GL,H,xi+wt+wg*H,yi)
    defs=('<linearGradient id="wm-g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" class="wm-hi"/><stop offset="1" class="wm-lo"/></linearGradient>'
          '<path id="wm-t" d="%s"/><path id="wm-l" d="%s"/>'%(t,l))
    r=5
    body=('<rect class="wm-kf" x="%s" y="%s" width="%s" height="%s" rx="%s"/>'%(n(sh),n(y0+sh),n(PW),n(PH),n(r))
          +'<rect class="wm-pe" x="0" y="%s" width="%s" height="%s" rx="%s"/>'%(n(y0),n(PW),n(PH),n(r))
          +'<rect class="wm-w" x="%s" y="%s" width="%s" height="%s" rx="%s"/>'%(n(hl),n(y0+hl),n(PW-2*hl),n(PH-2*hl),n(r-hl))
          +'<rect fill="url(#wm-g)" x="%s" y="%s" width="%s" height="%s" rx="%s"/>'%(n(hl+bw),n(y0+hl+bw),n(PW-2*(hl+bw)),n(PH-2*(hl+bw)),n(r-hl-bw))
          +'<g class="wm-k" transform="translate(%s %s)"><use href="#wm-t"/><use href="#wm-l"/></g><g class="wm-k"><use href="#wm-t"/><use href="#wm-l"/></g>'%(n(d),n(d))
          +'<use href="#wm-t" class="wm-y"/><use href="#wm-l" class="wm-wf"/>')
    css=('html.retro .wm-k{fill:var(--black);stroke:var(--black);stroke-width:%spx;stroke-linejoin:miter}html.retro .wm-kf{fill:var(--black)}html.retro .wm-y{fill:var(--yellow)}'
         'html.retro .wm-wf,html.retro .wm-w{fill:var(--white)}html.retro .wm-pe{fill:var(--peri)}html.retro .wm-hi{stop-color:var(--badge-hi)}html.retro .wm-lo{stop-color:var(--badge-lo)}'%n(2*o))
    return svg('B',PW+sh,body,defs),css,dict(W=PW+sh,H=H,PW=PW,PH=PH,y0=y0,yi=yi)
def optC(H=58,h=.5,o=1.25,d=2.5,dt=2,wg=.36,dy=0,fill='white',p=None,two=True):
    G=letters(**(p or {}));x=o;hh=H*h;nst=2 if two else 1
    _,wt=word(G,'THE',GT,hh);_,wl=word(G,'LEAGUE',GL,H)
    inkh=H+2*o+nst*d;y=(RH-inkh)/2+o+dy;gap=wg*hh+o*2
    t,_=word(G,'THE',GT,hh,x,y+H-hh);l,_=word(G,'LEAGUE',GL,H,x+wt+gap,y)
    W=x+wt+gap+wl+o+nst*d
    defs='<path id="wm-t" d="%s"/><path id="wm-l" d="%s"/>'%(t,l)
    body=('<use href="#wm-l" class="wm-s2" transform="translate(%s %s)"/><use href="#wm-l" class="wm-s1" transform="translate(%s %s)"/>'%(n(2*d),n(2*d),n(d),n(d))
          +'<use href="#wm-t" class="wm-s1" transform="translate(%s %s)"/>'%(n(dt),n(dt))
          +'<use href="#wm-l" class="wm-k"/><use href="#wm-t" class="wm-k"/><use href="#wm-l" class="wm-f"/><use href="#wm-t" class="wm-f2"/>')
    css=('html.retro .wm-k{fill:var(--black);stroke:var(--black);stroke-width:%spx;stroke-linejoin:miter}'
         'html.retro .wm-s1{fill:var(--orange);stroke:var(--orange);stroke-width:%spx;stroke-linejoin:miter}html.retro .wm-s2{fill:var(--peri);stroke:var(--peri);stroke-width:%spx;stroke-linejoin:miter}'
         'html.retro .wm-f{fill:var(--%s)}html.retro .wm-f2{fill:var(--%s)}'%(n(2*o),n(2*o),n(2*o),fill,'yellow' if fill=='white' else 'white'))
    return svg('C',W,body,defs),css,dict(W=W,H=H,y=y)

SLIM=dict(S=14,B=12.5,R=14,ri=5)
FINAL={'A':lambda:optA(),'B':lambda:optB(),'C':lambda:optC(p=SLIM)}
if __name__=='__main__':
    # python3 retro/wordmark_gen.py A|B|C > retro/wordmark.svg   (development only; the build reads the committed svg)
    sys.stdout.write(FINAL[sys.argv[1]]()[0]+'\n')
