"""
Seed de dados de demonstracao para Professor e NAPNE.

Cria usuarios ficticios com login local (ContaLocal), disciplinas
mockadas e vincula alunos reais ja existentes no banco as turmas
dos professores demo.

Uso:
    python -m scripts.seed_demo

Idempotente: pode ser executado multiplas vezes sem duplicar dados.
"""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from backend.database import SessionLocal
from backend.models.usuario import Usuario
from backend.models.conta_local import ContaLocal
from backend.models.disciplina import Disciplina
from backend.models.diario_aluno import DiarioAluno
from backend.models.aluno import Aluno
from backend.repositories.usuario import UsuarioRepository
from backend.repositories.conta_local import ContaLocalRepository
from backend.repositories.disciplina import DisciplinaRepository
from backend.repositories.diario_aluno import DiarioAlunoRepository
from backend.repositories.aluno import AlunoRepository
from backend.security import hash_senha
from backend.config import settings


DEMO_USERS = [
    {
        "suap_id": "demo_prof_1",
        "nome": "Professor Demo (Matematica)",
        "email": "professor.demo@ifrn.edu.br",
        "senha": "professor123",
        "tipo_perfil": "professor",
        "aprovado_napne": False,
        "matricula": "DEMO-PROF-001",
        "campus": "Natal-Central",
    },
    {
        "suap_id": "demo_prof_2",
        "nome": "Professora Demo (Informatica)",
        "email": "professora.demo@ifrn.edu.br",
        "senha": "professor123",
        "tipo_perfil": "professor",
        "aprovado_napne": False,
        "matricula": "DEMO-PROF-002",
        "campus": "Natal-Central",
    },
    {
        "suap_id": "demo_napne_1",
        "nome": "Equipe NAPNE Demo",
        "email": "napne.demo@ifrn.edu.br",
        "senha": "napne123",
        "tipo_perfil": "psicopedagogo",
        "aprovado_napne": True,
        "matricula": "DEMO-NAPNE-001",
        "campus": "Natal-Central",
    },
]

DEMO_DISCIPLINAS = [
    {
        "professor_suap_id": "demo_prof_1",
        "disciplinas": [
            {"suap_id": 900001, "sigla": "MAT.001", "descricao": "Matematica Basica", "codigo_turma": "MAT.001-2026.1", "semestre": "2026.1"},
            {"suap_id": 900002, "sigla": "MAT.002", "descricao": "Algebra Linear", "codigo_turma": "MAT.002-2026.1", "semestre": "2026.1"},
            {"suap_id": 900003, "sigla": "MAT.003", "descricao": "Calculo Diferencial e Integral", "codigo_turma": "MAT.003-2026.1", "semestre": "2026.1"},
        ],
    },
    {
        "professor_suap_id": "demo_prof_2",
        "disciplinas": [
            {"suap_id": 900011, "sigla": "INF.001", "descricao": "Programacao Web", "codigo_turma": "INF.001-2026.1", "semestre": "2026.1"},
            {"suap_id": 900012, "sigla": "INF.002", "descricao": "Banco de Dados", "codigo_turma": "INF.002-2026.1", "semestre": "2026.1"},
            {"suap_id": 900013, "sigla": "INF.003", "descricao": "Engenharia de Software", "codigo_turma": "INF.003-2026.1", "semestre": "2026.1"},
            {"suap_id": 900014, "sigla": "INF.004", "descricao": "Estrutura de Dados", "codigo_turma": "INF.004-2026.1", "semestre": "2026.1"},
        ],
    },
]

FALLBACK_ALUNOS = [
    {"nome": "Aluno Demo 1 - Ana Silva", "matricula": "DEMO.2024.001", "email": "ana.demo@academico.ifrn.edu.br"},
    {"nome": "Aluno Demo 2 - Bruno Costa", "matricula": "DEMO.2024.002", "email": "bruno.demo@academico.ifrn.edu.br"},
    {"nome": "Aluno Demo 3 - Carla Souza", "matricula": "DEMO.2024.003", "email": "carla.demo@academico.ifrn.edu.br"},
    {"nome": "Aluno Demo 4 - Diego Lima", "matricula": "DEMO.2024.004", "email": "diego.demo@academico.ifrn.edu.br"},
    {"nome": "Aluno Demo 5 - Eduarda Martins", "matricula": "DEMO.2024.005", "email": "eduarda.demo@academico.ifrn.edu.br"},
    {"nome": "Aluno Demo 6 - Felipe Rocha", "matricula": "DEMO.2024.006", "email": "felipe.demo@academico.ifrn.edu.br"},
    {"nome": "Aluno Demo 7 - Gabriela Alves", "matricula": "DEMO.2024.007", "email": "gabriela.demo@academico.ifrn.edu.br"},
    {"nome": "Aluno Demo 8 - Hugo Pereira", "matricula": "DEMO.2024.008", "email": "hugo.demo@academico.ifrn.edu.br"},
]


def _upsert_usuario(db, usuario_repo: UsuarioRepository, conta_repo: ContaLocalRepository, data: dict) -> Usuario:
    usuario = usuario_repo.get_by_suap_id(data["suap_id"])
    if usuario:
        for key in ("nome", "email", "tipo_perfil", "aprovado_napne", "matricula", "campus"):
            if key in data and getattr(usuario, key, None) != data[key]:
                setattr(usuario, key, data[key])
        db.commit()
        db.refresh(usuario)
        print(f"  [UPDATE] Usuario existente atualizado: {usuario.nome} ({usuario.email})")
    else:
        usuario = usuario_repo.create({
            "suap_id": data["suap_id"],
            "nome": data["nome"],
            "email": data["email"],
            "tipo_perfil": data["tipo_perfil"],
            "aprovado_napne": data.get("aprovado_napne", False),
            "matricula": data.get("matricula"),
            "campus": data.get("campus"),
        })
        print(f"  [CREATE] Usuario criado: {usuario.nome} ({usuario.email}) [id={usuario.id}]")

    conta = conta_repo.get_by_usuario_id(usuario.id)
    if conta:
        conta.senha_hash = hash_senha(data["senha"])
        conta.senha_temporaria = False
        conta.ativo = True
        db.commit()
        print(f"  [UPDATE] ContaLocal atualizada (senha redefinida, senha_temporaria=False)")
    else:
        conta_repo.create({
            "email": data["email"],
            "senha_hash": hash_senha(data["senha"]),
            "usuario_id": usuario.id,
            "ativo": True,
            "senha_temporaria": False,
        })
        print(f"  [CREATE] ContaLocal criada para {data['email']}")

    return usuario


def _upsert_disciplinas(db, disciplina_repo: DisciplinaRepository, professor: Usuario, disciplinas_cfg: list[dict]) -> list[Disciplina]:
    result: list[Disciplina] = []
    for d in disciplinas_cfg:
        existente = db.query(Disciplina).filter(
            Disciplina.suap_id == d["suap_id"],
            Disciplina.usuario_id == professor.id,
        ).first()
        if existente:
            for key in ("descricao", "sigla", "codigo_turma", "semestre"):
                if key in d and getattr(existente, key, None) != d[key]:
                    setattr(existente, key, d[key])
            db.commit()
            db.refresh(existente)
            result.append(existente)
            print(f"    [UPDATE] Disciplina: {existente.sigla} - {existente.descricao}")
        else:
            nova = disciplina_repo.create({
                "suap_id": d["suap_id"],
                "diario_id": d["suap_id"],
                "descricao": d["descricao"],
                "sigla": d["sigla"],
                "codigo_turma": d["codigo_turma"],
                "situacao": "Em andamento",
                "professor": professor.nome,
                "semestre": d["semestre"],
                "usuario_id": professor.id,
            })
            result.append(nova)
            print(f"    [CREATE] Disciplina: {nova.sigla} - {nova.descricao} [id={nova.id}]")
    return result


def _garantir_alunos_disponiveis(db, aluno_repo: AlunoRepository) -> list[Aluno]:
    alunos_ativos = aluno_repo.listar_por_status("ativo")
    if len(alunos_ativos) >= 5:
        print(f"  [OK] {len(alunos_ativos)} alunos reais ativos encontrados no banco")
        return alunos_ativos

    print(f"  [WARN] Apenas {len(alunos_ativos)} alunos ativos no banco. Criando alunos fallback demo...")
    fallback_ids: list[Aluno] = list(alunos_ativos)
    for fa in FALLBACK_ALUNOS:
        existente = aluno_repo.get_by_matricula(fa["matricula"])
        if existente:
            fallback_ids.append(existente)
            continue
        novo = aluno_repo.create({
            "nome": fa["nome"],
            "matricula": fa["matricula"],
            "email": fa["email"],
            "suap_id": f"demo_aluno_{fa['matricula']}",
            "curso": "Tecnologo em Analise e Desenvolvimento de Sistemas",
            "campus": "Natal-Central",
            "status_acompanhamento": "ativo",
        })
        fallback_ids.append(novo)
        print(f"    [CREATE] Aluno fallback: {novo.nome} ({novo.matricula})")
    return fallback_ids


def _vincular_alunos_turmas(
    db,
    diario_repo: DiarioAlunoRepository,
    disciplinas: list[Disciplina],
    alunos: list[Aluno],
    alunos_por_turma: int = 6,
) -> int:
    criados = 0
    if not alunos:
        return 0

    for idx, disc in enumerate(disciplinas):
        offset = (idx * 2) % len(alunos)
        selecionados = (alunos * 2)[offset:offset + alunos_por_turma]
        for aluno in selecionados:
            existente = diario_repo.get_by_disciplina_aluno(disc.id, aluno.id)
            if existente:
                continue
            diario_repo.create({
                "disciplina_id": disc.id,
                "aluno_id": aluno.id,
                "aluno_nome": aluno.nome,
                "aluno_matricula": aluno.matricula or "",
            })
            criados += 1
    return criados


def main() -> int:
    print("=" * 60)
    print("SEED DEMO - Professor e NAPNE (Acolhe+)")
    print("=" * 60)

    db = SessionLocal()
    try:
        usuario_repo = UsuarioRepository(db)
        conta_repo = ContaLocalRepository(db)
        disciplina_repo = DisciplinaRepository(db)
        diario_repo = DiarioAlunoRepository(db)
        aluno_repo = AlunoRepository(db)

        print("\n[1/4] Criando/atualizando usuarios demo...")
        professores: dict[str, Usuario] = {}
        for u in DEMO_USERS:
            usuario = _upsert_usuario(db, usuario_repo, conta_repo, u)
            if u["tipo_perfil"] == "professor":
                professores[u["suap_id"]] = usuario

        print("\n[2/4] Criando/atualizando disciplinas demo...")
        todas_disciplinas: list[Disciplina] = []
        for grupo in DEMO_DISCIPLINAS:
            prof = professores.get(grupo["professor_suap_id"])
            if not prof:
                print(f"  [SKIP] Professor {grupo['professor_suap_id']} nao encontrado")
                continue
            print(f"  Professor: {prof.nome}")
            disciplinas = _upsert_disciplinas(db, disciplina_repo, prof, grupo["disciplinas"])
            todas_disciplinas.extend(disciplinas)

        print("\n[3/4] Verificando alunos disponiveis para vincular as turmas...")
        alunos = _garantir_alunos_disponiveis(db, aluno_repo)

        print("\n[4/4] Vinculando alunos as disciplinas demo...")
        vinculos_criados = _vincular_alunos_turmas(db, diario_repo, todas_disciplinas, alunos)
        print(f"  {vinculos_criados} novos vinculos diario_aluno criados")

        print("\n" + "=" * 60)
        print("SEED CONCLUIDO")
        print("=" * 60)
        print("\nCredenciais de acesso:")
        for u in DEMO_USERS:
            print(f"  {u['tipo_perfil'].upper():14s} | {u['email']:40s} | senha: {u['senha']}")
        print()
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
