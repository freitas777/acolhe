(function() {
'use strict';

if (!acolheRequireRole(['aluno', 'professor'])) return;

  var tipoPerfil = acolheGetTipoPerfil();

  function init() {
    updateUserInfoUI();
    applyNavVisibility();
    setupEventListeners();
    loadDados();
  }

  function updateUserInfoUI() {
    var name = acolheGetUserName() || 'Usuario';
    if (name === 'Usuario') {
      try {
        var storedUser = JSON.parse(localStorage.getItem('acolhe_user') || '{}');
        if (storedUser && storedUser.nome) name = storedUser.nome;
      } catch (e) {}
    }
    var avatarEl = document.getElementById('user-avatar');
    var nameEl = document.getElementById('user-name');
    if (avatarEl) {
      avatarEl.textContent = name.split(' ').map(function(n){ return n[0]; }).slice(0,2).join('').toUpperCase() || '??';
    }
    if (nameEl) nameEl.textContent = name;
  }

  function applyNavVisibility() {
    var navPortal = document.getElementById('nav-portal');
    if (navPortal) navPortal.style.display = tipoPerfil === 'aluno' ? '' : 'none';
  }

  function setupEventListeners() {
    var btnLogout = document.getElementById('btn-logout');
    if (btnLogout) {
      btnLogout.addEventListener('click', function() {
        if (confirm('Deseja realmente sair?')) {
          acolheLogout();
        }
      });
    }
  }

  function loadDados() {
    showLoading();
    Promise.all([
      acolheFetch('/auth/disciplinas?semestre=' + encodeURIComponent(SEMESTRE_VIGENTE || ''))
        .then(function(r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); }),
      acolheFetch('/api/chat/conversations')
        .then(function(r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
    ])
    .then(function(resultados) {
      var disciplinas = resultados[0] || [];
      var conversas = resultados[1] || [];
      var counts = {};
      conversas.forEach(function(c) {
        if (c.disciplina_id) {
          counts[c.disciplina_id] = (counts[c.disciplina_id] || 0) + 1;
        }
      });
      renderCards(disciplinas, counts);
    })
    .catch(function() {
      renderEmpty('Erro ao carregar', 'Nao foi possivel carregar as materias. Tente novamente.');
    });
  }

  function renderCards(disciplinas, counts) {
    var grid = document.getElementById('conversas-grid');
    if (!grid) return;
    grid.innerHTML = '';

    if (!disciplinas || disciplinas.length === 0) {
      renderEmpty('Nenhuma materia encontrada', 'Sincronize suas disciplinas para comecar a conversar.');
      return;
    }

    disciplinas.forEach(function(disc) {
      var count = counts[disc.id] || 0;
      var sigla = disc.sigla || (disc.descricao || '').substring(0, 6).toUpperCase();

      var card = document.createElement('div');
      card.className = 'conversa-card';
      card.setAttribute('data-disciplina-id', disc.id);
      card.style.cursor = 'pointer';
      card.innerHTML =
        '<div class="conversa-card-header">' +
        '<div class="conversa-card-sigla">' + escapeHtml(sigla) + '</div>' +
        '<span class="conversa-card-count">' + count + ' conversa' + (count !== 1 ? 's' : '') + '</span>' +
        '</div>' +
        '<div class="conversa-card-descricao">' + escapeHtml(disc.descricao) + '</div>' +
        (disc.professor ? '<div class="conversa-card-professor">' + escapeHtml(disc.professor) + '</div>' : '') +
        '<div class="conversa-card-semestre">' + escapeHtml(disc.semestre) + '</div>';

      card.addEventListener('click', function() {
        try {
          sessionStorage.setItem('acolhe_open_conversa', JSON.stringify({
            tipo: 'disciplina',
            disciplina_id: disc.id,
            disciplina_descricao: disc.descricao
          }));
        } catch (e) {}
        window.location.href = '/chat';
      });

      grid.appendChild(card);
    });
  }

  function showLoading() {
    var grid = document.getElementById('conversas-grid');
    if (!grid) return;
    grid.innerHTML =
      '<div class="conversas-empty"><div class="spinner"></div><h3>Carregando...</h3></div>';
  }

  function renderEmpty(title, subtitle) {
    var grid = document.getElementById('conversas-grid');
    if (!grid) return;
    grid.innerHTML =
      '<div class="conversas-empty">' +
      '<h3>' + escapeHtml(title) + '</h3>' +
      '<p>' + escapeHtml(subtitle) + '</p>' +
      '</div>';
  }

  function escapeHtml(text) {
    if (!text) return '';
    var div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  document.addEventListener('DOMContentLoaded', init);
})();