import os
import tempfile

import streamlit as st

from main import run_pipeline
from core.rag_engine import ask_question

st.set_page_config(page_title="Video Notes", page_icon="🗒️", layout="centered")

# ---------- Styling ----------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,500;6..72,600&family=Instrument+Sans:wght@400;500;600&display=swap');

:root {
  --paper: #F5F0E6;
  --paper-deep: #ECE5D6;
  --card: #FBF8F1;
  --ink: #2B2924;
  --ink-soft: #6E6a5e;
  --line: #DDD4C1;
  --moss: #3E5A47;
  --moss-dark: #31483A;
}

html, body, [class*="css"], .stApp {
  font-family: 'Instrument Sans', sans-serif;
  color: var(--ink);
}
.stApp { background: var(--paper); }

#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none; }
header[data-testid="stHeader"] { background: transparent; }
.block-container { max-width: 760px; padding-top: 3.5rem; padding-bottom: 5rem; }

h1, h2, h3 { font-family: 'Newsreader', serif; font-weight: 500; letter-spacing: -0.01em; color: var(--ink); }
.masthead h1 { font-size: 2.6rem; line-height: 1.1; margin: 0 0 .5rem; }
.masthead p { color: var(--ink-soft); font-size: 1.02rem; max-width: 34rem; margin: 0 0 2rem; }

/* Inputs */
.stTextInput input, .stSelectbox [data-baseweb="select"] > div {
  background: var(--card); border: 1px solid var(--line); border-radius: 8px; color: var(--ink);
}
.stTextInput input:focus { border-color: var(--moss); box-shadow: 0 0 0 1px var(--moss); }
[data-testid="stFileUploaderDropzone"] { background: var(--card); border: 1px dashed #C9BFA8; border-radius: 8px; }
[data-testid="stWidgetLabel"] p { font-size: .88rem; color: var(--ink-soft); }

/* Source switch */
div[role="radiogroup"] { gap: .4rem; }
div[role="radiogroup"] label {
  background: transparent; border: 1px solid var(--line); border-radius: 999px; padding: .25rem .9rem;
}
div[role="radiogroup"] label:has(input:checked) { background: var(--moss); border-color: var(--moss); }
div[role="radiogroup"] label:has(input:checked) p { color: #F5F0E6; }
div[role="radiogroup"] label > div:first-child { display: none; }

/* Buttons */
.stButton > button, .stFormSubmitButton > button {
  background: var(--moss); color: #F5F0E6; border: none; border-radius: 8px;
  padding: .6rem 1.4rem; font-weight: 500; transition: background .15s;
}
.stButton > button:hover { background: var(--moss-dark); color: #fff; }
.stButton > button[kind="secondary"] { background: transparent; color: var(--ink-soft); border: 1px solid var(--line); }
.stButton > button[kind="secondary"]:hover { background: var(--paper-deep); color: var(--ink); }
:focus-visible { outline: 2px solid var(--moss); outline-offset: 2px; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 1.6rem; border-bottom: 1px solid var(--line); }
.stTabs [data-baseweb="tab"] { padding: .6rem 0; color: var(--ink-soft); background: transparent; }
.stTabs [aria-selected="true"] { color: var(--ink); }
.stTabs [data-baseweb="tab-highlight"] { background: var(--moss); height: 2px; }
.stTabs [data-baseweb="tab-border"] { display: none; }

/* Result title + panels */
.result-title { font-family: 'Newsreader', serif; font-size: 1.9rem; line-height: 1.2; margin: 2rem 0 1rem; }
.panel { background: var(--card); border: 1px solid var(--line); border-radius: 10px; padding: 1.3rem 1.5rem; line-height: 1.7; }
.panel p:last-child, .panel ul:last-child { margin-bottom: 0; }
.transcript { max-height: 28rem; overflow-y: auto; white-space: pre-wrap; font-size: .93rem; color: #433f36; }
.empty { color: var(--ink-soft); font-style: italic; }

/* Chat */
[data-testid="stChatMessage"] { background: transparent; padding: .5rem 0; }
[data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"] { display: none; }
[data-testid="stChatMessage"][aria-label*="user"] { 
  background: var(--paper-deep); border-radius: 10px; padding: .7rem 1rem; }
[data-testid="stChatInput"] { background: var(--card); border: 1px solid var(--line); border-radius: 10px; }

[data-testid="stStatusWidget"], [data-testid="stSpinner"] { color: var(--ink-soft); }
hr { border-color: var(--line); }
</style>
""",
    unsafe_allow_html=True,
)

# ---------- Helpers ----------
def as_markdown(value) -> str:
    if not value:
        return ""
    if isinstance(value, (list, tuple)):
        return "\n".join(f"- {v}" for v in value)
    return str(value)


def panel(value, empty_text="Nothing found in this recording."):
    text = as_markdown(value)
    if not text.strip():
        st.markdown(f'<div class="panel empty">{empty_text}</div>', unsafe_allow_html=True)
        return
    with st.container(border=True):
        st.markdown(text)


def reset():
    st.session_state.pop("result", None)
    st.session_state.pop("messages", None)


# ---------- Masthead ----------
st.markdown(
    """
<div class="masthead">
  <h1>Video Notes</h1>
  <p>Turn a recording into a summary, action items and decisions, then ask it questions.</p>
</div>
""",
    unsafe_allow_html=True,
)

# ---------- Input ----------
result = st.session_state.get("result")

if result is None:
    mode = st.radio("Source", ["YouTube link", "Upload a file"], horizontal=True, label_visibility="collapsed")

    source, upload = None, None
    if mode == "YouTube link":
        source = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...")
    else:
        upload = st.file_uploader(
            "Audio or video file",
            type=["mp3", "wav", "m4a", "mp4", "mov", "mkv", "webm"],
        )

    language = st.selectbox("Spoken language", ["english", "hinglish", "nepangrezi"], format_func=str.capitalize)

    if st.button("Analyze recording"):
        if mode == "YouTube link" and not (source or "").strip():
            st.warning("Paste a YouTube link to continue.")
        elif mode == "Upload a file" and upload is None:
            st.warning("Choose a file to continue.")
        else:
            tmp_path = None
            try:
                if upload is not None:
                    suffix = os.path.splitext(upload.name)[1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
                        f.write(upload.getbuffer())
                        tmp_path = f.name
                    source = tmp_path

                with st.spinner("Transcribing and analyzing. Longer recordings take a few minutes."):
                    st.session_state.result = run_pipeline(source.strip(), language)
                st.session_state.messages = []
                st.rerun()
            except Exception as e:
                st.error(f"Couldn't process this recording: {e}")
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)

# ---------- Results ----------
else:
    st.markdown(f'<div class="result-title">{result["title"]}</div>', unsafe_allow_html=True)

    tab_sum, tab_act, tab_dec, tab_q, tab_tr, tab_chat = st.tabs(
        ["Summary", "Action items", "Decisions", "Open questions", "Transcript", "Ask"]
    )

    with tab_sum:
        panel(result["summary"])
    with tab_act:
        panel(result["action_items"], "No action items were mentioned.")
    with tab_dec:
        panel(result["key_decisions"], "No decisions were made in this recording.")
    with tab_q:
        panel(result["open_questions"], "No open questions were raised.")
    with tab_tr:
        st.markdown(
            f'<div class="panel transcript">{result["transcript"]}</div>',
            unsafe_allow_html=True,
        )
        st.download_button("Download transcript", result["transcript"], file_name="transcript.txt")

    with tab_chat:
        messages = st.session_state.setdefault("messages", [])
        if not messages:
            st.markdown(
                '<p class="empty">Ask anything about the recording, for example "What deadline was agreed?"</p>',
                unsafe_allow_html=True,
            )
        for m in messages:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])

        if question := st.chat_input("Ask about this recording"):
            messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)
            with st.chat_message("assistant"):
                with st.spinner("Searching the transcript"):
                    answer = ask_question(result["rag_chain"], question)
                st.markdown(answer)
            messages.append({"role": "assistant", "content": answer})

    st.write("")
    st.button("Start a new recording", type="secondary", on_click=reset)