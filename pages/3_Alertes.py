import streamlit as st
import json
import os
from datetime import datetime
import sys
sys.path.append(".")
from data.collector import get_brvm_prices

st.set_page_config(page_title="Alertes", page_icon="🔔", layout="wide")
st.title("🔔 Gestion des alertes")

ALERTS_FILE = "data/alerts.json"

def load_alerts():
    if os.path.exists(ALERTS_FILE):
        try:
            with open(ALERTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_alerts(alerts):
    os.makedirs("data", exist_ok=True)
    with open(ALERTS_FILE, "w", encoding="utf-8") as f:
        json.dump(alerts, f, ensure_ascii=False, indent=2)

# Chargement
alerts = load_alerts()

# === Formulaire d'ajout ===
st.subheader("Ajouter une alerte")

with st.form("add_alert_form"):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        ticker = st.text_input("Ticker (ex: SNTS)", max_chars=10).upper().strip()
    
    with col2:
        alert_type = st.selectbox(
            "Type d'alerte",
            ["Prix au-dessus de", "Prix en-dessous de", "Variation jour > %"]
        )
    
    with col3:
        threshold = st.number_input("Seuil", min_value=0.0, step=0.1, value=0.0)
    
    submitted = st.form_submit_button("Ajouter l'alerte")
    
    if submitted:
        if not ticker:
            st.error("Le ticker est obligatoire.")
        else:
            new_id = max([a.get("id", 0) for a in alerts], default=0) + 1
            new_alert = {
                "id": new_id,
                "ticker": ticker,
                "type": alert_type,
                "threshold": float(threshold),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "active": True
            }
            alerts.append(new_alert)
            save_alerts(alerts)
            st.success(f"Alerte ajoutée pour {ticker}")
            st.rerun()

# === Liste des alertes ===
st.subheader("Mes alertes")

alerts = load_alerts()

if not alerts:
    st.info("Aucune alerte définie pour le moment.")
else:
    for alert in alerts:
        col1, col2, col3, col4 = st.columns([2, 4, 3, 1])
        with col1:
            st.write(f"**{alert['ticker']}**")
        with col2:
            st.write(f"{alert['type']} **{alert['threshold']}**")
        with col3:
            st.caption(alert.get("created_at", ""))
        with col4:
            if st.button("🗑️", key=f"del_{alert['id']}"):
                alerts = [a for a in alerts if a["id"] != alert["id"]]
                save_alerts(alerts)
                st.rerun()

st.divider()

# === Vérification des alertes ===
st.subheader("🔔 Alertes déclenchées")

tickers_to_check = list(set(a["ticker"] for a in alerts)) if alerts else []

if not tickers_to_check:
    st.info("Ajoutez des alertes pour commencer la surveillance.")
else:
    with st.spinner("Vérification des cours en cours..."):
        prices, date_str, source = get_brvm_prices(tickers_to_check)
    
    triggered = []
    
    for alert in alerts:
        if not alert.get("active", True):
            continue
            
        ticker = alert["ticker"]
        price_info = prices.get(ticker)
        
        if not price_info or price_info.get("price") is None:
            continue
        
        current_price = price_info["price"]
        change_str = str(price_info.get("change", "0")).replace("%", "").replace(",", ".").replace("+", "").strip()
        
        try:
            current_change = float(change_str)
        except:
            current_change = 0.0
        
        if alert["type"] == "Prix au-dessus de" and current_price > alert["threshold"]:
            triggered.append(f"🚨 **{ticker}** est à **{current_price:,.0f} FCFA** (seuil : {alert['threshold']})")
        elif alert["type"] == "Prix en-dessous de" and current_price < alert["threshold"]:
            triggered.append(f"🚨 **{ticker}** est à **{current_price:,.0f} FCFA** (seuil : {alert['threshold']})")
        elif alert["type"] == "Variation jour > %" and abs(current_change) >= alert["threshold"]:
            triggered.append(f"🚨 **{ticker}** a varié de **{current_change}%** (seuil : {alert['threshold']}%)")
    
    if triggered:
        for msg in triggered:
            st.error(msg)
    else:
        st.success("Aucune alerte déclenchée pour le moment.")

st.warning("⚠️ Outil d'aide à la décision uniquement. Ne constitue pas un conseil en investissement.")