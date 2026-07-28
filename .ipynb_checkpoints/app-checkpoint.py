"""
BAEL-Ebola · Streamlit Forecasting Dashboard
Ebola Bundibugyo Outbreak 2026, DRC
PhD AI · Université de l'Assomption au Congo (UAC)
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import StringIO
import json
import pickle
import warnings
from datetime import datetime, timedelta
from pathlib import Path
from contextlib import contextmanager
import requests
import tarfile
import zipfile

warnings.filterwarnings("ignore")

# ── Page config ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="BAEL-Ebola · Forecasting Dashboard",
    page_icon="🦠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #F8FAFC; }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1A237E 0%, #283593 60%, #1565C0 100%);
    }
    section[data-testid="stSidebar"] * { color: white !important; }
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stSlider label,
    section[data-testid="stSidebar"] .stFileUploader label { color: #90CAF9 !important; }
    div[data-testid="metric-container"] {
        background: white; border: 1px solid #E3E8EF;
        border-radius: 10px; padding: 12px 16px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    div[data-testid="metric-container"] label { color: #546E7A; font-size:12px; }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        color: #1A237E; font-size: 28px; font-weight: 700;
    }
    h1 { color: #1A237E !important; }
    h2 { color: #283593 !important; border-bottom: 2px solid #E8EAF6; padding-bottom: 6px; }
    h3 { color: #1565C0 !important; }
    .alert-red { background:#FFEBEE; border-left:4px solid #C62828; padding:12px 16px;
                   border-radius:6px; margin:8px 0; color:#B71C1C; font-weight:600; }
    .alert-orange{ background:#FFF3E0; border-left:4px solid #E65100; padding:12px 16px;
                   border-radius:6px; margin:8px 0; color:#BF360C; font-weight:600; }
    .alert-green { background:#E8F5E9; border-left:4px solid #2E7D32; padding:12px 16px;
                   border-radius:6px; margin:8px 0; color:#1B5E20; font-weight:600; }
    .info-box { background:#E8EAF6; border-left:4px solid #3949AB; padding:12px 16px;
                   border-radius:6px; margin:8px 0; color:#1A237E; }
    .report-card { background:white; border:1px solid #E3E8EF; border-radius:10px;
                   padding:16px; margin:8px 0; box-shadow:0 1px 4px rgba(0,0,0,0.06); }
    .model-card { background:white; border:1px solid #E3E8EF; border-radius:10px;
                   padding:14px; margin:6px 0; box-shadow:0 1px 3px rgba(0,0,0,0.06); }
</style>
""", unsafe_allow_html=True)

PALETTE = ["#1565C0", "#C62828", "#2E7D32", "#F57F17", "#6A1B9A", "#00695C", "#0277BD", "#E65100"]

# ── Matplotlib safety settings ─────────────────────────────────────
plt.rcParams["figure.dpi"] = 100
plt.rcParams["savefig.dpi"] = 100
plt.rcParams["figure.max_open_warning"] = 50
plt.rcParams["figure.figsize"] = (12, 8)

# ── Safe plotting helpers ──────────────────────────────────────────
@contextmanager
def safe_plot():
    try:
        yield
    except Exception as e:
        st.warning(f"⚠️ Plot error: {str(e)[:100]}")
        return


def clean_array(arr, max_val=1e6):
    arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
    return np.clip(arr, -max_val, max_val)


def clean_series(series, max_val=1e6):
    series = series.copy()
    series = series.replace([np.inf, -np.inf], 0)
    series = series.fillna(0)
    return series.clip(-max_val, max_val)


# ═══════════════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════════════

DATA_DIR = Path("donnees_ebola")
EXTRACT_DIR = Path("donnees_extraites")
MODEL_DIR = Path("saved_models")

CSV_MAP = {
    "nat_cases": "long/insp_sitrep__national_cumulative_confirmed_cases.csv",
    "nat_deaths": "long/insp_sitrep__national_cumulative_confirmed_deaths.csv",
    "nat_recovered": "long/insp_sitrep__national_cumulative_recovered_cases.csv",
    "nat_suspected": "long/insp_sitrep__national_cumulative_suspected_cases.csv",
    "new_cases": "long/insp_sitrep__new_confirmed_cases.csv",
    "cum_cases": "long/insp_sitrep__cumulative_confirmed_cases.csv",
    "cum_deaths": "long/insp_sitrep__cumulative_confirmed_deaths.csv",
    "cum_suspected": "long/insp_sitrep__cumulative_suspected_cases.csv",
}

GITHUB_API_URL = "https://api.github.com/repos/INRB-UMIE/BDBV2026-Data/releases"

MODEL_FILES = {
    "XGBoost": MODEL_DIR / "XGBoost.pkl",
    "RandomForest": MODEL_DIR / "RandomForest.pkl",
    "LinearRegression": MODEL_DIR / "LinearRegression.pkl",
    "LightGBM": MODEL_DIR / "LightGBM.pkl",
    "Ridge": MODEL_DIR / "Ridge.pkl",
    "TL-LSTM": MODEL_DIR / "tl_lstm.pt",
    "GNN-GraphSAGE": MODEL_DIR / "gnn_model.pt",
    "Scaler": MODEL_DIR / "scaler.pkl",
}

FEATURE_COLS = [
    'dow', 'month', 'doy', 'week', 'zone_enc',
    'lag_1', 'lag_3', 'lag_7', 'lag_14', 'lag_21', 'lag_30',
    'roll_mean_3', 'roll_mean_7', 'roll_mean_14',
    'roll_std_3', 'roll_std_7', 'roll_std_14',
    'growth_rate', 'zone_cumul'
]


def parse_date(val):
    if pd.isna(val) or str(val).strip() == '':
        return pd.NaT
    s = str(val).strip().replace(']', '').replace('[', '').replace('"', '')
    for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%Y/%m/%d']:
        try:
            return pd.to_datetime(s, format=fmt)
        except Exception:
            pass
    try:
        return pd.to_datetime(s)
    except Exception:
        return pd.NaT


def normalize_long_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if len(df.columns) == 3:
        df.columns = ['zone', 'date', 'value']
    elif len(df.columns) == 2:
        df.columns = ['date', 'value']
        df.insert(0, 'zone', 'DRC')
    df['zone'] = df['zone'].astype(str).str.strip()
    df['date'] = df['date'].apply(parse_date)
    df['value'] = pd.to_numeric(df['value'], errors='coerce').fillna(0)
    df = df.dropna(subset=['date'])
    return df.sort_values(['zone', 'date']).reset_index(drop=True)


def fetch_latest_release():
    try:
        r = requests.get(GITHUB_API_URL, timeout=15)
        r.raise_for_status()
        builds = [rel for rel in r.json() if 'build' in rel.get('tag_name', '')]
        return builds[0] if builds else None
    except Exception:
        return None


def download_and_extract_data():
    release = fetch_latest_release()
    if not release:
        return False

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)

    for asset in release.get('assets', []):
        name = asset['name']
        dst = DATA_DIR / name
        if dst.exists():
            continue
        try:
            r = requests.get(asset['browser_download_url'], timeout=60)
            r.raise_for_status()
            dst.write_bytes(r.content)
        except Exception:
            continue

        if name.endswith('.tar.gz'):
            with tarfile.open(dst, 'r:gz') as tar:
                tar.extractall(EXTRACT_DIR)
        elif name.endswith('.zip'):
            with zipfile.ZipFile(dst, 'r') as z:
                z.extractall(DATA_DIR)
    return True


def load_epidemio_data():
    base = EXTRACT_DIR / 'build'
    data = {}
    
    if not base.exists():
        return None

    for key, relpath in CSV_MAP.items():
        path = base / relpath
        if not path.exists():
            continue
        try:
            raw = pd.read_csv(path)
            df = normalize_long_df(raw)
            data[key] = df
        except Exception:
            continue
    
    return data if data else None


@st.cache_data
def demo_data():
    np.random.seed(42)
    N = 60
    start = datetime(2026, 1, 15)
    dates = [start + timedelta(days=i) for i in range(N)]

    t = np.linspace(0, 20, N)
    base = 50 * np.exp(-((t - 8) ** 2) / 6) + np.random.poisson(2, N)
    cum = np.cumsum(base).astype(int)
    cum = np.clip(cum, 0, 5000)

    zones = ['Butembo'] * N + ['Beni'] * N + ['Katwa'] * N
    dts = dates * 3
    values = (list(cum) + list((cum * 0.6).astype(int)) + list((cum * 0.35).astype(int)))

    return pd.DataFrame({'zone': zones, 'date': dts, 'value': values})


@st.cache_data
def load_epidemio_data_fallback():
    if download_and_extract_data():
        data = load_epidemio_data()
        if data:
            return data
    return {"cum_cases": demo_data()}


# ═══════════════════════════════════════════════════════════════════════
# MODEL LOADING
# ═══════════════════════════════════════════════════════════════════════
@st.cache_resource(show_spinner=False)
def load_models():
    loaded = {}
    status = {}

    pkl_keys = ["XGBoost", "RandomForest", "LinearRegression", "LightGBM", "Ridge", "Scaler"]
    for key in pkl_keys:
        path = MODEL_FILES[key]
        if path.exists():
            try:
                with open(path, "rb") as f:
                    loaded[key] = pickle.load(f)
                status[key] = "✅ Loaded"
            except Exception as e:
                loaded[key] = None
                status[key] = f"❌ Error"
        else:
            loaded[key] = None
            status[key] = "⚠️ Missing"

    try:
        import torch
        import torch.nn as nn

        class EpidemicEncoder(nn.Module):
            def __init__(self, input_dim=19, hidden=64, n_layers=2, dropout=0.2):
                super().__init__()
                self.encoder = nn.LSTM(input_dim, hidden, n_layers,
                                       batch_first=True,
                                       dropout=dropout if n_layers > 1 else 0.0)
                self.projector = nn.Sequential(
                    nn.Linear(hidden, 32), nn.ReLU(), nn.Linear(32, 1)
                )

            def forward(self, x):
                out, _ = self.encoder(x)
                return self.projector(out[:, -1, :]).squeeze(-1)

        try:
            import torch.nn.functional as F
            from torch_geometric.nn import SAGEConv

            class EbolaGNN(nn.Module):
                def __init__(self, in_dim=5, hidden=64, n_layers=2, dropout=0.3):
                    super().__init__()
                    self.convs = nn.ModuleList()
                    self.bns = nn.ModuleList()
                    self.convs.append(SAGEConv(in_dim, hidden))
                    self.bns.append(nn.BatchNorm1d(hidden))
                    for _ in range(n_layers - 1):
                        self.convs.append(SAGEConv(hidden, hidden))
                        self.bns.append(nn.BatchNorm1d(hidden))
                    self.head = nn.Sequential(
                        nn.Linear(hidden, 32), nn.ReLU(),
                        nn.Dropout(dropout), nn.Linear(32, 1)
                    )
                    self.dropout = dropout

                def forward(self, x, edge_index):
                    for conv, bn in zip(self.convs, self.bns):
                        h = conv(x, edge_index)
                        h = bn(h)
                        h = F.relu(h)
                        h = F.dropout(h, p=self.dropout, training=self.training)
                        x = x + h if x.size(-1) == h.size(-1) else h
                    return self.head(x).squeeze(-1)

            gnn_path = MODEL_FILES["GNN-GraphSAGE"]
            if gnn_path.exists():
                gnn = EbolaGNN()
                gnn.load_state_dict(torch.load(gnn_path, map_location='cpu', weights_only=True))
                gnn.eval()
                loaded["GNN-GraphSAGE"] = gnn
                status["GNN-GraphSAGE"] = "✅ Loaded"
            else:
                loaded["GNN-GraphSAGE"] = None
                status["GNN-GraphSAGE"] = "⚠️ Missing"

        except ImportError:
            loaded["GNN-GraphSAGE"] = None
            status["GNN-GraphSAGE"] = "⚠️ No torch_geometric"

        tl_path = MODEL_FILES["TL-LSTM"]
        if tl_path.exists():
            tl = EpidemicEncoder(input_dim=19)
            tl.load_state_dict(torch.load(tl_path, map_location='cpu', weights_only=True))
            tl.eval()
            loaded["TL-LSTM"] = tl
            status["TL-LSTM"] = "✅ Loaded"
        else:
            loaded["TL-LSTM"] = None
            status["TL-LSTM"] = "⚠️ Missing"

    except ImportError:
        loaded["TL-LSTM"] = None
        loaded["GNN-GraphSAGE"] = None
        status["TL-LSTM"] = "⚠️ No PyTorch"
        status["GNN-GraphSAGE"] = "⚠️ No PyTorch"

    return loaded, status


# ═══════════════════════════════════════════════════════════════════════
# FEATURE ENGINEERING
# ═══════════════════════════════════════════════════════════════════════
def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy().sort_values('date').reset_index(drop=True)
    df['dow'] = df['date'].dt.dayofweek
    df['month'] = df['date'].dt.month
    df['doy'] = df['date'].dt.dayofyear
    df['week'] = df['date'].dt.isocalendar().week.astype(int)

    for lag in [1, 3, 7, 14, 21, 30]:
        df[f'lag_{lag}'] = df['value'].shift(lag).fillna(0)

    for w in [3, 7, 14]:
        df[f'roll_mean_{w}'] = df['value'].rolling(w, min_periods=1).mean().fillna(0)
        df[f'roll_std_{w}'] = df['value'].rolling(w, min_periods=1).std().fillna(0)

    df['growth_rate'] = df['value'].pct_change().clip(-5, 5).fillna(0)
    df['zone_cumul'] = df['value'].cumsum()
    df['zone_enc'] = 0

    for col in FEATURE_COLS:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        df[col] = df[col].replace([np.inf, -np.inf], 0)

    return df


def clean_X(arr: np.ndarray) -> np.ndarray:
    arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
    for c in range(arr.shape[1]):
        q99 = np.percentile(arr[:, c], 99)
        q01 = np.percentile(arr[:, c], 1)
        arr[:, c] = np.clip(arr[:, c], q01, q99)
    return arr.astype(np.float32)


# ═══════════════════════════════════════════════════════════════════════
# PREDICTION HELPERS
# ═══════════════════════════════════════════════════════════════════════
def sklearn_predict(model, X: np.ndarray) -> np.ndarray:
    try:
        preds = model.predict(X)
        preds = np.nan_to_num(preds, nan=0.0, posinf=0.0, neginf=0.0)
        return np.clip(preds, 0, 1e6)
    except Exception as e:
        st.warning(f"Prediction error: {e}")
        return np.zeros(len(X))


def lstm_predict(model, X: np.ndarray, seq_len: int = 7) -> np.ndarray:
    try:
        import torch
        sl = min(seq_len, max(2, len(X) // 4))
        if len(X) <= sl:
            return np.zeros(1)
        seqs = np.array([X[i - sl:i] for i in range(sl, len(X))], dtype=np.float32)
        with torch.no_grad():
            out = model(torch.tensor(seqs)).numpy()
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return np.clip(out, 0, 1e6)
    except Exception as e:
        st.warning(f"TL-LSTM error: {e}")
        return np.zeros(max(1, len(X) - seq_len))


def compute_metrics(y_true, y_pred) -> dict:
    yt = np.array(y_true)
    yp = np.clip(np.array(y_pred), 0, None)
    n = min(len(yt), len(yp))
    if n < 2:
        return {'RMSE': '—', 'MAE': '—', 'R²': '—', 'MAPE%': '—'}

    yt, yp = yt[:n], yp[:n]
    yt = np.clip(yt, 0, 1e6)
    yp = np.clip(yp, 0, 1e6)
    
    rmse = float(np.sqrt(np.mean((yt - yp) ** 2)))
    mae = float(np.mean(np.abs(yt - yp)))
    ss_r = np.sum((yt - yp) ** 2)
    ss_t = np.sum((yt - yt.mean()) ** 2)
    r2 = float(1 - ss_r / (ss_t + 1e-8))
    r2 = max(-1.0, min(1.0, r2))
    
    mask = yt > 0
    if mask.sum() > 0:
        mape = float(np.mean(np.abs((yt[mask] - yp[mask]) / (yt[mask] + 1e-8))) * 100)
        mape = min(mape, 999.99)
    else:
        mape = np.nan

    return {
        'RMSE': round(rmse, 2),
        'MAE': round(mae, 2),
        'R²': round(r2, 4),
        'MAPE%': round(mape, 2) if not np.isnan(mape) else '—'
    }


def bootstrap_ci(residuals, point_pred, n=500) -> dict:
    boot = np.clip([point_pred + np.random.choice(residuals, replace=True)
                    for _ in range(n)], 0, None)
    return {
        'mean': float(np.mean(boot)),
        'median': float(np.median(boot)),
        'lower': float(np.percentile(boot, 2.5)),
        'upper': float(np.percentile(boot, 97.5))
    }


def sir_project(last_cases: float, horizon=30, R0=1.5, gamma=1/7, N=100_000):
    from scipy.integrate import odeint

    I0 = max(last_cases, 1)
    I0 = min(I0, N * 0.3)
    S0 = N - I0
    beta = R0 * gamma
    max_beta = 10.0 / N
    beta = min(beta, max_beta)

    def model(y, t):
        S, I, R = y
        if S < 0 or I < 0 or I > N:
            return [0, 0, 0]

        dS = -beta * S * I / N
        dI = beta * S * I / N - gamma * I
        dR = gamma * I

        dS = np.clip(dS, -N, 0)
        dI = np.clip(dI, -N, N)
        dR = np.clip(dR, 0, N)

        return [dS, dI, dR]

    try:
        t_eval = np.linspace(0, horizon, horizon * 2)
        sol = odeint(model, [S0, I0, 0], t_eval, rtol=1e-6, atol=1e-8, mxstep=5000)

        new_cases = np.maximum(-np.diff(sol[:, 0], prepend=sol[0, 0]), 0)
        new_cases = new_cases[::2][:horizon]
        new_cases = np.nan_to_num(new_cases, nan=0.0, posinf=0.0, neginf=0.0)

        if np.any(new_cases > 0):
            max_allowed = max(1e6, I0 * 10)
            new_cases = np.clip(new_cases, 0, max_allowed)
        else:
            new_cases = np.clip(new_cases, 0, None)

        if np.max(new_cases) > 1e7:
            new_cases = new_cases / 1000

        return new_cases

    except Exception as e:
        st.warning(f"SIR projection error: {e}")
        return np.array([last_cases * (1 + 0.02 * i) for i in range(horizon)])


def parse_csv(file) -> pd.DataFrame:
    content = file.read().decode('utf-8', errors='ignore')
    df = pd.read_csv(StringIO(content))
    df.columns = df.columns.str.strip()

    if len(df.columns) == 3:
        df.columns = ['zone', 'date', 'value']
    elif len(df.columns) == 2:
        df.columns = ['date', 'value']
        df.insert(0, 'zone', 'Uploaded')
    else:
        dc = next((c for c in df.columns if 'date' in c.lower()), df.columns[0])
        vc = next((c for c in df.columns
                   if any(k in c.lower() for k in ['case', 'value', 'cas', 'conf'])),
                  df.columns[-1])
        df = df[[dc, vc]].rename(columns={dc: 'date', vc: 'value'})
        df.insert(0, 'zone', 'Uploaded')

    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['value'] = pd.to_numeric(df['value'], errors='coerce').fillna(0).clip(lower=0)
    return df.dropna(subset=['date']).sort_values('date').reset_index(drop=True)


# ═══════════════════════════════════════════════════════════════════════
# LOAD DATA & MODELS
# ═══════════════════════════════════════════════════════════════════════
DATA = load_epidemio_data_fallback()
MODELS, MODEL_STATUS = load_models()

SCALER = MODELS.get("Scaler")
SKLEARN_MDLS = {k: MODELS[k] for k in
                ["XGBoost", "RandomForest", "LinearRegression", "LightGBM", "Ridge"]
                if MODELS.get(k) is not None}
TL_LSTM = MODELS.get("TL-LSTM")

n_loaded = sum(1 for v in MODELS.values() if v is not None)

# ═══════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🦠 BAEL-Ebola")
    st.markdown("**Bundibugyo 2026 · DRC**")

    st.markdown("### 🤖 Models")
    for k, v in MODEL_STATUS.items():
        if k == "Scaler":
            continue
        icon = "✅" if "Loaded" in v else "⚠️" if "Missing" in v else "❌"
        st.markdown(f"<span style='font-size:12px'>{icon} **{k}**</span>",
                    unsafe_allow_html=True)

    st.markdown(
        f"<div style='background:rgba(255,255,255,0.15);border-radius:8px;"
        f"padding:8px;margin:6px 0;font-size:12px;text-align:center;'>"
        f"<b>{n_loaded}</b> / {len(MODELS)} models ready</div>",
        unsafe_allow_html=True
    )

    st.markdown("---")
    st.markdown("### 📂 Data")
    data_src = st.radio("", ["Real data (INRB)", "Demo data", "Upload CSV"], label_visibility="collapsed")
    uploaded = None
    if data_src == "Upload CSV":
        uploaded = st.file_uploader("CSV: zone | date | value", type=['csv'])

    st.markdown("---")
    st.markdown("### ⚙️ Parameters")
    active_model = st.selectbox(
        "Primary model",
        options=list(SKLEARN_MDLS.keys()) + (["TL-LSTM"] if TL_LSTM else []),
        index=0
    )
    n_shots = st.slider("Few-Shot K (weeks)", 2, 10, 4)
    test_ratio = st.slider("Test ratio", 0.1, 0.4, 0.20, 0.05)
    horizon = st.slider("Forecast horizon (days)", 7, 30, 14)
    r0_val = st.slider("SIR R₀", 1.0, 2.5, 1.5, 0.1)
    n_boot = st.slider("Bootstrap N", 100, 500, 200, 50)
    risk_pct = st.slider("Risk percentile", 50, 95, 75)
    seq_len = st.slider("LSTM seq length", 3, 10, 5)

    st.markdown("---")
    st.markdown("""
    **UAC · Butembo · Nord-Kivu**
    PhD in Artificial Intelligence
    BAEL Framework
    """)

# ═══════════════════════════════════════════════════════════════════════
# DATA PREPARATION
# ═══════════════════════════════════════════════════════════════════════

if data_src == "Upload CSV" and uploaded:
    try:
        raw_df = parse_csv(uploaded)
        st.success(f"✅ {len(raw_df)} rows loaded")
    except Exception as e:
        st.error(f"Upload error: {e}")
        raw_df = demo_data()
elif data_src == "Real data (INRB)" and DATA:
    raw_df = DATA.get("cum_cases", demo_data())
else:
    raw_df = demo_data()

# Aggregate national series
nat = (raw_df.groupby('date')['value'].sum()
       .reset_index().sort_values('date').reset_index(drop=True))
nat.columns = ['date', 'value']
nat['new_cases'] = nat['value'].diff().clip(lower=0).fillna(0)
nat['rolling7'] = nat['new_cases'].rolling(7, min_periods=1).mean()
nat['growth_rate'] = nat['value'].pct_change().clip(-5, 5).fillna(0) * 100

zones = [z for z in raw_df['zone'].unique()
         if str(z).upper() not in ('DRC', 'NATIONAL', '')]
zone_latest = (raw_df.groupby('zone')['value'].last()
               .sort_values(ascending=False).reset_index())
last_dt = nat['date'].max().strftime('%d %b %Y')
gr_last = float(nat['growth_rate'].iloc[-1])

# Feature engineering
feat_df = build_features(nat.rename(columns={'value': 'value'}))
feat_df['value'] = nat['value'].values

all_dates = feat_df['date'].unique()
n_train = min(n_shots * 7, int(len(all_dates) * (1 - test_ratio)))
n_train = max(n_train, 10)
cutoff_idx = min(n_train, len(all_dates) - 3)
cutoff = all_dates[cutoff_idx]

train_df = feat_df[feat_df['date'] < cutoff]
test_df = feat_df[feat_df['date'] >= cutoff]

if len(train_df) < 5 or len(test_df) < 3:
    cutoff = all_dates[min(len(all_dates) // 2, len(all_dates) - 3)]
    train_df = feat_df[feat_df['date'] < cutoff]
    test_df = feat_df[feat_df['date'] >= cutoff]

X_train_raw = clean_X(train_df[FEATURE_COLS].values)
y_train = train_df['value'].values.astype(np.float64)
X_test_raw = clean_X(test_df[FEATURE_COLS].values)
y_test = test_df['value'].values.astype(np.float64)

# Apply scaler
if SCALER is not None:
    try:
        X_train_sc = SCALER.transform(X_train_raw)
        X_test_sc = SCALER.transform(X_test_raw)
    except Exception:
        mu = X_train_raw.mean(0)
        sd = X_train_raw.std(0) + 1e-8
        X_train_sc = (X_train_raw - mu) / sd
        X_test_sc = (X_test_raw - mu) / sd
else:
    mu = X_train_raw.mean(0)
    sd = X_train_raw.std(0) + 1e-8
    X_train_sc = (X_train_raw - mu) / sd
    X_test_sc = (X_test_raw - mu) / sd

X_train_sc = clean_X(X_train_sc)
X_test_sc = clean_X(X_test_sc)

# Predictions
if active_model == "TL-LSTM" and TL_LSTM:
    preds_train = lstm_predict(TL_LSTM, X_train_sc, seq_len)
    preds_test = lstm_predict(TL_LSTM, X_test_sc, seq_len)
    y_train_al = y_train[-len(preds_train):]
    y_test_al = y_test[-len(preds_test):]
else:
    mdl = SKLEARN_MDLS.get(active_model)
    if mdl:
        preds_train = sklearn_predict(mdl, X_train_sc)
        preds_test = sklearn_predict(mdl, X_test_sc)
    else:
        mu2 = X_train_sc.mean(0)
        sd2 = X_train_sc.std(0) + 1e-8
        X_tr2 = (X_train_sc - mu2) / sd2
        X_te2 = (X_test_sc - mu2) / sd2
        A = np.c_[np.ones(len(X_tr2)), X_tr2]
        w = np.linalg.lstsq(A.T @ A + 0.01 * np.eye(A.shape[1]), A.T @ y_train, rcond=None)[0]
        preds_train = np.clip(np.c_[np.ones(len(X_tr2)), X_tr2] @ w, 0, None)
        preds_test = np.clip(np.c_[np.ones(len(X_te2)), X_te2] @ w, 0, None)
    y_train_al, y_test_al = y_train, y_test

metrics_primary = compute_metrics(y_test_al, preds_test)

# All-model comparison
all_metrics = {}
for name, mdl in SKLEARN_MDLS.items():
    p = sklearn_predict(mdl, X_test_sc)
    all_metrics[name] = compute_metrics(y_test, p)
if TL_LSTM:
    p_tl = lstm_predict(TL_LSTM, X_test_sc, seq_len)
    all_metrics["TL-LSTM"] = compute_metrics(y_test[-len(p_tl):], p_tl)

# Risk threshold & bootstrap
pos_vals = y_train[y_train > 0]
risk_thr = float(np.percentile(pos_vals, risk_pct)) if len(pos_vals) else 1.0
resid = y_train_al[:len(preds_train)] - preds_train
ci_fc = bootstrap_ci(resid, float(preds_test[-1]) if len(preds_test) else 0, n_boot)
sir_proj = sir_project(float(nat['new_cases'].iloc[-1]), horizon, r0_val)

# ═══════════════════════════════════════════════════════════════════════
# HEADER + KPIs
# ═══════════════════════════════════════════════════════════════════════
st.markdown("# 🦠 BAEL-Ebola · Forecasting Dashboard")
st.markdown(
    f"**Ebola Bundibugyo Virus Disease 2026 · DRC** — "
    f"Active model: **{active_model}** | "
    f"{n_loaded}/{len(MODELS)} models loaded"
)

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Total Cases", f"{int(nat['value'].max()):,}")
c2.metric("New Cases (7d)", f"{int(nat['new_cases'].tail(7).sum()):,}")
c3.metric("Health Zones", str(len(zones)))
c4.metric("Last Report", last_dt)
c5.metric(f"{active_model} RMSE", str(metrics_primary.get('RMSE', '—')))
c6.metric(f"{active_model} R²", str(metrics_primary.get('R²', '—')))

if gr_last > 20:
    st.markdown(f'<div class="alert-red">⚠️ HIGH ALERT — Growth rate: {gr_last:.1f}% · Immediate response required</div>', unsafe_allow_html=True)
elif gr_last > 5:
    st.markdown(f'<div class="alert-orange">⚠️ ELEVATED RISK — Growth rate: {gr_last:.1f}% · Enhanced surveillance advised</div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="alert-green">✅ STABLE — Growth rate: {gr_last:.1f}% · Routine monitoring</div>', unsafe_allow_html=True)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Epidemiology", "🔮 Forecast", "📊 Model Comparison", "🗺️ Zone Analysis", "📋 Report"
])

# ─────────────────────────────────────────────────────────────────────
# TAB 1 · Epidemiology
# ─────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown("## National Epidemiological Overview")
    
    nat_clean = nat.copy()
    nat_clean['value'] = clean_series(nat_clean['value'])
    nat_clean['new_cases'] = clean_series(nat_clean['new_cases'])
    nat_clean['rolling7'] = clean_series(nat_clean['rolling7'])
    nat_clean['growth_rate'] = clean_series(nat_clean['growth_rate'], max_val=1000)

    with safe_plot():
        fig, axes = plt.subplots(2, 2, figsize=(12, 7), dpi=72)
        fig.suptitle(f"Ebola Bundibugyo 2026 · DRC | {last_dt}", fontsize=13, fontweight='bold')

        ax = axes[0, 0]
        ax.fill_between(nat_clean['date'], nat_clean['value'], alpha=0.18, color=PALETTE[0])
        ax.plot(nat_clean['date'], nat_clean['value'], color=PALETTE[0], lw=2.5)
        ax.set_title("A. Cumulative Confirmed Cases", fontweight='bold')
        ax.set_ylabel("Cases")
        ax.tick_params(axis='x', rotation=25)
        ax.grid(True, alpha=0.25)
        ax.spines[['top', 'right']].set_visible(False)

        ax = axes[0, 1]
        ax.bar(nat_clean['date'], nat_clean['new_cases'], alpha=0.5, color=PALETTE[1], label="Daily new cases")
        ax.plot(nat_clean['date'], nat_clean['rolling7'], color=PALETTE[0], lw=2, label="7-day rolling avg")
        ax.axhline(risk_thr, color='red', ls='--', lw=1.2, alpha=0.7,
                   label=f"Risk thr. ({int(risk_thr)} cases)")
        ax.set_title("B. Daily New Cases", fontweight='bold')
        ax.set_ylabel("Cases")
        ax.legend(fontsize=8)
        ax.tick_params(axis='x', rotation=25)
        ax.grid(True, alpha=0.25)
        ax.spines[['top', 'right']].set_visible(False)

        ax = axes[1, 0]
        colors_gr = [PALETTE[1] if g > 0 else PALETTE[2] for g in nat_clean['growth_rate']]
        ax.bar(nat_clean['date'], nat_clean['growth_rate'], color=colors_gr, alpha=0.7)
        ax.axhline(0, color='black', lw=0.8)
        ax.set_title("C. Daily Growth Rate (%)", fontweight='bold')
        ax.set_ylabel("Growth (%)")
        ax.tick_params(axis='x', rotation=25)
        ax.grid(True, alpha=0.25)
        ax.spines[['top', 'right']].set_visible(False)

        ax = axes[1, 1]
        nc = nat_clean['new_cases'][nat_clean['new_cases'] > 0]
        if len(nc) > 0:
            ax.hist(nc, bins=min(20, len(nc)), color=PALETTE[3], edgecolor='white', alpha=0.85)
            ax.axvline(nc.mean(), color=PALETTE[0], lw=2, ls='--', label=f"Mean {nc.mean():.1f}")
            ax.axvline(nc.median(), color=PALETTE[1], lw=2, ls='--', label=f"Median {nc.median():.1f}")
            ax.legend(fontsize=9)
        ax.set_title("D. New Case Distribution", fontweight='bold')
        ax.set_xlabel("Cases/day")
        ax.set_ylabel("Frequency")
        ax.spines[['top', 'right']].set_visible(False)

        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Summary Statistics")
        st.dataframe(pd.DataFrame({
            'Metric': ['Total cumulative', 'Peak daily', 'Mean daily',
                       'Median daily', 'Days active', 'Last 7-day total'],
            'Value': [f"{int(nat['value'].max()):,}",
                      f"{int(nat['new_cases'].max()):,}",
                      f"{nat['new_cases'].mean():.1f}",
                      f"{nat['new_cases'].median():.1f}",
                      f"{int((nat['new_cases'] > 0).sum())}",
                      f"{int(nat['new_cases'].tail(7).sum()):,}"]
        }), hide_index=True, use_container_width=True)

    with col2:
        st.markdown("#### Few-Shot Split")
        st.dataframe(pd.DataFrame({
            'Parameter': ['Training weeks K', 'Train obs', 'Test obs',
                          'Risk threshold', 'Cutoff date', 'Features'],
            'Value': [str(n_shots), str(len(train_df)), str(len(test_df)),
                      f"{risk_thr:.1f} ({risk_pct}th pct)",
                      str(pd.Timestamp(cutoff).date()),
                      str(len(FEATURE_COLS))]
        }), hide_index=True, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────
# TAB 2 · Forecast
# ─────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown(f"## Forecast — {active_model}")
    col1, col2 = st.columns([3, 1])

    with col1:
        sir_proj_clean = clean_array(sir_proj, max_val=1e6)
        max_historical = max(nat['new_cases'].max(), 100)
        max_allowed = max(max_historical * 5, 10000)
        sir_proj_clean = np.clip(sir_proj_clean, 0, max_allowed)

        if np.max(sir_proj_clean) > 1e6:
            st.warning(f"⚠️ SIR projection values are very large ({np.max(sir_proj_clean):.0f}). Scaling down.")
            sir_proj_clean = np.log1p(sir_proj_clean) * 100

        preds_test_clean = clean_array(preds_test, max_val=1e6)
        preds_test_clean = np.clip(preds_test_clean, 0, max(1000, preds_test_clean.max() * 2))
        y_test_clean = clean_array(y_test_al, max_val=1e6)
        td_clean = test_df['date'].values[-len(y_test_clean):]
        train_vals_clean = clean_array(train_df['value'].values)

        with safe_plot():
            fig, axes = plt.subplots(2, 1, figsize=(12, 8), dpi=72)

            ax = axes[0]
            ax.fill_between(train_df['date'], train_vals_clean, alpha=0.15, color=PALETTE[0])
            ax.plot(train_df['date'], train_vals_clean, color=PALETTE[0], lw=2, label='Training data')

            n_p = min(len(preds_test_clean), len(td_clean))
            if n_p > 0:
                ax.plot(td_clean[:n_p], y_test_clean[:n_p],
                        color=PALETTE[1], lw=2, label='Actual (test)')
                ax.plot(td_clean[:n_p], preds_test_clean[:n_p],
                        color=PALETTE[2], lw=2.5, ls='--',
                        label=f'{active_model} prediction')

            ax.axvline(pd.Timestamp(cutoff), color='grey', ls=':', lw=1.5, label='Split')
            ax.set_title(f"Predicted vs Actual — {active_model} (Few-Shot K={n_shots})",
                         fontweight='bold', fontsize=12)
            ax.set_ylabel("Cumulative cases")
            ax.legend(fontsize=9)
            ax.grid(True, alpha=0.25)
            ax.spines[['top', 'right']].set_visible(False)

            ax = axes[1]
            hist_days = min(30, len(nat))
            hist_dates = nat['date'].tail(hist_days)
            hist_cases = clean_array(nat['new_cases'].tail(hist_days).values)
            hist_cases = np.clip(hist_cases, 0, max_allowed)

            ax.plot(hist_dates, hist_cases, color=PALETTE[0], lw=2, label='Historical new cases')

            future_days = min(horizon, 60)
            future_dates = [nat['date'].max() + timedelta(days=i+1) for i in range(future_days)]
            sir_clean = sir_proj_clean[:future_days]

            if len(sir_clean) > 0 and np.any(sir_clean > 0) and np.max(sir_clean) < 1e8:
                ax.plot(future_dates, sir_clean, color=PALETTE[1], lw=2.5,
                        label=f'SIR projection (R₀={r0_val})')

                if np.all(np.isfinite(sir_clean)) and np.all(sir_clean >= 0) and np.max(sir_clean) < 1e7:
                    lower = np.maximum(0, sir_clean * 0.65)
                    upper = sir_clean * 1.35
                    ax.fill_between(future_dates, lower, upper,
                                    color=PALETTE[1], alpha=0.15,
                                    label='Uncertainty band (±35%)')
            else:
                ax.text(0.5, 0.5, 'SIR projection unavailable\n(values too extreme)',
                        transform=ax.transAxes, ha='center', va='center',
                        fontsize=12, color='red')

            ax.axvline(nat['date'].max(), color='grey', ls=':', lw=1.5)
            ax.set_title(f"{future_days}-Day SIR Projection", fontweight='bold', fontsize=12)
            ax.set_ylabel("New cases/day")
            ax.legend(fontsize=9)
            ax.grid(True, alpha=0.25)
            ax.tick_params(axis='x', rotation=25)
            ax.spines[['top', 'right']].set_visible(False)

            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

    with col2:
        ci_mean = max(0, ci_fc.get('mean', 0)) if np.isfinite(ci_fc.get('mean', 0)) else 0
        ci_median = max(0, ci_fc.get('median', 0)) if np.isfinite(ci_fc.get('median', 0)) else 0
        ci_lower = max(0, ci_fc.get('lower', 0)) if np.isfinite(ci_fc.get('lower', 0)) else 0
        ci_upper = max(0, ci_fc.get('upper', 0)) if np.isfinite(ci_fc.get('upper', 0)) else 0

        st.markdown("#### Bootstrap 95% CI")
        st.markdown(f"""
        <div style="background:#E8EAF6;padding:18px;border-radius:10px;text-align:center;">
            <div style="font-size:12px;color:#546E7A;margin-bottom:4px;">Next-step forecast</div>
            <div style="font-size:36px;font-weight:700;color:#1A237E;">{ci_mean:.0f}</div>
            <div style="font-size:12px;color:#546E7A;">cases (mean)</div>
            <hr style="margin:10px 0;border-color:#C5CAE9;">
            <div style="font-size:12px;color:#546E7A;">Median</div>
            <div style="font-size:24px;font-weight:600;color:#283593;">{ci_median:.0f}</div>
            <hr style="margin:10px 0;border-color:#C5CAE9;">
            <div style="font-size:12px;color:#546E7A;">95% Confidence Interval</div>
            <div style="font-size:20px;font-weight:600;color:#C62828;">
                [{ci_lower:.0f} — {ci_upper:.0f}]
            </div>
            <hr style="margin:10px 0;border-color:#C5CAE9;">
            <div style="font-size:11px;color:#78909C;">
            Model: <b>{active_model}</b><br>
            N={n_boot} bootstrap<br>
            Residual resampling
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### Primary Metrics")
        st.metric("RMSE", str(metrics_primary.get('RMSE', '—')))
        st.metric("MAE", str(metrics_primary.get('MAE', '—')))
        st.metric("R²", str(metrics_primary.get('R²', '—')))
        st.metric("MAPE%", str(metrics_primary.get('MAPE%', '—')))

# ─────────────────────────────────────────────────────────────────────
# TAB 3 · Model Comparison
# ─────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown("## All Models Comparison")

    if all_metrics:
        perf_df = pd.DataFrame(all_metrics).T.reset_index()
        perf_df.columns = ['Model', 'RMSE', 'MAE', 'R²', 'MAPE%']
        perf_df['RMSE_num'] = pd.to_numeric(perf_df['RMSE'], errors='coerce')
        perf_df['R2_num'] = pd.to_numeric(perf_df['R²'], errors='coerce')
        perf_df = perf_df.sort_values('R2_num', ascending=False)

        col1, col2 = st.columns([3, 2])

        with col1:
            st.markdown("#### Metrics Table (sorted by R²)")

            def highlight_best(row):
                if row['Model'] == perf_df.iloc[0]['Model']:
                    return ['background-color: #E8F5E9'] * len(row)
                return [''] * len(row)

            st.dataframe(
                perf_df[['Model', 'RMSE', 'MAE', 'R²', 'MAPE%']].style.apply(
                    highlight_best, axis=1),
                hide_index=True, use_container_width=True
            )

            with safe_plot():
                fig, ax = plt.subplots(figsize=(9, 4), dpi=72)
                valid = perf_df.dropna(subset=['R2_num'])
                if not valid.empty:
                    colors_m = [PALETTE[2] if m == active_model else PALETTE[0]
                                for m in valid['Model']]
                    bars = ax.bar(valid['Model'], valid['R2_num'],
                                  color=colors_m, edgecolor='white', alpha=0.88)
                    ax.axhline(0, color='black', lw=0.8, ls='--')
                    ax.set_title("R² Score — All Models", fontweight='bold')
                    ax.set_ylabel("R²")
                    ax.set_ylim(-0.15, 1.05)
                    for bar, v in zip(bars, valid['R2_num']):
                        ax.text(bar.get_x() + bar.get_width() / 2,
                                bar.get_height() + 0.02, f"{v:.3f}",
                                ha='center', fontsize=9, fontweight='bold')
                    ax.spines[['top', 'right']].set_visible(False)
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close()

        with col2:
            with safe_plot():
                fig, ax = plt.subplots(figsize=(6, 4), dpi=72)
                valid_r = perf_df.dropna(subset=['RMSE_num'])
                if not valid_r.empty:
                    colors_r = [PALETTE[1] if m == active_model else PALETTE[3]
                                for m in valid_r['Model']]
                    ax.barh(valid_r['Model'], valid_r['RMSE_num'],
                            color=colors_r, edgecolor='white', alpha=0.88)
                    ax.set_title("RMSE — lower is better", fontweight='bold')
                    ax.set_xlabel("RMSE")
                    ax.spines[['top', 'right']].set_visible(False)
                    ax.grid(True, alpha=0.25, axis='x')
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close()

            st.markdown("#### Residual Diagnostics")

            min_len = min(len(y_test_al), len(preds_test))
            if min_len > 1:
                resid_test = y_test_al[:min_len] - preds_test[:min_len]
                resid_test = clean_array(resid_test, max_val=1e6)

                if len(resid_test) > 2 and np.std(resid_test) > 1e-6:
                    try:
                        with safe_plot():
                            fig, axes = plt.subplots(1, 2, figsize=(6, 4), dpi=72)

                            ax = axes[0]
                            n_bins = min(12, len(resid_test))
                            ax.hist(resid_test, bins=n_bins,
                                    color=PALETTE[0], edgecolor='white', alpha=0.85, density=True)

                            if np.std(resid_test) > 1e-6:
                                mu, sig = resid_test.mean(), resid_test.std()
                                xs = np.linspace(resid_test.min(), resid_test.max(), 80)
                                norm_pdf = (1 / (sig * (2 * np.pi) ** 0.5)) * np.exp(-0.5 * ((xs - mu) / sig) ** 2)
                                ax.plot(xs, norm_pdf, color=PALETTE[1], lw=2)

                            ax.set_title("Residual dist.", fontweight='bold', fontsize=9)
                            ax.spines[['top', 'right']].set_visible(False)

                            ax = axes[1]
                            from scipy import stats as sp_stats
                            if np.std(resid_test) > 1e-6:
                                sp_stats.probplot(resid_test, dist='norm', plot=ax)
                                ax.set_title("QQ-Plot", fontweight='bold', fontsize=9)
                                ax.grid(True, alpha=0.25)
                            else:
                                ax.text(0.5, 0.5, 'Constant residuals\n(no variance)',
                                       transform=ax.transAxes, ha='center', va='center',
                                       fontsize=10, color='gray')

                            plt.tight_layout()
                            st.pyplot(fig)
                            plt.close()

                        if len(resid_test) >= 3 and np.std(resid_test) > 1e-6:
                            try:
                                from scipy import stats as sp_stats
                                sw_p = sp_stats.shapiro(resid_test)[1]
                                sw_p_str = f"{sw_p:.4f}" if not np.isnan(sw_p) else "N/A"
                                normal_msg = '— Normal ✅' if (not np.isnan(sw_p) and sw_p > 0.05) else '— Non-normal ⚠️'
                            except:
                                sw_p_str = "N/A"
                                normal_msg = '— Test failed'
                        else:
                            sw_p_str = "N/A"
                            normal_msg = '— Insufficient variance'

                        st.markdown(f"""
                        <div class="info-box" style="font-size:12px;">
                        Mean bias: <b>{resid_test.mean():.2f}</b><br>
                        MAE resid: <b>{np.abs(resid_test).mean():.2f}</b><br>
                        Std resid: <b>{resid_test.std():.2f}</b><br>
                        Shapiro-Wilk p: <b>{sw_p_str}</b>
                        {normal_msg}
                        </div>
                        """, unsafe_allow_html=True)

                    except Exception as e:
                        st.warning(f"Residual plot error: {str(e)[:100]}")
                        st.markdown(f"""
                        <div class="info-box">
                        <b>Residual Summary</b><br>
                        Mean: {resid_test.mean():.2f}<br>
                        Std: {resid_test.std():.2f}<br>
                        Min: {resid_test.min():.2f}<br>
                        Max: {resid_test.max():.2f}<br>
                        N: {len(resid_test)}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("Residual data is too limited or constant for plotting.")
            else:
                st.info("Not enough data points for residual analysis.")
    else:
        st.warning("No sklearn models could be loaded. Check paths in MODEL_FILES.")

# ─────────────────────────────────────────────────────────────────────
# TAB 4 · Zone Analysis
# ─────────────────────────────────────────────────────────────────────
with tab4:
    st.markdown("## Health Zone Analysis")
    if len(zones) > 0:
        col1, col2 = st.columns([2, 1])

        with col1:
            zl = zone_latest.copy()
            zl = zl.dropna(subset=['value'])
            zl = zl[zl['value'] > 0]
            zl = zl.sort_values('value', ascending=False)
            zl = zl.head(min(15, len(zl)))

            if len(zl) == 0:
                st.warning("No zone data available after cleaning.")
            else:
                with safe_plot():
                    fig, axes = plt.subplots(1, 2, figsize=(12, 5), dpi=72)

                    ax = axes[0]
                    zl_sorted = zl.sort_values('value')
                    mv = zl_sorted['value'].max() or 1

                    cz = [
                        PALETTE[1] if v / mv > 0.6 else
                        PALETTE[3] if v / mv > 0.3 else
                        PALETTE[0]
                        for v in zl_sorted['value']
                    ]

                    ax.barh(zl_sorted['zone'], zl_sorted['value'],
                            color=cz, edgecolor='white', alpha=0.88)
                    ax.axvline(risk_thr, color='red', ls='--', lw=1.5,
                               label=f'Risk threshold ({int(risk_thr):,})')
                    ax.set_title(f"Top {len(zl_sorted)} Health Zones", fontweight='bold')
                    ax.set_xlabel("Cumulative confirmed cases")
                    ax.legend(fontsize=9)

                    for p, v in zip(ax.patches, zl_sorted['value']):
                        if v > 1:
                            ax.text(p.get_width() + max(1, mv * 0.01),
                                    p.get_y() + p.get_height() / 2,
                                    f"{int(v):,}", va='center', fontsize=8)

                    ax.spines[['top', 'right']].set_visible(False)

                    ax = axes[1]
                    top5_zones = zl.head(5)['zone'].values
                    for k, z in enumerate(top5_zones):
                        zd = raw_df[raw_df['zone'] == z].sort_values('date')
                        if not zd.empty:
                            ax.plot(zd['date'], zd['value'],
                                    lw=2, label=z, color=PALETTE[k % len(PALETTE)])

                    ax.set_title("Evolution — Top 5 Zones", fontweight='bold')
                    ax.set_ylabel("Cumulative cases")
                    ax.legend(fontsize=9)
                    ax.grid(True, alpha=0.25)
                    ax.tick_params(axis='x', rotation=25)
                    ax.spines[['top', 'right']].set_visible(False)

                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close()

        with col2:
            st.markdown("#### Zone Risk Table")
            zr = zone_latest.copy()
            zr = zr.dropna(subset=['value'])
            if not zr.empty:
                max_val = zr['value'].max() or 1
                zr['Risk %'] = (zr['value'] / max_val * 100).round(1)
                zr['Level'] = zr['value'].apply(
                    lambda v: '🔴 HIGH' if v > risk_thr else
                              '🟡 MODERATE' if v > risk_thr * 0.4 else
                              '🟢 LOW'
                )
                st.dataframe(
                    zr[['zone', 'value', 'Risk %', 'Level']].rename(
                        columns={'zone': 'Zone', 'value': 'Cases'}
                    ),
                    hide_index=True, use_container_width=True
                )
                n_high = (zr['Level'] == '🔴 HIGH').sum()
                st.markdown(f"""
                <div class="info-box">
                <b>Summary</b><br>
                Total zones: <b>{len(zones)}</b><br>
                High risk: <b>{n_high}</b><br>
                Threshold: <b>{int(risk_thr):,} cases</b> ({risk_pct}th pct)
                </div>""", unsafe_allow_html=True)
    else:
        st.info("Upload a multi-zone CSV to see zone analysis.")

# ─────────────────────────────────────────────────────────────────────
# TAB 5 · Report
# ─────────────────────────────────────────────────────────────────────
with tab5:
    st.markdown("## Exportable Report")

    report = {
        'title': 'BAEL-Ebola Forecasting Report — Bundibugyo 2026',
        'generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'institution': "Université de l'Assomption au Congo (UAC), Butembo, DRC",
        'framework': 'BAEL · Behavior-Aware Explainability Loop',
        'active_model': active_model,
        'data': {
            'total_cases': int(nat['value'].max()),
            'n_zones': len(zones),
            'last_date': last_dt,
            'train_obs': len(train_df),
            'test_obs': len(test_df),
        },
        'parameters': {
            'few_shot_k': n_shots,
            'test_ratio': test_ratio,
            'risk_pct': risk_pct,
        },
        'metrics': {k: dict(v) for k, v in all_metrics.items() if v},
        'risk': {
            'threshold': round(risk_thr, 2),
            'growth_rate_last': round(gr_last, 2),
        },
        'forecast': {
            'bootstrap_mean': round(ci_fc['mean'], 2),
            'bootstrap_median': round(ci_fc['median'], 2),
            'ci_95_lower': round(ci_fc['lower'], 2),
            'ci_95_upper': round(ci_fc['upper'], 2),
            'bootstrap_n': n_boot,
            'sir_r0': r0_val,
            'horizon_days': horizon,
        },
    }

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Report Preview")
        
        # Clean report display as a table
        report_items = [
            ("**Generated**", report['generated']),
            ("**Institution**", report['institution']),
            ("**Active Model**", report['active_model']),
            ("**Total Cases**", f"{report['data']['total_cases']:,}"),
            ("**Health Zones**", report['data']['n_zones']),
            ("**Last Date**", report['data']['last_date']),
            ("**Risk Threshold**", f"{report['risk']['threshold']:.2f}"),
            ("**Growth Rate**", f"{report['risk']['growth_rate_last']:.2f}%"),
            ("**Forecast Mean**", f"{report['forecast']['bootstrap_mean']:.0f}"),
            ("**95% CI**", f"[{report['forecast']['ci_95_lower']:.0f} — {report['forecast']['ci_95_upper']:.0f}]"),
        ]
        
        st.markdown(
            "\n".join([f"| {k} | {v} |" for k, v in report_items]),
            unsafe_allow_html=True
        )

    with col2:
        st.markdown("#### Downloads")
        st.download_button(
            "⬇️ JSON Report",
            data=json.dumps(report, indent=2, ensure_ascii=False).encode('utf-8'),
            file_name=f"bael_ebola_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",
            use_container_width=True
        )

        forecast_csv = pd.DataFrame({
            'date': [nat['date'].max() + timedelta(days=i+1) for i in range(horizon)],
            'sir_projection': sir_proj.round(1),
        })
        st.download_button(
            "⬇️ Forecast CSV",
            data=forecast_csv.to_csv(index=False).encode('utf-8'),
            file_name=f"bael_forecast_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

        st.download_button(
            "⬇️ Raw Data CSV",
            data=raw_df.to_csv(index=False).encode('utf-8'),
            file_name=f"bael_data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

        st.markdown("---")
        st.markdown("#### Model Status")
        for k, v in MODEL_STATUS.items():
            icon = "✅" if "Loaded" in v else "❌"
            st.markdown(f"`{icon} {k}` — {v.split(':')[0]}")

        st.markdown("#### Model Performance")
        if all_metrics:
            perf_df = pd.DataFrame(all_metrics).T.reset_index()
            perf_df.columns = ['Model', 'RMSE', 'MAE', 'R²', 'MAPE%']
            styled = perf_df.style.highlight_max(subset=['R²'], color='#E8F5E9')
            st.dataframe(styled, hide_index=True, use_container_width=True)

        st.markdown("#### LaTeX Code")
        if all_metrics:
            latex = ("\\begin{table}[htbp]\n\\centering\n"
                     "\\caption{Model Comparison --- Ebola Bundibugyo 2026}\n"
                     "\\label{tab:models}\n"
                     "\\begin{tabular}{lrrrr}\n\\toprule\n"
                     "\\textbf{Model} & \\textbf{RMSE} & \\textbf{MAE} "
                     "& \\textbf{R$^2$} & \\textbf{MAPE\\%} \\\\\n\\midrule\n")
            for name, m in all_metrics.items():
                latex += f"{name} & {m['RMSE']} & {m['MAE']} & {m['R²']} & {m['MAPE%']} \\\\\n"
            latex += "\\bottomrule\n\\end{tabular}\n\\end{table}"
            st.code(latex, language='latex')
            st.caption("📋 Copy this LaTeX code for use in Overleaf or any LaTeX editor.")

# ── Footer ────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#90A4AE;font-size:12px;'>"
    "BAEL-Ebola · Université de l'Assomption au Congo (UAC) · Butembo, Nord-Kivu, DRC · "
    "PhD AI · Behavior-Aware Explainability Loop"
    "</div>",
    unsafe_allow_html=True
)