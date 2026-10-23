"""Кіру және студентті тіркеу беттері."""
import sqlite3

import streamlit as st

from core.audit import FAILED_LOGIN, is_locked, log_action
from core.config import LOCK_MINUTES, MIN_PASSWORD_LEN
from core.database import db
from core.security import hash_password, is_modern_hash, verify_password
from core.ui import stretch


def _login_tab():
    with st.form("login_form"):
        username = st.text_input("Пайдаланушы аты (Username)").strip()
        password = st.text_input("Пароль", type="password")
        submitted = st.form_submit_button(
            "Кіру", **stretch(st.form_submit_button), type="primary"
        )
    if not submitted:
        return

    key = username or "?"
    if is_locked(key):
        st.error(
            f"Тым көп қате әрекет. {LOCK_MINUTES} минуттан кейін қайталаңыз."
        )
        return

    with db() as conn:
        row = conn.execute(
            "SELECT id, username, full_name, role, password_hash"
            " FROM users WHERE username = ?",
            (username,),
        ).fetchone()

    if row and verify_password(password, row[4]):
        if not is_modern_hash(row[4]):  # ескі хэшті жаңартамыз
            with db() as conn:
                conn.execute(
                    "UPDATE users SET password_hash = ? WHERE id = ?",
                    (hash_password(password), row[0]),
                )
        st.session_state.logged_in = True
        st.session_state.user_info = {
            "id": row[0],
            "username": row[1],
            "full_name": row[2],
            "role": row[3],
        }
        log_action(row[1], "Жүйеге сәтті кірді")
        st.rerun()
    else:
        log_action(key, FAILED_LOGIN)
        st.error("Пайдаланушы аты немесе пароль қате!")


def _register_tab():
    st.caption(
        "Ашық тіркеу тек студенттерге арналған. Оқытушы аккаунтын әкімші"
        " жасайды."
    )
    with st.form("register_form"):
        username = st.text_input("Жаңа пайдаланушы аты").strip()
        fullname = st.text_input("Толық Аты-Жөні").strip()
        password = st.text_input(
            f"Пароль (кемінде {MIN_PASSWORD_LEN} таңба)", type="password"
        )
        group = st.text_input("Топ", value="ИС-301").strip()
        course = st.number_input("Курс", min_value=1, max_value=5, value=3)
        submitted = st.form_submit_button("Тіркелу", **stretch(st.form_submit_button))
    if not submitted:
        return

    if not (username and fullname and password and group):
        st.warning("Барлық өрістерді толтырыңыз!")
        return
    if len(password) < MIN_PASSWORD_LEN:
        st.warning(f"Пароль кемінде {MIN_PASSWORD_LEN} таңбадан тұруы керек!")
        return

    try:
        with db() as conn:
            cur = conn.execute(
                "INSERT INTO users (username, password_hash, full_name, role)"
                " VALUES (?, ?, ?, 'STUDENT')",
                (username, hash_password(password), fullname),
            )
            uid = cur.lastrowid
            conn.execute(
                "INSERT INTO students (user_id, student_code, full_name,"
                " group_name, course_num) VALUES (?, ?, ?, ?, ?)",
                (uid, f"ST-{uid:04d}", fullname, group, int(course)),
            )
        log_action(username, "Жаңа студент тіркелді")
        st.success("Тіркелу сәтті аяқталды! Енді жүйеге кіре аласыз.")
    except sqlite3.IntegrityError:
        st.error("Бұл пайдаланушы аты бос емес!")


def render_auth():
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class="hero">
                <div class="hero-title">🎓 Университет АЖ</div>
                <div class="hero-sub">Электрондық журнал және LMS порталы</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        tab_login, tab_register = st.tabs(
            ["🔐 Жүйеге кіру", "📝 Студентті тіркеу"]
        )
        with tab_login:
            _login_tab()
        with tab_register:
            _register_tab()
