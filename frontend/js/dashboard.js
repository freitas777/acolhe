(function() {
  'use strict';

  var suap = new SuapClient(SUAP_URL, CLIENT_ID, REDIRECT_URI, SCOPE);
  suap.init();

  if (!suap.isAuthenticated()) {
    window.location.href = '/';
    return;
  }

  var currentUser = null;

  async function init() {
    ChatStore.init();
    ChatUI.init();
    await loadUserData();
    setupEventListeners();
    renderInitialState();
  }

  async function loadUserData() {
    var savedUser = localStorage.getItem('acolhe_user');
    if (savedUser) {
      currentUser = JSON.parse(savedUser);
    }
    if (!currentUser && suap.isAuthenticated()) {
      try {
        await new Promise(function(resolve, reject) {
          suap.getResource(suap.getToken().getScope(), function(response) {
            if (response) {
              currentUser = response;
              localStorage.setItem('acolhe_user', JSON.stringify(response));
              resolve();
            } else {
              reject(new Error('Falha ao carregar dados'));
            }
          });
        });
      } catch (error) {
        console.error('Erro ao carregar dados do usuario:', error);
      }
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
    if (ChatUI.elements.btnDeleteConversation) {
      ChatUI.elements.btnDeleteConversation.addEventListener('click', handleDeleteConversation);
    }
    if (ChatUI.elements.btnLogout) {
      ChatUI.elements.btnLogout.addEventListener('click', handleLogout);
    }
    ChatUI.onConversationSelect = handleConversationSelect;
    ChatUI.onConversationDelete = handleConversationDelete;
  }

  function handleNewConversation() {
    var conversation = ChatService.createNewConversation();
    ChatUI.updateTitle(conversation.title);
    ChatUI.renderMessages([]);
    ChatUI.renderConversations(ChatService.getConversationsHistory(), conversation.id);
    ChatUI.closeSidebar();
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
      ChatUI.showTypingIndicator();

      var result = await ChatService.sendMessage(content);
      if (result.success) {
        ChatUI.removeTypingIndicator();
        ChatUI.appendMessage(result.message);
        if (result.assistantMessage) {
          await new Promise(function(resolve) { setTimeout(resolve, 500); });
          ChatUI.appendMessage(result.assistantMessage);
        }
        ChatUI.clearInput();
        var activeConv = ChatService.getActiveConversation();
        if (activeConv) {
          ChatUI.updateTitle(activeConv.title);
          ChatUI.renderConversations(ChatService.getConversationsHistory(), activeConv.id);
        }
      }
    } catch (error) {
      console.error('Erro ao enviar mensagem:', error);
      ChatUI.removeTypingIndicator();
      ChatUI.showError('Erro ao enviar: ' + error.message);
    } finally {
      input.disabled = false;
      input.focus();
      ChatUI.updateSendButton();
    }
  }

  function handleInput(e) {
    ChatUI.updateSendButton();
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 200) + 'px';
  }

  function handleKeydown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!ChatUI.elements.btnSend.disabled) handleSendMessage();
    }
  }

  function handleConversationSelect(id) {
    var conversation = ChatService.selectConversation(id);
    if (conversation) {
      ChatUI.updateTitle(conversation.title);
      ChatUI.renderMessages(conversation.messages);
      ChatUI.renderConversations(ChatService.getConversationsHistory(), conversation.id);
      ChatUI.closeSidebar();
    }
  }

  function handleConversationDelete(id) {
    if (confirm('Tem certeza que deseja excluir esta conversa?')) {
      ChatService.deleteConversation(id);
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

  function handleDeleteConversation() {
    var activeConv = ChatService.getActiveConversation();
    if (!activeConv) {
      alert('Nenhuma conversa selecionada');
      return;
    }
    handleConversationDelete(activeConv.id);
  }

  function handleLogout() {
    if (confirm('Deseja realmente sair?')) {
      suap.logout();
      localStorage.removeItem('acolhe_access_token');
      localStorage.removeItem('acolhe_user');
      localStorage.removeItem('acolhe_user_id');
      window.location.href = '/';
    }
  }

  function renderInitialState() {
    var conversations = ChatService.getConversationsHistory();
    var activeConv = ChatService.getActiveConversation();
    if (activeConv) {
      ChatUI.updateTitle(activeConv.title);
      ChatUI.renderMessages(activeConv.messages);
    } else if (conversations.length > 0) {
      handleConversationSelect(conversations[0].id);
    } else {
      ChatUI.updateTitle('Nova Conversa');
      ChatUI.renderMessages([]);
    }
    ChatUI.renderConversations(conversations, activeConv ? activeConv.id : null);
  }

  document.addEventListener('DOMContentLoaded', init);
})();
