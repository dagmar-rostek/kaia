"""
KAIA – Kinetic AI Agent
LLM Provider Abstraktionsschicht: Basis-Klassen

Zweck: Definiert den gemeinsamen Vertrag für alle LLM-Anbieter.
Jeder konkrete Provider (Claude, Mistral, Ollama) implementiert
dieselbe Schnittstelle – KAIA Core muss den Provider nie kennen.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Message:
    """Eine einzelne Nachricht im Gesprächsverlauf."""
    role: str       # "user" oder "assistant"
    content: str


@dataclass
class LLMResponse:
    """Standardisierte Antwort – unabhängig vom Provider."""
    content: str
    provider: str           # "claude" | "mistral" | "ollama"
    model: str
    tokens_used: Optional[int] = None
    latency_ms: Optional[float] = None   # für die Thesis-Evaluation


class LLMProvider(ABC):
    """
    Abstrakte Basisklasse für alle LLM-Anbieter.

    Neue Provider werden hinzugefügt durch:
    1. Neue Datei anlegen (z.B. gpt_provider.py)
    2. Diese Klasse erben
    3. complete() implementieren
    → KAIA Core bleibt unverändert.
    """

    @abstractmethod
    def complete(
        self,
        messages: list[Message],
        system_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        """
        Sendet eine Konversation an das LLM und gibt die Antwort zurück.

        Args:
            messages:      Gesprächsverlauf (User + Assistant turns)
            system_prompt: Dynamisch generierter KAIA-System-Prompt
            temperature:   Kreativität (0.0 = deterministisch, 1.0 = kreativ)
            max_tokens:    Maximale Antwortlänge

        Returns:
            LLMResponse mit normalisierter Antwort und Metadaten
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Eindeutiger Bezeichner des Providers (für Logging und Evaluation)."""
        pass

    @property
    @abstractmethod
    def model(self) -> str:
        """Verwendetes Modell (für Evaluation und Dokumentation)."""
        pass
