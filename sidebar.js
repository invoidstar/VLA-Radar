/* Local-only navigation sizing. No network requests or reading-state changes. */
'use strict';
(function () {
  const sidebar = document.getElementById('sidebar');
  if (!sidebar || document.getElementById('sidebar-resizer')) return;
  const root = document.documentElement;
  const desktop = window.matchMedia('(min-width: 701px)');
  const key = 'vla-radar.sidebar-width.v1';
  const MIN = 244, MAX = 380, CONTENT_MIN = 400;
  const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
  function readPreference() {
    try {
      const raw = localStorage.getItem(key);
      if (raw === null || !raw.trim()) return null;
      const value = Number(raw);
      return Number.isFinite(value) ? clamp(Math.round(value), MIN, MAX) : null;
    } catch { return null; }
  }
  let preferred = readPreference(), drag = null, frame = 0, pending = null;
  const handle = document.createElement('div');
  handle.id = 'sidebar-resizer';
  handle.className = 'sidebar-resizer';
  handle.setAttribute('role', 'separator');
  handle.setAttribute('aria-orientation', 'vertical');
  handle.setAttribute('aria-controls', 'sidebar');
  handle.setAttribute('aria-label', '网站导航宽度');
  handle.title = '拖拽调整导航宽度；双击或按 Enter 恢复默认；方向键微调';
  document.body.appendChild(handle);

  function bounds() {
    return {min: MIN, max: Math.max(MIN, Math.min(MAX, root.clientWidth - CONTENT_MIN))};
  }
  function updateAria() {
    const range = bounds();
    const width = Math.round(sidebar.getBoundingClientRect().width);
    handle.tabIndex = desktop.matches ? 0 : -1;
    handle.setAttribute('aria-hidden', String(!desktop.matches));
    handle.setAttribute('aria-valuemin', String(range.min));
    handle.setAttribute('aria-valuemax', String(range.max));
    handle.setAttribute('aria-valuenow', String(clamp(width, range.min, range.max)));
    handle.setAttribute('aria-valuetext', width + ' 像素');
  }
  function render(value = preferred) {
    if (value === null) root.style.removeProperty('--sidebar-user-width');
    else {
      const range = bounds();
      root.style.setProperty('--sidebar-user-width', clamp(value, range.min, range.max) + 'px');
    }
    updateAria();
  }
  function persist() {
    try {
      if (preferred === null) localStorage.removeItem(key);
      else localStorage.setItem(key, String(preferred));
    } catch { /* Storage may be disabled; resizing must still work. */ }
  }
  function cancelFrame() {
    if (frame) cancelAnimationFrame(frame);
    frame = 0; pending = null;
  }
  function finish(commit) {
    if (!drag) return;
    const current = drag;
    const next = pending === null ? Math.round(sidebar.getBoundingClientRect().width) : pending;
    cancelFrame();
    drag = null;
    root.classList.remove('sidebar-resizing');
    if (commit) {
      const range = bounds();
      preferred = clamp(next, range.min, range.max);
      persist();
    } else preferred = current.preferred;
    render();
    if (handle.hasPointerCapture(current.id)) handle.releasePointerCapture(current.id);
  }
  function reset() {
    finish(false); preferred = null; render(); persist();
  }
  handle.addEventListener('pointerdown', event => {
    if (!desktop.matches || event.button !== 0 || !event.isPrimary || drag) return;
    event.preventDefault();
    drag = {id: event.pointerId, x: event.clientX,
      width: sidebar.getBoundingClientRect().width, preferred};
    handle.focus({preventScroll: true});
    root.classList.add('sidebar-resizing');
    try { handle.setPointerCapture(event.pointerId); }
    catch { finish(false); }
  });
  handle.addEventListener('pointermove', event => {
    if (!drag || event.pointerId !== drag.id) return;
    const range = bounds();
    pending = clamp(Math.round(drag.width + event.clientX - drag.x), range.min, range.max);
    if (!frame) frame = requestAnimationFrame(() => {
      frame = 0;
      if (drag && pending !== null) render(pending);
    });
  });
  handle.addEventListener('pointerup', event => {
    if (drag && event.pointerId === drag.id) finish(true);
  });
  for (const type of ['pointercancel', 'lostpointercapture']) {
    handle.addEventListener(type, event => {
      if (drag && event.pointerId === drag.id) finish(false);
    });
  }
  handle.addEventListener('dblclick', reset);
  handle.addEventListener('keydown', event => {
    if (!desktop.matches) return;
    const range = bounds(), width = sidebar.getBoundingClientRect().width;
    const step = event.shiftKey ? 24 : 8;
    let next;
    if (event.key === 'Enter') { event.preventDefault(); reset(); return; }
    if (event.key === 'ArrowLeft') next = width - step;
    else if (event.key === 'ArrowRight') next = width + step;
    else if (event.key === 'Home') next = range.min;
    else if (event.key === 'End') next = range.max;
    else return;
    event.preventDefault();
    finish(false);
    preferred = clamp(Math.round(next), range.min, range.max);
    render(); persist();
  });
  document.addEventListener('keydown', event => {
    if (drag && event.key === 'Escape') {
      event.preventDefault(); finish(false);
    }
  });
  window.addEventListener('blur', () => finish(false));
  window.addEventListener('resize', () => {
    // Clamp the displayed width without destroying a wider-screen preference.
    finish(false); render();
  });
  window.addEventListener('storage', event => {
    if (!drag && (event.key === key || event.key === null)) {
      preferred = readPreference(); render();
    }
  });
  render();
})();
