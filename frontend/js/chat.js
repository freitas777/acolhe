(function() {
'use strict';

    if (!acolheRequireAuth()) return;

    var currentUser = null;
    var alunoSearchTimer = null;
    var isAluno = acolheGetTipoPerfil() === 'aluno';
    var isProfessorChat = acolheGetTipoPerfil() === 'professor';
    var isNapne = ['psicopedagogo', 'admin', 'servidor'].indexOf(acolheGetTipoPerfil()) !== -1;
    var disciplinasCache = [];

    if (isAluno) document.body.classList.add('role-aluno');

    var pendingDisciplina = null;
    var pendingAluno = null;
    var ementaPendente = null;
    var anexosPendentes = [];

    async function handlePendingContext() {
      var raw = null;
      try { raw = sessionStorage.getItem('acolhe_open_conversa'); } catch (e) {}
      if (!raw) return false;
      try {
        var data = JSON.parse(raw);
        if (data && data.tipo === 'disciplina' && data.disciplina_id) {
          pendingDisciplina = data;
          try { sessionStorage.removeItem('acolhe_open_conversa'); } catch (e) {}
          return 'disciplina';
        }
        if (data && data.tipo === 'aluno' && data.aluno_id) {
          pendingAluno = data;
          try { sessionStorage.removeItem('acolhe_open_conversa'); } catch (e) {}
          return 'aluno';
        }
      } catch (e) {}
      try { sessionStorage.removeItem('acolhe_open_conversa'); } catch (e) {}
      return false;
    }

    function getDisciplinaFromCache(disciplinaId) {
      for (var k = 0; k < disciplinasCache.length; k++) {
        if (disciplinasCache[k].id === disciplinaId) return disciplinasCache[k];
      }
      return null;
    }

    async function openDisciplinaContext(disciplinaData) {
      var disciplinaId = disciplinaData.disciplina_id;
      var disciplinaDescricao = disciplinaData.disciplina_descricao;

      if (isNapne) {
        ChatStore.clearDisciplinaContext();
        ChatUI.hideDisciplinaBadge();
        ChatUI.updateTitle('Nova Conversa');
        ChatUI.renderMessages([]);
        ChatUI.showToast('Contexto de disciplina e ementa sao exclusivos do perfil Professor.', 'info');
        return;
      }

      if (isProfessorChat) {
        var disc = getDisciplinaFromCache(disciplinaId);
        if (disc && !disc.tem_ementa) {
          ementaPendente = disciplinaData;
          ChatUI.openEmentaModal(disciplinaDescricao || disc.descricao || '', '');
          return;
        }
      }

      var discInfo = getDisciplinaFromCache(disciplinaId);
      var sigla = discInfo ? (discInfo.sigla || '') : '';

      ChatStore.setDisciplinaContext(disciplinaId, disciplinaDescricao, sigla);
      ChatStore.state.activeConversationId = null;
      ChatStore.save();
      if (disciplinaData.aluno_id) {
        ChatStore.setAlunoContext(disciplinaData.aluno_id, disciplinaData.aluno_nome || null);
        ChatUI.updateAlunoBadge(disciplinaData.aluno_nome || null);
      } else {
        syncAlunoBadge();
      }
      ChatUI.showDisciplinaBadge(disciplinaDescricao, sigla);
      ChatUI.updateTitle(disciplinaDescricao || 'Nova Conversa');
      ChatUI.renderMessages([]);
      renderSidebar(null);
      ChatUI.closeSidebar();
      if (ChatUI.elements.messageInput) ChatUI.elements.messageInput.focus();
    }

    function openAlunoContext(alunoData) {
      ChatStore.setAlunoContext(alunoData.aluno_id, alunoData.aluno_nome);
      ChatStore.state.activeConversationId = null;
      ChatStore.save();
      ChatUI.updateAlunoBadge(alunoData.aluno_nome);
      ChatUI.updateTitle('Nova Conversa');
      ChatUI.renderMessages([]);
      renderSidebar(null);
      ChatUI.closeSidebar();
      if (ChatUI.elements.messageInput) ChatUI.elements.messageInput.focus();
    }

  async function init() {
        ChatStore.init();
        if (isNapne) ChatStore.clearDisciplinaContext();
        ChatUI.init();
        applyRoleVisibility();
        await loadUserData();
        if (isProfessorChat) {
          await loadDisciplinas();
        }
        setupEventListeners();
        var hasContext = await handlePendingContext();
        if (hasContext === 'disciplina' && pendingDisciplina) {
          try { await ChatService.loadConversations(); } catch (e) {}
          await openDisciplinaContext(pendingDisciplina);
        } else if (hasContext === 'aluno' && pendingAluno) {
          try { await ChatService.loadConversations(); } catch (e) {}
          openAlunoContext(pendingAluno);
        } else {
          await renderInitialState();
        }
    }

async function loadDisciplinas() {
  disciplinasCache = await ChatService.listarDisciplinas();
}

async function handleEmentaSave() {
  var fileInput = ChatUI.elements.ementaFileInput;
  var file = fileInput && fileInput.files && fileInput.files[0];
  if (!file) {
    ChatUI.showToast('Selecione o arquivo da ementa.', 'warning');
    return;
  }
  if (!ementaPendente) {
    ChatUI.closeEmentaModal();
    return;
  }
  var id = ementaPendente.disciplina_id;
  var resp = await ChatService.salvarEmenta(id, file);
  if (!resp) {
    ChatUI.showToast('Erro ao enviar a ementa. Tente novamente.');
    return;
  }
  for (var k = 0; k < disciplinasCache.length; k++) {
    if (disciplinasCache[k].id === id) {
      disciplinasCache[k].ementa = resp.ementa || file.name;
      disciplinasCache[k].tem_ementa = true;
      break;
    }
  }
  ChatUI.closeEmentaModal();
  var pendente = ementaPendente;
  ementaPendente = null;
  await openDisciplinaContext(pendente);
}

function handleEmentaCancel() {
  ChatUI.closeEmentaModal();
  ementaPendente = null;
}

function applyRoleVisibility() {
if (isAluno) {
if (ChatUI.elements.btnAlunoContext) ChatUI.elements.btnAlunoContext.hidden = true;
if (ChatUI.elements.alunoContextBar) ChatUI.elements.alunoContextBar.hidden = true;
}

var perfil = acolheGetTipoPerfil();
var isNapne = perfil === 'psicopedagogo' || perfil === 'admin' || perfil === 'servidor';
var navPainel = document.getElementById('nav-painel');
var navNotificacoes = document.getElementById('nav-notificacoes');
var navPortal = document.getElementById('nav-portal');
var navDisciplinas = document.getElementById('nav-disciplinas');
var btnAnexo = ChatUI.elements.btnAnexo;

if (navPainel) navPainel.style.display = isNapne ? '' : 'none';
if (navNotificacoes) navNotificacoes.style.display = isNapne ? '' : 'none';
if (navPortal) navPortal.style.display = isAluno ? '' : 'none';
if (navDisciplinas) navDisciplinas.style.display = isAluno || perfil === 'professor' ? '' : 'none';
if (btnAnexo) btnAnexo.hidden = !isNapne;
}

async function loadUserData() {
    var userName = acolheGetUserName();
    var tipoPerfil = acolheGetTipoPerfil();
    currentUser = { nome: userName, tipo_perfil: tipoPerfil };
    ChatUI.updateUserInfo(currentUser);
}

  function setupEventListeners() {
    if (ChatUI.elements.btnNewChat) {
      ChatUI.elements.btnNewChat.addEventListener('click', handleNewConversation);
    }
    if (ChatUI.elements.btnSend) {
      ChatUI.elements.btnSend.addEventListener('click', handleSendMessage);
    }
    if (ChatUI.elements.messageInput) {
      ChatUI.elements.messageInput.addEventListener('input', handleInput);
      ChatUI.elements.messageInput.addEventListener('keydown', handleKeydown);
    }
    if (ChatUI.elements.ementaSave) {
      ChatUI.elements.ementaSave.addEventListener('click', handleEmentaSave);
    }
    if (ChatUI.elements.btnAnexo) {
      ChatUI.elements.btnAnexo.addEventListener('click', function(e) {
        e.stopPropagation();
        if (ChatUI.elements.anexoFileInput) ChatUI.elements.anexoFileInput.click();
      });
    }
    if (ChatUI.elements.anexoFileInput) {
      ChatUI.elements.anexoFileInput.addEventListener('change', async function(e) {
        var files = e.target.files;
        if (!files || files.length === 0) return;
        for (var i = 0; i < files.length; i++) {
          await handleAnexoUpload(files[i]);
        }
        e.target.value = '';
      });
    }
    ChatUI.onAnexoRemoved = handleAnexoRemoved;
    ChatUI.onAnexoConversaRemoved = handleAnexoConversaRemoved;
    if (ChatUI.elements.ementaFileInput) {
      ChatUI.elements.ementaFileInput.addEventListener('change', function(e) {
        var f = e.target.files && e.target.files[0];
        if (ChatUI.elements.ementaFileName && f) {
          ChatUI.elements.ementaFileName.textContent = f.name;
        }
      });
    }
    if (ChatUI.elements.ementaCancel) {
      ChatUI.elements.ementaCancel.addEventListener('click', handleEmentaCancel);
    }
    if (ChatUI.elements.ementaClose) {
      ChatUI.elements.ementaClose.addEventListener('click', handleEmentaCancel);
    }
    if (ChatUI.elements.btnMenuMobile) {
      ChatUI.elements.btnMenuMobile.addEventListener('click', function() {
        ChatUI.openSidebar();
      });
    }
    document.addEventListener('click', function(e) {
      if (window.innerWidth <= 768) {
        var sidebar = ChatUI.elements.sidebar;
        var menuBtn = ChatUI.elements.btnMenuMobile;
        if (sidebar && !sidebar.contains(e.target) && menuBtn && !menuBtn.contains(e.target)) {
          ChatUI.closeSidebar();
        }
      }
    });
if (ChatUI.elements.btnLogout) {
      ChatUI.elements.btnLogout.addEventListener('click', handleLogout);
    }
    ChatUI.onConversationSelect = handleConversationSelect;
    ChatUI.onConversationDelete = handleConversationDelete;

    if (ChatUI.elements.chatTitle) {
      ChatUI.elements.chatTitle.addEventListener('dblclick', handleTitleRename);
    }
    if (ChatUI.elements.btnRenomear) {
      ChatUI.elements.btnRenomear.addEventListener('click', handleTitleRename);
    }

    if (!isAluno) {
        ChatUI.onAlunoSelected = handleAlunoSelected;

        if (ChatUI.elements.btnAlunoContext) {
            ChatUI.elements.btnAlunoContext.addEventListener('click', function() {
                ChatUI.showAlunoSearch();
            });
        }
        if (ChatUI.elements.btnRemoveAluno) {
            ChatUI.elements.btnRemoveAluno.addEventListener('click', handleRemoveAluno);
        }
        if (ChatUI.elements.alunoSearchInput) {
            ChatUI.elements.alunoSearchInput.addEventListener('input', handleAlunoSearchInput);
            ChatUI.elements.alunoSearchInput.addEventListener('keydown', function(e) {
                if (e.key === 'Escape') {
                    ChatUI.hideAlunoSearchResults();
                    if (ChatStore.state.activeAlunoNome) {
                        ChatUI.updateAlunoBadge(ChatStore.state.activeAlunoNome);
                    } else {
                        ChatUI.hideAlunoContext();
                    }
                }
            });
        }
        if (ChatUI.elements.btnCloseAlunoSearch) {
            ChatUI.elements.btnCloseAlunoSearch.addEventListener('click', function() {
                ChatUI.hideAlunoSearchResults();
                ChatUI.elements.alunoSearchInput.value = '';
                if (ChatStore.state.activeAlunoNome) {
                    ChatUI.updateAlunoBadge(ChatStore.state.activeAlunoNome);
                } else {
                    ChatUI.hideAlunoContext();
                }
            });
        }
        document.addEventListener('click', function(e) {
            var searchResults = ChatUI.elements.alunoSearchResults;
            var searchInput = ChatUI.elements.alunoSearchInput;
            if (searchResults && !searchResults.contains(e.target) && e.target !== searchInput) {
                ChatUI.hideAlunoSearchResults();
            }
        });
    }
}

function handleNewConversation() {
  ChatStore.state.activeConversationId = null;
  ChatStore.state.activeAlunoId = null;
  ChatStore.state.activeAlunoNome = null;
  ChatStore.save();
  anexosPendentes = [];
  ChatUI.renderAnexosChips(anexosPendentes);
  var discNome = ChatStore.state.activeDisciplinaDescricao;
  ChatUI.updateTitle(discNome || 'Nova conversa');
  if (discNome) {
    ChatUI.showDisciplinaBadge(discNome, ChatStore.state.activeDisciplinaSigla || '');
  } else {
    ChatUI.hideDisciplinaBadge();
  }
  ChatUI.renderMessages([]);
  renderSidebar(null);
  ChatUI.renderAnexosConversa([]);
  ChatUI.closeSidebar();
  syncAlunoBadge();
  if (ChatUI.elements.messageInput) ChatUI.elements.messageInput.focus();
}

  async function handleSendMessage() {
    var input = ChatUI.elements.messageInput;
    if (!input) return;
    var content = input.value.trim();
    if (!content) return;

    if (isProfessorChat && !ChatStore.state.activeDisciplinaId) {
      ChatUI.showToast('Selecione uma disciplina antes de enviar a mensagem.', 'warning');
      return;
    }

    try {
      input.disabled = true;
      ChatUI.elements.btnSend.disabled = true;

      if (typeof ChatUI.removeLoadingMessage === 'function') ChatUI.removeLoadingMessage();
      ChatUI.appendMessage({ role: 'user', content: content, created_at: new Date().toISOString() });
      ChatUI.clearInput();

      var textEl = ChatUI.createStreamingMessage();

            var anexosIds = anexosPendentes.map(function(a) { return a.id; });
      anexosPendentes = [];
      ChatUI.renderAnexosChips(anexosPendentes);

      await ChatService.sendMessageStream(content, ChatStore.state.activeAlunoId, ChatStore.state.activeDisciplinaId, {
        onChunk: function(chunk, fullContent) {
          ChatUI.appendChunk(textEl, chunk);
        },
        onDone: async function(result) {
          ChatUI.removeTypingIndicator();

          if (result.conversationId) {
            var existingConv = ChatStore.state.conversations.find(function(c) { return c.id === result.conversationId; });
            if (!existingConv) {
              var newConv = {
                id: result.conversationId,
                title: content.substring(0, 50) + (content.length > 50 ? '...' : ''),
                messages: [],
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
                aluno_id: result.alunoId || ChatStore.state.activeAlunoId,
                aluno_nome: result.alunoNome || ChatStore.state.activeAlunoNome,
                disciplina_id: ChatStore.state.activeDisciplinaId
              };
              ChatStore.state.conversations.unshift(newConv);
            } else {
              existingConv.updated_at = new Date().toISOString();
            }
            ChatStore.state.activeConversationId = result.conversationId;
            ChatStore.save();
          }

          ChatStore.addMessage('user', content);

          var assistantContent = result.assistantMessage ? result.assistantMessage.content : '';
          ChatStore.addMessage('assistant', assistantContent);

          ChatUI.finalizeStreamMessage(textEl, assistantContent);

          if (result.alunoId && !ChatStore.state.activeAlunoId) {
            ChatStore.state.activeAlunoId = result.alunoId;
            ChatStore.state.activeAlunoNome = result.alunoNome;
          }

          var activeConv = ChatService.getActiveConversation();
          if (activeConv) {
            ChatUI.updateTitle(activeConv.title);
            renderSidebar(activeConv.id);
          }
          await atualizarAnexosConversa();
        },
        onError: function(errorContent, fullContent) {
          ChatUI.appendChunk(textEl, errorContent);
        }
      }, anexosIds);
    } catch (error) {
      ChatUI.removeTypingIndicator();

      var streamingMsg = document.getElementById('streaming-message');
      var textoParcialEl = streamingMsg ? streamingMsg.querySelector('.message-text') : null;
      var conteudoParcial = textoParcialEl ? textoParcialEl.textContent.trim() : '';

      if (conteudoParcial) {
        ChatUI.finalizeStreamMessage(textoParcialEl, conteudoParcial + '\n\n*[resposta interrompida — tente enviar novamente]*');
        ChatUI.showToast('A resposta foi interrompida.', 'warning');
      } else {
        ChatUI.removeStreamingMessage();
        if (error.name === 'AbortError') {
          ChatUI.showToast('A resposta demorou demais e foi cancelada. Tente novamente.', 'error');
        } else {
          ChatUI.showToast('Erro ao enviar: ' + error.message, 'error');
        }
      }

      anexosPendentes = [];
      ChatUI.renderAnexosChips(anexosPendentes);
    } finally {
      input.disabled = false;
      input.focus();
      ChatUI.updateSendButton();
    }
  }

  function handleInput(e) {
    var input = ChatUI.elements.messageInput;
    if (input) {
      input.style.height = 'auto';
      input.style.height = Math.min(input.scrollHeight, 200) + 'px';
    }
    ChatUI.updateSendButton();
  }

  function handleKeydown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!ChatUI.elements.btnSend.disabled) handleSendMessage();
    }
  }

async function handleConversationSelect(id) {
var conversation = ChatStore.setActiveConversation(id);
if (conversation) {
ChatUI.updateTitle(conversation.title);
ChatUI.showLoadingMessages();
  try {
    var fullConversa = await ChatService.loadConversationHistory(id);
    if (fullConversa) {
      conversation.messages = fullConversa.messages || [];
      conversation.title = fullConversa.title || conversation.title;
      if (fullConversa.aluno_id) {
        conversation.aluno_id = fullConversa.aluno_id;
        conversation.aluno_nome = fullConversa.aluno_nome || null;
        ChatStore.state.activeAlunoId = fullConversa.aluno_id;
        ChatStore.state.activeAlunoNome = fullConversa.aluno_nome || null;
      } else {
        conversation.aluno_id = null;
        conversation.aluno_nome = null;
        ChatStore.state.activeAlunoId = null;
        ChatStore.state.activeAlunoNome = null;
      }
      conversation.disciplina_id = fullConversa.disciplina_id || null;
      conversation.disciplina_descricao = fullConversa.disciplina_descricao || null;
      conversation.disciplina_sigla = fullConversa.disciplina_sigla || null;
      ChatStore.save();
      ChatUI.updateTitle(conversation.title);
      ChatUI.renderMessages(conversation.messages);
    } else {
      ChatUI.renderMessages(conversation.messages);
    }
  } catch (e) {
    console.error('Erro ao carregar histórico:', e);
    ChatUI.renderMessages(conversation.messages);
  }
  renderSidebar(conversation.id);
  ChatUI.closeSidebar();
  syncAlunoBadge();
  syncDisciplinaFromConversation(conversation);
  await atualizarAnexosConversa();
if (!isNapne && conversation.disciplina_descricao) {
ChatUI.showDisciplinaBadge(conversation.disciplina_descricao, conversation.disciplina_sigla);
} else {
ChatUI.hideDisciplinaBadge();
}
}
}

    async function handleConversationDelete(id) {
        if (!confirm('Tem certeza que deseja excluir esta conversa?')) return;

        var ok = await ChatService.deleteConversation(id);
        if (!ok) {
            ChatUI.showToast('Nao foi possivel excluir a conversa. Tente novamente.');
            return;
        }
        ChatStore.state.conversations = ChatStore.state.conversations.filter(function(c) {
            return c.id !== id;
        });

        if (ChatStore.state.activeConversationId === id) {
            ChatStore.state.activeConversationId = null;
        }

        ChatStore.save();

        var activeConv = ChatService.getActiveConversation();
        if (activeConv) {
            ChatUI.updateTitle(activeConv.title);
            ChatUI.renderMessages(activeConv.messages);
        } else {
            ChatUI.updateTitle('Nova Conversa');
            ChatUI.renderMessages([]);
        }
        renderSidebar(activeConv ? activeConv.id : null);
    }

    async function handleConversationRename(id, currentTitle) {
      var novo = prompt('Novo nome da conversa:', currentTitle || '');
      if (novo === null) return;
      novo = novo.trim();
      if (!novo) {
        ChatUI.showToast('O nome da conversa nao pode ser vazio.', 'warning');
        return;
      }
      var resp = await ChatService.renomearConversa(id, novo);
      if (!resp) {
        ChatUI.showToast('Nao foi possivel renomear a conversa. Tente novamente.');
        return;
      }
      var conv = ChatStore.state.conversations.find(function(c) { return c.id === id; });
      if (conv) {
        conv.title = resp.title || novo;
        ChatStore.save();
      }
      if (ChatStore.state.activeConversationId === id) {
        ChatUI.updateTitle(conv ? conv.title : novo);
      }
      renderSidebar(ChatStore.state.activeConversationId);
    }

function handleTitleRename() {
  var conv = ChatStore.getActiveConversation();
  if (!conv) {
    ChatUI.showToast('Abra uma conversa para renomear.', 'warning');
    return;
  }
  handleConversationRename(conv.id, conv.title || '');
}

async function handleAnexoUpload(file) {
  if (!file) return;
  var maxSize = 10 * 1024 * 1024;
  if (file.size > maxSize) {
    ChatUI.showToast('Arquivo muito grande. Tamanho maximo: 10MB', 'error');
    return;
  }
  var allowedExts = ['pdf', 'txt', 'docx', 'pptx', 'png', 'jpg', 'jpeg'];
  var ext = (file.name || '').split('.').pop().toLowerCase();
  if (allowedExts.indexOf(ext) === -1) {
    ChatUI.showToast('Tipo de arquivo nao permitido', 'error');
    return;
  }

  var resp = await ChatService.uploadAnexo(file);
  if (!resp || !resp.id) {
    ChatUI.showToast('Erro ao anexar o arquivo. Tente novamente.', 'error');
    return;
  }

  anexosPendentes.push({ id: resp.id, nome: resp.nome_original || file.name });
  ChatUI.renderAnexosChips(anexosPendentes);
  ChatUI.showToast('Arquivo "' + (resp.nome_original || file.name) + '" anexado.', 'success');
}

async function handleAnexoRemoved(anexoId) {
  anexosPendentes = anexosPendentes.filter(function(a) { return a.id !== anexoId; });
  ChatUI.renderAnexosChips(anexosPendentes);
  await ChatService.removerAnexo(anexoId);
}

async function handleAnexoConversaRemoved(anexoId) {
  var ok = await ChatService.removerAnexo(anexoId);
  if (ok) {
    ChatUI.showToast('Arquivo removido do contexto da conversa.', 'success');
  } else {
    ChatUI.showToast('Erro ao remover o arquivo.', 'error');
  }
  await atualizarAnexosConversa();
}

async function atualizarAnexosConversa() {
  var convId = ChatStore.state.activeConversationId;
  if (!convId) {
    ChatUI.renderAnexosConversa([]);
    return;
  }
  var anexos = await ChatService.listarAnexosConversa(convId);
  ChatUI.renderAnexosConversa(anexos);
}

function handleLogout() {
if (confirm('Deseja realmente sair?')) {
acolheLogout();
}
}

async function handleAlunoSelected(alunoId, alunoNome) {
  var conversationId = ChatStore.state.activeConversationId;
  if (!conversationId) {
    ChatUI.showToast('Selecione uma conversa primeiro', 'warning');
    return;
  }

  try {
    var response = await ChatService.vincularAluno(conversationId, alunoId);
    if (response) {
      ChatStore.setAlunoContext(alunoId, alunoNome);
      ChatUI.updateAlunoBadge(alunoNome);
      ChatUI.hideAlunoSearchResults();
      
      var conversation = ChatStore.getActiveConversation();
      if (conversation) {
        conversation.aluno_id = alunoId;
        conversation.aluno_nome = alunoNome;
        ChatStore.save();
      }
    } else {
      ChatUI.showToast('Erro ao vincular aluno');
    }
  } catch (error) {
    console.error('Erro ao vincular aluno:', error);
    ChatUI.showToast('Erro ao vincular aluno');
  }
}

async function handleRemoveAluno() {
  var conversationId = ChatStore.state.activeConversationId;
  if (!conversationId) {
    return;
  }

  try {
    var response = await ChatService.desvincularAluno(conversationId);
    if (response) {
      ChatStore.clearAlunoContext();
      ChatUI.hideAlunoContext();
      
      var conversation = ChatStore.getActiveConversation();
      if (conversation) {
        conversation.aluno_id = null;
        conversation.aluno_nome = null;
        ChatStore.save();
      }
    } else {
      ChatUI.showToast('Erro ao desvincular aluno');
    }
  } catch (error) {
    console.error('Erro ao desvincular aluno:', error);
    ChatUI.showToast('Erro ao desvincular aluno');
  }
}

function handleAlunoSearchInput(e) {
var query = e.target.value;
clearTimeout(alunoSearchTimer);
if (!query || query.trim().length < 2) {
ChatUI.hideAlunoSearchResults();
return;
}
alunoSearchTimer = setTimeout(async function() {
var results = await ChatService.searchAlunos(query);
ChatUI.renderAlunoSearchResults(results);
}, 300);
}

    function syncAlunoBadge() {
        if (isAluno) return;
        var nome = ChatStore.state.activeAlunoNome;
if (nome) {
ChatUI.updateAlunoBadge(nome);
} else {
ChatUI.hideAlunoContext();
}
}

function renderSidebar(activeId) {
  ChatUI.renderSidebar(activeId);
}

function syncDisciplinaFromConversation(conversation) {
  if (isNapne) {
    ChatStore.clearDisciplinaContext();
    return;
  }
  if (conversation && conversation.disciplina_id) {
    ChatStore.setDisciplinaContext(
      conversation.disciplina_id,
      conversation.disciplina_descricao || null,
      conversation.disciplina_sigla || null
    );
  } else {
    ChatStore.clearDisciplinaContext();
  }
}

async function renderInitialState() {
await ChatService.loadConversations();
ChatUI.updateTitle('Nova Conversa');
ChatUI.renderMessages([]);
renderSidebar(null);
syncAlunoBadge();
}

document.addEventListener('DOMContentLoaded', init);
})();
