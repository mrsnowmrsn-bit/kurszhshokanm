"""Интерфейс: тақырып (тема), стильдер және көмекші функциялар."""
import html
import inspect

import streamlit as st

FONT_STACK = "'Manrope', 'Inter', 'Segoe UI', 'PT Sans', system-ui, sans-serif"
INK = "#1b1b3a"
PRIMARY = "#5b5bf0"
PALETTE = ["#5b5bf0", "#14b8a6", "#f59e0b", "#ec4899", "#8b5cf6", "#0ea5e9"]

STYLES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
  --bg: #f4f6fb;
  --surface: #ffffff;
  --ink: #1b1b3a;
  --muted: #6b7280;
  --primary: #5b5bf0;
  --primary-2: #8b5cf6;
  --accent: #14b8a6;
  --border: #e6e8f2;
  --shadow: 0 10px 30px -14px rgba(40, 40, 120, .22);
}

/* ---------- Негізгі фон мен қаріп ---------- */
.stApp {
  background:
    radial-gradient(900px 480px at 92% -8%, rgba(139, 92, 246, .16), transparent 60%),
    radial-gradient(800px 460px at -8% 8%, rgba(20, 184, 166, .13), transparent 55%),
    var(--bg);
  color: var(--ink);
}
.stApp, .stApp p, .stApp label, .stApp li, .stApp input, .stApp textarea,
.stApp button, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
  font-family: 'Manrope', 'Inter', 'Segoe UI', 'PT Sans', system-ui, sans-serif !important;
}
/* Streamlit иконкалары өз қарпін сақтасын */
[data-testid="stIconMaterial"], .material-symbols-rounded, .material-icons {
  font-family: 'Material Symbols Rounded' !important;
}

header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer, .stDeployButton { visibility: hidden; }
.block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1180px; }

.stApp h1 { font-weight: 800; letter-spacing: -.025em; color: var(--ink); }
.stApp h2, .stApp h3 { font-weight: 700; letter-spacing: -.015em; color: var(--ink); }

/* ---------- Бүйір мәзір ---------- */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #1b1b3a 0%, #262669 55%, #3a2f8e 100%);
  border-right: none;
  box-shadow: 6px 0 24px rgba(20, 20, 70, .18);
}
[data-testid="stSidebar"] * { color: #eef0ff; }
[data-testid="stSidebar"] hr { border-color: rgba(255, 255, 255, .14); }
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
  font-size: .72rem; text-transform: uppercase; letter-spacing: .1em;
  opacity: .7; font-weight: 700;
}
[data-testid="stSidebar"] [role="radiogroup"] { gap: 4px; }
[data-testid="stSidebar"] [role="radiogroup"] label {
  width: 100%; padding: 10px 12px; border-radius: 12px;
  cursor: pointer; transition: background .15s ease;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background: rgba(255, 255, 255, .09); }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
  background: linear-gradient(90deg, rgba(255, 255, 255, .20), rgba(255, 255, 255, .05));
  box-shadow: inset 3px 0 0 #a5b4fc;
}
[data-testid="stSidebar"] .stButton > button {
  background: rgba(255, 255, 255, .08);
  border: 1px solid rgba(255, 255, 255, .25);
  color: #ffffff;
}
[data-testid="stSidebar"] .stButton > button:hover {
  background: rgba(255, 255, 255, .18);
  border-color: rgba(255, 255, 255, .45);
}

.profile { text-align: center; padding: 14px 8px 4px; }
.avatar {
  width: 68px; height: 68px; margin: 0 auto 10px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; font-size: 32px; font-weight: 800;
  background: linear-gradient(135deg, #8b5cf6, #14b8a6);
  box-shadow: 0 8px 20px rgba(0, 0, 0, .3);
}
.profile-name { font-weight: 800; font-size: 1.05rem; line-height: 1.25; }
.role-badge {
  display: inline-block; margin-top: 8px; padding: 3px 12px; border-radius: 999px;
  font-size: .72rem; font-weight: 700; letter-spacing: .06em;
  background: rgba(255, 255, 255, .14);
}

/* ---------- Батырмалар ---------- */
.stButton > button, .stDownloadButton > button,
[data-testid="stFormSubmitButton"] > button {
  border-radius: 12px; font-weight: 700; padding: .55rem 1.1rem;
  border: 1px solid var(--border); transition: transform .15s ease, box-shadow .15s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover,
[data-testid="stFormSubmitButton"] > button:hover {
  transform: translateY(-1px); box-shadow: 0 8px 18px -8px rgba(40, 40, 120, .35);
}
button[kind="primary"], button[kind="primaryFormSubmit"],
button[data-testid="stBaseButton-primary"],
button[data-testid="stBaseButton-primaryFormSubmit"] {
  background: linear-gradient(135deg, var(--primary), var(--primary-2));
  color: #ffffff; border: none;
}

/* ---------- Формалар, өрістер, кестелер ---------- */
[data-testid="stForm"] {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 18px; padding: 22px; box-shadow: var(--shadow);
}
div[data-baseweb="input"], div[data-baseweb="textarea"],
div[data-baseweb="select"] > div { border-radius: 12px !important; background: #ffffff; }

[data-testid="stDataFrame"] {
  border-radius: 14px; overflow: hidden;
  border: 1px solid var(--border); box-shadow: var(--shadow);
}
[data-testid="stMetric"] {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 16px; padding: 16px 18px; box-shadow: var(--shadow);
}
[data-testid="stMetricValue"] { font-weight: 800; }
[data-testid="stAlert"] { border-radius: 14px; }
[data-testid="stExpander"] details {
  background: var(--surface); border: 1px solid var(--border) !important;
  border-radius: 14px; box-shadow: var(--shadow);
}

.stTabs [data-baseweb="tab-list"] {
  gap: 6px; background: #eceefb; padding: 5px; border-radius: 14px;
}
.stTabs [data-baseweb="tab"] { border-radius: 10px; padding: 8px 16px; font-weight: 700; }
.stTabs [aria-selected="true"] { background: #ffffff; box-shadow: 0 2px 8px rgba(40, 40, 120, .12); }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }

/* ---------- Өз карточкаларымыз ---------- */
.hero {
  text-align: center; padding: 34px 24px; border-radius: 24px; color: #ffffff;
  background: linear-gradient(135deg, #3b3bd6 0%, #7c3aed 55%, #14b8a6 125%);
  box-shadow: 0 24px 50px -20px rgba(91, 91, 240, .55); margin-bottom: 22px;
}
.hero-title { font-size: 1.9rem; font-weight: 800; letter-spacing: -.02em; margin-bottom: 6px; }
.hero-sub { opacity: .9; font-weight: 500; }

.stat-card {
  display: flex; align-items: center; gap: 16px; background: var(--surface);
  border: 1px solid var(--border); border-radius: 18px; padding: 18px 20px;
  box-shadow: var(--shadow); transition: transform .15s ease, box-shadow .15s ease;
}
.stat-card:hover { transform: translateY(-2px); box-shadow: 0 18px 36px -16px rgba(40, 40, 120, .3); }
.stat-icon {
  flex: none; width: 52px; height: 52px; border-radius: 14px; font-size: 24px;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, rgba(91, 91, 240, .14), rgba(20, 184, 166, .18));
}
.stat-title { font-size: .74rem; color: var(--muted); font-weight: 700; text-transform: uppercase; letter-spacing: .08em; }
.stat-value { font-size: 1.9rem; font-weight: 800; color: var(--ink); line-height: 1.1; margin-top: 2px; }

.custom-card {
  position: relative; overflow: hidden; background: var(--surface);
  padding: 22px 24px 22px 28px; border-radius: 18px; margin-bottom: 18px;
  border: 1px solid var(--border); box-shadow: var(--shadow);
}
.custom-card::before {
  content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 5px;
  background: linear-gradient(180deg, var(--primary), var(--accent));
}
.custom-card h4 { margin: 0 0 8px; color: var(--ink); font-weight: 800; }
.custom-card p { margin: 0 0 10px; }
.custom-card .meta { color: var(--muted); font-size: .8rem; }

@media (max-width: 640px) {
  .stat-value { font-size: 1.5rem; }
  .hero-title { font-size: 1.5rem; }
}
</style>
"""


def inject_styles():
    st.markdown(STYLES, unsafe_allow_html=True)


def esc(value) -> str:
    """HTML экрандау (XSS қорғанысы)."""
    return html.escape(str(value if value is not None else ""))


def flash(message: str):
    """Rerun-нан кейін көрсетілетін хабарлама."""
    st.session_state["_flash"] = message


def show_flash():
    msg = st.session_state.pop("_flash", None)
    if msg:
        st.toast(msg, icon="✅")


def stat_card(title, value, icon: str = ""):
    icon_html = f'<div class="stat-icon">{esc(icon)}</div>' if icon else ""
    st.markdown(
        f'<div class="stat-card">{icon_html}<div>'
        f'<div class="stat-title">{esc(title)}</div>'
        f'<div class="stat-value">{esc(value)}</div></div></div>',
        unsafe_allow_html=True,
    )


def stretch(widget) -> dict:
    """Streamlit нұсқасына қарай «толық ен» параметрін таңдайды.

    Жаңа нұсқа: width="stretch"; ескі нұсқа: use_container_width=True
    (ол жаңа нұсқаларда ескірген, болашақта жойылады).
    """
    try:
        params = inspect.signature(widget).parameters
    except (TypeError, ValueError):
        return {}
    width = params.get("width")
    ucw = params.get("use_container_width")
    if width is not None and (ucw is None or ucw.default is None):
        return {"width": "stretch"}
    if ucw is not None:
        return {"use_container_width": True}
    return {}


def show_df(df):
    st.dataframe(df, hide_index=True, **stretch(st.dataframe))


def show_chart(fig):
    """Plotly графигін сайттың стиліне келтіріп көрсетеді."""
    fig.update_layout(
        font=dict(family=FONT_STACK, color=INK),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=PALETTE,
        margin=dict(l=10, r=10, t=56, b=10),
        title=dict(font=dict(size=16)),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(gridcolor="#e6e8f2", zeroline=False)
    fig.update_yaxes(gridcolor="#e6e8f2", zeroline=False)
    st.plotly_chart(fig, **stretch(st.plotly_chart))
