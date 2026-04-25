import streamlit as st
from datetime import datetime

st.set_page_config(page_title="RiskPulse — Risk Intelligence Dashboard", layout="wide")

st.markdown("""
<style>
body { background-color: #0d1b2a; color: #e0e6f0; }
.stApp { background-color: #0d1b2a; }
h1, h2, h3 { color: #00b4d8; }
.stMarkdown h2 { color: #00b4d8; border-bottom: 1px solid #00b4d8; padding-bottom: 4px; }
.stTextInput > div > div > input { background-color: #1a2a3a; color: #e0e6f0; }
</style>
""", unsafe_allow_html=True)


def _init_state():
    defaults = {
        "events": [],
        "analyses": [],
        "briefing": "",
        "chat_instance": None,
        "messages": [],
        "last_updated": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


_init_state()

# ── Header ──────────────────────────────────────────────────────────────────
col_title, col_meta, col_btn = st.columns([4, 3, 1])
with col_title:
    st.title("RiskPulse")
    st.caption("Real-Time Financial News Risk Intelligence")
with col_meta:
    if st.session_state.last_updated:
        st.markdown(f"**Last updated:** {st.session_state.last_updated}")
    if st.session_state.analyses:
        from frontend.components import render_risk_level
        render_risk_level(st.session_state.analyses)
with col_btn:
    refresh = st.button("Refresh", type="primary")

if refresh:
    with st.spinner("Agents analyzing risk landscape..."):
        try:
            from pipeline import run_pipeline
            events, analyses, briefing_text, chat = run_pipeline()
            st.session_state.events = events
            st.session_state.analyses = analyses
            st.session_state.briefing = briefing_text
            st.session_state.chat_instance = chat
            st.session_state.messages = []
            st.session_state.last_updated = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        except Exception as e:
            st.error(f"Pipeline error: {e}")

# ── Sidebar ──────────────────────────────────────────────────────────────────
from frontend.components import render_event_sidebar
render_event_sidebar(st.session_state.events, st.session_state.analyses)

# ── Main Tabs ────────────────────────────────────────────────────────────────
tab_briefing, tab_chat = st.tabs(["Risk Briefing", "Chat"])

with tab_briefing:
    if st.session_state.briefing:
        st.markdown(st.session_state.briefing)
    else:
        st.info("Click **Refresh** to generate a risk briefing.")

with tab_chat:
    if not st.session_state.chat_instance:
        st.info("Generate a briefing first by clicking **Refresh**.")
    else:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        user_input = st.chat_input("Ask about today's risk landscape...")
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                with st.spinner("Analyzing..."):
                    response = st.session_state.chat_instance.chat(user_input)
                st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
