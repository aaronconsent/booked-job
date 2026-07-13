// Email capture — wires any <form class="capform"> to /api/subscribe with inline success.
// Included on every article + tool page so the traffic magnets actually convert.
(function () {
  function wire(f) {
    f.addEventListener('submit', function (e) {
      e.preventDefault();
      var input = f.querySelector('input[type=email]');
      var email = (input && input.value || '').trim();
      if (!email) return;
      var btn = f.querySelector('button');
      if (btn) { btn.disabled = true; btn.dataset.t = btn.textContent; btn.textContent = 'Sending…'; }
      fetch('/api/subscribe', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email, source: location.pathname })
      }).then(function (r) { return r.json().catch(function () { return {}; }); })
        .then(function () {
          var box = f.closest('.capture') || f.parentElement;
          box.innerHTML = '<div class="capok">✅ You’re in. The honest math is on its way — check your inbox.</div>';
        }).catch(function () {
          if (btn) { btn.disabled = false; btn.textContent = btn.dataset.t || 'Try again'; }
        });
    });
  }
  document.querySelectorAll('form.capform').forEach(wire);
})();
