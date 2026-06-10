/**
 * Chat Store - Gerenciamento de Estado e Persistência
 * Responsável por CRUD de conversas e mensagens
 */

const ChatStore = {
  STORAGE_KEY: 'acolhe_chat_data',
  
  /**
   * Estado inicial
   */
  state: {
    conversations: [],
    activeConversationId: null,
    activeAlunoId: null,
    activeAlunoNome: null
  },

  /**
   * Inicializa o store carregando do localStorage
   */
  init() {
    const saved = localStorage.getItem(this.STORAGE_KEY);
    if (saved) {
      try {
        this.state = JSON.parse(saved);
        this.state.conversations = this.state.conversations.filter(
          c => c.id && !c.id.startsWith('conv_')
        );
        if (this.state.activeConversationId && this.state.activeConversationId.startsWith('conv_')) {
          this.state.activeConversationId = null;
          this.state.activeAlunoId = null;
          this.state.activeAlunoNome = null;
        }
        this.save();
    } catch (e) {
      this.state = { conversations: [], activeConversationId: null, activeAlunoId: null, activeAlunoNome: null };
      }
  }
  },

  /**
   * Salva estado no localStorage
   */
  save() {
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.state));
  },

  /**
   * Gera UUID único
   */
  generateId() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  },

  /**
   * Cria nova conversa
   */
  createConversation(title = 'Nova conversa', alunoId = null, alunoNome = null) {
    const conversation = {
      id: this.generateId(),
      title: title,
      messages: [],
      created_at: new Date().toISOString(),
      aluno_id: alunoId,
      aluno_nome: alunoNome
    };
    
    this.state.conversations.unshift(conversation);
    this.state.activeConversationId = conversation.id;
    this.save();
    return conversation;
  },

  /**
   * Obtém conversa ativa
   */
  getActiveConversation() {
    if (!this.state.activeConversationId) return null;
    return this.state.conversations.find(
      c => c.id === this.state.activeConversationId
    );
  },

  /**
   * Obtém conversa por ID
   */
  getConversation(id) {
    return this.state.conversations.find(c => c.id === id);
  },

  /**
   * Define conversa ativa
   */
  setActiveConversation(id) {
    const conversation = this.getConversation(id);
    if (conversation) {
      this.state.activeConversationId = id;
      this.state.activeAlunoId = conversation.aluno_id || null;
      this.state.activeAlunoNome = conversation.aluno_nome || null;
      this.save();
      return conversation;
    }
    return null;
  },

  /**
   * Adiciona mensagem à conversa ativa
   */
  addMessage(role, content) {
    const conversation = this.getActiveConversation();
    if (!conversation) return null;

    if (!content) content = '';
    const message = {
      id: this.generateId(),
      role: role, // 'user' ou 'assistant'
      content: content,
      created_at: new Date().toISOString()
    };

    conversation.messages.push(message);

    // Atualiza título se for primeira mensagem do usuário
    if (conversation.messages.length === 1 && role === 'user') {
      conversation.title = content.substring(0, 50) + (content.length > 50 ? '...' : '');
    }
    
    this.save();
    return message;
  },

  /**
   * Deleta conversa
   */
  deleteConversation(id) {
    const index = this.state.conversations.findIndex(c => c.id === id);
    if (index === -1) return false;

    this.state.conversations.splice(index, 1);
    
    // Se era a ativa, seleciona outra
    if (this.state.activeConversationId === id) {
      this.state.activeConversationId = this.state.conversations[0]?.id || null;
    }
    
    this.save();
    return true;
  },

  /**
   * Obtém todas as conversas
   */
  getAllConversations() {
    return this.state.conversations;
  },

  /**
   * Limpa todos os dados
   */
  clear() {
    this.state = { conversations: [], activeConversationId: null, activeAlunoId: null, activeAlunoNome: null };
    this.save();
    localStorage.removeItem(this.STORAGE_KEY);
  },

  setAlunoContext(alunoId, alunoNome) {
    this.state.activeAlunoId = alunoId;
    this.state.activeAlunoNome = alunoNome;
    const conversation = this.getActiveConversation();
    if (conversation) {
      conversation.aluno_id = alunoId;
      conversation.aluno_nome = alunoNome;
    }
    this.save();
  },

  clearAlunoContext() {
    this.state.activeAlunoId = null;
    this.state.activeAlunoNome = null;
    const conversation = this.getActiveConversation();
    if (conversation) {
      conversation.aluno_id = null;
      conversation.aluno_nome = null;
    }
    this.save();
  }
};

// Exporta para uso global
window.ChatStore = ChatStore;
