"""
KAIA – Kinetic AI Agent
Session Analyzer — automatische Gedächtnisbildung nach jeder Session

Am Ende einer Session analysiert KAIA den Gesprächsverlauf und schreibt
strukturierte Observations ins Langzeitgedächtnis (SQLite + ChromaDB).

Ablauf:
  1. Session-Nachrichten → kompakter Analyse-Prompt
  2. LLM gibt JSON zurück mit Observations pro Kategorie
  3. Jede Observation → MemoryStore.add_observation()

Die Qualität des Gedächtnisses wächst mit jeder Session.
"""

import json
import re
from dataclasses import dataclass

from .memory_store import MemoryStore
from .models import SessionRecord, UserProfile
from .survey_store import SurveyStore


# Kategorien die KAIA pro Session extrahiert
_ANALYSIS_PROMPT = """Du bist ein interner KAIA-Analysemodul. Analysiere das folgende Gespräch zwischen einem Lernenden und KAIA.

Extrahiere strukturierte Beobachtungen in genau diesem JSON-Format:
{{
  "mood": "Ein Satz über die Stimmung/emotionalen Zustand des Nutzers in dieser Session",
  "learning_style": "Ein Satz über beobachtete Lernpräferenzen (oder null, wenn nicht erkennbar)",
  "strength": "Eine beobachtete Stärke des Nutzers (oder null, wenn nicht erkennbar)",
  "blind_spot": "Eine beobachtete Schwierigkeit oder blinder Fleck (oder null, wenn nicht erkennbar)",
  "general": "Eine weitere relevante Beobachtung (oder null)",
  "sentiment_score": 0.0
}}

Regeln:
- sentiment_score: -1.0 (sehr negativ/frustriert) bis 1.0 (sehr positiv/motiviert), 0.0 = neutral
- Schreibe Observations aus KAIAs Perspektive über den Nutzer, kurz und präzise (1 Satz)
- Verwende die Sprache des Nutzers (Deutsch wenn Deutsch gesprochen wurde, etc.)
- Wenn eine Kategorie nicht erkennbar ist: null (nicht raten)
- Antworte NUR mit dem JSON-Objekt, kein weiterer Text

Nutzername: {name}
Neuroadaptiver Modus am Ende: {mode}

Gesprächsverlauf:
{transcript}"""


@dataclass
class AnalysisResult:
    """Ergebnis einer Session-Analyse."""
    mood: str | None
    learning_style: str | None
    strength: str | None
    blind_spot: str | None
    general: str | None
    sentiment_score: float


class SessionAnalyzer:
    """
    Analysiert einen Session-Verlauf und schreibt Observations ins Gedächtnis.

    Verwendung:
        analyzer = SessionAnalyzer(memory_store)
        result = analyzer.analyze_and_save(session, profile, provider)
    """

    def __init__(self, memory_store: MemoryStore, survey_store: SurveyStore | None = None):
        self._memory = memory_store
        self._surveys = survey_store

    def analyze_and_save(
        self,
        session: SessionRecord,
        profile: UserProfile,
        provider,          # LLMProvider — kein Import nötig, duck-typed
    ) -> AnalysisResult | None:
        """
        Analysiert den Gesprächsverlauf via LLM und speichert Observations.

        Args:
            session:  Abgeschlossener SessionRecord mit allen Nachrichten
            profile:  Nutzerprofil (für Name und aktuellen Modus)
            provider: Aktiver LLM-Provider (für den Analyse-Call)

        Returns:
            AnalysisResult oder None bei zu wenig Gesprächsinhalt
        """
        # Mindestens 2 Nutzer-Nachrichten für eine sinnvolle Analyse
        user_messages = [m for m in session.messages if m["role"] == "user"]
        if len(user_messages) < 2:
            return None

        transcript = self._build_transcript(session)
        prompt = _ANALYSIS_PROMPT.format(
            name=profile.name,
            mode=profile.current_mode.value,
            transcript=transcript,
        )

        try:
            from .models import NeuroadaptiveMode
            from providers.base import Message

            response = provider.complete(
                messages=[Message(role="user", content=prompt)],
                system_prompt="Du bist ein präzises Analyse-Modul. Antworte ausschließlich mit validen JSON.",
                temperature=0.2,   # niedrig für konsistente, strukturierte Ausgabe
                max_tokens=400,
            )
            result = self._parse_response(response.content)
        except Exception:
            return None

        if result is None:
            return None

        # Observations speichern
        self._save_observations(result, session, profile)

        # GSE-Update: ab Session 2 nach jeder Session neu einschätzen
        if self._surveys and profile.session_count >= 2 and profile.onboarding_complete:
            self._update_gse(profile, provider, transcript)

        return result

    # ── Private ────────────────────────────────────────────────────────────────

    def _build_transcript(self, session: SessionRecord) -> str:
        """Formatiert die Session-Nachrichten als lesbares Transkript."""
        lines = []
        for msg in session.messages:
            role = "Lernender" if msg["role"] == "user" else "KAIA"
            lines.append(f"{role}: {msg['content']}")
        return "\n".join(lines)

    def _parse_response(self, content: str) -> AnalysisResult | None:
        """Parst die JSON-Antwort des LLM."""
        # JSON aus der Antwort extrahieren (falls das LLM doch Text darum schreibt)
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if not match:
            return None

        try:
            data = json.loads(match.group())
        except json.JSONDecodeError:
            return None

        sentiment = data.get("sentiment_score", 0.0)
        if not isinstance(sentiment, (int, float)):
            sentiment = 0.0
        sentiment = max(-1.0, min(1.0, float(sentiment)))

        return AnalysisResult(
            mood=data.get("mood") or None,
            learning_style=data.get("learning_style") or None,
            strength=data.get("strength") or None,
            blind_spot=data.get("blind_spot") or None,
            general=data.get("general") or None,
            sentiment_score=round(sentiment, 2),
        )

    def _update_gse(
        self,
        profile: UserProfile,
        provider,
        transcript: str,
    ) -> None:
        """
        Schätzt GSE-Items (0–9, Skala 1–4) aus der Session-Konversation neu ein
        und speichert sie als 'post'-Messung mit Session-Nummer als timing-Suffix.
        Z.B. timing="session_2", "session_3", ...
        """
        gse_update_prompt = f"""Du bist ein wissenschaftlicher Analyse-Agent.
Analysiere das folgende Gespräch zwischen KAIA und {profile.name} bezüglich ihres/seines Themas.

Schätze für jedes der 10 GSE-Items (Schwarzer & Jerusalem, 1995) den aktuellen Wert ein,
basierend auf dem was {profile.name} in diesem Gespräch gezeigt hat:

Skala: 1 = Stimmt nicht | 2 = Stimmt kaum | 3 = Stimmt eher | 4 = Stimmt genau

Items:
  0: Widerstände überwinden, Mittel und Wege finden
  1: Schwierige Probleme durch Bemühen lösen
  2: Absichten und Ziele verwirklichen
  3: Verhalten in unerwarteten Situationen
  4: Überraschende Ereignisse bewältigen
  5: Gelassenheit durch Vertrauen in eigene Fähigkeiten
  6: Allgemeine Resilienz ("Ich werde klarkommen")
  7: Für jedes Problem eine Lösung finden
  8: Mit neuen Dingen umgehen
  9: Probleme aus eigener Kraft meistern

Antworte NUR mit validem JSON:
{{"gse_scores": {{"0": 3, "1": 3, "2": 3, "3": 3, "4": 3, "5": 3, "6": 3, "7": 3, "8": 3, "9": 3}}}}

Gesprächsverlauf:
{transcript}"""

        try:
            from providers.base import Message
            response = provider.complete(
                messages=[Message(role="user", content=gse_update_prompt)],
                system_prompt="Du bist ein präzises Analyse-Modul. Antworte ausschließlich mit validem JSON.",
                temperature=0.2,
                max_tokens=200,
            )
            match = re.search(r"\{.*\}", response.content, re.DOTALL)
            if not match:
                return
            data = json.loads(match.group())
            gse_raw = data.get("gse_scores", {})
            scores = {str(k): max(1, min(4, int(v))) for k, v in gse_raw.items()}
            # Fehlende Items mit 3 auffüllen
            for i in range(10):
                if str(i) not in scores:
                    scores[str(i)] = 3
            timing = f"session_{profile.session_count}"
            self._surveys.save_survey(profile.user_id, "gse", timing, scores)
        except Exception:
            pass

    def _save_observations(
        self,
        result: AnalysisResult,
        session: SessionRecord,
        profile: UserProfile,
    ) -> None:
        """Speichert alle nicht-leeren Observations im MemoryStore."""
        category_map = {
            "mood":           result.mood,
            "learning_style": result.learning_style,
            "strength":       result.strength,
            "blind_spot":     result.blind_spot,
            "general":        result.general,
        }

        for category, content in category_map.items():
            if content:
                self._memory.add_observation(
                    user_id=profile.user_id,
                    content=content,
                    category=category,
                    session_id=session.session_id,
                    sentiment_score=result.sentiment_score if category == "mood" else None,
                    mode=profile.current_mode.value,
                )
