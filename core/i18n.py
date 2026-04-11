"""
KAIA – Kinetic AI Agent
Internationalisierung (i18n) — DE / EN

Einfaches Dict-basiertes Übersetzungssystem.
Neue Sprache hinzufügen: neuen Block unter TRANSLATIONS anlegen.
"""

TRANSLATIONS = {
    "de": {
        # Allgemein
        "app_caption":          "Keen · Adaptive · Intelligent · Aware",
        "language_label":       "Sprache",

        # Sidebar Setup
        "setup_header":         "Einstellungen",
        "llm_provider_label":   "LLM Provider",
        "input_header":         "Eingabe",
        "voice_toggle":         "Spracheingabe aktivieren",
        "voice_local_only":     "Spracheingabe nur lokal verfügbar.",
        "stt_caption":          "STT: Whisper (lokal · DSGVO ✓)",
        "tts_header":           "Sprachausgabe (TTS)",
        "tts_provider_label":   "TTS Provider",
        "tts_none":             "— keiner —",
        "tts_voxtral_caption":  "Voxtral: EU-gehostet (Mistral AI) · AVV empfohlen",
        "tts_elevenlabs_warn":  "ElevenLabs: US-Server — AVV + Einwilligung erforderlich.",
        "voice_label":          "Stimme",

        # Profil
        "profile_header":       "Profil",
        "name_label":           "Dein Name",
        "name_placeholder":     "z.B. Dagmar",
        "context_label":        "Woran arbeitest du?",
        "context_placeholder":  "z.B. Masterthesis Data Science",
        "returning_user":       "Willkommen zurück, {name} — Session {n}.",
        "start_button":         "Session starten",
        "start_error_name":     "Bitte gib deinen Namen ein.",
        "start_success":        "Session {n} gestartet mit {provider}.",
        "start_fail":           "Session konnte nicht gestartet werden: {error}",

        # Aktives Profil
        "profile_user":         "**User:**",
        "profile_context":      "**Kontext:**",
        "profile_mode":         "**Modus:**",
        "profile_sessions":     "**Sessions:**",
        "profile_tts":          "**TTS:**",
        "end_button":           "Session beenden",
        "end_spinner":          "KAIA reflektiert die Session...",

        # Chat
        "no_profile_info":      "Richte dein Profil in der Sidebar ein, um mit KAIA zu sprechen.",
        "chat_input":           "Schreib mit KAIA...",
        "voice_ready":          "🎙️  Bereit — nimm deine Aufnahme auf",
        "voice_thinking":       "💭  KAIA denkt...",
        "voice_speaking":       "🔊  KAIA spricht...",
        "mic_label":            "⏺  Aufnehmen und abspielen zum Senden",
        "stt_spinner":          "Erkenne Sprache...",
        "stt_recognized":       'Erkannt: *"{text}"*',
        "stt_error":            "Spracherkennung fehlgeschlagen: {error}",
        "llm_spinner":          "KAIA denkt...",
        "tts_spinner":          "KAIA spricht...",
        "tts_error":            "Sprachausgabe fehlgeschlagen: {error}",
        "llm_error":            "Fehler: {error}",

        # System-Prompt Sprache
        "system_prompt_lang":   "Antworte immer auf Deutsch.",
    },
    "en": {
        # General
        "app_caption":          "Keen · Adaptive · Intelligent · Aware",
        "language_label":       "Language",

        # Sidebar Setup
        "setup_header":         "Settings",
        "llm_provider_label":   "LLM Provider",
        "input_header":         "Input",
        "voice_toggle":         "Enable voice input",
        "voice_local_only":     "Voice input only available locally.",
        "stt_caption":          "STT: Whisper (local · GDPR ✓)",
        "tts_header":           "Voice output (TTS)",
        "tts_provider_label":   "TTS Provider",
        "tts_none":             "— none —",
        "tts_voxtral_caption":  "Voxtral: EU-hosted (Mistral AI) · DPA recommended",
        "tts_elevenlabs_warn":  "ElevenLabs: US servers — DPA + participant consent required.",
        "voice_label":          "Voice",

        # Profile
        "profile_header":       "Profile",
        "name_label":           "Your name",
        "name_placeholder":     "e.g. Dagmar",
        "context_label":        "What are you working on?",
        "context_placeholder":  "e.g. studying for my thesis",
        "returning_user":       "Welcome back, {name} — Session {n}.",
        "start_button":         "Start session",
        "start_error_name":     "Please enter your name.",
        "start_success":        "Session {n} started with {provider}.",
        "start_fail":           "Could not start session: {error}",

        # Active profile
        "profile_user":         "**User:**",
        "profile_context":      "**Context:**",
        "profile_mode":         "**Mode:**",
        "profile_sessions":     "**Sessions:**",
        "profile_tts":          "**TTS:**",
        "end_button":           "End session",
        "end_spinner":          "KAIA is reflecting on the session...",

        # Chat
        "no_profile_info":      "Set up your profile in the sidebar to start talking to KAIA.",
        "chat_input":           "Write to KAIA...",
        "voice_ready":          "🎙️  Ready — record your message",
        "voice_thinking":       "💭  KAIA is thinking...",
        "voice_speaking":       "🔊  KAIA is speaking...",
        "mic_label":            "⏺  Record and play to send",
        "stt_spinner":          "Recognizing speech...",
        "stt_recognized":       'Recognized: *"{text}"*',
        "stt_error":            "Speech recognition failed: {error}",
        "llm_spinner":          "KAIA is thinking...",
        "tts_spinner":          "KAIA is speaking...",
        "tts_error":            "Voice output failed: {error}",
        "llm_error":            "Error: {error}",

        # System prompt language
        "system_prompt_lang":   "Always respond in English.",
    },
}


def t(key: str, lang: str = "de", **kwargs) -> str:
    """
    Gibt den übersetzten String zurück.
    Platzhalter werden via kwargs ersetzt: t("start_success", n=2, provider="claude")
    """
    text = TRANSLATIONS.get(lang, TRANSLATIONS["de"]).get(key, key)
    return text.format(**kwargs) if kwargs else text
