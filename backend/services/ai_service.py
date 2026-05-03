import google.generativeai as genai
from typing import Optional, List
import logging
import os

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.model = None
        self.chat_session = None
        self._initialize()
    
    def _initialize(self):
        try:
            api_key = os.environ.get('GEMINI_API_KEY')
            model_name = os.environ.get('GEMINI_MODEL')
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable is not set")
            if not model_name:
                raise ValueError("GEMINI_MODEL environment variable is not set")

            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name)
            logger.info("Gemini AI inicializado")
        except Exception as e:
            logger.error(f"Erro ao inicializar Gemini: {e}")
            raise
    
    def start_chat(self, system_instruction: Optional[str] = None):
        try:
            if self.model is None:
                raise RuntimeError("Modelo Gemini não foi inicializado")
            self.chat_session = self.model.start_chat(history=[])
            
            # Envia instrução de sistema (se houver)
            if system_instruction:
                self.chat_session.send_message(
                    f"Instrução do sistema: {system_instruction}\n\nAgora comece a conversar com o usuário."
                )
            
            logger.info("Sessão de chat iniciada")
            return True
        except Exception as e:
            logger.error(f"Erro ao iniciar chat: {e}")
            return False
    
    async def generate_response(self, user_message: str) -> str:
        try:
            if not self.chat_session:
                if not self.start_chat():
                    return "Desculpe, não foi possível iniciar a sessão de chat."
            
            assert self.chat_session is not None
            
            # Gera resposta
            response = self.chat_session.send_message(user_message)
            
            logger.info(f"Resposta gerada: {len(response.text)} caracteres")
            return response.text
            
        except Exception as e:
            logger.error(f"Erro ao gerar resposta: {e}")
            return f"Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente."
    
    def add_to_history(self, role: str, content: str):
        if self.chat_session:
            self.chat_session.history.append({  # type: ignore[arg-type]
                "role": role,
                "parts": [content]
            })
    
    def clear_history(self):
        if self.chat_session:
            self.chat_session.history = []
            logger.info("Histórico limpo")
    
    async def generate_educational_content(
        self,
        tema: str,
        perfil_aluno: dict
    ) -> str:
        prompt = self._build_educational_prompt(tema, perfil_aluno)
        return await self.generate_response(prompt)
    
    def _build_educational_prompt(
        self,
        tema: str,
        perfil_aluno: dict
    ) -> str:
        return f"""
Você é um assistente educacional especializado em educação inclusiva.
Sua tarefa é criar conteúdo adaptado para alunos com necessidades específicas.

**TEMA:** {tema}

**PERFIL DO ALUNO:**
- Nível de atenção: {perfil_aluno.get('nivel_atencao', 'não informado')}
- Dificuldade de leitura: {'Sim' if perfil_aluno.get('dificuldade_leitura') else 'Não'}
- Preferência de aprendizado: {perfil_aluno.get('preferencia', 'não informada')}
- Interesses: {perfil_aluno.get('interesses', 'não informados')}
- Diagnóstico: {perfil_aluno.get('diagnostico', 'não informado')}

**DIRETRIZES:**
1. Use linguagem clara e apropriada ao nível do aluno
2. Adapte o conteúdo ao estilo de aprendizado preferido
3. Inclua exemplos práticos relacionados aos interesses do aluno
4. Quebre informações complexas em partes menores
5. Use formatação que facilite a leitura (tópicos, negrito, etc.)
6. Seja encorajador e positivo

**FORMATO DE SAÍDA:**
- Título claro
- Explicação do conceito
- Exemplos práticos
- Atividades sugeridas
- Dicas de estudo

Crie o conteúdo agora:
"""

# Instância global
ai_service = AIService()
