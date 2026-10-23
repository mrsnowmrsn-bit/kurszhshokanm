"""Жүйенің тұрақтылары мен баптаулары."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_NAME = str(BASE_DIR / "university_portal_pro.db")

# Әдепкі әкімші паролін ORTA АЙНЫМАЛЫСЫМЕН беруге болады: ADMIN_PASSWORD
DEFAULT_ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
INSECURE_DEFAULT_PASSWORD = "admin123"

MAX_FAILED_ATTEMPTS = 5
LOCK_MINUTES = 10
PBKDF2_ITERATIONS = 200_000
MIN_PASSWORD_LEN = 6

ATTENDANCE_OPTIONS = ["Қатысты", "Қатыспады", "Себепті"]
DAYS_OF_WEEK = ["Дүйсенбі", "Сейсенбі", "Сәрсенбі", "Бейсенбі", "Жұма", "Сенбі"]

PROFILE_PAGE = "👤 Профиль"
ROLE_LABELS = {"ADMIN": "Әкімші", "TEACHER": "Оқытушы", "STUDENT": "Студент"}
