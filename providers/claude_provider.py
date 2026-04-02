"""
KAIA – Kinetic AI Agent
LLM Provider: Anthropic Claude

Verwendung im MVP und als Entwicklungs-Baseline.
Liest ANTHROPIC_API_KEY automatisch aus der .env-Datei.
"""

import time
import anthropic
from .base import LLMProvider, Message, LLMResponse


class ClaudeProvider(LLMProvider):

    _name = "claude"
    _model_id = "claude-sonnet-4-20250514"

    def __init__(self, model: str = None):
        """
        Args:
            model: Modell-ID überschreiben, z.B. "claude-opus-4-20250514"
                   Standardmäßig wird Sonnet 4 verwendet.
        """
        self._model_id = model or self._model_id
        # Liest ANTHROPIC_API_KEY automatisch aus Umgebungsvariablen
        self.client = anthropic.Anthropic()

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

        response = self.client.messages.create(
            model=self._model_id,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[
                {"role": m.role, "content": m.content}
                for m in messages
            ],
        )

        latency_ms = (time.time() - start) * 1000

        return LLMResponse(
            content=response.content[0].text,
            provider=self.name,
            model=self._model_id,
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            latency_ms=round(latency_ms, 1),
        )
