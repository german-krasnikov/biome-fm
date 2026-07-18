"""F300 — Cloud credential store. keyring when available, in-process dict fallback."""
from __future__ import annotations

import logging

try:
    import keyring as _keyring
except ImportError:
    _keyring = None  # type: ignore[assignment]

_FALLBACK: dict[tuple[str, str], str] = {}
_log = logging.getLogger(__name__)
_warned = False


def get_credential(service: str, account: str) -> str | None:
    """Return stored secret or None if not found."""
    if _keyring is not None:
        return _keyring.get_password(service, account)
    return _FALLBACK.get((service, account))


def set_credential(service: str, account: str, secret: str) -> None:
    global _warned
    if _keyring is not None:
        _keyring.set_password(service, account, secret)
    else:
        if not _warned:
            _log.warning(
                "keyring unavailable — credentials stored in memory only (not persisted)"
            )
            _warned = True
        _FALLBACK[(service, account)] = secret


def delete_credential(service: str, account: str) -> None:
    if _keyring is not None:
        _keyring.delete_password(service, account)
    else:
        _FALLBACK.pop((service, account), None)
