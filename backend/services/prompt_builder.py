from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from backend.models.aluno import Aluno
from backend.models.disciplina import Disciplina
from backend.models.mensagem import Mensagem
from backend.models.perfil_aluno import PerfilAluno
from backend.models.acomodacao_observacao import AcomodacaoObservacao

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_BASE = (
    "Você é o Acolhe+, assistente de tecnologias educacionais do IFRN. "
    "Você conhece as políticas de EaD da instituição e o ecossistema de ferramentas (Moodle/SUAP).\n\n"
    "# Regras de formatação (OBRIGATÓRIO seguir)\n\n"
    "1. Vá direto ao ponto. Nunca comece com \"Prezado(a)\", \"Compreendo sua solicitação\", "
    "\"Como Assessor...\", \"Excelente!\", ou qualquer introdução formal. Comece respondendo imediatamente.\n\n"
    "2. Nunca assine a resposta. Não use \"Atenciosamente\", \"Cordialmente\", \"Estou à disposição\", "
    "\"Como Assessor de Tecnologias...\", ou qualquer encerramento formal.\n\n"
    "3. Linguagem natural. Escreva como alguém explicando o assunto para um colega, não como um documento oficial.\n\n"
    "4. Use Markdown para estruturar:\n"
    "   - Títulos com ## para separar seções\n"
    "   - Negrito **apenas** para conceitos-chave (não frases inteiras)\n"
    "   - Listas com - para itens\n"
    "   - Tabelas quando comparar informações\n"
    "   - Não use --- entre parágrafos\n\n"
    "5. Hierarquia simples. Use apenas ## quando necessário. Não crie dezenas de subtítulos.\n\n"
    "6. Listas curtas. Prefira listas com 3-5 itens. Se precisar de mais, agrupe em subcategorias.\n\n"
    "7. Adapte o tamanho. Pergunta simples = resposta curta (2-3 parágrafos). Pergunta complexa = resposta completa.\n\n"
    "8. Não repita frases. Não fique repetindo \"Como Assessor...\", \"Nosso objetivo...\", \"O IFRN...\".\n\n"
    "9. Não explique o que você vai fazer antes de fazer. Apenas faça.\n\n"
    "10. Cada parágrafo deve ter no máximo 3-4 linhas. Evite blocos enormes de texto.\n\n"
    "# Exemplo de boa resposta:\n\n"
    "## O que é o Moodle\n\n"
    "O Moodle é a plataforma principal de EaD do IFRN. Nele você encontra:\n\n"
    "- Materiais didáticos organizados por disciplina\n"
    "- Fóruns de discussão com colegas e professores\n"
    "- Atividades e avaliações online\n"
    "- Acompanhamento de notas e frequência\n\n"
    "## Como acessar\n\n"
    "Acesse pelo portal do SUAP ou diretamente em moodle.ifrn.edu.br com sua matrícula e senha.\n\n"
    "# Contexto IFRN\n\n"
    "Quando aplicável, mencione SUAP, Moodle ou portais institucionais. "
    "Para cursos autoinstrucionais, priorize clareza e caminhos intuitivos.\n\n"
    "Se não tiver certeza sobre um normativo, sugira consultar a Política de EaD do IFRN, "
    "mas forneça a melhor prática geral."
)

MAX_HISTORY_MESSAGES = 20
MAX_HISTORY_CHARS = 4000
MAX_OBSERVATIONS_CHARS = 1500


@dataclass
class PromptContext:
    system_prompt: str = ""
    student_profile: str = ""
    teacher_observations: str = ""
    history_summary: str = ""
    current_task: str = ""
    discipline_context: str = ""
    metadata: dict = field(default_factory=dict)


class PromptBuilder:
    def __init__(self):
        self._system_prompt = SYSTEM_PROMPT_BASE

    def build_system_prompt(self) -> str:
        return self._system_prompt

    def build_student_profile(
        self,
        aluno: Aluno,
        perfil: Optional[PerfilAluno] = None,
    ) -> str:
        if not perfil:
            return ""

        nome = aluno.nome or "Não informado"
        nivel = perfil.nivel_atencao.value if perfil.nivel_atencao else "não informado"
        dificuldade_leitura = "Sim" if perfil.dificuldade_leitura else "Não"
        preferencia = perfil.preferencia.value if perfil.preferencia else "não informada"
        interesses = perfil.interesses or "não informados"
        diagnostico = perfil.diagnostico or "não informado"

        secoes = [
            "## PERFIL PSICOPEDAGÓGICO DO ALUNO",
            "",
            f"**Nome:** {nome}",
            f"**Nível de Atenção:** {nivel}",
            f"**Dificuldade de Leitura:** {dificuldade_leitura}",
            f"**Preferência de Aprendizado:** {preferencia}",
            f"**Interesses:** {interesses}",
            f"**Diagnóstico:** {diagnostico}",
        ]

        secoes.append("")
        secoes.append("### DIRETRIZES PEDAGÓGICAS BASEADAS NO PERFIL:")
        secoes.append(f"- Adapte estratégias ao nível de atenção: {nivel}")
        secoes.append(f"- Considere a dificuldade de leitura: {dificuldade_leitura}")
        secoes.append(f"- Utilize a preferência de aprendizado: {preferencia}")
        secoes.append(f"- Conecte conteúdo aos interesses: {interesses}")
        secoes.append(f"- Considere o diagnóstico nas abordagens: {diagnostico}")

        return "\n".join(secoes)

    def build_teacher_observations(
        self,
        observacoes: list[AcomodacaoObservacao],
        disciplina: Optional[Disciplina] = None,
    ) -> str:
        if not observacoes:
            return ""

        secoes = ["## OBSERVAÇÕES DO PROFESSOR"]

        if disciplina:
            secoes.append(f"**Disciplina:** {disciplina.descricao}")
            secoes.append("")

        for obs in observacoes:
            professor_nome = obs.professor_nome or "Professor"
            disciplina_sigla = obs.disciplina_sigla or "Disciplina"
            texto = obs.texto[:500] if len(obs.texto) > 500 else obs.texto
            data_formatada = obs.criado_em.strftime("%d/%m/%Y") if obs.criado_em else ""

            secoes.append(f"### Observação de {professor_nome} ({disciplina_sigla})")
            if data_formatada:
                secoes.append(f"*Registrado em: {data_formatada}*")
            secoes.append(texto)
            secoes.append("")

        resultado = "\n".join(secoes)
        if len(resultado) > MAX_OBSERVATIONS_CHARS:
            resultado = resultado[:MAX_OBSERVATIONS_CHARS] + "\n...[observações truncadas]"

        return resultado

    def build_history_summary(
        self,
        mensagens: list[Mensagem],
        max_messages: int = MAX_HISTORY_MESSAGES,
    ) -> str:
        if not mensagens:
            return ""

        mensagens_recentes = mensagens[-max_messages:]
        secoes = ["## RESUMO DO HISTÓRICO DA CONVERSA"]
        secoes.append("*Interações anteriores relevantes para contexto:*")
        secoes.append("")

        total_chars = 0
        for msg in mensagens_recentes:
            papel = "Usuário" if msg.papel == "usuario" else "Assistente"
            conteudo = msg.conteudo
            if total_chars + len(conteudo) > MAX_HISTORY_CHARS:
                conteudo = conteudo[:200] + "...[truncado]"

            secoes.append(f"**{papel}:** {conteudo}")
            secoes.append("")
            total_chars += len(conteudo)

        secoes.append("### CONTEXTO ACUMULADO:")
        secoes.append("- Considere o progresso e as adaptações já discutidas")
        secoes.append("- Mantenha consistência com estratégias anteriores")
        secoes.append("- Evite repetir informações já fornecidas")

        return "\n".join(secoes)

    def build_discipline_context(
        self,
        disciplina: Optional[Disciplina],
    ) -> str:
        if not disciplina:
            return ""

        descricao = disciplina.descricao or "não informada"
        sigla = disciplina.sigla or ""
        professor = getattr(disciplina, "professor", None) or "não informado"
        semestre = getattr(disciplina, "semestre", None) or "não informado"
        codigo_turma = getattr(disciplina, "codigo_turma", None) or ""

        secoes = [
            "## CONTEXTO DA DISCIPLINA",
            "",
            f"**Nome:** {descricao}",
        ]
        if sigla:
            secoes.append(f"**Sigla:** {sigla}")
        secoes.append(f"**Professor:** {professor}")
        secoes.append(f"**Semestre:** {semestre}")
        if codigo_turma:
            secoes.append(f"**Código da Turma:** {codigo_turma}")

        secoes.append("")
        secoes.append("### DIRETRIZES ESPECÍFICAS DA DISCIPLINA:")
        secoes.append("- Responda dúvidas relacionadas ao conteúdo desta disciplina")
        secoes.append("- Use exemplos e contextos pertinentes à área de conhecimento")
        secoes.append("- Adapte a explicação ao nível do estudante")
        secoes.append("- Sugira materiais complementares quando apropriado")

        return "\n".join(secoes)

    def build_current_task(
        self,
        mensagem_usuario: str,
    ) -> str:
        secoes = [
            "## QUESTÃO/TAREFA ATUAL",
            "",
            "**Solicitação do usuário:**",
            mensagem_usuario,
            "",
            "### INSTRUÇÕES PARA ESTA RESPOSTA:",
            "- Responda diretamente à questão apresentada",
            "- Integre o contexto do perfil do aluno na resposta",
            "- Considere as observações do professor quando relevantes",
            "- Mantenha consistência com o histórico da conversa",
            "- Forneça exemplos práticos e aplicáveis",
            "- Use formatação clara (tópicos, negrito) para facilitar a compreensão",
        ]
        return "\n".join(secoes)

    def assemble_prompt(
        self,
        aluno: Optional[Aluno] = None,
        perfil: Optional[PerfilAluno] = None,
        disciplina: Optional[Disciplina] = None,
        observacoes: Optional[list[AcomodacaoObservacao]] = None,
        mensagens: Optional[list[Mensagem]] = None,
        mensagem_usuario: str = "",
    ) -> PromptContext:
        context = PromptContext()

        context.system_prompt = self.build_system_prompt()

        if aluno and perfil:
            context.student_profile = self.build_student_profile(aluno, perfil)

        if observacoes:
            context.teacher_observations = self.build_teacher_observations(
                observacoes, disciplina
            )

        if mensagens:
            context.history_summary = self.build_history_summary(mensagens)

        if disciplina:
            context.discipline_context = self.build_discipline_context(disciplina)

        if mensagem_usuario:
            context.current_task = self.build_current_task(mensagem_usuario)

        return context

    def format_final_prompt(
        self,
        context: PromptContext,
    ) -> str:
        secoes = []

        secoes.append(context.system_prompt)
        secoes.append("")

        if context.student_profile:
            secoes.append(context.student_profile)
            secoes.append("")

        if context.discipline_context:
            secoes.append(context.discipline_context)
            secoes.append("")

        if context.teacher_observations:
            secoes.append(context.teacher_observations)
            secoes.append("")

        if context.history_summary:
            secoes.append(context.history_summary)
            secoes.append("")

        if context.current_task:
            secoes.append(context.current_task)

        prompt_final = "\n".join(secoes)

        logger.info(
            "Prompt montado: system=%d chars, profile=%d chars, observations=%d chars, "
            "history=%d chars, discipline=%d chars, task=%d chars, total=%d chars",
            len(context.system_prompt),
            len(context.student_profile),
            len(context.teacher_observations),
            len(context.history_summary),
            len(context.discipline_context),
            len(context.current_task),
            len(prompt_final),
        )

        return prompt_final

    def build_complete_prompt(
        self,
        aluno: Optional[Aluno] = None,
        perfil: Optional[PerfilAluno] = None,
        disciplina: Optional[Disciplina] = None,
        observacoes: Optional[list[AcomodacaoObservacao]] = None,
        mensagens: Optional[list[Mensagem]] = None,
        mensagem_usuario: str = "",
    ) -> str:
        context = self.assemble_prompt(
            aluno=aluno,
            perfil=perfil,
            disciplina=disciplina,
            observacoes=observacoes,
            mensagens=mensagens,
            mensagem_usuario=mensagem_usuario,
        )
        return self.format_final_prompt(context)

    def build_session_instruction(
        self,
        aluno: Optional[Aluno] = None,
        perfil: Optional[PerfilAluno] = None,
        disciplina: Optional[Disciplina] = None,
        observacoes: Optional[list[AcomodacaoObservacao]] = None,
        mensagens: Optional[list[Mensagem]] = None,
    ) -> str:
        context = self.assemble_prompt(
            aluno=aluno,
            perfil=perfil,
            disciplina=disciplina,
            observacoes=observacoes,
            mensagens=mensagens,
            mensagem_usuario="",
        )
        return self.format_final_prompt(context)


prompt_builder = PromptBuilder()
