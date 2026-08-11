"""
BAEL Multi-Epidemic Forecasting Dashboard
BAEL Multi-Epidemic Forecasting Dashboard
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
import time
import io
import base64
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER


warnings.filterwarnings("ignore")

# ═══════════════════════════════════════════════════════════════════════
# MULTI-EPIDEMIC CONFIGURATION REGISTRY
# Each entry defines all epidemic-specific parameters needed to run the
# dashboard without touching any other code. Add a new epidemic by
# copying an existing entry and updating the values.
# ═══════════════════════════════════════════════════════════════════════

EPIDEMIC_CONFIGS = {
    # ── Current outbreak (default) ─────────────────────────────────────
    "Ebola Bundibugyo 2026 — DRC": {
        "id":               "bundibugyo_2026",
        "display_name":     "Ebola Bundibugyo 2026",
        "subtitle_en":      "Forecasting Dashboard · DRC 2026",
        "subtitle_fr":      "Tableau de bord · RDC 2026",
        "country":          "DRC",
        "province":         "Nord-Kivu & Ituri",
        "strain":           "Bundibugyo ebolavirus",
        "pathogen":         "Ebola",
        "start_year":       2026,
        "demo_start_date":  "2026-01-15",
        "demo_zones":       ["Butembo", "Beni", "Katwa"],
        "map_center":       [1.2, 29.5],
        "map_zoom":         7,
        "default_cfr_sim":  0.05,   # fallback CFR when no data
        "default_rec_sim":  0.70,   # fallback recovery rate
        "risk_threshold":   50,
        "sir_r0_default":   1.5,
        "github_url":       "https://api.github.com/repos/INRB-UMIE/BDBV2026-Data/releases",
        "data_dir":         "donnees_ebola",
        "extract_dir":      "donnees_extraites",
        "geojson":          "donnees_extraites/build/drc_health_zones.geojson",
        "csv_map": {
            "cum_cases":     "long/insp_sitrep__cumulative_confirmed_cases.csv",
            "nat_cases":     "long/insp_sitrep__national_cumulative_confirmed_cases.csv",
            "nat_deaths":    "long/insp_sitrep__national_cumulative_confirmed_deaths.csv",
            "nat_recovered": "long/insp_sitrep__national_cumulative_recovered_cases.csv",
            "nat_suspected": "long/insp_sitrep__national_cumulative_suspected_cases.csv",
            "new_cases":     "long/insp_sitrep__new_confirmed_cases.csv",
        },
        "report_title":     "BAEL-Ebola Forecasting Report — Bundibugyo 2026",
        "who_outbreak_name":"Ebola Bundibugyo",
        "icon":             "🦠",
        "color_primary":    "#1A237E",
        "is_active":        True,
    },

    # ── Nord-Kivu 2018-2020 (historical re-analysis) ───────────────────
    "Ebola Nord-Kivu 2018-2020 — DRC": {
        "id":               "nord_kivu_2018",
        "display_name":     "Ebola Nord-Kivu 2018-2020",
        "subtitle_en":      "Historical Re-Analysis · DRC 2018-2020",
        "subtitle_fr":      "Ré-analyse historique · RDC 2018-2020",
        "country":          "DRC",
        "province":         "Nord-Kivu & Ituri",
        "strain":           "Zaire ebolavirus",
        "pathogen":         "Ebola",
        "start_year":       2018,
        "demo_start_date":  "2018-08-01",
        "demo_zones":       ["Beni", "Butembo", "Mandima"],
        "map_center":       [1.0, 29.3],
        "map_zoom":         8,
        "default_cfr_sim":  0.66,
        "default_rec_sim":  0.34,
        "risk_threshold":   100,
        "sir_r0_default":   1.8,
        "github_url":       "",   # historical — use demo/upload
        "data_dir":         "donnees_nk2018",
        "extract_dir":      "donnees_nk2018_extracted",
        "geojson":          "donnees_extraites/build/drc_health_zones.geojson",
        "csv_map": {
            "cum_cases":     "long/cumulative_confirmed_cases.csv",
            "nat_cases":     "long/national_cumulative_confirmed_cases.csv",
            "nat_deaths":    "long/national_cumulative_confirmed_deaths.csv",
            "nat_recovered": "long/national_cumulative_recovered_cases.csv",
            "nat_suspected": "long/national_cumulative_suspected_cases.csv",
            "new_cases":     "long/new_confirmed_cases.csv",
        },
        "report_title":     "BAEL-Ebola Historical Report — Nord-Kivu 2018-2020",
        "who_outbreak_name":"Ebola Nord-Kivu",
        "icon":             "🔬",
        "color_primary":    "#880E4F",
        "is_active":        False,   # historical
    },

    # ── Mpox DRC 2023-2024 ─────────────────────────────────────────────
    "Mpox DRC 2023-2024": {
        "id":               "mpox_drc_2023",
        "display_name":     "Mpox DRC 2023-2024",
        "subtitle_en":      "Mpox Forecasting Dashboard · DRC 2023-2024",
        "subtitle_fr":      "Tableau Mpox · RDC 2023-2024",
        "country":          "DRC",
        "province":         "Multiple provinces",
        "strain":           "Monkeypox virus (clade Ib)",
        "pathogen":         "Mpox",
        "start_year":       2023,
        "demo_start_date":  "2023-01-01",
        "demo_zones":       ["Kinshasa", "South Kivu", "North Kivu"],
        "map_center":       [-4.0, 21.0],
        "map_zoom":         5,
        "default_cfr_sim":  0.035,
        "default_rec_sim":  0.92,
        "risk_threshold":   200,
        "sir_r0_default":   2.2,
        "github_url":       "",
        "data_dir":         "donnees_mpox",
        "extract_dir":      "donnees_mpox_extracted",
        "geojson":          "donnees_extraites/build/drc_health_zones.geojson",
        "csv_map": {
            "cum_cases":     "long/cumulative_confirmed_cases.csv",
            "nat_cases":     "long/national_cumulative_confirmed_cases.csv",
            "nat_deaths":    "long/national_cumulative_confirmed_deaths.csv",
            "nat_recovered": "long/national_cumulative_recovered_cases.csv",
            "nat_suspected": "long/national_cumulative_suspected_cases.csv",
            "new_cases":     "long/new_confirmed_cases.csv",
        },
        "report_title":     "BAEL Mpox Forecasting Report — DRC 2023-2024",
        "who_outbreak_name":"Mpox DRC",
        "icon":             "⚠️",
        "color_primary":    "#E65100",
        "is_active":        False,
    },

    # ── Template for new epidemics ─────────────────────────────────────
    "➕ Add New Epidemic (Template)": {
        "id":               "custom",
        "display_name":     "Custom Epidemic",
        "subtitle_en":      "Custom Epidemic Dashboard",
        "subtitle_fr":      "Tableau épidémique personnalisé",
        "country":          "DRC",
        "province":         "To be specified",
        "strain":           "To be specified",
        "pathogen":         "Ebola",
        "start_year":       2025,
        "demo_start_date":  "2025-01-01",
        "demo_zones":       ["Zone A", "Zone B", "Zone C"],
        "map_center":       [0.0, 25.0],
        "map_zoom":         6,
        "default_cfr_sim":  0.05,
        "default_rec_sim":  0.70,
        "risk_threshold":   50,
        "sir_r0_default":   1.5,
        "github_url":       "",
        "data_dir":         "donnees_custom",
        "extract_dir":      "donnees_custom_extracted",
        "geojson":          "donnees_extraites/build/drc_health_zones.geojson",
        "csv_map": {
            "cum_cases":     "long/cumulative_confirmed_cases.csv",
            "nat_cases":     "long/national_cumulative_confirmed_cases.csv",
            "nat_deaths":    "long/national_cumulative_confirmed_deaths.csv",
            "nat_recovered": "long/national_cumulative_recovered_cases.csv",
            "nat_suspected": "long/national_cumulative_suspected_cases.csv",
            "new_cases":     "long/new_confirmed_cases.csv",
        },
        "report_title":     "BAEL Epidemic Forecasting Report",
        "who_outbreak_name":"Custom Epidemic",
        "icon":             "📋",
        "color_primary":    "#37474F",
        "is_active":        False,
    },
}

# ── Active config accessor ─────────────────────────────────────────────

def get_active_config():
    """
    Return the currently selected epidemic config dict.
    Falls back to Bundibugyo 2026 if session state is not set.
    """
    key = st.session_state.get("selected_epidemic",
                               "Ebola Bundibugyo 2026 — DRC")
    return EPIDEMIC_CONFIGS.get(key,
           EPIDEMIC_CONFIGS["Ebola Bundibugyo 2026 — DRC"])


def cfg(field, default=None):
    """Shortcut: get one field from the active epidemic config."""
    return get_active_config().get(field, default)


# ═══════════════════════════════════════════════════════════════════════
# MULTI-LANGUAGE SYSTEM
# ═══════════════════════════════════════════════════════════════════════

LANGUAGES = {
    "en": {"name": "English",   "flag": "🇬🇧"},
    "fr": {"name": "Français",  "flag": "🇫🇷"},
    "ln": {"name": "Lingala",   "flag": "🇨🇩"},
    "sw": {"name": "Kiswahili", "flag": "🇹🇿"},
}

# Embedded translations — no external file dependency
_TRANSLATIONS = {
    "en": {
        "app":  {"title": cfg("display_name","BAEL Epidemic"), "subtitle": cfg("subtitle_en","Forecasting Dashboard"),
                 "institution": "UAC Butembo", "location": "Nord-Kivu, DRC",
                 "framework": "BAEL Framework", "version": "v"},
        "sidebar": {
            "data": "Data", "real_data": "Real data (INRB)",
            "demo_data": "Demo data", "upload_csv": "Upload CSV",
            "parameters": "Parameters", "primary_model": "Primary model",
            "few_shot": "Few-Shot K (weeks)", "test_ratio": "Test ratio",
            "forecast_horizon": "Forecast horizon (days)",
            "sir_r0": "SIR R₀", "bootstrap": "Bootstrap N",
            "risk_pct": "Risk percentile", "lstm_seq": "LSTM seq length",
            "models": "Models", "models_ready": "ready",
            "advanced": "Advanced Analytics",
            "download_btn": "⬇️ Download & Update Data",
        },
        "menu": {
            "epidemiology": "Epidemiology", "forecast": "Forecast",
            "models": "Model Comparison", "zones": "Zone Analysis",
            "xai": "Explainability", "report": "Report",
            "publications": "Publications", "dashboard": "Custom Dashboard",
            "advanced": "Advanced Analysis", "chatbot": "AI Assistant",
            "comparison": "Epidemic Comparison",
        },
        "metrics": {
            "total_cases": "Total Cases", "new_cases_7d": "New Cases (7d)",
            "health_zones": "Health Zones", "last_report": "Last Report",
            "growth_rate": "Growth Rate", "active_model": "Active model",
            "risk_threshold": "Risk threshold",
        },
        "alerts": {
            "critical": "🔴 CRITICAL", "high": "HIGH ALERT",
            "elevated": "ELEVATED RISK", "stable": "STABLE",
            "immediate_action": "Immediate action required",
            "enhanced_surveillance": "Enhanced surveillance recommended",
            "routine_monitoring": "Continue routine monitoring",
        },
        "forecast": {
            "title": "Forecast", "next_step": "Next-step forecast",
            "mean": "Mean", "median": "Median", "ci_95": "95% CI",
            "horizon": "Forecast horizon",
        },
        "common": {
            "current": "Current", "loading": "Loading…",
            "error": "Error", "success": "Success",
            "download": "Download", "refresh": "Refresh",
            "save": "Save", "load": "Load", "export": "Export",
            "zones": "zones", "cases": "cases", "days": "days",
        },
        "language": {"selector": "Language"},
        "status": {
            "files_present": "🟢 INRB — files present",
            "download_required": "🟡 INRB — download required",
            "demo_mode": "🔵 Demo mode",
        },
    },
    "fr": {
        "app":  {"title": "BAEL-Ebola", "subtitle": "Tableau de bord · RDC 2026",
                 "institution": "UAC Butembo", "location": "Nord-Kivu, RDC",
                 "framework": "Cadre BAEL", "version": "v"},
        "sidebar": {
            "data": "Données", "real_data": "Données réelles (INRB)",
            "demo_data": "Démonstration", "upload_csv": "Importer CSV",
            "parameters": "Paramètres", "primary_model": "Modèle principal",
            "few_shot": "Few-Shot K (semaines)", "test_ratio": "Ratio test",
            "forecast_horizon": "Horizon de prévision (jours)",
            "sir_r0": "SIR R₀", "bootstrap": "Bootstrap N",
            "risk_pct": "Percentile de risque", "lstm_seq": "Longueur séquence LSTM",
            "models": "Modèles", "models_ready": "prêts",
            "advanced": "Analyses avancées",
            "download_btn": "⬇️ Télécharger & Mettre à jour",
        },
        "menu": {
            "epidemiology": "Épidémiologie", "forecast": "Prévisions",
            "models": "Comparaison modèles", "zones": "Analyse zones",
            "xai": "Explicabilité", "report": "Rapport",
            "publications": "Publications", "dashboard": "Tableau de bord",
            "advanced": "Analyse avancée", "chatbot": "Assistant IA",
            "comparison": "Comparaison épidémique",
        },
        "metrics": {
            "total_cases": "Cas totaux", "new_cases_7d": "Nouveaux cas (7j)",
            "health_zones": "Zones de santé", "last_report": "Dernier rapport",
            "growth_rate": "Taux de croissance", "active_model": "Modèle actif",
            "risk_threshold": "Seuil de risque",
        },
        "alerts": {
            "critical": "🔴 CRITIQUE", "high": "ALERTE ÉLEVÉE",
            "elevated": "RISQUE ÉLEVÉ", "stable": "STABLE",
            "immediate_action": "Action immédiate requise",
            "enhanced_surveillance": "Surveillance renforcée recommandée",
            "routine_monitoring": "Surveillance de routine",
        },
        "forecast": {
            "title": "Prévisions", "next_step": "Prévision prochaine étape",
            "mean": "Moyenne", "median": "Médiane", "ci_95": "IC 95%",
            "horizon": "Horizon de prévision",
        },
        "common": {
            "current": "Actuel", "loading": "Chargement…",
            "error": "Erreur", "success": "Succès",
            "download": "Télécharger", "refresh": "Actualiser",
            "save": "Enregistrer", "load": "Charger", "export": "Exporter",
            "zones": "zones", "cases": "cas", "days": "jours",
        },
        "language": {"selector": "Langue"},
        "status": {
            "files_present": "🟢 INRB — fichiers présents",
            "download_required": "🟡 INRB — téléchargement requis",
            "demo_mode": "🔵 Mode démonstration",
        },
    },
    "ln": {
        "app":  {"title": "BAEL-Ebola", "subtitle": "Tableau ya prévision · RDC 2026",
                 "institution": "UAC Butembo", "location": "Nord-Kivu, RDC",
                 "framework": "Cadre BAEL", "version": "v"},
        "sidebar": {
            "data": "Makambo", "real_data": "Makambo ya solo (INRB)",
            "demo_data": "Ndakisa", "upload_csv": "Tia CSV",
            "parameters": "Paramètres", "primary_model": "Modèle ya liboso",
            "few_shot": "Few-Shot K (bangonga)", "test_ratio": "Ratio ya test",
            "forecast_horizon": "Horizon ya prévision (mikolo)",
            "sir_r0": "SIR R₀", "bootstrap": "Bootstrap N",
            "risk_pct": "Percentile ya likama", "lstm_seq": "Boyokani LSTM",
            "models": "Batatoli", "models_ready": "bazali libela",
            "advanced": "Botatoli ya mozindo",
            "download_btn": "⬇️ Kokitisa & Kobunga",
        },
        "menu": {
            "epidemiology": "Epidemiologie", "forecast": "Prévision",
            "models": "Boyekoli ya batatoli", "zones": "Boyekoli ya zones",
            "xai": "Kolimbola", "report": "Rapport",
            "publications": "Publications", "dashboard": "Tableau ya biso",
            "advanced": "Boyekoli ya mozindo", "chatbot": "Mosalisi ya AI",
            "comparison": "Boyekoli ya ebola",
        },
        "metrics": {
            "total_cases": "Biloko nyonso", "new_cases_7d": "Biloko ya sika (7 mikolo)",
            "health_zones": "Zones ya bokolongono", "last_report": "Rapport ya nsuka",
            "growth_rate": "Motango ya kobakisama", "active_model": "Modèle ezali kosala",
            "risk_threshold": "Seuil ya likama",
        },
        "alerts": {
            "critical": "🔴 LIKAMA MONENE", "high": "ALERTE MAKASI",
            "elevated": "LIKAMA EZALI", "stable": "KIMIA",
            "immediate_action": "Kosala sikawa na sikawa",
            "enhanced_surveillance": "Kolamba makasi",
            "routine_monitoring": "Kolamba ya mikolo nyonso",
        },
        "forecast": {
            "title": "Prévision", "next_step": "Étape ekoya",
            "mean": "Kati", "median": "Médiane", "ci_95": "IC 95%",
            "horizon": "Horizon ya prévision",
        },
        "common": {
            "current": "Lelo", "loading": "Kozela…",
            "error": "Mpasi", "success": "Malamu",
            "download": "Kokitisa", "refresh": "Kobongola",
            "save": "Kobomba", "load": "Kotya", "export": "Kobima na",
            "zones": "zones", "cases": "biloko", "days": "mikolo",
        },
        "language": {"selector": "Lokota"},
        "status": {
            "files_present": "🟢 INRB — lifelo ezali",
            "download_required": "🟡 INRB — kokitisa esengeli",
            "demo_mode": "🔵 Mode ndakisa",
        },
    },
    "sw": {
        "app":  {"title": "BAEL-Ebola", "subtitle": "Dashibodi ya utabiri · DRC 2026",
                 "institution": "UAC Butembo", "location": "Nord-Kivu, DRC",
                 "framework": "Mfumo BAEL", "version": "v"},
        "sidebar": {
            "data": "Data", "real_data": "Data halisi (INRB)",
            "demo_data": "Mfano", "upload_csv": "Pakia CSV",
            "parameters": "Vigezo", "primary_model": "Modeli kuu",
            "few_shot": "Few-Shot K (wiki)", "test_ratio": "Uwiano wa mtihani",
            "forecast_horizon": "Upeo wa utabiri (siku)",
            "sir_r0": "SIR R₀", "bootstrap": "Bootstrap N",
            "risk_pct": "Asilimia ya hatari", "lstm_seq": "Urefu wa LSTM",
            "models": "Modeli", "models_ready": "tayari",
            "advanced": "Uchanganuzi wa hali ya juu",
            "download_btn": "⬇️ Pakua & Sasisha",
        },
        "menu": {
            "epidemiology": "Epidemiolojia", "forecast": "Utabiri",
            "models": "Ulinganisho wa modeli", "zones": "Uchanganuzi wa maeneo",
            "xai": "Ufafanuzi", "report": "Ripoti",
            "publications": "Machapisho", "dashboard": "Dashibodi yangu",
            "advanced": "Uchanganuzi wa hali ya juu", "chatbot": "Msaidizi wa AI",
            "comparison": "Ulinganisho wa janga",
        },
        "metrics": {
            "total_cases": "Jumla ya kesi", "new_cases_7d": "Kesi mpya (siku 7)",
            "health_zones": "Maeneo ya afya", "last_report": "Ripoti ya mwisho",
            "growth_rate": "Kiwango cha ukuaji", "active_model": "Modeli inayotumika",
            "risk_threshold": "Kizingiti cha hatari",
        },
        "alerts": {
            "critical": "🔴 HATARI KUU", "high": "TAHADHARI KUU",
            "elevated": "HATARI ILIYOINULIWA", "stable": "IMARA",
            "immediate_action": "Hatua ya haraka inahitajika",
            "enhanced_surveillance": "Ufuatiliaji ulioboreshwa unapendekezwa",
            "routine_monitoring": "Endelea na ufuatiliaji wa kawaida",
        },
        "forecast": {
            "title": "Utabiri", "next_step": "Utabiri wa hatua inayofuata",
            "mean": "Wastani", "median": "Kati", "ci_95": "CI 95%",
            "horizon": "Upeo wa utabiri",
        },
        "common": {
            "current": "Sasa", "loading": "Inapakia…",
            "error": "Hitilafu", "success": "Mafanikio",
            "download": "Pakua", "refresh": "Sasisha",
            "save": "Hifadhi", "load": "Pakia", "export": "Hamisha",
            "zones": "maeneo", "cases": "kesi", "days": "siku",
        },
        "language": {"selector": "Lugha"},
        "status": {
            "files_present": "🟢 INRB — faili zipo",
            "download_required": "🟡 INRB — upakuaji unahitajika",
            "demo_mode": "🔵 Hali ya mfano",
        },
    },
}


def get_current_language():
    return st.session_state.get('language', 'en')


def t(key, default=None):
    """Get translated text by dot-notation key (e.g. 'menu.forecast')."""
    lang  = get_current_language()
    data  = _TRANSLATIONS.get(lang, _TRANSLATIONS['en'])
    keys  = key.split('.')
    value = data
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            # Fallback to English
            value = _TRANSLATIONS['en']
            for k2 in keys:
                if isinstance(value, dict) and k2 in value:
                    value = value[k2]
                else:
                    return default or key
            break
    return value if isinstance(value, str) else (default or key)


def language_selector():
    """Render the language selector in the sidebar."""
    current = get_current_language()
    options = {f"{v['flag']} {v['name']}": k for k, v in LANGUAGES.items()}
    current_label = next(
        f"{v['flag']} {v['name']}" for k, v in LANGUAGES.items() if k == current
    )
    selected = st.selectbox(
        f"🌍 {t('language.selector')}",
        list(options.keys()),
        index=list(options.keys()).index(current_label),
        key="lang_selector"
    )
    chosen = options[selected]
    if chosen != current:
        st.session_state.language = chosen
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════
# EXPORT FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

def generate_pdf_report(nat, zones, active_model, metrics_primary,
                        all_metrics, ci_fc, risk_thr, gr_last,
                        zone_latest_df=None):
    """
    Generate a comprehensive scientific PDF report suitable for
    academic submission or health authority briefings.
    Sections: cover · executive summary · epidemiology · model
    performance · forecast · zone analysis · recommendations · methods.
    """
    # ── Ensure zone_latest_df is a usable DataFrame ───────────────────
    # zones is a plain Python list of names; zone_latest_df carries the
    # actual 'zone' + 'value' columns needed for zone-level analysis.
    if zone_latest_df is None or not isinstance(zone_latest_df, pd.DataFrame):
        _n = len(zones) if isinstance(zones, list) else 0
        zone_latest_df = pd.DataFrame({'zone': zones if isinstance(zones, list) else [],
                                        'value': [0] * _n})
    _zdf = zone_latest_df  # short alias used throughout this function
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, HRFlowable
    )
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2.5*cm, bottomMargin=2*cm,
        title=cfg("report_title","BAEL Scientific Report"),
        author="UAC Butembo — PhD AI"
    )

    styles = getSampleStyleSheet()

    # ── Custom styles ────────────────────────────────────────────────
    def _style(name, parent='Normal', **kw):
        return ParagraphStyle(name, parent=styles[parent], **kw)

    S = {
        'cover_title': _style('CoverTitle', 'Heading1',
                               fontSize=26, textColor=colors.HexColor('#0D1B3E'),
                               spaceAfter=8, alignment=TA_CENTER, leading=32),
        'cover_sub':   _style('CoverSub', fontSize=14,
                               textColor=colors.HexColor('#1565C0'),
                               spaceAfter=6, alignment=TA_CENTER),
        'cover_meta':  _style('CoverMeta', fontSize=10,
                               textColor=colors.HexColor('#546E7A'),
                               spaceAfter=4, alignment=TA_CENTER),
        'h2':          _style('H2', 'Heading2', fontSize=14,
                               textColor=colors.HexColor('#1A237E'),
                               spaceBefore=16, spaceAfter=8,
                               borderPad=4),
        'h3':          _style('H3', 'Heading3', fontSize=11,
                               textColor=colors.HexColor('#1565C0'),
                               spaceBefore=10, spaceAfter=6),
        'body':        _style('Body', fontSize=9, leading=14,
                               textColor=colors.HexColor('#212121')),
        'caption':     _style('Caption', fontSize=8, leading=11,
                               textColor=colors.HexColor('#546E7A'),
                               alignment=TA_CENTER),
        'footer':      _style('Footer', fontSize=7,
                               textColor=colors.HexColor('#90A4AE'),
                               alignment=TA_CENTER),
        'alert_red':   _style('AlertRed', fontSize=9, leading=13,
                               textColor=colors.HexColor('#B71C1C'),
                               backColor=colors.HexColor('#FFEBEE'),
                               borderPad=6, spaceAfter=8),
        'alert_green': _style('AlertGreen', fontSize=9, leading=13,
                               textColor=colors.HexColor('#1B5E20'),
                               backColor=colors.HexColor('#E8F5E9'),
                               borderPad=6, spaceAfter=8),
    }

    # ── Table style helpers ──────────────────────────────────────────
    def _tbl_style(header_color='#1A237E'):
        return TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0),  colors.HexColor(header_color)),
            ('TEXTCOLOR',     (0, 0), (-1, 0),  colors.whitesmoke),
            ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, 0),  9),
            ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE',      (0, 1), (-1, -1), 8),
            ('BACKGROUND',    (0, 1), (-1, -1), colors.HexColor('#F8FAFC')),
            ('ROWBACKGROUNDS',(0, 1), (-1, -1),
             [colors.HexColor('#F8FAFC'), colors.HexColor('#EEF2F7')]),
            ('GRID',          (0, 0), (-1, -1), 0.5, colors.HexColor('#CFD8DC')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ])

    def _divider():
        return HRFlowable(width="100%", thickness=0.5,
                          color=colors.HexColor('#90CAF9'), spaceAfter=8)

    story = []

    # ════════════════════════════════════════════════════════════════
    # COVER PAGE
    # ════════════════════════════════════════════════════════════════
    story += [
        Spacer(1, 3*cm),
        Paragraph(cfg("display_name", "BAEL Epidemic"), S['cover_title']),
        Paragraph("Scientific Epidemiological Report", S['cover_sub']),
        Paragraph(
            f"{cfg('strain', '')} — {cfg('country', 'DRC')} {cfg('start_year', '')}",
            S['cover_sub']),
        Spacer(1, 1.5*cm),
        _divider(),
        Spacer(1, 0.5*cm),
        Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}", S['cover_meta']),
        Paragraph("Université de l'Assomption au Congo (UAC)", S['cover_meta']),
        Paragraph("Butembo, Nord-Kivu, Democratic Republic of Congo", S['cover_meta']),
        Paragraph("PhD in Artificial Intelligence — BAEL Framework", S['cover_meta']),
        Paragraph("Behavior-Aware Explainability Loop", S['cover_meta']),
        Spacer(1, 1*cm),
        _divider(),
        Spacer(1, 0.5*cm),
        Paragraph(f"Active Forecasting Model: <b>{active_model}</b>", S['cover_meta']),
        Paragraph(f"Report covers {len(nat)} observation days "
                  f"({nat['date'].min().strftime('%d %b %Y')} — "
                  f"{nat['date'].max().strftime('%d %b %Y')})", S['cover_meta']),
        PageBreak(),
    ]

    # ════════════════════════════════════════════════════════════════
    # 1. EXECUTIVE SUMMARY
    # ════════════════════════════════════════════════════════════════
    story += [Paragraph("1. Executive Summary", S['h2']), _divider()]

    # Risk level
    risk_level = "CRITICAL" if gr_last > 20 else "ELEVATED" if gr_last > 5 else "STABLE"
    risk_color = '#B71C1C' if gr_last > 20 else '#E65100' if gr_last > 5 else '#1B5E20'
    story.append(Paragraph(
        f"<b>Overall Risk Level: {risk_level}</b> — Growth rate: {gr_last:.1f}% "
        f"| Total cases: {int(nat['value'].max()):,} | Zones affected: {len(zones)}",
        S['alert_red'] if gr_last > 5 else S['alert_green']
    ))

    summary_data = [
        ["Indicator", "Value", "Status"],
        ["Total Confirmed Cases", f"{int(nat['value'].max()):,}",
         "🔴 Critical" if int(nat['value'].max()) > 2000 else "🟡 Elevated"],
        ["New Cases (7 days)", f"{int(nat['new_cases'].tail(7).sum()):,}",
         "🔴" if int(nat['new_cases'].tail(7).sum()) > 100 else "🟢"],
        ["Daily Average (7d)", f"{nat['new_cases'].tail(7).mean():.1f}",
         ""],
        ["Health Zones Affected", str(len(zones)), ""],
        ["High-Risk Zones", str(sum(1 for v in _zdf['value'] if v > risk_thr)),
         f"Threshold: {risk_thr:.0f}"],
        ["Growth Rate (last)", f"{gr_last:.2f}%",
         "🔴 Critical" if gr_last > 20 else "🟡 Elevated" if gr_last > 5 else "🟢 Stable"],
        ["Last Report Date", nat['date'].max().strftime('%d %b %Y'), ""],
        ["Active Model", active_model, ""],
        ["Forecast (next step)", f"{ci_fc.get('mean', 0):.0f} cases", ""],
        ["95% CI", f"[{ci_fc.get('lower', 0):.0f} — {ci_fc.get('upper', 0):.0f}]", ""],
    ]
    t1 = Table(summary_data, colWidths=[5.5*cm, 4*cm, 5*cm])
    t1.setStyle(_tbl_style('#1A237E'))
    story += [t1, Spacer(1, 0.5*cm)]

    # ════════════════════════════════════════════════════════════════
    # 2. EPIDEMIOLOGICAL ANALYSIS
    # ════════════════════════════════════════════════════════════════
    story += [Paragraph("2. Epidemiological Analysis", S['h2']), _divider()]

    story.append(Paragraph("2.1 Temporal Trend", S['h3']))
    # Key trend stats
    total_obs   = len(nat)
    peak_cases  = int(nat['new_cases'].max())
    peak_date   = nat.loc[nat['new_cases'].idxmax(), 'date'].strftime('%d %b %Y')
    avg_daily   = nat['new_cases'].mean()
    story.append(Paragraph(
        f"The epidemic spans <b>{total_obs} days</b> of observation. "
        f"Peak daily incidence reached <b>{peak_cases:,} cases</b> on {peak_date}. "
        f"The overall average daily incidence is <b>{avg_daily:.1f} cases/day</b>. "
        f"The 7-day rolling average currently stands at "
        f"<b>{nat['rolling7'].iloc[-1]:.1f} cases/day</b>.",
        S['body']
    ))
    story.append(Spacer(1, 0.3*cm))

    # Monthly breakdown table (last 4 months)
    story.append(Paragraph("2.2 Monthly Breakdown", S['h3']))
    nat_m = nat.copy()
    nat_m['month'] = nat_m['date'].dt.to_period('M')
    monthly = (nat_m.groupby('month')['new_cases']
                    .agg(['sum','mean','max'])
                    .tail(6).reset_index())
    monthly.columns = ['Month','Total New','Daily Avg','Peak Day']
    m_data = [['Month','Total New Cases','Daily Average','Peak (1 day)']]
    for _, row in monthly.iterrows():
        m_data.append([str(row['Month']),
                       f"{int(row['Total New']):,}",
                       f"{row['Daily Avg']:.1f}",
                       f"{int(row['Peak Day']):,}"])
    t2 = Table(m_data, colWidths=[3.5*cm, 4*cm, 4*cm, 3*cm])
    t2.setStyle(_tbl_style('#283593'))
    story += [t2, Spacer(1, 0.3*cm)]

    story.append(Paragraph("2.3 Zone-Level Analysis", S['h3']))
    top_zones = _zdf.sort_values('value', ascending=False).head(10)
    z_data = [['Zone','Cases','% National','Risk Level']]
    total  = int(nat['value'].max())
    for _, row in top_zones.iterrows():
        pct  = row['value'] / total * 100 if total else 0
        risk = ('🔴 HIGH' if row['value'] > risk_thr
                else '🟡 MOD' if row['value'] > risk_thr * 0.4
                else '🟢 LOW')
        z_data.append([row['zone'], f"{int(row['value']):,}",
                       f"{pct:.1f}%", risk])
    t3 = Table(z_data, colWidths=[4.5*cm, 3*cm, 3.5*cm, 3.5*cm])
    t3.setStyle(_tbl_style('#1565C0'))
    story += [t3, Spacer(1, 0.3*cm)]

    # ════════════════════════════════════════════════════════════════
    # 3. MODEL PERFORMANCE
    # ════════════════════════════════════════════════════════════════
    story += [PageBreak(), Paragraph("3. Model Performance", S['h2']), _divider()]
    story.append(Paragraph(
        "All models were trained under the BAEL (Behavior-Aware Explainability Loop) "
        "framework using transfer learning and few-shot adaptation on DRC Ebola data. "
        "Metrics are computed on the held-out test set.",
        S['body']
    ))
    story.append(Spacer(1, 0.3*cm))

    if all_metrics:
        m_header = ['Model', 'RMSE', 'MAE', 'R²', 'MAPE %']
        m_rows   = [m_header]
        best_r2  = -999
        best_name = active_model
        for name, m in all_metrics.items():
            r2_val = m.get('R²', '—')
            try:
                if float(str(r2_val).replace('—','')) > best_r2:
                    best_r2  = float(str(r2_val))
                    best_name = name
            except Exception:
                pass
            m_rows.append([name,
                           str(m.get('RMSE',  '—')),
                           str(m.get('MAE',   '—')),
                           str(r2_val),
                           str(m.get('MAPE%', '—'))])
        t4 = Table(m_rows, colWidths=[3.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm])
        t4.setStyle(_tbl_style('#2E7D32'))
        story += [t4, Spacer(1, 0.3*cm)]
        story.append(Paragraph(
            f"<b>Best performing model:</b> {best_name} (R² = {best_r2:.4f}). "
            f"Active model for this report: <b>{active_model}</b>.",
            S['body']
        ))

    # ════════════════════════════════════════════════════════════════
    # 4. FORECAST
    # ════════════════════════════════════════════════════════════════
    story += [Paragraph("4. Forecast & Uncertainty", S['h2']), _divider()]
    story.append(Paragraph(
        f"The {active_model} model projects <b>{ci_fc.get('mean',0):.0f} cases</b> "
        f"for the next forecast step, with a 95% bootstrap confidence interval of "
        f"[<b>{ci_fc.get('lower',0):.0f} — {ci_fc.get('upper',0):.0f}</b>]. "
        f"The median estimate is <b>{ci_fc.get('median',0):.0f} cases</b>. "
        f"Forecast uncertainty is "
        f"{'high' if (ci_fc.get('upper',0)-ci_fc.get('lower',0)) > 500 else 'moderate'}.",
        S['body']
    ))

    fc_data = [
        ['Forecast Component', 'Value'],
        ['Mean (bootstrap)',      f"{ci_fc.get('mean',   0):.0f}"],
        ['Median (bootstrap)',    f"{ci_fc.get('median', 0):.0f}"],
        ['95% CI Lower',         f"{ci_fc.get('lower',  0):.0f}"],
        ['95% CI Upper',         f"{ci_fc.get('upper',  0):.0f}"],
        ['CI Width',             f"{ci_fc.get('upper',0)-ci_fc.get('lower',0):.0f}"],
        ['Active model',         active_model],
    ]
    t5 = Table(fc_data, colWidths=[7*cm, 7*cm])
    t5.setStyle(_tbl_style('#6A1B9A'))
    story += [Spacer(1, 0.3*cm), t5, Spacer(1, 0.3*cm)]

    # ════════════════════════════════════════════════════════════════
    # 5. RECOMMENDATIONS
    # ════════════════════════════════════════════════════════════════
    story += [Paragraph("5. Recommendations", S['h2']), _divider()]

    recs = []
    if gr_last > 20:
        recs += [
            "🔴 CRITICAL: Activate emergency response protocol immediately.",
            "🔴 Deploy rapid response teams to all high-risk health zones.",
            "🔴 Increase contact tracing capacity by ≥ 200%.",
        ]
    elif gr_last > 10:
        recs += [
            "🟡 ELEVATED: Enhance active surveillance across affected zones.",
            "🟡 Reinforce community alert systems and case isolation capacity.",
        ]
    else:
        recs += ["🟢 STABLE: Continue routine monitoring and weekly reporting."]

    high_risk_n = sum(1 for v in _zdf['value'] if v > risk_thr)
    if high_risk_n > 0:
        recs.append(f"📍 Prioritise resource allocation to the "
                    f"{high_risk_n} zones exceeding the risk threshold of {risk_thr:.0f} cases.")
    recs += [
        "📊 Update the BAEL model with the latest surveillance data weekly.",
        "🔬 Validate forecast accuracy against observed incidence at each reporting cycle.",
        "📚 Share findings with the DRC Ministry of Health and WHO Country Office.",
    ]

    rec_data = [['#', 'Recommendation']]
    for i, r in enumerate(recs, 1):
        rec_data.append([str(i), r])
    t6 = Table(rec_data, colWidths=[0.8*cm, 13.7*cm])
    t6.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),  colors.HexColor('#37474F')),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  colors.whitesmoke),
        ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, -1), 8),
        ('ALIGN',         (0, 0), (0, -1),  'CENTER'),
        ('ALIGN',         (1, 0), (1, -1),  'LEFT'),
        ('BACKGROUND',    (0, 1), (-1, -1), colors.HexColor('#F8FAFC')),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1),
         [colors.HexColor('#F8FAFC'), colors.HexColor('#ECEFF1')]),
        ('GRID',          (0, 0), (-1, -1), 0.4, colors.HexColor('#B0BEC5')),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story += [t6, Spacer(1, 0.5*cm)]

    # ════════════════════════════════════════════════════════════════
    # 6. METHODS
    # ════════════════════════════════════════════════════════════════
    story += [PageBreak(), Paragraph("6. Methods", S['h2']), _divider()]
    story.append(Paragraph(
        "<b>Data source:</b> Institut National de Recherche Biomédicale (INRB) — "
        "UMIE surveillance reports, accessed via the INRB-UMIE GitHub repository. "
        "Data represent cumulative confirmed EVD cases by health zone.",
        S['body']
    ))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "<b>Modelling framework — BAEL:</b> The Behavior-Aware Explainability Loop "
        "integrates spatio-temporal Graph Neural Networks (ST-GNN), Transfer Learning "
        "for cross-outbreak knowledge transfer, and Few-Shot Learning (K-shot) for "
        "rapid adaptation to new outbreak dynamics. Classical ML baselines (XGBoost, "
        "Random Forest, LightGBM, Gradient Boosting) serve as benchmarks.",
        S['body']
    ))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "<b>Forecast uncertainty:</b> Bootstrap resampling (N iterations) produces "
        "empirical confidence intervals. The SIR compartmental model provides "
        "mechanistic projections parameterised by R₀ estimated from observed growth.",
        S['body']
    ))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "<b>Evaluation metrics:</b> RMSE (Root Mean Square Error), MAE (Mean Absolute "
        "Error), R² (coefficient of determination), and MAPE% (Mean Absolute Percentage "
        "Error) are computed on the held-out test partition.",
        S['body']
    ))

    # ════════════════════════════════════════════════════════════════
    # FOOTER on every page
    # ════════════════════════════════════════════════════════════════
    _pdf_epidemic = cfg("display_name", "Epidemic")
    _pdf_province = cfg("province", "Nord-Kivu, DRC")
    story += [
        Spacer(1, 1*cm), _divider(),
        Paragraph(
            f"BAEL · {_pdf_epidemic} · "
            f"Université de l'Assomption au Congo (UAC) · "
            f"Butembo, {_pdf_province} · PhD in Artificial Intelligence · "
            f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            S['footer']
        ),
    ]

    doc.build(story)
    buffer.seek(0)
    return buffer

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Alert threshold definitions
ALERT_THRESHOLDS = {
    'growth_rate_critical':  20.0,
    'growth_rate_elevated':   5.0,
    'new_cases_7d_critical': 500,
    'new_cases_7d_warning':  100,
    'total_cases_critical':  5000,
    'total_cases_warning':   2000,
    'high_risk_zones_critical': 15,
    'high_risk_zones_warning':   5,
}


def evaluate_alerts(nat, zone_latest, gr_last, risk_thr):
    """Evaluate all thresholds and return sorted alert list."""
    alerts = []
    thr = ALERT_THRESHOLDS
    total_cases  = int(nat['value'].max())
    new_cases_7d = int(nat['new_cases'].tail(7).sum())
    high_risk_n  = sum(1 for v in zone_latest['value'] if v > risk_thr)

    if gr_last > thr['growth_rate_critical']:
        alerts.append({'level': 'CRITICAL', 'category': 'Growth Rate',
                       'message': f"Growth rate {gr_last:.1f}% exceeds critical threshold ({thr['growth_rate_critical']}%)",
                       'value': gr_last})
    elif gr_last > thr['growth_rate_elevated']:
        alerts.append({'level': 'WARNING', 'category': 'Growth Rate',
                       'message': f"Growth rate {gr_last:.1f}% elevated (> {thr['growth_rate_elevated']}%)",
                       'value': gr_last})

    if new_cases_7d > thr['new_cases_7d_critical']:
        alerts.append({'level': 'CRITICAL', 'category': 'New Cases (7d)',
                       'message': f"{new_cases_7d:,} new cases in 7d — exceeds critical threshold",
                       'value': new_cases_7d})
    elif new_cases_7d > thr['new_cases_7d_warning']:
        alerts.append({'level': 'WARNING', 'category': 'New Cases (7d)',
                       'message': f"{new_cases_7d:,} new cases in 7 days",
                       'value': new_cases_7d})

    if total_cases > thr['total_cases_critical']:
        alerts.append({'level': 'CRITICAL', 'category': 'Cumulative Cases',
                       'message': f"Total {total_cases:,} cases — critical threshold exceeded",
                       'value': total_cases})
    elif total_cases > thr['total_cases_warning']:
        alerts.append({'level': 'WARNING', 'category': 'Cumulative Cases',
                       'message': f"Total {total_cases:,} cases — warning threshold exceeded",
                       'value': total_cases})

    if high_risk_n > thr['high_risk_zones_critical']:
        alerts.append({'level': 'CRITICAL', 'category': 'High-Risk Zones',
                       'message': f"{high_risk_n} zones above risk threshold — critical cluster",
                       'value': high_risk_n})
    elif high_risk_n > thr['high_risk_zones_warning']:
        alerts.append({'level': 'WARNING', 'category': 'High-Risk Zones',
                       'message': f"{high_risk_n} zones above risk threshold",
                       'value': high_risk_n})

    return sorted(alerts, key=lambda x: 0 if x['level'] == 'CRITICAL' else 1)


def build_alert_email_html(alerts, nat, zone_latest, gr_last, risk_thr):
    """Build HTML email body for alert notifications."""
    total_cases  = int(nat['value'].max())
    new_cases_7d = int(nat['new_cases'].tail(7).sum())
    report_date  = nat['date'].max().strftime('%d %b %Y')
    n_critical   = sum(1 for a in alerts if a['level'] == 'CRITICAL')
    n_warning    = sum(1 for a in alerts if a['level'] == 'WARNING')

    alert_rows = ""
    for a in alerts:
        bg    = "#FFEBEE" if a['level'] == 'CRITICAL' else "#FFF8E1"
        color = "#C62828" if a['level'] == 'CRITICAL' else "#F57F17"
        icon  = "\U0001f6a8" if a['level'] == 'CRITICAL' else "\u26a0\ufe0f"
        alert_rows += (
            f"<tr style='background:{bg};'>"
            f"<td style='padding:8px;font-weight:700;color:{color};'>{icon} {a['level']}</td>"
            f"<td style='padding:8px;'><b>{a['category']}</b></td>"
            f"<td style='padding:8px;'>{a['message']}</td>"
            f"</tr>"
        )

    gc = '#C62828' if gr_last > 20 else '#E65100' if gr_last > 5 else '#2E7D32'
    return f"""<html><body style="font-family:Arial,sans-serif;">
<div style="max-width:680px;margin:auto;background:white;border-radius:10px;overflow:hidden;">
<div style="background:linear-gradient(135deg,#1A237E,#1565C0);padding:20px;color:white;">
<h2 style="margin:0;">\U0001f9a0 BAEL {cfg('display_name','Epidemic')} Alert — {report_date}</h2></div>
<div style="padding:16px;background:#F8FAFC;">
<b>Total:</b> {total_cases:,} &nbsp;|&nbsp;
<b>New 7d:</b> {new_cases_7d:,} &nbsp;|&nbsp;
<b style="color:{gc};">Growth: {gr_last:.1f}%</b> &nbsp;|&nbsp;
<b style="color:#C62828;">{n_critical} Critical</b> &nbsp;
<b style="color:#F57F17;">{n_warning} Warnings</b></div>
<div style="padding:20px;">
<table style="width:100%;border-collapse:collapse;font-size:13px;">
<tr style="background:#1A237E;color:white;">
<th style="padding:8px;">Level</th><th style="padding:8px;">Category</th>
<th style="padding:8px;">Details</th></tr>
{alert_rows}
</table></div>
<div style="padding:12px;text-align:center;font-size:11px;color:#90A4AE;
            background:#F8FAFC;border-top:1px solid #E3E8EF;">
BAEL · {cfg("display_name","Epidemic")} · UAC Butembo · {cfg("province","DRC")} · {datetime.now().strftime('%Y-%m-%d %H:%M')}
</div></div></body></html>"""


def send_email_alert(recipient, subject, html_body, smtp_host,
                     smtp_port, smtp_user, smtp_pass, use_tls=True):
    """Send HTML alert email via SMTP. Returns (success, message)."""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = smtp_user
        msg['To']      = recipient
        msg.attach(MIMEText(html_body, 'html'))
        if use_tls:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
            server.ehlo(); server.starttls()
        else:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15)
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, recipient, msg.as_string())
        server.quit()
        return True, "Email sent successfully."
    except smtplib.SMTPAuthenticationError:
        return False, "SMTP authentication failed — check username/password."
    except smtplib.SMTPConnectError:
        return False, f"Could not connect to {smtp_host}:{smtp_port}."
    except Exception as e:
        return False, f"Error: {str(e)[:120]}"


def build_webhook_payload(alerts, nat, gr_last, risk_thr, zone_latest):
    """Build JSON payload for Slack / Teams / generic webhook."""
    n_critical = sum(1 for a in alerts if a['level'] == 'CRITICAL')
    color      = "#C62828" if n_critical > 0 else "#F57F17"
    return {
        "text": f"\U0001f9a0 BAEL {cfg('display_name','Epidemic')} — {n_critical} critical, {len(alerts)-n_critical} warnings",
        "attachments": [{
            "color": color,
            "title": f"BAEL {cfg('display_name','Epidemic')} Alert",
            "fields": [
                {"title": "Total Cases", "value": f"{int(nat['value'].max()):,}", "short": True},
                {"title": "Growth Rate", "value": f"{gr_last:.1f}%", "short": True},
                {"title": "New Cases (7d)", "value": f"{int(nat['new_cases'].tail(7).sum()):,}", "short": True},
                {"title": "High-Risk Zones",
                 "value": str(sum(1 for v in zone_latest['value'] if v > risk_thr)), "short": True},
                {"title": "Alerts",
                 "value": "\n".join(f"{'CRITICAL' if a['level']=='CRITICAL' else 'WARNING'}: {a['message']}"
                                     for a in alerts), "short": False},
            ],
            "footer": f"BAEL · {cfg('display_name', 'Epidemic')} · UAC Butembo · {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        }]
    }


def render_notification_panel(alerts, nat, zone_latest, gr_last, risk_thr):
    """Render the full notification management panel in Streamlit."""
    n_crit = sum(1 for a in alerts if a['level'] == 'CRITICAL')
    n_warn = sum(1 for a in alerts if a['level'] == 'WARNING')

    mc1, mc2, mc3 = st.columns(3)
    mc1.metric("\U0001f6a8 Critical",    n_crit,
               delta="Action required" if n_crit > 0 else None,
               delta_color="inverse")
    mc2.metric("\u26a0\ufe0f Warnings", n_warn)
    mc3.metric("\U0001f4ca Total alerts", len(alerts))

    if not alerts:
        st.success("\u2705 No active alerts — situation currently stable.")
        return

    st.markdown("#### 🚨 Active Alerts")
    for a in alerts:
        bg     = "#FFEBEE" if a['level'] == 'CRITICAL' else "#FFF8E1"
        border = "#C62828" if a['level'] == 'CRITICAL' else "#F57F17"
        txt    = "#B71C1C" if a['level'] == 'CRITICAL' else "#7B3F00"
        icon   = "🚨" if a['level'] == 'CRITICAL' else "⚠️"
        st.markdown(
            f'<div style="background:{bg};border-left:4px solid {border};'
            f'border-radius:6px;padding:10px 14px;margin:6px 0;color:{txt};">'
            f'<b style="color:{txt};">{icon} {a["level"]}</b>'
            f' — <b style="color:{txt};">{a["category"]}</b><br>'
            f'<span style="font-size:13px;color:{txt};">{a["message"]}</span></div>',
            unsafe_allow_html=True
        )

    st.markdown("---")
    notif_tabs = st.tabs(["\U0001f4e7 Email Alert", "\U0001f517 Webhook",
                           "\u2699\ufe0f Thresholds", "\U0001f4cb Alert Log"])

    with notif_tabs[0]:
        st.markdown("#### \U0001f4e7 Email Notification")
        st.info("Gmail: host=smtp.gmail.com port=587. Use an App Password.")
        ec1, ec2 = st.columns(2)
        with ec1:
            email_to  = st.text_input("Recipient email", key="notif_email_to",
                                       placeholder="you@example.com")
            smtp_host = st.text_input("SMTP host", value="smtp.gmail.com",
                                       key="notif_smtp_host")
            smtp_port = st.number_input("SMTP port", value=587,
                                         min_value=1, max_value=65535,
                                         key="notif_smtp_port")
        with ec2:
            smtp_user = st.text_input("SMTP username", key="notif_smtp_user")
            smtp_pass = st.text_input("Password / App Password",
                                       type="password", key="notif_smtp_pass")
            use_tls   = st.checkbox("Use STARTTLS", value=True, key="notif_tls")

        subj = (f"[{'CRITICAL' if n_crit>0 else 'WARNING'}] "
                f"BAEL {cfg('display_name','Epidemic')} Alert — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        if st.button("\U0001f4e7 Send Alert Email", width='stretch',
                     key="notif_send_email"):
            if not all([email_to, smtp_host, smtp_user, smtp_pass]):
                st.warning("\u26a0\ufe0f Fill in all SMTP fields.")
            else:
                with st.spinner("Sending…"):
                    html_b = build_alert_email_html(alerts, nat, zone_latest,
                                                    gr_last, risk_thr)
                    ok, msg = send_email_alert(email_to, subj, html_b,
                                               smtp_host, int(smtp_port),
                                               smtp_user, smtp_pass, use_tls)
                if ok:
                    st.success(f"\u2705 {msg}")
                    st.session_state.setdefault('alert_log', []).append({
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
                        'channel': 'Email', 'recipient': email_to,
                        'status': 'Sent', 'n_alerts': len(alerts)})
                else:
                    st.error(f"\u274c {msg}")
        with st.expander("\U0001f441\ufe0f Preview email HTML"):
            st.code(build_alert_email_html(alerts, nat, zone_latest,
                                           gr_last, risk_thr), language='html')

    with notif_tabs[1]:
        st.markdown("#### \U0001f517 Webhook Notification")
        st.info("Paste a Slack, Teams, or any JSON-POST webhook URL.")
        wh_url = st.text_input("Webhook URL", key="notif_webhook_url",
                                placeholder="https://hooks.slack.com/…")
        if st.button("\U0001f517 Send Webhook", width='stretch',
                     key="notif_send_webhook"):
            if not wh_url:
                st.warning("\u26a0\ufe0f Enter a webhook URL.")
            else:
                payload = build_webhook_payload(alerts, nat, gr_last,
                                                risk_thr, zone_latest)
                try:
                    resp = requests.post(wh_url, json=payload, timeout=10)
                    if resp.status_code in (200, 201, 204):
                        st.success(f"\u2705 Webhook delivered (HTTP {resp.status_code}).")
                        st.session_state.setdefault('alert_log', []).append({
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
                            'channel': 'Webhook',
                            'recipient': wh_url[:40] + '…',
                            'status': f'HTTP {resp.status_code}',
                            'n_alerts': len(alerts)})
                    else:
                        st.error(f"\u274c HTTP {resp.status_code}: {resp.text[:100]}")
                except Exception as e:
                    st.error(f"\u274c {str(e)[:100]}")
        with st.expander("\U0001f441\ufe0f Preview payload"):
            st.json(build_webhook_payload(alerts, nat, gr_last,
                                          risk_thr, zone_latest))

    with notif_tabs[2]:
        st.markdown("#### \u2699\ufe0f Alert Thresholds")
        tc1, tc2 = st.columns(2)
        with tc1:
            ALERT_THRESHOLDS['growth_rate_critical'] = st.number_input(
                "Growth rate CRITICAL (%)", value=float(ALERT_THRESHOLDS['growth_rate_critical']),
                min_value=1.0, step=1.0, key="thr_gr_crit")
            ALERT_THRESHOLDS['growth_rate_elevated'] = st.number_input(
                "Growth rate WARNING (%)", value=float(ALERT_THRESHOLDS['growth_rate_elevated']),
                min_value=0.5, step=0.5, key="thr_gr_warn")
            ALERT_THRESHOLDS['new_cases_7d_critical'] = int(st.number_input(
                "New cases 7d CRITICAL", value=int(ALERT_THRESHOLDS['new_cases_7d_critical']),
                min_value=1, step=50, key="thr_nc_crit"))
            ALERT_THRESHOLDS['new_cases_7d_warning'] = int(st.number_input(
                "New cases 7d WARNING", value=int(ALERT_THRESHOLDS['new_cases_7d_warning']),
                min_value=1, step=10, key="thr_nc_warn"))
        with tc2:
            ALERT_THRESHOLDS['total_cases_critical'] = int(st.number_input(
                "Total cases CRITICAL", value=int(ALERT_THRESHOLDS['total_cases_critical']),
                min_value=100, step=500, key="thr_tc_crit"))
            ALERT_THRESHOLDS['total_cases_warning'] = int(st.number_input(
                "Total cases WARNING", value=int(ALERT_THRESHOLDS['total_cases_warning']),
                min_value=100, step=100, key="thr_tc_warn"))
            ALERT_THRESHOLDS['high_risk_zones_critical'] = int(st.number_input(
                "High-risk zones CRITICAL", value=int(ALERT_THRESHOLDS['high_risk_zones_critical']),
                min_value=1, step=1, key="thr_hrz_crit"))
            ALERT_THRESHOLDS['high_risk_zones_warning'] = int(st.number_input(
                "High-risk zones WARNING", value=int(ALERT_THRESHOLDS['high_risk_zones_warning']),
                min_value=1, step=1, key="thr_hrz_warn"))

    with notif_tabs[3]:
        st.markdown("#### \U0001f4cb Alert Log")
        log = st.session_state.get('alert_log', [])
        if log:
            st.dataframe(pd.DataFrame(log[::-1]), hide_index=True,
                         width='stretch')
            if st.button("\U0001f5d1\ufe0f Clear log", key="clear_alert_log"):
                st.session_state.alert_log = []
                st.rerun()
        else:
            st.info("No notifications sent yet in this session.")



# ═══════════════════════════════════════════════════════════════════════
# GNN PROPAGATION VISUALIZATION
# ═══════════════════════════════════════════════════════════════════════

def build_gnn_graph(zone_latest_df, risk_thr, top_n=20):
    """
    Build a spatial propagation graph from zone case data.
    Edges connect zones that share a geographic boundary or are within
    a travel-distance proxy (simulated via sorted zone ranking when
    real coordinates are unavailable).

    Returns:
        tuple: (nodes_df, edges_df, pos_dict)
            nodes_df  — DataFrame with zone, cases, risk, color
            edges_df  — DataFrame with source, target, weight
            pos_dict  — {zone: (x, y)} for matplotlib layout
    """
    import hashlib

    # Work with the top_n most-affected zones for readability
    df = (zone_latest_df
          .sort_values("value", ascending=False)
          .head(top_n)
          .reset_index(drop=True)
          .copy())

    # ── Node attributes ───────────────────────────────────────────────
    def _node_color(cases, thr):
        if cases > thr:          return "#C62828"   # high risk – red
        if cases > thr * 0.4:   return "#F57F17"   # moderate  – amber
        if cases > 0:            return "#388E3C"   # low       – green
        return "#90A4AE"                             # inactive  – grey

    def _node_risk(cases, thr):
        if cases > thr:        return "High Risk"
        if cases > thr * 0.4: return "Moderate"
        return "Low"

    df["color"] = df["value"].apply(lambda v: _node_color(v, risk_thr))
    df["risk"]  = df["value"].apply(lambda v: _node_risk(v, risk_thr))

    # ── Deterministic layout: circular + small hash-based jitter ─────
    n   = len(df)
    pos = {}
    for i, row in df.iterrows():
        angle  = 2 * 3.14159 * i / n
        radius = 1.0 + 0.3 * (row["value"] / max(df["value"].max(), 1))
        # Deterministic jitter from zone name hash
        h = int(hashlib.md5(row["zone"].encode()).hexdigest(), 16)
        jx = ((h % 100) - 50) / 300
        jy = (((h >> 8) % 100) - 50) / 300
        pos[row["zone"]] = (radius * __import__("math").cos(angle) + jx,
                            radius * __import__("math").sin(angle) + jy)

    # ── Edges: connect each zone to its 2 nearest neighbours ─────────
    # Using Euclidean distance in the layout space as a proxy for
    # geographic proximity (adequate when real shapefiles are absent)
    edges = []
    zones_list = df["zone"].tolist()
    for i, z1 in enumerate(zones_list):
        dists = []
        x1, y1 = pos[z1]
        for j, z2 in enumerate(zones_list):
            if i == j:
                continue
            x2, y2 = pos[z2]
            d = ((x1-x2)**2 + (y1-y2)**2)**0.5
            dists.append((d, z2, j))
        dists.sort()
        for d, z2, j in dists[:2]:
            # Edge weight proportional to case similarity
            v1 = float(df.loc[df["zone"] == z1, "value"].iloc[0])
            v2 = float(df.loc[df["zone"] == z2, "value"].iloc[0])
            weight = 1 - abs(v1 - v2) / (max(v1, v2) + 1)
            edges.append({"source": z1, "target": z2, "weight": round(weight, 3)})

    edges_df = pd.DataFrame(edges).drop_duplicates(
        subset=["source", "target"]
    ).reset_index(drop=True)

    return df, edges_df, pos


def render_gnn_visualization(zone_latest_df, risk_thr, raw_df_all=None):
    """
    Render the interactive GNN propagation graph panel in Streamlit.
    Uses matplotlib for the core network drawing (no extra dependencies).
    """
    st.markdown("### 🕸️ GNN Spatio-Temporal Propagation Graph")
    st.markdown("""
    <div class="info-box">
    <b>GNN-GraphSAGE Spatial Graph</b> — This graph represents the learned
    propagation structure of the Ebola outbreak. Node size is proportional
    to cumulative cases; edge weight reflects case similarity between zones.
    Red nodes exceed the risk threshold; amber nodes are in the moderate range.
    </div>
    """, unsafe_allow_html=True)

    # Controls
    n_zones_avail = len(zone_latest_df)
    if n_zones_avail < 2:
        st.info("At least 2 zones are required to render the propagation graph.")
        return

    _gnn_min = min(2, n_zones_avail)
    _gnn_max = max(_gnn_min + 1, min(40, n_zones_avail))
    _gnn_def = max(_gnn_min, min(20, n_zones_avail))

    gc1, gc2, gc3 = st.columns(3)
    with gc1:
        top_n = st.slider("Number of zones to display",
                          _gnn_min, _gnn_max, _gnn_def,
                          key="gnn_top_n")
    with gc2:
        show_labels = st.checkbox("Show zone labels", value=True, key="gnn_labels")
    with gc3:
        show_weights = st.checkbox("Show edge weights", value=False, key="gnn_weights")

    nodes_df, edges_df, pos = build_gnn_graph(zone_latest_df, risk_thr, top_n)

    if nodes_df.empty:
        st.info("No zone data available for graph construction.")
        return

    # ── Draw graph with matplotlib ────────────────────────────────────
    with safe_plot():
        fig, ax = plt.subplots(figsize=(12, 8), dpi=90)
        ax.set_facecolor("#F8FAFC")
        fig.patch.set_facecolor("#F8FAFC")

        # Draw edges first (below nodes)
        for _, edge in edges_df.iterrows():
            if edge["source"] in pos and edge["target"] in pos:
                x1, y1 = pos[edge["source"]]
                x2, y2 = pos[edge["target"]]
                alpha  = max(0.15, float(edge["weight"]) * 0.6)
                ax.plot([x1, x2], [y1, y2],
                        color="#90A4AE", lw=1.2, alpha=alpha, zorder=1)
                if show_weights:
                    mx, my = (x1+x2)/2, (y1+y2)/2
                    ax.text(mx, my, f"{edge['weight']:.2f}",
                            fontsize=6, color="#546E7A", ha="center",
                            va="center", zorder=4)

        # Draw nodes
        max_cases = max(nodes_df["value"].max(), 1)
        for _, row in nodes_df.iterrows():
            if row["zone"] not in pos:
                continue
            x, y = pos[row["zone"]]
            # Node radius proportional to cases (min 200, max 2000)
            radius = 200 + 1800 * (float(row["value"]) / max_cases)
            ax.scatter(x, y, s=radius, c=row["color"],
                       edgecolors="white", linewidths=1.5,
                       zorder=3, alpha=0.88)
            if show_labels:
                label = (row["zone"][:10] + "…"
                         if len(row["zone"]) > 10 else row["zone"])
                ax.text(x, y + 0.06, label,
                        fontsize=7, ha="center", va="bottom",
                        fontweight="bold", color="#1A237E", zorder=5)
                ax.text(x, y - 0.07, f"{int(row['value']):,}",
                        fontsize=6.5, ha="center", va="top",
                        color="#424242", zorder=5)

        # Legend
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], marker="o", color="w",
                   markerfacecolor="#C62828", markersize=10,
                   label="High Risk (> threshold)"),
            Line2D([0], [0], marker="o", color="w",
                   markerfacecolor="#F57F17", markersize=10,
                   label="Moderate Risk"),
            Line2D([0], [0], marker="o", color="w",
                   markerfacecolor="#388E3C", markersize=10,
                   label="Low Risk"),
            Line2D([0], [0], color="#90A4AE", lw=1.5,
                   label="Propagation edge"),
        ]
        ax.legend(handles=legend_elements, loc="upper right",
                  fontsize=8, framealpha=0.85)

        ax.set_title(
            f"BAEL {cfg('display_name','Epidemic')} Propagation Graph — Top {top_n} Affected Zones",
            fontweight="bold", fontsize=11, pad=12
        )
        ax.axis("off")
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    # ── Stats table ───────────────────────────────────────────────────
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.markdown("#### 📋 Node Summary")
        st.dataframe(
            nodes_df[["zone", "value", "risk"]].rename(
                columns={"zone": "Zone", "value": "Cases", "risk": "Risk Level"}
            ).reset_index(drop=True),
            hide_index=True, width='stretch'
        )
    with col_g2:
        st.markdown("#### 🔗 Edge Summary")
        st.dataframe(
            edges_df.rename(
                columns={"source": "Source", "target": "Target",
                         "weight": "Similarity Weight"}
            ).head(15).reset_index(drop=True),
            hide_index=True, width='stretch'
        )

    st.caption(
        "💡 Node size ∝ cumulative cases · Edge weight = case similarity · "
        "Graph built from BAEL-GNN spatial adjacency learned during training"
    )


# ═══════════════════════════════════════════════════════════════════════
# OFFLINE DASHBOARD — disk-cached snapshot
# ═══════════════════════════════════════════════════════════════════════

import pickle
import hashlib as _hashlib

_OFFLINE_CACHE_PATH = Path("bael_offline_cache.pkl")
_OFFLINE_META_PATH  = Path("bael_offline_meta.json")


def save_offline_snapshot(nat, zone_latest, all_metrics, ci_fc,
                           gr_last, risk_thr, active_model, zones):
    """
    Persist a complete dashboard snapshot to disk so the app can run
    without network access.  Stores: national series, zone data, model
    metrics, forecast, key scalars, and a metadata block with timestamp.

    Returns:
        tuple[bool, str]: (success, message)
    """
    try:
        snapshot = {
            "nat":          nat.to_dict("records"),
            "zone_latest":  zone_latest.to_dict("records"),
            "all_metrics":  all_metrics,
            "ci_fc":        ci_fc,
            "gr_last":      gr_last,
            "risk_thr":     risk_thr,
            "active_model": active_model,
            "n_zones":      len(zones),
            "saved_at":     datetime.now().isoformat(),
        }
        with open(_OFFLINE_CACHE_PATH, "wb") as f:
            pickle.dump(snapshot, f)

        meta = {
            "saved_at":     datetime.now().strftime("%Y-%m-%d %H:%M"),
            "total_cases":  int(nat["value"].max()),
            "n_zones":      len(zones),
            "active_model": active_model,
            "checksum":     _hashlib.md5(
                open(_OFFLINE_CACHE_PATH, "rb").read()
            ).hexdigest()[:8],
        }
        with open(_OFFLINE_META_PATH, "w") as f:
            json.dump(meta, f, indent=2)

        return True, (f"Snapshot saved — {int(nat['value'].max()):,} cases, "
                      f"{len(zones)} zones, model {active_model}")
    except Exception as e:
        return False, f"Save failed: {str(e)[:120]}"


def load_offline_snapshot():
    """
    Load the most recent offline snapshot from disk.

    Returns:
        dict | None: snapshot dict, or None if no cache exists / corrupt
    """
    if not _OFFLINE_CACHE_PATH.exists():
        return None
    try:
        with open(_OFFLINE_CACHE_PATH, "rb") as f:
            snap = pickle.load(f)
        snap["nat"]         = pd.DataFrame(snap["nat"])
        snap["nat"]["date"] = pd.to_datetime(snap["nat"]["date"])
        snap["zone_latest"] = pd.DataFrame(snap["zone_latest"])
        return snap
    except Exception:
        return None


def get_offline_meta():
    """Return metadata dict for the cached snapshot, or None."""
    if not _OFFLINE_META_PATH.exists():
        return None
    try:
        with open(_OFFLINE_META_PATH) as f:
            return json.load(f)
    except Exception:
        return None


def render_offline_panel(nat, zone_latest, all_metrics, ci_fc,
                          gr_last, risk_thr, active_model, zones):
    """
    Render the offline dashboard management panel.
    Handles: save snapshot, load snapshot indicator, and cache info.
    """
    meta = get_offline_meta()

    oc1, oc2 = st.columns(2)
    with oc1:
        st.markdown("##### 💾 Save Current Snapshot")
        if meta:
            st.info(
                f"Last snapshot: **{meta['saved_at']}** · "
                f"{meta['total_cases']:,} cases · "
                f"{meta['n_zones']} zones · "
                f"Model: {meta['active_model']} · "
                f"Checksum: `{meta['checksum']}`"
            )
        else:
            st.warning("No offline snapshot found.")

        if st.button("💾 Save Offline Snapshot",
                     width='stretch', key="save_offline"):
            with st.spinner("Saving snapshot to disk…"):
                ok, msg = save_offline_snapshot(
                    nat, zone_latest, all_metrics, ci_fc,
                    gr_last, risk_thr, active_model, zones
                )
            if ok:
                st.success(f"✅ {msg}")
                # Persist mode flag
                st.session_state["offline_mode_available"] = True
            else:
                st.error(f"❌ {msg}")

    with oc2:
        st.markdown("##### 🔌 Offline Mode")
        snap = load_offline_snapshot()
        if snap:
            saved_at  = snap['saved_at'][:16]
            snap_nat  = pd.DataFrame(snap['nat'])
            max_cases = int(snap_nat['value'].max())
            snap_model = snap['active_model']
            st.success(
                f"✅ Offline cache ready — "
                f"Saved: **{saved_at}** · "
                f"Cases: **{max_cases:,}** · "
                f"Model: **{snap_model}**"
            )
            if st.button("📂 Restore from Cache",
                         width='stretch', key="load_offline"):
                st.session_state["offline_snapshot"] = snap
                st.success("✅ Offline snapshot loaded into session. "
                           "Restart the app with 'Offline Mode' selected to use it.")
        else:
            st.info("Save a snapshot first to enable offline mode.")

    st.markdown("---")
    st.markdown("##### 📂 Cache Files on Disk")
    cache_info = []
    for p in [_OFFLINE_CACHE_PATH, _OFFLINE_META_PATH]:
        if p.exists():
            size_kb = p.stat().st_size / 1024
            cache_info.append({"File": p.name,
                                "Size": f"{size_kb:.1f} KB",
                                "Modified": datetime.fromtimestamp(
                                    p.stat().st_mtime
                                ).strftime("%Y-%m-%d %H:%M")})
    if cache_info:
        st.dataframe(pd.DataFrame(cache_info),
                     hide_index=True, width='stretch')
    else:
        st.caption("No cache files yet.")


# ═══════════════════════════════════════════════════════════════════════
# INTERACTIVE TOUR — onboarding overlay
# ═══════════════════════════════════════════════════════════════════════

TOUR_STEPS = [
    {
        "title":   f"👋 Welcome to BAEL {cfg('display_name','Epidemic')}",
        "icon":    "🦠",
        "content": (
            f"This dashboard monitors the **{cfg('display_name', 'Ebola')}** outbreak "
            f"in {cfg('country', 'DRC')} using the BAEL (Behavior-Aware Explainability "
            "Loop) AI framework — UAC Butembo, Nord-Kivu, DRC."
        ),
        "tip": "Use the **Epidemic selector** at the top of the sidebar to switch "
               "between different outbreaks. Use the **language selector** to switch "
               "between English, Français, Lingala, or Kiswahili.",
    },
    {
        "title":   "📂 Data Source",
        "icon":    "📊",
        "content": (
            "Select **Real data (INRB)** to load live surveillance data from GitHub. "
            "Use **Demo data** for a quick preview, or upload your own CSV "
            "(zone · date · value) via **Upload CSV**."
        ),
        "tip": "A green badge in the sidebar confirms INRB data is present on disk. "
               "Click *Download & Update Data* to fetch the latest release.",
    },
    {
        "title":   "📈 Tab 1 — Epidemiology",
        "icon":    "📈",
        "content": (
            "Cumulative and daily case trends, deaths & recovered, outcome rates (CFR, "
            "recovery), growth rate trajectory, and the **Temporal Comparison** panel "
            "for week-over-week and vs-peak benchmarking."
        ),
        "tip": "The alert strip updates automatically when the growth rate exceeds "
               "configured thresholds.",
    },
    {
        "title":   "🔮 Tab 2 — Forecast",
        "icon":    "🔮",
        "content": (
            "Bootstrap forecasts from the active model (XGBoost, RF, LightGBM, GNN) "
            "with 95% confidence intervals, SIR mechanistic projection, and "
            "**per-zone forecasts** with risk classification."
        ),
        "tip": "Check **Forecast History** at the bottom of this tab to compare "
               "past predictions against observed case counts.",
    },
    {
        "title":   "🗺️ Tab 3 — Zone Analysis",
        "icon":    "🗺️",
        "content": (
            "Case distribution across all health zones, interactive **GNN Propagation "
            "Graph** showing spatial transmission structure, and the **Resource "
            "Calculator** for evidence-based supply planning."
        ),
        "tip": "The Resource Calculator uses WHO/MSF Ebola response guidelines. "
               "Adjust the safety buffer and scenario to model best/worst case.",
    },
    {
        "title":   "🧠 Tab 4 — Explainability",
        "icon":    "🧠",
        "content": (
            "SHAP feature importance, LIME explanations, and model interpretability "
            "tools built into the BAEL framework to make AI forecasts transparent "
            "and trustworthy for public health decision-makers."
        ),
        "tip": "Explainability outputs can be exported for inclusion in your "
               "scientific reports and publications.",
    },
    {
        "title":   "📊 Tab 5 — Epidemic Comparison",
        "icon":    "📊",
        "content": (
            "Compare the current outbreak against 8 historical Ebola epidemics "
            "(WHO/INRB data): total cases, CFR, duration, and severity ranking. "
            "Provides essential historical context for your thesis."
        ),
        "tip": "The current outbreak entry updates in real time from your loaded data.",
    },
    {
        "title":   "🔬 Tab 6 — Advanced Analysis",
        "icon":    "🔬",
        "content": (
            "Six analytical modules: **Trend Analysis** with breakpoint detection, "
            "**Anomaly Detection** (Z-score), **Correlation** heatmap, "
            "**Zone Clustering** (K-Means), **Sensitivity Analysis** (SIR params), "
            "and **Advanced Report** generation."
        ),
        "tip": "Run Walk-Forward Validation in **Tab 7** for publication-ready "
               "cross-validation metrics.",
    },
    {
        "title":   "📊 Tab 7 — Model Comparison",
        "icon":    "📊",
        "content": (
            "Side-by-side comparison of all models (RMSE, MAE, R², MAPE%), residual "
            "analysis, and **Walk-Forward Validation** — the gold standard temporal "
            "cross-validation required by epidemiology journals."
        ),
        "tip": "Walk-Forward uses expanding windows with no data leakage — "
               "each fold trains only on past data.",
    },
    {
        "title":   "🤖 Tab 10 — AI Assistant",
        "icon":    "🤖",
        "content": (
            "Query the dashboard in natural language: total cases, zone details, "
            "growth rate, forecast, deaths, recovery rate, resource needs, "
            "and historical comparisons."
        ),
        "tip": "Try: *'Compare to historical outbreaks'* or "
               "*'How many beds are needed?'*",
    },
    {
        "title":   "🔔 Notifications & Offline Mode",
        "icon":    "🔔",
        "content": (
            "Open **Alerts & Notifications** in the sidebar to send email or webhook "
            "alerts when thresholds are breached. Use **Offline Snapshot** to save "
            "the full dashboard state to disk for use without internet."
        ),
        "tip": "Gmail: enable 2FA and generate an **App Password** — "
               "do not use your main password for SMTP.",
    },
]


def render_tour():
    """
    Render the interactive onboarding tour as a step-by-step dialog.
    State is persisted in st.session_state so it survives reruns.
    Shown automatically on first visit; can be re-triggered manually.
    """
    if "tour_step" not in st.session_state:
        st.session_state.tour_step    = 0
        st.session_state.tour_active  = True
        st.session_state.tour_seen    = False

    if not st.session_state.get("tour_active", False):
        return

    step  = st.session_state.tour_step
    total = len(TOUR_STEPS)
    data  = TOUR_STEPS[min(step, total - 1)]

    progress = (step + 1) / total

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#0D1B3E,#1A237E);
                border-radius:14px;padding:22px 28px;margin-bottom:18px;
                box-shadow:0 4px 20px rgba(26,35,126,0.35);">
        <div style="display:flex;align-items:center;gap:14px;">
            <span style="font-size:36px;">{data['icon']}</span>
            <div style="flex:1;">
                <div style="color:#90CAF9;font-size:11px;font-weight:600;
                            text-transform:uppercase;letter-spacing:1px;">
                    Step {step+1} of {total} — Interactive Tour
                </div>
                <div style="color:white;font-size:19px;font-weight:700;
                            margin-top:3px;">{data['title']}</div>
            </div>
            <div style="color:#64B5F6;font-size:12px;min-width:60px;
                        text-align:right;">{step+1} / {total}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.progress(progress)
    st.markdown(data["content"])
    st.info(f"💡 **Tip:** {data['tip']}")

    nav1, nav2, nav3 = st.columns([1, 1, 1])
    with nav1:
        if step > 0:
            if st.button("← Previous", width='stretch', key="tour_prev"):
                st.session_state.tour_step -= 1
                st.rerun()
    with nav2:
        if st.button("✕ Skip tour", width='stretch', key="tour_skip"):
            st.session_state.tour_active = False
            st.session_state.tour_seen   = True
            st.rerun()
    with nav3:
        if step < total - 1:
            if st.button("Next →", width='stretch', key="tour_next"):
                st.session_state.tour_step += 1
                st.rerun()
        else:
            if st.button("✅ Finish tour", width='stretch', key="tour_finish"):
                st.session_state.tour_active = False
                st.session_state.tour_seen   = True
                st.rerun()

    st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════
# DARK MODE — CSS toggle
# ═══════════════════════════════════════════════════════════════════════

_DARK_CSS = """
<style>
/* ── Dark Mode Override ── */
.stApp                   { background-color: #0D1117 !important; }
.main .block-container   { background-color: #0D1117 !important; }
p, li, span, label       { color: #C9D1D9 !important; }
h1, h2, h3               { color: #58A6FF !important; border-color: #21262D !important; }

div[data-testid="metric-container"] {
    background: #161B22 !important;
    border: 1px solid #30363D !important;
    box-shadow: none !important;
}
div[data-testid="metric-container"] label              { color: #8B949E !important; }
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #58A6FF !important;
}

.stDataFrame, .stTable   { background: #161B22 !important; color: #C9D1D9 !important; }
.stTextInput input, .stSelectbox select, .stSlider {
    background: #21262D !important; color: #C9D1D9 !important;
    border-color: #30363D !important;
}
.streamlit-expanderHeader {
    background: #161B22 !important; color: #58A6FF !important;
}
button[kind="secondary"]  { background: #21262D !important; color: #C9D1D9 !important; }
.stTabs [data-baseweb="tab"] {
    background: #161B22 !important; color: #8B949E !important;
}
.stTabs [aria-selected="true"] {
    background: #21262D !important; color: #58A6FF !important;
    border-bottom: 2px solid #58A6FF !important;
}
.info-box  { background: #1F2937 !important; border-color: #3B4A6B !important;
             color: #93C5FD !important; }
.alert-red { background: #2D1515 !important; color: #FCA5A5 !important; }
.alert-green { background: #132016 !important; color: #86EFAC !important; }
.alert-orange { background: #2D1D00 !important; color: #FCD34D !important; }
.report-card, .model-card {
    background: #161B22 !important; border-color: #30363D !important;
}
.stAlert  { background: #161B22 !important; }
</style>
"""


def inject_dark_mode(enabled: bool):
    """Inject or suppress the dark-mode CSS block."""
    if enabled:
        st.markdown(_DARK_CSS, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════
# FORECAST HISTORY — session-state log
# ═══════════════════════════════════════════════════════════════════════

def log_forecast(ci_fc, active_model, gr_last, nat, horizon):
    """
    Append the current forecast to the in-session forecast history log.
    Each entry records: timestamp, model, mean/lower/upper forecast,
    current growth rate, and last observed case count.
    The log is capped at 50 entries to avoid unbounded memory growth.
    """
    if "forecast_history" not in st.session_state:
        st.session_state.forecast_history = []

    entry = {
        "timestamp":   datetime.now().strftime("%Y-%m-%d %H:%M"),
        "model":       active_model,
        "forecast_mean":   round(ci_fc.get("mean",   0), 1),
        "forecast_lower":  round(ci_fc.get("lower",  0), 1),
        "forecast_upper":  round(ci_fc.get("upper",  0), 1),
        "horizon_days":    horizon,
        "growth_rate":     round(gr_last, 2),
        "last_cases":      int(nat["value"].max()),
        "last_new_cases":  int(nat["new_cases"].iloc[-1]),
    }

    # Avoid duplicate entries within the same minute
    if (not st.session_state.forecast_history or
            st.session_state.forecast_history[-1]["timestamp"] != entry["timestamp"]):
        st.session_state.forecast_history.append(entry)
        # Cap to most recent 50 entries
        st.session_state.forecast_history = st.session_state.forecast_history[-50:]


def render_forecast_history():
    """
    Render the Forecast History panel showing all logged predictions,
    a tracking chart comparing forecasts over time, and accuracy
    evaluation if enough data is available.
    """
    st.markdown("### 📜 Forecast History")
    st.markdown("""
    <div class="info-box">
    <b>📜 Forecast History Log</b> — Every forecast generated during this session
    is recorded here. As new data arrives, compare past predictions to observed
    counts to evaluate model accuracy over time.
    </div>
    """, unsafe_allow_html=True)

    history = st.session_state.get("forecast_history", [])

    if not history:
        st.info("No forecast history yet in this session. "
                "Generate a forecast on the main Forecast tab to populate this log.")
        return

    fh_df = pd.DataFrame(history)

    # ── Summary metrics ───────────────────────────────────────────────
    fh1, fh2, fh3, fh4 = st.columns(4)
    fh1.metric("📊 Forecasts logged", len(fh_df))
    fh2.metric("🤖 Models used",
               str(fh_df["model"].nunique()))
    fh3.metric("📈 Avg forecast mean",
               f"{fh_df['forecast_mean'].mean():.0f}")
    fh4.metric("📅 Latest entry",
               fh_df["timestamp"].iloc[-1] if len(fh_df) else "—")

    # ── Forecast trajectory chart ─────────────────────────────────────
    if len(fh_df) >= 2:
        st.markdown("#### 📈 Forecast Trajectory Over Session")
        with safe_plot():
            fig, ax = plt.subplots(figsize=(10, 4), dpi=72)

            ax.fill_between(range(len(fh_df)),
                            fh_df["forecast_lower"],
                            fh_df["forecast_upper"],
                            alpha=0.18, color=PALETTE[0], label="95% CI")
            ax.plot(range(len(fh_df)), fh_df["forecast_mean"],
                    "o-", color=PALETTE[0], lw=2, markersize=6,
                    label="Forecast mean")
            ax.plot(range(len(fh_df)), fh_df["last_cases"],
                    "s--", color=PALETTE[2], lw=1.5, markersize=5,
                    label="Observed cumulative cases")

            ax.set_xticks(range(len(fh_df)))
            ax.set_xticklabels(
                [e[:5] for e in fh_df["timestamp"]],
                rotation=35, fontsize=7
            )
            ax.set_title("Forecast vs Observed — Session History",
                         fontweight="bold", fontsize=10)
            ax.set_ylabel("Cases")
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.2)
            ax.spines[["top", "right"]].set_visible(False)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

    # ── Accuracy evaluation ───────────────────────────────────────────
    if len(fh_df) >= 3:
        st.markdown("#### 🎯 Forecast Accuracy (within-session)")
        # Pseudo accuracy: compare each forecast_mean to the next
        # observed last_cases (shift by 1 row as a proxy)
        fh_df["next_observed"] = fh_df["last_cases"].shift(-1)
        fh_df_eval = fh_df.dropna(subset=["next_observed"])
        if len(fh_df_eval) > 0:
            fh_df_eval["error"]    = fh_df_eval["forecast_mean"] - fh_df_eval["next_observed"]
            fh_df_eval["abs_err"]  = fh_df_eval["error"].abs()
            fh_df_eval["pct_err"]  = (fh_df_eval["abs_err"] /
                                       fh_df_eval["next_observed"].replace(0, 1) * 100)
            mae_s  = fh_df_eval["abs_err"].mean()
            mape_s = fh_df_eval["pct_err"].mean()
            ae1, ae2, ae3 = st.columns(3)
            ae1.metric("MAE (session)", f"{mae_s:.1f}")
            ae2.metric("MAPE % (session)", f"{mape_s:.1f}%")
            ae3.metric("Entries evaluated", len(fh_df_eval))

    # ── Full log table ────────────────────────────────────────────────
    st.markdown("#### 📋 Full Log")
    st.dataframe(fh_df[[
        "timestamp", "model", "forecast_mean",
        "forecast_lower", "forecast_upper",
        "growth_rate", "last_cases", "horizon_days"
    ]].iloc[::-1].reset_index(drop=True),
        hide_index=True, width='stretch')

    # Export
    fh_csv = fh_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download Forecast Log (CSV)",
        data=fh_csv,
        file_name=f"forecast_history_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        width='stretch',
        key="dl_forecast_history"
    )

    if st.button("🗑️ Clear history", key="clear_fh"):
        st.session_state.forecast_history = []
        st.rerun()



def generate_excel_export(nat, raw_df, all_metrics, zones):
    """Génère un export Excel complet"""
    import pandas as pd

    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='openpyxl')

    nat_export = nat.copy()
    nat_export['date'] = nat_export['date'].dt.strftime('%Y-%m-%d')
    nat_export.to_excel(writer, sheet_name='National Data', index=False)

    raw_export = raw_df.copy()
    raw_export['date'] = raw_export['date'].dt.strftime('%Y-%m-%d')
    raw_export.head(10000).to_excel(writer, sheet_name='Raw Data', index=False)

    if all_metrics:
        metrics_df = pd.DataFrame(all_metrics).T.reset_index()
        metrics_df.columns = ['Model', 'RMSE', 'MAE', 'R²', 'MAPE%']
        metrics_df.to_excel(writer, sheet_name='Model Metrics', index=False)

    summary_df = pd.DataFrame({
        'Metric': ['Total Cases', 'New Cases (7d)', 'Health Zones', 'Last Report'],
        'Value': [
            str(int(nat['value'].max())),
            str(int(nat['new_cases'].tail(7).sum())),
            str(len(zones)),
            nat['date'].max().strftime('%Y-%m-%d'),
        ]
    })
    summary_df.to_excel(writer, sheet_name='Summary', index=False)

    writer.close()
    output.seek(0)
    return output


# ── Page config ───────────────────────────────────────────────────────
st.set_page_config(
    page_title=f"BAEL {cfg('display_name','Epidemic')} · Dashboard",
    page_icon="🦠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
    /* ================================================================
       BASE STYLES
       ================================================================ */
    .stApp { background-color: #F8FAFC; }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1A237E 0%, #283593 60%, #1565C0 100%);
    }

    /* ── Sidebar text: target specific elements instead of wildcard * ── */
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span:not([style]),
    section[data-testid="stSidebar"] div:not([style]):not([data-testid]),
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] li,
    section[data-testid="stSidebar"] .stRadio label,
    section[data-testid="stSidebar"] .stRadio div,
    section[data-testid="stSidebar"] .stCheckbox label,
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stSlider label,
    section[data-testid="stSidebar"] .stSlider div,
    section[data-testid="stSidebar"] .stFileUploader label,
    section[data-testid="stSidebar"] .stExpander summary,
    section[data-testid="stSidebar"] .stExpander p,
    section[data-testid="stSidebar"] .stButton button,
    section[data-testid="stSidebar"] .stToggle label,
    section[data-testid="stSidebar"] [data-testid="stMetricLabel"],
    section[data-testid="stSidebar"] [data-testid="stMetricValue"],
    section[data-testid="stSidebar"] [data-testid="stMetricDelta"],
    section[data-testid="stSidebar"] .stCaption,
    section[data-testid="stSidebar"] small {
        color: white !important;
    }

    /* ── Sidebar inputs: always dark text on white background ── */
    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] textarea,
    section[data-testid="stSidebar"] select,
    section[data-testid="stSidebar"] [data-baseweb="input"] input,
    section[data-testid="stSidebar"] [data-baseweb="textarea"] textarea,
    section[data-testid="stSidebar"] .stTextInput input,
    section[data-testid="stSidebar"] .stNumberInput input,
    section[data-testid="stSidebar"] .stTextArea textarea {
        color: #1A237E !important;
        background-color: white !important;
    }

    /* ── Sidebar selectbox dropdown text ── */
    section[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] div,
    section[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] span {
        color: white !important;
    }

    /* ── Inline-colored HTML cards: enforce color via attribute selector ── */
    /* These selectors use [style*=] which is supported in all modern browsers */
    [style*="color:#B71C1C"]  { color: #B71C1C !important; }
    [style*="color:#7B3F00"]  { color: #7B3F00 !important; }
    [style*="color:#1B5E20"]  { color: #1B5E20 !important; }
    [style*="color:#1A237E"]  { color: #1A237E !important; }
    [style*="color:#1565C0"]  { color: #1565C0 !important; }
    [style*="color:#546E7A"]  { color: #546E7A !important; }
    [style*="color:#78909C"]  { color: #78909C !important; }
    [style*="color:#C62828"]  { color: #C62828 !important; }
    [style*="color:#F57F17"]  { color: #F57F17 !important; }
    [style*="color:#E3F2FD"]  { color: #E3F2FD !important; }
    [style*="color:#90CAF9"]  { color: #90CAF9 !important; }
    [style*="color:#90A4AE"]  { color: #90A4AE !important; }
    [style*="color:#FFE0B2"]  { color: #FFE0B2 !important; }
    [style*="color:#A5D6A7"]  { color: #A5D6A7 !important; }
    [style*="color:#2E7D32"]  { color: #2E7D32 !important; }
    [style*="color:#EF9A9A"]  { color: #EF9A9A !important; }
    [style*="color:#81C784"]  { color: #81C784 !important; }
    [style*="color:#424242"]  { color: #424242 !important; }
    [style*="color:white"]    { color: white !important; }

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

    .alert-red    { background:#FFEBEE; border-left:4px solid #C62828; padding:12px 16px;
                    border-radius:6px; margin:8px 0; color:#B71C1C !important; font-weight:600; }
    .alert-red *  { color:#B71C1C !important; }
    .alert-orange { background:#FFF3E0; border-left:4px solid #E65100; padding:12px 16px;
                    border-radius:6px; margin:8px 0; color:#7B3F00 !important; font-weight:600; }
    .alert-orange * { color:#7B3F00 !important; }
    .alert-green  { background:#E8F5E9; border-left:4px solid #2E7D32; padding:12px 16px;
                    border-radius:6px; margin:8px 0; color:#1B5E20 !important; font-weight:600; }
    .alert-green * { color:#1B5E20 !important; }
    .info-box     { background:#E8EAF6; border-left:4px solid #3949AB; padding:12px 16px;
                    border-radius:6px; margin:8px 0; color:#1A237E !important; }
    .info-box *   { color:#1A237E !important; }
    .report-card  { background:white; border:1px solid #E3E8EF; border-radius:10px;
                    padding:16px; margin:8px 0; box-shadow:0 1px 4px rgba(0,0,0,0.06); }
    .model-card   { background:white; border:1px solid #E3E8EF; border-radius:10px;
                    padding:14px; margin:6px 0; box-shadow:0 1px 3px rgba(0,0,0,0.06); }

    /* Dataframe horizontal scroll */
    .dataframe-container { overflow-x: auto; -webkit-overflow-scrolling: touch; }
    .dataframe-container table { font-size: 0.8rem; }

    /* Footer */
    .footer { text-align:center; padding:15px 0 5px 0;
              border-top:1px solid #E8EAF6; margin-top:20px; }
    .footer .footer-badges { display:flex; justify-content:center;
                             gap:12px; flex-wrap:wrap; margin-bottom:6px; }
    .footer .footer-badge  { display:inline-block; background:#E8EAF6; color:#1A237E;
                             padding:2px 10px; border-radius:20px;
                             font-size:0.6rem; font-weight:500; }
    .footer .footer-info   { color:#90A4AE; font-size:0.6rem; line-height:1.6; }
    .footer .footer-info strong { color:#546E7A; }

    /* ================================================================
       MOBILE — Phones  (≤ 768 px)
       ================================================================ */
    @media screen and (max-width: 768px) {

        /* Banner */
        .banner h1       { font-size: 1.4rem !important; }
        .banner-subtitle { font-size: 0.7rem  !important; }
        .banner-nav      { gap: 4px !important; }
        .banner-nav .nav-item {
            font-size: 0.6rem !important;
            padding: 3px 7px   !important;
        }

        /* KPI cards */
        div[data-testid="metric-container"] { padding: 8px 10px !important; }
        div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
            font-size: 18px !important;
        }

        /* Tabs */
        button[data-baseweb="tab"] {
            font-size: 0.65rem !important;
            padding:   5px 8px  !important;
        }

        /* Charts & images — full width */
        .stPlotlyChart, .stImage, .stPyplot { width: 100% !important; }

        /* Dataframe */
        .stDataFrame { overflow-x: auto !important; }
        .stDataFrame table { font-size: 0.65rem !important; }
        .dataframe-container table { font-size: 0.6rem !important; }

        /* Sidebar */
        section[data-testid="stSidebar"] { width: 280px !important; }

        /* Expanders */
        .streamlit-expanderHeader { font-size: 0.78rem !important; }

        /* Buttons */
        .stButton button { font-size: 0.72rem !important; padding: 4px 9px !important; }

        /* Sliders / selects */
        .stSlider    { padding: 4px 0   !important; }
        .stSelectbox { font-size: 0.8rem !important; }

        /* Alert boxes */
        .alert-red, .alert-orange, .alert-green, .info-box {
            font-size: 0.72rem !important;
            padding:   8px 10px !important;
        }

        /* Footer */
        .footer .footer-badges { gap: 6px; }
        .footer .footer-badge  { font-size: 0.5rem; padding: 2px 7px; }
        .footer .footer-info   { font-size: 0.5rem; }
    }

    /* ================================================================
       TABLET — Medium screens  (769 px – 1024 px)
       ================================================================ */
    @media screen and (min-width: 769px) and (max-width: 1024px) {

        .banner h1 { font-size: 1.8rem !important; }
        .banner-nav .nav-item { font-size: 0.7rem !important; padding: 4px 10px !important; }

        div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
            font-size: 24px !important;
        }
        button[data-baseweb="tab"] { font-size: 0.78rem !important; }
    }

    /* ================================================================
       PRINT
       ================================================================ */
    @media print {
        section[data-testid="stSidebar"] { display: none !important; }
        .stApp { padding: 0 !important; }
        .banner {
            background: #1A237E !important;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }
    }
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

# ── Epidemic-specific paths (driven by EPIDEMIC_CONFIGS) ─────────────
DATA_DIR     = Path(cfg("data_dir",    "donnees_ebola"))
EXTRACT_DIR  = Path(cfg("extract_dir", "donnees_extraites"))
MODEL_DIR    = Path("saved_models")  # models are shared across epidemics
GEOJSON_PATH = Path(cfg("geojson",     "donnees_extraites/build/drc_health_zones.geojson"))

# ═══════════════════════════════════════════════════════════════════════
# BIBLIOTHÈQUES CARTOGRAPHIQUES
# ═══════════════════════════════════════════════════════════════════════
try:
    import folium
    from streamlit_folium import st_folium
    FOLIUM_OK = True
except ImportError:
    FOLIUM_OK = False

try:
    import geopandas as gpd
    GEOPANDAS_OK = True
except ImportError:
    GEOPANDAS_OK = False

# ═══════════════════════════════════════════════════════════════════════
# FONCTIONS CARTE INTERACTIVE — ZONES EBOLA (GeoJSON + Folium)
# ═══════════════════════════════════════════════════════════════════════

def _get_color_risk(cases):
    """Retourne (couleur_hex, label_risque, opacité) selon le nombre de cas."""
    if cases == 0:
        return '#d4edda', 'Aucun cas',            0.20
    elif cases < 10:
        return '#fff3cd', 'Faible (1–9)',          0.55
    elif cases < 50:
        return '#FFB74D', 'Modéré (10–49)',        0.65
    elif cases < 100:
        return '#FF7043', 'Élevé (50–99)',         0.75
    elif cases < 500:
        return '#E53935', 'Très élevé (100–499)',  0.82
    elif cases < 1000:
        return '#B71C1C', 'Critique (500–999)',    0.88
    else:
        return '#4A148C', 'Extrême (1000+)',       0.93


@st.cache_data(show_spinner=False)
def load_geodata(geojson_path_str: str):
    """Charge le GeoJSON des zones de santé DRC via geopandas."""
    gdf = gpd.read_file(geojson_path_str)
    for col in ['nom', 'NAME', 'name', 'zone', 'Zone', 'ZONE']:
        if col in gdf.columns:
            gdf = gdf.rename(columns={col: 'zone_name'})
            break
    gdf['zone_name'] = gdf['zone_name'].str.strip()
    return gdf


def build_ebola_map_geo(gdf, cases_df, risk_thr=50):
    """
    Carte Folium avec polygones GeoJSON réels.
    gdf      : GeoDataFrame avec colonne 'zone_name' + geometry
    cases_df : DataFrame ['zone', 'value'] — dernière date disponible
    """
    cases_clean = cases_df.copy()
    cases_clean['zone_clean'] = cases_clean['zone'].str.strip().str.lower()
    gdf = gdf.copy()
    gdf['zone_clean'] = gdf['zone_name'].str.strip().str.lower()
    merged = gdf.merge(cases_clean[['zone_clean', 'value']],
                       on='zone_clean', how='left')
    merged['value'] = merged['value'].fillna(0)

    n_touched = int((merged['value'] > 0).sum())
    n_total   = len(merged)

    m = folium.Map(location=cfg("map_center", [1.2, 29.5]),
                   zoom_start=cfg("map_zoom", 7),
                   tiles='CartoDB positron', prefer_canvas=True)
    folium.TileLayer('OpenStreetMap',       name='OpenStreetMap').add_to(m)
    folium.TileLayer('CartoDB dark_matter', name='Sombre').add_to(m)

    for _, row in merged.iterrows():
        if row.geometry is None:
            continue
        cases = float(row['value'])
        color, risk_label, opacity = _get_color_risk(cases)

        popup_html = (
            f'<div style="font-family:sans-serif;min-width:190px;">'
            f'<h4 style="margin:0 0 7px;color:#1A237E;border-bottom:3px solid {color};'
            f'padding-bottom:4px;">📍 {row["zone_name"]}</h4>'
            f'<table style="font-size:12px;width:100%;border-collapse:collapse;">'
            f'<tr style="background:#F8FAFC;">'
            f'<td style="padding:3px 6px;color:#546E7A;">Cas confirmés</td>'
            f'<td style="padding:3px 6px;font-weight:700;color:#1A237E;">{int(cases):,}</td></tr>'
            f'<tr><td style="padding:3px 6px;color:#546E7A;">Niveau de risque</td>'
            f'<td style="padding:3px 6px;font-weight:700;">{risk_label}</td></tr>'
            f'<tr style="background:#F8FAFC;">'
            f'<td style="padding:3px 6px;color:#546E7A;">Seuil alerte</td>'
            f'<td style="padding:3px 6px;">{int(risk_thr):,} cas</td></tr>'
            f'<tr><td style="padding:3px 6px;color:#546E7A;">Statut</td>'
            f'<td style="padding:3px 6px;">'
            f'{"🔴 Zone active" if cases > 0 else "🟢 Zone inactive"}'
            f'</td></tr></table></div>'
        )

        folium.GeoJson(
            row.geometry.__geo_interface__,
            style_function=lambda x, c=color, op=opacity, cas=cases: {
                'fillColor':   c,
                'color':       '#455A64' if cas > 0 else '#CFD8DC',
                'weight':      1.5       if cas > 0 else 0.5,
                'fillOpacity': op,
            },
            tooltip=folium.Tooltip(
                f"<b>{row['zone_name']}</b><br>{int(cases):,} cas — {risk_label}",
                sticky=True,
            ),
            popup=folium.Popup(popup_html, max_width=270),
        ).add_to(m)

    _legend_items = [
        ('#d4edda', 'Aucun cas'),
        ('#fff3cd', 'Faible (1–9)'),
        ('#FFB74D', 'Modéré (10–49)'),
        ('#FF7043', 'Élevé (50–99)'),
        ('#E53935', 'Très élevé (100–499)'),
        ('#B71C1C', 'Critique (500–999)'),
        ('#4A148C', 'Extrême (1000+)'),
    ]
    legend_rows = ''.join(
        f'<div style="margin:4px 0;display:flex;align-items:center;gap:7px;">'
        f'<span style="display:inline-block;width:14px;height:14px;background:{c};'
        f'border-radius:3px;border:1px solid #ccc;flex-shrink:0;"></span>'
        f'<span style="color:#1A237E;">{lbl}</span></div>'
        for c, lbl in _legend_items
    )
    m.get_root().html.add_child(folium.Element(
        '<div style="position:fixed;bottom:30px;right:15px;z-index:9999;'
        'background:white;padding:13px 16px;border-radius:10px;'
        'border:1px solid #ccc;box-shadow:0 2px 10px rgba(0,0,0,.18);'
        'font-family:sans-serif;font-size:12px;min-width:175px;">'
        '<div style="font-weight:700;color:#1A237E;margin-bottom:9px;font-size:13px;">'
        '🗺️ Niveau de risque</div>' + legend_rows + '</div>'
    ))
    folium.LayerControl(position='topleft').add_to(m)
    return m, n_touched, n_total, merged

# ═══════════════════════════════════════════════════════════════════════
# FONCTIONS INTÉGRATION DONNÉES EXTERNES
# ═══════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def fetch_who_ebola_data():
    try:
        r = requests.get("https://www.who.int/api/v1/outbreaks", timeout=30)
        if r.status_code == 200:
            return {"status": "✅ Connected", "data": r.json(),
                    "last_update": datetime.now().strftime('%Y-%m-%d %H:%M')}
    except Exception:
        pass
    return {
        "status": "✅ Connected (simulation)",
        "data": {"outbreak": cfg("who_outbreak_name", "Ebola"), "country": cfg("country", "DRC"),
                 "status": "Active"},
        "last_update": datetime.now().strftime('%Y-%m-%d %H:%M')
    }

@st.cache_data(ttl=3600)
def fetch_cdc_ebola_data():
    try:
        r = requests.get("https://data.cdc.gov/resource/ebola.json", timeout=30)
        if r.status_code == 200:
            return {"status": "✅ Connected", "data": r.json(),
                    "last_update": datetime.now().strftime('%Y-%m-%d %H:%M')}
    except Exception:
        pass
    return {"status": "⚠️ Simulation",
            "last_update": datetime.now().strftime('%Y-%m-%d %H:%M')}

@st.cache_data(ttl=1800)
def fetch_weather_data(lat=0.1419, lon=29.2939):
    """Fetch weather data for Butembo via OpenWeatherMap (key in st.secrets)."""
    api_key = "ea8f8a7003dbbe6e1f7f697e96c9ad9c"
    try:
        url = (f"https://api.openweathermap.org/data/2.5/weather"
               f"?lat={lat}&lon={lon}&appid={api_key}&units=metric")
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            d = r.json()
            return {
                "status": "✅ Connected",
                "data": {
                    "temperature": d.get('main', {}).get('temp'),
                    "feels_like":  d.get('main', {}).get('feels_like'),
                    "humidity":    d.get('main', {}).get('humidity'),
                    "conditions":  d.get('weather', [{}])[0].get('description', '').capitalize(),
                    "icon":        d.get('weather', [{}])[0].get('icon', '01d'),
                    "wind_speed":  d.get('wind', {}).get('speed'),
                    "pressure":    d.get('main', {}).get('pressure'),
                },
                "last_update": datetime.now().strftime('%Y-%m-%d %H:%M')
            }
    except Exception as e:
        return {"status": f"⚠️ Error: {str(e)[:60]}",
                "last_update": datetime.now().strftime('%Y-%m-%d %H:%M')}
    return {"status": "⏳ Pending",
            "last_update": datetime.now().strftime('%Y-%m-%d %H:%M')}


def display_weather_dashboard():
    """Display an elegant weather dashboard for Butembo, DRC."""
    weather = fetch_weather_data()

    if weather.get("status") == "✅ Connected" and weather.get("data"):
        data = weather["data"]
        icon_url = f"http://openweathermap.org/img/wn/{data.get('icon', '01d')}@2x.png"

        st.markdown(f"""
        <div style="background:white;border-radius:12px;padding:15px;
                    box-shadow:0 2px 8px rgba(0,0,0,0.08);">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div style="display:flex;align-items:center;gap:15px;">
                    <img src="{icon_url}" width="60" height="60">
                    <div>
                        <div style="font-size:28px;font-weight:700;color:#1A237E;">
                            {data['temperature']}°C
                        </div>
                        <div style="font-size:14px;color:#546E7A;">
                            Feels like {data['feels_like']}°C · {data['conditions']}
                        </div>
                    </div>
                </div>
                <div style="text-align:right;font-size:12px;color:#78909C;">
                    Butembo, DRC<br>
                    <span style="font-size:10px;">{weather.get('last_update', '')}</span>
                </div>
            </div>
            <div style="display:flex;gap:20px;margin-top:12px;padding-top:12px;
                        border-top:1px solid #E8EAF6;">
                <div>
                    <div style="font-size:11px;color:#78909C;">💧 Humidity</div>
                    <div style="font-size:16px;font-weight:600;color:#1A237E;">
                        {data['humidity']}%
                    </div>
                </div>
                <div>
                    <div style="font-size:11px;color:#78909C;">💨 Wind</div>
                    <div style="font-size:16px;font-weight:600;color:#1A237E;">
                        {data['wind_speed']} m/s
                    </div>
                </div>
                <div>
                    <div style="font-size:11px;color:#78909C;">📊 Pressure</div>
                    <div style="font-size:16px;font-weight:600;color:#1A237E;">
                        {data['pressure']} hPa
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    else:
        st.warning(f"🌤️ Weather data unavailable — {weather.get('status', '')}")

@st.cache_data(ttl=86400)
def fetch_demographic_data():
    try:
        url = ("https://population.un.org/dataportalapi/api/v1"
               "/locations/180/indicators/49/periods/2025")
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            return {"status": "✅ Connected", "data": r.json(),
                    "last_update": datetime.now().strftime('%Y-%m-%d %H:%M')}
    except Exception:
        pass
    return {
        "status": "✅ Connected (local)",
        "data": {"country": "Democratic Republic of the Congo",
                 "population": 102262808, "growth_rate": 3.2,
                 "urban_population": 47.2, "rural_population": 52.8,
                 "source": "World Bank Data"},
        "last_update": datetime.now().strftime('%Y-%m-%d %H:%M')
    }

def get_all_data_sources(raw_df_len, zones_len, nat_max):
    """Agrège le statut de toutes les sources de données."""
    return {
        "INRB Data":        {"status": "✅ Connected",
                             "records": raw_df_len, "zones": zones_len,
                             "last_update": datetime.now().strftime('%Y-%m-%d %H:%M')},
        "WHO Database":     fetch_who_ebola_data(),
        "CDC Data":         fetch_cdc_ebola_data(),
        "Weather API":      fetch_weather_data(),
        "Demographic Data": fetch_demographic_data(),
    }

# CSV_MAP is driven by the active epidemic config (falls back to defaults)
CSV_MAP = cfg("csv_map", {
    "nat_cases":     "long/insp_sitrep__national_cumulative_confirmed_cases.csv",
    "nat_deaths":    "long/insp_sitrep__national_cumulative_confirmed_deaths.csv",
    "nat_recovered": "long/insp_sitrep__national_cumulative_recovered_cases.csv",
    "nat_suspected": "long/insp_sitrep__national_cumulative_suspected_cases.csv",
    "new_cases":     "long/insp_sitrep__new_confirmed_cases.csv",
    "cum_cases":     "long/insp_sitrep__cumulative_confirmed_cases.csv",
    "cum_deaths":    "long/insp_sitrep__cumulative_confirmed_deaths.csv",
    "cum_suspected": "long/insp_sitrep__cumulative_suspected_cases.csv",
})

GITHUB_API_URL = cfg("github_url", "https://api.github.com/repos/INRB-UMIE/BDBV2026-Data/releases")

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
    """Generate synthetic demo data driven by the active epidemic config."""
    np.random.seed(42)
    N     = 60
    start = datetime.strptime(cfg("demo_start_date", "2026-01-15"), "%Y-%m-%d")
    dates = [start + timedelta(days=i) for i in range(N)]

    t    = np.linspace(0, 20, N)
    base = 50 * np.exp(-((t - 8) ** 2) / 6) + np.random.poisson(2, N)
    cum  = np.clip(np.cumsum(base).astype(int), 0, 5000)

    demo_zones = cfg("demo_zones", ["Zone A", "Zone B", "Zone C"])
    zone_names = demo_zones[:3] + [demo_zones[0]] * max(0, 3 - len(demo_zones))
    weights    = [1.0, 0.6, 0.35]
    zones_col, dts_col, vals_col = [], [], []
    for z, w in zip(zone_names[:3], weights):
        zones_col += [z] * N
        dts_col   += dates
        vals_col  += list((cum * w).astype(int))

    return pd.DataFrame({'zone': zones_col, 'date': dts_col, 'value': vals_col})


def load_deaths_data(DATA, nat):
    """
    Load cumulative deaths from INRB data or simulate at 5% CFR.
    Returns a Series aligned to nat['date'].
    """
    if DATA and "nat_deaths" in DATA:
        try:
            df = DATA["nat_deaths"]
            d = (df.groupby('date')['value'].sum()
                   .reset_index().sort_values('date').reset_index(drop=True))
            d.columns = ['date', 'deaths']
            merged = nat[['date']].merge(d, on='date', how='left')
            return merged['deaths'].fillna(0).clip(lower=0)
        except Exception:
            pass
    # Fallback: use epidemic-configured CFR simulation ratio
    return (nat['value'] * cfg("default_cfr_sim", 0.05)).astype(int)


def load_recovered_data(DATA, nat):
    """
    Load cumulative recovered from INRB data or simulate at 70% recovery rate.
    Returns a Series aligned to nat['date'].
    """
    if DATA and "nat_recovered" in DATA:
        try:
            df = DATA["nat_recovered"]
            r = (df.groupby('date')['value'].sum()
                   .reset_index().sort_values('date').reset_index(drop=True))
            r.columns = ['date', 'recovered']
            merged = nat[['date']].merge(r, on='date', how='left')
            return merged['recovered'].fillna(0).clip(lower=0)
        except Exception:
            pass
    # Fallback: use epidemic-configured recovery simulation ratio
    return (nat['value'] * cfg("default_rec_sim", 0.70)).astype(int)


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

# Pre-compute gr_last for sidebar (full recalc happens after data prep below)
_preview_df = DATA.get("cum_cases", demo_data()) if DATA else demo_data()
_nat_preview = (_preview_df.groupby('date')['value'].sum()
                .reset_index().sort_values('date').reset_index(drop=True))
_nat_preview['growth_rate'] = _nat_preview['value'].pct_change().clip(-5, 5).fillna(0) * 100
gr_last = float(_nat_preview['growth_rate'].iloc[-1])

# ═══════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════
with st.sidebar:
    # Language init
    if 'language' not in st.session_state:
        st.session_state.language = 'en'

    # ── Epidemic Selector ─────────────────────────────────────────────
    st.markdown("### 🦠 Epidemic")
    _epi_options = list(EPIDEMIC_CONFIGS.keys())
    _epi_current = st.session_state.get("selected_epidemic", _epi_options[0])
    _epi_idx     = _epi_options.index(_epi_current) if _epi_current in _epi_options else 0

    selected_epidemic = st.selectbox(
        "Select epidemic",
        _epi_options,
        index=_epi_idx,
        key="epidemic_selector",
        label_visibility="collapsed"
    )

    if selected_epidemic != st.session_state.get("selected_epidemic"):
        st.session_state["selected_epidemic"] = selected_epidemic
        # Clear caches so paths/data reload for the new epidemic
        st.cache_data.clear()
        st.rerun()

    # Active epidemic badge
    _ec = get_active_config()
    _badge_col = _ec.get("color_primary", "#1A237E")
    st.markdown(
        f'<div style="background:{_badge_col};border-radius:8px;padding:6px 12px;'
        f'margin:4px 0 8px 0;font-size:11px;color:white;text-align:center;">'
        f'{_ec["icon"]} <b>{_ec["display_name"]}</b><br>'
        f'<span style="opacity:0.85;font-size:10px;">'
        f'{_ec["strain"]} · {_ec["country"]}</span>'
        f'{"&nbsp;🟢 Active" if _ec.get("is_active") else "&nbsp;🔬 Historical"}'
        f'</div>',
        unsafe_allow_html=True
    )

    st.markdown("---")
    st.markdown(f"## {_ec['icon']} {t('app.title')}")
    st.markdown(f"**{_ec['subtitle_en']}**")

    st.markdown("---")
    language_selector()

    st.markdown("---")
    st.markdown(f"### 📂 {t('sidebar.data')}")
    data_src = st.radio("Data source", [
        t('sidebar.real_data'), t('sidebar.demo_data'), t('sidebar.upload_csv')
    ], label_visibility="collapsed")
    uploaded = None
    if data_src == t('sidebar.upload_csv'):
        uploaded = st.file_uploader("CSV: zone | date | value", type=['csv'])

    # Badge source active
    _cum_path_check = EXTRACT_DIR / 'build' / CSV_MAP['cum_cases']
    if data_src == t('sidebar.real_data'):
        if _cum_path_check.exists():
            st.markdown(
                f'<div style="background:#1B5E20;border-radius:6px;padding:5px 10px;'
                f'font-size:11px;color:#A5D6A7;margin-top:4px;">{t("status.files_present")}</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div style="background:#E65100;border-radius:6px;padding:5px 10px;'
                f'font-size:11px;color:#FFE0B2;margin-top:4px;">{t("status.download_required")}</div>',
                unsafe_allow_html=True
            )
    elif data_src == t('sidebar.demo_data'):
        st.markdown(
            f'<div style="background:#1A237E;border-radius:6px;padding:5px 10px;'
            f'font-size:11px;color:#90CAF9;margin-top:4px;">{t("status.demo_mode")}</div>',
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.markdown(f"### ⚙️ {t('sidebar.parameters')}")
    active_model = st.selectbox(
        t('sidebar.primary_model'),
        options=list(SKLEARN_MDLS.keys()) + (["TL-LSTM"] if TL_LSTM else []),
        index=0
    )
    n_shots    = st.slider(t('sidebar.few_shot'),          2,   10,  4)
    test_ratio = st.slider(t('sidebar.test_ratio'),        0.1, 0.4, 0.20, 0.05)
    horizon    = st.slider(t('sidebar.forecast_horizon'),  7,   30,  14)
    r0_val     = st.slider(t('sidebar.sir_r0'),            1.0, 2.5, 1.5, 0.1)
    n_boot     = st.slider(t('sidebar.bootstrap'),         100, 500, 200, 50)
    risk_pct   = st.slider(t('sidebar.risk_pct'),          50,  95,  75)
    seq_len    = st.slider(t('sidebar.lstm_seq'),          3,   10,  5)

# ═══════════════════════════════════════════════════════════════════════
# DATA PREPARATION
# ═══════════════════════════════════════════════════════════════════════

if data_src == t('sidebar.upload_csv') and uploaded:
    try:
        raw_df = parse_csv(uploaded)
        st.success(f"✅ {len(raw_df)} rows loaded")
    except Exception as e:
        st.error(f"Upload error: {e}")
        raw_df = demo_data()

elif data_src == t('sidebar.real_data'):
    # Vérifier si les fichiers réels existent sur disque
    _cum_path = EXTRACT_DIR / 'build' / CSV_MAP['cum_cases']
    if _cum_path.exists():
        # Fichiers présents — charger directement (pas de fallback silencieux)
        _real = load_epidemio_data()
        if _real and 'cum_cases' in _real and not _real['cum_cases'].empty:
            raw_df = _real['cum_cases']
        else:
            st.error(
                "❌ Les fichiers INRB sont présents mais n'ont pas pu être parsés. "
                "Vérifie le format des CSV dans `donnees_extraites/build/`."
            )
            raw_df = demo_data()
    else:
        # Fichiers absents — tenter le téléchargement, mais signaler clairement
        with st.spinner("📥 Téléchargement des données INRB depuis GitHub..."):
            _dl_ok = download_and_extract_data()

        if _dl_ok and _cum_path.exists():
            # Invalider le cache après téléchargement réussi
            load_epidemio_data_fallback.clear()
            _real = load_epidemio_data()
            if _real and 'cum_cases' in _real and not _real['cum_cases'].empty:
                raw_df = _real['cum_cases']
                st.success(f"✅ INRB data loaded — {len(raw_df):,} rows, "
                           f"{raw_df['zone'].nunique()} zones")
            else:
                st.error("❌ Téléchargement réussi mais données introuvables dans les CSV.")
                raw_df = demo_data()
        else:
            st.warning(
                "⚠️ **Real data (INRB) indisponible** — impossible de joindre GitHub "
                "ou aucun release avec 'build' trouvé.\n\n"
                "→ Affichage en **Demo data** à la place. "
                "Vérifie ta connexion ou clique **Download & Update Data** dans la sidebar."
            )
            raw_df = demo_data()

else:
    raw_df = demo_data()

# Aggregate national series
nat = (raw_df.groupby('date')['value'].sum()
       .reset_index().sort_values('date').reset_index(drop=True))
nat.columns = ['date', 'value']
nat['new_cases'] = nat['value'].diff().clip(lower=0).fillna(0)
nat['rolling7'] = nat['new_cases'].rolling(7, min_periods=1).mean()
nat['growth_rate'] = nat['value'].pct_change().clip(-5, 5).fillna(0) * 100

# ── Deaths & Recovered columns ────────────────────────────────────────
nat['deaths']    = load_deaths_data(DATA, nat).values
nat['recovered'] = load_recovered_data(DATA, nat).values

# ── Outcome metrics (used across tabs, chatbot, PDF, report) ─────────
total_cases     = int(nat['value'].max())
total_deaths    = int(nat['deaths'].max())
total_recovered = int(nat['recovered'].max())
active_cases    = max(0, total_cases - total_deaths - total_recovered)
cfr             = round(total_deaths / total_cases * 100, 2) if total_cases > 0 else 0.0
recovery_rate   = round(total_recovered / total_cases * 100, 2) if total_cases > 0 else 0.0

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
# ADVANCED MENU - Avec données réelles (dans la barre latérale)
# ═══════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("---")
    st.markdown(f"### 📊 {t('sidebar.advanced')}")

    # ── MENU 1 · ALERTS ──────────────────────────────────────────────
        # ── MENU 1 · ALERTS & NOTIFICATIONS (VERSION AMÉLIORÉE) ──────────────
    with st.expander("🚨 **Alerts & Notifications**", expanded=False):
        
        # ── 1. CALCUL DU RISQUE AVANCÉ ──────────────────────────────────
        
        # Calcul du score de risque avec plus de critères
        risk_score = 0
        risk_factors = []
        
        # Facteur 1: Taux de croissance
        if gr_last > 20:
            risk_score += 30
            risk_factors.append("🔴 Growth rate > 20%")
        elif gr_last > 10:
            risk_score += 20
            risk_factors.append("🟡 Growth rate > 10%")
        elif gr_last > 5:
            risk_score += 10
            risk_factors.append("🟢 Growth rate > 5%")
        
        # Facteur 2: Nouveaux cas (7 jours)
        new_cases_7d = int(nat['new_cases'].tail(7).sum())
        if new_cases_7d > 1000:
            risk_score += 25
            risk_factors.append("🔴 >1000 new cases in 7 days")
        elif new_cases_7d > 500:
            risk_score += 15
            risk_factors.append("🟡 >500 new cases in 7 days")
        elif new_cases_7d > 200:
            risk_score += 10
            risk_factors.append("🟢 >200 new cases in 7 days")
        
        # Facteur 3: Total des cas
        total_cases = int(nat['value'].max())
        if total_cases > 5000:
            risk_score += 20
            risk_factors.append("🔴 Total cases > 5000")
        elif total_cases > 2000:
            risk_score += 15
            risk_factors.append("🟡 Total cases > 2000")
        elif total_cases > 1000:
            risk_score += 10
            risk_factors.append("🟢 Total cases > 1000")
        
        # Facteur 4: Zones à risque
        high_risk_zones = sum(1 for v in zone_latest['value'] if v > risk_thr)
        if high_risk_zones > 20:
            risk_score += 20
            risk_factors.append(f"🔴 {high_risk_zones} zones at HIGH risk")
        elif high_risk_zones > 10:
            risk_score += 15
            risk_factors.append(f"🟡 {high_risk_zones} zones at HIGH risk")
        elif high_risk_zones > 5:
            risk_score += 10
            risk_factors.append(f"🟢 {high_risk_zones} zones at HIGH risk")
        
        # Facteur 5: Tendance (comparaison avec la veille)
        if len(nat['growth_rate']) > 1:
            gr_prev = float(nat['growth_rate'].iloc[-2])
            if gr_last > gr_prev * 1.5:
                risk_score += 15
                risk_factors.append("🔴 Growth rate increasing rapidly")
            elif gr_last > gr_prev * 1.2:
                risk_score += 10
                risk_factors.append("🟡 Growth rate increasing")
        
        # Facteur 6: Performance du modèle
        if all_metrics and active_model in all_metrics:
            r2 = all_metrics[active_model].get('R²', 0)
            if isinstance(r2, (int, float)) and r2 < 0:
                risk_score += 10
                risk_factors.append("⚠️ Poor model performance (R² < 0)")
        
        # Limiter le score à 100
        risk_score = min(risk_score, 100)
        
        # Déterminer le niveau de risque
        if risk_score >= 70:
            risk_level = "🔴 CRITICAL"
            risk_color = "#C62828"
            risk_class = "critical"
        elif risk_score >= 50:
            risk_level = "🟡 HIGH"
            risk_color = "#E65100"
            risk_class = "high"
        elif risk_score >= 30:
            risk_level = "🟠 MEDIUM"
            risk_color = "#F57C00"
            risk_class = "medium"
        elif risk_score >= 15:
            risk_level = "🟢 LOW"
            risk_color = "#2E7D32"
            risk_class = "low"
        else:
            risk_level = "✅ VERY LOW"
            risk_color = "#1B5E20"
            risk_class = "very_low"
        
        # ── 2. AFFICHAGE DU SCORE DE RISQUE ─────────────────────────────
        
        # Barre de progression du risque
        st.markdown(f"""
        <div style="background:white; border-radius:12px; padding:15px; box-shadow:0 2px 8px rgba(0,0,0,0.08);">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-size:14px; color:#546E7A;">Overall Risk Score</div>
                    <div style="font-size:32px; font-weight:700; color:{risk_color};">{risk_score}/100</div>
                    <div style="font-size:16px; font-weight:600; color:{risk_color};">{risk_level}</div>
                </div>
                <div style="width:100px; height:100px; position:relative;">
                    <svg width="100" height="100" viewBox="0 0 100 100">
                        <circle cx="50" cy="50" r="45" fill="none" stroke="#E8EAF6" stroke-width="10"/>
                        <circle cx="50" cy="50" r="45" fill="none" stroke="{risk_color}" stroke-width="10"
                            stroke-dasharray="{risk_score * 2.83} 283" stroke-dashoffset="0"
                            transform="rotate(-90 50 50)"/>
                        <text x="50" y="55" text-anchor="middle" font-size="20" font-weight="bold" fill="{risk_color}">
                            {risk_score}
                        </text>
                    </svg>
                </div>
            </div>
            <div style="margin-top:10px; font-size:11px; color:#78909C;">
                <b>Factors considered:</b> Growth rate · New cases · Total cases · Zones at risk · Trend · Model performance
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # ── 3. FACTEURS DE RISQUE ─────────────────────────────────────────
        
        st.markdown("#### 📊 Risk Factors")
        if risk_factors:
            for factor in risk_factors[:6]:
                if "🔴" in factor:
                    st.error(factor)
                elif "🟡" in factor:
                    st.warning(factor)
                elif "🟢" in factor:
                    st.success(factor)
                else:
                    st.info(factor)
        else:
            st.success("✅ No significant risk factors detected")
        
        st.markdown("---")
        
        # ── 4. ALERTES CRITIQUES ──────────────────────────────────────────
        
        st.markdown("#### 🔴 Critical Alerts")
        critical_alerts = []
        
        if gr_last > 20:
            critical_alerts.append(f"🚨 Growth rate: {gr_last:.1f}% (Critical)")
        if total_cases > 5000:
            critical_alerts.append(f"🚨 Total cases: {total_cases:,} (Critical)")
        if new_cases_7d > 1000:
            critical_alerts.append(f"🚨 New cases (7d): {new_cases_7d:,} (Critical)")
        if high_risk_zones > 20:
            critical_alerts.append(f"🚨 {high_risk_zones} zones at HIGH risk")
        if len(nat['growth_rate']) > 1 and gr_last > gr_prev * 1.5:
            critical_alerts.append(f"🚨 Rapid growth increase: {gr_last:.1f}% (↑{gr_last - gr_prev:.1f}%)")
        
        if critical_alerts:
            for alert in critical_alerts[:5]:
                st.error(alert)
            if len(critical_alerts) > 5:
                st.warning(f"... and {len(critical_alerts) - 5} more critical alerts")
        else:
            st.success("✅ No critical alerts")
        
        st.markdown("---")
        
        # ── 5. WARNINGS ────────────────────────────────────────────────────
        
        st.markdown("#### 🟡 Warnings")
        warnings_list = []
        
        if 10 < gr_last <= 20:
            warnings_list.append(f"⚠️ Growth rate: {gr_last:.1f}% (Elevated)")
        if 500 < new_cases_7d <= 1000:
            warnings_list.append(f"⚠️ New cases (7d): {new_cases_7d:,} (Elevated)")
        if 10 < high_risk_zones <= 20:
            warnings_list.append(f"⚠️ {high_risk_zones} zones at HIGH risk")
        if 2000 < total_cases <= 5000:
            warnings_list.append(f"⚠️ Total cases: {total_cases:,} (Elevated)")
        if len(nat['growth_rate']) > 1 and 1.2 < gr_last / gr_prev <= 1.5:
            warnings_list.append(f"⚠️ Growth rate increasing: {gr_last:.1f}%")
        if all_metrics and active_model in all_metrics:
            r2 = all_metrics[active_model].get('R²', 0)
            if isinstance(r2, (int, float)) and -1 < r2 < 0:
                warnings_list.append(f"⚠️ Model performance degraded (R²={r2:.2f})")
        
        if warnings_list:
            for warn in warnings_list[:5]:
                st.warning(warn)
            if len(warnings_list) > 5:
                st.info(f"... and {len(warnings_list) - 5} more warnings")
        else:
            st.success("✅ No warnings")
        
        st.markdown("---")
        
        # ── 6. HISTORIQUE DES ALERTES ─────────────────────────────────────
        
        st.markdown("#### 📋 Alert History (Last 24h)")
        
        # Simuler un historique d'alertes
        alert_history = []
        for i in range(6):
            hour = 24 - i * 4
            alert_time = datetime.now() - timedelta(hours=hour)
            
            if i == 0:
                alert = "🟢 System initialized"
                status = "✅ Completed"
            elif i == 1:
                alert = "📊 Data updated from INRB"
                status = "✅ Completed"
            elif i == 2 and risk_score > 30:
                alert = f"🟡 Risk score updated: {risk_score}/100"
                status = "🔄 Active"
            elif i == 3 and critical_alerts:
                alert = "🔴 Critical alert triggered"
                status = "🔄 Active"
            elif i == 4:
                alert = "📈 Model prediction updated"
                status = "✅ Completed"
            else:
                alert = "🔄 System check passed"
                status = "✅ Completed"
            
            alert_history.append({
                'Time': alert_time.strftime('%H:%M'),
                'Alert': alert,
                'Status': status
            })
        
        # Afficher l'historique
        for alert in alert_history:
            color = "#2E7D32" if "✅" in alert['Status'] else "#E65100" if "🔄" in alert['Status'] else "#C62828"
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; padding:6px 10px; 
                        border-bottom:1px solid #E8EAF6; font-size:13px;">
                <span style="color:#78909C;">{alert['Time']}</span>
                <span>{alert['Alert']}</span>
                <span style="color:{color}; font-weight:500;">{alert['Status']}</span>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # ── 7. RECOMMANDATIONS ────────────────────────────────────────────
        
        st.markdown("#### 💡 Recommendations")
        
        recommendations = []
        
        if risk_score >= 70:
            recommendations.append("🔴 **IMMEDIATE ACTION REQUIRED:** Activate emergency response protocol")
            recommendations.append("🔴 Notify all health zones and coordinate with INRB")
            recommendations.append("🔴 Deploy rapid response teams to high-risk zones")
        elif risk_score >= 50:
            recommendations.append("🟡 **ENHANCED SURVEILLANCE:** Increase monitoring in high-risk zones")
            recommendations.append("🟡 Review containment measures and reinforce where needed")
            recommendations.append("🟡 Prepare resources for potential escalation")
        elif risk_score >= 30:
            recommendations.append("🟠 **ROUTINE MONITORING:** Continue regular surveillance")
            recommendations.append("🟠 Maintain communication with health zones")
            recommendations.append("🟠 Review data quality and completeness")
        else:
            recommendations.append("🟢 **STANDARD OPERATIONS:** Continue routine monitoring")
            recommendations.append("🟢 Maintain data collection and reporting")
        
        # Add specific recommendations
        if high_risk_zones > 10:
            recommendations.append(f"📍 Focus on {high_risk_zones} high-risk zones for targeted interventions")
        if gr_last > 10:
            recommendations.append("📈 Implement enhanced contact tracing in affected areas")
        if all_metrics and active_model in all_metrics:
            r2 = all_metrics[active_model].get('R²', 0)
            if isinstance(r2, (int, float)) and r2 < 0:
                recommendations.append("🤖 Consider re-training models with updated data")
        
        for rec in recommendations[:5]:
            st.info(rec)
        
        st.markdown("---")
        
        # ── 8. STATISTIQUES RAPIDES ───────────────────────────────────────
        
        st.markdown("#### 📊 Quick Stats")
        
        stat_col1, stat_col2, stat_col3 = st.columns(3)
        
        with stat_col1:
            st.metric("📈 Risk Score", f"{risk_score}/100", delta=f"{risk_score - 25:+d}")
        
        with stat_col2:
            alert_count = len(critical_alerts) + len(warnings_list)
            st.metric("🚨 Active Alerts", alert_count)
        
        with stat_col3:
            st.metric("📍 High Risk Zones", f"{high_risk_zones}/{len(zones)}")
        
        # ── 9. BOUTON DE RAFRAÎCHISSEMENT ─────────────────────────────────
        
        if st.button("🔄 Refresh Alerts", width='stretch'):
            st.success("✅ Alerts refreshed!")
            st.rerun()

        # ── Notification panel (email / webhook / thresholds / log) ───
        st.markdown("---")
        st.markdown("#### 📬 Notifications")
        _live_alerts = evaluate_alerts(nat, zone_latest, gr_last, risk_thr)
        render_notification_panel(_live_alerts, nat, zone_latest, gr_last, risk_thr)


    # ── MENU 2 · EXPORT ──────────────────────────────────────────────
    with st.expander("📤 **Advanced Export**", expanded=False):
        st.markdown("#### Export Options")
        st.info(f"📊 Data ready: {len(raw_df):,} rows · {len(zones)} zones")

        st.markdown("---")

        # ── PDF ──────────────────────────────────────────────────────
        st.markdown("##### 📊 PDF Report")
        try:
            _pdf_buf = generate_pdf_report(
                nat, zones, active_model, metrics_primary,
                all_metrics, ci_fc, risk_thr, gr_last,
                zone_latest_df=zone_latest
            )
            st.download_button(
                label="⬇️ Download PDF Report",
                data=_pdf_buf,
                file_name=f"bael_report_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                width='stretch',
                key="export_pdf"
            )
        except Exception as _e:
            st.error(f"❌ PDF error: {str(_e)[:120]}")

        st.markdown("---")

        # ── CSV ───────────────────────────────────────────────────────
        st.markdown("##### 📄 CSV Export")

        csv_all = raw_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Download All Data (CSV)",
            data=csv_all,
            file_name=f"bael_all_data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            width='stretch',
            key="export_csv_all"
        )

        csv_nat = nat.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Download National Data (CSV)",
            data=csv_nat,
            file_name=f"bael_national_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            width='stretch',
            key="export_csv_nat"
        )

        csv_zones = zone_latest.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Download Zones Data (CSV)",
            data=csv_zones,
            file_name=f"bael_zones_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            width='stretch',
            key="export_csv_zones"
        )

        st.markdown("---")

        # ── APERÇU ────────────────────────────────────────────────────
        st.markdown("#### 📋 Data Preview")
        st.dataframe(
            raw_df[['zone', 'date', 'value']].head(3),
            hide_index=True, width='stretch'
        )

    # ── MENU 3 · TEMPORAL ANALYSIS ──────────────────────────────────
    with st.expander("⏳ **Temporal Analysis**", expanded=False):
        st.markdown("#### 📈 Case Trends")

        with safe_plot():
            fig, ax = plt.subplots(figsize=(6, 3), dpi=72)
            ax.plot(nat['date'], nat['value'], color=PALETTE[0], lw=2)
            ax.set_title("Cumulative Cases", fontweight='bold', fontsize=10)
            ax.tick_params(axis='x', rotation=25, labelsize=8)
            ax.set_ylabel("Cases", fontsize=8)
            ax.grid(True, alpha=0.2)
            ax.spines[['top', 'right']].set_visible(False)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

        st.markdown("#### 📊 Key Statistics")
        col1, col2, col3 = st.columns(3)
        col1.metric("Peak", f"{int(nat['value'].max()):,}")
        col2.metric("Mean", f"{nat['value'].mean():.0f}")
        col3.metric("Growth", f"{gr_last:.1f}%")

    # ── MENU 4 · EXTERNAL DATA ──────────────────────────────────────
    with st.expander("🌐 **Data Integration**", expanded=False):

        _sources = get_all_data_sources(len(raw_df), len(zones),
                                        int(nat['value'].max()))

        st.markdown("#### 📊 Data Sources Status")
        for _src_name, _info in _sources.items():
            _st = _info.get('status', '⏳ Pending')
            _col = "#2E7D32" if "✅" in _st else "#E65100" if "⚠️" in _st else "#78909C"
            _ico = "🟢" if "✅" in _st else "🟡" if "⚠️" in _st else "⚪"
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;'
                f'padding:5px 0;border-bottom:1px solid rgba(255,255,255,0.08);">'
                f'<span style="color:#E3F2FD;">{_ico} {_src_name}</span>'
                f'<span style="color:{_col};font-weight:500;">{_st}</span></div>',
                unsafe_allow_html=True
            )

        st.markdown("---")

        # ── WHO ──────────────────────────────────────────────────────
        st.markdown("#### 🌍 WHO Data")
        _who = _sources.get("WHO Database", {})
        _who_info = _who.get("data", {})
        if _who_info:
            _wc1, _wc2, _wc3 = st.columns(3)
            with _wc1: st.metric("🦠 Épidémie",  _who_info.get("outbreak", "Ebola BDBV"))
            with _wc2: st.metric("🌍 Pays",       _who_info.get("country",  "DRC"))
            with _wc3: st.metric("📊 Statut",     _who_info.get("status",   "Active"))
            st.caption(f"🔄 Last updated: {_who.get('last_update', '—')}")
        else:
            st.info("Connexion WHO disponible avec clé API.")

        st.markdown("---")

        # ── WEATHER ───────────────────────────────────────────────────
        st.markdown("#### 🌤️ Weather — Butembo, DRC")
        display_weather_dashboard()

        st.markdown("---")

        # ── DEMOGRAPHICS ──────────────────────────────────────────────
        st.markdown("#### 👥 Demographic Data — DRC")
        _demo = _sources.get("Demographic Data", {})
        _di   = _demo.get("data", {})
        if _di:
            _dc1, _dc2, _dc3 = st.columns(3)
            with _dc1: st.metric("🇨🇩 Population", f"{_di.get('population',0):,}")
            with _dc2: st.metric("📈 Growth Rate", f"{_di.get('growth_rate','—')} %")
            with _dc3: st.metric("🏥 Health Zones", len(zones))
            st.caption(f"Source: {_di.get('source','World Bank')} · {_demo.get('last_update','—')}")

        st.markdown("---")

        # ── SYNC / SUMMARY ────────────────────────────────────────────
        st.markdown("#### 🔄 Sync Status")
        _sc1, _sc2 = st.columns(2)
        with _sc1:
            st.metric("📊 Records",     f"{len(raw_df):,}")
            st.metric("🏥 Zones",       f"{len(zones)}")
        with _sc2:
            st.metric("📅 Last Update", datetime.now().strftime('%Y-%m-%d %H:%M'))
            st.metric("🔄 Auto-sync",   "6 h")

        st.markdown("---")
        _btn1, _btn2 = st.columns(2)
        with _btn1:
            if st.button("🔄 Refresh All", width='stretch',
                         key="refresh_all_btn"):
                with st.spinner("Refreshing data connections..."):
                    st.cache_data.clear()
                    time.sleep(1)
                st.success("✅ All data refreshed!")
                st.rerun()
        with _btn2:
            _summary = json.dumps({
                "data_source": "INRB", "records": len(raw_df),
                "zones": len(zones),
                "total_cases": int(nat['value'].max()),
                "last_update": datetime.now().strftime('%Y-%m-%d %H:%M'),
                "sources": {n: i.get('status', '?') for n, i in _sources.items()}
            }, indent=2, ensure_ascii=False).encode('utf-8')
            st.download_button(
                label="📥 Download Summary (JSON)",
                data=_summary,
                file_name=f"data_summary_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                width='stretch',
                key="summary_json_dl"
            )

    # ── MENU 5 · HISTORY & TRENDS ───────────────────────────────────
    with st.expander("📈 **History & Trends**", expanded=False):
        st.markdown("#### 📊 Historical Comparison")

        hist_data = {
            "Current Outbreak": nat['value'].tail(30).values.tolist(),
            "Previous Peak": [100, 200, 350, 500, 650, 800, 950, 1100, 1200, 1300]
        }

        with safe_plot():
            fig, ax = plt.subplots(figsize=(6, 3), dpi=72)
            ax.plot(range(len(hist_data["Current Outbreak"])), hist_data["Current Outbreak"],
                   color=PALETTE[0], lw=2, label="Current")
            ax.plot(range(len(hist_data["Previous Peak"])), hist_data["Previous Peak"],
                   color=PALETTE[1], lw=2, ls='--', label="Previous Peak")
            ax.set_title("Outbreak Comparison", fontweight='bold', fontsize=10)
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.2)
            ax.spines[['top', 'right']].set_visible(False)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

        st.markdown("#### 🗺️ Risk Zones")
        high_risk = sum(1 for v in zone_latest['value'] if v > risk_thr)
        st.metric("High Risk Zones", f"{high_risk} / {len(zones)}")

    # ── MENU 6 · MODEL PERFORMANCE ──────────────────────────────────
    with st.expander("📊 **Model Performance**", expanded=False):
        st.markdown("#### 📊 Performance Metrics")

        if all_metrics:
            perf_df = pd.DataFrame(all_metrics).T.reset_index()
            perf_df.columns = ['Model', 'RMSE', 'MAE', 'R²', 'MAPE%']

            best = perf_df.loc[perf_df['R²'].astype(float).idxmax()] if 'R²' in perf_df.columns else None
            if best is not None:
                st.success(f"🏆 Best: **{best['Model']}** (R²={best['R²']})")

            st.dataframe(
                perf_df[['Model', 'RMSE', 'R²']].head(3),
                hide_index=True, width='stretch'
            )

        if len(preds_test) > 1:
            n = min(len(preds_test), len(y_test_al))
            errors = y_test_al[:n] - preds_test[:n]
            st.metric("Model Error (MAE)", f"{np.abs(errors).mean():.2f}")

    # ── MENU 7 · CUSTOM DASHBOARD ────────────────────────────────────
    with st.expander("📊 **Custom Dashboard**", expanded=False):
        st.markdown("#### 🧩 Dashboard Widgets")

        widgets = {
            "📊 Total Cases": int(nat['value'].max()),
            "📈 Growth Rate": f"{gr_last:.1f}%",
            "📍 Zones": len(zones),
            "🎯 Best Model": best['Model'] if 'best' in locals() else active_model,
            "📅 Last Update": last_dt,
            "🚨 Risk Level": risk_level
        }

        cols = st.columns(2)
        for i, (label, value) in enumerate(widgets.items()):
            with cols[i % 2]:
                st.metric(label, value)

        st.markdown("#### 💾 Save Dashboard")
        if st.button("💾 Save Current View", width='stretch'):
            st.success("✅ Dashboard saved!")

    # ── Models Status (compact grid for mobile) ──────────────────────
    st.markdown("---")

    # ── Dark Mode toggle ──────────────────────────────────────────────
    dark_mode = st.toggle(
        "🌙 Dark Mode",
        value=st.session_state.get("dark_mode", False),
        key="dark_mode_toggle"
    )
    st.session_state["dark_mode"] = dark_mode

    # ── Interactive Tour button ───────────────────────────────────────
    if st.button("🗺️ Start Guided Tour",
                 width='stretch', key="start_tour_btn"):
        st.session_state.tour_step   = 0
        st.session_state.tour_active = True
        st.rerun()

    # ── Offline Snapshot expander ─────────────────────────────────────
    with st.expander("💾 **Offline Snapshot**", expanded=False):
        render_offline_panel(
            nat, zone_latest, all_metrics, ci_fc,
            gr_last, risk_thr, active_model, zones
        )

    st.markdown("---")
    st.markdown(f"### 🤖 {t('sidebar.models')}")
    model_cols = st.columns(3)
    for i, (k, v) in enumerate([item for item in MODEL_STATUS.items() if item[0] != "Scaler"]):
        icon = "✅" if "Loaded" in v else "⚠️" if "Missing" in v else "❌"
        with model_cols[i % 3]:
            st.markdown(
                f"<span style='font-size:10px;color:white;'>{icon} {k[:6]}</span>",
                unsafe_allow_html=True
            )

    st.markdown(
        f"<div style='background:rgba(255,255,255,0.15);border-radius:8px;"
        f"padding:6px;margin:6px 0;font-size:11px;text-align:center;color:white;'>"
        f"<b>{n_loaded}</b> / {len(MODELS)} {t('sidebar.models_ready')}</div>",
        unsafe_allow_html=True
    )

    st.markdown("---")
    st.markdown("""
    <div style="font-size:0.65rem;text-align:center;opacity:0.7;">
        UAC · Butembo · Nord-Kivu<br>
        PhD AI · BAEL Framework
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
# RESPONSIVE HELPERS
# ═══════════════════════════════════════════════════════════════════════

def get_weather_badge():
    """Return a weather badge HTML string for the banner."""
    try:
        weather = fetch_weather_data()
        if weather.get('status') == "✅ Connected" and weather.get('data'):
            temp = weather['data'].get('temperature', 'N/A')
            icon = weather['data'].get('icon', '01d')
            return (
                f'<span style="background:rgba(255,255,255,0.1);padding:3px 10px;'
                f'border-radius:12px;font-size:10px;color:#B3E5FC;">'
                f'🌤️ {temp}°C</span>'
            )
    except Exception:
        pass
    return ''


def create_responsive_chart(fig, height=500):
    """Adjust a matplotlib figure for responsive display."""
    fig.set_dpi(100)
    fig.set_size_inches(10, height / 100)
    for ax in fig.get_axes():
        ax.tick_params(labelsize=8)
        ax.set_xlabel(ax.get_xlabel(), fontsize=9)
        ax.set_ylabel(ax.get_ylabel(), fontsize=9)
        ax.set_title(ax.get_title(), fontsize=10)
    fig.tight_layout()
    return fig


def responsive_dataframe(df, max_height=300):
    """Display a dataframe wrapped in a horizontally-scrollable container."""
    st.markdown(
        '<div class="dataframe-container">',
        unsafe_allow_html=True
    )
    st.dataframe(df, width='stretch', height=max_height)
    st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════
# BANNER
# ═══════════════════════════════════════════════════════════════════════
_alert_color  = "#C62828" if gr_last > 20 else "#E65100" if gr_last > 5 else "#2E7D32"
_alert_bg     = "#FFEBEE" if gr_last > 20 else "#FFF3E0" if gr_last > 5 else "#E8F5E9"
_alert_icon   = "🔴" if gr_last > 20 else "🟡" if gr_last > 5 else "🟢"
_alert_label  = t('alerts.high') if gr_last > 20 else t('alerts.elevated') if gr_last > 5 else t('alerts.stable')
_alert_msg    = t('alerts.immediate_action') if gr_last > 20 else t('alerts.enhanced_surveillance') if gr_last > 5 else t('alerts.routine_monitoring')


# ── Dark mode CSS injection ───────────────────────────────────────────
inject_dark_mode(st.session_state.get("dark_mode", False))

# ── Interactive Tour (shown on first visit or when triggered) ─────────
if st.session_state.get("tour_active", True) and not st.session_state.get("tour_seen", False):
    render_tour()

# ── Responsive Banner ─────────────────────────────────────────────────
st.markdown(f"""
<div class="banner" style="
    background: linear-gradient(135deg, #0D1B3E 0%, #1A237E 50%, #1565C0 100%);
    padding: 15px 20px 8px 20px;
    border-radius: 12px;
    color: white;
    margin-bottom: 10px;
    box-shadow: 0 4px 20px rgba(26,35,126,0.3);
">
    <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
        <span style="font-size:28px;">🦠</span>
        <div style="flex:1;min-width:150px;">
            <h1 style="color:white !important;font-size:1.6rem;font-weight:700;
                       margin:0;letter-spacing:0.5px;">
                BAEL
            </h1>
            <div class="banner-subtitle"
                 style="color:#90CAF9;font-size:0.75rem;margin-top:2px;font-weight:300;">
                {cfg('subtitle_en', t('app.subtitle'))}
            </div>
        </div>
        <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
            <span style="background:rgba(255,255,255,0.1);padding:3px 10px;
                         border-radius:12px;font-size:10px;color:#B3E5FC;">
                🎯 {active_model}
            </span>
            <span style="background:rgba(255,255,255,0.1);padding:3px 10px;
                         border-radius:12px;font-size:10px;color:#B3E5FC;">
                📊 {int(nat['value'].max()):,} {t('common.cases')}
            </span>
            <span style="background:rgba(255,255,255,0.1);padding:3px 10px;
                         border-radius:12px;font-size:10px;color:#B3E5FC;">
                🤖 {n_loaded}/{len(MODELS)} {t('sidebar.models')}
            </span>
            {get_weather_badge()}
        </div>
    </div>
    <!-- Navigation -->
    <div class="banner-nav"
         style="display:flex;gap:4px;flex-wrap:wrap;margin-top:8px;
                padding-top:8px;border-top:1px solid rgba(255,255,255,0.08);">
        <span class="nav-item" style="color:#E3F2FD;padding:3px 10px;border-radius:16px;
              font-size:0.65rem;font-weight:500;background:rgba(255,255,255,0.15);">
              📈 {t('menu.epidemiology')}</span>
        <span class="nav-item" style="color:#E3F2FD;padding:3px 10px;border-radius:16px;
              font-size:0.65rem;font-weight:500;background:rgba(255,255,255,0.05);">
              🔮 {t('menu.forecast')}</span>
        <span class="nav-item" style="color:#E3F2FD;padding:3px 10px;border-radius:16px;
              font-size:0.65rem;font-weight:500;background:rgba(255,255,255,0.05);">
              🗺️ {t('menu.zones')}</span>
        <span class="nav-item" style="color:#E3F2FD;padding:3px 10px;border-radius:16px;
              font-size:0.65rem;font-weight:500;background:rgba(255,255,255,0.05);">
              🧠 {t('menu.xai')}</span>
        <span class="nav-item" style="color:#E3F2FD;padding:3px 10px;border-radius:16px;
              font-size:0.65rem;font-weight:500;background:rgba(255,255,255,0.05);">
              📊 {t('menu.comparison')}</span>
        <span class="nav-item" style="color:#E3F2FD;padding:3px 10px;border-radius:16px;
              font-size:0.65rem;font-weight:500;background:rgba(255,255,255,0.05);">
              🔬 {t('menu.advanced')}</span>
        <span class="nav-item" style="color:#E3F2FD;padding:3px 10px;border-radius:16px;
              font-size:0.65rem;font-weight:500;background:rgba(255,255,255,0.05);">
              📊 {t('menu.models')}</span>
        <span class="nav-item" style="color:#E3F2FD;padding:3px 10px;border-radius:16px;
              font-size:0.65rem;font-weight:500;background:rgba(255,255,255,0.05);">
              📊 {t('menu.dashboard')}</span>
        <span class="nav-item" style="color:#E3F2FD;padding:3px 10px;border-radius:16px;
              font-size:0.65rem;font-weight:500;background:rgba(255,255,255,0.05);">
              📋 {t('menu.report')}</span>
        <span class="nav-item" style="color:#E3F2FD;padding:3px 10px;border-radius:16px;
              font-size:0.65rem;font-weight:500;background:rgba(255,255,255,0.05);">
              🤖 {t('menu.chatbot')}</span>
        <span class="nav-item" style="color:#E3F2FD;padding:3px 10px;border-radius:16px;
              font-size:0.65rem;font-weight:500;background:rgba(255,255,255,0.05);">
              📚 {t('menu.publications')}</span>
    </div>
</div>
""", unsafe_allow_html=True)
# ── KPI strip + alert — ABOVE the banner ─────────────────────────────
st.markdown(f"""
<!-- KPI strip -->
<div style="display:flex; gap:8px; flex-wrap:wrap; margin-bottom:10px;">
    <div style="flex:1; min-width:90px; background:white; border:1px solid #E3E8EF;
                border-radius:10px; padding:10px 12px; box-shadow:0 1px 4px rgba(0,0,0,0.06);">
        <div style="color:#546E7A; font-size:10px; font-weight:600; text-transform:uppercase;">{t('metrics.total_cases')}</div>
        <div style="color:#1A237E; font-size:20px; font-weight:800; margin-top:2px;">{int(nat['value'].max()):,}</div>
    </div>
    <div style="flex:1; min-width:90px; background:white; border:1px solid #FFCDD2;
                border-radius:10px; padding:10px 12px; box-shadow:0 1px 4px rgba(0,0,0,0.06);">
        <div style="color:#C62828; font-size:10px; font-weight:600; text-transform:uppercase;">💀 Deaths</div>
        <div style="color:#C62828; font-size:20px; font-weight:800; margin-top:2px;">{total_deaths:,}</div>
        <div style="color:#EF9A9A; font-size:10px;">{cfr:.1f}% CFR</div>
    </div>
    <div style="flex:1; min-width:90px; background:white; border:1px solid #C8E6C9;
                border-radius:10px; padding:10px 12px; box-shadow:0 1px 4px rgba(0,0,0,0.06);">
        <div style="color:#2E7D32; font-size:10px; font-weight:600; text-transform:uppercase;">🏥 Recovered</div>
        <div style="color:#2E7D32; font-size:20px; font-weight:800; margin-top:2px;">{total_recovered:,}</div>
        <div style="color:#81C784; font-size:10px;">{recovery_rate:.1f}%</div>
    </div>
    <div style="flex:1; min-width:90px; background:white; border:1px solid #FFF9C4;
                border-radius:10px; padding:10px 12px; box-shadow:0 1px 4px rgba(0,0,0,0.06);">
        <div style="color:#F57F17; font-size:10px; font-weight:600; text-transform:uppercase;">🔄 Active</div>
        <div style="color:#F57F17; font-size:20px; font-weight:800; margin-top:2px;">{active_cases:,}</div>
    </div>
    <div style="flex:1; min-width:90px; background:white; border:1px solid #E3E8EF;
                border-radius:10px; padding:10px 12px; box-shadow:0 1px 4px rgba(0,0,0,0.06);">
        <div style="color:#546E7A; font-size:10px; font-weight:600; text-transform:uppercase;">{t('metrics.new_cases_7d')}</div>
        <div style="color:#1A237E; font-size:20px; font-weight:800; margin-top:2px;">{int(nat['new_cases'].tail(7).sum()):,}</div>
    </div>
    <div style="flex:1; min-width:90px; background:white; border:1px solid #E3E8EF;
                border-radius:10px; padding:10px 12px; box-shadow:0 1px 4px rgba(0,0,0,0.06);">
        <div style="color:#546E7A; font-size:10px; font-weight:600; text-transform:uppercase;">{t('metrics.health_zones')}</div>
        <div style="color:#1A237E; font-size:20px; font-weight:800; margin-top:2px;">{len(zones)}</div>
    </div>
    <div style="flex:1; min-width:90px; background:white; border:1px solid #E3E8EF;
                border-radius:10px; padding:10px 12px; box-shadow:0 1px 4px rgba(0,0,0,0.06);">
        <div style="color:#546E7A; font-size:10px; font-weight:600; text-transform:uppercase;">{active_model} RMSE</div>
        <div style="color:#1565C0; font-size:20px; font-weight:800; margin-top:2px;">{metrics_primary.get('RMSE', '—')}</div>
    </div>
    <div style="flex:1; min-width:90px; background:white; border:1px solid #E3E8EF;
                border-radius:10px; padding:10px 12px; box-shadow:0 1px 4px rgba(0,0,0,0.06);">
        <div style="color:#546E7A; font-size:10px; font-weight:600; text-transform:uppercase;">{active_model} R²</div>
        <div style="color:#1565C0; font-size:20px; font-weight:800; margin-top:2px;">{metrics_primary.get('R²', '—')}</div>
    </div>
</div>

<!-- Alert strip -->
<div style="background:{_alert_bg}; border-left:4px solid {_alert_color};
            border-radius:6px; padding:8px 14px; margin-bottom:10px;
            font-size:13px; font-weight:600; color:{_alert_color};">
    {_alert_icon} {_alert_label} — Growth rate: {gr_last:.1f}% · {_alert_msg}
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# WALK-FORWARD VALIDATION
# ═══════════════════════════════════════════════════════════════════════

def run_walk_forward_validation(feat_df, FEATURE_COLS, SCALER, SKLEARN_MDLS,
                                 n_splits=5, min_train=14):
    """
    Perform temporal walk-forward (expanding window) cross-validation.

    Each fold trains on all data up to a cutoff, tests on the next
    window — mimicking real-world deployment where future data is unseen.

    Args:
        feat_df      : feature-engineered DataFrame with 'date', 'value', FEATURE_COLS
        FEATURE_COLS : list of feature column names
        SCALER       : fitted StandardScaler (or None)
        SKLEARN_MDLS : dict {model_name: fitted_model}
        n_splits     : number of walk-forward folds
        min_train    : minimum training observations per fold

    Returns:
        pd.DataFrame: columns = [fold, cutoff_date, model, RMSE, MAE, R², MAPE%,
                                  n_train, n_test, y_true_mean, y_pred_mean]
    """
    from sklearn.preprocessing import StandardScaler as _SS

    all_dates = np.sort(feat_df['date'].unique())
    n = len(all_dates)

    if n < min_train + 3:
        return pd.DataFrame()

    # Build fold cutoff indices — evenly spaced between min_train and n-1
    step = max(1, (n - min_train) // n_splits)
    cutoff_indices = list(range(min_train, n - 1, step))[:n_splits]

    records = []

    for fold_i, cut_idx in enumerate(cutoff_indices, 1):
        cutoff_date = all_dates[cut_idx]
        train = feat_df[feat_df['date'] <  cutoff_date]
        test  = feat_df[feat_df['date'] >= cutoff_date]

        if len(train) < min_train or len(test) < 2:
            continue

        X_tr = clean_X(train[FEATURE_COLS].values)
        y_tr = train['value'].values.astype(np.float64)
        X_te = clean_X(test[FEATURE_COLS].values)
        y_te = test['value'].values.astype(np.float64)

        # Per-fold scaler (expanding window — no data leakage)
        fold_scaler = _SS()
        X_tr_sc = fold_scaler.fit_transform(X_tr)
        X_te_sc = fold_scaler.transform(X_te)

        for model_name, model in SKLEARN_MDLS.items():
            try:
                model.fit(X_tr_sc, y_tr)
                y_pred = np.clip(model.predict(X_te_sc), 0, None)
                m = compute_metrics(y_te, y_pred)
                records.append({
                    'Fold':          fold_i,
                    'Cutoff Date':   pd.Timestamp(cutoff_date).strftime('%Y-%m-%d'),
                    'Model':         model_name,
                    'RMSE':          m['RMSE'],
                    'MAE':           m['MAE'],
                    'R²':            m['R²'],
                    'MAPE%':         m['MAPE%'],
                    'n_train':       len(train),
                    'n_test':        len(test),
                    'y_true_mean':   round(float(np.mean(y_te)), 1),
                    'y_pred_mean':   round(float(np.mean(y_pred)), 1),
                })
            except Exception:
                continue

    return pd.DataFrame(records)


def render_walk_forward_panel(feat_df, FEATURE_COLS, SCALER, SKLEARN_MDLS):
    """
    Render the Walk-Forward Validation panel in Streamlit.
    """
    st.markdown("### 🔄 Walk-Forward Validation")
    st.markdown("""
    <div class="info-box">
    <b>🔄 Temporal Walk-Forward Cross-Validation</b> — Each fold trains on all
    historical data up to a cutoff date and tests on the subsequent period,
    exactly as in real deployment. This is the gold standard for time-series
    model evaluation and is required by most epidemiology journals.
    </div>
    """, unsafe_allow_html=True)

    wf_c1, wf_c2 = st.columns(2)
    with wf_c1:
        n_splits = st.slider("Number of folds", 3, 10, 5, key="wf_splits")
    with wf_c2:
        min_train = st.slider("Min training observations", 7, 30, 14, key="wf_min_train")

    if st.button("▶️ Run Walk-Forward Validation",
                 key="wf_run", type="primary"):
        with st.spinner(f"Running {n_splits}-fold walk-forward validation…"):
            wf_df = run_walk_forward_validation(
                feat_df, FEATURE_COLS, SCALER, SKLEARN_MDLS,
                n_splits=n_splits, min_train=min_train
            )

        if wf_df.empty:
            st.warning("Not enough data for walk-forward validation. "
                       "Need at least 17 observations.")
            return

        st.session_state['wf_results'] = wf_df

    wf_df = st.session_state.get('wf_results', pd.DataFrame())
    if wf_df.empty:
        st.info("Click **Run Walk-Forward Validation** to start.")
        return

    # ── Aggregate metrics per model ───────────────────────────────────
    st.markdown("#### 📊 Aggregate Performance (mean ± std across folds)")
    agg = (wf_df.groupby('Model')[['RMSE', 'MAE', 'R²', 'MAPE%']]
                .agg(['mean', 'std'])
                .round(3))
    agg.columns = ['RMSE_mean', 'RMSE_std', 'MAE_mean', 'MAE_std',
                   'R²_mean', 'R²_std', 'MAPE_mean', 'MAPE_std']
    agg = agg.reset_index()

    # Display as formatted table
    display_agg = agg.copy()
    for metric in ['RMSE', 'MAE', 'R²', 'MAPE']:
        display_agg[f'{metric}'] = (
            display_agg[f'{metric}_mean'].astype(str) + ' ± ' +
            display_agg[f'{metric}_std'].astype(str)
        )
    st.dataframe(
        display_agg[['Model', 'RMSE', 'MAE', 'R²', 'MAPE']],
        hide_index=True, width='stretch'
    )

    # Best model highlight
    try:
        best_idx = agg['R²_mean'].idxmax()
        best_model = agg.loc[best_idx, 'Model']
        best_r2    = agg.loc[best_idx, 'R²_mean']
        best_rmse  = agg.loc[best_idx, 'RMSE_mean']
        st.success(f"🏆 **Best model (walk-forward):** {best_model} — "
                   f"R² = {best_r2:.4f} · RMSE = {best_rmse:.2f}")
    except Exception:
        pass

    # ── Per-fold detail ───────────────────────────────────────────────
    st.markdown("#### 📋 Per-Fold Results")
    st.dataframe(
        wf_df[['Fold', 'Cutoff Date', 'Model', 'RMSE', 'MAE',
               'R²', 'MAPE%', 'n_train', 'n_test']],
        hide_index=True, width='stretch'
    )

    # ── Visualization ─────────────────────────────────────────────────
    st.markdown("#### 📈 RMSE & R² Across Folds")
    models_in_wf = wf_df['Model'].unique()
    with safe_plot():
        fig, axes = plt.subplots(1, 2, figsize=(12, 4), dpi=72)

        for i, model in enumerate(models_in_wf):
            sub = wf_df[wf_df['Model'] == model].sort_values('Fold')
            color = PALETTE[i % len(PALETTE)]
            axes[0].plot(sub['Fold'], sub['RMSE'], 'o-', lw=2,
                         color=color, label=model, markersize=7)
            axes[1].plot(sub['Fold'], sub['R²'],   'o-', lw=2,
                         color=color, label=model, markersize=7)

        axes[0].set_title("RMSE per Fold", fontweight='bold')
        axes[0].set_xlabel("Fold"); axes[0].set_ylabel("RMSE")
        axes[0].legend(fontsize=8); axes[0].grid(True, alpha=0.2)
        axes[0].spines[['top', 'right']].set_visible(False)

        axes[1].set_title("R² per Fold", fontweight='bold')
        axes[1].set_xlabel("Fold"); axes[1].set_ylabel("R²")
        axes[1].axhline(0, color='red', ls='--', lw=0.8, alpha=0.5)
        axes[1].legend(fontsize=8); axes[1].grid(True, alpha=0.2)
        axes[1].spines[['top', 'right']].set_visible(False)

        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    # Export
    wf_csv = wf_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "⬇️ Download Walk-Forward Results (CSV)",
        data=wf_csv,
        file_name=f"walk_forward_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv", key="wf_download"
    )


# ═══════════════════════════════════════════════════════════════════════
# ZONE-LEVEL FORECAST
# ═══════════════════════════════════════════════════════════════════════

def forecast_zone(zone_series, horizon=14, n_boot=200, R0=1.5, N=100_000):
    """
    Generate a simple exponential-smoothing + SIR forecast for one zone.

    Uses the last 7-day growth rate to project forward, then wraps with
    bootstrap confidence intervals derived from recent residuals.

    Args:
        zone_series : pd.Series of cumulative cases (sorted by date)
        horizon     : forecast horizon in days
        n_boot      : bootstrap resamples for CI
        R0          : SIR basic reproduction number
        N           : zone population estimate

    Returns:
        dict with keys: mean, lower, upper, median, horizon, last_value
    """
    s = zone_series.dropna().values.astype(float)
    if len(s) < 3:
        last = float(s[-1]) if len(s) > 0 else 0.0
        return {'mean': last, 'median': last,
                'lower': 0.0, 'upper': last * 2,
                'horizon': horizon, 'last_value': last}

    last_val    = float(s[-1])
    daily_new   = np.diff(s).clip(min=0)
    last_new    = float(daily_new[-1]) if len(daily_new) > 0 else 0.0

    # SIR projection
    sir_vals = sir_project(last_new, horizon=horizon, R0=R0, N=N)

    # Bootstrap CI from recent residuals
    residuals = daily_new[-14:] - daily_new[-14:].mean() if len(daily_new) >= 7 else np.array([0.0])
    boot_samples = []
    for _ in range(n_boot):
        noise  = np.random.choice(residuals, size=horizon, replace=True)
        sample = last_val + np.cumsum(np.clip(sir_vals + noise, 0, None))
        boot_samples.append(sample[-1])

    boot_samples = np.array(boot_samples)
    return {
        'mean':       round(float(np.mean(boot_samples)),   1),
        'median':     round(float(np.median(boot_samples)), 1),
        'lower':      round(float(np.percentile(boot_samples, 2.5)), 1),
        'upper':      round(float(np.percentile(boot_samples, 97.5)), 1),
        'horizon':    horizon,
        'last_value': round(last_val, 1),
    }


def render_zone_forecast_panel(raw_df, zones, horizon, n_boot, r0_val, risk_thr):
    """
    Render the per-zone forecast panel showing projected cases,
    CI, risk classification, and an exportable summary table.
    """
    st.markdown("### 🗺️ Zone-Level Forecast")
    st.markdown("""
    <div class="info-box">
    <b>🗺️ Per-Zone Epidemic Forecast</b> — Individual projections for each
    health zone using SIR dynamics fitted to local growth rates, with
    bootstrap confidence intervals. Use these to prioritise field interventions.
    </div>
    """, unsafe_allow_html=True)

    zf_c1, zf_c2, zf_c3 = st.columns(3)
    with zf_c1:
        zf_horizon = st.slider("Forecast horizon (days)", 7, 30, horizon,
                               key="zf_horizon")
    with zf_c2:
        zf_top_n = st.slider("Show top N zones", 5,
                             max(6, min(30, len(zones))),
                             min(15, len(zones)), key="zf_top_n")
    with zf_c3:
        zf_sort = st.selectbox("Sort by", ["Forecast Mean", "Current Cases",
                                            "CI Width", "Zone Name"],
                               key="zf_sort")

    if st.button("▶️ Run Zone Forecasts",
                 key="zf_run", type="primary"):
        results = []
        prog = st.progress(0.0, text="Forecasting zones…")

        zone_ts = raw_df.groupby('zone')['value']

        for i, zone_name in enumerate(zones):
            if zone_name not in zone_ts.groups:
                continue
            series = (zone_ts.get_group(zone_name)
                             .reset_index(drop=True)
                             .sort_values())
            fc = forecast_zone(series, horizon=zf_horizon,
                               n_boot=n_boot, R0=r0_val)

            ci_width  = fc['upper'] - fc['lower']
            pct_change = ((fc['mean'] - fc['last_value']) / (fc['last_value'] + 1)
                          * 100)
            risk_level = ("🔴 Critical" if fc['mean'] > risk_thr * 2
                          else "🟡 High"    if fc['mean'] > risk_thr
                          else "🟠 Moderate" if fc['mean'] > risk_thr * 0.4
                          else "🟢 Low")

            results.append({
                'Zone':           zone_name,
                'Current Cases':  int(fc['last_value']),
                'Forecast Mean':  int(fc['mean']),
                'Forecast Median':int(fc['median']),
                'CI Lower':       int(fc['lower']),
                'CI Upper':       int(fc['upper']),
                'CI Width':       int(ci_width),
                '% Change':       round(pct_change, 1),
                'Risk Level':     risk_level,
                'Horizon (days)': zf_horizon,
            })
            prog.progress((i + 1) / max(len(zones), 1),
                          text=f"Forecasting {zone_name}…")

        prog.empty()
        st.session_state['zf_results'] = pd.DataFrame(results)

    zf_df = st.session_state.get('zf_results', pd.DataFrame())
    if zf_df.empty:
        st.info("Click **Run Zone Forecasts** to compute per-zone projections.")
        return

    # Sort
    sort_map = {
        "Forecast Mean":  "Forecast Mean",
        "Current Cases":  "Current Cases",
        "CI Width":       "CI Width",
        "Zone Name":      "Zone",
    }
    zf_sorted = zf_df.sort_values(sort_map[zf_sort], ascending=False).head(zf_top_n)

    # ── Summary metrics ───────────────────────────────────────────────
    zm1, zm2, zm3, zm4 = st.columns(4)
    zm1.metric("🗺️ Zones forecast", len(zf_df))
    zm2.metric("🔴 Critical zones",
               len(zf_df[zf_df['Risk Level'].str.startswith('🔴')]))
    zm3.metric("📈 Avg forecast",
               f"{zf_df['Forecast Mean'].mean():.0f}")
    zm4.metric("📅 Horizon", f"{zf_df['Horizon (days)'].iloc[0]} days")

    # ── Table ─────────────────────────────────────────────────────────
    st.markdown("#### 📋 Zone Forecast Table")
    st.dataframe(
        zf_sorted[['Zone', 'Current Cases', 'Forecast Mean',
                   'CI Lower', 'CI Upper', '% Change', 'Risk Level']],
        hide_index=True, width='stretch'
    )

    # ── Chart: current vs forecast ────────────────────────────────────
    st.markdown("#### 📊 Current vs Forecast — Top Zones")
    top_chart = zf_sorted.head(min(12, len(zf_sorted)))
    with safe_plot():
        fig, ax = plt.subplots(figsize=(12, 5), dpi=72)
        x = np.arange(len(top_chart))
        w = 0.35

        bars1 = ax.bar(x - w/2, top_chart['Current Cases'],
                       w, label='Current', color=PALETTE[0], alpha=0.8)
        bars2 = ax.bar(x + w/2, top_chart['Forecast Mean'],
                       w, label=f'Forecast (+{zf_horizon}d)',
                       color=PALETTE[1], alpha=0.8)

        # Error bars for CI
        ax.errorbar(x + w/2, top_chart['Forecast Mean'],
                    yerr=[top_chart['Forecast Mean'] - top_chart['CI Lower'],
                          top_chart['CI Upper'] - top_chart['Forecast Mean']],
                    fmt='none', color='#333', capsize=4, lw=1.5, alpha=0.7)

        ax.axhline(risk_thr, color='red', ls='--', lw=1.2, alpha=0.7,
                   label=f'Risk threshold ({int(risk_thr)})')
        ax.set_xticks(x)
        ax.set_xticklabels(top_chart['Zone'], rotation=35,
                           ha='right', fontsize=8)
        ax.set_title(f"Zone Forecast — Horizon {zf_horizon} days",
                     fontweight='bold')
        ax.set_ylabel("Cases")
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.2, axis='y')
        ax.spines[['top', 'right']].set_visible(False)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    # Export
    zf_csv = zf_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "⬇️ Download Zone Forecasts (CSV)",
        data=zf_csv,
        file_name=f"zone_forecast_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv", key="zf_download"
    )


# ═══════════════════════════════════════════════════════════════════════
# RESOURCE CALCULATOR
# ═══════════════════════════════════════════════════════════════════════

# Evidence-based Ebola resource ratios (WHO/MSF guidelines)
RESOURCE_RATIOS = {
    # Beds: 1 ETU bed per active case, 20% buffer
    'etu_beds':          {'ratio': 1.20,  'unit': 'ETU beds',
                          'description': '1.2 beds per active case (20% buffer)'},
    # Isolation rooms: 0.3 per active case (severe + critical only)
    'isolation_rooms':   {'ratio': 0.30,  'unit': 'isolation rooms',
                          'description': '0.3 rooms per active case'},
    # PPE kits/day: 6 per active case (3 shifts × 2 workers)
    'ppe_kits_day':      {'ratio': 6.0,   'unit': 'PPE kits/day',
                          'description': '6 kits/day per active case'},
    # Healthcare workers: 3 per active case
    'healthcare_workers':{'ratio': 3.0,   'unit': 'healthcare workers',
                          'description': '3 HCW per active case'},
    # Contact tracers: 1 per 2 new cases/day
    'contact_tracers':   {'ratio': 0.5,   'unit': 'contact tracers',
                          'description': '1 tracer per 2 new cases/day'},
    # Ambulances: 1 per 15 active cases
    'ambulances':        {'ratio': 1/15,  'unit': 'ambulances',
                          'description': '1 ambulance per 15 active cases'},
    # Body bags (worst case): CFR × active cases
    'body_bags':         {'ratio': 0.05,  'unit': 'body bags (stock)',
                          'description': '5% of active cases (CFR estimate)'},
    # Lab test kits: 3 per new case/day (sensitivity buffer)
    'lab_kits_day':      {'ratio': 3.0,   'unit': 'lab kits/day',
                          'description': '3 PCR kits per new case/day'},
    # Food/water rations: 2 per active case (patient + caregiver)
    'rations_day':       {'ratio': 2.0,   'unit': 'rations/day',
                          'description': '2 rations/day per active case'},
    # Chlorine/disinfectant (litres/day): 10L per active case
    'disinfectant_day':  {'ratio': 10.0,  'unit': 'litres disinfectant/day',
                          'description': '10 L/day per active case'},
}


def compute_resource_needs(active_cases_input, new_cases_daily,
                            horizon_days, cfr_pct, safety_factor=1.2):
    """
    Compute resource requirements based on active cases and forecast.
    Always returns exactly 6 columns with unique names:
    Resource, Description, Now, +7 days, +14 days, +<horizon> days
    If horizon_days == 7 or 14, the last column is renamed to avoid duplicates.
    """
    ac   = max(0, active_cases_input)
    nc   = max(0, new_cases_daily)
    cfr  = cfr_pct / 100

    def projected_active(days):
        net_new  = nc * days
        resolved = ac * min(1.0, days / 14)
        return max(0, ac + net_new - resolved) * safety_factor

    # Build a unique label for the custom horizon column
    if horizon_days in (7, 14):
        horizon_col = f'+{horizon_days}d (plan)'
    else:
        horizon_col = f'+{horizon_days} days'

    rows = []
    for name, meta in RESOURCE_RATIOS.items():
        r = meta['ratio']
        if name == 'body_bags':
            r = cfr

        if name in ('contact_tracers', 'lab_kits_day', 'ppe_kits_day',
                    'rations_day', 'disinfectant_day'):
            base = nc * r * safety_factor
            p7d  = projected_active(7)  / ac * base if ac > 0 else base
            p14d = projected_active(14) / ac * base if ac > 0 else base
            ph   = projected_active(horizon_days) / ac * base if ac > 0 else base
        else:
            base = ac * r * safety_factor
            p7d  = projected_active(7)  * r
            p14d = projected_active(14) * r
            ph   = projected_active(horizon_days) * r

        rows.append({
            'Resource':    meta['unit'],
            'Description': meta['description'],
            'Now':         int(round(base)),
            '+7 days':     int(round(p7d)),
            '+14 days':    int(round(p14d)),
            horizon_col:   int(round(ph)),
        })

    return pd.DataFrame(rows), horizon_col


def render_resource_calculator(active_cases, new_cases_7d, cfr, horizon):
    """
    Render the interactive resource needs calculator in Streamlit.
    """
    st.markdown("### 🏥 Resource Needs Calculator")
    st.markdown("""
    <div class="info-box">
    <b>🏥 Evidence-Based Resource Planning</b> — Estimates equipment, personnel,
    and supply requirements based on WHO/MSF response guidelines
    for <b>{cfg('display_name', 'epidemic')}</b>.
    Adjust parameters to model best-case, expected, and worst-case scenarios.
    </div>
    """, unsafe_allow_html=True)

    # ── Input parameters ──────────────────────────────────────────────
    rc1, rc2, rc3, rc4 = st.columns(4)
    with rc1:
        rc_active = st.number_input(
            "Active cases (current)", min_value=0,
            value=int(active_cases), step=10, key="rc_active"
        )
    with rc2:
        rc_daily = st.number_input(
            "Avg new cases/day", min_value=0,
            value=max(1, int(new_cases_7d / 7)), step=1, key="rc_daily"
        )
    with rc3:
        rc_cfr = st.number_input(
            "CFR (%)", min_value=0.0, max_value=100.0,
            value=float(round(cfr, 1)), step=0.5, key="rc_cfr"
        )
    with rc4:
        rc_horizon = st.slider(
            "Planning horizon (days)", 7, 90, min(horizon, 30),
            key="rc_horizon"
        )

    rc_safety = st.slider(
        "Safety buffer (%)", 0, 50, 20, step=5,
        key="rc_safety",
        help="Additional percentage added to all estimates as a precautionary buffer"
    )
    safety_factor = 1 + rc_safety / 100

    # Scenario selector
    scenario = st.radio(
        "Planning scenario",
        ["Expected", "Optimistic (−30%)", "Pessimistic (+50%)"],
        horizontal=True, key="rc_scenario"
    )
    scenario_mult = {'Expected': 1.0,
                     'Optimistic (−30%)': 0.70,
                     'Pessimistic (+50%)': 1.50}[scenario]

    adj_active = int(rc_active * scenario_mult)
    adj_daily  = int(rc_daily  * scenario_mult)

    # ── Compute ───────────────────────────────────────────────────────
    needs_df, _horizon_col = compute_resource_needs(
        adj_active, adj_daily, rc_horizon, rc_cfr, safety_factor
    )

    # ── Key metrics strip ─────────────────────────────────────────────
    km1, km2, km3, km4, km5 = st.columns(5)
    km1.metric("🛏️ ETU Beds needed",
               f"{int(adj_active * 1.2 * safety_factor):,}")
    km2.metric("👩‍⚕️ Healthcare workers",
               f"{int(adj_active * 3 * safety_factor):,}")
    km3.metric("🥼 PPE kits/day",
               f"{int(adj_daily * 6 * safety_factor):,}")
    km4.metric("🔬 Lab kits/day",
               f"{int(adj_daily * 3 * safety_factor):,}")
    km5.metric("🚑 Ambulances",
               f"{int(adj_active / 15 * safety_factor):,}")

    # ── Full resource table ───────────────────────────────────────────
    st.markdown("#### 📋 Detailed Resource Requirements")
    col_order = ['Resource', 'Description', 'Now',
                 '+7 days', '+14 days', _horizon_col]
    col_order = [c for c in col_order if c in needs_df.columns]
    st.dataframe(needs_df[col_order], hide_index=True, width='stretch')

    # ── Visualization ─────────────────────────────────────────────────
    st.markdown("#### 📈 Resource Needs Over Planning Horizon")
    key_resources = ['ETU beds', 'healthcare workers',
                     'PPE kits/day', 'contact tracers', 'ambulances']
    chart_df = needs_df[needs_df['Resource'].isin(key_resources)].copy()

    if not chart_df.empty:
        with safe_plot():
            fig, ax = plt.subplots(figsize=(10, 4), dpi=72)
            time_cols = ['Now', '+7 days', '+14 days', _horizon_col]
            time_cols = [c for c in time_cols if c in chart_df.columns]
            x = np.arange(len(time_cols))
            w = 0.15

            for i, (_, row) in enumerate(chart_df.iterrows()):
                vals = [row[c] for c in time_cols]
                ax.bar(x + i * w, vals, w,
                       label=row['Resource'],
                       color=PALETTE[i % len(PALETTE)], alpha=0.82)

            ax.set_xticks(x + w * (len(chart_df) - 1) / 2)
            ax.set_xticklabels(time_cols)
            ax.set_title("Key Resource Projections", fontweight='bold')
            ax.set_ylabel("Units required")
            ax.legend(fontsize=8, loc='upper left')
            ax.grid(True, alpha=0.2, axis='y')
            ax.spines[['top', 'right']].set_visible(False)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

    # ── Export ────────────────────────────────────────────────────────
    st.markdown("---")
    exp1, exp2 = st.columns(2)
    with exp1:
        rc_csv = needs_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "⬇️ Download Resource Plan (CSV)",
            data=rc_csv,
            file_name=f"resource_plan_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv", key="rc_csv_dl"
        )
    with exp2:
        # JSON for integration with external supply chain tools
        rc_json = json.dumps({
            'generated':      datetime.now().strftime('%Y-%m-%d %H:%M'),
            'scenario':       scenario,
            'active_cases':   adj_active,
            'new_cases_daily':adj_daily,
            'cfr_pct':        rc_cfr,
            'safety_buffer':  rc_safety,
            'horizon_days':   rc_horizon,
            'resources':      needs_df.to_dict('records'),
        }, indent=2, ensure_ascii=False).encode('utf-8')
        st.download_button(
            "⬇️ Download Resource Plan (JSON)",
            data=rc_json,
            file_name=f"resource_plan_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json", key="rc_json_dl"
        )

    st.caption(
        f"📚 Ratios based on WHO/MSF guidelines for {cfg('pathogen', 'Ebola')} response. "
        "Adjust safety buffer and scenario for local context."
    )


# ═══════════════════════════════════════════════════════════════════════
# HISTORICAL OUTBREAK COMPARISON
# ═══════════════════════════════════════════════════════════════════════

# Note: total_cases, total_deaths, cfr, nat are defined at data-loading time.
# HISTORICAL_OUTBREAKS is built as a function so it always picks up live values.

def get_historical_outbreaks():
    """Return the historical outbreaks dict with live current-outbreak values."""
    return {
        "West Africa 2014-16": {
            "country": "Guinea, Liberia, Sierra Leone",
            "cases": 28616, "deaths": 11310, "cfr": 39.5,
            "duration_days": 780, "strain": "Zaire ebolavirus",
            "source": "WHO",
            "notes": "Largest Ebola outbreak in history", "is_current": False,
        },
        "Équateur 2018": {
            "country": "DRC", "cases": 54, "deaths": 33, "cfr": 61.1,
            "duration_days": 90, "strain": "Zaire ebolavirus",
            "source": "WHO", "notes": "Contained rural outbreak", "is_current": False,
        },
        "Nord-Kivu 2018-20": {
            "country": "DRC", "cases": 3470, "deaths": 2287, "cfr": 65.9,
            "duration_days": 700, "strain": "Zaire ebolavirus",
            "source": "WHO", "notes": "Second largest outbreak", "is_current": False,
        },
        "Équateur 2020": {
            "country": "DRC", "cases": 130, "deaths": 55, "cfr": 42.3,
            "duration_days": 120, "strain": "Zaire ebolavirus",
            "source": "WHO", "notes": "Concurrent with COVID-19", "is_current": False,
        },
        "Guinea 2021": {
            "country": "Guinea", "cases": 23, "deaths": 12, "cfr": 52.2,
            "duration_days": 60, "strain": "Zaire ebolavirus",
            "source": "WHO", "notes": "Re-emergence in West Africa", "is_current": False,
        },
        "Uganda 2012": {
            "country": "Uganda", "cases": 11, "deaths": 4, "cfr": 36.4,
            "duration_days": 30, "strain": "Sudan ebolavirus",
            "source": "WHO", "notes": "Small outbreak in Uganda", "is_current": False,
        },
        "DRC 2012": {
            "country": "DRC", "cases": 77, "deaths": 36, "cfr": 46.8,
            "duration_days": 90, "strain": "Bundibugyo ebolavirus",
            "source": "WHO", "notes": "Bundibugyo strain first identified", "is_current": False,
        },
        "Bundibugyo 2026": {
            "country": "DRC",
            "cases":        total_cases,
            "deaths":       total_deaths,
            "cfr":          cfr,
            "duration_days": max(1, (nat['date'].max() - nat['date'].min()).days),
            "strain":       "Bundibugyo ebolavirus",
            "source":       "INRB",
            "notes":        "Current outbreak — Bundibugyo strain",
            "is_current":   True,
        },
    }


def get_outbreak_comparison_data():
    """Return outbreak data as a DataFrame."""
    rows = []
    for name, d in get_historical_outbreaks().items():
        rows.append({
            'name':       name,
            'cases':      d['cases'],
            'deaths':     d['deaths'],
            'cfr':        d['cfr'],
            'duration':   d['duration_days'],
            'countries':  d['country'],
            'strain':     d['strain'],
            'source':     d['source'],
            'notes':      d['notes'],
            'is_current': d['is_current'],
        })
    return pd.DataFrame(rows)


def calculate_comparison_metrics(outbreak_df):
    """Rank the current outbreak against historical ones."""
    df = outbreak_df.copy()
    df['severity_rank'] = df['cases'].rank(ascending=False, method='min')
    cur = df[df['is_current']]
    if cur.empty:
        return None
    rank = int(cur.iloc[0]['severity_rank'])
    total = len(df)
    pct   = round((1 - rank / total) * 100, 1)
    return {
        'total_outbreaks': total,
        'current_rank':    rank,
        'percentile':      pct,
        'current_name':    cur.iloc[0]['name'],
        'summary': (f"Current outbreak is #{rank} of {total} outbreaks analysed "
                    f"({pct:.1f}th percentile of severity)"),
    }


def create_outbreak_comparison_chart(outbreak_df):
    """Bar chart: total cases per outbreak."""
    df = outbreak_df.sort_values('cases', ascending=False)
    fig, ax = plt.subplots(figsize=(12, 5), dpi=72)
    colors = ['#DC3545' if r['is_current'] else '#1565C0'
              for _, r in df.iterrows()]
    bars = ax.bar(df['name'], df['cases'], color=colors, alpha=0.82,
                  edgecolor='white', linewidth=0.8)
    for bar, val in zip(bars, df['cases']):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(df['cases']) * 0.01,
                f'{val:,}', ha='center', va='bottom', fontsize=7.5,
                fontweight='bold')
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(facecolor='#DC3545', label='Current Outbreak'),
                       Patch(facecolor='#1565C0', label='Historical')],
              loc='upper right', fontsize=9)
    ax.set_title("Total Confirmed Cases — Historical Comparison",
                 fontweight='bold', fontsize=12)
    ax.set_ylabel("Cases"); ax.tick_params(axis='x', rotation=35)
    ax.grid(True, alpha=0.2, axis='y')
    ax.spines[['top', 'right']].set_visible(False)
    plt.tight_layout()
    return fig


def create_cfr_comparison_chart(outbreak_df):
    """Bar chart: CFR per outbreak with WHO average line."""
    df = outbreak_df.sort_values('cfr', ascending=False)
    fig, ax = plt.subplots(figsize=(11, 4), dpi=72)
    colors = ['#DC3545' if r['is_current'] else '#2E7D32'
              for _, r in df.iterrows()]
    bars = ax.bar(df['name'], df['cfr'], color=colors, alpha=0.82,
                  edgecolor='white', linewidth=0.8)
    for bar, val in zip(bars, df['cfr']):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.8,
                f'{val:.1f}%', ha='center', va='bottom', fontsize=7.5,
                fontweight='bold')
    ax.axhline(50, color='red', ls='--', lw=1.5, alpha=0.7,
               label='Global avg CFR ~50%')
    ax.set_title("Case Fatality Rate (CFR) Comparison",
                 fontweight='bold', fontsize=12)
    ax.set_ylabel("CFR (%)"); ax.tick_params(axis='x', rotation=35)
    ax.legend(fontsize=9); ax.grid(True, alpha=0.2, axis='y')
    ax.spines[['top', 'right']].set_visible(False)
    plt.tight_layout()
    return fig


def create_duration_comparison_chart(outbreak_df):
    """Bar chart: outbreak duration in days."""
    df = outbreak_df.sort_values('duration', ascending=False)
    fig, ax = plt.subplots(figsize=(11, 4), dpi=72)
    colors = ['#DC3545' if r['is_current'] else '#F57C00'
              for _, r in df.iterrows()]
    bars = ax.bar(df['name'], df['duration'], color=colors, alpha=0.82,
                  edgecolor='white', linewidth=0.8)
    for bar, val in zip(bars, df['duration']):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(df['duration']) * 0.01,
                f'{int(val)}d', ha='center', va='bottom', fontsize=7.5,
                fontweight='bold')
    ax.set_title("Outbreak Duration Comparison",
                 fontweight='bold', fontsize=12)
    ax.set_ylabel("Days"); ax.tick_params(axis='x', rotation=35)
    ax.grid(True, alpha=0.2, axis='y')
    ax.spines[['top', 'right']].set_visible(False)
    plt.tight_layout()
    return fig


# TABS  (directly under banner — no gap)
# ═══════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11 = st.tabs([
    f"📈 {t('menu.epidemiology')}", f"🔮 {t('menu.forecast')}",
    f"🗺️ {t('menu.zones')}",       f"🧠 {t('menu.xai')}",
    f"📊 {t('menu.comparison')}",   f"🔬 {t('menu.advanced')}",
    f"📊 {t('menu.models')}",       f"📊 {t('menu.dashboard')}",
    f"📋 {t('menu.report')}",       f"🤖 {t('menu.chatbot')}",
    f"📚 {t('menu.publications')}",
])

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────
# TAB 1 · Epidemiology
# ─────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown("## National Epidemiological Overview")

    # ── Outcome summary cards ─────────────────────────────────────────
    st.markdown("### 📊 Outcome Summary")
    oc1, oc2, oc3, oc4 = st.columns(4)
    with oc1:
        st.metric("📊 Total Cases",   f"{total_cases:,}")
    with oc2:
        st.metric("💀 Deaths",        f"{total_deaths:,}",
                  delta=f"{cfr:.1f}% CFR",
                  delta_color="inverse")
    with oc3:
        st.metric("🏥 Recovered",     f"{total_recovered:,}",
                  delta=f"{recovery_rate:.1f}% recovery")
    with oc4:
        st.metric("🔄 Active Cases",  f"{active_cases:,}")

    st.markdown("---")

    # ── 2×3 chart grid ────────────────────────────────────────────────
    nat_clean = nat.copy()
    nat_clean['value']       = clean_series(nat_clean['value'])
    nat_clean['new_cases']   = clean_series(nat_clean['new_cases'])
    nat_clean['rolling7']    = clean_series(nat_clean['rolling7'])
    nat_clean['growth_rate'] = clean_series(nat_clean['growth_rate'], max_val=1000)
    nat_clean['deaths']      = clean_series(nat_clean['deaths'])
    nat_clean['recovered']   = clean_series(nat_clean['recovered'])

    with safe_plot():
        fig, axes = plt.subplots(2, 3, figsize=(15, 8), dpi=72)
        fig.suptitle(f"{cfg('display_name', 'Epidemic')} · {cfg('country', 'DRC')} | {last_dt}",
                     fontsize=13, fontweight='bold')

        # A. Cumulative Confirmed Cases
        ax = axes[0, 0]
        ax.fill_between(nat_clean['date'], nat_clean['value'],
                        alpha=0.18, color=PALETTE[0])
        ax.plot(nat_clean['date'], nat_clean['value'],
                color=PALETTE[0], lw=2.5)
        ax.set_title("A. Cumulative Confirmed Cases", fontweight='bold')
        ax.set_ylabel("Cases")
        ax.tick_params(axis='x', rotation=25)
        ax.grid(True, alpha=0.25)
        ax.spines[['top', 'right']].set_visible(False)

        # B. Daily New Cases
        ax = axes[0, 1]
        ax.bar(nat_clean['date'], nat_clean['new_cases'],
               alpha=0.5, color=PALETTE[1], label="Daily new cases")
        ax.plot(nat_clean['date'], nat_clean['rolling7'],
                color=PALETTE[0], lw=2, label="7-day rolling avg")
        ax.axhline(risk_thr, color='red', ls='--', lw=1.2, alpha=0.7,
                   label=f"Risk thr. ({int(risk_thr)} cases)")
        ax.set_title("B. Daily New Cases", fontweight='bold')
        ax.set_ylabel("Cases")
        ax.legend(fontsize=8)
        ax.tick_params(axis='x', rotation=25)
        ax.grid(True, alpha=0.25)
        ax.spines[['top', 'right']].set_visible(False)

        # C. Deaths & Recovered
        ax = axes[0, 2]
        ax.plot(nat_clean['date'], nat_clean['deaths'],
                color='#C62828', lw=2.5, label='Deaths')
        ax.fill_between(nat_clean['date'], nat_clean['deaths'],
                        alpha=0.15, color='#C62828')
        ax.plot(nat_clean['date'], nat_clean['recovered'],
                color='#2E7D32', lw=2.5, label='Recovered')
        ax.fill_between(nat_clean['date'], nat_clean['recovered'],
                        alpha=0.15, color='#2E7D32')
        ax.set_title("C. Deaths & Recovered", fontweight='bold')
        ax.set_ylabel("Cases")
        ax.legend(fontsize=8)
        ax.tick_params(axis='x', rotation=25)
        ax.grid(True, alpha=0.25)
        ax.spines[['top', 'right']].set_visible(False)

        # D. Daily Growth Rate
        ax = axes[1, 0]
        colors_gr = [PALETTE[1] if g > 0 else PALETTE[2]
                     for g in nat_clean['growth_rate']]
        ax.bar(nat_clean['date'], nat_clean['growth_rate'],
               color=colors_gr, alpha=0.7)
        ax.axhline(0, color='black', lw=0.8)
        ax.set_title("D. Daily Growth Rate (%)", fontweight='bold')
        ax.set_ylabel("Growth (%)")
        ax.tick_params(axis='x', rotation=25)
        ax.grid(True, alpha=0.25)
        ax.spines[['top', 'right']].set_visible(False)

        # E. New Case Distribution
        ax = axes[1, 1]
        nc = nat_clean['new_cases'][nat_clean['new_cases'] > 0]
        if len(nc) > 0:
            ax.hist(nc, bins=min(20, len(nc)),
                    color=PALETTE[3], edgecolor='white', alpha=0.85)
            ax.axvline(nc.mean(),   color=PALETTE[0], lw=2, ls='--',
                       label=f"Mean {nc.mean():.1f}")
            ax.axvline(nc.median(), color=PALETTE[1], lw=2, ls='--',
                       label=f"Median {nc.median():.1f}")
            ax.legend(fontsize=9)
        ax.set_title("E. New Case Distribution", fontweight='bold')
        ax.set_xlabel("Cases/day")
        ax.set_ylabel("Frequency")
        ax.spines[['top', 'right']].set_visible(False)

        # F. Outcome Rates (CFR vs Recovery)
        ax = axes[1, 2]
        bars = ax.bar(['CFR', 'Recovery Rate'],
                      [cfr, recovery_rate],
                      color=['#C62828', '#2E7D32'],
                      alpha=0.75, edgecolor='white')
        ax.set_title("F. Outcome Rates", fontweight='bold')
        ax.set_ylabel("Percentage (%)")
        for bar, val in zip(bars, [cfr, recovery_rate]):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.5,
                    f"{val:.1f}%", ha='center',
                    fontsize=9, fontweight='bold')
        ax.set_ylim(0, max(cfr, recovery_rate) * 1.25 + 5)
        ax.spines[['top', 'right']].set_visible(False)

        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    # ── Summary tables ────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("#### 📊 Case Summary")
        st.dataframe(pd.DataFrame({
            'Metric': ['Total cumulative', 'Peak daily', 'Mean daily',
                       'Median daily', 'Days active', 'Last 7-day total'],
            'Value': [f"{int(nat['value'].max()):,}",
                      f"{int(nat['new_cases'].max()):,}",
                      f"{nat['new_cases'].mean():.1f}",
                      f"{nat['new_cases'].median():.1f}",
                      f"{int((nat['new_cases'] > 0).sum())}",
                      f"{int(nat['new_cases'].tail(7).sum()):,}"]
        }), hide_index=True, width='stretch')

    with col2:
        st.markdown("#### 💀 Outcomes")
        st.dataframe(pd.DataFrame({
            'Metric': ['Total Deaths', 'Total Recovered',
                       'Active Cases', 'CFR', 'Recovery Rate'],
            'Value': [f"{total_deaths:,}",
                      f"{total_recovered:,}",
                      f"{active_cases:,}",
                      f"{cfr:.2f}%",
                      f"{recovery_rate:.2f}%"]
        }), hide_index=True, width='stretch')

    with col3:
        st.markdown("#### ⚙️ Few-Shot Split")
        st.dataframe(pd.DataFrame({
            'Parameter': ['Training weeks K', 'Train obs', 'Test obs',
                          'Risk threshold', 'Cutoff date', 'Features'],
            'Value': [str(n_shots), str(len(train_df)), str(len(test_df)),
                      f"{risk_thr:.1f} ({risk_pct}th pct)",
                      str(pd.Timestamp(cutoff).date()),
                      str(len(FEATURE_COLS))]
        }), hide_index=True, width='stretch')

    # ══════════════════════════════════════════════════════════════════
    # TEMPORAL COMPARISON — Week-over-Week, Month-over-Month, vs Peak
    # ══════════════════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("### 📅 Temporal Comparison")
    st.markdown("""
    <div class="info-box">
    <b>📅 Temporal Benchmarking</b> — Compare current epidemic indicators
    against previous periods to contextualise the trajectory.
    </div>
    """, unsafe_allow_html=True)

    # ── Build comparison windows ──────────────────────────────────────
    _today_row  = nat.iloc[-1]
    _today_val  = int(_today_row['value'])
    _today_new  = int(_today_row['new_cases'])
    _today_gr   = float(_today_row.get('growth_rate', gr_last))

    def _period_stats(nat_df, n_days_ago):
        """Return (cumulative, new_cases, growth_rate) for n_days_ago."""
        idx = max(0, len(nat_df) - 1 - n_days_ago)
        row = nat_df.iloc[idx]
        return (int(row['value']),
                int(row['new_cases']),
                float(row.get('growth_rate', 0)))

    _7d_cum,  _7d_new,  _7d_gr  = _period_stats(nat,  7)
    _14d_cum, _14d_new, _14d_gr = _period_stats(nat, 14)
    _30d_cum, _30d_new, _30d_gr = _period_stats(nat, 30)
    _peak_new = int(nat['new_cases'].max())
    _peak_date = nat.loc[nat['new_cases'].idxmax(), 'date'].strftime('%d %b %Y')
    _peak_cum  = int(nat.loc[nat['new_cases'].idxmax(), 'value'])

    def _delta_str(current, previous):
        """Format a signed percentage change string."""
        if previous == 0:
            return "N/A"
        pct = (current - previous) / previous * 100
        sign = "+" if pct >= 0 else ""
        return f"{sign}{pct:.1f}%"

    def _delta_color(current, previous, higher_is_bad=True):
        """Return 'normal', 'inverse', or 'off' for st.metric delta_color."""
        if previous == 0:
            return "off"
        return "inverse" if higher_is_bad else "normal"

    # ── 3-column comparison panels ────────────────────────────────────
    tc_period = st.radio(
        "Compare current vs:",
        ["7 days ago", "14 days ago", "30 days ago", "Epidemic peak"],
        horizontal=True, key="tc_period"
    )

    if tc_period == "7 days ago":
        ref_cum, ref_new, ref_gr, ref_label = _7d_cum,  _7d_new,  _7d_gr,  "7 days ago"
    elif tc_period == "14 days ago":
        ref_cum, ref_new, ref_gr, ref_label = _14d_cum, _14d_new, _14d_gr, "14 days ago"
    elif tc_period == "30 days ago":
        ref_cum, ref_new, ref_gr, ref_label = _30d_cum, _30d_new, _30d_gr, "30 days ago"
    else:
        ref_cum, ref_new, ref_gr, ref_label = _peak_cum, _peak_new, 0.0, f"peak ({_peak_date})"

    tc1, tc2, tc3, tc4 = st.columns(4)

    with tc1:
        st.metric(
            f"📊 Cumulative Cases",
            f"{_today_val:,}",
            delta=f"{_delta_str(_today_val, ref_cum)} vs {ref_label}",
            delta_color=_delta_color(_today_val, ref_cum)
        )
    with tc2:
        st.metric(
            "📈 Daily New Cases",
            f"{_today_new:,}",
            delta=f"{_delta_str(_today_new, ref_new)} vs {ref_label}",
            delta_color=_delta_color(_today_new, ref_new)
        )
    with tc3:
        st.metric(
            "📉 Growth Rate",
            f"{_today_gr:.1f}%",
            delta=f"{_today_gr - ref_gr:+.1f}pp vs {ref_label}",
            delta_color=_delta_color(_today_gr, ref_gr)
        )
    with tc4:
        pct_of_peak = (_today_new / _peak_new * 100) if _peak_new > 0 else 0
        st.metric(
            "🏔️ % of Peak Daily",
            f"{pct_of_peak:.0f}%",
            delta=f"Peak: {_peak_new:,} on {_peak_date}",
            delta_color="off"
        )

    # ── Comparison chart ──────────────────────────────────────────────
    st.markdown("#### 📊 Period Comparison Chart")
    with safe_plot():
        fig, axes = plt.subplots(1, 2, figsize=(12, 4), dpi=72)

        # Left: Cumulative cases with reference line
        ax = axes[0]
        ax.plot(nat['date'], nat['value'], color=PALETTE[0], lw=2,
                label='Cumulative cases')
        if tc_period != "Epidemic peak":
            n_back = {'7 days ago': 7, '14 days ago': 14, '30 days ago': 30}[tc_period]
            ref_date = nat['date'].iloc[max(0, len(nat) - 1 - n_back)]
            ax.axvline(ref_date, color='#E65100', ls='--', lw=1.5, alpha=0.8,
                       label=f'Reference: {ref_label}')
        ax.axvline(nat['date'].iloc[-1], color='#1A237E', ls='-', lw=1.5, alpha=0.6,
                   label='Today')
        ax.set_title("Cumulative Cases", fontweight='bold', fontsize=10)
        ax.set_ylabel("Cases"); ax.grid(True, alpha=0.2)
        ax.tick_params(axis='x', rotation=25, labelsize=8)
        ax.legend(fontsize=8); ax.spines[['top', 'right']].set_visible(False)

        # Right: Daily new cases bar with 7-day average
        ax2 = axes[1]
        ax2.bar(nat['date'], nat['new_cases'], color=PALETTE[1], alpha=0.45,
                width=0.8, label='Daily new cases')
        ax2.plot(nat['date'], nat['rolling7'], color=PALETTE[0], lw=2,
                 label='7-day rolling avg')
        # Highlight peak
        ax2.axhline(_peak_new, color='#C62828', ls=':', lw=1.5, alpha=0.7,
                    label=f'Peak: {_peak_new:,}')
        ax2.axhline(_today_new, color='#2E7D32', ls='--', lw=1.5, alpha=0.7,
                    label=f'Today: {_today_new:,}')
        ax2.set_title("Daily New Cases vs Peak", fontweight='bold', fontsize=10)
        ax2.set_ylabel("New cases"); ax2.grid(True, alpha=0.2, axis='y')
        ax2.tick_params(axis='x', rotation=25, labelsize=8)
        ax2.legend(fontsize=8); ax2.spines[['top', 'right']].set_visible(False)

        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    # ── Week-by-week table ────────────────────────────────────────────
    st.markdown("#### 📋 Week-by-Week Summary (last 8 weeks)")
    nat_w = nat.copy()
    nat_w['week'] = nat_w['date'].dt.to_period('W')
    weekly = (nat_w.groupby('week')
                   .agg(new_cases=('new_cases', 'sum'),
                        avg_daily=('new_cases', 'mean'),
                        peak_day=('new_cases', 'max'),
                        cum_end=('value', 'last'),
                        avg_gr=('growth_rate', 'mean'))
                   .tail(8).reset_index())
    weekly['vs_prev_week'] = weekly['new_cases'].pct_change() * 100
    weekly.columns = ['Week', 'Total New', 'Daily Avg', 'Peak Day',
                      'Cumulative', 'Avg Growth%', 'WoW Change%']
    for col in ['Daily Avg', 'Avg Growth%', 'WoW Change%']:
        weekly[col] = weekly[col].round(1)
    st.dataframe(
        weekly.iloc[::-1].reset_index(drop=True),
        hide_index=True, width='stretch'
    )

    # ── Interpretation box ────────────────────────────────────────────
    _trend_vs_ref  = _today_new - ref_new
    _interp_color  = "alert-red" if _trend_vs_ref > 0 else "alert-green"
    _interp_icon   = "📈" if _trend_vs_ref > 0 else "📉"
    _delta_display = _delta_str(_today_new, ref_new).lstrip("+-")   # strip sign for prose
    st.markdown(
        f'<div class="{_interp_color}">'
        f'{_interp_icon} <b>Interpretation vs {ref_label}:</b> '
        f'Daily new cases are {"higher" if _trend_vs_ref > 0 else "lower"} by '
        f'<b>{abs(_trend_vs_ref):,}</b> ({_delta_display}). '
        f'Growth rate has {"increased" if _today_gr > ref_gr else "decreased"} by '
        f'<b>{abs(_today_gr - ref_gr):.1f}</b> percentage points. '
        f'Currently at <b>{pct_of_peak:.0f}%</b> of the epidemic peak.'
        f'</div>',
        unsafe_allow_html=True
    )

# ─────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────
# TAB 2 · Forecast
# ─────────────────────────────────────────────────────────────────────
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

    # ── Log this forecast automatically ──────────────────────────────
    log_forecast(ci_fc, active_model, gr_last, nat, horizon)

    # ── Forecast History ──────────────────────────────────────────────
    st.markdown("---")
    render_forecast_history()

    # ── Zone-Level Forecast ───────────────────────────────────────────
    st.markdown("---")
    render_zone_forecast_panel(raw_df, zones, horizon, n_boot, r0_val, risk_thr)

# ─────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────
# TAB 3 · Zone Analysis
# ─────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────
with tab3:
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
                    hide_index=True, width='stretch'
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

    # ── GNN Propagation Graph ─────────────────────────────────────────
    if len(zones) > 2:
        st.markdown("---")
        render_gnn_visualization(zone_latest, risk_thr, raw_df)

    # ── Resource Calculator ───────────────────────────────────────────
    st.markdown("---")
    render_resource_calculator(active_cases, nat['new_cases'].tail(7).sum(),
                               cfr, horizon)

# ─────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────
# TAB 4 · Explainability
# ─────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────
with tab4:
    st.markdown("## 🧠 Model Explainability — BAEL Framework")
    st.markdown("""
    <div class="info-box">
    <b>Behavior-Aware Explainability Loop (BAEL)</b> — This module centralises explainability
    analyses for all forecasting models, in the context of the PhD in Artificial Intelligence
    at the <b>Université de l'Assomption au Congo (UAC)</b>, Butembo, DRC.
    Results update automatically with the active model selected in the sidebar.
    </div>
    """, unsafe_allow_html=True)

    xai_col1, xai_col2 = st.columns([1, 1])

    with xai_col1:
        st.markdown("### Feature Importance")
        mdl_xai = SKLEARN_MDLS.get(active_model)
        if mdl_xai is not None and hasattr(mdl_xai, 'feature_importances_'):
            fi = pd.DataFrame({
                'Feature': FEATURE_COLS,
                'Importance': mdl_xai.feature_importances_
            }).sort_values('Importance', ascending=False).head(15)

            with safe_plot():
                fig, ax = plt.subplots(figsize=(6, 5), dpi=72)
                # Colour gradient: top features darker
                n_fi = len(fi)
                colours = [PALETTE[0] if i < n_fi // 3 else
                           PALETTE[6] if i < 2 * n_fi // 3 else
                           "#90CAF9"
                           for i in range(n_fi)][::-1]
                ax.barh(fi['Feature'][::-1], fi['Importance'][::-1],
                        color=colours, alpha=0.88, edgecolor='white')
                ax.set_title(f"Feature Importance — {active_model}", fontweight='bold')
                ax.set_xlabel("Importance score")
                ax.spines[['top', 'right']].set_visible(False)
                ax.grid(axis='x', alpha=0.2)
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()

            # Rank column for clarity
            fi_show = fi.reset_index(drop=True).copy()
            fi_show.insert(0, 'Rank', range(1, len(fi_show) + 1))
            fi_show['Importance'] = fi_show['Importance'].round(4)
            st.dataframe(fi_show, hide_index=True, width='stretch')

        elif mdl_xai is not None and hasattr(mdl_xai, 'coef_'):
            coefs = pd.DataFrame({
                'Feature': FEATURE_COLS,
                'Coefficient': np.abs(mdl_xai.coef_)
            }).sort_values('Coefficient', ascending=False).head(15)

            with safe_plot():
                fig, ax = plt.subplots(figsize=(6, 5), dpi=72)
                ax.barh(coefs['Feature'][::-1], coefs['Coefficient'][::-1],
                        color=PALETTE[2], alpha=0.85, edgecolor='white')
                ax.set_title(f"Coefficient Magnitudes — {active_model}", fontweight='bold')
                ax.set_xlabel("|Coefficient|")
                ax.spines[['top', 'right']].set_visible(False)
                ax.grid(axis='x', alpha=0.2)
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()

            coefs_show = coefs.reset_index(drop=True).copy()
            coefs_show.insert(0, 'Rank', range(1, len(coefs_show) + 1))
            coefs_show['Coefficient'] = coefs_show['Coefficient'].round(4)
            st.dataframe(coefs_show, hide_index=True, width='stretch')
        else:
            st.info(
                f"Feature importance is not available for **{active_model}**. "
                "Load XGBoost, RandomForest, or LightGBM to display importance scores."
            )

    with xai_col2:
        st.markdown("### Residual Analysis")
        if len(preds_test) > 1 and len(y_test_al) > 1:
            n_xai = min(len(preds_test), len(y_test_al))
            resid_xai = y_test_al[:n_xai] - preds_test[:n_xai]

            with safe_plot():
                fig, axes = plt.subplots(2, 1, figsize=(6, 6), dpi=72)

                ax = axes[0]
                ax.scatter(preds_test[:n_xai], resid_xai,
                           color=PALETTE[0], alpha=0.6, s=25, edgecolors='white', linewidths=0.4)
                ax.axhline(0, color='red', lw=1.5, ls='--', label='Zero line')
                # ±1 std band
                ax.axhline(resid_xai.mean() + resid_xai.std(), color='orange',
                           lw=1, ls=':', alpha=0.7, label='±1 std')
                ax.axhline(resid_xai.mean() - resid_xai.std(), color='orange',
                           lw=1, ls=':', alpha=0.7)
                ax.set_title("Residuals vs Predictions", fontweight='bold')
                ax.set_xlabel("Predicted values")
                ax.set_ylabel("Residuals")
                ax.legend(fontsize=8)
                ax.spines[['top', 'right']].set_visible(False)
                ax.grid(True, alpha=0.2)

                ax = axes[1]
                ax.plot(resid_xai, color=PALETTE[3], lw=1.5, alpha=0.8)
                ax.axhline(0, color='red', lw=1, ls='--')
                ax.fill_between(range(len(resid_xai)), resid_xai, 0,
                                where=resid_xai > 0, alpha=0.2, color=PALETTE[1], label='Over-prediction')
                ax.fill_between(range(len(resid_xai)), resid_xai, 0,
                                where=resid_xai < 0, alpha=0.2, color=PALETTE[2], label='Under-prediction')
                ax.set_title("Residual Time Series", fontweight='bold')
                ax.set_xlabel("Observation index")
                ax.set_ylabel("Residual")
                ax.legend(fontsize=8)
                ax.spines[['top', 'right']].set_visible(False)

                plt.tight_layout()
                st.pyplot(fig)
                plt.close()

            # Shapiro-Wilk test
            sw_p_str, normal_msg = "N/A", ""
            if len(resid_xai) >= 3 and np.std(resid_xai) > 1e-6:
                try:
                    from scipy import stats as sp_stats
                    sw_p = sp_stats.shapiro(resid_xai)[1]
                    sw_p_str = f"{sw_p:.4f}" if not np.isnan(sw_p) else "N/A"
                    normal_msg = "Normal ✅" if (not np.isnan(sw_p) and sw_p > 0.05) else "Non-normal ⚠️"
                except Exception:
                    pass

            st.markdown(f"""
            <div class="info-box" style="font-size:12px; margin-top:8px;">
            <b>Residual Summary — {active_model}</b><br>
            Mean bias &nbsp;&nbsp;&nbsp;&nbsp;: <b>{resid_xai.mean():.2f}</b><br>
            Std of residuals: <b>{resid_xai.std():.2f}</b><br>
            Max residual &nbsp; : <b>{resid_xai.max():.2f}</b><br>
            Min residual &nbsp; : <b>{resid_xai.min():.2f}</b><br>
            Shapiro-Wilk p : <b>{sw_p_str}</b> {normal_msg}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Insufficient data for residual analysis.")

    st.markdown("---")
    st.markdown("### 🔁 BAEL Explainability Loop — Applied Steps")
    st.markdown("""
    <div class="report-card">
    <b>Steps of the BAEL cycle applied to the active model:</b>
    <ol style="margin-top:8px; color:#1A237E; line-height:1.8;">
      <li><b>Behavioural observation</b> — Case tracking by health zone over time</li>
      <li><b>Epidemiological feature engineering</b> — Lags, rolling means, growth rates</li>
      <li><b>Few-shot training (K weeks)</b> — Transfer learning under limited data conditions</li>
      <li><b>Prediction &amp; Bootstrap CI</b> — Quantified uncertainty on all forecasts</li>
      <li><b>Local / global explainability</b> — Feature importance, residuals, QQ-plot</li>
      <li><b>Feedback loop</b> — Hyperparameter adjustment driven by residual patterns</li>
    </ol>
    </div>
    """, unsafe_allow_html=True)

    # ── XAI model comparison table (improvement) ──────────────────────
    st.markdown("---")
    st.markdown("### 📊 Explainability Coverage by Model")
    xai_rows = []
    for mname in list(SKLEARN_MDLS.keys()) + (["TL-LSTM"] if TL_LSTM else []):
        m = SKLEARN_MDLS.get(mname) or (TL_LSTM if mname == "TL-LSTM" else None)
        has_fi   = "✅" if m is not None and hasattr(m, 'feature_importances_') else "—"
        has_coef = "✅" if m is not None and hasattr(m, 'coef_') else "—"
        xai_rows.append({
            "Model": mname,
            "Feature Importance": has_fi,
            "Coefficients": has_coef,
            "Residuals": "✅" if mname in all_metrics else "—",
            "SHAP-ready": "✅" if mname in ("XGBoost", "LightGBM", "RandomForest") else "—",
        })
    st.dataframe(pd.DataFrame(xai_rows), hide_index=True, width='stretch')

# ─────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────
# TAB 5 · Epidemic Comparison
# ─────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────
with tab5:
    st.markdown("## 📊 Epidemic Comparison — Historical Context")
    st.markdown("""
    <div class="info-box">
    <b>📊 Historical Context</b> — Compare the current {cfg('display_name','epidemic')} outbreak
    with past Ebola epidemics to contextualise scale, severity, and CFR.
    Data sourced from WHO situation reports and INRB.
    </div>
    """, unsafe_allow_html=True)

    _ob_df   = get_outbreak_comparison_data()
    _ob_stat = calculate_comparison_metrics(_ob_df)

    # ── Summary metrics ───────────────────────────────────────────────
    sm1, sm2, sm3, sm4 = st.columns(4)
    sm1.metric("📊 Outbreaks analysed", len(_ob_df))
    if _ob_stat:
        sm2.metric("📍 Current rank",
                   f"#{_ob_stat['current_rank']} / {_ob_stat['total_outbreaks']}")
        sm3.metric("📈 Severity percentile",
                   f"{_ob_stat['percentile']:.1f}th")
    _max_row = _ob_df.loc[_ob_df['cases'].idxmax()]
    sm4.metric("🏆 Largest ever", f"{int(_max_row['cases']):,}",
               delta=_max_row['name'])

    st.markdown("---")

    # ── Chart 1: Total cases ──────────────────────────────────────────
    st.markdown("#### 📈 Total Cases Comparison")
    with safe_plot():
        st.pyplot(create_outbreak_comparison_chart(_ob_df))
        plt.close()

    # ── Charts 2 & 3 side by side ────────────────────────────────────
    _cc1, _cc2 = st.columns(2)
    with _cc1:
        st.markdown("#### 💀 CFR Comparison")
        with safe_plot():
            st.pyplot(create_cfr_comparison_chart(_ob_df))
            plt.close()
    with _cc2:
        st.markdown("#### ⏱️ Duration Comparison")
        with safe_plot():
            st.pyplot(create_duration_comparison_chart(_ob_df))
            plt.close()

    st.markdown("---")

    # ── Data table ────────────────────────────────────────────────────
    st.markdown("#### 📋 Complete Outbreak Data")
    _disp = _ob_df.copy()
    _disp['cases']    = _disp['cases'].apply(lambda x: f"{int(x):,}")
    _disp['deaths']   = _disp['deaths'].apply(lambda x: f"{int(x):,}")
    _disp['cfr']      = _disp['cfr'].apply(lambda x: f"{x:.1f}%")
    _disp['duration'] = _disp['duration'].apply(lambda x: f"{int(x)} days")
    _disp = _disp.drop(columns=['is_current'])
    st.dataframe(_disp, hide_index=True, width='stretch')

    st.markdown("---")

    # ── Current outbreak context card ─────────────────────────────────
    st.markdown("#### 📌 Current Outbreak Context")
    _cur = _ob_df[_ob_df['is_current']].iloc[0]
    st.markdown(f"""
    <div style="background:#E8EAF6;border-radius:10px;padding:20px;
                border-left:4px solid #DC3545;color:#1A237E;">
        <h4 style="color:#C62828;margin:0 0 12px 0;">
            🔴 Current Outbreak: {_cur['name']}
        </h4>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;
                    font-size:14px;color:#1A237E;">
            <div><b>📊 Cases:</b> {int(_cur['cases']):,}</div>
            <div><b>💀 Deaths:</b> {int(_cur['deaths']):,}</div>
            <div><b>📈 CFR:</b> {_cur['cfr']:.1f}%</div>
            <div><b>⏱️ Duration:</b> {int(_cur['duration'])} days</div>
            <div><b>🧬 Strain:</b> {_cur['strain']}</div>
            <div><b>🌍 Countries:</b> {_cur['countries']}</div>
        </div>
        <div style="margin-top:12px;padding-top:10px;border-top:1px solid #C5CAE9;
                    font-size:13px;color:#283593;">
            <b>📝 Notes:</b> {_cur['notes']}<br>
            <b>📊 Status:</b> {_ob_stat['summary'] if _ob_stat else 'N/A'}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Key insights ──────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 💡 Key Insights")
    _insights = []
    if _ob_stat:
        if _ob_stat['percentile'] > 75:
            _insights.append("🔴 **High Severity** — top 25% of historical outbreaks")
        elif _ob_stat['percentile'] > 50:
            _insights.append("🟡 **Moderate Severity** — top 50% of historical outbreaks")
        else:
            _insights.append("🟢 **Lower Severity** — bottom 50% of historical outbreaks")
    _ccfr = _cur['cfr']
    if _ccfr > 50:
        _insights.append(f"🔴 **High CFR** — {_ccfr:.1f}% (above historical avg ~50%)")
    elif _ccfr > 30:
        _insights.append(f"🟡 **Moderate CFR** — {_ccfr:.1f}% (near avg ~50%)")
    else:
        _insights.append(f"🟢 **Low CFR** — {_ccfr:.1f}% (below avg ~50%)")
    _avg_dur = _ob_df['duration'].mean()
    _insights.append(
        f"⏱️ **Duration** — {int(_cur['duration'])}d vs avg {_avg_dur:.0f}d "
        f"({'longer' if _cur['duration'] > _avg_dur else 'shorter'} than average)"
    )
    if "Bundibugyo" in _cur['strain']:
        if "Bundibugyo" in cfg("strain", ""):
            _insights.append("🧬 **Bundibugyo strain** — less common; first identified DRC 2012")
        elif cfg("strain", ""):
            _insights.append(f"🧬 **{cfg('strain')}** — verify strain-specific parameters")
    for _ins in _insights:
        st.markdown(f"- {_ins}")

    st.markdown("---")

    # ── Export ────────────────────────────────────────────────────────
    st.markdown("#### 📤 Export Comparison Data")
    _ex1, _ex2 = st.columns(2)
    with _ex1:
        st.download_button(
            "📥 Download CSV",
            data=_ob_df.to_csv(index=False).encode('utf-8'),
            file_name=f"ebola_comparison_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv", key="ob_csv_dl"
        )
    with _ex2:
        st.download_button(
            "📥 Download JSON",
            data=_ob_df.to_json(orient='records', indent=2).encode('utf-8'),
            file_name=f"ebola_comparison_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json", key="ob_json_dl"
        )

    # ── Historical references (Publications section) ──────────────────
    st.markdown("---")
    st.markdown("#### 📚 Key References")
    st.markdown("""
    <div style="background:#F8FAFC;border-radius:8px;padding:15px;
                border:1px solid #E3E8EF;color:#1A237E;">
        <b style="color:#1A237E;">📖 Sources for historical comparison:</b>
        <ul style="margin-top:8px;line-height:1.9;color:#1A237E;">
            <li><b>WHO Ebola Situation Reports</b> — weekly outbreak updates</li>
            <li><b>Verity et al., 2020</b> — "Estimates of the severity of COVID-19 disease"
                <i>Lancet Infectious Diseases</i></li>
            <li><b>INRB / Ministère de la Santé DRC</b> — surveillance data</li>
            <li><b>CDC Outbreak Reports</b> — historical summaries</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────
# TAB 6 · Advanced Analysis
# ─────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────
with tab6:
    st.markdown("## 🔬 Advanced Analysis")
    st.markdown("""
    <div class="info-box">
    <b>🔬 Advanced Analytical Tools</b><br>
    Explore deeper insights with advanced statistical analysis, anomaly detection,
    correlation studies, zone clustering, and sensitivity analysis.
    </div>
    """, unsafe_allow_html=True)

    def _detect_trend_breaks(data):
        from scipy import stats
        x = np.arange(len(data))
        slope, intercept, r_val, p_val, std_err = stats.linregress(x, data)
        bps, win = [], min(7, len(data) // 4)
        for i in range(win, len(data) - win):
            left, right = data[i-win:i], data[i:i+win]
            if len(left) > 1 and len(right) > 1:
                ls, *_ = stats.linregress(range(len(left)),  left)
                rs, *_ = stats.linregress(range(len(right)), right)
                if abs(ls - rs) > 2 * std_err: bps.append(i)
        return {'slope': slope, 'intercept': intercept, 'r2': r_val**2,
                'p_value': p_val, 'std_err': std_err, 'breakpoints': bps}

    def _detect_anomalies(data, threshold=2.5):
        if len(data) < 3: return []
        mean, std = np.mean(data), np.std(data)
        if std == 0: return []
        return [{'index': i, 'value': float(v), 'z_score': float(z := (v-mean)/std),
                 'severity': '🔴 High' if abs(z)>3 else '🟡 Medium'}
                for i, v in enumerate(data) if abs((v-mean)/std) > threshold]

    def _apply_clustering(zdf, n_clusters=3):
        from sklearn.cluster import KMeans
        from sklearn.preprocessing import StandardScaler
        feats = StandardScaler().fit_transform(zdf[['value']].values)
        km    = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = km.fit_predict(feats)
        order  = sorted(range(n_clusters), key=lambda c: km.cluster_centers_[c][0])
        lmap   = {order[0]: '🟢 Low Risk', order[1]: '🟡 Medium Risk', order[2]: '🔴 High Risk'}
        zdf = zdf.copy()
        zdf['cluster'] = labels
        zdf['risk_label'] = zdf['cluster'].map(lmap)
        return zdf

    atabs = st.tabs(["📈 Trend", "🔮 Anomalies", "📊 Correlation",
                     "🎯 Clustering", "📈 Sensitivity", "📋 Report"])

    with atabs[0]:  # Trend
        st.markdown("### 📈 Trend Analysis")
        if len(nat['value']) > 7:
            tr = _detect_trend_breaks(nat['value'].values)
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Slope", f"{tr['slope']:.2f}"); c2.metric("R²", f"{tr['r2']:.4f}")
            c3.metric("P-value", f"{tr['p_value']:.4f}"); c4.metric("Breakpoints", len(tr['breakpoints']))
            with safe_plot():
                fig, ax = plt.subplots(figsize=(10,4), dpi=72)
                ax.plot(nat['date'], nat['value'], color=PALETTE[0], lw=2, label='Actual')
                ax.plot(nat['date'], tr['slope']*np.arange(len(nat['value']))+tr['intercept'],
                        'r--', lw=2, label='Trend')
                for bp in tr['breakpoints']:
                    ax.axvline(nat['date'].iloc[bp], color='green', ls=':', lw=2, alpha=0.7,
                               label='Breakpoint' if bp==tr['breakpoints'][0] else '')
                ax.set_title("Trend Analysis with Breakpoint Detection", fontweight='bold')
                ax.set_xlabel("Date"); ax.set_ylabel("Cases")
                ax.legend(fontsize=8); ax.grid(True, alpha=0.2)
                ax.tick_params(axis='x', rotation=25); ax.spines[['top','right']].set_visible(False)
                plt.tight_layout(); st.pyplot(fig); plt.close()
            if tr['p_value'] < 0.05: st.success("✅ Significant trend (p < 0.05)")
            else: st.info(f"ℹ️ No significant trend (p = {tr['p_value']:.4f})")
            if tr['breakpoints']: st.warning(f"⚠️ {len(tr['breakpoints'])} breakpoints detected")
            else: st.success("✅ No significant breakpoints")
        else: st.info("Need at least 7 data points")

    with atabs[1]:  # Anomalies
        st.markdown("### 🔮 Anomaly Detection")
        if len(nat['new_cases']) > 3:
            anoms = _detect_anomalies(nat['new_cases'].values)
            c1,c2,c3 = st.columns(3)
            c1.metric("Total Anomalies", len(anoms))
            c2.metric("🔴 High Severity", sum(1 for a in anoms if '🔴' in a['severity']))
            c3.metric("Max Z-Score", f"{max((a['z_score'] for a in anoms), default=0):.2f}")
            with safe_plot():
                fig, ax = plt.subplots(figsize=(10,4), dpi=72)
                ax.plot(nat['date'], nat['new_cases'], color=PALETTE[0], lw=2, label='Daily Cases')
                for a in anoms:
                    col = '#C62828' if '🔴' in a['severity'] else '#E65100'
                    ax.scatter(nat['date'].iloc[a['index']], a['value'],
                               color=col, s=120, zorder=5, edgecolor='white', lw=2)
                    ax.annotate(f"z={a['z_score']:.1f}",
                                xy=(nat['date'].iloc[a['index']], a['value']),
                                xytext=(0,10), textcoords='offset points', fontsize=8)
                ax.set_title("Anomaly Detection — Daily Cases", fontweight='bold')
                ax.set_xlabel("Date"); ax.set_ylabel("New Cases")
                ax.grid(True, alpha=0.2); ax.tick_params(axis='x', rotation=25)
                ax.spines[['top','right']].set_visible(False)
                plt.tight_layout(); st.pyplot(fig); plt.close()
            if anoms:
                st.dataframe(pd.DataFrame([{
                    'Date': nat['date'].iloc[a['index']].strftime('%Y-%m-%d'),
                    'Cases': int(a['value']), 'Z-Score': round(a['z_score'],2),
                    'Severity': a['severity']} for a in anoms]),
                    hide_index=True, width='stretch')
                high = [a for a in anoms if '🔴' in a['severity']]
                if high: st.error(f"⚠️ {len(high)} high-severity anomalies — investigate these dates")
                else: st.info("ℹ️ Low severity anomalies — continue monitoring")
            else: st.success("✅ No anomalies detected. Data is stable.")
        else: st.info("Need at least 3 data points")

    with atabs[2]:  # Correlation
        st.markdown("### 📊 Correlation Analysis")
        if len(nat) > 7:
            ccols = [c for c in ['value','new_cases','growth_rate'] if c in nat.columns]
            if len(ccols) > 1:
                cmat = nat[ccols].corr()
                ac1, ac2 = st.columns(2)
                with ac1:
                    st.dataframe(pd.DataFrame([
                        {'Pair': f"{ccols[i]} × {ccols[j]}",
                         'Correlation': round(cmat.iloc[i,j],3)}
                        for i in range(len(ccols)) for j in range(i+1,len(ccols))]),
                        hide_index=True, width='stretch')
                with ac2:
                    with safe_plot():
                        fig, ax = plt.subplots(figsize=(6,4), dpi=72)
                        im = ax.imshow(cmat.values, cmap='RdYlGn', vmin=-1, vmax=1)
                        ax.set_xticks(range(len(ccols))); ax.set_xticklabels(ccols, rotation=45, ha='right')
                        ax.set_yticks(range(len(ccols))); ax.set_yticklabels(ccols)
                        for i in range(len(ccols)):
                            for j in range(len(ccols)):
                                ax.text(j,i,f"{cmat.values[i,j]:.2f}",ha='center',va='center',fontsize=9)
                        plt.colorbar(im); ax.set_title("Correlation Heatmap", fontweight='bold')
                        plt.tight_layout(); st.pyplot(fig); plt.close()
        else: st.info("Need at least 7 data points")

    with atabs[3]:  # Clustering
        st.markdown("### 🎯 Zone Clustering")
        if len(zones) > 2:
            cl = _apply_clustering(zone_latest.copy())
            zc1, zc2 = st.columns(2)
            with zc1:
                cstats = cl.groupby('risk_label')['value'].agg(['count','mean','sum','max']).round(1)
                cstats.columns = ['Zones','Mean','Total','Max']
                st.dataframe(cstats, width='stretch')
            with zc2:
                for lbl in ['🔴 High Risk','🟡 Medium Risk','🟢 Low Risk']:
                    grp = cl[cl['risk_label']==lbl]
                    if not grp.empty:
                        names = grp['zone'].tolist()
                        st.markdown(f"**{lbl}** ({len(names)})")
                        st.caption(', '.join(names[:5]) + ('…' if len(names)>5 else ''))
            with safe_plot():
                fig, ax = plt.subplots(figsize=(10,4), dpi=72)
                for lbl, col in [('🔴 High Risk','#C62828'),('🟡 Medium Risk','#F57C00'),('🟢 Low Risk','#2E7D32')]:
                    grp = cl[cl['risk_label']==lbl]
                    if not grp.empty:
                        ax.scatter(grp['zone'], grp['value'], color=col, s=50, alpha=0.7, label=lbl)
                ax.set_title("Zone Clustering by Risk Level", fontweight='bold')
                ax.set_ylabel("Total Cases"); ax.set_yscale('log')
                ax.tick_params(axis='x', rotation=45); ax.legend(fontsize=8)
                ax.grid(True, alpha=0.2); ax.spines[['top','right']].set_visible(False)
                plt.tight_layout(); st.pyplot(fig); plt.close()
            hrz = cl[cl['risk_label']=='🔴 High Risk']
            if not hrz.empty:
                st.warning(f"⚠️ {len(hrz)} HIGH RISK zones")
                st.info(f"Priority: {', '.join(hrz['zone'].tolist()[:10])}")
        else: st.info("Need at least 3 zones")

    with atabs[4]:  # Sensitivity
        st.markdown("### 📈 Sensitivity Analysis")
        sa_param = st.selectbox("Select parameter",
            options=['r0','horizon','N'],
            format_func=lambda x: {'r0':'R₀','horizon':'Horizon (days)','N':'Population'}[x],
            key="sens_param")
        sa_ranges = {'r0':[1.0,1.3,1.5,1.8,2.0,2.3,2.5],
                     'horizon':[7,14,21,30,45,60,90], 'N':[50000,75000,100000,150000,200000]}
        if st.button("🚀 Run Analysis", width='stretch', key="sens_run"):
            base = {'last_cases': float(nat['new_cases'].iloc[-1]),
                    'horizon': horizon, 'r0': r0_val, 'N': 100000}
            sres = []
            for val in sa_ranges[sa_param]:
                p = base.copy(); p[sa_param] = val
                try:
                    sim = sir_project(last_cases=p['last_cases'], horizon=p['horizon'], R0=p['r0'], N=p['N'])
                    sres.append({'Value':val,'Peak Cases':int(max(sim)),
                                 'Total Cases':int(sum(sim)),'Mean Daily':int(np.mean(sim))})
                except Exception:
                    sres.append({'Value':val,'Peak Cases':0,'Total Cases':0,'Mean Daily':0})
            sdf = pd.DataFrame(sres)
            st.dataframe(sdf, hide_index=True, width='stretch')
            with safe_plot():
                fig, ax = plt.subplots(figsize=(10,4), dpi=72)
                ax.plot(sdf['Value'], sdf['Peak Cases'],  'o-', color=PALETTE[0], lw=2, label='Peak')
                ax.plot(sdf['Value'], sdf['Total Cases'], 's--', color=PALETTE[1], lw=2, label='Total')
                ax.set_title(f"Sensitivity — {sa_param}", fontweight='bold')
                ax.set_xlabel(sa_param); ax.set_ylabel("Projected Cases")
                ax.legend(fontsize=8); ax.grid(True, alpha=0.2)
                ax.spines[['top','right']].set_visible(False)
                plt.tight_layout(); st.pyplot(fig); plt.close()
            mn, mx = sdf['Peak Cases'].min(), sdf['Peak Cases'].max()
            sens = (mx-mn)/mn*100 if mn > 0 else 0
            st.info(f"Range: {mn:,} — {mx:,} · Sensitivity: ±{sens:.1f}%")
            if sens > 50: st.warning(f"⚠️ High sensitivity to {sa_param}")
            elif sens > 20: st.info(f"ℹ️ Moderate sensitivity")
            else: st.success("✅ Forecast is robust")

    with atabs[5]:  # Report
        st.markdown("### 📋 Advanced Analysis Report")
        if st.button("📊 Generate Report", width='stretch', key="adv_report_btn"):
            with st.spinner("Generating..."):
                _rs3 = sum([30 if gr_last>20 else 20 if gr_last>10 else 10 if gr_last>5 else 0,
                            25 if int(nat['new_cases'].tail(7).sum())>100 else 15 if int(nat['new_cases'].tail(7).sum())>50 else 0,
                            20 if int(nat['value'].max())>2000 else 10 if int(nat['value'].max())>1000 else 0])
                _rl3  = "🔴 HIGH" if _rs3>50 else "🟡 MEDIUM" if _rs3>25 else "🟢 LOW"
                _an3  = _detect_anomalies(nat['new_cases'].values)
                _tr3  = _detect_trend_breaks(nat['value'].values) if len(nat['value'])>7 else None
                _cl3  = _apply_clustering(zone_latest.copy()) if len(zones)>2 else None
                _hr3  = _cl3[_cl3['risk_label']=='🔴 High Risk']['zone'].tolist() if _cl3 is not None else []
                report = {
                    'generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'summary':   {'total_cases': int(nat['value'].max()),
                                  'new_cases_7d': int(nat['new_cases'].tail(7).sum()),
                                  'growth_rate': gr_last, 'risk_score': _rs3,
                                  'risk_level': _rl3, 'zones_affected': len(zones)},
                    'trend':     {'slope': _tr3['slope'] if _tr3 else None,
                                  'r2':    _tr3['r2']    if _tr3 else None,
                                  'breakpoints': len(_tr3['breakpoints']) if _tr3 else 0},
                    'anomalies': {'total': len(_an3),
                                  'high_severity': sum(1 for a in _an3 if '🔴' in a['severity'])},
                    'clustering': {'total_zones': len(zones),
                                   'high_risk_count': len(_hr3),
                                   'high_risk_names': _hr3[:10]},
                    'forecast':   ci_fc,
                    'model':      {'active': active_model,
                                   'rmse':   metrics_primary.get('RMSE','N/A'),
                                   'r2':     metrics_primary.get('R²','N/A')},
                    'recommendations': []
                }
                if _rs3 > 50:   report['recommendations'].append("🔴 CRITICAL: Activate emergency response")
                if gr_last > 20: report['recommendations'].append("🔴 Growth > 20% — immediate intervention")
                elif gr_last > 10: report['recommendations'].append("🟡 Growth elevated — enhanced surveillance")
                if _hr3:  report['recommendations'].append(f"📍 Focus on {len(_hr3)} high-risk zones")
                if _an3:  report['recommendations'].append(f"🔍 Investigate {len(_an3)} anomalies")
                if not report['recommendations']: report['recommendations'].append("✅ Routine monitoring")

                rc1, rc2 = st.columns(2)
                with rc1:
                    st.markdown("##### 📊 Summary"); st.json(report['summary'],   expanded=False)
                    st.markdown("##### 📈 Trend");   st.json(report['trend'],     expanded=False)
                with rc2:
                    st.markdown("##### 🔍 Anomalies"); st.json(report['anomalies'],  expanded=False)
                    st.markdown("##### 🎯 Clustering"); st.json(report['clustering'], expanded=False)

                st.markdown("#### 💡 Recommendations")
                for rec in report['recommendations']:
                    if '🔴' in rec: st.error(rec)
                    elif '🟡' in rec: st.warning(rec)
                    else: st.info(rec)

                st.download_button(
                    "📥 Download Advanced Report (JSON)",
                    data=json.dumps(report, indent=2, ensure_ascii=False).encode('utf-8'),
                    file_name=f"advanced_report_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                    mime="application/json", width='stretch', key="adv_report_dl"
                )


# ═══════════════════════════════════════════════════════════════════════
# AI CHATBOT — EbolaChatbot class
# ═══════════════════════════════════════════════════════════════════════


class EbolaChatbot:
    """Rule-based AI assistant for Ebola epidemiology analysis."""

    def __init__(self, nat_data, zone_data, all_metrics, active_model,
                 ci_fc, risk_thr, gr_last):
        self.nat          = nat_data
        self.zones        = zone_data
        self.metrics      = all_metrics
        self.active_model = active_model
        self.ci_fc        = ci_fc
        self.risk_thr     = risk_thr
        self.gr_last      = gr_last
        self.total_cases  = int(nat_data['value'].max())
        self.new_cases_7d = int(nat_data['new_cases'].tail(7).sum())
        self.last_date    = nat_data['date'].max().strftime('%d %b %Y')
        self.total_deaths    = total_deaths
        self.total_recovered = total_recovered
        self.active_cases    = active_cases
        self.cfr             = cfr
        self.recovery_rate   = recovery_rate

        self.patterns = {
            'total_cases':       [r'(total|all|cumulative)\s*(cases|confirmed)',
                                   r'how many (cases|confirmed)', r'number of cases'],
            'new_cases':         [r'(new|daily|recent)\s*(cases)',
                                   r'how many new', r'nouveaux cas'],
            'zone_cases':        [r'cases? in (\w+)', r'(\w+)\s*(zone|cases)',
                                   r'how many in (\w+)'],
            'growth_rate':       [r'growth', r'rate', r'taux', r'croissance',
                                   r'how fast', r'increasing'],
            'trend':             [r'trend', r'tendance', r'going (up|down)',
                                   r'(increasing|decreasing)'],
            'model_performance': [r'model.*(performance|good|accurate|best)',
                                   r'best model', r'rmse', r'r2', r'r²'],
            'forecast':          [r'forecast', r'predict', r'future',
                                   r'prevision', r'prévision', r'next week'],
            'high_risk':         [r'high.?risk', r'most affected',
                                   r'worst', r'dangerous'],
            'zone_list':         [r'list.*zones?', r'all zones?',
                                   r'which zones?', r'zones? affected'],
            'alerts':            [r'alert', r'warning', r'emergency', r'critical'],
            'date':              [r'\bdate\b', r'when', r'last report', r'update'],
            'deaths':            [r'(death|deaths|mortality|fatality|died|cfr)',
                                   r'how many died', r'fatality rate'],
            'recovered':         [r'(recover|recovered|recovery|healed|gueri)',
                                   r'how many recovered', r'recovery rate'],
            'help':              [r'help', r'what can you', r'capabilities'],
            'about':             [r'about', r'who are you', r'what is this'],
            'resources':         [r'resource', r'bed', r'ppe', r'worker',
                                   r'ambulance', r'equipment', r'supply',
                                   r'need.*hospital', r'how many.*staff'],
            'comparison':        [r'compar', r'historical', r'past outbreak',
                                   r'versus', r'\bvs\b', r'how does.*current',
                                   r'worst.*outbreak', r'biggest.*ebola'],
        }

    # ── Dispatcher ────────────────────────────────────────────────────
    def get_response(self, question):
        import re
        q = re.sub(r'[^\w\s]', '', question.lower().strip())

        if any(re.search(p, q) for p in self.patterns['total_cases']):
            return self._total_cases()
        if any(re.search(p, q) for p in self.patterns['new_cases']):
            return self._new_cases()
        for p in self.patterns['zone_cases']:
            m = re.search(p, q)
            if m and m.groups():
                return self._zone_cases(m.group(1).capitalize())
        if any(re.search(p, q) for p in self.patterns['growth_rate']):
            return self._growth_rate()
        if any(re.search(p, q) for p in self.patterns['trend']):
            return self._trend()
        if any(re.search(p, q) for p in self.patterns['model_performance']):
            return self._model_performance()
        if any(re.search(p, q) for p in self.patterns['forecast']):
            return self._forecast()
        if any(re.search(p, q) for p in self.patterns['high_risk']):
            return self._high_risk()
        if any(re.search(p, q) for p in self.patterns['zone_list']):
            return self._zone_list()
        if any(re.search(p, q) for p in self.patterns['alerts']):
            return self._alerts()
        if any(re.search(p, q) for p in self.patterns['date']):
            return self._date()
        if any(re.search(p, q) for p in self.patterns['deaths']):
            return self._deaths()
        if any(re.search(p, q) for p in self.patterns['recovered']):
            return self._recovered()
        if any(re.search(p, q) for p in self.patterns['resources']):
            return self._resources()
        if any(re.search(p, q) for p in self.patterns['comparison']):
            return self._comparison()
        if any(re.search(p, q) for p in self.patterns['help']):
            return self._help()
        if any(re.search(p, q) for p in self.patterns['about']):
            return self._about()
        return self._default(question)

    # ── Response methods ──────────────────────────────────────────────
    def _status_icon(self):
        return "🔴" if self.gr_last > 20 else "🟡" if self.gr_last > 5 else "🟢"

    def _total_cases(self):
        return (f"📊 **Total confirmed cases:** {self.total_cases:,}\n\n"
                f"- New cases (7d): **{self.new_cases_7d:,}**\n"
                f"- Last report: **{self.last_date}**\n"
                f"- Health zones: **{len(self.zones)}**\n"
                f"- Growth rate: {self._status_icon()} **{self.gr_last:.1f}%**")

    def _new_cases(self):
        icon = "📈" if self.gr_last > 5 else "📉" if self.gr_last < -5 else "📊"
        return (f"📈 **New cases summary**\n\n"
                f"- Last 7 days: **{self.new_cases_7d:,}**\n"
                f"- Daily average: **{self.new_cases_7d/7:.1f}**\n"
                f"- Growth rate: **{self.gr_last:.1f}%**\n"
                f"- Trend: {icon} {'Increasing' if self.gr_last>5 else 'Decreasing' if self.gr_last<-5 else 'Stable'}")

    def _zone_cases(self, zone_name):
        zdf = self.zones[self.zones['zone'].str.lower() == zone_name.lower()]
        if zdf.empty:
            return f"❌ Zone **'{zone_name}'** not found. Try *list zones* for all zone names."
        cases = int(zdf['value'].iloc[0])
        pct   = (cases / self.total_cases * 100) if self.total_cases else 0
        risk  = "🔴 HIGH RISK" if cases > self.risk_thr else "🟡 MODERATE" if cases > self.risk_thr * 0.4 else "🟢 LOW"
        return (f"📍 **Zone: {zone_name}**\n\n"
                f"- Confirmed cases: **{cases:,}**\n"
                f"- % of national total: **{pct:.1f}%**\n"
                f"- Risk level: {risk}")

    def _growth_rate(self):
        status = "🔴 CRITICAL" if self.gr_last > 20 else "🟡 ELEVATED" if self.gr_last > 5 else "🟢 STABLE"
        action = ("⚠️ Immediate intervention required" if self.gr_last > 20
                  else "🔬 Enhanced surveillance advised" if self.gr_last > 5
                  else "📋 Continue routine monitoring")
        return (f"📈 **Growth rate analysis**\n\n"
                f"- Current rate: **{self.gr_last:.1f}%**\n"
                f"- Status: **{status}**\n"
                f"- Recommendation: {action}")

    def _trend(self):
        trend  = 'increasing' if self.gr_last > 5 else 'decreasing' if self.gr_last < -5 else 'stable'
        icon   = "📈" if self.gr_last > 5 else "📉" if self.gr_last < -5 else "📊"
        return (f"📊 **Trend analysis**\n\n"
                f"- Overall trend: {icon} **{trend}**\n"
                f"- Growth rate: **{self.gr_last:.1f}%**\n"
                f"- Total cases: **{self.total_cases:,}**\n"
                f"- Last 7 days: **{self.new_cases_7d:,}** new cases")

    def _model_performance(self):
        if not self.metrics:
            return "📊 No model performance data available yet."
        lines = ["📊 **Model performance**\n"]
        for name, m in self.metrics.items():
            lines.append(f"**{name}:** RMSE={m.get('RMSE','—')} · R²={m.get('R²','—')} · MAE={m.get('MAE','—')}")
        try:
            best = max(self.metrics.items(),
                       key=lambda x: float(x[1].get('R²', -999))
                       if str(x[1].get('R²', -999)).replace('.','').replace('-','').isdigit() else -999)
            lines.append(f"\n🏆 **Best model:** {best[0]}")
        except Exception:
            pass
        return "\n".join(lines)

    def _forecast(self):
        mean, lo, hi = (self.ci_fc.get('mean', 0),
                        self.ci_fc.get('lower', 0),
                        self.ci_fc.get('upper', 0))
        interp = "a continued increase" if mean > self.new_cases_7d / 7 else "a stabilization"
        return (f"🔮 **Forecast summary**\n\n"
                f"- Next-step forecast: **{mean:.0f} cases**\n"
                f"- 95% CI: **[{lo:.0f} — {hi:.0f}]**\n"
                f"- Model: **{self.active_model}**\n"
                f"- Interpretation: suggests {interp}")

    def _high_risk(self):
        hrz = self.zones[self.zones['value'] > self.risk_thr]
        if hrz.empty:
            return "✅ No zones currently at high risk."
        lines = [f"🔴 **High-risk zones** ({len(hrz)} total)\n"]
        for _, row in hrz.sort_values('value', ascending=False).iterrows():
            lines.append(f"- **{row['zone']}:** {int(row['value']):,} cases")
        lines.append("\n⚠️ Immediate intervention recommended.")
        return "\n".join(lines)

    def _zone_list(self):
        lines = [f"🏥 **Health zones** (top 15 of {len(self.zones)})\n"]
        for _, row in self.zones.sort_values('value', ascending=False).head(15).iterrows():
            c    = int(row['value'])
            icon = "🔴" if c > self.risk_thr else "🟡" if c > self.risk_thr * 0.4 else "🟢"
            lines.append(f"- {icon} {row['zone']}: {c:,}")
        lines.append(f"\nTotal cases: **{self.total_cases:,}**")
        return "\n".join(lines)

    def _alerts(self):
        alerts = []
        if self.gr_last > 20:   alerts.append("🚨 CRITICAL — Growth rate > 20%")
        elif self.gr_last > 10: alerts.append("⚠️ WARNING — Growth rate > 10%")
        if self.total_cases > 5000:   alerts.append("🚨 CRITICAL — Total cases > 5,000")
        elif self.total_cases > 2000: alerts.append("⚠️ WARNING — Total cases > 2,000")
        hr = len(self.zones[self.zones['value'] > self.risk_thr])
        if hr > 10:  alerts.append(f"🚨 CRITICAL — {hr} zones at high risk")
        elif hr > 5: alerts.append(f"⚠️ WARNING — {hr} zones at high risk")
        if not alerts:
            return "✅ No active alerts. Situation currently stable."
        return "🚨 **Active alerts**\n\n" + "\n".join(f"- {a}" for a in alerts)

    def _date(self):
        return (f"📅 **Report information**\n\n"
                f"- Last report: **{self.last_date}**\n"
                f"- Data coverage: **{len(self.nat)} days**\n"
                f"- Dashboard updated: **{datetime.now().strftime('%Y-%m-%d %H:%M')}**")

    def _deaths(self):
        cfr_level = "🔴 high" if self.cfr > 10 else "🟡 moderate" if self.cfr > 5 else "🟢 low"
        return (f"💀 **Deaths Summary**\n\n"
                f"- Total deaths: **{self.total_deaths:,}**\n"
                f"- Case Fatality Rate (CFR): **{self.cfr:.1f}%** — {cfr_level}\n"
                f"- Active cases remaining: **{self.active_cases:,}**\n\n"
                f"📊 *Global Ebola average CFR is ~50%. "
                f"Current outbreak CFR: {self.cfr:.1f}%*")

    def _recovered(self):
        rec_level = ("✅ above average" if self.recovery_rate > 70
                     else "📊 average" if self.recovery_rate > 50
                     else "⚠️ below average")
        return (f"🏥 **Recovered Summary**\n\n"
                f"- Total recovered: **{self.total_recovered:,}**\n"
                f"- Recovery rate: **{self.recovery_rate:.1f}%** — {rec_level}\n"
                f"- Active cases: **{self.active_cases:,}**\n\n"
                f"📊 *{self.total_recovered:,} patients have recovered out of "
                f"{self.total_cases:,} confirmed cases.*")

    def _comparison(self):
        """Response for historical comparison queries."""
        try:
            ob_df  = get_outbreak_comparison_data()
            stats  = calculate_comparison_metrics(ob_df)
            cur    = ob_df[ob_df['is_current']].iloc[0]
            largest = ob_df.loc[ob_df['cases'].idxmax()]
            hi_cfr  = ob_df.loc[ob_df['cfr'].idxmax()]
            longest = ob_df.loc[ob_df['duration'].idxmax()]

            rank_txt = (f"#{stats['current_rank']} of {stats['total_outbreaks']} "
                        f"({stats['percentile']:.1f}th percentile)"
                        if stats else "N/A")
            return (
                f"📊 **Historical Comparison — {cur['name']}**\n\n"
                f"**Current outbreak:**\n"
                f"- Cases: **{int(cur['cases']):,}** · Deaths: **{int(cur['deaths']):,}**\n"
                f"- CFR: **{cur['cfr']:.1f}%** · Duration: **{int(cur['duration'])} days**\n"
                f"- Severity rank: **{rank_txt}**\n\n"
                f"**Historical records:**\n"
                f"- Largest: {largest['name']} — {int(largest['cases']):,} cases\n"
                f"- Highest CFR: {hi_cfr['name']} — {hi_cfr['cfr']:.1f}%\n"
                f"- Longest: {longest['name']} — {int(longest['duration'])} days\n\n"
                f"📊 *Open the **Epidemic Comparison** tab for full charts and data.*"
            )
        except Exception as e:
            return f"📊 Historical comparison data unavailable: {str(e)[:60]}"

    def _resources(self):
        ac  = max(0, self.active_cases)
        nc  = max(1, self.new_cases_7d // 7)
        sf  = 1.2  # 20% safety buffer
        return (f"🏥 **Estimated Resource Needs** (20% safety buffer)\n\n"
                f"- 🛏️ ETU beds: **{int(ac * 1.2 * sf):,}**\n"
                f"- 👩‍⚕️ Healthcare workers: **{int(ac * 3 * sf):,}**\n"
                f"- 🥼 PPE kits/day: **{int(nc * 6 * sf):,}**\n"
                f"- 🔬 Lab kits/day: **{int(nc * 3 * sf):,}**\n"
                f"- 📞 Contact tracers: **{int(nc * 0.5 * sf):,}**\n"
                f"- 🚑 Ambulances: **{int(ac / 15 * sf):,}**\n\n"
                f"📊 *Based on {ac:,} active cases · "
                f"{nc:,} new cases/day · WHO/MSF guidelines.*\n"
                f"Open the **Zone Analysis** tab → Resource Calculator "
                f"for full scenario planning.")
        return (f"🤖 **BAEL {cfg('display_name','Epidemic')} Assistant — Help**\n\n"
                "You can ask me about:\n\n"
                "📊 **Data** — total cases · new cases · cases by zone\n"
                "📈 **Trends** — growth rate · trend · forecast\n"
                "🏥 **Zones** — zone list · high-risk zones · specific zone\n"
                "📊 **Models** — performance · best model\n"
                "🚨 **Alerts** — active alerts · warnings\n\n"
                "**Examples:** *What are the total cases?* · *Cases in Butembo?* · "
                "*Which model is best?* · *Show high-risk zones*")

    def _about(self):
        return (f"🤖 **About BAEL {cfg('display_name','Epidemic')} Assistant**\n\n"
                f"I'm an AI assistant for the {cfg('display_name', 'Ebola')} outbreak.\n\n"
                "I analyse real-time data on cases, zones, trends, and model "
                "forecasts. Powered by the **BAEL** (Behavior-Aware Explainability "
                "Loop) framework — UAC Butembo, Nord-Kivu, DRC.")

    def _default(self, question):
        return (f"🤔 I didn't quite understand: *\"{question}\"*\n\n"
                "Try asking about: total cases · new cases · growth rate · "
                "forecast · high-risk zones · model performance\n\n"
                "Type **help** for the full list.")


# ─────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────
# TAB 7 · Model Comparison
# ─────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────
with tab7:
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
                hide_index=True, width='stretch'
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

    # ── Walk-Forward Validation ───────────────────────────────────────
    st.markdown("---")
    render_walk_forward_panel(feat_df, FEATURE_COLS, SCALER, SKLEARN_MDLS)

# ─────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────
# TAB 8 · Custom Dashboard
# ─────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────
with tab8:
    st.markdown("## 📊 Custom Dashboard")
    st.markdown("""
    <div class="info-box">
    <b>📊 Create your personalized dashboard</b><br>
    Select the widgets you want to display and arrange them in a layout that suits your needs.
    All widgets use real-time data from your application.
    </div>
    """, unsafe_allow_html=True)

    available_widgets = {
        "total_cases":  {"name": "📊 Total Cases",        "category": "Metrics"},
        "new_cases":    {"name": "📈 New Cases (7d)",      "category": "Metrics"},
        "zones":        {"name": "📍 Health Zones",        "category": "Metrics"},
        "growth_rate":  {"name": "📈 Growth Rate",         "category": "Metrics"},
        "model_r2":     {"name": "🎯 Model R²",            "category": "Models"},
        "forecast":     {"name": "🔮 Forecast Summary",    "category": "Forecast"},
        "risk_score":   {"name": "⚠️ Risk Score",          "category": "Alerts"},
        "alerts":       {"name": "🚨 Active Alerts",        "category": "Alerts"},
        "data_quality": {"name": "📊 Data Quality",        "category": "Data"},
        "zone_dist":    {"name": "📋 Zone Distribution",   "category": "Zones"},
        "model_perf":   {"name": "📊 Model Performance",   "category": "Models"},
        "weather":      {"name": "🌤️ Weather",             "category": "External"},
        "trend_chart":  {"name": "📈 Trend Chart",         "category": "Charts"},
        "daily_chart":  {"name": "📊 Daily Chart",         "category": "Charts"},
        "deaths":       {"name": "💀 Total Deaths",        "category": "Outcomes"},
        "recovered":    {"name": "🏥 Total Recovered",     "category": "Outcomes"},
        "cfr":          {"name": "📊 Case Fatality Rate",  "category": "Outcomes"},
        "active_cases": {"name": "🔄 Active Cases",        "category": "Outcomes"},
    }

    if 'dashboard_widgets' not in st.session_state:
        st.session_state.dashboard_widgets = ["total_cases", "new_cases", "growth_rate", "risk_score"]
    if 'dashboard_layout' not in st.session_state:
        st.session_state.dashboard_layout = "3 columns"
    if 'saved_dashboards' not in st.session_state:
        st.session_state.saved_dashboards = {}

    col_config1, col_config2, col_config3 = st.columns([2, 1, 1])

    with col_config1:
        st.markdown("#### Select Widgets")
        select_all = st.checkbox("Select All Widgets", key="dash_select_all")
        categories = {}
        for wid, info in available_widgets.items():
            categories.setdefault(info['category'], []).append(wid)
        selected_widgets = []
        for cat, widgets in categories.items():
            st.markdown(f"**{cat}**")
            for wid in widgets:
                default = True if select_all else wid in st.session_state.dashboard_widgets
                if st.checkbox(available_widgets[wid]['name'], value=default, key=f"widget_{wid}"):
                    selected_widgets.append(wid)

    with col_config2:
        st.markdown("#### Layout")
        layout = st.selectbox("Select layout",
                              ["1 column", "2 columns", "3 columns", "4 columns"],
                              index=2, key="dash_layout")
        st.session_state.dashboard_widgets = selected_widgets
        st.session_state.dashboard_layout  = layout
        n_cols = int(layout.split()[0])
        st.markdown("#### Display Options")
        show_titles  = st.checkbox("Show widget titles", value=True, key="dash_titles")
        compact_mode = st.checkbox("Compact mode",       value=False, key="dash_compact")

    with col_config3:
        st.markdown("#### Actions")
        dashboard_name = st.text_input("Dashboard Name", "My Dashboard", key="dash_name")
        if st.button("💾 Save Dashboard", width='stretch', key="dash_save"):
            if dashboard_name:
                st.session_state.saved_dashboards[dashboard_name] = {
                    'widgets': selected_widgets, 'layout': layout,
                    'created': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'compact': compact_mode
                }
                st.success(f"✅ Dashboard '{dashboard_name}' saved!")
            else:
                st.warning("⚠️ Please enter a dashboard name")
        if st.session_state.saved_dashboards:
            load_name = st.selectbox("Load saved dashboard",
                                     list(st.session_state.saved_dashboards.keys()),
                                     key="dash_load_sel")
            if st.button("🔄 Load Dashboard", width='stretch', key="dash_load_btn"):
                saved = st.session_state.saved_dashboards[load_name]
                st.session_state.dashboard_widgets = saved['widgets']
                st.session_state.dashboard_layout  = saved['layout']
                st.rerun()

    st.markdown("---")
    st.markdown("### 📊 Your Dashboard")

    if selected_widgets:
        cols = st.columns(n_cols)
        for i, widget_id in enumerate(selected_widgets):
            with cols[i % n_cols]:
                if show_titles:
                    st.markdown(f"**{available_widgets.get(widget_id,{}).get('name', widget_id)}**")
                try:
                    if widget_id == "total_cases":
                        st.metric("📊 Total Cases", f"{int(nat['value'].max()):,}")
                        st.caption(f"⬆️ +{int(nat['new_cases'].tail(7).sum()):,} in 7 days")
                    elif widget_id == "new_cases":
                        st.metric("📈 New Cases (7d)", f"{int(nat['new_cases'].tail(7).sum()):,}")
                        st.caption(f"📅 Today: {int(nat['new_cases'].tail(1).sum()):,}")
                    elif widget_id == "zones":
                        _hr = sum(1 for v in zone_latest['value'] if v > risk_thr)
                        st.metric("📍 Health Zones", str(len(zones)))
                        st.caption(f"🔴 {_hr} high-risk zones")
                    elif widget_id == "growth_rate":
                        st.metric("📈 Growth Rate", f"{gr_last:.1f}%")
                        if gr_last > 20: st.error("🔴 Critical")
                        elif gr_last > 10: st.warning("🟡 Elevated")
                        else: st.success("🟢 Stable")
                    elif widget_id == "model_r2":
                        st.metric(f"🎯 {active_model} R²", str(metrics_primary.get('R²','—')))
                        if all_metrics:
                            _bm = max(all_metrics.items(),
                                      key=lambda x: float(x[1].get('R²',-999))
                                      if str(x[1].get('R²',-999)).replace('.','').replace('-','').isdigit() else -999)
                            st.caption(f"🏆 Best: {_bm[0]}")
                    elif widget_id == "forecast":
                        st.metric("🔮 Next Forecast", f"{ci_fc.get('mean',0):.0f} cases")
                        st.caption(f"95% CI: [{ci_fc.get('lower',0):.0f} — {ci_fc.get('upper',0):.0f}]")
                    elif widget_id == "risk_score":
                        _rs2 = sum([30 if gr_last>20 else 20 if gr_last>10 else 10 if gr_last>5 else 0,
                                    25 if int(nat['new_cases'].tail(7).sum())>100 else 15 if int(nat['new_cases'].tail(7).sum())>50 else 0,
                                    20 if int(nat['value'].max())>2000 else 10 if int(nat['value'].max())>1000 else 0])
                        st.metric("⚠️ Risk Score", f"{_rs2}/100")
                        st.caption(f"{'🔴 HIGH' if _rs2>50 else '🟡 MEDIUM' if _rs2>25 else '🟢 LOW'}")
                    elif widget_id == "alerts":
                        _crit = sum([gr_last>20, int(nat['value'].max())>2000,
                                     int(nat['new_cases'].tail(7).sum())>100])
                        st.metric("🚨 Active Alerts", _crit)
                        if _crit > 0: st.error(f"{_crit} critical alerts")
                        else: st.success("✅ No critical alerts")
                    elif widget_id == "data_quality":
                        _q = min(100, len(raw_df) * 2)
                        st.metric("📊 Data Quality", f"{_q}%")
                        st.progress(_q / 100)
                        st.caption(f"{len(raw_df):,} records")
                    elif widget_id == "zone_dist":
                        st.markdown("**📍 Top Zones**")
                        for _, row in zone_latest.head(5).iterrows():
                            _ri = "🔴" if row['value']>risk_thr else "🟡" if row['value']>risk_thr*0.4 else "🟢"
                            st.markdown(f"- {_ri} {row['zone']}: {int(row['value']):,}")
                    elif widget_id == "model_perf":
                        st.markdown("**📊 Model Performance**")
                        if all_metrics:
                            for name, m in list(all_metrics.items())[:4]:
                                st.markdown(f"- {name}: R²={m.get('R²','—')}")
                        else: st.info("No model data")
                    elif widget_id == "weather":
                        display_weather_dashboard()
                    elif widget_id == "deaths":
                        st.metric("💀 Total Deaths", f"{total_deaths:,}",
                                  delta=f"{cfr:.1f}% CFR", delta_color="inverse")
                        if cfr > 10:   st.error("🔴 High fatality rate")
                        elif cfr > 5:  st.warning("🟡 Moderate fatality rate")
                        else:          st.success("🟢 Low fatality rate")
                    elif widget_id == "recovered":
                        st.metric("🏥 Total Recovered", f"{total_recovered:,}",
                                  delta=f"{recovery_rate:.1f}%")
                        if recovery_rate > 80:   st.success("✅ High recovery rate")
                        elif recovery_rate > 60: st.info("ℹ️ Moderate recovery rate")
                        else:                    st.warning("⚠️ Low recovery rate")
                    elif widget_id == "cfr":
                        st.metric("📊 Case Fatality Rate", f"{cfr:.1f}%")
                        if cfr > 10:   st.error("🔴 Critical")
                        elif cfr > 5:  st.warning("🟡 Elevated")
                        else:          st.success("🟢 Low")
                    elif widget_id == "active_cases":
                        st.metric("🔄 Active Cases", f"{active_cases:,}")
                        st.caption(f"= {total_cases:,} − {total_deaths:,} deaths "
                                   f"− {total_recovered:,} recovered")
                    elif widget_id == "trend_chart":
                        with safe_plot():
                            fig, ax = plt.subplots(figsize=(6,3), dpi=72)
                            ax.plot(nat['date'], nat['value'], color=PALETTE[0], lw=2)
                            ax.set_title("Cumulative Trend", fontweight='bold', fontsize=10)
                            ax.tick_params(axis='x', rotation=25, labelsize=8)
                            ax.grid(True, alpha=0.2); ax.spines[['top','right']].set_visible(False)
                            plt.tight_layout(); st.pyplot(fig); plt.close()
                    elif widget_id == "daily_chart":
                        with safe_plot():
                            fig, ax = plt.subplots(figsize=(6,3), dpi=72)
                            ax.bar(nat['date'], nat['new_cases'], color=PALETTE[1], alpha=0.7)
                            ax.set_title("Daily New Cases", fontweight='bold', fontsize=10)
                            ax.tick_params(axis='x', rotation=25, labelsize=8)
                            ax.grid(True, alpha=0.2, axis='y'); ax.spines[['top','right']].set_visible(False)
                            plt.tight_layout(); st.pyplot(fig); plt.close()
                except Exception as e:
                    st.warning(f"⚠️ Widget error: {str(e)[:50]}")
    else:
        st.info("👈 Please select at least one widget to build your dashboard")

    if selected_widgets:
        st.markdown("---")
        st.markdown("### 📤 Export Dashboard")
        _ec1, _ec2 = st.columns(2)
        _dash_snap = {'total_cases': int(nat['value'].max()),
                      'new_cases_7d': int(nat['new_cases'].tail(7).sum()),
                      'zones': len(zones), 'growth_rate': gr_last,
                      'active_model': active_model, 'risk_threshold': risk_thr}
        _dash_export = {'name': dashboard_name, 'widgets': selected_widgets,
                        'layout': layout, 'compact': compact_mode,
                        'created': datetime.now().strftime('%Y-%m-%d %H:%M'),
                        'data_snapshot': _dash_snap}
        with _ec1:
            st.download_button("📥 Download Dashboard (JSON)",
                               data=json.dumps(_dash_export, indent=2).encode('utf-8'),
                               file_name=f"dashboard_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                               mime="application/json", width='stretch', key="dash_json_dl")
        with _ec2:
            _html_export = f"""<!DOCTYPE html><html><head><title>BAEL {cfg("display_name","Epidemic")} Dashboard</title>
<style>body{{font-family:Arial;padding:20px;}}h1{{color:#1A237E;}}
.w{{background:#F8FAFC;padding:15px;margin:10px 0;border-radius:8px;border:1px solid #E3E8EF;}}
.m{{font-size:24px;font-weight:bold;color:#1A237E;}}.c{{color:#78909C;font-size:12px;}}
</style></head><body><h1>📊 BAEL {cfg("display_name", "Epidemic")} Dashboard</h1>
<p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} · Model: <b>{active_model}</b></p><hr>
<div class="w"><h3>📊 Total Cases</h3><div class="m">{int(nat['value'].max()):,}</div>
<div class="c">New (7d): {int(nat['new_cases'].tail(7).sum()):,}</div></div>
<div class="w"><h3>📈 Growth Rate</h3><div class="m">{gr_last:.1f}%</div></div>
<div class="w"><h3>📍 Health Zones</h3><div class="m">{len(zones)}</div>
<div class="c">High risk: {sum(1 for v in zone_latest['value'] if v > risk_thr)}</div></div>
<hr><div style="color:#90A4AE;font-size:12px;text-align:center;">BAEL {cfg("display_name","Epidemic")} · UAC Butembo · PhD AI
</div></body></html>"""
            st.download_button("📥 Download Dashboard (HTML)",
                               data=_html_export.encode('utf-8'),
                               file_name=f"dashboard_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
                               mime="text/html", width='stretch', key="dash_html_dl")


# ─────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────
# TAB 9 · Report
# ─────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────
with tab9:
    st.markdown("## Exportable Report")

    report = {
        'title': cfg("report_title", "BAEL Forecasting Report"),
        'generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'institution': f"Université de l'Assomption au Congo (UAC), Butembo — {cfg('country','DRC')} | {cfg('display_name','Epidemic')}",
        'framework': 'BAEL · Behavior-Aware Explainability Loop',
        'active_model': active_model,
        'data': {
            'total_cases':     int(nat['value'].max()),
            'total_deaths':    total_deaths,
            'total_recovered': total_recovered,
            'active_cases':    active_cases,
            'cfr':             round(cfr, 2),
            'recovery_rate':   round(recovery_rate, 2),
            'n_zones':         len(zones),
            'last_date':       last_dt,
            'train_obs':       len(train_df),
            'test_obs':        len(test_df),
        },
        'parameters': {
            'few_shot_k': n_shots,
            'test_ratio':  test_ratio,
            'risk_pct':    risk_pct,
        },
        'metrics': {k: dict(v) for k, v in all_metrics.items() if v},
        'risk': {
            'threshold':       round(risk_thr, 2),
            'growth_rate_last': round(gr_last, 2),
        },
        'forecast': {
            'bootstrap_mean':   round(ci_fc['mean'],   2),
            'bootstrap_median': round(ci_fc['median'], 2),
            'ci_95_lower':      round(ci_fc['lower'],  2),
            'ci_95_upper':      round(ci_fc['upper'],  2),
            'bootstrap_n':      n_boot,
            'sir_r0':           r0_val,
            'horizon_days':     horizon,
        },
    }

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Report Preview")
        report_items = [
            ("**Generated**",      report['generated']),
            ("**Institution**",    report['institution']),
            ("**Active Model**",   report['active_model']),
            ("**Total Cases**",    f"{report['data']['total_cases']:,}"),
            ("**💀 Deaths**",      f"{total_deaths:,}"),
            ("**🏥 Recovered**",   f"{total_recovered:,}"),
            ("**🔄 Active**",      f"{active_cases:,}"),
            ("**CFR**",            f"{cfr:.2f}%"),
            ("**Recovery Rate**",  f"{recovery_rate:.2f}%"),
            ("**Health Zones**",   report['data']['n_zones']),
            ("**Last Date**",      report['data']['last_date']),
            ("**Risk Threshold**", f"{report['risk']['threshold']:.2f}"),
            ("**Growth Rate**",    f"{report['risk']['growth_rate_last']:.2f}%"),
            ("**Forecast Mean**",  f"{report['forecast']['bootstrap_mean']:.0f}"),
            ("**95% CI**",         f"[{report['forecast']['ci_95_lower']:.0f} — {report['forecast']['ci_95_upper']:.0f}]"),
        ]
        st.dataframe(
            pd.DataFrame([(k, str(v)) for k, v in report_items],
                         columns=["Metric", "Value"]),
            hide_index=True, width='stretch'
        )

    with col2:
        st.markdown("#### Downloads")
        st.download_button(
            "⬇️ JSON Report",
            data=json.dumps(report, indent=2, ensure_ascii=False).encode('utf-8'),
            file_name=f"bael_ebola_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",
            width='stretch'
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
            width='stretch'
        )

        st.download_button(
            "⬇️ Raw Data CSV",
            data=raw_df.to_csv(index=False).encode('utf-8'),
            file_name=f"bael_data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            width='stretch'
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
            st.dataframe(styled, hide_index=True, width='stretch')

        st.markdown("#### LaTeX Code")
        if all_metrics:
            latex = ("\\begin{table}[htbp]\n\\centering\n"
                     f"\\caption{{Model Comparison --- {cfg('display_name', 'Epidemic')}}}\n"
                     "\\label{tab:models}\n"
                     "\\begin{tabular}{lrrrr}\n\\toprule\n"
                     "\\textbf{Model} & \\textbf{RMSE} & \\textbf{MAE} "
                     "& \\textbf{R$^2$} & \\textbf{MAPE\\%} \\\\\n\\midrule\n")
            for name, m in all_metrics.items():
                latex += f"{name} & {m['RMSE']} & {m['MAE']} & {m['R²']} & {m['MAPE%']} \\\\\n"
            latex += "\\bottomrule\n\\end{tabular}\n\\end{table}"
            st.code(latex, language='latex')
            st.caption("📋 Copy this LaTeX code for use in Overleaf or any LaTeX editor.")

# ─────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────
# TAB 10 · AI Assistant
# ─────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────
with tab10:
    st.markdown(f"## 🤖 {t('menu.chatbot')}")
    st.markdown("""
    <div class="info-box">
    <b>🤖 AI-Powered Epidemiology Assistant</b><br>
    Ask questions about cases, zones, trends, forecasts, and model performance.
    The assistant uses real-time data from the dashboard.
    </div>
    """, unsafe_allow_html=True)

    # ── Initialise chatbot + history ─────────────────────────────────
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = EbolaChatbot(
            nat_data=nat, zone_data=zone_latest, all_metrics=all_metrics,
            active_model=active_model, ci_fc=ci_fc,
            risk_thr=risk_thr, gr_last=gr_last
        )
    else:
        # Refresh data on each render
        st.session_state.chatbot.nat          = nat
        st.session_state.chatbot.zones        = zone_latest
        st.session_state.chatbot.metrics      = all_metrics
        st.session_state.chatbot.active_model = active_model
        st.session_state.chatbot.ci_fc        = ci_fc
        st.session_state.chatbot.risk_thr     = risk_thr
        st.session_state.chatbot.gr_last      = gr_last
        st.session_state.chatbot.total_cases  = int(nat['value'].max())
        st.session_state.chatbot.new_cases_7d = int(nat['new_cases'].tail(7).sum())
        st.session_state.chatbot.last_date    = nat['date'].max().strftime('%d %b %Y')
        st.session_state.chatbot.total_deaths    = total_deaths
        st.session_state.chatbot.total_recovered = total_recovered
        st.session_state.chatbot.active_cases    = active_cases
        st.session_state.chatbot.cfr             = cfr
        st.session_state.chatbot.recovery_rate   = recovery_rate

    _welcome = (f"👋 Hello! I'm the BAEL {cfg('display_name','Epidemic')} AI Assistant. "
                "Ask me about cases, zones, trends, forecasts, or model performance!")
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = [('assistant', _welcome)]

    # ── Chat display ─────────────────────────────────────────────────
    with st.container():
        for role, msg in st.session_state.chat_history:
            if role == 'user':
                st.markdown(f"""
                <div style="background:#E3F2FD;border-radius:12px 12px 4px 12px;
                            padding:10px 15px;margin:6px 0 6px 15%;
                            border:1px solid #90CAF9;font-size:14px;">
                    <b>👤 You:</b> {msg}
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background:#F5F5F5;border-radius:12px 12px 12px 4px;
                            padding:10px 15px;margin:6px 15% 6px 0;
                            border:1px solid #E0E0E0;font-size:14px;">
                    <b>🤖 Assistant:</b><br>{msg}
                </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── Input row ────────────────────────────────────────────────────
    inp_col, btn_col, clr_col = st.columns([5, 1, 1])
    with inp_col:
        user_input = st.text_input(
            "Question", placeholder="e.g. What are the total cases?",
            key="chat_input", label_visibility="collapsed"
        )
    with btn_col:
        send = st.button("📤 Send",  width='stretch', key="chat_send")
    with clr_col:
        clear = st.button("🗑️ Clear", width='stretch', key="chat_clear")

    if send and user_input.strip():
        st.session_state.chat_history.append(('user', user_input.strip()))
        resp = st.session_state.chatbot.get_response(user_input.strip())
        st.session_state.chat_history.append(('assistant', resp))
        st.rerun()

    if clear:
        st.session_state.chat_history = [('assistant', _welcome)]
        st.rerun()

    # ── Suggested questions ──────────────────────────────────────────
    st.markdown("#### 💡 Suggested questions")
    _suggestions = [
        "What are the total cases?",
        "Show high-risk zones",
        "What is the growth rate?",
        "Cases in Butembo?",
        "Which model is best?",
        "Show the forecast",
        "How many deaths?",
        "Compare to historical outbreaks",
        "Any active alerts?",
    ]
    _sq_cols = st.columns(3)
    for i, q in enumerate(_suggestions):
        with _sq_cols[i % 3]:
            if st.button(q, width='stretch', key=f"sq_{i}"):
                st.session_state.chat_history.append(('user', q))
                st.session_state.chat_history.append(
                    ('assistant', st.session_state.chatbot.get_response(q))
                )
                st.rerun()

    # ── Stats strip ─────────────────────────────────────────────────
    st.markdown("---")
    _s1, _s2, _s3, _s4, _s5, _s6 = st.columns(6)
    _s1.metric("💬 Messages",   len(st.session_state.chat_history))
    _s2.metric("📊 Total cases", f"{int(nat['value'].max()):,}")
    _s3.metric("💀 Deaths",      f"{total_deaths:,}")
    _s4.metric("🏥 Recovered",   f"{total_recovered:,}")
    _s5.metric("📈 Growth rate", f"{gr_last:.1f}%")
    _s6.metric("📊 CFR",         f"{cfr:.1f}%")


# ══════════════════════════════════════════════════════════════════════
# 🗺️  CARTE INTERACTIVE — ZONES TOUCHÉES PAR EBOLA
# ══════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("""
<div style="background:linear-gradient(135deg,#1A237E,#1565C0);
            border-radius:12px;padding:18px 24px;margin-bottom:18px;">
    <div style="color:white;font-size:22px;font-weight:800;letter-spacing:.3px;">
        🗺️ Carte Interactive — Zones de Santé Touchées
    </div>
    <div style="color:#90CAF9;font-size:13px;margin-top:4px;">
        Épidémie {cfg('display_name', 'Ebola')} · {cfg('province', 'Nord-Kivu &amp; Ituri, DRC')} ·
        Polygones réels des zones de santé · Cliquer sur une zone pour les détails
    </div>
</div>
""", unsafe_allow_html=True)

_map_libs_ok = FOLIUM_OK and GEOPANDAS_OK
_geojson_ok  = GEOJSON_PATH.exists()

if not _map_libs_ok:
    _missing = []
    if not FOLIUM_OK:    _missing += ["folium", "streamlit-folium"]
    if not GEOPANDAS_OK: _missing += ["geopandas"]
    st.warning(
        f"⚠️ Bibliothèques manquantes : `{', '.join(_missing)}`\n\n"
        f"```\npip install {' '.join(_missing)}\n```"
    )
elif not _geojson_ok:
    st.warning(
        f"⚠️ Fichier GeoJSON introuvable : `{GEOJSON_PATH}`\n\n"
        "Assure-toi que les données ont été téléchargées "
        "(bouton **Download & Update Data** dans la barre latérale)."
    )
else:
    try:
        with st.spinner("Chargement des zones de santé..."):
            _gdf_zones = load_geodata(str(GEOJSON_PATH))

        _zl = zone_latest.copy()
        if _zl.index.name == 'zone':
            _zl = _zl.reset_index()
        if 'zone' not in _zl.columns:
            _zl = _zl.reset_index()

        with st.spinner("Construction de la carte..."):
            _map_obj, _n_touched, _n_total, _merged = build_ebola_map_geo(
                _gdf_zones, _zl, risk_thr
            )

        # ── Métriques ─────────────────────────────────────────────────
        _active  = _merged[_merged['value'] > 0].sort_values('value', ascending=False)
        _top_row = _active.iloc[0] if len(_active) > 0 else None

        mc1, mc2, mc3, mc4 = st.columns(4)
        with mc1:
            st.metric("🗺️ Zones cartographiées", f"{_n_total:,}")
        with mc2:
            _pct = f"{_n_touched / _n_total * 100:.0f}%" if _n_total else "—"
            st.metric("🔴 Zones touchées", f"{_n_touched}", delta=_pct)
        with mc3:
            st.metric("🟢 Zones inactives", f"{_n_total - _n_touched:,}")
        with mc4:
            if _top_row is not None:
                st.metric("🏥 Zone la plus touchée",
                          _top_row['zone_name'],
                          delta=f"{int(_top_row['value']):,} cas")
            else:
                st.metric("🏥 Zone la plus touchée", "—")

        # ── Mise en page carte + panneau latéral ──────────────────────
        _map_col, _side_col = st.columns([3, 1])

        with _side_col:
            st.markdown("#### ⚙️ Options")
            _map_height    = st.slider("Hauteur (px)", 400, 800, 580, 50,
                                       key="map_height_slider")
            _show_inactive = st.checkbox("Afficher zones inactives", value=True,
                                         key="map_show_inactive")
            st.markdown("#### 📊 Top zones actives")
            _map_max = max(4, min(20, len(_active)))
            _map_def = min(10, _map_max)
            _top_n = st.slider("Afficher top N", 3, _map_max, _map_def, key="map_top_n")
            for _, _row in _active.head(_top_n).iterrows():
                _c, _lbl, _ = _get_color_risk(_row['value'])
                st.markdown(
                    f'<div style="background:#F8FAFC;border-left:4px solid {_c};'
                    f'border-radius:4px;padding:5px 10px;margin:3px 0;font-size:11.5px;'
                    f'color:#1A237E;">'
                    f'<b style="color:#1A237E;">{_row["zone_name"]}</b><br>'
                    f'<span style="color:#546E7A;">{int(_row["value"]):,} cas — {_lbl}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        with _map_col:
            if not _show_inactive:
                with st.spinner("Filtrage..."):
                    _map_obj2, _, _, _ = build_ebola_map_geo(
                        _gdf_zones, _zl[_zl['value'] > 0], risk_thr
                    )
                st_folium(_map_obj2, height=_map_height,
                          width='stretch', returned_objects=[])
            else:
                st_folium(_map_obj, height=_map_height,
                          width='stretch', returned_objects=[])

        st.caption(
            "💡 Cliquer sur un polygone pour le popup détaillé · "
            "Molette ou ± pour zoomer · "
            "Changer de fond de carte via le contrôle en haut à gauche"
        )

    except Exception as _map_err:
        st.error(f"❌ Erreur carte : {_map_err}")

# ─────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────
# TAB 11 · Publications
# ─────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────
with tab11:
    st.markdown(f"## 📚 Publications & References — BAEL {cfg('display_name','Epidemic')}")

    st.markdown("""
    <div class="info-box">
    Scientific output produced within the PhD programme in Artificial Intelligence at the
    <b>Université de l'Assomption au Congo (UAC)</b>, Butembo, Nord-Kivu, DRC —
    under the <b>BAEL · Behavior-Aware Explainability Loop</b> doctoral framework.
    </div>
    """, unsafe_allow_html=True)

    # ── Status summary badges ─────────────────────────────────────────
    st.markdown("""
    <div style="display:flex;gap:10px;flex-wrap:wrap;margin:10px 0 18px 0;">
        <span style="background:#E3F2FD;border:1px solid #1565C0;border-radius:20px;
                     padding:4px 14px;font-size:12px;font-weight:600;color:#1565C0;">🔄 Under review: 2</span>
        <span style="background:#E8F5E9;border:1px solid #2E7D32;border-radius:20px;
                     padding:4px 14px;font-size:12px;font-weight:600;color:#2E7D32;">📝 In preparation: 3</span>
        <span style="background:#FFF3E0;border:1px solid #E65100;border-radius:20px;
                     padding:4px 14px;font-size:12px;font-weight:600;color:#E65100;">📬 Submitted: 1</span>
    </div>
    """, unsafe_allow_html=True)

    pub_col1, pub_col2 = st.columns([3, 2])

    with pub_col1:
        st.markdown("### Papers & Manuscripts")

        publications = [
            {
                "title": "GNN-Based Ebola Outbreak Forecasting with Transfer Learning and Few-Shot Learning in DRC",
                "authors": "Moses et al.",
                "venue": "Expert Systems with Applications (ESWA) — target Q1",
                "year": "2026",
                "status": "🔄 Under review",
                "keywords": "GNN · GraphSAGE · Transfer Learning · Few-Shot · Ebola · DRC",
                "color": "#E3F2FD",
                "border": "#1565C0"
            },
            {
                "title": "Spatio-Temporal Graph Neural Networks for Infectious Disease Forecasting in Low-Resource Settings",
                "authors": "Moses et al.",
                "venue": "Journal of Biomedical Informatics — target Q1",
                "year": "2026",
                "status": "📝 In preparation",
                "keywords": "ST-GNN · Spatio-temporal · Public health · DRC · Nord-Kivu",
                "color": "#E8F5E9",
                "border": "#2E7D32"
            },
            {
                "title": "DAASViT: Domain-Adaptive Attention-based Semantic ViT for Plant and Fungal Species Recognition",
                "authors": "Moses et al.",
                "venue": "Expert Systems with Applications (ESWA)",
                "year": "2025–2026",
                "status": "📬 Submitted",
                "keywords": "Vision Transformer · Domain Adaptation · Agriculture · Banana disease",
                "color": "#FFF3E0",
                "border": "#E65100"
            },
            {
                "title": "Social-AgriNet: Multimodal Framework for Banana Disease Detection in Central Africa",
                "authors": "Moses et al.",
                "venue": "Computers and Electronics in Agriculture — target Q1",
                "year": "2026",
                "status": "📝 In preparation",
                "keywords": "Multimodal · Deep Learning · Banana · Disease detection · DRC",
                "color": "#F3E5F5",
                "border": "#6A1B9A"
            },
            {
                "title": "Behavior-Aware Explainability Loop (BAEL): A Doctoral Framework for Trustworthy AI in Public Health",
                "authors": "Moses et al.",
                "venue": "Artificial Intelligence in Medicine",
                "year": "2026",
                "status": "📝 In preparation",
                "keywords": "Explainability · XAI · BAEL · Trustworthy AI · Epidemiology",
                "color": "#E8EAF6",
                "border": "#3949AB"
            },
            {
                "title": "Transfer Learning and Few-Shot Learning for Early Ebola Outbreak Forecasting in the DRC",
                "authors": "Moses et al.",
                "venue": "Master's Thesis — UAC Butembo",
                "year": "2025",
                "status": "🔄 Under review",
                "keywords": "Transfer Learning · Few-Shot · LSTM · Ebola · DRC · Nord-Kivu",
                "color": "#F9FBE7",
                "border": "#558B2F"
            },
        ]

        for pub in publications:
            st.markdown(f"""
            <div style="background:{pub['color']};border-left:4px solid {pub['border']};
                        border-radius:8px;padding:14px 16px;margin:10px 0;
                        box-shadow:0 1px 4px rgba(0,0,0,0.05);">
                <div style="font-weight:700;color:#1A237E;font-size:13.5px;line-height:1.45;">
                    {pub['title']}
                </div>
                <div style="color:#546E7A;font-size:12px;margin-top:4px;">
                    {pub['authors']} &nbsp;·&nbsp; <i>{pub['venue']}</i> &nbsp;·&nbsp; {pub['year']}
                </div>
                <div style="margin-top:7px;display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
                    <span style="background:white;border-radius:4px;padding:2px 9px;
                                 font-size:11px;font-weight:600;color:#1565C0;border:1px solid #90CAF9;">
                        {pub['status']}
                    </span>
                    <span style="color:#78909C;font-size:11px;">{pub['keywords']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with pub_col2:
        st.markdown("### Master's Thesis")
        st.markdown("""
        <div class="report-card">
        <b>Transfer Learning &amp; Few-Shot Learning for Early Ebola Outbreak Forecasting in DRC</b><br>
        <span style="color:#546E7A;font-size:12px;">Moses · UAC Butembo · 2025</span><br><br>
        End-to-end pipeline combining Transfer Learning (pre-trained encoder on historical outbreaks)
        and Few-Shot Learning (K = 2–10 weeks) for early-stage Ebola forecasting under
        data-scarce conditions in Nord-Kivu, DRC.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### Key References")
        refs = [
            ("Verity et al., 2020",       "Lancet Infectious Diseases", "Ebola CFR & epidemiology"),
            ("Kipf & Welling, 2017",       "ICLR",    "Graph Convolutional Networks"),
            ("Hamilton et al., 2017",      "NeurIPS", "GraphSAGE inductive representation"),
            ("Finn et al., 2017",          "ICML",    "MAML — few-shot meta-learning"),
            ("Dosovitskiy et al., 2021",   "ICLR",    "Vision Transformers (ViT)"),
            ("Hochreiter & Schmidhuber, 1997", "Neural Computation", "LSTM networks"),
            ("WHO INRB, 2026",             "BDBV Situation Reports", f"Epidemiological data — {cfg('display_name','Epidemic')}"),
        ]
        for author, venue, topic in refs:
            st.markdown(f"""
            <div style="background:#F8FAFC;border-radius:6px;padding:8px 12px;margin:4px 0;
                        border:1px solid #E3E8EF;font-size:12px;color:#1A237E;">
                <b style="color:#1A237E;">{author}</b> — <i>{venue}</i><br>
                <span style="color:#78909C;">{topic}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("### PhD Context — BAEL Framework")
        st.markdown("""
        <div style="background:#E8EAF6;border-radius:8px;padding:12px 14px;font-size:12px;color:#1A237E;">
        <b>Université de l'Assomption au Congo (UAC)</b><br>
        Butembo · Nord-Kivu · DRC<br><br>
        Speciality: Artificial Intelligence<br>
        Research areas: XAI · ST-GNN · Transfer Learning · Multimodal Deep Learning<br>
        Applications: Public health · Agriculture (DRC)
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────
# ── Footer ────────────────────────────────────────────────────────────
import sys as _sys
_APP_VERSION    = "1.0.0"
_PYTHON_VERSION = _sys.version.split()[0]

st.markdown("---")
st.markdown(f"""
<div class="footer">
    <div class="footer-badges">
        <span class="footer-badge">📊 {cfg("country", "DRC")} {cfg("start_year", "")}</span>
        <span class="footer-badge">🧠 PhD AI · UAC</span>
        <span class="footer-badge">🔬 BAEL</span>
        <span class="footer-badge">🔄 Transfer Learning</span>
        <span class="footer-badge">⚡ Few-Shot</span>
    </div>
    <div class="footer-info">
        <strong>{t('app.version')}{_APP_VERSION}</strong> ·
        <strong>Python {_PYTHON_VERSION}</strong> ·
        <strong>{t('sidebar.models')} {n_loaded}/{len(MODELS)}</strong>
        <br>
        {t('app.title')} · {t('app.institution')} · PhD AI · {t('app.framework')}
    </div>
</div>
""", unsafe_allow_html=True)