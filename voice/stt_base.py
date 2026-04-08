"""
KAIA – Kinetic AI Agent
Voice: Speech-to-Text Abstraktionsschicht

Abstrakte Basisklasse für alle STT-Provider.
Neue Provider werden hinzugefügt durch:
  1. Neue Datei anlegen (z.B. google_stt_provider.py)
  2. STTProvider erben
  3. transcribe() implementieren
  → app.py bleibt unverändert
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TranscriptionResult:
    """Standardisierte STT-Antwort — unabhängig vom Provider."""
    text: str
    provider: str
    language: str | None = None          # erkannte Sprache, z.B. "de"
    duration_s: float | None = None      # Audio-Länge in Sekunden
    latency_ms: float | None = None


class STTProvider(ABC):
    """
    Abstrakte Basisklasse für alle Speech-to-Text-Anbieter.
    Eingabe: Audio-Datei (WAV/MP3) oder Bytes.
    Ausgabe: TranscriptionResult mit erkanntem Text.
    """

    @abstractmethod
    def transcribe(
        self,
        audio: bytes | Path,
        language: str | None = None,
    ) -> TranscriptionResult:
        """
        Transkribiert Audio zu Text.

        Args:
            audio:    Audio als Bytes oder Pfad zu einer Datei (WAV/MP3/OGG)
            language: Sprachhinweis, z.B. "de" oder "en" (optional)

        Returns:
            TranscriptionResult mit erkanntem Text
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Eindeutiger Bezeichner, z.B. 'whisper', 'voxtral'."""
        pass

    @property
    @abstractmethod
    def is_local(self) -> bool:
        """True wenn vollständig lokal — relevant für DSGVO-Bewertung."""
        pass
