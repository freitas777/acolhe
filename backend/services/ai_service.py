from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import threading
import typing
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
MAX_MODELOS = 50


class AIService:
    def __init__(self):
        self._model: Optional[genai.GenerativeModel] = None
        self._modelos_por_contexto: OrderedDict[str, genai.GenerativeModel] = OrderedDict()
        self._sessoes: OrderedDict[str, genai.ChatSession] = OrderedDict()
        self._sessao_contexto: dict[str, str] = {}
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

    def _obter_modelo(self) -> genai.GenerativeModel:
        if self._model is None:
            raise RuntimeError("Modelo Gemini não foi inicializado. Verifique GEMINI_API_KEY.")
        return self._model

    def _obter_modelo_com_contexto(self, contexto_aluno: str) -> genai.GenerativeModel:
        chave = hashlib.sha256(contexto_aluno.encode()).hexdigest()
        if chave in self._modelos_por_contexto:
            self._modelos_por_contexto.move_to_end(chave)
            return self._modelos_por_contexto[chave]

        model_name = settings.gemini_model
        modelo = genai.GenerativeModel(model_name)
        self._modelos_por_contexto[chave] = modelo

        if len(self._modelos_por_contexto) > MAX_MODELOS:
            chave_mais_antiga = next(iter(self._modelos_por_contexto))
            del self._modelos_por_contexto[chave_mais_antiga]
            logger.info("Modelo com contexto removido por LRU: %s", chave_mais_antiga)

        logger.info("Modelo com contexto de aluno criado: %s", chave)
        return modelo

    def construir_contexto_aluno(self, aluno: object, perfil: object) -> str:
        nome = getattr(aluno, "nome", "Não informado")
        observacoes = getattr(aluno, "observacoes", None) or ""

        nivel = getattr(perfil, "nivel_atencao", None)
        nivel_str = nivel.value if nivel else "não informado"

        dificuldade = getattr(perfil, "dificuldade_leitura", False)
        dificuldade_str = "Sim" if dificuldade else "Não"

        preferencia = getattr(perfil, "preferencia", None)
        preferencia_str = preferencia.value if preferencia else "não informada"

        interesses = getattr(perfil, "interesses", None) or "não informados"
        diagnostico = getattr(perfil, "diagnostico", None) or "não informado"

        contexto = (
            f"**CONTEXTO: Você está conversando sobre um aluno específico.**\n\n"
            f"**DADOS DO ALUNO:**\n"
            f"- Nome: {nome}\n"
            f"- Nível de atenção: {nivel_str}\n"
            f"- Dificuldade de leitura: {dificuldade_str}\n"
            f"- Preferência de aprendizado: {preferencia_str}\n"
            f"- Interesses: {interesses}\n"
            f"- Diagnóstico: {diagnostico}\n"
        )

        if observacoes:
            contexto += f"- Observações: {observacoes}\n"

        contexto += (
            "\n**DIRETRIZES PARA ESTA CONVERSA:**\n"
            "1. Responda sempre considerando o perfil e necessidades deste aluno\n"
            "2. Adapte sugestões e estratégias ao nível de atenção e preferência de aprendizado\n"
            "3. Considere o diagnóstico ao recomendar abordagens pedagógicas\n"
            "4. Use os interesses do aluno como ponte para engajamento\n"
            "5. Quando pertinente, sugira adaptações específicas para as dificuldades relatadas\n"
        )

        return contexto

    def _construir_historico_base(self, contexto_aluno: Optional[str] = None) -> list[dict]:
        if contexto_aluno:
            instrucao = INSTRUCAO_SISTEMA + "\n\n" + contexto_aluno
        else:
            instrucao = INSTRUCAO_SISTEMA
        return [
            {"role": "user", "parts": [instrucao]},
            {"role": "model", "parts": ["Entendido. Sou o Acolhe+, pronto para ajudar."]},
        ]

    def _criar_sessao(self, conversa_id: str, contexto_aluno: Optional[str] = None) -> None:
        if contexto_aluno:
            modelo = self._obter_modelo_com_contexto(contexto_aluno)
            self._sessao_contexto[conversa_id] = contexto_aluno
        else:
            modelo = self._obter_modelo()
            self._sessao_contexto.pop(conversa_id, None)

        historico = self._construir_historico_base(contexto_aluno)
        sessao = modelo.start_chat(history=historico)
        self._sessoes[conversa_id] = sessao

        if len(self._sessoes) > MAX_SESSOES:
            chave_mais_antiga = next(iter(self._sessoes))
            del self._sessoes[chave_mais_antiga]
            self._sessao_contexto.pop(chave_mais_antiga, None)
            logger.info("Sessão removida por LRU: %s", chave_mais_antiga)

        logger.info("Sessão de chat iniciada: %s (contexto_aluno=%s)", conversa_id, bool(contexto_aluno))

    def _reconstruir_sessao(
        self,
        conversa_id: str,
        contexto_aluno: Optional[str] = None,
        mensagens: Optional[list] = None,
    ) -> None:
        if contexto_aluno:
            modelo = self._obter_modelo_com_contexto(contexto_aluno)
            self._sessao_contexto[conversa_id] = contexto_aluno
        else:
            modelo = self._obter_modelo()
            self._sessao_contexto.pop(conversa_id, None)

        historico = self._construir_historico_base(contexto_aluno)

        if mensagens:
            for msg in mensagens:
                papel = getattr(msg, "papel", None) or ""
                conteudo = getattr(msg, "conteudo", None) or ""
                role = "user" if papel == "usuario" else "model"
                historico.append({"role": role, "parts": [conteudo]})

        sessao = modelo.start_chat(history=historico)
        self._sessoes[conversa_id] = sessao

        if len(self._sessoes) > MAX_SESSOES:
            chave_mais_antiga = next(iter(self._sessoes))
            del self._sessoes[chave_mais_antiga]
            self._sessao_contexto.pop(chave_mais_antiga, None)
            logger.info("Sessão removida por LRU: %s", chave_mais_antiga)

        logger.info(
            "Sessão reconstruída: %s (contexto_aluno=%s, mensagens=%d)",
            conversa_id,
            bool(contexto_aluno),
            len(mensagens) if mensagens else 0,
        )

    async def iniciar_sessao(self, conversa_id: str, contexto_aluno: Optional[str] = None) -> None:
        async with self._lock:
            self._criar_sessao(conversa_id, contexto_aluno)

    async def obter_sessao(
        self,
        conversa_id: str,
        mensagens: Optional[list] = None,
    ) -> genai.ChatSession:
        async with self._lock:
            if conversa_id not in self._sessoes:
                contexto = self._sessao_contexto.get(conversa_id)
                if mensagens:
                    self._reconstruir_sessao(conversa_id, contexto_aluno=contexto, mensagens=mensagens)
                else:
                    self._criar_sessao(conversa_id, contexto_aluno=contexto)
            sessao = self._sessoes.pop(conversa_id)
            self._sessoes[conversa_id] = sessao
            return sessao

    async def garantir_sessao_com_contexto(
        self,
        conversa_id: str,
        contexto_aluno: Optional[str] = None,
        mensagens: Optional[list] = None,
    ) -> None:
        async with self._lock:
            if conversa_id not in self._sessoes:
                if mensagens:
                    self._reconstruir_sessao(conversa_id, contexto_aluno=contexto_aluno, mensagens=mensagens)
                else:
                    self._criar_sessao(conversa_id, contexto_aluno=contexto_aluno)

    async def encerrar_sessao(self, conversa_id: str) -> None:
        async with self._lock:
            if conversa_id in self._sessoes:
                del self._sessoes[conversa_id]
                self._sessao_contexto.pop(conversa_id, None)
                logger.info("Sessão encerrada: %s", conversa_id)

    async def gerar_resposta(
        self,
        conversa_id: str,
        mensagem_usuario: str,
        max_retries: int = 3,
        mensagens: Optional[list] = None,
    ) -> str:
        for tentativa in range(1, max_retries + 1):
            try:
                sessao = await self.obter_sessao(conversa_id, mensagens=mensagens)
                loop = asyncio.get_running_loop()
                resposta = await loop.run_in_executor(
                    None,
                    lambda s=sessao, m=mensagem_usuario: s.send_message(m),
                )
                logger.info(
                    "Resposta gerada: conversa=%s, tamanho=%d",
                    conversa_id,
                    len(resposta.text),
                )
                return resposta.text
            except Exception as exc:
                logger.warning(
                    "Tentativa %d/%d falhou para conversa=%s: %s",
                    tentativa, max_retries, conversa_id, exc,
                )
            if tentativa < max_retries:
                await asyncio.sleep(tentativa * 2)
            else:
                logger.error("Todas as tentativas falharam para conversa=%s", conversa_id)
                raise

    async def gerar_resposta_stream(
        self,
        conversa_id: str,
        mensagem_usuario: str,
        mensagens: Optional[list] = None,
    ) -> typing.AsyncIterator[str]:
        sessao = await self.obter_sessao(conversa_id, mensagens=mensagens)
        queue: asyncio.Queue = asyncio.Queue()
        _STREAM_SENTINEL = object()
        _STREAM_ERROR = object()

        def _consume_stream(s, m, q, loop):
            try:
                resposta = s.send_message(m, stream=True)
                for chunk in resposta:
                    texto = getattr(chunk, "text", None)
                    if texto:
                        loop.call_soon_threadsafe(q.put_nowait, texto)
                loop.call_soon_threadsafe(q.put_nowait, _STREAM_SENTINEL)
            except Exception as exc:
                loop.call_soon_threadsafe(q.put_nowait, (_STREAM_ERROR, exc))

        loop = asyncio.get_running_loop()
        thread = threading.Thread(
            target=_consume_stream,
            args=(sessao, mensagem_usuario, queue, loop),
            daemon=True,
        )
        thread.start()

        while True:
            item = await queue.get()
            if item is _STREAM_SENTINEL:
                break
            if isinstance(item, tuple) and len(item) == 2 and item[0] is _STREAM_ERROR:
                raise item[1]
            yield item

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
        nivel = perfil_aluno.get("nivel_atencao") or "não informado"
        dificuldade = "Sim" if perfil_aluno.get("dificuldade_leitura") else "Não"
        preferencia = perfil_aluno.get("preferencia") or "não informada"
        interesses = perfil_aluno.get("interesses") or "não informados"
        diagnostico = perfil_aluno.get("diagnostico") or "não informado"

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
