(function() {
'use strict';

if (!acolheRequireAuth()) return;

  var userId = localStorage.getItem('acolhe_user_id');
  var currentUser = null;
  var tipoPerfil = localStorage.getItem('acolhe_tipo_perfil') || 'aluno';
  var currentView = 'grid';

  function init() {
    if (!userId && acolheGetToken()) {
      syncWithBackend(function() {
        loadUserInfo();
        loadDisciplinas();
      });
    } else {
      loadUserInfo();
      loadDisciplinas();
    }
setupEventListeners();
applyNavVisibility();
var semestreEl = document.getElementById('semestre-text');
    if (semestreEl) semestreEl.textContent = SEMESTRE_VIGENTE;
  }

  function syncWithBackend(callback) {
    showLoading();
    acolheFetch('/auth/callback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ access_token: acolheGetToken(), semestre: SEMESTRE_VIGENTE })
    })
    .then(function(response) {
      if (!response.ok) throw new Error('HTTP ' + response.status);
      return response.json();
    })
    .then(function(data) {
      if (data.usuario) {
        currentUser = data.usuario;
        tipoPerfil = data.tipo_perfil || data.usuario.tipo_perfil || 'aluno';
        localStorage.setItem('acolhe_user', JSON.stringify(data.usuario));
        localStorage.setItem('acolhe_user_id', data.usuario.id);
        localStorage.setItem('acolhe_tipo_perfil', tipoPerfil);
        userId = data.usuario.id;
        updateUserInfoUI();
      }
      if (callback) callback();
    })
    .catch(function(error) {
      if (callback) callback();
    });
  }

  function loadUserInfo() {
  var savedUser = localStorage.getItem('acolhe_user');
    if (savedUser) {
        try {
            var parsed = JSON.parse(savedUser);
            currentUser = parsed;
            tipoPerfil = parsed.tipo_perfil || localStorage.getItem('acolhe_tipo_perfil') || 'aluno';
        } catch (e) {}
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
    var titleEl = document.querySelector('.page-title');
    if (titleEl) {
        if (tipoPerfil === 'professor') {
            titleEl.textContent = 'Meus Diarios';
        } else if (tipoPerfil === 'servidor') {
            titleEl.textContent = 'Meus Diarios';
        } else {
            titleEl.textContent = 'Minhas Disciplinas';
        }
    }

    if (tipoPerfil === 'servidor') {
        var napneBanner = document.createElement('div');
        napneBanner.className = 'napne-banner';
        napneBanner.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:18px;height:18px;flex-shrink:0"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg><span>Voce ainda nao tem acesso ao Painel NAPNE. Solicite ao Administrador do Sistema a liberacao do seu perfil.</span>';
        var mainEl = document.querySelector('.disciplinas-page');
        if (mainEl) mainEl.insertBefore(napneBanner, mainEl.firstChild);
    }
  }

  function loadDisciplinas() {
    if (!userId) {
      renderEmpty('Nenhuma disciplina encontrada', 'Clique em Sincronizar para buscar suas disciplinas no SUAP');
      return;
    }
    showLoading();
    var url = '/auth/disciplinas?usuario_id=' + userId + '&semestre=' + SEMESTRE_VIGENTE;
  if (tipoPerfil === 'professor' || tipoPerfil === 'servidor') url += '&apenas_assistidos=true';
  acolheFetch(url)
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
      renderEmpty('Erro ao carregar disciplinas', 'Tente sincronizar com o SUAP novamente');
    });
  }

  function handleSync() {
    var btnSync = document.getElementById('btn-sync');
    if (btnSync) btnSync.disabled = true;
    showLoading();

  if (!acolheGetToken()) {
    showToast('Token de acesso nao encontrado. Faca login novamente.', 'error');
    renderEmpty('Erro de autenticacao', 'Faca login novamente para sincronizar');
    if (btnSync) btnSync.disabled = false;
    return;
  }

  acolheFetch('/auth/callback', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ access_token: acolheGetToken(), semestre: SEMESTRE_VIGENTE })
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
        tipoPerfil = data.tipo_perfil || data.usuario.tipo_perfil || 'aluno';
        localStorage.setItem('acolhe_user', JSON.stringify(data.usuario));
        localStorage.setItem('acolhe_user_id', data.usuario.id);
        localStorage.setItem('acolhe_tipo_perfil', tipoPerfil);
        userId = data.usuario.id;
        updateUserInfoUI();
      }
      loadDisciplinas();
      if (data.disciplinas && data.disciplinas.length > 0) {
        showToast(data.disciplinas.length + ' disciplina(s) sincronizada(s)', 'success');
      } else {
        showToast('Nenhuma disciplina encontrada para o semestre ' + SEMESTRE_VIGENTE, 'warning');
      }
    })
    .catch(function(error) {
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

    var isProfessor = tipoPerfil === 'professor' || tipoPerfil === 'servidor';
    var colors = ['#0A7F70', '#1565C0', '#6A1B9A', '#C62828', '#E65100', '#2E7D32', '#00838F', '#4527A0', '#AD1457', '#00695C'];

    disciplinas.forEach(function(disc, index) {
      var color = colors[index % colors.length];
      var sigla = disc.sigla || (disc.descricao || '').substring(0, 6).toUpperCase();
      var situacaoClass = 'situacao-' + (disc.situacao || '').toLowerCase().replace(/\s+/g, '-');

      var card = document.createElement('div');
      card.className = 'disciplina-card';
      card.setAttribute('data-disciplina-id', disc.id);
      if (!isProfessor || disc.qtd_alunos_assistidos > 0) {
        card.style.cursor = 'pointer';
      }

      var assistidosBadge = '';
      if (isProfessor) {
        var count = disc.qtd_alunos_assistidos || 0;
        var badgeClass = count > 0 ? 'assistidos-badge has-assistidos' : 'assistidos-badge no-assistidos';
        assistidosBadge = '<div class="' + badgeClass + '">' +
          '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>' +
          '<span>' + count + ' assistido' + (count !== 1 ? 's' : '') + '</span></div>';
      }

      var conversaBtn = '';
      if (isProfessor) {
        conversaBtn = '<button class="disciplina-chat-btn" title="Conversa com a IA sobre esta disciplina" data-disciplina-id="' + disc.id + '">' +
          '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>' +
          '</button>';
      }

      var materiaisBtn = '<button class="disciplina-materiais-btn" title="Materiais da disciplina" data-disciplina-id="' + disc.id + '" data-disciplina-desc="' + escapeHtml(disc.descricao) + '">' +
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>' +
        '</button>';

      card.innerHTML =
        '<div class="disciplina-header" style="background:' + color + '">' +
        '<div class="disciplina-sigla">' + escapeHtml(sigla) + '</div>' +
        '<div class="disciplina-descricao">' + escapeHtml(disc.descricao) + '</div>' +
        '<div class="disciplina-card-actions">' + materiaisBtn + conversaBtn + '</div>' +
        '</div>' +
        '<div class="disciplina-body">' +
        (disc.codigo_turma && isProfessor
          ? '<div class="disciplina-info"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/></svg><span>' + escapeHtml(disc.codigo_turma) + '</span></div>'
          : '') +
        (disc.professor
          ? '<div class="disciplina-info"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg><span>' + escapeHtml(disc.professor) + '</span></div>'
          : '') +
        (!isProfessor && disc.situacao
          ? '<div class="disciplina-info"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg><span class="situacao-badge ' + situacaoClass + '">' + escapeHtml(disc.situacao) + '</span></div>'
          : '') +
        '<div class="disciplina-info"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg><span>' + escapeHtml(disc.semestre) + '</span></div>' +
        assistidosBadge +
        '</div>';

      if (!isProfessor) {
        card.addEventListener('click', function() {
          abrirConversaDisciplina(disc.id, disc.descricao);
        });
      } else if (disc.qtd_alunos_assistidos > 0) {
        card.addEventListener('click', function() {
          showAlunosAssistidos(disc.id, disc.descricao);
        });
      }

      var chatBtnEl = card.querySelector('.disciplina-chat-btn');
      if (chatBtnEl) {
        chatBtnEl.addEventListener('click', function(e) {
          e.stopPropagation();
          abrirConversaDisciplina(disc.id, disc.descricao);
        });
      }

      var materiaisBtnEl = card.querySelector('.disciplina-materiais-btn');
      if (materiaisBtnEl) {
        materiaisBtnEl.addEventListener('click', function(e) {
          e.stopPropagation();
          openMateriaisModal(disc.id, disc.descricao);
        });
      }

      grid.appendChild(card);
    });
  }

  function abrirConversaDisciplina(disciplinaId, disciplinaDescricao) {
    try {
      sessionStorage.setItem('acolhe_open_conversa', JSON.stringify({
        tipo: 'disciplina',
        disciplina_id: disciplinaId,
        disciplina_descricao: disciplinaDescricao,
        mensagem_inicial: 'Olá, sou ' + (currentUser ? (currentUser.nome || currentUser.nome_usual || 'aluno') : 'aluno') + ' e estou pronto para aprender ' + disciplinaDescricao
      }));
    } catch (e) {}
    window.location.href = '/chat';
  }

  function showAlunosAssistidos(disciplinaId, disciplinaNome) {
    currentView = 'alunos';
    var page = document.querySelector('.disciplinas-page');
    var gridSection = document.getElementById('disciplinas-grid');
    var badgeSection = document.getElementById('semestre-badge');
    if (badgeSection) badgeSection.style.display = 'none';

    if (gridSection) {
      gridSection.innerHTML =
        '<div class="alunos-assistidos-container">' +
        '<div class="alunos-header">' +
        '<button class="btn-back" id="btn-back">' +
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>' +
        '<span>Voltar</span></button>' +
        '<h2 class="alunos-title">' + escapeHtml(disciplinaNome) + '</h2>' +
        '</div>' +
        '<div class="alunos-list" id="alunos-list">' +
        '<div class="spinner"></div>' +
        '</div></div>';
    }

    document.getElementById('btn-back').addEventListener('click', function() {
      currentView = 'grid';
      if (badgeSection) badgeSection.style.display = '';
      loadDisciplinas();
    });

  acolheFetch('/auth/disciplinas/' + disciplinaId + '/alunos-assistidos')
    .then(function(response) {
      if (!response.ok) throw new Error('HTTP ' + response.status);
      return response.json();
    })
    .then(function(alunos) {
      var listEl = document.getElementById('alunos-list');
      if (!listEl) return;

      if (!alunos || alunos.length === 0) {
        listEl.innerHTML =
          '<div class="disciplinas-empty">' +
          '<div class="empty-state-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg></div>' +
          '<h3>Nenhum aluno assistido</h3>' +
          '<p>Nenhum aluno desta turma esta registrado como assistido pela equipe psicopedagogica</p>' +
          '</div>';
        return;
      }

      listEl.innerHTML = '';
      alunos.forEach(function(aluno) {
        var initials = (aluno.aluno_nome || '?').split(' ').map(function(n) { return n[0]; }).slice(0, 2).join('').toUpperCase();
        var item = document.createElement('div');
        item.className = 'aluno-item';
        item.innerHTML =
          '<div class="aluno-avatar">' + initials + '</div>' +
          '<div class="aluno-info">' +
          '<span class="aluno-nome">' + escapeHtml(aluno.aluno_nome) + '</span>' +
          (aluno.aluno_matricula ? '<span class="aluno-matricula">' + escapeHtml(aluno.aluno_matricula) + '</span>' : '') +
          '</div>' +
          '<button class="btn-profile" title="Detalhes" data-aluno-id="' + aluno.id + '" data-aluno-nome="' + escapeHtml(aluno.aluno_nome) + '" data-disciplina-id="' + disciplinaId + '">' +
          '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>' +
          '</button>';
        listEl.appendChild(item);
          var btn = item.querySelector('.btn-profile');
          if (btn) {
            btn.addEventListener('click', function(e) {
              e.stopPropagation();
              var alId = parseInt(this.dataset.alunoId);
              var discId = parseInt(this.dataset.disciplinaId);
              var alNome = this.dataset.alunoNome;
              openStudentModal(alId, discId, alNome);
            });
          }
      });
    })
    .catch(function(error) {
      var listEl = document.getElementById('alunos-list');
      if (listEl) {
        listEl.innerHTML =
          '<div class="disciplinas-empty"><h3>Erro ao carregar</h3><p>' + escapeHtml(error.message) + '</p></div>';
      }
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

// Utility: debounce
function debounce(func, wait) {
  var timeout;
  return function() {
    var args = arguments;
    clearTimeout(timeout);
    timeout = setTimeout(function() {
      func.apply(null, args);
    }, wait);
  };
}

// Render markdown safely using marked & DOMPurify (if available)
function renderMarkdown(text) {
  if (!text) return '';
  if (typeof window.marked !== 'undefined' && typeof window.DOMPurify !== 'undefined') {
    return window.DOMPurify.sanitize(window.marked.parse(text));
  }
  return escapeHtml(text);
}

// Modal focus trap (copied from painel.js)
var _trapHandler = null;
var _trapLastFocus = null;
function _trapFocus(modalEl) {
  _untrapFocus();
  _trapLastFocus = document.activeElement;
  var focusable = modalEl.querySelectorAll('a[href], button:not([disabled]), input:not([disabled]), textarea:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])');
  if (!focusable.length) return;
  var first = focusable[0];
  var last = focusable[focusable.length - 1];
  _trapHandler = function(e) {
    if (e.key === 'Escape') {
      var id = modalEl.id;
      if (id === 'student-modal') closeStudentModal();
      return;
    }
    if (e.key !== 'Tab') return;
    if (e.shiftKey) {
      if (document.activeElement === first) { e.preventDefault(); last.focus(); }
    } else {
      if (document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  };
  document.addEventListener('keydown', _trapHandler);
  setTimeout(function() { first.focus(); }, 50);
}
function _untrapFocus() {
  if (_trapHandler) { document.removeEventListener('keydown', _trapHandler); _trapHandler = null; }
  if (_trapLastFocus) { try { _trapLastFocus.focus(); } catch(e) {} _trapLastFocus = null; }
}

// Switch modal tabs for student modal
function switchStudentTab(tabName) {
  document.querySelectorAll('#student-modal .portal-tab').forEach(function(tab) {
    var name = tab.getAttribute('data-tab');
    tab.classList.toggle('active', name === tabName);
  });
  document.getElementById('modal-perfil').hidden = tabName !== 'perfil';
  document.getElementById('modal-conteudos').hidden = tabName !== 'conteudos';
  document.getElementById('modal-apoio').hidden = tabName !== 'apoio';
  document.getElementById('modal-observacao').hidden = tabName !== 'observacao';
}

// Open student modal and load sections
function openStudentModal(alunoId, disciplinaId, alunoNome) {
  var modal = document.getElementById('student-modal');
  if (!modal) return;
  var titleEl = document.getElementById('modal-student-title');
  if (titleEl) titleEl.textContent = 'Aluno: ' + (alunoNome || '');
  // Store ids for later use
  modal.dataset.alunoId = alunoId;
  modal.dataset.disciplinaId = disciplinaId;
  // Reset tabs to perfil
  switchStudentTab('perfil');
  // Show loading spinners in each section
  document.getElementById('modal-perfil').innerHTML = '<div class="spinner"></div>';
  document.getElementById('modal-conteudos').innerHTML = '<div class="spinner"></div>';
  document.getElementById('modal-apoio').innerHTML = '<div class="spinner"></div>';
  document.getElementById('modal-observacao').innerHTML = '<div class="spinner"></div>';

  modal.hidden = false;
  _trapFocus(modal);

  // Load data asynchronously
  loadStudentProfile(alunoId, alunoNome);
  loadStudentConteudos(alunoId);
  loadStudentObservacao(alunoId, disciplinaId);
}

function closeStudentModal() {
  _untrapFocus();
  var modal = document.getElementById('student-modal');
  if (modal) modal.hidden = true;
}

// Load student profile data
function loadStudentProfile(alunoId, alunoNome) {
  var container = document.getElementById('modal-perfil');
  acolheFetch('/auth/disciplinas/alunos/' + alunoId + '/perfil')
    .then(function(r){ if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
    .then(function(perfil) {
      var html = '<div class="perfil-card">' +
        '<div class="perfil-card-header"><h3 class="perfil-nome">' + escapeHtml(alunoNome) + '</h3></div>' +
        '<div class="perfil-card-body"><div class="perfil-info-grid">';
      html += '<div class="perfil-info-item"><span class="perfil-info-label">Nível de Atenção</span><span class="perfil-info-value">' + (perfil.nivel_atencao ? escapeHtml(perfil.nivel_atencao) : '-') + '</span></div>';
      html += '<div class="perfil-info-item"><span class="perfil-info-label">Dificuldade de Leitura</span><span class="perfil-info-value">' + (perfil.dificuldade_leitura ? 'Sim' : 'Não') + '</span></div>';
      html += '<div class="perfil-info-item"><span class="perfil-info-label">Preferência</span><span class="perfil-info-value">' + (perfil.preferencia ? escapeHtml(perfil.preferencia) : '-') + '</span></div>';
      html += '<div class="perfil-info-item"><span class="perfil-info-label">Interesses</span><span class="perfil-info-value">' + (perfil.interesses ? escapeHtml(perfil.interesses) : '-') + '</span></div>';
      html += '<div class="perfil-info-item"><span class="perfil-info-label">Diagnóstico</span><span class="perfil-info-value">' + (perfil.diagnostico ? escapeHtml(perfil.diagnostico) : '-') + '</span></div>';
      html += '</div></div></div>';
      container.innerHTML = html;
    })
    .catch(function(err){ container.innerHTML = '<p>Erro ao carregar perfil</p>'; showToast('Erro ao carregar perfil', 'error'); });
}

// Load adaptive content for student
function loadStudentConteudos(alunoId) {
  var container = document.getElementById('modal-conteudos');
  acolheFetch('/auth/disciplinas/alunos/' + alunoId + '/conteudos')
    .then(function(r){ if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
    .then(function(conteudos) {
      if (!conteudos || conteudos.length === 0) {
        container.innerHTML = '<p>Nenhum conteúdo encontrado.</p>';
        return;
      }
      container.innerHTML = '';
      conteudos.forEach(function(c){
        var card = document.createElement('div');
        card.className = 'conteudo-card';
        var dateStr = new Date(c.gerado_em).toLocaleString('pt-BR');
        card.innerHTML = '<div class="conteudo-card-header"><div class="conteudo-tema">' + escapeHtml(c.tema) + '</div><div class="conteudo-meta"><span class="conteudo-modelo">' + escapeHtml(c.modelo_ia) + '</span><span class="conteudo-data">' + escapeHtml(dateStr) + '</span></div></div>' +
          '<div class="conteudo-card-body"><div class="conteudo-texto">' + renderMarkdown(c.conteudo) + '</div></div>';
        container.appendChild(card);
      });
    })
    .catch(function(err){ container.innerHTML = '<p>Erro ao carregar conteúdo</p>'; showToast('Erro ao carregar conteúdo', 'error'); });
}

// Load observation (if any) and setup save on change
function loadStudentObservacao(alunoId, disciplinaId) {
  var container = document.getElementById('modal-observacao');
  acolheFetch('/auth/disciplinas/alunos/' + alunoId + '/observacao?disciplina_id=' + disciplinaId)
    .then(function(r){ if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
    .then(function(obs) {
      renderObservationForm(container, obs.texto);
    })
    .catch(function(err){
      // If 404, no observation yet
      if (err.message && err.message.includes('404')) {
        renderObservationForm(container, '');
      } else {
        container.innerHTML = '<p>Erro ao carregar observação</p>';
        showToast('Erro ao carregar observação', 'error');
      }
    });
  function renderObservationForm(parent, text) {
    var html = '<div class="form-group"><label for="observacao-textarea">Observação</label><textarea id="observacao-textarea" rows="4" class="campo-textarea" placeholder="Escreva sua observação...">' + escapeHtml(text) + '</textarea></div>';
    parent.innerHTML = html;
    var textarea = document.getElementById('observacao-textarea');
    if (textarea) {
      textarea.addEventListener('input', debounce(function(){
        saveObservation(alunoId, disciplinaId, textarea.value);
      }, 800));
    }
  }
}

function saveObservation(alunoId, disciplinaId, texto) {
  var payload = { disciplina_id: disciplinaId, texto: texto };
  acolheFetch('/auth/disciplinas/alunos/' + alunoId + '/observacao', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  .then(function(r){ if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
  .then(function(){ showToast('Observação salva com sucesso', 'success'); })
  .catch(function(){ showToast('Erro ao salvar observação', 'error'); });
}

// Load support request UI and handle submit
function loadStudentApoio(alunoId) {
  var container = document.getElementById('modal-apoio');
  var html = '<div class="form-group"><label for="apoio-motivo">Motivo</label><textarea id="apoio-motivo" rows="4" class="campo-textarea" placeholder="Descreva o motivo da solicitação..."></textarea></div>' +
    '<button class="btn-modal-save" id="apoio-submit">Solicitar Apoio</button>';
  container.innerHTML = html;
  var btn = document.getElementById('apoio-submit');
  if (btn) {
    btn.addEventListener('click', function(){
      var motivo = document.getElementById('apoio-motivo').value.trim();
      if (!motivo) { showToast('Informe o motivo', 'warning'); return; }
      btn.disabled = true; btn.textContent = 'Enviando...';
      acolheFetch('/auth/disciplinas/alunos/' + alunoId + '/solicitar-apoio', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ motivo: motivo })
      })
      .then(function(r){ if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(function(){ showToast('Solicitação de apoio enviada', 'success'); closeStudentModal(); })
      .catch(function(){ showToast('Erro ao solicitar apoio', 'error'); })
      .finally(function(){ btn.disabled = false; btn.textContent = 'Solicitar Apoio'; });
    });
  }
}

// Hook up tab clicks when modal is shown
function initStudentModal() {
  var tabs = document.querySelectorAll('#student-modal .portal-tab');
  tabs.forEach(function(tab){
    tab.addEventListener('click', function(){
      var name = this.getAttribute('data-tab');
      switchStudentTab(name);
      // Load respective section if needed
      if (name === 'apoio') { var alId = parseInt(document.getElementById('student-modal').dataset.alunoId); loadStudentApoio(alId); }
    });
  });
  var closeBtn = document.getElementById('student-modal-close');
  if (closeBtn) closeBtn.addEventListener('click', closeStudentModal);
  var overlay = document.getElementById('student-modal');
  if (overlay) overlay.addEventListener('click', function(e){ if (e.target === overlay) closeStudentModal(); });
}


function setupEventListeners() {
var btnSync = document.getElementById('btn-sync');
if (btnSync) btnSync.addEventListener('click', handleSync);

var btnLogout = document.getElementById('btn-logout');
if (btnLogout) btnLogout.addEventListener('click', handleLogout);

// Initialize student modal event handlers
initStudentModal();

// Initialize materials modal event handlers
initMateriaisModal();
}

// =========================================================================
// MATERIALS MODAL FUNCTIONS
// =========================================================================

var _materiaisDisciplinaId = null;
var _materiaisDisciplinaDesc = '';

function initMateriaisModal() {
  var closeBtn = document.getElementById('materiais-modal-close');
  if (closeBtn) closeBtn.addEventListener('click', closeMateriaisModal);
  var overlay = document.getElementById('materiais-modal');
  if (overlay) overlay.addEventListener('click', function(e){ if (e.target === overlay) closeMateriaisModal(); });

  var filtrosChips = document.querySelectorAll('.filtro-chip');
  filtrosChips.forEach(function(chip) {
    chip.addEventListener('click', function() {
      filtrosChips.forEach(function(c) { c.classList.remove('active'); });
      chip.classList.add('active');
      _materiaisCategoriaFiltro = chip.dataset.categoria || '';
      if (_materiaisDisciplinaId) {
        loadMateriais(_materiaisDisciplinaId, _materiaisCategoriaFiltro);
      }
    });
  });

  var uploadArea = document.getElementById('upload-area');
  var fileInput = document.getElementById('file-input');
  var btnSelectFile = document.getElementById('btn-select-file');

  if (btnSelectFile && fileInput) {
    btnSelectFile.addEventListener('click', function(e) {
      e.stopPropagation();
      fileInput.click();
    });
  }

  if (uploadArea && fileInput) {
    uploadArea.addEventListener('click', function() {
      fileInput.click();
    });

    uploadArea.addEventListener('dragover', function(e) {
      e.preventDefault();
      uploadArea.classList.add('drag-over');
    });

    uploadArea.addEventListener('dragleave', function(e) {
      e.preventDefault();
      uploadArea.classList.remove('drag-over');
    });

    uploadArea.addEventListener('drop', function(e) {
      e.preventDefault();
      uploadArea.classList.remove('drag-over');
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        handleFileUpload(e.dataTransfer.files[0]);
      }
    });
  }

  if (fileInput) {
    fileInput.addEventListener('change', function() {
      if (fileInput.files && fileInput.files.length > 0) {
        handleFileUpload(fileInput.files[0]);
        fileInput.value = '';
      }
    });
  }
}

var _materiaisCategoriaFiltro = '';

function openMateriaisModal(disciplinaId, disciplinaDesc) {
  _materiaisDisciplinaId = disciplinaId;
  _materiaisDisciplinaDesc = disciplinaDesc;
  _materiaisCategoriaFiltro = '';

  var modal = document.getElementById('materiais-modal');
  if (!modal) return;

  var titleEl = document.getElementById('modal-materiais-title');
  if (titleEl) titleEl.textContent = 'Materiais - ' + disciplinaDesc;

  var isProfessor = tipoPerfil === 'professor';
  var uploadSection = document.getElementById('materiais-upload-section');
  if (uploadSection) uploadSection.hidden = !isProfessor;

  var progressEl = document.getElementById('upload-progress');
  if (progressEl) progressEl.hidden = true;

  var categoriaSelect = document.getElementById('upload-categoria');
  if (categoriaSelect) categoriaSelect.value = 'outro';

  var filtrosChips = document.querySelectorAll('.filtro-chip');
  filtrosChips.forEach(function(chip) {
    chip.classList.remove('active');
    if (chip.dataset.categoria === '') chip.classList.add('active');
  });

  modal.hidden = false;
  _trapFocus(modal);

  loadMateriais(disciplinaId);
}

function closeMateriaisModal() {
  _untrapFocus();
  var modal = document.getElementById('materiais-modal');
  if (modal) modal.hidden = true;
  _materiaisDisciplinaId = null;
}

function loadMateriais(disciplinaId, categoria) {
  var listEl = document.getElementById('materiais-list');
  if (!listEl) return;
  listEl.innerHTML = '<div class="spinner"></div>';

  var url = '/api/materiais/disciplina/' + disciplinaId;
  if (categoria) url += '?categoria=' + encodeURIComponent(categoria);

  acolheFetch(url)
    .then(function(r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    })
    .then(function(materiais) {
      renderMateriaisList(materiais);
    })
    .catch(function(err) {
      listEl.innerHTML = '<div class="materiais-empty"><p>Erro ao carregar materiais</p></div>';
      showToast('Erro ao carregar materiais', 'error');
    });
}

function renderMateriaisList(materiais) {
  var listEl = document.getElementById('materiais-list');
  if (!listEl) return;

  if (!materiais || materiais.length === 0) {
    listEl.innerHTML = '<div class="materiais-empty">' +
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
      '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>' +
      '<polyline points="14 2 14 8 20 8"/>' +
      '</svg>' +
      '<p>Nenhum material enviado ainda</p>' +
      '</div>';
    return;
  }

  listEl.innerHTML = '';
  materiais.forEach(function(mat) {
    var ext = (mat.nome_original || '').split('.').pop().toLowerCase();
    var iconClass = ext || 'default';
    var sizeStr = formatFileSize(mat.tamanho);
    var dateStr = new Date(mat.criado_em).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
    var canDelete = (currentUser && currentUser.id === mat.usuario_id) || tipoPerfil === 'admin';

    var categoriaLabel = mat.categoria ? mat.categoria.charAt(0).toUpperCase() + mat.categoria.slice(1) : 'Outro';
    var categoriaBadge = '<span class="material-categoria-badge">' + escapeHtml(categoriaLabel) + '</span>';

    var item = document.createElement('div');
    item.className = 'material-item';
    item.innerHTML =
      '<div class="material-icon ' + iconClass + '">' + escapeHtml(ext.toUpperCase()) + '</div>' +
      '<div class="material-info">' +
      '<div class="material-name">' + escapeHtml(mat.nome_original) + categoriaBadge + '</div>' +
      '<div class="material-meta">' + sizeStr + ' &middot; ' + dateStr + (mat.usuario_nome ? ' &middot; ' + escapeHtml(mat.usuario_nome) : '') + '</div>' +
      '</div>' +
      '<div class="material-actions">' +
      '<button class="material-action-btn download" title="Baixar" data-material-id="' + mat.id + '">' +
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>' +
      '</button>' +
      (canDelete ? '<button class="material-action-btn delete" title="Excluir" data-material-id="' + mat.id + '">' +
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>' +
      '</button>' : '') +
      '</div>';

    var dlBtn = item.querySelector('.download');
    if (dlBtn) {
      dlBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        downloadMaterial(mat.id, mat.nome_original);
      });
    }

    var delBtn = item.querySelector('.delete');
    if (delBtn) {
      delBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        deleteMaterial(mat.id, mat.nome_original);
      });
    }

    listEl.appendChild(item);
  });
}

function handleFileUpload(file) {
  if (!_materiaisDisciplinaId) return;

  var maxSize = 10 * 1024 * 1024;
  if (file.size > maxSize) {
    showToast('Arquivo muito grande. Tamanho maximo: 10MB', 'error');
    return;
  }

  var allowedExts = ['pdf', 'doc', 'docx', 'ppt', 'pptx', 'png', 'jpg', 'jpeg', 'txt'];
  var ext = (file.name || '').split('.').pop().toLowerCase();
  if (allowedExts.indexOf(ext) === -1) {
    showToast('Tipo de arquivo nao permitido', 'error');
    return;
  }

  var progressEl = document.getElementById('upload-progress');
  var progressFill = document.getElementById('progress-fill');
  var progressText = document.getElementById('progress-text');
  var uploadArea = document.getElementById('upload-area');

  if (progressEl) progressEl.hidden = false;
  if (uploadArea) uploadArea.style.display = 'none';
  if (progressFill) progressFill.style.width = '30%';
  if (progressText) progressText.textContent = 'Enviando ' + file.name + '...';

  var formData = new FormData();
  formData.append('file', file);

  var categoriaSelect = document.getElementById('upload-categoria');
  var categoria = categoriaSelect ? categoriaSelect.value : 'outro';
  formData.append('categoria', categoria);

  var token = acolheGetToken();
  var xhr = new XMLHttpRequest();
  xhr.open('POST', '/api/materiais/disciplina/' + _materiaisDisciplinaId + '/upload');
  xhr.setRequestHeader('Authorization', 'Bearer ' + token);

  xhr.upload.onprogress = function(e) {
    if (e.lengthComputable) {
      var pct = Math.round((e.loaded / e.total) * 100);
      if (progressFill) progressFill.style.width = pct + '%';
      if (progressText) progressText.textContent = 'Enviando ' + file.name + '... ' + pct + '%';
    }
  };

  xhr.onload = function() {
    if (progressEl) progressEl.hidden = true;
    if (uploadArea) uploadArea.style.display = '';

    if (xhr.status >= 200 && xhr.status < 300) {
      showToast('Material enviado com sucesso', 'success');
      var categoriaSelect = document.getElementById('upload-categoria');
      if (categoriaSelect) categoriaSelect.value = 'outro';
      loadMateriais(_materiaisDisciplinaId, _materiaisCategoriaFiltro);
    } else {
      var detail = 'Erro ao enviar arquivo';
      try {
        var resp = JSON.parse(xhr.responseText);
        detail = resp.detail || detail;
      } catch(e) {}
      showToast(detail, 'error');
    }
  };

  xhr.onerror = function() {
    if (progressEl) progressEl.hidden = true;
    if (uploadArea) uploadArea.style.display = '';
    showToast('Erro de conexao ao enviar arquivo', 'error');
  };

  xhr.send(formData);
}

function downloadMaterial(materialId, nomeOriginal) {
  var token = acolheGetToken();
  var link = document.createElement('a');
  link.href = '/api/materiais/' + materialId + '/download';
  link.download = nomeOriginal;

  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/api/materiais/' + materialId + '/download');
  xhr.setRequestHeader('Authorization', 'Bearer ' + token);
  xhr.responseType = 'blob';

  xhr.onload = function() {
    if (xhr.status === 200) {
      var blob = xhr.response;
      var url = URL.createObjectURL(blob);
      var a = document.createElement('a');
      a.href = url;
      a.download = nomeOriginal;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } else {
      showToast('Erro ao baixar arquivo', 'error');
    }
  };

  xhr.onerror = function() {
    showToast('Erro de conexao ao baixar arquivo', 'error');
  };

  xhr.send();
}

function deleteMaterial(materialId, nomeOriginal) {
  if (!confirm('Tem certeza que deseja excluir "' + nomeOriginal + '"?')) return;

  acolheFetch('/api/materiais/' + materialId, {
    method: 'DELETE'
  })
    .then(function(r) {
      if (r.status === 204) {
        showToast('Material excluido com sucesso', 'success');
        if (_materiaisDisciplinaId) loadMateriais(_materiaisDisciplinaId);
      } else {
        return r.json().then(function(err) {
          throw new Error(err.detail || 'Erro ao excluir');
        });
      }
    })
    .catch(function(err) {
      showToast(err.message || 'Erro ao excluir material', 'error');
    });
}

function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  var units = ['B', 'KB', 'MB', 'GB'];
  var i = Math.floor(Math.log(bytes) / Math.log(1024));
  return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + units[i];
}

function applyNavVisibility() {
var isAluno = tipoPerfil === 'aluno';
var navPortal = document.getElementById('nav-portal');
if (navPortal) navPortal.style.display = isAluno ? '' : 'none';
}

  function handleLogout() {
  if (confirm('Deseja realmente sair?')) {
    acolheLogout();
  }
}

  document.addEventListener('DOMContentLoaded', init);
})();
