from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import func, or_, select, exists
from sqlalchemy.orm import Session, selectinload

from backend.models.notificacao import Notificacao, NotificacaoLeitura
from backend.models.usuario import Usuario
from backend.repositories.base import BaseRepository


class NotificacaoRepository(BaseRepository[Notificacao]):
    def __init__(self, db: Session):
        super().__init__(Notificacao, db)

    def listar_por_destino(
        self,
        *,
        destino_tipo: str,
        destino_id: Optional[int],
        campus: Optional[str] = None,
        usuario_id: int = 0,
        skip: int = 0,
        limit: int = 20,
    ) -> Sequence[Notificacao]:
        excluida_subq = (
            select(NotificacaoLeitura.notificacao_id)
            .where(
                NotificacaoLeitura.usuario_id == usuario_id,
                NotificacaoLeitura.excluida.is_(True),
            )
            .correlate(Notificacao)
        )

        stmt = (
            select(Notificacao)
            .options(selectinload(Notificacao.aluno))
            .filter(~Notificacao.id.in_(excluida_subq))
        )

        filters = []
        if destino_tipo == "napne":
            napne_filter = Notificacao.destino_tipo == "napne"
            if campus:
                stmt_campus = (
                    select(Notificacao.id)
                    .join(Usuario, Notificacao.remetente_id == Usuario.id, isouter=True)
                    .where(
                        Notificacao.destino_tipo == "napne",
                        or_(
                            Usuario.campus == campus,
                            Usuario.campus.is_(None),
                        ),
                    )
                )
                stmt = stmt.filter(Notificacao.id.in_(stmt_campus))
            else:
                filters.append(napne_filter)
        else:
            filters.append(Notificacao.destino_tipo == destino_tipo)
            if destino_id is not None:
                filters.append(Notificacao.destino_id == destino_id)

        for f in filters:
            stmt = stmt.where(f)

        stmt = stmt.order_by(Notificacao.criada_em.desc()).offset(skip).limit(limit)
        result = self.db.execute(stmt)
        return result.unique().scalars().all()

    def contar_nao_lidas(
        self,
        *,
        destino_tipo: str,
        destino_id: Optional[int],
        campus: Optional[str] = None,
        usuario_id: int = 0,
    ) -> int:
        leitura_subq = (
            select(NotificacaoLeitura.notificacao_id)
            .where(NotificacaoLeitura.usuario_id == usuario_id)
            .correlate(Notificacao)
        )

        excluida_subq = (
            select(NotificacaoLeitura.notificacao_id)
            .where(
                NotificacaoLeitura.usuario_id == usuario_id,
                NotificacaoLeitura.excluida.is_(True),
            )
            .correlate(Notificacao)
        )

        base = (
            self.db.query(func.count(Notificacao.id))
            .filter(~Notificacao.id.in_(leitura_subq))
            .filter(~Notificacao.id.in_(excluida_subq))
        )

        if destino_tipo == "napne":
            base = base.filter(Notificacao.destino_tipo == "napne")
            if campus:
                base = (
                    base.join(Usuario, Notificacao.remetente_id == Usuario.id, isouter=True)
                    .filter(
                        or_(
                            Usuario.campus == campus,
                            Usuario.campus.is_(None),
                        )
                    )
                )
        else:
            base = base.filter(Notificacao.destino_tipo == destino_tipo)
            if destino_id is not None:
                base = base.filter(Notificacao.destino_id == destino_id)

        return base.scalar()

    def marcar_como_lida(self, notificacao_id: int, usuario_id: int) -> bool:
        n = self.get_by_id(notificacao_id)
        if n is None:
            return False
        existing = self.db.get(NotificacaoLeitura, (notificacao_id, usuario_id))
        if existing is None:
            leitura = NotificacaoLeitura(
                notificacao_id=notificacao_id, usuario_id=usuario_id
            )
            self.db.add(leitura)
            self.db.commit()
        return True

    def marcar_todas_como_lidas(
        self,
        *,
        destino_tipo: str,
        destino_id: Optional[int],
        campus: Optional[str] = None,
        usuario_id: int = 0,
    ) -> int:
        leitura_subq = (
            select(NotificacaoLeitura.notificacao_id)
            .where(NotificacaoLeitura.usuario_id == usuario_id)
            .correlate(Notificacao)
        )

        excluida_subq = (
            select(NotificacaoLeitura.notificacao_id)
            .where(
                NotificacaoLeitura.usuario_id == usuario_id,
                NotificacaoLeitura.excluida.is_(True),
            )
            .correlate(Notificacao)
        )

        stmt_q = (
            select(Notificacao.id)
            .filter(~Notificacao.id.in_(leitura_subq))
            .filter(~Notificacao.id.in_(excluida_subq))
        )

        if destino_tipo == "napne":
            stmt_q = stmt_q.filter(Notificacao.destino_tipo == "napne")
            if campus:
                stmt_q = (
                    stmt_q.join(Usuario, Notificacao.remetente_id == Usuario.id, isouter=True)
                    .filter(
                        or_(
                            Usuario.campus == campus,
                            Usuario.campus.is_(None),
                        )
                    )
                )
        else:
            stmt_q = stmt_q.filter(Notificacao.destino_tipo == destino_tipo)
            if destino_id is not None:
                stmt_q = stmt_q.filter(Notificacao.destino_id == destino_id)

        ids_to_mark = self.db.execute(stmt_q).scalars().all()
        if not ids_to_mark:
            return 0

        for nid in ids_to_mark:
            existing = self.db.get(NotificacaoLeitura, (nid, usuario_id))
            if existing is None:
                self.db.add(NotificacaoLeitura(notificacao_id=nid, usuario_id=usuario_id))

        self.db.commit()
        return len(ids_to_mark)

    def esta_lida(self, notificacao_id: int, usuario_id: int) -> bool:
        existing = self.db.get(NotificacaoLeitura, (notificacao_id, usuario_id))
        return existing is not None and not existing.excluida

    def excluir(self, notificacao_id: int, usuario_id: int) -> bool:
        n = self.get_by_id(notificacao_id)
        if n is None:
            return False
        leitura = self.db.get(NotificacaoLeitura, (notificacao_id, usuario_id))
        if leitura is None:
            leitura = NotificacaoLeitura(
                notificacao_id=notificacao_id, usuario_id=usuario_id, excluida=True
            )
            self.db.add(leitura)
        else:
            leitura.excluida = True
        self.db.commit()
        return True
