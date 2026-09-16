from __future__ import annotations

import asyncio
import hashlib
import logging
import threading
import time
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

# Compactação de histórico (conversas longas)
MENSAGENS_RECENTES = 8
MAX_MENSAGENS_SESSAO = 16
MAX_RESUMO_CHARS = 2000


class AIService:
    def __init__(self):
        self._model: Optional[genai.GenerativeModel] = None
        self._sessoes: OrderedDict[str, genai.ChatSession] = OrderedDict()
        self._system_instructions: dict[str, str] = {}
        self._cache: OrderedDict[str, tuple[str, float]] = OrderedDict()
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

    def _construir_historico_base(
        self,
        system_instruction: Optional[str] = None,
    ) -> list[dict]:
        instrucao = system_instruction or INSTRUCAO_SISTEMA
        return [
            {"role": "user", "parts": [instrucao]},
            {"role": "model", "parts": ["Entendido. Sou o Acolhe+, pronto para ajudar."]},
        ]

    def _criar_sessao(
        self,
        conversa_id: str,
        system_instruction: Optional[str] = None,
    ) -> None:
        instrucao = system_instruction or INSTRUCAO_SISTEMA
        self._system_instructions[conversa_id] = instrucao

        historico = self._construir_historico_base(instrucao)
        sessao = self._obter_modelo().start_chat(history=historico)
        self._sessoes[conversa_id] = sessao

        self._evict_se_necessario()

        logger.info(
            "Sessão de chat iniciada: %s (com system_instruction=%s)",
            conversa_id,
            bool(system_instruction),
        )

    def _resumir_antigas(self, mensagens: list) -> str:
        if not mensagens:
            return ""
        trechos = []
        for msg in mensagens:
            conteudo = (getattr(msg, "conteudo", "") or "").strip()
            if not conteudo:
                continue
            trechos.append(conteudo[:120])
        resumo = "\n".join(trechos)
        if len(resumo) > MAX_RESUMO_CHARS:
            resumo = resumo[:MAX_RESUMO_CHARS] + "\n...[resumo truncado]"
        return resumo

    def _recriar_sessao(
        self,
        conversa_id: str,
        system_instruction: Optional[str] = None,
        mensagens: Optional[list] = None,
    ) -> None:
        instrucao = system_instruction
        if instrucao is None:
            instrucao = self._system_instructions.get(conversa_id) or INSTRUCAO_SISTEMA
        self._system_instructions[conversa_id] = instrucao

        historico = self._construir_historico_base(instrucao)

        recentes = []
        resumo = ""
        if mensagens:
            if len(mensagens) > MENSAGENS_RECENTES:
                resumo = self._resumir_antigas(mensagens[:-MENSAGENS_RECENTES])
            recentes = mensagens[-MENSAGENS_RECENTES:]

        if resumo:
            historico.append({
                "role": "user",
                "parts": ["## RESUMO DAS MENSAGENS ANTERIORES\n" + resumo],
            })
            historico.append({
                "role": "model",
                "parts": ["Entendido. Continuarei considerando este contexto."],
            })

        for msg in recentes:
            papel = getattr(msg, "papel", "") or ""
            conteudo = getattr(msg, "conteudo", "") or ""
            role = "user" if papel == "usuario" else "model"
            historico.append({"role": role, "parts": [conteudo]})

        sessao = self._obter_modelo().start_chat(history=historico)
        self._sessoes[conversa_id] = sessao

        self._evict_se_necessario()

        logger.info(
            "Sessão recriada: %s (mensagens=%d, resumo=%d chars)",
            conversa_id,
            len(mensagens) if mensagens else 0,
            len(resumo),
        )

    def _evict_se_necessario(self) -> None:
        while len(self._sessoes) > MAX_SESSOES:
            chave_mais_antiga = next(iter(self._sessoes))
            del self._sessoes[chave_mais_antiga]
            self._system_instructions.pop(chave_mais_antiga, None)
            logger.info("Sessão removida por LRU: %s", chave_mais_antiga)

    async def iniciar_sessao(
        self,
        conversa_id: str,
        system_instruction: Optional[str] = None,
    ) -> None:
        async with self._lock:
            self._criar_sessao(conversa_id, system_instruction=system_instruction)

    async def obter_sessao(
        self,
        conversa_id: str,
        mensagens: Optional[list] = None,
    ) -> genai.ChatSession:
        async with self._lock:
            if conversa_id not in self._sessoes:
                if mensagens:
                    self._recriar_sessao(conversa_id, mensagens=mensagens)
                else:
                    self._criar_sessao(conversa_id)
            elif mensagens and len(mensagens) > MAX_MENSAGENS_SESSAO:
                self._recriar_sessao(conversa_id, mensagens=mensagens)
            sessao = self._sessoes.pop(conversa_id)
            self._sessoes[conversa_id] = sessao
            return sessao

    async def garantir_sessao_com_contexto(
        self,
        conversa_id: str,
        mensagens: Optional[list] = None,
        system_instruction: Optional[str] = None,
    ) -> None:
        async with self._lock:
            if conversa_id not in self._sessoes:
                if mensagens:
                    self._recriar_sessao(
                        conversa_id,
                        system_instruction=system_instruction,
                        mensagens=mensagens,
                    )
                else:
                    self._criar_sessao(conversa_id, system_instruction=system_instruction)
            elif system_instruction:
                self._system_instructions[conversa_id] = system_instruction

    async def encerrar_sessao(self, conversa_id: str) -> None:
        async with self._lock:
            if conversa_id in self._sessoes:
                del self._sessoes[conversa_id]
                self._system_instructions.pop(conversa_id, None)
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
            last_exc = None
            for tentativa in range(1, 4):
                try:
                    resposta = s.send_message(m, stream=True)
                    for chunk in resposta:
                        texto = getattr(chunk, "text", None)
                        if texto:
                            loop.call_soon_threadsafe(q.put_nowait, texto)
                    loop.call_soon_threadsafe(q.put_nowait, _STREAM_SENTINEL)
                    return
                except Exception as exc:
                    last_exc = exc
                    if tentativa < 3:
                        time.sleep(tentativa)
            loop.call_soon_threadsafe(q.put_nowait, (_STREAM_ERROR, last_exc))

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

    def _cache_get(self, chave: str) -> Optional[str]:
        if chave in self._cache:
            resposta, timestamp = self._cache[chave]
            if time.time() - timestamp < settings.ai_cache_ttl_seconds:
                self._cache.move_to_end(chave)
                logger.info("Cache HIT: %s", chave[:16])
                return resposta
            else:
                del self._cache[chave]
                logger.info("Cache EXPIRED: %s", chave[:16])
        return None

    def _cache_set(self, chave: str, resposta: str) -> None:
        self._cache[chave] = (resposta, time.time())
        self._cache.move_to_end(chave)
        while len(self._cache) > settings.ai_cache_max_size:
            chave_antiga = next(iter(self._cache))
            del self._cache[chave_antiga]
        logger.info("Cache SET: %s (total=%d)", chave[:16], len(self._cache))

    async def gerar_conteudo_educacional(
        self,
        tema: str,
        perfil_aluno: dict,
    ) -> str:
        prompt = self._construir_prompt_educacional(tema, perfil_aluno)
        chave = hashlib.sha256(prompt.encode()).hexdigest()

        cached = self._cache_get(chave)
        if cached:
            return cached

        modelo = self._obter_modelo()
        loop = asyncio.get_running_loop()
        resposta = await loop.run_in_executor(
            None,
            lambda: modelo.generate_content(prompt),
        )

        self._cache_set(chave, resposta.text)
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