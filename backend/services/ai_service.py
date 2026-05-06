from __future__ import annotations

import asyncio
import logging
import os
from collections import OrderedDict
from typing import Optional

import google.generativeai as genai

from backend.config import settings

logger = logging.getLogger(__name__)

INSTRUCAO_SISTEMA = (
    "Você é o Acolhe+, um assistente educacional especializado em educação inclusiva. "
    "Seu objetivo é ajudar professores e psicopedagogos a criar estratégias e conteúdos "
    "adaptados para alunos com necessidades educacionais específicas. "
    "Seja prestativo, claro e sempre focado na inclusão e acessibilidade."
)

MAX_SESSOES = 100


class AIService:
    def __init__(self):
        self._model: Optional[genai.GenerativeModel] = None
        self._sessoes: OrderedDict[str, genai.ChatSession] = OrderedDict()
        self._lock = asyncio.Lock()
        self._inicializar()

    def _inicializar(self) -> None:
        try:
            api_key = settings.gemini_api_key
            model_name = settings.gemini_model

            if not api_key:
                logger.warning("GEMINI_API_KEY não configurada — IA desabilitada")
                return

            genai.configure(api_key=api_key)
            self._model = genai.GenerativeModel(model_name)
            logger.info("Gemini AI inicializado (modelo=%s)", model_name)
        except Exception as exc:
            logger.error("Erro ao inicializar Gemini: %s", exc)
            raise

    def _obter_modelo(self) -> genai.GenerativeModel:
        if self._model is None:
            raise RuntimeError("Modelo Gemini não foi inicializado. Verifique GEMINI_API_KEY.")
        return self._model

    def iniciar_sessao(self, conversa_id: str) -> None:
        modelo = self._obter_modelo()
        sessao = modelo.start_chat(history=[])
        self._sessoes[conversa_id] = sessao

        if len(self._sessoes) > MAX_SESSOES:
            chave_mais_antiga = next(iter(self._sessoes))
            del self._sessoes[chave_mais_antiga]
            logger.info("Sessão removida por LRU: %s", chave_mais_antiga)

        logger.info("Sessão de chat iniciada: %s", conversa_id)

    def obter_sessao(self, conversa_id: str) -> genai.ChatSession:
        if conversa_id not in self._sessoes:
            self.iniciar_sessao(conversa_id)
        sessao = self._sessoes.pop(conversa_id)
        self._sessoes[conversa_id] = sessao
        return sessao

    def encerrar_sessao(self, conversa_id: str) -> None:
        if conversa_id in self._sessoes:
            del self._sessoes[conversa_id]
            logger.info("Sessão encerrada: %s", conversa_id)

    async def gerar_resposta(
        self,
        conversa_id: str,
        mensagem_usuario: str,
    ) -> str:
        try:
            sessao = self.obter_sessao(conversa_id)
            loop = asyncio.get_running_loop()
            resposta = await loop.run_in_executor(
                None,
                lambda: sessao.send_message(mensagem_usuario),
            )
            logger.info(
                "Resposta gerada: conversa=%s, tamanho=%d",
                conversa_id,
                len(resposta.text),
            )
            return resposta.text
        except Exception as exc:
            logger.error("Erro ao gerar resposta: %s", exc)
            raise

    async def gerar_conteudo_educacional(
        self,
        tema: str,
        perfil_aluno: dict,
    ) -> str:
        prompt = self._construir_prompt_educacional(tema, perfil_aluno)
        modelo = self._obter_modelo()
        loop = asyncio.get_running_loop()
        resposta = await loop.run_in_executor(
            None,
            lambda: modelo.generate_content(prompt),
        )
        return resposta.text

    def _construir_prompt_educacional(
        self,
        tema: str,
        perfil_aluno: dict,
    ) -> str:
        nivel = perfil_aluno.get("nivel_atencao", "não informado")
        dificuldade = "Sim" if perfil_aluno.get("dificuldade_leitura") else "Não"
        preferencia = perfil_aluno.get("preferencia", "não informada")
        interesses = perfil_aluno.get("interesses", "não informados")
        diagnostico = perfil_aluno.get("diagnostico", "não informado")

        return (
            f"{INSTRUCAO_SISTEMA}\n\n"
            f"**TEMA:** {tema}\n\n"
            f"**PERFIL DO ALUNO:**\n"
            f"- Nível de atenção: {nivel}\n"
            f"- Dificuldade de leitura: {dificuldade}\n"
            f"- Preferência de aprendizado: {preferencia}\n"
            f"- Interesses: {interesses}\n"
            f"- Diagnóstico: {diagnostico}\n\n"
            f"**DIRETRIZES:**\n"
            "1. Use linguagem clara e apropriada ao nível do aluno\n"
            "2. Adapte o conteúdo ao estilo de aprendizado preferido\n"
            "3. Inclua exemplos práticos relacionados aos interesses do aluno\n"
            "4. Quebre informações complexas em partes menores\n"
            "5. Use formatação que facilite a leitura (tópicos, negrito, etc.)\n"
            "6. Seja encorajador e positivo\n\n"
            "**FORMATO DE SAÍDA:**\n"
            "- Título claro\n"
            "- Explicação do conceito\n"
            "- Exemplos práticos\n"
            "- Atividades sugeridas\n"
            "- Dicas de estudo\n\n"
            "Crie o conteúdo agora:"
        )


ai_service = AIService()
