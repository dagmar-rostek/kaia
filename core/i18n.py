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
        "theme_label":          "Design",
        "theme_dark":           "Dunkel",
        "theme_light":          "Hell",

        # Consent / DSGVO-Popup
        "consent_title":        "Datenschutz & Hinweise",
        "consent_body": (
            "**Datenschutzhinweis (DSGVO)**\n\n"
            "KAIA speichert folgende Daten lokal auf diesem Server:\n"
            "- Name, Lernkontext und Sitzungsverläufe (SQLite)\n"
            "- Semantische Beobachtungen als Vektoren (ChromaDB)\n\n"
            "Es werden **keine** personenbezogenen Daten an Dritte weitergegeben, "
            "außer an den von dir gewählten KI-Anbieter (Anthropic, Mistral oder lokal via Ollama) "
            "zur Verarbeitung deiner Eingaben.\n\n"
            "Wenn du Sprachausgabe (TTS) über **ElevenLabs** aktivierst, werden Texte "
            "an US-Server übertragen — nur mit deiner ausdrücklichen Einwilligung.\n\n"
            "---\n\n"
            "**Hinweis gemäß EU AI Act (Art. 52)**\n\n"
            "Du interagierst mit einem **KI-System**. "
            "KAIA ist ein empathischer Lernbegleiter auf Basis großer Sprachmodelle. "
            "Antworten können unvollständig oder fehlerhaft sein — "
            "bitte behalte stets dein eigenes Urteilsvermögen.\n\n"
            "---\n\n"
            "Mit Klick auf *Verstanden & Zustimmen* bestätigst du, "
            "dass du diese Hinweise gelesen und verstanden hast."
        ),
        "consent_checkbox":     "Ich habe die Datenschutzhinweise gelesen und stimme zu.",
        "consent_button":       "Verstanden & Zustimmen",
        "consent_must_check":   "Bitte setze den Haken, um fortzufahren.",

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
        "pin_label":            "PIN (4 Ziffern)",
        "pin_placeholder":      "••••",
        "returning_user":       "Willkommen zurück, {name} — Session {n}.",
        "start_button":         "Session starten",
        "start_error_name":     "Bitte gib deinen Namen ein.",
        "start_error_pin":      "Bitte gib eine 4-stellige PIN ein (nur Ziffern).",
        "start_error_pin_wrong":"Falscher Name oder falsche PIN.",
        "start_success":        "Session {n} gestartet mit {provider}.",
        "start_fail":           "Session konnte nicht gestartet werden: {error}",

        # Survey / Baseline-Messung
        "survey_title":         "Baseline-Messung vor dem ersten Gespräch",
        "survey_intro":         "Bevor du mit KAIA sprichst, bitten wir dich, zwei kurze Fragebögen auszufüllen. Das dauert ca. 3–5 Minuten. Deine Antworten bilden die wissenschaftliche Baseline für die Auswertung.",
        "survey_gse_title":     "Teil 1: Allgemeine Selbstwirksamkeit (GSE)",
        "survey_gse_info":      "Schwarzer & Jerusalem, 1995 — 10 Aussagen, Skala 1–4",
        "survey_psi_title":     "Teil 2: Wahrgenommene Problemlösekompetenz (PSI)",
        "survey_psi_info":      "Adaptiert nach Heppner & Petersen, 1982 — 6 Aussagen, Skala 1–5",
        "survey_submit":        "Weiter zum Gespräch",
        "survey_error":         "Bitte beantworte alle Fragen bevor du weiter machst.",
        "survey_post_title":    "Abschlussmessung",
        "survey_post_intro":    "Du hast mindestens 3 Sessions mit KAIA abgeschlossen. Bitte fülle jetzt die Abschlussmessung aus — sie ist der zweite Teil der wissenschaftlichen Auswertung.",
        "survey_post_button":   "Abschlussmessung starten",
        "survey_done":          "Vielen Dank — deine Antworten wurden gespeichert.",

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

        # Auswertungsseite
        "auswertung_title":        "Dein Lernprofil",
        "auswertung_locked":       "Die Auswertung ist nach Abschluss des Erstgesprächs verfügbar.",
        "auswertung_radar_title":  "Selbstwirksamkeitsprofil",
        "auswertung_strengths":    "Deine Stärken",
        "auswertung_blindspots":   "Wachstumsfelder",
        "auswertung_psp":          "Dein Problemlöseprofil",
        "auswertung_gse_total":    "GSE-Gesamtscore",
        "auswertung_gse_max":      "von 40 möglichen Punkten",
        "auswertung_no_profile":   "Bitte starte eine Session um dein Profil zu laden.",
        "auswertung_gse_dims": [
            "Widerstände überwinden",
            "Probleme durch Bemühen lösen",
            "Ziele verwirklichen",
            "Unerwartete Situationen",
            "Überraschungen bewältigen",
            "Gelassenheit & Vertrauen",
            "Allgemeine Resilienz",
            "Lösungen finden",
            "Neues bewältigen",
            "Eigenständigkeit",
        ],

        # Landing-Page / Login / Registrierung
        "landing_subtitle":       "Prototyp · Masterarbeit Dagmar Rostek · SRH Fernhochschule Riedlingen",
        "login_tab":              "Anmelden",
        "register_tab":           "Registrieren",
        "login_username":         "Benutzername",
        "login_password":         "Passwort",
        "login_button":           "Anmelden",
        "login_error":            "Benutzername oder Passwort falsch.",
        "register_email":         "E-Mail (optional)",
        "register_username":      "Benutzername wählen",
        "register_password":      "Passwort",
        "register_password2":     "Passwort wiederholen",
        "register_button":        "Konto erstellen",
        "register_error_fields":  "Bitte Benutzername und Passwort ausfüllen.",
        "register_error_match":   "Passwörter stimmen nicht überein.",
        "register_error_short":   "Passwort muss mindestens 6 Zeichen haben.",
        "register_error_taken":   "Benutzername bereits vergeben.",
        "context_greeting":       "Hallo {name} — schön, dass du dabei bist.",
        "context_title":          "Woran möchtest du arbeiten?",
        "context_caption":        "Damit kann KAIA unsere Gespräche auf dein Thema abstimmen.",
        "context_placeholder":    "z.B. Masterthesis, Statistik, Programmierung ...",
        "context_button":         "Los geht's →",
        "context_error":          "Bitte gib dein Lernthema ein.",
        "logout_button":          "Abmelden",

        # System-Prompt Sprache
        "system_prompt_lang":   "Antworte immer auf Deutsch.",
    },
    "en": {
        # General
        "app_caption":          "Keen · Adaptive · Intelligent · Aware",
        "language_label":       "Language",
        "theme_label":          "Theme",
        "theme_dark":           "Dark",
        "theme_light":          "Light",

        # Consent / Privacy popup
        "consent_title":        "Privacy & Notices",
        "consent_body": (
            "**Privacy Notice (GDPR)**\n\n"
            "KAIA stores the following data locally on this server:\n"
            "- Name, learning context and session history (SQLite)\n"
            "- Semantic observations as vectors (ChromaDB)\n\n"
            "No personal data is shared with third parties except the AI provider "
            "you selected (Anthropic, Mistral, or local via Ollama) for processing your inputs.\n\n"
            "If you enable voice output (TTS) via **ElevenLabs**, text will be "
            "transmitted to US servers — only with your explicit consent.\n\n"
            "---\n\n"
            "**Notice under EU AI Act (Art. 52)**\n\n"
            "You are interacting with an **AI system**. "
            "KAIA is an empathic learning companion based on large language models. "
            "Responses may be incomplete or incorrect — "
            "please always apply your own judgement.\n\n"
            "---\n\n"
            "By clicking *Understood & Agree* you confirm that you have read "
            "and understood these notices."
        ),
        "consent_checkbox":     "I have read the privacy notices and agree.",
        "consent_button":       "Understood & Agree",
        "consent_must_check":   "Please tick the box to continue.",

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

        # Survey / Baseline measurement
        "survey_title":         "Baseline measurement before your first conversation",
        "survey_intro":         "Before talking to KAIA, please fill in two short questionnaires. This takes about 3–5 minutes. Your answers form the scientific baseline for the study evaluation.",
        "survey_gse_title":     "Part 1: General Self-Efficacy (GSE)",
        "survey_gse_info":      "Schwarzer & Jerusalem, 1995 — 10 items, scale 1–4",
        "survey_psi_title":     "Part 2: Perceived Problem-Solving Competence (PSI)",
        "survey_psi_info":      "Adapted from Heppner & Petersen, 1982 — 6 items, scale 1–5",
        "survey_submit":        "Continue to conversation",
        "survey_error":         "Please answer all questions before continuing.",
        "survey_post_title":    "Post-measurement",
        "survey_post_intro":    "You have completed at least 3 sessions with KAIA. Please fill in the post-measurement now — it is the second part of the scientific evaluation.",
        "survey_post_button":   "Start post-measurement",
        "survey_done":          "Thank you — your answers have been saved.",

        # Profile
        "profile_header":       "Profile",
        "name_label":           "Your name",
        "name_placeholder":     "e.g. Dagmar",
        "context_label":        "What are you working on?",
        "context_placeholder":  "e.g. studying for my thesis",
        "pin_label":            "PIN (4 digits)",
        "pin_placeholder":      "••••",
        "returning_user":       "Welcome back, {name} — Session {n}.",
        "start_button":         "Start session",
        "start_error_name":     "Please enter your name.",
        "start_error_pin":      "Please enter a 4-digit PIN (numbers only).",
        "start_error_pin_wrong":"Incorrect name or PIN.",
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

        # Profile page
        "auswertung_title":        "Your Learning Profile",
        "auswertung_locked":       "The profile is available after completing the initial conversation.",
        "auswertung_radar_title":  "Self-Efficacy Profile",
        "auswertung_strengths":    "Your Strengths",
        "auswertung_blindspots":   "Growth Areas",
        "auswertung_psp":          "Your Problem-Solving Profile",
        "auswertung_gse_total":    "GSE Total Score",
        "auswertung_gse_max":      "out of 40 possible points",
        "auswertung_no_profile":   "Please start a session to load your profile.",
        "auswertung_gse_dims": [
            "Overcoming obstacles",
            "Solving problems through effort",
            "Achieving goals",
            "Unexpected situations",
            "Coping with surprises",
            "Calm & self-trust",
            "General resilience",
            "Finding solutions",
            "Handling new things",
            "Independence",
        ],

        # Landing-Page / Login / Registration
        "landing_subtitle":       "Prototype · Master's Thesis Dagmar Rostek · SRH Fernhochschule Riedlingen",
        "login_tab":              "Sign in",
        "register_tab":           "Register",
        "login_username":         "Username",
        "login_password":         "Password",
        "login_button":           "Sign in",
        "login_error":            "Incorrect username or password.",
        "register_email":         "E-mail (optional)",
        "register_username":      "Choose a username",
        "register_password":      "Password",
        "register_password2":     "Repeat password",
        "register_button":        "Create account",
        "register_error_fields":  "Please fill in username and password.",
        "register_error_match":   "Passwords do not match.",
        "register_error_short":   "Password must be at least 6 characters.",
        "register_error_taken":   "Username already taken.",
        "context_greeting":       "Hi {name} — great to have you here.",
        "context_title":          "What do you want to work on?",
        "context_caption":        "This helps KAIA tailor our conversations to your topic.",
        "context_placeholder":    "e.g. Master's thesis, Statistics, Programming ...",
        "context_button":         "Let's go →",
        "context_error":          "Please enter your learning topic.",
        "logout_button":          "Log out",

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
