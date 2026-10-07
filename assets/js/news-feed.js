(function () {
  'use strict';
  var items = document.getElementById('news-items');
  if (!items || !window.fetch || !window.URL) return;
  var status = document.getElementById('feed-status');
  var loading = false;
  var failed = false;
  var observer = null;

  function watch() {
    if (!observer) return;
    observer.disconnect();
    var link = items.querySelector('.feed-more');
    if (link && !failed) observer.observe(link);
  }

  function loadMore(link) {
    if (loading) return;
    loading = true;
    failed = false;
    link.setAttribute('aria-disabled', 'true');
    items.setAttribute('aria-busy', 'true');
    status.textContent = 'Загрузка…';
    var url = new URL(link.href, window.location.href);
    url.searchParams.set('fragment', '1');
    fetch(url.toString(), {credentials: 'same-origin'})
      .then(function (response) {
        if (!response.ok) throw new Error('Feed request failed');
        return response.text();
      })
      .then(function (html) {
        var page = document.createElement('div');
        page.innerHTML = html;
        var articles = page.querySelectorAll('.feed-article');
        if (!articles.length && !page.querySelector('.empty-state')) throw new Error('Invalid feed response');
        var focused = document.activeElement === link;
        var firstAdded = null;
        Array.prototype.forEach.call(articles, function (article) {
          var id = article.getAttribute('data-article-id');
          var duplicate = Array.prototype.some.call(items.querySelectorAll('[data-article-id]'), function (existing) {
            return existing.getAttribute('data-article-id') === id;
          });
          if (!duplicate) {
            if (!firstAdded) firstAdded = article;
            items.insertBefore(article, link.parentNode);
          }
        });
        var next = page.querySelector('.feed-pagination');
        link.parentNode.remove();
        if (next) items.appendChild(next);
        status.textContent = next ? '' : 'Все публикации загружены.';
        if (focused && firstAdded) {
          var headingLink = firstAdded.querySelector('h2 a, h3 a');
          headingLink.focus({preventScroll: true});
        }
      })
      .catch(function () {
        failed = true;
        link.removeAttribute('aria-disabled');
        link.textContent = 'Повторить загрузку';
        status.textContent = 'Не удалось загрузить публикации. Попробуйте ещё раз.';
      })
      .then(function () {
        loading = false;
        items.removeAttribute('aria-busy');
        watch();
      });
  }

  items.addEventListener('click', function (event) {
    var link = event.target.closest('.feed-more');
    if (!link || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || event.button !== 0) return;
    event.preventDefault();
    loadMore(link);
  });
  if ('IntersectionObserver' in window && items.dataset.autoload !== 'false') {
    observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting && !failed) loadMore(entry.target);
      });
    }, {rootMargin: '400px'});
    watch();
  }
}());
