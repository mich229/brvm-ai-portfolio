import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import json
import os
from datetime import datetime
sys.path.append(".")
from data.collector import get_brvm_prices

st.set_page_config(page_title="Mon Portefeuille", page_icon="💼", layout="wide")
st.title("💼 Mon Portefeuille BRVM")

HISTORY_FILE = "data/portfolio_history.json"
PORTFOLIO_FILE = "data/portfolio.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_history(history):
    os.makedirs("data", exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        try:
            with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    # Valeurs par défaut
    return [
        {"Ticker": "ABJC", "Nom": "Servair Abidjan CI", "Quantité": 10, "Prix_achat": 3200.0},
        {"Ticker": "BOAB", "Nom": "Bank of Africa Bénin", "Quantité": 3, "Prix_achat": 8500.0},
        {"Ticker": "ETIT", "Nom": "Ecobank Transnational Inc.", "Quantité": 30, "Prix_achat": 40.0},
        {"Ticker": "SNTS", "Nom": "Sonatel", "Quantité": 5, "Prix_achat": 30000.0},
    ]

def save_portfolio(portfolio):
    os.makedirs("data", exist_ok=True)
    with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f:
        json.dump(portfolio, f, ensure_ascii=False, indent=2)

# === Chargement du portefeuille (persistant) ===
if "portfolio" not in st.session_state:
    st.session_state.portfolio = load_portfolio()

# === Récupération des cours ===
with st.spinner("Récupération des cours BRVM..."):
    prices, date_str, source = get_brvm_prices([p["Ticker"] for p in st.session_state.portfolio])

if source == "live":
    st.caption(f"Dernière mise à jour : {date_str} • Source : **Direct BRVM**")
elif source == "cache":
    st.caption(f"Dernière mise à jour : {date_str} • Source : **Cache local**")
else:
    st.caption(f"Dernière mise à jour : {date_str} • Source : **Fallback**")

# === Édition du portefeuille ===
st.subheader("Modifier mon portefeuille")
edited_df = st.data_editor(
    pd.DataFrame(st.session_state.portfolio),
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Ticker": st.column_config.TextColumn("Ticker", required=True),
        "Nom": st.column_config.TextColumn("Nom"),
        "Quantité": st.column_config.NumberColumn("Quantité", min_value=0, step=1),
        "Prix_achat": st.column_config.NumberColumn("Prix d'achat (FCFA)", min_value=0, format="%.0f"),
    },
    key="portfolio_editor"
)

if st.button("💾 Enregistrer les modifications"):
    st.session_state.portfolio = edited_df.to_dict("records")
    save_portfolio(st.session_state.portfolio)
    st.success("Portefeuille sauvegardé de façon permanente !")
    st.rerun()

# === Calculs ===
rows = []
for p in st.session_state.portfolio:
    ticker = p["Ticker"]
    price_info = prices.get(ticker, {"price": 0, "change": "N/A"})
    cours = price_info["price"] or 0
    quantite = p["Quantité"]
    prix_achat = p.get("Prix_achat", 0)
    valorisation = quantite * cours
    cout = quantite * prix_achat
    pnl = valorisation - cout
    pnl_pct = (pnl / cout * 100) if cout > 0 else 0

    rows.append({
        "Ticker": ticker,
        "Nom": p["Nom"],
        "Quantité": quantite,
        "Prix d'achat": prix_achat,
        "Cours actuel": cours,
        "Variation jour": price_info["change"],
        "Valorisation": valorisation,
        "P&L (FCFA)": pnl,
        "P&L (%)": pnl_pct
    })

df = pd.DataFrame(rows)
total_val = df["Valorisation"].sum()
total_cout = (df["Quantité"] * df["Prix d'achat"]).sum()
total_pnl = total_val - total_cout
total_pnl_pct = (total_pnl / total_cout * 100) if total_cout > 0 else 0

# === Enregistrement dans l'historique ===
history = load_history()
today = datetime.now().strftime("%Y-%m-%d")
existing = next((h for h in history if h["date"] == today), None)
if existing:
    existing["valeur"] = total_val
else:
    history.append({"date": today, "valeur": total_val})
save_history(history)

# === Métriques ===
c1, c2, c3, c4 = st.columns(4)
c1.metric("Valeur totale", f"{total_val:,.0f} FCFA".replace(",", " "))
c2.metric("Coût d'acquisition", f"{total_cout:,.0f} FCFA".replace(",", " "))
c3.metric("P&L total", f"{total_pnl:,.0f} FCFA".replace(",", " "), delta=f"{total_pnl_pct:.1f}%")
c4.metric("Nombre d'actions", int(df["Quantité"].sum()))

st.subheader("Détail des positions")
st.dataframe(
    df.style.format({
        "Prix d'achat": "{:,.0f}",
        "Cours actuel": "{:,.0f}",
        "Valorisation": "{:,.0f}",
        "P&L (FCFA)": "{:,.0f}",
        "P&L (%)": "{:.1f}%"
    }),
    use_container_width=True,
    hide_index=True
)

# === Graphiques ===
col_a, col_b = st.columns(2)

with col_a:
    if total_val > 0:
        st.subheader("Allocation du portefeuille")
        fig_pie = px.pie(df, values="Valorisation", names="Ticker", title="Répartition par titre")
        st.plotly_chart(fig_pie, use_container_width=True)

with col_b:
    st.subheader("Évolution de la valorisation")
    history = load_history()
    
    if len(history) >= 1:
        hist_df = pd.DataFrame(history)
        hist_df["date"] = pd.to_datetime(hist_df["date"])
        hist_df = hist_df.sort_values("date").drop_duplicates(subset=["date"], keep="last")

        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=hist_df["date"],
            y=hist_df["valeur"],
            mode="lines+markers",
            name="Valeur du portefeuille",
            line=dict(color="#1f77b4", width=3),
            marker=dict(size=8)
        ))
        
        fig_line.update_layout(
            xaxis_title="Date",
            yaxis_title="Valeur (FCFA)",
            height=350,
            margin=dict(l=20, r=20, t=30, b=40),
            xaxis=dict(tickformat="%d/%m/%Y", type="date"),
            yaxis=dict(tickformat=",.0f")
        )
        
        if len(hist_df) == 1:
            fig_line.update_layout(
                xaxis_range=[
                    hist_df["date"].iloc[0] - pd.Timedelta(days=2),
                    hist_df["date"].iloc[0] + pd.Timedelta(days=2)
                ]
            )
            st.caption("Premier point d'historique enregistré. La courbe s'enrichira chaque jour.")
        
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("L'historique commencera à se constituer à partir d'aujourd'hui.")

if st.button("🔄 Actualiser les cours"):
    st.rerun()

st.warning("⚠️ Outil d'aide à la décision uniquement. Ne constitue pas un conseil en investissement.")