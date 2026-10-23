"""Дерекқормен жұмыс: қосылым, сұраулар, инициализация."""
import sqlite3
from contextlib import contextmanager

import pandas as pd

from core.config import DB_NAME, DEFAULT_ADMIN_PASSWORD
from core.schema import DEFAULT_SUBJECTS, TABLES, UNIQUE_SUBMISSION_INDEX
from core.security import hash_password


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@contextmanager
def db():
    """Қосылымды әрдайым жабатын контекст менеджер (қате болса rollback)."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def query_df(sql: str, params=()) -> pd.DataFrame:
    with db() as conn:
        return pd.read_sql_query(sql, conn, params=params)


def groups_list() -> list:
    df = query_df("SELECT DISTINCT group_name FROM students ORDER BY group_name")
    return df["group_name"].tolist()


def init_db():
    with db() as conn:
        for ddl in TABLES:
            conn.execute(ddl)
        try:
            conn.execute(UNIQUE_SUBMISSION_INDEX)
        except sqlite3.IntegrityError:
            pass  # ескі дубликаттар болса, код деңгейінде тексеріледі

        has_admin = conn.execute(
            "SELECT COUNT(*) FROM users WHERE role = 'ADMIN'"
        ).fetchone()[0]
        if has_admin == 0:
            conn.execute(
                "INSERT INTO users (username, password_hash, full_name, role)"
                " VALUES (?, ?, ?, ?)",
                (
                    "admin",
                    hash_password(DEFAULT_ADMIN_PASSWORD),
                    "Бас Администратор",
                    "ADMIN",
                ),
            )
            conn.executemany(
                "INSERT OR IGNORE INTO subjects (subject_name, credits)"
                " VALUES (?, ?)",
                DEFAULT_SUBJECTS,
            )
