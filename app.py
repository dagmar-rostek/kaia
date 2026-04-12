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
                  t, build_system_prompt, build_onboarding_prompt, OnboardingAnalyzer,
                  SurveyStore, GSE_ITEMS_DE, GSE_ITEMS_EN, GSE_SCALE_DE, GSE_SCALE_EN)
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
if "survey_store"         not in st.session_state:
    st.session_state.survey_store = None
if "onboarding_started"   not in st.session_state:
    st.session_state.onboarding_started = False
if "show_post_first_gse"  not in st.session_state:
    st.session_state.show_post_first_gse = False
if "post_gse_user_id"     not in st.session_state:
    st.session_state.post_gse_user_id = None

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
            is_first_session = (p.session_count == 1)
            if st.session_state.session and st.session_state.provider:
                with st.spinner(t("end_spinner", lang)):
                    store.close_session(st.session_state.session, p)
                    analyzer = SessionAnalyzer(memory)
                    analyzer.analyze_and_save(
                        session=st.session_state.session,
                        profile=p,
                        provider=st.session_state.provider,
                    )
            # Nach erster Session: GSE-Fragebogen zeigen
            if is_first_session and not st.session_state.survey_store.has_survey(
                p.user_id, "gse", "pre"
            ):
                st.session_state.show_post_first_gse = True
                st.session_state.post_gse_user_id    = p.user_id
            st.session_state.profile            = None
            st.session_state.session            = None
            st.session_state.provider           = None
            st.session_state.stt_provider       = None
            st.session_state.tts_provider       = None
            st.session_state.messages           = []
            st.session_state.kaia_state         = "ready"
            st.session_state.onboarding_started = False
            st.rerun()

# ── Kein Profil ────────────────────────────────────────────────────────────────
if not st.session_state.profile:
    # GSE nach erster Session — erscheint einmalig nach dem ersten Gespräch
    if st.session_state.show_post_first_gse and st.session_state.post_gse_user_id:
        survey_store = st.session_state.survey_store
        gse_user_id  = st.session_state.post_gse_user_id

        st.title(t("survey_gse_title", lang))
        st.info(
            "Danke für dein erstes Gespräch mit KAIA! "
            "Bevor du gehst, bitten wir dich, einen kurzen Fragebogen zur allgemeinen Selbstwirksamkeit auszufüllen (ca. 2 Minuten). "
            "Deine Antworten bilden die wissenschaftliche Baseline für die Studie."
            if lang == "de" else
            "Thank you for your first conversation with KAIA! "
            "Before you go, please fill in a short questionnaire on general self-efficacy (about 2 minutes). "
            "Your answers form the scientific baseline for the study."
        )
        st.caption(t("survey_gse_info", lang))

        gse_items = GSE_ITEMS_DE if lang == "de" else GSE_ITEMS_EN
        gse_scale = GSE_SCALE_DE if lang == "de" else GSE_SCALE_EN

        with st.form("post_first_gse_form"):
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
            submitted = st.form_submit_button(
                t("survey_submit", lang), type="primary", use_container_width=True
            )

        if submitted:
            if any(v is None for v in gse_responses.values()):
                st.error(t("survey_error", lang))
            else:
                survey_store.save_survey(gse_user_id, "gse", "pre", gse_responses)
                st.success(t("survey_done", lang))
                st.session_state.show_post_first_gse = False
                st.session_state.post_gse_user_id    = None
                st.rerun()
        st.stop()

    st.info(t("no_profile_info", lang))
    st.stop()

survey_store = st.session_state.survey_store
profile      = st.session_state.profile

# ── Onboarding: KAIA startet automatisch das erste Gespräch ───────────────────
if (
    profile.session_count == 1
    and not st.session_state.onboarding_started
    and not st.session_state.messages
):
    st.session_state.onboarding_started = True
    _onboarding_system = build_onboarding_prompt(
        name=profile.name,
        context=profile.context or "",
        language=lang,
    )
    _provider = st.session_state.provider
    if _provider:
        with st.spinner(t("llm_spinner", lang)):
            try:
                _trigger = [Message(role="user", content="__start__")]
                _resp = _provider.complete(_trigger, _onboarding_system)
                st.session_state.messages.append(
                    {"role": "assistant", "content": _resp.content}
                )
                session = st.session_state.session
                store.add_message(
                    session, "assistant", _resp.content,
                    tokens=_resp.tokens_used or 0,
                    latency_ms=_resp.latency_ms or 0,
                )
            except Exception:
                pass
    st.rerun()

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

    is_onboarding = (profile.session_count == 1 and not profile.onboarding_complete)

    # Onboarding: History beginnt mit KAIAs Eröffnungsnachricht (assistant).
    # Die meisten LLM-APIs erfordern jedoch user als erste Rolle → Trigger vorne einsetzen.
    if is_onboarding and history and history[0].role == "assistant":
        history = [Message(role="user", content="__start__")] + history

    if is_onboarding:
        system_prompt = build_onboarding_prompt(
            name=profile.name,
            context=profile.context or "",
            language=lang,
        )
    else:
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

            # [ONBOARDING_COMPLETE] erkennen und Analyse triggern
            onboarding_just_finished = (
                is_onboarding and "[ONBOARDING_COMPLETE]" in response.content
            )
            # Token aus der angezeigten Antwort entfernen
            display_content = response.content.replace("[ONBOARDING_COMPLETE]", "").strip()

            st.session_state.messages.append({
                "role": "assistant",
                "content": display_content,
            })
            store.add_message(session, "user", user_input)
            store.add_message(
                session, "assistant", display_content,
                tokens=response.tokens_used or 0,
                latency_ms=response.latency_ms or 0,
            )

            if onboarding_just_finished:
                with st.spinner("KAIA analysiert dein Profil..." if lang == "de" else "KAIA is analyzing your profile..."):
                    analyzer = OnboardingAnalyzer()
                    result = analyzer.analyze(
                        messages=st.session_state.messages,
                        provider=provider,
                        language=lang,
                    )
                    # GSE-Score speichern
                    survey_store = st.session_state.survey_store
                    survey_store.save_survey(
                        profile.user_id, "gse", "pre",
                        {str(k): v for k, v in result["gse_scores"].items()}
                    )
                    # Profil aktualisieren
                    profile.identified_strengths    = result["strengths"]
                    profile.identified_blind_spots  = result["blind_spots"]
                    profile.problem_solving_profile = result["problem_solving_profile"]
                    profile.onboarding_complete     = True
                    store.save_profile(profile)
                    st.session_state.profile = profile

            if not st.session_state.voice_mode:
                with st.chat_message("assistant"):
                    st.markdown(display_content)

            if tts:
                st.session_state.kaia_state = "speaking"
                try:
                    synthesis = tts.synthesize(display_content)
                    st.session_state.last_audio = synthesis.audio_bytes
                except Exception as e:
                    st.warning(t("tts_error", lang, error=e))

        except Exception as e:
            st.error(t("llm_error", lang, error=e))

    st.session_state.kaia_state = "ready"
    st.rerun()
