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
/* 3. Lineup score cells (Matchups and Playoffs): the points figure's ink centring, and one smaller size for a lineup that holds a
      five-character figure (theme.css, "lineup score cells"; RETRO.md rule 11).
      Why a script: CSS cannot see which glyphs a figure starts and ends with ("1" has .068em of room on its left, "4" .017em on
      its right, so "13.4" sits 0.6px right of where "0.7" does), nor how many characters it has.
      What it does: per cell, --fx (points figure) and --fy (delta) = (right bearing of the last glyph - left bearing of the first) in em (tables L / R below: Martian
      Mono wght 700 at wdth 75, from retro/fonts with fontTools, x .875 for size-adjust); per lineup (.lus), class fs5 when any of
      its figures has five characters or more. It reads text only, never layout (one probe at start measures this engine's glyph advance: WebKitGTK rounds it to whole
      px), and holds no element between runs.
      When: once at load, and for every node added later (a tab built on demand, a pane put back, live scores rewriting a cell). */
(function(){
  var K=.875,L={"0":.029,"1":.0777,"2":.054,"3":.049,"4":.0332,"5":.0468,"6":.046,"7":.0699,"8":.0473,"9":.046,"-":.0303,"+":.0303,"\u2212":.0303},
      R={"0":.029,"1":.0377,"2":.054,"3":.049,"4":.0193,"5":.0493,"6":.046,"7":.0699,"8":.0473,"9":.046};
  function fig(fs){for(var n=fs.firstChild;n;n=n.nextSibling)if(n.nodeType===3){var t=n.nodeValue.trim();if(t)return t}return ''}
  function off(t){var a=L[t.charAt(0)],b=R[t.charAt(t.length-1)];return (a===undefined||b===undefined)?'':((b-a)*K).toFixed(4)+'em'}
  function put(fs,k,v){if(fs.style.getPropertyValue(k)!==v){if(v)fs.style.setProperty(k,v);else fs.style.removeProperty(k)}}
  function run(root){
    var list=root.matches&&root.matches('.cv .fs')?[root]:(root.querySelectorAll?root.querySelectorAll('.cr.lu .cv .fs'):[]);if(!list.length)return;
    var ups=[],i,j;
    for(i=0;i<list.length;i++){var fs=list[i],df=fs.firstElementChild;put(fs,'--fx',off(fig(fs)));put(fs,'--fy',df&&df.className==='fdf'?off(df.textContent.trim()):'');
      var row=fs.closest('.cr.lu'),p=row&&(row.closest('.lus')||row.parentNode);if(p&&ups.indexOf(p)<0)ups.push(p)}
    for(i=0;i<ups.length;i++){var c=ups[i].querySelectorAll('.cr.lu .cv .fs'),five=false;for(j=0;j<c.length&&!five;j++)five=fig(c[j]).length>4;
      if(ups[i].classList.contains('fs5')!==five)ups[i].classList.toggle('fs5',five)}}
  // one layout read, once: the advance this engine gives a glyph at the four sizes used in the cells (see theme.css, --fxd ...)
  function probe(){var S=[['--fxd','700 14.5px'],['--fxe','700 11.5px'],['--fxf','700 10px'],['--fxg','600 11px'],['--fxh','700 18px'],['--fxi','700 14px']],d=document.createElement('div'),sp=[],w,i;
    d.style.cssText='position:absolute;left:-999px;top:0;visibility:hidden;white-space:nowrap';
    for(i=0;i<S.length;i++){var e=document.createElement('span');e.style.cssText='display:block;width:max-content;font:'+S[i][1]+'/1 "Martian Mono"';e.style.setProperty('letter-spacing','0','important');e.textContent='0000000000';d.appendChild(e);sp.push(e)}
    document.body.appendChild(d);w=sp.map(function(e){return e.getBoundingClientRect().width/10});d.remove();
    for(i=0;i<S.length;i++){var dl=w[i]-.525*parseFloat(S[i][1].split(' ')[1]);if(Math.abs(dl)>=.02&&Math.abs(dl)<1)document.documentElement.style.setProperty(S[i][0],dl.toFixed(3)+'px')}}
  if(document.fonts&&document.fonts.load)Promise.all([document.fonts.load('700 14.5px "Martian Mono"'),document.fonts.load('600 11px "Martian Mono"')]).then(probe,function(){});
  run(document);
  if(window.MutationObserver)new MutationObserver(function(ms){for(var i=0;i<ms.length;i++){var a=ms[i].addedNodes;for(var j=0;j<a.length;j++)if(a[j].nodeType===1&&(a[j].firstChild||0))run(a[j])}}).observe(document.body,{childList:true,subtree:true});
})();
/* 5. Compare > Schedule > Week by week: the right-hand seed chip (pass 2, 2026-11-11). Classic bug, present in Classic too: its tile
      fitter (ref() in new_tail.js) finds no text before that chip, so it takes the cell before it, "Wk 10", as the figure the chip
      stands beside (the label holds a digit), shrinks the chip to that label's cap height (14 x 10px, 8.75px digit) and moves it about
      10px up, onto the row's divider; the left-hand chip has no cell before it and is left alone (20 x 17px). The fitter's styles are
      inline and !important, so CSS cannot undo them. What this does: puts an empty comment node in front of the chip (ref() then finds
      "something that is not a figure" and skips the chip; a comment changes no selector and no layout) and removes what the fitter
      already wrote. Text and layout are never read. Remove once Classic's fitter skips these chips. Placed before item 4, so the chip
      is back to its own size when item 4 measures its glyphs. */
(function(){
  var SEL='.pane-cm .csr>span:last-child>.ch:first-child';
  function fix(t){var p=t.previousSibling;if(p&&p.nodeType===8)return;t.parentNode.insertBefore(document.createComment(''),t);
    t.removeAttribute('style');t.removeAttribute('data-oh');t.removeAttribute('data-of');var c=t.querySelector('.ct');if(c)c.removeAttribute('style')}
  function run(root){if(!root.querySelectorAll)return;var l=root.querySelectorAll(SEL),i;for(i=0;i<l.length;i++)fix(l[i])}
  run(document);
  if(window.MutationObserver)new MutationObserver(function(ms){for(var i=0;i<ms.length;i++){var a=ms[i].addedNodes;for(var j=0;j<a.length;j++)if(a[j].nodeType===1&&a[j].firstChild)run(a[j])}}).observe(document.body,{childList:true,subtree:true});
})();
/* 4. Ink centring of the chips and segments on Matchups and Playoffs, and of the Paper Trail > Picks tile digits (theme.css PART 5,
      "chips"; RETRO.md rule 11: left and right gaps
      between ink and frame equal within 0.5px).
      Why a script: a chip's text is centred by its advance box, and CSS cannot see which glyphs the text starts and ends with. Martian
      Mono's side bearings differ a lot ("L" .108em on its left, "K" .019em on its right at 11px bold: "FK" sits 0.5px right of centre,
      "@" 0.05px left), and Classic's own offsets were tuned for Barlow Condensed.
      What it does: per element in LIST, --ix = (right bearing of the last glyph - left bearing of the first) in em; theme.css turns it
      into a text-indent (which shifts a centred line by half of it). Bearings: table B below, Martian Mono wdth 75 at wght 400 / 500 /
      600 / 700, thousandths of an em, from retro/fonts with fontTools (x .875 for size-adjust). It reads text only, never layout. One
      exception: an engine that rounds glyph advances to whole pixels (WebKitGTK; Safari and Chromium do not) is detected by ONE probe,
      and only there each element's font size is read (style, not layout) and the rounding is added as --iw.
      When: at load, and for nodes added later (tabs built on demand, live scores). It holds no element between runs. */
(function(){
  var K=.875,C="!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~\u00b7\u2013\u2022\u2212",B={400:[221,221,139,139,42,42,80,54,35,35,64,32,240,240,200,140,140,200,57,57,60,60,213,211,60,60,221,221,105,105,55,55,100,60,80,80,75,75,54,46,78,76,75,75,87,87,74,74,75,75,221,221,213,211,100,100,90,90,100,100,88,92,44,48,45,45,105,55,76,54,80,55,120,80,140,60,65,65,80,80,80,80,70,90,115,49,160,60,60,60,74,74,55,55,110,42,55,55,98,32,80,54,50,50,74,74,45,45,20,20,46,46,36,36,90,90,240,140,105,105,140,240,94,94,60,60,138,138,70,106,92,62,91,68,62,92,88,74,114,16,64,98,100,90,125,75,75,144,136,46,110,90,67,63,100,90,74,74,92,62,62,92,84,56,96,84,76,76,90,100,60,60,24,24,60,60,60,60,108,108,170,110,253,253,110,170,80,80,221,221,65,65,125,125,60,60],500:[212,212,124,124,37,37,71,51,32,32,57,26,231,231,191,131,131,191,48,48,51,51,203,200,51,51,211,211,99,99,47,47,93,53,72,72,67,67,48,38,68,68,66,66,82,82,66,66,66,66,211,211,203,200,91,91,90,90,91,91,83,85,40,46,39,39,95,47,67,47,71,47,109,73,126,55,58,56,71,71,71,71,61,81,105,40,149,55,53,53,66,66,47,47,96,36,47,47,85,26,71,51,44,44,65,65,39,39,18,18,41,41,30,30,83,83,231,131,99,99,131,231,83,83,51,51,128,129,61,96,84,55,84,62,55,84,80,68,104,8,58,89,91,82,117,65,66,138,123,39,102,80,58,54,91,82,67,67,84,55,55,84,78,49,89,77,70,68,82,91,53,53,22,22,51,51,53,53,100,100,161,101,247,247,101,161,80,80,211,211,56,56,114,114,51,51],600:[203,203,106,106,32,32,62,47,28,28,48,20,222,222,181,121,121,181,38,38,41,41,192,187,41,41,199,199,92,92,38,38,85,45,63,63,58,58,40,28,58,58,56,56,76,76,56,56,56,56,199,199,192,187,81,81,90,90,81,81,78,77,35,43,32,32,83,38,58,39,61,38,96,65,111,50,50,45,61,61,61,61,51,71,93,31,136,50,45,45,58,58,38,38,81,30,38,38,71,20,62,47,36,36,55,55,32,32,16,16,35,35,23,23,75,75,221,121,92,92,121,221,70,70,41,41,117,118,52,86,76,46,75,55,46,76,72,61,93,-2,52,79,81,72,108,53,57,131,109,31,93,68,48,44,81,72,59,59,76,46,46,76,71,41,81,68,63,58,72,81,45,45,20,20,41,41,46,45,90,90,151,91,240,240,91,151,80,80,199,199,46,46,101,101,41,41],700:[194,194,88,88,27,27,52,44,24,24,40,14,212,212,170,110,110,170,29,29,30,30,180,175,30,30,188,188,85,85,29,29,78,38,54,54,49,49,33,19,47,49,46,46,70,70,47,47,46,46,188,188,180,175,70,70,90,90,70,70,73,70,31,41,25,25,72,29,48,32,50,29,83,58,95,45,42,34,50,50,50,50,40,60,82,22,123,45,38,38,49,49,29,29,65,24,29,29,56,14,52,44,29,29,44,44,25,25,14,14,29,29,17,17,68,68,210,110,85,85,110,210,57,57,30,30,106,108,42,75,67,38,66,49,38,67,63,54,81,-11,46,68,70,63,99,42,48,125,94,24,84,57,38,34,70,63,52,52,67,38,38,67,65,34,74,60,57,49,63,70,38,38,18,18,30,30,38,37,81,81,140,80,233,233,80,140,80,80,188,188,35,35,88,88,30,30]};
  // [selector, weight the bearings are taken at, text is shown in capitals, also copy the text to data-tx ("Week rank" figure, see theme.css)]
  var LIST=[['.cnm .gp .gha.ht',700,0],['.cr.lu .flg',700,0],['.cnm b .inj',700,0],['.mby',400,0],['.mcr em .hrt',700,1],['.mpk .stk',500,0],['.g4 .gsd',600,0],
    ['.hres',700,0],['.g4 .g4vs',700,1],['.slg .ss',700,1],['.pseg label',600,0],['.msw label',600,0],['.dd summary .ddk',700,0],['.mop .mt',700,0],['.dxl>u',700,0],['.stc b',700,1],['.stc i',400,0],['.stc em',700,0],
    ['.mres',700,0],['.pp.sm',700,0],['.pq .pqi>span',700,0],['.pq .pqi>b',700,0],['.ch:not([data-oh])',600,0],['.hrk .ch',700,0,1],
    ['.pane-pt .ptxn b',700,0],['.pane-pt .ptn b',700,0],['.pane-pt .ptn span',700,0],
    ['.cmx .nfl',700,0],['.cmx .pk',700,0],['.cmx .cgh>em',700,0],['.wrr .wpt b',700,0],['.wrr .wpt span',700,0],['.cmx .lbc.csub label',700,1]];   // pass 2: Compare team chips, pick chips, position heads and section pills, The Wire position tiles   // Paper Trail > Picks tile digits (see theme.css)
  var SEL=LIST.map(function(a){return a[0]}).join(','),RND=null,P={};
  function ix(t,w){var a=C.indexOf(t.charAt(0)),b=C.indexOf(t.charAt(t.length-1)),g=B[w];return a<0||b<0?'':((g[2*b+1]-g[2*a])*K/1000).toFixed(4)+'em'}
  function adv(w,fs){var k=w+' '+fs;if(P[k]!==undefined)return P[k];var e=document.createElement('span');e.style.cssText='position:absolute;left:-999px;top:0;visibility:hidden;white-space:nowrap;font:'+w+' '+fs+'px/1 "Martian Mono"';
    e.style.setProperty('letter-spacing','0','important');e.textContent='0000000000';document.body.appendChild(e);var d=e.getBoundingClientRect().width/10-.525*fs;e.remove();return P[k]=Math.abs(d)>=.02&&Math.abs(d)<1?d:0}
  function put(e,k,v){if(e.style.getPropertyValue(k)!==v){if(v)e.style.setProperty(k,v);else e.style.removeProperty(k)}}
  function run(root){
    if(!root.querySelectorAll)return;var i,j,l,e,t,W=[];
    for(i=0;i<LIST.length;i++){l=root.querySelectorAll(LIST[i][0]);if(root.matches&&root.matches(LIST[i][0]))l=[root].concat([].slice.call(l));
      for(j=0;j<l.length;j++){e=l[j];t=(e.textContent||'').trim();if(LIST[i][2])t=t.toUpperCase();if(LIST[i][3]&&e.getAttribute('data-tx')!==t)e.setAttribute('data-tx',t);W.push([e,ix(t,LIST[i][1]),LIST[i][1]])}}
    if(RND)for(i=0;i<W.length;i++)W[i][3]=parseFloat(getComputedStyle(W[i][0]).fontSize)||0;     // reads (style only), all before any write
    if(RND)for(i=0;i<W.length;i++)W[i][3]=W[i][3]?adv(W[i][2],W[i][3]):0;
    for(i=0;i<W.length;i++){put(W[i][0],'--ix',W[i][1]);if(RND)put(W[i][0],'--iw',W[i][3]?W[i][3].toFixed(3)+'px':'')}}
  run(document);
  if(document.fonts&&document.fonts.load)document.fonts.load('700 14.5px "Martian Mono"').then(function(){RND=adv(700,14.5)!==0;if(RND)run(document)},function(){});
  if(window.MutationObserver)new MutationObserver(function(ms){for(var i=0;i<ms.length;i++){var a=ms[i].addedNodes;for(var j=0;j<a.length;j++)if(a[j].nodeType===1&&(a[j].firstChild||0)&&(a[j].matches(SEL)||a[j].querySelector(SEL)))run(a[j])}}).observe(document.body,{childList:true,subtree:true});
})();
