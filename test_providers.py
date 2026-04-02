"""
KAIA – Provider-Schnelltest

Ausführen: python test_providers.py
Testet jeden Provider mit einer einfachen Frage.
"""

from dotenv import load_dotenv
load_dotenv()

from providers import get_provider, AVAILABLE_PROVIDERS, Message

TEST_MESSAGE = [Message(role="user", content="Antworte mit genau einem Satz: Was ist Lernen?")]
SYSTEM_PROMPT = "Du bist KAIA, ein empathischer Lernbegleiter. Antworte präzise und einfühlsam."

def test_provider(name: str):
    print(f"\n{'─'*50}")
    print(f"Provider: {name.upper()}")
    try:
        provider = get_provider(name)
        response = provider.complete(TEST_MESSAGE, SYSTEM_PROMPT)
        print(f"Modell:   {response.model}")
        print(f"Latenz:   {response.latency_ms} ms")
        print(f"Tokens:   {response.tokens_used}")
        print(f"Antwort:  {response.content}")
    except Exception as e:
        print(f"Fehler:   {e}")

if __name__ == "__main__":
    print("KAIA Provider-Test")
    for provider_name in AVAILABLE_PROVIDERS:
        test_provider(provider_name)
    print(f"\n{'─'*50}")
    print("Test abgeschlossen.")
