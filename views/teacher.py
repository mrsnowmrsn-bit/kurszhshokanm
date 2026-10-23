"""Оқытушы (TEACHER) беттері."""
import io

import plotly.express as px
import streamlit as st
import pandas as pd

from core.audit import log_action
from core.config import ATTENDANCE_OPTIONS
from core.database import db, groups_list, query_df
from core.ui import PRIMARY, flash, show_chart, show_df


def journal(user):
    st.title("📝 Электрондық Журнал Толтыру")
    students_df = query_df("SELECT id, full_name, group_name FROM students")
    subjects_df = query_df("SELECT id, subject_name FROM subjects")

    if students_df.empty or subjects_df.empty:
        st.warning("Студенттер немесе пәндер әлі қосылмаған.")
        return

    # Пән мен топ формадан тыс: өзгергенде студенттер тізімі жаңарады
    sub_idx = subjects_df.set_index("id")
    c1, c2 = st.columns(2)
    sub_id = c1.selectbox(
        "Пән",
        subjects_df["id"].tolist(),
        format_func=lambda i: sub_idx.loc[i, "subject_name"],
    )
    grp = c2.selectbox("Топ", sorted(students_df["group_name"].unique()))
    f_stud = students_df[students_df["group_name"] == grp].set_index("id")

    with st.form("teacher_mark"):
        stud_id = st.selectbox(
            "Студент",
            f_stud.index.tolist(),
            format_func=lambda i: f_stud.loc[i, "full_name"],
        )
        grade = st.slider("Баға (0-100)", 0, 100, 80)
        att = st.radio("Қатысуы", ATTENDANCE_OPTIONS, horizontal=True)
        date = st.date_input("Күні")
        submitted = st.form_submit_button("Сақтау", type="primary")

    if submitted:
        try:
            with db() as conn:
                conn.execute(
                    "INSERT INTO grades (student_id, subject_id, grade,"
                    " attendance, lesson_date) VALUES (?, ?, ?, ?, ?)",
                    (int(stud_id), int(sub_id), int(grade), att, str(date)),
                )
            log_action(
                user["username"],
                f"Баға қойды: student={stud_id}, subject={sub_id}",
            )
            flash("Баға сәтті сақталды!")
            st.rerun()
        except Exception as e:
            st.error(f"Қате орын алды: {e}")


def homeworks(user):
    st.title("📌 LMS: Үй тапсырмаларын беру")
    subjects_df = query_df("SELECT id, subject_name FROM subjects")
    groups = groups_list()

    if subjects_df.empty or not groups:
        st.warning("Пәндер немесе топтар жоқ.")
        return

    sub_idx = subjects_df.set_index("id")
    with st.form("hw_form"):
        sub_id = st.selectbox(
            "Пән",
            subjects_df["id"].tolist(),
            format_func=lambda i: sub_idx.loc[i, "subject_name"],
        )
        grp_sel = st.selectbox("Топ", groups)
        title = st.text_input("Тапсырма тақырыбы").strip()
        desc = st.text_area("Тапсырма сипаттамасы мен нұсқаулық")
        deadline = st.date_input("Орындау мерзімі (Deadline)")
        submitted = st.form_submit_button("Тапсырманы жүктеу")
    if submitted:
        if title:
            with db() as conn:
                conn.execute(
                    "INSERT INTO homeworks (subject_id, group_name, title,"
                    " description, deadline) VALUES (?, ?, ?, ?, ?)",
                    (int(sub_id), grp_sel, title, desc, str(deadline)),
                )
            flash("Тапсырма студенттерге жіберілді!")
            st.rerun()
        else:
            st.warning("Тақырыпты жазыңыз.")

    st.subheader("📥 Тапсырылған жұмыстар")
    hw_all = query_df(
        """SELECT h.id, h.group_name, h.title, h.deadline, s.subject_name
           FROM homeworks h JOIN subjects s ON h.subject_id = s.id
           ORDER BY h.id DESC"""
    )
    if hw_all.empty:
        st.info("Әзірге тапсырма берілмеген.")
        return

    hw_idx = hw_all.set_index("id")
    hw_id = st.selectbox(
        "Тапсырма",
        hw_all["id"].tolist(),
        format_func=lambda i: (
            f"{hw_idx.loc[i, 'subject_name']} — {hw_idx.loc[i, 'title']}"
            f" ({hw_idx.loc[i, 'group_name']})"
        ),
    )
    subs = query_df(
        """SELECT st.student_code AS 'Код', st.full_name AS 'Студент',
                  sb.content AS 'Жауап', sb.submitted_at AS 'Уақыты'
           FROM submissions sb JOIN students st ON sb.student_id = st.id
           WHERE sb.homework_id = ?""",
        (int(hw_id),),
    )
    total = query_df(
        "SELECT COUNT(*) AS n FROM students WHERE group_name = ?",
        (hw_idx.loc[hw_id, "group_name"],),
    )["n"][0]
    st.caption(f"Тапсырған: {len(subs)} / {total}")
    show_df(subs)


def debts(user):
    st.title("⚠️ Академиялық Қарыздар мен Пересдача тізімі")
    st.info(
        "Бағасы 50-ден төмен немесе сабаққа қатыспаған студенттер автоматты"
        " түрде көрсетіледі."
    )
    show_df(
        query_df(
            """SELECT s.student_code, s.full_name, s.group_name,
                      sub.subject_name, g.grade, g.attendance, g.lesson_date
               FROM grades g
               JOIN students s ON g.student_id = s.id
               JOIN subjects sub ON g.subject_id = sub.id
               WHERE g.grade < 50 OR g.attendance = 'Қатыспады'"""
        ),
    )


def timetable(user):
    st.title("📅 Сабақ Кестесі")
    show_df(
        query_df(
            "SELECT t.group_name, s.subject_name, t.day_of_week,"
            " t.time_slot, t.room FROM timetable t"
            " JOIN subjects s ON t.subject_id = s.id"
        ),
    )


def analytics(user):
    st.title("📊 Үлгерім Аналитикасы")
    df = query_df(
        """SELECT g.grade, g.attendance, sub.subject_name
           FROM grades g JOIN subjects sub ON g.subject_id = sub.id"""
    )
    if df.empty:
        st.info("Деректер жоқ.")
        return

    c1, c2 = st.columns(2)
    with c1:
        show_chart(
            px.histogram(df, x="grade", title="Бағалар таралуы",
                         color_discrete_sequence=[PRIMARY]),
        )
    with c2:
        show_chart(px.pie(df, names="attendance", title="Қатысу үлесі"))
    avg = df.groupby("subject_name", as_index=False)["grade"].mean()
    show_chart(
        px.bar(avg, x="subject_name", y="grade",
               title="Пәндер бойынша орташа баға"),
    )


def export(user):
    st.title("📥 Экспорттау")
    df = query_df(
        """SELECT s.student_code, s.full_name, s.group_name,
                  sub.subject_name, g.grade, g.attendance, g.lesson_date
           FROM grades g
           JOIN students s ON g.student_id = s.id
           JOIN subjects sub ON g.subject_id = sub.id"""
    )
    if df.empty:
        st.info("Экспорттайтын деректер жоқ.")
        return

    show_df(df)
    try:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Журнал")
        st.download_button(
            "Excel (.xlsx) жүктеу",
            data=buf.getvalue(),
            file_name="journal_export.xlsx",
            mime="application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet",
        )
    except ImportError:
        st.caption("Excel үшін `pip install openpyxl` қажет, CSV беріледі.")
    st.download_button(
        "CSV жүктеу",
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name="journal_export.csv",
        mime="text/csv",
    )


PAGES = {
    "📝 Электрондық Журнал": journal,
    "📌 Үй тапсырмаларын басқару": homeworks,
    "⚠️ Академиялық Қарыздар": debts,
    "📅 Сабақ Кестесі": timetable,
    "📊 Аналитика": analytics,
    "📥 Экспорттау": export,
}


def render(user: dict, choice: str):
    PAGES[choice](user)
