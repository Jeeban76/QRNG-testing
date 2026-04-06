
import streamlit as st
import numpy as np
import pandas as pd
import sqlite3
import json
import hashlib
import os
import time
import math
import io
from datetime import datetime
from pathlib import Path
from scipy import stats
from scipy.special import erfc, gammainc
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
import base64

# ── Streamlit page config 
st.set_page_config(
    page_title="Quantum RNG Tester",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS 
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600;700&family=Syne:wght@400;600;800&display=swap');

  :root {
    --bg:       #0a0d14;
    --surface:  #0f1421;
    --card:     #141929;
    --border:   #1e2a42;
    --accent:   #00d4ff;
    --accent2:  #7c3aed;
    --accent3:  #10b981;
    --warn:     #f59e0b;
    --danger:   #ef4444;
    --text:     #e2e8f0;
    --muted:    #64748b;
  }

  html, body, [class*="css"] {
    font-family: 'JetBrains Mono', monospace;
    background-color: var(--bg);
    color: var(--text);
  }

  /* Header banner */
  .qrng-header {
    background: linear-gradient(135deg, #0f1421 0%, #1a0a2e 50%, #0a1628 100%);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
  }
  .qrng-header::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(ellipse at 30% 40%, rgba(0,212,255,0.06) 0%, transparent 60%),
                radial-gradient(ellipse at 70% 60%, rgba(124,58,237,0.06) 0%, transparent 60%);
    pointer-events: none;
  }
  .qrng-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.2rem;
    font-weight: 800;
    background: linear-gradient(90deg, #00d4ff, #7c3aed, #10b981);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
  }
  .qrng-sub {
    color: var(--muted);
    font-size: 0.82rem;
    margin-top: 0.4rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  /* Cards */
  .metric-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
  }
  .metric-card h4 {
    font-family: 'Syne', sans-serif;
    font-size: 0.75rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--muted);
    margin: 0 0 0.4rem;
  }
  .metric-card .val {
    font-size: 1.9rem;
    font-weight: 700;
    color: var(--accent);
  }
  .metric-card .val.pass  { color: var(--accent3); }
  .metric-card .val.warn  { color: var(--warn); }
  .metric-card .val.fail  { color: var(--danger); }

  /* Test result badge */
  .badge { display:inline-block; padding:2px 10px; border-radius:99px; font-size:0.73rem; font-weight:600; }
  .badge.pass { background:rgba(16,185,129,0.15); color:#10b981; border:1px solid rgba(16,185,129,0.3); }
  .badge.fail { background:rgba(239,68,68,0.15);  color:#ef4444; border:1px solid rgba(239,68,68,0.3); }

  /* Section headings */
  .sec-head {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--accent);
    border-left: 3px solid var(--accent);
    padding-left: 0.8rem;
    margin: 1.6rem 0 1rem;
    letter-spacing: 0.04em;
  }

  /* Code / hex display */
  .hex-box {
    background: #080b12;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem;
    font-size: 0.72rem;
    word-break: break-all;
    color: var(--accent3);
    line-height: 1.7;
    max-height: 200px;
    overflow-y: auto;
  }

  /* Sidebar */
  [data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border);
  }

  /* Streamlit overrides */
  .stButton>button {
    background: linear-gradient(135deg, #00d4ff22, #7c3aed22);
    border: 1px solid var(--accent);
    color: var(--accent);
    border-radius: 8px;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 600;
    letter-spacing: 0.05em;
    transition: all 0.2s;
  }
  .stButton>button:hover {
    background: linear-gradient(135deg, #00d4ff44, #7c3aed44);
    box-shadow: 0 0 20px rgba(0,212,255,0.25);
  }
  div[data-testid="stDataFrame"] { border-radius: 10px; }
  .stTabs [data-baseweb="tab-list"] { background: var(--card); border-radius: 10px; gap:4px; }
  .stTabs [data-baseweb="tab"] { color: var(--muted); border-radius:8px; font-family:'JetBrains Mono',monospace; }
  .stTabs [aria-selected="true"] { background:var(--accent2) !important; color:#fff !important; }
  .stProgress .st-bo { background: var(--accent); }
  label { color: var(--muted) !important; }
  .stSelectbox>div>div { background: var(--card); border-color: var(--border); }
  .stSlider>div>div { background: var(--border); }
  [data-testid="metric-container"] { background: var(--card); border:1px solid var(--border); border-radius:10px; padding:0.8rem; }
</style>
""", unsafe_allow_html=True)


# 
#  DATABASE LAYER
# 

DB_PATH = Path("qrng_results.db")

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS experiments (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id      TEXT    NOT NULL,
            timestamp   TEXT    NOT NULL,
            source      TEXT    NOT NULL,
            bits_length INTEGER NOT NULL,
            block_size  INTEGER,
            note        TEXT,
            config_json TEXT
        );

        CREATE TABLE IF NOT EXISTS test_results (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id        TEXT    NOT NULL,
            test_name     TEXT    NOT NULL,
            p_value       REAL,
            statistic     REAL,
            passed        INTEGER,
            details_json  TEXT,
            FOREIGN KEY (run_id) REFERENCES experiments(run_id)
        );

        CREATE TABLE IF NOT EXISTS entropy_metrics (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id      TEXT    NOT NULL,
            shannon_ent REAL,
            min_entropy REAL,
            bit_balance REAL,
            FOREIGN KEY (run_id) REFERENCES experiments(run_id)
        );

        CREATE TABLE IF NOT EXISTS derived_keys (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id      TEXT    NOT NULL,
            method      TEXT,
            key_bits    INTEGER,
            key_hex     TEXT,
            salt_hex    TEXT,
            kdf_params  TEXT,
            FOREIGN KEY (run_id) REFERENCES experiments(run_id)
        );
        """)

init_db()


def save_experiment(run_id, source, bits_length, block_size, note, config):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO experiments(run_id,timestamp,source,bits_length,block_size,note,config_json) "
            "VALUES(?,?,?,?,?,?,?)",
            (run_id, datetime.utcnow().isoformat(), source, bits_length, block_size,
             note, json.dumps(config))
        )

def save_test_result(run_id, name, p_value, statistic, passed, details=None):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO test_results(run_id,test_name,p_value,statistic,passed,details_json) "
            "VALUES(?,?,?,?,?,?)",
            (run_id, name, p_value, statistic, int(passed), json.dumps(details or {}))
        )

def save_entropy(run_id, shannon, min_ent, balance):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO entropy_metrics(run_id,shannon_ent,min_entropy,bit_balance) VALUES(?,?,?,?)",
            (run_id, shannon, min_ent, balance)
        )

def save_key(run_id, method, key_bits, key_hex, salt_hex, kdf_params):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO derived_keys(run_id,method,key_bits,key_hex,salt_hex,kdf_params) VALUES(?,?,?,?,?,?)",
            (run_id, method, key_bits, key_hex, salt_hex, json.dumps(kdf_params))
        )

def load_history():
    with get_db() as conn:
        rows = conn.execute("""
            SELECT e.run_id, e.timestamp, e.source, e.bits_length,
                   COUNT(t.id)           AS total_tests,
                   SUM(t.passed)         AS passed_tests,
                   em.shannon_ent,
                   em.min_entropy
            FROM experiments e
            LEFT JOIN test_results t   ON e.run_id = t.run_id
            LEFT JOIN entropy_metrics em ON e.run_id = em.run_id
            GROUP BY e.run_id
            ORDER BY e.timestamp DESC
            LIMIT 100
        """).fetchall()
    return [dict(r) for r in rows]

def load_run_detail(run_id):
    with get_db() as conn:
        tests = conn.execute(
            "SELECT * FROM test_results WHERE run_id=?", (run_id,)
        ).fetchall()
        keys  = conn.execute(
            "SELECT * FROM derived_keys WHERE run_id=?", (run_id,)
        ).fetchall()
        exp   = conn.execute(
            "SELECT * FROM experiments WHERE run_id=?", (run_id,)
        ).fetchone()
    return dict(exp) if exp else {}, [dict(t) for t in tests], [dict(k) for k in keys]


# ═══════════════════════════════════════════════════════════════════
#  BIT-STREAM GENERATORS
#  

def gen_prng(n: int) -> np.ndarray:
    """Cryptographically strong OS PRNG (secrets/os.urandom)."""
    raw = os.urandom(math.ceil(n / 8))
    bits = np.unpackbits(np.frombuffer(raw, dtype=np.uint8))
    return bits[:n]

def gen_biased(n: int, p: float = 0.7) -> np.ndarray:
    """Intentionally biased: P(1)=p."""
    rng = np.random.default_rng()
    return rng.choice([0, 1], size=n, p=[1 - p, p]).astype(np.uint8)

def gen_numpy_prng(n: int) -> np.ndarray:
    """NumPy Mersenne-Twister PRNG (weaker than OS)."""
    rng = np.random.default_rng(seed=None)
    return rng.integers(0, 2, size=n, dtype=np.uint8)

def gen_qiskit_sim(n: int) -> np.ndarray:
    """
    Quantum circuit simulator via Qiskit Aer.
    Each qubit measured in superposition → true quantum randomness model.
    Falls back to OS PRNG if Qiskit not installed.
    """
    try:
        from qiskit import QuantumCircuit
        from qiskit_aer import AerSimulator

        bits = []
        batch = min(n, 1024)          # measure up to 1024 qubits at once
        sim   = AerSimulator()

        while len(bits) < n:
            k   = min(batch, n - len(bits))
            qc  = QuantumCircuit(k, k)
            qc.h(range(k))
            qc.measure(range(k), range(k))
            job    = sim.run(qc, shots=1)
            result = job.result()
            counts = result.get_counts()
            bs     = list(counts.keys())[0].replace(" ", "")
            bits.extend([int(b) for b in bs[:k]])

        return np.array(bits[:n], dtype=np.uint8)

    except ImportError:
        st.warning("⚠️ Qiskit not installed — using OS PRNG as fallback for quantum source.")
        return gen_prng(n)

def gen_from_file(uploaded_file, n: int) -> np.ndarray:
    """Parse uploaded binary/text file into bits."""
    raw = uploaded_file.read()
    # Try text first
    try:
        text = raw.decode("utf-8").strip()
        bits = np.array([int(c) for c in text if c in "01"], dtype=np.uint8)
    except Exception:
        bits = np.unpackbits(np.frombuffer(raw, dtype=np.uint8))
    if len(bits) < n:
        st.error(f"File only has {len(bits)} bits, need {n}. Padding with OS PRNG.")
        bits = np.concatenate([bits, gen_prng(n - len(bits))])
    return bits[:n]


# 
#  NIST SP 800-22 STATISTICAL TESTS
# 

ALPHA = 0.01  # significance threshold

def test_monobit(bits: np.ndarray) -> dict:
    """NIST Test 1 — Frequency (Monobit)."""
    n  = len(bits)
    s  = int(np.sum(bits)) * 2 - n          # sum of (+1/-1)
    s_obs = abs(s) / math.sqrt(n)
    p  = erfc(s_obs / math.sqrt(2))
    return {
        "test": "Frequency (Monobit)",
        "statistic": round(s_obs, 6),
        "p_value":   round(float(p), 6),
        "passed":    p >= ALPHA,
        "details":   {"ones": int(np.sum(bits)), "zeros": int(n - np.sum(bits))}
    }

def test_block_frequency(bits: np.ndarray, M: int = 128) -> dict:
    """NIST Test 2 — Block Frequency."""
    n = len(bits)
    N = n // M
    if N < 1:
        return {"test": "Block Frequency", "statistic": None, "p_value": None, "passed": False,
                "details": {"error": "Sequence too short"}}
    blocks = bits[:N * M].reshape(N, M)
    pis    = blocks.mean(axis=1)
    chi_sq = 4 * M * np.sum((pis - 0.5) ** 2)
    p      = 1 - stats.chi2.cdf(chi_sq, df=N)
    return {
        "test": "Block Frequency",
        "statistic": round(float(chi_sq), 6),
        "p_value":   round(float(p), 6),
        "passed":    p >= ALPHA,
        "details":   {"blocks": N, "block_size": M}
    }

def test_runs(bits: np.ndarray) -> dict:
    """NIST Test 3 — Runs."""
    n    = len(bits)
    pi   = float(np.mean(bits))
    if abs(pi - 0.5) >= 2 / math.sqrt(n):
        return {"test": "Runs", "statistic": None, "p_value": 0.0, "passed": False,
                "details": {"note": "Pre-condition failed (|pi-0.5| >= 2/sqrt(n))", "pi": round(pi, 4)}}
    vobs = 1 + int(np.sum(bits[:-1] != bits[1:]))
    num  = abs(vobs - 2 * n * pi * (1 - pi))
    den  = 2 * math.sqrt(2 * n) * pi * (1 - pi)
    p    = erfc(num / den)
    return {
        "test": "Runs",
        "statistic": round(float(vobs), 6),
        "p_value":   round(float(p), 6),
        "passed":    p >= ALPHA,
        "details":   {"V_obs": int(vobs), "pi": round(pi, 4)}
    }

def test_longest_run(bits: np.ndarray) -> dict:
    """NIST Test 4 — Longest Run of Ones in a Block."""
    n = len(bits)
    if n < 128:
        return {"test": "Longest Run", "statistic": None, "p_value": None, "passed": False,
                "details": {"error": "Need >= 128 bits"}}
    M = 8
    N = n // M
    blocks = bits[:N * M].reshape(N, M)
    # max run of 1s in each block
    def max_run(row):
        mx = cur = 0
        for b in row:
            cur = cur + 1 if b == 1 else 0
            mx = max(mx, cur)
        return mx
    runs = np.array([max_run(b) for b in blocks])
    # NIST pi table for M=8
    pi = [0.2148, 0.3672, 0.2305, 0.1875]
    v  = np.array([np.sum(runs <= 1), np.sum(runs == 2),
                   np.sum(runs == 3), np.sum(runs >= 4)], dtype=float)
    chi_sq = np.sum((v - N * np.array(pi)) ** 2 / (N * np.array(pi)))
    p = 1 - stats.chi2.cdf(chi_sq, df=3)
    return {
        "test": "Longest Run (Ones)",
        "statistic": round(float(chi_sq), 6),
        "p_value":   round(float(p), 6),
        "passed":    p >= ALPHA,
        "details":   {"max_run_overall": int(runs.max()), "avg_max_run": round(float(runs.mean()), 2)}
    }

def test_serial(bits: np.ndarray, m: int = 3) -> dict:
    """NIST Test 11 — Serial (approximate)."""
    n = len(bits)
    if n < 2 ** m:
        return {"test": "Serial", "statistic": None, "p_value": None, "passed": False,
                "details": {"error": "Too short for serial test"}}

    def count_patterns(seq, length):
        counts = {}
        for i in range(len(seq) - length + 1):
            k = tuple(seq[i:i + length])
            counts[k] = counts.get(k, 0) + 1
        return counts

    def psi_sq(seq, length):
        counts = count_patterns(seq, length)
        total  = len(seq) - length + 1
        return (2 ** length / total) * sum(c ** 2 for c in counts.values()) - total

    psi_m   = psi_sq(bits, m)
    psi_m1  = psi_sq(bits, m - 1)
    psi_m2  = psi_sq(bits, m - 2) if m >= 2 else 0
    d1 = psi_m - psi_m1
    d2 = psi_m - 2 * psi_m1 + psi_m2
    p1 = 1 - stats.chi2.cdf(d1, df=2 ** (m - 1))
    p2 = 1 - stats.chi2.cdf(d2, df=2 ** (m - 2))
    p  = min(p1, p2)
    return {
        "test": "Serial",
        "statistic": round(float(d1), 6),
        "p_value":   round(float(p), 6),
        "passed":    p >= ALPHA,
        "details":   {"m": m, "p1": round(float(p1), 4), "p2": round(float(p2), 4)}
    }

def run_all_tests(bits: np.ndarray, block_size: int = 128) -> list[dict]:
    return [
        test_monobit(bits),
        test_block_frequency(bits, M=block_size),
        test_runs(bits),
        test_longest_run(bits),
        test_serial(bits),
    ]


# 
#  ENTROPY METRICS
# 

def shannon_entropy(bits: np.ndarray) -> float:
    p1 = float(np.mean(bits))
    p0 = 1 - p1
    if p1 == 0 or p0 == 0:
        return 0.0
    return -(p1 * math.log2(p1) + p0 * math.log2(p0))

def min_entropy(bits: np.ndarray) -> float:
    p_max = max(float(np.mean(bits)), 1 - float(np.mean(bits)))
    if p_max == 0:
        return float("inf")
    return -math.log2(p_max)

def bit_balance(bits: np.ndarray) -> float:
    return float(np.mean(bits))


# 
#  KEY DERIVATION
# 

def derive_key(bits: np.ndarray, method: str = "PBKDF2-SHA256",
               key_bits: int = 256, iterations: int = 100_000) -> dict:
    seed_bytes = np.packbits(bits).tobytes()[:64]   # use first 64 bytes as seed material
    salt       = os.urandom(32)

    if method == "PBKDF2-SHA256":
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=key_bits // 8,
            salt=salt,
            iterations=iterations,
        )
        key = kdf.derive(seed_bytes)
    elif method == "SHA-256 Hash":
        key = hashlib.sha256(seed_bytes + salt).digest()[: key_bits // 8]
    elif method == "SHA-3-256":
        key = hashlib.sha3_256(seed_bytes + salt).digest()[: key_bits // 8]
    else:
        key = hashlib.blake2b(seed_bytes + salt, digest_size=key_bits // 8).digest()

    return {
        "method":     method,
        "key_bits":   key_bits,
        "key_hex":    key.hex(),
        "salt_hex":   salt.hex(),
        "kdf_params": {"iterations": iterations} if "PBKDF2" in method else {},
    }


# 
#  PLOTLY CHARTS
# 

DARK = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="JetBrains Mono", color="#94a3b8", size=11),
    xaxis=dict(gridcolor="#1e2a42", linecolor="#1e2a42"),
    yaxis=dict(gridcolor="#1e2a42", linecolor="#1e2a42"),
    margin=dict(l=40, r=20, t=40, b=40),
)

def chart_pvalue_bar(results: list[dict]):
    tests  = [r["test"] for r in results]
    pvals  = [r["p_value"] if r["p_value"] is not None else 0 for r in results]
    colors = ["#10b981" if r["passed"] else "#ef4444" for r in results]

    fig = go.Figure(go.Bar(
        x=tests, y=pvals,
        marker_color=colors,
        text=[f"{v:.4f}" for v in pvals],
        textposition="outside",
    ))
    fig.add_hline(y=ALPHA, line_dash="dash", line_color="#f59e0b",
                  annotation_text=f"α={ALPHA}", annotation_position="top right")
    fig.update_layout(
        title="P-Values per Test", yaxis_title="P-Value", yaxis_range=[0, 1.1],
        **DARK
    )
    return fig

def chart_bit_distribution(bits: np.ndarray):
    zeros = int(np.sum(bits == 0))
    ones  = int(np.sum(bits == 1))
    fig = go.Figure(go.Pie(
        labels=["0 (Zeros)", "1 (Ones)"],
        values=[zeros, ones],
        marker=dict(colors=["#7c3aed", "#00d4ff"]),
        hole=0.45,
        textinfo="label+percent",
    ))
    fig.update_layout(title="Bit Distribution", **DARK)
    return fig

def chart_entropy_gauge(shannon: float, min_ent: float):
    fig = make_subplots(rows=1, cols=2,
                        specs=[[{"type": "indicator"}, {"type": "indicator"}]])
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=round(shannon, 4),
        title={"text": "Shannon Entropy (bits)"},
        gauge={"axis": {"range": [0, 1]},
               "bar": {"color": "#00d4ff"},
               "steps": [{"range": [0, 0.8], "color": "#1e2a42"},
                         {"range": [0.8, 0.95], "color": "rgba(124,58,237,0.2)"},
                         {"range": [0.95, 1], "color": "rgba(16,185,129,0.2)"}],
               "threshold": {"value": 0.99, "line": {"color": "#10b981", "width": 2}}},
    ), row=1, col=1)
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=round(min_ent, 4),
        title={"text": "Min-Entropy (bits)"},
        gauge={"axis": {"range": [0, 1]},
               "bar": {"color": "#7c3aed"},
               "steps": [{"range": [0, 0.8], "color": "#1e2a42"},
                         {"range": [0.8, 0.95], "color": "rgba(124,58,237,0.2)"},
                         {"range": [0.95, 1], "color": "rgba(16,185,129,0.2)"}],
               "threshold": {"value": 0.99, "line": {"color": "#10b981", "width": 2}}},
    ), row=1, col=2)
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="JetBrains Mono", color="#94a3b8"),
                      margin=dict(l=20, r=20, t=40, b=20))
    return fig

def chart_bit_sequence(bits: np.ndarray, sample: int = 500):
    sample_bits = bits[:sample]
    runs = []
    val  = None
    run  = 0
    for b in sample_bits:
        if b == val:
            run += 1
        else:
            if val is not None:
                runs.append((val, run))
            val = b
            run = 1
    if val is not None:
        runs.append((val, run))

    x, y, clr = [], [], []
    pos = 0
    for (v, r) in runs:
        x.extend([pos, pos + r])
        y.extend([v, v])
        clr.append("#00d4ff" if v == 1 else "#7c3aed")
        pos += r

    fig = go.Figure()
    pos = 0
    for (v, r) in runs:
        fig.add_trace(go.Scatter(
            x=[pos, pos + r], y=[v, v],
            mode="lines",
            line=dict(color="#00d4ff" if v == 1 else "#7c3aed", width=3),
            showlegend=False,
        ))
        pos += r
    dark_bit = {**DARK, "yaxis": {**DARK.get("yaxis", {}), "tickvals": [0, 1], "ticktext": ["0", "1"]}}
    fig.update_layout(
        title=f"Bit Sequence (first {sample})",
        **dark_bit
    )
    return fig

def chart_history_comparison(history: list[dict]):
    if not history:
        return None
    df = pd.DataFrame(history)
    df["pass_rate"] = df["passed_tests"] / df["total_tests"].replace(0, 1) * 100
    df["label"]     = df["source"] + " — " + df["timestamp"].str[:16]
    fig = px.scatter(
        df.dropna(subset=["shannon_ent", "min_entropy"]),
        x="shannon_ent", y="min_entropy",
        color="source",
        size="bits_length",
        hover_name="label",
        title="Entropy Space — All Experiments",
        labels={"shannon_ent": "Shannon Entropy", "min_entropy": "Min-Entropy"},
        color_discrete_sequence=["#00d4ff", "#7c3aed", "#10b981", "#f59e0b"],
    )
    fig.update_layout(**DARK)
    return fig

def chart_pvalue_histogram(history_runs: list[dict]):
    """P-value uniformity across all stored runs."""
    pvals = [r["p_value"] for r in history_runs if r.get("p_value") is not None]
    if not pvals:
        return None
    fig = go.Figure(go.Histogram(
        x=pvals, nbinsx=20,
        marker_color="#7c3aed",
        opacity=0.8,
    ))
    fig.update_layout(
        title="P-Value Distribution (All Stored Results)",
        xaxis_title="P-Value", yaxis_title="Count",
        **DARK
    )
    return fig


# 
#  SIDEBAR
# 

with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:1rem 0 0.5rem;">
      <span style="font-size:2.5rem;">⚛️</span>
      <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:1rem;
                  color:#00d4ff;letter-spacing:0.1em;">QRNG TESTER</div>
      <div style="color:#64748b;font-size:0.68rem;letter-spacing:0.08em;">NIST SP 800-22 SUITE</div>
    </div>
    <hr style="border-color:#1e2a42;margin:0.8rem 0;">
    """, unsafe_allow_html=True)

    st.markdown("**⚙️ Bit-Source Configuration**")

    source = st.selectbox(
        "Randomness Source",
        ["OS / Crypto PRNG", "NumPy Mersenne-Twister", "Biased Stream",
         "Qiskit Quantum Simulator", "Upload QRNG File"]
    )

    n_bits = st.select_slider(
        "Bitstream Length",
        options=[1_000, 5_000, 10_000, 50_000, 100_000],
        value=10_000,
    )

    block_size = st.slider("Block Size (NIST Block Freq)", 64, 512, 128, step=64)

    if source == "Biased Stream":
        bias_p = st.slider("P(1) — Bias Probability", 0.1, 0.9, 0.7, step=0.05)
    else:
        bias_p = 0.5

    uploaded_file = None
    if source == "Upload QRNG File":
        uploaded_file = st.file_uploader("Upload bit-file (.txt or binary)", type=["txt", "bin", "dat"])

    st.markdown("---")
    st.markdown("**🔑 Key Derivation**")

    kdf_method = st.selectbox("KDF Method",
                               ["PBKDF2-SHA256", "SHA-256 Hash", "SHA-3-256", "BLAKE2b"])
    key_bits   = st.selectbox("Key Length", [128, 192, 256, 512], index=2)
    kdf_iters  = st.slider("PBKDF2 Iterations", 10_000, 500_000, 100_000, step=10_000)

    st.markdown("---")
    run_note = st.text_input("Experiment Note (optional)", placeholder="e.g., Baseline test")

    st.markdown("---")
    st.markdown("""
    <div style="font-size:0.65rem;color:#475569;line-height:1.6;">
    <b style="color:#64748b;">NIST Tests Implemented</b><br>
    ① Frequency (Monobit)<br>
    ② Block Frequency<br>
    ③ Runs<br>
    ④ Longest Run of Ones<br>
    ⑤ Serial<br><br>
    <b style="color:#64748b;">Threshold:</b> α = 0.01<br>
    <b style="color:#64748b;">DB:</b> SQLite (local)
    </div>
    """, unsafe_allow_html=True)


# 
#  HEADER
# 

st.markdown("""
<div class="qrng-header">
  <h1 class="qrng-title">⚛ Quantum Randomness Quality Tester</h1>
  <p class="qrng-sub">NIST SP 800-22 · Qiskit · Shannon & Min-Entropy · Key Derivation · SQLite Analytics</p>
</div>
""", unsafe_allow_html=True)


# 
#  TABS
# 

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🧪 Run Test",
    "📊 Analysis",
    "🔑 Key Derivation",
    "🗄️ History & DB",
    "📖 Documentation",
])


# 
# TAB 1 — RUN TEST
# 
with tab1:
    st.markdown('<div class="sec-head">Bitstream Generation & NIST Tests</div>', unsafe_allow_html=True)

    col_cfg, col_run = st.columns([3, 1])
    with col_cfg:
        st.info(f"**Source:** {source} · **Length:** {n_bits:,} bits · **Block size:** {block_size}")
    with col_run:
        run_btn = st.button("▶ Run Full Test Suite", use_container_width=True)

    if run_btn:
        if source == "Upload QRNG File" and uploaded_file is None:
            st.error("Please upload a bit-file first.")
            st.stop()

        # ── Generate bits 
        with st.spinner("Generating bitstream…"):
            t0 = time.time()
            if source == "OS / Crypto PRNG":
                bits = gen_prng(n_bits)
            elif source == "NumPy Mersenne-Twister":
                bits = gen_numpy_prng(n_bits)
            elif source == "Biased Stream":
                bits = gen_biased(n_bits, p=bias_p)
            elif source == "Qiskit Quantum Simulator":
                bits = gen_qiskit_sim(n_bits)
            else:
                bits = gen_from_file(uploaded_file, n_bits)
            gen_time = time.time() - t0

        st.success(f"Generated {n_bits:,} bits in {gen_time:.2f}s")

        # ── Entropy 
        sh_ent  = shannon_entropy(bits)
        min_ent = min_entropy(bits)
        balance = bit_balance(bits)

        # ── NIST Tests 
        with st.spinner("Running NIST statistical tests…"):
            results = run_all_tests(bits, block_size)

        # ── Key derivation 
        key_info = derive_key(bits, method=kdf_method,
                              key_bits=key_bits, iterations=kdf_iters)

        # ── Save to DB 
        run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S_") + source[:4].replace(" ", "")
        save_experiment(run_id, source, n_bits, block_size, run_note,
                        {"bias_p": bias_p, "kdf": kdf_method})
        for r in results:
            save_test_result(run_id, r["test"], r["p_value"], r["statistic"],
                             r["passed"], r["details"])
        save_entropy(run_id, sh_ent, min_ent, balance)
        save_key(run_id, key_info["method"], key_info["key_bits"],
                 key_info["key_hex"], key_info["salt_hex"], key_info["kdf_params"])

        # ── Store in session for Analysis tab 
        st.session_state["last_bits"]    = bits
        st.session_state["last_results"] = results
        st.session_state["last_entropy"] = (sh_ent, min_ent, balance)
        st.session_state["last_run_id"]  = run_id
        st.session_state["last_key"]     = key_info

        # ── Summary cards 
        passed = sum(r["passed"] for r in results)
        total  = len(results)
        pass_rate = passed / total * 100

        c1, c2, c3, c4 = st.columns(4)
        cls = "pass" if pass_rate == 100 else ("warn" if pass_rate >= 60 else "fail")
        c1.markdown(f'<div class="metric-card"><h4>Pass Rate</h4>'
                    f'<div class="val {cls}">{pass_rate:.0f}%</div>'
                    f'<div style="color:#64748b;font-size:0.75rem">{passed}/{total} tests</div></div>',
                    unsafe_allow_html=True)
        ent_cls = "pass" if sh_ent > 0.95 else ("warn" if sh_ent > 0.8 else "fail")
        c2.markdown(f'<div class="metric-card"><h4>Shannon Entropy</h4>'
                    f'<div class="val {ent_cls}">{sh_ent:.5f}</div>'
                    f'<div style="color:#64748b;font-size:0.75rem">ideal = 1.0</div></div>',
                    unsafe_allow_html=True)
        men_cls = "pass" if min_ent > 0.95 else ("warn" if min_ent > 0.8 else "fail")
        c3.markdown(f'<div class="metric-card"><h4>Min-Entropy</h4>'
                    f'<div class="val {men_cls}">{min_ent:.5f}</div>'
                    f'<div style="color:#64748b;font-size:0.75rem">crypto critical</div></div>',
                    unsafe_allow_html=True)
        bal_cls = "pass" if 0.48 <= balance <= 0.52 else ("warn" if 0.45 <= balance <= 0.55 else "fail")
        c4.markdown(f'<div class="metric-card"><h4>Bit Balance (P₁)</h4>'
                    f'<div class="val {bal_cls}">{balance:.4f}</div>'
                    f'<div style="color:#64748b;font-size:0.75rem">ideal = 0.5</div></div>',
                    unsafe_allow_html=True)

        # ── Per-test table 
        st.markdown('<div class="sec-head">Test Results</div>', unsafe_allow_html=True)
        rows = []
        for r in results:
            status = "✅ PASS" if r["passed"] else "❌ FAIL"
            rows.append({
                "Test": r["test"],
                "Statistic": r["statistic"],
                "P-Value": r["p_value"],
                "Status": status,
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # ── Charts 
        st.markdown('<div class="sec-head">Visualisations</div>', unsafe_allow_html=True)
        vc1, vc2 = st.columns(2)
        vc1.plotly_chart(chart_pvalue_bar(results), use_container_width=True)
        vc2.plotly_chart(chart_bit_distribution(bits),  use_container_width=True)
        st.plotly_chart(chart_bit_sequence(bits, sample=500), use_container_width=True)

        st.success(f"✅ Run saved to DB — Run ID: `{run_id}`")


# 
# TAB 2 — ANALYSIS
# 
with tab2:
    st.markdown('<div class="sec-head">Entropy & Statistical Analysis</div>', unsafe_allow_html=True)

    if "last_entropy" not in st.session_state:
        st.info("Run a test first (Tab 1) to see analysis.")
    else:
        sh_ent, min_ent, balance = st.session_state["last_entropy"]
        bits    = st.session_state["last_bits"]
        results = st.session_state["last_results"]

        st.plotly_chart(chart_entropy_gauge(sh_ent, min_ent), use_container_width=True)

        # Detailed entropy table
        st.markdown('<div class="sec-head">Entropy Metrics Detail</div>', unsafe_allow_html=True)
        ent_df = pd.DataFrame([
            {"Metric": "Shannon Entropy H(X)", "Value": f"{sh_ent:.6f}", "Ideal": "1.0",
             "Formula": "H = -Σ pᵢ log₂(pᵢ)"},
            {"Metric": "Min-Entropy H∞(X)", "Value": f"{min_ent:.6f}", "Ideal": "1.0",
             "Formula": "H∞ = -log₂(max pᵢ)"},
            {"Metric": "Bit Balance P(1)", "Value": f"{balance:.6f}", "Ideal": "0.5",
             "Formula": "sum(bits)/N"},
            {"Metric": "Total Bits", "Value": f"{len(bits):,}", "Ideal": "≥ 1000", "Formula": "N"},
        ])
        st.dataframe(ent_df, use_container_width=True, hide_index=True)

        # P-value breakdown per test
        st.markdown('<div class="sec-head">P-Value Interpretation</div>', unsafe_allow_html=True)
        for r in results:
            pv = r["p_value"]
            if pv is None:
                pv_display = "N/A"
                badge = "fail"
            else:
                pv_display = f"{pv:.6f}"
                badge = "pass" if r["passed"] else "fail"

            interp = ("Strong randomness evidence" if pv and pv > 0.1 else
                      "Borderline" if pv and pv >= 0.01 else "Fail — bias detected")

            st.markdown(
                f'<div class="metric-card" style="margin-bottom:0.5rem">'
                f'<span class="badge {badge}">{("PASS" if r["passed"] else "FAIL")}</span>'
                f'&nbsp; <b>{r["test"]}</b>'
                f'<span style="float:right;color:#94a3b8">{pv_display}</span><br>'
                f'<small style="color:#64748b">{interp} · Statistic: {r["statistic"]}</small>'
                f'</div>', unsafe_allow_html=True
            )

        # Failure clustering analysis
        st.markdown('<div class="sec-head">Failure Clustering Assessment</div>', unsafe_allow_html=True)
        failed = [r for r in results if not r["passed"]]
        if not failed:
            st.success("✅ No failures — no systematic bias detected.")
        elif len(failed) <= 1:
            st.warning(f"⚠️ {len(failed)} sporadic failure — likely statistical fluctuation.")
        else:
            st.error(f"❌ {len(failed)} failures — **structural bias detected**. "
                     "Multiple test failures indicate a non-random source.")


# 
# TAB 3 — KEY DERIVATION
# 

with tab3:
    st.markdown('<div class="sec-head">Cryptographic Key Derivation Pipeline</div>', unsafe_allow_html=True)

    if "last_key" not in st.session_state:
        st.info("Run a test first (Tab 1) to derive and view a key.")
    else:
        k = st.session_state["last_key"]
        r = st.session_state["last_entropy"]
        results = st.session_state["last_results"]

        # Pipeline diagram
        st.markdown("""
        <div class="metric-card">
        <pre style="color:#94a3b8;font-size:0.75rem;line-height:1.8;margin:0">
 Raw Bitstream  →  Seed Material (first 512 bits packed to 64 bytes)
       │
       ▼
 Salt (32 bytes OS random)
       │
       ▼
 ┌─────────────────────────────┐
 │  KDF: {method:<24}│
 │  Key Length: {kl} bits           │
 │  Iterations: {it:<15}│
 └─────────────────────────────┘
       │
       ▼
 Derived Cryptographic Key
        </pre>
        </div>
        """.format(method=k["method"], kl=k["key_bits"],
                   it=str(k["kdf_params"].get("iterations", "N/A"))),
        unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        c1.markdown(f'<div class="metric-card"><h4>Method</h4>'
                    f'<div class="val" style="font-size:1.1rem">{k["method"]}</div></div>',
                    unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><h4>Key Length</h4>'
                    f'<div class="val">{k["key_bits"]} bits</div></div>',
                    unsafe_allow_html=True)

        st.markdown('<div class="sec-head">Derived Key (hex)</div>', unsafe_allow_html=True)
       # 🔑 Derived Key
        st.markdown('<div class="sec-head">🔑 Derived Key (Hex)</div>', unsafe_allow_html=True)

        col1, col2 = st.columns([5, 1])

        with col1:
            st.code(k["key_hex"], language="text")

        with col2:
            if st.button("📋 Copy", key="copy_key"):
                st.toast("Key copied (visual confirmation)")

        # 🔄 Base64 format (optional but useful)
        import base64
        try:
            key_bytes = bytes.fromhex(k["key_hex"])
            key_b64 = base64.b64encode(key_bytes).decode()

            with st.expander("Show Base64 Format"):
                st.code(key_b64, language="text")
        except:
            st.warning("Unable to convert key format") 

        st.markdown('<div class="sec-head">Salt (hex)</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-head">🧂 Salt (Hex)</div>', unsafe_allow_html=True)
        st.code(k["salt_hex"], language="text")
        # Suitability assessment
        sh, mn, _ = r
        passed = sum(r2["passed"] for r2 in results)
        total  = len(results)

        st.markdown('<div class="sec-head">Cryptographic Suitability Assessment</div>',
                    unsafe_allow_html=True)

        score = 0
        checks = [
            ("Shannon Entropy ≥ 0.99",  sh  >= 0.99),
            ("Min-Entropy ≥ 0.99",       mn  >= 0.99),
            ("All NIST tests passed",    passed == total),
            ("Key length ≥ 256 bits",    k["key_bits"] >= 256),
            ("Strong KDF used",          k["method"] in ["PBKDF2-SHA256", "SHA-3-256", "BLAKE2b"]),
        ]
        for label, ok in checks:
            score += ok
            ico = "✅" if ok else "❌"
            st.markdown(
                f'<div style="padding:0.4rem 0;border-bottom:1px solid #1e2a42;">'
                f'{ico} <span style="color:{"#10b981" if ok else "#ef4444"}">{label}</span>'
                f'</div>', unsafe_allow_html=True
            )

        verdict = ("🔒 **SUITABLE** for cryptographic key generation" if score >= 4 else
                   "⚠️ **MARGINAL** — review entropy and test failures" if score >= 2 else
                   "🚫 **NOT SUITABLE** — significant weaknesses detected")
        st.markdown(f'<div class="metric-card" style="margin-top:1rem">{verdict}</div>',
                    unsafe_allow_html=True)

        # Download key
        key_data = f"Method: {k['method']}\nKey ({k['key_bits']} bits):\n{k['key_hex']}\nSalt:\n{k['salt_hex']}\n"
        st.download_button("⬇ Download Key Material", key_data,
                           file_name="derived_key.txt", mime="text/plain")


# 
# TAB 4 — HISTORY & DB
# 
with tab4:
    st.markdown('<div class="sec-head">Experiment History (SQLite)</div>', unsafe_allow_html=True)

    history = load_history()
    if not history:
        st.info("No experiments yet. Run a test to populate the database.")
    else:
        df_hist = pd.DataFrame(history)
        df_hist["pass_rate"] = (df_hist["passed_tests"] / df_hist["total_tests"].replace(0, 1) * 100).round(1)
        df_hist["shannon_ent"] = df_hist["shannon_ent"].round(5)
        df_hist["min_entropy"] = df_hist["min_entropy"].round(5)
        display_cols = ["run_id", "timestamp", "source", "bits_length",
                        "pass_rate", "shannon_ent", "min_entropy"]
        st.dataframe(df_hist[display_cols], use_container_width=True, hide_index=True)

        # Entropy scatter
        fig_hist = chart_history_comparison(history)
        if fig_hist:
            st.plotly_chart(fig_hist, use_container_width=True)

        # Per-run drilldown
        st.markdown('<div class="sec-head">Run Detail</div>', unsafe_allow_html=True)
        run_ids  = [r["run_id"] for r in history]
        sel_run  = st.selectbox("Select Run ID", run_ids)

        if sel_run:
            exp, tests, keys = load_run_detail(sel_run)
            st.json({"experiment": exp})

            if tests:
                tests_df = pd.DataFrame(tests)[
                    ["test_name", "p_value", "statistic", "passed"]
                ].copy()
                tests_df["passed"] = tests_df["passed"].map({1: "✅", 0: "❌"})
                st.dataframe(tests_df, use_container_width=True, hide_index=True)

                # P-value distribution for this run
                pvals = [t["p_value"] for t in tests if t.get("p_value") is not None]
                if pvals:
                    fig_pv = go.Figure(go.Bar(
                        x=[t["test_name"] for t in tests if t.get("p_value") is not None],
                        y=pvals,
                        marker_color=["#10b981" if t["passed"] else "#ef4444" for t in tests
                                      if t.get("p_value") is not None],
                    ))
                    fig_pv.add_hline(y=0.01, line_dash="dash", line_color="#f59e0b")
                    fig_pv.update_layout(title="P-Values", **DARK)
                    st.plotly_chart(fig_pv, use_container_width=True)

            if keys:
                st.markdown('<div class="sec-head">Stored Keys</div>', unsafe_allow_html=True)
                for k in keys:
                    st.markdown(
                        f'<div class="metric-card">'
                        f'<b>{k["method"]}</b> — {k["key_bits"]} bits<br>'
                        f'<div class="hex-box" style="margin-top:0.5rem">{k["key_hex"]}</div>'
                        f'</div>', unsafe_allow_html=True
                    )

        # Global p-value histogram across all runs
        st.markdown('<div class="sec-head">Global P-Value Distribution</div>',
                    unsafe_allow_html=True)
        with get_db() as conn:
            all_tests = conn.execute("SELECT * FROM test_results").fetchall()
        all_tests = [dict(t) for t in all_tests]
        fig_glob = chart_pvalue_histogram(all_tests)
        if fig_glob:
            st.plotly_chart(fig_glob, use_container_width=True)
            st.caption("A uniform distribution indicates a high-quality random source.")

        # Export
        st.markdown('<div class="sec-head">Export Database</div>', unsafe_allow_html=True)
        csv = df_hist[display_cols].to_csv(index=False)
        st.download_button("⬇ Export History CSV", csv,
                           file_name="qrng_history.csv", mime="text/csv")

        # DB path info
        st.markdown(
            f'<div class="metric-card" style="font-size:0.75rem;color:#64748b;">'
            f'📦 DB file: <code>{DB_PATH.resolve()}</code> '
            f'— {DB_PATH.stat().st_size / 1024:.1f} KB</div>',
            unsafe_allow_html=True
        )


# 
# TAB 5 — DOCUMENTATION
# 
with tab5:
    st.markdown('<div class="sec-head">NIST SP 800-22 Test Reference</div>', unsafe_allow_html=True)

    tests_doc = [
        ("① Frequency (Monobit)", "Counts proportion of 1s and 0s. Ideal: 50/50 split.",
         "S_obs = |Σs_i| / √n",  "H₀: uniform bit distribution"),
        ("② Block Frequency", "Divides sequence into blocks; tests each block's proportion.",
         "χ² = 4M·Σ(πᵢ − ½)²", "H₀: uniform within blocks"),
        ("③ Runs", "Counts consecutive identical bits (runs). Tests length distribution.",
         "V_obs = 1 + Σ(bₖ ≠ bₖ₊₁)", "H₀: runs match expected for random"),
        ("④ Longest Run (Ones)", "Finds longest run of 1s per block; tests histogram.",
         "χ² = Σ(Vᵢ − Nπᵢ)²/Nπᵢ", "H₀: longest run matches random expectation"),
        ("⑤ Serial", "Tests distribution of all m-bit overlapping patterns.",
         "∇ψ²ₘ = ψ²ₘ − ψ²ₘ₋₁", "H₀: all patterns equally likely"),
    ]

    for name, desc, formula, hyp in tests_doc:
        st.markdown(f"""
        <div class="metric-card">
        <b style="color:#00d4ff">{name}</b><br>
        <span style="color:#94a3b8;font-size:0.82rem">{desc}</span><br>
        <code style="color:#10b981;font-size:0.8rem">{formula}</code><br>
        <small style="color:#64748b">{hyp}</small>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="sec-head">Entropy Metrics</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="metric-card">
    <b style="color:#7c3aed">Shannon Entropy H(X)</b><br>
    <span style="color:#94a3b8;font-size:0.82rem">
    Measures average information per bit. For binary: H = −p log₂p − (1−p)log₂(1−p).
    Maximum = 1.0 bit per bit. Cryptographic keys require H &gt; 0.99.
    </span>
    </div>
    <div class="metric-card">
    <b style="color:#7c3aed">Min-Entropy H∞(X)</b><br>
    <span style="color:#94a3b8;font-size:0.82rem">
    Worst-case measure: H∞ = −log₂(max pᵢ). More conservative than Shannon.
    NIST SP 800-90B uses min-entropy as the primary metric for entropy sources.
    A value &lt; 1.0 means an adversary can predict some bits better than chance.
    </span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sec-head">Key Derivation Guide</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="metric-card">
    <b style="color:#f59e0b">Safe Cryptographic Parameters</b><br><br>
    <table style="width:100%;font-size:0.78rem;color:#94a3b8;border-collapse:collapse">
      <tr style="color:#64748b;border-bottom:1px solid #1e2a42">
        <th>Parameter</th><th>Minimum</th><th>Recommended</th>
      </tr>
      <tr><td>Key length</td><td>128 bits</td><td>256 bits (AES-256)</td></tr>
      <tr><td>PBKDF2 iterations</td><td>10,000</td><td>100,000–600,000</td></tr>
      <tr><td>Salt length</td><td>16 bytes</td><td>32 bytes</td></tr>
      <tr><td>Shannon entropy</td><td>0.9</td><td>&gt; 0.999</td></tr>
      <tr><td>Min-entropy</td><td>0.9</td><td>&gt; 0.999</td></tr>
    </table>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sec-head">Architecture</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="hex-box" style="color:#94a3b8">
Bit Sources (PRNG | Biased | Qiskit | QRNG File)
         ↓
  Raw Bitstreams [n bits]
         ↓
  NIST SP 800-22 Tests   +   Entropy Metrics
  [Monobit, Block Freq,       [Shannon, Min-Entropy,
   Runs, Longest Run,          Bit Balance]
   Serial]
         ↓
  Statistical Analysis
  [pass rate, p-values, failure clustering]
         ↓
  Key Derivation (PBKDF2 / SHA-256 / SHA-3 / BLAKE2b)
         ↓
  Cryptographic Suitability Assessment
         ↓
  SQLite Database (experiments, test_results, entropy_metrics, derived_keys)
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sec-head">Quantum vs Classical Randomness</div>',
                unsafe_allow_html=True)
    st.markdown("""
    <div class="metric-card">
    <span style="color:#94a3b8;font-size:0.83rem;line-height:1.8">
    <b style="color:#00d4ff">Classical PRNG (OS/urandom):</b> Deterministic algorithms seeded with
    hardware entropy. Cryptographically secure but computationally bounded.<br><br>
    <b style="color:#7c3aed">Quantum RNG (Qiskit):</b> Measurement of qubits in superposition 
    produces intrinsically random outcomes — guaranteed by quantum mechanics, not computational 
    hardness. Immune to algorithmic prediction.<br><br>
    <b style="color:#10b981">Practical Difference:</b> Both pass NIST tests when implemented 
    correctly. QRNG provides stronger theoretical guarantees and is preferred for long-lived
    keys, post-quantum cryptography, and high-assurance applications.
    </span>
    </div>
    """, unsafe_allow_html=True)
