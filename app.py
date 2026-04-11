"""
KAIA – Kinetic AI Agent
Streamlit App — MVP Interface mit Text- und Spracheingabe

Run with: streamlit run app.py
"""

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from providers import get_provider, Message
from core import ProfileStore, MemoryStore, SessionAnalyzer, NeuroadaptiveMode
from voice import get_stt_provider, get_tts_provider, AVAILABLE_TTS_PROVIDERS

load_dotenv()

# Prüfen ob Whisper verfügbar ist (nur lokal, nicht in der Cloud)
try:
    import faster_whisper  # noqa: F401
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

# DATA_DIR: lokal = "data/", Railway = "/app/data" (via Env-Variable)
DATA_DIR    = Path(os.environ.get("DATA_DIR", "data"))
DB_PATH     = DATA_DIR / "kaia.db"
CHROMA_PATH = DATA_DIR / "chroma"

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="KAIA",
    page_icon="✦",
    layout="centered",
)

# ── Session state defaults ─────────────────────────────────────────────────────
if "store"        not in st.session_state:
    st.session_state.store = ProfileStore(db_path=DB_PATH)
if "memory"       not in st.session_state:
    st.session_state.memory = MemoryStore(chroma_path=CHROMA_PATH, db_path=DB_PATH)
if "profile"      not in st.session_state:
    st.session_state.profile = None
if "session"      not in st.session_state:
    st.session_state.session = None
if "messages"     not in st.session_state:
    st.session_state.messages = []
if "provider"     not in st.session_state:
    st.session_state.provider = None
if "tts_provider" not in st.session_state:
    st.session_state.tts_provider = None
if "stt_provider" not in st.session_state:
    st.session_state.stt_provider = None
if "voice_mode"   not in st.session_state:
    st.session_state.voice_mode = False
if "kaia_state"   not in st.session_state:
    st.session_state.kaia_state = "ready"   # ready | thinking | speaking
if "last_audio"     not in st.session_state:
    st.session_state.last_audio = None      # TTS-Bytes für nächsten Render
if "audio_counter"  not in st.session_state:
    st.session_state.audio_counter = 0      # Widget-Key — Reset nach jeder Aufnahme

store  = st.session_state.store
memory = st.session_state.memory

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("✦ KAIA")
st.caption("Keen · Adaptive · Intelligent · Aware")
st.divider()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Setup")

    provider_name = st.selectbox(
        "LLM Provider",
        options=["claude", "mistral", "ollama"],
        index=0,
    )

    # ── Voice-Modus Toggle ─────────────────────────────────────────────────────
    st.divider()
    st.subheader("Eingabe")
    if not WHISPER_AVAILABLE:
        st.caption("Spracheingabe nur lokal verfügbar.")
        voice_mode = False
        st.session_state.voice_mode = False
    else:
        voice_mode = st.toggle("Spracheingabe aktivieren", value=st.session_state.voice_mode)
        st.session_state.voice_mode = voice_mode

    if voice_mode:
        st.caption("STT: Whisper (lokal · DSGVO ✓)")

        st.subheader("Sprachausgabe (TTS)")
        tts_name = st.selectbox(
            "TTS Provider",
            options=["— keiner —"] + AVAILABLE_TTS_PROVIDERS,
            index=0,
            help="Voxtral: EU-Server | ElevenLabs: USA (AVV erforderlich)"
        )

        if tts_name == "voxtral":
            st.caption("Voxtral: EU-gehostet (Mistral AI) · AVV empfohlen")
        elif tts_name == "elevenlabs":
            st.warning("ElevenLabs: US-Server — AVV + Einwilligung erforderlich.")

        if tts_name != "— keiner —":
            try:
                tts = get_tts_provider(tts_name)
                voices = tts.list_voices(language="de") or tts.list_voices()
                voice_options = {v.name: v.voice_id for v in voices}
                selected_voice_name = st.selectbox("Stimme", options=list(voice_options.keys()))
                selected_voice_id = voice_options[selected_voice_name]
            except Exception as e:
                st.error(f"TTS nicht verfügbar: {e}")
                tts_name = "— keiner —"
    else:
        tts_name = "— keiner —"

    # ── User Profile ───────────────────────────────────────────────────────────
    st.divider()
    st.subheader("Profil")
    name    = st.text_input("Dein Name", placeholder="z.B. Dagmar")
    context = st.text_input("Woran arbeitest du?", placeholder="z.B. Masterthesis Data Science")

    if name:
        existing = store.find_by_name(name)
        if existing:
            st.caption(f"Willkommen zurück, {existing.name} — Session {existing.session_count + 1}.")

    if st.button("Session starten", type="primary", use_container_width=True):
        if not name:
            st.error("Bitte gib deinen Namen ein.")
        else:
            try:
                profile = store.find_by_name(name)
                if profile:
                    if context and context != profile.context:
                        profile.context = context
                        store.save_profile(profile)
                else:
                    profile = store.create_profile(name=name, context=context)

                llm_provider = get_provider(provider_name)
                session = store.start_session(profile, llm_provider.name, llm_provider.model)

                stt = get_stt_provider("whisper") if voice_mode else None

                tts = None
                if voice_mode and tts_name != "— keiner —":
                    try:
                        tts = get_tts_provider(tts_name, voice_id=selected_voice_id)
                    except Exception as e:
                        st.warning(f"TTS konnte nicht geladen werden: {e}")

                st.session_state.profile      = profile
                st.session_state.session      = session
                st.session_state.provider     = llm_provider
                st.session_state.stt_provider = stt
                st.session_state.tts_provider = tts
                st.session_state.messages     = []
                st.session_state.kaia_state   = "ready"
                st.success(f"Session {profile.session_count} gestartet mit {provider_name}.")
            except Exception as e:
                st.error(f"Session konnte nicht gestartet werden: {e}")

    # ── Aktives Profil ─────────────────────────────────────────────────────────
    if st.session_state.profile:
        st.divider()
        p = st.session_state.profile
        st.caption(f"**User:** {p.name}")
        st.caption(f"**Kontext:** {p.context or '—'}")
        st.caption(f"**Modus:** {p.current_mode.value}")
        st.caption(f"**Sessions:** {p.session_count}")
        if st.session_state.tts_provider:
            st.caption(f"**TTS:** {st.session_state.tts_provider.name}")

        if st.button("Session beenden", use_container_width=True):
            if st.session_state.session and st.session_state.provider:
                with st.spinner("KAIA reflektiert die Session..."):
                    store.close_session(st.session_state.session, p)
                    analyzer = SessionAnalyzer(memory)
                    analyzer.analyze_and_save(
                        session=st.session_state.session,
                        profile=p,
                        provider=st.session_state.provider,
                    )
            st.session_state.profile      = None
            st.session_state.session      = None
            st.session_state.provider     = None
            st.session_state.stt_provider = None
            st.session_state.tts_provider = None
            st.session_state.messages     = []
            st.session_state.kaia_state   = "ready"
            st.rerun()

# ── Kein Profil ────────────────────────────────────────────────────────────────
if not st.session_state.profile:
    st.info("Richte dein Profil in der Sidebar ein, um mit KAIA zu sprechen.")
    st.stop()

# ── Voice-Modus: Gesprächsansicht ──────────────────────────────────────────────
if st.session_state.voice_mode:
    _STATE_LABELS = {
        "ready":    "🎙️  Bereit — nimm deine Aufnahme auf",
        "thinking": "💭  KAIA denkt...",
        "speaking": "🔊  KAIA spricht...",
    }
    st.info(_STATE_LABELS.get(st.session_state.kaia_state, ""))

    # Audio aus letzter Antwort abspielen (wird nach einem Render gelöscht)
    if st.session_state.last_audio:
        st.audio(st.session_state.last_audio, format="audio/mp3", autoplay=True)
        st.session_state.last_audio = None

    # Letzten Austausch anzeigen (kompakt)
    if st.session_state.messages:
        for msg in st.session_state.messages[-2:]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    st.divider()

    # Mikrofon — Key wechselt nach jeder Aufnahme → Widget wird zurückgesetzt
    audio_key = f"mic_{st.session_state.audio_counter}"
    if st.session_state.kaia_state == "ready":
        audio_bytes = st.audio_input("⏺  Aufnehmen und abspielen zum Senden", key=audio_key)
    else:
        st.audio_input("⏺  Aufnehmen und abspielen zum Senden", key=audio_key, disabled=True)
        audio_bytes = None

    user_input = None
    if audio_bytes:
        st.session_state.audio_counter += 1   # Widget zurücksetzen für nächste Runde
        stt = st.session_state.stt_provider
        if stt:
            with st.spinner("Erkenne Sprache..."):
                try:
                    result = stt.transcribe(audio_bytes.read())
                    user_input = result.text
                    st.caption(f'Erkannt: *"{user_input}"*')
                except Exception as e:
                    st.error(f"Spracherkennung fehlgeschlagen: {e}")
                    st.session_state.kaia_state = "ready"

# ── Text-Modus: Chat-Ansicht ───────────────────────────────────────────────────
else:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Schreib mit KAIA...")

# ── LLM-Aufruf ────────────────────────────────────────────────────────────────
if user_input:
    profile  = st.session_state.profile
    session  = st.session_state.session
    provider = st.session_state.provider
    tts      = st.session_state.tts_provider

    if not st.session_state.voice_mode:
        with st.chat_message("user"):
            st.markdown(user_input)

    st.session_state.messages.append({"role": "user", "content": user_input})
    history = [Message(role=m["role"], content=m["content"]) for m in st.session_state.messages]

    memory_context = memory.build_memory_context(profile.user_id)
    system_prompt = f"""You are KAIA — a Kinetic AI Agent.
You are an empathic learning companion. Your role is not to lecture,
but to guide the learner to discover answers themselves through thoughtful questions.

Learner name: {profile.name}
Context: {profile.context or 'general learning'}
Current mode: {profile.current_mode.value}

{memory_context}

Be warm, curious, and encouraging. Ask one good question rather than giving long explanations.
Respond in the same language the learner uses."""

    st.session_state.kaia_state = "thinking"
    with st.spinner("KAIA denkt..."):
        try:
            response = provider.complete(history, system_prompt)

            st.session_state.messages.append({
                "role": "assistant",
                "content": response.content,
            })

            store.add_message(session, "user", user_input)
            store.add_message(
                session, "assistant", response.content,
                tokens=response.tokens_used or 0,
                latency_ms=response.latency_ms or 0,
            )

            # Im Text-Modus sofort anzeigen
            if not st.session_state.voice_mode:
                with st.chat_message("assistant"):
                    st.markdown(response.content)

            # TTS — Audio in session_state speichern, wird beim nächsten Render abgespielt
            if tts:
                st.session_state.kaia_state = "speaking"
                try:
                    synthesis = tts.synthesize(response.content)
                    st.session_state.last_audio = synthesis.audio_bytes
                except Exception as e:
                    st.warning(f"Sprachausgabe fehlgeschlagen: {e}")

        except Exception as e:
            st.error(f"Fehler: {e}")

    st.session_state.kaia_state = "ready"
    st.rerun()
