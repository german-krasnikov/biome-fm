"""F300 — Cloud credential store. keyring when available, in-process dict fallback."""
from __future__ import annotations

import logging

try:
    import keyring as _keyring
except ImportError:
    _keyring = None  # type: ignore[assignment]

CRED_SERVICE = "biome-fm"
_FALLBACK: dict[tuple[str, str], str] = {}
_log = logging.getLogger(__name__)
_warned = False


def _warn_unavailable() -> None:
    global _warned
    if not _warned:
        _log.warning("keyring unavailable — credentials stored in memory only (not persisted)")
        _warned = True


def get_credential(service: str, account: str) -> str | None:
    """Return stored secret or None if not found."""
    if _keyring is not None:
        try:
            return _keyring.get_password(service, account)
        except Exception:
            _warn_unavailable()
    return _FALLBACK.get((service, account))


def set_credential(service: str, account: str, secret: str) -> bool:
    """Store secret. Returns True if durably persisted, False if only in-process fallback."""
    if _keyring is not None:
        try:
            _keyring.set_password(service, account, secret)
            return True
        except Exception:
            _log.warning("keyring set_password failed — falling back to in-process store")
    _warn_unavailable()
    _FALLBACK[(service, account)] = secret
    return False


def delete_credential(service: str, account: str) -> None:
    if _keyring is not None:
        try:
            _keyring.delete_password(service, account)
        except Exception:
            _log.debug("keyring delete_password failed for %s/%s", service, account, exc_info=True)
    _FALLBACK.pop((service, account), None)
