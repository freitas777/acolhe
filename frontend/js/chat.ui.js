/**
 * Chat UI - Manipulação de DOM e Renderização
 */

const ChatUI = {
  elements: {},

  /**
   * Inicializa referências do DOM
   */
  init() {
    this.elements = {
      sidebar: document.getElementById('sidebar'),
      conversationsList: document.getElementById('conversations-list'),
      messagesWrapper: document.getElementById('messages-wrapper'),
      emptyState: document.getElementById('empty-state'),
      messageInput: document.getElementById('message-input'),
      btnSend: document.getElementById('btn-send'),
      btnNewChat: document.getElementById('btn-new-chat'),
      btnMenuMobile: document.getElementById('btn-menu-mobile'),
      btnDeleteConversation: document.getElementById('btn-delete-conversation'),
      btnLogout: document.getElementById('btn-logout'),
      chatTitle: document.getElementById('chat-title'),
      userAvatarSmall: document.getElementById('user-avatar-small'),
      userNameSmall: document.getElementById('user-name-small'),
      userRoleSmall: document.getElementById('user-role-small')
    };

    console.log('🎨 ChatUI inicializado');
  },

  /**
   * Renderiza lista de conversas na sidebar
   */
  renderConversations(conversations, activeId) {
    const list = this.elements.conversationsList;
    if (!list) return;

    list.innerHTML = '';

    if (conversations.length === 0) {
      list.innerHTML = `
        <div style="text-align: center; padding: 1rem; color: var(--color-text-muted); font-size: 0.875rem;">
          Nenhuma conversa ainda
        </div>
      `;
      return;
    }

    conversations.forEach(conv => {
      const item = document.createElement('div');
      item.className = `conversation-item ${conv.id === activeId ? 'active' : ''}`;
      item.dataset.conversationId = conv.id;
      
      item.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
        <span>${this.escapeHtml(conv.title)}</span>
        <button class="delete-btn" title="Excluir conversa">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
          </svg>
        </button>
      `;

      // Clique para selecionar
      item.addEventListener('click', (e) => {
        if (!e.target.closest('.delete-btn')) {
          this.onConversationSelect(conv.id);
        }
      });

      // Clique para deletar
      const deleteBtn = item.querySelector('.delete-btn');
      deleteBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.onConversationDelete(conv.id);
      });

      list.appendChild(item);
    });
  },

  /**
   * Renderiza mensagens da conversa ativa
   */
  renderMessages(messages) {
    const wrapper = this.elements.messagesWrapper;
    const emptyState = this.elements.emptyState;
    
    if (!wrapper) return;

    // Remove mensagens antigas (mantém empty state)
    const existingMessages = wrapper.querySelectorAll('.message');
    existingMessages.forEach(msg => msg.remove());

    if (!messages || messages.length === 0) {
      if (emptyState) emptyState.style.display = 'flex';
      return;
    }

    if (emptyState) emptyState.style.display = 'none';

    messages.forEach(msg => {
      const messageEl = this.createMessageElement(msg);
      wrapper.appendChild(messageEl);
    });

    // Scroll para última mensagem
    this.scrollToBottom();
  },

  /**
   * Cria elemento de mensagem
   */
  createMessageElement(message) {
    const div = document.createElement('div');
    div.className = 'message';
    
    const isUser = message.role === 'user';
    const avatar = isUser ? this.getUserInitials() : 'AI';
    const author = isUser ? 'Você' : 'Acolhe+';
    const time = this.formatTime(message.created_at);

    div.innerHTML = `
      <div class="message-avatar ${message.role}">${avatar}</div>
      <div class="message-content">
        <div class="message-header">
          <span class="message-author">${author}</span>
          <span class="message-time">${time}</span>
        </div>
        <div class="message-text">${this.escapeHtml(message.content)}</div>
      </div>
    `;

    return div;
  },

  /**
   * Adiciona mensagem à UI em tempo real
   */
  appendMessage(message) {
    const wrapper = this.elements.messagesWrapper;
    const emptyState = this.elements.emptyState;
    
    if (!wrapper) return;

    if (emptyState) emptyState.style.display = 'none';

    const messageEl = this.createMessageElement(message);
    wrapper.appendChild(messageEl);
    this.scrollToBottom();
  },

  /**
   * Atualiza título do chat
   */
  updateTitle(title) {
    if (this.elements.chatTitle) {
      this.elements.chatTitle.textContent = title || 'Nova Conversa';
    }
  },

  /**
   * Atualiza informações do usuário
   */
  updateUserInfo(user) {
    if (!user) return;

    if (this.elements.userAvatarSmall) {
      this.elements.userAvatarSmall.textContent = this.getUserInitials(user.nome);
    }
    if (this.elements.userNameSmall) {
      this.elements.userNameSmall.textContent = user.nome || 'Usuário';
    }
    if (this.elements.userRoleSmall) {
      this.elements.userRoleSmall.textContent = user.tipo_vinculo || user.matricula || '-';
    }
  },

  /**
   * Limpa input
   */
  clearInput() {
    if (this.elements.messageInput) {
      this.elements.messageInput.value = '';
      this.elements.messageInput.style.height = 'auto';
    }
    this.updateSendButton();
  },

  /**
   * Atualiza estado do botão enviar
   */
  updateSendButton() {
    if (this.elements.btnSend && this.elements.messageInput) {
      const hasContent = this.elements.messageInput.value.trim().length > 0;
      this.elements.btnSend.disabled = !hasContent;
    }
  },

  /**
   * Scroll para última mensagem
   */
  scrollToBottom() {
    const container = document.getElementById('messages-container');
    if (container) {
      container.scrollTop = container.scrollHeight;
    }
  },

  /**
   * Abre sidebar no mobile
   */
  openSidebar() {
    if (this.elements.sidebar) {
      this.elements.sidebar.classList.add('open');
    }
  },

  /**
   * Fecha sidebar no mobile
   */
  closeSidebar() {
    if (this.elements.sidebar) {
      this.elements.sidebar.classList.remove('open');
    }
  },

  /**
   * Handlers de eventos
   */
  onConversationSelect(id) {
    // Implementado no dashboard.js
    console.log('📍 Selecionar conversa:', id);
  },

  onConversationDelete(id) {
    // Implementado no dashboard.js
    console.log('🗑️ Deletar conversa:', id);
  },

  /**
   * Utilitários
   */
  getUserInitials(name) {
    if (!name) return '??';
    return name
      .split(' ')
      .map(n => n[0])
      .slice(0, 2)
      .join('')
      .toUpperCase();
  },

  formatTime(isoString) {
    const date = new Date(isoString);
    return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  },

  escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  },

    /**
   * Mostra indicador de "digitando..."
   */
  showTypingIndicator() {
    const wrapper = this.elements.messagesWrapper;
    if (!wrapper) return;

    const typingDiv = document.createElement('div');
    typingDiv.className = 'message typing-indicator';
    typingDiv.id = 'typing-indicator';
    
    typingDiv.innerHTML = `
      <div class="message-avatar assistant">AI</div>
      <div class="message-content">
        <div class="typing-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    `;

    wrapper.appendChild(typingDiv);
    this.scrollToBottom();
  },

  /**
   * Remove indicador de digitando
   */
  removeTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
      indicator.remove();
    }
  },

  /**
   * Mostra erro na mensagem
   */
  showError(message) {
    const wrapper = this.elements.messagesWrapper;
    if (!wrapper) return;

    const errorDiv = document.createElement('div');
    errorDiv.className = 'message error-message';
    errorDiv.innerHTML = `
      <div class="message-content" style="width: 100%;">
        <div class="message-text" style="color: var(--color-error);">
          ⚠️ ${message}
        </div>
      </div>
    `;

    wrapper.appendChild(errorDiv);
    this.scrollToBottom();
  }

  
};

// Exporta para uso global
window.ChatUI = ChatUI;

