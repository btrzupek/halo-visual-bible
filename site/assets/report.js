// Report a problem: a small dialog that lets a reader flag a scene's picture or narration
// (extra fingers, a modern object, a mispronounced name). Shared by every book page and every
// /read/<book> page. Reports go to /api/report (api/report.js), which files them in a private
// GitHub repo. Nothing personal is collected: no name, no email, no cookies.
//
// Book pages: loaded with defer after the page script; adds a link to each scene (article.scene)
// and to the hero. The reader (present.js) calls VBReport.open(...) from its own button.
(function () {
  var REASONS = {
    image: [
      ['limbs', 'Extra or missing limbs, hands or fingers'],
      ['body', 'A distorted face or body'],
      ['modern', 'A modern object (a watch, glasses, plastic, writing)'],
      ['text', 'Does not match the passage'],
      ['history', 'Theologically or historically wrong'],
      ['modesty', 'Immodest or too violent'],
      ['other', 'Something else']
    ],
    audio: [
      ['name', 'A name is mispronounced'],
      ['word', 'A word is misread, skipped or repeated'],
      ['glitch', 'A glitch, noise or cut-off'],
      ['sync', 'The highlighted verse is out of step'],
      ['other', 'Something else']
    ]
  };
  var NOTE_MAX = 500, HOUR = 3600e3, DAY = 24 * HOUR;
  var FLAG = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 3h2v18H5zM8 4h10l-2 4 2 4H8z"/></svg>';

  function esc(s) { return String(s).replace(/[&<>"]/g, function (m) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[m]; }); }
  function refText(ctx) { return ctx.book + ' ' + ctx.c + ':' + ctx.a + (ctx.b > ctx.a ? '–' + ctx.b : ''); }

  // ---- styles: injected here so book pages and the reader need no CSS changes
  var css =
    '.vbr{--r-bg:var(--bg,#12162a);--r-panel:var(--panel,#1a1f36);--r-ink:var(--ink,#e7dfcc);--r-muted:var(--muted,var(--soft,#a3a3b4));' +
      '--r-gilt:var(--gilt,#cfa959);--r-rule:var(--rule,rgba(212,176,102,.28));' +
      'width:min(30rem,calc(100vw - 1.5rem));max-height:calc(100svh - 1.5rem);overflow:auto;padding:1.3rem 1.4rem 1.2rem;' +
      'border:1px solid var(--r-rule);border-radius:6px;background:var(--r-bg);color:var(--r-ink);font-family:var(--serif,Georgia,serif);' +
      'font-size:1rem;line-height:1.5;box-shadow:0 30px 80px -20px rgba(0,0,0,.6)}' +
    '.vbr::backdrop{background:rgba(5,6,10,.6)}' +
    '.vbr h2{font-family:var(--display,Georgia,serif);font-weight:400;font-size:1.35rem;line-height:1.2;margin:0 0 .2rem}' +
    '.vbr .vbr-where{color:var(--r-muted);font-style:italic;margin:0 0 1rem}' +
    '.vbr fieldset{border:0;padding:0;margin:0 0 1rem;min-width:0}' +
    '.vbr legend,.vbr .vbr-label{display:block;font-family:var(--display,Georgia,serif);color:var(--r-gilt);font-size:.95rem;letter-spacing:.04em;padding:0;margin:0 0 .4rem}' +
    '.vbr .vbr-kind{display:flex;gap:.4rem}' +
    '.vbr .vbr-kind label{flex:1;text-align:center;border:1px solid var(--r-rule);border-radius:999px;padding:.4rem .6rem;cursor:pointer}' +
    '.vbr .vbr-kind input{position:absolute;opacity:0;pointer-events:none}' +
    '.vbr .vbr-kind label:has(input:checked){background:var(--r-gilt);border-color:var(--r-gilt);color:var(--r-bg)}' +
    '.vbr .vbr-kind label:has(input:focus-visible){outline:2px solid var(--r-gilt);outline-offset:2px}' +
    '.vbr .vbr-reasons label{display:flex;gap:.55rem;align-items:flex-start;padding:.22rem 0;cursor:pointer}' +
    '.vbr .vbr-reasons input{margin:.3rem 0 0;accent-color:var(--r-gilt)}' +
    '.vbr textarea{display:block;width:100%;min-height:4.5rem;resize:vertical;font:inherit;font-size:.95rem;color:var(--r-ink);' +
      'background:var(--r-panel);border:1px solid var(--r-rule);border-radius:4px;padding:.5rem .6rem}' +
    '.vbr .vbr-hint{color:var(--r-muted);font-size:.85rem;margin:.35rem 0 0}' +
    '.vbr .vbr-hp{position:absolute;left:-10000px;width:1px;height:1px;overflow:hidden}' +
    '.vbr .vbr-row{display:flex;justify-content:flex-end;gap:.6rem;margin-top:1rem}' +
    '.vbr button{font-family:var(--display,Georgia,serif);font-size:1rem;letter-spacing:.03em;border-radius:999px;padding:.5rem 1.2rem;cursor:pointer;' +
      'border:1px solid var(--r-rule);background:none;color:var(--r-ink)}' +
    '.vbr button.vbr-send{background:var(--r-gilt);border-color:var(--r-gilt);color:var(--r-bg)}' +
    '.vbr button:disabled{opacity:.5;cursor:default}' +
    '.vbr .vbr-msg{margin:.8rem 0 0;color:var(--r-gilt)}' +
    '.vbr .vbr-msg:empty{display:none}' +
    '.vbr-flag{display:inline-flex;align-items:center;gap:.35rem;margin-top:1rem;padding:0;border:0;background:none;cursor:pointer;' +
      'font-family:var(--display,Georgia,serif);font-size:.85rem;letter-spacing:.03em;color:var(--muted,#a3a3b4);opacity:.75}' +
    '.vbr-flag:hover,.vbr-flag:focus-visible{opacity:1;color:var(--gilt,#cfa959)}' +
    '.vbr-flag svg{width:.95em;height:.95em;fill:currentColor}' +
    '.hero .vbr-flag{color:#cbbf9f}';
  var style = document.createElement('style');
  style.textContent = css;
  document.head.appendChild(style);

  // ---- the dialog, built once
  var dlg, form, ctx, openedAt = 0, onclose = null;
  function build() {
    dlg = document.createElement('dialog');
    dlg.className = 'vbr';
    dlg.setAttribute('aria-labelledby', 'vbr-title');
    dlg.innerHTML =
      '<form method="dialog" novalidate>' +
      '<h2 id="vbr-title">Report a problem</h2><p class="vbr-where"></p>' +
      '<fieldset><legend>What is wrong?</legend><div class="vbr-kind">' +
        '<label><input type="radio" name="kind" value="image"> The picture</label>' +
        '<label><input type="radio" name="kind" value="audio"> The narration</label></div></fieldset>' +
      '<fieldset><legend>Reason</legend><div class="vbr-reasons"></div></fieldset>' +
      '<label class="vbr-label" for="vbr-note">Anything else? (optional)</label>' +
      '<textarea id="vbr-note" name="note" maxlength="' + NOTE_MAX + '"></textarea>' +
      '<p class="vbr-hint">Please leave out your name, email and other personal details. Reports go to a private list for review.</p>' +
      '<div class="vbr-hp" aria-hidden="true"><label>Website <input type="text" name="website" tabindex="-1" autocomplete="off"></label></div>' +
      '<p class="vbr-msg" role="status"></p>' +
      '<div class="vbr-row"><button type="button" class="vbr-cancel">Cancel</button><button type="submit" class="vbr-send">Send report</button></div>' +
      '</form>';
    document.body.appendChild(dlg);
    form = dlg.querySelector('form');
    form.addEventListener('change', function (e) { if (e.target.name === 'kind') reasons(e.target.value); });
    dlg.querySelector('.vbr-cancel').onclick = close;
    form.addEventListener('submit', function (e) { e.preventDefault(); send(); });
    dlg.addEventListener('close', function () { var f = onclose; onclose = null; if (f) f(); });
    // a click on the backdrop closes it
    dlg.addEventListener('click', function (e) { if (e.target === dlg) close(); });
  }
  var EXAMPLE = { image: 'For example: the man on the left has six fingers', audio: 'For example: a name in verse 3 sounds wrong' };
  function reasons(kind) {
    form.querySelector('textarea').placeholder = EXAMPLE[kind];
    dlg.querySelector('.vbr-reasons').innerHTML = REASONS[kind].map(function (r) {
      return '<label><input type="radio" name="reason" value="' + r[0] + '"><span>' + esc(r[1]) + '</span></label>';
    }).join('');
  }
  function msg(t) { dlg.querySelector('.vbr-msg').textContent = t; }
  function close() { if (dlg.open) dlg.close(); }

  // ctx: {slug, book, c, a, b, file, audio?, kind?: 'image'|'audio', onclose?}
  function open(c) {
    if (!dlg) build();
    ctx = c; onclose = c.onclose || null;
    form.reset();
    var kind = c.kind === 'audio' ? 'audio' : 'image';
    form.querySelector('input[name="kind"][value="' + kind + '"]').checked = true;
    reasons(kind);
    dlg.querySelector('.vbr-where').textContent = refText(c) + (c.title ? ', ' + c.title : '');
    msg('');
    var send = dlg.querySelector('.vbr-send');
    send.disabled = false; send.hidden = false;
    dlg.querySelector('.vbr-cancel').textContent = 'Cancel';
    openedAt = Date.now();
    if (dlg.showModal) dlg.showModal(); else dlg.setAttribute('open', '');
    form.querySelector('input[name="kind"]:checked').focus();
  }

  // ---- light client-side limits (the server has its own): 10 an hour, no repeats for a day
  function sent() {
    try { return JSON.parse(localStorage.getItem('vb-reports') || '[]').filter(function (r) { return Date.now() - r[0] < DAY; }); }
    catch (e) { return []; }
  }
  function remember(key) {
    try { var s = sent(); s.push([Date.now(), key]); localStorage.setItem('vb-reports', JSON.stringify(s.slice(-40))); } catch (e) {}
  }

  function send() {
    var f = new FormData(form), kind = f.get('kind'), reason = f.get('reason');
    if (!reason) { msg('Please choose a reason.'); return; }
    var scene = ctx.slug + '.' + ctx.c + '.' + ctx.a, key = scene + '/' + kind + '/' + reason, past = sent();
    if (past.some(function (r) { return r[1] === key; })) { msg('You already reported this. Thank you.'); return; }
    if (past.filter(function (r) { return Date.now() - r[0] < HOUR; }).length >= 10) { msg('That is a lot of reports in an hour. Please try again later.'); return; }
    var btn = dlg.querySelector('.vbr-send');
    btn.disabled = true; msg('Sending…');
    var body = {
      v: 1, slug: ctx.slug, chapter: ctx.c, verse: ctx.a, last: ctx.b, scene: scene,
      file: ctx.file, audio: ctx.audio || null, kind: kind, reason: reason,
      note: String(f.get('note') || '').slice(0, NOTE_MAX), url: location.href,
      website: f.get('website') || '', t: Date.now() - openedAt
    };
    fetch('/api/report', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body), credentials: 'omit' })
      .then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { return { ok: r.ok, status: r.status, j: j }; }); })
      .then(function (r) {
        if (r.ok) {
          remember(key);
          msg('Thank you. The report was sent.');
          btn.hidden = true;
          dlg.querySelector('.vbr-cancel').textContent = 'Close';
        } else {
          btn.disabled = false;
          msg(r.status === 429 ? 'Too many reports right now. Please try again later.'
            : (r.j && r.j.error) || 'Sorry, the report could not be sent. Please try again later.');
        }
      })
      .catch(function () { btn.disabled = false; msg('Sorry, the report could not be sent. Please check your connection and try again.'); });
  }

  window.VBReport = { open: open };

  // ---- book pages: a link on every scene and on the hero
  if (window.READ || !window.VB || !VB.ch) return;
  var folder = location.pathname.split('/')[1] || '';
  var slug = folder === 'bible' ? 'john' : folder;
  function flag() { return '<button type="button" class="vbr-flag">' + FLAG + 'Report a problem</button>'; }
  function scene(c, a) {
    var s = VB.ch[c] && VB.ch[c].scenes.filter(function (x) { return x[0] === a; })[0];
    return s ? { slug: slug, c: c, a: a, b: s[1], file: s[2], title: s[3] } : null;
  }
  // the book's name as the page prints it ("1 Samuel 3:1–10" gives "1 Samuel")
  var m0 = /^(.+?) \d+:\d+/.exec((document.querySelector('article.scene .ref') || {}).textContent || '');
  var book = m0 ? m0[1] : slug;
  [].forEach.call(document.querySelectorAll('article.scene'), function (art) {
    var m = /^s(\d+)-(\d+)$/.exec(art.id), t = art.querySelector('.text');
    if (m && t) { t.insertAdjacentHTML('beforeend', flag()); t.lastChild.dataset.scene = m[1] + '-' + m[2]; }
  });
  var hero = document.getElementById('prologue') || document.getElementById('hero-ref'), first = VB.ch[1] && VB.ch[1].scenes[0];
  if (hero && first) { hero.insertAdjacentHTML('afterend', flag()); hero.nextSibling.dataset.scene = '1-' + first[0]; }
  document.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('.vbr-flag'); if (!b) return;
    var p = b.dataset.scene.split('-'), c = scene(+p[0], +p[1]); if (!c) return;
    c.book = book;
    open(c);
  });
})();
