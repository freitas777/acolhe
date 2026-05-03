/**
 * Chat Service - Com IA Integrada
 */

const ChatService = {
  API_BASE_URL: window.location.origin,

  /**
   * Envia mensagem e recebe resposta da IA
   */
  async sendMessage(content) {
    if (!content || !content.trim()) {
      throw new Error('Mensagem não pode estar vazia');
    }

    const trimmedContent = content.trim();

    // ✅ MODO COM BACKEND + IA
    try {
      const response = await fetch(`${this.API_BASE_URL}/api/chat/send`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('acolhe_access_token')}`
        },
        body: JSON.stringify({
          message: trimmedContent,
          conversation_id: ChatStore.state.activeConversationId
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Erro na API');
      }

      const data = await response.json();
      
      // Salva no localStorage também (backup)
      ChatStore.addMessage('user', trimmedContent);
      if (data.assistant_message) {
        ChatStore.addMessage('assistant', data.assistant_message.content);
      }

      console.log('🤖 Resposta da IA recebida');

      return {
        success: true,
        message: data.user_message,
        assistantMessage: data.assistant_message,
        conversationId: data.conversation_id
      };

    } catch (error) {
      console.error('Erro ao chamar API:', error);
      
      // Fallback para localStorage apenas
      const userMessage = ChatStore.addMessage('user', trimmedContent);
      
      return {
        success: true,
        message: userMessage,
        assistantMessage: null,
        needsAIResponse: true
      };
    }
  },

  /**
   * Gera conteúdo educacional adaptado
   */
  async generateEducationalContent(tema, perfilAluno) {
    try {
      const response = await fetch(`${this.API_BASE_URL}/api/chat/educational-content`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('acolhe_access_token')}`
        },
        body: JSON.stringify({
          tema: tema,
          perfil_aluno: perfilAluno
        })
      });

      if (!response.ok) {
        throw new Error('Erro ao gerar conteúdo');
      }

      const data = await response.json();
      return data.conteudo;

    } catch (error) {
      console.error('Erro ao gerar conteúdo:', error);
      throw error;
    }
  },

  /**
   * Carrega conversas do backend
   */
  async loadConversations() {
    try {
      const response = await fetch(`${this.API_BASE_URL}/api/chat/conversations`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('acolhe_access_token')}`
        }
      });

      if (response.ok) {
        const conversations = await response.json();
        return conversations;
      }
    } catch (error) {
      console.error('Erro ao carregar conversas:', error);
    }

    return ChatStore.getAllConversations();
  },

  /**
   * Cria nova conversa
   */
  async createNewConversation() {
    try {
      const response = await fetch(`${this.API_BASE_URL}/api/chat/conversations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('acolhe_access_token')}`
        },
        body: JSON.stringify({ title: 'Nova conversa' })
      });

      if (response.ok) {
        const conversation = await response.json();
        return conversation;
      }
    } catch (error) {
      console.error('Erro ao criar conversa:', error);
    }

    return ChatStore.createConversation();
  },

  /**
   * Deleta conversa
   */
  async deleteConversation(id) {
    try {
      await fetch(`${this.API_BASE_URL}/api/chat/conversations/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('acolhe_access_token')}`
        }
      });
    } catch (error) {
      console.error('Erro ao deletar no backend:', error);
    }

    return ChatStore.deleteConversation(id);
  },

  getActiveConversation() {
    return ChatStore.getActiveConversation();
  },

  getConversationsHistory() {
    return ChatStore.getAllConversations();
  }
};

window.ChatService = ChatService;
