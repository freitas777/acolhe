import hashlib
import hmac
import base64
import json
import os
import time
from typing import Optional

from backend.config import settings

def _get_legacy_keys() -> list:
    raw = settings.legacy_secret_keys
    if not raw:
        return []
    return [k.strip() for k in raw.split(",") if k.strip()]


def hash_senha(senha: str) -> str:
    salt = os.urandom(16).hex()
    hash_val = hashlib.pbkdf2_hmac(
        "sha256", senha.encode("utf-8"), salt.encode("utf-8"), 100000
    ).hex()
    return f"{salt}${hash_val}"


def verificar_senha(senha: str, senha_hash: str) -> bool:
    if "$" in senha_hash:
        salt, stored_hash = senha_hash.split("$", 1)
        computed = hashlib.pbkdf2_hmac(
            "sha256", senha.encode("utf-8"), salt.encode("utf-8"), 100000
        ).hex()
        return hmac.compare_digest(computed, stored_hash)
    for key in [settings.secret_key] + _get_legacy_keys():
        legacy_hash = hashlib.pbkdf2_hmac(
            "sha256", senha.encode("utf-8"), key.encode("utf-8"), 100000
        ).hex()
        if hmac.compare_digest(legacy_hash, senha_hash):
            return True
    return False


_JWT_HEADER = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "acolhe-local"}).encode()).rstrip(b"=")


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
        if header.get("typ") != "acolhe-local":
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
    if token.count(".") != 2:
        return False
    if len(token) >= 500:
        return False
    try:
        header_b64 = token.split(".")[0]
        padding = 4 - len(header_b64) % 4
        if padding != 4:
            header_b64 += "=" * padding
        header = json.loads(base64.urlsafe_b64decode(header_b64))
        return header.get("typ") == "acolhe-local"
    except Exception:
        return False
