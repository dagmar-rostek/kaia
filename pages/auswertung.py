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

# ── Alle GSE-Messungen laden ───────────────────────────────────────────────────
from core.db import get_connection, json_decode

dims = t("auswertung_gse_dims", lang)

def _load_item_scores(user_id: str, timing: str) -> list[int] | None:
    """Lädt die 10 Item-Scores einer GSE-Messung aus der DB."""
    with get_connection(DB_PATH) as conn:
        row = conn.execute(
            "SELECT responses FROM surveys WHERE user_id = ? AND instrument = ? AND timing = ? ORDER BY created_at DESC LIMIT 1",
            (user_id, "gse", timing),
        ).fetchone()
    if not row:
        return None
    raw = json_decode(dict(row)["responses"])
    return [max(1, min(4, int(raw.get(str(i), raw.get(i, 3))))) for i in range(10)]

# Baseline (Onboarding)
baseline_scores = _load_item_scores(profile.user_id, "pre")

# Neueste Session-Messung (session_2, session_3, ...)
latest_session_scores = None
latest_session_label  = None
for sn in range(profile.session_count, 1, -1):
    s = _load_item_scores(profile.user_id, f"session_{sn}")
    if s:
        latest_session_scores = s
        latest_session_label  = f"Session {sn}"
        break

# ── Radar-Chart ────────────────────────────────────────────────────────────────
st.subheader(t("auswertung_radar_title", lang))

if baseline_scores:
    radar_dims = dims + [dims[0]]
    is_dark    = (theme == "dark")
    bg_color   = "rgba(0,0,0,0)"
    text_color = "#e0e0e0" if is_dark else "#1a1d23"
    grid_color = "rgba(255,255,255,0.15)" if is_dark else "rgba(0,0,0,0.1)"

    fig = go.Figure()

    # Baseline — Blau
    fig.add_trace(go.Scatterpolar(
        r=baseline_scores + [baseline_scores[0]],
        theta=radar_dims,
        fill="toself",
        fillcolor="rgba(123,180,227,0.2)",
        line=dict(color="#7BB4E3", width=2),
        marker=dict(size=5, color="#7BB4E3"),
        name="Baseline" if lang == "de" else "Baseline",
    ))

    # Entwicklung — Grün (nur wenn Folgesession-Messung vorhanden)
    if latest_session_scores:
        fig.add_trace(go.Scatterpolar(
            r=latest_session_scores + [latest_session_scores[0]],
            theta=radar_dims,
            fill="toself",
            fillcolor="rgba(100,200,140,0.2)",
            line=dict(color="#64C88C", width=2, dash="dot"),
            marker=dict(size=5, color="#64C88C"),
            name=latest_session_label,
        ))

    fig.update_layout(
        polar=dict(
            bgcolor=bg_color,
            radialaxis=dict(
                visible=True, range=[0, 4], tickvals=[1, 2, 3, 4],
                tickfont=dict(size=10, color=text_color),
                gridcolor=grid_color, linecolor=grid_color,
            ),
            angularaxis=dict(
                tickfont=dict(size=11, color=text_color),
                gridcolor=grid_color, linecolor=grid_color,
            ),
        ),
        paper_bgcolor=bg_color,
        plot_bgcolor=bg_color,
        showlegend=bool(latest_session_scores),
        legend=dict(font=dict(color=text_color)),
        margin=dict(l=60, r=60, t=40, b=40),
        height=440,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Score-Metriken nebeneinander
    baseline_total = sum(baseline_scores)
    if latest_session_scores:
        col1, col2, col3 = st.columns(3)
        latest_total = sum(latest_session_scores)
        delta = latest_total - baseline_total
        col1.metric(
            "Baseline",
            f"{baseline_total} / 40",
        )
        col2.metric(
            latest_session_label,
            f"{latest_total} / 40",
            delta=f"{delta:+d}" if delta != 0 else "±0",
        )
        col3.metric(
            t("auswertung_gse_total", lang),
            f"{latest_total} / 40",
            help=t("auswertung_gse_max", lang),
        )
    else:
        st.metric(
            label=t("auswertung_gse_total", lang),
            value=f"{baseline_total} / 40",
            help=t("auswertung_gse_max", lang),
        )
else:
    st.info("Keine GSE-Scores vorhanden." if lang == "de" else "No GSE scores available.")

st.divider()

# ── Stärken — aus allen Sessions kumuliert ─────────────────────────────────────
st.subheader(t("auswertung_strengths", lang))

# Aus Observations (Folgesessions) zusätzliche Stärken laden
with get_connection(DB_PATH) as conn:
    obs_strengths = conn.execute(
        "SELECT content FROM observations WHERE user_id = ? AND category = 'strength' ORDER BY created_at",
        (profile.user_id,),
    ).fetchall()

all_strengths = list(profile.identified_strengths)
for row in obs_strengths:
    s = dict(row)["content"]
    if s not in all_strengths:
        all_strengths.append(s)

if all_strengths:
    cols = st.columns(min(3, len(all_strengths)))
    for i, strength in enumerate(all_strengths):
        # Erste N Stärken = Onboarding (Blau), Rest = neue Erkenntnisse (Grün)
        is_new = i >= len(profile.identified_strengths)
        with cols[i % len(cols)]:
            if is_new:
                st.success(f"✦  {strength}")
                st.caption("neu" if lang == "de" else "new")
            else:
                st.success(f"✓  {strength}")
else:
    st.caption("—")

st.divider()

# ── Blinde Flecken / Wachstumsfelder — kumuliert ──────────────────────────────
st.subheader(t("auswertung_blindspots", lang))

with get_connection(DB_PATH) as conn:
    obs_blindspots = conn.execute(
        "SELECT content FROM observations WHERE user_id = ? AND category = 'blind_spot' ORDER BY created_at",
        (profile.user_id,),
    ).fetchall()

all_blindspots = list(profile.identified_blind_spots)
for row in obs_blindspots:
    s = dict(row)["content"]
    if s not in all_blindspots:
        all_blindspots.append(s)

if all_blindspots:
    cols = st.columns(min(3, len(all_blindspots)))
    for i, spot in enumerate(all_blindspots):
        is_new = i >= len(profile.identified_blind_spots)
        with cols[i % len(cols)]:
            if is_new:
                st.info(f"◈  {spot}")
                st.caption("neu" if lang == "de" else "new")
            else:
                st.info(f"◎  {spot}")
else:
    st.caption("—")

st.divider()

# ── Problemlöseprofil ──────────────────────────────────────────────────────────
st.subheader(t("auswertung_psp", lang))
if profile.problem_solving_profile:
    st.markdown(f"> {profile.problem_solving_profile}")

# Neueste allgemeine Observations aus Folgesessions
with get_connection(DB_PATH) as conn:
    obs_general = conn.execute(
        "SELECT content, created_at FROM observations WHERE user_id = ? AND category = 'general' ORDER BY created_at DESC LIMIT 5",
        (profile.user_id,),
    ).fetchall()

if obs_general:
    label = "Neue Erkenntnisse aus deinen Sessions" if lang == "de" else "New insights from your sessions"
    with st.expander(label, expanded=False):
        for row in obs_general:
            r = dict(row)
            date = r["created_at"][:10]
            st.caption(f"{date} — {r['content']}")

if not profile.problem_solving_profile and not obs_general:
    st.caption("—")
