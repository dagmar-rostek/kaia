"""
KAIA – Gedächtnis-Systemtest

Testet den vollständigen Memory-Fluss:
  1. Profil anlegen (SQLite)
  2. Session starten + Nachrichten hinzufügen
  3. SessionAnalyzer: Session analysieren → Observations speichern
  4. MemoryStore: Semantisches Retrieval
  5. build_memory_context: System-Prompt-Anreicherung
  6. Sentiment-Zeitreihe abrufen

Ausführen: python test_memory.py
Optionaler echter LLM-Test: python test_memory.py --live
"""

import sys
import tempfile
import shutil
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from providers.base import Message, LLMResponse
from core import ProfileStore, MemoryStore, SessionAnalyzer, NeuroadaptiveMode
from core.session_analyzer import AnalysisResult


# ── Mock-Provider (kein API-Call nötig) ───────────────────────────────────────

class MockProvider:
    """Simuliert einen LLM-Provider mit einer vordefinierten Analyse-Antwort."""

    name  = "mock"
    model = "mock-1.0"

    def complete(self, messages, system_prompt, temperature=0.7, max_tokens=1000):
        # Simulierte JSON-Antwort des SessionAnalyzers
        mock_json = """{
  "mood": "Dagmar war heute sehr fokussiert und motiviert, zeigte echtes Interesse am Thema",
  "learning_style": "Bevorzugt konkrete Beispiele vor abstrakten Definitionen",
  "strength": "Starke Fähigkeit zur Selbstreflexion und zum kritischen Hinterfragen",
  "blind_spot": "Tendenz zum Overthinking bei komplexen, mehrstufigen Konzepten",
  "general": "Profitiert von kurzen Zwischenfragen, die den Fokus halten",
  "sentiment_score": 0.72
}"""
        return LLMResponse(
            content=mock_json,
            provider="mock",
            model="mock-1.0",
            tokens_used=80,
            latency_ms=12.0,
        )


# ── Test-Hilfsfunktionen ───────────────────────────────────────────────────────

GREEN  = "\033[92m"
RED    = "\033[91m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"


def section(title: str):
    print(f"\n{BOLD}── {title} {'─' * (50 - len(title))}{RESET}")


def ok(msg: str):
    print(f"  {GREEN}✓{RESET}  {msg}")


def fail(msg: str):
    print(f"  {RED}✗  {msg}{RESET}")
    sys.exit(1)


# ── Tests ──────────────────────────────────────────────────────────────────────

def run_tests(use_live_llm: bool = False):
    # Temporäres Datenverzeichnis — wird nach dem Test gelöscht
    tmp_dir = Path(tempfile.mkdtemp())
    db_path     = tmp_dir / "kaia_test.db"
    chroma_path = tmp_dir / "chroma_test"

    try:
        store   = ProfileStore(db_path=db_path)
        memory  = MemoryStore(chroma_path=chroma_path, db_path=db_path)

        # 1. Profil anlegen
        section("1. Profil anlegen (SQLite)")
        profile = store.create_profile(
            name="Dagmar",
            context="Masterthesis — neuroadaptive Lernbegleitung",
        )
        ok(f"Profil erstellt: {profile.user_id[:8]}...")
        store.update_mode(profile, NeuroadaptiveMode.FLOW)
        ok(f"Modus gesetzt: {profile.current_mode.value}")

        reloaded = store.load_profile(profile.user_id)
        assert reloaded.name == "Dagmar", "Name stimmt nicht nach Reload"
        assert reloaded.current_mode == NeuroadaptiveMode.FLOW
        ok("Profil korrekt aus SQLite geladen")

        # 2. Session mit Nachrichten
        section("2. Session starten + Nachrichten")
        session = store.start_session(profile, provider="mock", model="mock-1.0")
        ok(f"Session gestartet: {session.session_id[:8]}...")

        messages = [
            ("user",      "Ich verstehe nicht, warum Gradientenabstieg funktioniert."),
            ("assistant", "Was denkst du passiert, wenn wir uns einem Minimum nähern?"),
            ("user",      "Die Schritte werden kleiner?"),
            ("assistant", "Genau — was verrät dir das über die Lernrate?"),
            ("user",      "Ah, sie passt sich an die Steilheit an!"),
            ("assistant", "Du hast es erfasst. Was bedeutet das für flache Regionen?"),
        ]
        for role, content in messages:
            store.add_message(session, role, content, tokens=15, latency_ms=300)

        assert session.message_count == len(messages)
        ok(f"{session.message_count} Nachrichten, {session.total_tokens} Tokens, "
           f"{session.avg_latency_ms} ms Ø-Latenz")

        # 3. SessionAnalyzer — Observations generieren
        section("3. SessionAnalyzer — Observations ins Gedächtnis schreiben")

        if use_live_llm:
            from dotenv import load_dotenv
            load_dotenv()
            from providers import get_provider
            provider = get_provider("claude")
            print("  → Echter Claude-API-Call...")
        else:
            provider = MockProvider()
            print("  → Mock-Provider (kein API-Call)")

        store.close_session(session, profile)
        analyzer = SessionAnalyzer(memory)
        result = analyzer.analyze_and_save(session, profile, provider)

        assert result is not None, "Analyse hat kein Ergebnis zurückgegeben"
        assert result.mood is not None
        assert -1.0 <= result.sentiment_score <= 1.0
        ok(f"Stimmung:        {result.mood}")
        ok(f"Lernstil:        {result.learning_style}")
        ok(f"Stärke:          {result.strength}")
        ok(f"Blinder Fleck:   {result.blind_spot}")
        ok(f"Allgemein:       {result.general}")
        ok(f"Sentiment-Score: {result.sentiment_score:+.2f}")

        # 4. Semantisches Retrieval
        section("4. Semantisches Retrieval (ChromaDB)")

        hits = memory.retrieve(profile.user_id, "Wie lernt Dagmar am besten?", k=3)
        assert len(hits) > 0, "Kein Retrieval-Ergebnis"
        ok(f"{len(hits)} Observation(s) gefunden:")
        for h in hits:
            print(f"  {DIM}   [{h['category']}] {h['content'][:70]}  (relevance={h['relevance']}){RESET}")

        strengths = memory.get_observations_by_category(profile.user_id, "strength")
        assert len(strengths) > 0
        ok(f"Stärken in SQLite: {strengths[0]['content'][:60]}")

        # 5. System-Prompt-Anreicherung
        section("5. build_memory_context — System-Prompt-Block")
        context_block = memory.build_memory_context(profile.user_id)
        assert "[KAIA Memory" in context_block, "Memory-Block fehlt"
        ok("Memory-Block generiert:")
        for line in context_block.split("\n"):
            print(f"  {DIM}   {line}{RESET}")

        # 6. Sentiment-Zeitreihe
        section("6. Sentiment-Zeitreihe")
        history = memory.get_sentiment_history(profile.user_id, limit=10)
        assert len(history) > 0
        ok(f"{len(history)} Einträge in der Zeitreihe, Score: {history[0]['sentiment_score']:+.2f}")

        # 7. Zweite Session — zeigt dass Gedächtnis kumuliert
        section("7. Zweite Session — Gedächtnis wächst")
        profile2 = store.load_profile(profile.user_id)
        session2 = store.start_session(profile2, provider="mock", model="mock-1.0")
        for role, content in [
            ("user",      "Heute bin ich müde und kann mich kaum konzentrieren."),
            ("assistant", "Lass uns heute mit etwas Leichtem beginnen."),
            ("user",      "Gut, ein kurzes Beispiel wäre hilfreich."),
        ]:
            store.add_message(session2, role, content, tokens=10)

        store.close_session(session2, profile2)
        result2 = analyzer.analyze_and_save(session2, profile2, provider)
        if result2:
            ok(f"Zweite Analyse: {result2.sentiment_score:+.2f} Sentiment")

        history2 = memory.get_sentiment_history(profile.user_id, limit=10)
        ok(f"Zeitreihe jetzt: {len(history2)} Einträge")

        print(f"\n{GREEN}{'─' * 55}")
        print(f"  {BOLD}✓  Alle Tests bestanden. Gedächtnis-System funktioniert.{RESET}{GREEN}")
        print(f"{'─' * 55}{RESET}\n")

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    live = "--live" in sys.argv
    if live:
        print("KAIA Memory-Test  [LIVE — echter API-Call]")
    else:
        print("KAIA Memory-Test  [Mock-Provider, kein API-Call]")
    run_tests(use_live_llm=live)
