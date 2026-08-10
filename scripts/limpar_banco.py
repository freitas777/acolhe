"""Script para limpar todos os dados das tabelas sem dropar o banco ou as tabelas."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text

from backend.database import engine, Base

TABELAS_ORDEM = [
    "notificacao_leitura",
    "notificacoes",
    "mensagens",
    "conversas",
    "conteudo_feedback",
    "conteudos_gerados",
    "acomodacao_observacoes",
    "diario_alunos",
    "pendencias_validacao",
    "materiais",
    "disciplinas",
    "perfis_aluno",
    "alunos",
    "audit_logs",
    "tokens_revogados",
    "contas_locais",
    "usuarios",
]


def obter_tabelas_existentes(conn) -> list[str]:
    result = conn.execute(
        text("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
    )
    return [row[0] for row in result]


def limpar(confirmar: bool = True) -> None:
    if confirmar:
        resp = input(
            "[!] Isso vai apagar TODOS os dados de todas as tabelas.\n"
            "Digite 'SIM' para confirmar: "
        )
        if resp.strip() != "SIM":
            print("Operacao cancelada.")
            return

    with engine.begin() as conn:
        tabelas_existentes = obter_tabelas_existentes(conn)
        tabelas_para_limpar = [t for t in TABELAS_ORDEM if t in tabelas_existentes]
        tabelas_faltando = [t for t in TABELAS_ORDEM if t not in tabelas_existentes]

        if tabelas_faltando:
            print(f"  [!] Tabelas nao encontradas (ignoradas): {', '.join(tabelas_faltando)}")

        conn.execute(text("SET session_replication_role = 'replica';"))
        for tabela in tabelas_para_limpar:
            print(f"  Limpando {tabela}...")
            conn.execute(text(f'TRUNCATE TABLE "{tabela}" RESTART IDENTITY CASCADE;'))
        conn.execute(text("SET session_replication_role = 'origin';"))

    print("[OK] Banco limpo com sucesso.")


if __name__ == "__main__":
    skip_confirm = "--yes" in sys.argv or "-y" in sys.argv
    limpar(confirmar=not skip_confirm)
