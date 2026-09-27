import streamlit as st
import pandas as pd

st.set_page_config(page_title="Mon Portefeuille", page_icon="💼", layout="wide")

st.title("💼 Mon Portefeuille BRVM")
st.caption("Données de clôture du 18 septembre 2026 (source : BRVM)")

# === Ton portefeuille ===
data = {
    "Ticker": ["ABJC", "BOAB", "ETIT", "SNTS"],
    "Nom": [
        "Servair Abidjan CI",
        "Bank of Africa Bénin",
        "Ecobank Transnational Inc.",
        "Sonatel"
    ],
    "Quantité": [10, 3, 30, 5],
    "Cours (FCFA)": [3930, 9850, 70, 42190],
    "Variation jour": ["-2,96%", "-2,48%", "0,00%", "+7,49%"]
}

df = pd.DataFrame(data)
df["Valorisation (FCFA)"] = df["Quantité"] * df["Cours (FCFA)"]

# Affichage
col1, col2, col3 = st.columns(3)
total_valeur = df["Valorisation (FCFA)"].sum()

col1.metric("Valeur totale du portefeuille", f"{total_valeur:,.0f} FCFA".replace(",", " "))
col2.metric("Nombre de lignes", len(df))
col3.metric("Nombre total d'actions", df["Quantité"].sum())

st.subheader("Détail des positions")
st.dataframe(
    df.style.format({
        "Cours (FCFA)": "{:,.0f}",
        "Valorisation (FCFA)": "{:,.0f}"
    }),
    width="stretch",
    hide_index=True
)

st.info("Prochaine étape : automatiser la récupération des cours tous les jours + calcul du P&L.")
st.warning("⚠️ Outil d'aide à la décision uniquement. Ne constitue pas un conseil en investissement.")