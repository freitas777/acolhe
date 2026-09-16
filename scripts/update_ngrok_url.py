"""
Atualiza a SUAP_REDIRECT_URI no .env com a URL do ngrok.

Uso:
    python -m scripts.update_ngrok_url <nova-url-ngrok>

Exemplo:
    python -m scripts.update_ngrok_url https://abc123.ngrok-free.dev
"""
from __future__ import annotations

import sys
import re
from pathlib import Path


def update_redirect_uri(new_url: str) -> bool:
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        print(f"[ERRO] Arquivo .env não encontrado em {env_path}")
        return False

    content = env_path.read_text(encoding="utf-8")
    
    # Garantir que a URL termine com /
    if not new_url.endswith("/"):
        new_url += "/"
    
    # Substituir SUAP_REDIRECT_URI
    pattern = r'^SUAP_REDIRECT_URI=.*$'
    replacement = f'SUAP_REDIRECT_URI={new_url}'
    new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    if new_content == content:
        print(f"[WARN] SUAP_REDIRECT_URI não encontrado no .env")
        return False
    
    env_path.write_text(new_content, encoding="utf-8")
    print(f"[OK] SUAP_REDIRECT_URI atualizado para: {new_url}")
    print()
    print("PRÓXIMOS PASSOS:")
    print(f"1. Acesse https://suap.ifrn.edu.br/api/")
    print(f"2. Edite seu aplicativo OAuth")
    print(f"3. Adicione '{new_url}' em Redirect URIs")
    print(f"4. Reinicie o servidor: python main.py")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python -m scripts.update_ngrok_url <nova-url-ngrok>")
        print("Exemplo: python -m scripts.update_ngrok_url https://abc123.ngrok-free.dev")
        sys.exit(1)
    
    new_url = sys.argv[1]
    success = update_redirect_uri(new_url)
    sys.exit(0 if success else 1)
