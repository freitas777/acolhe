(function() {
'use strict';

 if (!acolheRequireRole(['aluno'])) return;

 var currentUser = null;
    var perfilData = null;
    var currentTab = 'perfil';
    var conteudosLoaded = false;

    var PREFERENCIA_LABELS = {
        'visual': 'Visual',
        'auditivo': 'Auditivo',
        'cinestesico': 'Cinestesico',
        'leitura_escrita': 'Leitura/Escrita',
        'misto': 'Misto'
    };

    var STATUS_LABELS = {
        'aguardando_indicacao': 'Aguardando Indicacao',
        'pendente': 'Pendencia de Validacao',
        'ativo': 'Ativo',
        'rejeitado': 'Rejeitado'
    };

    var STATUS_CLASSES = {
        'aguardando_indicacao': 'status-aguardando',
        'pendente': 'status-pendente',
        'ativo': 'status-ativo',
        'rejeitado': 'status-rejeitado'
    };

    function init() {
        loadUserInfo();
        setupTabs();
        setupEventListeners();
        loadMeuPerfil();
    }

    function loadUserInfo() {
        var savedUser = localStorage.getItem('acolhe_user');
        if (savedUser) {
            try {
                currentUser = JSON.parse(savedUser);
            } catch (e) {}
        }
        updateUserInfoUI();
    }

    function updateUserInfoUI() {
        if (!currentUser) return;
        var name = currentUser.nome || currentUser.nome_usual || 'Usuario';
        var avatarEl = document.getElementById('user-avatar');
        var nameEl = document.getElementById('user-name');
        var perfilAvatarEl = document.getElementById('perfil-avatar');

        if (avatarEl) {
            avatarEl.textContent = name.split(' ').map(function(n) { return n[0]; }).slice(0, 2).join('').toUpperCase();
        }
        if (nameEl) nameEl.textContent = name;
        if (perfilAvatarEl) {
            perfilAvatarEl.textContent = name.split(' ').map(function(n) { return n[0]; }).slice(0, 2).join('').toUpperCase();
        }
    }

    function setupTabs() {
        var tabs = document.querySelectorAll('.portal-tab');
        tabs.forEach(function(tab) {
            tab.addEventListener('click', function() {
                var tabName = this.getAttribute('data-tab');
                switchTab(tabName);
            });
        });
    }

    function switchTab(tabName) {
        currentTab = tabName;

        document.querySelectorAll('.portal-tab').forEach(function(tab) {
            tab.classList.toggle('active', tab.getAttribute('data-tab') === tabName);
        });

        document.getElementById('section-perfil').hidden = tabName !== 'perfil';
        document.getElementById('section-conteudos').hidden = tabName !== 'conteudos';

        if (tabName === 'conteudos' && !conteudosLoaded) {
            loadMeusConteudos();
            conteudosLoaded = true;
        }
    }

    function setupEventListeners() {
        var btnSave = document.getElementById('btn-save-perfil');
        var selectPreferencia = document.getElementById('campo-preferencia');
        var textareaInteresses = document.getElementById('campo-interesses');

        if (btnSave) {
            btnSave.addEventListener('click', handleSavePerfil);
        }

        if (selectPreferencia) {
            selectPreferencia.addEventListener('change', checkPerfilChanged);
        }
        if (textareaInteresses) {
            textareaInteresses.addEventListener('input', checkPerfilChanged);
        }

  var btnLogout = document.getElementById('btn-logout');
  if (btnLogout) {
    btnLogout.addEventListener('click', function() {
      if (confirm('Deseja realmente sair?')) {
        acolheLogout();
      }
    });
  }
    }

    function checkPerfilChanged() {
        var btnSave = document.getElementById('btn-save-perfil');
        if (!btnSave || !perfilData) return;

        var currentPreferencia = document.getElementById('campo-preferencia').value;
        var currentInteresses = document.getElementById('campo-interesses').value;

        var originalPreferencia = perfilData.preferencia || '';
        var originalInteresses = perfilData.interesses || '';

        var changed = currentPreferencia !== originalPreferencia || currentInteresses !== originalInteresses;
        btnSave.disabled = !changed;
    }

    function loadMeuPerfil() {
        var loadingEl = document.getElementById('perfil-loading');
        var notFoundEl = document.getElementById('perfil-not-found');
        var contentEl = document.getElementById('perfil-content');

        loadingEl.hidden = false;
        notFoundEl.hidden = true;
        contentEl.hidden = true;

  acolheFetch('/portal/meu-perfil')
  .then(function(response) {
    if (!response.ok) {
      throw new Error('HTTP ' + response.status);
    }
    return response.json();
  })
        .then(function(data) {
            loadingEl.hidden = true;

            if (!data.existe || !data.aluno) {
                notFoundEl.hidden = false;
                return;
            }

            contentEl.hidden = false;
            renderPerfil(data.aluno);
        })
    .catch(function(error) {
      loadingEl.hidden = true;
            notFoundEl.hidden = false;
            notFoundEl.querySelector('h3').textContent = 'Erro ao carregar perfil';
            notFoundEl.querySelector('p').textContent = 'Tente novamente mais tarde.';
            showToast('Erro ao carregar perfil', 'error');
        });
    }

    function renderPerfil(aluno) {
        var name = aluno.nome || '-';
        document.getElementById('perfil-nome').textContent = name;

        var statusKey = aluno.status_acompanhamento || 'aguardando_indicacao';
        var statusEl = document.getElementById('perfil-status');
        statusEl.textContent = STATUS_LABELS[statusKey] || statusKey;
        statusEl.className = 'perfil-status-badge ' + (STATUS_CLASSES[statusKey] || '');

        document.getElementById('perfil-matricula').textContent = aluno.matricula || '-';
        document.getElementById('perfil-curso').textContent = aluno.curso || '-';
        document.getElementById('perfil-campus').textContent = aluno.campus || '-';
        document.getElementById('perfil-email').textContent = aluno.email || '-';

        var perfil = aluno.perfil;
        if (perfil) {
            perfilData = perfil;
            document.getElementById('campo-nivel-atencao').textContent = perfil.nivel_atencao ? capitalizeFirst(perfil.nivel_atencao) : 'Nao definido';
            document.getElementById('campo-dificuldade-leitura').textContent = perfil.dificuldade_leitura ? 'Sim' : 'Nao';
            document.getElementById('campo-diagnostico').textContent = perfil.diagnostico || 'Nao definido';

            document.getElementById('campo-preferencia').value = perfil.preferencia || '';
            document.getElementById('campo-interesses').value = perfil.interesses || '';
        } else {
            perfilData = { preferencia: '', interesses: '' };
            document.getElementById('campo-nivel-atencao').textContent = 'Nao definido';
            document.getElementById('campo-dificuldade-leitura').textContent = 'Nao';
            document.getElementById('campo-diagnostico').textContent = 'Nao definido';
            document.getElementById('campo-preferencia').value = '';
            document.getElementById('campo-interesses').value = '';
        }

        document.getElementById('btn-save-perfil').disabled = true;
    }

    function handleSavePerfil() {
        var btnSave = document.getElementById('btn-save-perfil');
        var preferencia = document.getElementById('campo-preferencia').value;
        var interesses = document.getElementById('campo-interesses').value;

        btnSave.disabled = true;
        btnSave.querySelector('span').textContent = 'Salvando...';

        var payload = {};
        if (preferencia) payload.preferencia = preferencia;
        if (interesses) payload.interesses = interesses;

  acolheFetch('/portal/meu-perfil', {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  })
        .then(function(response) {
            if (!response.ok) {
                return response.json().then(function(err) {
                    throw new Error(err.detail || 'Erro ao salvar');
                });
            }
            return response.json();
        })
        .then(function(data) {
            perfilData = data;
            showToast('Perfil atualizado com sucesso!', 'success');
        })
    .catch(function(error) {
      showToast('Erro ao salvar: ' + error.message, 'error');
            btnSave.disabled = false;
        })
        .finally(function() {
            btnSave.querySelector('span').textContent = 'Salvar Alteracoes';
            checkPerfilChanged();
        });
    }

    function loadMeusConteudos() {
        var loadingEl = document.getElementById('conteudos-loading');
        var emptyEl = document.getElementById('conteudos-empty');
        var listEl = document.getElementById('conteudos-list');

        loadingEl.hidden = false;
        emptyEl.hidden = true;
        listEl.innerHTML = '';

  acolheFetch('/portal/meus-conteudos')
  .then(function(response) {
    if (!response.ok) {
      throw new Error('HTTP ' + response.status);
    }
    return response.json();
  })
        .then(function(conteudos) {
            loadingEl.hidden = true;

            if (!conteudos || conteudos.length === 0) {
                emptyEl.hidden = false;
                return;
            }

            conteudos.forEach(function(conteudo) {
                listEl.appendChild(createConteudoCard(conteudo));
            });
        })
    .catch(function(error) {
      loadingEl.hidden = true;
            emptyEl.hidden = false;
            emptyEl.querySelector('h3').textContent = 'Erro ao carregar conteudos';
            emptyEl.querySelector('p').textContent = 'Tente novamente mais tarde.';
            showToast('Erro ao carregar conteudos', 'error');
        });
    }

    function createConteudoCard(conteudo) {
        var card = document.createElement('div');
        card.className = 'conteudo-card';

        var dateStr = formatDate(conteudo.gerado_em);

        card.innerHTML =
            '<div class="conteudo-card-header">' +
                '<div class="conteudo-tema">' + escapeHtml(conteudo.tema) + '</div>' +
                '<div class="conteudo-meta">' +
                    '<span class="conteudo-modelo">' + escapeHtml(conteudo.modelo_ia) + '</span>' +
                    '<span class="conteudo-data">' + dateStr + '</span>' +
                '</div>' +
            '</div>' +
            '<div class="conteudo-card-actions">' +
                '<button class="btn-toggle-conteudo" data-conteudo-id="' + conteudo.id + '">' +
                    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px">' +
                        '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>' +
                        '<circle cx="12" cy="12" r="3"/>' +
                    '</svg>' +
                    '<span>Ver conteudo</span>' +
                '</button>' +
            '</div>' +
            '<div class="conteudo-card-body" id="conteudo-body-' + conteudo.id + '" hidden>' +
                '<div class="conteudo-texto">' + escapeHtml(conteudo.conteudo) + '</div>' +
            '</div>';

        var toggleBtn = card.querySelector('.btn-toggle-conteudo');
        toggleBtn.addEventListener('click', function() {
            var body = document.getElementById('conteudo-body-' + conteudo.id);
            var isHidden = body.hidden;
            body.hidden = !isHidden;
            toggleBtn.querySelector('span').textContent = isHidden ? 'Ocultar conteudo' : 'Ver conteudo';
            if (isHidden) {
                card.classList.add('conteudo-expanded');
            } else {
                card.classList.remove('conteudo-expanded');
            }
        });

        return card;
    }

    function showToast(message, type) {
        var toast = document.getElementById('toast');
        var toastMsg = document.getElementById('toast-message');
        if (!toast || !toastMsg) return;

        toast.className = 'toast toast-' + type;
        toastMsg.textContent = message;
        toast.hidden = false;

        setTimeout(function() {
            toast.hidden = true;
        }, 3500);
    }

    function escapeHtml(text) {
        if (!text) return '';
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function capitalizeFirst(str) {
        if (!str) return '';
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    function formatDate(isoString) {
        if (!isoString) return '-';
        var date = new Date(isoString);
        return date.toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    document.addEventListener('DOMContentLoaded', init);
})();
