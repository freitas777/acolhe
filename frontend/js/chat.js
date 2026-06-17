(function() {
'use strict';

    if (!acolheRequireAuth()) return;

    var currentUser = null;
    var alunoSearchTimer = null;
    var isAluno = (localStorage.getItem('acolhe_tipo_perfil') || 'aluno') === 'aluno';

    if (isAluno) document.body.classList.add('role-aluno');

    async function init() {
        ChatStore.init();
        ChatUI.init();
        applyRoleVisibility();
        await loadUserData();
        setupEventListeners();
        await renderInitialState();
    }

function applyRoleVisibility() {
if (isAluno) {
if (ChatUI.elements.btnAlunoContext) ChatUI.elements.btnAlunoContext.hidden = true;
if (ChatUI.elements.alunoContextBar) ChatUI.elements.alunoContextBar.hidden = true;
}

var perfil = localStorage.getItem('acolhe_tipo_perfil') || 'aluno';
var isNapne = perfil === 'psicopedagogo' || perfil === 'admin' || perfil === 'servidor';
var navPainel = document.getElementById('nav-painel');
var navPortal = document.getElementById('nav-portal');
var navDisciplinas = document.getElementById('nav-disciplinas');

if (navPainel) navPainel.style.display = isNapne ? '' : 'none';
if (navPortal) navPortal.style.display = isAluno ? '' : 'none';
if (navDisciplinas) navDisciplinas.style.display = isAluno || perfil === 'professor' ? '' : 'none';
}

async function loadUserData() {
    var savedUser = localStorage.getItem('acolhe_user');
    if (savedUser) {
        try { currentUser = JSON.parse(savedUser); } catch(e) {}
    }
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
        document.addEventListener('click', function(e) {
            var searchResults = ChatUI.elements.alunoSearchResults;
            var searchInput = ChatUI.elements.alunoSearchInput;
            if (searchResults && !searchResults.contains(e.target) && e.target !== searchInput) {
                ChatUI.hideAlunoSearchResults();
            }
        });
    }
}

async function handleNewConversation() {
var alunoId = ChatStore.state.activeAlunoId || null;
var alunoNome = ChatStore.state.activeAlunoNome || null;
var conversation = await ChatService.createNewConversation(alunoId);
if (conversation && conversation.id) {
var localConv = {
id: conversation.id,
title: conversation.title || 'Nova conversa',
messages: [],
created_at: conversation.created_at || new Date().toISOString(),
aluno_id: conversation.aluno_id || alunoId,
aluno_nome: conversation.aluno_nome || alunoNome
};
ChatStore.state.conversations.unshift(localConv);
ChatStore.state.activeConversationId = localConv.id;
ChatStore.state.activeAlunoId = localConv.aluno_id || null;
ChatStore.state.activeAlunoNome = localConv.aluno_nome || null;
ChatStore.save();
ChatUI.updateTitle(localConv.title);
ChatUI.renderMessages([]);
ChatUI.renderConversations(ChatStore.getAllConversations(), localConv.id);
} else {
var localConv = ChatStore.createConversation('Nova conversa', alunoId, alunoNome);
ChatUI.updateTitle(localConv.title);
ChatUI.renderMessages([]);
ChatUI.renderConversations(ChatStore.getAllConversations(), localConv.id);
}
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

      ChatUI.appendMessage({ role: 'user', content: content, created_at: new Date().toISOString() });
      ChatUI.clearInput();

      var textEl = ChatUI.createStreamingMessage();

      await ChatService.sendMessageStream(content, ChatStore.state.activeAlunoId, {
        onChunk: function(chunk, fullContent) {
          ChatUI.appendChunk(textEl, chunk);
        },
        onDone: function(result) {
          ChatUI.removeTypingIndicator();

          if (result.conversationId && !ChatStore.state.activeConversationId) {
            ChatStore.state.activeConversationId = result.conversationId;
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

function handleConversationSelect(id) {
var conversation = ChatStore.setActiveConversation(id);
if (conversation) {
ChatUI.updateTitle(conversation.title);
ChatUI.renderMessages(conversation.messages);
ChatUI.renderConversations(ChatService.getConversationsHistory(), conversation.id);
ChatUI.closeSidebar();
syncAlunoBadge();
}
}

    async function handleConversationDelete(id) {
        if (confirm('Tem certeza que deseja excluir esta conversa?')) {
            await ChatService.deleteConversation(id);
            var activeConv = ChatService.getActiveConversation();
            if (activeConv) {
                ChatUI.updateTitle(activeConv.title);
                ChatUI.renderMessages(activeConv.messages);
            } else {
                ChatUI.updateTitle('Nova Conversa');
                ChatUI.renderMessages([]);
            }
            ChatUI.renderConversations(ChatService.getConversationsHistory(), activeConv ? activeConv.id : null);
        }
    }

function handleLogout() {
if (confirm('Deseja realmente sair?')) {
acolheLogout();
}
}

function handleAlunoSelected(alunoId, alunoNome) {
ChatStore.setAlunoContext(alunoId, alunoNome);
ChatUI.updateAlunoBadge(alunoNome);
ChatUI.hideAlunoSearchResults();
}

function handleRemoveAluno() {
ChatStore.clearAlunoContext();
ChatUI.hideAlunoContext();
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
