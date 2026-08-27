from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from backend.models.usuario import Usuario
from backend.models.disciplina import Disciplina
from backend.models.diario_aluno import DiarioAluno
from backend.models.aluno import Aluno
from backend.repositories.usuario import UsuarioRepository
from backend.repositories.disciplina import DisciplinaRepository
from backend.repositories.diario_aluno import DiarioAlunoRepository
from backend.repositories.aluno import AlunoRepository
from backend.repositories.perfil_aluno import PerfilAlunoRepository
from backend.models.pendencia_validacao import PendenciaValidacao, StatusPendencia
from backend.repositories.pendencia_validacao import PendenciaValidacaoRepository
from backend.config import settings
from backend.services.suap_service import SUAPService
from backend.services.notificacao_service import NotificacaoService
from backend.schemas.auth import UsuarioSUAPResponse, DisciplinaResponse, AlunoAssistidoResponse, PendenciaResponse
from backend.database import get_db
from fastapi import Depends, HTTPException, status

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        self.usuario_repo = UsuarioRepository(db)
        self.disciplina_repo = DisciplinaRepository(db)
        self.diario_aluno_repo = DiarioAlunoRepository(db)
        self.perfil_aluno_repo = PerfilAlunoRepository(db)
        self.aluno_repo = AlunoRepository(db)
        self.pendencia_repo = PendenciaValidacaoRepository(db)
        self.suap_service = SUAPService()

    async def login_com_suap(self, token: str, semestre: str = "") -> dict:
        logger.info("[LOGIN SUAP] Iniciando login com token (semestre=%s)", semestre)

        scope = settings.suap_scope or "identificacao email documentos_pessoais"
        eu_dados = await self.suap_service.get_eu(token, scope=scope)
        logger.info("[LOGIN SUAP] eu_dados recebido: %s", eu_dados)

        suap_id = str(eu_dados.get("identificacao", "") or eu_dados.get("id", ""))
        nome = eu_dados.get("nome_usual", "") or eu_dados.get("nome", "")
        email = eu_dados.get("email", "")
        campus = eu_dados.get("campus", "")

        logger.info("[LOGIN SUAP] Dados extraidos: suap_id=%s, nome=%s, email=%s, campus=%s",
                   suap_id, nome, email, campus)

        matricula = ""
        tipo_vinculo = ""
        setor = ""
        try:
            vinculos = await self.suap_service.get_meus_vinculos(token, scope=scope)
            if vinculos:
                primeiro = vinculos[0]
                matricula = primeiro.get("identificador", "") or primeiro.get("matricula", "")
                tipo_vinculo = primeiro.get("tipo", "") or primeiro.get("tipo_vinculo", "")
                if not campus:
                    campus = primeiro.get("campus", "") or ""
                detalhe = primeiro.get("detalhamento") or {}
                setor = detalhe.get("cargo", "") or detalhe.get("modalidade", "") or ""
                logger.info("[LOGIN SUAP] Vinculo: matricula=%s, tipo=%s, campus=%s", matricula, tipo_vinculo, campus)
        except Exception as e:
            logger.warning("Falha ao obter vinculos do SUAP: %s", e)

        tipo_perfil = "aluno"
        if tipo_vinculo and tipo_vinculo.lower() not in ("aluno", "estudante"):
            tipo_perfil = "servidor"
        
        logger.info("[LOGIN SUAP] Tipo vinculo: '%s', Tipo perfil determinado: '%s'", tipo_vinculo, tipo_perfil)

        usuario = self.usuario_repo.get_by_suap_id(suap_id)
        if usuario and usuario.aprovado_napne:
            tipo_perfil = "psicopedagogo"
            logger.info("[LOGIN SUAP] Usuario existente aprovado NAPNE - tipo alterado para psicopedagogo")
        if usuario:
            update_data = {
                "nome": nome,
                "email": email,
                "matricula": matricula,
                "tipo_vinculo": tipo_vinculo,
                "campus": campus,
                "setor": setor,
            }
            if tipo_perfil in ("psicopedagogo", "servidor"):
                update_data["tipo_perfil"] = tipo_perfil
            for key, value in update_data.items():
                setattr(usuario, key, value)
            self.db.commit()
            self.db.refresh(usuario)
        else:
            usuario_data = {
                "suap_id": suap_id,
                "nome": nome,
                "email": email,
                "matricula": matricula,
                "tipo_vinculo": tipo_vinculo,
                "campus": campus,
                "setor": setor,
                "tipo_perfil": tipo_perfil,
            }
            logger.info("[LOGIN SUAP] Criando novo usuario com dados: %s", usuario_data)
            usuario = self.usuario_repo.create(usuario_data)
            logger.info("[LOGIN SUAP] Usuario criado com id=%s", usuario.id)

        curso = ""
        if tipo_perfil == "aluno" and matricula:
            try:
                resumidos = await self.suap_service.buscar_alunos_resumido(token, matricula=matricula)
                if resumidos:
                    r = resumidos[0]
                    a_data = r.get("aluno", r)
                    c = a_data.get("curso", "")
                    curso = c.get("descricao", "") if isinstance(c, dict) else str(c) if c else ""
            except Exception as e:
                logger.warning("[LOGIN SUAP] Falha ao buscar curso do aluno: %s", e)

        if tipo_perfil == "aluno":
            aluno_existente = self.aluno_repo.get_by_suap_id(suap_id)
            if not aluno_existente:
                aluno_data = {
                    "suap_id": suap_id,
                    "nome": nome,
                    "email": email,
                    "matricula": matricula or None,
                    "curso": curso or None,
                    "campus": campus or None,
                    "status_acompanhamento": "ativo",
                }
                self.aluno_repo.create(aluno_data)
                logger.info("[LOGIN SUAP] Aluno criado automaticamente para suap_id=%s", suap_id)
            else:
                updated = False
                if aluno_existente.nome != nome:
                    aluno_existente.nome = nome
                    updated = True
                if email and aluno_existente.email != email:
                    aluno_existente.email = email
                    updated = True
                if matricula and not aluno_existente.matricula:
                    aluno_existente.matricula = matricula
                    updated = True
                if curso and not aluno_existente.curso:
                    aluno_existente.curso = curso
                    updated = True
                if campus and not aluno_existente.campus:
                    aluno_existente.campus = campus
                    updated = True
                if updated:
                    self.db.commit()
                    logger.info("[LOGIN SUAP] Dados do aluno atualizados para suap_id=%s", suap_id)

        disciplinas_salvas = []
        try:
            logger.info("[LOGIN SUAP] Iniciando sincronizacao para usuario %s (tipo=%s)", usuario.id, tipo_perfil)
            if tipo_perfil == "psicopedagogo":
                logger.info("[LOGIN SUAP] Usuario psicopedagogo - pulando sincronizacao de disciplinas")
            elif tipo_perfil in ("professor", "servidor"):
                logger.info("[LOGIN SUAP] Usuario professor/servidor - sincronizando diarios")
                await self._sincronizar_diarios_professor(usuario, token, semestre, scope=scope)
            else:
                logger.info("[LOGIN SUAP] Usuario aluno - sincronizando disciplinas do semestre %s", semestre)
                disciplinas_raw = await self.suap_service.get_disciplinas(token, semestre, scope=scope)
                logger.info("[LOGIN SUAP] Disciplinas recebidas do SUAP: %d", len(disciplinas_raw))
                if disciplinas_raw:
                    logger.info("[LOGIN SUAP] Primeira disciplina: %s", disciplinas_raw[0] if disciplinas_raw else "N/A")
                self._sincronizar_disciplinas(usuario.id, disciplinas_raw, semestre)
            disciplinas_salvas = self.disciplina_repo.listar_por_usuario(usuario.id, semestre)
            logger.info("[LOGIN SUAP] Disciplinas salvas no banco: %d", len(disciplinas_salvas))
        except Exception as e:
            logger.error("[LOGIN SUAP] Falha ao sincronizar para usuario %s: %s", usuario.id, e, exc_info=True)

        self.db.refresh(usuario)

        if not disciplinas_salvas:
            disciplinas_salvas = self.disciplina_repo.listar_por_usuario(usuario.id, semestre)
        logger.info("[LOGIN SUAP] Total de disciplinas no banco para usuario %s: %d", usuario.id, len(disciplinas_salvas))

        result = {
            "usuario": UsuarioSUAPResponse.model_validate(usuario),
            "tipo_perfil": tipo_perfil,
            "disciplinas": [DisciplinaResponse.model_validate(d) for d in disciplinas_salvas],
        }

        return result

    async def _sincronizar_diarios_professor(self, usuario: Usuario, token: str, semestre: str, scope: str = ""):
        parts = semestre.split(".")
        ano_letivo = int(parts[0])
        periodo_letivo = int(parts[1]) if len(parts) > 1 else 1

        diarios_raw = await self.suap_service.get_meus_diarios(token, ano_letivo, periodo_letivo, scope=scope)
        logger.info("Professor %s: %d diarios encontrados no SUAP", usuario.id, len(diarios_raw))

        existing_disciplinas = self.disciplina_repo.listar_por_usuario(usuario.id, semestre)
        existing_aluno_pairs: set[tuple[int, int]] = set()
        for disc in existing_disciplinas:
            for da in disc.alunos_assistidos:
                existing_aluno_pairs.add((disc.suap_id or disc.diario_id or 0, da.aluno_id))

        self.disciplina_repo.deletar_por_usuario_e_semestre(usuario.id, semestre)

        assistidos_by_matricula = self.aluno_repo.get_matricula_lookup()
        new_assistidos: list[tuple[int, str, str]] = []

        for diario in diarios_raw:
            diario_id = diario.get("id", 0)
            componente_curricular = diario.get("componente_curricular", "")
            sigla = ""
            descricao = componente_curricular

            if " - " in componente_curricular:
                parts = componente_curricular.split(" - ", 1)
                sigla = parts[0].strip()
                descricao = parts[1].strip() if len(parts) > 1 else componente_curricular
            elif " – " in componente_curricular:
                parts = componente_curricular.split(" – ", 1)
                sigla = parts[0].strip()
                descricao = parts[1].strip() if len(parts) > 1 else componente_curricular
            elif len(componente_curricular.split()) > 1:
                first_word = componente_curricular.split()[0]
                if len(first_word) <= 10 and "." in first_word:
                    sigla = first_word
                    descricao = componente_curricular[len(first_word):].strip(" -–")

            codigo_turma = sigla or componente_curricular

            professores_nomes = ""
            professores = diario.get("professores", [])
            if professores:
                professores_nomes = ", ".join(p.get("nome", "") for p in professores)

            disciplina_data = {
                "suap_id": diario_id,
                "diario_id": diario_id,
                "descricao": descricao,
                "sigla": sigla,
                "codigo_turma": codigo_turma,
                "situacao": "",
                "professor": professores_nomes,
                "semestre": semestre,
                "usuario_id": usuario.id,
            }
            disciplina = self.disciplina_repo.create(disciplina_data)

            try:
                alunos_diario = await self.suap_service.get_alunos_diario(token, diario_id, scope=scope)
                logger.info("Diario %d: %d alunos", diario_id, len(alunos_diario))

                for aluno_suap in alunos_diario:
                    matricula_aluno = aluno_suap.get("matricula", "")
                    if matricula_aluno in assistidos_by_matricula:
                        aluno_db = assistidos_by_matricula[matricula_aluno]
                        existing = self.diario_aluno_repo.get_by_disciplina_aluno(disciplina.id, aluno_db.id)
                        if not existing:
                            self.diario_aluno_repo.create({
                                "disciplina_id": disciplina.id,
                                "aluno_id": aluno_db.id,
                                "aluno_nome": aluno_suap.get("nome", aluno_db.nome),
                                "aluno_matricula": matricula_aluno,
                            })
                            pair_key = (diario_id, aluno_db.id)
                            if pair_key not in existing_aluno_pairs:
                                new_assistidos.append((aluno_db.id, aluno_db.nome, descricao))
            except Exception as e:
                logger.warning("Falha ao buscar alunos do diario %d: %s", diario_id, e)

        if new_assistidos:
            try:
                notif_service = NotificacaoService(self.db)
                for aluno_id, aluno_nome, disc_desc in new_assistidos:
                    notif_service.criar_notificacao(
                        tipo="assistido_na_turma",
                        titulo=f"Aluno assistido na sua turma: {aluno_nome}",
                        mensagem=f"O aluno assistido {aluno_nome} esta matriculado na disciplina {disc_desc}.",
                        aluno_id=aluno_id,
                        destino_tipo="professor",
                        destino_id=usuario.id,
                    )
            except Exception as e:
                logger.warning("Falha ao criar notificacoes de assistido na turma: %s", e)

    def _sincronizar_disciplinas(self, usuario_id: int, disciplinas_raw: list[dict], semestre: str):
        self.disciplina_repo.deletar_por_usuario_e_semestre(usuario_id, semestre)

        for disc_raw in disciplinas_raw:
            disciplina_data = {
                "suap_id": disc_raw.get("id", 0),
                "diario_id": disc_raw.get("id", 0),
                "descricao": disc_raw.get("descricao", ""),
                "sigla": disc_raw.get("sigla", ""),
                "codigo_turma": disc_raw.get("sigla", ""),
                "situacao": disc_raw.get("situacao", {}).get("rotulo", "") if isinstance(disc_raw.get("situacao"), dict) else str(disc_raw.get("situacao", "")),
                "professor": disc_raw.get("docente", "") or disc_raw.get("professor", ""),
                "semestre": semestre,
                "usuario_id": usuario_id,
            }
            self.disciplina_repo.create(disciplina_data)

    def obter_usuario_atual(self, usuario_id: int) -> Usuario:
        usuario = self.usuario_repo.get_by_id(usuario_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado",
            )
        return usuario

    def obter_disciplinas(self, usuario_id: int, semestre: str | None = None) -> list[Disciplina]:
        return self.disciplina_repo.listar_por_usuario(usuario_id, semestre)

    def obter_alunos_assistidos(self, disciplina_id: int) -> list[DiarioAluno]:
        return self.diario_aluno_repo.listar_por_disciplina(disciplina_id)

    # --- New methods for Professor Dashboard ---
    def obter_perfil_aluno(self, professor_id: int, aluno_id: int):
        # Verify professor has this aluno in any of their disciplinas
        if not self.diario_aluno_repo.verificar_professor_aluno(professor_id, aluno_id):
            raise HTTPException(status_code=403, detail="Acesso negado ao perfil do aluno.")
        perfil = self.perfil_aluno_repo.get_by_aluno_id(aluno_id)
        if not perfil:
            raise HTTPException(status_code=404, detail="Perfil do aluno não encontrado.")
        return perfil

    def obter_conteudos_aluno(self, professor_id: int, aluno_id: int):
        # Verify professor association
        if not self.diario_aluno_repo.verificar_professor_aluno(professor_id, aluno_id):
            raise HTTPException(status_code=403, detail="Acesso negado ao conteúdo do aluno.")
        # Use existing repository
        from backend.repositories.conteudo_gerado import ConteudoGeradoRepository
        repo = ConteudoGeradoRepository(self.db)
        return repo.list_by_aluno(aluno_id)

    def solicitar_apoio_napne(self, professor_id: int, aluno_id: int, motivo: str):
        # Verify association
        if not self.diario_aluno_repo.verificar_professor_aluno(professor_id, aluno_id):
            raise HTTPException(status_code=403, detail="Acesso negado ao aluno.")
        # Check for existing pending pendencia
        existing = self.pendencia_repo.get_pendente_por_aluno(aluno_id)
        if existing:
            raise HTTPException(status_code=409, detail="Já existe pendência pendente para este aluno.")
        # Create pendencia (reuse existing logic)
        pend = self.pendencia_repo.create({
            "aluno_id": aluno_id,
            "indicado_por_id": professor_id,
            "motivo": motivo,
            "status": StatusPendencia.pendente,
        })
        # Notify NAPNE
        notif_service = NotificacaoService(self.db)
        notif_service.criar_notificacao(
            tipo="solicitacao_apoio",
            titulo="Solicitação de apoio do NAPNE",
            mensagem=motivo,
            aluno_id=aluno_id,
            destino_tipo="napne",
        )
        return pend

    def criar_ou_atualizar_observacao(self, professor_id: int, aluno_id: int, disciplina_id: int, texto: str):
        # Verify association
        if not self.diario_aluno_repo.verificar_professor_aluno(professor_id, aluno_id):
            raise HTTPException(status_code=403, detail="Acesso negado ao aluno.")
        from backend.repositories.acomodacao_observacao import AcomodacaoObservacaoRepository
        repo = AcomodacaoObservacaoRepository(self.db)
        observacao = repo.criar_ou_atualizar(aluno_id, disciplina_id, professor_id, texto)
        # Notify NAPNE
        notif_service = NotificacaoService(self.db)
        notif_service.criar_notificacao(
            tipo="observacao_acomodacao",
            titulo="Nova observação de acomodação",
            mensagem=f"Observação para o aluno {aluno_id} na disciplina {disciplina_id}",
            aluno_id=aluno_id,
            destino_tipo="napne",
        )
        return observacao

    def obter_observacao(self, professor_id: int, aluno_id: int, disciplina_id: int):
        # Verify association
        if not self.diario_aluno_repo.verificar_professor_aluno(professor_id, aluno_id):
            raise HTTPException(status_code=403, detail="Acesso negado ao aluno.")
        from backend.repositories.acomodacao_observacao import AcomodacaoObservacaoRepository
        repo = AcomodacaoObservacaoRepository(self.db)
        obs = repo.get_by_aluno_disciplina_professor(aluno_id, disciplina_id, professor_id)
        if not obs:
            raise HTTPException(status_code=404, detail="Observação não encontrada")
        return obs

    def obter_pendencias(self) -> list[PendenciaValidacao]:
        return self.pendencia_repo.listar_pendentes()

    def obter_alunos_ativos(self) -> list[Aluno]:
        return self.aluno_repo.listar_por_status("ativo")

    def buscar_alunos(self, query: str) -> list[Aluno]:
        return self.aluno_repo.buscar_por_nome_ou_matricula(query)

    def validar_pendencia(self, pendencia_id: int, validado_por_id: int, acao: str) -> PendenciaValidacao:
        pendencia = self.pendencia_repo.get_by_id(pendencia_id)
        if not pendencia:
            raise HTTPException(status_code=404, detail="Pendência não encontrada")
        if pendencia.status != StatusPendencia.pendente:
            raise HTTPException(status_code=400, detail="Pendência já foi processada")
        from datetime import datetime, timezone
        update_data = {
            "status": acao,
            "validado_por_id": validado_por_id,
            "validado_em": datetime.now(timezone.utc),
        }
        pendencia = self.pendencia_repo.update(pendencia_id, update_data)
        if acao in (StatusPendencia.validado.value, StatusPendencia.rejeitado.value) and pendencia.aluno_id:
            aluno = self.aluno_repo.get_by_id(pendencia.aluno_id)
            if aluno:
                if acao == StatusPendencia.validado.value and aluno.status_acompanhamento == "aguardando_indicacao":
                    aluno.status_acompanhamento = "ativo"
                elif acao == StatusPendencia.rejeitado.value:
                    aluno.status_acompanhamento = "rejeitado"
                self.db.commit()
                self.db.refresh(aluno)
        return pendencia

    def criar_pendencia(self, aluno_id: int, indicado_por_id: int, motivo: str = None) -> PendenciaValidacao:
        aluno = self.aluno_repo.get_by_id(aluno_id)
        if not aluno:
            raise HTTPException(status_code=404, detail="Aluno não encontrado")
        existing = self.pendencia_repo.get_pendente_por_aluno(aluno_id)
        if existing:
            raise HTTPException(status_code=400, detail="Já existe pendência pendente para este aluno")
        return self.pendencia_repo.create({
            "aluno_id": aluno_id,
            "indicado_por_id": indicado_por_id,
            "motivo": motivo,
            "status": StatusPendencia.pendente,
        })

    def atualizar_perfil_usuario(self, usuario_id: int, novo_perfil: str) -> Usuario:
        usuario = self.usuario_repo.get_by_id(usuario_id)
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        if novo_perfil == "psicopedagogo":
            usuario.tipo_perfil = "psicopedagogo"
            usuario.aprovado_napne = True
        else:
            usuario.tipo_perfil = novo_perfil
            if novo_perfil != "psicopedagogo":
                usuario.aprovado_napne = False
        self.db.commit()
        self.db.refresh(usuario)
        return usuario
