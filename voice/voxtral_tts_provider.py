"""
KAIA – Kinetic AI Agent
TTS Provider: Voxtral (Mistral AI API)

EU-gehostet, OpenAI-kompatibler Endpunkt.
Kosten: $0.016 pro 1.000 Zeichen.
Stimmen werden live von der API geladen.

Liest MISTRAL_API_KEY aus der .env-Datei.
"""

import os
import time
import requests

from .tts_base import TTSProvider, SynthesisResult, VoiceInfo


_DEFAULT_VOICE = "en_paul_neutral"
_API_URL       = "https://api.mistral.ai/v1/audio/speech"
_VOICES_URL    = "https://api.mistral.ai/v1/audio/voices"


class VoxtralTTSProvider(TTSProvider):

    _name = "voxtral"

    def __init__(self, voice_id: str = _DEFAULT_VOICE):
        self._default_voice = voice_id
        self._api_key = os.environ.get("MISTRAL_API_KEY", "")
        if not self._api_key:
            raise ValueError("MISTRAL_API_KEY nicht in .env gefunden.")
        self._voices_cache: list[VoiceInfo] | None = None

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
        voice = voice_id or self._default_voice
        start = time.time()

        response = requests.post(
            _API_URL,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "voxtral-mini-tts-latest",
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
        """Lädt Stimmen live von der Mistral API."""
        if self._voices_cache is None:
            try:
                resp = requests.get(
                    _VOICES_URL,
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    timeout=10,
                )
                resp.raise_for_status()
                self._voices_cache = [
                    VoiceInfo(
                        voice_id=v["slug"],
                        name=v["name"],
                        language=v["languages"][0] if v["languages"] else "en",
                        gender=v.get("gender"),
                        description=", ".join(v.get("tags", [])),
                    )
                    for v in resp.json().get("items", [])
                ]
            except Exception:
                self._voices_cache = [
                    VoiceInfo(_DEFAULT_VOICE, "Paul - Neutral", "en_us", "male")
                ]

        if language:
            filtered = [v for v in self._voices_cache if language in v.language]
            return filtered if filtered else self._voices_cache

        return self._voices_cache
