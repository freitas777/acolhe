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
from backend.models.pendencia_validacao import PendenciaValidacao
from backend.repositories.pendencia_validacao import PendenciaValidacaoRepository
from backend.services.suap_service import SUAPService
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
        self.aluno_repo = AlunoRepository(db)
        self.pendencia_repo = PendenciaValidacaoRepository(db)
        self.suap_service = SUAPService()

    async def login_com_suap(self, token: str, semestre: str = "2026.1") -> dict:
        meus_dados = await self.suap_service.get_meus_dados(token)
        eu_dados = await self.suap_service.get_eu(token)

        suap_id = str(meus_dados.get("id", ""))
        nome = eu_dados.get("nome_usual", "") or eu_dados.get("nome", "") or meus_dados.get("nome", "")
        email = eu_dados.get("email", "") or meus_dados.get("email", "")
        campus = eu_dados.get("campus", "")

        matricula = ""
        tipo_vinculo = ""
        setor = ""
        try:
            vinculos = await self.suap_service.get_meus_vinculos(token)
            if vinculos:
                primeiro = vinculos[0]
                matricula = primeiro.get("identificador", "")
                tipo_vinculo = primeiro.get("tipo", "")
                if not campus:
                    campus = primeiro.get("campus", "") or ""
                detalhe = primeiro.get("detalhamento") or {}
                setor = detalhe.get("cargo", "") or detalhe.get("modalidade", "") or ""
        except Exception as e:
            logger.warning(f"Falha ao obter vinculos do SUAP: {e}")

        tipo_perfil = "aluno"
        if tipo_vinculo and tipo_vinculo.lower() not in ("aluno", "estudante"):
            tipo_perfil = "servidor"

        usuario_existente = self.usuario_repo.get_by_suap_id(suap_id)
        if usuario_existente and usuario_existente.aprovado_napne:
            tipo_perfil = "psicopedagogo"

        usuario = self.usuario_repo.get_by_suap_id(suap_id)
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
            usuario = self.usuario_repo.create(usuario_data)

        try:
            if tipo_perfil == "psicopedagogo":
                pass
            elif tipo_perfil in ("professor", "servidor"):
                await self._sincronizar_diarios_professor(usuario, token, semestre)
            else:
                disciplinas_raw = await self.suap_service.get_disciplinas(token, semestre)
                self._sincronizar_disciplinas(usuario.id, disciplinas_raw, semestre)
        except Exception as e:
            logger.warning(f"Falha ao sincronizar para usuario {usuario.id}: {e}")

        self.db.refresh(usuario)

        result = {
            "usuario": UsuarioSUAPResponse.model_validate(usuario),
            "tipo_perfil": tipo_perfil,
        }

        if tipo_perfil == "professor":
            result["disciplinas"] = [
                DisciplinaResponse.model_validate(d)
                for d in self.disciplina_repo.listar_por_usuario(usuario.id, semestre)
            ]
        else:
            result["disciplinas"] = [
                DisciplinaResponse.model_validate(d)
                for d in self.disciplina_repo.listar_por_usuario(usuario.id, semestre)
            ]

        return result

    async def _sincronizar_diarios_professor(self, usuario: Usuario, token: str, semestre: str):
        parts = semestre.split(".")
        ano_letivo = int(parts[0])
        periodo_letivo = int(parts[1]) if len(parts) > 1 else 1

        diarios_raw = await self.suap_service.get_meus_diarios(token, ano_letivo, periodo_letivo)
        logger.info(f"Professor {usuario.id}: {len(diarios_raw)} diarios encontrados no SUAP")

        self.disciplina_repo.deletar_por_usuario_e_semestre(usuario.id, semestre)

        alunos_assistidos_db = self.aluno_repo.list_all(limit=10000)
        assistidos_by_matricula = {}
        for a in alunos_assistidos_db:
            if a.matricula:
                assistidos_by_matricula[a.matricula] = a

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
                alunos_diario = await self.suap_service.get_alunos_diario(token, diario_id)
                logger.info(f"Diario {diario_id}: {len(alunos_diario)} alunos")

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
            except Exception as e:
                logger.warning(f"Falha ao buscar alunos do diario {diario_id}: {e}")

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
        if pendencia.status != "pendente":
            raise HTTPException(status_code=400, detail="Pendência já foi processada")
        from datetime import datetime
        update_data = {
            "status": acao,
            "validado_por_id": validado_por_id,
            "validado_em": datetime.utcnow(),
        }
        pendencia = self.pendencia_repo.update(pendencia_id, update_data)
        if acao in ("validado", "rejeitado") and pendencia.aluno_id:
            aluno = self.aluno_repo.get_by_id(pendencia.aluno_id)
            if aluno:
                if acao == "validado" and aluno.status_acompanhamento == "aguardando_indicacao":
                    aluno.status_acompanhamento = "ativo"
                elif acao == "rejeitado":
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
            "status": "pendente",
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
