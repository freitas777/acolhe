(function() {
'use strict';

if (!acolheRequireRole(['psicopedagogo', 'servidor', 'admin'])) return;

  var currentUser = null;

  function init() {
    loadUserInfo();
    setupEventListeners();
  }

  function loadUserInfo() {
    var userName = acolheGetUserName();
    currentUser = { nome: userName };
    updateUserInfoUI();
  }

  function updateUserInfoUI() {
    if (!currentUser) return;
    var name = currentUser.nome || currentUser.nome_usual || 'Usuario';
    var avatarEl = document.getElementById('user-avatar');
    var nameEl = document.getElementById('user-name');
    if (avatarEl) {
      avatarEl.textContent = name.split(' ').map(function(n){ return n[0]; }).slice(0,2).join('').toUpperCase();
    }
    if (nameEl) nameEl.textContent = name;
  }

  function setupEventListeners() {
    var btnLogout = document.getElementById('btn-logout');
    var manualForm = document.getElementById('manual-form');

    if (btnLogout) {
      btnLogout.addEventListener('click', function() {
        if (confirm('Deseja realmente sair?')) {
          acolheLogout();
        }
      });
    }

    if (manualForm) {
      manualForm.addEventListener('submit', function(e) {
        e.preventDefault();
        handleManualSubmit();
      });
    }
  }

  function showToast(message, type) {
    var toast = document.getElementById('toast');
    var toastMsg = document.getElementById('toast-message');
    var toastIcon = document.getElementById('toast-icon');
    if (!toast || !toastMsg) return;
    toast.className = 'toast toast-' + (type || 'info');
    toastMsg.textContent = message;
    var icons = { success: '\u2713', error: '\u2717', warning: '\u26A0', info: '\u2139' };
    if (toastIcon) toastIcon.textContent = icons[type] || icons.info;
    toast.hidden = false;
    clearTimeout(window._toastTimeout);
    window._toastTimeout = setTimeout(function() { toast.hidden = true; }, 4000);
  }

  function escapeHtml(text) {
    if (!text) return '';
    var div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function handleManualSubmit() {
    var nomeEl = document.getElementById('manual-nome');
    var matriculaEl = document.getElementById('manual-matricula');
    var cursoEl = document.getElementById('manual-curso');
    var campusEl = document.getElementById('manual-campus');
    var emailEl = document.getElementById('manual-email');
    var btnSubmit = document.getElementById('btn-manual-submit');

    var nome = nomeEl ? nomeEl.value.trim() : '';
    var matricula = matriculaEl ? matriculaEl.value.trim() : '';

    if (!nome) {
      showToast('Informe o nome do aluno', 'warning');
      if (nomeEl) nomeEl.focus();
      return;
    }
    if (!matricula) {
      showToast('Informe a matricula do aluno', 'warning');
      if (matriculaEl) matriculaEl.focus();
      return;
    }

    var payload = {
      nome: nome,
      matricula: matricula,
      curso: cursoEl ? cursoEl.value.trim() : '',
      campus: campusEl ? campusEl.value.trim() : '',
      email: emailEl ? emailEl.value.trim() : ''
    };

    if (btnSubmit) {
      btnSubmit.disabled = true;
      btnSubmit.textContent = 'Cadastrando...';
    }

    acolheFetch('/importacao/manual', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    .then(function(r) {
      if (r.status === 409) {
        return r.json().then(function(data) {
          throw new Error(data.detail || 'Aluno ja cadastrado');
        });
      }
      if (!r.ok) {
        return r.json().then(function(data) {
          throw new Error(data.detail || 'Erro ao cadastrar aluno');
        }).catch(function(e) {
          if (e.message === 'Sessao expirada') throw e;
          throw new Error(e.message || 'Erro ao cadastrar aluno');
        });
      }
      return r.json();
    })
    .then(function(aluno) {
      showToast('Aluno ' + escapeHtml(aluno.nome || matricula) + ' cadastrado com sucesso!', 'success');
      if (nomeEl) nomeEl.value = '';
      if (matriculaEl) matriculaEl.value = '';
      if (cursoEl) cursoEl.value = '';
      if (campusEl) campusEl.value = '';
      if (emailEl) emailEl.value = '';
      if (nomeEl) nomeEl.focus();
    })
    .catch(function(err) {
      if (err.message === 'Sessao expirada. Faca login novamente.') return;
      showToast('Erro: ' + err.message, 'error');
    })
    .finally(function() {
      if (btnSubmit) {
        btnSubmit.disabled = false;
        btnSubmit.innerHTML = '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><line x1="20" y1="8" x2="20" y2="14"/><line x1="23" y1="11" x2="17" y2="11"/></svg> Cadastrar Aluno';
      }
    });
  }

  document.addEventListener('DOMContentLoaded', init);
})();