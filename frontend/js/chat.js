(function() {
'use strict';

    if (!acolheRequireAuth()) return;

    var currentUser = null;
    var alunoSearchTimer = null;
    var isAluno = acolheGetTipoPerfil() === 'aluno';
    var isProfessorChat = acolheGetTipoPerfil() === 'professor';
    var disciplinasCache = [];

    if (isAluno) document.body.classList.add('role-aluno');

    var pendingDisciplina = null;
    var pendingAluno = null;
    var ementaPendente = null;

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
      if (isProfessorChat) ChatUI.selectDisciplina(disciplinaId);
      ChatUI.showDisciplinaBadge(disciplinaDescricao, sigla);
      ChatUI.updateTitle('Nova Conversa');
      ChatUI.renderMessages([]);
      ChatUI.renderConversations(ChatStore.getAllConversations(), null);
      ChatUI.closeSidebar();
      if (ChatUI.elements.messageInput) ChatUI.elements.messageInput.focus();
    }

    function openAlunoContext(alunoData) {
      ChatStore.setAlunoContext(alunoData.aluno_id, alunoData.aluno_nome);
      ChatUI.updateAlunoBadge(alunoData.aluno_nome);
      ChatUI.updateTitle('Nova Conversa');
      ChatUI.renderMessages([]);
      ChatUI.renderConversations(ChatStore.getAllConversations(), null);
      ChatUI.closeSidebar();
      if (ChatUI.elements.messageInput) ChatUI.elements.messageInput.focus();
    }

  async function init() {
        ChatStore.init();
        ChatUI.init();
        applyRoleVisibility();
        await loadUserData();
        if (isProfessorChat) {
          ChatUI.showDisciplinaSelector();
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
  ChatUI.populateDisciplinas(disciplinasCache);
}

async function handleDisciplinaChange(e) {
  var id = parseInt(e.target.value, 10);
  if (!id) {
    ChatStore.clearDisciplinaContext();
    ChatUI.resetDisciplinaSelect();
    return;
  }
  var descricao = '';
  for (var i = 0; i < disciplinasCache.length; i++) {
    if (disciplinasCache[i].id === id) {
      descricao = disciplinasCache[i].descricao || '';
      break;
    }
  }
  await openDisciplinaContext({ disciplina_id: id, disciplina_descricao: descricao });
}

async function handleEmentaSave() {
  var fileInput = ChatUI.elements.ementaFileInput;
  var file = fileInput && fileInput.files && fileInput.files[0];
  if (!file) {
    ChatUI.showError('Selecione o arquivo da ementa.');
    return;
  }
  if (!ementaPendente) {
    ChatUI.closeEmentaModal();
    return;
  }
  var id = ementaPendente.disciplina_id;
  var resp = await ChatService.salvarEmenta(id, file);
  if (!resp) {
    ChatUI.showError('Erro ao enviar a ementa. Tente novamente.');
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

if (navPainel) navPainel.style.display = isNapne ? '' : 'none';
if (navNotificacoes) navNotificacoes.style.display = isNapne ? '' : 'none';
if (navPortal) navPortal.style.display = isAluno ? '' : 'none';
if (navDisciplinas) navDisciplinas.style.display = isAluno || perfil === 'professor' ? '' : 'none';
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
    if (ChatUI.elements.disciplinaSelect) {
      ChatUI.elements.disciplinaSelect.addEventListener('change', handleDisciplinaChange);
    }
    if (ChatUI.elements.ementaSave) {
      ChatUI.elements.ementaSave.addEventListener('click', handleEmentaSave);
    }
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
    ChatUI.onConversationRename = handleConversationRename;

    document.addEventListener('click', function(e) {
      if (!e.target.closest('.conversation-menu') && !e.target.closest('.conversation-more-btn')) {
        ChatUI.closeConversationMenus();
      }
    });
    if (ChatUI.elements.conversationsList) {
      ChatUI.elements.conversationsList.addEventListener('scroll', function() {
        ChatUI.closeConversationMenus();
      });
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
  ChatStore.clearDisciplinaContext();
  ChatUI.updateTitle('Nova conversa');
  ChatUI.renderMessages([]);
  ChatUI.renderConversations(ChatStore.getAllConversations(), null);
  ChatUI.hideDisciplinaBadge();
  ChatUI.closeSidebar();
  syncAlunoBadge();
  if (isProfessorChat) ChatUI.resetDisciplinaSelect();
  if (ChatUI.elements.messageInput) ChatUI.elements.messageInput.focus();
}

  async function handleSendMessage() {
    var input = ChatUI.elements.messageInput;
    if (!input) return;
    var content = input.value.trim();
    if (!content) return;

    if (isProfessorChat && !ChatStore.state.activeDisciplinaId) {
      ChatUI.showError('Selecione uma disciplina antes de enviar a mensagem.');
      return;
    }

    try {
      input.disabled = true;
      ChatUI.elements.btnSend.disabled = true;

      if (typeof ChatUI.removeLoadingMessage === 'function') ChatUI.removeLoadingMessage();
      ChatUI.appendMessage({ role: 'user', content: content, created_at: new Date().toISOString() });
      ChatUI.clearInput();

      var textEl = ChatUI.createStreamingMessage();

      await ChatService.sendMessageStream(content, ChatStore.state.activeAlunoId, ChatStore.state.activeDisciplinaId, {
        onChunk: function(chunk, fullContent) {
          ChatUI.appendChunk(textEl, chunk);
        },
        onDone: function(result) {
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
                aluno_nome: result.alunoNome || ChatStore.state.activeAlunoNome
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
            ChatUI.renderConversations(ChatService.getConversationsHistory(), activeConv.id);
          }
        },
        onError: function(errorContent, fullContent) {
          ChatUI.appendChunk(textEl, errorContent);
        }
      });
    } catch (error) {
      ChatUI.removeTypingIndicator();
      ChatUI.removeStreamingMessage();
      ChatUI.showError('Erro ao enviar: ' + error.message);
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
  ChatUI.renderConversations(ChatService.getConversationsHistory(), conversation.id);
  ChatUI.closeSidebar();
  syncAlunoBadge();
  syncDisciplinaFromConversation(conversation);
if (conversation.disciplina_descricao) {
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
            ChatUI.showError('Nao foi possivel excluir a conversa. Tente novamente.');
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
        ChatUI.renderConversations(ChatStore.getAllConversations(), activeConv ? activeConv.id : null);
    }

    async function handleConversationRename(id, currentTitle) {
      var novo = prompt('Novo nome da conversa:', currentTitle || '');
      if (novo === null) return;
      novo = novo.trim();
      if (!novo) {
        ChatUI.showError('O nome da conversa nao pode ser vazio.');
        return;
      }
      var resp = await ChatService.renomearConversa(id, novo);
      if (!resp) {
        ChatUI.showError('Nao foi possivel renomear a conversa. Tente novamente.');
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
      ChatUI.renderConversations(ChatStore.getAllConversations(), ChatStore.state.activeConversationId);
    }

function handleLogout() {
if (confirm('Deseja realmente sair?')) {
acolheLogout();
}
}

async function handleAlunoSelected(alunoId, alunoNome) {
  var conversationId = ChatStore.state.activeConversationId;
  if (!conversationId) {
    ChatUI.showError('Selecione uma conversa primeiro');
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
      ChatUI.showError('Erro ao vincular aluno');
    }
  } catch (error) {
    console.error('Erro ao vincular aluno:', error);
    ChatUI.showError('Erro ao vincular aluno');
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
      ChatUI.showError('Erro ao desvincular aluno');
    }
  } catch (error) {
    console.error('Erro ao desvincular aluno:', error);
    ChatUI.showError('Erro ao desvincular aluno');
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

function syncDisciplinaFromConversation(conversation) {
  if (conversation && conversation.disciplina_id) {
    ChatStore.setDisciplinaContext(
      conversation.disciplina_id,
      conversation.disciplina_descricao || null,
      conversation.disciplina_sigla || null
    );
    if (isProfessorChat) ChatUI.selectDisciplina(conversation.disciplina_id);
  } else {
    ChatStore.clearDisciplinaContext();
    if (isProfessorChat) ChatUI.resetDisciplinaSelect();
  }
}

async function renderInitialState() {
await ChatService.loadConversations();
ChatUI.updateTitle('Nova Conversa');
ChatUI.renderMessages([]);
ChatUI.renderConversations(ChatStore.getAllConversations(), null);
syncAlunoBadge();
}

document.addEventListener('DOMContentLoaded', init);
})();
