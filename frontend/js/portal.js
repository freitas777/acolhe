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
        var userName = acolheGetUserName();
        currentUser = { nome: userName };
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

  var btnExportDados = document.getElementById('btn-export-dados');
  if (btnExportDados) {
    btnExportDados.addEventListener('click', function() {
      acolheFetch('/api/lgpd/export/meus-dados')
        .then(function(r) {
          if (!r.ok) throw new Error('HTTP ' + r.status);
          return r.blob();
        })
        .then(function(blob) {
          var url = window.URL.createObjectURL(blob);
          var a = document.createElement('a');
          a.href = url;
          a.download = 'meus-dados.json';
          document.body.appendChild(a);
          a.click();
          a.remove();
          window.URL.revokeObjectURL(url);
          showToast('Dados exportados com sucesso!', 'success');
        })
        .catch(function(err) {
          showToast('Erro ao exportar dados: ' + err.message, 'error');
        });
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
                if (conteudo.tipo === 'conversa') {
                    listEl.appendChild(createConversaCard(conteudo));
                } else {
                    listEl.appendChild(createConteudoCard(conteudo));
                }
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

        var dateStr = formatDate(conteudo.data);

        card.innerHTML =
            '<div class="conteudo-card-header">' +
                '<div class="conteudo-tema">' + escapeHtml(conteudo.titulo) + '</div>' +
                '<div class="conteudo-meta">' +
                    '<span class="conteudo-modelo">' + escapeHtml(conteudo.modelo_ia) + '</span>' +
                    '<span class="conteudo-data">' + dateStr + '</span>' +
                    '<span class="conteudo-versao">v' + (conteudo.versao || 1) + '</span>' +
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
                '<button class="btn-refazer" title="Refazer com ajustes">' +
                    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px">' +
                        '<polyline points="23 4 23 10 17 10"/>' +
                        '<path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>' +
                    '</svg>' +
                    '<span>Refazer</span>' +
                '</button>' +
                '<button class="btn-historico" title="Ver histórico">' +
                    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px">' +
                        '<circle cx="12" cy="12" r="10"/>' +
                        '<polyline points="12 6 12 12 16 14"/>' +
                    '</svg>' +
                    '<span>Histórico</span>' +
                '</button>' +
            '</div>' +
            '<div class="conteudo-card-body" id="conteudo-body-' + conteudo.id + '" hidden>' +
                '<div class="conteudo-texto">' + renderMarkdown(conteudo.conteudo) + '</div>' +
                '<div class="feedback-section" id="feedback-section-' + conteudo.id + '">' +
                    '<h4 class="feedback-title">Esta sugestão foi útil para você?</h4>' +
                    '<div class="feedback-rating">' +
                        '<button class="feedback-star" data-value="1" title="Muito inútil">☆</button>' +
                        '<button class="feedback-star" data-value="2" title="Inútil">☆</button>' +
                        '<button class="feedback-star" data-value="3" title="Neutro">☆</button>' +
                        '<button class="feedback-star" data-value="4" title="Útil">☆</button>' +
                        '<button class="feedback-star" data-value="5" title="Muito útil">☆</button>' +
                    '</div>' +
                    '<div class="feedback-quick">' +
                        '<button class="feedback-quick-btn" data-avaliacao="util">👍 Útil</button>' +
                        '<button class="feedback-quick-btn" data-avaliacao="parcial">👍👎 Parcial</button>' +
                        '<button class="feedback-quick-btn" data-avaliacao="nao_util">👎 Não útil</button>' +
                    '</div>' +
                    '<textarea class="feedback-comentario" placeholder="Comentário opcional (sugestões de melhoria)..." rows="3"></textarea>' +
                    '<button class="btn-feedback-submit">Enviar feedback</button>' +
                    '<div class="feedback-thanks" hidden>Obrigado pelo seu feedback!</div>' +
                '</div>' +
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

        // Setup feedback stars
        var stars = card.querySelectorAll('.feedback-star');
        var selectedRating = 0;
        stars.forEach(function(star) {
            star.addEventListener('click', function() {
                selectedRating = parseInt(this.dataset.value);
                stars.forEach(function(s, idx) {
                    if (idx < selectedRating) {
                        s.textContent = '★';
                        s.classList.add('active');
                    } else {
                        s.textContent = '☆';
                        s.classList.remove('active');
                    }
                });
            });
        });

        // Setup quick feedback
        var quickBtns = card.querySelectorAll('.feedback-quick-btn');
        var selectedAvaliacao = null;
        quickBtns.forEach(function(btn) {
            btn.addEventListener('click', function() {
                selectedAvaliacao = this.dataset.avaliacao;
                quickBtns.forEach(function(b) {
                    b.classList.remove('active');
                });
                this.classList.add('active');
            });
        });

        // Submit feedback
        var submitBtn = card.querySelector('.btn-feedback-submit');
        submitBtn.addEventListener('click', function() {
            if (!selectedAvaliacao && selectedRating === 0) {
                alert('Por favor, selecione uma avaliação.');
                return;
            }

            var comentario = card.querySelector('.feedback-comentario').value.trim();

            acolheFetch('/api/feedback/conteudos/' + conteudo.id, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    disciplina_id: null,
                    avaliacao: selectedAvaliacao || 'util',
                    utilidade_percebida: selectedRating > 0 ? selectedRating : null,
                    comentario: comentario || null,
                }),
            })
            .then(function() {
                card.querySelector('.feedback-section').hidden = true;
                card.querySelector('.feedback-thanks').hidden = false;
                showToast('Feedback enviado com sucesso!', 'success');
            })
            .catch(function(err) {
                console.error(err);
                showToast('Erro ao enviar feedback.', 'error');
            });
        });

        // Botão de refazer/iteração
        var refazerBtn = card.querySelector('.btn-refazer');
        if (refazerBtn) {
            refazerBtn.addEventListener('click', function() {
                var novoPrompt = prompt('Descreva os ajustes desejados (ex: "mais atividades visuais", "linguagem mais simples"):');
                if (!novoPrompt || !novoPrompt.trim()) return;

                acolheFetch('/conteudos/' + conteudo.id + '/iteracao', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        novo_prompt: novoPrompt.trim(),
                    }),
                })
                .then(function(r) { return r.json(); })
                .then(function(novaIteracao) {
                    showToast('Nova versão gerada! Carregando...', 'success');
                    // Recarregar lista de conteúdos
                    setTimeout(function() {
                        window.location.reload();
                    }, 1500);
                })
                .catch(function(err) {
                    console.error(err);
                    showToast('Erro ao gerar nova versão.', 'error');
                });
            });
        }

        // Botão de histórico
        var historicoBtn = card.querySelector('.btn-historico');
        if (historicoBtn) {
            historicoBtn.addEventListener('click', function() {
                acolheFetch('/conteudos/' + conteudo.id + '/historico')
                .then(function(r) { return r.json(); })
                .then(function(historico) {
                    if (!historico || historico.length <= 1) {
                        alert('Este é o conteúdo original (sem iterações).');
                        return;
                    }
                    
                    var msg = 'Histórico de iterações:\n\n';
                    historico.forEach(function(v, idx) {
                        var data = new Date(v.gerado_em).toLocaleString('pt-BR');
                        msg += 'Versão ' + v.versao + ' - ' + data + '\n';
                        if (idx < historico.length - 1) msg += '  ↓\n';
                    });
                    alert(msg);
                })
                .catch(function(err) {
                    console.error(err);
                    alert('Erro ao carregar histórico.');
                });
            });
        }

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

 function renderMarkdown(text) {
 if (!text) return '';
 if (typeof window.marked !== 'undefined' && typeof window.DOMPurify !== 'undefined') {
 return DOMPurify.sanitize(marked.parse(text));
 }
 return escapeHtml(text);
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

    function createConversaCard(conversa) {
        var card = document.createElement('div');
        card.className = 'conteudo-card';

        var dateStr = formatDate(conversa.data);
        var messageCount = conversa.messages ? conversa.messages.length : 0;

        card.innerHTML =
            '<div class="conteudo-card-header">' +
                '<div class="conteudo-tema">' + escapeHtml(conversa.titulo) + '</div>' +
                '<div class="conteudo-meta">' +
                    '<span class="conteudo-data">' + dateStr + '</span>' +
                    '<span class="conteudo-versao">' + messageCount + ' mensagens</span>' +
                '</div>' +
            '</div>' +
            '<div class="conteudo-card-actions">' +
                '<button class="btn-toggle-conteudo" data-conversa-id="' + conversa.id + '">' +
                    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px">' +
                        '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>' +
                        '<circle cx="12" cy="12" r="3"/>' +
                    '</svg>' +
                    '<span>Ver conversa</span>' +
                '</button>' +
            '</div>' +
            '<div class="conteudo-card-body" id="conversa-body-' + conversa.id + '" hidden>' +
                '<div class="conversa-timeline">' +
                    renderConversaTimeline(conversa.messages || [], conversa.usuario_tipo) +
                '</div>' +
            '</div>';

        var toggleBtn = card.querySelector('.btn-toggle-conteudo');
        toggleBtn.addEventListener('click', function() {
            var body = document.getElementById('conversa-body-' + conversa.id);
            var isHidden = body.hidden;
            body.hidden = !isHidden;
            toggleBtn.querySelector('span').textContent = isHidden ? 'Ocultar conversa' : 'Ver conversa';
            if (isHidden) {
                card.classList.add('conteudo-expanded');
            } else {
                card.classList.remove('conteudo-expanded');
            }
        });

        var actorItems = card.querySelectorAll('.timeline-actor');
        console.log('Found', actorItems.length, 'actor items');
        actorItems.forEach(function(item) {
            item.addEventListener('click', function() {
                var msgId = this.dataset.messageId;
                console.log('Clicked actor, msgId:', msgId);
                showMessageContent(msgId, this);
            });
        });

        return card;
    }

    function renderConversaTimeline(messages, usuarioTipo) {
        if (!messages || messages.length === 0) {
            return '<p class="conversa-empty">Nenhuma mensagem nesta conversa.</p>';
        }

        console.log('Messages:', messages);

        var html = '';
        messages.forEach(function(msg) {
            var papel = msg.papel || msg.role || '';
            var conteudo = msg.conteudo || msg.content || '';
            var actorLabel = '';
            var actorClass = '';
            if (papel === 'usuario') {
                actorLabel = usuarioTipo ? getTipoPerfilLabel(usuarioTipo) : 'Servidor';
                actorClass = 'actor-user';
            } else {
                actorLabel = 'Assistente';
                actorClass = 'actor-assistant';
            }

            var userIcon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>';
            var botIcon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/><path d="M12 7v4"/><line x1="8" y1="16" x2="8" y2="16"/><line x1="16" y1="16" x2="16" y2="16"/></svg>';

            console.log('Message:', { id: msg.id, papel: papel, conteudo: conteudo ? conteudo.substring(0, 50) : '' });

            html +=
                '<div class="timeline-item">' +
                    '<div class="timeline-actor ' + actorClass + '" data-message-id="' + msg.id + '">' +
                        '<div class="actor-icon">' + (papel === 'usuario' ? userIcon : botIcon) + '</div>' +
                        '<div class="actor-label">' + escapeHtml(actorLabel) + '</div>' +
                    '</div>' +
                    '<div class="timeline-message" id="msg-' + msg.id + '" hidden>' +
                        '<div class="message-content">' + renderMarkdown(conteudo) + '</div>' +
                    '</div>' +
                '</div>';
        });
        return html;
    }

    function showMessageContent(msgId, actorElement) {
        var elementId = 'msg-' + msgId;
        console.log('showMessageContent called with msgId:', msgId, 'looking for element:', elementId);
        var messageDiv = document.getElementById(elementId);
        if (!messageDiv) {
            console.error('Message element not found:', elementId);
            return;
        }

        var isHidden = messageDiv.hidden;
        console.log('Message div found, isHidden:', isHidden);

        document.querySelectorAll('.timeline-message').forEach(function(div) {
            div.hidden = true;
        });
        document.querySelectorAll('.timeline-actor').forEach(function(actor) {
            actor.classList.remove('active');
        });

        if (isHidden) {
            messageDiv.hidden = false;
            actorElement.classList.add('active');
            console.log('Message shown');
        } else {
            console.log('Message hidden');
        }
    }

    function getTipoPerfilLabel(tipo) {
        var labels = {
            'napne': 'NAPNE',
            'psicopedagogo': 'Psicopedagogo',
            'servidor': 'Servidor',
            'professor': 'Professor',
            'aluno': 'Aluno'
        };
        return labels[tipo] || tipo.charAt(0).toUpperCase() + tipo.slice(1);
    }

    document.addEventListener('DOMContentLoaded', init);
})();
