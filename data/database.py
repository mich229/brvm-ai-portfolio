import sqlite3
import os
from datetime import datetime

DB_PATH = "data/brvm_portfolio.db"

def get_connection():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Table portefeuille
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            nom TEXT,
            quantite REAL NOT NULL,
            prix_achat REAL NOT NULL,
            updated_at TEXT
        )
    """)

    # Table historique de valorisation
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,
            valeur REAL NOT NULL
        )
    """)

    # Table alertes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            type TEXT NOT NULL,
            threshold REAL NOT NULL,
            created_at TEXT,
            active INTEGER DEFAULT 1
        )
    """)

    conn.commit()
    conn.close()

# ========== PORTEFEUILLE ==========

def load_portfolio():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ticker, nom, quantite, prix_achat FROM portfolio")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        # Données par défaut
        default = [
            ("ABJC", "Servair Abidjan CI", 10, 3200.0),
            ("BOAB", "Bank of Africa Bénin", 3, 8500.0),
            ("ETIT", "Ecobank Transnational Inc.", 30, 40.0),
            ("SNTS", "Sonatel", 5, 30000.0),
        ]
        save_portfolio([
            {"Ticker": t, "Nom": n, "Quantité": q, "Prix_achat": p} for t, n, q, p in default
        ])
        return load_portfolio()

    return [
        {
            "Ticker": row["ticker"],
            "Nom": row["nom"],
            "Quantité": row["quantite"],
            "Prix_achat": row["prix_achat"]
        }
        for row in rows
    ]

def save_portfolio(portfolio):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM portfolio")
    for p in portfolio:
        cursor.execute(
            "INSERT INTO portfolio (ticker, nom, quantite, prix_achat, updated_at) VALUES (?, ?, ?, ?, ?)",
            (p["Ticker"], p.get("Nom", ""), p["Quantité"], p["Prix_achat"], datetime.now().isoformat())
        )
    conn.commit()
    conn.close()

# ========== HISTORIQUE ==========

def load_history():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT date, valeur FROM history ORDER BY date")
    rows = cursor.fetchall()
    conn.close()
    return [{"date": row["date"], "valeur": row["valeur"]} for row in rows]

def save_history_point(date_str, valeur):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO history (date, valeur) VALUES (?, ?)",
        (date_str, valeur)
    )
    conn.commit()
    conn.close()

# ========== ALERTES ==========

def load_alerts():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, ticker, type, threshold, created_at, active FROM alerts")
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row["id"],
            "ticker": row["ticker"],
            "type": row["type"],
            "threshold": row["threshold"],
            "created_at": row["created_at"],
            "active": bool(row["active"])
        }
        for row in rows
    ]

def save_alert(alert):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO alerts (ticker, type, threshold, created_at, active) VALUES (?, ?, ?, ?, ?)",
        (alert["ticker"], alert["type"], alert["threshold"], alert["created_at"], 1)
    )
    conn.commit()
    conn.close()

def delete_alert(alert_id):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))
    conn.commit()
    conn.close()