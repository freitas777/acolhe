import hashlib
import hmac
import base64
import json
import time
from typing import Optional

from backend.config import settings


def hash_senha(senha: str) -> str:
    salt = settings.secret_key
    return hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt.encode("utf-8"), 100000).hex()


def verificar_senha(senha: str, senha_hash: str) -> bool:
    return hmac.compare_digest(hash_senha(senha), senha_hash)


_JWT_HEADER = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).rstrip(b"=")


def criar_jwt(payload: dict, expira_em_horas: int = 24) -> str:
    now = int(time.time())
    payload["iat"] = now
    payload["exp"] = now + (expira_em_horas * 3600)
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=")
    signing_input = _JWT_HEADER + b"." + payload_b64
    signature = hmac.new(settings.secret_key.encode(), signing_input, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).rstrip(b"=")
    return (signing_input + b"." + sig_b64).decode("utf-8")


def validar_jwt(token: str) -> Optional[dict]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64 = parts[0] + "=" * (4 - len(parts[0]) % 4)
        payload_b64 = parts[1] + "=" * (4 - len(parts[1]) % 4)
        sig_b64 = parts[2] + "=" * (4 - len(parts[2]) % 4)

        header = json.loads(base64.urlsafe_b64decode(header_b64))
        if header.get("alg") != "HS256":
            return None

        signing_input = (parts[0] + "." + parts[1]).encode()
        expected_sig = hmac.new(settings.secret_key.encode(), signing_input, hashlib.sha256).digest()
        actual_sig = base64.urlsafe_b64decode(sig_b64)
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        if payload.get("exp", 0) < int(time.time()):
            return None

        return payload
    except Exception:
        return None


def is_jwt_local(token: str) -> bool:
    return token.count(".") == 2 and len(token) < 500
