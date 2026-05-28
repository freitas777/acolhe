import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from backend.database import SessionLocal
from backend.models.usuario import Usuario
from backend.models.conta_local import ContaLocal
from backend.repositories.usuario import UsuarioRepository
from backend.repositories.conta_local import ContaLocalRepository
from backend.security import hash_senha


def create_admin(email: str, senha: str, nome: str):
    db = SessionLocal()
    try:
        conta_repo = ContaLocalRepository(db)
        existing = conta_repo.get_by_email(email)
        if existing:
            print(f"[SKIP] Conta local ja existe para: {email}")
            return

        usuario_repo = UsuarioRepository(db)
        usuario = usuario_repo.create({
            "suap_id": f"local_{email}",
            "nome": nome,
            "email": email,
            "tipo_perfil": "admin",
            "aprovado_napne": True,
        })

        conta = conta_repo.create({
            "email": email,
            "senha_hash": hash_senha(senha),
            "usuario_id": usuario.id,
            "ativo": True,
        })

        print(f"[OK] Admin criado: {nome} ({email})")
        print(f"     Usuario ID: {usuario.id}")
        print(f"     Conta ID:   {conta.id}")
    except Exception as e:
        print(f"[ERRO] {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    email = input("Email do admin: ").strip()
    senha = input("Senha do admin: ").strip()
    nome = input("Nome do admin: ").strip()
    if not email or not senha or not nome:
        print("Todos os campos sao obrigatorios.")
        sys.exit(1)
    create_admin(email, senha, nome)
