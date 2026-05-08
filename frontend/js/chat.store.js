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
    activeConversationId: null
  },

  /**
   * Inicializa o store carregando do localStorage
   */
  init() {
    const saved = localStorage.getItem(this.STORAGE_KEY);
    if (saved) {
      try {
        this.state = JSON.parse(saved);
      } catch (e) {
        console.error('Erro ao carregar dados do chat:', e);
        this.state = { conversations: [], activeConversationId: null };
      }
    }
    console.log('📦 ChatStore inicializado');
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
    return 'conv_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  },

  /**
   * Cria nova conversa
   */
  createConversation(title = 'Nova conversa') {
    const conversation = {
      id: this.generateId(),
      title: title,
      messages: [],
      created_at: new Date().toISOString()
    };
    
    this.state.conversations.unshift(conversation);
    this.state.activeConversationId = conversation.id;
    this.save();
    
    console.log('✅ Conversa criada:', conversation.id);
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
      this.save();
      console.log('📍 Conversa ativa:', id);
      return conversation;
    }
    return null;
  },

  /**
   * Adiciona mensagem à conversa ativa
   */
  addMessage(role, content) {
    const conversation = this.getActiveConversation();
    if (!conversation) {
      console.error('❌ Nenhuma conversa ativa');
      return null;
    }

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
    console.log('💬 Mensagem adicionada:', message.id);
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
    console.log('🗑️ Conversa deletada:', id);
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
    this.state = { conversations: [], activeConversationId: null };
    this.save();
    localStorage.removeItem(this.STORAGE_KEY);
    console.log('🧹 ChatStore limpo');
  }
};

// Exporta para uso global
window.ChatStore = ChatStore;
