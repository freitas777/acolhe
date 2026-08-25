import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from backend.database import Base, get_db
from backend.models import (
    Usuario, ContaLocal, Aluno, PerfilAluno, Disciplina,
    DiarioAluno, PendenciaValidacao, Conversa, Mensagem, ConteudoGerado
)
from backend.security import hash_senha, criar_jwt
from main import app


@pytest.fixture(scope="function")
def db_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    TestingSessionLocal = sessionmaker(
        bind=db_engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def client(db_engine):
    TestingSessionLocal = sessionmaker(
        bind=db_engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def usuario_admin(db_engine):
    TestingSessionLocal = sessionmaker(bind=db_engine, autocommit=False, autoflush=False, expire_on_commit=False)
    session = TestingSessionLocal()
    try:
        usuario = Usuario(
            suap_id="admin_001",
            nome="Admin Teste",
            email="admin@test.com",
            tipo_perfil="admin",
            aprovado_napne=True,
        )
        session.add(usuario)
        session.commit()
        session.refresh(usuario)

        conta = ContaLocal(
            email="admin@test.com",
            senha_hash=hash_senha("admin123"),
            usuario_id=usuario.id,
            ativo=True,
            senha_temporaria=False,
        )
        session.add(conta)
        session.commit()

        token = criar_jwt({"usuario_id": usuario.id, "tipo_perfil": "admin"})
        return {
            "usuario": usuario,
            "conta": conta,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"},
        }
    finally:
        session.close()


@pytest.fixture
def usuario_psicopedagogo(db_engine):
    TestingSessionLocal = sessionmaker(bind=db_engine, autocommit=False, autoflush=False, expire_on_commit=False)
    session = TestingSessionLocal()
    try:
        usuario = Usuario(
            suap_id="psi_001",
            nome="Psicopedagogo Teste",
            email="psi@test.com",
            tipo_perfil="psicopedagogo",
            aprovado_napne=True,
        )
        session.add(usuario)
        session.commit()
        session.refresh(usuario)

        conta = ContaLocal(
            email="psi@test.com",
            senha_hash=hash_senha("psi123"),
            usuario_id=usuario.id,
            ativo=True,
            senha_temporaria=False,
        )
        session.add(conta)
        session.commit()

        token = criar_jwt({"usuario_id": usuario.id, "tipo_perfil": "psicopedagogo"})
        return {
            "usuario": usuario,
            "conta": conta,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"},
        }
    finally:
        session.close()


@pytest.fixture
def usuario_professor(db_engine):
    TestingSessionLocal = sessionmaker(bind=db_engine, autocommit=False, autoflush=False, expire_on_commit=False)
    session = TestingSessionLocal()
    try:
        usuario = Usuario(
            suap_id="prof_001",
            nome="Professor Teste",
            email="prof@test.com",
            tipo_perfil="professor",
            aprovado_napne=False,
        )
        session.add(usuario)
        session.commit()
        session.refresh(usuario)

        token = criar_jwt({"usuario_id": usuario.id, "tipo_perfil": "professor"})
        return {
            "usuario": usuario,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"},
        }
    finally:
        session.close()


@pytest.fixture
def usuario_aluno(db_engine):
    TestingSessionLocal = sessionmaker(bind=db_engine, autocommit=False, autoflush=False, expire_on_commit=False)
    session = TestingSessionLocal()
    try:
        usuario = Usuario(
            suap_id="aluno_001",
            nome="Aluno Teste",
            email="aluno@test.com",
            tipo_perfil="aluno",
            aprovado_napne=False,
        )
        session.add(usuario)
        session.commit()
        session.refresh(usuario)
        conta = ContaLocal(
            email="aluno@test.com",
            senha_hash=hash_senha("aluno123"),
            usuario_id=usuario.id,
            ativo=True,
            senha_temporaria=False,
        )
        session.add(conta)
        session.commit()
        token = criar_jwt({"usuario_id": usuario.id, "tipo_perfil": "aluno"})
        return {
            "usuario": usuario,
            "conta": conta,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"},
        }
    finally:
        session.close()


@pytest.fixture
def aluno_com_perfil(db_engine):
    TestingSessionLocal = sessionmaker(bind=db_engine, autocommit=False, autoflush=False, expire_on_commit=False)
    session = TestingSessionLocal()
    try:
        aluno = Aluno(
            nome="Aluno Exemplo",
            matricula="123456",
            suap_id="aluno_exemplo_001",
            curso="Curso Teste",
            campus="Campus Teste",
            status_acompanhamento="ativo",
        )
        session.add(aluno)
        session.commit()
        session.refresh(aluno)

        perfil = PerfilAluno(
            aluno_id=aluno.id,
            nivel_atencao="alto",
            dificuldade_leitura=True,
            preferencia="visual",
            interesses="jogos, musica",
            diagnostico="TEA",
        )
        session.add(perfil)
        session.commit()
        session.refresh(perfil)

        return {"aluno": aluno, "perfil": perfil}
    finally:
        session.close()
