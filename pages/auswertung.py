"""
KAIA – Kinetic AI Agent
Auswertungsseite — Persönliches Lernprofil

Zeigt nach abgeschlossenem Onboarding:
  - Radar-Chart: Selbstwirksamkeitsprofil (GSE, 10 Dimensionen)
  - Stärken-Karten
  - Blinde-Flecken / Wachstumsfelder-Karten
  - Persönliches Problemlöseprofil
  - GSE-Gesamtscore
"""

import os
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

from core import ProfileStore, SurveyStore, t

load_dotenv()

DATA_DIR = Path(os.environ.get("DATA_DIR", "data"))
DB_PATH  = DATA_DIR / "kaia.db"

st.set_page_config(page_title="KAIA – Auswertung", page_icon="✦", layout="centered")

# ── Session state übernehmen ───────────────────────────────────────────────────
lang  = st.session_state.get("lang", "de")
theme = st.session_state.get("theme", "dark")

if theme == "light":
    st.markdown("""
    <style>
    .stApp { background-color: #f5f7fa; }
    .stApp > header { background-color: #f5f7fa !important; }
    section[data-testid="stSidebar"] { background-color: #e8ecf1; }
    .stApp, .stMarkdown, p, span, label, h1, h2, h3,
    div[data-testid="stChatMessage"] { color: #1a1d23 !important; }
    </style>
    """, unsafe_allow_html=True)

# ── Stores ─────────────────────────────────────────────────────────────────────
if "store" not in st.session_state:
    st.session_state.store = ProfileStore(db_path=DB_PATH)
if "survey_store" not in st.session_state:
    st.session_state.survey_store = SurveyStore(db_path=DB_PATH)

store        = st.session_state.store
survey_store = st.session_state.survey_store
profile      = st.session_state.get("profile")

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("✦ " + t("auswertung_title", lang))
st.divider()

# ── Kein Profil ────────────────────────────────────────────────────────────────
if not profile:
    st.info(t("auswertung_no_profile", lang))
    st.stop()

# ── Onboarding noch nicht abgeschlossen ───────────────────────────────────────
if not profile.onboarding_complete:
    st.info(t("auswertung_locked", lang))
    st.stop()

# ── GSE-Scores laden ───────────────────────────────────────────────────────────
scores_list = survey_store.get_scores(profile.user_id)
gse_pre = next(
    (s for s in scores_list if s["instrument"] == "gse" and s["timing"] == "pre"),
    None,
)

# ── Layout ─────────────────────────────────────────────────────────────────────
dims = t("auswertung_gse_dims", lang)  # Liste mit 10 Dimensionsnamen

# ── Radar-Chart ────────────────────────────────────────────────────────────────
st.subheader(t("auswertung_radar_title", lang))

if gse_pre:
    # Aus survey-Tabelle nur den total_score — für detaillierte Item-Scores brauchen wir responses
    from core.db import get_connection, json_decode
    with get_connection(DB_PATH) as conn:
        row = conn.execute(
            "SELECT responses FROM surveys WHERE user_id = ? AND instrument = ? AND timing = ?",
            (profile.user_id, "gse", "pre"),
        ).fetchone()

    if row:
        raw_responses = json_decode(dict(row)["responses"])
        # Keys können strings oder ints sein
        item_scores = [int(raw_responses.get(str(i), raw_responses.get(i, 3))) for i in range(10)]
    else:
        item_scores = [3] * 10

    # Radar schließen (ersten Punkt wiederholen)
    radar_values = item_scores + [item_scores[0]]
    radar_dims   = dims + [dims[0]]

    is_dark = (theme == "dark")
    bg_color   = "rgba(0,0,0,0)"
    line_color = "#7BB4E3"
    fill_color = "rgba(123,180,227,0.25)"
    text_color = "#e0e0e0" if is_dark else "#1a1d23"
    grid_color = "rgba(255,255,255,0.15)" if is_dark else "rgba(0,0,0,0.1)"

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=radar_values,
        theta=radar_dims,
        fill="toself",
        fillcolor=fill_color,
        line=dict(color=line_color, width=2),
        marker=dict(size=6, color=line_color),
        name=profile.name,
    ))
    fig.update_layout(
        polar=dict(
            bgcolor=bg_color,
            radialaxis=dict(
                visible=True,
                range=[0, 4],
                tickvals=[1, 2, 3, 4],
                tickfont=dict(size=10, color=text_color),
                gridcolor=grid_color,
                linecolor=grid_color,
            ),
            angularaxis=dict(
                tickfont=dict(size=11, color=text_color),
                gridcolor=grid_color,
                linecolor=grid_color,
            ),
        ),
        paper_bgcolor=bg_color,
        plot_bgcolor=bg_color,
        showlegend=False,
        margin=dict(l=60, r=60, t=40, b=40),
        height=420,
    )
    st.plotly_chart(fig, use_container_width=True)

    # GSE-Gesamtscore
    total = sum(item_scores)
    st.metric(
        label=t("auswertung_gse_total", lang),
        value=f"{total} / 40",
        help=t("auswertung_gse_max", lang),
    )
else:
    st.info("Keine GSE-Scores vorhanden." if lang == "de" else "No GSE scores available.")

st.divider()

# ── Stärken ────────────────────────────────────────────────────────────────────
st.subheader(t("auswertung_strengths", lang))
if profile.identified_strengths:
    cols = st.columns(min(3, len(profile.identified_strengths)))
    for i, strength in enumerate(profile.identified_strengths):
        with cols[i % len(cols)]:
            st.success(f"✓  {strength}")
else:
    st.caption("—")

st.divider()

# ── Blinde Flecken / Wachstumsfelder ──────────────────────────────────────────
st.subheader(t("auswertung_blindspots", lang))
if profile.identified_blind_spots:
    cols = st.columns(min(3, len(profile.identified_blind_spots)))
    for i, spot in enumerate(profile.identified_blind_spots):
        with cols[i % len(cols)]:
            st.info(f"◎  {spot}")
else:
    st.caption("—")

st.divider()

# ── Problemlöseprofil ──────────────────────────────────────────────────────────
st.subheader(t("auswertung_psp", lang))
if profile.problem_solving_profile:
    st.markdown(f"> {profile.problem_solving_profile}")
else:
    st.caption("—")
