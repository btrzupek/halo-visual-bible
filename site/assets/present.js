// Read: the full-window presentation player shared by every /read/<book> page.
// Each page sets window.READ = {book, title, lede, back} and loads the book's chapter files
// (VB.add), plus optional VB.motion (Ken Burns frames) and VB.audio (narration with verse times).
(function () {
  var R = window.READ, VB = window.VB, IMG = '/images/full/';
  var MOTION = VB.motion || {}, AUDIO = VB.audio || null;
  var DEFAULT = [[0.5, 0.5, 1], [0.5, 0.42, 1.14]];  // a slow push-in when a scene has no frames yet
  var portrait = matchMedia('(max-aspect-ratio: 1/1), (max-width: 760px)');  // same test as the CSS sheet layout
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var tuning = /[?&]tune\b/.test(location.search);
  function $(s) { return document.querySelector(s); }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (m) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[m]; }); }
  function webp(f) { return f.replace(/\.png$/, '.webp'); }

  // ---- the scene list, in reading order
  var list = [];
  Object.keys(VB.ch).map(Number).sort(function (a, b) { return a - b; }).forEach(function (c) {
    VB.ch[c].scenes.forEach(function (s, i) {
      list.push({ c: c, a: s[0], b: s[1], file: s[2], title: s[3], sub: s[4], trim: s[5], kind: s[6] || 0,
        key: c + ':' + s[0], id: 's' + c + '-' + s[0], first: i === 0 });
    });
  });
  function verses(sc) { var v = VB.ch[sc.c].v, out = []; for (var n = sc.a; n <= sc.b; n++) out.push([n, v[n - 1]]); return out; }
  function words(sc) { return verses(sc).reduce(function (t, v) { return t + v[1].split(/\s+/).length; }, 0); }
  function refText(sc) { return R.book + ' ' + sc.c + ':' + sc.a + (sc.b > sc.a ? '–' + sc.b : ''); }

  // ---- DOM
  document.body.insertAdjacentHTML('beforeend',
    '<div class="stage" id="stage"><div class="layer"><img alt=""></div><div class="layer"><img alt=""></div></div>' +
    '<div class="card" id="card" aria-hidden="true"><span></span></div>' +
    '<aside class="panel" id="panel" aria-live="polite"><p class="ref"></p><h1></h1><p class="sub"></p>' +
      '<div class="verses" id="verses" tabindex="0"></div><button class="cue" id="cue" type="button">Continue</button></aside>' +
    '<div class="progress" aria-hidden="true"><i id="bar"></i></div>' +
    '<div class="top"><a class="back" href="' + R.back + '">' + esc(R.book) + '</a><span class="place" id="place"></span></div>' +
    '<div class="controls" role="group" aria-label="Player">' +
      '<select id="chap" aria-label="Chapter"></select><span class="sep"></span>' +
      '<button type="button" id="prev" aria-label="Previous scene"><svg viewBox="0 0 24 24"><path d="M6 5h2v14H6zM20 5v14L9 12z"/></svg></button>' +
      '<button type="button" id="play" class="main" aria-label="Pause"><svg viewBox="0 0 24 24"></svg></button>' +
      '<button type="button" id="next" aria-label="Next scene"><svg viewBox="0 0 24 24"><path d="M16 5h2v14h-2zM4 5v14l11-7z"/></svg></button>' +
      '<span class="sep"></span>' +
      '<button type="button" id="voice" aria-label="Narration" aria-pressed="false" hidden><svg viewBox="0 0 24 24"><path d="M4 9v6h4l5 4V5L8 9zm12.5 3a4.5 4.5 0 0 0-2.5-4v8a4.5 4.5 0 0 0 2.5-4zM14 3.2v2.1a7 7 0 0 1 0 13.4v2.1a9 9 0 0 0 0-17.6z"/></svg></button>' +
      '<button type="button" id="full" aria-label="Full screen"><svg viewBox="0 0 24 24"><path d="M4 4h6v2H6v4H4zm10 0h6v6h-2V6h-4zM4 14h2v4h4v2H4zm14 0h2v6h-6v-2h4z"/></svg></button>' +
    '</div>');

  var stage = $('#stage'), layers = stage.querySelectorAll('.layer'), panel = $('#panel'), vbox = $('#verses'),
      cue = $('#cue'), bar = $('#bar'), card = $('#card'), playBtn = $('#play'), chap = $('#chap'), voiceBtn = $('#voice');
  var ICON_PLAY = '<path d="M7 4v16l13-8z"/>', ICON_PAUSE = '<path d="M6 4h4v16H6zm8 0h4v16h-4z"/>';

  var opts = '';
  list.forEach(function (sc, i) { if (sc.first) opts += '<option value="' + i + '">Chapter ' + sc.c + '</option>'; });
  chap.innerHTML = opts;

  // ---- state
  var idx = 0, cur = 0, playing = true, narrate = false, voiced = false, anim = null, dur = 0, done = false, token = 0;
  var audio = new Audio(), nextAudio = null, advanceTimer = null, followPause = 0, frames = null;
  audio.preload = 'auto';
  if (AUDIO) {
    voiceBtn.hidden = false;
    try { narrate = localStorage.getItem('read-narrate') === '1'; } catch (e) {}
  }

  // ---- Ken Burns geometry. A frame is [x, y, s]: the point of interest as a fraction of the
  // image, and a zoom (1 = the whole window covered, as with object-fit: cover). The point is
  // brought to the middle of the part of the window the text panel leaves free.
  function geometry(img) {
    var W = innerWidth, H = innerHeight, iw = img.naturalWidth || 1344, ih = img.naturalHeight || 768;
    var k = Math.max(W / iw, H / ih), dw = iw * k, dh = ih * k, p = panel.getBoundingClientRect(), cx = W / 2, cy = H / 2, sheet = false, floor = H;
    if (p.width && p.height) {
      // sheet at the bottom: the point sits a little low in the space above it, so faces stay in view
      // the picture may rise until its bottom edge is a little under the sheet, so the lower half is reachable
      if (p.width > W * 0.6) { cy = p.top * 0.6; sheet = true; floor = p.top + (H - p.top) * 0.3; }
      else if (p.left > W / 2) cx = p.left / 2;            // panel on the right
      else cx = (p.right + W) / 2;                          // panel on the left
    }
    img.style.width = dw + 'px'; img.style.height = dh + 'px';
    return { W: W, H: H, dw: dw, dh: dh, cx: cx, cy: cy, sheet: sheet, floor: floor };
  }
  function transform(g, f, trim) {
    // a portrait window already crops a wide picture hard, so it gets half the zoom
    var s = (g.sheet ? 1 + (f[2] - 1) / 2 : f[2]) * (trim ? 1.03 : 1);
    var tx = Math.min(0, Math.max(g.W - s * g.dw, g.cx - s * f[0] * g.dw));
    var ty = Math.min(0, Math.max(g.floor - s * g.dh, g.cy - s * f[1] * g.dh));
    return 'translate(' + tx.toFixed(1) + 'px,' + ty.toFixed(1) + 'px) scale(' + s.toFixed(4) + ')';
  }
  // entries 3 and 4, when present, are the start and end for portrait windows, which see a narrow slice
  function framesFor(sc) {
    var m = MOTION[sc.key] || DEFAULT;
    if (portrait.matches && m[2]) m = [m[2], m[3] || m[2]];
    // wide-screen points low in the picture land on bodies without heads on a phone, so cap them there
    else if (portrait.matches) m = [m[0], m[1]].map(function (f) { return [f[0], Math.min(f[1], 0.42), f[2]]; });
    else m = [m[0], m[1]];
    return reduce ? [m[0], m[0]] : m;
  }

  function startMotion(img, sc, seconds) {
    if (anim) anim.cancel();
    var g = geometry(img), f = frames;
    if (tuning) { img.style.transform = transform(g, tune.f, sc.trim); anim = null; return; }
    anim = img.animate([{ transform: transform(g, f[0], sc.trim) }, { transform: transform(g, f[1], sc.trim) }],
      { duration: seconds * 1000, easing: 'cubic-bezier(.42,0,.58,1)', fill: 'forwards' });
    anim.onfinish = function () { if (!voiced) finish(); };
    if (!playing) anim.pause();
  }
  addEventListener('resize', function () {
    var img = layers[cur].querySelector('img'), sc = list[idx];
    if (!img.naturalWidth) return;
    if (tuning) return startMotion(img, sc, 0);
    if (!anim) return;
    frames = framesFor(sc);  // a phone turned sideways switches between portrait and landscape frames
    var g = geometry(img);
    anim.effect.setKeyframes([{ transform: transform(g, frames[0], sc.trim) }, { transform: transform(g, frames[1], sc.trim) }]);
  });

  // ---- one scene
  function readingSeconds(sc) { return Math.max(16, Math.min(120, words(sc) / 2.6)); }
  function place(sc) {
    $('#place').innerHTML = esc(refText(sc)) + ' <b>·</b> ' + (idx + 1) + ' of ' + list.length;
    var c = 0; [].forEach.call(chap.options, function (o, i) { if (+o.value <= idx) c = i; }); chap.selectedIndex = c;
  }
  function fillPanel(sc) {
    var tag = sc.kind === 1 ? ' <span class="tag">· A parable</span>' : sc.kind === 2 ? ' <span class="tag">· A vision</span>' : '';
    panel.querySelector('.ref').innerHTML = esc(refText(sc)) + tag;
    panel.querySelector('h1').textContent = sc.title;
    panel.querySelector('.sub').textContent = sc.sub;
    vbox.innerHTML = verses(sc).map(function (v) { return '<p data-v="' + v[0] + '"><sup>' + v[0] + '</sup>' + esc(v[1]) + '</p>'; }).join('');
    vbox.scrollTop = 0;
    // the panel sits on the side away from where the camera ends up
    var x = frames[1][0], left = x > 0.56 ? true : x < 0.44 ? false : idx % 2 === 1;
    panel.classList.toggle('left', left); panel.classList.toggle('right', !left);
  }
  function wait(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }

  function show(i) {
    if (i < 0 || i >= list.length) return;
    var my = ++token, sc = list[i], prev = idx;
    idx = i; done = false; frames = framesFor(sc);
    clearTimeout(advanceTimer); audio.pause(); if (anim) anim.pause(); spoken = null;
    cue.classList.remove('on'); panel.classList.remove('on', 'narrating'); bar.style.transform = 'scaleX(0)';
    try { history.replaceState(null, '', '#' + sc.id); } catch (e) {}
    if (tuning) tune.load(sc);
    place(sc);

    var nl = layers[1 - cur], img = nl.querySelector('img');
    nl.classList.toggle('dream', !!sc.kind);
    img.alt = sc.title + ': ' + sc.sub;
    img.src = IMG + webp(sc.file);
    // wait for the load, then a decode, but never hang on either (decode() can stall in a hidden tab)
    var ready = new Promise(function (ok) {
      img.onload = img.onerror = function () { ok(); };
      if (img.complete && img.naturalWidth) ok();
      setTimeout(ok, 6000);
    }).then(function () {
      return Promise.race([img.decode ? img.decode().catch(function () {}) : null, wait(500)]);
    });
    var card1 = sc.first && !(prev === i && i !== 0);
    Promise.all([ready, wait(prev === i ? 0 : 450)]).then(function () {
      if (my !== token) return;
      fillPanel(sc);
      var a = narrate && AUDIO && AUDIO[sc.key], lead = card1 ? 2.2 : 0.9;
      voiced = !!a;
      dur = a ? a.dur + lead + 0.6 : readingSeconds(sc);
      startMotion(img, sc, dur);
      layers[cur].classList.remove('on'); nl.classList.add('on'); cur = 1 - cur;
      if (card1) { card.firstChild.textContent = 'Chapter ' + sc.c; card.classList.add('on'); setTimeout(function () { card.classList.remove('on'); }, 1700); }
      setTimeout(function () {
        if (my !== token) return;
        panel.classList.add('on'); panel.classList.toggle('narrating', !!a);
        if (a) speak(sc, a);
      }, lead * 1000);
      preload(i + 1);
    });
  }
  function preload(i) {
    var sc = list[i]; if (!sc) return;
    new Image().src = IMG + webp(sc.file);
    if (narrate && AUDIO && AUDIO[sc.key]) { nextAudio = new Audio(AUDIO[sc.key].src); nextAudio.preload = 'auto'; }
  }
  function finish() {
    if (done) return; done = true;
    if (idx === list.length - 1) { cue.textContent = 'Back to ' + R.book; }
    else cue.textContent = 'Continue';
    cue.classList.add('on');
    if (voiced && playing && idx < list.length - 1) advanceTimer = setTimeout(function () { show(idx + 1); }, 1500);
  }
  function next() { if (idx < list.length - 1) show(idx + 1); else location.href = R.back; }
  function prev() { show(Math.max(0, idx - 1)); }

  // ---- narration
  function speak(sc, a) {
    audio.src = a.src; audio.currentTime = 0;
    audio.onended = function () { finish(); };
    audio.ontimeupdate = function () { follow(a); };
    if (playing) audio.play().catch(function () { setPlaying(false); });
    mediaSession(sc);
  }
  var spoken = null;  // {a: audio entry, n: verse index} while narrating
  function follow(a) {
    var t = audio.currentTime, n = 0;
    for (var k = 0; k < a.t.length; k++) if (a.t[k] <= t + 0.05) n = k;
    spoken = { a: a, n: n };
    var p = vbox.children[n];
    if (!p || p.classList.contains('now')) return;
    [].forEach.call(vbox.children, function (q) { q.classList.toggle('now', q === p); });
  }
  // Keep the spoken words in view. Driven from the animation frame, not scrollTo({behavior:'smooth'}),
  // which browsers cancel or overshoot inconsistently (it did both on phones).
  function followScroll() {
    if (!spoken || !panel.classList.contains('narrating') || Date.now() < followPause) return;
    var p = vbox.children[spoken.n]; if (!p) return;
    var a = spoken.a, room = vbox.clientHeight, h = p.offsetHeight;
    var top = p.getBoundingClientRect().top - vbox.getBoundingClientRect().top + vbox.scrollTop, want;
    if (h + 24 <= room) {
      want = top - Math.min(room * 0.2, room - h - 12);        // a short verse sits near the top and stays
    } else {                                                    // a tall one glides past as it is read
      var t0 = a.t[spoken.n], t1 = a.t[spoken.n + 1] || a.dur;
      var f = Math.min(1, Math.max(0, (audio.currentTime - t0) / Math.max(0.1, t1 - t0)));
      // the line being spoken (estimated by time) sits a third of the way down, never past either end
      want = Math.min(top + h - room + 24, Math.max(top - 12, top + f * h - room * 0.33));
    }
    want = Math.max(0, Math.min(want, vbox.scrollHeight - room));
    var d = want - vbox.scrollTop;
    if (Math.abs(d) > 0.5) vbox.scrollTop = reduce || Math.abs(d) > room * 2 ? want : vbox.scrollTop + d * 0.12;
  }
  ['wheel', 'touchmove'].forEach(function (ev) { vbox.addEventListener(ev, function () { followPause = Date.now() + 6000; }, { passive: true }); });
  function mediaSession(sc) {
    if (!('mediaSession' in navigator)) return;
    navigator.mediaSession.metadata = new MediaMetadata({ title: sc.title, artist: refText(sc), album: R.title,
      artwork: [{ src: IMG + webp(sc.file), sizes: '1344x768', type: 'image/webp' }] });
    navigator.mediaSession.setActionHandler('play', function () { setPlaying(true); });
    navigator.mediaSession.setActionHandler('pause', function () { setPlaying(false); });
    navigator.mediaSession.setActionHandler('nexttrack', next);
    navigator.mediaSession.setActionHandler('previoustrack', prev);
  }
  function setNarrate(on) {
    narrate = !!on && !!AUDIO;
    voiceBtn.setAttribute('aria-pressed', String(narrate));
    try { localStorage.setItem('read-narrate', narrate ? '1' : '0'); } catch (e) {}
  }

  // ---- play / pause
  function setPlaying(on) {
    playing = on;
    playBtn.querySelector('svg').innerHTML = on ? ICON_PAUSE : ICON_PLAY;
    playBtn.setAttribute('aria-label', on ? 'Pause' : 'Play');
    if (on) {
      if (anim && anim.playState === 'paused') anim.play();
      if (panel.classList.contains('narrating') && audio.src && !audio.ended) audio.play().catch(function () {});
      if (done && voiced) advanceTimer = setTimeout(next, 800);
    } else {
      if (anim) anim.pause(); audio.pause(); clearTimeout(advanceTimer);
    }
    idle();
  }
  function tick() {
    followScroll();
    if (anim && dur) {
      var p = panel.classList.contains('narrating') && audio.duration ? audio.currentTime / audio.duration : (anim.currentTime || 0) / (dur * 1000);
      bar.style.transform = 'scaleX(' + Math.min(1, p).toFixed(4) + ')';
    }
    requestAnimationFrame(tick);
  }

  // ---- controls, keys, touch, idle
  playBtn.onclick = function () { if (done && !voiced) next(); else setPlaying(!playing); };
  $('#next').onclick = next; $('#prev').onclick = prev; cue.onclick = next;
  chap.onchange = function () { show(+chap.value); chap.blur(); };
  voiceBtn.onclick = function () { setNarrate(!narrate); show(idx); };
  var fullBtn = $('#full');
  if (!document.documentElement.requestFullscreen) fullBtn.hidden = true;
  fullBtn.onclick = function () { document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen().catch(function () {}); };

  document.addEventListener('keydown', function (e) {
    if (e.target.closest && e.target.closest('select,textarea,input')) return;
    if (!$('#start').hidden) return;
    var k = e.key;
    if (k === ' ' || k === 'k') { e.preventDefault(); playBtn.click(); }
    else if (k === 'ArrowRight' || k === 'l') next();
    else if (k === 'ArrowLeft' || k === 'j') prev();
    else if (k === 'f') fullBtn.click();
    else if (k === 'n' && AUDIO) voiceBtn.click();
    else return;
    idle();
  });
  var t0 = null;
  document.addEventListener('touchstart', function (e) { t0 = e.touches.length === 1 ? [e.touches[0].clientX, e.touches[0].clientY] : null; }, { passive: true });
  document.addEventListener('touchend', function (e) {
    if (!t0 || tuning || !$('#start').hidden) return;
    var dx = e.changedTouches[0].clientX - t0[0], dy = e.changedTouches[0].clientY - t0[1];
    if (Math.abs(dx) > 60 && Math.abs(dx) > 2 * Math.abs(dy)) dx < 0 ? next() : prev();
  }, { passive: true });

  var idleTimer;
  function idle() {
    document.body.classList.remove('idle'); clearTimeout(idleTimer);
    idleTimer = setTimeout(function () {
      if (playing && !tuning && $('#start').hidden && document.activeElement !== chap) document.body.classList.add('idle');
    }, 3000);
  }
  ['mousemove', 'pointerdown', 'touchstart'].forEach(function (ev) { document.addEventListener(ev, idle, { passive: true }); });

  // ---- start screen
  // #s3-16 opens the scene that holds John 3:16, whether or not a scene starts there
  var startAt = 0, h = /^#s(\d+)-(\d+)$/.exec(location.hash);
  if (h) list.forEach(function (sc, i) { if (sc.c === +h[1] && sc.a <= +h[2] && +h[2] <= sc.b) startAt = i; });
  var s0 = list[startAt];
  document.body.insertAdjacentHTML('beforeend',
    '<section class="start" id="start"><img src="' + IMG + webp(s0.file) + '" alt="">' +
    '<div class="inner"><h1>' + R.title.replace(' of ', '<br>of ') + '</h1><p>' + esc(startAt ? 'Continue from ' + refText(s0) + ', ' + s0.title + '.' : R.lede) + '</p>' +
    '<div class="go">' + (AUDIO ? '<button class="primary" data-n="1">Listen</button><button class="ghost" data-n="0">Read at my own pace</button>'
                                : '<button class="primary" data-n="0">Begin</button>') +
    '<a class="ghost" href="' + R.back + '">The book page</a></div></div></section>');
  $('#start').addEventListener('click', function (e) {
    var b = e.target.closest('button'); if (!b) return;
    setNarrate(b.dataset.n === '1');
    $('#start').hidden = true;
    setPlaying(true);
    show(startAt);
  });
  setPlaying(true);
  requestAnimationFrame(tick);
  R.player = { audio: audio, show: show, list: list };  // handle for debugging from the console

  // ---- ?tune: drag to pan, scroll to zoom, then set the start and end frames for this scene
  var tune = { f: [0.5, 0.5, 1], edits: {} };
  tune.load = function (sc) { tune.f = (tune.edits[sc.key] || frames)[0].slice(); tune.out(); };
  tune.out = function () {
    var sc = list[idx], m = tune.edits[sc.key] || MOTION[sc.key] || DEFAULT, r = function (f) { return '[' + f.map(function (n) { return +n.toFixed(3); }).join(',') + ']'; };
    $('#tune-now').textContent = 'View ' + r(tune.f);
    $('#tune-txt').value = Object.keys(tune.edits).map(function (k) { return '"' + k + '": [' + r(tune.edits[k][0]) + ', ' + r(tune.edits[k][1]) + '],'; }).join('\n')
      || '"' + sc.key + '": [' + r(m[0]) + ', ' + r(m[1]) + '],';
  };
  if (tuning) {
    document.body.classList.add('tuning');
    document.body.insertAdjacentHTML('beforeend', '<div class="tune"><p>Drag to pan, scroll to zoom. Set the start and end views, then Preview. Copy the lines into the motion file.</p>' +
      '<p id="tune-now"></p><div class="row"><button data-t="a">Start = view</button><button data-t="b">End = view</button><button data-t="p">Preview</button><button data-t="c">Copy</button></div><textarea id="tune-txt" spellcheck="false"></textarea></div>');
    var redraw = function () { startMotion(layers[cur].querySelector('img'), list[idx], 0); tune.out(); };
    $('.tune').addEventListener('click', function (e) {
      var t = e.target.dataset.t, sc = list[idx]; if (!t) return;
      var m = tune.edits[sc.key] || (MOTION[sc.key] || DEFAULT).map(function (f) { return f.slice(); });
      if (t === 'a') { m[0] = tune.f.slice(); tune.edits[sc.key] = m; }
      if (t === 'b') { m[1] = tune.f.slice(); tune.edits[sc.key] = m; }
      if (t === 'p') { tuning = false; frames = m; startMotion(layers[cur].querySelector('img'), sc, 8); anim.onfinish = function () { tuning = true; }; return; }
      if (t === 'c') { navigator.clipboard && navigator.clipboard.writeText($('#tune-txt').value); }
      tune.out();
    });
    var drag = null;
    stage.addEventListener('pointerdown', function (e) { drag = [e.clientX, e.clientY]; stage.setPointerCapture(e.pointerId); });
    stage.addEventListener('pointerup', function () { drag = null; });
    stage.addEventListener('pointermove', function (e) {
      if (!drag) return;
      var img = layers[cur].querySelector('img'), g = geometry(img), f = tune.f;
      f[0] = Math.min(1, Math.max(0, f[0] - (e.clientX - drag[0]) / (f[2] * g.dw)));
      f[1] = Math.min(1, Math.max(0, f[1] - (e.clientY - drag[1]) / (f[2] * g.dh)));
      drag = [e.clientX, e.clientY]; redraw();
    });
    stage.addEventListener('wheel', function (e) { e.preventDefault(); tune.f[2] = Math.min(2.6, Math.max(1, tune.f[2] * Math.exp(-e.deltaY * 0.0015))); redraw(); }, { passive: false });
  }
})();
