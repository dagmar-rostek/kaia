"""
KAIA – Kinetic AI Agent
TTS Provider: ElevenLabs

US-gehostet (AVV erforderlich für DSGVO-Konformität).
Beste Stimmenqualität, Voice Cloning verfügbar.
Kosten: abhängig vom Tarif (Starter ab $5/Monat).

Liest ELEVENLABS_API_KEY aus der .env-Datei.

DSGVO-Hinweis:
  ElevenLabs server are located in the USA (Drittland).
  Für den Einsatz in der Thesis-Studie: AVV abschließen +
  Einwilligung der Probanden einholen.
"""

import os
import time
import requests

from .tts_base import TTSProvider, SynthesisResult, VoiceInfo


_API_URL  = "https://api.elevenlabs.io/v1/text-to-speech"
_VOICES_URL = "https://api.elevenlabs.io/v1/voices"

# Bekannte Standard-Stimmen (werden zur Laufzeit via API ergänzt)
_DEFAULT_VOICES = [
    VoiceInfo("21m00Tcm4TlvDq8ikWAM", "Rachel",  "en", "female",  "Calm and professional"),
    VoiceInfo("AZnzlk1XvdvUeBnXmlld", "Domi",    "en", "female",  "Confident and expressive"),
    VoiceInfo("EXAVITQu4vr4xnSDxMaL", "Bella",   "en", "female",  "Soft and warm"),
    VoiceInfo("ErXwobaYiN019PkySvjV", "Antoni",   "en", "male",   "Calm narrator"),
    VoiceInfo("MF3mGyEYCl7XYWbV9V6O", "Elli",    "en", "female",  "Young and clear"),
    VoiceInfo("TxGEqnHWrfWFTfGW9XjX", "Josh",    "en", "male",   "Deep and warm"),
]

_DEFAULT_VOICE = "EXAVITQu4vr4xnSDxMaL"   # Bella — weich, passend für KAIA


class ElevenLabsTTSProvider(TTSProvider):

    _name = "elevenlabs"

    def __init__(self, voice_id: str = _DEFAULT_VOICE):
        self._default_voice = voice_id
        self._api_key = os.environ.get("ELEVENLABS_API_KEY", "")
        if not self._api_key:
            raise ValueError("ELEVENLABS_API_KEY nicht in .env gefunden.")

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_local(self) -> bool:
        return False

    @property
    def gdpr_tier(self) -> str:
        return "third"    # USA — AVV erforderlich

    def synthesize(
        self,
        text: str,
        voice_id: str | None = None,
        language: str | None = None,
    ) -> SynthesisResult:
        """
        Sendet Text an ElevenLabs API und gibt MP3-Audio zurück.
        language wird ignoriert — ElevenLabs erkennt die Sprache automatisch.
        """
        voice = voice_id or self._default_voice
        start = time.time()

        response = requests.post(
            f"{_API_URL}/{voice}",
            headers={
                "xi-api-key": self._api_key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            },
            json={
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                },
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
        """
        Lädt Stimmen von der ElevenLabs API (inkl. eigene geklonte Stimmen).
        Fallback auf Standardliste wenn API nicht erreichbar.
        """
        try:
            resp = requests.get(
                _VOICES_URL,
                headers={"xi-api-key": self._api_key},
                timeout=10,
            )
            resp.raise_for_status()
            voices = []
            for v in resp.json().get("voices", []):
                voices.append(VoiceInfo(
                    voice_id=v["voice_id"],
                    name=v["name"],
                    language="multi",
                    description=v.get("description", ""),
                ))
            return voices
        except Exception:
            return _DEFAULT_VOICES
