"""
KAIA – Kinetic AI Agent
Voice: Text-to-Speech Abstraktionsschicht

Abstrakte Basisklasse für alle TTS-Provider.
Neue Provider werden hinzugefügt durch:
  1. Neue Datei anlegen (z.B. coqui_tts_provider.py)
  2. TTSProvider erben
  3. synthesize() implementieren
  → app.py bleibt unverändert
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class VoiceInfo:
    """Metadaten zu einer verfügbaren Stimme."""
    voice_id: str
    name: str
    language: str
    gender: str | None = None            # "female" | "male" | "neutral"
    description: str = ""


@dataclass
class SynthesisResult:
    """Standardisierte TTS-Antwort — unabhängig vom Provider."""
    audio_bytes: bytes
    provider: str
    voice_id: str
    format: str = "mp3"                  # "mp3" | "wav" | "pcm"
    latency_ms: float | None = None
    characters_used: int | None = None   # für Kostentracking


class TTSProvider(ABC):
    """
    Abstrakte Basisklasse für alle Text-to-Speech-Anbieter.
    Eingabe: Text-String.
    Ausgabe: SynthesisResult mit Audio-Bytes.

    Implementierte Provider:
      - VoxtralTTSProvider  (Mistral API, EU, $0.016/1k Zeichen)
      - ElevenLabsProvider  (ElevenLabs API, USA, AVV erforderlich)
      — CoquiTTSProvider    (lokal, geplant)
    """

    @abstractmethod
    def synthesize(
        self,
        text: str,
        voice_id: str | None = None,
        language: str | None = None,
    ) -> SynthesisResult:
        """
        Synthetisiert Text zu Audio.

        Args:
            text:     Zu sprechender Text
            voice_id: Provider-spezifische Stimmen-ID (None = Default-Stimme)
            language: Sprach-Hint, z.B. "de" (optional, Provider-abhängig)

        Returns:
            SynthesisResult mit Audio als Bytes
        """
        pass

    @abstractmethod
    def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        """
        Gibt verfügbare Stimmen zurück, optional gefiltert nach Sprache.
        Wird in der Sidebar zur Auswahl angeboten.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Eindeutiger Bezeichner, z.B. 'voxtral', 'elevenlabs'."""
        pass

    @property
    @abstractmethod
    def is_local(self) -> bool:
        """True wenn vollständig lokal — relevant für DSGVO-Bewertung."""
        pass

    @property
    def gdpr_tier(self) -> str:
        """
        DSGVO-Einschätzung für die UI und Thesis-Evaluation.
          'local'  — vollständig lokal, keine Daten verlassen das Gerät
          'eu'     — EU-Server, AVV empfohlen
          'third'  — Drittland (USA etc.), AVV erforderlich
        """
        return "local" if self.is_local else "unknown"
