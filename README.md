# KAIA – Kinetic AI Agent

> **K**een · **A**daptive · **I**ntelligent · **A**ware

Masterthesis | SRH Fernhochschule | M.Sc. Data Science & Analytics  
Dagmar Rostek · 2025/2026

---

## Kurzübersicht

KAIA ist ein empathischer AI-Agent zur neuroadaptiven personalisierten Lernbegleitung. Der Agent erkennt den aktuellen Zustand eines Lernenden (Persönlichkeitsprofil, Stresslevel, Lernmodus) und passt Tonalität, Herausforderungsniveau und Begleitstrategie in Echtzeit an – ohne den Lernenden zu führen, sondern ihn in Bewegung zu bringen.

---

## Branch-Struktur

| Branch | Zweck |
|---|---|
| `main` | Stabiler Code, nur via Pull Request |
| `develop` | Aktive Entwicklung |
| `feature/provider-claude` | Claude API Integration |
| `feature/provider-mistral` | Mistral AI Integration (EU-Souveränität) |
| `feature/provider-ollama` | Ollama lokal (maximale DSGVO-Konformität) |
| `eval/llm-comparison` | LLM-Evaluationsexperimente |

---

## Projektstruktur

```
kaia/
├── providers/          # LLM-Abstraktionsschicht
│   ├── base.py         # Abstrakte Basisklasse
│   ├── claude_provider.py
│   ├── mistral_provider.py
│   ├── ollama_provider.py
│   └── __init__.py     # Factory & öffentliche API
├── core/               # KAIA-Logik (Assessment, State, Prompt Builder)
├── data/               # Nutzerprofil-Speicher (lokal, nicht in Git)
├── app.py              # Streamlit UI (Einstiegspunkt)
├── requirements.txt
└── .env.example        # API-Key-Vorlage
```

---

## Schnellstart

```bash
# 1. Repository klonen
git clone https://github.com/deinname/kaia.git
cd kaia

# 2. Virtuelle Umgebung
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Abhängigkeiten
pip install -r requirements.txt

# 4. API Keys eintragen
cp .env.example .env
# .env öffnen und Keys eintragen

# 5. Provider testen
python test_providers.py

# 6. App starten
streamlit run app.py
```

---

## LLM-Evaluation

Drei Provider werden gegenübergestellt:

| Provider | Anbieter | Datenschutz | Thesis-Relevanz |
|---|---|---|---|
| Claude Sonnet 4 | Anthropic (USA) | API-basiert | Entwicklungs-Baseline |
| Mistral Large | Mistral AI (FR) | EU-Souveränität | DSGVO-Vergleich |
| Llama 3.2 via Ollama | Meta / lokal | 100 % lokal | Maximale Konformität |

---

## Theoretische Grundlage

- Polyvagal-Theorie (Porges, 1994, 2011) – neuroadaptive Zustandserkennung
- Selbstbestimmungstheorie (Deci & Ryan, 2000) – intrinsische Motivation
- Flow-Theorie (Csikszentmihalyi / Oliveira & Hamari, 2024)
- Design Science Research (Hevner et al., 2004) – Forschungsmethode

---

## Hinweis

Dieses Repository ist Teil einer Masterthesis.  
Nutzerdaten aus der Evaluationsstudie werden **nicht** versioniert (siehe `.gitignore`).
