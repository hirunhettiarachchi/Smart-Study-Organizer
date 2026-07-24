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
from datetime import date, datetime, timedelta, timezone
import pandas as pd
from google import genai
from PIL import Image
import PyPDF2


try:
    from dotenv import load_dotenv
    load_dotenv()  # loads variables from a .env file in the project folder, if one exists
except ImportError:
    pass  # python-dotenv not installed — .env files just won't be picked up; secrets.toml or a real env var still work

# PAGE CONFIG
st.set_page_config(page_title="Smart Study Organizer Pro", page_icon="🎓", layout="wide")


DB_FILE = "study_organizer.db"
LEGACY_JSON_FILE = "study_organizer_data.json"  # only read once, to migrate old data in

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
    "email": "",
    "password_hash": None,   # None = no password set (Google-only account, or legacy pre-auth profile)
    "auth_provider": "password",  # "password" or "google"
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
#
# Previously this app kept everyone's data in one big JSON file and
# rewrote the ENTIRE file on every save. That has two real problems under
# concurrent use: (1) a crash mid-write can corrupt the whole file for
# every user, and (2) if two people are using the app at the same time,
# whichever one saves last silently overwrites the other's changes — even
# to a completely different profile — because each save dumps that
# session's whole in-memory snapshot, stale bits and all.
#
# SQLite (one row per user, in WAL mode) fixes both: writes are atomic
# and scoped to a single row, so saving your profile can never clobber
# someone else's, and a crash mid-write can't corrupt other people's data.
_db_lock = threading.Lock()

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL;")  # lets multiple users read/write concurrently and safely
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
    """One-time import: if an old study_organizer_data.json exists and the
    new database is still empty, pull its profiles in so nobody's existing
    data gets lost by upgrading. Safe to leave in place permanently — it
    only ever runs when the database has zero rows."""
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
        pass  # if the legacy file is unreadable, just start fresh in the new database
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
            continue  # skip a corrupted row rather than crashing the whole app
    return {"users": users}

def save_profile(key, profile):
    """Atomically write ONE user's row. Always prefer this over save_all_data —
    it's what makes concurrent use safe, since it can never touch anyone
    else's data."""
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

def save_all_data(data):
    """Kept for any leftover call sites, but writes every row from this
    session's in-memory snapshot — prefer save_profile() for anything that
    only touches one user, since that can't clobber concurrent changes to
    other profiles the way a wholesale rewrite can."""
    for key, profile in data.get("users", {}).items():
        save_profile(key, profile)

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
    profile.setdefault("email", "")
    profile.setdefault("password_hash", None)
    profile.setdefault("auth_provider", "password")
    return profile

# ACCOUNT SECURITY
# Passwords are hashed with PBKDF2-HMAC-SHA256 (stdlib only — no extra
# dependency). This is a well-vetted, OWASP-recommended algorithm; the
# iteration count below matches current OWASP guidance for SHA-256.
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
    """Look up a profile by username (dict key) or by email. Returns (key, profile) or (None, None)."""
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
    """Very basic in-session brute-force slow-down: 5 failed attempts locks that
    identifier out for the rest of the browser session. This is a light backstop,
    not a substitute for real infra-level rate limiting on a public deployment."""
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

def current_profile():
    return st.session_state.all_data["users"][st.session_state.active_user]

def save_current():
    key = st.session_state.active_user
    users = st.session_state.all_data.get("users", {})
    if key and key in users:
        save_profile(key, users[key])

# AI SETUP
def get_api_key():
    # 1) Streamlit secrets file: .streamlit/secrets.toml
    try:
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    # 2) A real environment variable (set in the shell, or via a .env file loaded above)
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
        return (
            "⚠️ **No Gemini API key found.** The app checked three places and found nothing:\n\n"
            "1. `.streamlit/secrets.toml` in your project folder, containing a line: `GEMINI_API_KEY = \"your-key-here\"`\n"
            "2. A `GEMINI_API_KEY` environment variable set in the terminal you launched the app from\n"
            "3. A `.env` file in your project folder, containing a line: `GEMINI_API_KEY=your-key-here`\n\n"
            "After adding the key with one of these methods, **fully stop and restart** `streamlit run app.py` — "
            "it only reads the key once when the server starts, so a running app won't pick up a key you just added.\n\n"
            "අවශ්‍ය නම්: ඉහත ක්‍රම 3න් එකකින් `GEMINI_API_KEY` එක එකතු කර, යෙදුම නවත්වා යළි ආරම්භ කරන්න."
        )
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
        if "401" in err_text or "UNAUTHENTICATED" in err_text or "ACCESS_TOKEN_TYPE_UNSUPPORTED" in err_text or "invalid_api_key" in err_text.lower():
            return (
                "⚠️ **Your API key was found, but Google rejected it (401/authentication error).** "
                "This is a known issue in 2026: Google is migrating Gemini API keys from the old `AIza...` format "
                "to a new `AQ....` \"auth key\" format, and some `google-genai` SDK versions don't authenticate the new "
                "format correctly yet. If your key starts with `AQ.`, try:\n\n"
                "1. Upgrade the SDK: run `pip install --upgrade google-genai` and fully restart the app.\n"
                "2. If that doesn't help, generate a fresh key in Google AI Studio and try again — some existing `AQ.` keys "
                "have had propagation issues.\n\n"
                f"Raw error: {err_text}"
            )
        return f"ERROR: Please check your internet connection ({err_text})"

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

# THEME SYSTEM — "Liquid Glass"
# One theme only: a deep dark backdrop with soft floating colour blobs, and
# every panel (dock, profile card, buttons, badges, pomodoro ring, flash
# cards) rendered as frosted, translucent glass with a subtle specular
# highlight along its top edge — Apple's "Liquid Glass" language.
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

    /* 2. Apply font ONLY to main app content & sidebar text */
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

    /* 3. HARD RESET for Streamlit's Header Icons */
    [data-testid="stHeader"] *, 
    [data-testid="stAppHeader"] *,
    header * {{
        font-family: 'Material Symbols Rounded', 'Material Icons', sans-serif !important;
    }}

    /* ---------- Liquid backdrop: soft static colour wash, no filters/animation ---------- */
    /* (A blurred, animated, full-viewport layer here can make some browsers/GPUs
       stall and paint nothing at all — so this stays a plain, static gradient.) */
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

    /* Subtle page-load transition so switching sections feels alive, not jarring */
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

    /* ---------- Glass helper: frosted surface + top specular highlight ---------- */
    .profile-card, .streak-pill, .pomo-ring-inner, .flash-face,
    div[data-testid="stMetric"], div[data-testid="stExpander"],
    div[data-testid="stForm"] {{
        background: var(--card-bg) !important;
        backdrop-filter: blur(22px) saturate(180%);
        -webkit-backdrop-filter: blur(22px) saturate(180%);
        border: 1px solid var(--border) !important;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.18), var(--shadow);
    }}

    /* ---------- Inputs, selects, textareas, file uploader: same glass surface ---------- */
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
    div[data-testid="stTextInput"] input:focus,
    div[data-testid="stNumberInput"] input:focus,
    div[data-testid="stTextArea"] textarea:focus,
    div[data-testid="stSelectbox"] div[data-baseweb="select"]:focus-within > div {{
        border-color: var(--accent-1) !important;
        box-shadow: 0 0 0 3px var(--accent-soft) !important;
    }}

    /* Selectbox / multiselect dropdown popover menu */
    div[data-baseweb="popover"] div[data-baseweb="menu"] {{
        background: var(--bg-elevated) !important;
        backdrop-filter: blur(24px) saturate(180%) !important;
        -webkit-backdrop-filter: blur(24px) saturate(180%) !important;
        border: 1px solid var(--border) !important;
        border-radius: 14px !important;
        box-shadow: var(--shadow) !important;
    }}
    div[data-baseweb="popover"] li, div[data-baseweb="popover"] li * {{
        color: var(--text) !important;
    }}
    div[data-baseweb="popover"] li:hover {{
        background: var(--accent-soft) !important;
    }}

    /* Sliders: glowing glass thumb + tinted track */
    div[data-testid="stSlider"] [data-baseweb="slider"] > div:nth-child(2) {{
        background: var(--track-bg) !important;
    }}
    div[data-testid="stSlider"] [role="slider"] {{
        background: linear-gradient(135deg, var(--accent-1), var(--accent-2)) !important;
        border: 2px solid rgba(255, 255, 255, 0.6) !important;
        box-shadow: 0 0 0 4px var(--accent-soft), 0 2px 10px rgba(0, 0, 0, 0.4) !important;
    }}

    /* ---------- Floating dock navigation ---------- */
    div[class*="st-key-nav_dock"] div[data-testid="stRadio"] {{
        position: fixed !important;
        right: 20px !important;
        top: 0 !important;
        transform: translateY(50%) !important;
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
    div[class*="st-key-nav_dock"] div[data-testid="stRadio"] label > div:first-child {{ display: none !important; }}
    div[class*="st-key-nav_dock"] div[data-testid="stRadio"] label {{
        background: transparent !important;
        padding: 6px 12px !important;
        border-radius: 14px !important;
        color: var(--muted) !important;
        cursor: pointer !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        white-space: nowrap;
    }}
    div[class*="st-key-nav_dock"] div[data-testid="stRadio"] label:hover {{
        color: var(--text) !important;
        background: var(--accent-soft) !important;
    }}
    div[class*="st-key-nav_dock"] div[data-testid="stRadio"] label[data-checked="true"] {{
        background: linear-gradient(135deg, var(--accent-1) 0%, var(--accent-2) 100%) !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 16px rgba(124, 140, 255, 0.4);
    }}

    /* On narrow / mobile screens the side dock becomes a bottom nav bar */
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
        }}
        div[class*="st-key-nav_dock"] div[data-testid="stRadio"] > div {{
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
        border-radius: 18px;
        padding: 16px;
    }}

    /* ---------- Buttons: glossy glass pills ---------- */
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
    .stButton > button:active {{
        transform: translateY(0px) scale(0.98) !important;
        box-shadow: 0 2px 8px rgba(124, 140, 255, 0.3) !important;
    }}
    .stButton > button:focus-visible {{
        outline: 2px solid var(--accent-1) !important;
        outline-offset: 2px !important;
    }}

    /* ---------- Profile card ---------- */
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

    /* ---------- Pomodoro ring ---------- */
    .pomo-ring {{
        width: 220px; height: 220px; border-radius: 50%;
        margin: 12px auto 20px auto;
        background: conic-gradient(var(--accent-1) var(--pct, 0%), var(--track-bg) 0);
        display: flex; align-items: center; justify-content: center;
        transition: background 0.6s linear;
        box-shadow: 0 0 50px rgba(124, 140, 255, 0.3);
    }}
    .pomo-ring-inner {{
        width: 178px; height: 178px; border-radius: 50%;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        gap: 4px;
    }}
    .pomo-time {{ font-size: 2.1rem; font-weight: 700; letter-spacing: 0.5px; color: var(--text); font-variant-numeric: tabular-nums; }}
    .pomo-label {{ font-size: 0.75rem; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; }}

    /* ---------- Flashcards ---------- */
    .flash-face {{
        padding: 24px; border-radius: 18px; text-align: center; font-size: 1.25rem;
    }}
    </style>
    """, unsafe_allow_html=True)


# PARENT / TEACHER READ-ONLY VIEW
# Reached via a link like "?view=parent&user=<student name>" — shows a
# read-only progress summary for that one profile. No login, no editing,
# no AI calls happen on this path; it just reads existing saved data.
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

# If Google auth is configured and the user just completed the Google
# redirect flow, st.user.is_logged_in will be true here. Find or create
# their profile by email and log them straight in, skipping the form.

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
                # First time this Google account has signed in — collect the
                # same profile details a manual sign-up would ask for, rather
                # than silently defaulting to Grade 8 / age 13.
                st.session_state.google_pending_email = google_email
                st.session_state.google_pending_name = st.user.name or google_email.split("@")[0]
    except Exception:
        pass  # st.user has no attributes until a login attempt has happened at least once

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
            if st.session_state.get("auth_method") == "google":
                try:
                    st.logout()
                except Exception:
                    pass
            st.session_state.active_user = None
            st.session_state.auth_method = None
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
    "💡": show_daily_facts,
    "🗺️": show_mindmap,
    "📝": show_summarizer,
    "❓": show_mcq_quiz,
    "🧠": show_math_solver,
    "🎴": show_flashcards,
    "⏱️": show_pomodoro,
    "✍️": show_scribble_pad,
    "📊": show_analytics,
}

st.markdown("""
<style>
[data-testid="stMainBlockContainer"] { padding-right: 240px !important; }
@media (max-width: 900px) {
    [data-testid="stMainBlockContainer"] { padding-right: 1.2rem !important; padding-bottom: 96px !important; }
}
</style>
""", unsafe_allow_html=True)

with st.container(key="nav_dock"):
    choice = st.radio(
        "Navigation",
        options=list(PAGES.keys()),
        horizontal=True,
        label_visibility="collapsed"
    )

# EXECUTE SELECTED PAGE FUNCTION
PAGES[choice]()