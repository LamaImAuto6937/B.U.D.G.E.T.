
/* ── Theme Toggle ─────────────────────────────────── */
(function () {
  const root = document.documentElement, btn = document.querySelector('[data-theme-toggle]');
  
  // darkMode aus localStorage laden (Boolean: true = dark, false = light), oder OS-Einstellung als Fallback
  let darkModeEnabled = localStorage.getItem('darkMode') !== null 
    ? JSON.parse(localStorage.getItem('darkMode'))
    : matchMedia('(prefers-color-scheme:dark)').matches;
  
  let d = darkModeEnabled ? 'dark' : 'light';
  
  function apply(t) {
    d = t;
    darkModeEnabled = t === 'dark';
    root.setAttribute('data-theme', t);
    localStorage.setItem('darkMode', JSON.stringify(darkModeEnabled));
    btn.innerHTML = t === 'dark'
      ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>'
      : '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
    btn.setAttribute('aria-label', 'Zu ' + (t === 'dark' ? 'hellem' : 'dunklem') + ' Modus wechseln');
  }
  
  apply(d);
  btn.addEventListener('click', () => apply(d === 'dark' ? 'light' : 'dark'));
})();

/* ── Tab Switch ──────────────────────────────────── */
function switchTab(w) {
  ['login', 'register'].forEach(t => {
    document.getElementById('tab-' + t).classList.toggle('active', t === w);
    document.getElementById('tab-' + t).setAttribute('aria-selected', t === w);
    document.getElementById('panel-' + t).classList.toggle('active', t === w);
  });
  clearBanners();
}

/* ── Password Visibility ─────────────────────────── */
const EYE_OPEN = '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12S5 5 12 5s11 7 11 7-4 7-11 7S1 12 1 12z"/><circle cx="12" cy="12" r="3"/></svg>';
const EYE_OFF = '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>';
function togglePw(id, btn) {
  const inp = document.getElementById(id), show = inp.type === 'text';
  inp.type = show ? 'password' : 'text';
  btn.innerHTML = show ? EYE_OPEN : EYE_OFF;
  btn.setAttribute('aria-label', show ? 'Passwort anzeigen' : 'Passwort verbergen');
}

/* ── Password Strength (proper algorithm) ────────── */
// Criteria: length, upper, lower, digit, special/umlaut
// Penalty for common patterns
const COMMON = /passwort|password|passw0rt|123456|qwertz|qwerty|abcdef|letmein|willkommen|hallo|login|admin|berlin/i;
const SEQ_NUM = /01234|12345|23456|34567|45678|56789|67890/;

function evalCriteria(pw) {
  return {
    len: pw.length >= 8,
    upper: /[A-ZÄÖÜ]/.test(pw),
    lower: /[a-zäöüß]/.test(pw),
    digit: /[0-9]/.test(pw),
    special: /[^A-Za-z0-9äöüÄÖÜß]/.test(pw) || /[äöüÄÖÜß]/.test(pw),
  };
}

function calcStrength(pw) {
  if (!pw) return 0;
  const c = evalCriteria(pw);
  let score = 0;

  // Complexity points (max 5)
  if (c.len) score++;
  if (c.upper) score++;
  if (c.lower) score++;
  if (c.digit) score++;
  if (c.special) score++;

  // Bonus for longer passwords
  if (pw.length >= 12) score++;
  if (pw.length >= 16) score++;

  // Hard penalties
  if (COMMON.test(pw)) score -= 4;   // common word
  if (SEQ_NUM.test(pw)) score -= 1;  // sequential numbers

  // Must have minimum length — no length, no higher than Schwach
  if (!c.len) score = Math.min(score, 1);

  score = Math.max(0, score);

  if (score <= 1) return 1; // Sehr schwach
  if (score <= 3) return 2; // Schwach
  if (score <= 5) return 3; // Mittel
  return 4;                // Stark
}

const STRENGTH_CONFIG = [
  null,
  { label: 'Sehr schwach', cls: 's1', color: '#e05c4b' },
  { label: 'Schwach', cls: 's2', color: '#e08a3b' },
  { label: 'Mittel', cls: 's3', color: '#b8a000' },
  { label: 'Stark', cls: 's4', color: 'var(--color-success)' },
];

function onPwInput(pw) {
  const fill = document.getElementById('strength-fill');
  const lbl = document.getElementById('strength-label');
  const crit = evalCriteria(pw);
  const level = calcStrength(pw);

  // Update bar
  fill.className = 'strength-bar-fill';
  if (!pw) {
    fill.style.width = '0%';
    lbl.textContent = 'Passwort eingeben';
    lbl.style.color = 'var(--color-text-faint)';
  } else {
    const cfg = STRENGTH_CONFIG[level];
    fill.classList.add(cfg.cls);
    lbl.textContent = cfg.label;
    lbl.style.color = cfg.color;
  }

  // Update criteria badges
  toggleCrit('crit-len', crit.len);
  toggleCrit('crit-upper', crit.upper);
  toggleCrit('crit-lower', crit.lower);
  toggleCrit('crit-digit', crit.digit);
  toggleCrit('crit-special', crit.special);

  checkConfirm();
}

function toggleCrit(id, met) {
  document.getElementById(id).classList.toggle('met', met);
}

/* ── Confirm Match ───────────────────────────────── */
function checkConfirm() {
  const pw1 = document.getElementById('reg-password').value;
  const pw2 = document.getElementById('reg-password2').value;
  const inp = document.getElementById('reg-password2');
  const msg = document.getElementById('reg-pw2-msg');
  if (!pw2) { inp.classList.remove('input-success', 'input-error'); msg.textContent = ''; msg.className = 'field-msg muted'; return; }
  const match = pw1 === pw2;
  inp.classList.toggle('input-success', match);
  inp.classList.toggle('input-error', !match);
  msg.textContent = match ? '✓ Passwörter stimmen überein' : '✗ Passwörter stimmen nicht überein';
  msg.className = 'field-msg ' + (match ? 'success' : 'error');
}

/* ── Login Handler ───────────────────────────────── */
function handleLogin(e) {
  e.preventDefault();
  const username = document.getElementById('login-username').value.trim();
  const pw = document.getElementById('login-password').value;
  let valid = true;
  
  if (!username) {
    setField('login-username', 'login-username-msg', 'Bitte gib deinen Benutzernamen ein.', 'error');
    valid = false;
  } else {
    clearField('login-username', 'login-username-msg');
  }
  
  if (!pw) {
    setField('login-password', 'login-pw-msg', 'Bitte gib dein Passwort ein.', 'error');
    valid = false;
  } else {
    clearField('login-password', 'login-pw-msg');
  }
  
  if (!valid) return;
  
  // Formular absenden
  document.getElementById('login-form').submit();
}

/* ── Register Handler ────────────────────────────── */
function handleRegister(e) {
  e.preventDefault();
  const username = document.getElementById('reg-username').value.trim();
  const pw1 = document.getElementById('reg-password').value;
  const pw2 = document.getElementById('reg-password2').value;
  let valid = true;

  if (!username) {
    setField('reg-username', 'reg-username-msg', 'Bitte gib einen Benutzernamen ein.', 'error'); valid = false;
  } else clearField('reg-username', 'reg-username-msg');

  if (calcStrength(pw1) < 2) {
    setField('reg-password', 'reg-pw-msg', 'Wähle ein stärkeres Passwort.', 'error'); valid = false;
  } else clearField('reg-password', 'reg-pw-msg');

  if (pw1 !== pw2) {
    setField('reg-password2', 'reg-pw2-msg', '✗ Passwörter stimmen nicht überein', 'error'); valid = false;
  }
  if (!valid) return;
  
  // Formular absenden
  document.getElementById('register-form').submit();
}

/* ── Forgot Password Modal ───────────────────────── */
function openForgot(e) {
  if (e) e.preventDefault();
  // reset modal state
  document.getElementById('forgot-form-body').style.display = '';
  document.getElementById('forgot-success').classList.remove('show');
  document.getElementById('forgot-email').value = '';
  document.getElementById('forgot-email-msg').textContent = '';
  document.getElementById('forgot-email-msg').className = 'field-msg muted';
  document.getElementById('forgot-backdrop').classList.add('open');
  setTimeout(() => document.getElementById('forgot-email').focus(), 260);
}
function closeForgot() {
  document.getElementById('forgot-backdrop').classList.remove('open');
}
function closeForgotOnBackdrop(e) {
  if (e.target === document.getElementById('forgot-backdrop')) closeForgot();
}
function submitForgot() {
  const email = document.getElementById('forgot-email').value.trim();
  const msg = document.getElementById('forgot-email-msg');
  if (!email || !/\S+@\S+\.\S+/.test(email)) {
    msg.textContent = 'Bitte gib eine gültige E-Mail-Adresse ein.';
    msg.className = 'field-msg error';
    document.getElementById('forgot-email').classList.add('input-error');
    return;
  }
  msg.textContent = ''; msg.className = 'field-msg muted';
  document.getElementById('forgot-email').classList.remove('input-error');
  
  // Sende POST-Request zum Backend
  const formData = new FormData();
  formData.append('email', email);
  
  fetch('/reset_password', {
    method: 'POST',
    body: formData
  })
  .then(response => {
    document.getElementById('forgot-form-body').style.display = 'none';
    const sMsg = document.getElementById('forgot-success-msg');
    sMsg.textContent = 'Wir haben einen Reset-Link an ' + email + ' gesendet, falls ein Konto existiert.';
    document.getElementById('forgot-success').classList.add('show');
  })
  .catch(error => {
    console.error('Fehler beim Passwort-Reset:', error);
    msg.textContent = 'Fehler beim Senden. Bitte versuche es später erneut.';
    msg.className = 'field-msg error';
  });
}

// Close modal on Escape
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeForgot(); });

/* ── Helpers ─────────────────────────────────────── */
function setField(inputId, msgId, text, type) {
  document.getElementById(inputId).classList.add('input-' + type);
  const m = document.getElementById(msgId); m.textContent = text; m.className = 'field-msg ' + type;
}
function clearField(inputId, msgId) {
  document.getElementById(inputId).classList.remove('input-error', 'input-success');
  const m = document.getElementById(msgId); m.textContent = ''; m.className = 'field-msg muted';
}
function clearBanners() {
  ['login-banner', 'register-banner'].forEach(id => {
    const el = document.getElementById(id); el.className = 'msg-banner'; el.textContent = '';
  });
}

/* ── Password Character Filter ───────────────────────── */
// Allowed: latin letters (incl. umlauts/ß), digits, common symbols
// Blocked: spaces, CJK, emoji, control chars, etc.
const PW_CHAR_RE = /[a-zA-Z0-9äöüÄÖÜß!"§$%&\/()=?\+\*#\-_\.,;:@<>\[\]{}|~\^`'\\]/;

function filterPwInput(e) {
  const inp = e.target;
  const orig = inp.value;
  const cur = inp.selectionStart;
  const filtered = orig.split('').filter(ch => PW_CHAR_RE.test(ch)).join('');
  if (filtered !== orig) {
    const removed = orig.length - filtered.length;
    inp.value = filtered;
    const newPos = Math.max(0, cur - removed);
    inp.setSelectionRange(newPos, newPos);
  }
}

document.addEventListener('DOMContentLoaded', function () {
  ['login-password', 'reg-password', 'reg-password2'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('input', filterPwInput, true);
  });
  
  // Flask-Meldungen anzeigen (error/success)
  const urlParams = new URLSearchParams(window.location.search);
  const errorMsg = document.body.getAttribute('data-error');
  const successMsg = document.body.getAttribute('data-success');
  
  if (errorMsg) {
    const banner = document.getElementById('login-banner');
    banner.className = 'msg-banner error';
    banner.textContent = '✗ ' + errorMsg;
  }
  if (successMsg) {
    const banner = document.getElementById('register-banner');
    banner.className = 'msg-banner success';
    banner.textContent = '✓ ' + successMsg;
  }
});