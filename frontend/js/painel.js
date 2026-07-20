(function() {
'use strict';

 if (!acolheRequireRole(['psicopedagogo', 'servidor', 'admin'])) return;

 var userId = localStorage.getItem('acolhe_user_id');
    var currentUser = null;
    var searchTimeout = null;

function init() {
 loadUserInfo();
 loadEquipe();
 loadPendencias();
 loadAlunosAtivos();
 setupEventListeners();
 checkSenhaTemporaria();
}

function checkSenhaTemporaria() {
 if (localStorage.getItem('acolhe_senha_temporaria') === 'true') {
  openSenhaModal(true);
 }
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

    function loadEquipe() {
  var listEl = document.getElementById('equipe-list');
  var countEl = document.getElementById('equipe-count');
  if (!listEl) return;

 acolheFetch('/equipe/membros')
  .then(function(r) {
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return r.json();
  })
  .then(function(membros) {
    if (countEl) countEl.textContent = membros.length;
    if (!membros || membros.length === 0) {
      listEl.innerHTML = '<div class="empty-col"><p>Nenhum membro na equipe</p></div>';
      return;
    }
    listEl.innerHTML = '';
    membros.forEach(function(m) {
      var initials = (m.nome || '?').split(' ').map(function(n){ return n[0]; }).slice(0,2).join('').toUpperCase();
      var tipoLabel = {admin: 'Admin', psicopedagogo: 'Psicopedagogo', servidor: 'Servidor'}[m.tipo_perfil] || m.tipo_perfil;
      var statusHtml = '';
      if (m.senha_temporaria) {
        statusHtml = '<span class="membro-badge badge-pendente">Senha temporaria</span>';
      } else if (!m.conta_ativa) {
        statusHtml = '<span class="membro-badge badge-inativo">Inativo</span>';
      }
      var item = document.createElement('div');
      item.className = 'equipe-item';
      item.innerHTML =
        '<div class="ativo-avatar">' + escapeHtml(initials) + '</div>' +
        '<div class="ativo-info">' +
        '<div class="ativo-nome">' + escapeHtml(m.nome) + '</div>' +
        '<div class="ativo-matricula">' + escapeHtml(tipoLabel) + ' &middot; ' + escapeHtml(m.email) + '</div>' +
        statusHtml +
        '</div>';
      listEl.appendChild(item);
    });
  })
  .catch(function(err) {
    listEl.innerHTML = '<div class="empty-col"><p>Erro ao carregar equipe</p></div>';
  });
}

function loadPendencias() {
        var listEl = document.getElementById('pendencias-list');
        var countEl = document.getElementById('pendencias-count');
        if (!listEl) return;

 acolheFetch('/equipe/pendencias')
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
btn.addEventListener('click', function() {
if (confirm('Deseja realmente rejeitar esta pendencia? O aluno sera excluido do acompanhamento.')) {
validarPendencia(parseInt(btn.dataset.id), 'rejeitado');
}
});
});
        })
        .catch(function(err) {
            listEl.innerHTML = '<div class="empty-col"><p>Erro ao carregar pendencias</p></div>';
        });
    }

function validarPendencia(pendenciaId, acao) {
 acolheFetch('/equipe/pendencias/' + pendenciaId, {
 method: 'PUT',
 headers: { 'Content-Type': 'application/json' },
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

 acolheFetch('/equipe/alunos-ativos')
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
var initials = (a.nome || '?').split(' ').map(function(n){ return n[0]; }).slice(0,2).join('').toUpperCase();
    var item = document.createElement('div');
    item.className = 'aluno-ativo-item';
      item.setAttribute('data-aluno-id', a.id);
      item.setAttribute('data-aluno-nome', a.nome);
      item.innerHTML =
        '<div class="ativo-avatar">' + escapeHtml(initials) + '</div>' +
        '<div class="ativo-info">' +
        '<div class="ativo-nome">' + escapeHtml(a.nome) + '</div>' +
        (a.matricula ? '<div class="ativo-matricula">' + escapeHtml(a.matricula) + '</div>' : '') +
        (a.diagnostico ? '<div class="ativo-diagnostico">' + escapeHtml(a.diagnostico) + '</div>' : '') +
        '</div>' +
        '<button class="btn-profile" title="Editar perfil" data-aluno-id="' + a.id + '" data-aluno-nome="' + escapeHtml(a.nome) + '">' +
        '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>' +
        '</button>';
      listEl.appendChild(item);
    });

    listEl.querySelectorAll('.btn-profile').forEach(function(btn) {
      btn.addEventListener('click', function(e) {
        e.stopPropagation();
        openProfileModal(parseInt(btn.dataset.alunoId), btn.dataset.alunoNome);
      });
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

 acolheFetch('/equipe/alunos-busca?q=' + encodeURIComponent(query))
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
var initials = (a.nome || '?').split(' ').map(function(n){ return n[0]; }).slice(0,2).join('').toUpperCase();
var item = document.createElement('div');
item.className = 'search-result-item';
item.setAttribute('data-aluno-id', a.id);
item.setAttribute('data-aluno-nome', a.nome);
item.innerHTML =
'<div class="result-avatar">' + escapeHtml(initials) + '</div>' +
'<div class="result-info">' +
'<div class="result-nome">' + escapeHtml(a.nome) + '</div>' +
(a.matricula ? '<div class="result-matricula">' + escapeHtml(a.matricula) + '</div>' : '') +
(a.diagnostico ? '<div class="result-diagnostico">' + escapeHtml(a.diagnostico) + '</div>' : '') +
'</div>';
item.addEventListener('click', function() {
openProfileModal(a.id, a.nome);
resultsEl.hidden = true;
document.getElementById('search-input').value = '';
});
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
            if (id === 'profile-modal') closeProfileModal();
            else if (id === 'invite-modal') closeInviteModal();
            else if (id === 'senha-modal') closeSenhaModal();
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

function openProfileModal(alunoId, alunoNome) {
   var modal = document.getElementById('profile-modal');
   var nameEl = document.getElementById('modal-aluno-name');
   var idEl = document.getElementById('profile-aluno-id');
   if (!modal || !idEl) return;

   idEl.value = alunoId;
   if (nameEl) nameEl.textContent = 'Perfil: ' + (alunoNome || 'Aluno');

   document.getElementById('profile-nivel-atencao').value = '';
   document.getElementById('profile-dificuldade-leitura').value = 'false';
   document.getElementById('profile-preferencia').value = '';
   document.getElementById('profile-interesses').value = '';
   document.getElementById('profile-diagnostico').value = '';

   modal.hidden = false;

   acolheFetch('/equipe/alunos/' + alunoId + '/perfil')
     .then(function(r) {
       if (!r.ok) throw new Error('HTTP ' + r.status);
       return r.json();
     })
     .then(function(perfil) {
       if (perfil.nivel_atencao) document.getElementById('profile-nivel-atencao').value = perfil.nivel_atencao;
       document.getElementById('profile-dificuldade-leitura').value = String(perfil.dificuldade_leitura || false);
       if (perfil.preferencia) document.getElementById('profile-preferencia').value = perfil.preferencia;
       if (perfil.interesses) document.getElementById('profile-interesses').value = perfil.interesses;
           if (perfil.diagnostico) document.getElementById('profile-diagnostico').value = perfil.diagnostico;
     })
     .catch(function() {
       showToast('Erro ao carregar perfil', 'error');
     });
   // Load professor observations for this aluno (NAPNE view)
   loadProfessorObservacoes(alunoId);
   _trapFocus(modal);
}

function closeProfileModal() {
    _untrapFocus();
    var modal = document.getElementById('profile-modal');
    if (modal) modal.hidden = true;
}

function saveProfile(e) {
  e.preventDefault();
  var alunoId = document.getElementById('profile-aluno-id').value;
  if (!alunoId) return;

  var payload = {
    nivel_atencao: document.getElementById('profile-nivel-atencao').value || null,
    dificuldade_leitura: document.getElementById('profile-dificuldade-leitura').value === 'true',
    preferencia: document.getElementById('profile-preferencia').value || null,
    interesses: document.getElementById('profile-interesses').value || null,
    diagnostico: document.getElementById('profile-diagnostico').value || null,
  };

 acolheFetch('/equipe/alunos/' + alunoId + '/perfil', {
 method: 'PUT',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify(payload)
  })
  .then(function(r) {
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return r.json();
  })
  .then(function() {
    showToast('Perfil salvo com sucesso', 'success');
    closeProfileModal();
    loadAlunosAtivos();
  })
  .catch(function(err) {
    showToast('Erro ao salvar perfil: ' + err.message, 'error');
  });
}

function openInviteModal() {
  var modal = document.getElementById('invite-modal');
  if (!modal) return;
  document.getElementById('invite-nome').value = '';
  document.getElementById('invite-email').value = '';
  document.getElementById('invite-tipo').value = 'psicopedagogo';
  var resultEl = document.getElementById('invite-result');
  if (resultEl) resultEl.hidden = true;
  var actionsEl = document.getElementById('invite-actions');
  if (actionsEl) actionsEl.hidden = false;
  var submitBtn = document.getElementById('invite-submit');
    if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = 'Convidar'; }
    modal.hidden = false;
    _trapFocus(modal);
}

function closeInviteModal() {
    _untrapFocus();
    var modal = document.getElementById('invite-modal');
    if (modal) modal.hidden = true;
}

function handleInvite(e) {
  e.preventDefault();
  var nome = document.getElementById('invite-nome').value.trim();
  var email = document.getElementById('invite-email').value.trim();
  var tipo = document.getElementById('invite-tipo').value;
  var btn = document.getElementById('invite-submit');
  var errorEl = document.getElementById('error-message');
  var errorText = document.getElementById('error-text');

  if (!nome || !email) {
    showToast('Preencha nome e email.', 'warning');
    return;
  }

  btn.disabled = true;
  btn.textContent = 'Enviando...';

 acolheFetch('/auth/convite', {
 method: 'POST',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify({ nome: nome, email: email, tipo_perfil: tipo })
  })
  .then(function(r) {
    if (!r.ok) return r.json().then(function(d) { throw new Error(d.detail || 'HTTP ' + r.status); });
    return r.json();
  })
  .then(function(data) {
    document.getElementById('invite-result-email').textContent = data.email;
    document.getElementById('invite-result-senha').textContent = data.senha_temporaria;
    document.getElementById('invite-result').hidden = false;
    document.getElementById('invite-actions').hidden = true;
    showToast('Convite criado com sucesso!', 'success');
    loadEquipe();
  })
  .catch(function(err) {
    showToast('Erro: ' + err.message, 'error');
    btn.disabled = false;
    btn.textContent = 'Convidar';
  });
}

function openSenhaModal(forceTemp) {
 var modal = document.getElementById('senha-modal');
 if (!modal) return;
 document.getElementById('senha-atual').value = '';
 document.getElementById('senha-nova').value = '';
 document.getElementById('senha-nova-conf').value = '';
 var noticeEl = document.getElementById('senha-temp-notice');
 var isTemp = !!forceTemp;
 if (noticeEl) noticeEl.hidden = !isTemp;
 var cancelBtn = document.getElementById('senha-cancel');
 if (cancelBtn) cancelBtn.style.display = isTemp ? 'none' : '';
 var submitBtn = document.getElementById('senha-submit');
    if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = 'Alterar Senha'; }
    modal.hidden = false;
    _trapFocus(modal);
}

function closeSenhaModal() {
    _untrapFocus();
    var modal = document.getElementById('senha-modal');
    if (modal) modal.hidden = true;
    if (localStorage.getItem('acolhe_senha_temporaria') === 'true') {
        acolheLogout();
    }
}

function handleAlterarSenha(e) {
 e.preventDefault();
 var senhaAtual = document.getElementById('senha-atual').value;
 var senhaNova = document.getElementById('senha-nova').value;
 var senhaConf = document.getElementById('senha-nova-conf').value;
 var btn = document.getElementById('senha-submit');

 if (!senhaAtual || !senhaNova) {
  showToast('Preencha todos os campos.', 'warning');
  return;
 }
 if (senhaNova.length < 6) {
  showToast('A nova senha deve ter pelo menos 6 caracteres.', 'warning');
  return;
 }
 if (senhaNova !== senhaConf) {
  showToast('As senhas nao coincidem.', 'warning');
  return;
 }

 btn.disabled = true;
 btn.textContent = 'Alterando...';

 acolheFetch('/auth/alterar-senha', {
 method: 'PUT',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify({ senha_atual: senhaAtual, nova_senha: senhaNova })
 })
 .then(function(r) {
  if (!r.ok) return r.json().then(function(d) { throw new Error(d.detail || 'HTTP ' + r.status); });
  return r.json();
 })
 .then(function() {
  localStorage.setItem('acolhe_senha_temporaria', 'false');
  showToast('Senha alterada com sucesso!', 'success');
  closeSenhaModal();
  loadEquipe();
 })
 .catch(function(err) {
  showToast('Erro: ' + err.message, 'error');
  btn.disabled = false;
  btn.textContent = 'Alterar Senha';
 });
}

function setupEventListeners() {        var searchInput = document.getElementById('search-input');
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
        acolheLogout();
      }
    });
  }

    var modalClose = document.getElementById('modal-close');
    if (modalClose) modalClose.addEventListener('click', closeProfileModal);

    var modalCancel = document.getElementById('modal-cancel');
    if (modalCancel) modalCancel.addEventListener('click', closeProfileModal);

    var profileModal = document.getElementById('profile-modal');
    if (profileModal) profileModal.addEventListener('click', function(e) {
      if (e.target === profileModal) closeProfileModal();
    });

  var profileForm = document.getElementById('profile-form');
  if (profileForm) profileForm.addEventListener('submit', saveProfile);

  var btnGerarRelatorioPdf = document.getElementById('btn-gerar-relatorio-pdf');
  if (btnGerarRelatorioPdf) btnGerarRelatorioPdf.addEventListener('click', gerarRelatorioPDF);

  var btnInvite = document.getElementById('btn-invite');
  if (btnInvite) btnInvite.addEventListener('click', openInviteModal);

  var inviteModalClose = document.getElementById('invite-modal-close');
  if (inviteModalClose) inviteModalClose.addEventListener('click', closeInviteModal);

  var inviteCancel = document.getElementById('invite-cancel');
  if (inviteCancel) inviteCancel.addEventListener('click', closeInviteModal);

  var inviteModal = document.getElementById('invite-modal');
  if (inviteModal) inviteModal.addEventListener('click', function(e) {
    if (e.target === inviteModal) closeInviteModal();
  });

  var inviteForm = document.getElementById('invite-form');
  if (inviteForm) inviteForm.addEventListener('submit', handleInvite);

  var btnSenha = document.getElementById('btn-senha');
  if (btnSenha) btnSenha.addEventListener('click', openSenhaModal);

  var senhaModalClose = document.getElementById('senha-modal-close');
  if (senhaModalClose) senhaModalClose.addEventListener('click', closeSenhaModal);

  var senhaCancel = document.getElementById('senha-cancel');
  if (senhaCancel) senhaCancel.addEventListener('click', closeSenhaModal);

  var senhaModal = document.getElementById('senha-modal');
  if (senhaModal) senhaModal.addEventListener('click', function(e) {
   if (e.target === senhaModal) closeSenhaModal();
  });

  var senhaForm = document.getElementById('senha-form');
  if (senhaForm) senhaForm.addEventListener('submit', handleAlterarSenha);
 }

     document.addEventListener('DOMContentLoaded', init);

// Load observations of professors for a given aluno (NAPNE view)
function loadProfessorObservacoes(alunoId) {
   var container = document.getElementById('profile-observacoes');
   if (!container) return;
   acolheFetch('/equipe/alunos/' + alunoId + '/observacoes')
     .then(function(r){ if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
     .then(function(obsList) {
       if (!obsList || obsList.length === 0) {
         container.innerHTML = '<p>Nenhuma observação registrada.</p>';
         return;
       }
       var html = '';
       obsList.forEach(function(obs) {
         // obs is expected to have: id, aluno_id, disciplina_id, professor_id, disciplina_sigla, professor_nome, texto, criado_em
         var date = new Date(obs.criado_em);
         var dateStr = date.toLocaleString('pt-BR');
         html += '<div class="observacao-item">' +
                 '<div class="observacao-header">' +
                 '<strong>Professor ' + escapeHtml(obs.professor_nome) + '</strong> ' +
                 '<span class="disciplina-sigla">[' + escapeHtml(obs.disciplina_sigla) + ']</span> ' +
                 '<span class="data">' + escapeHtml(dateStr) + '</span>' +
                 '</div>' +
                 '<div class="observacao-texto">' + escapeHtml(obs.texto) + '</div>' +
                 '</div>';
       });
container.innerHTML = html;
     })
     .catch(function(err){
       container.innerHTML = '<p>Erro ao carregar observações</p>';
       console.error(err);
     });
}

function loadDashboardMetrics() {
 acolheFetch('/equipe/dashboard')
   .then(function(r) { return r.json(); })
   .then(function(data) {
     document.getElementById('metric-alunos-ativos').textContent = data.alunos_ativos !== undefined ? data.alunos_ativos : '0';
     document.getElementById('metric-pendencias').textContent = data.pendencias_pendentes !== undefined ? data.pendencias_pendentes : '0';
     document.getElementById('metric-observacoes').textContent = data.observacoes_mes !== undefined ? data.observacoes_mes : '0';
     document.getElementById('metric-conteudos').textContent = data.conteudos_gerados !== undefined ? data.conteudos_gerados : '0';
   })
   .catch(function(err) {
     console.error('Erro ao carregar dashboard:', err);
     // Fallback para 0 em caso de erro
     document.getElementById('metric-alunos-ativos').textContent = '0';
     document.getElementById('metric-pendencias').textContent = '0';
     document.getElementById('metric-observacoes').textContent = '0';
     document.getElementById('metric-conteudos').textContent = '0';
    });
}

function gerarRelatorioPDF() {
  var alunoId = document.getElementById('profile-aluno-id').value;
  if (!alunoId) {
    showToast('Selecione um aluno primeiro', 'warning');
    return;
  }

  var btn = document.getElementById('btn-gerar-relatorio-pdf');
  if (btn) {
    btn.disabled = true;
    btn.textContent = 'Gerando...';
  }

  var token = acolheGetToken();
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/api/relatorios/aluno/' + alunoId + '/pdf');
  xhr.setRequestHeader('Authorization', 'Bearer ' + token);
  xhr.responseType = 'blob';

  xhr.onload = function() {
    if (btn) {
      btn.disabled = false;
      btn.textContent = 'Gerar Relatório PDF';
    }

    if (xhr.status === 200) {
      var blob = xhr.response;
      var url = window.URL.createObjectURL(blob);
      var a = document.createElement('a');
      a.href = url;
      a.download = 'relatorio-aluno-' + alunoId + '-' + new Date().toISOString().split('T')[0] + '.pdf';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      showToast('Relatório PDF gerado com sucesso', 'success');
    } else {
      var msg = 'Erro ao gerar relatório PDF';
      try {
        var reader = new FileReader();
        reader.onload = function() {
          try {
            var err = JSON.parse(reader.result);
            showToast(err.detail || msg, 'error');
          } catch(e) {
            showToast(msg, 'error');
          }
        };
        reader.readAsText(xhr.response);
      } catch(e) {
        showToast(msg, 'error');
      }
    }
  };

  xhr.onerror = function() {
    if (btn) {
      btn.disabled = false;
      btn.textContent = 'Gerar Relatório PDF';
    }
    showToast('Erro de conexão ao gerar relatório', 'error');
  };

  xhr.send();
}

})();
