import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import json
import os

st.set_page_config(page_title="Dashboard Marché", page_icon="📊", layout="wide")
st.title("📊 Dashboard Marché BRVM")

CACHE_FILE = "data/last_market.json"

def save_market_cache(data):
    os.makedirs("data", exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_market_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return None

@st.cache_data(ttl=180)
def get_market_data():
    url = "https://www.brvm.org/fr"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        text = BeautifulSoup(r.text, "lxml").get_text(separator=" ")

        indices = {}
        for name in ["BRVM-C", "BRVM-30", "BRVM-PRES"]:
            patterns = [
                rf"{name}\s+([\d\s,\.]+)\s+([+-]?\d+[,.]?\d*\s*%?)",
                rf"{name}\s*\|\s*([\d\s,\.]+)\s*\|\s*([+-]?\d+[,.]?\d*%?)"
            ]
            found = False
            for pat in patterns:
                match = re.search(pat, text, re.IGNORECASE)
                if match:
                    value = match.group(1).replace(" ", "").replace(",", ".")
                    change = match.group(2).replace(" ", "")
                    indices[name] = {"value": value, "change": change}
                    found = True
                    break
            if not found:
                indices[name] = {"value": "N/A", "change": ""}

        # Top 5
        top5 = []
        top_section = re.search(r"Top 5.*?Flop 5", text, re.DOTALL | re.IGNORECASE)
        if top_section:
            rows = re.findall(r"([A-Z]{4})\s+([\d\s]{3,})\s+([+-]?\d+[,.]?\d*%?)", top_section.group(0))
            for t, p, c in rows[:5]:
                top5.append({"Ticker": t, "Cours": p.strip(), "Variation": c.strip()})

        # Flop 5
        flop5 = []
        flop_section = re.search(r"Flop 5.*?Activités du marché|Flop 5.*?BRVM-C", text, re.DOTALL | re.IGNORECASE)
        if flop_section:
            rows = re.findall(r"([A-Z]{4})\s+([\d\s]{3,})\s+([+-]?\d+[,.]?\d*%?)", flop_section.group(0))
            for t, p, c in rows[:5]:
                flop5.append({"Ticker": t, "Cours": p.strip(), "Variation": c.strip()})

        # Stats
        trans = re.search(r"Valeur des transactions\s+([\d\s]+)", text)
        cap = re.search(r"Capitalisation Actions\s+([\d\s]+)", text)
        stats = {
            "transactions": trans.group(1).strip() if trans else "N/A",
            "cap_actions": cap.group(1).strip() if cap else "N/A"
        }

        # Si on a de bonnes données, on sauvegarde
        if indices.get("BRVM-C", {}).get("value") != "N/A" or len(top5) > 0:
            cache_data = {
                "indices": indices,
                "top5": top5,
                "flop5": flop5,
                "stats": stats,
                "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "source": "live"
            }
            save_market_cache(cache_data)
            return indices, top5, flop5, stats, cache_data["date"], "live"

        raise Exception("Données insuffisantes")

    except Exception as e:
        cache = load_market_cache()
        if cache:
            return (
                cache.get("indices", {}),
                cache.get("top5", []),
                cache.get("flop5", []),
                cache.get("stats", {}),
                cache.get("date", "Cache"),
                "cache"
            )

        # Fallback hardcodé
        indices = {
            "BRVM-C": {"value": "553.71", "change": "+1.03%"},
            "BRVM-30": {"value": "268.91", "change": "+1.36%"},
            "BRVM-PRES": {"value": "203.01", "change": "+1.80%"}
        }
        top5 = [
            {"Ticker": "SNTS", "Cours": "42 190", "Variation": "+7,49%"},
            {"Ticker": "TTLS", "Cours": "3 950", "Variation": "+3,95%"},
            {"Ticker": "SAFC", "Cours": "4 980", "Variation": "+3,00%"},
            {"Ticker": "SGBC", "Cours": "38 900", "Variation": "+2,37%"},
            {"Ticker": "BICC", "Cours": "31 675", "Variation": "+1,36%"},
        ]
        flop5 = [
            {"Ticker": "SDCC", "Cours": "12 485", "Variation": "-7,48%"},
            {"Ticker": "SHEC", "Cours": "2 760", "Variation": "-7,38%"},
            {"Ticker": "STAC", "Cours": "2 275", "Variation": "-6,57%"},
            {"Ticker": "PRSC", "Cours": "4 305", "Variation": "-3,91%"},
            {"Ticker": "TTLC", "Cours": "3 160", "Variation": "-3,36%"},
        ]
        stats = {"transactions": "4 643 339 086", "cap_actions": "21 351 609 922 235"}
        return indices, top5, flop5, stats, "Fallback (18/09/2026)", "fallback"

indices, top5, flop5, stats, date_str, source = get_market_data()

# Affichage de la source
if source == "live":
    st.caption(f"Dernière mise à jour : {date_str} • **Source : Direct BRVM**")
elif source == "cache":
    st.caption(f"Dernière mise à jour : {date_str} • **Source : Cache local**")
else:
    st.caption(f"Dernière mise à jour : {date_str} • **Source : Fallback**")

# Indices
st.subheader("Indices principaux")
c1, c2, c3 = st.columns(3)
for col, name in zip([c1, c2, c3], ["BRVM-C", "BRVM-30", "BRVM-PRES"]):
    data = indices.get(name, {"value": "N/A", "change": ""})
    col.metric(name, data["value"], data["change"])

st.divider()

# Top / Flop
col1, col2 = st.columns(2)
with col1:
    st.subheader("📈 Top 5 du jour")
    if top5:
        st.dataframe(pd.DataFrame(top5), use_container_width=True, hide_index=True)
    else:
        st.info("Top 5 non disponible")

with col2:
    st.subheader("📉 Flop 5 du jour")
    if flop5:
        st.dataframe(pd.DataFrame(flop5), use_container_width=True, hide_index=True)
    else:
        st.info("Flop 5 non disponible")

st.divider()

st.subheader("Activités du marché")
c1, c2 = st.columns(2)
c1.metric("Valeur des transactions", f"{stats.get('transactions', 'N/A')} FCFA")
c2.metric("Capitalisation Actions", f"{stats.get('cap_actions', 'N/A')} FCFA")

st.markdown("[Voir le site officiel BRVM](https://www.brvm.org/fr)")

if st.button("🔄 Actualiser le dashboard"):
    st.cache_data.clear()
    st.rerun()

st.warning("⚠️ Outil d'aide à la décision uniquement. Ne constitue pas un conseil en investissement.")