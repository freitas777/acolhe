/**
 * Dashboard - Inicialização e Orquestração
 */

(function() {
  'use strict';

  // ========================================
  // Verifica Autenticação SUAP
  // ========================================
  const suap = new SuapClient(SUAP_URL, CLIENT_ID, REDIRECT_URI, SCOPE);
  suap.init();

  if (!suap.isAuthenticated()) {
    console.log('❌ Não autenticado, indo para login');
    window.location.href = '/';
    return;
  }

  console.log('✅ Usuário autenticado no SUAP');

  // ========================================
  // Estado da Aplicação
  // ========================================
  let currentUser = null;

  // ========================================
  // Inicialização
  // ========================================
  async function init() {
    console.log('🚀 Acolhe+ Dashboard - Inicializando...');

    // Inicializa módulos
    ChatStore.init();
    ChatUI.init();

    // Carrega dados do usuário
    await loadUserData();

    // Configura event listeners
    setupEventListeners();

    // Renderiza estado inicial
    renderInitialState();

    console.log('✅ Dashboard pronto');
  }

  // ========================================
  // Dados do Usuário
  // ========================================
  async function loadUserData() {
    // Tenta obter do localStorage primeiro
    const savedUser = localStorage.getItem('acolhe_user');
    if (savedUser) {
      currentUser = JSON.parse(savedUser);
    }

    // Se não tiver, busca do SUAP
    if (!currentUser && suap.isAuthenticated()) {
      try {
        await new Promise((resolve, reject) => {
          suap.getResource(suap.getToken().getScope(), (response) => {
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
        console.error('Erro ao carregar dados do usuário:', error);
      }
    }

    // Atualiza UI
    ChatUI.updateUserInfo(currentUser);
  }

  // ========================================
  // Event Listeners
  // ========================================
  function setupEventListeners() {
    // Nova conversa
    if (ChatUI.elements.btnNewChat) {
      ChatUI.elements.btnNewChat.addEventListener('click', handleNewConversation);
    }

    // Enviar mensagem
    if (ChatUI.elements.btnSend) {
      ChatUI.elements.btnSend.addEventListener('click', handleSendMessage);
    }

    // Input de mensagem
    if (ChatUI.elements.messageInput) {
      ChatUI.elements.messageInput.addEventListener('input', handleInput);
      ChatUI.elements.messageInput.addEventListener('keydown', handleKeydown);
    }

    // Menu mobile
    if (ChatUI.elements.btnMenuMobile) {
      ChatUI.elements.btnMenuMobile.addEventListener('click', () => {
        ChatUI.openSidebar();
      });
    }

    // Fechar sidebar ao clicar fora (mobile)
    document.addEventListener('click', (e) => {
      if (window.innerWidth <= 768) {
        const sidebar = ChatUI.elements.sidebar;
        const menuBtn = ChatUI.elements.btnMenuMobile;
        if (sidebar && !sidebar.contains(e.target) && !menuBtn.contains(e.target)) {
          ChatUI.closeSidebar();
        }
      }
    });

    // Deletar conversa
    if (ChatUI.elements.btnDeleteConversation) {
      ChatUI.elements.btnDeleteConversation.addEventListener('click', handleDeleteConversation);
    }

    // Logout
    if (ChatUI.elements.btnLogout) {
      ChatUI.elements.btnLogout.addEventListener('click', handleLogout);
    }

    // Atualiza handlers do ChatUI
    ChatUI.onConversationSelect = handleConversationSelect;
    ChatUI.onConversationDelete = handleConversationDelete;
  }

  // ========================================
  // Handlers
  // ========================================
  function handleNewConversation() {
    const conversation = ChatService.createNewConversation();
    ChatUI.updateTitle(conversation.title);
    ChatUI.renderMessages([]);
    ChatUI.renderConversations(
      ChatService.getConversationsHistory(),
      conversation.id
    );
    ChatUI.closeSidebar();
    
    // Foca no input
    if (ChatUI.elements.messageInput) {
      ChatUI.elements.messageInput.focus();
    }
  }

    async function handleSendMessage() {
    const input = ChatUI.elements.messageInput;
    if (!input) return;

    const content = input.value.trim();
    if (!content) return;

    try {
      // Desabilita input enquanto processa
      input.disabled = true;
      ChatUI.elements.btnSend.disabled = true;

      // Mostra indicador de digitando
      ChatUI.showTypingIndicator();

      // Envia mensagem
      const result = await ChatService.sendMessage(content);
      
      if (result.success) {
        // Remove typing indicator
        ChatUI.removeTypingIndicator();

        // Adiciona mensagem do usuário
        ChatUI.appendMessage(result.message);
        
        // Adiciona resposta da IA se existir
        if (result.assistantMessage) {
          // Delay para parecer mais natural
          await new Promise(resolve => setTimeout(resolve, 500));
          ChatUI.appendMessage(result.assistantMessage);
        }
        
        // Limpa input
        ChatUI.clearInput();
        
        // Atualiza sidebar
        const activeConv = ChatService.getActiveConversation();
        if (activeConv) {
          ChatUI.updateTitle(activeConv.title);
          ChatUI.renderConversations(
            ChatService.getConversationsHistory(),
            activeConv.id
          );
        }
      }

    } catch (error) {
      console.error('Erro ao enviar mensagem:', error);
      ChatUI.removeTypingIndicator();
      ChatUI.showError('Erro ao enviar: ' + error.message);
    } finally {
      // Reabilita input
      input.disabled = false;
      input.focus();
      ChatUI.updateSendButton();
    }
  }

  function handleInput(e) {
    ChatUI.updateSendButton();
    
    // Auto-resize do textarea
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 200) + 'px';
  }

  function handleKeydown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!ChatUI.elements.btnSend.disabled) {
        handleSendMessage();
      }
    }
  }

  function handleConversationSelect(id) {
    const conversation = ChatService.selectConversation(id);
    if (conversation) {
      ChatUI.updateTitle(conversation.title);
      ChatUI.renderMessages(conversation.messages);
      ChatUI.renderConversations(
        ChatService.getConversationsHistory(),
        conversation.id
      );
      ChatUI.closeSidebar();
    }
  }

  function handleConversationDelete(id) {
    if (confirm('Tem certeza que deseja excluir esta conversa?')) {
      ChatService.deleteConversation(id);
      
      // Atualiza UI
      const activeConv = ChatService.getActiveConversation();
      if (activeConv) {
        ChatUI.updateTitle(activeConv.title);
        ChatUI.renderMessages(activeConv.messages);
      } else {
        ChatUI.updateTitle('Nova Conversa');
        ChatUI.renderMessages([]);
      }
      
      ChatUI.renderConversations(
        ChatService.getConversationsHistory(),
        activeConv?.id || null
      );
    }
  }

  function handleDeleteConversation() {
    const activeConv = ChatService.getActiveConversation();
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
      window.location.href = '/';
    }
  }

  // ========================================
  // Renderização Inicial
  // ========================================
  function renderInitialState() {
    const conversations = ChatService.getConversationsHistory();
    const activeConv = ChatService.getActiveConversation();

    if (activeConv) {
      ChatUI.updateTitle(activeConv.title);
      ChatUI.renderMessages(activeConv.messages);
    } else if (conversations.length > 0) {
      // Seleciona primeira conversa
      handleConversationSelect(conversations[0].id);
    } else {
      ChatUI.updateTitle('Nova Conversa');
      ChatUI.renderMessages([]);
    }

    ChatUI.renderConversations(conversations, activeConv?.id || null);
  }

  // ========================================
  // Inicializa
  // ========================================
  document.addEventListener('DOMContentLoaded', init);

})();
