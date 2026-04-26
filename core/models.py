"""
KAIA – Kinetic AI Agent
Data models for user profiles and session memory.

Design decision: Plain dataclasses with JSON serialization.
No ORM, no database overhead for the MVP.
Migration path: JSON → SQLite → PostgreSQL (if needed).
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class NeuroadaptiveMode(str, Enum):
    """
    The three stress-response states KAIA detects.
    Based on Polyvagal Theory (Porges, 1994, 2011).
    """
    FLOW   = "flow"    # engaged, curious, open to challenge
    FIGHT  = "fight"   # resistant, defensive, frustrated
    FLIGHT = "flight"  # avoidant, overwhelmed, withdrawing
    FREEZE = "freeze"  # blocked, paralyzed, disengaged
    UNKNOWN = "unknown"  # not yet assessed


class LearningStyle(str, Enum):
    """Detected dominant learning preference."""
    REFLECTIVE  = "reflective"   # thinks before acting
    ACTIVE      = "active"       # learns by doing
    CONCEPTUAL  = "conceptual"   # needs the big picture first
    SEQUENTIAL  = "sequential"   # prefers step-by-step


@dataclass
class PersonalitySnapshot:
    """
    A point-in-time reading of the user's personality and state.
    Captured during the assessment phase (KEEN dimension of KAIA).
    """
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    mode: NeuroadaptiveMode = NeuroadaptiveMode.UNKNOWN
    stress_level: int = 0          # 0 (none) to 10 (extreme)
    energy_level: int = 5          # 0 (depleted) to 10 (high)
    learning_style: Optional[LearningStyle] = None
    notes: str = ""                # free-text observations from assessment


@dataclass
class UserProfile:
    """
    Persistent profile for a single KAIA user.
    Grows richer with every session.

    This is the core data structure that enables KAIA's
    ADAPTIVE and AWARE dimensions — the agent knows the
    user better with each conversation.
    """
    user_id: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # Identity
    name: str = ""
    context: str = ""              # e.g. "preparing for data science exam"

    # Current state (updated each session)
    current_mode: NeuroadaptiveMode = NeuroadaptiveMode.UNKNOWN
    dominant_style: Optional[LearningStyle] = None

    # Personality traits (0.0 to 1.0 scale, updated incrementally)
    traits: dict[str, float] = field(default_factory=dict)
    # Examples:
    # "openness": 0.8       — receptive to new ideas
    # "perfectionism": 0.6  — sets high standards, can freeze
    # "autonomy_need": 0.7  — prefers self-directed learning

    # History
    snapshots: list[dict] = field(default_factory=list)
    session_count: int = 0
    total_messages: int = 0

    # Blind spots and strengths (populated by KAIA over time)
    identified_strengths: list[str] = field(default_factory=list)
    identified_blind_spots: list[str] = field(default_factory=list)

    # Onboarding
    onboarding_complete: bool = False
    problem_solving_profile: str = ""  # 2-3 sentence narrative from onboarding analysis

    # Auth
    email: str = ""
    password_hash: str = ""


@dataclass
class SessionRecord:
    """
    A single conversation session with KAIA.
    Stored separately from the profile to keep profiles lightweight.
    """
    session_id: str
    user_id: str
    provider: str                  # which LLM was used
    model: str
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    ended_at: Optional[str] = None
    mode_at_start: NeuroadaptiveMode = NeuroadaptiveMode.UNKNOWN
    mode_at_end: NeuroadaptiveMode = NeuroadaptiveMode.UNKNOWN
    message_count: int = 0
    total_tokens: int = 0
    avg_latency_ms: float = 0.0
    messages: list[dict] = field(default_factory=list)
    # Each message: {"role": "user"|"assistant", "content": "...", "timestamp": "..."}
