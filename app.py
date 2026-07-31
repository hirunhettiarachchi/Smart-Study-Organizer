import streamlit as st
import streamlit.components.v1 as components
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
import wave
import io
import base64
from datetime import date, datetime, timedelta, timezone
import pandas as pd
from groq import Groq
from PIL import Image
import PyPDF2
import random
import numpy as np

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
    "audio_overview_created": 10,
    "exam_completed": 20,
    "study_pack_exported": 5,
    "schedule_created": 10,
}

BADGES = {
    "first_steps": {"label": "🌱 First Steps", "desc": "Completed your first quiz"},
    "quiz_5": {"label": "📚 Quiz Regular", "desc": "Completed 5 quizzes"},
    "quiz_20": {"label": "🏆 Quiz Master", "desc": "Completed 20 quizzes"},
    "perfect_score": {"label": "💯 Perfectionist", "desc": "Got a perfect quiz score"},
    "pomodoro_5": {"label": "🍅 Focus Builder", "desc": "Finished 5 Pomodoro sessions"},
    "pomodoro_25": {"label": "🔥 Deep Work Pro", "desc": "Finished 25 Pomodoro sessions"},
    "streak_3": {"label": "⚡ 3-Day Streak", "desc": "Studied 3 days in a row"},
    "streak_7": {"label": "🌟 7-Day Streak", "desc": "Studied 7 days in a row"},
    "streak_30": {"label": "👑 30-Day Streak", "desc": "Studied 30 days in a row"},
    "flashcard_10": {"label": "🧠 Card Crusher", "desc": "Reviewed 10 flashcards"},
    "level_5": {"label": "🚀 Rising Star", "desc": "Reached Level 5"},
    "level_10": {"label": "🌌 Study Legend", "desc": "Reached Level 10"},
    "science_whiz": {"label": "🔬 Science Whiz", "desc": "Complete 50 science quiz questions"},
    "math_wizard": {"label": "🧮 Math Wizard", "desc": "Complete 50 math problems correctly"},
    "history_hero": {"label": "📜 History Hero", "desc": "Complete 30 history quiz questions"},
    "night_owl": {"label": "🦉 Night Owl", "desc": "Complete 10 study sessions after 9 PM"},
    "early_bird": {"label": "🌅 Early Bird", "desc": "Complete 10 study sessions before 7 AM"},
    "streak_50": {"label": "💎 50-Day Streak", "desc": "Maintain a 50-day study streak"},
    "streak_100": {"label": "👑 100-Day Streak", "desc": "Maintain a 100-day study streak"},
    "perfect_exam": {"label": "🏅 Exam Master", "desc": "Score 100% on 5 exams"},
    "flashcard_100": {"label": "📚 Card Master", "desc": "Review 100 flashcards"},
    "pomodoro_100": {"label": "⏰ Time Lord", "desc": "Complete 100 Pomodoro sessions"},
}

TRANSLATIONS = {
    "💡 Daily Facts": "💡 දිනපතා තොරතුරු",
    "🗺️ Mindmap": "🗺️ මනසේ සිතියම",
    "📝 Summarizer": "📝 සාරාංශකරණය",
    "🎧 Audio Overview": "🎧 ශ්‍රව්‍ය දළ විශ්ලේෂණය",
    "Turn your notes into a short two-host podcast-style discussion you can listen to.": "ඔබේ සටහන් සවන් දිය හැකි කෙටි, ධාරකයන් දෙදෙනෙකුගේ පොඩ්කාස්ට් ශෛලියේ සංවාදයක් බවට පත් කරන්න.",
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
        "audio_overviews_created": 0,
        "science_questions": 0,
        "history_questions": 0,
        "perfect_exams": 0,
        "night_sessions": 0,
        "morning_sessions": 0,
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
    "exam_history": [],
    "summary_history": [],
    "schedule_data": None,
}

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

def save_all_data(data):
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
    profile.setdefault("exam_history", [])
    profile.setdefault("summary_history", [])
    profile.setdefault("schedule_data", None)
    return profile

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
    check_advanced_badges(profile)

def check_advanced_badges(profile):
    g = profile["gamification"]
    a = profile["analytics"]
    
    if a.get("science_questions", 0) >= 50:
        award_badge(profile, "science_whiz")
    if a.get("math_problems_solved", 0) >= 50:
        award_badge(profile, "math_wizard")
    if a.get("history_questions", 0) >= 30:
        award_badge(profile, "history_hero")
    if g["streak"] >= 50:
        award_badge(profile, "streak_50")
    if g["streak"] >= 100:
        award_badge(profile, "streak_100")
    if a.get("night_sessions", 0) >= 10:
        award_badge(profile, "night_owl")
    if a.get("morning_sessions", 0) >= 10:
        award_badge(profile, "early_bird")
    if a.get("perfect_exams", 0) >= 5:
        award_badge(profile, "perfect_exam")
    if a.get("flashcards_reviewed", 0) >= 100:
        award_badge(profile, "flashcard_100")
    if a["pomodoro_sessions"] >= 100:
        award_badge(profile, "pomodoro_100")

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
        st.balloons()
        st.markdown(f"""
<div class="level-up-overlay">
<div class="level-up-card">
<div class="level-up-icon">🚀</div>
<div class="level-up-title">Level Up!</div>
<div class="level-up-sub">You're now Level {lvl}</div>
</div>
</div>
""", unsafe_allow_html=True)
    st.session_state["level_up_queue"] = []
    for badge_id in st.session_state.get("new_badges_queue", []):
        badge = BADGES.get(badge_id)
        if badge:
            st.markdown(f"""
<div class="badge-popup">
<span class="badge-popup-icon">🏅</span>
<span class="badge-popup-text">Badge unlocked: <strong>{badge['label']}</strong></span>
</div>
""", unsafe_allow_html=True)
    st.session_state["new_badges_queue"] = []

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

# AI SETUP (Groq — ultra-low latency inference)
GROQ_COMPLEX_MODEL = "llama-3.3-70b-versatile"   # exam generation, step-by-step tutoring, study schedules
GROQ_INSTANT_MODEL = "llama-3.1-8b-instant"      # flashcards, quick Q&A, floating chat
GROQ_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"  # only used when an image is attached, since the two models above are text-only
GROQ_TTS_MODEL = "playai-tts"
HOST_VOICES = {"Host1": "Fritz-PlayAI", "Host2": "Arista-PlayAI"}

def get_api_key():
    try:
        if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
            return st.secrets["GROQ_API_KEY"]
    except Exception:
        pass
    key = os.environ.get("GROQ_API_KEY")
    if key:
        return key
    return None

@st.cache_resource(show_spinner=False)
def get_client():
    api_key = get_api_key()
    if not api_key:
        return None
    return Groq(api_key=api_key)

def _image_to_data_url(image):
    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, format="JPEG")
    b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"

def get_ai_response(prompt, image=None, task="complex"):
    """task: 'complex' -> llama-3.3-70b-versatile, 'instant' -> llama-3.1-8b-instant.
    If an image is attached, the vision model is used automatically regardless of task."""
    client = get_client()
    if client is None:
        return "⚠️ **No Groq API key found.** Please add your API key to use AI features. The app will use offline mode for basic functionality."
    try:
        if image is not None:
            model = GROQ_VISION_MODEL
            messages = [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": _image_to_data_url(image)}},
                ],
            }]
        else:
            model = GROQ_INSTANT_MODEL if task == "instant" else GROQ_COMPLEX_MODEL
            messages = [{"role": "user", "content": prompt}]
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=4096,
        )
        return response.choices[0].message.content
    except Exception as e:
        err_text = str(e)
        if "401" in err_text or "invalid_api_key" in err_text.lower() or "authentication" in err_text.lower():
            return "⚠️ **API key authentication failed.** Please check your API key and try again. Using offline mode."
        return f"ERROR: Please check your internet connection ({err_text})"

def _tts_segment_bytes(client, text, voice):
    resp = client.audio.speech.create(
        model=GROQ_TTS_MODEL,
        voice=voice,
        input=text,
        response_format="wav",
    )
    read_fn = getattr(resp, "read", None)
    if callable(read_fn):
        return read_fn()
    return resp.content

def generate_audio_overview_wav(script_text):
    """Turns a 'Host1: ... / Host2: ...' script into a single stitched two-voice WAV
    using Groq's PlayAI TTS (one voice per host), replacing Gemini's native multi-speaker TTS."""
    client = get_client()
    if client is None:
        return None, "No Groq API key found"
    try:
        segments = []
        for line in script_text.splitlines():
            line = line.strip()
            if not line:
                continue
            match = re.match(r"^(Host1|Host2):\s*(.*)$", line)
            if not match:
                continue
            speaker, text = match.group(1), match.group(2).strip()
            if not text:
                continue
            voice = HOST_VOICES.get(speaker, "Fritz-PlayAI")
            segments.append(_tts_segment_bytes(client, text, voice))

        if not segments:
            return None, "No speaker lines found in script"

        params = None
        frames = []
        for seg in segments:
            with wave.open(io.BytesIO(seg), "rb") as wf:
                if params is None:
                    params = wf.getparams()
                frames.append(wf.readframes(wf.getnframes()))

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as out:
            out.setparams(params)
            for fr in frames:
                out.writeframes(fr)
        return buffer.getvalue(), None
    except Exception as e:
        return None, str(e)

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

# ==================== OFFLINE CONTENT MANAGER ====================

class OfflineContentManager:
    def __init__(self):
        self.offline_questions = self.load_offline_questions()
        self.offline_flashcards = self.load_offline_flashcards()
        self.offline_facts = self.load_offline_facts()
    
    def is_online(self):
        return get_client() is not None
    
    def load_offline_questions(self):
        return {
            "Science": {
                "Easy": [
                    {"question": "What is photosynthesis?", "A": "Process of making food", "B": "Plant reproduction", "C": "Water absorption", "D": "Nutrient transport", "correct": "A"},
                    {"question": "What is the chemical symbol for water?", "A": "H2O", "B": "CO2", "C": "NaCl", "D": "HCl", "correct": "A"},
                    {"question": "What organ pumps blood in the human body?", "A": "Liver", "B": "Heart", "C": "Lungs", "D": "Kidney", "correct": "B"},
                    {"question": "What is the process of cell division called?", "A": "Mitosis", "B": "Photosynthesis", "C": "Respiration", "D": "Digestion", "correct": "A"},
                    {"question": "What is the pH of pure water?", "A": "5", "B": "7", "C": "9", "D": "11", "correct": "B"},
                ],
                "Medium": [
                    {"question": "What is the law of conservation of mass?", "A": "Matter cannot be created or destroyed", "B": "Energy cannot be created", "C": "Atoms are indivisible", "D": "Molecules move randomly", "correct": "A"},
                    {"question": "What is the function of mitochondria?", "A": "Energy production", "B": "Protein synthesis", "C": "Cell division", "D": "Waste removal", "correct": "A"},
                ]
            },
            "Math": {
                "Easy": [
                    {"question": "What is 7 x 8?", "A": "48", "B": "56", "C": "64", "D": "72", "correct": "B"},
                    {"question": "What is the square root of 81?", "A": "7", "B": "8", "C": "9", "D": "10", "correct": "C"},
                    {"question": "What is 15 + 27?", "A": "42", "B": "52", "C": "32", "D": "62", "correct": "A"},
                ],
                "Medium": [
                    {"question": "What is the area of a triangle with base 6 and height 4?", "A": "12", "B": "24", "C": "48", "D": "10", "correct": "A"},
                    {"question": "What is 25% of 200?", "A": "25", "B": "50", "C": "75", "D": "100", "correct": "B"},
                ]
            },
            "History": {
                "Easy": [
                    {"question": "Who was the first president of Sri Lanka?", "A": "D.S. Senanayake", "B": "J.R. Jayawardene", "C": "S.W.R.D. Bandaranaike", "D": "R. Premadasa", "correct": "A"},
                    {"question": "In which year did Sri Lanka gain independence?", "A": "1946", "B": "1947", "C": "1948", "D": "1949", "correct": "C"},
                ]
            }
        }
    
    def load_offline_flashcards(self):
        return [
            {"front": "What is the largest planet?", "back": "Jupiter", "subject": "Science"},
            {"front": "What is 2 + 2?", "back": "4", "subject": "Math"},
            {"front": "What is the capital of Sri Lanka?", "back": "Sri Jayawardenepura Kotte", "subject": "Geography"},
            {"front": "What is photosynthesis?", "back": "Process where plants make food using sunlight", "subject": "Science"},
            {"front": "What is the atomic number of oxygen?", "back": "8", "subject": "Science"},
            {"front": "What is the formula for area of a circle?", "back": "πr²", "subject": "Math"},
            {"front": "Who invented the telephone?", "back": "Alexander Graham Bell", "subject": "History"},
            {"front": "What is the boiling point of water?", "back": "100°C", "subject": "Science"},
            {"front": "What is the largest ocean?", "back": "Pacific Ocean", "subject": "Geography"},
            {"front": "What is the square root of 144?", "back": "12", "subject": "Math"},
        ]
    
    def load_offline_facts(self):
        return [
            "💡 The average human brain has about 86 billion neurons.",
            "💡 A day on Venus is longer than its year.",
            "💡 Bananas are technically berries, while strawberries are not.",
            "💡 The world's oldest known living tree is over 5,000 years old.",
            "💡 The human body contains about 60% water.",
            "💡 The speed of light is approximately 299,792,458 meters per second.",
            "💡 Antarctica is the largest desert on Earth.",
            "💡 The Great Wall of China is over 13,000 miles long.",
            "💡 A group of flamingos is called a 'flamboyance'.",
            "💡 The Eiffel Tower can grow up to 6 inches taller in summer.",
        ]
    
    def get_offline_quiz(self, subject, difficulty):
        subject_data = self.offline_questions.get(subject, {})
        questions = subject_data.get(difficulty, subject_data.get("Easy", []))
        return questions[:5]
    
    def get_offline_fact(self, index=None):
        if index is None:
            index = random.randint(0, len(self.offline_facts) - 1)
        return self.offline_facts[index % len(self.offline_facts)]

# ==================== EXAM EXAMINER FEATURE ====================

def show_exam_examiner():
    st.header("🤖 Interactive AI Exam Examiner Mode")
    st.caption("Answer open-ended questions and get detailed feedback from an AI examiner")
    
    profile = current_profile()
    
    col1, col2 = st.columns(2)
    with col1:
        subject = st.text_input("Subject:", value="Science", key="exam_subject")
        topic = st.text_input("Topic/Chapter:", key="exam_topic")
        num_questions = st.slider("Number of questions:", 1, 5, 3, key="exam_count")
    with col2:
        difficulty = st.select_slider("Difficulty:", ["Beginner", "Intermediate", "Advanced"], value="Intermediate", key="exam_difficulty")
        exam_type = st.selectbox("Exam Type:", ["Theory", "Application", "Mixed"], key="exam_type")
    
    exam_file = st.file_uploader("Upload notes/PDF to base questions on:", type=["pdf", "txt"], key="exam_upload")
    
    if st.button("📝 Generate Exam Questions", use_container_width=True):
        if topic or exam_file:
            with st.spinner("AI is generating exam questions..."):
                content = topic or ""
                if exam_file:
                    if exam_file.name.endswith(".pdf"):
                        content += "\n" + extract_text_from_pdf(exam_file)
                    else:
                        content += "\n" + exam_file.read().decode('utf-8')
                
                offline_manager = OfflineContentManager()
                if offline_manager.is_online():
                    prompt = build_exam_prompt(subject, topic, difficulty, num_questions, exam_type, content)
                    raw_response = get_ai_response(prompt, task="complex")
                    try:
                        exam_data = parse_exam_json(raw_response)
                        st.session_state.current_exam = exam_data
                        st.session_state.exam_subject = subject
                        st.session_state.exam_answers = {}
                        st.session_state.exam_graded = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not generate exam questions: {e}")
                        offline_questions = offline_manager.get_offline_quiz(subject, difficulty)
                        if offline_questions:
                            st.session_state.current_exam = [{"question": q["question"], "marks": 5, "rubric": "Based on standard marking", "topic": subject} for q in offline_questions]
                            st.session_state.exam_subject = subject
                            st.session_state.exam_answers = {}
                            st.session_state.exam_graded = False
                            st.info("Using offline questions as fallback")
                            st.rerun()
                else:
                    offline_questions = offline_manager.get_offline_quiz(subject, difficulty)
                    if offline_questions:
                        st.session_state.current_exam = [{"question": q["question"], "marks": 5, "rubric": "Based on standard marking", "topic": subject} for q in offline_questions]
                        st.session_state.exam_subject = subject
                        st.session_state.exam_answers = {}
                        st.session_state.exam_graded = False
                        st.info("📶 Offline Mode - Using pre-loaded questions")
                        st.rerun()
                    else:
                        st.warning("No offline questions available for this subject. Try 'Science' or 'Math'.")
        else:
            st.warning("Please provide a topic or upload notes")
    
    if st.session_state.get("current_exam") and not st.session_state.get("exam_graded", False):
        exam = st.session_state.current_exam
        st.write("---")
        st.write("### ✍️ Answer the following questions:")
        st.caption("💡 Be thorough - the AI examiner will grade based on completeness, accuracy, and structure")
        
        for idx, q in enumerate(exam):
            st.markdown(f"#### Question {idx+1}: {q.get('question', '')}")
            st.caption(f"*Marks: {q.get('marks', 5)} | Topic: {q.get('topic', 'General')}*")
            
            if q.get('rubric'):
                with st.expander("📋 View Marking Rubric"):
                    st.markdown(q['rubric'])
            
            answer = st.text_area(f"Your Answer (Q{idx+1}):", key=f"exam_ans_{idx}", height=150)
            st.session_state.exam_answers[idx] = answer
        
        if st.button("📊 Submit for Grading", use_container_width=True, type="primary"):
            if all(ans.strip() for ans in st.session_state.exam_answers.values()):
                st.session_state.exam_graded = True
                st.rerun()
            else:
                st.warning("Please answer all questions before submitting")
    
    if st.session_state.get("exam_graded", False):
        exam = st.session_state.current_exam
        total_marks = 0
        earned_marks = 0
        
        st.write("---")
        st.write("### 📊 Grading Results")
        
        for idx, q in enumerate(exam):
            student_answer = st.session_state.exam_answers.get(idx, "")
            
            with st.expander(f"📝 Question {idx+1} Feedback", expanded=(idx==0)):
                offline_manager = OfflineContentManager()
                if offline_manager.is_online():
                    with st.spinner(f"Grading question {idx+1}..."):
                        feedback = get_exam_feedback(q, student_answer, q.get('marks', 5))
                        
                        try:
                            feedback_data = parse_feedback_json(feedback)
                            marks_awarded = feedback_data.get('marks_awarded', 0)
                            max_marks = feedback_data.get('max_marks', q.get('marks', 5))
                            total_marks += max_marks
                            earned_marks += marks_awarded
                            
                            st.markdown(f"**Marks: {marks_awarded}/{max_marks}**")
                            st.progress(marks_awarded/max_marks if max_marks > 0 else 0)
                            
                            st.markdown("#### 📋 Examiner Feedback")
                            st.markdown(feedback_data.get('feedback', ''))
                            
                            st.markdown("#### 💡 Suggested Improvement")
                            st.markdown(feedback_data.get('improvement', ''))
                            
                            st.markdown("#### 🎯 Model Answer Key Points")
                            for point in feedback_data.get('model_answer', []):
                                st.markdown(f"- {point}")
                        except:
                            st.write(feedback)
                else:
                    word_count = len(student_answer.split())
                    marks_awarded = min(q.get('marks', 5), max(0, word_count // 10))
                    total_marks += q.get('marks', 5)
                    earned_marks += marks_awarded
                    st.markdown(f"**Marks: {marks_awarded}/{q.get('marks', 5)}**")
                    st.info("📶 Offline Mode - Basic grading based on answer length")
        
        st.write("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📊 Total Score", f"{earned_marks}/{total_marks}")
        with col2:
            percentage = int((earned_marks/total_marks)*100) if total_marks > 0 else 0
            st.metric("🎯 Percentage", f"{percentage}%")
        with col3:
            grade = get_grade(percentage)
            st.metric("🏆 Grade", grade)
        
        profile = current_profile()
        xp_earned = min(20, int(earned_marks / max(1, total_marks) * 20))
        add_xp(profile, xp_earned, "exam_completed")
        
        profile.setdefault("exam_history", [])
        profile["exam_history"].append({
            "date": str(date.today()),
            "subject": st.session_state.exam_subject,
            "score": earned_marks,
            "total": total_marks,
            "questions": len(exam)
        })
        
        if percentage >= 100:
            profile["analytics"]["perfect_exams"] = profile["analytics"].get("perfect_exams", 0) + 1
        
        save_current()
        
        if percentage >= 90:
            st.balloons()
            st.success("🌟 Outstanding performance! You're an exam champion!")
        elif percentage >= 70:
            st.success("📚 Good work! Keep practicing to reach higher!")
        elif percentage >= 50:
            st.info("💪 Keep studying! Review the feedback above to improve.")
        else:
            st.warning("📖 Time to review! Use the feedback to understand where you can improve.")
        
        render_gamification_popups()
        
        if st.button("🔄 Start New Exam"):
            st.session_state.pop("current_exam", None)
            st.session_state.exam_graded = False
            st.session_state.exam_answers = {}
            st.rerun()

def build_exam_prompt(subject, topic, difficulty, num_questions, exam_type, content):
    user_info = current_profile()
    return f"""
    {_who_line()} {_syllabus_notice('open-ended exam questions')}

    You are an AI examiner. Create {num_questions} open-ended exam questions for this student studying {subject}.
    
    Topic: {topic}
    Difficulty: {difficulty}
    Exam Type: {exam_type}
    
    IMPORTANT RULES:
    1. Each question must be challenging but appropriate for the student's exact grade level and age
    2. Questions must test understanding, not just memorization
    3. Include a detailed marking rubric for each question
    4. Questions, terminology, and expected depth MUST strictly match the Sri Lankan local school syllabus for this student's grade — do not include concepts taught in later grades
    
    Content to base questions on: {content[:2000]}
    
    Return EXACTLY a JSON array with {num_questions} objects, each with:
    - "question": the exam question text
    - "topic": the specific subtopic
    - "marks": number of marks (5-10)
    - "rubric": detailed marking criteria as a string
    - "expected_key_points": list of key points expected in a good answer
    
    Format as a raw JSON array only, no additional text or explanation.
    """

def get_exam_feedback(question, student_answer, max_marks):
    prompt = f"""
    {_who_line()} {_syllabus_notice('exam answer feedback')}

    You are an AI examiner grading an exam answer.
    
    Question: {question.get('question', '')}
    Expected Key Points: {question.get('expected_key_points', [])}
    Marking Rubric: {question.get('rubric', '')}
    
    Student Answer: {student_answer[:1000]}
    Maximum Marks: {max_marks}
    
    Provide detailed feedback including:
    1. Marks awarded (integer 0-{max_marks})
    2. Detailed feedback explaining what was good and what was missing
    3. Specific improvements the student can make
    4. A model answer outline with key points that should have been covered
    
    Return as a JSON object with keys: "marks_awarded", "max_marks", "feedback", "improvement", "model_answer" (array)
    """
    return get_ai_response(prompt, task="complex")

def parse_feedback_json(raw):
    try:
        cleaned = raw.strip()
        cleaned = re.sub(r"^```json|```$", "", cleaned)
        return json.loads(cleaned)
    except:
        return {"marks_awarded": 0, "max_marks": 5, "feedback": raw, "improvement": "Unable to parse feedback", "model_answer": []}

def parse_exam_json(raw):
    cleaned = raw.strip()
    cleaned = re.sub(r"^```json|```$", "", cleaned)
    return json.loads(cleaned)

def get_grade(percentage):
    if percentage >= 90: return "A+ 🏆"
    elif percentage >= 80: return "A 📚"
    elif percentage >= 70: return "B 💪"
    elif percentage >= 60: return "C 📖"
    elif percentage >= 50: return "D 🔄"
    else: return "F 📝"

# ==================== STUDY PACK EXPORTER ====================

def show_study_pack_exporter():
    st.header("📑 Automated Study Pack Exporter")
    st.caption("Export your study materials as a printable PDF or Anki-compatible package")
    
    profile = current_profile()
    
    export_type = st.selectbox(
        "Export Format:",
        ["📄 PDF Study Pack", "🃏 Anki Package (.apkg)", "📋 Combined Notes"]
    )
    
    st.subheader("📦 Select Materials to Include")
    
    col1, col2 = st.columns(2)
    with col1:
        include_flashcards = st.checkbox("📝 Flashcards", value=True)
        include_notes = st.checkbox("📒 Scribble Notes", value=True)
        include_quiz_results = st.checkbox("📊 Quiz Results", value=True)
    
    with col2:
        include_exam_results = st.checkbox("📝 Exam Results", value=True)
        include_summaries = st.checkbox("📋 Summaries", value=True)
        include_schedule = st.checkbox("📅 Study Schedule", value=True)
    
    all_subjects = set()
    for card in profile.get("flashcards", []):
        all_subjects.add(card.get("subject", "General"))
    subject_filter = st.multiselect("Filter by Subject:", sorted(list(all_subjects)), key="export_subjects")
    
    if st.button("📥 Generate Study Pack", use_container_width=True, type="primary"):
        with st.spinner("Generating your study pack..."):
            content = build_study_pack_content(
                profile,
                include_flashcards,
                include_notes,
                include_quiz_results,
                include_exam_results,
                include_summaries,
                include_schedule,
                subject_filter
            )
            
            if export_type.startswith("📄"):
                try:
                    pdf_bytes = generate_study_pdf(content, profile)
                    st.download_button(
                        "⬇️ Download PDF Study Pack",
                        data=pdf_bytes,
                        file_name=f"study_pack_{date.today()}.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.warning(f"PDF generation failed: {e}")
                    st.download_button(
                        "⬇️ Download as Text (Fallback)",
                        data=content,
                        file_name=f"study_pack_{date.today()}.txt",
                        mime="text/plain"
                    )
            elif export_type.startswith("🃏"):
                apkg_bytes = generate_anki_package(profile, subject_filter)
                if apkg_bytes:
                    st.download_button(
                        "⬇️ Download Anki Package",
                        data=apkg_bytes,
                        file_name=f"flashcards_{date.today()}.apkg",
                        mime="application/zip"
                    )
            else:
                st.text_area("📋 Combined Notes Preview", value=content, height=400)
                st.download_button(
                    "⬇️ Download as Text",
                    data=content,
                    file_name=f"study_notes_{date.today()}.txt",
                    mime="text/plain"
                )
            
            add_xp(profile, XP_REWARDS["study_pack_exported"], "study_pack_exported")
            save_current()
            render_gamification_popups()

def build_study_pack_content(profile, include_flashcards, include_notes, include_quiz_results, 
                            include_exam_results, include_summaries, include_schedule, subject_filter):
    content = f"""
    ========================================
    STUDY PACK - {date.today()}
    Student: {profile.get('user_name', '')} | Grade: {profile.get('user_grade', '')}
    ========================================
    
    """
    
    if include_flashcards and profile.get("flashcards"):
        content += "\n📝 FLASHCARDS\n" + "-" * 40 + "\n"
        for card in profile["flashcards"]:
            subject = card.get("subject", "General")
            if subject_filter and subject not in subject_filter:
                continue
            content += f"\nSubject: {subject}\nQ: {card.get('front', '')}\nA: {card.get('back', '')}\nDue: {card.get('due_date', '')}\n" + "-" * 20 + "\n"
    
    if include_notes and profile.get("scribble_notes"):
        content += "\n📒 SCRIBBLE NOTES\n" + "-" * 40 + "\n"
        for i, note in enumerate(profile["scribble_notes"], 1):
            content += f"\nNote {i}:\n{note}\n" + "-" * 20 + "\n"
    
    if include_quiz_results and profile.get("quiz_history"):
        content += "\n📊 QUIZ HISTORY\n" + "-" * 40 + "\n"
        for entry in profile["quiz_history"]:
            content += f"\n{entry.get('date', '')} - {entry.get('subject', '')}\nScore: {entry.get('score', 0)}/{entry.get('total', 0)}\n" + "-" * 20 + "\n"
    
    if include_exam_results and profile.get("exam_history"):
        content += "\n📝 EXAM HISTORY\n" + "-" * 40 + "\n"
        for entry in profile["exam_history"]:
            content += f"\n{entry.get('date', '')} - {entry.get('subject', '')}\nScore: {entry.get('score', 0)}/{entry.get('total', 0)}\nQuestions: {entry.get('questions', 0)}\n" + "-" * 20 + "\n"
    
    if include_summaries and profile.get("summary_history"):
        content += "\n📋 NOTE SUMMARIES\n" + "-" * 40 + "\n"
        for summary in profile.get("summary_history", []):
            content += f"\n{summary.get('date', '')}\n{summary.get('content', '')}\n" + "-" * 20 + "\n"
    
    if include_schedule and profile.get("schedule_data"):
        content += "\n📅 STUDY SCHEDULE\n" + "-" * 40 + "\n"
        schedule = profile["schedule_data"]
        content += f"Subject: {schedule.get('subject', '')}\nExam Date: {schedule.get('exam_date', '')}\n"
        for day in schedule.get('days', [])[:7]:
            content += f"\n{day.get('date', '')}: {', '.join(day.get('topics', []))}\n"
    
    content += "\n" + "=" * 50 + "\nEND OF STUDY PACK\n"
    content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    return content

def generate_study_pdf(content, profile):
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.units import inch
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, alignment=TA_CENTER, spaceAfter=30)
        heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'], fontSize=18, spaceAfter=12, textColor='#1a1a2e')
        normal_style = ParagraphStyle('CustomNormal', parent=styles['Normal'], fontSize=11, spaceAfter=6, leading=14)
        
        story = [Paragraph("📚 Study Pack", title_style), Spacer(1, 0.2*inch)]
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        lines = content.split('\n')
        for line in lines:
            if line.strip() and not line.startswith('='):
                if any(line.startswith(prefix) for prefix in ['📝', '📒', '📊', '📋', '📅']):
                    story.append(Paragraph(line, heading_style))
                else:
                    story.append(Paragraph(line.replace('-', '•'), normal_style))
        
        doc.build(story)
        return buffer.getvalue()
    except ImportError:
        return content.encode('utf-8')

def generate_anki_package(profile, subject_filter):
    try:
        import zipfile
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            collection = {"decks": {}, "cards": [], "notes": [], "models": {}}
            model_id = 1234567890
            collection["models"] = {
                str(model_id): {
                    "id": model_id,
                    "name": "Basic",
                    "flds": [{"name": "Front"}, {"name": "Back"}],
                    "tmpls": [{"name": "Card 1", "qfmt": "{{Front}}", "afmt": "{{FrontSide}}\n\n<hr id=answer>\n\n{{Back}}"}],
                    "css": ".card { font-family: arial; font-size: 20px; text-align: center; color: black; background-color: white; }"
                }
            }
            deck_id = 987654321
            collection["decks"][str(deck_id)] = {"id": deck_id, "name": "Study Organizer Flashcards"}
            note_id_counter = 1
            for card in profile.get("flashcards", []):
                subject = card.get("subject", "General")
                if subject_filter and subject not in subject_filter:
                    continue
                note = {
                    "id": note_id_counter,
                    "mid": model_id,
                    "flds": [f"{subject}: {card.get('front', '')}", card.get('back', '')],
                    "tags": [subject],
                    "mod": int(time.time())
                }
                collection["notes"].append(note)
                collection["cards"].append({
                    "id": note_id_counter * 10,
                    "nid": note_id_counter,
                    "did": deck_id,
                    "ord": 0,
                    "mod": int(time.time()),
                    "type": 0,
                    "queue": 0,
                    "due": 0,
                    "ivl": 0,
                    "factor": 0,
                    "lapses": 0
                })
                note_id_counter += 1
            zip_file.writestr("collection.json", json.dumps(collection))
        return buffer.getvalue()
    except Exception as e:
        st.error(f"Could not generate Anki package: {e}")
        return None

# ==================== STUDY SCHEDULE BUILDER ====================

def show_study_schedule_builder():
    st.header("📅 AI Adaptive Study Schedule Builder")
    st.caption("Enter your exam date and chapters - get a personalized study plan")
    
    profile = current_profile()
    
    col1, col2 = st.columns(2)
    with col1:
        exam_subject = st.text_input("Subject:", value="Science", key="schedule_subject")
        exam_date = st.date_input("Exam Date:", min_value=date.today() + timedelta(days=7), key="exam_date")
    with col2:
        chapters = st.text_area("Chapters to cover (one per line):", height=100, key="schedule_chapters")
        daily_study_hours = st.slider("Daily Study Hours Available:", 0.5, 4.0, 1.5, 0.5, key="study_hours")

    schedule_file = st.file_uploader("Upload syllabus/notes PDF (optional):", type=["pdf", "txt"], key="schedule_upload")
    schedule_pdf_text = ""
    if schedule_file is not None:
        if schedule_file.name.lower().endswith(".pdf"):
            schedule_pdf_text = extract_text_from_pdf(schedule_file)
            st.success("PDF loaded successfully!")
        else:
            schedule_pdf_text = schedule_file.read().decode("utf-8", errors="ignore")

    if st.button("📅 Generate Study Schedule", use_container_width=True, type="primary"):
        if exam_subject and chapters and exam_date > date.today():
            with st.spinner("AI is creating your personalized study schedule..."):
                schedule_data = generate_study_schedule(
                    exam_subject, 
                    chapters.split('\n'), 
                    exam_date, 
                    daily_study_hours,
                    profile,
                    schedule_pdf_text
                )
                
                if schedule_data:
                    profile["schedule_data"] = schedule_data
                    st.session_state.schedule_data = schedule_data
                    st.session_state.schedule_generated = True
                    add_xp(profile, XP_REWARDS["schedule_created"], "schedule_created")
                    save_current()
                    st.rerun()
        else:
            st.warning("Please fill in all fields and ensure the exam date is in the future")
    
    if st.session_state.get("schedule_generated", False) or profile.get("schedule_data"):
        schedule = st.session_state.get("schedule_data") or profile.get("schedule_data")
        if schedule:
            days_until_exam = (schedule['exam_date'] - date.today()).days if isinstance(schedule.get('exam_date'), date) else 0
            
            st.write("---")
            st.subheader(f"📚 Your Study Plan for {schedule['subject']}")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📅 Days Until Exam", days_until_exam)
            with col2:
                st.metric("📖 Chapters", len(schedule.get('chapters', [])))
            with col3:
                total_hours = sum(day.get('study_hours', 0) for day in schedule.get('days', []))
                st.metric("⏱️ Total Study Hours", f"{total_hours:.1f}h")
            with col4:
                st.metric("🔄 Reviews", schedule.get('total_reviews', 0))
            
            st.subheader("📋 Day-by-Day Study Plan")
            
            for i, day in enumerate(schedule.get('days', [])):
                with st.expander(f"📅 {day.get('date', '')} - {day.get('day_name', '')}", expanded=(i < 3)):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**Topics:** {', '.join(day.get('topics', []))}")
                        if day.get('review_topics'):
                            st.markdown(f"🔄 **Review:** {', '.join(day.get('review_topics', []))}")
                        st.markdown("**Study Tasks:**")
                        for task in day.get('tasks', []):
                            st.markdown(f"- {task}")
                    with col2:
                        st.metric("⏱️ Study", f"{day.get('study_hours', 0):.1f}h")
                        st.metric("🎯 Goals", day.get('quiz_goal', 0))
                        if day.get('completed', False):
                            st.success("✅ Completed")
                        else:
                            st.info("⏳ Pending")
            
            st.subheader("🎯 Quiz Milestones")
            for milestone in schedule.get('milestones', []):
                st.markdown(f"**Day {milestone.get('day', 0)}:** {milestone.get('quiz_subject', '')} - {milestone.get('chapters', '')}")
                st.caption(f"{milestone.get('description', '')}")
            
            render_gamification_popups()
            
            if st.button("📤 Export Schedule"):
                schedule_text = format_schedule_to_text(schedule)
                st.download_button(
                    "⬇️ Download Schedule",
                    data=schedule_text,
                    file_name=f"study_schedule_{date.today()}.txt",
                    mime="text/plain"
                )

def generate_study_schedule(subject, chapters, exam_date, daily_hours, profile, reference_content=""):
    try:
        offline_manager = OfflineContentManager()
        if not offline_manager.is_online():
            return generate_offline_schedule(subject, chapters, exam_date, daily_hours)
        
        days_until = (exam_date - date.today()).days
        user_info = current_profile()
        
        prompt = f"""
        {_who_line()} {_syllabus_notice('a study schedule')}

        Create a study schedule for this student studying {subject}. Pacing, topic breakdown, and difficulty MUST strictly match the Sri Lankan local school syllabus for their grade.
        
        Exam Date: {exam_date}
        Days Until Exam: {days_until}
        Daily Study Hours: {daily_hours}
        Chapters to Cover: {chapters}
        {f"Reference material uploaded by the student (base the topic breakdown on this where relevant): {reference_content[:3000]}" if reference_content else ""}
        
        Create an adaptive schedule with:
        1. Spaced repetition reviews
        2. Pomodoro session recommendations (25 min sessions)
        3. Daily quiz milestones
        4. Progressive difficulty increase
        
        Return as a JSON object with:
        - "subject": the subject name
        - "exam_date": the exam date as string (YYYY-MM-DD)
        - "chapters": list of chapters
        - "days": array of day objects, each with:
          - "date": date string (YYYY-MM-DD)
          - "day_name": "Monday", etc.
          - "topics": list of topics to study
          - "review_topics": list of topics to review
          - "study_hours": number
          - "tasks": list of specific tasks
          - "quiz_goal": number of quiz questions
          - "completed": false
        - "milestones": array of milestone objects
        - "total_reviews": number of planned reviews
        """
        
        response = get_ai_response(prompt, task="complex")
        cleaned = re.sub(r"^```json|```$", "", response.strip())
        schedule = json.loads(cleaned)
        
        if isinstance(schedule.get('exam_date'), str):
            schedule['exam_date'] = datetime.strptime(schedule['exam_date'], '%Y-%m-%d').date()
        
        return schedule
    except Exception as e:
        st.error(f"Could not generate schedule: {e}")
        return generate_offline_schedule(subject, chapters, exam_date, daily_hours)

def generate_offline_schedule(subject, chapters, exam_date, daily_hours):
    days_until = (exam_date - date.today()).days
    if days_until <= 0:
        return None
    
    chapter_list = [c.strip() for c in chapters if c.strip()]
    if not chapter_list:
        chapter_list = ["Chapter 1", "Chapter 2", "Chapter 3"]
    
    schedule = {
        "subject": subject,
        "exam_date": exam_date,
        "chapters": chapter_list,
        "days": [],
        "milestones": [],
        "total_reviews": 0
    }
    
    chapters_per_day = max(1, len(chapter_list) // min(days_until, 7))
    
    for i in range(min(days_until, 14)):
        day_date = date.today() + timedelta(days=i)
        topics = []
        start_idx = i * chapters_per_day
        end_idx = min(start_idx + chapters_per_day, len(chapter_list))
        if start_idx < len(chapter_list):
            topics = chapter_list[start_idx:end_idx]
        else:
            topics = ["Review Day"]
        
        review_topics = []
        if i > 0 and i % 3 == 0:
            prev_idx = max(0, (i - 1) * chapters_per_day)
            prev_end = min(prev_idx + chapters_per_day, len(chapter_list))
            review_topics = chapter_list[prev_idx:prev_end]
        
        day = {
            "date": str(day_date),
            "day_name": day_date.strftime("%A"),
            "topics": topics,
            "review_topics": review_topics,
            "study_hours": daily_hours,
            "tasks": [f"Study {topic}" for topic in topics],
            "quiz_goal": 5 if len(topics) > 0 else 0,
            "completed": False
        }
        schedule["days"].append(day)
        
        if i % 3 == 0 and i > 0:
            schedule["milestones"].append({
                "day": i,
                "quiz_subject": subject,
                "chapters": ", ".join(topics),
                "description": f"Quiz on {', '.join(topics)}"
            })
    
    schedule["total_reviews"] = len([d for d in schedule["days"] if d.get('review_topics')])
    return schedule

def format_schedule_to_text(schedule):
    text = f"""
    ========================================
    STUDY SCHEDULE
    ========================================
    
    Subject: {schedule.get('subject', '')}
    Exam Date: {schedule.get('exam_date', '')}
    Created: {datetime.now().strftime('%Y-%m-%d %H:%M')}
    
    ========================================
    DAILY PLAN
    ========================================
    
    """
    for day in schedule.get('days', []):
        text += f"""
    📅 {day.get('date', '')} ({day.get('day_name', '')})
    ----------------------------------------
    Study Hours: {day.get('study_hours', 0)}h
    Topics: {', '.join(day.get('topics', []))}
    
    """
        if day.get('review_topics'):
            text += f"Review: {', '.join(day.get('review_topics', []))}\n"
        text += "\nTasks:\n"
        for task in day.get('tasks', []):
            text += f"  - {task}\n"
        text += "\n"
    return text

# ==================== AMBIENT FOCUS SOUNDSCAPES ====================

def show_ambient_sound_player():
    st.subheader("🎵 Ambient Focus Soundscapes")
    st.caption("Background audio to help maintain deep focus during study sessions")
    
    sound_options = {
        "🌧️ Rain": "rain",
        "🎵 Lo-Fi Beats": "lofi", 
        "🌊 Ocean Waves": "ocean",
        "🔥 Fire Crackling": "fire",
        "🌿 Forest": "forest",
        "🤫 White Noise": "white_noise"
    }
    
    col1, col2 = st.columns([2, 1])
    with col1:
        selected_sound = st.selectbox("Select a soundscape:", list(sound_options.keys()))
    with col2:
        volume = st.slider("Volume:", 0, 100, 50)
    
    sound_data = generate_ambient_sound(sound_options[selected_sound], volume)
    
    if sound_data:
        st.markdown(f"""
        <div style="background: var(--card-bg); border-radius: 14px; padding: 16px; margin: 10px 0; border: 1px solid var(--border);">
            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 1.5rem;">{selected_sound.split()[0]}</span>
                <audio controls style="flex: 1; height: 40px; background: transparent; border-radius: 20px;">
                    <source src="data:audio/wav;base64,{sound_data}" type="audio/wav">
                </audio>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 8px; font-size: 0.8rem; color: var(--muted);">
                <span>🎯 Focus Mode</span>
                <span>💡 Helps maintain concentration</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("🎧 Soundscape player ready - select a sound and press play")

def generate_ambient_sound(sound_type, volume):
    try:
        sample_rate = 22050
        duration = 180
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        if sound_type == "rain":
            noise = np.random.normal(0, 0.5, len(t))
            filtered = np.convolve(noise, np.exp(-np.linspace(0, 0.1, 100)), mode='same')
            filtered = filtered / np.max(np.abs(filtered))
            audio = filtered * (volume / 100) * 0.5
            
        elif sound_type == "lofi":
            beat = np.sin(2 * np.pi * 1.5 * t) * 0.25
            melody = np.sin(2 * np.pi * 220 * t) * 0.15 + np.sin(2 * np.pi * 277 * t) * 0.1
            melody += np.sin(2 * np.pi * 330 * t) * 0.08
            crackle = np.random.normal(0, 0.02, len(t))
            audio = (beat + melody + crackle) * (volume / 100)
            
        elif sound_type == "ocean":
            wave1 = np.sin(2 * np.pi * 0.2 * t) * np.exp(-t * 0.001)
            wave2 = np.sin(2 * np.pi * 0.15 * t + 1.2) * np.exp(-t * 0.002)
            noise = np.random.normal(0, 0.15, len(t)) * np.exp(-t * 0.003)
            audio = (wave1 * 0.3 + wave2 * 0.3 + noise * 0.4) * (volume / 100)
            
        elif sound_type == "fire":
            crackles = np.random.exponential(0.02, len(t))
            crackle_envelope = np.exp(-t * 0.01) * 0.3 + 0.1
            rumble = np.sin(2 * np.pi * 0.5 * t) * 0.05
            audio = (crackles * crackle_envelope + rumble) * (volume / 100)
            
        elif sound_type == "forest":
            wind = np.random.normal(0, 0.1, len(t)) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.01 * t))
            chirp = np.sin(2 * np.pi * 800 * t) * np.exp(-((t % 2) * 10)) * 0.05
            audio = (wind + chirp) * (volume / 100)
            
        else:
            audio = np.random.normal(0, 0.3, len(t)) * (volume / 100)
        
        audio = np.clip(audio, -1, 1)
        audio_int16 = (audio * 32767).astype(np.int16)
        
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_int16.tobytes())
        
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    except Exception as e:
        return None

# ==================== MCQUIZ WITH OFFLINE SUPPORT ====================

def show_mcq_quiz_with_offline():
    st.header(t("❓ AI Anti-Cheat MCQ Quiz"))
    st.caption(t("Test your knowledge with questions based on the Sri Lankan Syllabus."))
    
    offline_manager = OfflineContentManager()
    is_online = offline_manager.is_online()
    
    if not is_online:
        st.warning("📶 Offline Mode Active - Using pre-loaded questions")
    else:
        st.info("🌐 Online Mode - AI generating questions")
    
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
            with st.spinner(f"{num_questions} questions are being created..."):
                if is_online:
                    combined_context = (topic or "") + "\n" + pdf_text
                    prompt = build_quiz_prompt(
                        subject, difficulty, num_questions,
                        combined_context if combined_context.strip() else "see attached image"
                    )
                    raw_json = get_ai_response(prompt, image=q_img, task="complex")
                    try:
                        st.session_state.quiz_list = parse_quiz_json(raw_json)
                        st.session_state.quiz_subject = subject
                        st.session_state.quiz_answers = {}
                        st.session_state.quiz_checked = False
                        st.success("✅ Questions generated successfully!")
                    except Exception as e:
                        st.error(f"AI generation failed. Switching to offline mode...")
                        st.session_state.quiz_list = offline_manager.get_offline_quiz(subject, difficulty)
                        st.session_state.quiz_subject = subject
                        st.session_state.quiz_answers = {}
                        st.session_state.quiz_checked = False
                else:
                    st.session_state.quiz_list = offline_manager.get_offline_quiz(subject, difficulty)
                    st.session_state.quiz_subject = subject
                    st.session_state.quiz_answers = {}
                    st.session_state.quiz_checked = False
                    if st.session_state.quiz_list:
                        st.info("📶 Using offline questions")
                    else:
                        st.warning("No offline questions available. Try 'Science', 'Math', or 'History'.")
        else:
            st.warning("Please give a topic or upload a file.")
    
    if "quiz_list" in st.session_state and st.session_state.quiz_list:
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
            
            subject_lower = st.session_state.quiz_subject.lower()
            if "science" in subject_lower:
                profile["analytics"]["science_questions"] = profile["analytics"].get("science_questions", 0) + total_qs
            elif "history" in subject_lower:
                profile["analytics"]["history_questions"] = profile["analytics"].get("history_questions", 0) + total_qs
            
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
                render_quiz_result_card(idx, q, u_ans)

            total_qs = len(st.session_state.quiz_list)
            st.markdown(f"## 🏆 Total Score: **{score} / {total_qs}**")
            if score == total_qs:
                st.balloons()
                st.success("Perfect! All questions are correct! 🥳")
            render_gamification_popups()

# ==================== POMODORO WITH SOUNDSCAPES ====================

def show_pomodoro_with_soundscapes():
    st.header(t("⏱️ Pomodoro & Goal Progress Tracker"))
    
    tab1, tab2 = st.tabs(["⏱️ Timer", "🎵 Soundscapes"])
    
    with tab1:
        col1, col2 = st.columns(2)
        profile = current_profile()

        with col1:
            st.subheader(t("🤖 AI Auto Task Generator"))
            goal = st.text_input("What is your goal today?")
            if st.button("Make Your Task List 📋"):
                if goal:
                    with st.spinner("Your task list is being created by AI..."):
                        offline_manager = OfflineContentManager()
                        if offline_manager.is_online():
                            prompt = build_goal_tasks_prompt(goal)
                            ai_tasks = get_ai_response(prompt, task="instant").split("\n")
                        else:
                            ai_tasks = [
                                f"Break down {goal} into parts",
                                f"Research {goal}",
                                f"Practice {goal}",
                                f"Review {goal} knowledge"
                            ]
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
    
    with tab2:
        show_ambient_sound_player()

def build_goal_tasks_prompt(goal):
    return f"{_who_line()} {_syllabus_notice('a study goal task breakdown')} Break down this study goal into 4 short actionable tasks appropriate for this student's grade level, using the Sri Lankan school syllabus for context. Provide only the tasks, without numbers, one per line:\n{goal}"

# ==================== THEME SYSTEM ====================

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

def apply_theme(theme=None, with_nav=True):
    t = GLASS_TOKENS
    root_vars = "".join(f"--{k}: {v};" for k, v in t.items())
    nav_padding_css = '[data-testid="stMainBlockContainer"] { padding-right: 280px !important; }' if with_nav else ""

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

    .profile-card, .streak-pill, .pomo-ring-inner, .flash-face,
    div[data-testid="stMetric"], div[data-testid="stExpander"],
    div[data-testid="stForm"] {{
        background: var(--card-bg) !important;
        backdrop-filter: blur(22px) saturate(180%);
        -webkit-backdrop-filter: blur(22px) saturate(180%);
        border: 1px solid var(--border) !important;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.18), var(--shadow);
    }}

    div[data-testid="stMetric"] {{
        border-radius: 16px !important;
        padding: 14px 16px 16px 16px !important;
        min-height: 92px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }}
    div[data-testid="stMetric"] [data-testid="stMetricLabel"] {{
        overflow: visible !important;
        height: auto !important;
    }}
    div[data-testid="stMetric"] [data-testid="stMetricLabel"] p {{
        white-space: normal !important;
        overflow: visible !important;
        text-overflow: unset !important;
        line-height: 1.25 !important;
        font-size: 0.82rem !important;
        color: var(--muted) !important;
    }}
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
        font-size: 1.7rem !important;
        margin-top: 2px;
    }}

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

    div[data-testid="stSlider"] [data-baseweb="slider"] > div:nth-child(2) {{
        background: var(--track-bg) !important;
    }}
    div[data-testid="stSlider"] [role="slider"] {{
        background: linear-gradient(135deg, var(--accent-1), var(--accent-2)) !important;
        border: 2px solid rgba(255, 255, 255, 0.6) !important;
        box-shadow: 0 0 0 4px var(--accent-soft), 0 2px 10px rgba(0, 0, 0, 0.4) !important;
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
    .stButton > button:active {{
        transform: translateY(0px) scale(0.98) !important;
        box-shadow: 0 2px 8px rgba(124, 140, 255, 0.3) !important;
    }}
    .stButton > button:focus-visible {{
        outline: 2px solid var(--accent-1) !important;
        outline-offset: 2px !important;
    }}

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

    .flash-face {{
        padding: 24px; border-radius: 18px; text-align: center; font-size: 1.25rem;
    }}

    .shimmer-block {{ display: flex; flex-direction: column; gap: 10px; padding: 4px 0; }}
    .shimmer-bar {{
        height: 14px; border-radius: 8px;
        background: linear-gradient(90deg, rgba(255,255,255,0.05) 25%, rgba(255,255,255,0.14) 50%, rgba(255,255,255,0.05) 75%);
        background-size: 200% 100%;
        animation: sso-shimmer 1.3s ease-in-out infinite;
    }}
    @keyframes sso-shimmer {{
        0% {{ background-position: 200% 0; }}
        100% {{ background-position: -200% 0; }}
    }}
    @media (prefers-reduced-motion: reduce) {{ .shimmer-bar {{ animation: none; }} }}

    .empty-state {{
        text-align: center; padding: 22px 16px; border-radius: 16px;
        background: var(--card-bg); border: 1px dashed var(--border);
        color: var(--muted); font-size: 0.9rem;
    }}
    .empty-state .empty-icon {{ font-size: 1.8rem; display: block; margin-bottom: 6px; }}

    .level-up-overlay {{
        position: fixed; inset: 0; z-index: 999998;
        display: flex; align-items: center; justify-content: center;
        background: rgba(5, 7, 13, 0.35);
        animation: sso-overlay-fade 2.6s ease forwards;
        pointer-events: none;
    }}
    @keyframes sso-overlay-fade {{
        0% {{ opacity: 0; }} 10% {{ opacity: 1; }} 75% {{ opacity: 1; }} 100% {{ opacity: 0; }}
    }}
    .level-up-card {{
        background: var(--card-bg); backdrop-filter: blur(26px) saturate(180%);
        border: 1px solid var(--border); border-radius: 24px; padding: 28px 40px;
        text-align: center; box-shadow: inset 0 1px 0 rgba(255,255,255,0.2), 0 20px 60px rgba(0,0,0,0.5);
        animation: sso-pop-in 0.5s cubic-bezier(.34,1.56,.64,1);
    }}
    @keyframes sso-pop-in {{
        0% {{ transform: scale(0.6); opacity: 0; }}
        60% {{ transform: scale(1.08); opacity: 1; }}
        100% {{ transform: scale(1); opacity: 1; }}
    }}
    .level-up-icon {{ font-size: 2.6rem; }}
    .level-up-title {{
        font-size: 1.6rem; font-weight: 800; margin-top: 6px;
        background: linear-gradient(135deg, var(--accent-1), var(--accent-2));
        -webkit-background-clip: text; background-clip: text; color: transparent;
    }}
    .level-up-sub {{ font-size: 0.95rem; color: var(--muted); margin-top: 2px; }}

    .badge-popup {{
        position: fixed; top: 20px; right: 20px; z-index: 999997;
        display: flex; align-items: center; gap: 10px;
        background: var(--card-bg); backdrop-filter: blur(22px) saturate(180%);
        border: 1px solid rgba(124,140,255,0.35); border-radius: 16px; padding: 12px 18px;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.2), var(--shadow);
        animation: sso-badge-slide 3.2s ease forwards;
    }}
    @keyframes sso-badge-slide {{
        0% {{ transform: translateX(120%); opacity: 0; }}
        10% {{ transform: translateX(0); opacity: 1; }}
        85% {{ transform: translateX(0); opacity: 1; }}
        100% {{ transform: translateX(120%); opacity: 0; }}
    }}
    .badge-popup-icon {{ font-size: 1.4rem; }}
    .badge-popup-text {{ font-size: 0.85rem; color: var(--text); }}

    .quiz-result-card {{
        background: var(--card-bg); backdrop-filter: blur(18px) saturate(180%);
        border: 1px solid var(--border); border-radius: 16px; padding: 14px 16px; margin-bottom: 12px;
        opacity: 0; animation: sso-fade-in 0.45s ease forwards;
    }}
    .quiz-result-card.quiz-card-correct {{ border-color: rgba(34, 197, 94, 0.45); }}
    .quiz-result-card.quiz-card-wrong {{ border-color: rgba(239, 68, 68, 0.45); }}
    .quiz-result-q {{ font-weight: 700; margin-bottom: 8px; color: var(--text); }}
    .quiz-opt {{
        padding: 7px 12px; border-radius: 10px; margin-bottom: 5px; font-size: 0.88rem;
        background: rgba(255,255,255,0.03); border: 1px solid transparent; color: var(--muted);
    }}
    .quiz-opt-correct {{ background: rgba(34, 197, 94, 0.14); border-color: rgba(34, 197, 94, 0.4); color: var(--text); }}
    .quiz-opt-wrong {{ background: rgba(239, 68, 68, 0.14); border-color: rgba(239, 68, 68, 0.4); color: var(--text); }}

    .cbar-chart {{ display: flex; flex-direction: column; gap: 10px; padding: 6px 0; }}
    .cbar-row {{ display: flex; align-items: center; gap: 10px; }}
    .cbar-label {{ width: 130px; font-size: 0.8rem; color: var(--muted); flex-shrink: 0; }}
    .cbar-track {{
        flex: 1; height: 14px; border-radius: 8px; background: var(--track-bg);
        border: 1px solid var(--border); overflow: hidden;
    }}
    .cbar-fill {{
        height: 100%; border-radius: 8px;
        background: linear-gradient(90deg, var(--accent-1), var(--accent-2));
        box-shadow: 0 0 10px rgba(124,140,255,0.5);
        transition: width 0.8s ease;
    }}
    .cbar-value {{ width: 46px; text-align: right; font-size: 0.8rem; color: var(--text); flex-shrink: 0; }}

    /* ===== Right-side navigation bar ===== */
    div.st-key-right_navbar {{
        position: fixed !important;
        top: 5.2rem;
        right: 1.2rem;
        width: 232px;
        max-height: calc(100vh - 7rem);
        overflow-y: auto;
        z-index: 999;
        padding: 1.1rem 0.85rem;
        border-radius: 24px;
        background: var(--dock-bg);
        backdrop-filter: blur(26px) saturate(180%);
        -webkit-backdrop-filter: blur(26px) saturate(180%);
        border: 1px solid var(--border);
        box-shadow: var(--shadow);
        scrollbar-width: thin;
    }}
    div.st-key-right_navbar::-webkit-scrollbar {{ width: 6px; }}
    div.st-key-right_navbar::-webkit-scrollbar-thumb {{
        background: var(--accent-soft); border-radius: 6px;
    }}
    div.st-key-right_navbar .stButton {{ margin-bottom: 2px; }}
    div.st-key-right_navbar .stButton > button {{
        width: 100% !important;
        justify-content: flex-start !important;
        text-align: left !important;
        padding: 0.55rem 0.7rem !important;
        font-size: 0.86rem !important;
        border-radius: 12px !important;
        transform: none !important;
    }}
    div.st-key-right_navbar .stButton > button:hover {{
        transform: translateX(-3px) !important;
    }}
    div.st-key-right_navbar .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, var(--accent-1), var(--accent-2)) !important;
        border: none !important;
        color: #FFFFFF !important;
        box-shadow: 0 6px 18px rgba(124, 140, 255, 0.4), inset 0 1px 0 rgba(255,255,255,0.3) !important;
    }}
    .navbar-title {{
        font-weight: 700; font-size: 1.0rem; letter-spacing: 0.01em;
        padding: 0.1rem 0.35rem 0.7rem 0.35rem; color: var(--text);
        display: flex; align-items: center; gap: 0.4rem;
    }}
    .navbar-group-label {{
        font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.07em;
        font-weight: 700; color: var(--muted-2);
        margin: 0.85rem 0.35rem 0.3rem 0.35rem;
    }}
    .navbar-divider {{
        height: 1px; background: var(--border); margin: 0.6rem 0.35rem;
    }}
    {nav_padding_css}
    @media (max-width: 900px) {{
        div.st-key-right_navbar {{
            display: none !important;
        }}
        [data-testid="stMainBlockContainer"] {{
            padding-right: 1rem !important;
            padding-left: 1rem !important;
            padding-top: 1rem !important;
        }}
        div.st-key-quick_access_grid [data-testid="stHorizontalBlock"] {{
            display: grid !important;
            grid-template-columns: 1fr 1fr !important;
            gap: 0.6rem !important;
        }}
        div.st-key-quick_access_grid [data-testid="stHorizontalBlock"] > div {{
            width: 100% !important;
            min-width: 0 !important;
            flex: unset !important;
        }}
        div[data-testid="stMetric"] [data-testid="stHorizontalBlock"],
        [data-testid="stHorizontalBlock"]:has(div[data-testid="stMetric"]) {{
            display: grid !important;
            grid-template-columns: 1fr 1fr !important;
            gap: 0.6rem !important;
        }}
        [data-testid="stHorizontalBlock"]:has(div[data-testid="stMetric"]) > div {{
            width: 100% !important;
            min-width: 0 !important;
            flex: unset !important;
        }}
        [data-testid="stMain"] h1 {{ font-size: 1.55rem !important; line-height: 1.3 !important; }}
        [data-testid="stMain"] h2 {{ font-size: 1.25rem !important; }}
        [data-testid="stMain"] h3 {{ font-size: 1.08rem !important; }}
        div.st-key-auth_card {{ margin-top: 1.4rem !important; }}
    }}
    div.st-key-sidebar_navbar {{
        padding-top: 0.4rem;
        border-top: 1px solid var(--border);
        margin-top: 0.6rem;
    }}
    div.st-key-sidebar_navbar .stButton > button {{
        justify-content: flex-start !important;
        text-align: left !important;
        border-radius: 12px !important;
    }}
    @media (min-width: 901px) {{
        div.st-key-sidebar_navbar {{ display: none !important; }}
    }}

    /* ===== Auth screen (login / sign up) ===== */
    div.st-key-auth_card {{
        max-width: 480px;
        margin: 3.2rem auto 2rem auto;
        padding: 2.5rem 2.3rem 2.1rem 2.3rem;
        border-radius: 28px;
        background: var(--card-bg);
        backdrop-filter: blur(30px) saturate(180%);
        -webkit-backdrop-filter: blur(30px) saturate(180%);
        border: 1px solid var(--border);
        box-shadow: var(--shadow);
    }}
    .auth-logo {{
        width: 62px; height: 62px; margin: 0 auto 1rem auto;
        border-radius: 20px;
        background: linear-gradient(135deg, var(--accent-1), var(--accent-2));
        display: flex; align-items: center; justify-content: center;
        font-size: 1.9rem;
        box-shadow: 0 8px 24px rgba(124, 140, 255, 0.45), inset 0 1px 0 rgba(255,255,255,0.3);
    }}
    .auth-title {{
        text-align: center; font-weight: 700; font-size: 1.5rem;
        margin: 0 0 0.3rem 0; color: var(--text);
    }}
    .auth-subtitle {{
        text-align: center; font-size: 0.9rem; color: var(--muted);
        margin: 0 0 1.5rem 0;
    }}
    .auth-divider-text {{
        text-align: center; font-size: 0.8rem; color: var(--muted-2);
        margin: 0.9rem 0; position: relative;
    }}
    div.st-key-auth_card div[data-testid="stTabs"] {{
        width: 100% !important;
    }}
    div.st-key-auth_card div[data-testid="stTabs"] [data-baseweb="tab-list"] {{
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        width: 100% !important;
        gap: 0.35rem; border-bottom: none;
        background: var(--track-bg); padding: 0.3rem;
        border-radius: 14px; margin-bottom: 1.3rem;
    }}
    div.st-key-auth_card div[data-testid="stTabs"] button[data-baseweb="tab"],
    div.st-key-auth_card div[data-testid="stTabs"] [data-baseweb="tab"] {{
        flex: 1 1 0% !important;
        width: auto !important;
        max-width: none !important;
        min-width: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 0.35rem;
        border-radius: 10px !important;
        padding: 0.6rem 0.5rem !important;
        color: var(--muted) !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        outline: none !important;
        box-shadow: none !important;
        border: none !important;
    }}
    div.st-key-auth_card div[data-testid="stTabs"] button[data-baseweb="tab"]:focus,
    div.st-key-auth_card div[data-testid="stTabs"] button[data-baseweb="tab"]:focus-visible,
    div.st-key-auth_card div[data-testid="stTabs"] [data-baseweb="tab"]:focus,
    div.st-key-auth_card div[data-testid="stTabs"] [data-baseweb="tab"]:focus-visible {{
        outline: none !important;
        box-shadow: none !important;
    }}
    div.st-key-auth_card div[data-testid="stTabs"] [aria-selected="true"] {{
        background: linear-gradient(135deg, var(--accent-1), var(--accent-2)) !important;
        color: #FFFFFF !important;
    }}
    div.st-key-auth_card div[data-testid="stTabs"] [data-baseweb="tab"] p,
    div.st-key-auth_card div[data-testid="stTabs"] [data-baseweb="tab"] div {{
        color: inherit !important;
        font-weight: inherit !important;
        margin: 0 !important;
    }}
    div.st-key-auth_card div[data-testid="stTabs"] [data-baseweb="tab-highlight"],
    div.st-key-auth_card div[data-testid="stTabs"] [data-baseweb="tab-border"] {{
        display: none !important;
    }}
    @media (max-width: 560px) {{
        div.st-key-auth_card {{ margin: 1.2rem 0.5rem; padding: 1.8rem 1.4rem; }}
    }}

    /* ===== Home page: Quick Access tiles ===== */
    div.st-key-quick_access_grid .stButton {{ margin-bottom: 0.9rem; }}
    div.st-key-quick_access_grid .stButton > button {{
        height: 96px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 0.35rem;
        white-space: pre-line;
        line-height: 1.25;
        border-radius: 18px !important;
        font-size: 0.86rem !important;
        font-weight: 600 !important;
    }}
    div.st-key-quick_access_grid .stButton > button:first-line {{
        font-size: 1.7rem;
    }}
    div.st-key-quick_access_grid .stButton > button:hover {{
        transform: translateY(-4px) scale(1.02) !important;
    }}

    /* ===== Floating AI Assistant button (#floating-ai-btn) ===== */
    div.st-key-floating-ai-btn {{
        position: fixed !important;
        bottom: 24px;
        left: 24px;
        z-index: 999999;
        width: auto !important;
    }}
    div.st-key-floating-ai-btn .stButton > button {{
        border-radius: 999px !important;
        padding: 0.85rem 1.5rem !important;
        background: linear-gradient(135deg, var(--accent-1), var(--accent-2)) !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5) !important;
        transition: transform 0.2s ease !important;
    }}
    div.st-key-floating-ai-btn .stButton > button:hover {{
        transform: translateY(-3px) scale(1.03) !important;
    }}

    /* ===== Leaderboard: podium & rankings ===== */
    .podium-wrap {{
        display: flex;
        align-items: flex-end;
        justify-content: center;
        gap: 1rem;
        margin: 1.5rem 0 2rem 0;
        flex-wrap: wrap;
    }}
    .podium-card {{
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 1.2rem 1rem;
        text-align: center;
        width: 160px;
        backdrop-filter: blur(10px);
        box-shadow: var(--shadow);
    }}
    .podium-card.rank-1 {{ order: 2; padding-top: 2.2rem; border: 1px solid rgba(255,215,0,0.6); box-shadow: 0 0 30px rgba(255,215,0,0.25); }}
    .podium-card.rank-2 {{ order: 1; }}
    .podium-card.rank-3 {{ order: 3; }}
    .podium-medal {{ font-size: 2rem; }}
    .podium-avatar {{ font-size: 2.4rem; margin: 0.3rem 0; }}
    .podium-name {{ font-weight: 700; color: #F5F7FA; }}
    .podium-xp {{ color: var(--accent-1); font-weight: 600; font-size: 0.9rem; }}
    .rank-row {{
        display: flex;
        align-items: center;
        gap: 0.9rem;
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 0.7rem 1rem;
        margin-bottom: 0.6rem;
    }}
    .rank-num {{ font-weight: 700; width: 28px; text-align: center; color: var(--accent-2); }}
    .rank-avatar {{ font-size: 1.5rem; }}
    .rank-info {{ flex: 1; }}
    .rank-name {{ font-weight: 600; color: #F5F7FA; }}
    .rank-sub {{ font-size: 0.78rem; opacity: 0.7; }}
    .rank-badges {{ display: flex; gap: 0.3rem; flex-wrap: wrap; max-width: 220px; }}
    .rank-milestone {{ font-size: 0.72rem; background: var(--accent-soft); padding: 0.15rem 0.5rem; border-radius: 8px; }}
    .rank-xp {{ font-weight: 700; color: var(--accent-1); min-width: 70px; text-align: right; }}
    </style>
    """, unsafe_allow_html=True)

# ==================== SHARED UI HELPERS ====================

def show_shimmer(placeholder, lines=3):
    widths = [95, 88, 72, 60][:max(1, lines)]
    bars = "".join(f'<div class="shimmer-bar" style="width:{w}%;"></div>' for w in widths)
    placeholder.markdown(f'<div class="shimmer-block">{bars}</div>', unsafe_allow_html=True)

def empty_state(icon, text):
    st.markdown(f'<div class="empty-state"><span class="empty-icon">{icon}</span>{text}</div>', unsafe_allow_html=True)

def render_flip_card(front_text, back_text, card_id):
    safe_front = (front_text or "").replace("</div>", "").replace("<script", "")
    safe_back = (back_text or "").replace("</div>", "").replace("<script", "")
    html = f"""
<div style="font-family:'Plus Jakarta Sans',-apple-system,sans-serif; perspective:1200px;">
  <div id="card-{card_id}" onclick="this.classList.toggle('flipped')"
       style="position:relative;width:100%;height:190px;cursor:pointer;
              transition:transform 0.6s cubic-bezier(.4,.2,.2,1);transform-style:preserve-3d;">
    <div style="position:absolute;inset:0;backface-visibility:hidden;
                display:flex;align-items:center;justify-content:center;text-align:center;
                padding:20px;border-radius:18px;font-size:1.1rem;color:#F5F7FA;line-height:1.4;
                background:rgba(255,255,255,0.07);backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);
                border:1px solid rgba(255,255,255,0.16);box-sizing:border-box;
                box-shadow:inset 0 1px 0 rgba(255,255,255,0.2);">
      {safe_front}
    </div>
    <div style="position:absolute;inset:0;backface-visibility:hidden;transform:rotateY(180deg);
                display:flex;align-items:center;justify-content:center;text-align:center;
                padding:20px;border-radius:18px;font-size:1rem;color:#F5F7FA;line-height:1.4;
                background:rgba(255,255,255,0.07);backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);
                border:1px solid rgba(199,125,255,0.45);box-sizing:border-box;
                box-shadow:inset 0 1px 0 rgba(255,255,255,0.2);">
      {safe_back}
    </div>
  </div>
  <style> #card-{card_id}.flipped {{ transform: rotateY(180deg); }} </style>
  <p style="text-align:center;color:#7C8699;font-size:0.72rem;margin-top:8px;">Tap the card to flip</p>
</div>
"""
    components.html(html, height=230)

def render_quiz_result_card(idx, q, u_ans):
    is_correct = (u_ans == q["correct"])
    options_html = ""
    for letter in ["A", "B", "C", "D"]:
        cls = ""
        icon = "&nbsp;&nbsp;"
        if letter == q["correct"]:
            cls, icon = "quiz-opt-correct", "✅"
        elif letter == u_ans:
            cls, icon = "quiz-opt-wrong", "❌"
        options_html += f'<div class="quiz-opt {cls}">{icon} {letter}) {q.get(letter, "")}</div>'
    status_cls = "quiz-card-correct" if is_correct else "quiz-card-wrong"
    st.markdown(f"""
<div class="quiz-result-card {status_cls}" style="animation-delay:{idx * 0.06}s;">
<div class="quiz-result-q">Question {idx + 1}: {q['question']}</div>
{options_html}
</div>
""", unsafe_allow_html=True)

def render_custom_bars(labels_values, unit=""):
    values = [v for _, v in labels_values]
    max_v = max(values) if values else 1
    max_v = max_v or 1
    rows = ""
    for label, value in labels_values:
        pct = int((value / max_v) * 100)
        rows += (
            f'<div class="cbar-row"><div class="cbar-label">{label}</div>'
            f'<div class="cbar-track"><div class="cbar-fill" style="width:{pct}%;"></div></div>'
            f'<div class="cbar-value">{value}{unit}</div></div>'
        )
    st.markdown(f'<div class="cbar-chart">{rows}</div>', unsafe_allow_html=True)

# ==================== PROMPT BUILDERS ====================

def _syllabus_notice(task_name):
    return f"CRITICAL RULE: This request is for {task_name} ONLY — produce nothing else. This content MUST strictly align with the Sri Lankan local school syllabus for the user's grade."

def _who_line():
    user_info = current_profile()
    return f"The user is {user_info.get('user_age', 13)} years old in {user_info.get('user_grade', 'Grade 8')} in Sri Lanka."

def build_quiz_prompt(subject, difficulty, num_questions, content):
    return (
        f"{_who_line()} {_syllabus_notice('a multiple-choice quiz')} "
        f"Subject: {subject}. Difficulty: {difficulty}. Generate ONLY exactly "
        f"{num_questions} multiple choice questions. Return ONLY a raw JSON array of exactly {num_questions} "
        "objects, each with keys: 'question', 'A', 'B', 'C', 'D', 'correct' (one of 'A'/'B'/'C'/'D'). "
        f"Topic/Content: {content[:2000]}"
    )

def language_instruction():
    user_info = current_profile()
    lang = user_info.get('language', 'en')
    if lang == "si":
        return "Respond in Sinhala (සිංහල)."
    return "Respond in English."

# ==================== PARENT / TEACHER VIEW ====================

if st.query_params.get("view") == "parent":
    apply_theme(with_nav=False)
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

# ==================== LOGIN / PROFILE SELECTION ====================

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
    apply_theme(with_nav=False)
    with st.container(key="auth_card"):
        st.markdown('<div class="auth-logo">🎓</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-title">Almost there!</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="auth-subtitle">Signed in as {st.session_state.google_pending_email} — tell us a bit about yourself</div>', unsafe_allow_html=True)

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
    apply_theme(with_nav=False)
    with st.container(key="auth_card"):
        st.markdown('<div class="auth-logo">🎓</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-title">Welcome to Smart Study Organizer Pro!</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-subtitle">Your all-in-one AI study companion 👋</div>', unsafe_allow_html=True)

        if is_google_auth_configured():
            if st.button("🔵 Continue with Google", use_container_width=True):
                st.login()
            st.markdown('<div class="auth-divider-text">— or use a password —</div>', unsafe_allow_html=True)

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
                        st.warning("⚠️ This account hasn't been secured with a password yet. Set one now to claim it.")
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

# ==================== PERSONALIZED CONTEXT ====================

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

# ==================== DYNAMIC SIDEBAR RENDERER ====================

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
                empty_state("🥇", t("No badges unlocked yet!"))

        st.markdown("<div style='margin: 15px 0;'></div>", unsafe_allow_html=True)

        if st.button("⚙️ " + t("Settings"), use_container_width=True):
            st.session_state["nav_choice"] = "⚙️"
            st.rerun()

        if st.button(t("🔄 Switch Profile"), use_container_width=True):
            if st.session_state.get("auth_method") == "google":
                try:
                    st.logout()
                except Exception:
                    pass
            st.session_state.active_user = None
            st.session_state.auth_method = None
            st.rerun()

render_sidebar()

# ==================== FLOATING AI ASSISTANT (FAB) ====================

@st.dialog("💬 AI Study Assistant")
def show_ai_assistant_dialog():
    st.caption("Ask me anything about what you're studying — I respond fast, right where you are.")
    if "floating_chat_history" not in st.session_state:
        st.session_state.floating_chat_history = []

    for msg in st.session_state.floating_chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_msg = st.chat_input("Ask a quick question...")
    if user_msg:
        st.session_state.floating_chat_history.append({"role": "user", "content": user_msg})
        with st.chat_message("user"):
            st.write(user_msg)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                tutor_prompt = f"{_who_line()} Answer this student's question clearly, briefly, and in a friendly tutor tone: {user_msg}"
                reply = get_ai_response(tutor_prompt, task="instant")
            st.write(reply)
        st.session_state.floating_chat_history.append({"role": "assistant", "content": reply})

def render_floating_ai_assistant():
    with st.container(key="floating-ai-btn"):
        if st.button("💬 Ask AI Assistant", key="floating_ai_btn_trigger"):
            st.session_state["_open_ai_dialog"] = True
    if st.session_state.get("_open_ai_dialog"):
        st.session_state["_open_ai_dialog"] = False
        show_ai_assistant_dialog()

# ==================== PAGE FUNCTIONS ====================

def show_home():
    profile = current_profile()
    gam = profile["gamification"]
    lvl, into_level, needed = xp_progress(gam["xp"])

    st.markdown(f"## {greeting}")
    st.caption(f"{profile.get('user_grade', '')} · Level {lvl}")

    c1, c2, c3 = st.columns(3)
    c1.metric("XP", gam["xp"])
    c2.metric("Streak", f"{gam.get('streak', 0)} 🔥")
    c3.metric("Badges", f"{len(gam.get('badges', []))}/{len(BADGES)}")

    st.write("")
    st.write("### Quick Access")

    quick_links = [
        ("💡", "Daily Facts"), ("🗺️", "Mindmap"), ("📝", "Summarizer"),
        ("🎧", "Audio Overview"), ("❓", "MCQ Quiz"), ("🧠", "Math Solver"),
        ("🎴", "Flashcards"), ("⏱️", "Pomodoro"), ("✍️", "Scribble Pad"),
        ("👨‍🏫", "Exam Examiner"), ("📦", "Study Pack"), ("📅", "Schedule"),
        ("📊", "Analytics"),
    ]

    with st.container(key="quick_access_grid"):
        cols = st.columns(4)
        for i, (icon, label) in enumerate(quick_links):
            with cols[i % 4]:
                if st.button(f"{icon}\n{label}", use_container_width=True, key=f"home_{icon}"):
                    st.session_state["nav_choice"] = icon
                    st.rerun()

    quiz_history = profile.get("quiz_history", [])
    if quiz_history:
        st.write("")
        st.write("### Recent activity")
        for entry in quiz_history[-3:][::-1]:
            st.caption(f"📝 {entry['date']} — {entry['subject']}: {entry['score']}/{entry['total']}")

def show_settings():
    st.header("⚙️ " + t("Settings"))
    profile = current_profile()

    st.subheader("🌐 " + t("Language"))
    is_sinhala = profile.get("language", "en") == "si"
    lang_choice = st.toggle("🇱🇰 සිංහල (Sinhala)", value=is_sinhala, key="settings_language_toggle")
    new_lang = "si" if lang_choice else "en"
    if new_lang != profile.get("language", "en"):
        profile["language"] = new_lang
        save_current()
        st.rerun()

    st.write("---")
    st.subheader("🔗 " + t("Parent / Teacher View"))
    st.caption("Share this with a parent or teacher for a read-only progress summary — no login, no editing.")
    encoded_key = urllib.parse.quote(st.session_state.active_user, safe="")
    st.code(f"?view=parent&user={encoded_key}", language=None)
    st.caption("Append this to the app's web address in your browser and share that full link.")

    st.write("---")
    st.subheader("👤 " + t("Account"))
    st.write(f"**Name:** {profile.get('user_name', '')}")
    st.write(f"**Grade:** {profile.get('user_grade', '')}")
    st.write(f"**Age:** {profile.get('user_age', '')}")
    if profile.get("email"):
        st.write(f"**Signed in with:** Google ({profile['email']})")
    else:
        st.write("**Signed in with:** Username & password")

def show_daily_facts():
    st.header(t("💡 Daily Tech & Science Facts"))
    st.caption(t("Get interesting Tech/Science facts here"))
    
    offline_manager = OfflineContentManager()
    if not offline_manager.is_online():
        st.info("📶 Offline Mode - Using pre-loaded facts")
    
    today_str = str(date.today())
    need_new = ("daily_fact" not in st.session_state or st.session_state.get("daily_fact_date") != today_str)

    if st.button("Get a new Fact 🧠") or need_new:
        ph = st.empty()
        show_shimmer(ph, lines=3)
        
        offline_manager = OfflineContentManager()
        if offline_manager.is_online():
            prompt = build_daily_fact_prompt()
            st.session_state.daily_fact = get_ai_response(prompt, task="instant")
        else:
            st.session_state.daily_fact = offline_manager.get_offline_fact()
        
        st.session_state.daily_fact_date = today_str
        ph.empty()

    st.info(st.session_state.daily_fact)

def build_daily_fact_prompt():
    return f"{_who_line()} Tell ONLY one amazing, mind-blowing, yet easy-to-understand science or computer technology fact. Explain it in 3 clear bullet points."

def show_mindmap():
    st.header(t("🗺️ AI Mindmap Generator"))
    st.caption(t("Turn your notes or PDFs into a structured, easy-to-understand mindmap."))
    
    mm_file = st.file_uploader("Upload Notes (PDF, PNG, JPG):", type=["pdf", "png", "jpg", "jpeg"])
    mm_text = st.text_area("Or type/paste the main topic or notes here:", height=100)

    if st.button("Generate Mindmap 🧠"):
        if mm_file or mm_text:
            ph = st.empty()
            show_shimmer(ph, lines=4)
            extracted_content = mm_text
            img = None

            if mm_file:
                if mm_file.name.lower().endswith(".pdf"):
                    extracted_content += "\n" + extract_text_from_pdf(mm_file)
                else:
                    img = Image.open(mm_file)

            prompt = build_mindmap_prompt(extracted_content)

            mm_output = get_ai_response(prompt, image=img, task="complex")
            ph.empty()
            st.success("Your Mindmap is Ready:")
            st.markdown(mm_output)

            profile = current_profile()
            add_xp(profile, XP_REWARDS["mindmap_created"], "mindmap_created")
            save_current()
            render_gamification_popups()
        else:
            st.warning("Please provide a topic or upload a file to generate a mindmap.")

def build_mindmap_prompt(content):
    return f"{_who_line()} {_syllabus_notice('a mindmap')} Based on the following content, generate ONLY a clear, logical, structured text-based mindmap. Format it using clean nested markdown bullet points. Content: {content[:2000]}"

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
                prompt = build_summarizer_prompt(combined_text)
                output = get_ai_response(prompt, image=img, task="complex")
                st.success("Here is the Summary:")
                st.write(output)
                
                profile = current_profile()
                profile.setdefault("summary_history", [])
                profile["summary_history"].append({
                    "date": str(date.today()),
                    "content": output
                })
                add_xp(profile, XP_REWARDS["note_summarized"], "note_summarized")
                save_current()
                render_gamification_popups()
        else:
            st.warning("Please provide a note or upload a file.")

def build_summarizer_prompt(notes_text):
    return f"{_who_line()} {_syllabus_notice('a note summary')} Summarize these notes clearly in bullet points ONLY. Notes: {notes_text[:2000]}."

def show_audio_overview():
    st.header(t("🎧 Audio Overview"))
    st.caption(t("Turn your notes into a short two-host podcast-style discussion you can listen to."))

    uploaded_file = st.file_uploader("Upload Notes (PDF, PNG, JPG):", type=["pdf", "png", "jpg", "jpeg"], key="audio_ov_upload")
    user_note = st.text_area("Or paste the note here:", height=150, key="audio_ov_text")

    img = None
    pdf_text = ""
    if uploaded_file:
        if uploaded_file.name.lower().endswith(".pdf"):
            pdf_text = extract_text_from_pdf(uploaded_file)
            st.success("PDF loaded successfully!")
        else:
            img = Image.open(uploaded_file)
            st.image(img, width=300)

    if st.button("🎙️ Generate Audio Overview"):
        if uploaded_file or user_note:
            profile = current_profile()
            combined_text = user_note + "\n" + pdf_text

            script_ph = st.empty()
            show_shimmer(script_ph, lines=4)
            script_prompt = build_audio_overview_script_prompt(combined_text if combined_text.strip() else "see attached image")
            script_text = get_ai_response(script_prompt, image=img, task="complex")
            script_ph.empty()

            if script_text.startswith("ERROR") or script_text.startswith("⚠️"):
                st.error(script_text)
                return

            with st.expander("📄 View script", expanded=False):
                st.write(script_text)

            with st.spinner("Recording the audio overview..."):
                audio_bytes, audio_err = generate_audio_overview_wav(script_text)

            if audio_err:
                st.error(f"Couldn't generate the audio ({audio_err}). The script above is still available to read.")
            else:
                st.success("Your Audio Overview is ready:")
                st.audio(audio_bytes, format="audio/wav")
                st.download_button("⬇️ Download audio", data=audio_bytes, file_name="audio_overview.wav", mime="audio/wav")
                profile["analytics"]["audio_overviews_created"] = profile["analytics"].get("audio_overviews_created", 0) + 1
                add_xp(profile, XP_REWARDS["audio_overview_created"], "audio_overview_created")
                save_current()
                render_gamification_popups()
        else:
            st.warning("Please provide a note or upload a file.")

def build_audio_overview_script_prompt(content):
    return f"{_who_line()} {_syllabus_notice('a two-host podcast-style audio overview script')} Write ONLY a short, natural, conversational script between two hosts discussing and explaining the notes below. Format EVERY line as exactly 'Host1: <line>' or 'Host2: <line>'. Notes: {content[:2000]}"

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
                prompt = build_math_prompt(math_query)
                math_solution = get_ai_response(prompt, image=math_img, task="complex")
                st.success("Here is how to solve your question:")
                st.write(math_solution)

                profile = current_profile()
                profile["analytics"]["math_problems_solved"] = profile["analytics"].get("math_problems_solved", 0) + 1
                add_xp(profile, XP_REWARDS["math_solved"], "math_solved")
                save_current()
                render_gamification_popups()
        else:
            st.warning("Please provide a question or image")

def build_math_prompt(math_query):
    return f"{_who_line()} {_syllabus_notice('a step-by-step math solution')} Solve ONLY this one math problem step-by-step: {math_query}. Act like a friendly tutor teaching a beginner."

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
                empty_state("🎴", "You don't have any flashcards yet. Head to 'Generate New Cards' to create some.")
        else:
            st.caption(f"{len(due_cards)} card(s) due today")
            review_idx = st.session_state.get("flash_review_idx", 0)
            if review_idx >= len(due_cards):
                st.session_state.flash_review_idx = 0
                review_idx = 0

            card = due_cards[review_idx]
            st.markdown(f"**Subject:** {card.get('subject', 'General')}  ·  Card {review_idx + 1}/{len(due_cards)}")
            render_flip_card(card["front"], card["back"], card["id"])

            st.write("How well did you know this? (flip the card first)")
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
                st.session_state.flash_review_idx = review_idx
                render_gamification_popups()
                st.rerun()

    with tab_generate:
        gen_subject = st.text_input("Subject:", value="General Knowledge", key="flash_gen_subject")
        gen_topic = st.text_input("Topic:", key="flash_gen_topic")
        gen_count = st.slider("Number of flashcards:", min_value=3, max_value=20, value=8, key="flash_gen_count")

        gen_file = st.file_uploader("Upload notes/PDF to base flashcards on (optional):", type=["pdf", "txt"], key="flash_gen_upload")
        gen_pdf_text = ""
        if gen_file is not None:
            if gen_file.name.lower().endswith(".pdf"):
                gen_pdf_text = extract_text_from_pdf(gen_file)
                st.success("PDF loaded successfully!")
            else:
                gen_pdf_text = gen_file.read().decode("utf-8", errors="ignore")

        if st.button("✨ Generate Flashcards with AI"):
            if gen_topic or gen_pdf_text:
                with st.spinner(f"Creating {gen_count} flashcards..."):
                    offline_manager = OfflineContentManager()
                    if offline_manager.is_online():
                        prompt = build_flashcards_prompt(gen_subject, gen_topic, gen_count, gen_pdf_text)
                        raw_json = get_ai_response(prompt, task="instant")
                        try:
                            parsed = parse_quiz_json(raw_json)
                            for item in parsed:
                                profile["flashcards"].append(new_flashcard(item["front"], item["back"], gen_subject))
                            save_current()
                            st.success(f"Added {len(parsed)} new flashcards to your deck!")
                        except Exception:
                            st.error("There was an error creating flashcards. Please try again.")
                    else:
                        offline_cards = offline_manager.load_offline_flashcards()
                        for card in offline_cards[:gen_count]:
                            profile["flashcards"].append(new_flashcard(card["front"], card["back"], gen_subject))
                        save_current()
                        st.success(f"Added {min(gen_count, len(offline_cards))} offline flashcards to your deck!")
            else:
                st.warning("Please give a topic or upload a PDF")

    with tab_manage:
        if not profile["flashcards"]:
            empty_state("📋", "No flashcards yet.")
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

def build_flashcards_prompt(subject, topic, count, reference_content=""):
    topic_line = f"the topic '{topic}'" if topic else "the uploaded reference material"
    ref_block = f" Base the flashcards on this reference material: {reference_content[:3000]}" if reference_content else ""
    return f"{_who_line()} {_syllabus_notice('flashcards')} Subject: {subject}. Create ONLY exactly {count} flashcards for {topic_line}.{ref_block} Return ONLY a raw JSON array of exactly {count} objects, each with keys 'front' and 'back'."

# ==================== POMODORO TIMER ====================

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
        hour_now = datetime.now().hour
        if hour_now >= 21:
            profile["analytics"]["night_sessions"] = profile["analytics"].get("night_sessions", 0) + 1
        elif hour_now < 7:
            profile["analytics"]["morning_sessions"] = profile["analytics"].get("morning_sessions", 0) + 1
        add_xp(profile, XP_REWARDS["pomodoro_session"], "pomodoro_session")
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

def show_pomodoro():
    show_pomodoro_with_soundscapes()

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
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("MCQ Quizzes Taken", analytics["quiz_taken"])
    accuracy = 0
    if analytics["total_questions"] > 0:
        accuracy = int((analytics["total_score"] / analytics["total_questions"]) * 100)
    col2.metric("MCQ Accuracy", f"{accuracy}%")
    col3.metric("Pomodoro Sessions", analytics["pomodoro_sessions"])
    col4.metric("Math Problems Solved", analytics.get("math_problems_solved", 0))
    col5.metric("Audio Overviews", analytics.get("audio_overviews_created", 0))

    st.write("---")
    st.subheader("📊 Subject Mastery")
    subject_stats = []
    if analytics.get("science_questions", 0) > 0:
        subject_stats.append(("Science", analytics.get("science_questions", 0)))
    if analytics.get("math_problems_solved", 0) > 0:
        subject_stats.append(("Math", analytics.get("math_problems_solved", 0)))
    if analytics.get("history_questions", 0) > 0:
        subject_stats.append(("History", analytics.get("history_questions", 0)))
    if subject_stats:
        render_custom_bars(subject_stats)
    else:
        empty_state("📊", "Complete subject-specific activities to see mastery stats here.")

    st.write("---")
    st.subheader(t("📈 Overall Score vs Missed Questions"))
    if analytics["total_questions"] > 0:
        render_custom_bars([
            ("Correct Answers", analytics["total_score"]),
            ("Incorrect Answers", analytics["total_questions"] - analytics["total_score"]),
        ])
    else:
        empty_state("📈", "No quizzes taken yet — your score breakdown will show up here.")

    st.subheader(t("⏱️ Pomodoro Minutes Over Time"))
    pom_history = profile.get("pomodoro_history", [])
    if pom_history:
        pdf = pd.DataFrame(pom_history)
        pdf = pdf.groupby("date", as_index=False).agg(minutes=("minutes", "sum")).tail(14)
        render_custom_bars(list(zip(pdf["date"], pdf["minutes"])), unit=" min")
    else:
        empty_state("⏱️", "No focus sessions logged yet — complete a Pomodoro session to see your history here.")
    
    st.write("---")
    st.subheader("📝 Exam History")
    exam_history = profile.get("exam_history", [])
    if exam_history:
        exam_df = pd.DataFrame(exam_history)
        st.dataframe(exam_df[["date", "subject", "score", "total"]], use_container_width=True, hide_index=True)
    else:
        empty_state("📝", "No exams taken yet — try the Exam Examiner feature!")

# ==================== LEADERBOARD & GAMIFICATION ====================

LEADERBOARD_AVATARS = ["🦁", "🐼", "🦊", "🐯", "🐨", "🐸", "🦉", "🐵", "🐰", "🐺", "🦄", "🐳"]

def leaderboard_avatar(username):
    idx = int(hashlib.md5(username.encode("utf-8")).hexdigest(), 16) % len(LEADERBOARD_AVATARS)
    return LEADERBOARD_AVATARS[idx]

def compute_leaderboard_xp(profile):
    """XP engine for the rankings page: +10 XP per correct quiz answer, +50 perfect-score bonus,
    +2 XP per flashcard reviewed, +1 XP per focus (Pomodoro) minute."""
    analytics = profile.get("analytics", {})
    quiz_correct = analytics.get("total_score", 0)
    perfect_quizzes = sum(
        1 for q in profile.get("quiz_history", [])
        if q.get("total", 0) > 0 and q.get("score") == q.get("total")
    )
    perfect_exams = analytics.get("perfect_exams", 0)
    flashcards_reviewed = analytics.get("flashcards_reviewed", 0)
    focus_minutes = sum(h.get("minutes", 0) for h in profile.get("pomodoro_history", []))

    xp = (quiz_correct * 10) + ((perfect_quizzes + perfect_exams) * 50) + (flashcards_reviewed * 2) + (focus_minutes * 1)
    return xp, {
        "quiz_correct": quiz_correct,
        "perfect_count": perfect_quizzes + perfect_exams,
        "flashcards_reviewed": flashcards_reviewed,
        "focus_minutes": focus_minutes,
    }

def leaderboard_milestones(profile, breakdown):
    gam = profile.get("gamification", {})
    milestones = []
    if gam.get("streak", 0) >= 3:
        milestones.append("🔥 Study Machine")
    if profile.get("analytics", {}).get("quiz_taken", 0) >= 10:
        milestones.append("⚡ Quiz Master")
    if breakdown["focus_minutes"] >= 300:
        milestones.append("⏳ Focus Champion")
    if breakdown["flashcards_reviewed"] >= 50:
        milestones.append("🧠 Card Crusher")
    if breakdown["perfect_count"] >= 3:
        milestones.append("💯 Perfectionist")
    return milestones

def build_leaderboard_rows():
    users = st.session_state.all_data.get("users", {})
    rows = []
    for username, profile in users.items():
        display_name = profile.get("user_name") or username
        xp, breakdown = compute_leaderboard_xp(profile)
        gam = profile.get("gamification", {})
        rows.append({
            "username": username,
            "display_name": display_name,
            "avatar": leaderboard_avatar(username),
            "xp": xp,
            "streak": gam.get("streak", 0),
            "level": gam.get("level", 1),
            "milestones": leaderboard_milestones(profile, breakdown),
        })
    rows.sort(key=lambda r: r["xp"], reverse=True)
    return rows

def render_podium(rows):
    top3 = rows[:3]
    if not top3:
        return
    medals = ["🥇", "🥈", "🥉"]
    cards_html = ""
    rank_classes = ["rank-1", "rank-2", "rank-3"]
    for i, row in enumerate(top3):
        cards_html += f"""
<div class="podium-card {rank_classes[i]}">
<div class="podium-medal">{medals[i]}</div>
<div class="podium-avatar">{row['avatar']}</div>
<div class="podium-name">{row['display_name']}</div>
<div class="podium-xp">{row['xp']} XP</div>
<div class="rank-sub">🔥 {row['streak']}-day streak · Lvl {row['level']}</div>
</div>"""
    st.markdown(f'<div class="podium-wrap">{cards_html}</div>', unsafe_allow_html=True)

def render_rankings_table(rows):
    for i, row in enumerate(rows):
        badges_html = "".join(f'<span class="rank-milestone">{m}</span>' for m in row["milestones"])
        st.markdown(f"""
<div class="rank-row">
<div class="rank-num">#{i + 1}</div>
<div class="rank-avatar">{row['avatar']}</div>
<div class="rank-info">
<div class="rank-name">{row['display_name']}</div>
<div class="rank-sub">🔥 {row['streak']}-day streak · Level {row['level']}</div>
<div class="rank-badges">{badges_html}</div>
</div>
<div class="rank-xp">{row['xp']} XP</div>
</div>
""", unsafe_allow_html=True)

def show_leaderboard():
    st.header("🏆 Leaderboard & Gamification")
    st.caption("Rankings are calculated from quiz answers, perfect scores, flashcard reviews, and focus minutes across all study profiles on this app.")

    rows = build_leaderboard_rows()
    if not rows:
        empty_state("🏆", "No study activity yet — complete a quiz, review some flashcards, or run a Pomodoro session to appear on the leaderboard!")
        return

    render_podium(rows)
    st.write("---")
    st.subheader("📋 Full Rankings")
    render_rankings_table(rows)

    st.write("---")
    with st.expander("ℹ️ How XP is calculated"):
        st.markdown("""
- **+10 XP** for every correct quiz answer
- **+50 XP** bonus for every perfect quiz or exam score
- **+2 XP** for every flashcard reviewed
- **+1 XP** for every minute of focused (Pomodoro) study
        """)

# ==================== PAGE ROUTING - COMPACT DOCK ====================

# Define PAGES dictionary FIRST
PAGES = {
    "🏠": show_home,
    "💡": show_daily_facts,
    "🗺️": show_mindmap,
    "📝": show_summarizer,
    "🎧": show_audio_overview,
    "❓": show_mcq_quiz_with_offline,
    "🧠": show_math_solver,
    "🎴": show_flashcards,
    "⏱️": show_pomodoro,
    "✍️": show_scribble_pad,
    "📊": show_analytics,
    "👨‍🏫": show_exam_examiner,
    "📦": show_study_pack_exporter,
    "📅": show_study_schedule_builder,
    "🏆": show_leaderboard,
    "⚙️": show_settings,
}

# Navigation groups for display
NAV_GROUPS = {
    "🏠": "Home",
    "📚 Study": {
        "💡": "Daily Facts",
        "🗺️": "Mindmap", 
        "📝": "Summarizer",
        "🎧": "Audio Overview",
        "❓": "MCQ Quiz",
        "🧠": "Math Solver",
    },
    "🎯 Tools": {
        "🎴": "Flashcards",
        "⏱️": "Pomodoro",
        "✍️": "Scribble Pad",
    },
    "📊 Advanced": {
        "👨‍🏫": "Exam Examiner",
        "📦": "Study Pack",
        "📅": "Schedule",
        "📊": "Analytics",
        "🏆": "Leaderboard",
    },
    "⚙️": "Settings"
}

# Flatten navigation items
NAV_ITEMS = []
for key, value in NAV_GROUPS.items():
    if isinstance(value, dict):
        for sub_key, sub_label in value.items():
            NAV_ITEMS.append((sub_key, sub_label))
    else:
        NAV_ITEMS.append((key, value))

# Create a clean vertical nav bar docked to the right side of the screen
def render_nav_bar():
    """Render navigation as a floating vertical panel on the right"""
    current = st.session_state.get("nav_choice", "🏠")

    with st.container(key="right_navbar"):
        st.markdown('<div class="navbar-title">🧭 Navigate</div>', unsafe_allow_html=True)

        for key, value in NAV_GROUPS.items():
            if isinstance(value, dict):
                st.markdown(f'<div class="navbar-group-label">{key}</div>', unsafe_allow_html=True)
                for nav_key, nav_label in value.items():
                    is_active = nav_key == current
                    if st.button(
                        f"{nav_key}  {nav_label}",
                        key=f"nav_btn_{nav_key}",
                        use_container_width=True,
                        type="primary" if is_active else "secondary"
                    ):
                        st.session_state.nav_choice = nav_key
                        st.rerun()
            else:
                is_active = key == current
                if st.button(
                    f"{key}  {value}",
                    key=f"nav_btn_{key}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary"
                ):
                    st.session_state.nav_choice = key
                    st.rerun()
                if key == "🏠":
                    st.markdown('<div class="navbar-divider"></div>', unsafe_allow_html=True)

def render_sidebar_nav():
    """Render navigation inside the sidebar — shown only on mobile/tablet widths via CSS,
    since the floating right-side panel doesn't fit on smaller screens."""
    current = st.session_state.get("nav_choice", "🏠")

    with st.sidebar:
        with st.container(key="sidebar_navbar"):
            st.markdown('<div class="navbar-title">🧭 Navigate</div>', unsafe_allow_html=True)

            for key, value in NAV_GROUPS.items():
                if isinstance(value, dict):
                    st.markdown(f'<div class="navbar-group-label">{key}</div>', unsafe_allow_html=True)
                    for nav_key, nav_label in value.items():
                        is_active = nav_key == current
                        if st.button(
                            f"{nav_key}  {nav_label}",
                            key=f"sbnav_btn_{nav_key}",
                            use_container_width=True,
                            type="primary" if is_active else "secondary"
                        ):
                            st.session_state.nav_choice = nav_key
                            st.rerun()
                else:
                    is_active = key == current
                    if st.button(
                        f"{key}  {value}",
                        key=f"sbnav_btn_{key}",
                        use_container_width=True,
                        type="primary" if is_active else "secondary"
                    ):
                        st.session_state.nav_choice = key
                        st.rerun()
                    if key == "🏠":
                        st.markdown('<div class="navbar-divider"></div>', unsafe_allow_html=True)

# Render navigation
render_nav_bar()
render_sidebar_nav()

# Execute selected page
page_key = st.session_state.get("nav_choice", "🏠")
if page_key in PAGES:
    PAGES[page_key]()
else:
    show_home()

# Floating "Ask AI Assistant" button — available on every page
render_floating_ai_assistant()