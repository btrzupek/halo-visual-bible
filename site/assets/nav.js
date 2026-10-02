// Site nav: the Back button, and the Books menu (close it on an outside click or Escape).
(function () {
  // Back: the same "Back" in the upper left of every page but the home page. It returns to the page you came
  // from on this site; with no such page (a shared link, a new tab) it goes up instead: an All scenes page to its
  // reader, everything else home. The reader has the same button in its own top bar (present.js).
  var nav = document.querySelector('.sitenav');
  var path = location.pathname.replace(/\/+$/, '') || '/';
  if (nav && path !== '/') {
    var book = path.slice(1), up = '/';
    if (/^[a-z0-9]+$/.test(book) && document.querySelector('.chapnav')) up = '/read/' + (book === 'bible' ? 'john' : book);
    var a = document.createElement('a');
    a.className = 'navback'; a.href = up; a.textContent = 'Back';
    nav.insertBefore(a, nav.firstChild);
    var from = false;
    try { var r = new URL(document.referrer); from = r.origin === location.origin && (r.pathname.replace(/\/+$/, '') || '/') !== path; } catch (e) {}
    var start = history.length;   // chapter links on this page add history entries; step back over them too
    a.addEventListener('click', function (e) {
      if (!from) return;
      e.preventDefault();
      history.go(-(1 + Math.max(0, history.length - start)));
    });
  }

  function closeAll(except) {
    document.querySelectorAll('.sitenav details.books[open]').forEach(function (d) { if (d !== except) d.removeAttribute('open'); });
  }
  document.addEventListener('click', function (e) { closeAll(e.target.closest('.sitenav details.books')); });
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    var open = document.querySelector('.sitenav details.books[open]');
    if (open) { open.removeAttribute('open'); open.querySelector('summary').focus(); }
  });
})();
