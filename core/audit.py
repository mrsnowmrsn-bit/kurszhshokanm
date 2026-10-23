"""Аудит логтары және кіру әрекеттерін шектеу."""
from core.config import LOCK_MINUTES, MAX_FAILED_ATTEMPTS
from core.database import db

FAILED_LOGIN = "Кіру сәтсіз"


def log_action(username: str, action: str):
    with db() as conn:
        conn.execute(
            "INSERT INTO audit_logs (username, action) VALUES (?, ?)",
            (username, action),
        )


def is_locked(username: str) -> bool:
    """Соңғы LOCK_MINUTES минутта қате кіру саны шектен асты ма."""
    with db() as conn:
        n = conn.execute(
            "SELECT COUNT(*) FROM audit_logs WHERE username = ?"
            " AND action = ? AND timestamp > datetime('now', ?)",
            (username, FAILED_LOGIN, f"-{LOCK_MINUTES} minutes"),
        ).fetchone()[0]
    return n >= MAX_FAILED_ATTEMPTS
