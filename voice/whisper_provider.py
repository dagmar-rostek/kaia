"""
KAIA – Kinetic AI Agent
STT Provider: Whisper (lokal via faster-whisper)

Vollständig lokal — kein API-Call, DSGVO-maximale Konformität.
Modell wird beim ersten Aufruf einmalig heruntergeladen (~150 MB für "base").

Modellgrößen (Qualität vs. Geschwindigkeit):
  tiny   — schnellst, für Tests
  base   — guter Kompromiss (empfohlen für MVP)
  small  — bessere Qualität
  medium — sehr gut, ~1 GB
  large  — Referenzqualität, ~3 GB
"""

import io
import time
from pathlib import Path

from .stt_base import STTProvider, TranscriptionResult


class WhisperProvider(STTProvider):

    _name = "whisper"

    def __init__(self, model_size: str = "base", device: str = "cpu"):
        """
        Args:
            model_size: "tiny" | "base" | "small" | "medium" | "large"
            device:     "cpu" | "cuda" (für GPU-Beschleunigung)
        """
        self._model_size = model_size
        self._device = device
        self._model = None               # lazy loading — erst beim ersten transcribe()

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_local(self) -> bool:
        return True

    def _load_model(self):
        """Lädt das Whisper-Modell beim ersten Aufruf (lazy)."""
        if self._model is None:
            from faster_whisper import WhisperModel
            self._model = WhisperModel(
                self._model_size,
                device=self._device,
                compute_type="int8",     # speichereffizient auf CPU
            )

    def transcribe(
        self,
        audio: bytes | Path,
        language: str | None = None,
    ) -> TranscriptionResult:
        """
        Transkribiert Audio-Bytes oder eine Datei zu Text.

        Streamlit liefert via st.audio_input() Audio als bytes (WAV).
        """
        self._load_model()
        start = time.time()

        # bytes → temporäre In-Memory-Datei
        if isinstance(audio, bytes):
            audio_file = io.BytesIO(audio)
        else:
            audio_file = str(audio)

        segments, info = self._model.transcribe(
            audio_file,
            language=language,
            beam_size=5,
        )

        text = " ".join(seg.text.strip() for seg in segments).strip()
        latency_ms = (time.time() - start) * 1000

        return TranscriptionResult(
            text=text,
            provider=self.name,
            language=info.language,
            duration_s=round(info.duration, 2),
            latency_ms=round(latency_ms, 1),
        )
