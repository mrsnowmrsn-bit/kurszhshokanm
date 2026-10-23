"""Әкімші (ADMIN) беттері."""
import datetime
import sqlite3

import streamlit as st

from core.audit import log_action
from core.config import DAYS_OF_WEEK, DB_NAME, MIN_PASSWORD_LEN
from core.database import db, groups_list, query_df
from core.security import hash_password
from core.ui import flash, show_df, stat_card, stretch


def dashboard(user):
    st.title("📊 Деканат: Басқару Панелі")
    df_students = query_df("SELECT * FROM students")
    df_subjects = query_df("SELECT * FROM subjects")
    df_grades = query_df("SELECT * FROM grades")

    n_groups = df_students["group_name"].nunique() if not df_students.empty else 0
    avg_g = round(df_grades["grade"].mean(), 1) if not df_grades.empty else 0
    cards = [
        ("Студенттер", len(df_students), "🎓"),
        ("Оқу топтары", n_groups, "🏫"),
        ("Пәндер", len(df_subjects), "📚"),
        ("Орташа баға", avg_g, "⭐"),
    ]
    for col, (title, val, icon) in zip(st.columns(4), cards):
        with col:
            stat_card(title, val, icon)


def students(user):
    st.title("👨‍🎓 Студенттерді Басқару")
    df_s = query_df(
        "SELECT id, student_code, full_name, group_name, course_num"
        " FROM students"
    )
    show_df(df_s)
    if df_s.empty:
        return

    st.subheader("✏️ Студентті өңдеу / жою")
    idx = df_s.set_index("id")
    sid = st.selectbox(
        "Студент",
        df_s["id"].tolist(),
        format_func=lambda i: f"{idx.loc[i, 'student_code']} — {idx.loc[i, 'full_name']}",
    )
    cur = idx.loc[sid]
    with st.form("edit_student"):
        e_name = st.text_input("Аты-жөні", value=cur["full_name"])
        e_group = st.text_input("Топ", value=cur["group_name"])
        e_course = st.number_input("Курс", 1, 5, int(cur["course_num"]))
        c1, c2 = st.columns(2)
        save = c1.form_submit_button("Сақтау", type="primary")
        delete = c2.form_submit_button("🗑️ Жою")

    if save and e_name.strip() and e_group.strip():
        with db() as conn:
            conn.execute(
                "UPDATE students SET full_name=?, group_name=?, course_num=?"
                " WHERE id=?",
                (e_name.strip(), e_group.strip(), int(e_course), int(sid)),
            )
            # пайдаланушы аккаунтындағы аты да сәйкес болуы керек
            conn.execute(
                "UPDATE users SET full_name=? WHERE id ="
                " (SELECT user_id FROM students WHERE id=?)",
                (e_name.strip(), int(sid)),
            )
        log_action(user["username"], f"Студент өзгертілді: id={sid}")
        flash("Студент мәліметі жаңартылды")
        st.rerun()
    if delete:
        with db() as conn:
            row = conn.execute(
                "SELECT user_id FROM students WHERE id=?", (int(sid),)
            ).fetchone()
            conn.execute("DELETE FROM students WHERE id=?", (int(sid),))
            if row and row[0]:  # жетім аккаунт қалмауы үшін
                conn.execute("DELETE FROM users WHERE id=?", (row[0],))
        log_action(user["username"], f"Студент жойылды: id={sid}")
        flash("Студент жойылды")
        st.rerun()


def users(user):
    st.title("👥 Пайдаланушыларды басқару")
    users_df = query_df("SELECT id, username, full_name, role FROM users")
    show_df(users_df)

    st.subheader("➕ Оқытушы / әкімші қосу")
    with st.form("add_staff"):
        u_name = st.text_input("Пайдаланушы аты").strip()
        u_full = st.text_input("Толық аты-жөні").strip()
        u_pw = st.text_input("Уақытша пароль", type="password")
        u_role = st.selectbox(
            "Рөлі",
            ["TEACHER", "ADMIN"],
            format_func=lambda x: "Оқытушы" if x == "TEACHER" else "Әкімші",
        )
        submitted = st.form_submit_button("Қосу")
    if submitted:
        if u_name and u_full and len(u_pw) >= MIN_PASSWORD_LEN:
            try:
                with db() as conn:
                    conn.execute(
                        "INSERT INTO users (username, password_hash,"
                        " full_name, role) VALUES (?, ?, ?, ?)",
                        (u_name, hash_password(u_pw), u_full, u_role),
                    )
                log_action(user["username"], f"Аккаунт құрылды: {u_name}")
                flash("Пайдаланушы қосылды")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("Бұл пайдаланушы аты бос емес!")
        else:
            st.warning(
                f"Өрістерді толтырыңыз (пароль ≥ {MIN_PASSWORD_LEN} таңба)."
            )

    st.subheader("🔄 Парольді қалпына келтіру")
    idx = users_df.set_index("id")
    with st.form("reset_pw"):
        target = st.selectbox(
            "Пайдаланушы",
            users_df["id"].tolist(),
            format_func=lambda i: idx.loc[i, "username"],
        )
        npw = st.text_input("Жаңа пароль", type="password")
        submitted = st.form_submit_button("Қалпына келтіру")
    if submitted:
        if len(npw) >= MIN_PASSWORD_LEN:
            with db() as conn:
                conn.execute(
                    "UPDATE users SET password_hash=? WHERE id=?",
                    (hash_password(npw), int(target)),
                )
            log_action(
                user["username"], f"Пароль қалпына келтірілді: user_id={target}"
            )
            st.success("Пароль жаңартылды.")
        else:
            st.warning(f"Пароль кемінде {MIN_PASSWORD_LEN} таңба болуы керек.")


def subjects(user):
    st.title("📚 Пәндер және ECTS Кредиттер")
    df_sub = query_df("SELECT * FROM subjects")
    show_df(df_sub)

    with st.form("add_sub_form"):
        s_name = st.text_input("Жаңа пән атауы").strip()
        s_cred = st.number_input(
            "Кредит саны (ECTS)", min_value=1, max_value=10, value=3
        )
        submitted = st.form_submit_button("Пән қосу")
    if submitted and s_name:
        try:
            with db() as conn:
                conn.execute(
                    "INSERT INTO subjects (subject_name, credits) VALUES (?, ?)",
                    (s_name, int(s_cred)),
                )
            flash("Пән сәтті қосылды!")
            st.rerun()
        except sqlite3.IntegrityError:
            st.error("Мұндай пән бар.")

    if df_sub.empty:
        return
    st.subheader("🗑️ Пәнді жою")
    idx = df_sub.set_index("id")
    del_id = st.selectbox(
        "Пән",
        df_sub["id"].tolist(),
        format_func=lambda i: idx.loc[i, "subject_name"],
        key="del_sub",
    )
    st.caption("Пәнді жойса, оған байланысты бағалар мен кесте де жойылады.")
    if st.button("Жою", key="del_sub_btn"):
        with db() as conn:
            conn.execute("DELETE FROM subjects WHERE id=?", (int(del_id),))
        log_action(user["username"], f"Пән жойылды: id={del_id}")
        flash("Пән жойылды")
        st.rerun()


def timetable(user):
    st.title("📅 Университет Кестесін Басқару")
    subjects_df = query_df("SELECT id, subject_name FROM subjects")
    timetable_df = query_df(
        """SELECT t.id, t.group_name, s.subject_name, t.day_of_week,
                  t.time_slot, t.room
           FROM timetable t JOIN subjects s ON t.subject_id = s.id"""
    )
    show_df(timetable_df)

    if subjects_df.empty:
        st.warning("Алдымен пән қосыңыз.")
    else:
        idx = subjects_df.set_index("id")
        with st.form("add_timetable"):
            known_groups = groups_list()
            if known_groups:  # тізімнен таңдау — атау сәйкессіздігін болдырмайды
                g_name = st.selectbox("Топ", known_groups)
            else:
                g_name = st.text_input("Топ атауы (мысалы, ИС-301)").strip()
            sub_id = st.selectbox(
                "Пән",
                subjects_df["id"].tolist(),
                format_func=lambda i: idx.loc[i, "subject_name"],
            )
            day = st.selectbox("Апта күні", DAYS_OF_WEEK)
            slot = st.text_input("Уақыты (мысалы, 09:00 - 10:20)")
            room = st.text_input("Аудитория (мысалы, 404-А)")
            submitted = st.form_submit_button("Кестеге қосу")
        if submitted:
            if g_name and slot:
                with db() as conn:
                    conn.execute(
                        "INSERT INTO timetable (group_name, subject_id,"
                        " day_of_week, time_slot, room)"
                        " VALUES (?, ?, ?, ?, ?)",
                        (g_name, int(sub_id), day, slot, room),
                    )
                flash("Кестеге сабақ қосылды!")
                st.rerun()
            else:
                st.warning("Топ пен уақытты толтырыңыз.")

    if not timetable_df.empty:
        tid = st.selectbox("Жойылатын жазба (id)", timetable_df["id"].tolist())
        if st.button("Кестеден жою"):
            with db() as conn:
                conn.execute("DELETE FROM timetable WHERE id=?", (int(tid),))
            flash("Жазба жойылды")
            st.rerun()


def announcements(user):
    st.title("📢 Хабарландыру тарату")
    with st.form("ann_form"):
        title = st.text_input("Хабарландыру тақырыбы").strip()
        content = st.text_area("Мәтіні").strip()
        target = st.selectbox("Кімге", ["Барлығы"] + groups_list())
        submitted = st.form_submit_button("Жариялау")
    if submitted:
        if title and content:
            with db() as conn:
                conn.execute(
                    "INSERT INTO announcements (title, content, target_group)"
                    " VALUES (?, ?, ?)",
                    (title, content, target),
                )
            log_action(user["username"], f"Хабарландыру: {title}")
            st.success("Хабарландыру сәтті жіберілді!")
        else:
            st.warning("Тақырып пен мәтінді толтырыңыз.")


def audit_logs(user):
    st.title("🛡️ Жүйелік әрекеттер журналы (Audit Logs)")
    show_df(
        query_df("SELECT * FROM audit_logs ORDER BY timestamp DESC"),
    )


def backup(user):
    st.title("💾 Деректер қорының сақтық көшірмесі")
    with open(DB_NAME, "rb") as f:
        st.download_button(
            "📦 Базаны жүктеу (.db)",
            data=f.read(),
            file_name=f"backup_{datetime.datetime.now():%Y%m%d}.db",
            mime="application/x-sqlite3",
            **stretch(st.download_button),
        )


# Мәзір атауы -> бет функциясы (реті мәзірдегі ретімен бірдей)
PAGES = {
    "📊 Басқару Панелі": dashboard,
    "👨‍🎓 Студенттер": students,
    "👥 Пайдаланушылар": users,
    "📚 Пәндер мен Кредиттер": subjects,
    "📅 Сабақ Кестесі": timetable,
    "📢 Хабарландырулар": announcements,
    "🛡️ Аудит Логтары": audit_logs,
    "💾 Резервтік көшірме": backup,
}


def render(user: dict, choice: str):
    PAGES[choice](user)
