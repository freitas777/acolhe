(function() {
'use strict';

    if (!acolheRequireAuth()) return;

    var currentUser = null;
    var alunoSearchTimer = null;
    var isAluno = acolheGetTipoPerfil() === 'aluno';

    if (isAluno) document.body.classList.add('role-aluno');

    var pendingDisciplina = null;
    var pendingInitialMessage = null;

    async function handlePendingDisciplina() {
      var raw = null;
      try { raw = sessionStorage.getItem('acolhe_open_conversa'); } catch (e) {}
      if (!raw) return false;
      try {
        var data = JSON.parse(raw);
        if (data && data.tipo === 'disciplina' && data.disciplina_id) {
          pendingDisciplina = data;
          pendingInitialMessage = data.mensagem_inicial || null;
          try { sessionStorage.removeItem('acolhe_open_conversa'); } catch (e) {}
          return true;
        }
      } catch (e) {}
      try { sessionStorage.removeItem('acolhe_open_conversa'); } catch (e) {}
      return false;
    }

    async function openDisciplinaConversa() {
      var conversa = await ChatService.getOrCreateConversaByDisciplina(pendingDisciplina.disciplina_id);
      if (!conversa || !conversa.id) {
        ChatUI.showError('Não foi possível abrir a conversa da disciplina');
        return;
      }

      var localConv = {
        id: conversa.id,
        title: conversa.title || ('Conversa sobre ' + (pendingDisciplina.disciplina_descricao || '')),
        messages: conversa.messages || [],
        created_at: conversa.created_at || new Date().toISOString(),
        aluno_id: conversa.aluno_id || null,
        aluno_nome: conversa.aluno_nome || null,
        disciplina_id: conversa.disciplina_id || pendingDisciplina.disciplina_id,
        disciplina_descricao: conversa.disciplina_descricao || pendingDisciplina.disciplina_descricao,
        disciplina_sigla: conversa.disciplina_sigla || null
      };

      var exists = ChatStore.state.conversations.find(function(c) { return c.id === localConv.id; });
      if (!exists) {
        ChatStore.state.conversations.unshift(localConv);
      } else {
        Object.assign(exists, localConv);
      }
      ChatStore.state.activeConversationId = localConv.id;
      ChatStore.save();

      ChatUI.updateTitle(localConv.title);
      ChatUI.renderMessages(localConv.messages);
      ChatUI.renderConversations(ChatStore.getAllConversations(), localConv.id);
      ChatUI.showDisciplinaBadge(localConv.disciplina_descricao, localConv.disciplina_sigla);
      ChatUI.closeSidebar();

      if (pendingInitialMessage && localConv.messages.length === 0) {
        if (ChatUI.elements.messageInput) {
          ChatUI.elements.messageInput.value = pendingInitialMessage;
        }
        pendingInitialMessage = null;
        if (ChatUI.elements.btnSend && !ChatUI.elements.btnSend.disabled) {
          handleSendMessage();
        } else {
          try { ChatUI.updateSendButton(); } catch (e) {}
          setTimeout(function() {
            if (ChatUI.elements.btnSend && !ChatUI.elements.btnSend.disabled) {
              handleSendMessage();
            }
          }, 100);
        }
      } else if (localConv.disciplina_descricao) {
        ChatUI.showDisciplinaBadge(localConv.disciplina_descricao, localConv.disciplina_sigla);
      }
    }

  async function init() {
        ChatStore.init();
        ChatUI.init();
        applyRoleVisibility();
        await loadUserData();
        setupEventListeners();
        var hasDisciplina = await handlePendingDisciplina();
        if (hasDisciplina && pendingDisciplina) {
          try { await ChatService.loadConversations(); } catch (e) {}
          await openDisciplinaConversa();
        } else {
          await renderInitialState();
        }
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
if (navPortal) navPortal.style.display = isAluno || perfil === 'professor' ? '' : 'none';
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
  ChatUI.updateTitle('Nova conversa');
  ChatUI.renderMessages([]);
  ChatUI.renderConversations(ChatStore.getAllConversations(), null);
  ChatUI.hideDisciplinaBadge();
  ChatUI.closeSidebar();
  syncAlunoBadge();
  if (ChatUI.elements.messageInput) ChatUI.elements.messageInput.focus();
}

  async function handleSendMessage() {
    var input = ChatUI.elements.messageInput;
    if (!input) return;
    var content = input.value.trim();
    if (!content) return;

    try {
      input.disabled = true;
      ChatUI.elements.btnSend.disabled = true;

      if (typeof ChatUI.removeLoadingMessage === 'function') ChatUI.removeLoadingMessage();
      ChatUI.appendMessage({ role: 'user', content: content, created_at: new Date().toISOString() });
      ChatUI.clearInput();

      var textEl = ChatUI.createStreamingMessage();

      await ChatService.sendMessageStream(content, ChatStore.state.activeAlunoId, {
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
      ChatStore.save();
      ChatUI.updateTitle(conversation.title);
      ChatUI.renderMessages(conversation.messages);
    } else {
      ChatUI.renderMessages(conversation.messages);
    }
  } catch (e) {
    console.error('Erro ao carregar histÃ³rico:', e);
    ChatUI.renderMessages(conversation.messages);
  }
  ChatUI.renderConversations(ChatService.getConversationsHistory(), conversation.id);
  ChatUI.closeSidebar();
  syncAlunoBadge();
if (conversation.disciplina_descricao) {
ChatUI.showDisciplinaBadge(conversation.disciplina_descricao, conversation.disciplina_sigla);
} else {
ChatUI.hideDisciplinaBadge();
}
}
}

    async function handleConversationDelete(id) {
        if (!confirm('Tem certeza que deseja excluir esta conversa?')) return;

        await ChatService.deleteConversation(id);

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

async function renderInitialState() {
var conversations = await ChatService.loadConversations();
var activeConv = ChatService.getActiveConversation();
if (activeConv) {
ChatUI.updateTitle(activeConv.title);
ChatUI.renderMessages(activeConv.messages);
} else if (conversations && conversations.length > 0) {
handleConversationSelect(conversations[0].id);
return;
} else {
ChatUI.updateTitle('Nova Conversa');
ChatUI.renderMessages([]);
}
ChatUI.renderConversations(conversations || [], activeConv ? activeConv.id : null);
syncAlunoBadge();
}

document.addEventListener('DOMContentLoaded', init);
})();
