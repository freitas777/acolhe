"""
Backfill de conteudo_texto para materiais ja existentes.

Extrai o texto interno dos arquivos (PDF/DOCX/PPTX/TXT) ja salvos
e preenche a coluna `materiais.conteudo_texto`.

Idempotente: processa apenas materiais sem texto extraido.

Uso:
    python -m scripts.backfill_materiais_texto
"""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from pathlib import Path

from sqlalchemy import or_

from backend.config import settings
from backend.database import SessionLocal
from backend.models.material import Material
from backend.services.text_extractor import extrair_texto


def _get_ext(nome: str) -> str:
    return (nome or "").split(".")[-1].lower()


def main() -> int:
    db = SessionLocal()
    try:
        materiais = (
            db.query(Material)
            .filter(or_(Material.conteudo_texto.is_(None), Material.conteudo_texto == ""))
            .all()
        )

        if not materiais:
            print("Nenhum material sem texto extraido.")
            return 0

        base = Path(settings.uploads_dir) / "materiais"
        atualizados = 0

        for m in materiais:
            path = base / m.nome_arquivo
            if not path.exists():
                print(f"  [SKIP] arquivo nao encontrado: {m.nome_arquivo}")
                continue

            ext = _get_ext(m.nome_original or m.nome_arquivo)
            try:
                texto = extrair_texto(ext, path.read_bytes())
            except Exception as e:
                print(f"  [ERRO] {m.nome_original}: {e}")
                continue

            if texto:
                m.conteudo_texto = texto
                db.commit()
                atualizados += 1
                print(f"  [OK] {m.nome_original}: {len(texto)} caracteres")
            else:
                print(f"  [SEM TEXTO] {m.nome_original} (tipo .{ext})")

        print(f"\n{atualizados} material(is) atualizado(s).")
        return 0
    except Exception as e:
        db.rollback()
        print(f"\n[ERRO] {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())