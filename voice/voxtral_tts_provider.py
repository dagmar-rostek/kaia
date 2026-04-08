"""
KAIA – Kinetic AI Agent
TTS Provider: Voxtral (Mistral AI API)

EU-gehostet, OpenAI-kompatibler Endpunkt.
Kosten: $0.016 pro 1.000 Zeichen.
Latenz: ~0.8s Time-to-First-Audio (PCM), ~3s (MP3).

Liest MISTRAL_API_KEY aus der .env-Datei.
"""

import os
import time
import requests

from .tts_base import TTSProvider, SynthesisResult, VoiceInfo


# 20 voreingestellte Voxtral-Stimmen (Stand: April 2026)
_VOXTRAL_VOICES = [
    VoiceInfo("river",   "River",   "en", "neutral",  "Warm and balanced"),
    VoiceInfo("vale",    "Vale",    "en", "female",   "Clear and professional"),
    VoiceInfo("luna",    "Luna",    "de", "female",   "Sanft und deutlich"),
    VoiceInfo("felix",   "Felix",   "de", "male",     "Ruhig und präzise"),
    VoiceInfo("aurora",  "Aurora",  "fr", "female",   "Douce et expressive"),
    VoiceInfo("marco",   "Marco",   "it", "male",     "Energico e chiaro"),
    VoiceInfo("sol",     "Sol",     "es", "neutral",  "Cálida y cercana"),
    VoiceInfo("aria",    "Aria",    "en", "female",   "Expressive and warm"),
    VoiceInfo("orion",   "Orion",   "en", "male",     "Deep and reassuring"),
    VoiceInfo("nova",    "Nova",    "en", "female",   "Bright and energetic"),
]

_DEFAULT_VOICE = "luna"     # Deutsch, weiblich — passend für KAIA
_API_URL = "https://api.mistral.ai/v1/audio/speech"


class VoxtralTTSProvider(TTSProvider):

    _name = "voxtral"

    def __init__(self, voice_id: str = _DEFAULT_VOICE):
        self._default_voice = voice_id
        self._api_key = os.environ.get("MISTRAL_API_KEY", "")
        if not self._api_key:
            raise ValueError("MISTRAL_API_KEY nicht in .env gefunden.")

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_local(self) -> bool:
        return False

    @property
    def gdpr_tier(self) -> str:
        return "eu"

    def synthesize(
        self,
        text: str,
        voice_id: str | None = None,
        language: str | None = None,
    ) -> SynthesisResult:
        """
        Sendet Text an Voxtral API und gibt Audio-Bytes zurück.
        Format: MP3 (kompatibel mit st.audio()).
        """
        voice = voice_id or self._default_voice
        start = time.time()

        response = requests.post(
            _API_URL,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "voxtral-mini-tts",
                "input": text,
                "voice": voice,
            },
            timeout=30,
        )
        response.raise_for_status()

        latency_ms = (time.time() - start) * 1000

        return SynthesisResult(
            audio_bytes=response.content,
            provider=self.name,
            voice_id=voice,
            format="mp3",
            latency_ms=round(latency_ms, 1),
            characters_used=len(text),
        )

    def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        if language:
            return [v for v in _VOXTRAL_VOICES if v.language == language]
        return _VOXTRAL_VOICES
