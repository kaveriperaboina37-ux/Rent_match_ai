import os
import sqlite3
from pathlib import Path

DATA_DIR = Path(os.getenv("RENTMATCH_DATA_DIR", Path(__file__).resolve().parent))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "rentmatch.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _add_column(conn, table, column, definition):
    existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db():
    conn = get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      email TEXT NOT NULL UNIQUE,
      password_hash TEXT NOT NULL,
      role TEXT NOT NULL DEFAULT 'tenant',
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS properties(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      area TEXT NOT NULL,
      rent INTEGER NOT NULL,
      bhk INTEGER NOT NULL,
      distance_km REAL NOT NULL DEFAULT 0,
      furnished INTEGER NOT NULL DEFAULT 0,
      parking INTEGER NOT NULL DEFAULT 0,
      wifi INTEGER NOT NULL DEFAULT 0,
      bathrooms INTEGER NOT NULL DEFAULT 1,
      amenities_json TEXT NOT NULL DEFAULT '[]',
      image TEXT NOT NULL,
      gallery_json TEXT NOT NULL DEFAULT '[]',
      owner_name TEXT NOT NULL,
      owner_phone TEXT NOT NULL,
      owner_email TEXT NOT NULL,
      owner_user_id INTEGER,
      lat REAL NOT NULL,
      lng REAL NOT NULL,
      description TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'available',
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY(owner_user_id) REFERENCES users(id) ON DELETE SET NULL
    );
    CREATE TABLE IF NOT EXISTS favorites(
      user_id INTEGER NOT NULL,
      property_id INTEGER NOT NULL,
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY(user_id, property_id),
      FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
      FOREIGN KEY(property_id) REFERENCES properties(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS searches(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      query TEXT NOT NULL,
      requirements_json TEXT NOT NULL,
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # Upgrade databases created by older project versions.
    _add_column(conn, "users", "role", "TEXT NOT NULL DEFAULT 'tenant'")
    _add_column(conn, "properties", "gallery_json", "TEXT NOT NULL DEFAULT '[]'")
    _add_column(conn, "properties", "owner_user_id", "INTEGER")
    _add_column(conn, "properties", "status", "TEXT NOT NULL DEFAULT 'available'")
    _add_column(conn, "properties", "created_at", "TEXT")
    conn.execute("UPDATE properties SET gallery_json=json_array(image) WHERE gallery_json='[]' OR gallery_json IS NULL")
    conn.execute("UPDATE properties SET created_at=CURRENT_TIMESTAMP WHERE created_at IS NULL OR created_at=''")
    conn.commit()
    conn.close()
