/**
 * Chat Service - Com IA Integrada
 */

const ChatService = {
  API_BASE_URL: window.location.origin,

  /**
   * Envia mensagem e recebe resposta da IA
   */
  async sendMessageStream(content, alunoId, callbacks) {
    if (!content || !content.trim()) {
      throw new Error('Mensagem não pode estar vazia');
    }

    var trimmedContent = content.trim();
    var onChunk = callbacks.onChunk || function() {};
    var onDone = callbacks.onDone || function() {};
    var onError = callbacks.onError || function() {};

    try {
      var body = {
        message: trimmedContent,
        conversation_id: ChatStore.state.activeConversationId
      };
      if (alunoId) body.aluno_id = alunoId;

      var response = await acolheFetch(this.API_BASE_URL + '/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream'
        },
        body: JSON.stringify(body)
      });

      if (!response.ok) {
        var detail = 'Erro na API';
        try {
          var errorData = await response.json();
          detail = errorData.detail || detail;
        } catch (_) {}
        throw new Error(detail);
      }

      var reader = response.body.getReader();
      var decoder = new TextDecoder();
      var buffer = '';
      var userMessage = null;
      var conversationId = null;
      var alunoIdResult = null;
      var alunoNomeResult = null;
      var fullContent = '';

      while (true) {
        var result = await reader.read();
        if (result.done) break;

        buffer += decoder.decode(result.value, { stream: true });
        var lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (var i = 0; i < lines.length; i++) {
          var line = lines[i].trim();
          if (line.indexOf('data: ') !== 0) continue;
          var jsonStr = line.substring(6);
          if (!jsonStr) continue;

          try {
            var event = JSON.parse(jsonStr);
          } catch (_) {
            continue;
          }

          if (event.type === 'user_message') {
            userMessage = event.message;
          } else if (event.type === 'conversation_id') {
            conversationId = event.conversation_id;
          } else if (event.type === 'meta') {
            alunoIdResult = event.aluno_id || null;
            alunoNomeResult = event.aluno_nome || null;
          } else if (event.type === 'chunk') {
            fullContent += event.content;
            onChunk(event.content, fullContent);
          } else if (event.type === 'error') {
            fullContent += event.content;
            onError(event.content, fullContent);
          } else if (event.type === 'done') {
            onDone({
              userMessage: userMessage,
              assistantMessage: event.message || { role: 'assistant', content: fullContent },
              conversationId: conversationId,
              alunoId: alunoIdResult,
              alunoNome: alunoNomeResult
            });
          }
        }
      }
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
