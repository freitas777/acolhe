from __future__ import annotations

from sqlalchemy.orm import Session, selectinload

from backend.models.aluno import Aluno
from backend.models.conteudo_gerado import ConteudoGerado
from backend.models.perfil_aluno import PerfilAluno
from backend.schemas.portal import PerfilAlunoSelfUpdate


class PortalService:
    def __init__(self, db: Session):
        self.db = db

    def obter_meu_perfil(self, suap_id: str) -> Aluno | None:
        return (
            self.db.query(Aluno)
            .options(selectinload(Aluno.perfil))
            .filter(Aluno.suap_id == suap_id)
            .first()
        )

    def atualizar_meu_perfil(
        self, suap_id: str, data: PerfilAlunoSelfUpdate
    ) -> PerfilAluno:
        aluno = (
            self.db.query(Aluno)
            .options(selectinload(Aluno.perfil))
            .filter(Aluno.suap_id == suap_id)
            .first()
        )
        if not aluno:
            raise ValueError("Aluno nao encontrado para o suap_id informado")

        perfil = aluno.perfil
        if not perfil:
            perfil = PerfilAluno(aluno_id=aluno.id)
            self.db.add(perfil)
            self.db.flush()

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(perfil, key, value)

        self.db.commit()
        self.db.refresh(perfil)
        return perfil

    def listar_meus_conteudos(self, suap_id: str) -> list:
        from backend.models.conversa import Conversa
        from backend.schemas.portal import ConteudoPortalResponse
        
        aluno = (
            self.db.query(Aluno)
            .filter(Aluno.suap_id == suap_id)
            .first()
        )
        if not aluno:
            return []

        conteudos_gerados = (
            self.db.query(ConteudoGerado)
            .filter(ConteudoGerado.aluno_id == aluno.id)
            .all()
        )

        conversas = (
            self.db.query(Conversa)
            .options(selectinload(Conversa.mensagens), selectinload(Conversa.usuario))
            .filter(Conversa.aluno_id == aluno.id)
            .all()
        )

        resultado = []
        
        for cg in conteudos_gerados:
            resultado.append(ConteudoPortalResponse(
                id=str(cg.id),
                tipo="conteudo_gerado",
                titulo=cg.tema,
                data=cg.gerado_em,
                conteudo=cg.conteudo,
                modelo_ia=cg.modelo_ia,
                versao=cg.versao,
            ))
        
        for conv in conversas:
            usuario_tipo = None
            if conv.usuario:
                usuario_tipo = conv.usuario.tipo_perfil
            
            resultado.append(ConteudoPortalResponse(
                id=conv.id,
                tipo="conversa",
                titulo=conv.titulo,
                data=conv.atualizada_em,
                conteudo=None,
                modelo_ia=None,
                versao=None,
                usuario_tipo=usuario_tipo,
                messages=[
                    {
                        "id": m.id,
                        "role": m.papel,
                        "content": m.conteudo,
                        "created_at": m.criada_em,
                    }
                    for m in conv.mensagens
                ],
            ))
        
        resultado.sort(key=lambda x: x.data, reverse=True)
        return resultado

    def obter_conteudo(self, suap_id: str, conteudo_id: int) -> ConteudoGerado | None:
        aluno = (
            self.db.query(Aluno)
            .filter(Aluno.suap_id == suap_id)
            .first()
        )
        if not aluno:
            return None

        conteudo = (
            self.db.query(ConteudoGerado)
            .filter(
                ConteudoGerado.id == conteudo_id,
                ConteudoGerado.aluno_id == aluno.id,
            )
            .first()
        )
        return conteudo


