import streamlit as st
import time
import math
import json
import os
import ast
import re
import uuid
import operator
from datetime import date, datetime, timedelta
import pandas as pd
from google import genai
from PIL import Image
import PyPDF2

# PAGE CONFIG
st.set_page_config(page_title="Smart Study Organizer Pro", page_icon="🎓", layout="wide")

DATA_FILE = "study_organizer_data.json"

# Gamification constants
XP_PER_LEVEL = 100
XP_REWARDS = {
    "quiz_question_correct": 8,
    "quiz_complete": 15,
    "pomodoro_session": 25,
    "flashcard_review": 5,
    "note_summarized": 10,
    "task_list_created": 5,
    "mindmap_created": 10,
    "math_solved": 8,
}

BADGES = {
    "first_steps":      {"label": "🌱 First Steps",        "desc": "Completed your first quiz"},
    "quiz_5":           {"label": "📚 Quiz Regular",        "desc": "Completed 5 quizzes"},
    "quiz_20":          {"label": "🏆 Quiz Master",         "desc": "Completed 20 quizzes"},
    "perfect_score":    {"label": "💯 Perfectionist",       "desc": "Got a perfect quiz score"},
    "pomodoro_5":       {"label": "🍅 Focus Builder",       "desc": "Finished 5 Pomodoro sessions"},
    "pomodoro_25":      {"label": "🔥 Deep Work Pro",       "desc": "Finished 25 Pomodoro sessions"},
    "streak_3":         {"label": "⚡ 3-Day Streak",        "desc": "Studied 3 days in a row"},
    "streak_7":         {"label": "🌟 7-Day Streak",        "desc": "Studied 7 days in a row"},
    "streak_30":        {"label": "👑 30-Day Streak",       "desc": "Studied 30 days in a row"},
    "flashcard_10":     {"label": "🧠 Card Crusher",        "desc": "Reviewed 10 flashcards"},
    "level_5":          {"label": "🚀 Rising Star",         "desc": "Reached Level 5"},
    "level_10":         {"label": "🌌 Study Legend",        "desc": "Reached Level 10"},
}

# TRANSLATIONS (English -> Sinhala) for core UI text.
# Usage: wrap any English UI string with t("...") to get it translated when
# the active profile's language is set to Sinhala. Falls back to the
# original English string for anything not in this dictionary.
TRANSLATIONS = {
    "💡 Daily Facts": "💡 දිනපතා තොරතුරු",
    "🗺️ Mindmap": "🗺️ මනසේ සිතියම",
    "📝 Summarizer": "📝 සාරාංශකරණය",
    "❓ MCQ Quiz": "❓ ප්‍රශ්නාවලිය",
    "🧠 Math Solver": "🧠 ගණිත විසඳුම",
    "🎴 Flashcards": "🎴 ෆ්ලෑෂ් කාඩ්",
    "⏱️ Pomodoro": "⏱️ පොමදෝරෝ",
    "✍️ Scribble Pad": "✍️ සටහන් පොත",
    "📊 Analytics": "📊 විශ්ලේෂණ",
    "💡 Daily Tech & Science Facts": "💡 දෛනික තාක්ෂණික හා විද්‍යා තොරතුරු",
    "Get interesting Tech/Science facts here": "රසවත් තාක්ෂණික/විද්‍යා තොරතුරු මෙතැනින්",
    "🗺️ AI Mindmap Generator": "🗺️ AI මනසේ සිතියම් සකසනය",
    "Turn your notes or PDFs into a structured, easy-to-understand mindmap.": "ඔබේ සටහන් හෝ PDF ගොනු පහසුවෙන් තේරුම්ගත හැකි මනසේ සිතියමක් බවට පත් කරන්න.",
    "📝 AI Note Summarizer": "📝 AI සටහන් සාරාංශකරණය",
    "❓ AI Anti-Cheat MCQ Quiz": "❓ AI ප්‍රශ්නාවලිය",
    "Test your knowledge with questions based on the Sri Lankan Syllabus.": "ශ්‍රී ලංකා විෂය නිර්දේශය මත පදනම් ප්‍රශ්න මගින් ඔබේ දැනුම පරීක්ෂා කරන්න.",
    "🧠 AI Math Problem Solver": "🧠 AI ගණිත ප්‍රශ්න විසඳුම",
    "Learn math step-by-step with AI": "AI සමඟ පියවරෙන් පියවර ගණිතය ඉගෙන ගන්න",
    "🗂️ Flashcards & Spaced Repetition": "🗂️ ෆ්ලෑෂ් කාඩ් සහ පුනරාවර්තනය",
    "Generate flashcards with AI, then review them on a smart schedule.": "AI මගින් ෆ්ලෑෂ් කාඩ් සාදා, සුදුසු කාලසටහනකට අනුව සමාලෝචනය කරන්න.",
    "⏱️ Pomodoro & Goal Progress Tracker": "⏱️ පොමදෝරෝ සහ ඉලක්ක ප්‍රගති නිරීක්ෂණය",
    "🤖 AI Auto Task Generator": "🤖 AI කාර්ය ලේඛන සකසනය",
    "🎯 Study Goal Tracker": "🎯 අධ්‍යයන ඉලක්ක නිරීක්ෂණය",
    "⏱️ Pomodoro Timer": "⏱️ පොමදෝරෝ ටයිමරය",
    "📝 Quick Scribble Pad / Sticky Notes": "📝 ඉක්මන් සටහන් පොත",
    "Quickly note down important ideas here.": "වැදගත් අදහස් මෙතැන ඉක්මනින් සටහන් කරන්න.",
    "📊 Personal Study Analytics": "📊 පුද්ගලික අධ්‍යයන විශ්ලේෂණ",
    "🚀 Progress Overview": "🚀 ප්‍රගති දළ විශ්ලේෂණය",
    "📈 Overall Score vs Missed Questions": "📈 සමස්ත ලකුණු එදිරිව වැරදි පිළිතුරු",
    "⏱️ Pomodoro Minutes Over Time": "⏱️ කාලයත් සමඟ පොමදෝරෝ මිනිත්තු",
    "▶️ Start": "▶️ ආරම්භය",
    "▶️ Resume": "▶️ දිගටම",
    "🔁 Restart": "🔁 නැවත ආරම්භය",
    "⏸️ Pause": "⏸️ විරාමය",
    "🔄 Reset": "🔄 යළි සකසන්න",
    "Focusing…": "අවධානය යොමුව…",
    "Session complete 🎉": "සැසිය අවසන් 🎉",
    "Paused": "විරාමයේ",
    "Ready": "සූදානම්",
    "Great job! Now take a short break. ☕": "වැඩක් කරා! දැන් කෙටි විවේකයක් ගන්න. ☕",
    "🔄 Switch Profile": "🔄 පැතිකඩ මාරු කරන්න",
    "No badges unlocked yet!": "තවම බැජ් කිසිවක් හිමි වී නැත!",
}

def t(text):
    """Translate a UI string to the active profile's language (falls back to English)."""
    lang = st.session_state.get("app_language", "en")
    if lang == "si":
        return TRANSLATIONS.get(text, text)
    return text

DEFAULT_PROFILE = {
    "user_name": "",
    "user_grade": "Grade 8",
    "user_age": 13,
    "user_gender": "Prefer not to say",
    "theme": "dark",
    "language": "en",
    "todo_list": [],
    "scribble_notes": [],
    "flashcards": [],
    "analytics": {
        "quiz_taken": 0,
        "total_score": 0,
        "total_questions": 0,
        "pomodoro_sessions": 0,
        "flashcards_reviewed": 0,
        "math_problems_solved": 0,
    },
    "gamification": {
        "xp": 0,
        "level": 1,
        "streak": 0,
        "longest_streak": 0,
        "last_active_date": None,
        "badges": [],
    },
    "quiz_history": [],
    "pomodoro_history": [],
}

# PDF HELPER FUNCTION
def extract_text_from_pdf(pdf_file):
    try:
        reader = PyPDF2.PdfReader(pdf_file)
        text = "".join([page.extract_text() + "\n" for page in reader.pages if page.extract_text()])
        return text
    except Exception as e:
        return f"Error extracting text from PDF: {e}"

# DATA PERSISTENCE
def load_all_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "users" not in data or not isinstance(data["users"], dict):
                    data["users"] = {}
                return data
        except Exception:
            return {"users": {}}
    return {"users": {}}

def save_all_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def new_profile(name, grade, age, gender):
    profile = json.loads(json.dumps(DEFAULT_PROFILE))
    profile["user_name"] = name
    profile["user_grade"] = grade
    profile["user_age"] = age
    profile["user_gender"] = gender
    return profile

def ensure_profile_shape(profile):
    for key, val in DEFAULT_PROFILE.items():
        if key not in profile:
            profile[key] = json.loads(json.dumps(val))
    if "analytics" not in profile or not isinstance(profile["analytics"], dict):
        profile["analytics"] = json.loads(json.dumps(DEFAULT_PROFILE["analytics"]))
    for key, val in DEFAULT_PROFILE["analytics"].items():
        profile["analytics"].setdefault(key, val)
    if "gamification" not in profile or not isinstance(profile["gamification"], dict):
        profile["gamification"] = json.loads(json.dumps(DEFAULT_PROFILE["gamification"]))
    for key, val in DEFAULT_PROFILE["gamification"].items():
        profile["gamification"].setdefault(key, val)
    profile.setdefault("theme", "dark")
    profile.setdefault("language", "en")
    profile.setdefault("flashcards", [])
    return profile

# GAMIFICATION ENGINE
def level_for_xp(xp):
    return (xp // XP_PER_LEVEL) + 1

def xp_progress(xp):
    lvl = level_for_xp(xp)
    into_level = xp % XP_PER_LEVEL
    return lvl, into_level, XP_PER_LEVEL

def award_badge(profile, badge_id):
    if badge_id not in profile["gamification"]["badges"]:
        profile["gamification"]["badges"].append(badge_id)
        st.session_state.setdefault("new_badges_queue", [])
        st.session_state["new_badges_queue"].append(badge_id)

def check_badges(profile):
    g = profile["gamification"]
    a = profile["analytics"]

    if a["quiz_taken"] >= 1: award_badge(profile, "first_steps")
    if a["quiz_taken"] >= 5: award_badge(profile, "quiz_5")
    if a["quiz_taken"] >= 20: award_badge(profile, "quiz_20")
    if a["pomodoro_sessions"] >= 5: award_badge(profile, "pomodoro_5")
    if a["pomodoro_sessions"] >= 25: award_badge(profile, "pomodoro_25")
    if a.get("flashcards_reviewed", 0) >= 10: award_badge(profile, "flashcard_10")
    if g["streak"] >= 3: award_badge(profile, "streak_3")
    if g["streak"] >= 7: award_badge(profile, "streak_7")
    if g["streak"] >= 30: award_badge(profile, "streak_30")
    if g["level"] >= 5: award_badge(profile, "level_5")
    if g["level"] >= 10: award_badge(profile, "level_10")

def add_xp(profile, amount, reason=""):
    g = profile["gamification"]
    old_level = g["level"]
    g["xp"] += amount
    new_level = level_for_xp(g["xp"])
    g["level"] = new_level
    if new_level > old_level:
        st.session_state.setdefault("level_up_queue", [])
        st.session_state["level_up_queue"].append(new_level)
    check_badges(profile)

def touch_daily_streak(profile):
    g = profile["gamification"]
    today_str = str(date.today())
    last = g.get("last_active_date")

    if last == today_str: return

    if last is None:
        g["streak"] = 1
    else:
        try:
            last_date = datetime.strptime(last, "%Y-%m-%d").date()
            gap = (date.today() - last_date).days
        except Exception:
            gap = 99
        if gap == 1:
            g["streak"] += 1
        elif gap >= 2:
            g["streak"] = 1

    g["longest_streak"] = max(g.get("longest_streak", 0), g["streak"])
    g["last_active_date"] = today_str
    check_badges(profile)

def render_gamification_popups():
    for lvl in st.session_state.get("level_up_queue", []):
        st.toast(f"🎉 Level Up! You're now Level {lvl}!", icon="🚀")
    st.session_state["level_up_queue"] = []
    for badge_id in st.session_state.get("new_badges_queue", []):
        badge = BADGES.get(badge_id)
        if badge:
            st.toast(f"Badge unlocked: {badge['label']}", icon="🏅")
    st.session_state["new_badges_queue"] = []

# SPACED REPETITION ENGINE (SM-2 lite)
def new_flashcard(front, back, subject):
    return {
        "id": str(uuid.uuid4())[:8],
        "front": front,
        "back": back,
        "subject": subject,
        "ease": 2.5,
        "interval_days": 0,
        "due_date": str(date.today()),
        "reps": 0,
    }

def schedule_flashcard(card, grade):
    ease = card.get("ease", 2.5)
    interval = card.get("interval_days", 0)
    reps = card.get("reps", 0)

    if grade == "again":
        ease = max(1.3, ease - 0.3)
        interval = 0
        reps = 0
    else:
        if grade == "hard":
            ease = max(1.3, ease - 0.15)
            factor = 1.2
        elif grade == "good":
            factor = ease
        else:  
            ease = ease + 0.15
            factor = ease * 1.3
        interval = 1 if interval == 0 else max(1, round(interval * factor))
        reps += 1

    card["ease"] = round(ease, 2)
    card["interval_days"] = interval
    card["reps"] = reps
    card["due_date"] = str(date.today() + timedelta(days=interval))
    return card

if "all_data" not in st.session_state:
    st.session_state.all_data = load_all_data()

if "active_user" not in st.session_state:
    st.session_state.active_user = None

# PARENT / TEACHER READ-ONLY VIEW
# Reached via a link like "?view=parent&user=<student name>" — shows a
# read-only progress summary for that one profile. No login, no editing,
# no AI calls happen on this path; it just reads existing saved data.
if st.query_params.get("view") == "parent":
    viewed_user = st.query_params.get("user", "")

    st.markdown("<h2 style='text-align:center;'>👀 Parent / Teacher View</h2>", unsafe_allow_html=True)
    users = st.session_state.all_data.get("users", {})
    if viewed_user not in users:
        st.error("No profile found for this link. Please check the link with the student.")
    else:
        p = ensure_profile_shape(users[viewed_user])
        gam = p["gamification"]
        analytics = p["analytics"]
        lvl, into_level, needed = xp_progress(gam["xp"])

        st.subheader(f"{p['user_name']} — {p['user_grade']}")
        st.caption("Read-only summary. This link cannot edit anything or start any AI activity.")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Level", lvl)
        c2.metric("Total XP", gam["xp"])
        c3.metric("Current Streak", f"{gam.get('streak', 0)} 🔥")
        c4.metric("Longest Streak", gam.get("longest_streak", 0))

        accuracy = 0
        if analytics.get("total_questions", 0) > 0:
            accuracy = int((analytics["total_score"] / analytics["total_questions"]) * 100)
        c5, c6, c7 = st.columns(3)
        c5.metric("Quizzes Taken", analytics.get("quiz_taken", 0))
        c6.metric("Quiz Accuracy", f"{accuracy}%")
        c7.metric("Pomodoro Sessions", analytics.get("pomodoro_sessions", 0))

        if gam.get("badges"):
            st.write("**Badges earned:**")
            st.write(", ".join(BADGES[b]["label"] for b in gam["badges"] if b in BADGES))

        pom_history = p.get("pomodoro_history", [])
        if pom_history:
            st.write("**Recent focus sessions:**")
            pdf_hist = pd.DataFrame(pom_history).groupby("date", as_index=False).agg(minutes=("minutes", "sum"))
            st.bar_chart(data=pdf_hist, x="date", y="minutes", use_container_width=True)

        quiz_hist = p.get("quiz_history", [])
        if quiz_hist:
            st.write("**Recent quiz results:**")
            st.dataframe(pd.DataFrame(quiz_hist)[["date", "subject", "score", "total"]], use_container_width=True, hide_index=True)
    st.stop()

def current_profile():
    return st.session_state.all_data["users"][st.session_state.active_user]

def save_current():
    save_all_data(st.session_state.all_data)

# AI SETUP
def get_api_key():
    key = st.secrets.get("GEMINI_API_KEY") if hasattr(st, "secrets") else None
    if not key:
        key = os.environ.get("GEMINI_API_KEY")
    return key

@st.cache_resource(show_spinner=False)
def get_client():
    api_key = get_api_key()
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

def get_ai_response(prompt, image=None):
    client = get_client()
    if client is None:
        return ("⚠️ API Key සොයාගත නොහැක. .streamlit/secrets.toml ගොනුවේ "
                "GEMINI_API_KEY = \"your-key-here\" ලෙස එක් කරන්න.")
    try:
        contents_list = [prompt]
        if image is not None:
            contents_list.append(image)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents_list,
        )
        return response.text
    except Exception as e:
        return f"ERROR: Please check your internet connection ({e})"

def parse_quiz_json(raw_text):
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```json", "", cleaned)
    cleaned = re.sub(r"^```", "", cleaned)
    cleaned = re.sub(r"```$", "", cleaned)
    cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except Exception:
        pass
    try:
        return ast.literal_eval(cleaned)
    except Exception:
        pass
    match = re.search(r"\[.*\]", cleaned, re.DOTALL)
    if match:
        block = match.group(0)
        try:
            return json.loads(block)
        except Exception:
            return ast.literal_eval(block)
    raise ValueError("Could not parse quiz JSON")

# THEME SYSTEM
# Both themes now share ONE CSS ruleset driven by CSS variables, so every
# component (dock, profile card, badges, pomodoro ring, buttons) looks
# equally polished regardless of which theme is active.
THEME_TOKENS = {
    "dark": {
        "bg": "#0B0F17",
        "bg-elevated": "#161B26",
        "text": "#F1F5F9",
        "muted": "#94A3B8",
        "muted-2": "#64748B",
        "sidebar-bg": "#111827",
        "border": "rgba(255, 255, 255, 0.08)",
        "card-bg": "rgba(30, 41, 59, 0.5)",
        "dock-bg": "rgba(15, 23, 42, 0.85)",
        "track-bg": "rgba(255, 255, 255, 0.08)",
        "accent-1": "#6366F1",
        "accent-2": "#A855F7",
        "accent-soft": "rgba(99, 102, 241, 0.15)",
        "shadow": "0 4px 12px rgba(0, 0, 0, 0.25)",
    },
    "light": {
        "bg": "#F8FAFC",
        "bg-elevated": "#FFFFFF",
        "text": "#0F172A",
        "muted": "#475569",
        "muted-2": "#64748B",
        "sidebar-bg": "#FFFFFF",
        "border": "rgba(15, 23, 42, 0.08)",
        "card-bg": "rgba(255, 255, 255, 0.9)",
        "dock-bg": "rgba(255, 255, 255, 0.85)",
        "track-bg": "rgba(15, 23, 42, 0.08)",
        "accent-1": "#6366F1",
        "accent-2": "#A855F7",
        "accent-soft": "rgba(99, 102, 241, 0.10)",
        "shadow": "0 4px 12px rgba(15, 23, 42, 0.08)",
    },
}

def apply_theme(theme="dark"):
    t = THEME_TOKENS.get(theme, THEME_TOKENS["dark"])
    root_vars = "".join(f"--{k}: {v};" for k, v in t.items())

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    :root {{ {root_vars} }}

    html, body, .stApp, [class*="css"],
    h1, h2, h3, h4, h5, h6, p, span, label, button, input, textarea, select,
    div[data-testid="stMarkdownContainer"] * {{
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }}

    .stApp {{ background-color: var(--bg); color: var(--text); }}

    section[data-testid="stSidebar"] {{
        background-color: var(--sidebar-bg);
        border-right: 1px solid var(--border);
    }}

    /* Subtle page-load transition so switching sections feels alive, not jarring */
    [data-testid="stMainBlockContainer"] {{
        padding-right: 240px !important;
        padding-top: 2rem !important;
        padding-left: 2rem !important;
        animation: sso-fade-in 0.35s ease;
    }}
    @keyframes sso-fade-in {{
        from {{ opacity: 0; transform: translateY(6px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    @media (prefers-reduced-motion: reduce) {{
        [data-testid="stMainBlockContainer"] {{ animation: none; }}
    }}

    /* ---------- Floating dock navigation ---------- */
    div[data-testid="stRadio"] {{
        position: fixed !important;
        right: 20px !important;
        top: 0 !important;
        transform: translateY(50%) !important;
        left: auto !important;
        z-index: 999999 !important;
        background: var(--dock-bg) !important;
        backdrop-filter: blur(20px) saturate(180%) !important;
        border: 1px solid var(--border) !important;
        padding: 10px 8px !important;
        border-radius: 20px !important;
        box-shadow: -5px 10px 30px rgba(0, 0, 0, 0.25);
        max-height: 90vh !important;
        width: auto !important;
        transition: background 0.3s ease, border-color 0.3s ease;
    }}
    div[data-testid="stRadio"] > div {{
        display: flex !important;
        flex-direction: column !important;
        gap: 6px !important;
    }}
    div[data-testid="stRadio"] label > div:first-child {{ display: none !important; }}
    div[data-testid="stRadio"] label {{
        background: transparent !important;
        padding: 6px 12px !important;
        border-radius: 12px !important;
        color: var(--muted) !important;
        cursor: pointer !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        white-space: nowrap;
    }}
    div[data-testid="stRadio"] label:hover {{
        color: var(--text) !important;
        background: var(--accent-soft) !important;
    }}
    div[data-testid="stRadio"] label[data-checked="true"] {{
        background: linear-gradient(135deg, var(--accent-1) 0%, var(--accent-2) 100%) !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }}

    /* On narrow / mobile screens the side dock becomes a bottom nav bar */
    @media (max-width: 900px) {{
        div[data-testid="stRadio"] {{
            top: auto !important;
            bottom: 0 !important;
            right: 0 !important;
            left: 0 !important;
            transform: none !important;
            width: 100% !important;
            max-height: none !important;
            border-radius: 20px 20px 0 0 !important;
            border-bottom: none !important;
        }}
        div[data-testid="stRadio"] > div {{
            flex-direction: row !important;
            overflow-x: auto !important;
            justify-content: flex-start !important;
        }}
        [data-testid="stMainBlockContainer"] {{
            padding-right: 1.2rem !important;
            padding-left: 1.2rem !important;
            padding-bottom: 96px !important;
        }}
    }}

    div[data-testid="stMetric"] {{
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 16px;
    }}

    /* ---------- Buttons ---------- */
    .stButton > button {{
        border-radius: 12px !important;
        border: 1px solid rgba(99, 102, 241, 0.4) !important;
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(168, 85, 247, 0.15)) !important;
        color: var(--text) !important;
        font-weight: 600 !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: var(--shadow) !important;
    }}
    .stButton > button:hover {{
        transform: translateY(-2px) scale(1.02) !important;
        background: linear-gradient(135deg, var(--accent-1) 0%, var(--accent-2) 100%) !important;
        color: #FFFFFF !important;
        border-color: transparent !important;
        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.45) !important;
    }}
    .stButton > button:active {{
        transform: translateY(0px) scale(0.98) !important;
        box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3) !important;
    }}
    .stButton > button:focus-visible {{
        outline: 2px solid var(--accent-1) !important;
        outline-offset: 2px !important;
    }}

    /* ---------- Profile card ---------- */
    .profile-card {{
        background: var(--card-bg);
        backdrop-filter: blur(16px);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 18px;
        margin-bottom: 12px;
    }}
    .profile-header {{ display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }}
    .avatar-box {{
        font-size: 1.8rem;
        background: var(--accent-soft);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 14px;
        padding: 6px 10px;
    }}
    .profile-title {{ margin: 0; font-size: 1.1rem; font-weight: 700; color: var(--text); }}
    .profile-subtitle {{ margin: 0; font-size: 0.78rem; color: var(--muted); }}
    .profile-meta {{ display: flex; justify-content: space-between; font-size: 0.78rem; color: var(--muted-2); margin-bottom: 10px; }}
    .level-badge {{ background: linear-gradient(135deg, var(--accent-1), var(--accent-2)); color: #FFF; padding: 2px 8px; border-radius: 8px; font-weight: 600; }}
    .xp-section {{ margin-bottom: 12px; }}
    .xp-labels {{ display: flex; justify-content: space-between; font-size: 0.73rem; color: var(--muted); margin-bottom: 5px; }}
    .xp-track {{ background: var(--track-bg); border-radius: 10px; height: 7px; width: 100%; overflow: hidden; }}
    .xp-bar {{ background: linear-gradient(90deg, var(--accent-1), var(--accent-2)); height: 100%; border-radius: 10px; transition: width 0.5s ease; }}
    .streak-pill {{ display: flex; justify-content: space-between; background: var(--card-bg); border: 1px solid var(--border); padding: 6px 12px; border-radius: 12px; font-size: 0.8rem; }}
    .badges-grid {{ display: flex; flex-wrap: wrap; gap: 6px; }}
    .badge-tag, .badge-chip {{
        background: var(--accent-soft);
        border: 1px solid rgba(99, 102, 241, 0.25);
        color: var(--text);
        font-size: 0.72rem;
        padding: 4px 8px;
        border-radius: 8px;
        display: inline-block;
        margin: 2px;
    }}

    /* ---------- Pomodoro ring ---------- */
    .pomo-ring {{
        width: 220px; height: 220px; border-radius: 50%;
        margin: 12px auto 20px auto;
        background: conic-gradient(var(--accent-1) var(--pct, 0%), var(--track-bg) 0);
        display: flex; align-items: center; justify-content: center;
        transition: background 0.6s linear;
        box-shadow: 0 0 40px rgba(99, 102, 241, 0.2);
    }}
    .pomo-ring-inner {{
        width: 178px; height: 178px; border-radius: 50%;
        background: var(--bg-elevated);
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        gap: 4px;
        border: 1px solid var(--border);
    }}
    .pomo-time {{ font-size: 2.1rem; font-weight: 700; letter-spacing: 0.5px; color: var(--text); font-variant-numeric: tabular-nums; }}
    .pomo-label {{ font-size: 0.75rem; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; }}

    /* ---------- Flashcards ---------- */
    .flash-face {{
        padding: 24px; border-radius: 14px; text-align: center; font-size: 1.25rem;
        background: var(--card-bg); border: 1px solid var(--border);
    }}
    </style>
    """, unsafe_allow_html=True)


# LOGIN / PROFILE SELECTION SCREEN
if st.session_state.active_user is None:
    apply_theme("dark")
    st.markdown("<h2 style='text-align:center;'>👋 Welcome to Smart Study Organizer Pro!</h2>", unsafe_allow_html=True)
    existing_users = list(st.session_state.all_data["users"].keys())
    tab1, tab2 = st.tabs(["🙋 Existing Profile", "✨ New Profile"])

    with tab1:
        if existing_users:
            picked = st.selectbox("Please choose your profile:", existing_users)
            if st.button("Enter the app ➡️", use_container_width=True):
                st.session_state.all_data["users"][picked] = ensure_profile_shape(st.session_state.all_data["users"][picked])
                st.session_state.active_user = picked
                st.rerun()
        else:
            st.info("It looks like you haven't created an account yet. You can create one from the New Profile tab.")

    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            name_input = st.text_input("Your Name:")
            grade_input = st.selectbox("Grade:", [f"Grade {i}" for i in range(1, 14)])
        with col2:
            age_input = st.number_input("Age:", min_value=5, max_value=18, value=13)
            gender_input = st.selectbox("Gender:", ["Male", "Female", "Prefer not to say"])

        if st.button("Create your Profile 🚀", use_container_width=True):
            if not name_input.strip():
                st.error("Please enter your name")
            elif name_input.strip() in existing_users:
                st.error("This name already exists. Please try another name.")
            else:
                profile = new_profile(name_input.strip(), grade_input, age_input, gender_input)
                st.session_state.all_data["users"][name_input.strip()] = profile
                save_all_data(st.session_state.all_data)
                st.session_state.active_user = name_input.strip()
                st.rerun()

    st.stop()

# PERSONALIZED CONTEXT
user_info = current_profile()
user_gender = user_info.get("user_gender", "Prefer not to say")
user_age = user_info.get("user_age", 13)
user_grade = user_info.get("user_grade", "Grade 8")

apply_theme(user_info.get("theme", "dark"))
st.session_state.app_language = user_info.get("language", "en")

if not st.session_state.get(f"_streak_touched_{st.session_state.active_user}"):
    touch_daily_streak(user_info)
    save_current()
    st.session_state[f"_streak_touched_{st.session_state.active_user}"] = True
render_gamification_popups()

if user_gender == "Male": greeting = "Welcome back, King 👑"
elif user_gender == "Female": greeting = "Welcome back, Queen 👑"
else: greeting = "Welcome back, Champion 🌟"

LANGUAGE_NAMES = {"en": "English", "si": "Sinhala"}
language_instruction = (
    f"Respond in {LANGUAGE_NAMES.get(user_info.get('language', 'en'), 'English')}, "
    "using vocabulary and sentence structure appropriate for the student's age and grade."
)

# Strict syllabus-bounded context: used for every study/learning module
# (Mindmap, Summarizer, MCQ Quiz, Math Solver, Flashcards) so the AI never
# introduces content beyond what the student's grade actually covers.
# Deliberately NOT used for Daily Facts, which is meant to explore general
# knowledge beyond the syllabus.
age_context = (
    f"The user is {user_age} years old in {user_grade} in Sri Lanka. "
    "CRITICAL RULE: Note Summarizer, MindMap Generator, AI MCQ Quiz, Math Problem Solver, and FlashCards MUST strictly align "
    "with the Sri Lankan local school syllabus for the user's grade — not above it, not below it. Use valid sources "
    "(e.g. edupub.gov.lk, dpeducation.lk, e-thaksalawa.moe.gov.lk). Do NOT introduce any concept, term, formula, or vocabulary "
    "that is not part of this grade's official syllabus, even if it is technically related or commonly taught in other "
    "countries or exam systems. If a topic the user asks about is normally taught at a higher grade, simplify it down to what "
    "is appropriate for this grade rather than teaching the advanced version. "
    "Keep explanations beginner-friendly, clean, and engaging. " + language_instruction
)

# Lighter context for Daily Facts only — general knowledge, not syllabus-bound.
daily_facts_context = (
    f"The user is {user_age} years old in {user_grade} in Sri Lanka. "
    "Keep explanations beginner-friendly, clean, and engaging. " + language_instruction
)


# DYNAMIC SIDEBAR RENDERER
def render_sidebar():
    profile = current_profile()
    gam = profile["gamification"]
    badges = gam.get("badges", [])
    
    lvl, into_level, needed = xp_progress(gam["xp"])
    pct = int((into_level / needed) * 100)

    with st.sidebar:
        st.markdown(f"""
            <div class="profile-card">
                <div class="profile-header">
                    <div class="avatar-box">👾</div>
                    <div>
                        <h3 class="profile-title">{profile['user_name']}'s Space</h3>
                        <p class="profile-subtitle">{greeting}</p>
                    </div>
                </div>
                
                <div class="profile-meta">
                    <span>Age: {profile['user_age']} &bull; {profile['user_grade']}</span>
                    <span class="level-badge">Level {lvl}</span>
                </div>

                <div class="xp-section">
                    <div class="xp-labels">
                        <span>XP Progress</span>
                        <span>{into_level} / {needed} XP</span>
                    </div>
                    <div class="xp-track">
                        <div class="xp-bar" style="width: {pct}%;"></div>
                    </div>
                </div>

                <div class="streak-pill">
                    <span>🔥 <strong>{gam.get('streak', 0)}-day streak</strong></span>
                    <span class="streak-best">(best: {gam.get('longest_streak', 0)})</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with st.expander(f"🥇 Badges ({len(badges)}/{len(BADGES)})", expanded=False):
            if badges:
                badge_tags = "".join([f'<span class="badge-tag">{BADGES[b]["label"]}</span>' for b in badges if b in BADGES])
                st.markdown(f'<div class="badges-grid">{badge_tags}</div>', unsafe_allow_html=True)
            else:
                st.caption(t("No badges unlocked yet!"))

        st.markdown("<div style='margin: 15px 0;'></div>", unsafe_allow_html=True)

        is_dark = profile.get("theme", "dark") == "dark"
        theme_choice = st.toggle("🌙 Dark mode", value=is_dark, key="theme_toggle")
        new_theme = "dark" if theme_choice else "light"
        if new_theme != profile.get("theme", "dark"):
            profile["theme"] = new_theme
            save_current()
            st.rerun()

        is_sinhala = profile.get("language", "en") == "si"
        lang_choice = st.toggle("🇱🇰 සිංහල (Sinhala)", value=is_sinhala, key="language_toggle")
        new_lang = "si" if lang_choice else "en"
        if new_lang != profile.get("language", "en"):
            profile["language"] = new_lang
            save_current()
            st.rerun()

        with st.expander("🔗 Parent / Teacher View"):
            st.caption("Share this with a parent or teacher for a read-only progress summary — no login, no editing.")
            st.code(f"?view=parent&user={profile['user_name']}", language=None)
            st.caption("Append this to the app's web address in your browser and share that full link.")

        if st.button(t("🔄 Switch Profile"), use_container_width=True):
            st.session_state.active_user = None
            st.rerun()

# Invoking sidebar rendering
render_sidebar()

# MODULE FUNCTIONS
def show_daily_facts():
    st.header(t("💡 Daily Tech & Science Facts"))
    st.caption(t("Get interesting Tech/Science facts here"))
    today_str = str(date.today())
    need_new = ("daily_fact" not in st.session_state or st.session_state.get("daily_fact_date") != today_str)

    if st.button("Get a new Fact 🧠") or need_new:
        with st.spinner("Your fact is being retrieved by AI..."):
            prompt = f"{daily_facts_context} Tell an amazing, mind-blowing, yet easy-to-understand science or computer technology fact. Explain it in 3 clear bullet points."
            st.session_state.daily_fact = get_ai_response(prompt)
            st.session_state.daily_fact_date = today_str

    st.info(st.session_state.daily_fact)

def show_mindmap():
    st.header(t("🗺️ AI Mindmap Generator"))
    st.caption(t("Turn your notes or PDFs into a structured, easy-to-understand mindmap."))
    
    mm_file = st.file_uploader("Upload Notes (PDF, PNG, JPG):", type=["pdf", "png", "jpg", "jpeg"])
    mm_text = st.text_area("Or type/paste the main topic or notes here:", height=100)

    if st.button("Generate Mindmap 🧠"):
        if mm_file or mm_text:
            with st.spinner("Structuring your mindmap..."):
                extracted_content = mm_text
                img = None
                
                if mm_file:
                    if mm_file.name.lower().endswith(".pdf"):
                        extracted_content += "\n" + extract_text_from_pdf(mm_file)
                    else:
                        img = Image.open(mm_file)

                prompt = (
                    f"{age_context} Based on the following content, generate a clear, logical, and structured text-based Mindmap. "
                    "Format the Mindmap using clean nested markdown bullet points. Make it extremely intuitive for a beginner to study. "
                    f"Content: {extracted_content}"
                )
                
                mm_output = get_ai_response(prompt, image=img)
                st.success("Your Mindmap is Ready:")
                st.markdown(mm_output)
                
                profile = current_profile()
                add_xp(profile, XP_REWARDS["mindmap_created"], "mindmap_created")
                save_current()
                render_gamification_popups()
        else:
            st.warning("Please provide a topic or upload a file to generate a mindmap.")

def show_summarizer():
    st.header(t("📝 AI Note Summarizer"))
    uploaded_file = st.file_uploader("Upload Notes (PDF, PNG, JPG):", type=["pdf", "png", "jpg", "jpeg"])
    user_note = st.text_area("Or paste the note here:", height=150)

    img = None
    pdf_text = ""
    if uploaded_file:
        if uploaded_file.name.lower().endswith(".pdf"):
            pdf_text = extract_text_from_pdf(uploaded_file)
            st.success("PDF loaded successfully!")
        else:
            img = Image.open(uploaded_file)
            st.image(img, width=300)

    if st.button("Summarize the note ✨"):
        if uploaded_file or user_note:
            with st.spinner("Your note is being summarized by AI..."):
                combined_text = user_note + "\n" + pdf_text
                prompt = f"{age_context} Summarize these notes clearly in bullet points. Notes: {combined_text}. Explain it simply so a beginner can master it."
                output = get_ai_response(prompt, image=img)
                st.success("Here is the Summary:")
                st.write(output)
                
                profile = current_profile()
                add_xp(profile, XP_REWARDS["note_summarized"], "note_summarized")
                save_current()
                render_gamification_popups()
        else:
            st.warning("Please provide a note or upload a file.")

def show_mcq_quiz():
    st.header(t("❓ AI Anti-Cheat MCQ Quiz"))
    st.caption(t("Test your knowledge with questions based on the Sri Lankan Syllabus."))

    subject = st.text_input("Subject — e.g. Science, History, Maths:", value="General Knowledge")
    q_file = st.file_uploader("Upload Notes to test yourself (PDF, PNG, JPG):", type=["pdf", "png", "jpg", "jpeg"])
    topic = st.text_input("Topic of lesson:")
    difficulty = st.select_slider("Difficulty:", options=["Easy", "Medium", "Hard"], value="Medium")
    num_questions = st.slider("Number of questions:", min_value=1, max_value=20, value=5)

    q_img = None
    pdf_text = ""
    if q_file:
        if q_file.name.lower().endswith(".pdf"):
            pdf_text = extract_text_from_pdf(q_file)
            st.success("PDF loaded successfully!")
        else:
            q_img = Image.open(q_file)
            st.image(q_img, width=300)

    if st.button("Get your MCQ questions 🎯"):
        if q_file or topic:
            with st.spinner(f"{num_questions} questions are being created by AI..."):
                combined_context = (topic or "") + "\n" + pdf_text
                prompt = (
                    f"{age_context} Subject: {subject}. Difficulty: {difficulty}. "
                    f"Based on the topic/image/document, generate exactly {num_questions} multiple choice questions. "
                    f"Return ONLY a raw JSON array of exactly {num_questions} objects, each with keys: "
                    "'question', 'A', 'B', 'C', 'D', 'correct' (one of 'A'/'B'/'C'/'D'). "
                    "No explanation outside the JSON. Topic/Content: " + (combined_context if combined_context.strip() else "see attached image")
                )
                raw_json = get_ai_response(prompt, image=q_img)
                try:
                    st.session_state.quiz_list = parse_quiz_json(raw_json)
                    st.session_state.quiz_subject = subject
                    st.session_state.quiz_answers = {}
                    st.session_state.quiz_checked = False
                except Exception:
                    st.error("There was an error while creating questions. Please try again.")
        else:
            st.warning("Please give a topic or upload a file.")

    if "quiz_list" in st.session_state:
        st.write("---")
        st.write("### ✍️ Answer the questions:")

        for idx, q in enumerate(st.session_state.quiz_list):
            st.markdown(f"#### **Question {idx+1}:** {q['question']}")
            options = [f"A) {q['A']}", f"B) {q['B']}", f"C) {q['C']}", f"D) {q['D']}"]
            user_choice = st.radio(f"q_{idx}", options, key=f"q_ans_{idx}", label_visibility="collapsed")
            st.session_state.quiz_answers[idx] = user_choice[0]
            st.write("")

        if st.button("Submit Answers ✔️") and not st.session_state.get("quiz_checked", False):
            st.session_state.quiz_checked = True
            score = 0
            for idx, q in enumerate(st.session_state.quiz_list):
                if st.session_state.quiz_answers.get(idx, "-") == q["correct"]:
                    score += 1

            total_qs = len(st.session_state.quiz_list)
            profile = current_profile()
            profile["analytics"]["quiz_taken"] += 1
            profile["analytics"]["total_score"] += score
            profile["analytics"]["total_questions"] += total_qs
            profile["quiz_history"].append({
                "date": str(date.today()),
                "subject": st.session_state.get("quiz_subject", "General"),
                "score": score,
                "total": total_qs,
            })
            add_xp(profile, score * XP_REWARDS["quiz_question_correct"], "quiz_question_correct")
            add_xp(profile, XP_REWARDS["quiz_complete"], "quiz_complete")
            if total_qs > 0 and score == total_qs:
                award_badge(profile, "perfect_score")
            save_current()

        if st.session_state.get("quiz_checked", False):
            score = 0
            st.write("---")
            st.write("### 📊 Result Summary:")
            for idx, q in enumerate(st.session_state.quiz_list):
                u_ans = st.session_state.quiz_answers.get(idx, "-")
                if u_ans == q["correct"]:
                    score += 1
                    st.success(f"✅ Question {idx+1}: Correct! (Answer: {u_ans})")
                else:
                    st.error(f"❌ Question {idx+1}: Wrong! (Your Answer: {u_ans} | Correct: {q['correct']})")

            total_qs = len(st.session_state.quiz_list)
            st.markdown(f"## 🏆 Total Score: **{score} / {total_qs}**")
            if score == total_qs:
                st.balloons()
                st.success("Perfect! All questions are correct! 🥳")
            render_gamification_popups()

def show_math_solver():
    st.header(t("🧠 AI Math Problem Solver"))
    st.caption(t("Learn math step-by-step with AI"))

    math_file = st.file_uploader("Picture of a math question (Optional):", type=["png", "jpg", "jpeg"])
    math_query = st.text_input("Or write down your question here:")

    math_img = Image.open(math_file) if math_file else None
    if math_img:
        st.image(math_img, width=300)

    if st.button("Solve problem 🧮"):
        if math_img or math_query:
            with st.spinner("Your question is being solved by AI..."):
                prompt = (
                    f"{age_context} Solve this math problem step-by-step: {math_query}. "
                    "Do NOT just give the final answer. Act like a friendly tutor teaching a beginner. "
                    "Break down every step clearly."
                )
                math_solution = get_ai_response(prompt, image=math_img)
                st.success("Here is how to solve your question:")
                st.write(math_solution)

                profile = current_profile()
                profile["analytics"]["math_problems_solved"] = profile["analytics"].get("math_problems_solved", 0) + 1
                add_xp(profile, XP_REWARDS["math_solved"], "math_solved")
                save_current()
                render_gamification_popups()
        else:
            st.warning("Please provide a question or image")

def show_flashcards():
    st.header(t("🗂️ Flashcards & Spaced Repetition"))
    st.caption(t("Generate flashcards with AI, then review them on a smart schedule."))
    profile = current_profile()
    profile.setdefault("flashcards", [])

    tab_review, tab_generate, tab_manage = st.tabs(["🧠 Review Due Cards", "✨ Generate New Cards", "📋 Manage All Cards"])

    today_str = str(date.today())
    due_cards = [c for c in profile["flashcards"] if c.get("due_date", today_str) <= today_str]

    with tab_review:
        if not due_cards:
            if profile["flashcards"]:
                st.success("🎉 No cards due right now — you're all caught up! Come back tomorrow.")
            else:
                st.info("You don't have any flashcards yet. Head to 'Generate New Cards' to create some.")
        else:
            st.caption(f"{len(due_cards)} card(s) due today")
            review_idx = st.session_state.get("flash_review_idx", 0)
            if review_idx >= len(due_cards):
                st.session_state.flash_review_idx = 0
                review_idx = 0

            card = due_cards[review_idx]
            st.markdown(f"**Subject:** {card.get('subject', 'General')}  ·  Card {review_idx + 1}/{len(due_cards)}")
            st.markdown(f"<div class='flash-face'>{card['front']}</div>", unsafe_allow_html=True)

            show_answer = st.session_state.get(f"show_back_{card['id']}", False)
            if not show_answer:
                if st.button("👁️ Show Answer", use_container_width=True):
                    st.session_state[f"show_back_{card['id']}"] = True
                    st.rerun()
            else:
                st.markdown(f"<div class='flash-face' style='margin-top:10px;border-color:var(--accent-2);'>{card['back']}</div>", unsafe_allow_html=True)
                st.write("How well did you know this?")
                g1, g2, g3, g4 = st.columns(4)
                grade_clicked = None
                if g1.button("😵 Again", use_container_width=True): grade_clicked = "again"
                if g2.button("😬 Hard", use_container_width=True): grade_clicked = "hard"
                if g3.button("🙂 Good", use_container_width=True): grade_clicked = "good"
                if g4.button("😎 Easy", use_container_width=True): grade_clicked = "easy"

                if grade_clicked:
                    for c in profile["flashcards"]:
                        if c["id"] == card["id"]:
                            schedule_flashcard(c, grade_clicked)
                            break
                    profile["analytics"]["flashcards_reviewed"] = profile["analytics"].get("flashcards_reviewed", 0) + 1
                    add_xp(profile, XP_REWARDS["flashcard_review"], "flashcard_review")
                    save_current()
                    st.session_state[f"show_back_{card['id']}"] = False
                    st.session_state.flash_review_idx = review_idx
                    render_gamification_popups()
                    st.rerun()

    with tab_generate:
        gen_subject = st.text_input("Subject:", value="General Knowledge", key="flash_gen_subject")
        gen_topic = st.text_input("Topic:", key="flash_gen_topic")
        gen_count = st.slider("Number of flashcards:", min_value=3, max_value=20, value=8, key="flash_gen_count")

        if st.button("✨ Generate Flashcards with AI"):
            if gen_topic:
                with st.spinner(f"Creating {gen_count} flashcards..."):
                    prompt = (
                        f"{age_context} Subject: {gen_subject}. Create exactly {gen_count} flashcards for the topic "
                        f"'{gen_topic}'. Return ONLY a raw JSON array of exactly {gen_count} objects, each with keys "
                        "'front' (a short question or term) and 'back' (a concise, clear answer/definition). "
                        "No explanation outside the JSON."
                    )
                    raw_json = get_ai_response(prompt)
                    try:
                        parsed = parse_quiz_json(raw_json)
                        for item in parsed:
                            profile["flashcards"].append(new_flashcard(item["front"], item["back"], gen_subject))
                        save_current()
                        st.success(f"Added {len(parsed)} new flashcards to your deck!")
                    except Exception:
                        st.error("There was an error creating flashcards. Please try again.")
            else:
                st.warning("Please give a topic")

    with tab_manage:
        if not profile["flashcards"]:
            st.info("No flashcards yet.")
        else:
            subjects = sorted(set(c.get("subject", "General") for c in profile["flashcards"]))
            for subj in subjects:
                with st.expander(f"📁 {subj} ({sum(1 for c in profile['flashcards'] if c.get('subject')==subj)} cards)"):
                    for c in [card for card in profile["flashcards"] if card.get("subject") == subj]:
                        confirm_key = f"confirm_del_card_{c['id']}"
                        cc1, cc2 = st.columns([5, 1])
                        cc1.markdown(f"**Q:** {c['front']}  \n**A:** {c['back']}  \n*Due: {c['due_date']} · Reps: {c['reps']}*")
                        if not st.session_state.get(confirm_key):
                            if cc2.button("🗑️", key=f"del_card_{c['id']}"):
                                st.session_state[confirm_key] = True
                                st.rerun()
                        else:
                            cc2.markdown("Sure?")
                            yc1, yc2 = st.columns(2)
                            if yc1.button("✅", key=f"del_card_yes_{c['id']}"):
                                profile["flashcards"] = [x for x in profile["flashcards"] if x["id"] != c["id"]]
                                save_current()
                                st.session_state.pop(confirm_key, None)
                                st.rerun()
                            if yc2.button("✖️", key=f"del_card_no_{c['id']}"):
                                st.session_state.pop(confirm_key, None)
                                st.rerun()

def show_pomodoro():
    st.header(t("⏱️ Pomodoro & Goal Progress Tracker"))
    col1, col2 = st.columns(2)
    profile = current_profile()

    with col1:
        st.subheader(t("🤖 AI Auto Task Generator"))
        goal = st.text_input("What is your goal today?")
        if st.button("Make Your Task List 📋"):
            if goal:
                with st.spinner("Your task list is being created by AI..."):
                    prompt = f"{age_context} Break down this study goal into 4 short actionable tasks. Provide only tasks without numbers, one per line:\n{goal}"
                    ai_tasks = get_ai_response(prompt).split("\n")
                    profile["todo_list"] = [t.strip("-• ").strip() for t in ai_tasks if t.strip()]
                    add_xp(profile, XP_REWARDS["task_list_created"], "task_list_created")
                    save_current()
                    render_gamification_popups()

        st.write("---")
        st.subheader(t("🎯 Study Goal Tracker"))
        todo_list = profile["todo_list"]
        checked_count = 0
        if todo_list:
            for i, task in enumerate(todo_list):
                if st.checkbox(task, key=f"saved_task_{i}"):
                    checked_count += 1
            progress_pct = int((checked_count / len(todo_list)) * 100)
            st.markdown(f"**Daily Progress: {progress_pct}% Completed**")
            st.progress(progress_pct)
        else:
            st.write("You haven't created a Task List yet.")

    with col2:
        st.subheader(t("⏱️ Pomodoro Timer"))
        render_pomodoro_timer()

def _pomodoro_defaults():
    st.session_state.setdefault("pomo_duration", 25 * 60)
    st.session_state.setdefault("pomo_remaining", st.session_state.get("pomo_duration", 25 * 60))
    st.session_state.setdefault("pomo_running", False)
    st.session_state.setdefault("pomo_end_ts", None)
    st.session_state.setdefault("pomo_just_completed", False)

def _finish_pomodoro_session(profile, minutes, completed):
    st.session_state.pomo_running = False
    st.session_state.pomo_end_ts = None
    if completed:
        profile["analytics"]["pomodoro_sessions"] += 1
        profile["pomodoro_history"].append({"date": str(date.today()), "minutes": minutes})
        add_xp(profile, XP_REWARDS["pomodoro_session"], "pomodoro_session")
        save_current()
    else:
        st.info("Timer paused — no worries, pick up whenever you're ready.")

@st.fragment(run_every=1)
def render_pomodoro_timer():
    # Non-blocking timer: previously this used a `time.sleep()` loop that
    # froze the entire app for the whole session (no navigating away, no
    # other button worked). st.fragment re-runs just this widget every
    # second instead, so the rest of the app stays fully usable.
    _pomodoro_defaults()
    profile = current_profile()
    running = st.session_state.pomo_running

    if running:
        remaining = max(0, st.session_state.pomo_end_ts - time.time())
        st.session_state.pomo_remaining = remaining
        if remaining <= 0 and not st.session_state.pomo_just_completed:
            st.session_state.pomo_just_completed = True
            minutes = st.session_state.pomo_duration // 60
            _finish_pomodoro_session(profile, minutes, completed=True)

    remaining = st.session_state.pomo_remaining
    total = st.session_state.pomo_duration
    fresh = (not running) and (remaining == total) and not st.session_state.pomo_just_completed

    if fresh:
        chosen_minutes = st.slider("Time (minutes):", 5, 60, total // 60, key="pomo_len_slider")
        st.session_state.pomo_duration = chosen_minutes * 60
        st.session_state.pomo_remaining = chosen_minutes * 60
        total = st.session_state.pomo_duration
        remaining = st.session_state.pomo_remaining

    pct = 0 if total == 0 else int(((total - remaining) / total) * 100)
    mins_left, secs_left = divmod(int(remaining), 60)
    status = t("Focusing…") if running else (t("Session complete 🎉") if st.session_state.pomo_just_completed else (t("Paused") if remaining < total else t("Ready")))

    st.markdown(f"""
        <div class="pomo-ring" style="--pct:{pct}%;">
            <div class="pomo-ring-inner">
                <span class="pomo-time">{mins_left:02d}:{secs_left:02d}</span>
                <span class="pomo-label">{status}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    b1, b2, b3 = st.columns(3)
    with b1:
        if not running:
            label = t("🔁 Restart") if st.session_state.pomo_just_completed else (t("▶️ Resume") if remaining < total else t("▶️ Start"))
            if st.button(label, use_container_width=True, key="pomo_start"):
                if st.session_state.pomo_just_completed or remaining <= 0:
                    st.session_state.pomo_remaining = st.session_state.pomo_duration
                    remaining = st.session_state.pomo_remaining
                st.session_state.pomo_end_ts = time.time() + remaining
                st.session_state.pomo_running = True
                st.session_state.pomo_just_completed = False
                st.rerun()
        else:
            if st.button(t("⏸️ Pause"), use_container_width=True, key="pomo_pause"):
                st.session_state.pomo_remaining = max(0, st.session_state.pomo_end_ts - time.time())
                _finish_pomodoro_session(profile, st.session_state.pomo_duration // 60, completed=False)
                st.rerun()
    with b2:
        if st.button(t("🔄 Reset"), use_container_width=True, key="pomo_reset"):
            st.session_state.pomo_running = False
            st.session_state.pomo_remaining = st.session_state.pomo_duration
            st.session_state.pomo_just_completed = False
            st.rerun()
    with b3:
        st.caption(f"{pct}% done")

    if st.session_state.pomo_just_completed:
        st.balloons()
        st.success(t("Great job! Now take a short break. ☕"))
        render_gamification_popups()

def show_scribble_pad():
    st.header(t("📝 Quick Scribble Pad / Sticky Notes"))
    st.caption(t("Quickly note down important ideas here."))
    profile = current_profile()

    with st.form("new_note_form", clear_on_submit=True):
        new_note = st.text_area("New Note:", height=120)
        submitted = st.form_submit_button("➕ Add Note")
        if submitted and new_note.strip():
            profile["scribble_notes"].append(new_note.strip())
            save_current()

    st.write("---")
    if profile["scribble_notes"]:
        for i, note in enumerate(reversed(profile["scribble_notes"])):
            real_idx = len(profile["scribble_notes"]) - 1 - i
            with st.expander(f"🗒️ Note {real_idx + 1}", expanded=(i == 0)):
                st.write(note)
                confirm_key = f"confirm_del_note_{real_idx}"
                if not st.session_state.get(confirm_key):
                    if st.button("🗑️ Delete", key=f"del_note_{real_idx}"):
                        st.session_state[confirm_key] = True
                        st.rerun()
                else:
                    st.warning("Delete this note? This can't be undone.")
                    cc1, cc2 = st.columns(2)
                    if cc1.button("✅ Yes, delete", key=f"del_note_yes_{real_idx}", use_container_width=True):
                        profile["scribble_notes"].pop(real_idx)
                        save_current()
                        st.session_state.pop(confirm_key, None)
                        st.rerun()
                    if cc2.button("✖️ Cancel", key=f"del_note_no_{real_idx}", use_container_width=True):
                        st.session_state.pop(confirm_key, None)
                        st.rerun()
    else:
        st.info("No notes found. Add a new note above.")

def show_analytics():
    st.header(t("📊 Personal Study Analytics"))
    profile = current_profile()
    analytics = profile["analytics"]
    gam = profile["gamification"]

    st.subheader(t("🚀 Progress Overview"))
    g1, g2, g3, g4 = st.columns(4)
    g1.metric("Level", gam["level"])
    g2.metric("Total XP", gam["xp"])
    g3.metric("Current Streak", f"{gam['streak']} 🔥")
    g4.metric("Badges Earned", f"{len(gam.get('badges', []))}/{len(BADGES)}")

    if gam.get("badges"):
        st.write("**Unlocked Badges:**")
        chips_html = "".join(f'<span class="badge-chip" title="{BADGES[b]["desc"]}">{BADGES[b]["label"]}</span>' for b in gam["badges"] if b in BADGES)
        st.markdown(chips_html, unsafe_allow_html=True)

    st.write("---")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("MCQ Quizzes Taken", analytics["quiz_taken"])
    accuracy = 0
    if analytics["total_questions"] > 0:
        accuracy = int((analytics["total_score"] / analytics["total_questions"]) * 100)
    col2.metric("MCQ Accuracy", f"{accuracy}%")
    col3.metric("Pomodoro Sessions", analytics["pomodoro_sessions"])
    col4.metric("Math Problems Solved", analytics.get("math_problems_solved", 0))

    st.write("---")
    st.subheader(t("📈 Overall Score vs Missed Questions"))
    if analytics["total_questions"] > 0:
        chart_data = pd.DataFrame({
            "Activity": ["Correct Answers", "Incorrect Answers"],
            "Count": [analytics["total_score"], analytics["total_questions"] - analytics["total_score"]],
        })
        st.bar_chart(data=chart_data, x="Activity", y="Count", use_container_width=True)

    st.subheader(t("⏱️ Pomodoro Minutes Over Time"))
    pom_history = profile.get("pomodoro_history", [])
    if pom_history:
        pdf = pd.DataFrame(pom_history)
        pdf = pdf.groupby("date", as_index=False).agg(minutes=("minutes", "sum"))
        st.bar_chart(data=pdf, x="date", y="minutes", use_container_width=True)

# PAGE ROUTING DICTIONARY WITH LABELS
PAGES = {
    "💡 Daily Facts": show_daily_facts,
    "🗺️ Mindmap": show_mindmap,
    "📝 Summarizer": show_summarizer,
    "❓ MCQ Quiz": show_mcq_quiz,
    "🧠 Math Solver": show_math_solver,
    "🎴 Flashcards": show_flashcards,
    "⏱️ Pomodoro": show_pomodoro,
    "✍️ Scribble Pad": show_scribble_pad,
    "📊 Analytics": show_analytics,
}

# FLOATING DOCK RADIO SELECTION
choice = st.radio(
    "Navigation",
    options=list(PAGES.keys()),
    horizontal=True,
    label_visibility="collapsed"
)

# EXECUTE SELECTED PAGE FUNCTION
PAGES[choice]()