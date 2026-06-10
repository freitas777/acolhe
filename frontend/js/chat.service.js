/**
 * Chat Service - Com IA Integrada
 */

const ChatService = {
  API_BASE_URL: window.location.origin,

  /**
   * Envia mensagem e recebe resposta da IA
   */
  async sendMessage(content, alunoId) {
    if (!content || !content.trim()) {
      throw new Error('Mensagem não pode estar vazia');
    }

    const trimmedContent = content.trim();

    try {
      const body = {
        message: trimmedContent,
        conversation_id: ChatStore.state.activeConversationId
      };
      if (alunoId) body.aluno_id = alunoId;

      const response = await acolheFetch(`${this.API_BASE_URL}/api/chat/send`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(body)
      });

    if (!response.ok) {
      let detail = 'Erro na API';
      try {
        const error = await response.json();
        detail = error.detail || detail;
      } catch (_) {}
      throw new Error(detail);
    }

    const data = await response.json();

    return {
      success: true,
      userMessage: data.user_message,
      assistantMessage: data.assistant_message,
      conversationId: data.conversation_id,
      alunoId: data.aluno_id || null,
      alunoNome: data.aluno_nome || null
    };

  } catch (error) {
    throw error;
  }
},

  /**
   * Gera conteúdo educacional adaptado
   */
  async generateEducationalContent(tema, perfilAluno) {
    try {
      const response = await acolheFetch(`${this.API_BASE_URL}/api/chat/educational-content`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
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
throw error;
}
},

  /**
   * Carrega conversas do backend
   */
  async loadConversations() {
    try {
      const response = await acolheFetch(`${this.API_BASE_URL}/api/chat/conversations`);

      if (response.ok) {
        const conversations = await response.json();
        ChatStore.state.conversations = conversations.map(function(c) {
          return {
            id: c.id,
            title: c.title,
            messages: c.messages || [],
            created_at: c.created_at,
            aluno_id: c.aluno_id || null,
            aluno_nome: c.aluno_nome || null
          };
        });
        ChatStore.save();
        return ChatStore.getAllConversations();
      }
    } catch (error) {
      ChatUI.showError('Erro ao carregar conversas');
    }
    return ChatStore.getAllConversations();
  },

  /**
   * Cria nova conversa
   */
  async createNewConversation(alunoId) {
    try {
      const body = { title: 'Nova conversa' };
      if (alunoId) body.aluno_id = alunoId;

      const response = await acolheFetch(`${this.API_BASE_URL}/api/chat/conversations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(body)
      });

      if (response.ok) {
        const conversation = await response.json();
        return conversation;
      }
    } catch (error) {
      ChatUI.showError('Erro ao criar conversa');
    }
    return ChatStore.createConversation();
  },

  /**
   * Deleta conversa
   */
  async deleteConversation(id) {
    try {
      await acolheFetch(`${this.API_BASE_URL}/api/chat/conversations/${id}`, {
        method: 'DELETE'
      });
    } catch (error) {
      ChatUI.showError('Erro ao excluir conversa');
    }
    return ChatStore.deleteConversation(id);
  },

  getActiveConversation() {
    return ChatStore.getActiveConversation();
  },

  getConversationsHistory() {
    return ChatStore.getAllConversations();
  },

  async searchAlunos(query) {
    if (!query || query.trim().length < 2) return [];
    try {
      const response = await acolheFetch(`${this.API_BASE_URL}/alunos/busca?q=${encodeURIComponent(query.trim())}`);
      if (response.ok) {
        return await response.json();
      }
  } catch (error) {
  }
  return [];
  }
};

window.ChatService = ChatService;
