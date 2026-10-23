"""Кестелер құрылымы және бастапқы деректер."""

TABLES = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT CHECK(role IN ('ADMIN', 'TEACHER', 'STUDENT')) NOT NULL
    )""",
    """
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        student_code TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        group_name TEXT NOT NULL,
        course_num INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    )""",
    """
    CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_name TEXT UNIQUE NOT NULL,
        credits INTEGER DEFAULT 3
    )""",
    """
    CREATE TABLE IF NOT EXISTS grades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        subject_id INTEGER NOT NULL,
        grade INTEGER CHECK(grade >= 0 AND grade <= 100),
        attendance TEXT CHECK(attendance IN ('Қатысты', 'Қатыспады', 'Себепті')) NOT NULL,
        lesson_date TEXT NOT NULL,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
        FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
    )""",
    """
    CREATE TABLE IF NOT EXISTS timetable (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_name TEXT NOT NULL,
        subject_id INTEGER NOT NULL,
        day_of_week TEXT NOT NULL,
        time_slot TEXT NOT NULL,
        room TEXT,
        FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
    )""",
    """
    CREATE TABLE IF NOT EXISTS homeworks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id INTEGER NOT NULL,
        group_name TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        deadline TEXT,
        FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
    )""",
    """
    CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        homework_id INTEGER NOT NULL,
        student_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (homework_id) REFERENCES homeworks(id) ON DELETE CASCADE,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
    )""",
    """
    CREATE TABLE IF NOT EXISTS announcements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        target_group TEXT DEFAULT 'Барлығы',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        action TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
]

UNIQUE_SUBMISSION_INDEX = (
    "CREATE UNIQUE INDEX IF NOT EXISTS ux_submission"
    " ON submissions(homework_id, student_id)"
)

DEFAULT_SUBJECTS = [
    ("C# және .NET Тұғырнамасы", 5),
    ("Microsoft SQL Server Деректер Қоры", 5),
    ("Веб-бағдарламалау (Python/Streamlit)", 4),
    ("Алгоритмдер мен деректер құрылымы", 4),
]
