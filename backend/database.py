import sqlite3
from datetime import datetime, timezone
from typing import List, Dict, Any

DB_PATH = "fleet.db"


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DB_PATH) -> None:
    """Creates the aircraft fleet and mission log tables if they do not exist."""
    with get_connection(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS aircraft (
                aircraft_id TEXT PRIMARY KEY,
                model TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'READY',
                battery_pct REAL NOT NULL DEFAULT 100.0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS missions (
                mission_id INTEGER PRIMARY KEY AUTOINCREMENT,
                aircraft_id TEXT NOT NULL,
                start_coord TEXT NOT NULL,
                goal_coord TEXT NOT NULL,
                waypoint_count INTEGER NOT NULL,
                final_status TEXT NOT NULL,
                final_battery_pct REAL NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (aircraft_id) REFERENCES aircraft (aircraft_id)
            )
        """)
        # Seed default V-BAT and X-BAT fleet units if table is empty
        cursor = conn.execute("SELECT COUNT(*) FROM aircraft")
        if cursor.fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO aircraft (aircraft_id, model, status, battery_pct) VALUES (?, ?, ?, ?)",
                [
                    ("VBAT-01", "V-BAT Tactical VTOL", "READY", 100.0),
                    ("VBAT-02", "V-BAT Reconnaissance", "READY", 96.5),
                    ("XBAT-01", "X-BAT Autonomous Fighter", "READY", 100.0),
                ]
            )
        conn.commit()


def list_aircraft(db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        rows = conn.execute("SELECT * FROM aircraft ORDER BY aircraft_id").fetchall()
        return [dict(row) for row in rows]


def log_mission(
    aircraft_id: str,
    start_coord: str,
    goal_coord: str,
    waypoint_count: int,
    final_status: str,
    final_battery_pct: float,
    db_path: str = DB_PATH
) -> int:
    timestamp = datetime.now(timezone.utc).isoformat()
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO missions (
                aircraft_id, start_coord, goal_coord,
                waypoint_count, final_status, final_battery_pct, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (aircraft_id, start_coord, goal_coord, waypoint_count, final_status, final_battery_pct, timestamp)
        )
        conn.execute(
            "UPDATE aircraft SET battery_pct = ?, status = ? WHERE aircraft_id = ?",
            (final_battery_pct, "READY" if final_battery_pct > 25.0 else "CHARGING", aircraft_id)
        )
        conn.commit()
        return int(cursor.lastrowid)


def list_missions(limit: int = 20, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM missions ORDER BY mission_id DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(row) for row in rows]


if __name__ == "__main__":
    init_db()
    print("Seeded aircraft fleet:", list_aircraft())
