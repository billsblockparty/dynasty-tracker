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
    # pass 5 (ODL badge, favicon): O D S N Y in the same construction. O / D = the U's bowl closed (D keeps a flat left side);
    # S = two half bowls with the G's arm ends; N = two stems and a straight diagonal (square corners, as T H E L);
    # Y = a half-height U (the cup) on a centred stem
    cnt=[(S,100-B,ri),(WR-S,100-B,ri),(WR-S,B,ri),(S,B,ri)]
    G['O']=(WR,[[(0,0,R),(WR,0,R),(WR,100,R),(0,100,R)],cnt])
    G['D']=(WR,[[(0,0),(WR,0,R),(WR,100,R),(0,100)],cnt])
    SW=54
    G['S']=(SW,[[(SW,GE),(SW,0,R),(0,0,R),(0,m1,R),(SW-S,m1,ri),(SW-S,100-B,ri),(S,100-B,ri),(S,100-GE),(0,100-GE),(0,100,R),(SW,100,R),(SW,m0,R),(S,m0,ri),(S,B,ri),(SW-S,B,ri),(SW-S,GE)]])
    dw=S*1.2
    G['N']=(WR,[[(0,100),(0,0),(dw,0),(WR-S,100*(WR-S-dw)/(WR-dw)),(WR-S,0),(WR,0),(WR,100),(WR-dw,100),(S,100*S/(WR-dw)),(S,100)]])
    YC=56
    G['Y']=(WR,[[(0,0),(S,0),(S,YC-B,ri),(WR-S,YC-B,ri),(WR-S,0),(WR,0),(WR,YC,R),(WR/2+S/2,YC),(WR/2+S/2,100),(WR/2-S/2,100),(WR/2-S/2,YC),(0,YC,R)]])
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

# ---- pass 5 / cleanup job 1: the loop page's badge and the favicon (TL since 2026-11-12), in the stepped title style (option C) ----
GO=[12,10]                 # ODL pair gaps: O-D between a round and a flat side, D-L before the L's stem
GD=[12,12,12,12,8,8]       # DYNASTY; S-T and T-Y tighter (the T's overhang)
TOK={'white':'#fff','yellow':'#ffff6f','orange':'#e28144','peri':'#8b9df8','black':'#000','badge-hi':'#5f6def','badge-lo':'#2040fa'}   # the loop's tokens (template.html :root), for files that cannot read them
def badge(VW=127,VH=100,k=5/3):
    """the loop header's badge (TL since 2026-11-12, cleanup job 1; was ODL over DYNASTY): TL alone, the favicon's composition (icon():
    grid letters, cap 36 of a 60 plate, stroke 6, outline 2, steps 2 / 4) scaled by k so the cap is 60 of the plate's 100, centred on the
    plate. T yellow (as THE), L white (as LEAGUE), black outline, orange then periwinkle step; T's steps reach L's outline. Drawn for
    the .mk box (aspect 466 / 367); the plate itself stays CSS. Units: 100 = the plate's height. Returns (svg, css, metrics).
    The O D S N Y letters of letters() and the pair gaps GO / GD (the ODL / DYNASTY badge of pass 5) are no longer used by anything."""
    H,S,tw,lw,g,o,d=36*k,6*k,18*k,12*k,6*k,2*k,2*k
    inkw=tw+g+lw+2*o+2*d;x=(VW-inkw)/2+o;y=(VH-(H+2*o+2*d))/2+o
    P=lambda pts:'M'+'L'.join('%s %s'%(n(a),n(b)) for a,b in pts)+'Z';c=x+(tw-S)/2;lx=x+tw+g
    t=P([(x,y),(x+tw,y),(x+tw,y+S),(c+S,y+S),(c+S,y+H),(c,y+H),(c,y+S),(x,y+S)]);l=P([(lx,y),(lx+S,y),(lx+S,y+H-S),(lx+lw,y+H-S),(lx+lw,y+H),(lx,y+H)])
    defs='<path id="mk-a" d="%s"/><path id="mk-t" d="%s"/><path id="mk-l" d="%s"/>'%(t+l,t,l)
    body=('<use href="#mk-a" class="mk-s2" transform="translate(%s %s)"/><use href="#mk-a" class="mk-s1" transform="translate(%s %s)"/>'%(n(2*d),n(2*d),n(d),n(d))
          +'<use href="#mk-a" class="mk-k"/><use href="#mk-t" class="mk-f2"/><use href="#mk-l" class="mk-f"/>')
    css=('.mk-k{fill:var(--black);stroke:var(--black);stroke-width:%s;stroke-linejoin:miter}'
         '.mk-s1{fill:var(--orange);stroke:var(--orange);stroke-width:%s;stroke-linejoin:miter}.mk-s2{fill:var(--peri);stroke:var(--peri);stroke-width:%s;stroke-linejoin:miter}'
         '.mk-f{fill:var(--white)}.mk-f2{fill:var(--yellow)}'%(n(2*o),n(2*o),n(2*o)))
    return ('<svg class="mk-g" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %s %s" aria-hidden="true" focusable="false"><defs>%s</defs>%s</svg>'%(n(VW),n(VH),defs,body),css,
            dict(x=x,y=y,H=H))
def _plate(V,sh,bw,r,T=TOK):
    """the badge plate of the icons: hard shadow, white border, gradient fill (the loop's --badge-hi / --badge-lo)"""
    P=V-sh
    return ('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s"/>'%(n(sh),n(sh),n(P),n(P),n(r),T['black'])
            +'<rect width="%s" height="%s" rx="%s" fill="%s"/>'%(n(P),n(P),n(r),T['white'])
            +'<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="url(#g)"/>'%(n(bw),n(bw),n(P-2*bw),n(P-2*bw),n(r-bw)))
def _tl(x,y,H,S,tw,lw,gap):
    """T and L of the icons on a whole-unit grid (square corners, as the wordmark's T and L): cap height H, stroke S, T tw wide, L lw wide"""
    c=x+(tw-S)//2;lx=x+tw+gap;P=lambda pts:'M'+'L'.join('%s %s'%(n(a),n(b)) for a,b in pts)+'Z'
    return (P([(x,y),(x+tw,y),(x+tw,y+S),(c+S,y+S),(c+S,y+H),(c,y+H),(c,y+S),(x,y+S)]),
            P([(lx,y),(lx+S,y),(lx+S,y+H-S),(lx+lw,y+H-S),(lx+lw,y+H),(lx,y+H)]))
_GRAD='<linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient>'%(TOK['badge-hi'],TOK['badge-lo'])
def icon(V=64,o=2,d=2):
    """favicon, 32px and up (2026-11-12, cleanup job 1): TL on the badge plate. T yellow (as THE), L white (as LEAGUE), the stepped
    title's treatment: black outline (o), orange step at d / d, periwinkle step at 2d / 2d. T's steps touch L's outline, as in the
    wordmark. viewBox 64 = 2 units per pixel at 32px: stems 3px, total ink 2.5px from the plate's inner frame all round.
    Self-contained (literal token values, no classes): a favicon cannot read the page's custom properties."""
    t,l=_tl(10,10,36,6,18,12,6);T=TOK;u='<use href="#a" %sfill="%s" stroke="%s" stroke-width="%s" stroke-linejoin="miter"/>'
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %s %s"><defs>%s<path id="a" d="%s"/></defs>'%(n(V),n(V),_GRAD,t+l)+_plate(V,4,3,9)
            +u%('transform="translate(%s %s)" '%(n(2*d),n(2*d)),T['peri'],T['peri'],n(2*o))+u%('transform="translate(%s %s)" '%(n(d),n(d)),T['orange'],T['orange'],n(2*o))
            +u%('',T['black'],T['black'],n(2*o))+'<path d="%s" fill="%s"/><path d="%s" fill="%s"/></svg>'%(t,T['yellow'],l,T['white']))
def icon16():
    """favicon at 16px, hand-hinted on the pixel grid (viewBox 16 = 1 unit per pixel): plain letters, 2px strokes, no outline and no
    steps (at 16px they close the letters: the ODL icon was a block of texture there). T 6 x 9, L 4 x 9, 1px apart; ink to the
    plate's inner frame 1 / 1 / 2 / 2px (left / right / top / bottom)."""
    t,l=_tl(2,3,9,2,6,4,1);T=TOK
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><defs>%s</defs>'%_GRAD+_plate(16,1,1,2)
            +'<g shape-rendering="crispEdges"><path d="%s" fill="%s"/><path d="%s" fill="%s"/></g></svg>'%(t,T['yellow'],l,T['white']))
def icon180():
    """apple-touch-icon source: the 32px artwork on the ground's purple, 14px margin (opaque: iOS fills transparency with black)"""
    a=icon();i=a.index('>')+1
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 180"><rect width="180" height="180" fill="#332370"/><g transform="translate(14 14) scale(2.375)">'+a[i:-6]+'</g></svg>'
FINAL={'A':lambda:optA(),'B':lambda:optB(),'C':lambda:optC(p=SLIM)}
def icon_links(here):
    """the three <link> tags, self-contained (data URIs) from the committed files: favicon-16.png (hand-hinted), favicon-32.png,
    favicon-180.png. PNG only, each with its size: a browser tab at 1x takes the 16px drawing and at 2x the 32px one. An svg icon link
    (any size) is left out on purpose: a browser that prefers it would scale the 32px artwork down to 16px, the unreadable case."""
    import base64,os
    b=lambda f:base64.b64encode(open(os.path.join(here,f),'rb').read()).decode()
    return ('<link rel="icon" type="image/png" sizes="16x16" href="data:image/png;base64,%s">\n<link rel="icon" type="image/png" sizes="32x32" href="data:image/png;base64,%s">\n'
            '<link rel="apple-touch-icon" sizes="180x180" href="data:image/png;base64,%s">'%(b('favicon-16.png'),b('favicon-32.png'),b('favicon-180.png')))
def apply(here):
    """development only: writes retro/favicon.html (read by theme_build.py, patch 9) and the two marked blocks of template.html"""
    import os,re
    links=icon_links(here);open(os.path.join(here,'favicon.html'),'w').write(links+'\n')
    t=open(os.path.join(here,'template.html'),encoding='utf-8').read();bs,bc,_=badge()
    for a,b,body in (('<!--ICON-->','<!--/ICON-->','\n'+links+'\n'),('<!--MK-->','<!--/MK-->',bs),('/*MK-CSS*/','/*/MK-CSS*/',bc)):
        assert t.count(a)==1 and t.count(b)==1,'template.html: marker '+a
        i=t.index(a)+len(a);j=t.index(b);t=t[:i]+body+t[j:]
    open(os.path.join(here,'template.html'),'w',encoding='utf-8').write(t)
if __name__=='__main__':
    # python3 retro/wordmark_gen.py A|B|C > retro/wordmark.svg   (development only; the build reads the committed svg)
    #                       badge | icon | icon16 | icon180 -> the svg on stdout (the committed copies are in template.html, retro/favicon.svg and retro/favicon-16.svg; see RETRO.md, "TL badge and favicon")
    #                       apply -> writes favicon.html and the marked blocks of template.html from the committed favicon files and badge()
    if sys.argv[1]=='apply':
        import os;apply(os.path.dirname(os.path.abspath(__file__)))
    elif sys.argv[1]=='badge':sys.stdout.write(badge()[0]+'\n')
    elif sys.argv[1]=='badge-css':sys.stdout.write(badge()[1]+'\n')
    elif sys.argv[1] in('icon','icon16','icon180'):sys.stdout.write({'icon':icon,'icon16':icon16,'icon180':icon180}[sys.argv[1]]()+'\n')
    else:sys.stdout.write(FINAL[sys.argv[1]]()[0]+'\n')
