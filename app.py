"""
KAIA – Kinetic AI Agent
Streamlit App — MVP Interface

Run with: streamlit run app.py
"""

import streamlit as st
from dotenv import load_dotenv
from providers import get_provider, Message
from core import ProfileStore, NeuroadaptiveMode

load_dotenv()

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="KAIA",
    page_icon="✦",
    layout="centered",
)

# ── Session state defaults ─────────────────────────────────────────────────────
if "store"    not in st.session_state:
    st.session_state.store = ProfileStore()
if "profile"  not in st.session_state:
    st.session_state.profile = None
if "session"  not in st.session_state:
    st.session_state.session = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "provider" not in st.session_state:
    st.session_state.provider = None

store = st.session_state.store

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("✦ KAIA")
st.caption("Keen · Adaptive · Intelligent · Aware")
st.divider()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Setup")

    # Provider selection
    provider_name = st.selectbox(
        "LLM Provider",
        options=["claude", "mistral", "ollama"],
        index=0,
    )

    # User profile
    st.subheader("Profile")
    name    = st.text_input("Your name", placeholder="e.g. Dagmar")
    context = st.text_input("What are you working on?", placeholder="e.g. studying for my thesis")

    if st.button("Start session", type="primary", use_container_width=True):
        if not name:
            st.error("Please enter your name.")
        else:
            try:
                # Create profile and provider
                profile  = store.create_profile(name=name, context=context)
                provider = get_provider(provider_name)
                session  = store.start_session(profile, provider.name, provider.model)

                st.session_state.profile  = profile
                st.session_state.session  = session
                st.session_state.provider = provider
                st.session_state.messages = []
                st.success(f"Session started with {provider_name}.")
            except Exception as e:
                st.error(f"Could not start session: {e}")

    # Show active profile info
    if st.session_state.profile:
        st.divider()
        p = st.session_state.profile
        st.caption(f"**User:** {p.name}")
        st.caption(f"**Context:** {p.context or '—'}")
        st.caption(f"**Mode:** {p.current_mode.value}")
        st.caption(f"**Sessions:** {p.session_count}")

        if st.button("End session", use_container_width=True):
            if st.session_state.session:
                store.close_session(st.session_state.session, p)
            st.session_state.profile  = None
            st.session_state.session  = None
            st.session_state.provider = None
            st.session_state.messages = []
            st.rerun()

# ── Chat area ──────────────────────────────────────────────────────────────────
if not st.session_state.profile:
    st.info("Set up your profile in the sidebar to start talking to KAIA.")
    st.stop()

# Display message history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
user_input = st.chat_input("Talk to KAIA...")

if user_input:
    profile  = st.session_state.profile
    session  = st.session_state.session
    provider = st.session_state.provider

    # Show user message immediately
    with st.chat_message("user"):
        st.markdown(user_input)

    # Build message history for the LLM
    st.session_state.messages.append({"role": "user", "content": user_input})
    history = [Message(role=m["role"], content=m["content"]) for m in st.session_state.messages]

    # System prompt (minimal for now — will be replaced by Prompt Builder)
    system_prompt = f"""You are KAIA — a Kinetic AI Agent.
You are an empathic learning companion. Your role is not to lecture,
but to guide the learner to discover answers themselves through thoughtful questions.

Learner name: {profile.name}
Context: {profile.context or 'general learning'}
Current mode: {profile.current_mode.value}

Be warm, curious, and encouraging. Ask one good question rather than giving long explanations.
Respond in the same language the learner uses."""

    # Get response
    with st.chat_message("assistant"):
        with st.spinner("KAIA is thinking..."):
            try:
                response = provider.complete(history, system_prompt)
                st.markdown(response.content)

                # Store message
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response.content,
                })

                # Persist to session record
                store.add_message(session, "user", user_input)
                store.add_message(
                    session, "assistant", response.content,
                    tokens=response.tokens_used or 0,
                    latency_ms=response.latency_ms or 0,
                )

            except Exception as e:
                st.error(f"Error: {e}")
