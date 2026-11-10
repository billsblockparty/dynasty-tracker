/* retro/theme.js: the only script the theme adds (injected by theme_build.py after the theme's stylesheet).
   1. Re-fit after H2H / Median. Classic bug, present in Classic too (2026-11-09, 360P and 402P): pressing H2H or Median
      redraws the cards but does not re-run s2Fit, so the Opp / All-play / Luck line stays on one line, runs past its
      box and is cut (it is fitted again only on the next resize). CSS cannot re-run a fitter; this calls Classic's own
      window.__fitAll(). Remove once Classic re-fits by itself. */
(function(){
  function refit(){requestAnimationFrame(function(){requestAnimationFrame(function(){if(window.__fitAll)window.__fitAll()})})}
  document.addEventListener('click',function(e){var t=e.target&&e.target.closest&&e.target.closest('#bh,#bm');if(t)refit()},true);
})();
/* 2. Ink centring of the FAAB tile ("$" + digits) and of the CSS rank tile's digit, on the device-pixel grid.
      Why a script: (a) the ink is not centred in its advance box and CSS cannot see the text ("$" left bearing .0518em, last
      digit's right bearing .0193em for "4" to .0699em for "7"); (b) engines snap a text run's origin and a box's edges to
      device pixels separately, so a tile at a fractional position shows up to 2 device pixels more room on one side.
      Method: glyph ink from the font's own outlines (table G below: left bearing, right bearing, lowest and highest point,
      in em, wdth 75; read from retro/fonts with fontTools, never from a canvas); for each tile take its painted edges
      (document position rounded to device pixels), then choose the whole device pixel for the text origin (across) and for
      the baseline (down) that leaves the most equal gaps, and express it as text-indent / padding-top. Result by
      construction: gaps differ by at most 1 device pixel each way. Vertical centring is on the whole ink box; for "$NN" that
      is the digits' cap band too, because "$" overshoots it by the same .1em above and below.
      Phones only (below 1100px; desktop rows are zoomed 1.1 and keep the CSS defaults). Runs after every run of Classic's
      tnFit (load, fonts, resize, H2H / Median redraw). Reads first, then writes. Needs text-box trim; without it nothing is set. */
(function(){
  var K=.875,ADV=.6,G={700:{"$":[0.0518,0.0436,-0.1,0.9],"0":[0.029,0.029,-0.019,0.819],"1":[0.0777,0.0377,0.0,0.8],"2":[0.054,0.054,0.0,0.819],"3":[0.049,0.049,-0.019,0.819],"4":[0.0332,0.0193,0.0,0.8],"5":[0.0468,0.0493,-0.019,0.8],"6":[0.046,0.046,-0.019,0.8],"7":[0.0699,0.0699,0.0,0.8],"8":[0.0473,0.0473,-0.019,0.819],"9":[0.046,0.046,0.0,0.819]},800:{"$":[0.042,0.04,-0.1,0.9],"0":[0.02,0.02,-0.02,0.82],"1":[0.07,0.03,0.0,0.8],"2":[0.045,0.045,0.0,0.82],"3":[0.04,0.04,-0.02,0.82],"4":[0.026,0.01,0.0,0.8],"5":[0.036,0.04,-0.02,0.8],"6":[0.036,0.036,-0.02,0.8],"7":[0.064,0.064,0.0,0.8],"8":[0.038,0.038,-0.02,0.82],"9":[0.036,0.036,0.0,0.82]}};
  var TRIM=window.CSS&&CSS.supports&&CSS.supports('text-box','trim-both cap alphabetic');
  // the grid engines snap layout to: 1 / devicePixelRatio CSS px. A phone's page scale (0.85 here) is applied to the finished raster
  // afterwards and scales both gaps alike, so it is not part of the unit
  function unit(){return 1/(window.devicePixelRatio||1)}
  // box [x,y,w,h] in document px, text s, weight w, font size fs, top inset of the text's cap line region = box edge to edge
  function plan(x,y,w,h,s,wt,fs,u,adv){
    var g=G[wt],em=K*fs,A=s.length*adv,i,c,y0=9,y1=-9;
    for(i=0;i<s.length;i++){c=g[s.charAt(i)];if(!c)return null;if(c[2]<y0)y0=c[2];if(c[3]>y1)y1=c[3]}
    var L=g[s.charAt(0)][0]*em,R=adv-(ADV-g[s.charAt(s.length-1)][1])*em;   // ink insets of the run; adv = the advance this engine uses (WebKitGTK rounds it to whole px)
    var pl=Math.round(x/u),pr=Math.round((x+w)/u),pt=Math.round(y/u),pb=Math.round((y+h)/u);
    // across: origin m (device px) so that (m + L/u - pl) = (pr - (m + (A-R)/u))
    var m=Math.round((pl+pr-(A+L-R)/u)/2),n=Math.round((pt+pb+(y0+y1)*em/u)/2);  // n: baseline
    return {ti:2*(m*u-x-(w-A)/2),base:n*u-y}}
  // what THIS engine lays out: the distance from the top of a cap-trimmed line to its baseline (WebKit rounds the cap height
  // to whole px, Chromium does not) and the digit advance (WebKitGTK rounds it to whole px): a hidden probe with a zero-size inline-block on the baseline, one per font
  function capOf(font){var d=document.createElement('div'),i=document.createElement('i');
    d.style.cssText='position:absolute;left:-999px;top:0;visibility:hidden;padding:0;border:0;margin:0;white-space:nowrap;letter-spacing:0;text-box:trim-both cap alphabetic;font:'+font;
    i.style.cssText='display:inline-block;width:0;height:0;padding:0;margin:0;border:0;vertical-align:baseline';
    var s=document.createElement('span');s.textContent='0000000000';d.appendChild(s);d.appendChild(i);d.style.setProperty('letter-spacing','0','important');s.style.setProperty('letter-spacing','0','important');document.body.appendChild(d);
    var c={cap:i.getBoundingClientRect().bottom-d.getBoundingClientRect().top,adv:s.getBoundingClientRect().width/10};d.remove();return c}
  function fit(){
    if(!TRIM||innerWidth>=1100)return;var u=unit(),sx=window.scrollX||0,sy=window.scrollY||0,W=[],C={};
    function cap(cs){var f=cs.fontWeight+' '+cs.fontSize+'/1 '+cs.fontFamily;return C[f]||(C[f]=capOf(f))}
    [].forEach.call(document.querySelectorAll('.board .r .nm .fab b'),function(b){
      var t=(b.textContent||'').trim(),r=b.getBoundingClientRect(),cs=getComputedStyle(b);if(!r.width||t.charAt(0)!=='$')return;
      var q=cap(cs),p=plan(r.left+sx,r.top+sy,r.width,r.height,t,700,parseFloat(cs.fontSize),u,q.adv);if(!p)return;
      var sum=parseFloat(cs.paddingTop)+parseFloat(cs.paddingBottom),top=p.base-q.cap;
      top=Math.round(top*64)/64;   // layout units are 1/64px: keep top + bottom exactly as before, so the tile's height and every row below stay where they are
      if(top<1||sum-top<1)return;W.push([b,'textIndent',p.ti.toFixed(3)+'px'],[b,'paddingTop',top+'px'],[b,'paddingBottom',(sum-top)+'px'])});
    if(!document.documentElement.classList.contains('rk-art'))[].forEach.call(document.querySelectorAll('.board .r>.rk .rkn'),function(k){
      var im=k.querySelector('img'),t=im&&im.getAttribute('alt'),r=k.getBoundingClientRect(),cs=getComputedStyle(k,'::before');if(!t||!r.width||cs.content==='none')return;
      var w=parseFloat(cs.width),h=parseFloat(cs.height),bw=parseFloat(cs.borderTopWidth),x=r.left+sx+(r.width-w)/2,y=r.top+sy+(r.height-h)/2;
      var q=cap(cs),p=plan(x,y,w,h,t,800,parseFloat(cs.fontSize),u,q.adv);if(!p)return;
      W.push([k,'--rk-ti',p.ti.toFixed(3)+'px'],[k,'--rk-pt',(p.base-q.cap-bw).toFixed(3)+'px'])});
    W.forEach(function(a){if(a[1].charAt(0)==='-')a[0].style.setProperty(a[1],a[2]);else a[0].style[a[1]]=a[2]})}
  function clear(){[].forEach.call(document.querySelectorAll('.board .r .nm .fab b'),function(b){b.style.textIndent=b.style.paddingTop=b.style.paddingBottom=''});
    [].forEach.call(document.querySelectorAll('.board .r>.rk .rkn'),function(k){k.style.removeProperty('--rk-ti');k.style.removeProperty('--rk-pt')})}
  var orig=window.tnFit;
  // fit() runs straight after tnFit and once more two frames later: Classic's other fitters (stat lines, right column) run
  // after tnFit and can move a row by a fraction of a pixel, which changes where its tiles meet the device grid
  var raf=0;function later(){if(raf)return;raf=requestAnimationFrame(function(){requestAnimationFrame(function(){raf=0;clear();fit();fit()})})}   // twice: the second pass reads the positions the first one left (a tile within 1/64px of a device-pixel boundary can flip)
  if(typeof orig==='function')window.tnFit=function(){clear();var r=orig.apply(this,arguments);fit();later();return r};
  if(window.__fitAll)requestAnimationFrame(function(){window.__fitAll()});else fit();
})();
