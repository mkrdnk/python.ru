(function () {
  'use strict';
  var theme = document.querySelector('.theme-toggle');
  var menu = document.querySelector('.mobile-menu');
  var nav = document.getElementById('main-nav');
  var dialog = document.querySelector('.search-dialog');
  var opener = null;
  function updateTheme() {
    var dark = document.documentElement.dataset.theme === 'dark';
    theme.setAttribute('aria-label', dark ? 'Включить светлую тему' : 'Включить тёмную тему');
    theme.setAttribute('aria-pressed', String(dark));
  }
  if (theme) {
    theme.hidden = false;
    updateTheme();
    theme.addEventListener('click', function () {
      var value = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
      document.documentElement.dataset.theme = value;
      try { localStorage.setItem('pythonru-theme', value); } catch (error) {}
      updateTheme();
    });
  }
  function closeMenu() {
    if (!menu || !nav) return;
    nav.classList.remove('is-open');
    menu.setAttribute('aria-expanded', 'false');
    menu.setAttribute('aria-label', 'Открыть меню');
  }
  if (menu && nav) {
    menu.hidden = false;
    menu.addEventListener('click', function () {
      var expanded = nav.classList.toggle('is-open');
      menu.setAttribute('aria-expanded', String(expanded));
      menu.setAttribute('aria-label', expanded ? 'Закрыть меню' : 'Открыть меню');
    });
    nav.addEventListener('click', closeMenu);
    document.addEventListener('click', function (event) {
      if (!nav.contains(event.target) && !menu.contains(event.target)) closeMenu();
    });
    // Hidden desktop/mobile navigation must not retain an expanded state on resize.
    window.addEventListener('resize', closeMenu);
  }
  function openSearch(event) {
    if (!dialog || typeof dialog.showModal !== 'function') return;
    if (event) event.preventDefault();
    if (dialog.open) return;
    opener = document.activeElement;
    closeMenu();
    dialog.showModal();
    document.body.classList.add('modal-open');
    dialog.querySelector('input').focus();
  }
  if (dialog) {
    document.querySelectorAll('[data-open-search]').forEach(function (link) {
      link.addEventListener('click', function (event) {
        if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
        openSearch(event);
      });
    });
    dialog.querySelector('[data-close-search]').addEventListener('click', function () { dialog.close(); });
    dialog.addEventListener('click', function (event) { if (event.target === dialog) dialog.close(); });
    dialog.addEventListener('close', function () {
      document.body.classList.remove('modal-open');
      if (opener) opener.focus();
    });
  }
  document.addEventListener('keydown', function (event) {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') openSearch(event);
    if (event.key === 'Escape') closeMenu();
  });
}());
