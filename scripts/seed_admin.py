"""Script para criar usuário admin inicial com conta local."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import SessionLocal
from backend.models.usuario import Usuario
from backend.models.conta_local import ContaLocal
from backend.security import hash_senha


def seed_admin(
    email: str,
    nome: str,
    senha: str,
):
    """Cria usuário admin com conta local."""
    db = SessionLocal()
    
    try:
        existing = db.query(Usuario).filter(Usuario.email == email).first()
        if existing:
            print(f"[!] Usuário com email {email} já existe (id={existing.id})")
            return
        
        usuario = Usuario(
            suap_id=f"local_{email}",
            nome=nome,
            email=email,
            tipo_perfil="admin",
            aprovado_napne=True,
        )
        db.add(usuario)
        db.flush()
        
        conta = ContaLocal(
            email=email,
            senha_hash=hash_senha(senha),
            usuario_id=usuario.id,
            ativo=True,
            senha_temporaria=False,
        )
        db.add(conta)
        db.commit()
        
        print(f"[OK] Admin criado com sucesso!")
        print(f"  Email: {email}")
        print(f"  Senha: {senha}")
        print(f"  ID: {usuario.id}")
        print(f"\n[!] IMPORTANTE: Altere a senha após o primeiro login!")
        
    except Exception as e:
        db.rollback()
        print(f"[ERRO] Falha ao criar admin: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Uso: python seed_admin.py <email> <nome> <senha>")
        print("Exemplo: python seed_admin.py admin@acolhe.com Administrador MinhaSenhaForte123!")
        sys.exit(1)

    email = sys.argv[1]
    nome = sys.argv[2]
    senha = sys.argv[3]

    if len(senha) < 8:
        print("[ERRO] A senha deve ter pelo menos 8 caracteres.")
        sys.exit(1)

    seed_admin(email, nome, senha)
