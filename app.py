import streamlit as st
import pandas as pd
import sqlite3
import os
import re
import traceback
from io import StringIO

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PAGE CONFIG  (must be the very first Streamlit call)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.set_page_config(
    page_title="AI SQL Data Analyst",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SAFE IMPORTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_OK = True
except ImportError:
    PLOTLY_OK = False

try:
    from groq import Groq
    GROQ_OK = True
except ImportError:
    GROQ_OK = False

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CUSTOM CSS — dark cyberpunk theme
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;1,400&display=swap');

:root {
    --bg:       #07090f;
    --surface:  #0f1623;
    --surface2: #161f30;
    --surface3: #1c2840;
    --accent:   #00e5ff;
    --accent2:  #7c3aed;
    --accent3:  #f472b6;
    --success:  #10b981;
    --warn:     #f59e0b;
    --danger:   #ef4444;
    --text:     #e2e8f0;
    --muted:    #64748b;
    --border:   #1e2d45;
    --radius:   14px;
    --glow:     0 0 20px rgba(0,229,255,.18);
}

/* ── Base ── */
html, body, [data-testid="stAppViewContainer"],
[data-testid="stMain"], .main {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] * { color: var(--text) !important; }
[data-testid="stSidebar"] input {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
}

/* ── Headers ── */
h1, h2, h3, h4 {
    font-family: 'Space Mono', monospace !important;
    letter-spacing: -.02em;
}

/* ── Metrics ── */
[data-testid="stMetricValue"] {
    font-family: 'Space Mono', monospace !important;
    color: var(--accent) !important;
    font-size: 1.65rem !important;
    text-shadow: var(--glow);
}
[data-testid="stMetricLabel"] { color: var(--muted) !important; font-size:.8rem !important; }
[data-testid="stMetric"] {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 1rem !important;
}

/* ── Inputs ── */
.stTextInput input, .stTextArea textarea {
    background: var(--surface2) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(0,229,255,.12) !important;
    outline: none !important;
}

/* ── Primary Button ── */
.stButton > button {
    background: linear-gradient(135deg, var(--accent2) 0%, var(--accent) 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: var(--radius) !important;
    font-family: 'Space Mono', monospace !important;
    font-weight: 700 !important;
    font-size: .82rem !important;
    padding: .55rem 1.4rem !important;
    transition: all .2s ease !important;
    letter-spacing: .03em;
}
.stButton > button:hover {
    opacity: .85 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(0,229,255,.25) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* ── SQL block ── */
.sql-block {
    background: var(--surface2);
    border-left: 3px solid var(--accent);
    border-radius: var(--radius);
    padding: 1rem 1.25rem;
    font-family: 'Space Mono', monospace;
    font-size: .8rem;
    color: #a5f3fc;
    overflow-x: auto;
    white-space: pre-wrap;
    word-break: break-word;
    margin: .4rem 0 1rem;
    line-height: 1.6;
}

/* ── Answer card ── */
.answer-card {
    background: linear-gradient(135deg, rgba(0,229,255,.05) 0%, rgba(124,58,237,.06) 100%);
    border: 1px solid rgba(0,229,255,.22);
    border-radius: var(--radius);
    padding: 1.1rem 1.4rem;
    margin: .4rem 0 1rem;
    line-height: 1.7;
    font-size: .95rem;
}

/* ── Info / status pills ── */
.pill {
    display: inline-flex; align-items: center; gap: .35rem;
    padding: .25rem .8rem;
    border-radius: 999px;
    font-size: .72rem;
    font-family: 'Space Mono', monospace;
    font-weight: 700;
    letter-spacing: .04em;
}
.pill-ok   { background: rgba(16,185,129,.12); color: #10b981; border: 1px solid #10b981; }
.pill-err  { background: rgba(239,68,68,.12);  color: #ef4444; border: 1px solid #ef4444; }
.pill-warn { background: rgba(245,158,11,.12); color: #f59e0b; border: 1px solid #f59e0b; }
.pill-info { background: rgba(0,229,255,.10);  color: #00e5ff; border: 1px solid #00e5ff; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--surface) !important;
    border-radius: var(--radius) var(--radius) 0 0 !important;
    padding: .2rem .4rem 0 !important;
    gap: .1rem !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Space Mono', monospace !important;
    font-size: .78rem !important;
    color: var(--muted) !important;
    padding: .55rem 1rem !important;
    border-radius: 8px 8px 0 0 !important;
}
.stTabs [aria-selected="true"] {
    color: var(--accent) !important;
    background: var(--surface2) !important;
    border-bottom: 2px solid var(--accent) !important;
}
.stTabs [data-baseweb="tab-panel"] {
    background: var(--surface2) !important;
    border-radius: 0 var(--radius) var(--radius) var(--radius) !important;
    padding: 1.5rem !important;
    border: 1px solid var(--border) !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    border: 2px dashed var(--border) !important;
    border-radius: var(--radius) !important;
    background: var(--surface2) !important;
    padding: .5rem !important;
    transition: border-color .2s;
}
[data-testid="stFileUploader"]:hover { border-color: var(--accent) !important; }

/* ── Selectbox ── */
[data-testid="stSelectbox"] > div > div {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    color: var(--text) !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
}
[data-testid="stExpander"] summary { color: var(--muted) !important; }

/* ── Alert / info boxes ── */
[data-testid="stAlert"] {
    border-radius: var(--radius) !important;
    border: 1px solid var(--border) !important;
}

/* ── Divider ── */
hr { border-color: var(--border) !important; margin: 1.2rem 0 !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent2); }

/* ── Suggestion button pill style ── */
.sug-btn > button {
    background: var(--surface3) !important;
    border: 1px solid var(--border) !important;
    color: var(--muted) !important;
    font-size: .75rem !important;
    font-family: 'DM Sans', sans-serif !important;
    padding: .35rem .8rem !important;
    border-radius: 999px !important;
    font-weight: 400 !important;
}
.sug-btn > button:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
    background: rgba(0,229,255,.05) !important;
    transform: none !important;
    box-shadow: none !important;
}

/* ── Hero gradient text ── */
.hero-title {
    font-family: 'Space Mono', monospace;
    font-size: 2.1rem;
    font-weight: 700;
    background: linear-gradient(90deg, #00e5ff 0%, #7c3aed 60%, #f472b6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    line-height: 1.2;
}
.hero-sub {
    color: #475569;
    font-size: .92rem;
    margin-top: .35rem;
    font-family: 'DM Sans', sans-serif;
}

/* ── Feature card ── */
.feat-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.5rem;
    height: 100%;
    transition: border-color .2s, box-shadow .2s;
}
.feat-card:hover {
    border-color: var(--accent);
    box-shadow: 0 4px 24px rgba(0,229,255,.08);
}
.feat-icon { font-size: 2rem; margin-bottom: .6rem; }
.feat-title {
    font-family: 'Space Mono', monospace;
    font-size: .88rem;
    font-weight: 700;
    margin-bottom: .4rem;
}
.feat-desc { color: var(--muted); font-size: .84rem; line-height: 1.55; }
</style>
""", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CORE HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@st.cache_data(show_spinner=False)
def load_csv(file_bytes: bytes, _filename: str) -> pd.DataFrame:
    return pd.read_csv(StringIO(file_bytes.decode("utf-8", errors="replace")))


def df_to_sqlite(df: pd.DataFrame, table_name: str = "data") -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    return conn


def get_schema(conn: sqlite3.Connection, table: str) -> str:
    cur = conn.execute(f"PRAGMA table_info({table})")
    cols = cur.fetchall()
    lines = [f"  {c[1]}  ({c[2]})" for c in cols]
    return f"Table: {table}\nColumns:\n" + "\n".join(lines)


def run_sql(conn: sqlite3.Connection, query: str) -> pd.DataFrame:
    return pd.read_sql_query(query, conn)


def build_sql_prompt(question: str, schema: str, sample_csv: str, table: str) -> str:
    return f"""You are an expert SQLite analyst.

TABLE SCHEMA:
{schema}

SAMPLE DATA (first 3 rows as CSV):
{sample_csv}

STRICT RULES:
1. Output ONLY the raw SQL query — zero markdown, zero backticks, zero explanation.
2. Table name is exactly: {table}
3. SQLite syntax only.
4. Always add column aliases for aggregates (e.g. AS total_sales).
5. If impossible to answer, output: SELECT 'Cannot answer this with SQL.' AS message;

QUESTION: {question}

SQL:"""


def build_answer_prompt(question: str, result_csv: str) -> str:
    return f"""The user asked: "{question}"

The SQL query returned this data:
{result_csv}

Write a concise 1-3 sentence plain-English insight. Be specific with numbers.
No markdown, no SQL, no bullet points — just a clean paragraph."""


def call_groq_llm(api_key: str, prompt: str, model: str) -> str:
    client = Groq(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=512,
    )
    return resp.choices[0].message.content.strip()


def clean_sql(raw: str) -> str:
    """Strip markdown fences and take the first SQL statement."""
    raw = re.sub(r"```(?:sql)?", "", raw, flags=re.IGNORECASE)
    raw = raw.strip().strip("`").strip()
    stmts = [s.strip() for s in raw.split(";") if s.strip()]
    return (stmts[0] + ";") if stmts else raw


def auto_chart(df: pd.DataFrame, question: str):
    """Return a Plotly figure auto-selected from df shape + question keywords."""
    if not PLOTLY_OK or df is None or df.empty:
        return None

    q          = question.lower()
    num_cols   = df.select_dtypes(include="number").columns.tolist()
    cat_cols   = df.select_dtypes(exclude="number").columns.tolist()
    time_hints = [c for c in df.columns
                  if any(k in c.lower() for k in ["date","year","month","time","day","week"])]

    PALETTE = ["#00e5ff","#7c3aed","#f472b6","#10b981","#f59e0b"]

    try:
        fig = None

        if df.shape[1] == 1:
            col = df.columns[0]
            fig = px.histogram(df, x=col, title=f"Distribution — {col}",
                               color_discrete_sequence=[PALETTE[0]])

        elif cat_cols and num_cols:
            x_cat, y_num = cat_cols[0], num_cols[0]
            if any(k in q for k in ["pie","share","portion","proportion","percent","breakdown"]):
                fig = px.pie(df.head(12), names=x_cat, values=y_num,
                             title=f"{y_num} breakdown by {x_cat}",
                             color_discrete_sequence=PALETTE)
            elif time_hints:
                fig = px.line(df, x=time_hints[0], y=y_num,
                              title=f"{y_num} over time",
                              markers=True,
                              color_discrete_sequence=[PALETTE[0]])
            elif any(k in q for k in ["scatter","correlation","vs","versus","compare"]) and len(num_cols) >= 2:
                fig = px.scatter(df, x=num_cols[0], y=num_cols[1],
                                 title=f"{num_cols[1]} vs {num_cols[0]}",
                                 color_discrete_sequence=[PALETTE[1]])
            else:
                fig = px.bar(df.head(30), x=x_cat, y=y_num,
                             title=f"{y_num} by {x_cat}",
                             color=y_num, color_continuous_scale="teal",
                             text_auto=".2s")

        elif len(num_cols) >= 2:
            fig = px.scatter(df, x=num_cols[0], y=num_cols[1],
                             title=f"{num_cols[1]} vs {num_cols[0]}",
                             color_discrete_sequence=[PALETTE[1]])

        else:
            fig = px.bar(df.head(30), title="Query Results",
                         color_discrete_sequence=[PALETTE[0]])

        if fig:
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#cbd5e1", family="DM Sans", size=12),
                title_font=dict(family="Space Mono", size=13, color="#00e5ff"),
                xaxis=dict(gridcolor="#1e2d45", linecolor="#1e2d45",
                           tickfont=dict(color="#64748b")),
                yaxis=dict(gridcolor="#1e2d45", linecolor="#1e2d45",
                           tickfont=dict(color="#64748b")),
                legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#1e2d45"),
                margin=dict(l=10, r=10, t=50, b=10),
                hoverlabel=dict(bgcolor="#0f1623", bordercolor="#1e2d45",
                                font=dict(color="#e2e8f0", family="Space Mono")),
            )
        return fig

    except Exception:
        return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SIDEBAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with st.sidebar:
    st.markdown("""
    <div style="padding:.4rem 0 1.2rem">
      <div style="font-family:'Space Mono',monospace;font-size:1.05rem;
                  color:#00e5ff;font-weight:700;letter-spacing:.05em;">
        🧠 AI SQL ANALYST
      </div>
      <div style="color:#334155;font-size:.72rem;margin-top:.2rem;">
        CSV → SQL → Insights
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Groq API Key ──────────────────────────────────────────────────────────
    st.markdown("**🔑 Groq API Key**")
    st.markdown(
        '<div style="color:#64748b;font-size:.75rem;margin-bottom:.4rem;">'
        'Free key at <a href="https://console.groq.com" target="_blank" '
        'style="color:#00e5ff;">console.groq.com</a></div>',
        unsafe_allow_html=True,
    )

    # Read from st.secrets if deployed (optional), else from text_input
    default_key = ""
    try:
        default_key = st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        pass

    groq_key = st.text_input(
        "Groq API Key",
        value=default_key,
        type="password",
        placeholder="gsk_...",
        label_visibility="collapsed",
    )

    if groq_key:
        st.markdown('<div style="margin:.3rem 0"><span class="pill pill-ok">✓ Key loaded</span></div>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<div style="margin:.3rem 0"><span class="pill pill-warn">⚠ Key required</span></div>',
                    unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Model picker ──────────────────────────────────────────────────────────
    st.markdown("**🤖 LLM Model**")
    model_options = {
        "Llama 3.3 70B (Recommended)": "llama-3.3-70b-versatile",
        "Llama 3.1 8B (Fastest)":      "llama-3.1-8b-instant",
        "Mixtral 8x7B":                "mixtral-8x7b-32768",
        "Gemma 2 9B":                  "gemma2-9b-it",
    }
    model_label = st.selectbox(
        "Model", list(model_options.keys()), label_visibility="collapsed"
    )
    model = model_options[model_label]

    st.markdown("<br>", unsafe_allow_html=True)

    # ── CSV Upload ────────────────────────────────────────────────────────────
    st.markdown("**📂 Upload Your CSV**")
    uploaded_file = st.file_uploader(
        "CSV file",
        type=["csv"],
        label_visibility="collapsed",
        help="Any CSV file — sales, logs, surveys, etc.",
    )

    st.markdown("---")
    st.markdown("""
<div style="color:#334155;font-size:.73rem;line-height:1.8;">
<b style="color:#475569">HOW IT WORKS</b><br>
① Upload CSV<br>
② Data → SQLite DB<br>
③ Ask in plain English<br>
④ LLM → SQL query<br>
⑤ Execute → Answer + Chart
</div>
""", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SESSION STATE INIT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
for key, val in [
    ("conn",       None),
    ("df",         None),
    ("schema",     None),
    ("table_name", "data"),
    ("history",    []),
    ("last_q",     ""),
]:
    if key not in st.session_state:
        st.session_state[key] = val


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  LOAD CSV WHEN UPLOADED
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if uploaded_file is not None:
    try:
        file_bytes = uploaded_file.read()
        df = load_csv(file_bytes, uploaded_file.name)
        raw_name = os.path.splitext(uploaded_file.name)[0]
        tname    = re.sub(r"\W+", "_", raw_name).lower().strip("_") or "data"

        st.session_state.df         = df
        st.session_state.conn       = df_to_sqlite(df, tname)
        st.session_state.schema     = get_schema(st.session_state.conn, tname)
        st.session_state.table_name = tname
    except Exception as e:
        st.error(f"❌ Failed to load CSV: {e}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  HERO HEADER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("""
<div style="padding:.4rem 0 .2rem">
  <p class="hero-title">AI SQL Data Analyst Agent</p>
  <p class="hero-sub">Upload any CSV · Ask in plain English · Get SQL + Answer + Chart instantly</p>
</div>
""", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MAIN CONTENT — with data
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if st.session_state.df is not None:
    df     = st.session_state.df
    conn   = st.session_state.conn
    schema = st.session_state.schema
    tname  = st.session_state.table_name

    tab_ask, tab_data, tab_schema, tab_hist = st.tabs([
        "💬  Ask a Question",
        "📊  Data Preview",
        "🗂  Schema",
        "🕒  History",
    ])

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 1 — ASK A QUESTION
    # ══════════════════════════════════════════════════════════════════════════
    with tab_ask:

        # Metrics row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Rows",    f"{df.shape[0]:,}")
        m2.metric("Columns", df.shape[1])
        m3.metric("Table",   tname)
        m4.metric("Queries run", len(st.session_state.history))

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Suggestion chips ──────────────────────────────────────────────────
        st.markdown(
            '<div style="color:#475569;font-size:.78rem;margin-bottom:.5rem;">'
            '💡 <b>Quick starts</b></div>',
            unsafe_allow_html=True,
        )

        SUGGESTIONS = [
            f"Show the first 10 rows from {tname}",
            "How many total records are there?",
            "Show top 10 rows sorted by the first numeric column descending",
            "What are the unique values and their counts for the first text column?",
            "Show average and sum of all numeric columns",
            "Which row has the maximum value in the first numeric column?",
        ]

        chosen = None
        cols_sug = st.columns(3)
        for i, sug in enumerate(SUGGESTIONS):
            with cols_sug[i % 3]:
                st.markdown('<div class="sug-btn">', unsafe_allow_html=True)
                if st.button(sug[:48] + ("…" if len(sug) > 48 else ""), key=f"sug_{i}"):
                    chosen = sug
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Question input ────────────────────────────────────────────────────
        question = st.text_area(
            "Your question",
            value=chosen if chosen else st.session_state.last_q,
            placeholder="e.g. What are the top 5 products by total revenue?",
            height=95,
            label_visibility="collapsed",
        )

        btn_col, _ = st.columns([1, 4])
        run_btn = btn_col.button("🚀  Run Analysis", use_container_width=True)

        # ── Validation warnings ───────────────────────────────────────────────
        if run_btn and not question.strip():
            st.warning("Please type a question first.")
            run_btn = False
        if run_btn and not groq_key:
            st.error("❌ Add your Groq API key in the sidebar.")
            run_btn = False
        if run_btn and not GROQ_OK:
            st.error("❌ `groq` package missing. Check requirements.txt.")
            run_btn = False

        # ── Run pipeline ──────────────────────────────────────────────────────
        if run_btn and question.strip() and groq_key:
            st.session_state.last_q = question

            with st.spinner("🧠 Generating SQL…"):
                try:
                    sample_csv  = df.head(3).to_csv(index=False)
                    sql_prompt  = build_sql_prompt(question, schema, sample_csv, tname)
                    raw_sql     = call_groq_llm(groq_key, sql_prompt, model)
                    sql_query   = clean_sql(raw_sql)
                except Exception as e:
                    st.error(f"LLM error: {e}")
                    sql_query = None

            if sql_query:
                with st.spinner("⚡ Executing query…"):
                    try:
                        result_df = run_sql(conn, sql_query)
                        exec_ok   = True
                    except Exception as e:
                        st.error(f"SQL execution error: {e}")
                        st.markdown(f'<div class="sql-block">{sql_query}</div>',
                                    unsafe_allow_html=True)
                        exec_ok = False
                        result_df = None

                if exec_ok and result_df is not None:
                    with st.spinner("✍️ Writing insight…"):
                        try:
                            ans_prompt = build_answer_prompt(
                                question, result_df.head(20).to_csv(index=False)
                            )
                            answer = call_groq_llm(groq_key, ans_prompt, model)
                        except Exception:
                            answer = f"Query returned {len(result_df)} row(s)."

                    # Save to history
                    st.session_state.history.append({
                        "question": question,
                        "sql":      sql_query,
                        "answer":   answer,
                        "df":       result_df.copy(),
                        "model":    model_label,
                    })

                    # ── Results layout ────────────────────────────────────────
                    st.markdown("<hr>", unsafe_allow_html=True)

                    left, right = st.columns([1, 1], gap="large")

                    with left:
                        st.markdown("#### 📝 Generated SQL")
                        st.markdown(f'<div class="sql-block">{sql_query}</div>',
                                    unsafe_allow_html=True)

                        st.markdown("#### 💬 Answer")
                        st.markdown(f'<div class="answer-card">{answer}</div>',
                                    unsafe_allow_html=True)

                        st.markdown("#### 📋 Result Table")
                        st.dataframe(
                            result_df,
                            use_container_width=True,
                            height=min(240, 38 + len(result_df) * 35),
                        )
                        st.markdown(
                            f'<div style="color:#334155;font-size:.72rem;'
                            f'margin-top:.3rem;">{len(result_df):,} row(s) returned</div>',
                            unsafe_allow_html=True,
                        )

                    with right:
                        st.markdown("#### 📊 Visualization")
                        fig = auto_chart(result_df, question)
                        if fig:
                            st.plotly_chart(fig, use_container_width=True,
                                            config={"displayModeBar": False})
                        else:
                            st.markdown("""
<div style="background:var(--surface3,#1c2840);border:1px dashed #1e2d45;
border-radius:14px;padding:2.5rem;text-align:center;color:#334155;">
  <div style="font-size:2rem">📉</div>
  <div style="font-size:.82rem;margin-top:.5rem">
    No chart suitable for this result shape
  </div>
</div>""", unsafe_allow_html=True)

                        # Download button
                        st.markdown("<br>", unsafe_allow_html=True)
                        csv_bytes = result_df.to_csv(index=False).encode()
                        st.download_button(
                            label="⬇️  Download Results CSV",
                            data=csv_bytes,
                            file_name="query_results.csv",
                            mime="text/csv",
                            use_container_width=True,
                        )

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 2 — DATA PREVIEW
    # ══════════════════════════════════════════════════════════════════════════
    with tab_data:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Rows",    f"{df.shape[0]:,}")
        m2.metric("Columns", df.shape[1])
        m3.metric("Nulls",   f"{df.isnull().sum().sum():,}")
        m4.metric("Size",    f"{df.memory_usage(deep=True).sum()/1024:.1f} KB")

        st.markdown("<br>", unsafe_allow_html=True)
        st.dataframe(df.head(100), use_container_width=True, height=380)

        with st.expander("📈 Descriptive Statistics"):
            st.dataframe(df.describe(include="all").T.round(3),
                         use_container_width=True)

        with st.expander("🔍 Null / Missing Values"):
            null_df = df.isnull().sum().reset_index()
            null_df.columns = ["Column", "Null Count"]
            null_df["Null %"] = (null_df["Null Count"] / len(df) * 100).round(1)
            null_df = null_df[null_df["Null Count"] > 0]
            if null_df.empty:
                st.success("✅ No null values found!")
            else:
                st.dataframe(null_df, use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 3 — SCHEMA
    # ══════════════════════════════════════════════════════════════════════════
    with tab_schema:
        st.markdown("**SQLite Schema**")
        st.markdown(f'<div class="sql-block">{schema}</div>',
                    unsafe_allow_html=True)

        st.markdown("**Column Types**")
        dtype_df = pd.DataFrame({
            "Column":   df.columns,
            "Pandas dtype": df.dtypes.astype(str).values,
            "SQLite type": [
                "REAL" if str(t).startswith("float") else
                "INTEGER" if str(t).startswith("int") else "TEXT"
                for t in df.dtypes
            ],
            "Non-null": df.notna().sum().values,
            "Unique":   [df[c].nunique() for c in df.columns],
        })
        st.dataframe(dtype_df, use_container_width=True)

        st.markdown("**Quick SELECT preview**")
        preview_q = f"SELECT * FROM {tname} LIMIT 5;"
        st.markdown(f'<div class="sql-block">{preview_q}</div>',
                    unsafe_allow_html=True)
        st.dataframe(run_sql(conn, preview_q), use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 4 — HISTORY
    # ══════════════════════════════════════════════════════════════════════════
    with tab_hist:
        if not st.session_state.history:
            st.info("No queries yet — ask your first question in the ✦ Ask tab!")
        else:
            hcol1, hcol2 = st.columns([3, 1])
            hcol1.markdown(
                f'<span class="pill pill-info">{len(st.session_state.history)} queries</span>',
                unsafe_allow_html=True,
            )
            if hcol2.button("🗑 Clear History"):
                st.session_state.history = []
                st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)

            for item in reversed(st.session_state.history):
                idx = st.session_state.history.index(item) + 1
                with st.expander(f"#{idx}  {item['question'][:90]}"):
                    st.markdown(
                        f'<span class="pill pill-info">{item.get("model","")}</span>',
                        unsafe_allow_html=True,
                    )
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("**SQL Query:**")
                    st.markdown(f'<div class="sql-block">{item["sql"]}</div>',
                                unsafe_allow_html=True)
                    st.markdown("**Answer:**")
                    st.markdown(f'<div class="answer-card">{item["answer"]}</div>',
                                unsafe_allow_html=True)
                    st.dataframe(item["df"], use_container_width=True,
                                 height=min(200, 38 + len(item["df"]) * 34))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  LANDING — no CSV yet
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
else:
    st.markdown("""
<div style="text-align:center;padding:3rem 1rem 2rem">
  <div style="font-size:3.5rem;margin-bottom:.8rem">📁</div>
  <h2 style="font-family:'Space Mono',monospace;color:#00e5ff;margin-bottom:.5rem;">
    Upload a CSV to begin
  </h2>
  <p style="color:#475569;max-width:480px;margin:0 auto;font-size:.9rem;line-height:1.65;">
    Use the sidebar to upload any CSV file — sales data, logs, survey results,
    financial records, anything. Then ask questions in plain English.
  </p>
</div>
""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3, gap="medium")
    CARDS = [
        ("📤", "#00e5ff", "1. Upload CSV",
         "Drop any .csv file in the sidebar — no size limit, any structure."),
        ("🔑", "#7c3aed", "2. Add API Key",
         "Get a free Groq key at console.groq.com. Paste it in the sidebar."),
        ("💬", "#f472b6", "3. Ask Anything",
         "Type questions like 'Top 10 by sales' and get SQL + chart instantly."),
    ]
    for col, (icon, color, title, desc) in zip([c1, c2, c3], CARDS):
        col.markdown(f"""
<div class="feat-card">
  <div class="feat-icon">{icon}</div>
  <div class="feat-title" style="color:{color};">{title}</div>
  <div class="feat-desc">{desc}</div>
</div>""", unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # Show example
    with st.expander("💡 What kind of questions can I ask?"):
        examples = [
            ("Sales data",     "What are the top 5 products by total revenue?"),
            ("User logs",      "How many unique users visited each day last week?"),
            ("HR data",        "What is the average salary by department?"),
            ("E-commerce",     "Which country has the highest number of orders?"),
            ("Finance",        "Show monthly trend of profit for 2023"),
            ("Any dataset",    "Which rows have missing values?"),
        ]
        for category, q in examples:
            st.markdown(
                f'<div style="padding:.35rem 0;border-bottom:1px solid #1e2d45;">'
                f'<span style="color:#475569;font-size:.75rem;font-family:Space Mono,monospace;">'
                f'{category}</span><br>'
                f'<span style="color:#cbd5e1;font-size:.88rem;">{q}</span></div>',
                unsafe_allow_html=True,
            )
