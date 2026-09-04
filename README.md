# 🦠 BAEL-Ebola — Multi-Epidemic Forecasting Dashboard

> **MSCS Computer Science · University of the Philippines Diliman · Philippines, Quezon City, PH**  
> Behavior-Aware Explainability Loop (BAEL) Framework

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-red)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.0.0-orange)](app.py)

---

## 📋 Overview

BAEL-Ebola is a production-ready epidemiological forecasting dashboard built for
real-time surveillance and decision support during Ebola outbreaks in the DRC.
It integrates Transfer Learning, Few-Shot Learning, Spatio-Temporal GNNs, and
classical ML models within the BAEL framework — making AI forecasts transparent,
explainable, and actionable for public health authorities.

The app is **multi-epidemic**: switching between outbreaks (Ebola Bundibugyo 2026,
Nord-Kivu 2018-2020, Mpox DRC, or any custom epidemic) requires no code changes —
just selecting from the sidebar dropdown.

---

## ✨ Features

| Category | Features |
|----------|----------|
| **Epidemiology** | Cumulative/daily trends · Deaths & recovered · CFR · Growth rate · Temporal comparison |
| **Forecasting** | XGBoost · RandomForest · LightGBM · Ridge · TL-LSTM · GNN-GraphSAGE · SIR · Bootstrap CI |
| **Zone Analysis** | Per-zone case maps · GNN propagation graph · Zone-level forecasts · Resource calculator |
| **Explainability** | SHAP · LIME · Feature importance · Residual analysis |
| **Comparison** | 8 historical Ebola outbreaks · CFR · Duration · Severity ranking |
| **Advanced** | Walk-Forward Validation · Anomaly detection · Trend breakpoints · Zone clustering · Sensitivity analysis |
| **Notifications** | Email (SMTP) · Webhook (Slack/Teams) · Configurable thresholds · Alert log |
| **Multi-language** | English · Français · Lingala · Kiswahili |
| **Export** | PDF scientific report · Excel · CSV · JSON · Walk-Forward results |
| **Offline** | Full dashboard snapshot saved to disk |
| **AI Assistant** | Natural language queries on all dashboard data |
| **Dark Mode** | Full CSS dark theme toggle |
| **Responsive** | Mobile-optimised layout |

---

## 🗂️ Tab Structure

| # | Tab | Description |
|---|-----|-------------|
| 1 | 📈 Epidemiology | National trends, outcomes, temporal comparison |
| 2 | 🔮 Forecast | Model forecasts, CI, SIR, forecast history, zone forecasts |
| 3 | 🗺️ Zone Analysis | Zone maps, GNN graph, resource calculator |
| 4 | 🧠 Explainability | SHAP, LIME, feature importance |
| 5 | 📊 Epidemic Comparison | Historical context vs 8 past outbreaks |
| 6 | 🔬 Advanced Analysis | Trend, anomaly, correlation, clustering, sensitivity |
| 7 | 📊 Model Comparison | All-model metrics, Walk-Forward Validation |
| 8 | 📊 Custom Dashboard | Configurable widget layout |
| 9 | 📋 Report | Exportable JSON report |
| 10 | 🤖 AI Assistant | Natural language chatbot |
| 11 | 📚 Publications | References and BAEL framework citations |
---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/KasMoise/bael-ebola-dashboard.git
cd bael-ebola-dashboard


### 2. Create a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate
```

### 3. Install dependencies

**Core (required):**
```bash
pip install streamlit pandas numpy matplotlib scipy scikit-learn \
            xgboost lightgbm reportlab openpyxl requests
```

**Interactive map (recommended):**
```bash
pip install folium streamlit-folium geopandas
```

**Auto-refresh (optional):**
```bash
pip install streamlit-autorefresh
```

**Deep learning models (optional — required for TL-LSTM & GNN):**
```bash
pip install torch torch-geometric
```

### 4. Run the app

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## 📁 Project Structure

```
bael-ebola-dashboard/
│
├── app.py              # Main application (7 500+ lines)
│
├── saved_models/             # Pre-trained model files (shared across epidemics)
│   ├── XGBoost.pkl
│   ├── RandomForest.pkl
│   ├── LightGBM.pkl
│   ├── LinearRegression.pkl
│   ├── Ridge.pkl
│   ├── scaler.pkl
│   ├── tl_lstm.pt            # Transfer Learning LSTM
│   └── gnn_model.pt          # GNN-GraphSAGE
│
├── donnees_ebola/            # Downloaded INRB release archives
├── donnees_extraites/        # Extracted CSV files
│   └── build/
│       ├── drc_health_zones.geojson
│       └── long/
│           ├── insp_sitrep__cumulative_confirmed_cases.csv
│           ├── insp_sitrep__national_cumulative_confirmed_cases.csv
│           ├── insp_sitrep__national_cumulative_confirmed_deaths.csv
│           ├── insp_sitrep__national_cumulative_recovered_cases.csv
│           └── insp_sitrep__new_confirmed_cases.csv
│
├── bael_offline_cache.pkl    # Offline snapshot (auto-generated)
├── bael_offline_meta.json    # Snapshot metadata
│
└── README.md
```

---

## 📊 Data Sources

| Source | Type | Update frequency |
|--------|------|-----------------|
| **INRB-UMIE GitHub** | Surveillance CSVs | Daily during active outbreak |
| **WHO Ebola Reports** | Historical context | Static |
| **OpenWeatherMap API** | Weather (Butembo) | Every 30 min |
| **UN Population API** | Demographics DRC | Annual |
| **Demo data** | Synthetic (fallback) | On demand |

### Loading real INRB data

1. Select **Real data (INRB)** in the sidebar
2. Click **⬇️ Download & Update Data**
3. The app fetches the latest release from the INRB GitHub and extracts it

CSV format required for manual upload:
```
zone,date,value
Butembo,2026-01-15,42
Beni,2026-01-15,18
...
```

---

## 🦠 Multi-Epidemic Support

The app supports multiple epidemics via `EPIDEMIC_CONFIGS` in `demo2_app.py`.

### Pre-configured epidemics

| Epidemic | Strain | Status |
|----------|--------|--------|
| Ebola Bundibugyo 2026 — DRC | Bundibugyo ebolavirus | 🟢 Active |
| Ebola Nord-Kivu 2018-2020 — DRC | Zaire ebolavirus | 🔬 Historical |
| Mpox DRC 2023-2024 | Monkeypox clade Ib | 🔬 Historical |
| ➕ Add New Epidemic (Template) | — | Template |

### Adding a new epidemic

Copy the template entry in `EPIDEMIC_CONFIGS` and fill in:

```python
"My New Epidemic 2025": {
    "id":               "my_epidemic_2025",
    "display_name":     "My Epidemic 2025",
    "subtitle_en":      "My Epidemic Dashboard · 2025",
    "country":          "DRC",
    "province":         "Province name",
    "strain":           "Pathogen name",
    "pathogen":         "Ebola",          # or "Mpox", "Cholera", etc.
    "start_year":       2025,
    "demo_start_date":  "2025-01-01",
    "demo_zones":       ["Zone A", "Zone B", "Zone C"],
    "map_center":       [lat, lon],
    "map_zoom":         7,
    "default_cfr_sim":  0.05,
    "default_rec_sim":  0.70,
    "risk_threshold":   50,
    "sir_r0_default":   1.5,
    "github_url":       "https://api.github.com/repos/.../releases",
    "data_dir":         "donnees_my_epidemic",
    "extract_dir":      "donnees_my_epidemic_extracted",
    "geojson":          "path/to/health_zones.geojson",
    "csv_map":          { ... },          # same keys as default
    "report_title":     "BAEL Report — My Epidemic 2025",
    "who_outbreak_name":"My Epidemic",
    "icon":             "🦠",
    "color_primary":    "#1A237E",
    "is_active":        True,
},
```

No other code changes required.

---

## 🤖 ML Models

| Model | Type | File |
|-------|------|------|
| XGBoost | Gradient Boosting | `saved_models/XGBoost.pkl` |
| RandomForest | Ensemble | `saved_models/RandomForest.pkl` |
| LightGBM | Gradient Boosting | `saved_models/LightGBM.pkl` |
| Ridge | Linear | `saved_models/LinearRegression.pkl` |
| TL-LSTM | Transfer Learning LSTM | `saved_models/tl_lstm.pt` |
| GNN-GraphSAGE | Graph Neural Network | `saved_models/gnn_model.pt` |

**Feature engineering** (19 features):
```
dow, month, doy, week, zone_enc,
lag_1, lag_3, lag_7, lag_14, lag_21, lag_30,
roll_mean_3, roll_mean_7, roll_mean_14,
roll_std_3, roll_std_7, roll_std_14,
growth_rate, zone_cumul
```

---

## 🔔 Email Notifications Setup

1. Open **Alerts & Notifications** in the sidebar
2. Go to the **📧 Email Alert** tab
3. Fill in SMTP credentials:

| Field | Gmail example |
|-------|--------------|
| SMTP host | `smtp.gmail.com` |
| SMTP port | `587` |
| Username | `your@gmail.com` |
| Password | **App Password** (not main password) |
| STARTTLS | ✅ checked |

> **Gmail**: Enable 2FA → Google Account → Security → App Passwords → generate one for "BAEL-Ebola".

---

## 🌤️ Weather API Setup (optional)

1. Register at [openweathermap.org](https://openweathermap.org/api) (free tier)
2. The API key is set directly in `demo2_app.py`:
```python
api_key = "your_api_key_here"   # in fetch_weather_data()
```

---

## 🌍 Languages

Switch language in the sidebar. Supported:

| Code | Language | Coverage |
|------|----------|----------|
| `en` | 🇬🇧 English | Full |
| `fr` | 🇫🇷 Français | Full |
| `ln` | 🇨🇩 Lingala | Full |
| `sw` | 🇹🇿 Kiswahili | Full |

To add a language, add an entry to `_TRANSLATIONS` in `app.py`.

---

## 📖 Scientific Framework

This dashboard implements the **BAEL (Behavior-Aware Explainability Loop)** framework:

```
Data (INRB) → Feature Engineering → Few-Shot Split
     ↓
ML Models (XGBoost, RF, LightGBM, Ridge)
     +
Transfer Learning LSTM (cross-outbreak knowledge)
     +
GNN-GraphSAGE (spatio-temporal propagation)
     ↓
Bootstrap Forecast + SIR Mechanistic Model
     ↓
Walk-Forward Validation → Explainability (SHAP/LIME)
     ↓
Dashboard → Alerts → Resource Planning → PDF Report
```

### Key references

- **INRB-UMIE** — Institut National de Recherche Biomédicale, DRC
- **WHO Ebola Situation Reports** — weekly surveillance updates
- **MSF Ebola Response Guidelines** — resource ratio benchmarks
- Verity et al. (2020) — *Lancet Infectious Diseases* — CFR methodology

---

## 🏥 Resource Calculator Ratios

Based on WHO/MSF Ebola field protocols:

| Resource | Ratio | Basis |
|----------|-------|-------|
| ETU beds | 1.2 per active case | 20% safety buffer |
| Healthcare workers | 3 per active case | 3 shifts |
| PPE kits/day | 6 per new case/day | 3 shifts × 2 workers |
| Contact tracers | 1 per 2 new cases/day | WHO standard |
| Ambulances | 1 per 15 active cases | MSF field ratio |
| Lab kits/day | 3 per new case/day | Sensitivity buffer |

---

## ⚙️ Configuration

Key constants in `app.py`:

```python
# Model directory
MODEL_DIR = Path("saved_models")

# Alert thresholds (adjustable in sidebar)
ALERT_THRESHOLDS = {
    'growth_rate_critical':  20.0,   # %
    'growth_rate_elevated':   5.0,   # %
    'new_cases_7d_critical': 500,
    'new_cases_7d_warning':  100,
    'total_cases_critical':  5000,
    'total_cases_warning':   2000,
    'high_risk_zones_critical': 15,
    'high_risk_zones_warning':   5,
}

# App version
_APP_VERSION = "1.0.0"
```

---

## 🐛 Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `NameError: name 'X' is not defined` | Function called before definition | Ensure functions are defined before `st.tabs()` |
| `SliderError: min >= max` | Small dataset (demo data) | Normal — slider adapts to data size |
| `ArrowTypeError: Expected bytes, got int` | Mixed types in DataFrame column | All values cast to `str` before `st.dataframe()` |
| `SMTP Authentication Failed` | Wrong credentials | Use App Password for Gmail, not main password |
| `No internet connection` | GitHub API unreachable | Use Demo data or Upload CSV |
| Map not showing | `folium`/`geopandas` not installed | `pip install folium streamlit-folium geopandas` |
| GeoJSON not found | Data not downloaded | Click **Download & Update Data** |

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/new-epidemic`
3. Add your epidemic config to `EPIDEMIC_CONFIGS`
4. Test with demo data
5. Submit a pull request

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 👤 Author

**KAMBALE KASAMBYA MOISE** — MSCS candidate in Computer Science  
University of the Philippines Diliman· Quezon City, Philippines, PH  
Research: Explainable AI · Spatio-temporal GNNs · Transfer Learning · Public Health  
Framework: **BAEL — Behavior-Aware Explainability Loop**

---

*BAEL-Ebola v1.0.0 · UP Diliman · MSCS Computer Science · 2026*
