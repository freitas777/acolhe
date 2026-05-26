"""
Backfill PendenciaValidacao records for existing alunos with
status_acompanhamento='aguardando_indicacao' that have no pendencia.

Run:  python -m scripts.backfill_pendencias
"""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.database import SessionLocal
from backend.models.aluno import Aluno
from backend.models.pendencia_validacao import PendenciaValidacao
from sqlalchemy import select


def main():
    db = SessionLocal()
    try:
        alunos = (
            db.query(Aluno)
            .filter(Aluno.status_acompanhamento == "aguardando_indicacao")
            .all()
        )

        existing_aluno_ids = {
            row[0]
            for row in db.query(PendenciaValidacao.aluno_id)
            .filter(PendenciaValidacao.status == "pendente")
            .all()
        }

        created = 0
        for aluno in alunos:
            if aluno.id in existing_aluno_ids:
                continue
            pendencia = PendenciaValidacao(
                aluno_id=aluno.id,
                status="pendente",
                motivo="Aguardando indicacao",
                criado_em=aluno.data_importacao or aluno.criado_em,
            )
            db.add(pendencia)
            created += 1

        if created:
            db.commit()
            print(f"Backfill concluido: {created} pendencias criadas para alunos orfaos.")
        else:
            print("Nenhum aluno orfao encontrado. Nenhuma pendencia criada.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
