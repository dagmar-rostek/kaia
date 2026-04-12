"""
KAIA – Kinetic AI Agent
Onboarding Analyzer — Extrahiert strukturierte Profildaten aus dem Onboarding-Gespräch.

Nach Abschluss des dreiphasigen Onboardings analysiert dieser Modul die gesamte
Konversation und extrahiert:
  - GSE-Scores (Items 0–9, Skala 1–4) — aus den Szenarien operationalisiert
  - Stärken (3–5 konkrete, spezifische Stärken)
  - Blinde Flecken (2–3 wachstumsorientiert)
  - Problemlöseprofil (2–3 Sätze Freitext)

Wissenschaftlicher Hintergrund:
  - GSE-Operationalisierung: Schwarzer & Jerusalem (1995), 1=nicht zutreffend, 4=genau zutreffend
  - Qualitative Inhaltsanalyse nach Mayring (2015)
"""

import json
import re


# ── Analyzer Prompt ────────────────────────────────────────────────────────────

_ANALYZER_SYSTEM_DE = """Du bist ein wissenschaftlicher Analyse-Agent.
Du erhältst ein vollständiges Onboarding-Gespräch zwischen KAIA (Assistent) und einem Lernenden (User).
KAIA hat in Phase 2 des Gesprächs 10 Szenario-Fragen gestellt, die intern auf die 10 Items der
General Self-Efficacy Scale (GSE, Schwarzer & Jerusalem, 1995) gemappt sind.

GSE Item-Mapping (Szenario-Reihenfolge Q1–Q10):
  Q1  → Item 0: Widerstände überwinden, Mittel und Wege finden
  Q2  → Item 1: Schwierige Probleme durch Bemühen lösen
  Q3  → Item 2: Absichten und Ziele verwirklichen
  Q4  → Item 3: Verhalten in unerwarteten Situationen
  Q5  → Item 4: Überraschende Ereignisse bewältigen
  Q6  → Item 5: Gelassenheit durch Vertrauen in eigene Fähigkeiten
  Q7  → Item 6: Allgemeine Resilienz "Ich werde klarkommen"
  Q8  → Item 7: Für jedes Problem eine Lösung finden
  Q9  → Item 8: Mit neuen Dingen umgehen
  Q10 → Item 9: Probleme aus eigener Kraft meistern

Bewerte jede User-Antwort auf dem jeweiligen GSE-Item:
  1 = Stimmt nicht (vermeidet, weicht aus, starkes Misstrauen in eigene Fähigkeiten)
  2 = Stimmt kaum (eher unsicher, braucht viel externe Unterstützung)
  3 = Stimmt eher (meistens zuversichtlich, kleinere Zweifel)
  4 = Stimmt genau (klares Vertrauen, aktive Bewältigungsstrategie)

Basierend auf dem GESAMTEN Gespräch (nicht nur Phase 2) identifiziere außerdem:
  - 3–5 konkrete Stärken (spezifisch aus dem Gespräch, nicht generisch)
  - 2–3 blinde Flecken (wachstumsorientiert formuliert, niemals abwertend)
  - Ein 2–3-sätiges Problemlöseprofil (wie geht diese Person an Probleme heran?)

Antworte AUSSCHLIESSLICH mit validem JSON, kein Markdown, keine Erklärung:
{
  "gse_scores": {"0": 3, "1": 4, "2": 2, "3": 3, "4": 3, "5": 4, "6": 3, "7": 2, "8": 3, "9": 4},
  "strengths": ["...", "...", "..."],
  "blind_spots": ["...", "..."],
  "problem_solving_profile": "..."
}"""

_ANALYZER_SYSTEM_EN = """You are a scientific analysis agent.
You receive a complete onboarding conversation between KAIA (assistant) and a learner (user).
In Phase 2 of the conversation, KAIA asked 10 scenario questions that are internally mapped
to the 10 items of the General Self-Efficacy Scale (GSE, Schwarzer & Jerusalem, 1995).

GSE Item Mapping (scenario order Q1–Q10):
  Q1  → Item 0: Overcoming obstacles, finding means and ways
  Q2  → Item 1: Solving difficult problems through effort
  Q3  → Item 2: Achieving intentions and goals
  Q4  → Item 3: Coping with unexpected situations (behavior)
  Q5  → Item 4: Coping with surprising events (confidence)
  Q6  → Item 5: Staying calm through trust in own abilities
  Q7  → Item 6: General resilience ("I'll manage")
  Q8  → Item 7: Finding solutions to every problem
  Q9  → Item 8: Handling new things
  Q10 → Item 9: Solving problems independently

Rate each user response on the corresponding GSE item:
  1 = Not at all true (avoids, deflects, strong distrust in own abilities)
  2 = Hardly true (rather uncertain, needs much external support)
  3 = Moderately true (mostly confident, minor doubts)
  4 = Exactly true (clear confidence, active coping strategy)

Based on the FULL conversation (not just Phase 2), also identify:
  - 3–5 concrete strengths (specific to this conversation, not generic)
  - 2–3 blind spots (growth-oriented language, never judgmental)
  - A 2–3 sentence problem-solving profile (how does this person approach problems?)

Respond ONLY with valid JSON, no markdown, no explanation:
{
  "gse_scores": {"0": 3, "1": 4, "2": 2, "3": 3, "4": 3, "5": 4, "6": 3, "7": 2, "8": 3, "9": 4},
  "strengths": ["...", "...", "..."],
  "blind_spots": ["...", "..."],
  "problem_solving_profile": "..."
}"""


class OnboardingAnalyzer:
    """
    Analysiert das abgeschlossene Onboarding-Gespräch und extrahiert strukturierte
    Profildaten via einem zweiten LLM-Call.
    """

    def analyze(
        self,
        messages: list[dict],
        provider,
        language: str = "de",
    ) -> dict:
        """
        Analysiert die Onboarding-Konversation.

        Args:
            messages:  Liste der Chat-Nachrichten ({"role": ..., "content": ...})
            provider:  LLM-Provider (muss .complete() unterstützen)
            language:  "de" oder "en"

        Returns:
            dict mit: gse_scores, strengths, blind_spots, problem_solving_profile
        """
        # Konversation als Transcript formatieren
        transcript = self._build_transcript(messages)

        system_prompt = _ANALYZER_SYSTEM_DE if language == "de" else _ANALYZER_SYSTEM_EN

        try:
            from providers import Message as ProviderMessage
            trigger = [ProviderMessage(
                role="user",
                content=f"Hier ist das Onboarding-Gespräch zur Analyse:\n\n{transcript}"
                        if language == "de"
                        else f"Here is the onboarding conversation to analyze:\n\n{transcript}",
            )]
            response = provider.complete(trigger, system_prompt)
            return self._parse_response(response.content)
        except Exception:
            return self._fallback()

    # ── Private ────────────────────────────────────────────────────────────────

    def _build_transcript(self, messages: list[dict]) -> str:
        lines = []
        for msg in messages:
            role = "KAIA" if msg["role"] == "assistant" else "User"
            # [ONBOARDING_COMPLETE] aus Transcript entfernen
            content = msg["content"].replace("[ONBOARDING_COMPLETE]", "").strip()
            if content:
                lines.append(f"{role}: {content}")
        return "\n\n".join(lines)

    def _parse_response(self, raw: str) -> dict:
        """Extrahiert JSON aus LLM-Antwort — tolerant gegenüber Markdown-Wrapping."""
        # Markdown-Codeblöcke entfernen
        cleaned = re.sub(r"```(?:json)?", "", raw).strip()
        # Erstes { bis letztes } extrahieren
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            return self._fallback()
        try:
            data = json.loads(match.group())
            # Typsicherheit: gse_scores als int-Werte
            gse_raw = data.get("gse_scores", {})
            gse_scores = {int(k): max(1, min(4, int(v))) for k, v in gse_raw.items()}
            # Fehlende Items mit 3 (Mittelwert) auffüllen
            for i in range(10):
                if i not in gse_scores:
                    gse_scores[i] = 3
            return {
                "gse_scores":             gse_scores,
                "strengths":              data.get("strengths", []),
                "blind_spots":            data.get("blind_spots", []),
                "problem_solving_profile": data.get("problem_solving_profile", ""),
            }
        except (json.JSONDecodeError, ValueError, KeyError):
            return self._fallback()

    def _fallback(self) -> dict:
        """Gibt neutrale Defaults zurück wenn die Analyse fehlschlägt."""
        return {
            "gse_scores":              {i: 3 for i in range(10)},
            "strengths":               [],
            "blind_spots":             [],
            "problem_solving_profile": "",
        }
