"""
KAIA – Kinetic AI Agent
LLM Provider Factory

Einziger Einstiegspunkt für den Rest der Anwendung.
KAIA Core importiert ausschließlich aus diesem Modul.

Verwendung:
    from providers import get_provider, LLMProvider

    provider = get_provider("claude")
    response = provider.complete(messages, system_prompt)
"""

from .base import LLMProvider, Message, LLMResponse
from .claude_provider import ClaudeProvider
from .mistral_provider import MistralProvider
from .ollama_provider import OllamaProvider

# Registry: Name → Klasse
# Neuen Provider hinzufügen = eine Zeile hier
_REGISTRY: dict[str, type[LLMProvider]] = {
    "claude":  ClaudeProvider,
    "mistral": MistralProvider,
    "ollama":  OllamaProvider,
}

AVAILABLE_PROVIDERS = list(_REGISTRY.keys())


def get_provider(name: str, **kwargs) -> LLMProvider:
    """
    Gibt einen initialisierten LLM-Provider zurück.

    Args:
        name:    Provider-Name ("claude", "mistral", "ollama")
        **kwargs: Optionale Parameter, z.B. model="claude-opus-4-20250514"

    Returns:
        Initialisierter LLMProvider

    Raises:
        ValueError: Wenn der Provider-Name unbekannt ist.

    Beispiel:
        provider = get_provider("claude")
        provider = get_provider("ollama", model="llama3.2")
    """
    if name not in _REGISTRY:
        raise ValueError(
            f"Unbekannter Provider: '{name}'. "
            f"Verfügbar: {AVAILABLE_PROVIDERS}"
        )
    return _REGISTRY[name](**kwargs)


__all__ = [
    "get_provider",
    "AVAILABLE_PROVIDERS",
    "LLMProvider",
    "Message",
    "LLMResponse",
]
