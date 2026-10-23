"""Барлық рөлдерге ортақ: бүйір мәзір, парольді өзгерту, ескертулер."""
import streamlit as st

from core.audit import log_action
from core.config import INSECURE_DEFAULT_PASSWORD, MIN_PASSWORD_LEN, ROLE_LABELS
from core.database import db
from core.security import hash_password, verify_password
from core.ui import esc, stretch


def render_sidebar(user: dict, menu: list) -> str:
    with st.sidebar:
        st.markdown(
            f"""
        <div class="profile">
            <div class="avatar">{esc(user['full_name'][:1].upper())}</div>
            <div class="profile-name">{esc(user['full_name'])}</div>
            <span class="role-badge">{esc(ROLE_LABELS.get(user['role'], user['role']))}</span>
        </div>
        """,
            unsafe_allow_html=True,
        )
        st.markdown("---")
        choice = st.radio("Мәзір:", menu)
        st.markdown("---")
        if st.button("🚪 Жүйеден шығу", **stretch(st.button)):
            log_action(user["username"], "Жүйеден шықты")
            st.session_state.pop("_default_pw", None)
            st.session_state.logged_in = False
            st.session_state.user_info = None
            st.rerun()
    return choice


def warn_default_admin_password(user: dict):
    if user["role"] != "ADMIN":
        return
    # PBKDF2 баяу, сондықтан нәтижені сессияда бір рет сақтаймыз
    flag = st.session_state.get("_default_pw")
    if flag is None:
        with db() as conn:
            row = conn.execute(
                "SELECT password_hash FROM users WHERE id = ?", (user["id"],)
            ).fetchone()
        flag = bool(row and verify_password(INSECURE_DEFAULT_PASSWORD, row[0]))
        st.session_state["_default_pw"] = flag
    if flag:
        st.warning(
            "⚠️ Әдепкі пароль (admin123) қолданылып жатыр. «Профиль → Қауіпсіздік»"
            " бөлімінде ауыстырыңыз."
        )


def render_password_change(user: dict):
    st.subheader("🔑 Парольді өзгерту")
    with st.form("pwd_form"):
        old_pw = st.text_input("Ағымдағы пароль", type="password")
        new_pw = st.text_input(
            f"Жаңа пароль (кемінде {MIN_PASSWORD_LEN} таңба)", type="password"
        )
        new_pw2 = st.text_input("Жаңа парольді қайталаңыз", type="password")
        submitted = st.form_submit_button("Өзгерту")
    if not submitted:
        return

    with db() as conn:
        stored = conn.execute(
            "SELECT password_hash FROM users WHERE id = ?", (user["id"],)
        ).fetchone()[0]

    if not verify_password(old_pw, stored):
        st.error("Ағымдағы пароль қате!")
    elif len(new_pw) < MIN_PASSWORD_LEN:
        st.warning("Жаңа пароль тым қысқа!")
    elif new_pw != new_pw2:
        st.warning("Парольдер сәйкес келмейді!")
    else:
        with db() as conn:
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (hash_password(new_pw), user["id"]),
            )
        st.session_state.pop("_default_pw", None)
        log_action(user["username"], "Парольді өзгертті")
        st.success("Пароль сәтті өзгертілді!")
