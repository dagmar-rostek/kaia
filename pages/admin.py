"""
KAIA – Kinetic AI Agent
Admin-Dashboard — Learning Analytics

Zugang: ADMIN_PASSWORD aus .env
Zeigt alle Nutzerdaten, Sessions, Survey-Scores und Observations.
"""

import json
import os
from pathlib import Path

import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

from core import ProfileStore, SurveyStore, t
from core.db import get_connection, json_decode
from core.i18n import TRANSLATIONS
from core.memory_store import MemoryStore

_ROOT = Path(__file__).parent.parent
load_dotenv(_ROOT / ".env", override=True)

DATA_DIR       = Path(os.environ.get("DATA_DIR", str(_ROOT / "data")))
DB_PATH        = DATA_DIR / "kaia.db"
CHROMA_PATH    = DATA_DIR / "chroma"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "kaia-admin")

st.set_page_config(page_title="KAIA Admin", page_icon="⚙", layout="wide")

# ── Theme ──────────────────────────────────────────────────────────────────────
lang  = st.session_state.get("lang", "de")
theme = st.session_state.get("theme", "dark")

if theme == "light":
    st.markdown("""<style>
    .stApp { background-color: #f5f7fa; }
    section[data-testid="stSidebar"] { background-color: #e8ecf1; }
    </style>""", unsafe_allow_html=True)

# ── Auth ───────────────────────────────────────────────────────────────────────
if "admin_auth" not in st.session_state:
    st.session_state.admin_auth = False

if not st.session_state.admin_auth:
    st.title("⚙ KAIA Admin")
    st.divider()
    pw = st.text_input(
        "Admin-Passwort" if lang == "de" else "Admin Password",
        type="password",
    )
    if st.button("Anmelden" if lang == "de" else "Login", type="primary"):
        if pw == ADMIN_PASSWORD:
            st.session_state.admin_auth = True
            st.rerun()
        else:
            st.error("Falsches Passwort." if lang == "de" else "Wrong password.")
    st.stop()

# ── Stores ─────────────────────────────────────────────────────────────────────
store        = ProfileStore(db_path=DB_PATH)
survey_store = SurveyStore(db_path=DB_PATH)

# ── Daten laden ────────────────────────────────────────────────────────────────
profiles  = store.list_profiles_full()
sessions  = store.get_all_sessions()
obs_all   = store.get_all_observations()
gse_all   = survey_store.get_all_scores()

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("⚙ KAIA Admin — Learning Analytics")
if st.button("Abmelden" if lang == "de" else "Logout", key="logout"):
    st.session_state.admin_auth = False
    st.rerun()
st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# TAB-NAVIGATION
# ══════════════════════════════════════════════════════════════════════════════
tab_labels = (
    ["📊 Übersicht", "👤 Nutzer", "📈 GSE-Auswertung", "💬 Sessions", "🔍 Observations"]
    if lang == "de" else
    ["📊 Overview", "👤 Users", "📈 GSE Analysis", "💬 Sessions", "🔍 Observations"]
)
tabs = st.tabs(tab_labels)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — ÜBERSICHT
# ══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    n_users     = len(profiles)
    n_onboarded = sum(1 for p in profiles if p.get("onboarding_complete"))
    n_sessions  = len(sessions)
    n_messages  = sum(s.get("message_count", 0) for s in sessions)

    providers = {}
    for s in sessions:
        p = s.get("provider", "?")
        providers[p] = providers.get(p, 0) + 1

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Nutzer gesamt" if lang == "de" else "Total users",       n_users)
    c2.metric("Onboarding abgeschlossen" if lang == "de" else "Onboarding complete", n_onboarded)
    c3.metric("Sessions gesamt" if lang == "de" else "Total sessions",  n_sessions)
    c4.metric("Nachrichten gesamt" if lang == "de" else "Total messages", n_messages)

    st.divider()

    col_a, col_b = st.columns(2)

    # Provider-Verteilung
    with col_a:
        st.subheader("LLM Provider")
        if providers:
            fig = px.pie(
                names=list(providers.keys()),
                values=list(providers.values()),
                color_discrete_sequence=["#7BB4E3", "#64C88C", "#F0A868"],
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=30, b=0),
                height=260,
                showlegend=True,
                legend=dict(font=dict(color="#e0e0e0" if theme == "dark" else "#1a1d23")),
            )
            fig.update_traces(textfont_color="#e0e0e0" if theme == "dark" else "#1a1d23")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.caption("—")

    # Neuroadaptive Modi
    with col_b:
        st.subheader("Neuroadaptive Modi (Session-Ende)" if lang == "de" else "Neuroadaptive Modes (end of session)")
        modes = {}
        for s in sessions:
            m = s.get("mode_at_end", "unknown")
            modes[m] = modes.get(m, 0) + 1
        if modes:
            color_map = {
                "flow": "#64C88C", "fight": "#E37B7B",
                "flight": "#F0A868", "freeze": "#9B8EC4", "unknown": "#888",
            }
            fig2 = px.bar(
                x=list(modes.keys()), y=list(modes.values()),
                color=list(modes.keys()),
                color_discrete_map=color_map,
                labels={"x": "Modus", "y": "Sessions"},
            )
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                margin=dict(l=0, r=0, t=10, b=0),
                height=260,
                xaxis=dict(tickfont=dict(color="#e0e0e0" if theme == "dark" else "#1a1d23")),
                yaxis=dict(tickfont=dict(color="#e0e0e0" if theme == "dark" else "#1a1d23")),
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.caption("—")

    # Stimmungsverlauf
    st.subheader("Stimmungsverlauf (Sentiment)" if lang == "de" else "Sentiment over time")
    mood_obs = [o for o in obs_all if o.get("category") == "mood" and o.get("sentiment_score") is not None]
    if mood_obs:
        dates  = [o["created_at"][:10] for o in mood_obs]
        scores = [o["sentiment_score"] for o in mood_obs]
        names  = [o["name"] for o in mood_obs]
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=dates, y=scores,
            mode="markers+lines",
            marker=dict(color="#7BB4E3", size=8),
            line=dict(color="#7BB4E3", width=1),
            text=names,
            hovertemplate="%{text}: %{y:.2f}<extra></extra>",
        ))
        fig3.add_hline(y=0, line_dash="dot", line_color="#888", line_width=1)
        fig3.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(range=[-1.1, 1.1], title="Sentiment",
                       tickfont=dict(color="#e0e0e0" if theme == "dark" else "#1a1d23")),
            xaxis=dict(tickfont=dict(color="#e0e0e0" if theme == "dark" else "#1a1d23")),
            margin=dict(l=0, r=0, t=10, b=0),
            height=220,
        )
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.caption("Noch keine Stimmungsdaten." if lang == "de" else "No sentiment data yet.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — NUTZER
# ══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    st.subheader(f"{n_users} Nutzer registriert" if lang == "de" else f"{n_users} users registered")

    gse_dims = TRANSLATIONS[lang]["auswertung_gse_dims"]

    for p in profiles:
        onboarded = bool(p.get("onboarding_complete"))
        badge = "✅" if onboarded else "⏳"
        label = f"{badge} **{p['name']}** — {p['session_count']} Sessions · {p['updated_at'][:10]}"

        with st.expander(label, expanded=False):
            col1, col2 = st.columns([1, 2])

            with col1:
                st.caption(f"**Kontext:** {p.get('context') or '—'}")
                st.caption(f"**Modus:** {p.get('current_mode', '?')}")
                st.caption(f"**Onboarding:** {'Ja' if onboarded else 'Nein'}")
                st.caption(f"**Registriert:** {p['created_at'][:10]}")
                st.caption(f"**Nachrichten gesamt:** {sum(s['message_count'] for s in sessions if s['user_id'] == p['user_id'])}")

                if p.get("problem_solving_profile"):
                    st.markdown("**Problemlöseprofil:**")
                    st.markdown(f"> {p['problem_solving_profile']}")

                strengths  = json_decode(p.get("identified_strengths", "[]")) or []
                blindspots = json_decode(p.get("identified_blind_spots", "[]")) or []

                if strengths:
                    st.markdown("**Stärken:**")
                    for s in strengths:
                        st.success(f"✓ {s}")
                if blindspots:
                    st.markdown("**Wachstumsfelder:**")
                    for b in blindspots:
                        st.info(f"◎ {b}")

            with col2:
                # GSE-Verlauf für diesen Nutzer
                user_surveys = [g for g in gse_all if g["user_id"] == p["user_id"] and g["instrument"] == "gse"]

                if user_surveys:
                    # Item-Scores aus DB laden
                    def load_scores(uid, timing):
                        with get_connection(DB_PATH) as conn:
                            row = conn.execute(
                                "SELECT responses FROM surveys WHERE user_id=? AND instrument='gse' AND timing=? ORDER BY created_at DESC LIMIT 1",
                                (uid, timing),
                            ).fetchone()
                        if not row:
                            return None
                        raw = json_decode(dict(row)["responses"])
                        return [max(1, min(4, int(raw.get(str(i), raw.get(i, 3))))) for i in range(10)]

                    baseline = load_scores(p["user_id"], "pre")
                    is_dark  = (theme == "dark")
                    tc       = "#e0e0e0" if is_dark else "#1a1d23"
                    gc       = "rgba(255,255,255,0.12)" if is_dark else "rgba(0,0,0,0.08)"

                    if baseline:
                        radar_dims = gse_dims + [gse_dims[0]]
                        fig_r = go.Figure()
                        fig_r.add_trace(go.Scatterpolar(
                            r=baseline + [baseline[0]], theta=radar_dims,
                            fill="toself", fillcolor="rgba(123,180,227,0.2)",
                            line=dict(color="#7BB4E3", width=2),
                            name="Baseline",
                        ))

                        # Neueste Session-Messung
                        for sn in range(p["session_count"], 1, -1):
                            latest = load_scores(p["user_id"], f"session_{sn}")
                            if latest:
                                fig_r.add_trace(go.Scatterpolar(
                                    r=latest + [latest[0]], theta=radar_dims,
                                    fill="toself", fillcolor="rgba(100,200,140,0.2)",
                                    line=dict(color="#64C88C", width=2, dash="dot"),
                                    name=f"Session {sn}",
                                ))
                                break

                        fig_r.update_layout(
                            polar=dict(
                                bgcolor="rgba(0,0,0,0)",
                                radialaxis=dict(visible=True, range=[0,4], tickvals=[1,2,3,4],
                                                tickfont=dict(size=9, color=tc),
                                                gridcolor=gc, linecolor=gc),
                                angularaxis=dict(tickfont=dict(size=9, color=tc),
                                                 gridcolor=gc, linecolor=gc),
                            ),
                            paper_bgcolor="rgba(0,0,0,0)",
                            showlegend=True,
                            legend=dict(font=dict(size=10, color=tc)),
                            margin=dict(l=40, r=40, t=20, b=20),
                            height=300,
                        )
                        st.plotly_chart(fig_r, use_container_width=True)

                        # Score-Tabelle
                        gse_total = sum(baseline)
                        st.caption(f"GSE Baseline: **{gse_total}/40**")

                # Observations für diesen Nutzer
                user_obs = [o for o in obs_all if o["name"] == p["name"]]
                if user_obs:
                    with st.expander("Alle Observations" if lang == "de" else "All observations"):
                        for o in user_obs:
                            cat   = o.get("category", "?")
                            date  = o.get("created_at", "")[:10]
                            score = o.get("sentiment_score")
                            score_str = f" · {score:+.2f}" if score is not None else ""
                            st.caption(f"`{cat}`{score_str} · {date}")
                            st.write(o.get("content", ""))

            # DSGVO Art. 17 — Admin-Löschung
            st.divider()
            _del_key = f"admin_del_{p['user_id']}"
            with st.expander(
                f"{'Nutzer löschen' if lang == 'de' else 'Delete user'} — {p['name']}",
            ):
                st.warning(
                    f"Löscht **alle** Daten von {p['name']} unwiderruflich."
                    if lang == "de" else
                    f"Permanently deletes **all** data for {p['name']}."
                )
                if st.button(
                    f"{'Jetzt löschen' if lang == 'de' else 'Delete now'}: {p['name']}",
                    type="primary",
                    key=_del_key,
                ):
                    _mem = MemoryStore(chroma_path=CHROMA_PATH, db_path=DB_PATH)
                    _mem.delete_user(p["user_id"])
                    store.delete_profile(p["user_id"])
                    st.success(
                        f"{p['name']} wurde gelöscht." if lang == "de"
                        else f"{p['name']} has been deleted."
                    )
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — GSE-AUSWERTUNG (Gruppenebene)
# ══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    st.subheader("GSE — Gruppenauswertung" if lang == "de" else "GSE — Group Analysis")

    # Alle Baseline-Scores laden
    all_baseline_item_scores = []
    for p in profiles:
        if not p.get("onboarding_complete"):
            continue
        with get_connection(DB_PATH) as conn:
            row = conn.execute(
                "SELECT responses FROM surveys WHERE user_id=? AND instrument='gse' AND timing='pre' ORDER BY created_at DESC LIMIT 1",
                (p["user_id"],),
            ).fetchone()
        if row:
            raw = json_decode(dict(row)["responses"])
            scores = [max(1, min(4, int(raw.get(str(i), raw.get(i, 3))))) for i in range(10)]
            all_baseline_item_scores.append({"name": p["name"], "scores": scores})

    if all_baseline_item_scores:
        gse_dims = TRANSLATIONS[lang]["auswertung_gse_dims"]
        is_dark  = (theme == "dark")
        tc       = "#e0e0e0" if is_dark else "#1a1d23"
        gc       = "rgba(255,255,255,0.12)" if is_dark else "rgba(0,0,0,0.08)"

        # Durchschnitt pro Item
        n = len(all_baseline_item_scores)
        avg_scores = [
            round(sum(e["scores"][i] for e in all_baseline_item_scores) / n, 2)
            for i in range(10)
        ]

        col_r, col_t = st.columns([3, 2])

        with col_r:
            st.caption(f"Durchschnitt über {n} Nutzer" if lang == "de" else f"Average across {n} users")
            radar_dims = gse_dims + [gse_dims[0]]
            fig_g = go.Figure()
            fig_g.add_trace(go.Scatterpolar(
                r=avg_scores + [avg_scores[0]], theta=radar_dims,
                fill="toself", fillcolor="rgba(123,180,227,0.25)",
                line=dict(color="#7BB4E3", width=2),
                name="Ø Gruppe" if lang == "de" else "Ø Group",
            ))
            fig_g.update_layout(
                polar=dict(
                    bgcolor="rgba(0,0,0,0)",
                    radialaxis=dict(visible=True, range=[0,4], tickvals=[1,2,3,4],
                                    tickfont=dict(size=10, color=tc),
                                    gridcolor=gc, linecolor=gc),
                    angularaxis=dict(tickfont=dict(size=11, color=tc),
                                     gridcolor=gc, linecolor=gc),
                ),
                paper_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                margin=dict(l=60, r=60, t=30, b=30),
                height=400,
            )
            st.plotly_chart(fig_g, use_container_width=True)

        with col_t:
            st.caption("Item-Scores (Ø)" if lang == "de" else "Item Scores (avg)")
            rows_data = []
            for i, (dim, avg) in enumerate(zip(gse_dims, avg_scores)):
                rows_data.append({"#": i+1, "Dimension": dim, "Ø": avg})
            import pandas as pd
            df = pd.DataFrame(rows_data)
            st.dataframe(df, hide_index=True, use_container_width=True)

        # Boxplot
        st.subheader("Score-Verteilung (GSE gesamt)" if lang == "de" else "Score Distribution (GSE total)")
        totals = [sum(e["scores"]) for e in all_baseline_item_scores]
        names  = [e["name"] for e in all_baseline_item_scores]
        fig_b = go.Figure()
        fig_b.add_trace(go.Box(
            y=totals, text=names,
            boxpoints="all", jitter=0.3, pointpos=-1.8,
            marker=dict(color="#7BB4E3", size=8),
            line=dict(color="#7BB4E3"),
            fillcolor="rgba(123,180,227,0.2)",
            name="GSE",
        ))
        fig_b.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(range=[10, 40], title="Score",
                       tickfont=dict(color=tc), gridcolor=gc),
            showlegend=False,
            margin=dict(l=0, r=0, t=10, b=0),
            height=280,
        )
        st.plotly_chart(fig_b, use_container_width=True)

    else:
        st.info("Noch keine abgeschlossenen Onboardings." if lang == "de" else "No completed onboardings yet.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — SESSIONS
# ══════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    st.subheader(f"{len(sessions)} Sessions" )

    if sessions:
        import pandas as pd
        df_s = pd.DataFrame([{
            "Nutzer"      if lang == "de" else "User":      s["name"],
            "Provider":                                      s["provider"],
            "Modell"      if lang == "de" else "Model":     s["model"],
            "Nachrichten" if lang == "de" else "Messages":  s["message_count"],
            "Tokens":                                        s["total_tokens"],
            "Latenz (ms)" if lang == "de" else "Latency":   round(s["avg_latency_ms"], 0),
            "Modus Start" if lang == "de" else "Mode start": s["mode_at_start"],
            "Modus Ende"  if lang == "de" else "Mode end":  s["mode_at_end"],
            "Datum":                                         s["started_at"][:10],
        } for s in sessions])
        st.dataframe(df_s, use_container_width=True, hide_index=True)

        # Durchschnittliche Latenz pro Provider
        st.subheader("Ø Latenz pro Provider (ms)" if lang == "de" else "Avg. Latency per Provider (ms)")
        prov_lat = {}
        prov_cnt = {}
        for s in sessions:
            pv = s["provider"]
            prov_lat[pv] = prov_lat.get(pv, 0) + s["avg_latency_ms"]
            prov_cnt[pv] = prov_cnt.get(pv, 0) + 1
        avg_lat = {pv: round(prov_lat[pv] / prov_cnt[pv], 0) for pv in prov_lat}

        fig_lat = px.bar(
            x=list(avg_lat.keys()), y=list(avg_lat.values()),
            color=list(avg_lat.keys()),
            color_discrete_sequence=["#7BB4E3", "#64C88C", "#F0A868"],
            labels={"x": "Provider", "y": "ms"},
        )
        fig_lat.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            margin=dict(l=0, r=0, t=10, b=0),
            height=220,
            xaxis=dict(tickfont=dict(color="#e0e0e0" if theme == "dark" else "#1a1d23")),
            yaxis=dict(tickfont=dict(color="#e0e0e0" if theme == "dark" else "#1a1d23"),
                       gridcolor="rgba(255,255,255,0.1)" if theme == "dark" else "rgba(0,0,0,0.08)"),
        )
        st.plotly_chart(fig_lat, use_container_width=True)
    else:
        st.caption("Noch keine Sessions." if lang == "de" else "No sessions yet.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — OBSERVATIONS
# ══════════════════════════════════════════════════════════════════════════════
with tabs[4]:
    st.subheader(f"{len(obs_all)} Observations")

    cat_filter = st.multiselect(
        "Kategorien filtern" if lang == "de" else "Filter categories",
        options=["mood", "strength", "blind_spot", "learning_style", "general"],
        default=["mood", "strength", "blind_spot", "learning_style", "general"],
    )

    filtered = [o for o in obs_all if o.get("category") in cat_filter]

    if filtered:
        import pandas as pd
        df_o = pd.DataFrame([{
            "Nutzer"     if lang == "de" else "User":      o["name"],
            "Kategorie"  if lang == "de" else "Category":  o["category"],
            "Inhalt"     if lang == "de" else "Content":   o["content"],
            "Sentiment":                                    round(o["sentiment_score"], 2) if o.get("sentiment_score") is not None else "—",
            "Modus"      if lang == "de" else "Mode":      o.get("mode", "—"),
            "Datum":                                        o["created_at"][:10],
        } for o in filtered])
        st.dataframe(df_o, use_container_width=True, hide_index=True)
    else:
        st.caption("Keine Observations in dieser Auswahl." if lang == "de" else "No observations in this selection.")
