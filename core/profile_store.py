"""
KAIA – Kinetic AI Agent
Profile Store — SQLite-basierter Persistenzlayer.

Ersetzt den früheren JSON-basierten Store.
Die öffentliche API (create_profile, start_session, add_message, etc.)
ist identisch geblieben — app.py und Provider-Schicht bleiben unverändert.

DSGVO: Alle Daten bleiben lokal in data/kaia.db.
Die data/-Directory ist via .gitignore ausgeschlossen.
"""

import hashlib
import secrets
import uuid
from datetime import datetime
from pathlib import Path

from .db import init_db, get_connection, json_encode, json_decode
from .models import (
    UserProfile,
    SessionRecord,
    NeuroadaptiveMode,
    LearningStyle,
    PersonalitySnapshot,
)
from dataclasses import asdict


def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    key  = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
    return f"{salt}:{key.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt, key_hex = stored.split(":", 1)
        key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
        return secrets.compare_digest(key.hex(), key_hex)
    except Exception:
        return False


class ProfileStore:
    """
    Liest und schreibt Nutzerprofile und Session-Records via SQLite.

    Öffentliche API ist kompatibel mit dem früheren JSON-basierten Store.
    """

    def __init__(self, db_path: Path = Path("data") / "kaia.db"):
        self._db_path = db_path
        init_db(db_path)

    # ── User Profiles ──────────────────────────────────────────────────────────

    @staticmethod
    def pin_user_id(name: str, pin: str) -> str:
        """Erzeugt eine deterministische user_id aus Name + PIN (SHA-256)."""
        raw = f"{name.strip().lower()}:{pin}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def find_by_pin(self, name: str, pin: str) -> "UserProfile | None":
        """
        Sucht ein Profil anhand der PIN-basierten user_id.
        Gibt None zurück wenn kein Profil gefunden wurde oder PIN falsch ist.
        """
        user_id = self.pin_user_id(name, pin)
        with get_connection(self._db_path) as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
        return self._row_to_profile(dict(row)) if row else None

    def create_profile(self, name: str = "", context: str = "", user_id: str | None = None) -> UserProfile:
        """Erstellt ein neues Nutzerprofil und persistiert es."""
        now = datetime.now().isoformat()
        profile = UserProfile(
            user_id=user_id or str(uuid.uuid4()),
            created_at=now,
            updated_at=now,
            name=name,
            context=context,
        )
        self._save_profile(profile)
        return profile

    def load_profile(self, user_id: str) -> UserProfile:
        """Lädt ein Profil anhand der user_id."""
        with get_connection(self._db_path) as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()

        if row is None:
            raise FileNotFoundError(f"No profile found for user_id: {user_id}")

        return self._row_to_profile(dict(row))

    def save_profile(self, profile: UserProfile) -> None:
        """Persistiert ein aktualisiertes Profil."""
        profile.updated_at = datetime.now().isoformat()
        self._save_profile(profile)

    def update_mode(self, profile: UserProfile, mode: NeuroadaptiveMode) -> None:
        """Aktualisiert den neuroadaptiven Modus und hängt einen Snapshot an."""
        snapshot = PersonalitySnapshot(mode=mode)
        profile.current_mode = mode
        profile.snapshots.append(asdict(snapshot))
        self.save_profile(profile)

    def update_trait(self, profile: UserProfile, trait: str, value: float) -> None:
        """
        Aktualisiert einen Persönlichkeitstrait via Exponential Moving Average.
        alpha=0.3: 30% neuer Wert, 70% bisherige Geschichte.
        """
        current = profile.traits.get(trait, 0.5)
        alpha = 0.3
        profile.traits[trait] = round(alpha * value + (1 - alpha) * current, 3)
        self.save_profile(profile)

    def find_by_name(self, name: str) -> UserProfile | None:
        """
        Sucht das zuletzt aktive Profil mit diesem Namen (case-insensitive).
        Gibt None zurück wenn kein Profil gefunden wurde.
        """
        with get_connection(self._db_path) as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE LOWER(name) = LOWER(?) ORDER BY updated_at DESC LIMIT 1",
                (name,),
            ).fetchone()
        return self._row_to_profile(dict(row)) if row else None

    def create_account(self, email: str, username: str, password: str) -> "UserProfile":
        """
        Erstellt ein neues Konto mit gehashtem Passwort.
        Wirft ValueError wenn der Benutzername bereits vergeben ist.
        """
        with get_connection(self._db_path) as conn:
            row = conn.execute(
                "SELECT user_id FROM users WHERE LOWER(name) = LOWER(?)", (username,)
            ).fetchone()
        if row:
            raise ValueError("Benutzername bereits vergeben.")

        now = datetime.now().isoformat()
        profile = UserProfile(
            user_id=str(uuid.uuid4()),
            created_at=now,
            updated_at=now,
            name=username,
            email=email,
            password_hash=_hash_password(password),
        )
        self._save_profile(profile)
        return profile

    def authenticate(self, username: str, password: str) -> "UserProfile | None":
        """
        Prüft Credentials und gibt das Profil zurück — oder None bei Fehler.
        """
        with get_connection(self._db_path) as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE LOWER(name) = LOWER(?)", (username,)
            ).fetchone()
        if not row:
            return None
        profile = self._row_to_profile(dict(row))
        if not profile.password_hash:
            return None  # Legacy-User ohne Passwort
        if _verify_password(password, profile.password_hash):
            return profile
        return None

    def delete_profile(self, user_id: str) -> None:
        """
        Löscht alle personenbezogenen Daten eines Nutzers aus der Datenbank.
        DSGVO Art. 17: Recht auf Löschung.
        Reihenfolge: surveys → sessions → users (FK-Constraints).
        ChromaDB-Daten müssen separat via MemoryStore.delete_user() gelöscht werden.
        """
        with get_connection(self._db_path) as conn:
            conn.execute("DELETE FROM surveys      WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM sessions     WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM users        WHERE user_id = ?", (user_id,))

    def list_profiles(self) -> list[dict]:
        """Gibt eine Kurzübersicht aller Profile zurück."""
        with get_connection(self._db_path) as conn:
            rows = conn.execute(
                "SELECT user_id, name, updated_at, session_count FROM users ORDER BY updated_at DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    def list_profiles_full(self) -> list[dict]:
        """Gibt alle Profildaten zurück — für Admin-Dashboard."""
        with get_connection(self._db_path) as conn:
            rows = conn.execute(
                """SELECT user_id, name, context, current_mode, session_count,
                          total_messages, onboarding_complete, problem_solving_profile,
                          identified_strengths, identified_blind_spots,
                          created_at, updated_at
                   FROM users ORDER BY updated_at DESC"""
            ).fetchall()
        return [dict(r) for r in rows]

    def get_all_sessions(self) -> list[dict]:
        """Gibt alle Sessions mit Nutzernamen zurück — für Admin-Dashboard."""
        with get_connection(self._db_path) as conn:
            rows = conn.execute(
                """SELECT s.session_id, s.user_id, u.name, s.provider, s.model,
                          s.message_count, s.total_tokens, s.avg_latency_ms,
                          s.mode_at_start, s.mode_at_end,
                          s.started_at, s.ended_at
                   FROM sessions s
                   JOIN users u ON s.user_id = u.user_id
                   ORDER BY s.started_at DESC"""
            ).fetchall()
        return [dict(r) for r in rows]

    def get_all_observations(self) -> list[dict]:
        """Gibt alle Observations mit Nutzernamen zurück — für Admin-Dashboard."""
        with get_connection(self._db_path) as conn:
            rows = conn.execute(
                """SELECT o.category, o.content, o.sentiment_score, o.mode,
                          o.created_at, u.name
                   FROM observations o
                   JOIN users u ON o.user_id = u.user_id
                   ORDER BY o.created_at DESC"""
            ).fetchall()
        return [dict(r) for r in rows]

    # ── Sessions ───────────────────────────────────────────────────────────────

    def start_session(self, profile: UserProfile, provider: str, model: str) -> SessionRecord:
        """Öffnet eine neue Session und verknüpft sie mit dem Nutzerprofil."""
        now = datetime.now().isoformat()
        session = SessionRecord(
            session_id=str(uuid.uuid4()),
            user_id=profile.user_id,
            provider=provider,
            model=model,
            started_at=now,
            mode_at_start=profile.current_mode,
        )
        self._save_session(session)

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
        """Hängt eine Nachricht an die Session und aktualisiert Metriken."""
        session.messages.append({
            "role":       role,
            "content":    content,
            "timestamp":  datetime.now().isoformat(),
            "tokens":     tokens,
            "latency_ms": latency_ms,
        })
        session.message_count += 1
        session.total_tokens += tokens

        if latency_ms > 0:
            n = session.message_count
            session.avg_latency_ms = round(
                session.avg_latency_ms * (n - 1) / n + latency_ms / n, 1
            )

        self._save_session(session)

    def close_session(self, session: SessionRecord, profile: UserProfile) -> None:
        """Schließt eine Session und aktualisiert das Profil."""
        session.ended_at = datetime.now().isoformat()
        session.mode_at_end = profile.current_mode
        profile.total_messages += session.message_count
        self._save_session(session)
        self.save_profile(profile)

    def get_onboarding_messages(self, user_id: str) -> list[dict]:
        """
        Gibt alle gespeicherten Nachrichten aus früheren Onboarding-Sessions zurück.
        Wird genutzt um das Onboarding nach Unterbrechung fortzusetzen.
        Filtert __start__-Trigger und leere Nachrichten heraus.
        """
        with get_connection(self._db_path) as conn:
            rows = conn.execute(
                """SELECT messages FROM sessions
                   WHERE user_id = ?
                   ORDER BY started_at ASC""",
                (user_id,),
            ).fetchall()

        all_messages = []
        for row in rows:
            msgs = json_decode(dict(row)["messages"]) or []
            for m in msgs:
                content = m.get("content", "").strip()
                if content and content != "__start__":
                    all_messages.append({"role": m["role"], "content": content})
        return all_messages

    def load_session(self, session_id: str) -> SessionRecord:
        """Lädt einen Session-Record anhand der session_id."""
        with get_connection(self._db_path) as conn:
            row = conn.execute(
                "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()

        if row is None:
            raise FileNotFoundError(f"No session found: {session_id}")

        return self._row_to_session(dict(row))

    # ── Private helpers ────────────────────────────────────────────────────────

    def _save_profile(self, profile: UserProfile) -> None:
        with get_connection(self._db_path) as conn:
            conn.execute(
                """
                INSERT INTO users
                    (user_id, name, context, current_mode, dominant_style,
                     traits, snapshots, session_count, total_messages,
                     identified_strengths, identified_blind_spots,
                     onboarding_complete, problem_solving_profile,
                     email, password_hash,
                     created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    name                    = excluded.name,
                    context                 = excluded.context,
                    current_mode            = excluded.current_mode,
                    dominant_style          = excluded.dominant_style,
                    traits                  = excluded.traits,
                    snapshots               = excluded.snapshots,
                    session_count           = excluded.session_count,
                    total_messages          = excluded.total_messages,
                    identified_strengths    = excluded.identified_strengths,
                    identified_blind_spots  = excluded.identified_blind_spots,
                    onboarding_complete     = excluded.onboarding_complete,
                    problem_solving_profile = excluded.problem_solving_profile,
                    email                   = excluded.email,
                    password_hash           = excluded.password_hash,
                    updated_at              = excluded.updated_at
                """,
                (
                    profile.user_id,
                    profile.name,
                    profile.context,
                    profile.current_mode.value,
                    profile.dominant_style.value if profile.dominant_style else None,
                    json_encode(profile.traits),
                    json_encode(profile.snapshots),
                    profile.session_count,
                    profile.total_messages,
                    json_encode(profile.identified_strengths),
                    json_encode(profile.identified_blind_spots),
                    1 if profile.onboarding_complete else 0,
                    profile.problem_solving_profile,
                    profile.email,
                    profile.password_hash,
                    profile.created_at,
                    profile.updated_at,
                ),
            )

    def _save_session(self, session: SessionRecord) -> None:
        with get_connection(self._db_path) as conn:
            conn.execute(
                """
                INSERT INTO sessions
                    (session_id, user_id, provider, model,
                     mode_at_start, mode_at_end, message_count,
                     total_tokens, avg_latency_ms, messages,
                     started_at, ended_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    mode_at_end    = excluded.mode_at_end,
                    message_count  = excluded.message_count,
                    total_tokens   = excluded.total_tokens,
                    avg_latency_ms = excluded.avg_latency_ms,
                    messages       = excluded.messages,
                    ended_at       = excluded.ended_at
                """,
                (
                    session.session_id,
                    session.user_id,
                    session.provider,
                    session.model,
                    session.mode_at_start.value,
                    session.mode_at_end.value,
                    session.message_count,
                    session.total_tokens,
                    session.avg_latency_ms,
                    json_encode(session.messages),
                    session.started_at,
                    session.ended_at,
                ),
            )

    def _row_to_profile(self, row: dict) -> UserProfile:
        return UserProfile(
            user_id=row["user_id"],
            name=row["name"],
            context=row["context"],
            current_mode=NeuroadaptiveMode(row["current_mode"]),
            dominant_style=LearningStyle(row["dominant_style"]) if row["dominant_style"] else None,
            traits=json_decode(row["traits"]) or {},
            snapshots=json_decode(row["snapshots"]) or [],
            session_count=row["session_count"],
            total_messages=row["total_messages"],
            identified_strengths=json_decode(row["identified_strengths"]) or [],
            identified_blind_spots=json_decode(row["identified_blind_spots"]) or [],
            onboarding_complete=bool(row.get("onboarding_complete", 0)),
            problem_solving_profile=row.get("problem_solving_profile", ""),
            email=row.get("email", ""),
            password_hash=row.get("password_hash", ""),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _row_to_session(self, row: dict) -> SessionRecord:
        return SessionRecord(
            session_id=row["session_id"],
            user_id=row["user_id"],
            provider=row["provider"],
            model=row["model"],
            started_at=row["started_at"],
            ended_at=row["ended_at"],
            mode_at_start=NeuroadaptiveMode(row["mode_at_start"]),
            mode_at_end=NeuroadaptiveMode(row["mode_at_end"]),
            message_count=row["message_count"],
            total_tokens=row["total_tokens"],
            avg_latency_ms=row["avg_latency_ms"],
            messages=json_decode(row["messages"]) or [],
        )
