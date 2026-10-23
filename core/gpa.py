"""GPA есептеу логикасы."""
import pandas as pd


def grade_to_points(grade: float) -> float:
    if grade >= 90:
        return 4.0
    if grade >= 75:
        return 3.0
    if grade >= 50:
        return 2.0
    return 1.0


def calculate_gpa(grades: pd.DataFrame, grade_col: str = "Баға",
                  credit_col: str = "Кредит") -> float:
    """Кредит бойынша өлшенген GPA (4.0 шкала)."""
    total_points = 0.0
    total_credits = 0
    for _, row in grades.iterrows():
        g = row[grade_col]
        if pd.isna(g):
            continue
        credit = 0 if pd.isna(row[credit_col]) else int(row[credit_col])
        total_points += grade_to_points(g) * credit
        total_credits += credit
    return round(total_points / total_credits, 2) if total_credits else 0.0
