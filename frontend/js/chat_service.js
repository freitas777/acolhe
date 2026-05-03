/**
 * Chat Service - Regras de Negócio
 * Agora com integração backend preparada
 */

const ChatService = {
  API_BASE_URL: window.location.origin,

  /**
   * Envia mensagem do usuário
   */
  async sendMessage(content) {
    if (!content || !content.trim()) {
      throw new Error('Mensagem não pode estar vazia');
    }

    const trimmedContent = content.trim();

    // ✅ MODO 1: Apenas localStorage (atual)
    const userMessage = ChatStore.addMessage('user', trimmedContent);
    
    if (!userMessage) {
      throw new Error('Falha ao adicionar mensagem');
    }

    console.log('📤 Mensagem enviada:', userMessage.id);

    // 🔮 MODO 2: Com backend (descomentar quando implementar)
    /*
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
        throw new Error('Erro na API');
      }

      const data = await response.json();
      
      // Adiciona resposta da IA se existir
      if (data.assistant_message) {
        ChatStore.addMessage('assistant', data.assistant_message.content);
      }
    } catch (error) {
      console.error('Erro ao chamar API:', error);
      // Fallback para localStorage
    }
    */

    return {
      success: true,
      message: userMessage,
      needsAIResponse: true
    };
  },

  /**
   * Carrega conversas do backend
   */
  async loadConversations() {
    // 🔮 FUTURO: Buscar do backend
    /*
    try {
      const response = await fetch(`${this.API_BASE_URL}/api/chat/conversations`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('acolhe_access_token')}`
        }
      });
      if (response.ok) {
        return await response.json();
      }
    } catch (error) {
      console.error('Erro ao carregar conversas:', error);
    }
    */
    return ChatStore.getAllConversations();
  },

  /**
   * Salva conversa no backend
   */
  async saveConversation(conversation) {
    // 🔮 FUTURO: Salvar no backend
    console.log('💾 Salvar conversa no backend:', conversation.id);
  },

  /**
   * Cria nova conversa
   */
  createNewConversation() {
    const conversation = ChatStore.createConversation();
    this.saveConversation(conversation);
    return conversation;
  },

  /**
   * Seleciona conversa
   */
  selectConversation(id) {
    return ChatStore.setActiveConversation(id);
  },

  /**
   * Deleta conversa
   */
  async deleteConversation(id) {
    // 🔮 FUTURO: Deletar no backend também
    /*
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
    */
    return ChatStore.deleteConversation(id);
  },

  /**
   * Obtém conversa ativa
   */
  getActiveConversation() {
    return ChatStore.getActiveConversation();
  },

  /**
   * Histórico de conversas
   */
  getConversationsHistory() {
    return ChatStore.getAllConversations();
  }
};

window.ChatService = ChatService;
