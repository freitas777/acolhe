/**
 * Chat UI - Manipulação de DOM e Renderização
 */

const ChatUI = {
  elements: {},

  isAluno() {
    return (localStorage.getItem('acolhe_tipo_perfil') || 'aluno') === 'aluno';
  },

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
      btnLogout: document.getElementById('btn-logout'),
      chatTitle: document.getElementById('chat-title'),
      userAvatarSmall: document.getElementById('user-avatar-small'),
      userNameSmall: document.getElementById('user-name-small'),
      userRoleSmall: document.getElementById('user-role-small'),
      alunoContextBar: document.getElementById('aluno-context-bar'),
      alunoBadge: document.getElementById('aluno-badge'),
      alunoBadgeName: document.getElementById('aluno-badge-name'),
      btnRemoveAluno: document.getElementById('btn-remove-aluno'),
      btnAlunoContext: document.getElementById('btn-aluno-context'),
      alunoSearchWrapper: document.getElementById('aluno-search-wrapper'),
      alunoSearchInput: document.getElementById('aluno-search-input'),
      alunoSearchResults: document.getElementById('aluno-search-results')
  };

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
        ${(!this.isAluno() && conv.aluno_id) ? '<svg class="aluno-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>' : ''}
        <button class="delete-btn" title="Excluir conversa">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
          </svg>
        </button>
      `;

      // Clique para selecionar
      item.addEventListener('click', (e) => {
        if (e.target.closest('.delete-btn')) {
          this.onConversationDelete(conv.id);
          return;
        }
        this.onConversationSelect(conv.id);
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
  },

  onConversationDelete(id) {
  },

    updateAlunoBadge(alunoNome) {
        if (this.isAluno()) return;

        const bar = this.elements.alunoContextBar;
    const badge = this.elements.alunoBadge;
    const badgeName = this.elements.alunoBadgeName;
    const searchWrapper = this.elements.alunoSearchWrapper;

    if (!bar) return;

    bar.hidden = false;

    if (alunoNome) {
      if (badge) badge.hidden = false;
      if (badgeName) badgeName.textContent = alunoNome;
      if (searchWrapper) searchWrapper.hidden = true;
    } else {
      if (badge) badge.hidden = true;
      if (searchWrapper) searchWrapper.hidden = true;
    }
  },

  hideAlunoContext() {
    const bar = this.elements.alunoContextBar;
    if (bar) bar.hidden = true;
  },

    showAlunoSearch() {
        if (this.isAluno()) return;

        const bar = this.elements.alunoContextBar;
    const badge = this.elements.alunoBadge;
    const searchWrapper = this.elements.alunoSearchWrapper;
    const input = this.elements.alunoSearchInput;

    if (bar) bar.hidden = false;
    if (badge) badge.hidden = true;
    if (searchWrapper) searchWrapper.hidden = false;
    if (input) {
      input.value = '';
      input.focus();
    }
  },

  renderAlunoSearchResults(alunos) {
    const container = this.elements.alunoSearchResults;
    if (!container) return;

    container.innerHTML = '';

    if (!alunos || alunos.length === 0) {
      container.hidden = false;
      container.innerHTML = '<div class="aluno-search-empty">Nenhum aluno encontrado</div>';
      return;
    }

    container.hidden = false;

    alunos.forEach(aluno => {
      const item = document.createElement('div');
      item.className = 'aluno-search-item';
      item.dataset.alunoId = aluno.id;
      item.dataset.alunoNome = aluno.nome;

      let detail = '';
      if (aluno.matricula) detail += aluno.matricula;
      if (aluno.diagnostico) detail += (detail ? ' · ' : '') + aluno.diagnostico;

      item.innerHTML = `
        <span class="aluno-search-item-nome">${this.escapeHtml(aluno.nome)}</span>
        ${detail ? '<span class="aluno-search-item-detail">' + this.escapeHtml(detail) + '</span>' : ''}
      `;

      item.addEventListener('click', () => {
        this.onAlunoSelected(aluno.id, aluno.nome);
      });

      container.appendChild(item);
    });
  },

  hideAlunoSearchResults() {
    const container = this.elements.alunoSearchResults;
    if (container) {
      container.innerHTML = '';
      container.hidden = true;
    }
  },

  onAlunoSelected(alunoId, alunoNome) {
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
        if (!isoString) return '';
        const date = new Date(isoString);
        if (isNaN(date.getTime())) return '';
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
                    ⚠️ ${this.escapeHtml(message)}
                </div>
            </div>
        `;

    wrapper.appendChild(errorDiv);
    this.scrollToBottom();
  }

  
};

// Exporta para uso global
window.ChatUI = ChatUI;

