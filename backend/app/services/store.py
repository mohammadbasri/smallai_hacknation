"""SQLite persistence (stdlib only, so the edge-box image stays small).

Tables: sync_records, enquiries, bookings, feedback, profile, sms_outbox. One file, created on first use.
"""
from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from app.config import get_settings

_lock = threading.Lock()
_conn: sqlite3.Connection | None = None
_conn_path: str | None = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS sync_records (
    id TEXT PRIMARY KEY, client_id TEXT, kind TEXT, payload TEXT, captured_at TEXT, language TEXT, received_at TEXT
);
CREATE TABLE IF NOT EXISTS enquiries (
    id TEXT PRIMARY KEY, created_at TEXT, source TEXT, visitor_contact TEXT, text TEXT, language TEXT,
    intent TEXT, confidence REAL, decision TEXT, reply_for_visitor TEXT, status TEXT, operator_action TEXT, sent_text TEXT
);
CREATE TABLE IF NOT EXISTS bookings (
    id TEXT PRIMARY KEY, created_at TEXT, updated_at TEXT, visitor_name TEXT, visitor_contact TEXT, language TEXT,
    date TEXT, time TEXT, party_size INTEGER, status TEXT, notes TEXT, source TEXT, enquiry_id TEXT
);
CREATE TABLE IF NOT EXISTS feedback (
    id TEXT PRIMARY KEY, created_at TEXT, source TEXT, visitor_contact TEXT, text TEXT, language TEXT, clauses TEXT
);
CREATE TABLE IF NOT EXISTS profile (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS sms_outbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT, direction TEXT, counterpart TEXT, text TEXT, language TEXT, purpose TEXT
);
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _connect() -> sqlite3.Connection:
    global _conn, _conn_path
    path = get_settings().db_path
    if _conn is None or _conn_path != path:
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(path, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.executescript(SCHEMA)
        _conn_path = path
    return _conn


@contextmanager
def db():
    with _lock:
        conn = _connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def reset_for_tests() -> None:
    """Drop every table (tests use a throwaway DB path)."""
    with db() as conn:
        for t in ("sync_records", "enquiries", "bookings", "feedback", "profile", "sms_outbox"):
            conn.execute(f"DELETE FROM {t}")


# --------------------------------------------------------------------------- sync
def sync_exists(record_id: str) -> bool:
    with db() as conn:
        return conn.execute("SELECT 1 FROM sync_records WHERE id=?", (record_id,)).fetchone() is not None


def sync_insert(client_id: str, rec: dict) -> None:
    with db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO sync_records VALUES (?,?,?,?,?,?,?)",
            (rec["id"], client_id, rec["kind"], json.dumps(rec["payload"]), rec["captured_at"], rec["language"], now_iso()),
        )


def sync_count() -> int:
    with db() as conn:
        return conn.execute("SELECT COUNT(*) FROM sync_records").fetchone()[0]


def sync_list(limit: int = 200) -> list[dict]:
    with db() as conn:
        rows = conn.execute("SELECT * FROM sync_records ORDER BY received_at DESC LIMIT ?", (limit,)).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["payload"] = json.loads(d["payload"])
            out.append(d)
        return out


# --------------------------------------------------------------------------- enquiries
def enquiry_upsert(e: dict) -> None:
    with db() as conn:
        conn.execute(
            """INSERT INTO enquiries (id, created_at, source, visitor_contact, text, language, intent, confidence, decision,
                                       reply_for_visitor, status, operator_action, sent_text)
               VALUES (:id, :created_at, :source, :visitor_contact, :text, :language, :intent, :confidence, :decision,
                       :reply_for_visitor, :status, :operator_action, :sent_text)
               ON CONFLICT(id) DO UPDATE SET status=excluded.status, operator_action=excluded.operator_action,
                       sent_text=excluded.sent_text""",
            {"operator_action": None, "sent_text": None, "status": "new", "source": "app", "visitor_contact": "", **e},
        )


def enquiry_get(enquiry_id: str) -> dict | None:
    with db() as conn:
        r = conn.execute("SELECT * FROM enquiries WHERE id=?", (enquiry_id,)).fetchone()
        return dict(r) if r else None


def enquiry_latest_open_for(contact: str | None = None) -> dict | None:
    with db() as conn:
        if contact:
            r = conn.execute(
                "SELECT * FROM enquiries WHERE status='new' AND visitor_contact=? ORDER BY created_at DESC LIMIT 1", (contact,)
            ).fetchone()
        else:
            r = conn.execute("SELECT * FROM enquiries WHERE status='new' ORDER BY created_at DESC LIMIT 1").fetchone()
        return dict(r) if r else None


def enquiry_update(enquiry_id: str, **fields) -> None:
    if not fields:
        return
    sets = ", ".join(f"{k}=?" for k in fields)
    with db() as conn:
        conn.execute(f"UPDATE enquiries SET {sets} WHERE id=?", (*fields.values(), enquiry_id))


def enquiry_list(limit: int = 100) -> list[dict]:
    with db() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM enquiries ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()]


# --------------------------------------------------------------------------- bookings
def booking_upsert(b: dict) -> dict:
    with db() as conn:
        conn.execute(
            """INSERT INTO bookings (id, created_at, updated_at, visitor_name, visitor_contact, language, date, time,
                                      party_size, status, notes, source, enquiry_id)
               VALUES (:id, :created_at, :updated_at, :visitor_name, :visitor_contact, :language, :date, :time,
                       :party_size, :status, :notes, :source, :enquiry_id)
               ON CONFLICT(id) DO UPDATE SET updated_at=excluded.updated_at, visitor_name=excluded.visitor_name,
                       visitor_contact=excluded.visitor_contact, language=excluded.language, date=excluded.date,
                       time=excluded.time, party_size=excluded.party_size, status=excluded.status, notes=excluded.notes""",
            b,
        )
        return dict(conn.execute("SELECT * FROM bookings WHERE id=?", (b["id"],)).fetchone())


def booking_get(booking_id: str) -> dict | None:
    with db() as conn:
        r = conn.execute("SELECT * FROM bookings WHERE id=?", (booking_id,)).fetchone()
        return dict(r) if r else None


def booking_list(status: str | None = None) -> list[dict]:
    with db() as conn:
        if status:
            rows = conn.execute("SELECT * FROM bookings WHERE status=? ORDER BY date, time", (status,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM bookings ORDER BY date, time").fetchall()
        return [dict(r) for r in rows]


def booking_patch(booking_id: str, fields: dict) -> dict | None:
    fields = {k: v for k, v in fields.items() if v is not None}
    if not fields:
        return booking_get(booking_id)
    fields["updated_at"] = now_iso()
    sets = ", ".join(f"{k}=?" for k in fields)
    with db() as conn:
        conn.execute(f"UPDATE bookings SET {sets} WHERE id=?", (*fields.values(), booking_id))
    return booking_get(booking_id)


# --------------------------------------------------------------------------- feedback
def feedback_upsert(f: dict) -> None:
    with db() as conn:
        conn.execute(
            """INSERT INTO feedback (id, created_at, source, visitor_contact, text, language, clauses)
               VALUES (:id, :created_at, :source, :visitor_contact, :text, :language, :clauses)
               ON CONFLICT(id) DO UPDATE SET clauses=excluded.clauses, language=excluded.language""",
            {**f, "clauses": json.dumps(f["clauses"])},
        )


def feedback_list(limit: int = 500) -> list[dict]:
    with db() as conn:
        rows = conn.execute("SELECT * FROM feedback ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["clauses"] = json.loads(d["clauses"])
            out.append(d)
        return out


# --------------------------------------------------------------------------- profile
def profile_get() -> dict | None:
    with db() as conn:
        r = conn.execute("SELECT value FROM profile WHERE key='profile'").fetchone()
        return json.loads(r[0]) if r else None


def profile_set(p: dict) -> None:
    with db() as conn:
        conn.execute("INSERT INTO profile (key, value) VALUES ('profile', ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                     (json.dumps(p),))


# --------------------------------------------------------------------------- sms outbox
def sms_log(direction: str, counterpart: str, text: str, language: str, purpose: str) -> dict:
    with db() as conn:
        cur = conn.execute(
            "INSERT INTO sms_outbox (created_at, direction, counterpart, text, language, purpose) VALUES (?,?,?,?,?,?)",
            (now_iso(), direction, counterpart, text, language, purpose),
        )
        return dict(conn.execute("SELECT * FROM sms_outbox WHERE id=?", (cur.lastrowid,)).fetchone())


def sms_list(limit: int = 100) -> list[dict]:
    with db() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM sms_outbox ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]
