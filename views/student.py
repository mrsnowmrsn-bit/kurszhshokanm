"""Студент (STUDENT) беттері."""
import datetime

import plotly.express as px
import streamlit as st

from core.database import db, query_df
from core.gpa import calculate_gpa
from core.ui import esc, flash, show_chart, show_df


def journal_gpa(user, stud):
    my_grades = query_df(
        """SELECT sub.subject_name AS 'Пән', sub.credits AS 'Кредит',
                  g.grade AS 'Баға', g.attendance AS 'Қатысуы',
                  g.lesson_date AS 'Күні'
           FROM grades g JOIN subjects sub ON g.subject_id = sub.id
           WHERE g.student_id = ?
           ORDER BY g.lesson_date DESC""",
        (stud["id"],),
    )
    st.subheader("📝 Бағалар мен ECTS Кредиттер")
    if my_grades.empty:
        st.warning("Сізге әлі баға қойылмаған.")
        return
    st.metric("Сіздің GPA көрсеткішіңіз:", f"{calculate_gpa(my_grades)} / 4.0")
    show_df(my_grades)


def timetable(user, stud):
    st.title("📅 Менің Тобымның Сабақ Кестесі")
    show_df(
        query_df(
            "SELECT s.subject_name AS 'Пән', t.day_of_week AS 'Апта күні',"
            " t.time_slot AS 'Уақыты', t.room AS 'Аудитория'"
            " FROM timetable t JOIN subjects s ON t.subject_id = s.id"
            " WHERE t.group_name = ?",
            (stud["group"],),
        ),
    )


def homeworks(user, stud):
    st.title("📂 LMS: Үй тапсырмаларын тапсыру")
    hw_df = query_df(
        """SELECT h.id, sub.subject_name, h.title, h.description, h.deadline
           FROM homeworks h JOIN subjects sub ON h.subject_id = sub.id
           WHERE h.group_name = ? ORDER BY h.deadline""",
        (stud["group"],),
    )
    if hw_df.empty:
        st.info("Әзірге орындауға тиіс тапсырмалар жоқ.")
        return

    today = datetime.date.today()
    for _, row in hw_df.iterrows():
        hw_id = int(row["id"])
        try:
            overdue = datetime.date.fromisoformat(row["deadline"]) < today
        except (TypeError, ValueError):
            overdue = False

        with db() as conn:
            prev = conn.execute(
                "SELECT content FROM submissions"
                " WHERE homework_id=? AND student_id=?",
                (hw_id, stud["id"]),
            ).fetchone()

        status = (
            "✅ Тапсырылды" if prev
            else "⛔ Мерзімі өтті" if overdue
            else "🕓 Күтілуде"
        )
        with st.expander(
            f"📚 {row['subject_name']} — {row['title']}"
            f" (Мерзімі: {row['deadline']}) · {status}"
        ):
            st.write(f"**Сипаттамасы:** {row['description']}")
            if overdue:
                st.error("Тапсыру мерзімі аяқталды.")
                continue

            ans = st.text_area(
                "Жауабыңызды немесе сілтемені жазыңыз",
                value=prev[0] if prev else "",
                key=f"ans_{hw_id}",
            )
            label = "Қайта жіберу" if prev else "Тапсырманы жіберу"
            if st.button(label, key=f"btn_{hw_id}"):
                if not ans.strip():
                    st.warning("Жауап бос болмауы керек.")
                    continue
                with db() as conn:
                    if prev:
                        conn.execute(
                            "UPDATE submissions SET content=?,"
                            " submitted_at=CURRENT_TIMESTAMP"
                            " WHERE homework_id=? AND student_id=?",
                            (ans.strip(), hw_id, stud["id"]),
                        )
                    else:
                        conn.execute(
                            "INSERT INTO submissions (homework_id, student_id,"
                            " content) VALUES (?, ?, ?)",
                            (hw_id, stud["id"], ans.strip()),
                        )
                flash("Тапсырма сәтті жіберілді!")
                st.rerun()


def announcements(user, stud):
    st.title("📢 Университет Жаңалықтары")
    ann_df = query_df(
        "SELECT title, content, created_at FROM announcements"
        " WHERE target_group IN ('Барлығы', ?) ORDER BY created_at DESC",
        (stud["group"],),
    )
    if ann_df.empty:
        st.info("Хабарландырулар жоқ.")
    for _, row in ann_df.iterrows():
        st.markdown(
            f"""
            <div class="custom-card">
                <h4>{esc(row['title'])}</h4>
                <p>{esc(row['content'])}</p>
                <div class="meta">Жарияланған күні: {esc(row['created_at'])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def statistics(user, stud):
    st.title("📈 Жеке үлгерім динамикасы")
    my_grades = query_df(
        "SELECT sub.subject_name, g.grade, g.lesson_date FROM grades g"
        " JOIN subjects sub ON g.subject_id = sub.id"
        " WHERE g.student_id = ? ORDER BY g.lesson_date",
        (stud["id"],),
    )
    if my_grades.empty:
        st.info("Деректер жоқ.")
        return
    show_chart(
        px.line(my_grades, x="lesson_date", y="grade", color="subject_name",
                markers=True, title="Бағалар динамикасы"),
    )


PAGES = {
    "📖 Журнал және GPA": journal_gpa,
    "📅 Сабақ Кестесі": timetable,
    "📂 Үй Тапсырмалары": homeworks,
    "📢 Хабарландырулар": announcements,
    "📈 Статистика": statistics,
}


def _load_student(user_id: int):
    with db() as conn:
        row = conn.execute(
            "SELECT id, student_code, group_name FROM students"
            " WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    if not row:
        return None
    return {"id": row[0], "code": row[1], "group": row[2]}


def render(user: dict, choice: str):
    st.title(f"📖 Жеке Кабинет: {user['full_name']}")
    stud = _load_student(user["id"])
    if not stud:
        st.warning("Аккаунтыңыз студенттер базасымен байланыстырылмаған.")
        return
    st.info(f"Студент Коды: **{stud['code']}** | Топ: **{stud['group']}**")
    PAGES[choice](user, stud)
