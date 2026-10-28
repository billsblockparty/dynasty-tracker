# Radial playoff bracket: seed-1 half on the left, seed-2 half on the right, meeting at the championship in the centre.
# Quarterfinal teams sit on the outer ring; bye teams start one ring in (already in the semifinal).
import math
def build(S,GAMES,win,winp,PT,SHORT,seed,e,tone):
    W=312.0;CX=156.0
    RO,RQ,RS=0.40*W,0.27*W,0.17*W
    TOPPAD=60.0  # room above the upper team circles for their labels
    def pol(a,r,cy):return CX+r*math.cos(math.radians(a)),cy-r*math.sin(math.radians(a))
    top=RO*math.sin(math.radians(65))  # upper team nodes at 65/115 deg
    CY=TOPPAD+top
    BOT=CY+RQ*math.sin(math.radians(40))+19+7+32  # bye circle + two-line label
    H=round(BOT+6)
    (q1,q2,s1,s2,fn)=[g[2] for g in GAMES]
    # left half: 4 at 160, 5 at 120 (QF qf2), seed 1 bye at 220; right half mirrored: 3 at 20, 6 at 60 (qf1), seed 2 at 320
    L=dict(qf='qf2',sf='sf1',pair=q2,angs=(165,115),qa=140,bye=S[0],ba=220,sa=180)
    R=dict(qf='qf1',sf='sf2',pair=q1,angs=(15,65),qa=40,bye=S[1],ba=320,sa=0)
    wk={'qf1':15,'qf2':15,'sf1':16,'sf2':16,'fin':17}
    paths=[];nodes=[];btns=[]
    def arc(r,a1,a2,cls):
        x1,y1=pol(a1,r,CY);x2,y2=pol(a2,r,CY);d=(a2-a1+180)%360-180;big=0;sw=0 if d>0 else 1
        paths.append(f'<path class="{cls}" d="M{x1:.2f} {y1:.2f}A{r:.2f} {r:.2f} 0 {big} {sw} {x2:.2f} {y2:.2f}"/>')
    def spoke(a,r1,r2,cls):
        x1,y1=pol(a,r1,CY);x2,y2=pol(a,r2,CY);paths.append(f'<path class="{cls}" d="M{x1:.2f} {y1:.2f}L{x2:.2f} {y2:.2f}"/>')
    pos=lambda x,y:f'left:{x/W*100:.3f}%;top:{y/H*100:.3f}%'
    def team(t,a,r,w,winner,bye=False,above=False):
        x,y=pol(a,r,CY);sd=seed(t)
        sc='Bye' if bye else f'{PT[(t,w)]:.1f}'
        nodes.append(f'<span class="prn s-{(tone(sd).split() or ["n"])[0]}{" prw" if winner else ""}{" prby" if bye else ""}" style="{pos(x,y)}"><i>{sd}</i>'
                     f'<span class="prl{" up" if above else ""}"><b>{e(SHORT[t])}</b><em>{sc}</em></span></span>')
    def btn(k,a,r,cls=''):
        x,y=pol(a,r,CY) if r else (CX,CY);a_,b_=dict((g[0],g[2]) for g in GAMES)[k];w=wk[k];wn=win(a_,b_,w);p=winp(wn,b_ if wn==a_ else a_,w)
        lab={'qf1':'QF','qf2':'QF','sf1':'SF','sf2':'SF','fin':'Final'}[k]
        btns.append(f'<label for="bk-{k}" class="prg{cls}" style="{pos(x,y)}"><small>{lab}</small><b>{p}%</b></label>')
    for side in (L,R):
        a,b=side['pair'];wn=win(a,b,15)
        for t,ang in zip(side['pair'],side['angs']):
            cl='rp on' if t==wn else 'rp'
            spoke(ang,RO,RQ,cl);arc(RQ,ang,side['qa'],cl)
            team(t,ang,RO,15,t==wn,above=ang in(115,65))
        sfa,sfb=dict((g[0],g[2]) for g in GAMES)[side['sf']];swn=win(sfa,sfb,16)
        # QF winner path into the semifinal, and the bye team's path
        cl='rp on' if wn==swn else 'rp';spoke(side['qa'],RQ,RS,cl);arc(RS,side['qa'],side['sa'],cl)
        cl='rp on' if side['bye']==swn else 'rp';spoke(side['ba'],RQ,RS,cl);arc(RS,side['ba'],side['sa'],cl)
        team(side['bye'],side['ba'],RQ,16,side['bye']==swn,bye=True)
        fa,fb=fn;fw=win(fa,fb,17)
        spoke(side['sa'],RS,0,'rp on' if swn==fw else 'rp')
        btn(side['qf'],side['qa'],RQ);btn(side['sf'],side['sa'],RS)
    btn('fin',0,0,' rf')
    svg=f'<svg viewBox="0 0 {W:.0f} {H}" aria-hidden="true">'+''.join(sorted(paths,key=lambda p:' on' in p))+'</svg>'
    html=f'<div class="prd" style="aspect-ratio:{W:.0f}/{H}">'+svg+''.join(nodes)+''.join(btns)+'</div><div class="rkey"><span><b>QF</b> Wk 15</span><span><b>SF</b> Wk 16</span><span><b>Final</b> Wk 17</span><span><i class="rk-l"></i>projected path</span></div>'
    css=('.prd{position:relative;width:100%;max-width:440px;margin:6px auto 0;container-type:inline-size}'
         '.prd svg{position:absolute;inset:0;width:100%;height:100%;overflow:visible}'
         '.prd path{fill:none;stroke:var(--line-strong);stroke-width:1.5;vector-effect:non-scaling-stroke;stroke-linecap:round}'
         '.prd path.on{stroke:var(--steel)}'
         '.prd .prn,.prd .prg{position:absolute;transform:translate(-50%,-50%)}'
         '.prd .prn>i{display:flex;align-items:center;justify-content:center;width:38px;height:38px;border-radius:50%;box-sizing:border-box;font-style:normal;'
         'font-family:var(--display);font-weight:700;font-size:19px;line-height:1;padding-top:1px;background:var(--deck-2);border:1.5px solid var(--line-strong);color:var(--steel)}'
         '.prd .prn.s-gold>i{color:#f4c451;border-color:rgba(244,196,81,.55);background:#221f19}.prd .prn.s-g>i{color:var(--win);border-color:rgba(63,214,155,.45);background:#17241f}'
         '.prd .prn.prby>i{box-shadow:0 0 0 3px var(--deck),0 0 0 4.5px var(--line-strong)}'
         '.prd .prl{position:absolute;left:50%;top:calc(100% + 4px);transform:translateX(-50%);display:flex;flex-direction:column;align-items:center;white-space:nowrap;line-height:1.15}'
         '.prd .prl.up{top:auto;bottom:calc(100% + 4px)}.prd .prby .prl{top:calc(100% + 7px)}'
         '.prd .prl b{font-size:12.5px;font-weight:500;color:var(--steel)}.prd .prw .prl b{color:var(--chalk)}'
         '.prd .prl em{font-style:normal;font-family:var(--display);font-weight:600;font-size:13px;color:var(--steel);letter-spacing:.02em}.prd .prby .prl em{font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--dim)}'
         '.prd .prg{display:flex;flex-direction:column;align-items:center;justify-content:center;width:36px;height:36px;border-radius:50%;box-sizing:border-box;cursor:pointer;'
         'background:var(--deck);border:1.5px solid var(--line-strong);line-height:1}'
         '.prd .prg small{font-family:var(--display);font-weight:600;font-size:9px;letter-spacing:.1em;text-transform:uppercase;color:var(--dim);margin-bottom:2px}'
         '.prd .prg b{font-family:var(--display);font-weight:700;font-size:13px;color:var(--label);font-variant-numeric:tabular-nums}'
         '.rkey{display:flex;justify-content:center;flex-wrap:wrap;gap:4px 14px;margin-top:8px;font-size:11.5px;color:var(--steel)}.rkey b{font-family:var(--display);font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--label);margin-right:3px}'
         '.rkey span{display:inline-flex;align-items:center;white-space:nowrap}.rk-l{display:inline-block;width:16px;height:1.5px;background:var(--steel);margin-right:6px}'
         '.prd .prg.rf{width:58px;height:58px}.prd .prg.rf small{font-size:10px}.prd .prg.rf b{font-size:17px}')
    return html,css,H
