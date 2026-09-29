// Books menu in the site nav: close it on an outside click or Escape.
(function () {
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
