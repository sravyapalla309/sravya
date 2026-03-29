import streamlit as st
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

st.set_page_config(page_title="RCEE AI Code Reviewer", page_icon="🤖", layout="centered")

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

dark = st.session_state.dark_mode

if dark:
    bg        = "#0a0a0f"
    surface   = "#12121a"
    border    = "#3a1f6e"
    text      = "#e8d5ff"
    subtext   = "#b388ff"
    code_text = "#ce93d8"
    btn_bg    = "#6a1b9a"
    btn_hover = "#7b1fa2"
    btn_text  = "#f3e5f5"
    row_bg    = "#1a1228"
    caption   = "#4a3560"
else:
    bg        = "#faf7ff"
    surface   = "#ffffff"
    border    = "#c9a8f0"
    text      = "#1a0a2e"
    subtext   = "#5e35b1"
    code_text = "#4a148c"
    btn_bg    = "#6a1b9a"
    btn_hover = "#7b1fa2"
    btn_text  = "#ffffff"
    row_bg    = "#f3e5f5"
    caption   = "#9575cd"

st.markdown(f"""
<style>
    .stApp {{ background-color: {bg}; color: {text}; }}
    .stTextArea textarea {{
        background-color: {surface} !important;
        color: {code_text} !important;
        font-family: 'Courier New', monospace !important;
        font-size: 20px !important;
        border: 1px solid {border} !important;
        border-radius: 8px !important;
    }}
    .stSelectbox div[data-baseweb="select"] {{
        background-color: {surface} !important;
        border: 1px solid {border} !important;
        color: {text} !important;
        font-size: 20px !important;
    }}
    .stButton > button, .stFormSubmitButton > button {{
        background-color: {btn_bg} !important;
        color: {btn_text} !important;
        font-size: 20px !important;
        border: none !important;
        border-radius: 8px !important;
    }}
    .stButton > button:hover, .stFormSubmitButton > button:hover {{
        background-color: {btn_hover} !important;
    }}
    h1 {{ color: {subtext} !important; font-size: 36px !important; }}
    h2, h3, label, p, .stMarkdown p {{
        color: {subtext} !important;
        font-size: 20px !important;
    }}
    .result-row {{
        background-color: {row_bg};
        border: 1px solid {border};
        border-radius: 8px;
        padding: 0.8rem 1.2rem;
        margin-bottom: 10px;
        font-size: 20px;
        color: {text};
        line-height: 1.6;
    }}
    hr {{ border-color: {border} !important; }}
    .stCaption {{ color: {caption} !important; font-size: 13px !important; }}
</style>
""", unsafe_allow_html=True)

# ─── Header + Toggle ──────────────────────────────────────────
col_title, col_toggle = st.columns([4, 1])
with col_title:
    st.title("🌑 RCEE AI Code Reviewer")
with col_toggle:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("☀️ Light" if dark else "🌑 Dark", use_container_width=True):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

st.divider()

if not GROQ_API_KEY:
    st.error("❌ GROQ_API_KEY not found in .env file.")
    st.stop()

languages = ["Auto Detect", "Python", "Java", "C", "C++", "JavaScript", "TypeScript",
             "Go", "Rust", "Ruby", "PHP", "Swift", "Kotlin", "SQL", "HTML/CSS", "Other"]

col1, col2 = st.columns([2, 1])
with col1:
    language = st.selectbox("🌐 Language", languages)
with col2:
    review_depth = st.selectbox("🔍 Depth", ["Standard", "Deep", "Quick"])

with st.form("analyze_form"):
    code = st.text_area(
        "📋 Paste your code  *(Ctrl+Enter to analyze)*",
        height=300,
        placeholder="// Paste your code here..."
    )
    analyze_clicked = st.form_submit_button("🚀 Analyze Code", use_container_width=True)

# ─── Analysis ─────────────────────────────────────────────────
if analyze_clicked:
    if not code.strip():
        st.warning("⚠️ Please paste some code first!")
    else:
        numbered_code = "\n".join(
            f"{i+1:3} | {line}" for i, line in enumerate(code.splitlines())
        )

        lang_note = ("Detect the programming language automatically."
                     if language == "Auto Detect" else f"Language is {language}.")
        depth_note = {
            "Quick":    "Only critical errors and 1 suggestion. Very brief.",
            "Standard": "Cover errors, warnings, and suggestions concisely.",
            "Deep":     "Cover errors, security, performance, and best practices."
        }[review_depth]

        prompt = f"""You are a senior software engineer. {lang_note} {depth_note}

The code has line numbers. Mention exact line number for errors/warnings.

Respond in EXACTLY this format — each on its own line, no extra text, no paragraphs:

🔤 Language   : <language name>
🐛 Errors     : <Line X: what's wrong — or ✅ None>
⚠️ Warnings   : <Line X: potential issue — or ✅ None>
💡 Suggestions: <top improvement>
⭐ Rating     : <X/10 — one sentence>

Code:
```
{numbered_code}
```"""

        with st.spinner("🔍 Analyzing..."):
            try:
                client = Groq(api_key=GROQ_API_KEY)

                full_response = ""
                for chunk in client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=300,
                    stream=True
                ):
                    delta = chunk.choices[0].delta.content
                    if delta:
                        full_response += delta

                # ── Parse & display line by line ──────────────
                st.markdown("<br>", unsafe_allow_html=True)
                lines = [l.strip() for l in full_response.strip().splitlines() if l.strip()]
                for line in lines:
                    st.markdown(f'<div class="result-row">{line}</div>', unsafe_allow_html=True)

            except Exception as e:
                err = str(e)
                if "auth" in err.lower() or "401" in err:
                    st.error("❌ Invalid API Key.")
                elif "rate" in err.lower() or "429" in err:
                    st.error("⏳ Rate limit hit. Try again shortly.")
                else:
                    st.error(f"❌ {err}")

st.divider()