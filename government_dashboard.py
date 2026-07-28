# government_dashboard.py - Dashboard pour le Ministère de la Santé

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="BAEL-Ebola · Gouvernement", layout="wide")

st.title("🦠 Tableau de Bord Épidémiologique - RDC")
st.markdown("### Ministère de la Santé Publique, Hygiène et Prévention")

# KPIs Nationaux
col1, col2, col3, col4 = st.columns(4)
col1.metric("Cas Actifs", "1,247", "↓ 12%")
col2.metric("Zones à Risque", "8", "↑ 2")
col3.metric("Taux de Reproduction (R₀)", "1.42", "↑ 0.15")
col4.metric("Lits Disponibles", "342", "↓ 18%")

# Carte des zones à risque
st.subheader("🗺️ Carte des Zones de Santé")
risk_map = create_risk_map()
st.plotly_chart(risk_map, use_container_width=True)

# Tendances par zone
st.subheader("📈 Tendances par Zone de Santé")
zone_data = load_zone_data()
fig = px.line(zone_data, x='date', y='cases', color='zone',
              title="Évolution des Cas par Zone")
st.plotly_chart(fig, use_container_width=True)

# Rapport de synthèse
st.subheader("📋 Rapport de Synthèse")
col1, col2 = st.columns(2)
with col1:
    st.markdown("#### 🔴 Zones Critiques")
    st.dataframe(get_critical_zones())
with col2:
    st.markdown("#### 🟡 Actions Recommandées")
    st.dataframe(get_recommended_actions())