from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from backend.models.token_revogado import TokenRevogado


class TokenRevogadoRepository:
    def __init__(self, db: Session):
        self.db = db

    def revogar_token(self, jti: str, usuario_id: int, expira_em: datetime) -> TokenRevogado:
        token_revogado = TokenRevogado(
            jti=jti,
            usuario_id=usuario_id,
            expira_em=expira_em,
        )
        self.db.add(token_revogado)
        self.db.commit()
        self.db.refresh(token_revogado)
        return token_revogado

    def esta_revogado(self, jti: str) -> bool:
        token = self.db.query(TokenRevogado).filter(TokenRevogado.jti == jti).first()
        return token is not None

    def limpar_tokens_expirados(self, batch_size: int = 1000) -> int:
        total_removidos = 0
        agora = datetime.now(timezone.utc)
        while True:
            ids = [
                row[0] for row in
                self.db.query(TokenRevogado.id).filter(
                    TokenRevogado.expira_em < agora
                ).limit(batch_size).all()
            ]
            if not ids:
                break
            self.db.query(TokenRevogado).filter(
                TokenRevogado.id.in_(ids)
            ).delete(synchronize_session=False)
            self.db.commit()
            total_removidos += len(ids)
            if len(ids) < batch_size:
                break
        return total_removidos
