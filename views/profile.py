"""Профиль беті: жеке мәлімет, статистика, қауіпсіздік (барлық рөлге ортақ)."""
import streamlit as st

from core.audit import log_action
from core.config import ROLE_LABELS
from core.database import db, query_df
from core.gpa import calculate_gpa
from core.ui import esc, flash, show_df, stat_card
from views.common import render_password_change

LOGIN_OK = "Жүйеге сәтті кірді"


def _count(table: str) -> int:
    # table атауы тек осы файлдағы тұрақтылардан беріледі
    return int(query_df(f"SELECT COUNT(*) AS n FROM {table}")["n"][0])


def _cards(cards: list, per_row: int = 3):
    for start in range(0, len(cards), per_row):
        row = cards[start:start + per_row]
        for col, (title, value, icon) in zip(st.columns(per_row), row):
            with col:
                stat_card(title, value, icon)


def _previous_login(username: str) -> str:
    """Ағымдағы кіруден бұрынғы соңғы кіру уақыты (UTC)."""
    df = query_df(
        "SELECT timestamp FROM audit_logs WHERE username = ? AND action = ?"
        " ORDER BY timestamp DESC LIMIT 2",
        (username, LOGIN_OK),
    )
    return str(df["timestamp"].iloc[1]) if len(df) > 1 else "—"


def _role_stats(user: dict) -> list:
    role = user["role"]
    if role == "STUDENT":
        stud = query_df(
            "SELECT id, student_code, group_name, course_num FROM students"
            " WHERE user_id = ?",
            (user["id"],),
        )
        if stud.empty:
            return []
        s = stud.iloc[0]
        grades = query_df(
            """SELECT sub.credits AS 'Кредит', g.grade AS 'Баға',
                      g.attendance AS 'Қатысуы'
               FROM grades g JOIN subjects sub ON g.subject_id = sub.id
               WHERE g.student_id = ?""",
            (int(s["id"]),),
        )
        gpa = calculate_gpa(grades) if not grades.empty else 0.0
        att = (
            round(100 * (grades["Қатысуы"] == "Қатысты").mean())
            if not grades.empty else 0
        )
        return [
            ("Студент коды", s["student_code"], "🪪"),
            ("Топ", s["group_name"], "🏫"),
            ("Курс", int(s["course_num"]), "📅"),
            ("GPA", f"{gpa} / 4.0", "🎓"),
            ("Қатысу", f"{att}%", "✅"),
            ("Бағалар саны", len(grades), "📝"),
        ]
    if role == "TEACHER":
        return [
            ("Студенттер", _count("students"), "🎓"),
            ("Қойылған бағалар", _count("grades"), "📝"),
            ("Берілген тапсырмалар", _count("homeworks"), "📌"),
        ]
    return [  # ADMIN
        ("Студенттер", _count("students"), "🎓"),
        ("Пайдаланушылар", _count("users"), "👥"),
        ("Пәндер", _count("subjects"), "📚"),
    ]


def _edit_form(user: dict):
    st.subheader("✏️ Жеке мәлімет")
    with st.form("profile_edit"):
        st.text_input("Пайдаланушы аты", value=user["username"], disabled=True)
        new_name = st.text_input(
            "Толық аты-жөні", value=user["full_name"]
        ).strip()
        submitted = st.form_submit_button("Сақтау", type="primary")
    if not submitted:
        return
    if not new_name:
        st.warning("Аты-жөні бос болмауы керек.")
        return
    with db() as conn:
        conn.execute(
            "UPDATE users SET full_name = ? WHERE id = ?",
            (new_name, user["id"]),
        )
        conn.execute(
            "UPDATE students SET full_name = ? WHERE user_id = ?",
            (new_name, user["id"]),
        )
    st.session_state.user_info["full_name"] = new_name
    log_action(user["username"], "Профильді өзгертті")
    flash("Профиль жаңартылды")
    st.rerun()


def render_profile(user: dict):
    name = user["full_name"]
    role_label = ROLE_LABELS.get(user["role"], user["role"])
    st.markdown(
        f"""
        <div class="hero">
            <div class="avatar" style="margin: 0 auto 12px; border: 3px solid rgba(255,255,255,.55);">{esc(name[:1].upper())}</div>
            <div class="hero-title">{esc(name)}</div>
            <div class="hero-sub">@{esc(user['username'])} · {esc(role_label)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_info, tab_security = st.tabs(["📋 Мәлімет", "🔒 Қауіпсіздік"])

    with tab_info:
        stats = _role_stats(user)
        if stats:
            _cards(stats)
        st.caption(f"Алдыңғы кіру (UTC): {_previous_login(user['username'])}")
        _edit_form(user)

        st.subheader("🕘 Соңғы әрекеттер")
        show_df(
            query_df(
                "SELECT timestamp AS 'Уақыты (UTC)', action AS 'Әрекет'"
                " FROM audit_logs WHERE username = ?"
                " ORDER BY timestamp DESC LIMIT 10",
                (user["username"],),
            )
        )

    with tab_security:
        render_password_change(user)
