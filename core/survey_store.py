"""
KAIA – Kinetic AI Agent
Survey Store — GSE und PSI Pre/Post-Messungen

Standardisierte Skalen für die Thesis-Evaluation:

  GSE — General Self-Efficacy Scale (Schwarzer & Jerusalem, 1995)
        10 Items, Likert 1–4, Score 10–40
        Misst wahrgenommene allgemeine Selbstwirksamkeit

  PSI — Problem Solving Inventory, Kurzform (Heppner & Petersen, 1982)
        6 Items, Likert 1–5, Score nach Umkodierung
        Misst wahrgenommene Problemlösekompetenz (3 Subskalen:
        Lösungsvertrauen, Annäherungs-/Vermeidungsstil, Kontrollüberzeugung)

Pre-Messung:  vor der ersten Session
Post-Messung: nach Abschluss der Studie (mind. 3 Sessions)
"""

import uuid
from datetime import datetime
from pathlib import Path

from .db import get_connection, json_encode, json_decode


# ── GSE Items (Schwarzer & Jerusalem, 1995) ────────────────────────────────────
# Skala: 1 = Stimmt nicht | 2 = Stimmt kaum | 3 = Stimmt eher | 4 = Stimmt genau

GSE_ITEMS_DE = [
    "Wenn sich Widerstände auftun, finde ich Mittel und Wege, mich durchzusetzen.",
    "Die Lösung schwieriger Probleme gelingt mir immer, wenn ich mich darum bemühe.",
    "Es bereitet mir keine Schwierigkeiten, meine Absichten und Ziele zu verwirklichen.",
    "In unerwarteten Situationen weiß ich immer, wie ich mich verhalten soll.",
    "Auch bei überraschenden Ereignissen glaube ich, dass ich gut mit ihnen umgehen kann.",
    "Schwierigkeiten sehe ich gelassen entgegen, weil ich meinen Fähigkeiten vertrauen kann.",
    "Was auch immer passiert, ich werde schon klarkommen.",
    "Für jedes Problem kann ich eine Lösung finden.",
    "Wenn eine neue Sache auf mich zukommt, weiß ich, wie ich damit umgehen kann.",
    "Wenn ein Problem auftaucht, kann ich es aus eigener Kraft meistern.",
]

GSE_ITEMS_EN = [
    "I can always manage to solve difficult problems if I try hard enough.",
    "If someone opposes me, I can find the means and ways to get what I want.",
    "It is easy for me to stick to my aims and accomplish my goals.",
    "I am confident that I could deal efficiently with unexpected events.",
    "Thanks to my resourcefulness, I know how to handle unforeseen situations.",
    "I can solve most problems if I invest the necessary effort.",
    "I can remain calm when facing difficulties because I can rely on my coping abilities.",
    "When I am confronted with a problem, I can usually find several solutions.",
    "If I am in trouble, I can usually think of a solution.",
    "I can usually handle whatever comes my way.",
]

GSE_SCALE_DE = {1: "Stimmt nicht", 2: "Stimmt kaum", 3: "Stimmt eher", 4: "Stimmt genau"}
GSE_SCALE_EN = {1: "Not at all true", 2: "Hardly true", 3: "Moderately true", 4: "Exactly true"}


# ── PSI Items — Kurzform (adaptiert nach Heppner & Petersen, 1982) ─────────────
# Skala: 1 = Trifft gar nicht zu … 5 = Trifft vollständig zu
# Items mit * werden umgekehrt kodiert (score = 6 - raw)

PSI_ITEMS_DE = [
    ("Ich bin zuversichtlich, dass ich schwierige Probleme lösen kann, wenn ich es wirklich versuche.", False),
    ("Ich zweifle oft an meiner Fähigkeit, Probleme selbstständig zu lösen.", True),   # umgekehrt
    ("Wenn ein Problem auftaucht, gehe ich es direkt und aktiv an.", False),
    ("Ich neige dazu, Probleme so lange zu ignorieren, bis sie sich von selbst lösen.", True),  # umgekehrt
    ("Ich habe das Gefühl, die Kontrolle über meine eigenen Problemlöseprozesse zu haben.", False),
    ("Wenn ich an einem Problem sitze, fühle ich mich oft hilflos und weiß nicht weiter.", True),  # umgekehrt
]

PSI_ITEMS_EN = [
    ("I am confident that I can solve difficult problems if I really try.", False),
    ("I often doubt my ability to solve problems on my own.", True),
    ("When a problem comes up, I address it directly and actively.", False),
    ("I tend to ignore problems and hope they resolve themselves.", True),
    ("I feel in control of my own problem-solving processes.", False),
    ("When working on a problem, I often feel helpless and stuck.", True),
]

PSI_SCALE_DE = {1: "Trifft gar nicht zu", 2: "Trifft kaum zu", 3: "Teils/teils", 4: "Trifft eher zu", 5: "Trifft vollständig zu"}
PSI_SCALE_EN = {1: "Not at all true", 2: "Hardly true", 3: "Somewhat true", 4: "Mostly true", 5: "Completely true"}


# ── Survey Store ───────────────────────────────────────────────────────────────

class SurveyStore:

    def __init__(self, db_path: Path | None = None):
        self._db_path = db_path

    def save_survey(
        self,
        user_id: str,
        instrument: str,   # 'gse' oder 'psi'
        timing: str,       # 'pre' oder 'post'
        responses: dict,   # {item_index: raw_score}
    ) -> float:
        """
        Speichert eine Befragung und gibt den berechneten Gesamtscore zurück.
        PSI-Items mit umgekehrter Kodierung werden automatisch transformiert.
        """
        total_score = self._calculate_score(instrument, responses)
        now = datetime.now().isoformat()

        with get_connection(self._db_path) as conn:
            conn.execute(
                """
                INSERT INTO surveys (survey_id, user_id, timing, instrument, responses, total_score, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (str(uuid.uuid4()), user_id, timing, instrument,
                 json_encode(responses), total_score, now),
            )
        return total_score

    def has_survey(self, user_id: str, instrument: str, timing: str) -> bool:
        """Prüft ob eine Messung bereits vorliegt."""
        with get_connection(self._db_path) as conn:
            row = conn.execute(
                "SELECT survey_id FROM surveys WHERE user_id = ? AND instrument = ? AND timing = ?",
                (user_id, instrument, timing),
            ).fetchone()
        return row is not None

    def has_pre_surveys(self, user_id: str) -> bool:
        """Prüft ob beide Pre-Messungen (GSE + PSI) abgeschlossen sind."""
        return (
            self.has_survey(user_id, "gse", "pre") and
            self.has_survey(user_id, "psi", "pre")
        )

    def get_scores(self, user_id: str) -> list[dict]:
        """Gibt alle Survey-Ergebnisse eines Nutzers zurück."""
        with get_connection(self._db_path) as conn:
            rows = conn.execute(
                "SELECT instrument, timing, total_score, created_at FROM surveys WHERE user_id = ? ORDER BY created_at",
                (user_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_all_scores(self) -> list[dict]:
        """Gibt alle Survey-Ergebnisse aller Nutzer zurück — für Admin-Dashboard."""
        with get_connection(self._db_path) as conn:
            rows = conn.execute(
                """
                SELECT s.instrument, s.timing, s.total_score, s.created_at,
                       u.name, u.user_id
                FROM surveys s
                JOIN users u ON s.user_id = u.user_id
                ORDER BY s.created_at
                """,
            ).fetchall()
        return [dict(r) for r in rows]

    # ── Private ────────────────────────────────────────────────────────────────

    def _calculate_score(self, instrument: str, responses: dict) -> float:
        """Berechnet den Gesamtscore. PSI: umgekehrt kodierte Items werden transformiert."""
        if instrument == "gse":
            return float(sum(responses.values()))

        if instrument == "psi":
            total = 0.0
            for i, (_, reverse) in enumerate(PSI_ITEMS_DE):
                raw = responses.get(i, 3)
                total += (6 - raw) if reverse else raw
            return total

        return float(sum(responses.values()))
