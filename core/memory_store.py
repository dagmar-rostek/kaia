"""
KAIA – Kinetic AI Agent
Semantisches Gedächtnis via ChromaDB

Jede Observation (komprimierte Erkenntnis aus einer Session) wird:
  1. Als Text in SQLite gespeichert (strukturiert, durchsuchbar)
  2. Als Vektor in ChromaDB gespiegelt (semantisch abrufbar)

Beim Session-Start fragt KAIA: "Was weiß ich Relevantes über diesen User?"
→ Semantic Search liefert die Top-k nützlichsten Observations
→ Diese fließen in den System-Prompt ein

Alle Embeddings werden lokal berechnet (sentence-transformers).
Kein API-Call, kein Datenaustausch nach außen → DSGVO-konform.
"""

import uuid
from datetime import datetime
from pathlib import Path

import chromadb
from chromadb.config import Settings

from .db import get_connection, json_encode


_DEFAULT_CHROMA_PATH = Path("data") / "chroma"


class MemoryStore:
    """
    Verwaltet das semantische Langzeitgedächtnis von KAIA.

    Jede Instanz ist an einen ChromaDB-Client gebunden.
    Eine Collection pro User: "user_{user_id}"

    Verwendung:
        store = MemoryStore()
        store.add_observation(user_id, session_id, "mood", "Dagmar war heute sehr motiviert")
        memories = store.retrieve(user_id, "Wie geht Dagmar mit Druck um?", k=5)
    """

    def __init__(
        self,
        chroma_path: Path = _DEFAULT_CHROMA_PATH,
        db_path: Path = Path("data") / "kaia.db",
    ):
        chroma_path.mkdir(parents=True, exist_ok=True)
        self._db_path = db_path
        self._client = chromadb.PersistentClient(
            path=str(chroma_path),
            settings=Settings(anonymized_telemetry=False),
        )

    # ── Observations hinzufügen ────────────────────────────────────────────────

    def add_observation(
        self,
        user_id: str,
        content: str,
        category: str = "general",
        session_id: str | None = None,
        sentiment_score: float | None = None,
        mode: str | None = None,
    ) -> str:
        """
        Speichert eine neue Beobachtung in SQLite + ChromaDB.

        Args:
            user_id:         ID des Nutzers
            content:         Freitext, z.B. "Reagiert gut auf konkrete Beispiele"
            category:        'mood' | 'learning_style' | 'topic' | 'strength' | 'blind_spot' | 'general'
            session_id:      Verknüpfung zur auslösenden Session (optional)
            sentiment_score: -1.0 bis 1.0 (optional)
            mode:            NeuroadaptiveMode zum Zeitpunkt (optional)

        Returns:
            obs_id der neuen Observation
        """
        obs_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        # 1. SQLite — strukturierte Speicherung
        with get_connection(self._db_path) as conn:
            conn.execute(
                """
                INSERT INTO observations
                    (obs_id, user_id, session_id, category, content,
                     sentiment_score, mode, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (obs_id, user_id, session_id, category, content,
                 sentiment_score, mode, now),
            )

        # 2. ChromaDB — semantische Speicherung
        collection = self._get_collection(user_id)
        collection.add(
            ids=[obs_id],
            documents=[content],
            metadatas=[{
                "category":        category,
                "session_id":      session_id or "",
                "sentiment_score": sentiment_score if sentiment_score is not None else 0.0,
                "mode":            mode or "unknown",
                "created_at":      now,
            }],
        )

        return obs_id

    # ── Semantisches Retrieval ─────────────────────────────────────────────────

    def retrieve(
        self,
        user_id: str,
        query: str,
        k: int = 5,
        category: str | None = None,
    ) -> list[dict]:
        """
        Findet die k relevantesten Observations für eine Query.

        Beispiel-Queries für den System-Prompt:
          "Wie reagiert der User auf Herausforderungen?"
          "Was sind die Stärken des Nutzers?"
          "Aktuelle Stimmung und Lernmodus"

        Args:
            user_id:  ID des Nutzers
            query:    Semantische Suchanfrage (Freitext)
            k:        Anzahl zurückgegebener Observations (default 5)
            category: Filter nach Kategorie (optional)

        Returns:
            Liste von Dicts mit 'content', 'category', 'mode', 'sentiment_score', 'created_at'
        """
        collection = self._get_collection(user_id)

        if collection.count() == 0:
            return []

        where = {"category": category} if category else None

        results = collection.query(
            query_texts=[query],
            n_results=min(k, collection.count()),
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        observations = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            observations.append({
                "content":         doc,
                "category":        meta.get("category"),
                "mode":            meta.get("mode"),
                "sentiment_score": meta.get("sentiment_score"),
                "created_at":      meta.get("created_at"),
                "relevance":       round(1 - dist, 3),  # Nähe 0–1
            })

        return observations

    # ── Sentiment-Zeitreihe ────────────────────────────────────────────────────

    def get_sentiment_history(self, user_id: str, limit: int = 30) -> list[dict]:
        """
        Gibt die letzten N Sentiment-Scores zurück — für Längsschnitt-Analyse.
        Liefert Basis für Tagesform-Muster und Stressindikatoren in der Thesis.
        """
        with get_connection(self._db_path) as conn:
            rows = conn.execute(
                """
                SELECT sentiment_score, mode, created_at
                FROM observations
                WHERE user_id = ? AND sentiment_score IS NOT NULL
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()

        return [dict(row) for row in rows]

    def get_observations_by_category(
        self, user_id: str, category: str, limit: int = 20
    ) -> list[dict]:
        """Lädt alle Observations einer Kategorie aus SQLite (strukturiert, schnell)."""
        with get_connection(self._db_path) as conn:
            rows = conn.execute(
                """
                SELECT obs_id, content, sentiment_score, mode, created_at
                FROM observations
                WHERE user_id = ? AND category = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, category, limit),
            ).fetchall()

        return [dict(row) for row in rows]

    # ── Helpers ────────────────────────────────────────────────────────────────

    def delete_user(self, user_id: str) -> None:
        """
        Löscht alle Daten eines Nutzers — ChromaDB-Collection + SQLite-Observations.
        DSGVO Art. 17: Recht auf Löschung.
        """
        # ChromaDB-Collection löschen
        collection_name = f"user_{user_id.replace('-', '_')}"
        try:
            self._client.delete_collection(collection_name)
        except Exception:
            pass  # Collection existierte nicht

        # SQLite-Observations löschen
        with get_connection(self._db_path) as conn:
            conn.execute("DELETE FROM observations WHERE user_id = ?", (user_id,))

    def _get_collection(self, user_id: str):
        """
        Gibt die ChromaDB-Collection für einen User zurück.
        Wird automatisch erstellt, falls sie noch nicht existiert.
        """
        collection_name = f"user_{user_id.replace('-', '_')}"
        return self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def build_memory_context(self, user_id: str) -> str:
        """
        Erstellt einen kompakten Memory-Block für den System-Prompt.

        Ruft semantisch relevante Observations zu den wichtigsten Dimensionen ab
        und formatiert sie als lesbaren Kontext für das LLM.

        Beispieloutput:
            [KAIA Memory]
            Stärken: Analytisches Denken, gute Selbstreflexion
            Herausforderungen: Tendenz zum Overthinking bei abstrakten Konzepten
            Lernstil: Bevorzugt konkrete Beispiele vor Theorie
            Aktuelle Stimmungstendenz: eher positiv (+0.6 Ø)
        """
        strengths   = self.retrieve(user_id, "Stärken und Fähigkeiten des Nutzers", k=3, category="strength")
        blind_spots = self.retrieve(user_id, "Schwierigkeiten und blinde Flecken", k=3, category="blind_spot")
        style       = self.retrieve(user_id, "Lernstil und Lernpräferenzen", k=2, category="learning_style")
        mood        = self.retrieve(user_id, "aktuelle Stimmung und emotionaler Zustand", k=2, category="mood")

        if not any([strengths, blind_spots, style, mood]):
            return ""  # Noch kein Gedächtnis aufgebaut

        lines = ["[KAIA Memory — personalisierter Kontext]"]

        if strengths:
            lines.append("Stärken: " + " | ".join(o["content"] for o in strengths))
        if blind_spots:
            lines.append("Herausforderungen: " + " | ".join(o["content"] for o in blind_spots))
        if style:
            lines.append("Lernstil: " + " | ".join(o["content"] for o in style))
        if mood:
            lines.append("Stimmung (recent): " + " | ".join(o["content"] for o in mood))

        # Sentiment-Durchschnitt der letzten 5 Sessions
        history = self.get_sentiment_history(user_id, limit=5)
        if history:
            scores = [h["sentiment_score"] for h in history if h["sentiment_score"] is not None]
            if scores:
                avg = round(sum(scores) / len(scores), 2)
                lines.append(f"Sentiment-Trend (letzte {len(scores)} Sessions): {avg:+.2f}")

        return "\n".join(lines)
