(function() {
'use strict';

if (!acolheRequireRole(['psicopedagogo', 'servidor', 'admin'])) return;

  var currentUser = null;
  var searchTimeout = null;
  var currentQuery = '';
  var isSearching = false;
  var isMatriculaMode = false;

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
    var searchInput = document.getElementById('search-input');
    var btnClear = document.getElementById('btn-clear-search');
    var filterCampus = document.getElementById('filter-meu-campus');
	var btnLogout = document.getElementById('btn-logout');
    var manualForm = document.getElementById('manual-form');

    if (searchInput) {
      searchInput.addEventListener('input', function() {
        var val = searchInput.value.trim();
        if (btnClear) btnClear.hidden = val.length === 0;
        clearTimeout(searchTimeout);
        if (val.length < 2) {
          hideResults();
          showInitialState();
          return;
        }
        searchTimeout = setTimeout(function() {
          performSearch(val);
        }, 400);
      });

      searchInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
          clearTimeout(searchTimeout);
          var val = searchInput.value.trim();
          if (val.length >= 2) performSearch(val);
        }
      });

      searchInput.focus();
    }

    if (btnClear) {
      btnClear.addEventListener('click', function() {
        searchInput.value = '';
        btnClear.hidden = true;
        hideResults();
        showInitialState();
        searchInput.focus();
      });
    }

    if (filterCampus) {
      filterCampus.addEventListener('change', function() {
        if (currentQuery.length >= 2) performSearch(currentQuery);
      });
    }

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

  function performSearch(query) {
    currentQuery = query;
    if (isSearching) return;

    isMatriculaMode = /^\d{4,}$/.test(query);

    var apenasMeuCampus = document.getElementById('filter-meu-campus');
    var campusParam = apenasMeuCampus && apenasMeuCampus.checked;

	showLoading();
	hideSuapAlert();
    hideResults();
    hideInitialState();
    hideEmptyState();
    isSearching = true;

    var params = 'q=' + encodeURIComponent(query) + '&apenas_meu_campus=' + campusParam;
    if (isMatriculaMode) {
      params += '&matricula=' + encodeURIComponent(query);
    }

  acolheFetch('/importacao/buscar?' + params)
  .then(function(r) {
    if (r.status === 403) {
      throw new Error('Acesso negado. Apenas membros do NAPNE podem importar alunos.');
    }
    if (r.status === 502) {
      return r.json().then(function(data) {
        throw new Error(data.detail || 'Erro HTTP 502');
      });
    }
    if (!r.ok) {
      return r.json().then(function(data) {
        throw new Error(data.detail || 'Erro HTTP ' + r.status);
      }).catch(function(e) {
        if (e.message === 'Sessao expirada') throw e;
        throw new Error(e.message || 'Erro HTTP ' + r.status);
      });
    }
    return r.json();
  })
      .then(function(results) {
        isSearching = false;
        hideLoading();
        if (!results || results.length === 0) {
          showEmptyState();
          return;
        }
        showCount(results.length);
        renderResults(results);
      })
  .catch(function(err) {
    isSearching = false;
    hideLoading();

    var msg = err.message || '';
    if (msg === 'Sessao expirada. Faca login novamente.') return;
    if (msg.indexOf('[SUAP_MODULE_ERROR]') !== -1) {
          showSuapAlert();
          showEmptyState();
        } else if (msg.indexOf('Acesso negado') !== -1 || msg.indexOf('indispon') !== -1) {
          showToast(msg, 'error');
          showEmptyState();
        }
      });
  }

  function renderResults(results) {
    var listEl = document.getElementById('results-list');
    if (!listEl) return;

    listEl.innerHTML = '';

    results.forEach(function(aluno) {
      var card = document.createElement('div');
      card.className = 'result-card' + (aluno.ja_importado ? ' result-imported' : '');

      var fotoHtml = '';
      if (aluno.foto_url) {
        fotoHtml = '<img src="' + escapeAttr(aluno.foto_url) + '" alt="Foto" class="result-foto" onerror="this.style.display=\'none\'">';
      }
      if (!aluno.foto_url || !fotoHtml) {
        var initials = (aluno.nome || '?').split(' ').map(function(n){ return n[0]; }).slice(0,2).join('').toUpperCase();
        fotoHtml = '<div class="result-foto-placeholder">' + escapeHtml(initials) + '</div>';
      }

      var badgeHtml = '';
      if (aluno.ja_importado) {
        var badgeClass = 'badge-acompanhamento';
        var badgeText = 'Em acompanhamento';
        if (aluno.status_acompanhamento === 'aguardando_indicacao') {
          badgeClass = 'badge-aguardando';
          badgeText = 'Aguardando indicacao';
        } else if (aluno.status_acompanhamento === 'pendente') {
          badgeClass = 'badge-pendente';
          badgeText = 'Pendente validacao';
        }
        badgeHtml = '<span class="status-badge ' + badgeClass + '">' + escapeHtml(badgeText) + '</span>';
      }

      var btnHtml = '';
      if (aluno.ja_importado) {
        btnHtml = '<button class="btn-import btn-import-disabled" disabled>Ja importado</button>';
      } else {
        btnHtml = '<button class="btn-import btn-import-active" data-matricula="' + escapeAttr(aluno.matricula) + '">Importar</button>';
      }

      card.innerHTML =
        '<div class="result-foto-col">' + fotoHtml + '</div>' +
        '<div class="result-info-col">' +
        '<div class="result-nome-row">' +
        '<span class="result-nome">' + escapeHtml(aluno.nome) + '</span>' +
        badgeHtml +
        '</div>' +
        '<div class="result-detail">' +
        '<span class="detail-label">Matricula:</span> ' +
        '<span class="detail-value">' + escapeHtml(aluno.matricula) + '</span>' +
        '</div>' +
        (aluno.curso ? '<div class="result-detail"><span class="detail-label">Curso:</span> <span class="detail-value">' + escapeHtml(aluno.curso) + '</span></div>' : '') +
        (aluno.campus ? '<div class="result-detail"><span class="detail-label">Campus:</span> <span class="detail-value">' + escapeHtml(aluno.campus) + '</span></div>' : '') +
        '</div>' +
        '<div class="result-action-col">' + btnHtml + '</div>';

      listEl.appendChild(card);
    });

    listEl.querySelectorAll('.btn-import-active').forEach(function(btn) {
      btn.addEventListener('click', function() {
        var matricula = btn.getAttribute('data-matricula');
        importarAluno(matricula, btn);
      });
    });

    document.getElementById('results-section').hidden = false;
  }

  function importarAluno(matricula, btnEl) {
    if (btnEl.disabled) return;

    btnEl.disabled = true;
    btnEl.textContent = 'Importando...';
    btnEl.className = 'btn-import btn-import-loading';

  acolheFetch('/importacao/importar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ matricula: matricula })
  })
  .then(function(r) {
    if (r.status === 403) {
      throw new Error('Acesso negado. Apenas membros do NAPNE podem importar alunos.');
    }
    if (r.status === 409) {
      return r.json().then(function(data) {
        throw new Error(data.detail || 'Aluno ja importado');
      });
    }
    if (!r.ok) {
      return r.json().then(function(data) {
        throw new Error(data.detail || 'Erro ao importar aluno');
      }).catch(function(e) {
        if (e.message === 'Sessao expirada') throw e;
        throw new Error(e.message || 'Erro ao importar aluno');
      });
    }
    return r.json();
  })
      .then(function(aluno) {
        btnEl.textContent = 'Importado';
        btnEl.className = 'btn-import btn-import-done';
        btnEl.disabled = true;

        var card = btnEl.closest('.result-card');
        if (card) {
          card.classList.add('result-imported');
          var nomeRow = card.querySelector('.result-nome-row');
          if (nomeRow && !nomeRow.querySelector('.status-badge')) {
            var badge = document.createElement('span');
            badge.className = 'status-badge badge-aguardando';
            badge.textContent = 'Aguardando indicacao';
            nomeRow.appendChild(badge);
          }
        }

        showToast('Aluno ' + escapeHtml(aluno.nome || matricula) + ' importado com sucesso!', 'success');
      })
  .catch(function(err) {
    if (err.message === 'Sessao expirada. Faca login novamente.') return;
    btnEl.disabled = false;
        btnEl.textContent = 'Importar';
        btnEl.className = 'btn-import btn-import-active';
        showToast('Erro: ' + err.message, 'error');
      });
  }

function showLoading() {
	var el = document.getElementById('status-loading');
	var section = document.getElementById('search-status');
	if (el) el.style.display = 'flex';
	if (section) section.style.display = 'flex';
}

function hideLoading() {
	var el = document.getElementById('status-loading');
	if (el) el.style.display = 'none';
	updateStatusSection();
}

function hideSuapAlert() {
    var el = document.getElementById('suap-alert');
    if (el) el.hidden = true;
  }

  function showSuapAlert() {
    var el = document.getElementById('suap-alert');
    if (el) el.hidden = false;
  }

function showCount(count) {
    hideSuapAlert();
    var el = document.getElementById('status-count');
    var text = document.getElementById('count-text');
    if (el) el.hidden = false;
    if (text) {
      var suffix = count !== 1 ? 's encontrados' : ' encontrado';
      if (isMatriculaMode) {
        text.textContent = count + ' resultado' + suffix;
      } else {
        text.textContent = count + ' aluno' + suffix + ' na base local';
      }
    }
    updateStatusSection();
  }

function updateStatusSection() {
	var section = document.getElementById('search-status');
	if (section) {
		var loadingEl = document.getElementById('status-loading');
		var countEl = document.getElementById('status-count');
		var anyVisible = (loadingEl && loadingEl.style.display !== 'none') ||
			(countEl && countEl.style.display !== 'none' && !countEl.hidden);
		section.style.display = anyVisible ? 'flex' : 'none';
	}
}

function hideResults() {
	var el = document.getElementById('results-section');
	if (el) el.hidden = true;
	var countEl = document.getElementById('status-count');
	if (countEl) countEl.hidden = true;
	var section = document.getElementById('search-status');
	if (section) section.style.display = 'none';
}

  function showInitialState() {
    var el = document.getElementById('initial-state');
    if (el) el.hidden = false;
  }

  function hideInitialState() {
    var el = document.getElementById('initial-state');
    if (el) el.hidden = true;
  }

function showEmptyState() {
    var el = document.getElementById('empty-state');
    if (el) el.hidden = false;
    var titleEl = document.getElementById('empty-title');
    var textEl = document.getElementById('empty-text');
    var suapAlertEl = document.getElementById('suap-alert');
    var suapVisible = suapAlertEl && !suapAlertEl.hidden;
    if (isMatriculaMode || suapVisible) {
        if (titleEl) titleEl.textContent = 'Aluno nao encontrado';
        if (textEl) textEl.textContent = 'Nenhum aluno encontrado com esta matricula. Verifique o numero ou busque pelo nome na base local.';
    } else {
        if (titleEl) titleEl.textContent = 'Nenhum aluno encontrado';
        if (textEl) textEl.textContent = 'Nenhum aluno encontrado na base local com este nome.';
    }
}

  function hideEmptyState() {
    var el = document.getElementById('empty-state');
    if (el) el.hidden = true;
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

  function escapeAttr(text) {
    if (!text) return '';
    return text.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
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