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
    var searchTimeout = null;

    function init() {
        loadUserInfo();
        loadPendencias();
        loadAlunosAtivos();
        setupEventListeners();
    }

    function loadUserInfo() {
        var savedUser = localStorage.getItem('acolhe_user');
        if (savedUser) {
            try { currentUser = JSON.parse(savedUser); } catch(e) {}
        }
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

    function loadPendencias() {
        var listEl = document.getElementById('pendencias-list');
        var countEl = document.getElementById('pendencias-count');
        if (!listEl) return;

        fetch('/equipe/pendencias', {
            headers: { 'Authorization': 'Bearer ' + accessToken }
        })
      .then(function(r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(function(pendencias) {
            if (countEl) countEl.textContent = pendencias.length;
            if (!pendencias || pendencias.length === 0) {
                listEl.innerHTML = '<div class="empty-col"><p>Nenhuma pendencia no momento</p></div>';
                return;
            }
            listEl.innerHTML = '';
            pendencias.forEach(function(p) {
                var initials = (p.aluno_nome || '?').split(' ').map(function(n){ return n[0]; }).slice(0,2).join('').toUpperCase();
                var item = document.createElement('div');
                item.className = 'pendencia-item';
                item.innerHTML =
                    '<div class="pendencia-avatar">' + escapeHtml(initials) + '</div>' +
                    '<div class="pendencia-info">' +
                        '<div class="pendencia-nome">' + escapeHtml(p.aluno_nome || 'Aluno') + '</div>' +
                        (p.aluno_matricula ? '<div class="pendencia-matricula">' + escapeHtml(p.aluno_matricula) + '</div>' : '') +
                        (p.motivo ? '<div class="pendencia-motivo">' + escapeHtml(p.motivo) + '</div>' : '') +
                        (p.indicado_por_nome ? '<div class="pendencia-indicado">Indicado por: ' + escapeHtml(p.indicado_por_nome) + '</div>' : '') +
                    '</div>' +
                    '<div class="pendencia-actions">' +
                        '<button class="btn-validate btn-approve" data-id="' + p.id + '">Validar</button>' +
                        '<button class="btn-validate btn-reject" data-id="' + p.id + '">Rejeitar</button>' +
                    '</div>';
                listEl.appendChild(item);
            });

            listEl.querySelectorAll('.btn-approve').forEach(function(btn) {
                btn.addEventListener('click', function() { validarPendencia(parseInt(btn.dataset.id), 'validado'); });
            });
            listEl.querySelectorAll('.btn-reject').forEach(function(btn) {
                btn.addEventListener('click', function() { validarPendencia(parseInt(btn.dataset.id), 'rejeitado'); });
            });
        })
        .catch(function(err) {
            listEl.innerHTML = '<div class="empty-col"><p>Erro ao carregar pendencias</p></div>';
        });
    }

    function validarPendencia(pendenciaId, acao) {
        fetch('/equipe/pendencias/' + pendenciaId, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + accessToken
            },
            body: JSON.stringify({ acao: acao })
        })
        .then(function(r) {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        })
        .then(function() {
            showToast(acao === 'validado' ? 'Aluno validado com sucesso' : 'Pendencia rejeitada', acao === 'validado' ? 'success' : 'warning');
            loadPendencias();
            loadAlunosAtivos();
        })
        .catch(function(err) {
            showToast('Erro: ' + err.message, 'error');
        });
    }

    function loadAlunosAtivos() {
        var listEl = document.getElementById('ativos-list');
        var countEl = document.getElementById('ativos-count');
        if (!listEl) return;

    fetch('/equipe/alunos-ativos', {
      headers: { 'Authorization': 'Bearer ' + accessToken }
    })
      .then(function(r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(function(alunos) {
        if (countEl) countEl.textContent = alunos.length;
            if (!alunos || alunos.length === 0) {
                listEl.innerHTML = '<div class="empty-col"><p>Nenhum aluno ativo registrado</p></div>';
                return;
            }
            listEl.innerHTML = '';
            alunos.forEach(function(a) {
                var initials = a.nome.split(' ').map(function(n){ return n[0]; }).slice(0,2).join('').toUpperCase();
                var item = document.createElement('div');
                item.className = 'aluno-ativo-item';
                item.innerHTML =
                    '<div class="ativo-avatar">' + escapeHtml(initials) + '</div>' +
                    '<div class="ativo-info">' +
                        '<div class="ativo-nome">' + escapeHtml(a.nome) + '</div>' +
                        (a.matricula ? '<div class="ativo-matricula">' + escapeHtml(a.matricula) + '</div>' : '') +
                        (a.diagnostico ? '<div class="ativo-diagnostico">' + escapeHtml(a.diagnostico) + '</div>' : '') +
                    '</div>';
                listEl.appendChild(item);
            });
        })
        .catch(function(err) {
            listEl.innerHTML = '<div class="empty-col"><p>Erro ao carregar alunos</p></div>';
        });
    }

    function handleSearch(query) {
        var resultsEl = document.getElementById('search-results');
        if (!resultsEl) return;

        if (!query || query.length < 2) {
            resultsEl.hidden = true;
            return;
        }

    fetch('/equipe/alunos-busca?q=' + encodeURIComponent(query), {
      headers: { 'Authorization': 'Bearer ' + accessToken }
    })
      .then(function(r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(function(alunos) {
            if (!alunos || alunos.length === 0) {
                resultsEl.innerHTML = '<div class="search-empty">Nenhum aluno encontrado</div>';
                resultsEl.hidden = false;
                return;
            }
            resultsEl.innerHTML = '';
            alunos.forEach(function(a) {
                var initials = a.nome.split(' ').map(function(n){ return n[0]; }).slice(0,2).join('').toUpperCase();
                var item = document.createElement('div');
                item.className = 'search-result-item';
                item.innerHTML =
                    '<div class="result-avatar">' + escapeHtml(initials) + '</div>' +
                    '<div class="result-info">' +
                        '<div class="result-nome">' + escapeHtml(a.nome) + '</div>' +
                        (a.matricula ? '<div class="result-matricula">' + escapeHtml(a.matricula) + '</div>' : '') +
                        (a.diagnostico ? '<div class="result-diagnostico">' + escapeHtml(a.diagnostico) + '</div>' : '') +
                    '</div>';
                resultsEl.appendChild(item);
            });
            resultsEl.hidden = false;
        })
        .catch(function() {
            resultsEl.innerHTML = '<div class="search-empty">Erro ao buscar</div>';
            resultsEl.hidden = false;
        });
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

    function setupEventListeners() {
        var searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.addEventListener('input', function() {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(function() {
                    handleSearch(searchInput.value.trim());
                }, 300);
            });
            searchInput.addEventListener('blur', function() {
                setTimeout(function() {
                    var resultsEl = document.getElementById('search-results');
                    if (resultsEl) resultsEl.hidden = true;
                }, 200);
            });
            searchInput.addEventListener('focus', function() {
                if (searchInput.value.trim().length >= 2) {
                    handleSearch(searchInput.value.trim());
                }
            });
        }

        var btnLogout = document.getElementById('btn-logout');
        if (btnLogout) {
            btnLogout.addEventListener('click', function() {
                if (confirm('Deseja realmente sair?')) {
                    if (suap.isAuthenticated()) suap.getToken().revoke();
                    localStorage.removeItem('acolhe_access_token');
                    localStorage.removeItem('acolhe_user');
                    localStorage.removeItem('acolhe_user_id');
                    localStorage.removeItem('acolhe_tipo_perfil');
                    window.location.replace('/');
                }
            });
        }
    }

    document.addEventListener('DOMContentLoaded', init);
})();
