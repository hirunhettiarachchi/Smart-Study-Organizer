# app.py - Smart Study Organizer Pro with all enhancements

import streamlit as st
import time
import math
import json
import os
import ast
import re
import uuid
import operator
import hashlib
import hmac
import sqlite3
import threading
import urllib.parse
from datetime import date, datetime, timedelta, timezone
import pandas as pd
from google import genai
from PIL import Image
import PyPDF2


try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# PAGE CONFIG
st.set_page_config(page_title="Smart Study Organizer Pro", page_icon="🎓", layout="wide")


DB_FILE = "study_organizer.db"
LEGACY_JSON_FILE = "study_organizer_data.json"

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
    "first_steps":      {"label": "🌱 First Steps",        "desc": "Completed your first quiz", "icon": "🌱"},
    "quiz_5":           {"label": "📚 Quiz Regular",        "desc": "Completed 5 quizzes", "icon": "📚"},
    "quiz_20":          {"label": "🏆 Quiz Master",         "desc": "Completed 20 quizzes", "icon": "🏆"},
    "perfect_score":    {"label": "💯 Perfectionist",       "desc": "Got a perfect quiz score", "icon": "💯"},
    "pomodoro_5":       {"label": "🍅 Focus Builder",       "desc": "Finished 5 Pomodoro sessions", "icon": "🍅"},
    "pomodoro_25":      {"label": "🔥 Deep Work Pro",       "desc": "Finished 25 Pomodoro sessions", "icon": "🔥"},
    "streak_3":         {"label": "⚡ 3-Day Streak",        "desc": "Studied 3 days in a row", "icon": "⚡"},
    "streak_7":         {"label": "🌟 7-Day Streak",        "desc": "Studied 7 days in a row", "icon": "🌟"},
    "streak_30":        {"label": "👑 30-Day Streak",       "desc": "Studied 30 days in a row", "icon": "👑"},
    "flashcard_10":     {"label": "🧠 Card Crusher",        "desc": "Reviewed 10 flashcards", "icon": "🧠"},
    "level_5":          {"label": "🚀 Rising Star",         "desc": "Reached Level 5", "icon": "🚀"},
    "level_10":         {"label": "🌌 Study Legend",        "desc": "Reached Level 10", "icon": "🌌"},
}

# TRANSLATIONS
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
    "🏠 Home": "🏠 මුල් පිටුව",
    "⚙️ Settings": "⚙️ සැකසුම්",
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
    "🏠 Dashboard": "🏠 උපකරණ පුවරුව",
    "Welcome back!": "ආපසු සාදරයෙන් පිළිගනිමු!",
    "Pick up where you left off": "ඔබ නතර කළ තැනින් ආරම්භ කරන්න",
    "Quick Actions": "ඉක්මන් ක්‍රියා",
    "Study Progress": "අධ්‍යයන ප්‍රගතිය",
    "Recent Activity": "මෑත ක්‍රියාකාරකම්",
}

def t(text):
    """Translate a UI string to the active profile's language."""
    lang = st.session_state.get("app_language", "en")
    if lang == "si":
        return TRANSLATIONS.get(text, text)
    return text

DEFAULT_PROFILE = {
    "user_name": "",
    "email": "",
    "password_hash": None,
    "auth_provider": "password",
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
    "last_feature_used": None,
    "last_visit_date": None,
    "custom_theme": {
        "enabled": False,
        "primary_color": "#7C8CFF",
        "secondary_color": "#C77DFF",
        "background_start": "#05070D",
        "background_mid": "#11141F",
        "text_color": "#F5F7FA",
        "card_color": "#1A1A2E",
        "accent_color": "#1A1A2E",
        "border_color": "#2A2A3E",
        "background_image": None,
        "glass_blur": 22,
        "glass_opacity": 0.06,
        "glass_saturation": 180,
        "glow_intensity": 60,
        "solid_bg": "#05070D",
        "grad_start": "#05070D",
        "grad_end": "#1a1a3e",
        "grad_angle": 135,
        "bg_blur": 0,
        "particle_density": "Medium",
        "particle_color": "#7C8CFF",
        "particle_speed": 3,
    },
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
_db_lock = threading.Lock()

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_db():
    conn = get_db_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                username TEXT PRIMARY KEY,
                email TEXT,
                data TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.commit()
    finally:
        conn.close()

def _migrate_legacy_json_if_needed():
    if not os.path.exists(LEGACY_JSON_FILE):
        return
    conn = get_db_connection()
    try:
        count = conn.execute("SELECT COUNT(*) FROM profiles").fetchone()[0]
        if count > 0:
            return
        with open(LEGACY_JSON_FILE, "r", encoding="utf-8") as f:
            legacy = json.load(f)
        users = legacy.get("users", {})
        if not users:
            return
        now = datetime.now(timezone.utc).isoformat()
        with _db_lock:
            for username, profile in users.items():
                conn.execute(
                    "INSERT OR IGNORE INTO profiles (username, email, data, updated_at) VALUES (?, ?, ?, ?)",
                    (username, profile.get("email", ""), json.dumps(profile, ensure_ascii=False), now),
                )
            conn.commit()
    except Exception:
        pass
    finally:
        conn.close()

def load_all_data():
    init_db()
    _migrate_legacy_json_if_needed()
    conn = get_db_connection()
    try:
        rows = conn.execute("SELECT username, data FROM profiles").fetchall()
    finally:
        conn.close()
    users = {}
    for username, data_json in rows:
        try:
            users[username] = json.loads(data_json)
        except Exception:
            continue
    return {"users": users}

def save_profile(key, profile):
    conn = get_db_connection()
    try:
        with _db_lock:
            conn.execute(
                "INSERT INTO profiles (username, email, data, updated_at) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(username) DO UPDATE SET email=excluded.email, data=excluded.data, updated_at=excluded.updated_at",
                (key, profile.get("email", ""), json.dumps(profile, ensure_ascii=False), datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()
    finally:
        conn.close()

def new_profile(name, grade, age, gender):
    profile = json.loads(json.dumps(DEFAULT_PROFILE))
    profile["user_name"] = name
    profile["user_grade"] = grade
    profile["user_age"] = age
    profile["user_gender"] = gender
    return profile

def migrate_theme_colors(profile):
    """Migrate old rgba theme colors to hex values"""
    if "custom_theme" in profile:
        theme = profile["custom_theme"]
        
        # Fix rgba values in theme
        rgba_to_hex = {
            "rgba(255, 255, 255, 0.06)": "#1A1A2E",
            "rgba(255, 255, 255, 0.14)": "#2A2A3E",
            "rgba(124, 140, 255, 0.18)": "#1A1A2E",
            "rgba(255, 255, 255, 0.08)": "#1A1A2E",
        }
        
        for key in ["card_color", "accent_color", "border_color"]:
            if key in theme and theme[key] in rgba_to_hex:
                theme[key] = rgba_to_hex[theme[key]]
        
        # Ensure all required keys exist
        default_theme = DEFAULT_PROFILE["custom_theme"]
        for key, value in default_theme.items():
            if key not in theme:
                theme[key] = value
    
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
    profile.setdefault("email", "")
    profile.setdefault("password_hash", None)
    profile.setdefault("auth_provider", "password")
    profile.setdefault("last_feature_used", None)
    profile.setdefault("last_visit_date", None)
    
    # Migrate theme colors
    profile = migrate_theme_colors(profile)
    
    return profile

# ACCOUNT SECURITY
PBKDF2_ITERATIONS = 260_000

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"{salt.hex()}${dk.hex()}"

def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, hash_hex = stored.split("$")
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False

def find_account(identifier: str):
    identifier = (identifier or "").strip().lower()
    if not identifier:
        return None, None
    users = st.session_state.all_data.get("users", {})
    for key, profile in users.items():
        if key.strip().lower() == identifier:
            return key, profile
        if profile.get("email", "").strip().lower() == identifier:
            return key, profile
    return None, None

def is_google_auth_configured() -> bool:
    try:
        return bool(st.secrets.get("auth", {}).get("client_id"))
    except Exception:
        return False

def login_rate_limited(identifier: str) -> bool:
    attempts = st.session_state.setdefault("login_attempts", {})
    return attempts.get(identifier, 0) >= 5

def record_failed_login(identifier: str):
    attempts = st.session_state.setdefault("login_attempts", {})
    attempts[identifier] = attempts.get(identifier, 0) + 1

def clear_failed_logins(identifier: str):
    st.session_state.setdefault("login_attempts", {}).pop(identifier, None)

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
    """Enhanced popups with confetti/celebration effects"""
    for lvl in st.session_state.get("level_up_queue", []):
        st.markdown(f"""
        <div class="level-up-celebration">
            <div class="confetti-container">
                <div class="confetti-piece"></div>
                <div class="confetti-piece"></div>
                <div class="confetti-piece"></div>
                <div class="confetti-piece"></div>
                <div class="confetti-piece"></div>
                <div class="confetti-piece"></div>
                <div class="confetti-piece"></div>
                <div class="confetti-piece"></div>
                <div class="confetti-piece"></div>
                <div class="confetti-piece"></div>
            </div>
            <div class="level-up-content">
                🚀 Level {lvl} Unlocked!
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.balloons()
        st.toast(f"🎉 Level Up! You're now Level {lvl}!", icon="🚀")
    st.session_state["level_up_queue"] = []
    
    for badge_id in st.session_state.get("new_badges_queue", []):
        badge = BADGES.get(badge_id)
        if badge:
            st.markdown(f"""
            <div class="badge-unlock">
                <div class="badge-unlock-icon">{badge['icon']}</div>
                <div class="badge-unlock-content">
                    <strong>Badge Unlocked!</strong>
                    <br>{badge['label']}
                    <br><small>{badge['desc']}</small>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.toast(f"🏅 Badge unlocked: {badge['label']}", icon="🏅")
    st.session_state["new_badges_queue"] = []

# SPACED REPETITION ENGINE
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

def current_profile():
    return st.session_state.all_data["users"][st.session_state.active_user]

def save_current():
    key = st.session_state.active_user
    users = st.session_state.all_data.get("users", {})
    if key and key in users:
        save_profile(key, users[key])

# AI SETUP
def get_api_key():
    try:
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    return None

@st.cache_resource(show_spinner=False)
def get_client():
    api_key = get_api_key()
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

def get_ai_response(prompt, image=None):
    client = get_client()
    if client is None:
        return "⚠️ **No Gemini API key found.** Please add your API key."
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
        err_text = str(e)
        if "401" in err_text or "UNAUTHENTICATED" in err_text:
            return f"⚠️ **API Key error:** {err_text}"
        return f"ERROR: {err_text}"

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

# THEME SYSTEM — "Liquid Glass" Enhanced
GLASS_TOKENS = {
    "bg": "#05070D",
    "bg-elevated": "#11141F",
    "text": "#F5F7FA",
    "muted": "#A3ADC2",
    "muted-2": "#7C8699",
    "sidebar-bg": "rgba(10, 13, 22, 0.55)",
    "border": "rgba(255, 255, 255, 0.14)",
    "card-bg": "rgba(255, 255, 255, 0.06)",
    "dock-bg": "rgba(20, 24, 38, 0.55)",
    "track-bg": "rgba(255, 255, 255, 0.10)",
    "accent-1": "#7C8CFF",
    "accent-2": "#C77DFF",
    "accent-soft": "rgba(124, 140, 255, 0.18)",
    "shadow": "0 8px 32px rgba(0, 0, 0, 0.45)",
}

def apply_theme(theme=None):
    t = GLASS_TOKENS
    root_vars = "".join(f"--{k}: {v};" for k, v in t.items())

    st.markdown(f"""
    <style>
    
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    :root {{ {root_vars} }}

    [data-testid="stMain"] p, 
    [data-testid="stMain"] h1, 
    [data-testid="stMain"] h2, 
    [data-testid="stMain"] h3, 
    [data-testid="stMain"] h4, 
    [data-testid="stMain"] label, 
    [data-testid="stMain"] input, 
    [data-testid="stMain"] button,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label {{
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }}

    [data-testid="stHeader"] *, 
    [data-testid="stAppHeader"] *,
    header * {{
        font-family: 'Material Symbols Rounded', 'Material Icons', sans-serif !important;
    }}

    .stApp {{
        background:
            radial-gradient(1200px 800px at 10% 0%, rgba(124, 140, 255, 0.16), transparent 55%),
            radial-gradient(1000px 800px at 90% 15%, rgba(199, 125, 255, 0.13), transparent 55%),
            radial-gradient(1200px 900px at 20% 100%, rgba(56, 189, 248, 0.10), transparent 55%),
            var(--bg);
        color: var(--text);
    }}
    [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{ background: transparent; }}
    section[data-testid="stSidebar"] {{
        background: var(--sidebar-bg);
        backdrop-filter: blur(20px) saturate(150%);
        -webkit-backdrop-filter: blur(20px) saturate(150%);
        border-right: 1px solid var(--border);
    }}

    [data-testid="stMainBlockContainer"] {{
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

    /* Enhanced Glass Effects */
    .profile-card, .streak-pill, .pomo-ring-inner, .flash-face,
    div[data-testid="stMetric"], div[data-testid="stExpander"],
    div[data-testid="stForm"], .home-card, .quick-action-card {{
        background: var(--card-bg) !important;
        backdrop-filter: blur(22px) saturate(180%);
        -webkit-backdrop-filter: blur(22px) saturate(180%);
        border: 1px solid var(--border) !important;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.18), var(--shadow);
        border-radius: 18px;
        padding: 20px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    .home-card:hover, .quick-action-card:hover {{
        transform: translateY(-4px);
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.25), 0 12px 40px rgba(0, 0, 0, 0.5);
    }}

    /* Inputs */
    div[data-testid="stTextInput"] input,
    div[data-testid="stNumberInput"] input,
    div[data-testid="stTextArea"] textarea,
    div[data-testid="stDateInput"] input,
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
    div[data-testid="stMultiSelect"] div[data-baseweb="select"] > div,
    section[data-testid="stFileUploaderDropzone"],
    section[data-testid="stFileUploadDropzone"] {{
        background: var(--card-bg) !important;
        backdrop-filter: blur(18px) saturate(180%) !important;
        -webkit-backdrop-filter: blur(18px) saturate(180%) !important;
        border: 1px solid var(--border) !important;
        border-radius: 14px !important;
        color: var(--text) !important;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.15) !important;
    }}

    /* Floating dock navigation with tooltips */
    div[class*="st-key-nav_dock"] div[data-testid="stRadio"] {{
        position: fixed !important;
        right: 20px !important;
        top: 50% !important;
        transform: translateY(-50%) !important;
        left: auto !important;
        z-index: 999999 !important;
        background: var(--dock-bg) !important;
        backdrop-filter: blur(24px) saturate(180%) !important;
        -webkit-backdrop-filter: blur(24px) saturate(180%) !important;
        border: 1px solid var(--border) !important;
        padding: 10px 8px !important;
        border-radius: 22px !important;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2), -5px 10px 30px rgba(0, 0, 0, 0.4);
        max-height: 90vh !important;
        width: auto !important;
        transition: background 0.3s ease, border-color 0.3s ease;
    }}
    div[class*="st-key-nav_dock"] div[data-testid="stRadio"] > div {{
        display: flex !important;
        flex-direction: column !important;
        gap: 6px !important;
    }}
    div[class*="st-key-nav_dock"] div[data-testid="stRadio"] label {{
        display: flex !important;
        align-items: center !important;
        gap: 0 !important;
        background: transparent !important;
        padding: 8px 12px !important;
        border-radius: 14px !important;
        color: var(--muted) !important;
        cursor: pointer !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        white-space: nowrap !important;
        position: relative !important;
        margin: 0 !important;
    }}
    div[class*="st-key-nav_dock"] div[data-testid="stRadio"] label:hover {{
        color: var(--text) !important;
        background: var(--accent-soft) !important;
    }}
    div[class*="st-key-nav_dock"] div[data-testid="stRadio"] label .st-emotion-cache-1f5stn {{
        display: none !important;
    }}
    div[class*="st-key-nav_dock"] div[data-testid="stRadio"] label .st-emotion-cache-1p1m4ay {{
        display: none !important;
    }}
    div[class*="st-key-nav_dock"] div[data-testid="stRadio"] label .st-emotion-cache-1q1hqs3 {{
        display: none !important;
    }}
    div[class*="st-key-nav_dock"] div[data-testid="stRadio"] label .st-emotion-cache-1v0mbdj {{
        display: none !important;
    }}

    div[class*="st-key-nav_dock"] div[data-testid="stRadio"] label .st-emotion-cache-1l284xh {{
        display: none !important;
    }}

    div[class*="st-key-nav_dock"] div[data-testid="stRadio"] label .st-emotion-cache-1vzeuhh {{
        margin: 0 !important;
        padding: 0 !important;
    }}

    div[class*="st-key-nav_dock"] div[data-testid="stRadio"] label[data-baseweb="radio"] {{
        background: transparent !important;
    }}
    div[class*="st-key-nav_dock"] div[data-testid="stRadio"] label[data-baseweb="radio"][aria-checked="true"] {{
        background: linear-gradient(135deg, var(--accent-1) 0%, var(--accent-2) 100%) !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 16px rgba(124, 140, 255, 0.4) !important;
    }}

    div[class*="st-key-nav_dock"] div[data-testid="stRadio"] label[data-baseweb="radio"]:hover::after {{
        content: attr(data-tooltip);
        position: absolute;
        right: calc(100% + 14px);
        top: 50%;
        transform: translateY(-50%);
        background: var(--bg-elevated);
        color: var(--text);
        padding: 4px 12px;
        border-radius: 8px;
        font-size: 0.75rem;
        white-space: nowrap;
        border: 1px solid var(--border);
        box-shadow: var(--shadow);
        font-weight: 500;
        letter-spacing: 0.3px;
        pointer-events: none;
        z-index: 1000000;
    }}
    div[class*="st-key-nav_dock"] div[data-testid="stRadio"] label[data-baseweb="radio"]:hover::before {{
        content: '';
        position: absolute;
        right: calc(100% + 8px);
        top: 50%;
        transform: translateY(-50%);
        border: 6px solid transparent;
        border-left-color: var(--bg-elevated);
        z-index: 1000000;
    }}

    @media (max-width: 900px) {{
        div[class*="st-key-nav_dock"] div[data-testid="stRadio"] {{
            top: auto !important;
            bottom: 0 !important;
            right: 0 !important;
            left: 0 !important;
            transform: none !important;
            width: 100% !important;
            max-height: none !important;
            border-radius: 22px 22px 0 0 !important;
            border-bottom: none !important;
            padding: 8px 4px !important;
        }}
        div[class*="st-key-nav_dock"] div[data-testid="stRadio"] > div {{
            flex-direction: row !important;
            overflow-x: auto !important;
            justify-content: flex-start !important;
            gap: 2px !important;
            padding: 0 4px;
        }}
        div[class*="st-key-nav_dock"] div[data-testid="stRadio"] label[data-baseweb="radio"] {{
            font-size: 0.75rem !important;
            padding: 6px 10px !important;
            flex-shrink: 0;
        }}
        div[class*="st-key-nav_dock"] div[data-testid="stRadio"] label[data-baseweb="radio"]:hover::after {{
            display: none !important;
        }}
        div[class*="st-key-nav_dock"] div[data-testid="stRadio"] label[data-baseweb="radio"]:hover::before {{
            display: none !important;
        }}
        [data-testid="stMainBlockContainer"] {{
            padding-right: 1.2rem !important;
            padding-left: 1.2rem !important;
            padding-bottom: 96px !important;
        }}
    }}

    .stButton > button {{
        border-radius: 14px !important;
        border: 1px solid rgba(255, 255, 255, 0.18) !important;
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.14), rgba(255, 255, 255, 0.03)) !important;
        backdrop-filter: blur(16px) saturate(180%) !important;
        -webkit-backdrop-filter: blur(16px) saturate(180%) !important;
        color: var(--text) !important;
        font-weight: 600 !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.25), var(--shadow) !important;
    }}
    .stButton > button:hover {{
        transform: translateY(-2px) scale(1.02) !important;
        background: linear-gradient(135deg, var(--accent-1) 0%, var(--accent-2) 100%) !important;
        color: #FFFFFF !important;
        border-color: transparent !important;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.35), 0 10px 30px rgba(124, 140, 255, 0.45) !important;
    }}

    /* Flashcard 3D Flip */
    .flashcard-container {{
        perspective: 1000px;
        margin: 20px 0;
    }}
    .flashcard {{
        position: relative;
        width: 100%;
        min-height: 200px;
        transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        transform-style: preserve-3d;
        cursor: pointer;
    }}
    .flashcard.flipped {{
        transform: rotateY(180deg);
    }}
    .flashcard-face {{
        position: absolute;
        width: 100%;
        min-height: 200px;
        backface-visibility: hidden;
        border-radius: 18px;
        padding: 30px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.25rem;
        text-align: center;
        background: var(--card-bg);
        backdrop-filter: blur(22px) saturate(180%);
        border: 1px solid var(--border);
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.18), var(--shadow);
    }}
    .flashcard-back {{
        transform: rotateY(180deg);
        border-color: var(--accent-2);
    }}
    
    /* Quiz answer feedback animations */
    .quiz-correct {{
        animation: quiz-pop-green 0.5s ease;
        border-left: 4px solid #4CAF50 !important;
        padding-left: 16px !important;
        background: rgba(76, 175, 80, 0.1) !important;
    }}
    .quiz-incorrect {{
        animation: quiz-pop-red 0.5s ease;
        border-left: 4px solid #f44336 !important;
        padding-left: 16px !important;
        background: rgba(244, 67, 54, 0.1) !important;
    }}
    @keyframes quiz-pop-green {{
        0% {{ transform: scale(1); background: rgba(76, 175, 80, 0); }}
        50% {{ transform: scale(1.02); background: rgba(76, 175, 80, 0.2); }}
        100% {{ transform: scale(1); background: rgba(76, 175, 80, 0.1); }}
    }}
    @keyframes quiz-pop-red {{
        0% {{ transform: scale(1); background: rgba(244, 67, 54, 0); }}
        50% {{ transform: scale(1.02); background: rgba(244, 67, 54, 0.2); }}
        100% {{ transform: scale(1); background: rgba(244, 67, 54, 0.1); }}
    }}
    
    /* Level-up celebration */
    .level-up-celebration {{
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: var(--bg-elevated);
        border: 2px solid var(--accent-1);
        border-radius: 24px;
        padding: 40px 60px;
        z-index: 9999;
        animation: level-up-pop 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        text-align: center;
        backdrop-filter: blur(30px);
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.8);
    }}
    .level-up-content {{
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, var(--accent-1), var(--accent-2));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}
    @keyframes level-up-pop {{
        0% {{ transform: translate(-50%, -50%) scale(0.5); opacity: 0; }}
        100% {{ transform: translate(-50%, -50%) scale(1); opacity: 1; }}
    }}
    
    /* Badge unlock */
    .badge-unlock {{
        display: flex;
        align-items: center;
        gap: 16px;
        background: var(--card-bg);
        border: 1px solid var(--accent-2);
        border-radius: 16px;
        padding: 16px 24px;
        margin: 12px 0;
        animation: badge-unlock-slide 0.5s cubic-bezier(0.4, 0, 0.2, 1);
        backdrop-filter: blur(20px);
        box-shadow: 0 8px 32px rgba(199, 125, 255, 0.2);
    }}
    .badge-unlock-icon {{
        font-size: 3rem;
    }}
    .badge-unlock-content {{
        color: var(--text);
    }}
    @keyframes badge-unlock-slide {{
        0% {{ transform: translateX(-50px); opacity: 0; }}
        100% {{ transform: translateX(0); opacity: 1; }}
    }}
    
    /* Confetti */
    .confetti-container {{
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        overflow: hidden;
        pointer-events: none;
    }}
    .confetti-piece {{
        position: absolute;
        width: 10px;
        height: 10px;
        animation: confetti-fall 3s linear infinite;
    }}
    .confetti-piece:nth-child(1) {{ background: #ff6b6b; left: 10%; animation-delay: 0s; }}
    .confetti-piece:nth-child(2) {{ background: #ffd93d; left: 20%; animation-delay: 0.2s; }}
    .confetti-piece:nth-child(3) {{ background: #6bcb77; left: 30%; animation-delay: 0.4s; }}
    .confetti-piece:nth-child(4) {{ background: #4d96ff; left: 40%; animation-delay: 0.6s; }}
    .confetti-piece:nth-child(5) {{ background: #ff6b6b; left: 50%; animation-delay: 0.8s; }}
    .confetti-piece:nth-child(6) {{ background: #ffd93d; left: 60%; animation-delay: 1s; }}
    .confetti-piece:nth-child(7) {{ background: #6bcb77; left: 70%; animation-delay: 1.2s; }}
    .confetti-piece:nth-child(8) {{ background: #4d96ff; left: 80%; animation-delay: 1.4s; }}
    .confetti-piece:nth-child(9) {{ background: #c77dff; left: 90%; animation-delay: 1.6s; }}
    .confetti-piece:nth-child(10) {{ background: #ff6b6b; left: 15%; animation-delay: 1.8s; }}
    @keyframes confetti-fall {{
        0% {{ transform: translateY(-100px) rotate(0deg); opacity: 1; }}
        100% {{ transform: translateY(300px) rotate(720deg); opacity: 0; }}
    }}
    
    /* Shimmer loading skeleton */
    .shimmer {{
        background: linear-gradient(90deg, var(--card-bg) 25%, var(--track-bg) 50%, var(--card-bg) 75%);
        background-size: 200% 100%;
        animation: shimmer 1.5s infinite;
        border-radius: 12px;
        min-height: 100px;
        margin: 10px 0;
    }}
    @keyframes shimmer {{
        0% {{ background-position: 200% 0; }}
        100% {{ background-position: -200% 0; }}
    }}
    
    /* Home dashboard cards */
    .home-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
        margin: 20px 0;
    }}
    .quick-action-card {{
        text-align: center;
        padding: 24px 16px;
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    .quick-action-card:hover {{
        transform: translateY(-4px) scale(1.02);
        border-color: var(--accent-1);
    }}
    .quick-action-icon {{
        font-size: 2.5rem;
        margin-bottom: 8px;
    }}
    .quick-action-label {{
        font-size: 0.9rem;
        font-weight: 500;
        color: var(--text);
    }}
    
    /* Empty state illustrations */
    .empty-state {{
        text-align: center;
        padding: 40px 20px;
        color: var(--muted);
    }}
    .empty-state-icon {{
        font-size: 4rem;
        margin-bottom: 16px;
        opacity: 0.6;
    }}
    .empty-state-text {{
        font-size: 1.1rem;
        font-weight: 500;
    }}
    .empty-state-hint {{
        font-size: 0.9rem;
        color: var(--muted-2);
        margin-top: 8px;
    }}
    
    /* Profile card enhancements */
    .profile-card {{
        border-radius: 22px;
        padding: 18px;
        margin-bottom: 12px;
        position: relative;
        overflow: hidden;
    }}
    .profile-card::after {{
        content: "";
        position: absolute;
        top: -60%; left: -20%;
        width: 60%; height: 140%;
        background: linear-gradient(120deg, rgba(255,255,255,0.10), transparent 60%);
        pointer-events: none;
    }}
    .profile-header {{ display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }}
    .avatar-box {{
        font-size: 1.8rem;
        background: var(--accent-soft);
        border: 1px solid rgba(124, 140, 255, 0.35);
        border-radius: 16px;
        padding: 6px 10px;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2);
    }}
    .profile-title {{ margin: 0; font-size: 1.1rem; font-weight: 700; color: var(--text); }}
    .profile-subtitle {{ margin: 0; font-size: 0.78rem; color: var(--muted); }}
    .profile-meta {{ display: flex; justify-content: space-between; font-size: 0.78rem; color: var(--muted-2); margin-bottom: 10px; }}
    .level-badge {{ background: linear-gradient(135deg, var(--accent-1), var(--accent-2)); color: #FFF; padding: 2px 8px; border-radius: 10px; font-weight: 600; }}
    .xp-section {{ margin-bottom: 12px; }}
    .xp-labels {{ display: flex; justify-content: space-between; font-size: 0.73rem; color: var(--muted); margin-bottom: 5px; }}
    .xp-track {{ background: var(--track-bg); border-radius: 10px; height: 7px; width: 100%; overflow: hidden; }}
    .xp-bar {{ background: linear-gradient(90deg, var(--accent-1), var(--accent-2)); height: 100%; border-radius: 10px; transition: width 0.5s ease; box-shadow: 0 0 10px rgba(124, 140, 255, 0.6); }}
    .streak-pill {{ display: flex; justify-content: space-between; padding: 6px 12px; border-radius: 14px; font-size: 0.8rem; }}
    .badges-grid {{ display: flex; flex-wrap: wrap; gap: 6px; }}
    .badge-tag, .badge-chip {{
        background: var(--accent-soft);
        border: 1px solid rgba(124, 140, 255, 0.3);
        color: var(--text);
        font-size: 0.72rem;
        padding: 4px 8px;
        border-radius: 10px;
        display: inline-block;
        margin: 2px;
        backdrop-filter: blur(10px);
    }}

    /* Audio Player */
    .audio-player-container {{
        background: var(--card-bg);
        border-radius: 18px;
        padding: 24px;
        border: 1px solid var(--border);
        margin: 16px 0;
    }}
    .audio-controls {{
        display: flex;
        align-items: center;
        gap: 16px;
        flex-wrap: wrap;
    }}
    .audio-controls button {{
        padding: 10px 20px;
        border-radius: 12px;
        border: 1px solid var(--border);
        background: var(--accent-soft);
        color: var(--text);
        cursor: pointer;
        font-weight: 600;
        transition: all 0.2s ease;
    }}
    .audio-controls button:hover {{
        transform: translateY(-2px);
        background: var(--accent-1);
        color: white;
    }}
    .audio-controls button:disabled {{
        opacity: 0.5;
        cursor: not-allowed;
        transform: none;
    }}
    .status-indicator {{
        padding: 8px 16px;
        border-radius: 8px;
        background: var(--track-bg);
        color: var(--muted);
        font-size: 0.9rem;
    }}

    /* Theme Builder Preview */
    .theme-preview {{
        border-radius: 18px;
        padding: 30px;
        border: 1px solid var(--border);
        margin: 10px 0;
    }}
    .theme-preview .preview-card {{
        background: var(--card-bg);
        backdrop-filter: blur(20px);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 20px;
        margin: 10px 0;
    }}
    .theme-preview .preview-accent {{
        border-radius: 12px;
        padding: 12px 24px;
        color: white;
        font-weight: 600;
        display: inline-block;
        margin: 5px;
    }}
    </style>
    """, unsafe_allow_html=True)

# PARENT / TEACHER READ-ONLY VIEW
if st.query_params.get("view") == "parent":
    apply_theme()
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

# LOGIN / PROFILE SELECTION SCREEN
if st.session_state.active_user is None and is_google_auth_configured():
    try:
        if st.user.is_logged_in:
            google_email = (st.user.email or "").strip().lower()
            key, profile = find_account(google_email)
            if profile is not None:
                st.session_state.active_user = key
                st.session_state.auth_method = "google"
                st.rerun()
            else:
                st.session_state.google_pending_email = google_email
                st.session_state.google_pending_name = st.user.name or google_email.split("@")[0]
    except Exception:
        pass

if st.session_state.active_user is None and st.session_state.get("google_pending_email"):
    apply_theme()
    st.markdown("<h2 style='text-align:center;'>👋 Almost there — tell us about yourself</h2>", unsafe_allow_html=True)
    st.caption(f"Signed in with Google as {st.session_state.google_pending_email}")

    col1, col2 = st.columns(2)
    with col1:
        g_name = st.text_input("Your Name:", value=st.session_state.google_pending_name, key="g_onboard_name")
        g_grade = st.selectbox("Grade:", [f"Grade {i}" for i in range(1, 14)], key="g_onboard_grade")
    with col2:
        g_age = st.number_input("Age:", min_value=5, max_value=18, value=13, key="g_onboard_age")
        g_gender = st.selectbox("Gender:", ["Male", "Female", "Prefer not to say"], key="g_onboard_gender")

    if st.button("Create your Profile 🚀", use_container_width=True, key="g_onboard_submit"):
        clean_name = g_name.strip()
        if not clean_name:
            st.error("Please enter your name.")
        else:
            email = st.session_state.google_pending_email
            profile = new_profile(clean_name, g_grade, g_age, g_gender)
            profile["email"] = email
            profile["auth_provider"] = "google"
            st.session_state.all_data["users"][email] = profile
            save_profile(email, profile)
            st.session_state.active_user = email
            st.session_state.auth_method = "google"
            del st.session_state["google_pending_email"]
            del st.session_state["google_pending_name"]
            st.rerun()
    st.stop()

if st.session_state.active_user is None and not st.session_state.get("google_pending_email"):
    apply_theme()
    st.markdown("<h2 style='text-align:center;'>👋 Welcome to Smart Study Organizer Pro!</h2>", unsafe_allow_html=True)

    if is_google_auth_configured():
        gcol1, gcol2, gcol3 = st.columns([1, 2, 1])
        with gcol2:
            if st.button("🔵 Continue with Google", use_container_width=True):
                st.login()
        st.markdown("<p style='text-align:center; color:var(--muted);'>— or use a password —</p>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🙋 Log In", "✨ Sign Up"])

    with tab1:
        login_id = st.text_input("Username or email:", key="login_id")
        login_pw = st.text_input("Password:", type="password", key="login_pw")

        if st.button("Log in ➡️", use_container_width=True):
            identifier = login_id.strip().lower()
            if login_rate_limited(identifier):
                st.error("Too many failed attempts. Please wait and try again later.")
            else:
                key, profile = find_account(login_id)
                if profile is None:
                    st.error("No account found with that username or email.")
                    record_failed_login(identifier)
                elif profile.get("password_hash") is None:
                    st.warning(
                        "⚠️ This account hasn't been secured with a password yet "
                        "(it predates the login system). Set one now to claim it — "
                        "do this immediately if you plan to make the app public, since "
                        "anyone could otherwise claim an unsecured account first."
                    )
                    new_pw = st.text_input("Set a password:", type="password", key="claim_pw")
                    confirm_pw = st.text_input("Confirm password:", type="password", key="claim_pw2")
                    if st.button("Secure this account", use_container_width=True, key="claim_btn"):
                        if len(new_pw) < 8:
                            st.error("Password must be at least 8 characters.")
                        elif new_pw != confirm_pw:
                            st.error("Passwords don't match.")
                        else:
                            profile["password_hash"] = hash_password(new_pw)
                            save_profile(key, profile)
                            st.session_state.active_user = key
                            st.session_state.auth_method = "password"
                            st.rerun()
                elif verify_password(login_pw, profile["password_hash"]):
                    clear_failed_logins(identifier)
                    st.session_state.active_user = key
                    st.session_state.auth_method = "password"
                    st.rerun()
                else:
                    st.error("Incorrect password.")
                    record_failed_login(identifier)

    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            name_input = st.text_input("Your Name:", key="signup_name")
            email_input = st.text_input("Email:", key="signup_email")
            grade_input = st.selectbox("Grade:", [f"Grade {i}" for i in range(1, 14)])
        with col2:
            age_input = st.number_input("Age:", min_value=5, max_value=18, value=13)
            gender_input = st.selectbox("Gender:", ["Male", "Female", "Prefer not to say"])
            pw_input = st.text_input("Password:", type="password", key="signup_pw")
            pw_confirm = st.text_input("Confirm password:", type="password", key="signup_pw2")

        if st.button("Create your Profile 🚀", use_container_width=True):
            clean_name = name_input.strip()
            clean_email = email_input.strip().lower()
            existing_key, existing_profile = find_account(clean_name)
            existing_by_email, _ = find_account(clean_email) if clean_email else (None, None)
            if not clean_name:
                st.error("Please enter your name.")
            elif not clean_email or "@" not in clean_email:
                st.error("Please enter a valid email address.")
            elif existing_profile is not None or existing_by_email is not None:
                st.error("That name or email is already registered. Try logging in instead.")
            elif len(pw_input) < 8:
                st.error("Password must be at least 8 characters.")
            elif pw_input != pw_confirm:
                st.error("Passwords don't match.")
            else:
                profile = new_profile(clean_name, grade_input, age_input, gender_input)
                profile["email"] = clean_email
                profile["password_hash"] = hash_password(pw_input)
                profile["auth_provider"] = "password"
                st.session_state.all_data["users"][clean_name] = profile
                save_profile(clean_name, profile)
                st.session_state.active_user = clean_name
                st.session_state.auth_method = "password"
                st.rerun()

    st.stop()

# PERSONALIZED CONTEXT
user_info = current_profile()
user_gender = user_info.get("user_gender", "Prefer not to say")
user_age = user_info.get("user_age", 13)
user_grade = user_info.get("user_grade", "Grade 8")

apply_theme()
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

# PER-FEATURE PROMPT BUILDERS
def _syllabus_notice(task_name):
    return (
        f"CRITICAL RULE: This request is for {task_name} ONLY — produce nothing else. Do not add a summary, quiz "
        f"questions, flashcards, a mindmap, or any other feature's output; only the {task_name} is wanted. "
        "This content MUST strictly align with the Sri Lankan local school syllabus for the user's grade — not "
        "above it, not below it. Use valid sources (e.g. edupub.gov.lk, dpeducation.lk, e-thaksalawa.moe.gov.lk). "
        "Do NOT introduce any concept, term, formula, or vocabulary that is not part of this grade's official "
        "syllabus, even if it is technically related or commonly taught in other countries or exam systems. If a "
        "topic is normally taught at a higher grade, simplify it down to what is appropriate for this grade rather "
        "than teaching the advanced version. Keep explanations beginner-friendly, clean, and engaging."
    )

def _who_line():
    return f"The user is {user_age} years old in {user_grade} in Sri Lanka."

def build_mindmap_prompt(content):
    return (
        f"{_who_line()} {_syllabus_notice('a mindmap')} {language_instruction} "
        "Based on the following content, generate ONLY a clear, logical, structured text-based mindmap. Format it "
        "using clean nested markdown bullet points, extremely intuitive for a beginner to study. "
        f"Content: {content}"
    )

def build_summarizer_prompt(notes_text):
    return (
        f"{_who_line()} {_syllabus_notice('a note summary')} {language_instruction} "
        f"Summarize these notes clearly in bullet points ONLY. Notes: {notes_text}. Explain it simply so a "
        "beginner can master it."
    )

def build_quiz_prompt(subject, difficulty, num_questions, content):
    return (
        f"{_who_line()} {_syllabus_notice('a multiple-choice quiz')} {language_instruction} "
        f"Subject: {subject}. Difficulty: {difficulty}. Based on the topic/image/document, generate ONLY exactly "
        f"{num_questions} multiple choice questions. Return ONLY a raw JSON array of exactly {num_questions} "
        "objects, each with keys: 'question', 'A', 'B', 'C', 'D', 'correct' (one of 'A'/'B'/'C'/'D'). No "
        f"explanation outside the JSON. Topic/Content: {content}"
    )

def build_math_prompt(math_query):
    return (
        f"{_who_line()} {_syllabus_notice('a step-by-step math solution')} {language_instruction} "
        f"Solve ONLY this one math problem step-by-step: {math_query}. Do NOT just give the final answer. Act "
        "like a friendly tutor teaching a beginner. Break down every step clearly."
    )

def build_flashcards_prompt(subject, content, count):
    if len(content) > 8000:
        content = content[:8000] + "... (truncated)"
    
    return (
        f"{_who_line()} {_syllabus_notice('flashcards')} {language_instruction} "
        f"Subject: {subject}. Based on the following content, create ONLY exactly {count} flashcards. "
        "Extract key concepts, definitions, and important facts from the content. "
        f"Return ONLY a raw JSON array of exactly {count} objects, each with keys 'front' (a short question or term) "
        "and 'back' (a concise, clear answer/definition). No explanation outside the JSON.\n\n"
        f"Content: {content}"
    )

def build_goal_tasks_prompt(goal):
    return (
        f"{_who_line()} {_syllabus_notice('a short study task list')} {language_instruction} "
        f"Break down ONLY this one study goal into 4 short actionable tasks. Provide only the tasks, without "
        f"numbers, one per line:\n{goal}"
    )

def build_daily_fact_prompt():
    return (
        f"{_who_line()} {language_instruction} "
        "Tell ONLY one amazing, mind-blowing, yet easy-to-understand science or computer technology fact — no "
        "summary, quiz, mindmap, or flashcards. Explain it in 3 clear bullet points."
    )

def build_audio_overview_prompt(content, style="overview"):
    """Build prompt for generating audio overview script"""
    style_instructions = {
        "overview": "Create a clear, engaging audio overview that summarizes the key points. Use a conversational tone, as if you're explaining it to a student. Include natural pauses and emphasis on important concepts.",
        "detailed": "Create a comprehensive audio lesson that explains the content in detail. Use a teaching tone with clear explanations, examples, and natural pacing for learning.",
        "study_guide": "Create a study guide audio that highlights the most important facts, definitions, and concepts. Use a focused, exam-prep tone with clear emphasis on key terms."
    }
    
    instruction = style_instructions.get(style, style_instructions["overview"])
    
    return (
        f"{_who_line()} {language_instruction} "
        f"Based on the following content, generate a script for a text-to-speech audio file. "
        f"{instruction} "
        "The script should be well-structured with clear sections, natural language, and appropriate pacing for spoken word. "
        "Use short, clear sentences. Add brief pauses with '...' where appropriate. "
        "Format the script with clear section breaks using '---' between major topics. "
        "Make it engaging and easy to listen to.\n\n"
        f"Content: {content}"
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
                st.markdown("""
                <div class="empty-state">
                    <div class="empty-state-icon">🏅</div>
                    <div class="empty-state-text">No badges yet!</div>
                    <div class="empty-state-hint">Complete activities to earn badges</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<div style='margin: 15px 0;'></div>", unsafe_allow_html=True)

        is_sinhala = profile.get("language", "en") == "si"
        lang_choice = st.toggle("🇱🇰 සිංහල (Sinhala)", value=is_sinhala, key="language_toggle")
        new_lang = "si" if lang_choice else "en"
        if new_lang != profile.get("language", "en"):
            profile["language"] = new_lang
            save_current()
            st.rerun()

        with st.expander("🔗 Parent / Teacher View"):
            st.caption("Share this with a parent or teacher for a read-only progress summary — no login, no editing.")
            encoded_key = urllib.parse.quote(st.session_state.active_user, safe="")
            st.code(f"?view=parent&user={encoded_key}", language=None)
            st.caption("Append this to the app's web address in your browser and share that full link.")

        if st.button(t("🔄 Switch Profile"), use_container_width=True):
            if st.session_state.get("auth_method") == "google":
                try:
                    st.logout()
                except Exception:
                    pass
            st.session_state.active_user = None
            st.session_state.auth_method = None
            st.rerun()

# MODULE FUNCTIONS

def show_home():
    """🏠 Home Dashboard - the new landing page with quick actions and overview"""
    profile = current_profile()
    gam = profile["gamification"]
    analytics = profile["analytics"]
    
    st.header("🏠 " + t("Dashboard"))
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"### {t('Welcome back!')} {profile['user_name']} 👋")
        st.caption(f"{t('Study Progress')} - {profile['user_grade']}")
        
        q1, q2, q3, q4 = st.columns(4)
        q1.metric("Level", gam["level"])
        q2.metric("🔥 Streak", gam.get("streak", 0))
        q3.metric("📚 Quizzes", analytics.get("quiz_taken", 0))
        q4.metric("⏱️ Pomodoro", analytics.get("pomodoro_sessions", 0))
    
    with col2:
        lvl, into_level, needed = xp_progress(gam["xp"])
        pct = int((into_level / needed) * 100)
        st.markdown(f"""
        <div style="background: var(--card-bg); padding: 16px; border-radius: 14px; border: 1px solid var(--border);">
            <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: var(--muted);">
                <span>XP Progress</span>
                <span>{into_level} / {needed}</span>
            </div>
            <div style="background: var(--track-bg); border-radius: 10px; height: 8px; margin-top: 4px; overflow: hidden;">
                <div style="background: linear-gradient(90deg, var(--accent-1), var(--accent-2)); height: 100%; width: {pct}%; border-radius: 10px;"></div>
            </div>
            <div style="margin-top: 8px; font-size: 0.7rem; color: var(--muted-2);">
                {len(gam.get('badges', []))} badges earned
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("### " + t("Quick Actions"))
    action_cols = st.columns(4)
    
    quick_actions = [
        ("📝", "Summarizer", "AI Note Summarizer"),
        ("🗺️", "Mindmap", "AI Mindmap Generator"),
        ("❓", "Quiz", "MCQ Quiz"),
        ("🧠", "Math", "Math Solver"),
    ]
    
    for col, (icon, label, feature) in zip(action_cols, quick_actions):
        with col:
            if st.button(f"{icon} {label}", use_container_width=True):
                st.session_state["nav_choice"] = icon
                st.rerun()
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### " + t("Pick up where you left off"))
        last_feature = profile.get("last_feature_used", "💡")
        feature_names = {
            "💡": "Daily Facts",
            "🗺️": "Mindmap",
            "📝": "Summarizer",
            "❓": "MCQ Quiz",
            "🧠": "Math Solver",
            "🎴": "Flashcards",
            "⏱️": "Pomodoro",
            "✍️": "Scribble Pad",
            "🎧": "Audio Overview",
            "📊": "Analytics",
            "⚙️": "Settings"
        }
        st.info(f"🔁 Continue with **{feature_names.get(last_feature, 'Daily Facts')}**")
        if st.button("↩️ Resume", use_container_width=True):
            st.session_state["nav_choice"] = last_feature
            st.rerun()
    
    with col2:
        st.markdown("### " + t("Recent Activity"))
        quiz_hist = profile.get("quiz_history", [])
        pom_hist = profile.get("pomodoro_history", [])
        
        if quiz_hist or pom_hist:
            recent_items = []
            for q in quiz_hist[-3:]:
                recent_items.append(f"📚 Quiz: {q.get('score', 0)}/{q.get('total', 0)} ({q.get('date', '')})")
            for p in pom_hist[-3:]:
                recent_items.append(f"⏱️ Focus: {p.get('minutes', 0)}min ({p.get('date', '')})")
            
            for item in recent_items[-3:]:
                st.text(item)
        else:
            st.caption("No recent activity yet. Start studying to see your progress here!")

def show_daily_facts():
    st.header(t("💡 Daily Tech & Science Facts"))
    st.caption(t("Get interesting Tech/Science facts here"))
    today_str = str(date.today())
    need_new = ("daily_fact" not in st.session_state or st.session_state.get("daily_fact_date") != today_str)

    if st.button("Get a new Fact 🧠") or need_new:
        with st.spinner("Your fact is being retrieved by AI..."):
            prompt = build_daily_fact_prompt()
            st.session_state.daily_fact = get_ai_response(prompt)
            st.session_state.daily_fact_date = today_str

    st.info(st.session_state.daily_fact)
    
    profile = current_profile()
    profile["last_feature_used"] = "💡"
    save_current()

def show_mindmap():
    st.header(t("🗺️ AI Mindmap Generator"))
    st.caption(t("Turn your notes or PDFs into a structured, easy-to-understand mindmap."))
    
    mm_file = st.file_uploader("Upload Notes (PDF, PNG, JPG):", type=["pdf", "png", "jpg", "jpeg"])
    mm_text = st.text_area("Or type/paste the main topic or notes here:", height=100)

    if st.button("Generate Mindmap 🧠"):
        if mm_file or mm_text:
            with st.spinner("Structuring your mindmap..."):
                st.markdown('<div class="shimmer" style="height:200px;"></div>', unsafe_allow_html=True)
                
                extracted_content = mm_text
                img = None
                
                if mm_file:
                    if mm_file.name.lower().endswith(".pdf"):
                        extracted_content += "\n" + extract_text_from_pdf(mm_file)
                    else:
                        img = Image.open(mm_file)

                prompt = build_mindmap_prompt(extracted_content)
                
                mm_output = get_ai_response(prompt, image=img)
                st.success("Your Mindmap is Ready:")
                st.markdown(mm_output)
                
                profile = current_profile()
                add_xp(profile, XP_REWARDS["mindmap_created"], "mindmap_created")
                profile["last_feature_used"] = "🗺️"
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
                st.markdown('<div class="shimmer" style="height:150px;"></div>', unsafe_allow_html=True)
                
                combined_text = user_note + "\n" + pdf_text
                prompt = build_summarizer_prompt(combined_text)
                output = get_ai_response(prompt, image=img)
                st.success("Here is the Summary:")
                st.write(output)
                
                profile = current_profile()
                add_xp(profile, XP_REWARDS["note_summarized"], "note_summarized")
                profile["last_feature_used"] = "📝"
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
                st.markdown('<div class="shimmer" style="height:200px;"></div>', unsafe_allow_html=True)
                
                combined_context = (topic or "") + "\n" + pdf_text
                prompt = build_quiz_prompt(
                    subject, difficulty, num_questions,
                    combined_context if combined_context.strip() else "see attached image"
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
            with st.container():
                st.markdown(f"#### **Question {idx+1}:** {q['question']}")
                options = [f"A) {q['A']}", f"B) {q['B']}", f"C) {q['C']}", f"D) {q['D']}"]
                user_choice = st.radio(f"q_{idx}", options, key=f"q_ans_{idx}", label_visibility="collapsed", index=None)
                st.session_state.quiz_answers[idx] = user_choice[0] if user_choice else ""
                st.write("")

        if st.button("Submit Answers ✔️") and not st.session_state.get("quiz_checked", False):
            st.session_state.quiz_checked = True
            score = 0
            for idx, q in enumerate(st.session_state.quiz_list):
                if st.session_state.quiz_answers.get(idx, "") == q["correct"]:
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
            profile["last_feature_used"] = "❓"
            save_current()

        if st.session_state.get("quiz_checked", False):
            score = 0
            st.write("---")
            st.write("### 📊 Result Summary:")
            for idx, q in enumerate(st.session_state.quiz_list):
                u_ans = st.session_state.quiz_answers.get(idx, "")
                is_correct = u_ans == q["correct"]
                if is_correct:
                    score += 1
                    st.markdown(f'<div class="quiz-correct">✅ <strong>Question {idx+1}:</strong> Correct! (Answer: {u_ans})</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="quiz-incorrect">❌ <strong>Question {idx+1}:</strong> Wrong! (Your Answer: {u_ans} | Correct: {q["correct"]})</div>', unsafe_allow_html=True)

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
                st.markdown('<div class="shimmer" style="height:150px;"></div>', unsafe_allow_html=True)
                
                prompt = build_math_prompt(math_query)
                math_solution = get_ai_response(prompt, image=math_img)
                st.success("Here is how to solve your question:")
                st.write(math_solution)

                profile = current_profile()
                profile["analytics"]["math_problems_solved"] = profile["analytics"].get("math_problems_solved", 0) + 1
                add_xp(profile, XP_REWARDS["math_solved"], "math_solved")
                profile["last_feature_used"] = "🧠"
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
            
            is_flipped = st.session_state.get(f"flash_flipped_{card['id']}", False)
            flip_class = "flipped" if is_flipped else ""
            
            st.markdown(f"""
            <div class="flashcard-container">
                <div class="flashcard {flip_class}" onclick="this.classList.toggle('flipped')">
                    <div class="flashcard-face">
                        <div>{card['front']}</div>
                    </div>
                    <div class="flashcard-face flashcard-back">
                        <div>{card['back']}</div>
                    </div>
                </div>
            </div>
            <p style="text-align:center;color:var(--muted);font-size:0.8rem;">Click the card to flip it</p>
            """, unsafe_allow_html=True)
            
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
                profile["last_feature_used"] = "🎴"
                save_current()
                st.session_state[f"flash_flipped_{card['id']}"] = False
                st.session_state.flash_review_idx = review_idx + 1
                render_gamification_popups()
                st.rerun()

    with tab_generate:
        st.subheader("📄 Upload PDF to Generate Flashcards")
        st.caption("Upload a PDF document and AI will extract key concepts and create flashcards from it.")
        
        pdf_file = st.file_uploader("Upload PDF Document:", type=["pdf"], key="flash_pdf_upload")
        
        if pdf_file:
            with st.spinner("Extracting text from PDF..."):
                pdf_text = extract_text_from_pdf(pdf_file)
                if pdf_text and len(pdf_text) > 50:
                    st.success(f"✅ PDF loaded successfully! Extracted {len(pdf_text)} characters.")
                    with st.expander("Preview extracted text (first 500 characters)"):
                        st.text(pdf_text[:500] + "...")
                else:
                    st.warning("Could not extract enough text from the PDF. Please try another file.")
                    pdf_text = None
        else:
            pdf_text = None
        
        st.markdown("---")
        st.subheader("✏️ Or Enter Topic Manually")
        
        gen_subject = st.text_input("Subject:", value="General Knowledge", key="flash_gen_subject")
        gen_topic = st.text_area("Topic or Notes:", placeholder="Enter a topic or paste notes here...", key="flash_gen_topic")
        gen_count = st.slider("Number of flashcards:", min_value=3, max_value=20, value=8, key="flash_gen_count")
        
        if st.button("✨ Generate Flashcards with AI", use_container_width=True):
            if pdf_text and len(pdf_text) > 50:
                content_to_use = pdf_text
                source_type = "PDF document"
            elif gen_topic.strip():
                content_to_use = gen_topic.strip()
                source_type = "topic"
            else:
                st.warning("Please either upload a PDF or enter a topic/notes to generate flashcards.")
                return
            
            with st.spinner(f"Creating {gen_count} flashcards from {source_type}..."):
                prompt = build_flashcards_prompt(gen_subject, content_to_use, gen_count)
                raw_json = get_ai_response(prompt)
                try:
                    parsed = parse_quiz_json(raw_json)
                    if parsed and len(parsed) > 0:
                        for item in parsed:
                            profile["flashcards"].append(new_flashcard(item["front"], item["back"], gen_subject))
                        save_current()
                        st.success(f"✅ Added {len(parsed)} new flashcards to your deck from {source_type}!")
                        
                        with st.expander("📋 Preview generated flashcards"):
                            for i, item in enumerate(parsed[:5]):
                                st.markdown(f"**{i+1}.** Q: {item['front']}")
                                st.markdown(f"   A: {item['back']}")
                                st.divider()
                            if len(parsed) > 5:
                                st.caption(f"... and {len(parsed) - 5} more cards generated.")
                    else:
                        st.error("No flashcards were generated. Please try again with different content.")
                except Exception as e:
                    st.error(f"Error parsing AI response: {str(e)}")
                    st.error("Please try again or use a different topic.")
    
    with tab_manage:
        if not profile["flashcards"]:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">🗂️</div>
                <div class="empty-state-text">No flashcards yet</div>
                <div class="empty-state-hint">Generate your first set of flashcards above</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            subjects = sorted(set(c.get("subject", "General") for c in profile["flashcards"]))
            
            total_cards = len(profile["flashcards"])
            total_due = len(due_cards)
            st.info(f"📊 Total: {total_cards} cards · {total_due} due for review today")
            
            for subj in subjects:
                with st.expander(f"📁 {subj} ({sum(1 for c in profile['flashcards'] if c.get('subject')==subj)} cards)"):
                    cards_in_subject = [c for c in profile["flashcards"] if c.get("subject") == subj]
                    for c in cards_in_subject:
                        confirm_key = f"confirm_del_card_{c['id']}"
                        cc1, cc2 = st.columns([5, 1])
                        
                        due_status = "🔴 Due" if c.get("due_date", today_str) <= today_str else f"📅 Due: {c.get('due_date', 'N/A')}"
                        cc1.markdown(f"**Q:** {c['front']}  \n**A:** {c['back']}  \n*{due_status} · Reps: {c['reps']}*")
                        
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
                    prompt = build_goal_tasks_prompt(goal)
                    ai_tasks = get_ai_response(prompt).split("\n")
                    profile["todo_list"] = [t.strip("-• ").strip() for t in ai_tasks if t.strip()]
                    add_xp(profile, XP_REWARDS["task_list_created"], "task_list_created")
                    profile["last_feature_used"] = "⏱️"
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
            st.caption("You haven't created a Task List yet.")

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
        profile["last_feature_used"] = "⏱️"
        save_current()
    else:
        st.info("Timer paused — no worries, pick up whenever you're ready.")

@st.fragment(run_every=1)
def render_pomodoro_timer():
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
            profile["last_feature_used"] = "✍️"
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
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">✍️</div>
            <div class="empty-state-text">No notes yet</div>
            <div class="empty-state-hint">Add your first note above to capture ideas</div>
        </div>
        """, unsafe_allow_html=True)

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
    
    profile["last_feature_used"] = "📊"
    save_current()

def show_audio_overview():
    """🎧 Text-to-Speech Audio Overview - Convert notes/lessons to audio"""
    st.header("🎧 Audio Overview Generator")
    st.caption("Turn your notes and lessons into audio overviews for listening on the go")
    
    profile = current_profile()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📝 Content Input")
        
        content_source = st.radio(
            "Choose content source:",
            ["Paste text", "Upload PDF", "Upload Image"],
            horizontal=True,
            key="audio_source"
        )
        
        input_text = ""
        img = None
        
        if content_source == "Paste text":
            input_text = st.text_area(
                "Paste your notes or lesson content here:",
                height=200,
                placeholder="Paste your study notes, lesson content, or any text you want to convert to audio...",
                key="audio_text_input"
            )
        elif content_source == "Upload PDF":
            pdf_file = st.file_uploader("Upload PDF document:", type=["pdf"], key="audio_pdf")
            if pdf_file:
                with st.spinner("Extracting text from PDF..."):
                    extracted_text = extract_text_from_pdf(pdf_file)
                    if extracted_text and len(extracted_text) > 50:
                        st.success(f"✅ Extracted {len(extracted_text)} characters")
                        with st.expander("Preview extracted text"):
                            st.text(extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text)
                        input_text = extracted_text
                    else:
                        st.warning("Could not extract enough text from the PDF. Please try another file.")
        else:
            img_file = st.file_uploader("Upload image (PNG, JPG):", type=["png", "jpg", "jpeg"], key="audio_img")
            if img_file:
                img = Image.open(img_file)
                st.image(img, width=300, caption="Uploaded Image")
                st.info("AI will read text from the image and convert it to audio.")
                st.session_state.audio_img = img
    
    with col2:
        st.subheader("🎵 Audio Settings")
        
        audio_style = st.selectbox(
            "Audio Style:",
            ["overview", "detailed", "study_guide"],
            format_func=lambda x: {
                "overview": "📊 Quick Overview",
                "detailed": "📚 Detailed Lesson",
                "study_guide": "📝 Study Guide"
            }.get(x, x),
            key="audio_style"
        )
        
        speech_speed = st.slider(
            "Speech Speed:",
            min_value=0.5,
            max_value=2.0,
            value=1.0,
            step=0.1,
            help="1.0 is normal speed, 0.5 is half speed, 2.0 is double speed"
        )
        
        voice_pitch = st.slider(
            "Voice Pitch:",
            min_value=0.5,
            max_value=2.0,
            value=1.0,
            step=0.1,
            help="1.0 is normal pitch"
        )
        
        st.divider()
        char_count = len(input_text)
        st.caption(f"📊 Content length: {char_count} characters")
        if char_count > 5000:
            st.warning("⚠️ Long content will be truncated to 5000 characters for processing.")
    
    st.divider()
    
    if st.button("🎧 Generate Audio Overview", use_container_width=True, type="primary"):
        if not input_text and not img:
            st.error("Please provide content to convert to audio.")
            return
        
        with st.spinner("Generating audio script with AI..."):
            content_to_use = input_text if input_text else "Image content (analyzed by AI)"
            prompt = build_audio_overview_prompt(content_to_use, audio_style)
            img_to_send = st.session_state.get("audio_img") if content_source == "Upload Image" else None
            script = get_ai_response(prompt, image=img_to_send)
            
            if "ERROR" in script or "⚠️" in script:
                st.error("Failed to generate audio script. Please try again.")
                st.write(script)
                return
            
            st.session_state.audio_script = script
            st.session_state.audio_style_used = audio_style
            st.session_state.speech_speed = speech_speed
            st.session_state.voice_pitch = voice_pitch
            
            add_xp(profile, 10, "audio_overview_created")
            profile["last_feature_used"] = "🎧"
            save_current()
            render_gamification_popups()
            
            st.success("✅ Audio script generated successfully!")
            st.rerun()
    
    if "audio_script" in st.session_state:
        st.divider()
        st.subheader("🎧 Audio Player")
        
        with st.expander("📄 View Audio Script", expanded=False):
            st.text(st.session_state.audio_script)
        
        st.markdown("""
        <div class="audio-player-container">
            <div style="margin-bottom: 12px; font-weight: 600; color: var(--text);">
                🔊 Audio Overview
            </div>
            <div class="audio-controls">
                <button id="playAudioBtn" onclick="playAudio()">▶️ Play</button>
                <button id="pauseAudioBtn" onclick="pauseAudio()">⏸️ Pause</button>
                <button id="stopAudioBtn" onclick="stopAudio()">⏹️ Stop</button>
                <span class="status-indicator" id="audioStatus">⏸️ Ready</span>
            </div>
        </div>
        
        <script>
        let utterance = null;
        let isPlaying = false;
        let audioScript = null;
        
        function getAudioScript() {
            if (!audioScript) {
                const scriptElement = document.querySelector('[data-testid="stExpander"] .stMarkdown');
                if (scriptElement) {
                    audioScript = scriptElement.textContent || '';
                }
            }
            return audioScript;
        }
        
        function playAudio() {
            const script = getAudioScript();
            if (!script || script.trim() === '') {
                document.getElementById('audioStatus').textContent = '⚠️ No script available';
                return;
            }
            
            window.speechSynthesis.cancel();
            utterance = new SpeechSynthesisUtterance(script);
            utterance.rate = 1.0;
            utterance.pitch = 1.0;
            utterance.volume = 1.0;
            
            const voices = window.speechSynthesis.getVoices();
            if (voices.length > 0) {
                const preferredVoice = voices.find(v => v.lang.startsWith('en') && v.name.includes('Female'));
                if (preferredVoice) {
                    utterance.voice = preferredVoice;
                } else if (voices.find(v => v.lang.startsWith('en'))) {
                    utterance.voice = voices.find(v => v.lang.startsWith('en'));
                }
            }
            
            utterance.onstart = function() {
                isPlaying = true;
                document.getElementById('audioStatus').textContent = '▶️ Playing...';
                document.getElementById('playAudioBtn').disabled = true;
            };
            
            utterance.onend = function() {
                isPlaying = false;
                document.getElementById('audioStatus').textContent = '✅ Complete';
                document.getElementById('playAudioBtn').disabled = false;
            };
            
            utterance.onerror = function(event) {
                isPlaying = false;
                document.getElementById('audioStatus').textContent = '⚠️ Error: ' + event.error;
                document.getElementById('playAudioBtn').disabled = false;
            };
            
            window.speechSynthesis.speak(utterance);
            document.getElementById('audioStatus').textContent = '▶️ Starting...';
        }
        
        function pauseAudio() {
            if (window.speechSynthesis.speaking) {
                window.speechSynthesis.pause();
                document.getElementById('audioStatus').textContent = '⏸️ Paused';
            } else {
                document.getElementById('audioStatus').textContent = '⏸️ Nothing playing';
            }
        }
        
        function stopAudio() {
            window.speechSynthesis.cancel();
            isPlaying = false;
            document.getElementById('audioStatus').textContent = '⏹️ Stopped';
            document.getElementById('playAudioBtn').disabled = false;
        }
        
        window.speechSynthesis.onvoiceschanged = function() {
            window.speechSynthesis.getVoices();
        };
        </script>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            script_text = st.session_state.audio_script
            st.download_button(
                label="📥 Download Script (TXT)",
                data=script_text,
                file_name=f"audio_overview_{date.today()}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with col2:
            if st.button("🔄 Regenerate Script", use_container_width=True):
                st.session_state.pop("audio_script", None)
                st.rerun()
        
        with col3:
            if st.button("❌ Clear Audio", use_container_width=True):
                st.session_state.pop("audio_script", None)
                st.session_state.pop("audio_img", None)
                st.rerun()
        
        with st.expander("💡 Tips for best results"):
            st.markdown("""
            **For best audio quality:**
            - Keep content concise and well-structured
            - Use short sentences for better natural speech
            - Include section headers to help the AI organize the content
            - The AI will automatically add natural pauses and emphasis
            
            **Browser compatibility:**
            - Works best on Chrome, Edge, and Safari
            - Firefox has limited voice support
            - Mobile devices may use system voices
            
            **Troubleshooting:**
            - If no sound plays, check your device volume
            - Try a different browser if voices aren't available
            - For long content, the script may take a moment to generate
            """)

def show_settings():
    """⚙️ Settings page - consolidated language, theme, account settings"""
    st.header("⚙️ Settings")
    profile = current_profile()
    
    # Initialize custom theme with hex values only
    if "custom_theme" not in profile:
        profile["custom_theme"] = {
            "enabled": False,
            "primary_color": "#7C8CFF",
            "secondary_color": "#C77DFF",
            "background_start": "#05070D",
            "background_mid": "#11141F",
            "text_color": "#F5F7FA",
            "card_color": "#1A1A2E",
            "accent_color": "#1A1A2E",
            "border_color": "#2A2A3E",
            "background_image": None,
            "glass_blur": 22,
            "glass_opacity": 0.06,
            "glass_saturation": 180,
            "glow_intensity": 60,
            "solid_bg": "#05070D",
            "grad_start": "#05070D",
            "grad_end": "#1a1a3e",
            "grad_angle": 135,
            "bg_blur": 0,
            "particle_density": "Medium",
            "particle_color": "#7C8CFF",
            "particle_speed": 3,
        }
        save_current()
        st.rerun()
    
    custom_theme = profile["custom_theme"]
    
    tab1, tab2, tab3, tab4 = st.tabs(["🌐 Language", "🎨 Theme Builder", "🔐 Account", "💾 Data"])
    
    with tab1:
        st.subheader("Language Settings")
        current_lang = profile.get("language", "en")
        lang_options = {"en": "English", "si": "Sinhala (සිංහල)"}
        new_lang = st.selectbox(
            "Select your preferred language:",
            options=list(lang_options.keys()),
            format_func=lambda x: lang_options[x],
            index=0 if current_lang == "en" else 1
        )
        if new_lang != current_lang:
            profile["language"] = new_lang
            save_current()
            st.success("Language updated! The app will reload with your new language.")
            st.rerun()
    
    with tab2:
        st.subheader("🎨 Custom Theme Builder")
        st.caption("Design your own unique color scheme and appearance for the app")
        
        theme_tab1, theme_tab2, theme_tab3, theme_tab4 = st.tabs(["🎨 Colors", "🖼️ Background", "✨ Glass Effects", "📦 Presets"])
        
        with theme_tab1:
            st.subheader("Color Customization")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Primary Colors")
                primary = st.color_picker(
                    "Primary Color (Accent 1):",
                    value=custom_theme.get("primary_color", "#7C8CFF"),
                    key="theme_primary"
                )
                secondary = st.color_picker(
                    "Secondary Color (Accent 2):",
                    value=custom_theme.get("secondary_color", "#C77DFF"),
                    key="theme_secondary"
                )
                
                st.markdown("### Text Colors")
                text = st.color_picker(
                    "Text Color:",
                    value=custom_theme.get("text_color", "#F5F7FA"),
                    key="theme_text"
                )
            
            with col2:
                st.markdown("### Background Colors")
                bg_start = st.color_picker(
                    "Background Start:",
                    value=custom_theme.get("background_start", "#05070D"),
                    key="theme_bg_start"
                )
                bg_mid = st.color_picker(
                    "Background Middle:",
                    value=custom_theme.get("background_mid", "#11141F"),
                    key="theme_bg_mid"
                )
                
                st.markdown("### Card & Border Colors")
                card = st.color_picker(
                    "Card Background:",
                    value=custom_theme.get("card_color", "#1A1A2E"),
                    key="theme_card"
                )
                border = st.color_picker(
                    "Border Color:",
                    value=custom_theme.get("border_color", "#2A2A3E"),
                    key="theme_border"
                )
            
            st.markdown("---")
            st.markdown("### 🎯 Live Preview")
            
            def hex_to_rgba(hex_color, alpha=0.06):
                hex_color = hex_color.lstrip('#')
                if len(hex_color) == 6:
                    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
                    return f"rgba({r}, {g}, {b}, {alpha})"
                return hex_color
            
            card_rgba = hex_to_rgba(card, 0.06)
            border_rgba = hex_to_rgba(border, 0.14)
            
            st.markdown(f"""
            <div class="theme-preview" style="background: linear-gradient(135deg, {bg_start} 0%, {bg_mid} 50%, {bg_start} 100%); border: 1px solid {border_rgba};">
                <div class="preview-card" style="background: {card_rgba}; border: 1px solid {border_rgba}; color: {text};">
                    <h3 style="color: {text};">Sample Card</h3>
                    <p style="color: {text};">This is how your theme will look</p>
                    <div style="display: flex; gap: 10px; flex-wrap: wrap; margin: 10px 0;">
                        <span class="preview-accent" style="background: linear-gradient(135deg, {primary}, {secondary});">Button</span>
                        <span class="preview-accent" style="background: {card_rgba}; border: 1px solid {primary}; color: {text};">Secondary</span>
                    </div>
                    <p style="color: {text}99;">Muted text appears like this</p>
                    <div style="background: {primary}22; border-left: 4px solid {primary}; padding: 10px; border-radius: 8px;">
                        <p style="color: {text};">Highlighted content</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("💾 Save Color Theme", use_container_width=True):
                custom_theme["primary_color"] = primary
                custom_theme["secondary_color"] = secondary
                custom_theme["background_start"] = bg_start
                custom_theme["background_mid"] = bg_mid
                custom_theme["text_color"] = text
                custom_theme["card_color"] = card
                custom_theme["border_color"] = border
                custom_theme["enabled"] = True
                save_current()
                st.success("✅ Color theme saved successfully!")
                st.rerun()
        
        with theme_tab2:
            st.subheader("Background Customization")
            
            bg_option = st.radio(
                "Background Type:",
                ["Solid Color", "Gradient", "Upload Image", "Particles"],
                horizontal=True,
                key="bg_type"
            )
            
            if bg_option == "Solid Color":
                solid_color = st.color_picker(
                    "Choose background color:",
                    value=custom_theme.get("solid_bg", "#05070D"),
                    key="solid_bg"
                )
                custom_theme["solid_bg"] = solid_color
                
                st.markdown(f"""
                <style>
                .stApp {{
                    background: {solid_color} !important;
                }}
                </style>
                """, unsafe_allow_html=True)
                
            elif bg_option == "Gradient":
                col1, col2 = st.columns(2)
                with col1:
                    grad_start = st.color_picker(
                        "Gradient Start:",
                        value=custom_theme.get("grad_start", "#05070D"),
                        key="grad_start"
                    )
                with col2:
                    grad_end = st.color_picker(
                        "Gradient End:",
                        value=custom_theme.get("grad_end", "#1a1a3e"),
                        key="grad_end"
                    )
                
                grad_angle = st.slider(
                    "Gradient Angle:",
                    min_value=0,
                    max_value=360,
                    value=custom_theme.get("grad_angle", 135),
                    step=5,
                    key="grad_angle"
                )
                
                custom_theme["grad_start"] = grad_start
                custom_theme["grad_end"] = grad_end
                custom_theme["grad_angle"] = grad_angle
                
                st.markdown(f"""
                <style>
                .stApp {{
                    background: linear-gradient({grad_angle}deg, {grad_start}, {grad_end}) !important;
                }}
                </style>
                """, unsafe_allow_html=True)
                
            elif bg_option == "Upload Image":
                st.info("Upload an image to use as your background. Recommended: 1920x1080 or larger.")
                
                bg_image = st.file_uploader(
                    "Upload Background Image:",
                    type=["jpg", "jpeg", "png", "webp"],
                    key="bg_image_upload"
                )
                
                if bg_image:
                    import base64
                    image_data = bg_image.getvalue()
                    b64_image = base64.b64encode(image_data).decode()
                    
                    st.session_state.bg_image_data = b64_image
                    st.image(bg_image, use_container_width=True)
                    
                    st.markdown(f"""
                    <style>
                    .stApp {{
                        background: url(data:image/{bg_image.type.split('/')[-1]};base64,{b64_image}) !important;
                        background-size: cover !important;
                        background-position: center !important;
                        background-attachment: fixed !important;
                    }}
                    .stApp::before {{
                        content: "";
                        position: fixed;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                        background: rgba(0,0,0,0.4);
                        z-index: 0;
                    }}
                    [data-testid="stAppViewContainer"] {{
                        position: relative;
                        z-index: 1;
                    }}
                    </style>
                    """, unsafe_allow_html=True)
                    
                    st.success("✅ Background image applied!")
                    
                    blur_amount = st.slider(
                        "Blur Amount:",
                        min_value=0,
                        max_value=20,
                        value=custom_theme.get("bg_blur", 0),
                        step=1,
                        key="bg_blur"
                    )
                    custom_theme["bg_blur"] = blur_amount
                    
                    if blur_amount > 0:
                        st.markdown(f"""
                        <style>
                        .stApp {{
                            backdrop-filter: blur({blur_amount}px) !important;
                        }}
                        </style>
                        """, unsafe_allow_html=True)
            
            elif bg_option == "Particles":
                st.info("✨ Animated particle background (lightweight CSS animation)")
                
                particle_density = st.select_slider(
                    "Particle Density:",
                    options=["Low", "Medium", "High"],
                    value=custom_theme.get("particle_density", "Medium"),
                    key="particle_density"
                )
                
                particle_color = st.color_picker(
                    "Particle Color:",
                    value=custom_theme.get("particle_color", "#7C8CFF"),
                    key="particle_color"
                )
                
                particle_speed = st.slider(
                    "Animation Speed:",
                    min_value=1,
                    max_value=10,
                    value=custom_theme.get("particle_speed", 3),
                    step=1,
                    key="particle_speed"
                )
                
                custom_theme["particle_density"] = particle_density
                custom_theme["particle_color"] = particle_color
                custom_theme["particle_speed"] = particle_speed
                
                particle_count = {"Low": 30, "Medium": 60, "High": 100}[particle_density]
                
                particles_html = ""
                for i in range(particle_count):
                    size = 3 + (i % 5)
                    x = i * (100 / particle_count)
                    y = (i * 37) % 100
                    delay = (i * 0.3) % 5
                    duration = 5 + (i % 10)
                    particles_html += f"""
                    <div class="particle" style="
                        left: {x}%;
                        top: {y}%;
                        width: {size}px;
                        height: {size}px;
                        background: {particle_color};
                        animation-delay: {delay}s;
                        animation-duration: {duration}s;
                        opacity: {0.3 + (i % 5) * 0.1};
                    "></div>
                    """
                
                st.markdown(f"""
                <style>
                .particle-container {{
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    pointer-events: none;
                    z-index: 0;
                    overflow: hidden;
                }}
                .particle {{
                    position: absolute;
                    border-radius: 50%;
                    animation: float-particle {particle_speed * 2}s ease-in-out infinite alternate;
                }}
                @keyframes float-particle {{
                    0% {{ transform: translate(0, 0) scale(1); }}
                    100% {{ transform: translate(50px, -50px) scale(1.5); }}
                }}
                </style>
                <div class="particle-container">
                    {particles_html}
                </div>
                """, unsafe_allow_html=True)
                
                st.success("✅ Particle background activated!")
            
            if st.button("💾 Save Background Settings", use_container_width=True):
                save_current()
                st.success("✅ Background settings saved!")
                st.rerun()
        
        with theme_tab3:
            st.subheader("Glass Effects Customization")
            
            glass_blur = st.slider(
                "Glass Blur Intensity:",
                min_value=5,
                max_value=40,
                value=custom_theme.get("glass_blur", 22),
                step=1,
                key="glass_blur",
                help="Higher values create more frosted glass effect"
            )
            
            glass_opacity = st.slider(
                "Glass Opacity:",
                min_value=0.05,
                max_value=0.4,
                value=custom_theme.get("glass_opacity", 0.06),
                step=0.01,
                key="glass_opacity",
                help="Opacity of the glass panels"
            )
            
            glass_saturation = st.slider(
                "Color Saturation:",
                min_value=100,
                max_value=250,
                value=custom_theme.get("glass_saturation", 180),
                step=5,
                key="glass_saturation",
                help="Saturation of colors behind glass"
            )
            
            glow_intensity = st.slider(
                "Glow Intensity:",
                min_value=0,
                max_value=100,
                value=custom_theme.get("glow_intensity", 60),
                step=5,
                key="glow_intensity",
                help="Glow effect on accent colors"
            )
            
            st.markdown("### Preview")
            glass_color = f"rgba(255, 255, 255, {glass_opacity})"
            
            st.markdown(f"""
            <div style="
                background: {glass_color};
                backdrop-filter: blur({glass_blur}px) saturate({glass_saturation}%);
                -webkit-backdrop-filter: blur({glass_blur}px) saturate({glass_saturation}%);
                border: 1px solid rgba(255, 255, 255, 0.14);
                border-radius: 18px;
                padding: 30px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.18);
                color: white;
                text-align: center;
            ">
                <h3>Glass Effect Preview</h3>
                <p>Blur: {glass_blur}px | Opacity: {glass_opacity:.2f} | Saturation: {glass_saturation}%</p>
                <div style="display: flex; gap: 10px; justify-content: center; margin-top: 10px;">
                    <span style="background: linear-gradient(135deg, {custom_theme.get('primary_color', '#7C8CFF')}, {custom_theme.get('secondary_color', '#C77DFF')}); padding: 8px 16px; border-radius: 10px; box-shadow: 0 0 {glow_intensity}px rgba(124, 140, 255, 0.4);">Glowing Element</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            custom_theme["glass_blur"] = glass_blur
            custom_theme["glass_opacity"] = glass_opacity
            custom_theme["glass_saturation"] = glass_saturation
            custom_theme["glow_intensity"] = glow_intensity
            
            if st.button("💾 Save Glass Settings", use_container_width=True):
                save_current()
                st.success("✅ Glass settings saved!")
                st.rerun()
        
        with theme_tab4:
            st.subheader("Theme Presets")
            st.caption("Quickly apply pre-designed themes")
            
            presets = {
                "Liquid Glass (Default)": {
                    "primary": "#7C8CFF",
                    "secondary": "#C77DFF",
                    "bg_start": "#05070D",
                    "bg_mid": "#11141F",
                    "text": "#F5F7FA",
                    "card": "#1A1A2E",
                    "border": "#2A2A3E",
                },
                "Midnight Aurora": {
                    "primary": "#00D4FF",
                    "secondary": "#7B2FBE",
                    "bg_start": "#0a0a1a",
                    "bg_mid": "#1a0a2e",
                    "text": "#E0E7FF",
                    "card": "#0D1A2B",
                    "border": "#1A2A4A",
                },
                "Warm Sunset": {
                    "primary": "#FF6B35",
                    "secondary": "#FFD93D",
                    "bg_start": "#1a0a0a",
                    "bg_mid": "#2a1510",
                    "text": "#FFF5E6",
                    "card": "#2A1A10",
                    "border": "#3A2A20",
                },
                "Forest Calm": {
                    "primary": "#4CAF50",
                    "secondary": "#8BC34A",
                    "bg_start": "#0a1a0a",
                    "bg_mid": "#102010",
                    "text": "#E8F5E9",
                    "card": "#0A1A0A",
                    "border": "#1A2A1A",
                },
                "Ocean Deep": {
                    "primary": "#0077B6",
                    "secondary": "#00B4D8",
                    "bg_start": "#050a15",
                    "bg_mid": "#0a1520",
                    "text": "#E0F7FA",
                    "card": "#0A1520",
                    "border": "#152A3A",
                },
                "Neon Dream": {
                    "primary": "#FF006E",
                    "secondary": "#FFD93D",
                    "bg_start": "#0a000a",
                    "bg_mid": "#1a001a",
                    "text": "#FFE0FF",
                    "card": "#1A001A",
                    "border": "#2A0A2A",
                },
                "Minimal Light": {
                    "primary": "#3B82F6",
                    "secondary": "#8B5CF6",
                    "bg_start": "#F8FAFC",
                    "bg_mid": "#E2E8F0",
                    "text": "#1E293B",
                    "card": "#FFFFFF",
                    "border": "#CBD5E1",
                },
            }
            
            cols = st.columns(3)
            for idx, (preset_name, preset_colors) in enumerate(presets.items()):
                col = cols[idx % 3]
                with col:
                    def hex_to_rgba_preview(hex_color, alpha=0.06):
                        hex_color = hex_color.lstrip('#')
                        if len(hex_color) == 6:
                            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
                            return f"rgba({r}, {g}, {b}, {alpha})"
                        return hex_color
                    
                    card_rgba = hex_to_rgba_preview(preset_colors["card"], 0.06)
                    border_rgba = hex_to_rgba_preview(preset_colors["border"], 0.14)
                    
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, {preset_colors['bg_start']}, {preset_colors['bg_mid']});
                        border: 1px solid {border_rgba};
                        border-radius: 14px;
                        padding: 16px;
                        margin: 8px 0;
                    ">
                        <div style="
                            background: {card_rgba};
                            backdrop-filter: blur(10px);
                            border: 1px solid {border_rgba};
                            border-radius: 10px;
                            padding: 12px;
                            color: {preset_colors['text']};
                        ">
                            <div style="display: flex; gap: 8px; margin-bottom: 8px;">
                                <span style="background: {preset_colors['primary']}; width: 20px; height: 20px; border-radius: 50%; display: inline-block;"></span>
                                <span style="background: {preset_colors['secondary']}; width: 20px; height: 20px; border-radius: 50%; display: inline-block;"></span>
                            </div>
                            <strong>{preset_name}</strong>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"Apply", key=f"preset_{idx}"):
                        custom_theme["primary_color"] = preset_colors["primary"]
                        custom_theme["secondary_color"] = preset_colors["secondary"]
                        custom_theme["background_start"] = preset_colors["bg_start"]
                        custom_theme["background_mid"] = preset_colors["bg_mid"]
                        custom_theme["text_color"] = preset_colors["text"]
                        custom_theme["card_color"] = preset_colors["card"]
                        custom_theme["border_color"] = preset_colors["border"]
                        custom_theme["enabled"] = True
                        save_current()
                        st.success(f"✅ Applied {preset_name} theme!")
                        st.rerun()
            
            st.markdown("---")
            if st.button("🔄 Reset to Default Theme", use_container_width=True, type="primary"):
                custom_theme["enabled"] = False
                save_current()
                st.success("✅ Reset to default theme!")
                st.rerun()
        
        st.markdown("---")
        col1, col2 = st.columns([1, 3])
        with col1:
            enabled = st.toggle(
                "Enable Custom Theme",
                value=custom_theme.get("enabled", False),
                key="theme_enabled"
            )
        
        with col2:
            if enabled:
                st.success("🟢 Custom theme is active")
            else:
                st.info("⚪ Using default Liquid Glass theme")
        
        if enabled != custom_theme.get("enabled", False):
            custom_theme["enabled"] = enabled
            save_current()
            st.rerun()
    
    with tab3:
        st.subheader("Account Settings")
        st.write(f"**Username:** {st.session_state.active_user}")
        st.write(f"**Email:** {profile.get('email', 'Not set')}")
        st.write(f"**Auth Method:** {profile.get('auth_provider', 'password').title()}")
        
        if profile.get("auth_provider") == "password":
            st.write("---")
            st.subheader("Change Password")
            old_pw = st.text_input("Current Password:", type="password", key="settings_old_pw")
            new_pw = st.text_input("New Password:", type="password", key="settings_new_pw")
            confirm_pw = st.text_input("Confirm New Password:", type="password", key="settings_confirm_pw")
            
            if st.button("Update Password", key="settings_update_pw"):
                if len(new_pw) < 8:
                    st.error("Password must be at least 8 characters.")
                elif new_pw != confirm_pw:
                    st.error("Passwords don't match.")
                elif not verify_password(old_pw, profile.get("password_hash", "")):
                    st.error("Current password is incorrect.")
                else:
                    profile["password_hash"] = hash_password(new_pw)
                    save_current()
                    st.success("Password updated successfully!")
        
        if st.button("🗑️ Delete Account", use_container_width=True, key="settings_delete_account"):
            st.warning("⚠️ This will permanently delete your account and all data. This cannot be undone.")
            confirm = st.text_input("Type your username to confirm deletion:")
            if st.button("Confirm Delete", use_container_width=True, key="settings_confirm_delete"):
                if confirm == st.session_state.active_user:
                    conn = get_db_connection()
                    try:
                        with _db_lock:
                            conn.execute("DELETE FROM profiles WHERE username = ?", (st.session_state.active_user,))
                            conn.commit()
                    finally:
                        conn.close()
                    del st.session_state.all_data["users"][st.session_state.active_user]
                    st.session_state.active_user = None
                    st.session_state.auth_method = None
                    st.success("Account deleted successfully.")
                    st.rerun()
                else:
                    st.error("Username does not match. Deletion cancelled.")
    
    with tab4:
        st.subheader("💾 Data Management")
        
        st.markdown("### Export Data")
        st.caption("Download all your data as a backup file")
        
        if st.button("📥 Export All Data", use_container_width=True):
            export_data = {
                "profile": profile,
                "username": st.session_state.active_user,
                "export_date": str(datetime.now()),
                "version": "1.0"
            }
            
            json_data = json.dumps(export_data, indent=2, ensure_ascii=False)
            st.download_button(
                label="⬇️ Download Backup",
                data=json_data,
                file_name=f"study_organizer_backup_{date.today()}.json",
                mime="application/json",
                use_container_width=True
            )
        
        st.markdown("---")
        st.markdown("### Import Data")
        st.caption("Restore your data from a backup file")
        
        import_file = st.file_uploader("Upload backup file:", type=["json"], key="import_backup")
        
        if import_file:
            try:
                import_data = json.load(import_file)
                st.success("✅ Backup file loaded successfully!")
                st.json(import_data)
                
                if st.button("🔄 Restore Data (WARNING: Overwrites current data)", use_container_width=True, type="primary"):
                    if st.checkbox("I understand this will overwrite my current data"):
                        for key, value in import_data.get("profile", {}).items():
                            profile[key] = value
                        save_current()
                        st.success("✅ Data restored successfully! The app will reload.")
                        st.rerun()
            except Exception as e:
                st.error(f"Error reading backup file: {str(e)}")
        
        st.markdown("---")
        st.markdown("### Storage Info")
        st.caption(f"Profile last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        total_flashcards = len(profile.get("flashcards", []))
        total_notes = len(profile.get("scribble_notes", []))
        total_quizzes = profile.get("analytics", {}).get("quiz_taken", 0)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("📚 Flashcards", total_flashcards)
        col2.metric("📝 Notes", total_notes)
        col3.metric("❓ Quizzes Taken", total_quizzes)

# Add this anywhere in your main app after login
with st.sidebar:
    st.markdown("---")
    st.subheader("🔗 Parent / Teacher View")
    st.caption("Share this link for a read-only progress summary:")
    encoded_key = urllib.parse.quote(st.session_state.active_user, safe="")
    full_url = f"{st.get_option('server.baseUrlPath') or 'https://smart-study-organizer.streamlit.app'}?view=parent&user={encoded_key}"
    st.code(full_url, language=None)
    st.caption("No login required - parents/teachers can see your progress.")
    st.markdown("---")

# PAGE ROUTING DICTIONARY WITH LABELS
PAGES = {
    "🏠": show_home,
    "💡": show_daily_facts,
    "🗺️": show_mindmap,
    "📝": show_summarizer,
    "❓": show_mcq_quiz,
    "🧠": show_math_solver,
    "🎴": show_flashcards,
    "⏱️": show_pomodoro,
    "✍️": show_scribble_pad,
    "🎧": show_audio_overview,
    "📊": show_analytics,
    "⚙️": show_settings,
}

# FLOATING DOCK RADIO SELECTION
st.markdown("""
<style>
[data-testid="stMainBlockContainer"] { padding-right: 240px !important; }
@media (max-width: 900px) {
    [data-testid="stMainBlockContainer"] { padding-right: 1.2rem !important; padding-bottom: 96px !important; }
}
</style>
""", unsafe_allow_html=True)

# Build nav options with labels for tooltips
nav_options = list(PAGES.keys())
nav_labels = {
    "🏠": "Home Dashboard",
    "💡": "Daily Facts",
    "🗺️": "Mindmap",
    "📝": "Summarizer",
    "❓": "MCQ Quiz",
    "🧠": "Math Solver",
    "🎴": "Flashcards",
    "⏱️": "Pomodoro",
    "✍️": "Scribble Pad",
    "🎧": "Audio Overview",
    "📊": "Analytics",
    "⚙️": "Settings",
}

# Initialize session state for navigation
if "nav_choice" not in st.session_state:
    profile = current_profile()
    last_feature = profile.get("last_feature_used", "🏠")
    st.session_state["nav_choice"] = last_feature if last_feature in PAGES else "🏠"

with st.container(key="nav_dock"):
    choice = st.radio(
        "Navigation",
        options=nav_options,
        horizontal=True,
        label_visibility="collapsed",
        key="nav_radio",
        index=nav_options.index(st.session_state["nav_choice"])
    )
    
    if choice != st.session_state["nav_choice"]:
        st.session_state["nav_choice"] = choice
        st.rerun()

# Add tooltips using CSS
st.markdown("""
<style>
div[class*="st-key-nav_dock"] label[data-baseweb="radio"]:nth-child(1) { --tooltip: 'Home Dashboard'; }
div[class*="st-key-nav_dock"] label[data-baseweb="radio"]:nth-child(2) { --tooltip: 'Daily Facts'; }
div[class*="st-key-nav_dock"] label[data-baseweb="radio"]:nth-child(3) { --tooltip: 'Mindmap'; }
div[class*="st-key-nav_dock"] label[data-baseweb="radio"]:nth-child(4) { --tooltip: 'Summarizer'; }
div[class*="st-key-nav_dock"] label[data-baseweb="radio"]:nth-child(5) { --tooltip: 'MCQ Quiz'; }
div[class*="st-key-nav_dock"] label[data-baseweb="radio"]:nth-child(6) { --tooltip: 'Math Solver'; }
div[class*="st-key-nav_dock"] label[data-baseweb="radio"]:nth-child(7) { --tooltip: 'Flashcards'; }
div[class*="st-key-nav_dock"] label[data-baseweb="radio"]:nth-child(8) { --tooltip: 'Pomodoro'; }
div[class*="st-key-nav_dock"] label[data-baseweb="radio"]:nth-child(9) { --tooltip: 'Scribble Pad'; }
div[class*="st-key-nav_dock"] label[data-baseweb="radio"]:nth-child(10) { --tooltip: 'Audio Overview'; }
div[class*="st-key-nav_dock"] label[data-baseweb="radio"]:nth-child(11) { --tooltip: 'Analytics'; }
div[class*="st-key-nav_dock"] label[data-baseweb="radio"]:nth-child(12) { --tooltip: 'Settings'; }

div[class*="st-key-nav_dock"] label[data-baseweb="radio"]:hover::after {
    content: var(--tooltip) !important;
}
</style>
""", unsafe_allow_html=True)

# EXECUTE SELECTED PAGE FUNCTION
page_to_show = st.session_state.get("nav_choice", "🏠")
if page_to_show in PAGES:
    PAGES[page_to_show]()
else:
    PAGES["🏠"]()