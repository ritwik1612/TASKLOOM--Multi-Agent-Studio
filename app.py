from __future__ import annotations

import asyncio
import base64
import json
from datetime import datetime, timedelta
from html import escape
from pathlib import Path

import streamlit as st

from artifacts import build_artifact_pdf
from config import refresh_credentials, settings
from credential_store import delete_api_key, save_api_key, secure_storage_available
from orchestrator import Orchestrator
from paths import resource_path
from providers import GeminiFailoverProvider


st.set_page_config(
    page_title="Taskloom · Multi-Agent Studio",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def local_font_uri(filename: str | Path, mime_type: str) -> str:
    """Embed the project's licensed display font so the design is self-contained."""
    font_path = resource_path("FONTS") / filename
    return f"data:{mime_type};base64," + base64.b64encode(font_path.read_bytes()).decode("ascii")


def humanize_task_id(task_id: str) -> str:
    """Turn model-oriented identifiers such as task_1 or T1 into UI copy."""
    compact = task_id.strip().replace("_", " ")
    lowered = compact.lower()
    if lowered.startswith("task"):
        suffix = compact[4:].strip()
        return f"Task {suffix}" if suffix else "Task"
    if len(compact) > 1 and compact[0].lower() == "t" and compact[1:].isdigit():
        return f"Task {compact[1:]}"
    return compact.title()


def preserve_theme_query() -> None:
    """Keep the selected visual mode when a navigation action clears panel routes."""
    st.query_params.clear()
    st.query_params["theme"] = "night" if st.session_state.get("night_mode", False) else "light"


olivera_font_uri = local_font_uri("Olivera_Demo.ttf", "font/ttf")
product_sans_font_uri = local_font_uri(Path("product sans") / "product-sans-regular.ttf", "font/ttf")
night_sky_path = resource_path("assets", "taskloom-night-sky.png")
night_sky_uri = "data:image/png;base64," + base64.b64encode(night_sky_path.read_bytes()).decode("ascii")
night_ribbon_logo_path = resource_path("assets", "taskloom-ribbon-logo-night.png")
night_ribbon_logo_src = "data:image/png;base64," + base64.b64encode(night_ribbon_logo_path.read_bytes()).decode("ascii")
taskloom_logo_svg = (
    '<svg class="taskloom-symbol" viewBox="0 0 48 48" fill="none" aria-hidden="true">'
    '<path class="loom-ribbon" d="M12 8C12 17 18 21 25 26C32 31 40 35 40 44"/>'
    '<path class="loom-ribbon" d="M36 8C36 17 30 21 23 26C16 31 8 35 8 44"/>'
    '<path class="loom-diamond" d="M24 21L29 26L24 31L19 26Z"/></svg>'
)


def inject_theme() -> None:
    night_css = (
        """
        /* Night-sky theme: the same Taskloom system, with a calmer nocturnal surface. */
        :root {
          --maf-ink:#071126;
          --maf-panel:#0c1933;
          --maf-panel-soft:#122348;
          --maf-stroke:rgba(216,228,255,.25);
          --maf-stroke-hot:rgba(245,241,232,.72);
          --maf-text:#f5f1e8;
          --maf-muted:rgba(245,241,232,.70);
          --maf-gold:#91a8ff;
          --maf-gold-bright:#cbd5ff;
        }
        .stApp {
          background:
            linear-gradient(rgba(4,11,29,.46),rgba(4,11,29,.64)),
            url('__TASKLOOM_NIGHT_SKY__') center / cover fixed!important;
          color:#f5f1e8!important;
        }
        .stApp::before {
          display:block!important;z-index:0;opacity:1!important;
          background:radial-gradient(ellipse at center,transparent 0 28%,rgba(4,11,29,.18) 72%,rgba(4,11,29,.42) 100%);
        }
        .taskloom-splash {
          background:
            radial-gradient(circle at 50% 42%,rgba(82,105,220,.18),transparent 24rem),
            linear-gradient(rgba(4,11,29,.33),rgba(4,11,29,.62)),
            url('__TASKLOOM_NIGHT_SKY__') center / cover!important;
        }
        .taskloom-splash::before {
          display:block!important;border-color:rgba(203,213,255,.32)!important;
          box-shadow:0 0 46px rgba(91,114,240,.18)!important;
        }
        .taskloom-splash-network { display:none!important; }
        .taskloom-splash .taskloom-splash-vector,.taskloom-splash .taskloom-splash-light-logo { display:none!important; }
        .taskloom-splash .taskloom-splash-dark-logo {
          display:block!important;position:relative;z-index:1;width:min(25vw,190px)!important;height:min(29vw,220px)!important;
          object-fit:contain;filter:drop-shadow(0 14px 26px rgba(0,0,0,.22));animation:taskloom-ribbon-arrive .95s .08s var(--maf-ease) both!important;
        }
        .taskloom-splash strong { color:#f5f1e8!important;text-shadow:0 2px 18px rgba(0,0,0,.42); }
        .block-container { position:relative;z-index:1; }
        .maf-hero,.maf-chat-intro { background:transparent!important; }
        .maf-hero h1,.maf-hero h1 a,.maf-hero h1 span,.maf-chat-intro h1,
        .maf-panel-hero h1,.maf-workspace-head h2,.maf-decision-head h3,.maf-revision-head h3,
        .maf-info-card dd,.maf-agent-card b,.maf-map-detail b,.maf-architecture-detail b,
        .maf-architecture-flow b { color:#f5f1e8!important; }
        .maf-hero h1 .maf-hero-accent,.maf-kicker,.maf-section-label,.maf-eyebrow,
        .maf-info-card dt,.maf-map-detail i,.maf-architecture-detail i,.maf-architecture-flow i,
        .maf-trace strong { color:#a7b8ff!important; }
        .maf-hero p,.maf-chat-intro p,.maf-panel-hero p,.maf-decision-head p,.maf-revision-head p,
        .maf-info-card .maf-note,.maf-map-detail p,.maf-architecture-detail p,.maf-architecture-flow span,
        .maf-task-objective,.maf-trace small,.maf-footer,[data-testid="stCaptionContainer"] { color:rgba(245,241,232,.7)!important; }
        .maf-network path,.maf-chat-network path { stroke:#91a8ff!important; }
        .maf-network circle,.maf-chat-network circle { fill:#cbd5ff!important; }
        .maf-live { background:#0c1933!important;border-color:rgba(203,213,255,.55)!important;color:#f5f1e8!important; }
        .maf-live,.maf-live * { color:#f5f1e8!important; }
        .maf-mark img { filter:none!important; }
        [data-testid="stTextArea"] [data-baseweb="textarea"] {
          padding:0!important;background:transparent!important;border:0!important;border-radius:0!important;
          clip-path:none!important;box-shadow:none!important;
        }
        [data-testid="stTextArea"] textarea {
          background:linear-gradient(135deg,#0c1933,#0a1730)!important;color:#f5f1e8!important;
          caret-color:#f5f1e8!important;border:1px solid rgba(203,213,255,.42)!important;
          border-radius:8px!important;clip-path:none!important;box-shadow:inset 0 1px 0 rgba(245,241,232,.04)!important;
        }
        [data-testid="stTextArea"] textarea:focus {
          border-color:#91a8ff!important;box-shadow:0 0 0 3px rgba(145,168,255,.13),inset 0 1px 0 rgba(245,241,232,.04)!important;
        }
        [data-testid="stTextArea"] textarea::placeholder { color:rgba(245,241,232,.48)!important; }
        .stButton > button[kind="primary"] { background:#3158ea!important;color:#f5f1e8!important; }
        .stButton > button[kind="primary"] p { color:#f5f1e8!important; }
        .stButton > button[kind="primary"]:hover { background:#4669ee!important;box-shadow:0 8px 18px rgba(0,0,0,.34)!important; }
        .stButton > button:not([kind="primary"]),.stDownloadButton > button {
          background:#0c1933!important;border-color:rgba(203,213,255,.55)!important;color:#f5f1e8!important;
        }
        .stButton > button:not([kind="primary"]) p,.stDownloadButton > button p { color:#f5f1e8!important; }
        .stButton > button:not([kind="primary"]):hover,.stDownloadButton > button:hover { background:#122348!important;border-color:#cbd5ff!important;color:#f5f1e8!important;box-shadow:0 8px 18px rgba(0,0,0,.28)!important; }
        [data-testid="stMetric"],.maf-info-card dl div,.maf-agent-card,.maf-map-detail,.maf-architecture-detail,
        .maf-architecture-flow > div,.maf-connect-step,.maf-connection-status > div,[data-testid="stStatusWidget"],[data-testid="stExpander"] { background:#0c1933!important;border-color:rgba(203,213,255,.30)!important; }
        .maf-connect-step b,.maf-connection-status b,.maf-security-strip strong { color:#f5f1e8!important; }
        .maf-connect-step i,.maf-connection-status i { color:#b9c7ff!important; }
        .maf-connect-step p,.maf-connection-status p,.maf-key-help,.maf-security-strip { color:rgba(245,241,232,.78)!important; }
        .maf-security-strip { background:rgba(145,168,255,.09)!important;border-left-color:#91a8ff!important; }
        [data-testid="stMetricLabel"],[data-testid="stMetricValue"],.maf-task-role { color:#f5f1e8!important; }
        .maf-preview { background:#0c1933!important;border-color:rgba(203,213,255,.30)!important;box-shadow:0 20px 55px rgba(0,0,0,.28)!important;color:#f5f1e8!important; }
        .maf-preview,.maf-preview p,.maf-preview li,.maf-preview h1,.maf-preview h2,.maf-preview h3 { color:#f5f1e8!important; }
        .st-key-output_content {
          margin-top:.8rem;padding:clamp(1.15rem,2.4vw,2.1rem)!important;background:rgba(10,23,48,.94)!important;
          border:1px solid rgba(203,213,255,.28)!important;border-radius:10px!important;
          box-shadow:0 18px 42px rgba(0,0,0,.24),inset 0 1px 0 rgba(245,241,232,.035)!important;
        }
        .st-key-output_content,.st-key-output_content p,.st-key-output_content li,.st-key-output_content h1,
        .st-key-output_content h2,.st-key-output_content h3,.st-key-output_content h4,.st-key-output_content blockquote { color:#f5f1e8!important; }
        .st-key-output_content pre,.st-key-output_content code,.st-key-output_content [data-testid="stCode"] {
          background:#0a1730!important;color:#f5f1e8!important;border-color:rgba(203,213,255,.22)!important;
        }
        .st-key-output_content button { background:#122348!important;border-color:rgba(203,213,255,.34)!important;color:#f5f1e8!important; }
        .st-key-output_content button svg { fill:#f5f1e8!important;color:#f5f1e8!important; }
        .maf-role { background:#3158ea!important;color:#f5f1e8!important; }
        [data-baseweb="tab-list"] { border-color:rgba(203,213,255,.30)!important; }
        [data-baseweb="tab"] { color:rgba(245,241,232,.70)!important; }
        [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] { color:#f5f1e8!important;border-bottom-color:#91a8ff!important; }
        [data-testid="stTabs"] [data-baseweb="tab-highlight"],[data-testid="stTabs"] [data-baseweb="tab-border"] { background-color:#91a8ff!important; }
        .maf-task-row { border-color:rgba(203,213,255,.22)!important; }
        .maf-task-id,.maf-message-flow div,.maf-agent-core,.maf-agent-output { background:#3158ea!important;color:#f5f1e8!important;border-color:#3158ea!important; }
        [data-testid="stExpander"] > details > summary { background:#3158ea!important;color:#f5f1e8!important; }
        [data-testid="stPopoverBody"] { background:#0c1933!important;border-color:rgba(203,213,255,.40)!important;box-shadow:0 16px 40px rgba(0,0,0,.36)!important; }
        [data-testid="stPopoverBody"] .stButton > button,[data-testid="stPopoverBody"] [data-testid="stDownloadButton"] > button { color:#f5f1e8!important;border-top-color:rgba(203,213,255,.22)!important; }
        [data-testid="stPopoverBody"] .stButton > button:hover,[data-testid="stPopoverBody"] [data-testid="stDownloadButton"] > button:hover { background:#122348!important; }
        [data-testid="stPopoverBody"] [data-testid="stRadio"] label { color:#f5f1e8!important; }
        div[data-testid="stElementContainer"]:has(.maf-home-native-anchor) + div[data-testid="stElementContainer"] .stButton > button::after { color:#f5f1e8!important; }
        div[data-testid="stElementContainer"]:has(.maf-home-native-anchor) + div[data-testid="stElementContainer"] .stButton > button::before { color:rgba(245,241,232,.68)!important; }
        div[data-testid="stElementContainer"]:has(.maf-gemini-native-anchor) + div[data-testid="stElementContainer"] .stButton > button { background:#0c1933!important;border-color:rgba(203,213,255,.55)!important; }
        div[data-testid="stElementContainer"]:has(.maf-gemini-native-anchor) + div[data-testid="stElementContainer"] .stButton > button::after { color:#f5f1e8!important; }
        .st-key-agent_menu_slot [data-testid="stPopoverButton"] { color:#cbd5ff!important; }
        .st-key-agent_menu_slot [data-testid="stPopoverButton"]:hover { color:#f5f1e8!important; }
        [data-testid="stAlert"] { background:#0c1933!important;border-color:rgba(203,213,255,.32)!important;color:#f5f1e8!important; }
        [data-testid="stAlert"] * { color:#f5f1e8!important; }
        /* Final contrast pass: these selectors deliberately outrank the daylight typography rules. */
        .maf-hero h1 .maf-hero-primary { color:#f5f1e8!important;text-shadow:0 4px 24px rgba(0,0,0,.30); }
        .maf-hero h1 .maf-hero-accent { color:#b9c7ff!important;text-shadow:0 4px 24px rgba(0,0,0,.26); }
        .maf-hero p,.maf-chat-intro p { color:rgba(245,241,232,.78)!important;text-shadow:0 2px 14px rgba(0,0,0,.32); }
        .stApp [data-testid="stMarkdownContainer"] h1,.stApp [data-testid="stMarkdownContainer"] h2,
        .stApp [data-testid="stMarkdownContainer"] h3,.stApp [data-testid="stMarkdownContainer"] h4,
        .stApp [data-testid="stMarkdownContainer"] h5,.stApp [data-testid="stMarkdownContainer"] h6 { color:#f5f1e8!important; }
        .stApp [data-testid="stMarkdownContainer"] p,.stApp [data-testid="stMarkdownContainer"] li,
        .stApp [data-testid="stMarkdownContainer"] blockquote,.stApp [data-testid="stMarkdownContainer"] small { color:rgba(245,241,232,.78)!important; }
        .maf-kicker,.maf-section-label,.maf-eyebrow,.maf-info-card dt,.maf-map-detail i,
        .maf-architecture-detail i,.maf-architecture-flow i,.maf-trace strong { color:#b9c7ff!important; }
        div[data-testid="stElementContainer"]:has(.maf-back-anchor) + div[data-testid="stElementContainer"] .stButton > button {
          width:auto!important;min-height:auto!important;overflow:visible!important;clip-path:none!important;
          padding:.35rem 0!important;white-space:nowrap!important;
        }
        """.replace("__TASKLOOM_NIGHT_SKY__", night_sky_uri)
        if st.session_state.get("night_mode", False)
        else ""
    )
    st.markdown(
        f"""
        <style>
        @font-face {{ font-family:'Taskloom Olivera'; src:url('{olivera_font_uri}') format('truetype'); font-display:swap; }}
        @font-face {{ font-family:'Taskloom Product Sans'; src:url('{product_sans_font_uri}') format('truetype'); font-display:swap; }}
        @import url('https://fonts.googleapis.com/css2?family=Courier+Prime:ital,wght@0,400;0,700;1,400&family=Roboto:wght@400;500&display=swap');
        :root {{
          --maf-ink: #1026e8;
          --maf-panel: #ffffff;
          --maf-panel-soft: #e9ebff;
          --maf-stroke: rgba(255,255,255,.32);
          --maf-stroke-hot: rgba(255,255,255,.8);
          --maf-text: #ffffff;
          --maf-muted: rgba(255,255,255,.72);
          --maf-gold: #ffffff;
          --maf-gold-bright: #ffffff;
          --maf-coral: #ffffff;
          --maf-ease: cubic-bezier(.22,1,.36,1);
        }}
        .stApp {{
          background:var(--maf-ink);
          color: var(--maf-text);
          font-family:'Courier Prime','Courier New',monospace;
        }}
        .stApp::before {{
          content:""; position:fixed; inset:0; pointer-events:none; opacity:.15;
          display:none;
        }}
        [data-testid="stHeader"] {{ background:transparent!important;height:0!important;pointer-events:none!important;z-index:0!important; }}
        [data-testid="stToolbar"], [data-testid="stDecoration"] {{ display:none!important; }}
        .block-container {{ max-width: 1180px; padding-top: 1.15rem; padding-bottom: 5rem; }}
        h1, h2, h3 {{ letter-spacing: -.035em; }}
        p {{ color: var(--maf-muted); }}
        @keyframes maf-rise {{ from {{ opacity:0; transform:translateY(18px); }} to {{ opacity:1; transform:none; }} }}
        @keyframes maf-pulse {{ 0%,100% {{ opacity:.6; transform:scale(.92); }} 50% {{ opacity:1; transform:scale(1); }} }}
        @keyframes maf-drift {{ from {{ transform:translate3d(0,0,0) rotate(0); }} to {{ transform:translate3d(-18px,12px,0) rotate(4deg); }} }}
        @keyframes taskloom-weave {{
          0% {{ stroke-dashoffset:1;opacity:0; }}
          18% {{ opacity:1; }}
          100% {{ stroke-dashoffset:0;opacity:1; }}
        }}
        @keyframes taskloom-settle {{
          0% {{ opacity:0;transform:scale(.72) rotate(-7deg); }}
          72% {{ opacity:1;transform:scale(1.06) rotate(1deg); }}
          100% {{ opacity:1;transform:scale(1) rotate(0); }}
        }}
        @keyframes taskloom-splash-logo {{
          0% {{ opacity:0;transform:scale(.88);clip-path:inset(100% 0 0);filter:hue-rotate(225deg) saturate(.8) brightness(1.25) drop-shadow(0 0 0 transparent); }}
          22% {{ opacity:1; }}
          72% {{ clip-path:inset(0 0 0);transform:scale(1.035);filter:hue-rotate(225deg) saturate(.8) brightness(1.25) drop-shadow(0 22px 48px rgba(139,92,246,.34)); }}
          100% {{ opacity:1;transform:scale(1);clip-path:inset(0);filter:hue-rotate(225deg) saturate(.8) brightness(1.2) drop-shadow(0 16px 38px rgba(139,92,246,.25)); }}
        }}
        @keyframes taskloom-ring {{
          0% {{ opacity:0;transform:scale(.55); }}
          45% {{ opacity:.5; }}
          100% {{ opacity:0;transform:scale(1.35); }}
        }}
        @keyframes taskloom-name {{ from {{ opacity:0;transform:translateY(10px);letter-spacing:.5em; }} to {{ opacity:1;transform:none;letter-spacing:.26em; }} }}
        @keyframes maf-orbit {{ from {{ transform:translate3d(0,0,0) rotate(-5deg); }} to {{ transform:translate3d(-16px,-10px,0) rotate(6deg); }} }}
        @keyframes taskloom-splash-exit {{
          0%,72% {{ opacity:1;visibility:visible; }}
          100% {{ opacity:0;visibility:hidden; }}
        }}

        .maf-nav {{
          display:flex; align-items:center; justify-content:space-between;
          min-height:52px; margin-bottom:1.25rem; animation:maf-rise .6s var(--maf-ease) both;
        }}
        .maf-brand {{ display:flex; align-items:center; gap:.75rem; color:var(--maf-text); font-weight:700; }}
        .maf-mark {{
          width:42px; height:42px; display:grid; place-items:center;
          filter:none;overflow:visible;
        }}
        .maf-mark img {{ width:40px;height:40px;object-fit:contain;mix-blend-mode:screen; }}
        .taskloom-splash {{
          position:fixed;inset:0;z-index:999999;display:flex;flex-direction:column;align-items:center;justify-content:center;
          background:radial-gradient(circle at center,rgba(65,44,135,.28),transparent 25rem),#050506;
          animation:taskloom-splash-exit 1.55s var(--maf-ease) forwards;pointer-events:none;
        }}
        .taskloom-splash::before {{ content:"";position:absolute;width:min(45vw,410px);aspect-ratio:1;border:1px solid rgba(181,156,255,.35);border-radius:50%;animation:taskloom-ring 1.15s var(--maf-ease) both; }}
        .taskloom-splash img {{
          width:min(34vw,300px);height:min(34vw,300px);object-fit:contain;
          mix-blend-mode:screen;animation:taskloom-splash-logo 1.05s var(--maf-ease) both;
        }}
        .taskloom-splash strong {{ color:#f5f3ff;font-size:.8rem;text-transform:uppercase;margin-top:1.15rem;font-weight:650;animation:taskloom-name .55s .5s var(--maf-ease) both; }}
        .taskloom-logo {{ width:39px;height:39px;overflow:visible;transform-origin:center;animation:taskloom-settle 1s var(--maf-ease) both; }}
        .taskloom-logo path {{
          fill:none;stroke-linecap:round;stroke-linejoin:round;stroke-width:5.2;
          stroke-dasharray:1;stroke-dashoffset:1;animation:taskloom-weave .82s var(--maf-ease) forwards;
        }}
        .taskloom-logo .loom-a {{ stroke:url(#loom-hot);animation-delay:.04s; }}
        .taskloom-logo .loom-b {{ stroke:url(#loom-warm);animation-delay:.13s; }}
        .taskloom-logo .loom-c {{ stroke:#ffb35f;animation-delay:.21s; }}
        .taskloom-logo .loom-d {{ stroke:#ff7a1a;animation-delay:.29s; }}
        .maf-wordmark small {{ display:block; color:var(--maf-muted); font-size:.63rem; letter-spacing:.16em; font-weight:600; }}
        .maf-live {{
          display:inline-flex; align-items:center; gap:.5rem; padding:.36rem .7rem;
          border:1px solid var(--maf-stroke); border-radius:999px; color:#4e4d49; font-size:.72rem;
          background:rgba(255,255,255,.72); backdrop-filter:blur(12px);
        }}
        .maf-live i {{ width:6px;height:6px;border-radius:50%;background:#171716;box-shadow:none;animation:none; }}

        .maf-hero {{
          min-height:500px; position:relative; overflow:hidden;
          border:0;border-radius:0;background:transparent;box-shadow:none;
          display:flex;align-items:center;justify-content:center;padding:clamp(2.5rem,6vw,5.5rem);
          animation:maf-rise .75s .08s var(--maf-ease) both;
        }}
        .maf-hero::after {{
          display:none;
        }}
        .maf-hero::before {{
          content:"";position:absolute;left:-8%;right:-8%;bottom:-15%;height:56%;opacity:.74;
          background-image:radial-gradient(circle,rgba(20,20,20,.78) 0 1px,transparent 1.35px);
          background-size:8px 8px;mask-image:linear-gradient(to top,black 10%,transparent 86%);
          transform:perspective(650px) rotateX(63deg);
        }}
        .maf-hero-copy {{ max-width:690px;width:100%;position:relative;z-index:2;text-align:center; }}
        .maf-kicker {{ color:var(--maf-gold); font-size:.72rem; letter-spacing:.18em; text-transform:uppercase; font-weight:750; }}
        .maf-hero h1,.maf-hero h1 a {{ color:#171716!important;font-size:clamp(3rem,5.6vw,5.7rem);line-height:.93;margin:1rem auto 1.35rem;max-width:730px; }}
        .maf-hero h1 span {{ color:#171716; }}
        .maf-hero h1 em {{ font-family:'DM Serif Display',Georgia,serif;font-weight:400;letter-spacing:-.045em; }}
        .maf-hero p {{ max-width:510px;font-size:.97rem;line-height:1.7;color:#74736f;margin:0 auto; }}
        .maf-hero-orb {{
          display:none;
        }}
        .maf-home-actions {{ max-width:430px;margin:-1.4rem auto 2.5rem;position:relative;z-index:4; }}
        .maf-home-actions + div {{ position:relative;z-index:5; }}
        .maf-proof {{ display:flex;align-items:center;justify-content:center;gap:2rem;flex-wrap:wrap;margin:1.8rem auto 4rem;color:#777570;font-size:.68rem;letter-spacing:.1em;text-transform:uppercase; }}
        .maf-proof span {{ display:flex;align-items:center;gap:.5rem; }}
        .maf-proof i {{ width:4px;height:4px;background:#9c7ff3;border-radius:50%;box-shadow:0 0 9px #8b5cf6; }}
        .maf-chat-intro {{ padding:1.5rem 0 .25rem;text-align:center; }}
        .maf-chat-intro h1 {{ color:#171716;font-size:clamp(2rem,4vw,3.35rem);margin:.4rem 0 .6rem; }}
        .maf-chat-intro p {{ margin:0 auto;max-width:530px; }}
        .maf-section-label {{ margin-top:1.65rem; color:var(--maf-gold); font-size:.68rem; letter-spacing:.18em; text-transform:uppercase; font-weight:750;text-align:center; }}
        .maf-section-title {{ margin:.35rem 0 .2rem; color:var(--maf-text); font-size:1.55rem; font-weight:700;text-align:center; }}
        .maf-section-copy {{ color:var(--maf-muted); margin-bottom:1rem;text-align:center; }}

        [data-testid="stTextArea"] textarea {{
          min-height:142px; border-radius:16px; border:1px solid var(--maf-stroke);
          background:#fff; color:var(--maf-text); padding:1.2rem 1.25rem;
          font-size:1rem; line-height:1.6; box-shadow:inset 0 1px rgba(255,255,255,.025);
          transition:border-color .2s ease,box-shadow .2s ease,background .2s ease;
        }}
        [data-testid="stTextArea"] textarea:focus {{
          border-color:rgba(17,17,17,.65); box-shadow:0 0 0 4px rgba(17,17,17,.06);background:#fff;
        }}
        [data-testid="stTextArea"] label {{ display:none; }}
        .stButton > button[kind="primary"] {{
          min-height:2.85rem;border:0; border-radius:999px; color:#fff; font-weight:700;
          background:#171716;box-shadow:none;transition:transform .18s var(--maf-ease),background .18s ease;
        }}
        .stButton > button[kind="primary"] p {{ color:#fff!important; }}
        .stButton > button[kind="primary"]:hover {{ color:#fff; background:#373634;transform:translateY(-1px); }}
        .stButton > button:not([kind="primary"]), .stDownloadButton > button {{
          min-height:2.85rem;border:1px solid var(--maf-stroke); border-radius:999px; color:#383733;
          background:#fff;transition:border-color .18s ease,color .18s ease,transform .18s ease;
        }}
        .stButton > button:not([kind="primary"]):hover, .stDownloadButton > button:hover {{
          border-color:#171716; color:#171716;transform:translateY(-1px);
        }}

        .maf-workspace-head {{
          display:flex; justify-content:space-between; align-items:flex-end; gap:1rem;
          padding:1.4rem 0 .9rem; border-bottom:1px solid var(--maf-stroke); margin-top:1.8rem;animation:maf-rise .5s var(--maf-ease) both;
        }}
        .maf-workspace-head h2 {{ margin:0;color:var(--maf-text); }}
        .maf-eyebrow {{ color:var(--maf-gold); font-size:.69rem; letter-spacing:.14em; text-transform:uppercase; }}
        .maf-role-row {{ display:flex;gap:.45rem;flex-wrap:wrap;margin:.9rem 0 1.2rem; }}
        .maf-role {{
          border:1px solid var(--maf-stroke); border-radius:999px; padding:.35rem .66rem;
          background:#151515; color:#c7c7c7; font-size:.74rem;
        }}
        .maf-preview {{
          padding:clamp(1.4rem,3vw,2.6rem); background:linear-gradient(145deg,#121212,#0e0e0e);
          border:1px solid var(--maf-stroke); border-radius:18px; line-height:1.76;
          box-shadow:0 22px 60px rgba(0,0,0,.18),inset 0 1px rgba(255,255,255,.025);animation:maf-rise .5s var(--maf-ease) both;
        }}
        .maf-preview h1,.maf-preview h2,.maf-preview h3 {{ color:#fff; }}
        [data-testid="stMetric"] {{
          background:#0f0f0f; border:1px solid var(--maf-stroke); padding:.9rem 1rem;border-radius:13px;
        }}
        [data-testid="stMetricValue"] {{ color:var(--maf-text); font-size:1.4rem; }}
        [data-testid="stMetricLabel"] {{ color:var(--maf-muted); }}
        [data-baseweb="tab-list"] {{ gap:1.35rem; border-bottom:1px solid var(--maf-stroke); }}
        [data-baseweb="tab"] {{ padding:.8rem .1rem; }}
        [aria-selected="true"] {{ color:var(--maf-gold-bright) !important; }}
        [data-testid="stExpander"] {{ border:1px solid var(--maf-stroke); border-radius:12px; background:rgba(16,23,33,.45); }}
        .maf-task-row {{
          display:grid; grid-template-columns:34px minmax(150px,.65fr) 1.35fr; gap:1rem;
          align-items:start; padding:.85rem 0; border-bottom:1px solid rgba(240,223,187,.07);
        }}
        .maf-task-id {{ color:var(--maf-gold); font-family:'DM Sans',Arial,sans-serif; font-size:.78rem; }}
        .maf-task-role {{ color:var(--maf-text); font-weight:650; }}
        .maf-task-objective {{ color:var(--maf-muted); font-size:.87rem; }}
        .maf-trace {{
          border-left:1px solid rgba(231,184,108,.25); padding:0 0 .9rem 1rem; margin-left:.35rem;
        }}
        .maf-trace strong {{ color:#e5d8c3; }}
        .maf-trace small {{ color:var(--maf-muted); }}
        .maf-footer {{ text-align:center;color:#5e5c59;font-size:.7rem;letter-spacing:.06em;margin-top:3.5rem; }}
        [data-testid="stAlert"] {{ border-radius:13px;border-color:var(--maf-stroke); }}
        [data-testid="stStatusWidget"] {{ border-color:var(--maf-stroke);border-radius:14px;background:#101010; }}
        div[data-testid="stPopover"] > button {{ width:100%; }}
        @media (prefers-reduced-motion:reduce) {{
          *,*::before,*::after {{ animation:none!important;transition:none!important; }}
          .taskloom-logo path {{ stroke-dashoffset:0!important;opacity:1!important; }}
          .taskloom-splash {{ display:none!important; }}
        }}
        @media(max-width:700px) {{
          .maf-hero {{ min-height:620px;align-items:center;padding:2rem 1rem 3.5rem; }}
          .maf-hero h1 {{ font-size:2.55rem; }}
          .maf-hero-copy {{ width:100%;text-align:center; }}
          .maf-task-row {{ grid-template-columns:30px 1fr; }}
          .maf-task-objective {{ grid-column:2; }}
          .maf-live {{ font-size:0;width:34px;height:34px;justify-content:center;padding:0; }}
        }}

        /* Taskloom's visual system: cobalt blue and white, with no secondary accents. */
        @keyframes taskloom-line-draw {{ to {{ stroke-dashoffset:0; }} }}
        @keyframes taskloom-splash-symbol {{
          0% {{ opacity:0; transform:translateY(16px) scale(.82); }}
          55% {{ opacity:1; transform:translateY(0) scale(1.03); }}
          100% {{ opacity:1; transform:translateY(0) scale(1); }}
        }}
        @keyframes taskloom-splash-word {{ from {{ opacity:0; letter-spacing:.72em; }} to {{ opacity:1; letter-spacing:.3em; }} }}
        @keyframes taskloom-splash-exit {{ 0%,78% {{ opacity:1;visibility:visible; }} 100% {{ opacity:0;visibility:hidden; }} }}
        @keyframes taskloom-network-float {{
          0%,100% {{ transform:translate3d(0,0,0) scale(1); }}
          50% {{ transform:translate3d(0,-7px,0) scale(1.012); }}
        }}
        .block-container {{ max-width:1280px; padding-top:2rem; }}
        .maf-nav {{ color:#fff; margin-bottom:0; min-height:60px; }}
        .maf-brand, .maf-wordmark {{ color:#fff!important; font-family:'DM Sans',Arial,sans-serif; }}
        .maf-wordmark {{ font-size:.95rem; letter-spacing:-.04em; }}
        .maf-wordmark small {{ color:rgba(255,255,255,.62); font-size:.56rem; letter-spacing:.18em; margin-top:.16rem; }}
        .maf-mark {{ width:39px;height:39px; }}
        .maf-mark img {{ width:38px;height:38px;mix-blend-mode:normal;filter:grayscale(1) brightness(0) invert(1); }}
        .maf-live {{ color:#fff;background:transparent;border-color:rgba(255,255,255,.35);font-family:'DM Sans',Arial,sans-serif;font-size:.62rem; }}
        .maf-live i {{ background:#fff;box-shadow:0 0 0 3px rgba(255,255,255,.16); }}

        .taskloom-splash {{ background:#1026e8; animation:taskloom-splash-exit 1.7s var(--maf-ease) forwards; overflow:hidden; }}
        .taskloom-splash::before {{ display:none; }}
        .taskloom-splash-network {{ position:absolute; width:min(1100px,120vw); height:auto; opacity:.78; }}
        .taskloom-splash-network path {{ fill:none;stroke:#fff;stroke-width:1.15;stroke-linecap:round;stroke-dasharray:1 1;stroke-dashoffset:1;animation:taskloom-line-draw .8s .08s var(--maf-ease) forwards; }}
        .taskloom-splash-network path:nth-child(2) {{ animation-delay:.15s; }}
        .taskloom-splash-network path:nth-child(3) {{ animation-delay:.22s; }}
        .taskloom-splash-network path:nth-child(4) {{ animation-delay:.29s; }}
        .taskloom-splash-network path:nth-child(5) {{ animation-delay:.36s; }}
        .taskloom-splash-network circle {{ fill:#fff;opacity:0;animation:maf-rise .35s .65s var(--maf-ease) forwards; }}
        .taskloom-splash img {{ position:relative;z-index:1;width:min(17vw,132px);height:min(17vw,132px);mix-blend-mode:normal;filter:grayscale(1) brightness(0) invert(1);animation:taskloom-splash-symbol .8s .25s var(--maf-ease) both; }}
        .taskloom-splash strong {{ position:relative;z-index:1;color:#fff;font-family:'DM Sans',Arial,sans-serif;font-size:.68rem;font-weight:500;margin-top:1rem;animation:taskloom-splash-word .48s .55s var(--maf-ease) both; }}

        .maf-hero {{ min-height:480px;display:flex;align-items:center;justify-content:flex-start;padding:clamp(3rem,6vw,5.5rem) clamp(1rem,7vw,6rem);background:#1026e8; }}
        .maf-hero::before,.maf-hero::after {{ display:none; }}
        .maf-hero-copy {{ max-width:650px;width:54%;text-align:left; }}
        .maf-network {{ position:absolute;z-index:1;right:-7%;top:0;width:63%;height:100%;opacity:.9; }}
        .maf-network {{ animation:taskloom-network-float 10s ease-in-out infinite;transform-origin:62% 50%; }}
        .maf-network path {{ fill:none;stroke:#fff;stroke-width:1.25;stroke-linecap:round;opacity:.84; }}
        .maf-network .network-fine {{ stroke-width:.8;opacity:.5; }}
        .maf-network circle {{ fill:#fff; }}
        .maf-kicker,.maf-section-label,.maf-eyebrow {{ color:#fff!important;font-family:'DM Sans',Arial,sans-serif;font-size:.67rem;letter-spacing:.2em;font-weight:600; }}
        .maf-hero h1,.maf-hero h1 a,.maf-hero h1 span {{ color:#fff!important;font-family:'Taskloom Olivera',Georgia,serif;font-weight:500;font-size:clamp(3.6rem,6.2vw,7.15rem);line-height:.82;letter-spacing:-.075em;max-width:700px;margin:1.25rem 0 1.65rem; }}
        .maf-hero h1 em {{ font-family:'Taskloom Olivera',Georgia,serif;font-weight:400;letter-spacing:-.085em; }}
        .maf-hero p {{ color:rgba(255,255,255,.78);font-family:'DM Sans',Arial,sans-serif;max-width:480px;font-size:.82rem;line-height:1.85;margin:0; }}
        .maf-hero + div {{ margin-top:-4.2rem;position:relative;z-index:4; }}
        .stButton > button[kind="primary"] {{ background:#fff;color:#1026e8;border-radius:0;min-height:3.2rem;font-family:'DM Sans',Arial,sans-serif;font-size:.72rem;font-weight:600;letter-spacing:.08em; }}
        .stButton > button[kind="primary"] p {{ color:#1026e8!important; }}
        .stButton > button[kind="primary"]:hover {{ background:#fff;color:#1026e8;transform:translateY(-3px);box-shadow:0 10px 0 rgba(255,255,255,.18); }}
        .maf-proof {{ display:none; }}
        .maf-footer {{ color:rgba(255,255,255,.58);font-family:'DM Sans',Arial,sans-serif;margin-top:4.5rem; }}

        /* Conversation workspace: a quiet writing surface using the same cobalt editorial system. */
        .maf-chat-intro {{ position:relative;overflow:hidden;max-width:930px;margin:2.3rem auto 0;padding:4rem 2rem 2.8rem;text-align:left;isolation:isolate; }}
        .maf-chat-intro::after {{ content:"";position:absolute;left:2rem;right:2rem;bottom:0;border-bottom:1px solid rgba(255,255,255,.35); }}
        .maf-chat-intro > :not(.maf-chat-network) {{ position:relative;z-index:2; }}
        .maf-chat-network {{ position:absolute;z-index:1;right:-8%;top:-12%;width:63%;height:120%;opacity:.34;animation:taskloom-network-float 12s ease-in-out infinite; }}
        .maf-chat-network path {{ fill:none;stroke:#fff;stroke-width:1.1;stroke-linecap:round; }}
        .maf-chat-network .network-fine {{ stroke-width:.75;opacity:.64; }}
        .maf-chat-network circle {{ fill:#fff; }}
        .maf-chat-intro h1 {{ color:#fff!important;font-family:'Taskloom Olivera',Georgia,serif;font-weight:500;font-size:clamp(3.3rem,6vw,6rem);line-height:.84;letter-spacing:-.075em;margin:.9rem 0 1.15rem;max-width:640px; }}
        .maf-chat-intro p {{ color:rgba(255,255,255,.78)!important;font-family:'DM Sans',Arial,sans-serif;font-size:.8rem;line-height:1.85;margin:0;max-width:500px; }}
        .maf-section-label {{ margin:2.35rem auto .6rem;max-width:830px;text-align:left; }}
        [data-testid="stTextArea"] {{ max-width:830px;margin:0 auto; }}
        [data-testid="stTextArea"] textarea {{ min-height:172px!important;background:#fff!important;color:#1026e8!important;border:1px solid rgba(255,255,255,.92)!important;border-radius:4px!important;font-family:'DM Sans',Arial,sans-serif!important;font-size:.86rem!important;line-height:1.75!important;box-shadow:0 12px 34px rgba(1,12,110,.18)!important; }}
        [data-testid="stTextArea"] textarea::placeholder {{ color:rgba(16,38,232,.48)!important; }}
        [data-testid="stTextArea"] textarea:focus {{ border-color:#fff!important;box-shadow:0 0 0 3px rgba(255,255,255,.2),0 12px 34px rgba(1,12,110,.18)!important; }}
        [data-testid="stTextArea"] + div {{ max-width:830px;margin:1rem auto 0; }}
        .stButton > button:not([kind="primary"]), .stDownloadButton > button {{ background:transparent!important;border-color:rgba(255,255,255,.52)!important;border-radius:0!important;color:#fff!important;font-family:'DM Sans',Arial,sans-serif!important;font-size:.7rem!important;letter-spacing:.06em; }}
        .stButton > button:not([kind="primary"]) p, .stDownloadButton > button p {{ color:#fff!important; }}
        .stButton > button:not([kind="primary"]):hover, .stDownloadButton > button:hover {{ background:rgba(255,255,255,.1)!important;border-color:#fff!important;color:#fff!important;transform:translateY(-2px); }}
        [data-testid="stCaptionContainer"] {{ color:rgba(255,255,255,.62)!important;font-family:'DM Sans',Arial,sans-serif;font-size:.67rem;line-height:1.6; }}
        .maf-chat-intro ~ div [data-testid="stHorizontalBlock"] {{ max-width:830px;margin-left:auto;margin-right:auto; }}
        @media(max-width:700px) {{
          .maf-hero {{ min-height:580px;padding:4rem 1.5rem 7rem; }}
          .maf-hero-copy {{ width:100%; }}
          .maf-network {{ width:130%;right:-45%;opacity:.32; }}
          .maf-hero h1 {{ font-size:3.45rem; }}
          .taskloom-splash img {{ width:110px;height:110px; }}
          .maf-chat-intro {{ margin-top:1.2rem;padding:3.2rem 1.4rem 2.4rem; }}
          .maf-chat-intro::after {{ left:1.4rem;right:1.4rem; }}
          .maf-chat-intro h1 {{ font-size:3.4rem; }}
          .maf-chat-network {{ width:115%;right:-46%;opacity:.25; }}
        }}

        /* Ivory inversion: blue is now a precise accent, not the whole canvas. */
        :root {{
          --maf-ink:#f5f1e8;
          --maf-panel:#ffffff;
          --maf-panel-soft:#e7ecff;
          --maf-text:#16172a;
          --maf-muted:#626579;
          --maf-stroke:rgba(24,56,223,.22);
          --maf-stroke-hot:rgba(24,56,223,.72);
          --maf-gold:#1838df;
          --maf-gold-bright:#1838df;
        }}
        .stApp {{ background:var(--maf-ink);color:var(--maf-text); }}
        .maf-nav {{ color:var(--maf-text); }}
        .maf-brand,.maf-wordmark {{ color:var(--maf-text)!important; }}
        .maf-wordmark small {{ color:rgba(22,23,42,.58); }}
        .maf-mark img {{ filter:brightness(0) saturate(100%) invert(18%) sepia(92%) saturate(3492%) hue-rotate(228deg) brightness(86%) contrast(105%); }}
        .maf-live {{ color:#1838df;background:rgba(255,255,255,.54);border-color:rgba(24,56,223,.28); }}
        .maf-live i {{ background:#1838df;box-shadow:0 0 0 3px rgba(24,56,223,.12); }}
        .maf-hero {{ background:transparent;padding-top:clamp(4rem,8vw,7rem);padding-bottom:clamp(3rem,6vw,5rem); }}
        .maf-network {{ opacity:.8; }}
        .maf-network path {{ stroke:#1838df;opacity:.68; }}
        .maf-network .network-fine {{ opacity:.3; }}
        .maf-network circle {{ fill:#1838df; }}
        .maf-kicker,.maf-section-label,.maf-eyebrow {{ color:#1838df!important; }}
        .maf-hero h1,.maf-hero h1 a,.maf-hero h1 span {{ color:var(--maf-text)!important;font-family:'Taskloom Olivera',Georgia,serif;font-size:clamp(3.7rem,6.2vw,7rem);font-weight:400;letter-spacing:-.055em; }}
        .maf-hero h1 .maf-hero-primary {{ color:#16172a!important;font-family:'Taskloom Olivera',Georgia,serif; }}
        .maf-hero h1 .maf-hero-accent {{ color:#1838df!important;font-family:'Taskloom Olivera',Georgia,serif; }}
        .maf-hero p {{ color:var(--maf-muted); }}
        .maf-hero + div {{ margin-top:-1.35rem; }}
        .stButton > button[kind="primary"] {{ background:#1838df;color:#fff;border-radius:0; }}
        .stButton > button[kind="primary"] p {{ color:#fff!important; }}
        .stButton > button[kind="primary"]:hover {{ background:#1838df;color:#fff;box-shadow:0 10px 0 rgba(24,56,223,.16); }}
        .maf-footer {{ color:rgba(22,23,42,.54); }}

        .maf-chat-intro {{ background:transparent; }}
        .maf-chat-intro::after {{ border-color:rgba(24,56,223,.28); }}
        .maf-chat-network {{ opacity:.45; }}
        .maf-chat-network path {{ stroke:#1838df; }}
        .maf-chat-network circle {{ fill:#1838df; }}
        .maf-chat-intro h1 {{ color:var(--maf-text)!important;font-family:'Taskloom Olivera',Georgia,serif;font-weight:400;letter-spacing:-.06em; }}
        .maf-chat-intro p {{ color:var(--maf-muted)!important; }}
        [data-testid="stTextArea"] textarea {{ background:#fff!important;color:#16172a!important;border-color:rgba(24,56,223,.5)!important;box-shadow:0 12px 34px rgba(24,56,223,.08)!important; }}
        [data-testid="stTextArea"] textarea::placeholder {{ color:rgba(22,23,42,.42)!important; }}
        [data-testid="stTextArea"] textarea:focus {{ border-color:#1838df!important;box-shadow:0 0 0 3px rgba(24,56,223,.12),0 12px 34px rgba(24,56,223,.08)!important; }}
        .stButton > button:not([kind="primary"]),.stDownloadButton > button {{ color:#1838df!important;background:transparent!important;border-color:rgba(24,56,223,.5)!important; }}
        .stButton > button:not([kind="primary"]) p,.stDownloadButton > button p {{ color:#1838df!important; }}
        .stButton > button:not([kind="primary"]):hover,.stDownloadButton > button:hover {{ background:rgba(24,56,223,.06)!important;border-color:#1838df!important;color:#1838df!important; }}
        [data-testid="stCaptionContainer"] {{ color:var(--maf-muted)!important; }}
        .maf-preview {{ background:#fff;border-color:rgba(24,56,223,.25);box-shadow:0 20px 55px rgba(24,56,223,.08);color:var(--maf-text); }}
        .maf-preview h1,.maf-preview h2,.maf-preview h3 {{ color:var(--maf-text);font-family:'Taskloom Olivera',Georgia,serif; }}
        .maf-role {{ background:#fff;color:#1838df;border-color:rgba(24,56,223,.25); }}
        [data-testid="stMetric"] {{ background:#fff;border-color:rgba(24,56,223,.2); }}
        [data-testid="stMetricValue"] {{ color:var(--maf-text); }}
        /* A focused prompt screen, deliberately quieter than the homepage. */
        .maf-chat-intro {{ max-width:760px;margin:1.55rem auto 0;padding:2.25rem 0 1.7rem;text-align:center; }}
        .maf-chat-intro::after {{ left:0;right:0; }}
        .maf-chat-network {{ display:none; }}
        .maf-chat-intro > :not(.maf-chat-network) {{ position:relative;z-index:2; }}
        .maf-chat-intro h1 {{ max-width:680px;margin:.65rem auto .85rem;font-size:clamp(3rem,4.5vw,4.9rem);line-height:.91;letter-spacing:-.045em; }}
        .maf-chat-intro p {{ max-width:590px;margin:0 auto;font-family:'DM Sans',Arial,sans-serif;font-size:.98rem;line-height:1.55; }}
        .maf-section-label {{ max-width:760px;margin:1.5rem auto .55rem;text-align:left;font-family:'DM Sans',Arial,sans-serif; }}
        [data-testid="stTextArea"] {{ max-width:760px; }}
        [data-testid="stTextArea"] textarea {{ min-height:122px!important;border-radius:8px!important;padding:1.1rem 1.2rem!important;font-family:'DM Sans',Arial,sans-serif!important;font-size:1rem!important;line-height:1.55!important;box-shadow:0 8px 22px rgba(24,56,223,.06)!important; }}
        [data-testid="stTextArea"] + div {{ max-width:760px;margin-top:.8rem; }}
        .stButton > button[kind="primary"],.stButton > button:not([kind="primary"]),.stDownloadButton > button {{ font-family:'DM Sans',Arial,sans-serif!important;font-size:.86rem!important;letter-spacing:0!important;border-radius:7px!important;min-height:3.05rem!important; }}
        [data-testid="stCaptionContainer"] {{ max-width:760px;margin:0 auto;font-family:'DM Sans',Arial,sans-serif;font-size:.74rem; }}
        .stButton > button[kind="primary"],.stButton > button:not([kind="primary"]),.stDownloadButton > button {{ font-family:'DM Sans',Arial,sans-serif!important;font-size:.86rem!important;font-weight:600!important;letter-spacing:.01em!important; }}
        .maf-decision-head,.maf-revision-head {{ margin:2.8rem auto 1.15rem;max-width:760px;padding-top:1.85rem;border-top:1px solid rgba(24,56,223,.28); }}
        .maf-decision-head h3,.maf-revision-head h3 {{ margin:.55rem 0 .4rem;color:var(--maf-text);font-family:'Taskloom Olivera',Georgia,serif;font-size:clamp(2rem,3vw,2.85rem);font-weight:400;letter-spacing:-.04em;line-height:1; }}
        .maf-decision-head p,.maf-revision-head p {{ margin:0;color:var(--maf-muted);font-family:'DM Sans',Arial,sans-serif;font-size:.92rem;line-height:1.55;max-width:570px; }}
        .maf-action-label {{ margin:.55rem 0 .48rem;color:#1838df;font-family:'DM Sans',Arial,sans-serif;font-size:.65rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase; }}
        .maf-action-label span {{ display:inline-block;margin-right:.45rem;color:rgba(24,56,223,.55); }}
        .maf-revision-head {{ margin-top:2.2rem; }}
        .maf-workspace-head {{ max-width:1030px;margin:2.75rem auto 1.25rem;padding:1.15rem 0;border-color:rgba(24,56,223,.28); }}
        .maf-workspace-head h2 {{ font-family:'Taskloom Olivera',Georgia,serif;font-size:clamp(2rem,3vw,3rem);font-weight:400;letter-spacing:-.04em; }}
        [data-testid="stMetric"] {{ border-radius:7px;padding:1rem;background:rgba(255,255,255,.72); }}
        [data-testid="stMetricLabel"] {{ color:var(--maf-muted);font-family:'DM Sans',Arial,sans-serif;font-size:.76rem; }}
        [data-testid="stMetricValue"] {{ font-family:'DM Sans',Arial,sans-serif;font-weight:600; }}
        [data-baseweb="tab-list"] {{ max-width:1030px;margin:0 auto;border-color:rgba(24,56,223,.28);gap:1.7rem; }}
        [data-baseweb="tab"] {{ color:var(--maf-muted);font-family:'DM Sans',Arial,sans-serif;font-size:.86rem;padding:1rem .05rem; }}
        [aria-selected="true"] {{ color:#1838df!important; }}
        [data-testid="stStatusWidget"], [data-testid="stExpander"] {{ background:rgba(255,255,255,.72);border-color:rgba(24,56,223,.24); }}
        [data-testid="stAlert"] {{ background:rgba(255,255,255,.75);border-color:rgba(24,56,223,.28);color:var(--maf-text); }}
        [data-testid="stHorizontalBlock"]:has(.maf-action-label) > [data-testid="column"] {{ padding:1rem 1rem 1.1rem;border:1px solid rgba(24,56,223,.24);background:rgba(255,255,255,.58); }}
        [data-testid="stHorizontalBlock"]:has(.maf-action-label) > [data-testid="column"]:first-child {{ border-radius:8px 0 0 8px; }}
        [data-testid="stHorizontalBlock"]:has(.maf-action-label) > [data-testid="column"]:last-child {{ margin-left:-1px;border-radius:0 8px 8px 0; }}
        /* The display face stays special; utility copy follows the Hermes-inspired mono face. */
        .maf-wordmark,.maf-live {{ font-family:'DM Sans',Arial,sans-serif!important; }}
        .maf-kicker,.maf-section-label,.maf-eyebrow,.maf-action-label,.maf-footer {{ font-family:'Courier Prime','Courier New',monospace!important; }}
        .maf-kicker,.maf-section-label,.maf-eyebrow,.maf-action-label {{ font-size:.68rem!important;font-weight:700!important;letter-spacing:.14em!important; }}
        .maf-live {{ font-size:.72rem!important;font-weight:600; }}
        .maf-footer {{ font-size:.72rem;letter-spacing:.03em; }}
        .stButton > button[kind="primary"],.stButton > button:not([kind="primary"]),.stDownloadButton > button,
        .stButton > button[kind="primary"] *, .stButton > button:not([kind="primary"]) *, .stDownloadButton > button * {{ font-family:'DM Sans',Arial,sans-serif!important;font-size:.86rem!important;font-weight:600!important;letter-spacing:.01em!important; }}
        [data-testid="stMetricValue"] {{ font-family:'DM Sans',Arial,sans-serif!important;font-weight:600; }}
        .maf-mark {{ width:35px;height:35px;color:#1838df;display:grid;place-items:center; }}
        .maf-mark img {{ display:none; }}
        .taskloom-symbol {{ width:34px;height:34px;overflow:visible; }}
        .taskloom-symbol .loom-ribbon {{ stroke:currentColor;stroke-width:5.7;stroke-linecap:round;stroke-linejoin:round; }}
        .taskloom-symbol .loom-diamond {{ stroke:currentColor;stroke-width:1.25;stroke-linejoin:round; }}
        @keyframes taskloom-ribbon-draw {{ from {{ stroke-dashoffset:1;opacity:0; }} to {{ stroke-dashoffset:0;opacity:1; }} }}
        .taskloom-splash {{ background:#f5f1e8; }}
        .taskloom-splash-network {{ opacity:.4; }}
        .taskloom-splash-network path {{ stroke:#1838df; }}
        .taskloom-splash-network circle {{ fill:#1838df; }}
        .taskloom-splash .taskloom-symbol {{ position:relative;z-index:1;width:min(18vw,142px);height:min(18vw,142px);color:#1838df;animation:taskloom-splash-symbol .58s .14s var(--maf-ease) both; }}
        .taskloom-splash .loom-ribbon {{ stroke-dasharray:1;stroke-dashoffset:1;animation:taskloom-ribbon-draw .72s .16s var(--maf-ease) forwards; }}
        .taskloom-splash .loom-ribbon:nth-child(2) {{ animation-delay:.29s; }}
        .taskloom-splash .loom-diamond {{ stroke-dasharray:1;stroke-dashoffset:1;animation:taskloom-ribbon-draw .3s .78s var(--maf-ease) forwards; }}
        .taskloom-splash strong {{ color:#1838df;animation:taskloom-splash-word .42s .68s var(--maf-ease) both; }}
        .taskloom-splash img {{ display:none; }}
        /* Hermes-style system font: Courier Prime for every interface surface. */
        .stApp,.stApp button,.stApp input,.stApp textarea,.stApp [data-baseweb],.stApp p,.stApp small,.stApp label,.stApp [data-testid="stCaptionContainer"] {{ font-family:'Courier Prime','Courier New',monospace!important; }}
        .stApp h1,.stApp h2,.stApp h3,.maf-hero h1,.maf-chat-intro h1,.maf-workspace-head h2,.maf-preview h1,.maf-preview h2,.maf-preview h3,.maf-decision-head h3,.maf-revision-head h3 {{ font-family:'Taskloom Olivera',Georgia,serif!important; }}
        /* Keep the review workspace's smaller headings and trace panels in the interface face too. */
        .stApp h4,.stApp h5,.stApp h6,[data-testid="stMetricLabel"],[data-testid="stMetricValue"],[data-baseweb="tab"],
        [data-testid="stJson"] pre,[data-testid="stJson"] code,[data-testid="stCode"] pre,[data-testid="stCode"] code {{ font-family:'Courier Prime','Courier New',monospace!important; }}
        .stApp h4,.stApp h5,.stApp h6 {{ font-weight:700!important;letter-spacing:.01em!important; }}
        .stButton > button[kind="primary"],.stButton > button:not([kind="primary"]),.stDownloadButton > button,
        .stButton > button[kind="primary"] *, .stButton > button:not([kind="primary"]) *, .stDownloadButton > button * {{ font-family:'Courier Prime','Courier New',monospace!important;font-weight:700!important; }}
        /* Selected ribbon identity: use the exact approved render, not an SVG approximation. */
        @keyframes taskloom-ribbon-arrive {{
          0% {{ opacity:0;transform:translateY(18px) scale(.88); }}
          72% {{ opacity:1;transform:translateY(0) scale(1.025); }}
          100% {{ opacity:1;transform:translateY(0) scale(1); }}
        }}
        .maf-mark {{ width:43px;height:48px; }}
        .maf-mark .taskloom-symbol {{ display:none; }}
        .maf-mark img {{ display:block!important;width:40px!important;height:46px!important;object-fit:contain;filter:none!important;mix-blend-mode:normal!important; }}
        .maf-wordmark {{ font-family:'Taskloom Olivera',Georgia,serif!important;font-size:1.28rem!important;font-weight:400!important;letter-spacing:-.04em!important; }}
        .maf-wordmark small {{ font-family:'Courier Prime','Courier New',monospace!important;font-size:.57rem!important;letter-spacing:.14em!important; }}
        .taskloom-splash {{ background:#f5f1e8!important; }}
        .taskloom-splash-network {{ display:none!important; }}
        .taskloom-splash .taskloom-symbol {{ display:none!important; }}
        .taskloom-splash img.taskloom-splash-dark-logo {{ display:none!important; }}
        .taskloom-splash img {{ display:block!important;position:relative;z-index:1;width:min(25vw,190px)!important;height:min(29vw,220px)!important;object-fit:contain;filter:none!important;mix-blend-mode:normal!important;animation:taskloom-ribbon-arrive .95s .08s var(--maf-ease) both!important; }}
        .taskloom-splash strong {{ color:#1838df!important;font-family:'Courier Prime','Courier New',monospace!important;font-size:.7rem!important;font-weight:700!important;letter-spacing:.22em!important;animation:taskloom-splash-word .42s .54s var(--maf-ease) both!important; }}
        .maf-live {{ text-decoration:none!important;cursor:pointer; }}
        .maf-live i {{ display:none!important; }}
        /* Keep Google/Gemini's clean sans treatment confined to the connection badge. */
        .maf-live,.maf-live * {{ font-family:'Taskloom Product Sans','Google Sans Text','Google Sans',Roboto,Arial,sans-serif!important;letter-spacing:0!important;font-weight:500!important; }}
        .gemini-logo {{ width:17px;height:17px;object-fit:contain;flex:0 0 auto; }}
        .maf-usage-limit {{ max-width:760px;margin:1.5rem auto .8rem;padding:1.35rem 1.45rem;display:flex;align-items:flex-start;gap:1rem;border:1px solid rgba(24,56,223,.2);border-radius:10px;background:rgba(255,255,255,.74);box-shadow:0 14px 34px rgba(24,56,223,.06);animation:maf-rise .34s var(--maf-ease) both; }}
        .maf-usage-limit-mark {{ width:31px;height:31px;flex:0 0 31px;display:grid;place-items:center;border-radius:50%;background:#1838df;color:#fff;font-family:'Taskloom Olivera',Georgia,serif;font-size:1.1rem;line-height:1; }}
        .maf-usage-limit .maf-kicker {{ margin:0 0 .32rem;color:#1838df!important; }}
        .maf-usage-limit h3 {{ margin:0;color:#151526;font-family:'Taskloom Olivera',Georgia,serif!important;font-size:1.55rem!important;font-weight:400!important;letter-spacing:-.035em!important; }}
        .maf-usage-limit p {{ margin:.42rem 0 0;color:#626173;font-family:'Courier Prime','Courier New',monospace!important;font-size:.75rem!important;line-height:1.65!important; }}
        .maf-footer {{ font-family:'Courier Prime','Courier New',monospace!important;letter-spacing:.06em!important; }}
        .maf-back-anchor {{ display:none!important; }}
        div[data-testid="stElementContainer"]:has(.maf-back-anchor) + div[data-testid="stElementContainer"] {{ width:max-content!important;max-width:none!important;overflow:visible!important; }}
        div[data-testid="stElementContainer"]:has(.maf-back-anchor) + div[data-testid="stElementContainer"] .stButton {{ width:max-content!important;overflow:visible!important; }}
        div[data-testid="stElementContainer"]:has(.maf-back-anchor) + div[data-testid="stElementContainer"] .stButton > button {{ width:max-content!important;min-height:auto!important;padding:.35rem .12rem!important;background:transparent!important;border:0!important;border-radius:0!important;box-shadow:none!important;color:#1838df!important;font-family:'Courier Prime','Courier New',monospace!important;font-size:.78rem!important;font-weight:700!important;letter-spacing:.02em!important;overflow:visible!important; }}
        div[data-testid="stElementContainer"]:has(.maf-back-anchor) + div[data-testid="stElementContainer"] .stButton > button:hover {{ background:transparent!important;color:#102aa9!important;transform:translateX(-2px); }}
        .maf-brand {{ position:relative; }}
        .maf-home-logo {{ display:none!important; }}
        .maf-logo-context {{ position:relative; }}
        .maf-mark {{ cursor:pointer;list-style:none; }}
        .maf-mark::-webkit-details-marker {{ display:none; }}
        .maf-mark:focus,.maf-mark:focus-visible {{ outline:none; }}
        .maf-logo-menu {{ display:none; }}
        .maf-menu-kicker {{ margin-bottom:.7rem;color:#1838df;font-family:'Courier Prime','Courier New',monospace;font-size:.63rem;font-weight:700;letter-spacing:.12em; }}
        [data-testid="stPopoverButton"] {{ min-height:2.65rem!important;margin:0!important;padding:.72rem 1rem!important;transform:none!important;border:1px solid #1026e8!important;border-radius:999px!important;background:#1026e8!important;color:#fff!important;font-family:'Courier Prime','Courier New',monospace!important;font-size:.67rem!important;font-weight:700!important;letter-spacing:.08em!important;box-shadow:none!important;transition:background .18s ease,transform .18s ease!important; }}
        [data-testid="stPopoverButton"] [aria-hidden="true"] {{ display:none!important; }}
        [data-testid="stPopoverButton"]:hover {{ background:#1838df!important;color:#fff!important;transform:translateY(-1px)!important; }}
        [data-testid="stPopoverBody"] {{ border:1px solid rgba(24,56,223,.22)!important;border-radius:14px!important;background:#f7f4ec!important;box-shadow:0 16px 40px rgba(24,56,223,.16)!important; }}
        [data-testid="stPopoverBody"] .stButton > button {{ border:0!important;border-top:1px solid rgba(24,56,223,.18)!important;border-radius:0!important;background:transparent!important;color:#1838df!important;font-family:'Courier Prime','Courier New',monospace!important;font-size:.76rem!important;text-align:left!important; }}
        [data-testid="stPopoverBody"] [data-testid="stDownloadButton"] > button {{ min-height:2.55rem!important;border:0!important;border-top:1px solid rgba(24,56,223,.18)!important;border-radius:0!important;background:transparent!important;color:#1838df!important;font-family:'Courier Prime','Courier New',monospace!important;font-size:.76rem!important;font-weight:700!important;letter-spacing:.02em!important;text-align:left!important;box-shadow:none!important; }}
        [data-testid="stPopoverBody"] [data-testid="stDownloadButton"] > button:hover {{ background:rgba(24,56,223,.05)!important;transform:translateX(2px)!important; }}
        [data-testid="stPopoverBody"] [data-testid="stRadio"] label {{ color:#151526!important;font-family:'Courier Prime','Courier New',monospace!important;font-size:.7rem!important; }}
        /* One angular vocabulary for actions, menus, and agent states. */
        .stButton > button,.stDownloadButton > button,[data-testid="stPopoverButton"] {{ border-radius:0!important;clip-path:polygon(10px 0,100% 0,calc(100% - 10px) 100%,0 100%)!important; }}
        .stLinkButton > a {{ min-height:3.05rem!important;border:0!important;border-radius:0!important;clip-path:polygon(10px 0,100% 0,calc(100% - 10px) 100%,0 100%)!important;background:#1838df!important;color:#fff!important;font-family:'Courier Prime','Courier New',monospace!important;font-size:.78rem!important;font-weight:700!important;letter-spacing:.02em!important;transition:transform .18s ease,box-shadow .18s ease,background .18s ease!important; }}
        .stLinkButton > a * {{ min-height:0!important;border:0!important;border-radius:0!important;clip-path:none!important;background:transparent!important;color:#fff!important;font-family:'Courier Prime','Courier New',monospace!important;font-size:inherit!important;font-weight:inherit!important;letter-spacing:inherit!important; }}
        .stLinkButton > a:hover {{ transform:translateY(-2px)!important;background:#294be1!important;box-shadow:0 8px 18px rgba(24,56,223,.2)!important;color:#fff!important; }}
        .stButton > button,.stDownloadButton > button,[data-testid="stPopoverButton"] {{ transition:transform .18s ease,box-shadow .18s ease,background .18s ease,color .18s ease!important; }}
        .stButton > button:hover,.stDownloadButton > button:hover,[data-testid="stPopoverButton"]:hover {{ transform:translateY(-2px)!important;box-shadow:0 8px 18px rgba(24,56,223,.16)!important; }}
        .stApp {{ --primary-color:#1838df!important; }}
        .maf-role {{ display:inline-flex;align-items:center;min-height:34px;padding:.38rem .78rem!important;border:0!important;border-radius:0!important;background:#1838df!important;color:#fff!important;font-family:'Courier Prime','Courier New',monospace!important;font-size:.68rem!important;clip-path:polygon(9px 0,100% 0,calc(100% - 9px) 100%,0 100%)!important; }}
        [data-testid="stTextArea"] [data-baseweb="textarea"] {{ padding:1px!important;border:0!important;border-radius:0!important;background:#1838df!important;clip-path:polygon(12px 0,100% 0,calc(100% - 12px) 100%,0 100%)!important;box-shadow:0 8px 20px rgba(24,56,223,.1)!important; }}
        [data-testid="stTextArea"] textarea {{ border:0!important;border-radius:0!important;background:#fff!important;box-shadow:none!important; }}
        [data-testid="stProgress"],[data-testid="stProgress"] > div,[data-testid="stProgress"] div[role="progressbar"] {{ border:0!important;border-radius:0!important;clip-path:polygon(8px 0,100% 0,calc(100% - 8px) 100%,0 100%)!important; }}
        [data-testid="stProgress"] > div {{ background:rgba(24,56,223,.14)!important; }}
        [data-testid="stProgress"] div[role="progressbar"] {{ background:#1838df!important; }}
        [data-testid="stTabs"] [data-baseweb="tab-highlight"],[data-testid="stTabs"] [data-baseweb="tab-border"],
        [data-testid="stTabs"] [role="tab"][aria-selected="true"]::after {{ background-color:#1838df!important; }}
        [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {{ color:#1838df!important;border-bottom-color:#1838df!important; }}
        [data-testid="stPopoverBody"],[data-testid="stMetric"],[data-testid="stExpander"],
        [data-testid="stHorizontalBlock"]:has(.maf-action-label) > [data-testid="column"] {{ border-radius:0!important; }}
        [data-testid="stMetric"],.maf-info-card dl div {{ border-radius:0!important;clip-path:polygon(12px 0,100% 0,calc(100% - 12px) 100%,0 100%)!important; }}
        .maf-info-card dl div {{ border:1px solid rgba(24,56,223,.28)!important;background:rgba(255,255,255,.72)!important; }}
        [data-testid="stStatusWidget"],[data-testid="stStatusWidget"] * {{ clip-path:none!important; }}
        [data-testid="stStatusWidget"] {{ border-radius:0!important;background:rgba(255,255,255,.72)!important;border-color:rgba(24,56,223,.28)!important; }}
        [data-testid="stExpander"] {{ background:rgba(255,255,255,.74)!important;border:0!important;clip-path:polygon(12px 0,100% 0,calc(100% - 12px) 100%,0 100%)!important; }}
        [data-testid="stExpander"] > details > summary {{ min-height:42px!important;display:flex!important;align-items:center!important;gap:.55rem!important;padding:.65rem 1rem!important;background:#1838df!important;color:#fff!important; }}
        [data-testid="stExpander"] > details > summary::-webkit-details-marker {{ color:#fff!important; }}
        [data-testid="stExpander"] > details {{ border:0!important;border-radius:0!important;background:transparent!important; }}
        [data-testid="stExpander"] > details > summary * {{ position:static!important;color:#fff!important;line-height:1.2!important; }}
        [data-testid="stExpander"] > details > summary [data-testid="stIconMaterial"] {{ font-family:'Material Symbols Rounded'!important;font-size:16px!important; }}
        [data-testid="stExpander"] > details > summary [data-testid="stMarkdownContainer"],
        [data-testid="stExpander"] > details > summary [data-testid="stMarkdownContainer"] p {{ font-family:'Courier Prime','Courier New',monospace!important; }}
        .maf-task-row {{ grid-template-columns:74px minmax(170px,.65fr) 1.35fr!important;gap:1.2rem!important;padding:1rem 0!important;border-bottom:1px solid rgba(24,56,223,.22)!important; }}
        .maf-task-id {{ min-width:66px;min-height:36px;display:inline-flex;align-items:center;justify-content:center;padding:0 .55rem;background:#1838df!important;color:#fff!important;font-family:'Taskloom Olivera',Georgia,serif!important;font-size:1rem!important;font-weight:400!important;letter-spacing:-.02em!important;line-height:1!important;white-space:nowrap;clip-path:polygon(9px 0,100% 0,calc(100% - 9px) 100%,0 100%); }}
        .maf-task-role {{ color:#151526!important;font-family:'Courier Prime','Courier New',monospace!important;font-size:.8rem!important;font-weight:700!important; }}
        .maf-task-objective {{ color:#626173!important;font-family:'Courier Prime','Courier New',monospace!important;font-size:.76rem!important;line-height:1.55!important; }}
        .maf-trace {{ border-left:2px solid #1838df!important;padding:0 0 1rem 1rem!important; }}
        .maf-trace strong {{ color:#1838df!important;font-family:'Courier Prime','Courier New',monospace!important; }}
        .maf-trace small {{ color:#626173!important;font-family:'Courier Prime','Courier New',monospace!important; }}
        @media(max-width:700px) {{ .maf-task-row {{ grid-template-columns:66px 1fr!important;gap:.8rem!important; }} .maf-task-objective {{ grid-column:2!important; }} }}
        .maf-panel-hero {{ max-width:1030px;margin:2.8rem auto 1.6rem;padding:3.5rem 0 2.5rem;border-bottom:1px solid rgba(24,56,223,.28); }}
        .maf-panel-hero h1 {{ color:var(--maf-text);font-family:'Taskloom Olivera',Georgia,serif;font-size:clamp(3.4rem,6vw,6.4rem);font-weight:400;line-height:.83;letter-spacing:-.06em;margin:.85rem 0 1.2rem; }}
        .maf-panel-hero p {{ max-width:560px;margin:0;color:var(--maf-muted);font-family:'Courier Prime','Courier New',monospace;font-size:.92rem;line-height:1.7; }}
        .maf-info-card {{ max-width:1030px;margin:1.5rem auto 0;padding:1.7rem 0;border-top:1px solid rgba(24,56,223,.28); }}
        .maf-info-card dl {{ display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin:1rem 0 1.5rem; }}
        .maf-info-card dl div {{ background:rgba(255,255,255,.58);border:1px solid rgba(24,56,223,.2);padding:1rem; }}
        .maf-info-card dt {{ color:#1838df;font-size:.66rem;font-weight:700;letter-spacing:.11em;text-transform:uppercase; }}
        .maf-info-card dd {{ margin:.55rem 0 0;color:var(--maf-text);font-size:.9rem; }}
        .maf-note {{ color:var(--maf-muted);font-size:.78rem;line-height:1.65;max-width:760px; }}
        .maf-connect-steps,.maf-connection-status {{ max-width:1030px;margin:1.2rem auto 0;display:grid;grid-template-columns:repeat(3,1fr);gap:1rem; }}
        .maf-connect-step,.maf-connection-status > div {{ min-height:160px;padding:1.15rem;border:1px solid rgba(24,56,223,.28);background:rgba(255,255,255,.62);clip-path:polygon(12px 0,100% 0,calc(100% - 12px) 100%,0 100%); }}
        .maf-connect-step i,.maf-connection-status i {{ display:block;color:#1838df;font-family:'Courier Prime','Courier New',monospace;font-style:normal;font-size:.65rem;font-weight:700;letter-spacing:.12em; }}
        .maf-connect-step b,.maf-connection-status b {{ display:block;margin:.7rem 0 .4rem;color:var(--maf-text);font-family:'Taskloom Olivera',Georgia,serif;font-size:1.38rem;font-weight:400;line-height:.95; }}
        .maf-connect-step p,.maf-connection-status p {{ margin:0;color:var(--maf-muted);font-family:'Courier Prime','Courier New',monospace;font-size:.72rem;line-height:1.55; }}
        .maf-security-strip {{ max-width:1030px;margin:1rem auto 1.3rem;padding:1rem 1.15rem;border-left:3px solid #1838df;background:rgba(24,56,223,.06);color:var(--maf-muted);font-family:'Courier Prime','Courier New',monospace;font-size:.75rem;line-height:1.65; }}
        .maf-security-strip strong {{ color:var(--maf-text); }}
        .maf-key-help {{ max-width:1030px;margin:.4rem auto 1rem;color:var(--maf-muted);font-family:'Courier Prime','Courier New',monospace;font-size:.72rem;line-height:1.5; }}
        .maf-ready-actions {{ max-width:1030px;margin:1.4rem auto 0; }}
        .maf-agent-map {{ max-width:1030px;margin:1.5rem auto 0;display:grid;grid-template-columns:1fr 2fr;gap:1rem;align-items:stretch; }}
        .maf-agent-core,.maf-agent-output {{ border:1px solid #1838df;background:#1838df;color:#fff;padding:2rem;display:flex;flex-direction:column;justify-content:center;min-height:170px; }}
        .maf-agent-core span,.maf-agent-output b {{ font-family:'Taskloom Olivera',Georgia,serif;font-size:2.25rem;font-weight:400;letter-spacing:-.04em; }}
        .maf-agent-core small,.maf-agent-output span {{ margin-top:.45rem;font-family:'Courier Prime','Courier New',monospace;font-size:.76rem; }}
        .maf-agent-branches {{ display:grid;grid-template-columns:repeat(2,1fr);gap:1rem; }}
        .maf-agent-card {{ min-height:100px;border:1px solid rgba(24,56,223,.28);background:rgba(255,255,255,.56);padding:1.1rem;display:flex;flex-direction:column;justify-content:flex-end; }}
        .maf-agent-card b {{ color:var(--maf-text);font-family:'Taskloom Olivera',Georgia,serif;font-size:1.35rem;font-weight:400; }}
        .maf-agent-card span {{ color:var(--maf-muted);font-family:'Courier Prime','Courier New',monospace;font-size:.72rem;line-height:1.45;margin-top:.35rem; }}
        .maf-map-detail-grid,.maf-architecture-detail-grid {{ max-width:1030px;margin:1rem auto 0;display:grid;grid-template-columns:repeat(3,1fr);gap:1rem; }}
        .maf-map-detail,.maf-architecture-detail {{ min-height:165px;padding:1.15rem;border:1px solid rgba(24,56,223,.28);background:rgba(255,255,255,.58);clip-path:polygon(12px 0,100% 0,calc(100% - 12px) 100%,0 100%); }}
        .maf-map-detail i,.maf-architecture-detail i {{ display:block;color:#1838df;font-family:'Courier Prime','Courier New',monospace;font-style:normal;font-size:.65rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase; }}
        .maf-map-detail b,.maf-architecture-detail b {{ display:block;margin:.7rem 0 .45rem;color:var(--maf-text);font-family:'Taskloom Olivera',Georgia,serif;font-size:1.42rem;font-weight:400;line-height:.95; }}
        .maf-map-detail p,.maf-architecture-detail p {{ margin:0;color:var(--maf-muted);font-family:'Courier Prime','Courier New',monospace;font-size:.72rem;line-height:1.55; }}
        .maf-message-flow {{ max-width:1030px;margin:1rem auto 0;padding:1.25rem;border-top:1px solid rgba(24,56,223,.28);border-bottom:1px solid rgba(24,56,223,.28);display:grid;grid-template-columns:repeat(5,1fr);gap:.55rem; }}
        .maf-message-flow div {{ min-height:84px;padding:.8rem;background:#1838df;color:#fff;clip-path:polygon(9px 0,100% 0,calc(100% - 9px) 100%,0 100%); }}
        .maf-message-flow i {{ display:block;font-family:'Courier Prime','Courier New',monospace;font-style:normal;font-size:.61rem;font-weight:700;letter-spacing:.1em;opacity:.72; }}
        .maf-message-flow b {{ display:block;margin-top:.45rem;font-family:'Courier Prime','Courier New',monospace;font-size:.7rem;line-height:1.35; }}
        .maf-observable-note {{ max-width:1030px;margin:1rem auto 0;padding:1rem 1.15rem;border-left:3px solid #1838df;background:rgba(24,56,223,.06);color:var(--maf-muted);font-family:'Courier Prime','Courier New',monospace;font-size:.75rem;line-height:1.65; }}
        .maf-agent-output {{ grid-column:1 / -1;min-height:110px;flex-direction:row;align-items:center;justify-content:space-between; }}
        .maf-architecture-flow {{ max-width:1030px;margin:1.5rem auto 0;display:flex;align-items:stretch;gap:.55rem; }}
        .maf-architecture-flow > div {{ flex:1;min-height:180px;border:1px solid rgba(24,56,223,.28);background:rgba(255,255,255,.58);padding:1rem;display:flex;flex-direction:column;justify-content:flex-end; }}
        .maf-architecture-flow i {{ color:#1838df;font-family:'Courier Prime','Courier New',monospace;font-style:normal;font-weight:700;font-size:.68rem;letter-spacing:.1em; }}
        .maf-architecture-flow b {{ color:var(--maf-text);font-family:'Taskloom Olivera',Georgia,serif;font-size:1.45rem;font-weight:400;line-height:.95;margin:.8rem 0 .5rem; }}
        .maf-architecture-flow span {{ color:var(--maf-muted);font-family:'Courier Prime','Courier New',monospace;font-size:.7rem;line-height:1.45; }}
        .maf-architecture-flow > em {{ align-self:center;color:#1838df;font-family:'Courier Prime','Courier New',monospace;font-style:normal;font-size:1.3rem; }}
        @media(max-width:700px) {{ .maf-info-card dl,.maf-agent-map,.maf-agent-branches,.maf-map-detail-grid,.maf-architecture-detail-grid,.maf-message-flow,.maf-connect-steps,.maf-connection-status {{ grid-template-columns:1fr; }} .maf-agent-output {{ grid-column:auto;flex-direction:column;align-items:flex-start; }} .maf-architecture-flow {{ flex-direction:column; }} .maf-architecture-flow > em {{ transform:rotate(90deg);align-self:center; }} }}
        @media(max-width:700px) {{ .maf-hero {{ background:transparent; }} }}
        /* Keep the landing-page call to action in view on projector-sized 16:9 screens. */
        @media (min-width:701px) and (max-height:800px) {{
          .maf-hero {{ min-height:390px!important;padding-top:2rem!important;padding-bottom:2rem!important; }}
          .maf-hero h1,.maf-hero h1 a,.maf-hero h1 span {{ font-size:clamp(3.25rem,5.2vw,5.4rem)!important;margin:.75rem 0 1rem!important; }}
          .maf-hero + div {{ margin-top:-.35rem!important; }}
          .maf-footer {{ margin-top:1.65rem!important; }}
        }}
        {night_css}
        </style>
        """,
        unsafe_allow_html=True,
    )
def get_provider() -> GeminiFailoverProvider:
    if not settings.gemini_api_key:
        raise ValueError("Gemini is not configured. Add GEMINI_API_KEY to the .env file.")
    return GeminiFailoverProvider(
        [settings.gemini_api_key, settings.gemini_backup_api_key or ""],
        settings.gemini_model,
    )


def run_agents(text: str):
    provider = get_provider()
    result = asyncio.run(Orchestrator(provider).run(text))
    return result, provider.last_call_cached, provider.successful_requests_today()


def local_usage_snapshot() -> tuple[int, int, int]:
    """Return Taskloom's own successful-call count, never pretending to know global key usage."""
    if not settings.gemini_api_key:
        return 0, settings.gemini_daily_request_limit, settings.gemini_daily_request_limit
    provider = get_provider()
    used = provider.successful_requests_today()
    budget = settings.gemini_daily_request_limit
    return used, budget, max(budget - used, 0)


def render_panel_back(key: str, destination: str = "home", label: str = "← Back to home") -> None:
    st.markdown('<div class="maf-back-anchor" aria-hidden="true"></div>', unsafe_allow_html=True)
    if st.button(label, key=key):
        st.session_state.page = destination
        preserve_theme_query()
        st.rerun()


def render_agent_menu() -> None:
    """Render real Streamlit controls so agent navigation remains reliable."""
    with st.container(key="agent_menu_slot"):
        with st.popover("AGENT MENU", use_container_width=True):
            st.markdown('<div class="maf-menu-kicker">AGENT NAVIGATION</div>', unsafe_allow_html=True)
            if st.button("Agent map", key="open_agent_map", use_container_width=True):
                st.session_state.page = "agent_map"
                preserve_theme_query()
                st.rerun()
            if st.button("Architecture", key="open_architecture", use_container_width=True):
                st.session_state.page = "architecture"
                preserve_theme_query()
                st.rerun()


def render_home_logo_control() -> None:
    """Place a native button over the visual mark so Home navigation is reliable."""
    st.markdown('<div class="maf-home-native-anchor" aria-hidden="true"></div>', unsafe_allow_html=True)
    if st.button("Taskloom home", key="taskloom_home_logo"):
        st.session_state.page = "home"
        preserve_theme_query()
        st.rerun()


def render_gemini_usage_control() -> None:
    """Provide a native, in-app action over the Gemini connection badge."""
    st.markdown('<div class="maf-gemini-native-anchor" aria-hidden="true"></div>', unsafe_allow_html=True)
    if st.button("Taskloom Gemini usage", key="taskloom_gemini_usage"):
        st.session_state.page = "usage"
        preserve_theme_query()
        st.rerun()


def render_theme_control() -> None:
    """Switch between the editorial daylight surface and the night-sky surface."""
    st.markdown('<div class="maf-theme-anchor" aria-hidden="true"></div>', unsafe_allow_html=True)
    label = "☀ DAY MODE" if st.session_state.get("night_mode", False) else "☾ NIGHT MODE"
    if st.button(label, key="taskloom_theme_toggle"):
        st.session_state.night_mode = not st.session_state.get("night_mode", False)
        st.query_params["theme"] = "night" if st.session_state.night_mode else "light"
        st.rerun()


def inject_navigation_asset_styles(ribbon_src: str, connected: bool) -> None:
    gemini_label = "✦  GEMINI CONNECTED" if connected else "CONNECT GEMINI"
    dark_navigation_css = """
        div[data-testid="stElementContainer"]:has(.maf-theme-anchor) + div[data-testid="stElementContainer"] .stButton > button {
          background:#0c1933!important;border-color:rgba(203,213,255,.55)!important;color:#f5f1e8!important;
        }
        div[data-testid="stElementContainer"]:has(.maf-gemini-native-anchor) + div[data-testid="stElementContainer"] .stButton > button {
          background:#0c1933!important;border-color:rgba(203,213,255,.55)!important;
        }
        div[data-testid="stElementContainer"]:has(.maf-gemini-native-anchor) + div[data-testid="stElementContainer"] .stButton > button::after {
          color:#f5f1e8!important;
        }
        .st-key-agent_menu_slot [data-testid="stPopoverButton"] { color:#cbd5ff!important; }
        .st-key-agent_menu_slot [data-testid="stPopoverButton"]:hover { color:#f5f1e8!important; }
        [data-testid="stPopoverBody"] { background:#0c1933!important;border-color:rgba(203,213,255,.40)!important;box-shadow:0 16px 40px rgba(0,0,0,.36)!important; }
    """ if st.session_state.get("night_mode", False) else ""
    st.markdown(
        f'''<style>
        /* One real navigation bar, fixed independently of Streamlit's scroll area. */
        div[data-testid="stElementContainer"]:has(.maf-nav) {{
          position:fixed!important;top:0!important;left:0!important;right:0!important;
          z-index:10050!important;height:0!important;margin:0!important;
          background:transparent!important;pointer-events:none!important;
        }}
        .maf-nav {{
          position:fixed!important;top:0!important;left:max(24px,calc((100vw - 1180px) / 2))!important;
          right:max(24px,calc((100vw - 1180px) / 2))!important;transform:none!important;
          width:auto!important;min-height:68px!important;margin:0!important;
          padding:1.05rem 0 .7rem!important;z-index:10051!important;
          pointer-events:auto!important;animation:none!important;
        }}
        .maf-nav form {{ margin:0!important; }}
        .maf-brand {{ color:#151526!important; }}
        .maf-home-logo {{ display:flex;align-items:center;gap:.75rem; }}
        .maf-brand > button {{ display:flex!important;align-items:center!important;border:0!important;padding:0!important;background:transparent!important;color:inherit!important;text-align:left!important;cursor:pointer!important; }}
        .maf-live {{ border:0!important;padding:0!important;background:transparent!important; }}
        .maf-live > button {{ display:inline-flex!important;align-items:center!important;gap:.5rem!important;padding:.36rem .7rem!important;border:1px solid #bfc9ff!important;border-radius:999px!important;background:#fff!important;color:#1838df!important;font:inherit!important;cursor:pointer!important; }}
        .maf-live > button:hover {{ transform:translateY(-1px)!important;box-shadow:0 6px 14px rgba(24,56,223,.14)!important; }}
        .maf-nav-actions {{ display:flex;flex-direction:column;align-items:flex-end;gap:.55rem; }}
        .maf-agent-menu {{ position:fixed!important;z-index:10071!important;top:62px!important;right:max(24px,calc((100vw - 1180px) / 2))!important;display:block;color:#52546a;font-family:'Courier Prime','Courier New',monospace;font-size:.67rem;font-weight:700;letter-spacing:.08em;line-height:1;text-align:center; }}
        .maf-agent-menu > span {{ display:block;padding:.25rem 0 .55rem;cursor:pointer;transition:color .18s ease,transform .18s ease; }}
        .maf-agent-menu:hover > span {{ color:#1838df;transform:translateY(-1px);text-decoration:underline;text-underline-offset:4px; }}
        .maf-agent-menu-panel {{ position:absolute;top:100%;right:0;min-width:172px;padding:.5rem;background:#fff;border:1px solid #c7d0ff;box-shadow:0 10px 22px rgba(21,21,38,.12);opacity:0;visibility:hidden;transform:translateY(-4px);pointer-events:none;transition:opacity .2s ease,transform .2s ease,visibility 0s linear .28s; }}
        .maf-agent-menu:hover .maf-agent-menu-panel {{ opacity:1;visibility:visible;transform:none;pointer-events:auto;transition-delay:0s; }}
        .maf-agent-menu-panel form {{ display:block!important; }}
        .maf-agent-menu-panel button {{ display:block;width:100%;margin:.2rem 0!important;border:0!important;padding:.62rem .72rem!important;background:#1838df!important;color:#fff!important;font:inherit!important;font-size:.64rem!important;font-weight:700!important;letter-spacing:.06em!important;text-align:left!important;white-space:nowrap;cursor:pointer!important;clip-path:polygon(9px 0,100% 0,calc(100% - 9px) 100%,0 100%)!important;transition:transform .18s ease,box-shadow .18s ease,filter .18s ease!important; }}
        .maf-agent-menu-panel button:hover {{ color:#fff!important;background:#1838df!important;transform:translateY(-1px)!important;filter:brightness(1.08)!important;box-shadow:0 6px 12px rgba(24,56,223,.22)!important; }}
        .block-container {{ padding-top:6.5rem!important; }}
        .maf-brand,.maf-live {{ display:none!important; }}
        .maf-home-native-anchor,.maf-gemini-native-anchor,.maf-theme-anchor {{ display:none!important; }}
        .maf-agent-menu {{ display:none!important; }}
        div[data-testid="stElementContainer"]:has(.maf-home-native-anchor) + div[data-testid="stElementContainer"] {{ position:fixed!important;z-index:10070!important;top:10px!important;left:max(24px,calc((100vw - 1180px) / 2))!important;width:265px!important;height:52px!important;display:block!important;pointer-events:auto!important; }}
        div[data-testid="stElementContainer"]:has(.maf-home-native-anchor) + div[data-testid="stElementContainer"] .stButton,div[data-testid="stElementContainer"]:has(.maf-home-native-anchor) + div[data-testid="stElementContainer"] .stButton > button {{ display:block!important;width:265px!important;height:52px!important;min-height:52px!important;margin:0!important;padding:0!important;border:0!important;border-radius:0!important;clip-path:none!important;background:transparent url('{ribbon_src}') left center/42px 48px no-repeat!important;color:transparent!important;box-shadow:none!important;position:relative!important;cursor:pointer!important; }}
        div[data-testid="stElementContainer"]:has(.maf-home-native-anchor) + div[data-testid="stElementContainer"] .stButton > button > div,div[data-testid="stElementContainer"]:has(.maf-home-native-anchor) + div[data-testid="stElementContainer"] .stButton > button p {{ display:none!important; }}
        div[data-testid="stElementContainer"]:has(.maf-home-native-anchor) + div[data-testid="stElementContainer"] .stButton > button::after {{ content:'TASKLOOM';position:absolute;left:54px;top:7px;color:#151526;font-family:'Taskloom Olivera',Georgia,serif;font-size:1.28rem;font-weight:400;letter-spacing:-.04em;line-height:1;white-space:nowrap; }}
        div[data-testid="stElementContainer"]:has(.maf-home-native-anchor) + div[data-testid="stElementContainer"] .stButton > button::before {{ content:'MULTI-AGENT LANGUAGE STUDIO';position:absolute;left:54px;top:31px;color:#626173;font-family:'Courier Prime','Courier New',monospace;font-size:.57rem;font-weight:700;letter-spacing:.14em;line-height:1;white-space:nowrap; }}
        div[data-testid="stElementContainer"]:has(.maf-home-native-anchor) + div[data-testid="stElementContainer"] .stButton > button:hover {{ transform:translateY(-1px)!important;filter:brightness(.92)!important; }}
        div[data-testid="stElementContainer"]:has(.maf-gemini-native-anchor) + div[data-testid="stElementContainer"] {{ position:fixed!important;z-index:10070!important;top:16px!important;right:max(24px,calc((100vw - 1180px) / 2))!important;width:180px!important;height:36px!important;display:block!important;pointer-events:auto!important; }}
        div[data-testid="stElementContainer"]:has(.maf-gemini-native-anchor) + div[data-testid="stElementContainer"] .stButton,div[data-testid="stElementContainer"]:has(.maf-gemini-native-anchor) + div[data-testid="stElementContainer"] .stButton > button {{ display:block!important;width:180px!important;height:36px!important;min-height:36px!important;margin:0!important;padding:0!important;border:1px solid #afbdff!important;border-radius:0!important;clip-path:polygon(9px 0,100% 0,calc(100% - 9px) 100%,0 100%)!important;background:rgba(255,255,255,.86)!important;color:transparent!important;box-shadow:inset 0 0 0 1px rgba(24,56,223,.05)!important;position:relative!important;cursor:pointer!important; }}
        div[data-testid="stElementContainer"]:has(.maf-gemini-native-anchor) + div[data-testid="stElementContainer"] .stButton > button > div,div[data-testid="stElementContainer"]:has(.maf-gemini-native-anchor) + div[data-testid="stElementContainer"] .stButton > button p {{ display:none!important; }}
        div[data-testid="stElementContainer"]:has(.maf-gemini-native-anchor) + div[data-testid="stElementContainer"] .stButton > button::after {{ content:'{gemini_label}';position:absolute;inset:0;display:grid;place-items:center;color:#1838df;font-family:'Taskloom Product Sans',Arial,sans-serif;font-size:.72rem;font-weight:600;white-space:nowrap; }}
        div[data-testid="stElementContainer"]:has(.maf-gemini-native-anchor) + div[data-testid="stElementContainer"] .stButton > button:hover {{ transform:translateY(-2px)!important;box-shadow:0 8px 16px rgba(24,56,223,.16)!important;border-color:#1838df!important; }}
        div[data-testid="stElementContainer"]:has(.maf-theme-anchor) + div[data-testid="stElementContainer"] {{ position:fixed!important;z-index:10070!important;top:16px!important;right:calc(max(24px,calc((100vw - 1180px) / 2)) + 192px)!important;width:140px!important;height:36px!important;display:block!important;pointer-events:auto!important; }}
        div[data-testid="stElementContainer"]:has(.maf-theme-anchor) + div[data-testid="stElementContainer"] .stButton,div[data-testid="stElementContainer"]:has(.maf-theme-anchor) + div[data-testid="stElementContainer"] .stButton > button {{ display:block!important;width:140px!important;height:36px!important;min-height:36px!important;margin:0!important;padding:0 8px!important;border:1px solid #1838df!important;border-radius:0!important;clip-path:polygon(9px 0,100% 0,calc(100% - 9px) 100%,0 100%)!important;background:#1838df!important;color:#fff!important;box-shadow:none!important;font-family:'Courier Prime','Courier New',monospace!important;font-size:.61rem!important;font-weight:700!important;letter-spacing:.06em!important;white-space:nowrap!important;cursor:pointer!important; }}
        div[data-testid="stElementContainer"]:has(.maf-theme-anchor) + div[data-testid="stElementContainer"] .stButton > button > div,div[data-testid="stElementContainer"]:has(.maf-theme-anchor) + div[data-testid="stElementContainer"] .stButton > button p {{ color:#fff!important;white-space:nowrap!important;line-height:1!important; }}
        div[data-testid="stElementContainer"]:has(.maf-theme-anchor) + div[data-testid="stElementContainer"] .stButton > button:hover {{ transform:translateY(-2px)!important;box-shadow:0 8px 16px rgba(24,56,223,.22)!important;background:#294be1!important; }}
        .st-key-agent_menu_slot {{ position:fixed!important;z-index:10071!important;top:62px!important;right:max(24px,calc((100vw - 1180px) / 2))!important;width:172px!important;pointer-events:auto!important; }}
        .st-key-agent_menu_slot [data-testid="stPopover"],.st-key-agent_menu_slot [data-testid="stPopoverButton"] {{ width:100%!important; }}
        .st-key-agent_menu_slot [data-testid="stPopoverButton"] {{ min-height:25px!important;margin:0!important;padding:0!important;border:0!important;border-radius:0!important;clip-path:none!important;background:transparent!important;color:#52546a!important;font-family:'Courier Prime','Courier New',monospace!important;font-size:.67rem!important;font-weight:700!important;letter-spacing:.08em!important;text-align:center!important;box-shadow:none!important; }}
        .st-key-agent_menu_slot [data-testid="stPopoverButton"]:hover {{ color:#1838df!important;transform:translateY(-1px)!important;text-decoration:underline!important;text-underline-offset:4px!important; }}
        [data-testid="stPopoverBody"] {{ border:1px solid #c7d0ff!important;border-radius:0!important;background:#fff!important;box-shadow:0 10px 22px rgba(21,21,38,.12)!important; }}
        [data-testid="stPopoverBody"] .stButton > button {{ margin:.2rem 0!important;padding:.62rem .72rem!important;background:#1838df!important;color:#fff!important;font-family:'Courier Prime','Courier New',monospace!important;font-size:.64rem!important;font-weight:700!important;letter-spacing:.06em!important;clip-path:polygon(9px 0,100% 0,calc(100% - 9px) 100%,0 100%)!important; }}
        [data-testid="stPopoverBody"] .stButton > button > div,[data-testid="stPopoverBody"] .stButton > button p {{ display:block!important;color:#fff!important;font:inherit!important;opacity:1!important;visibility:visible!important; }}
        @media(max-width:700px) {{
          .maf-nav {{ left:16px!important;right:16px!important;padding:.8rem 0 .55rem!important; }}
          .maf-wordmark small {{ display:none!important; }}
          .maf-live {{ font-size:.62rem!important;padding:.3rem .48rem!important; }}
          .maf-agent-menu {{ top:58px!important;right:16px!important; }}
          .maf-agent-menu-panel {{ right:-4px; }}
          .st-key-agent_menu_slot {{ top:103px!important;right:16px!important; }}
          div[data-testid="stElementContainer"]:has(.maf-home-native-anchor) + div[data-testid="stElementContainer"] {{ top:8px!important;left:16px!important; }}
          div[data-testid="stElementContainer"]:has(.maf-gemini-native-anchor) + div[data-testid="stElementContainer"] {{ top:13px!important;right:16px!important; }}
          div[data-testid="stElementContainer"]:has(.maf-theme-anchor) + div[data-testid="stElementContainer"] {{ top:58px!important;right:16px!important; }}
        }}
        {dark_navigation_css}
        </style>''',
        unsafe_allow_html=True,
    )


def render_usage_page() -> None:
    if not settings.gemini_api_key:
        render_connection_page()
        return

    render_panel_back("usage_back")
    used, budget, remaining = local_usage_snapshot()
    reset_at = (datetime.now().astimezone() + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    st.markdown(
        """
        <section class="maf-panel-hero">
          <div class="maf-kicker">Private Gemini connection</div>
          <h1>YOU'RE<br>READY TO WEAVE.</h1>
          <p>Your keys are saved only on this device. Start a task when you are ready; Taskloom uses your primary key first and preserves the backup for a 429 rate limit.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    backup_state = "Ready for 429 failover" if settings.gemini_backup_api_key else "Not added yet"
    backup_detail = (
        "Taskloom tries it only after the primary key is rate-limited."
        if settings.gemini_backup_api_key
        else "Optional: add one for uninterrupted work when the primary key hits a 429 limit."
    )
    st.markdown(
        f"""
        <section class="maf-connection-status">
          <div><i>PRIMARY KEY</i><b>Saved securely</b><p>Used for new Gemini requests unless it receives a rate-limit response.</p></div>
          <div><i>BACKUP KEY</i><b>{escape(backup_state)}</b><p>{escape(backup_detail)}</p></div>
          <div><i>CONNECTION CHECK</i><b>First task verifies access</b><p>Saving a key never spends quota. Gemini validates it only when you submit your first task.</p></div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    if st.session_state.pop("just_connected", False):
        st.success("Gemini keys saved securely. You are ready to start your first task.")
    left, centre, right = st.columns(3)
    left.metric("Taskloom API calls today", used)
    centre.metric("Local calls remaining", remaining)
    right.metric("Local daily request budget", budget)
    st.markdown(
        f"""
        <section class="maf-info-card">
          <div class="maf-kicker">Connection details</div>
          <dl>
            <div><dt>Model</dt><dd>{escape(settings.gemini_model)}</dd></div>
            <div><dt>Budget resets</dt><dd>{escape(reset_at.strftime('%d %b, %I:%M %p %Z'))}</dd></div>
            <div><dt>Cached responses</dt><dd>Do not use a Gemini request</dd></div>
          </dl>
          <p class="maf-note">These are local app counters, not Gemini’s live remaining quota. Google can apply separate per-minute, per-day, model, project, or shared-key limits before this local budget is used.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="maf-ready-actions">', unsafe_allow_html=True)
    start_col, manage_col = st.columns([3, 1])
    with start_col:
        if st.button("Start a task  →", type="primary", use_container_width=True, key="usage_start_task"):
            st.session_state.page = "home"
            preserve_theme_query()
            st.rerun()
    with manage_col:
        if st.button("Manage keys", use_container_width=True, key="usage_manage_keys"):
            st.session_state.page = "connection"
            preserve_theme_query()
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def render_connection_page() -> None:
    """First-run onboarding for the packaged desktop app."""
    render_panel_back("connection_back")
    st.markdown(
        """
        <section class="maf-panel-hero">
          <div class="maf-kicker">Private device setup</div>
          <h1>CONNECT<br>YOUR GEMINI.</h1>
          <p>Set up your personal keys once, on this device. Taskloom uses them only for requests you choose to send.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <section class="maf-connect-steps">
          <div class="maf-connect-step"><i>01 · CREATE</i><b>Make your key</b><p>Open Google AI Studio, choose <strong>Get API key</strong>, then create a key for your own Google project.</p></div>
          <div class="maf-connect-step"><i>02 · ADD A SPARE</i><b>Optional, recommended</b><p>Create a second key if you want continuity. It stays unused unless the primary key receives a Gemini 429 limit.</p></div>
          <div class="maf-connect-step"><i>03 · SAVE LOCALLY</i><b>Keep control</b><p>Paste the key(s) below. Taskloom saves them to Windows Credential Manager—not to a project file or download.</p></div>
        </section>
        <section class="maf-security-strip">
          <strong>Before you paste:</strong> API keys grant access to your Gemini quota. Do not share them in messages, screenshots, or repositories. Saving a key here does not make a Gemini request or use quota.
        </section>
        """,
        unsafe_allow_html=True,
    )
    st.link_button("Open Google AI Studio  →", "https://aistudio.google.com/apikey", use_container_width=True)

    if not secure_storage_available():
        st.error("Secure credential storage is not available in this installation. Install the packaged Taskloom desktop application before entering a key.")
        return

    st.markdown('<div class="maf-section-label">Save keys on this device</div>', unsafe_allow_html=True)
    primary_key = st.text_input("Primary Gemini API key · required", type="password", placeholder="Paste the key you will use most often", key="desktop_primary_key")
    st.markdown('<p class="maf-key-help">This key is used first. It is stored securely in Windows Credential Manager and is never displayed after you save it.</p>', unsafe_allow_html=True)
    backup_key = st.text_input("Backup Gemini API key · optional", type="password", placeholder="Paste a separate spare key for 429 failover", key="desktop_backup_key")
    st.markdown('<p class="maf-key-help">The backup is not rotated on every request. Taskloom only tries it after Gemini rate-limits the primary key with a 429 response.</p>', unsafe_allow_html=True)
    save_col, remove_col = st.columns([4, 1])
    with save_col:
        save_clicked = st.button("Save securely and connect  →", type="primary", use_container_width=True)
    with remove_col:
        remove_clicked = st.button("Remove saved keys", use_container_width=True, disabled=not bool(settings.gemini_api_key or settings.gemini_backup_api_key))

    if save_clicked:
        if not primary_key.strip():
            st.warning("Paste a primary Gemini API key to continue.")
        else:
            try:
                save_api_key("primary", primary_key)
                if backup_key.strip():
                    save_api_key("backup", backup_key)
                elif settings.gemini_backup_api_key:
                    delete_api_key("backup")
                refresh_credentials()
                st.session_state.just_connected = True
                st.session_state.page = "usage"
                preserve_theme_query()
                st.rerun()
            except Exception as exc:
                st.error(f"Taskloom could not save the keys securely: {exc}")

    if remove_clicked:
        try:
            delete_api_key("primary")
            delete_api_key("backup")
            refresh_credentials()
            st.success("Saved Gemini keys were removed from this device.")
        except Exception as exc:
            st.error(f"Taskloom could not remove the saved keys: {exc}")


def render_agent_map_page() -> None:
    render_panel_back("agent_map_back")
    st.markdown(
        """
        <section class="maf-panel-hero maf-map-hero">
          <div class="maf-kicker">Agent map</div>
          <h1>ONE HOST.<br>MANY ROLES.</h1>
          <p>Each request is interpreted, decomposed, produced, reviewed, and returned as one human-readable result.</p>
        </section>
        <section class="maf-agent-map">
          <div class="maf-agent-core"><span>Host Agent</span><small>Owns the workflow · routes information · preserves the task state</small></div>
          <div class="maf-agent-branches">
            <div class="maf-agent-card"><b>Language Analyst</b><span>Normalizes the request and extracts intent, entities, constraints, ambiguity, and a semantic frame.</span></div>
            <div class="maf-agent-card"><b>Planning Agent</b><span>Creates bounded tasks, dependencies, expected outputs, and specialist roles.</span></div>
            <div class="maf-agent-card"><b>Specialist Agents</b><span>Produce task-specific material such as research, drafting, comparison, structure, or tone work.</span></div>
            <div class="maf-agent-card"><b>Review Agent</b><span>Scores relevance, completeness, specificity, consistency, and instruction compliance.</span></div>
          </div>
          <div class="maf-agent-output"><b>NLG Writer</b><span>Synthesizes approved findings into one preview for human approval.</span></div>
        </section>
        <section class="maf-message-flow">
          <div><i>01 · receive</i><b>User request</b></div>
          <div><i>02 · interpret</i><b>Language analysis</b></div>
          <div><i>03 · allocate</i><b>Task plan</b></div>
          <div><i>04 · verify</i><b>Review score</b></div>
          <div><i>05 · return</i><b>Final preview</b></div>
        </section>
        <section class="maf-map-detail-grid">
          <div class="maf-map-detail"><i>Why separate roles?</i><b>Focused work</b><p>Each stage has a single responsibility, which reduces repeated reasoning and makes failures easier to locate.</p></div>
          <div class="maf-map-detail"><i>What is recorded?</i><b>Visible trace</b><p>Task IDs, specialist assignments, task results, review status, and final delivery are retained as an observable communication trace.</p></div>
          <div class="maf-map-detail"><i>Who decides?</i><b>Human in control</b><p>The system returns a preview. The user can approve it, request a focused revision, or begin a new task.</p></div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_architecture_page() -> None:
    render_panel_back("architecture_back")
    st.markdown(
        """
        <section class="maf-panel-hero maf-map-hero">
          <div class="maf-kicker">Architecture</div>
          <h1>THE PATH<br>OF A PROMPT.</h1>
          <p>Taskloom keeps the model call efficient while making the language-processing and approval stages visible.</p>
        </section>
        <section class="maf-architecture-flow">
          <div><i>01</i><b>Natural-language request</b><span>User describes the outcome.</span></div>
          <em>→</em><div><i>02</i><b>SLP analysis</b><span>Intent, entities, tone, constraints.</span></div>
          <em>→</em><div><i>03</i><b>Task planning</b><span>Dependencies and specialist roles.</span></div>
          <em>→</em><div><i>04</i><b>Validated generation</b><span>Gemini returns structured workflow data.</span></div>
          <em>→</em><div><i>05</i><b>Review + approval</b><span>Quality check, preview, and human decision.</span></div>
        </section>
        <section class="maf-architecture-detail-grid">
          <div class="maf-architecture-detail"><i>Application layer · Streamlit</i><b>Interface & control</b><p>Captures the request, shows agent traces and quality data, manages session state, and provides approval, revision, download, and read-aloud actions.</p></div>
          <div class="maf-architecture-detail"><i>Orchestration layer · Python</i><b>Deterministic coordinator</b><p>The Host Agent coordinates the logical stages, manages task dependencies, limits task count and parallel work, and records the observable trace.</p></div>
          <div class="maf-architecture-detail"><i>Intelligence layer · Gemini</i><b>Structured generation</b><p>Gemini produces a schema-validated compact run result containing analysis, plan, specialist findings, review, and final answer.</p></div>
          <div class="maf-architecture-detail"><i>Reliability layer · Pydantic</i><b>Validated data</b><p>Every stage uses typed schemas, so malformed analysis, plans, review scores, or task IDs are rejected before reaching the interface.</p></div>
          <div class="maf-architecture-detail"><i>Efficiency layer · DiskCache</i><b>Local reuse</b><p>Repeated prompts return cached answers without consuming another Gemini request. Daily local call counters make consumption visible.</p></div>
          <div class="maf-architecture-detail"><i>Resilience layer · Failover</i><b>Quota-aware delivery</b><p>When the primary Gemini key receives a 429 rate limit, Taskloom tries the spare key. A friendly usage message appears only when both are unavailable.</p></div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def revise_artifact(original_request: str, current_output: str, feedback: str):
    prompt = f"""You are the Revision and NLG Agent. Revise the existing content according to the
user's latest feedback. Preserve useful material that still fits, remove material the feedback no
longer asks for, and return only the complete revised content. Do not discuss the revision,
workflow, agents, or prompt.

ORIGINAL REQUEST:
{original_request}

CURRENT CONTENT:
{current_output}

USER'S REVISION:
{feedback}
"""
    provider = get_provider()
    output = asyncio.run(provider.generate_text(prompt))
    return output, provider.last_call_cached, provider.successful_requests_today()


def reset_run() -> None:
    for key in (
        "result", "accepted", "final_output", "revision_count", "original_request",
        "response_source", "local_requests_today", "revision_mode", "revision_feedback",
    ):
        st.session_state.pop(key, None)


def show_run_error(exc: Exception) -> None:
    details = str(exc)
    quota_error = any(token in details.lower() for token in ("429", "quota", "resource_exhausted"))
    if quota_error:
        st.markdown(
            """
            <section class="maf-usage-limit" role="status">
              <div class="maf-usage-limit-mark">•</div>
              <div>
                <div class="maf-kicker">Gemini temporarily unavailable</div>
                <h3>Gemini rate-limited this request.</h3>
                <p>Your work is safe. Gemini returned a provider quota or rate-limit response; this is separate from the local call counter shown in this app. Please wait a moment and try again.</p>
              </div>
            </section>
            """,
            unsafe_allow_html=True,
        )
        if st.button("View local call counter", key="quota_usage_link"):
            st.session_state.page = "usage"
            preserve_theme_query()
            st.rerun()
        return
    else:
        st.error("Gemini could not complete this run. Check the connection and try again.")
    with st.expander("Technical details"):
        st.code(details)


def render_tts(text: str) -> None:
    safe = json.dumps(text)
    st.components.v1.html(
        f"""
        <div style="display:flex;gap:8px;align-items:center;font:13px Arial;color:#d8dce2">
          <button onclick='speak()'>▶ Read aloud</button>
          <button onclick='speechSynthesis.pause()'>Pause</button>
          <button onclick='speechSynthesis.resume()'>Resume</button>
          <button onclick='speechSynthesis.cancel()'>Stop</button>
          <label>Speed <input id="rate" type="range" min="0.6" max="1.6" value="1" step="0.1"></label>
        </div>
        <script>
          function speak() {{
            speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance({safe});
            utterance.rate = Number(document.getElementById('rate').value);
            speechSynthesis.speak(utterance);
          }}
        </script>
        """,
        height=52,
    )


if "night_mode" not in st.session_state:
    st.session_state.night_mode = st.query_params.get("theme") == "night"

inject_theme()

ribbon_logo_path = resource_path("assets", "taskloom-ribbon-logo-transparent.png")
ribbon_logo_src = "data:image/png;base64," + base64.b64encode(ribbon_logo_path.read_bytes()).decode("ascii")
gemini_logo_path = resource_path("assets", "gemini-logo.png")
gemini_logo_src = "data:image/png;base64," + base64.b64encode(gemini_logo_path.read_bytes()).decode("ascii")
inject_navigation_asset_styles(ribbon_logo_src, bool(settings.gemini_api_key))

if not st.session_state.get("splash_seen"):
    st.markdown(
        f'''<div class="taskloom-splash">
          <svg class="taskloom-splash-network" viewBox="0 0 1200 620" aria-hidden="true">
            <path d="M-30 110 C250 85, 410 270, 600 310 S950 130, 1230 80"/>
            <path d="M-20 490 C250 430, 380 335, 600 310 S930 400, 1230 535"/>
            <path d="M140 -20 C270 200, 420 270, 600 310 S900 250, 1060 -20"/>
            <path d="M165 650 C310 460, 455 355, 600 310 S850 410, 1060 650"/>
            <path d="M-20 305 C255 305, 420 305, 600 310 S950 305, 1220 305"/>
            <circle cx="600" cy="310" r="5"/><circle cx="411" cy="270" r="3"/><circle cx="796" cy="264" r="3"/>
          </svg>
          <div class="taskloom-splash-vector" aria-label="Taskloom ribbon logo">{taskloom_logo_svg}</div>
          <img class="taskloom-splash-light-logo" src="{ribbon_logo_src}" alt="Taskloom ribbon logo">
          <img class="taskloom-splash-dark-logo" src="{night_ribbon_logo_src}" alt=""><strong>Taskloom</strong>
        </div>''',
        unsafe_allow_html=True,
    )
    st.session_state.splash_seen = True

if settings.gemini_api_key and st.session_state.get("result"):
    if "Mock research result" in st.session_state.result.final_answer:
        reset_run()

connected = bool(settings.gemini_api_key)
status = (
    f'<img class="gemini-logo" src="{gemini_logo_src}" alt="Gemini">'
    '<span>GEMINI CONNECTED</span>'
    if connected
    else '<span>GEMINI NOT CONFIGURED</span>'
)
if "page" not in st.session_state:
    st.session_state.page = "home"

requested_panel = st.query_params.get("taskloom_panel")
if requested_panel in {"usage", "agent_map", "architecture"}:
    st.session_state.page = requested_panel
elif requested_panel == "home":
    st.session_state.page = "home"

st.markdown(
    f"""
    <div class="maf-nav">
      <form class="maf-brand" method="get">
        <button type="submit" name="taskloom_panel" value="home" aria-label="Return to Taskloom home">
          <div class="maf-home-logo">
            <div class="maf-mark"><img src="{ribbon_logo_src}" alt="Taskloom ribbon mark"></div>
            <div class="maf-wordmark">TASKLOOM<small>MULTI-AGENT LANGUAGE STUDIO</small></div>
          </div>
        </button>
      </form>
      <div class="maf-nav-actions">
        <form class="maf-live" method="get">
          <button type="submit" name="taskloom_panel" value="usage" title="View Taskloom Gemini usage">{status}</button>
        </form>
        <div class="maf-agent-menu">
          <span>AGENT MENU</span>
          <div class="maf-agent-menu-panel">
            <form method="get"><button type="submit" name="taskloom_panel" value="agent_map">Agent map</button></form>
            <form method="get"><button type="submit" name="taskloom_panel" value="architecture">Architecture</button></form>
          </div>
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

render_home_logo_control()
render_gemini_usage_control()
render_theme_control()
render_agent_menu()

if st.session_state.page == "usage":
    render_usage_page()
    st.stop()

if st.session_state.page == "connection":
    render_connection_page()
    st.stop()

if st.session_state.page == "agent_map":
    render_agent_map_page()
    st.stop()

if st.session_state.page == "architecture":
    render_architecture_page()
    st.stop()

if st.session_state.page == "home":
    st.markdown(
        """
        <section class="maf-hero">
      <svg class="maf-network" viewBox="0 0 850 650" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
        <path d="M220 -40 C300 112, 380 220, 530 315 S700 422, 875 600"/>
        <path d="M370 -30 C400 135, 455 215, 530 315 S655 470, 705 685"/>
        <path d="M860 72 C685 142, 625 235, 530 315 S307 455, 220 665"/>
        <path d="M880 230 C704 238, 622 280, 530 315 S330 340, 145 350"/>
        <path class="network-fine" d="M570 -20 C545 130, 550 205, 530 315 S438 490, 350 670"/>
        <path class="network-fine" d="M875 480 C692 410, 612 357, 530 315 S320 165, 254 -10"/>
        <circle cx="530" cy="315" r="7"/><circle cx="625" cy="235" r="3"/><circle cx="438" cy="490" r="3"/>
      </svg>
      <div class="maf-hero-copy">
        <div class="maf-kicker">One prompt · many specialists · one result</div>
        <h1><span class="maf-hero-primary">ONE TASK.</span><br><span class="maf-hero-accent">MANY MINDS.</span></h1>
        <p>Tell us what you need. We will make a response for you.</p>
      </div>
    </section>
        """,
        unsafe_allow_html=True,
    )
    _, start_col, _ = st.columns([4, 4, 4])
    with start_col:
        if st.button("Start chat  →", type="primary", use_container_width=True):
            st.session_state.page = "chat"
            preserve_theme_query()
            st.rerun()
    st.markdown(
        """
        <div class="maf-footer">TASKLOOM · Multi-agent language processing · Human-controlled output</div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

if st.session_state.page == "output":
    render_panel_back("output_back", destination="chat", label="← Edit request")
else:
    render_panel_back("chat_back")

    st.markdown(
        """
        <section class="maf-chat-intro">
          <svg class="maf-chat-network" viewBox="0 0 850 510" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
            <path d="M790 -25 C680 78, 637 140, 520 222 S315 345, 58 520"/>
            <path d="M870 95 C696 137, 614 180, 520 222 S319 244, 40 222"/>
            <path d="M655 -20 C615 98, 577 164, 520 222 S431 380, 380 530"/>
            <path class="network-fine" d="M870 350 C692 330, 617 274, 520 222 S344 82, 255 -20"/>
            <circle cx="520" cy="222" r="6"/><circle cx="614" cy="180" r="3"/><circle cx="431" cy="380" r="3"/>
          </svg>
          <div class="maf-kicker">Taskloom workspace</div>
          <h1>WHAT WILL<br>WE MAKE?</h1>
          <p>Tell us what you need. We will put it together for you.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="maf-section-label">New conversation</div>', unsafe_allow_html=True)

    if "task_input" not in st.session_state:
        st.session_state.task_input = ""

    _, composer, _ = st.columns([1, 10, 1])
    with composer:
        prompt = st.text_area("Task", key="task_input", height=124)
        action_col, clear_col = st.columns([5, 1])
        with action_col:
            run_clicked = st.button(
                "Weave this task  →", type="primary", use_container_width=True, disabled=not connected,
            )
        with clear_col:
            if st.button("Clear", use_container_width=True):
                reset_run()
                st.session_state.task_input = ""
                st.rerun()
        st.caption("↳ One request creates the complete preview. Exact repeats are served locally without using Gemini quota.")

    if not connected:
        st.warning("Connect your personal Gemini API keys from the Gemini button before starting a task.")

    if run_clicked:
        if not prompt.strip():
            st.warning("Describe a task before starting the team.")
        else:
            try:
                existing_request = st.session_state.get("original_request", "").strip()
                if st.session_state.get("result") and prompt.strip() == existing_request:
                    st.session_state.response_source = "existing preview"
                    st.session_state.page = "output"
                    st.rerun()
                with st.status("Host Agent is orchestrating the team", expanded=True) as run_status:
                    st.write("Interpreting intent, entities, constraints, and ambiguity")
                    st.write("Planning subtasks and selecting specialist roles")
                    st.write("Generating, reviewing, and synthesizing the preview")
                    result_value, was_cached, local_count = run_agents(prompt)
                    st.session_state.result = result_value
                    st.session_state.original_request = prompt
                    st.session_state.accepted = False
                    st.session_state.revision_count = 0
                    st.session_state.revision_mode = False
                    st.session_state.response_source = "local cache" if was_cached else "Gemini API"
                    st.session_state.local_requests_today = local_count
                    run_status.update(label="Preview ready", state="complete", expanded=False)
                st.session_state.page = "output"
                st.rerun()
            except Exception as exc:
                show_run_error(exc)

result = st.session_state.get("result")
if result:
    roles = list(dict.fromkeys(task.assigned_role for task in result.plan.tasks))
    accepted = bool(st.session_state.get("accepted"))
    st.markdown(
        f"""
        <div class="maf-workspace-head">
          <div><div class="maf-eyebrow">Current run · {escape(st.session_state.get('response_source', 'Gemini API'))}</div>
          <h2>{'Approved content' if accepted else 'Review the preview'}</h2></div>
          <div class="maf-live"><i></i>{'Finalized' if accepted else 'Awaiting your decision'}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    metrics = st.columns(4)
    metrics[0].metric("Interpreted intent", result.analysis.intent.replace("_", " ").title())
    metrics[1].metric("Specialists", len(roles))
    review_label = "Initial review score" if st.session_state.get("revision_count", 0) else "Reviewer score"
    metrics[2].metric(review_label, f"{result.review.score}/10")
    metrics[3].metric(
        "Local API calls today",
        st.session_state.get("local_requests_today", "—"),
        help="Successful uncached Gemini calls made by this app today. Google AI Studio is the authoritative quota source.",
    )
    badges = "".join(f'<span class="maf-role">{escape(role)}</span>' for role in roles)
    st.markdown(f'<div class="maf-role-row">{badges}</div>', unsafe_allow_html=True)

    preview_tab, plan_tab, language_tab, review_tab = st.tabs(
        ["Content", "Agent map", "Language trace", "Quality review"]
    )
    with preview_tab:
        output = st.session_state.get("final_output", result.final_answer) if accepted else result.final_answer
        with st.container(key="output_content"):
            st.markdown(output)

        if not accepted:
            st.markdown(
                """
                <section class="maf-decision-head">
                  <div class="maf-kicker">Your decision</div>
                  <h3>Keep it, or shape it further.</h3>
                  <p>Approve this version when it is ready. Otherwise, give the Revision Agent a clear direction.</p>
                </section>
                """,
                unsafe_allow_html=True,
            )
            accept_col, revise_col = st.columns(2)
            with accept_col:
                st.markdown('<div class="maf-action-label"><span>01</span>Finalise this version</div>', unsafe_allow_html=True)
            with revise_col:
                st.markdown('<div class="maf-action-label"><span>02</span>Ask for changes</div>', unsafe_allow_html=True)
            if accept_col.button("Approve content", key="accept_artifact", type="primary", use_container_width=True):
                st.session_state.accepted = True
                st.session_state.final_output = result.final_answer
                st.session_state.revision_mode = False
                st.rerun()
            if revise_col.button("Revise content", key="open_revision", use_container_width=True):
                st.session_state.revision_mode = True
                st.rerun()

            if st.session_state.get("revision_mode", False):
                st.markdown(
                    """
                    <section class="maf-revision-head">
                      <div class="maf-kicker">Revision brief</div>
                      <h3>Tell the team what to change.</h3>
                      <p>Be specific about tone, structure, detail, or format. Your original goal remains in context.</p>
                    </section>
                    """,
                    unsafe_allow_html=True,
                )
                feedback = st.text_area(
                    "Revision direction",
                    key="revision_feedback",
                    height=118,
                    placeholder="For example: make the tone warmer, cut it to 150 words, and add a stronger ending.",
                )
                cancel_col, send_col = st.columns([1, 2])
                if cancel_col.button("Cancel", key="cancel_revision", use_container_width=True):
                    st.session_state.revision_mode = False
                    st.rerun()
                if send_col.button("Send revision  →", key="send_revision", type="primary", use_container_width=True):
                    if feedback.strip():
                        try:
                            with st.spinner("Revision Agent is refining the content…"):
                                revised_output, was_cached, local_count = revise_artifact(
                                    st.session_state.original_request,
                                    result.final_answer,
                                    feedback.strip(),
                                )
                                result.final_answer = revised_output
                                st.session_state.result = result
                                st.session_state.revision_count += 1
                                st.session_state.response_source = "local cache" if was_cached else "Gemini API"
                                st.session_state.local_requests_today = local_count
                                st.session_state.revision_mode = False
                            st.rerun()
                        except Exception as exc:
                            show_run_error(exc)
                    else:
                        st.warning("Add revision directions first.")
        else:
            st.success("Content approved")
            download_col, new_col = st.columns(2)
            with download_col:
                with st.popover("Download content", use_container_width=True):
                    st.markdown('<div class="maf-menu-kicker">CHOOSE A FORMAT</div>', unsafe_allow_html=True)
                    st.download_button(
                        "Markdown (.md)", output, "maf-approved-output.md", "text/markdown",
                        key="download_content_markdown", use_container_width=True,
                    )
                    plain_text = output.replace("**", "").replace("### ", "")
                    st.download_button(
                        "Plain text (.txt)", plain_text, "maf-approved-output.txt", "text/plain",
                        key="download_content_text", use_container_width=True,
                    )
                    st.download_button(
                        "PDF (.pdf)", build_artifact_pdf(output), "maf-approved-output.pdf", "application/pdf",
                        key="download_content_pdf", use_container_width=True,
                    )
            if new_col.button("Start another task", use_container_width=True):
                reset_run()
                st.session_state.page = "chat"
                st.rerun()
            with st.expander("Read aloud"):
                render_tts(output)

    with plan_tab:
        st.caption("The Host created this hierarchy and allocated each bounded task to a specialist.")
        for task in result.plan.tasks:
            deps = ", ".join(task.dependencies) or "No dependencies"
            st.markdown(
                f"""
                <div class="maf-task-row">
                  <div class="maf-task-id">{escape(humanize_task_id(task.id))}</div>
                  <div><div class="maf-task-role">{escape(task.assigned_role)}</div><small>{escape(task.title)}</small></div>
                  <div class="maf-task-objective">{escape(task.objective)}<br><small>{escape(deps)}</small></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with st.expander("Communication trace"):
            for message in result.messages:
                st.markdown(
                    f'<div class="maf-trace"><strong>{escape(message.sender)} → {escape(message.receiver)}</strong><br><small>{escape(message.human_summary)}</small></div>',
                    unsafe_allow_html=True,
                )

    with language_tab:
        st.caption("This is the observable Speech & Language Processing layer. It shows extracted structure, not private model reasoning.")
        st.markdown("#### Normalized request")
        st.write(result.analysis.normalized_text)
        left, right = st.columns(2)
        with left:
            st.markdown("#### Meaning extracted")
            st.write("**Intent**", result.analysis.intent.replace("_", " "))
            st.write("**Entities**", result.analysis.entities or "None explicitly stated")
            st.write("**Key phrases**", result.analysis.key_phrases)
        with right:
            st.markdown("#### Communication constraints")
            st.json(result.analysis.constraints.model_dump())
        with st.expander("Semantic frame"):
            st.json(result.analysis.semantic_frame)
        if result.analysis.ambiguities:
            st.warning(result.analysis.ambiguities[0].question)

    with review_tab:
        if st.session_state.get("revision_count", 0):
            st.info("To conserve free-tier quota, focused revisions do not rerun the full Reviewer Agent. The score below belongs to the initial preview.")
        decision = "Approved by the Reviewer Agent" if result.review.approved else "Revision recommended"
        st.markdown(f"### {decision}")
        st.progress(result.review.score / 10)
        left, right = st.columns(2)
        with left:
            st.markdown("#### Strengths")
            for strength in result.review.strengths:
                st.write("✓", strength)
        with right:
            st.markdown("#### Issues")
            if result.review.issues:
                for issue in result.review.issues:
                    st.write("•", issue)
            else:
                st.write("No blocking issues found.")

st.markdown(
    '<div class="maf-footer">TASKLOOM · Hierarchical task decomposition · Structured agent communication · Natural language generation</div>',
    unsafe_allow_html=True,
)
