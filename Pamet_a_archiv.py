# -*- coding: utf-8 -*-
import json
import os
import sqlite3
from datetime import datetime

import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "archiv.db")


def _connect():
    return sqlite3.connect(DB_PATH)


def init_db():
    """Inicializuje databázi a doplní chybějící sloupce."""
    conn = _connect()
    c = conn.cursor()

    c.execute(
        """CREATE TABLE IF NOT EXISTS melodie
           (id INTEGER PRIMARY KEY AUTOINCREMENT,
            jmeno TEXT,
            atmosfera TEXT,
            nastroj TEXT,
            noty_json TEXT,
            bpm INTEGER,
            rating INTEGER DEFAULT 0,
            datum TEXT,
            tags TEXT DEFAULT '',
            source_type TEXT DEFAULT 'generated',
            rating_updated_at TEXT)"""
    )

    c.execute("""CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)""")

    c.execute("PRAGMA table_info(melodie)")
    columns = [col[1] for col in c.fetchall()]

    migrations = {
        "rating": "ALTER TABLE melodie ADD COLUMN rating INTEGER DEFAULT 0",
        "nastroj": "ALTER TABLE melodie ADD COLUMN nastroj TEXT",
        "bpm": "ALTER TABLE melodie ADD COLUMN bpm INTEGER",
        "atmosfera": "ALTER TABLE melodie ADD COLUMN atmosfera TEXT",
        "tags": "ALTER TABLE melodie ADD COLUMN tags TEXT DEFAULT ''",
        "source_type": "ALTER TABLE melodie ADD COLUMN source_type TEXT DEFAULT 'generated'",
        "rating_updated_at": "ALTER TABLE melodie ADD COLUMN rating_updated_at TEXT",
    }

    for col, query in migrations.items():
        if col not in columns:
            c.execute(query)

    conn.commit()
    conn.close()


def get_setting(key, default_val):
    """Načte hodnotu z tabulky settings. Podporuje JSON formát."""
    try:
        conn = _connect()
        c = conn.cursor()
        c.execute("SELECT value FROM settings WHERE key = ?", (key,))
        res = c.fetchone()
        conn.close()
        if res:
            try:
                return json.loads(res[0])
            except (json.JSONDecodeError, TypeError):
                return res[0]
        return default_val
    except Exception:
        return default_val


def save_setting(key, value):
    """Uloží hodnotu do tabulky settings ve formátu JSON."""
    conn = _connect()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, json.dumps(value)))
    conn.commit()
    conn.close()


def save_to_db(jmeno, atmosfera, nastroj, noty_json, bpm, rating, tags="", source_type="generated"):
    """Uloží položku do archivu."""
    conn = _connect()
    c = conn.cursor()
    datum = datetime.now().strftime("%Y-%m-%d %H:%M")
    rating_val = max(0, min(5, int(rating or 0)))
    rating_ts = datum if rating_val > 0 else None
    c.execute(
        """INSERT INTO melodie (jmeno, atmosfera, nastroj, noty_json, bpm, rating, datum, tags, source_type, rating_updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            jmeno,
            atmosfera,
            nastroj,
            json.dumps(noty_json),
            int(bpm or 90),
            rating_val,
            datum,
            str(tags or ""),
            str(source_type or "generated"),
            rating_ts,
        ),
    )
    conn.commit()
    conn.close()


def update_rating(item_id, rating):
    """Okamžitě uloží hodnocení položky (0-5)."""
    conn = _connect()
    c = conn.cursor()
    val = max(0, min(5, int(rating or 0)))
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute("UPDATE melodie SET rating = ?, rating_updated_at = ? WHERE id = ?", (val, ts, int(item_id)))
    conn.commit()
    conn.close()


def update_tags(item_id, tags):
    """Aktualizuje tagy u položky v archivu."""
    conn = _connect()
    c = conn.cursor()
    c.execute("UPDATE melodie SET tags = ? WHERE id = ?", (str(tags or ""), int(item_id)))
    conn.commit()
    conn.close()


def delete_from_db(item_id):
    """Smaže záznam z archivu podle ID."""
    conn = _connect()
    c = conn.cursor()
    c.execute("DELETE FROM melodie WHERE id = ?", (int(item_id),))
    conn.commit()
    conn.close()


def get_all_melodies():
    """Vrátí všechny uložené melodie jako Pandas DataFrame."""
    conn = _connect()
    try:
        df = pd.read_sql_query("SELECT * FROM melodie ORDER BY datum DESC", conn)
    finally:
        conn.close()
    return df


def get_producers_and_themes():
    """Vrací seznam producentů a témat včetně uživatelských položek."""
    base_producers = [
        "Žádný (vypnuto)",
        "J Dilla",
        "DJ Premier",
        "The Alchemist",
        "Madlib",
        "RZA",
        "Pete Rock",
        "9th Wonder",
        "Havoc",
        "Dr Dre",
        "Kanye West",
        "Daringer",
        "Apollo Brown",
        "Nujabes",
        "Knxwledge",
        "MF DOOM",
        "Q-Tip",
        "Just Blaze",
        "Timbaland",
        "Metro Boomin",
    ]

    base_themes = [
        "Žádné (vypnuto)",
        "Dark",
        "Melancholic",
        "Lo-Fi Chill",
        "Hard Boom Bap",
        "Jazzy",
        "Dreamy",
        "Experimental",
    ]

    custom_producers = get_setting("custom_producers", [])
    custom_themes = get_setting("custom_themes", [])

    return base_producers + custom_producers, base_themes + custom_themes


init_db()
