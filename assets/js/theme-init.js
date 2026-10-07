(function () {
  document.documentElement.classList.add('js');
  var theme = 'light';
  try { theme = localStorage.getItem('pythonru-theme') || theme; } catch (error) {}
  document.documentElement.dataset.theme = theme === 'dark' ? 'dark' : 'light';
}());
