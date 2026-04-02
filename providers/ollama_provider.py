"""
KAIA – Kinetic AI Agent
LLM Provider: Ollama (lokal)

Relevanz für die Thesis:
Ollama läuft vollständig lokal – keine Daten verlassen das Gerät.
Maximale Datensouveränität, DSGVO-konform ohne Abstriche.
Geeignet für: Llama 3.2, Mistral (lokal), Phi-3, Gemma 2.

Installation: https://ollama.ai
Modell laden:  ollama pull llama3.2

Kein API-Key erforderlich.
"""

import time
import requests
from .base import LLMProvider, Message, LLMResponse


class OllamaProvider(LLMProvider):

    _name = "ollama"

    def __init__(
        self,
        model: str = "llama3.2",
        host: str = "http://localhost:11434",
    ):
        """
        Args:
            model: Beliebiges bei Ollama verfügbares Modell.
            host:  Ollama-Server-Adresse (Standard: lokal).
        """
        self._model_id = model
        self.host = host
        self._check_connection()

    def _check_connection(self):
        """Prüft ob Ollama läuft – gibt eine klare Fehlermeldung."""
        try:
            requests.get(f"{self.host}/api/tags", timeout=3)
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                "Ollama ist nicht erreichbar. "
                "Bitte starte Ollama mit: ollama serve"
            )

    @property
    def name(self) -> str:
        return self._name

    @property
    def model(self) -> str:
        return self._model_id

    def complete(
        self,
        messages: list[Message],
        system_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:

        start = time.time()

        all_messages = [{"role": "system", "content": system_prompt}]
        all_messages += [
            {"role": m.role, "content": m.content}
            for m in messages
        ]

        response = requests.post(
            f"{self.host}/api/chat",
            json={
                "model": self._model_id,
                "messages": all_messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            },
            timeout=120,   # lokale Modelle können länger brauchen
        )
        response.raise_for_status()
        data = response.json()

        latency_ms = (time.time() - start) * 1000

        return LLMResponse(
            content=data["message"]["content"],
            provider=self.name,
            model=self._model_id,
            tokens_used=data.get("eval_count"),
            latency_ms=round(latency_ms, 1),
        )
