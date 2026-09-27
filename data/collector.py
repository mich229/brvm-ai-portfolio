import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import json
import os

CACHE_FILE = "data/last_prices.json"

def save_cache(data):
    os.makedirs("data", exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return None
    return None

def get_brvm_prices(tickers=None):
    """
    Récupère les cours avec plusieurs tentatives + cache local.
    """
    if tickers is None:
        tickers = ["ABJC", "BOAB", "ETIT", "SNTS"]

    url = "https://www.brvm.org/fr"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    prices = {}
    source = "live"
    date_str = datetime.now().strftime("%d/%m/%Y %H:%M")

    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        text = BeautifulSoup(r.text, "lxml").get_text(separator=" ")

        for ticker in tickers:
            # Plusieurs patterns de recherche
            patterns = [
                rf"{ticker}\s+([\d\s]{{3,}})\s+([+-]?\d+[,.]?\d*%?)",
                rf"{ticker}\s*\|\s*([\d\s]+)\s*\|\s*([+-]?\d+[,.]?\d*%?)",
            ]
            found = False
            for pat in patterns:
                match = re.search(pat, text)
                if match:
                    price_str = match.group(1).replace(" ", "").replace("\xa0", "")
                    change = match.group(2).strip()
                    try:
                        price = float(price_str)
                        prices[ticker] = {"price": price, "change": change}
                        found = True
                        break
                    except:
                        continue
            if not found:
                prices[ticker] = {"price": None, "change": "N/A"}

        # Si on a au moins 2 prix valides, on considère que c'est bon
        valid_count = sum(1 for v in prices.values() if v["price"] is not None)
        if valid_count >= 2:
            cache_data = {
                "prices": prices,
                "date": date_str,
                "source": "live"
            }
            save_cache(cache_data)
            return prices, date_str, "live"
        else:
            raise Exception("Trop peu de prix récupérés")

    except Exception as e:
        # On charge le cache
        cache = load_cache()
        if cache and "prices" in cache:
            return cache["prices"], cache.get("date", "Cache"), "cache"
        
        # Dernier recours : valeurs hardcodées
        fallback = {
            "ABJC": {"price": 3930.0, "change": "-2,96%"},
            "BOAB": {"price": 9850.0, "change": "-2,48%"},
            "ETIT": {"price": 70.0, "change": "0,00%"},
            "SNTS": {"price": 42190.0, "change": "+7,49%"},
        }
        return fallback, "Fallback (18/09/2026)", "fallback"