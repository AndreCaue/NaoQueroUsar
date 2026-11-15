"""SOC-04: crypto dedicada Fernet para tokens sociais (sem DB)."""

from __future__ import annotations

import pytest
from cryptography.fernet import Fernet

from app.services.social.crypto import (
    SocialTokenDecryptError,
    decrypt_token,
    encrypt_token,
    validate_fernet_key,
)


def test_encrypt_decrypt_roundtrip_returns_plaintext() -> None:
    key = Fernet.generate_key().decode()
    plaintext = "page-access-token-secreto"

    ciphertext = encrypt_token(plaintext, key)

    assert isinstance(ciphertext, str)
    assert ciphertext != plaintext
    assert decrypt_token(ciphertext, key) == plaintext


def test_decrypt_with_wrong_key_raises_safe_domain_error() -> None:
    key = Fernet.generate_key().decode()
    other_key = Fernet.generate_key().decode()
    ciphertext = encrypt_token("segredo", key)

    with pytest.raises(SocialTokenDecryptError) as excinfo:
        decrypt_token(ciphertext, other_key)

    msg = str(excinfo.value)
    assert msg == "token social inválido ou chave de criptografia incorreta"
    assert "segredo" not in msg
    assert key not in msg
    assert other_key not in msg
    assert ciphertext not in msg


def test_decrypt_invalid_ciphertext_raises_safe_domain_error() -> None:
    key = Fernet.generate_key().decode()

    with pytest.raises(SocialTokenDecryptError) as excinfo:
        decrypt_token("not-a-fernet-token", key)

    assert str(excinfo.value) == "token social inválido ou chave de criptografia incorreta"


def test_validate_fernet_key_accepts_valid_key_and_rejects_invalid_without_echo() -> None:
    valid = Fernet.generate_key().decode()
    validate_fernet_key(valid)
    validate_fernet_key(valid.encode())

    bad = "chave-invalida"
    with pytest.raises(ValueError) as excinfo:
        validate_fernet_key(bad)

    msg = str(excinfo.value)
    assert msg == "SOCIAL_TOKEN_ENCRYPTION_KEY inválida"
    assert bad not in msg
