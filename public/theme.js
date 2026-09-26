(() => {
  const storageKey = 'wa_display_theme';
  const root = document.documentElement;
  const systemPreference = window.matchMedia?.('(prefers-color-scheme: dark)');
  let preference = null;

  try {
    const saved = localStorage.getItem(storageKey);
    if (saved === 'light' || saved === 'dark') preference = saved;
  } catch {}

  const activeTheme = () => preference || (systemPreference?.matches ? 'dark' : 'light');

  const renderTheme = () => {
    const dark = activeTheme() === 'dark';
    root.dataset.theme = dark ? 'dark' : 'light';
    const toggle = document.getElementById('theme-toggle');
    if (!toggle) return;
    const label = dark ? '밝은 화면으로 전환' : '다크 모드 켜기';
    toggle.setAttribute('aria-label', label);
    toggle.setAttribute('title', label);
    toggle.setAttribute('aria-pressed', String(dark));
  };

  renderTheme();

  const bindToggle = () => {
    const toggle = document.getElementById('theme-toggle');
    toggle?.addEventListener('click', () => {
      preference = activeTheme() === 'dark' ? 'light' : 'dark';
      try {
        localStorage.setItem(storageKey, preference);
      } catch {}
      renderTheme();
    });
    renderTheme();
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bindToggle, { once: true });
  } else {
    bindToggle();
  }

  systemPreference?.addEventListener('change', () => {
    if (!preference) renderTheme();
  });
})();
