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
from core import (ProfileStore, MemoryStore, SessionAnalyzer, NeuroadaptiveMode,
                  t, build_system_prompt, SurveyStore,
                  GSE_ITEMS_DE, GSE_ITEMS_EN, PSI_ITEMS_DE, PSI_ITEMS_EN,
                  GSE_SCALE_DE, GSE_SCALE_EN, PSI_SCALE_DE, PSI_SCALE_EN)
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
if "store"          not in st.session_state:
    st.session_state.store = ProfileStore(db_path=DB_PATH)
if "memory"         not in st.session_state:
    st.session_state.memory = MemoryStore(chroma_path=CHROMA_PATH, db_path=DB_PATH)
if "profile"        not in st.session_state:
    st.session_state.profile = None
if "session"        not in st.session_state:
    st.session_state.session = None
if "messages"       not in st.session_state:
    st.session_state.messages = []
if "provider"       not in st.session_state:
    st.session_state.provider = None
if "tts_provider"   not in st.session_state:
    st.session_state.tts_provider = None
if "stt_provider"   not in st.session_state:
    st.session_state.stt_provider = None
if "voice_mode"     not in st.session_state:
    st.session_state.voice_mode = False
if "kaia_state"     not in st.session_state:
    st.session_state.kaia_state = "ready"
if "last_audio"     not in st.session_state:
    st.session_state.last_audio = None
if "audio_counter"  not in st.session_state:
    st.session_state.audio_counter = 0
if "lang"           not in st.session_state:
    st.session_state.lang = "de"
if "theme"          not in st.session_state:
    st.session_state.theme = "dark"
if "consent_given"  not in st.session_state:
    st.session_state.consent_given = False
if "survey_store"   not in st.session_state:
    st.session_state.survey_store = None

store  = st.session_state.store
memory = st.session_state.memory
lang   = st.session_state.lang

if st.session_state.survey_store is None:
    st.session_state.survey_store = SurveyStore(db_path=DB_PATH)

# ── Theme CSS-Injection ────────────────────────────────────────────────────────
_LIGHT_CSS = """
<style>
.stApp { background-color: #f5f7fa; }
.stApp > header { background-color: #f5f7fa !important; }
section[data-testid="stSidebar"] { background-color: #e8ecf1; }
.stApp, .stMarkdown, p, span, label, h1, h2, h3,
div[data-testid="stChatMessage"] { color: #1a1d23 !important; }
.stTextInput input, .stSelectbox div[data-baseweb="select"] {
    background-color: #ffffff !important; color: #1a1d23 !important;
}
div[data-testid="stChatMessage"] { background-color: #e8ecf1 !important; }
</style>
"""

if st.session_state.theme == "light":
    st.markdown(_LIGHT_CSS, unsafe_allow_html=True)

# ── Consent-Popup ──────────────────────────────────────────────────────────────
@st.dialog(t("consent_title", lang), width="large")
def show_consent_dialog():
    st.markdown(t("consent_body", lang))
    checked = st.checkbox(t("consent_checkbox", lang), key="consent_checkbox_widget")
    if st.button(t("consent_button", lang), type="primary", use_container_width=True):
        if checked:
            st.session_state.consent_given = True
            st.rerun()
        else:
            st.error(t("consent_must_check", lang))

if not st.session_state.consent_given:
    show_consent_dialog()
    st.stop()

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("✦ KAIA")
st.caption(t("app_caption", lang))
st.divider()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    # Sprache + Design — ganz oben, nebeneinander
    _col_lang, _col_theme = st.columns(2)
    with _col_lang:
        lang_choice = st.radio(
            t("language_label", lang),
            options=["DE", "EN"],
            index=0 if lang == "de" else 1,
            horizontal=True,
        )
        st.session_state.lang = "de" if lang_choice == "DE" else "en"
        lang = st.session_state.lang
    with _col_theme:
        theme_dark_label  = t("theme_dark", lang)
        theme_light_label = t("theme_light", lang)
        theme_choice = st.radio(
            t("theme_label", lang),
            options=[theme_dark_label, theme_light_label],
            index=0 if st.session_state.theme == "dark" else 1,
            horizontal=True,
        )
        new_theme = "dark" if theme_choice == theme_dark_label else "light"
        if new_theme != st.session_state.theme:
            st.session_state.theme = new_theme
            st.rerun()

    st.header(t("setup_header", lang))

    provider_name = st.selectbox(
        t("llm_provider_label", lang),
        options=["claude", "mistral", "ollama"],
        index=0,
    )

    # ── Voice-Modus Toggle ─────────────────────────────────────────────────────
    st.divider()
    st.subheader(t("input_header", lang))
    if not WHISPER_AVAILABLE:
        st.caption(t("voice_local_only", lang))
        voice_mode = False
        st.session_state.voice_mode = False
    else:
        voice_mode = st.toggle(t("voice_toggle", lang), value=st.session_state.voice_mode)
        st.session_state.voice_mode = voice_mode

    if voice_mode:
        st.caption(t("stt_caption", lang))

        st.subheader(t("tts_header", lang))
        tts_options = [t("tts_none", lang)] + AVAILABLE_TTS_PROVIDERS
        tts_name = st.selectbox(t("tts_provider_label", lang), options=tts_options, index=0)

        if tts_name == "voxtral":
            st.caption(t("tts_voxtral_caption", lang))
        elif tts_name == "elevenlabs":
            st.warning(t("tts_elevenlabs_warn", lang))

        tts_none = t("tts_none", lang)
        if tts_name != tts_none:
            try:
                tts_preview = get_tts_provider(tts_name)
                # Stimmen nach Sprache filtern
                voice_lang_filter = "de" if lang == "de" else "en"
                voices = tts_preview.list_voices(language=voice_lang_filter) or tts_preview.list_voices()
                voice_options = {v.name: v.voice_id for v in voices}
                selected_voice_name = st.selectbox(t("voice_label", lang), options=list(voice_options.keys()))
                selected_voice_id = voice_options[selected_voice_name]
            except Exception as e:
                st.error(f"TTS: {e}")
                tts_name = tts_none
    else:
        tts_name = t("tts_none", lang)
        tts_none = tts_name

    # ── User Profile ───────────────────────────────────────────────────────────
    st.divider()
    st.subheader(t("profile_header", lang))
    name    = st.text_input(t("name_label", lang), placeholder=t("name_placeholder", lang))
    pin     = st.text_input(t("pin_label", lang), placeholder=t("pin_placeholder", lang),
                            type="password", max_chars=4)
    context = st.text_input(t("context_label", lang), placeholder=t("context_placeholder", lang))

    if name and pin and len(pin) == 4 and pin.isdigit():
        existing = store.find_by_pin(name, pin)
        if existing:
            st.caption(t("returning_user", lang, name=existing.name, n=existing.session_count + 1))

    if st.button(t("start_button", lang), type="primary", use_container_width=True):
        if not name:
            st.error(t("start_error_name", lang))
        elif not pin or len(pin) != 4 or not pin.isdigit():
            st.error(t("start_error_pin", lang))
        else:
            try:
                pin_uid = store.pin_user_id(name, pin)
                profile = store.find_by_pin(name, pin)
                if profile:
                    if context and context != profile.context:
                        profile.context = context
                        store.save_profile(profile)
                else:
                    profile = store.create_profile(name=name, context=context, user_id=pin_uid)

                llm_provider = get_provider(provider_name)
                session = store.start_session(profile, llm_provider.name, llm_provider.model)

                stt = get_stt_provider("whisper") if voice_mode else None

                tts = None
                if voice_mode and tts_name != tts_none:
                    try:
                        tts = get_tts_provider(tts_name, voice_id=selected_voice_id)
                    except Exception as e:
                        st.warning(f"TTS: {e}")

                st.session_state.profile      = profile
                st.session_state.session      = session
                st.session_state.provider     = llm_provider
                st.session_state.stt_provider = stt
                st.session_state.tts_provider = tts
                st.session_state.messages     = []
                st.session_state.kaia_state   = "ready"
                st.success(t("start_success", lang, n=profile.session_count, provider=provider_name))
            except Exception as e:
                st.error(t("start_fail", lang, error=e))

    # ── Aktives Profil ─────────────────────────────────────────────────────────
    if st.session_state.profile:
        st.divider()
        p = st.session_state.profile
        st.caption(f"{t('profile_user', lang)} {p.name}")
        st.caption(f"{t('profile_context', lang)} {p.context or '—'}")
        st.caption(f"{t('profile_mode', lang)} {p.current_mode.value}")
        st.caption(f"{t('profile_sessions', lang)} {p.session_count}")
        if st.session_state.tts_provider:
            st.caption(f"{t('profile_tts', lang)} {st.session_state.tts_provider.name}")

        if st.button(t("end_button", lang), use_container_width=True):
            if st.session_state.session and st.session_state.provider:
                with st.spinner(t("end_spinner", lang)):
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
    st.info(t("no_profile_info", lang))
    st.stop()

# ── Baseline-Messung (Pre-Survey) ──────────────────────────────────────────────
# Erscheint einmalig vor dem ersten Gespräch — GSE + PSI als Pflichtmessung

survey_store = st.session_state.survey_store
profile      = st.session_state.profile

if not survey_store.has_pre_surveys(profile.user_id):
    st.title(t("survey_title", lang))
    st.info(t("survey_intro", lang))

    gse_items  = GSE_ITEMS_DE  if lang == "de" else GSE_ITEMS_EN
    gse_scale  = GSE_SCALE_DE  if lang == "de" else GSE_SCALE_EN
    psi_items  = PSI_ITEMS_DE  if lang == "de" else PSI_ITEMS_EN
    psi_scale  = PSI_SCALE_DE  if lang == "de" else PSI_SCALE_EN

    with st.form("pre_survey_form"):
        # GSE
        st.subheader(t("survey_gse_title", lang))
        st.caption(t("survey_gse_info", lang))
        gse_responses = {}
        for i, item in enumerate(gse_items):
            gse_responses[i] = st.radio(
                f"{i+1}. {item}",
                options=list(gse_scale.keys()),
                format_func=lambda x, s=gse_scale: s[x],
                index=None,
                horizontal=True,
                key=f"gse_{i}",
            )

        st.divider()

        # PSI
        st.subheader(t("survey_psi_title", lang))
        st.caption(t("survey_psi_info", lang))
        psi_responses = {}
        for i, (item, _) in enumerate(psi_items):
            psi_responses[i] = st.radio(
                f"{i+1}. {item}",
                options=list(psi_scale.keys()),
                format_func=lambda x, s=psi_scale: s[x],
                index=None,
                horizontal=True,
                key=f"psi_{i}",
            )

        submitted = st.form_submit_button(t("survey_submit", lang), type="primary", use_container_width=True)

    if submitted:
        # Validierung: alle Items beantwortet?
        gse_missing = any(v is None for v in gse_responses.values())
        psi_missing = any(v is None for v in psi_responses.values())
        if gse_missing or psi_missing:
            st.error(t("survey_error", lang))
        else:
            survey_store.save_survey(profile.user_id, "gse", "pre", gse_responses)
            survey_store.save_survey(profile.user_id, "psi", "pre", psi_responses)
            st.success(t("survey_done", lang))
            st.rerun()

    st.stop()

# ── Voice-Modus: Gesprächsansicht ──────────────────────────────────────────────
if st.session_state.voice_mode:
    _state_key = {
        "ready":    "voice_ready",
        "thinking": "voice_thinking",
        "speaking": "voice_speaking",
    }.get(st.session_state.kaia_state, "voice_ready")
    st.info(t(_state_key, lang))

    # Audio aus letzter Antwort abspielen
    if st.session_state.last_audio:
        st.audio(st.session_state.last_audio, format="audio/mp3", autoplay=True)
        st.session_state.last_audio = None

    # Letzten Austausch anzeigen
    if st.session_state.messages:
        for msg in st.session_state.messages[-2:]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    st.divider()

    audio_key = f"mic_{st.session_state.audio_counter}"
    if st.session_state.kaia_state == "ready":
        audio_bytes = st.audio_input(t("mic_label", lang), key=audio_key)
    else:
        st.audio_input(t("mic_label", lang), key=audio_key, disabled=True)
        audio_bytes = None

    user_input = None
    if audio_bytes:
        st.session_state.audio_counter += 1
        stt = st.session_state.stt_provider
        if stt:
            with st.spinner(t("stt_spinner", lang)):
                try:
                    result = stt.transcribe(audio_bytes.read())
                    user_input = result.text
                    st.caption(t("stt_recognized", lang, text=user_input))
                except Exception as e:
                    st.error(t("stt_error", lang, error=e))
                    st.session_state.kaia_state = "ready"

# ── Text-Modus: Chat-Ansicht ───────────────────────────────────────────────────
else:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    user_input = st.chat_input(t("chat_input", lang))

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
    system_prompt = build_system_prompt(
        profile=profile,
        memory_context=memory_context,
        language=lang,
    )

    st.session_state.kaia_state = "thinking"
    with st.spinner(t("llm_spinner", lang)):
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

            if not st.session_state.voice_mode:
                with st.chat_message("assistant"):
                    st.markdown(response.content)

            if tts:
                st.session_state.kaia_state = "speaking"
                try:
                    synthesis = tts.synthesize(response.content)
                    st.session_state.last_audio = synthesis.audio_bytes
                except Exception as e:
                    st.warning(t("tts_error", lang, error=e))

        except Exception as e:
            st.error(t("llm_error", lang, error=e))

    st.session_state.kaia_state = "ready"
    st.rerun()
