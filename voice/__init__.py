"""
KAIA – Kinetic AI Agent
Voice module — öffentliche API

Analog zu providers/__init__.py:
  get_stt_provider("whisper")     → WhisperProvider
  get_tts_provider("voxtral")     → VoxtralTTSProvider
  get_tts_provider("elevenlabs")  → ElevenLabsTTSProvider

Neuen Provider hinzufügen:
  1. Datei in voice/ anlegen
  2. In STT_PROVIDERS oder TTS_PROVIDERS registrieren
  → Rest bleibt unverändert
"""

from .stt_base import STTProvider, TranscriptionResult
from .tts_base import TTSProvider, SynthesisResult, VoiceInfo


# ── Registries ─────────────────────────────────────────────────────────────────

AVAILABLE_STT_PROVIDERS = ["whisper"]
AVAILABLE_TTS_PROVIDERS = ["voxtral", "elevenlabs"]


def get_stt_provider(name: str, **kwargs) -> STTProvider:
    """
    Factory für STT-Provider.

    Args:
        name:   "whisper"
        kwargs: Provider-spezifische Optionen (z.B. model_size="small")
    """
    if name == "whisper":
        from .whisper_provider import WhisperProvider
        return WhisperProvider(**kwargs)

    raise ValueError(
        f"Unbekannter STT-Provider: '{name}'. "
        f"Verfügbar: {AVAILABLE_STT_PROVIDERS}"
    )


def get_tts_provider(name: str, **kwargs) -> TTSProvider:
    """
    Factory für TTS-Provider.

    Args:
        name:   "voxtral" | "elevenlabs"
        kwargs: Provider-spezifische Optionen (z.B. voice_id="luna")
    """
    if name == "voxtral":
        from .voxtral_tts_provider import VoxtralTTSProvider
        return VoxtralTTSProvider(**kwargs)

    if name == "elevenlabs":
        from .elevenlabs_tts_provider import ElevenLabsTTSProvider
        return ElevenLabsTTSProvider(**kwargs)

    raise ValueError(
        f"Unbekannter TTS-Provider: '{name}'. "
        f"Verfügbar: {AVAILABLE_TTS_PROVIDERS}"
    )


__all__ = [
    "STTProvider", "TranscriptionResult",
    "TTSProvider", "SynthesisResult", "VoiceInfo",
    "get_stt_provider", "get_tts_provider",
    "AVAILABLE_STT_PROVIDERS", "AVAILABLE_TTS_PROVIDERS",
]
