(function() {
  'use strict';

  var suap = new SuapClient(SUAP_URL, CLIENT_ID, REDIRECT_URI, SCOPE);
  suap.init();

  if (!suap.isAuthenticated()) {
    window.location.href = '/';
    return;
  }

  var accessToken = localStorage.getItem('acolhe_access_token') || suap.getToken().getValue();
  var userId = localStorage.getItem('acolhe_user_id');
  var currentUser = null;

  function init() {
    if (!userId && accessToken) {
      syncWithBackend(function() {
        loadUserInfo();
        loadDisciplinas();
      });
    } else {
      loadUserInfo();
      loadDisciplinas();
    }
    setupEventListeners();
    var semestreEl = document.getElementById('semestre-text');
    if (semestreEl) semestreEl.textContent = SEMESTRE_VIGENTE;
  }

  function syncWithBackend(callback) {
    showLoading();
    fetch('/auth/callback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ access_token: accessToken, semestre: SEMESTRE_VIGENTE })
    })
    .then(function(response) {
      if (!response.ok) throw new Error('HTTP ' + response.status);
      return response.json();
    })
    .then(function(data) {
      if (data.usuario) {
        currentUser = data.usuario;
        localStorage.setItem('acolhe_user', JSON.stringify(data.usuario));
        localStorage.setItem('acolhe_user_id', data.usuario.id);
        userId = data.usuario.id;
        updateUserInfoUI();
      }
      if (callback) callback();
    })
    .catch(function(error) {
      console.error('Erro ao sincronizar no init:', error);
      if (callback) callback();
    });
  }

  function loadUserInfo() {
    var savedUser = localStorage.getItem('acolhe_user');
    if (savedUser) {
      try {
        currentUser = JSON.parse(savedUser);
      } catch (e) {}
    }
    if (!currentUser) {
      suap.getResource(suap.getToken().getScope(), function(response) {
        if (response) {
          currentUser = response;
          localStorage.setItem('acolhe_user', JSON.stringify(response));
          updateUserInfoUI();
        }
      });
    }
    updateUserInfoUI();
  }

  function updateUserInfoUI() {
    if (!currentUser) return;
    var name = currentUser.nome || currentUser.nome_usual || 'Usuario';
    var avatarEl = document.getElementById('user-avatar');
    var nameEl = document.getElementById('user-name');
    if (avatarEl) {
      avatarEl.textContent = name.split(' ').map(function(n) { return n[0]; }).slice(0, 2).join('').toUpperCase();
    }
    if (nameEl) nameEl.textContent = name;
  }

  function loadDisciplinas() {
    if (!userId) {
      renderEmpty('Nenhuma disciplina encontrada', 'Clique em Sincronizar para buscar suas disciplinas no SUAP');
      return;
    }
    showLoading();
    fetch('/auth/disciplinas?usuario_id=' + userId + '&semestre=' + SEMESTRE_VIGENTE, {
      headers: { 'Authorization': 'Bearer ' + accessToken }
    })
    .then(function(response) {
      if (!response.ok) throw new Error('HTTP ' + response.status);
      return response.json();
    })
    .then(function(disciplinas) {
      if (disciplinas && disciplinas.length > 0) {
        renderDisciplinas(disciplinas);
      } else {
        renderEmpty('Nenhuma disciplina encontrada', 'Clique em Sincronizar para buscar suas disciplinas no SUAP');
      }
    })
    .catch(function(error) {
      console.error('Erro ao carregar disciplinas:', error);
      renderEmpty('Erro ao carregar disciplinas', 'Tente sincronizar com o SUAP novamente');
    });
  }

  function handleSync() {
    var btnSync = document.getElementById('btn-sync');
    if (btnSync) btnSync.disabled = true;
    showLoading();

    if (!accessToken) {
      showToast('Token de acesso nao encontrado. Faca login novamente.', 'error');
      renderEmpty('Erro de autenticacao', 'Faca login novamente para sincronizar');
      if (btnSync) btnSync.disabled = false;
      return;
    }

    fetch('/auth/callback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ access_token: accessToken, semestre: SEMESTRE_VIGENTE })
    })
    .then(function(response) {
      if (!response.ok) {
        return response.json().then(function(err) {
          throw new Error(err.detail || 'Erro na sincronizacao');
        });
      }
      return response.json();
    })
    .then(function(data) {
      if (data.usuario) {
        currentUser = data.usuario;
        localStorage.setItem('acolhe_user', JSON.stringify(data.usuario));
        localStorage.setItem('acolhe_user_id', data.usuario.id);
        userId = data.usuario.id;
        updateUserInfoUI();
      }
      if (data.disciplinas && data.disciplinas.length > 0) {
        renderDisciplinas(data.disciplinas);
        showToast(data.disciplinas.length + ' disciplina(s) sincronizada(s)', 'success');
      } else {
        renderEmpty('Nenhuma disciplina encontrada', 'Voce nao esta matriculado em nenhuma disciplina neste semestre');
        showToast('Nenhuma disciplina encontrada para o semestre ' + SEMESTRE_VIGENTE, 'warning');
      }
    })
    .catch(function(error) {
      console.error('Erro ao sincronizar:', error);
      var msg = error.message || 'Erro desconhecido';
      if (msg.indexOf('SUAP') !== -1 || msg.indexOf('Connection') !== -1 || msg.indexOf('timeout') !== -1) {
        renderEmpty('SUAP indisponivel', 'Nao foi possivel conectar ao SUAP no momento. Tente novamente mais tarde.');
        showToast('SUAP fora do ar. Tente novamente mais tarde.', 'error');
      } else {
        renderEmpty('Erro ao sincronizar', msg);
        showToast('Erro ao sincronizar: ' + msg, 'error');
      }
    })
    .finally(function() {
      if (btnSync) btnSync.disabled = false;
    });
  }

  function renderDisciplinas(disciplinas) {
    var grid = document.getElementById('disciplinas-grid');
    if (!grid) return;
    grid.innerHTML = '';

    var colors = ['#0A7F70', '#1565C0', '#6A1B9A', '#C62828', '#E65100', '#2E7D32', '#00838F', '#4527A0', '#AD1457', '#00695C'];

    disciplinas.forEach(function(disc, index) {
      var color = colors[index % colors.length];
      var sigla = disc.sigla || disc.descricao.substring(0, 6).toUpperCase();
      var situacaoClass = 'situacao-' + (disc.situacao || '').toLowerCase().replace(/\s+/g, '-');

      var card = document.createElement('div');
      card.className = 'disciplina-card';
      card.innerHTML =
        '<div class="disciplina-header" style="background:' + color + '">' +
          '<div class="disciplina-sigla">' + escapeHtml(sigla) + '</div>' +
          '<div class="disciplina-descricao">' + escapeHtml(disc.descricao) + '</div>' +
        '</div>' +
        '<div class="disciplina-body">' +
          (disc.professor
            ? '<div class="disciplina-info">' +
                '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>' +
                '<span>' + escapeHtml(disc.professor) + '</span>' +
              '</div>'
            : '') +
          (disc.situacao
            ? '<div class="disciplina-info">' +
                '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>' +
                '<span class="situacao-badge ' + situacaoClass + '">' + escapeHtml(disc.situacao) + '</span>' +
              '</div>'
            : '') +
          '<div class="disciplina-info">' +
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>' +
            '<span>' + escapeHtml(disc.semestre) + '</span>' +
          '</div>' +
        '</div>';

      grid.appendChild(card);
    });
  }

  function showLoading() {
    var grid = document.getElementById('disciplinas-grid');
    if (!grid) return;
    grid.innerHTML =
      '<div class="disciplinas-empty">' +
        '<div class="spinner"></div>' +
        '<h3>Sincronizando com SUAP...</h3>' +
        '<p>Aguarde enquanto buscamos suas disciplinas</p>' +
      '</div>';
  }

  function renderEmpty(title, subtitle) {
    var grid = document.getElementById('disciplinas-grid');
    if (!grid) return;
    grid.innerHTML =
      '<div class="disciplinas-empty">' +
        '<div class="empty-state-icon">' +
          '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">' +
            '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>' +
            '<path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>' +
          '</svg>' +
        '</div>' +
        '<h3>' + escapeHtml(title) + '</h3>' +
        '<p>' + escapeHtml(subtitle) + '</p>' +
      '</div>';
  }

  function showToast(message, type) {
    var toast = document.getElementById('toast');
    var toastMsg = document.getElementById('toast-message');
    var toastIcon = document.getElementById('toast-icon');
    if (!toast || !toastMsg) return;

    toast.className = 'toast toast-' + (type || 'info');
    toastMsg.textContent = message;

    var icons = {
      success: '\u2713',
      error: '\u2717',
      warning: '\u26A0',
      info: '\u2139'
    };
    if (toastIcon) toastIcon.textContent = icons[type] || icons.info;

    toast.hidden = false;
    clearTimeout(window._toastTimeout);
    window._toastTimeout = setTimeout(function() {
      toast.hidden = true;
    }, 4000);
  }

  function escapeHtml(text) {
    if (!text) return '';
    var div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function setupEventListeners() {
    var btnSync = document.getElementById('btn-sync');
    if (btnSync) btnSync.addEventListener('click', handleSync);

    var btnLogout = document.getElementById('btn-logout');
    if (btnLogout) btnLogout.addEventListener('click', handleLogout);
  }

  function handleLogout() {
    if (confirm('Deseja realmente sair?')) {
      if (suap.isAuthenticated()) {
        suap.getToken().revoke();
      }
      localStorage.removeItem('acolhe_access_token');
      localStorage.removeItem('acolhe_user');
      localStorage.removeItem('acolhe_user_id');
      window.location.replace('/');
    }
  }

  document.addEventListener('DOMContentLoaded', init);
})();
