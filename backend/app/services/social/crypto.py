from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken


class SocialTokenDecryptError(Exception):
    """Falha segura de descriptografia de token social (sem expor segredo)."""


def validate_fernet_key(key: str | bytes) -> None:
    """Valida formato de chave Fernet sem ecoar o valor da chave."""
    try:
        key_bytes = key.encode() if isinstance(key, str) else key
        Fernet(key_bytes)
    except Exception as exc:
        raise ValueError("SOCIAL_TOKEN_ENCRYPTION_KEY inválida") from exc


def encrypt_token(plaintext: str, key: str | bytes) -> str:
    """Criptografa explicitamente um token social com Fernet e retorna texto."""
    key_bytes = key.encode() if isinstance(key, str) else key
    return Fernet(key_bytes).encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str, key: str | bytes) -> str:
    """Descriptografa explicitamente um token social com falha segura."""
    try:
        key_bytes = key.encode() if isinstance(key, str) else key
        return Fernet(key_bytes).decrypt(ciphertext.encode()).decode()
    except (InvalidToken, ValueError, TypeError) as exc:
        raise SocialTokenDecryptError(
            "token social inválido ou chave de criptografia incorreta"
        ) from exc
