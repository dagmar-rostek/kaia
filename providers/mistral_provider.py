"""
KAIA – Kinetic AI Agent
LLM Provider: Mistral AI

Relevanz für die Thesis:
Mistral ist ein französisches Unternehmen → europäische Datensouveränität.
Verwendung als direkter Vergleichskandidat zu Claude in der Evaluation.
Liest MISTRAL_API_KEY aus der .env-Datei.
"""

import os
import time
from mistralai.client import Mistral
from .base import LLMProvider, Message, LLMResponse


class MistralProvider(LLMProvider):

    _name = "mistral"
    _model_id = "mistral-large-latest"

    def __init__(self, model: str = None):
        """
        Args:
            model: z.B. "mistral-medium-latest" oder "mistral-small-latest"
        """
        self._model_id = model or self._model_id
        self.client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])

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

        # Mistral erwartet den System-Prompt als erste Nachricht
        all_messages = [{"role": "system", "content": system_prompt}]
        all_messages += [
            {"role": m.role, "content": m.content}
            for m in messages
        ]

        response = self.client.chat.complete(
            model=self._model_id,
            messages=all_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        latency_ms = (time.time() - start) * 1000

        return LLMResponse(
            content=response.choices[0].message.content,
            provider=self.name,
            model=self._model_id,
            tokens_used=response.usage.total_tokens,
            latency_ms=round(latency_ms, 1),
        )
