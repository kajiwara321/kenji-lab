"""SQLite への保存処理"""

import sqlite3
import os
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "smiles.db")


def init_db():
    """DBとテーブルを初期化する（冪等）"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS photos (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            flickr_id          TEXT UNIQUE NOT NULL,
            photo_page_url     TEXT,
            url_medium         TEXT,
            lat                REAL,
            lon                REAL,
            geo_accuracy       INTEGER,
            license_id         INTEGER,
            emotion_happy_prob REAL,
            taken_date         TEXT,
            collected_at       TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_photo(photo: dict) -> bool:
    """
    写真データをDBに保存する。
    flickr_id が重複する場合はスキップして False を返す。
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            """
            INSERT INTO photos
                (flickr_id, photo_page_url, url_medium, lat, lon,
                 geo_accuracy, license_id, emotion_happy_prob, taken_date, collected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                photo["flickr_id"],
                photo.get("photo_page_url"),
                photo.get("url_medium"),
                photo.get("lat"),
                photo.get("lon"),
                photo.get("geo_accuracy"),
                photo.get("license_id"),
                photo.get("emotion_happy_prob"),
                photo.get("taken_date"),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # 重複スキップ
    finally:
        conn.close()


def count_photos() -> int:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT COUNT(*) FROM photos").fetchone()
    conn.close()
    return row[0]
