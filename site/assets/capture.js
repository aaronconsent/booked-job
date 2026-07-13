// Email capture — (1) wires any inline <form class="capform"> to /api/subscribe,
// (2) shows ONE tasteful, dismissible slide-in bar after the reader is engaged
// (55% scroll) to catch the majority who never reach the footer form.
(function () {
  var DONE_KEY = 'bj_sub';      // set once they subscribe anywhere
  var HIDE_KEY = 'bj_cap_x';    // set if they dismiss the slide-in

  function ls(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }

  function submit(form, onOk) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var input = form.querySelector('input[type=email]');
      var email = (input && input.value || '').trim();
      if (!email) return;
      var btn = form.querySelector('button');
      if (btn) { btn.disabled = true; btn.dataset.t = btn.textContent; btn.textContent = 'Sending…'; }
      fetch('/api/subscribe', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email, source: location.pathname })
      }).then(function (r) { return r.json().catch(function () { return {}; }); })
        .then(function () { set(DONE_KEY, '1'); onOk(form); })
        .catch(function () { if (btn) { btn.disabled = false; btn.textContent = btn.dataset.t || 'Try again'; } });
    });
  }

  // 1) inline forms
  document.querySelectorAll('form.capform').forEach(function (f) {
    submit(f, function (form) {
      var box = form.closest('.capture') || form.parentElement;
      box.innerHTML = '<div class="capok">✅ You’re in. The honest math is on its way — check your inbox.</div>';
    });
  });

  // 2) slide-in bar — only on article/tool pages, once, if not subscribed/dismissed
  if (ls(DONE_KEY) || ls(HIDE_KEY)) return;
  if (!document.querySelector('article')) return;   // skip homepage etc.

  var bar, shown = false;
  function build() {
    bar = document.createElement('div');
    bar.className = 'capbar';
    bar.innerHTML =
      '<button class="capbar-x" aria-label="Close">×</button>' +
      '<div class="capbar-txt"><b>Getting the honest math?</b> One short email — real lead costs, review targets, the numbers nobody else shows you.</div>' +
      '<form class="capform capbar-form"><input type="email" placeholder="you@yourshop.com" required aria-label="Email" /><button type="submit">Send it →</button></form>';
    document.body.appendChild(bar);
    bar.querySelector('.capbar-x').addEventListener('click', function () { set(HIDE_KEY, '1'); bar.classList.remove('show'); setTimeout(function () { bar.remove(); }, 300); });
    submit(bar.querySelector('form'), function () {
      bar.querySelector('.capbar-form').outerHTML = '<div class="capbar-ok">✅ You’re in — check your inbox.</div>';
      setTimeout(function () { bar.classList.remove('show'); }, 2600);
    });
    requestAnimationFrame(function () { bar.classList.add('show'); });
  }
  function onScroll() {
    if (shown) return;
    var h = document.documentElement;
    var depth = (h.scrollTop + h.clientHeight) / h.scrollHeight;
    if (depth > 0.55) { shown = true; window.removeEventListener('scroll', onScroll); build(); }
  }
  window.addEventListener('scroll', onScroll, { passive: true });
})();
