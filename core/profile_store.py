"""
KAIA – Kinetic AI Agent
Profile Store — JSON-based persistence layer.

MVP decision: JSON files per user, stored locally.
One file per user profile, one file per session.
No database setup required, runs on any machine.

GDPR note: All data stays local. The data/ directory
is excluded from version control via .gitignore.

Migration path to SQLite: replace load/save methods only.
All callers remain unchanged.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict

from .models import (
    UserProfile,
    SessionRecord,
    NeuroadaptiveMode,
    LearningStyle,
    PersonalitySnapshot,
)


class ProfileStore:
    """
    Reads and writes user profiles and session records.

    Directory layout:
        data/
        ├── profiles/
        │   └── {user_id}.json      ← one file per user
        └── sessions/
            └── {session_id}.json   ← one file per session
    """

    def __init__(self, data_dir: str = "data"):
        self.profiles_dir = Path(data_dir) / "profiles"
        self.sessions_dir = Path(data_dir) / "sessions"
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    # ── User Profiles ──────────────────────────────────────────────────────────

    def create_profile(self, name: str = "", context: str = "") -> UserProfile:
        """
        Creates and persists a new user profile.

        Args:
            name:    User's name (optional, for personalization)
            context: What the user is working on, e.g. "studying for exams"

        Returns:
            Newly created UserProfile with a unique ID.
        """
        profile = UserProfile(
            user_id=str(uuid.uuid4()),
            name=name,
            context=context,
        )
        self._save_profile(profile)
        return profile

    def load_profile(self, user_id: str) -> UserProfile:
        """
        Loads a profile by user ID.

        Raises:
            FileNotFoundError: If no profile exists for this user_id.
        """
        path = self.profiles_dir / f"{user_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"No profile found for user_id: {user_id}")

        data = json.loads(path.read_text(encoding="utf-8"))
        return self._dict_to_profile(data)

    def save_profile(self, profile: UserProfile) -> None:
        """Persists an updated profile to disk."""
        profile.updated_at = datetime.now().isoformat()
        self._save_profile(profile)

    def update_mode(self, profile: UserProfile, mode: NeuroadaptiveMode) -> None:
        """
        Updates the user's current neuroadaptive mode and appends a snapshot.
        Called after each state detection cycle.
        """
        snapshot = PersonalitySnapshot(mode=mode)
        profile.current_mode = mode
        profile.snapshots.append(asdict(snapshot))
        self.save_profile(profile)

    def update_trait(self, profile: UserProfile, trait: str, value: float) -> None:
        """
        Updates a single personality trait value (0.0 to 1.0).

        Uses exponential moving average to avoid overreacting
        to a single session — the profile evolves gradually.
        """
        current = profile.traits.get(trait, 0.5)
        alpha = 0.3   # learning rate: 30% new, 70% history
        profile.traits[trait] = round(alpha * value + (1 - alpha) * current, 3)
        self.save_profile(profile)

    def list_profiles(self) -> list[dict]:
        """Returns a summary list of all profiles (id + name + last updated)."""
        summaries = []
        for path in self.profiles_dir.glob("*.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            summaries.append({
                "user_id":    data.get("user_id"),
                "name":       data.get("name", "—"),
                "updated_at": data.get("updated_at"),
                "sessions":   data.get("session_count", 0),
            })
        return sorted(summaries, key=lambda x: x["updated_at"], reverse=True)

    # ── Sessions ───────────────────────────────────────────────────────────────

    def start_session(self, profile: UserProfile, provider: str, model: str) -> SessionRecord:
        """
        Opens a new session record and links it to the user profile.

        Args:
            profile:  The active user profile.
            provider: LLM provider name ("claude", "mistral", "ollama")
            model:    Exact model identifier for evaluation logging.

        Returns:
            A new SessionRecord, already persisted.
        """
        session = SessionRecord(
            session_id=str(uuid.uuid4()),
            user_id=profile.user_id,
            provider=provider,
            model=model,
            mode_at_start=profile.current_mode,
        )
        self._save_session(session)

        # Update profile counters
        profile.session_count += 1
        self.save_profile(profile)

        return session

    def add_message(
        self,
        session: SessionRecord,
        role: str,
        content: str,
        tokens: int = 0,
        latency_ms: float = 0.0,
    ) -> None:
        """
        Appends a message to the session record.
        Keeps running totals for evaluation metrics.
        """
        session.messages.append({
            "role":       role,
            "content":    content,
            "timestamp":  datetime.now().isoformat(),
            "tokens":     tokens,
            "latency_ms": latency_ms,
        })
        session.message_count += 1
        session.total_tokens += tokens

        # Update rolling average latency
        if latency_ms > 0:
            n = session.message_count
            session.avg_latency_ms = round(
                session.avg_latency_ms * (n - 1) / n + latency_ms / n, 1
            )

        self._save_session(session)

    def close_session(self, session: SessionRecord, profile: UserProfile) -> None:
        """Marks the session as ended and updates the profile's message count."""
        session.ended_at = datetime.now().isoformat()
        session.mode_at_end = profile.current_mode
        profile.total_messages += session.message_count
        self._save_session(session)
        self.save_profile(profile)

    def load_session(self, session_id: str) -> SessionRecord:
        """Loads a session record by ID."""
        path = self.sessions_dir / f"{session_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"No session found: {session_id}")
        data = json.loads(path.read_text(encoding="utf-8"))
        return self._dict_to_session(data)

    # ── Private helpers ────────────────────────────────────────────────────────

    def _save_profile(self, profile: UserProfile) -> None:
        path = self.profiles_dir / f"{profile.user_id}.json"
        path.write_text(
            json.dumps(asdict(profile), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _save_session(self, session: SessionRecord) -> None:
        path = self.sessions_dir / f"{session.session_id}.json"
        path.write_text(
            json.dumps(asdict(session), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _dict_to_profile(self, data: dict) -> UserProfile:
        data["current_mode"] = NeuroadaptiveMode(data.get("current_mode", "unknown"))
        style = data.get("dominant_style")
        data["dominant_style"] = LearningStyle(style) if style else None
        return UserProfile(**data)

    def _dict_to_session(self, data: dict) -> SessionRecord:
        data["mode_at_start"] = NeuroadaptiveMode(data.get("mode_at_start", "unknown"))
        data["mode_at_end"]   = NeuroadaptiveMode(data.get("mode_at_end", "unknown"))
        return SessionRecord(**data)
