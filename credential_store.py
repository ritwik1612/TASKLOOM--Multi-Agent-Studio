"""Per-user Gemini credential storage for the desktop distribution."""

from __future__ import annotations

from typing import Literal

SERVICE_NAME = "Taskloom Desktop"
CredentialSlot = Literal["primary", "backup"]


def _account_name(slot: CredentialSlot) -> str:
    return f"gemini-{slot}-api-key"


def _keyring_module():
    try:
        import keyring
    except ImportError:
        return None
    return keyring


def secure_storage_available() -> bool:
    """Return whether this installation can use the operating-system key store."""
    keyring = _keyring_module()
    if keyring is None:
        return False
    try:
        return keyring.get_keyring().priority > 0
    except Exception:
        return False


def get_api_key(slot: CredentialSlot) -> str | None:
    keyring = _keyring_module()
    if keyring is None:
        return None
    try:
        return keyring.get_password(SERVICE_NAME, _account_name(slot)) or None
    except Exception:
        return None


def save_api_key(slot: CredentialSlot, value: str) -> None:
    key = value.strip()
    if not key:
        raise ValueError("An API key cannot be empty.")
    keyring = _keyring_module()
    if keyring is None:
        raise RuntimeError("Secure credential storage is unavailable. Install the keyring package.")
    keyring.set_password(SERVICE_NAME, _account_name(slot), key)


def delete_api_key(slot: CredentialSlot) -> None:
    keyring = _keyring_module()
    if keyring is None or not get_api_key(slot):
        return
    keyring.delete_password(SERVICE_NAME, _account_name(slot))
