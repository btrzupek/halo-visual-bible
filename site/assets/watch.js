// Watch: the epistle-mode film player. The narration is the clock; every shot in manifest.json has a start and an
// end on that clock. Pans are CSS transforms of the keyframe, parallax is a small WebGL depth shader, video shots
// play muted over the narration (or, in the animatic, hold their keyframe with a slow push-in).
(function () {
  'use strict';
  var W = window.WATCH, base = location.pathname.replace(/[^/]*$/, '');
  var q = new URLSearchParams(location.search), DEBUG = q.has('debug');
  // Review builds label every shot with its storyboard ID so a tweak can be named exactly ("M3.S04").
  function $(s, r) { return (r || document).querySelector(s); }
  function el(tag, cls, html) { var e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (m) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[m]; }); }
  function fmt(t) { t = Math.max(0, Math.floor(t)); return Math.floor(t / 60) + ':' + ('0' + (t % 60)).slice(-2); }
  var ease = {
    'linear': function (p) { return p; },
    'in': function (p) { return p * p; },
    'out': function (p) { return 1 - (1 - p) * (1 - p); },
    'in-out': function (p) { return p < .5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2; }
  };

  fetch(base + W.manifest).then(function (r) { return r.json(); }).then(start);

  function start(M) {
    var shots = M.shots, verses = M.verses;
    document.title = 'Watch ' + M.short + ': a visual Bible';

    // ---- stage
    var stage = el('div', 'stage'); document.body.appendChild(stage);
    var layers = [el('div', 'layer'), el('div', 'layer')]; layers.forEach(function (l) { stage.appendChild(l); });
    document.body.appendChild(el('div', 'shade'));
    var black = el('div', 'black'); document.body.appendChild(black);
    var verseBox = el('div', 'verse'); document.body.appendChild(verseBox);
    var showIds = q.has('ids') ? q.get('ids') !== '0' : (M.review || DEBUG);
    var dbg = showIds ? document.body.appendChild(el('div', 'debug')) : null;

    var top = el('div', 'top', '<a class="back" href="/read/' + M.book + '">Back</a><span class="name">' + esc(M.short) + '</span>');
    document.body.appendChild(top);
    var ctl = el('div', 'ctl',
      '<input class="scrub" type="range" min="0" max="' + M.duration + '" step="0.1" value="0" aria-label="Position">' +
      '<div class="row"><button class="play" aria-label="Pause">&#10074;&#10074;</button><span class="time"></span>' +
      '<button class="txt" aria-pressed="true">Text</button><div class="moves"></div></div>');
    document.body.appendChild(ctl);
    var scrub = $('.scrub', ctl), playBtn = $('.play', ctl), timeEl = $('.time', ctl), txtBtn = $('.txt', ctl);
    M.movements.forEach(function (m) {
      var b = el('button', null, esc(m.title)); b.dataset.t = m.start; $('.moves', ctl).appendChild(b);
      b.addEventListener('click', function () { seek(m.start + 0.01); });
    });
    var showText = q.get('overlay') !== 'off';
    try { if (localStorage.getItem('vb-watch-text') === 'off' && !q.has('overlay')) showText = false; } catch (e) {}
    function setText(on) { showText = on; document.body.classList.toggle('notext', !on); txtBtn.setAttribute('aria-pressed', on); try { localStorage.setItem('vb-watch-text', on ? 'on' : 'off'); } catch (e) {} }
    setText(showText);
    txtBtn.addEventListener('click', function () { setText(!showText); });

    // ---- audio: the narration is several files back to back; the clock runs on past them for the epilogue
    var audio = new Audio(); audio.preload = 'auto';
    var seg = -1, playing = false, tailT0 = null, tailBase = 0;
    function segAt(t) { for (var i = M.audio.length - 1; i >= 0; i--) if (t >= M.audio[i].start) return i; return 0; }
    function clock() {
      if (seg >= 0 && seg < M.audio.length) return M.audio[seg].start + (audio.currentTime || 0);
      if (tailT0 != null) return tailBase + (playing ? (performance.now() - tailT0) / 1000 : 0);
      return tailBase;
    }
    function loadSeg(i, offset) {
      seg = i;
      if (i >= M.audio.length) { audio.pause(); tailBase = M.narration_end + (offset || 0); tailT0 = performance.now(); return; }
      tailT0 = null;
      var src = M.audio[i].src;
      if (audio.getAttribute('src') !== src) audio.src = src;
      var set = function () { try { audio.currentTime = offset || 0; } catch (e) {} if (playing) audio.play().catch(function () {}); };
      if (audio.readyState >= 1) set(); else audio.addEventListener('loadedmetadata', set, { once: true });
    }
    audio.addEventListener('ended', function () { loadSeg(seg + 1, 0); });
    function seek(t) {
      t = Math.max(0, Math.min(M.duration - 0.05, t));
      ended = false; black.classList.remove('on'); $('#endcard') && ($('#endcard').hidden = true);
      if (t >= M.narration_end) { seg = M.audio.length; audio.pause(); tailBase = t; tailT0 = performance.now(); }
      else { var i = segAt(t); loadSeg(i, t - M.audio[i].start); }
      cur = -1;
    }
    function setPlaying(on) {
      var t = clock();
      playing = on;
      playBtn.innerHTML = on ? '&#10074;&#10074;' : '&#9654;&#xFE0E;'; playBtn.setAttribute('aria-label', on ? 'Pause' : 'Play');
      if (seg < M.audio.length) { if (on) audio.play().catch(function () {}); else audio.pause(); }
      else { tailBase = t; tailT0 = performance.now(); }
      var v = layers[front].querySelector('video'); if (v) { if (on) v.play().catch(function () {}); else v.pause(); }
    }
    playBtn.addEventListener('click', function () { setPlaying(!playing); });
    scrub.addEventListener('input', function () { seek(+scrub.value); });

    // ---- shots
    var front = 0, cur = -1, active = null, ended = false;
    function shotAt(t) { for (var i = shots.length - 1; i >= 0; i--) if (t >= shots[i].start) return i; return 0; }
    var preloaded = {};
    function preload(i) {
      var s = shots[i]; if (!s || preloaded[i]) return; preloaded[i] = 1;
      if (s.img) { var im = new Image(); im.src = base + s.img; }
      if (s.depth) { var d = new Image(); d.src = base + s.depth; }
    }
    function build(s, layer) {
      layer.innerHTML = ''; layer.className = 'layer' + (s.grade === 'flashback' ? ' flashback' : '');
      var r = { s: s, layer: layer };
      if (s.type === 'video' && s.video) {
        var v = el('video'); v.muted = true; v.playsInline = true; v.setAttribute('playsinline', ''); v.preload = 'auto';
        v.poster = s.img ? base + s.img : ''; v.src = base + s.video; layer.appendChild(v); r.video = v;
        if (playing) v.play().catch(function () {});
        return r;
      }
      if (s.type === 'parallax' && s.depth && s.img) {
        var gl = Parallax(layer, base + s.img, base + s.depth);
        if (gl) { r.gl = gl; return r; }
      }
      var img = el('img'); img.alt = ''; img.decoding = 'async'; img.src = s.img ? base + s.img : ''; layer.appendChild(img); r.img = img;
      return r;
    }
    // crop rect [x, y, w, h] (fractions of the keyframe) -> cover the viewport with that region centred
    function placeImg(img, rect) {
      var iw = img.naturalWidth, ih = img.naturalHeight; if (!iw) return;
      var vw = innerWidth, vh = innerHeight, cw = rect[2] * iw, ch = rect[3] * ih;
      var s = Math.max(vw / cw, vh / ch, vw / iw, vh / ih);
      var cx = (rect[0] + rect[2] / 2) * iw * s, cy = (rect[1] + rect[3] / 2) * ih * s;
      var tx = Math.min(0, Math.max(vw - iw * s, vw / 2 - cx)), ty = Math.min(0, Math.max(vh - ih * s, vh / 2 - cy));
      img.style.width = iw + 'px'; img.style.height = ih + 'px';
      img.style.transform = 'translate3d(' + tx.toFixed(1) + 'px,' + ty.toFixed(1) + 'px,0) scale(' + s.toFixed(5) + ')';
    }
    function lerpRect(a, b, p) { return [0, 1, 2, 3].map(function (k) { return a[k] + (b[k] - a[k]) * p; }); }
    function zoomRect(z) { var w = 1 / z; return [(1 - w) / 2, (1 - w) / 2, w, w]; }
    function render(r, t) {
      var s = r.s, p = Math.max(0, Math.min(1, (t - s.start) / Math.max(0.01, s.end - s.start))), m = s.motion || {};
      if (r.video) {
        var v = r.video; if (v.duration && playing && Math.abs(v.currentTime - Math.min(t - s.start, v.duration - 0.05)) > 0.6) v.currentTime = Math.min(t - s.start, v.duration - 0.05);
        return;
      }
      if (r.gl) {
        var amt = m.amount || 0.05, e = ease['in-out'](p);
        r.gl.draw(m.dolly === 'in' ? amt * e : m.dolly === 'out' ? amt * (1 - e) : 0,
                  m.orbit === 'left' ? -amt * (e - .5) * 2 : m.orbit === 'right' ? amt * (e - .5) * 2 : 0);
        return;
      }
      var rect;
      if (s.type === 'pan' && m.from && m.to) rect = lerpRect(m.from, m.to, (ease[m.ease] || ease['in-out'])(p));
      else if (s.type === 'video') rect = zoomRect(1 + 0.08 * ease['in-out'](p));                       // animatic stand-in
      else if (s.type === 'parallax') { var a2 = (m.amount || 0.05) * 1.6; rect = zoomRect(1 + (m.dolly === 'out' ? a2 * (1 - p) : a2 * p)); }
      else rect = [0, 0, 1, 1];
      if (r.img.complete) placeImg(r.img, rect);
    }

    // ---- verse overlay
    var curVerse = -1;
    function verseAt(t) { for (var i = 0; i < verses.length; i++) if (t >= verses[i].start - 0.1 && t < verses[i].end) return i; return -1; }
    function setVerse(i) {
      if (i === curVerse) return; curVerse = i;
      if (i < 0) { verseBox.classList.remove('on'); return; }
      verseBox.classList.remove('on');
      setTimeout(function () {
        if (curVerse !== i) return;
        verseBox.innerHTML = '<sup>' + verses[i].n + '</sup>' + esc(verses[i].text);
        verseBox.classList.add('on');
      }, verseBox.innerHTML ? 260 : 0);
    }

    // ---- frame loop
    var lastMove = -1;
    function tick() {
      var t = clock();
      if (!ended && t >= M.duration) return finish();
      var i = shotAt(t);
      if (i !== cur) {
        cur = i; front = 1 - front;
        active = build(shots[i], layers[front]);
        var on = layers[front], off = layers[1 - front];
        requestAnimationFrame(function () { on.classList.add('on'); off.classList.remove('on'); });
        setTimeout(function () { if (!off.classList.contains('on')) { var v = off.querySelector('video'); if (v) v.pause(); off.innerHTML = ''; } }, 600);
        preload(i + 1); preload(i + 2);
        if (dbg) dbg.textContent = shots[i].id + '  ' + shots[i].type + (shots[i].type === 'video' && !shots[i].video ? ' (still for now)' : '') +
          (shots[i].placeholder ? '  STAND-IN' : '') + '  v' + (shots[i].verses || '-') + (DEBUG ? '  ' + shots[i].start.toFixed(1) + '-' + shots[i].end.toFixed(1) : '');
      }
      if (active) render(active, t);
      setVerse(t < M.narration_end ? verseAt(t) : -1);
      if (document.activeElement !== scrub) scrub.value = t;
      timeEl.textContent = fmt(t) + ' / ' + fmt(M.duration);
      var mv = 0; M.movements.forEach(function (m, k) { if (t >= m.start) mv = k; });
      if (mv !== lastMove) { lastMove = mv; [].forEach.call($('.moves', ctl).children, function (b, k) { b.classList.toggle('cur', k === mv); }); }
      requestAnimationFrame(tick);
    }
    function finish() {
      ended = true; setPlaying(false); black.classList.add('on'); setVerse(-1);
      setTimeout(function () { endCard(); }, (M.end_card && M.end_card.hold_black || 2) * 1000);
      requestAnimationFrame(function wait() { if (ended) requestAnimationFrame(wait); else tick(); });
    }

    // ---- title and end cards
    function card(id, img, h1, p, buttons) {
      var c = el('section', 'card'); c.id = id;
      c.innerHTML = (img ? '<img src="' + base + img + '" alt="">' : '') + '<a class="cardback" href="/read/' + M.book + '">Back</a>' +
        '<div class="inner"><h1>' + h1 + '</h1><p>' + esc(p) + '</p><div class="go">' + buttons + '</div></div>';
      document.body.appendChild(c); return c;
    }
    var first = shots[0];
    var title = card('titlecard', first.img, esc(M.title).replace(' to ', '<br>to '),
      'A short film of the whole letter, read aloud. ' + fmt(M.duration) + '. King James Version.',
      '<button class="primary" data-go="watch">Watch</button><a class="btn ghost" href="/read/' + M.book + '">Read instead</a>');
    title.addEventListener('click', function (e) {
      if (!e.target.closest('[data-go]')) return;
      title.hidden = true; seek(0); setPlaying(true); requestAnimationFrame(tick); idle();
    });
    function endCard() {
      var c = $('#endcard');
      if (!c) {
        c = card('endcard', null, esc(M.title).replace(' to ', '<br>to '), 'The King James Version, read aloud over pictures made on one AMD Ryzen AI Halo box.',
          '<button class="primary" data-go="again">Watch again</button><a class="btn ghost" href="/read/' + M.book + '">Read ' + esc(M.short) + '</a>' +
          '<a class="btn ghost" href="/' + M.book + '">Browse all media</a>');
        c.addEventListener('click', function (e) { if (e.target.closest('[data-go="again"]')) { c.hidden = true; seek(0); setPlaying(true); } });
      }
      c.hidden = false;
    }

    // ---- keys, idle hiding, resize
    document.addEventListener('keydown', function (e) {
      if (e.target.closest && e.target.closest('input')) return;
      if (e.key === ' ' || e.key === 'k') { e.preventDefault(); setPlaying(!playing); }
      else if (e.key === 'ArrowRight') seek(clock() + 5);
      else if (e.key === 'ArrowLeft') seek(clock() - 5);
      else if (e.key === 't') setText(!showText);
    });
    var idleT;
    function idle() { document.body.classList.remove('idle'); clearTimeout(idleT); idleT = setTimeout(function () { if (playing) document.body.classList.add('idle'); }, 2600); }
    ['mousemove', 'pointerdown', 'touchstart', 'keydown'].forEach(function (ev) { document.addEventListener(ev, idle, { passive: true }); });
    stage.addEventListener('click', function () { if (!document.body.classList.contains('idle')) setPlaying(!playing); });
    addEventListener('resize', function () { if (active) render(active, clock()); });
    window.WATCH.player = { seek: seek, clock: clock, M: M };
  }

  // ---- 2.5D parallax: the keyframe displaced by its depth map. dolly = push toward the near plane, orbit = sideways.
  function Parallax(layer, imgSrc, depthSrc) {
    var c = document.createElement('canvas'), gl = c.getContext('webgl', { premultipliedAlpha: false, antialias: false });
    if (!gl) return null;
    layer.appendChild(c);
    var vs = 'attribute vec2 p;varying vec2 v;void main(){v=p*.5+.5;v.y=1.-v.y;gl_Position=vec4(p,0.,1.);}';
    // Parallax as an inverse lookup: for each screen pixel, step from the nearest depth layer to the farthest and take
    // the first layer whose source pixel is at least that near. Near things then cover far things cleanly (no ghost
    // edges); the 24 steps are refined by one linear step between the last two layers.
    var fs = 'precision mediump float;varying vec2 v;uniform sampler2D img,dep;uniform vec2 cov;uniform float dolly,orbit;' +
      'vec2 src(vec2 u,float L){return (u-.5-vec2(orbit*(L-.45),0.))/(1.+dolly*(.35+.9*L))+.5;}' +
      'void main(){vec2 u=(v-.5)*cov+.5;float pl=1.,pd=0.;vec2 s=src(u,0.);' +
      'for(int i=0;i<=24;i++){float L=1.-float(i)/24.;vec2 c=clamp(src(u,L),0.,1.);float d=texture2D(dep,c).r;' +
      'if(d>=L){float a=(pd-pl)-(d-L);float t=abs(a)>1e-4?(pd-pl)/a:0.;s=clamp(src(u,mix(pl,L,clamp(t,0.,1.))),0.,1.);break;}pl=L;pd=d;s=c;}' +
      'gl_FragColor=texture2D(img,s);}';
    function sh(t, s) { var o = gl.createShader(t); gl.shaderSource(o, s); gl.compileShader(o); return o; }
    var pr = gl.createProgram(); gl.attachShader(pr, sh(gl.VERTEX_SHADER, vs)); gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, fs)); gl.linkProgram(pr);
    if (!gl.getProgramParameter(pr, gl.LINK_STATUS)) { layer.removeChild(c); return null; }
    gl.useProgram(pr);
    var b = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
    var loc = gl.getAttribLocation(pr, 'p'); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    var U = {}; ['img', 'dep', 'cov', 'dolly', 'orbit'].forEach(function (n) { U[n] = gl.getUniformLocation(pr, n); });
    var ready = 0, iw = 16, ih = 9, last = [0, 0];
    function tex(unit, src, uni) {
      var t = gl.createTexture(), im = new Image(); im.crossOrigin = 'anonymous';
      im.onload = function () {
        gl.activeTexture(gl.TEXTURE0 + unit); gl.bindTexture(gl.TEXTURE_2D, t);
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, im);
        [gl.TEXTURE_WRAP_S, gl.TEXTURE_WRAP_T].forEach(function (k) { gl.texParameteri(gl.TEXTURE_2D, k, gl.CLAMP_TO_EDGE); });
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
        gl.uniform1i(uni, unit); if (unit === 0) { iw = im.naturalWidth; ih = im.naturalHeight; }
        ready++; draw(last[0], last[1]);
      };
      im.src = src;
    }
    tex(0, imgSrc, U.img); tex(1, depthSrc, U.dep);
    function draw(dolly, orbit) {
      last = [dolly, orbit]; if (ready < 2) return;
      var dpr = Math.min(window.devicePixelRatio || 1, 2), w = Math.round(c.clientWidth * dpr), h = Math.round(c.clientHeight * dpr);
      if (c.width !== w || c.height !== h) { c.width = w; c.height = h; }
      gl.viewport(0, 0, w, h);
      var va = w / h, ia = iw / ih;                            // cover: show the centre of the keyframe at the viewport's aspect
      gl.uniform2f(U.cov, va > ia ? 1 : va / ia, va > ia ? ia / va : 1);
      gl.uniform1f(U.dolly, dolly); gl.uniform1f(U.orbit, orbit);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    }
    return { draw: draw };
  }
})();
