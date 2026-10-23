"""Кіру нүктесі: streamlit run app.py"""
import streamlit as st

st.set_page_config(
    page_title="Университет: Электрондық Журнал (Pro)",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

from core.config import PROFILE_PAGE  # noqa: E402
from core.database import init_db  # noqa: E402
from core.ui import inject_styles, show_flash  # noqa: E402
from views import admin, student, teacher  # noqa: E402
from views.auth import render_auth  # noqa: E402
from views.common import (  # noqa: E402
    render_sidebar,
    warn_default_admin_password,
)
from views.profile import render_profile  # noqa: E402

ROLE_VIEWS = {
    "ADMIN": admin,
    "TEACHER": teacher,
    "STUDENT": student,
}


def main():
    inject_styles()
    init_db()

    st.session_state.setdefault("logged_in", False)
    st.session_state.setdefault("user_info", None)

    if not st.session_state.logged_in:
        render_auth()
        return

    user = st.session_state.user_info
    role_view = ROLE_VIEWS[user["role"]]

    menu = list(role_view.PAGES) + [PROFILE_PAGE]
    choice = render_sidebar(user, menu)

    show_flash()
    warn_default_admin_password(user)

    if choice == PROFILE_PAGE:
        render_profile(user)
    else:
        role_view.render(user, choice)


main()
