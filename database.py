"""
Voyager Travel Planner — Database Layer
SQLite with full schema for users, sessions, OTPs, plans, history
"""
import sqlite3, os, json
from datetime import datetime, timezone

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "..", "voyager.db"))


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA foreign_keys=ON")
    return c


def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    db = _conn()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL DEFAULT '',
            email       TEXT NOT NULL UNIQUE,
            password    TEXT NOT NULL,
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            last_login  TEXT
        );
        CREATE TABLE IF NOT EXISTS otps (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            email       TEXT NOT NULL,
            code        TEXT NOT NULL,
            purpose     TEXT NOT NULL,
            meta        TEXT DEFAULT '',
            expires_at  TEXT NOT NULL,
            used        INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token       TEXT NOT NULL UNIQUE,
            expires_at  TEXT NOT NULL,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS travel_plans (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            origin          TEXT NOT NULL,
            destination     TEXT NOT NULL,
            travel_date     TEXT NOT NULL,
            passengers      INTEGER NOT NULL DEFAULT 1,
            travel_class    TEXT NOT NULL DEFAULT 'Economy',
            selected_mode   TEXT,
            selected_price  TEXT,
            selected_dur    TEXT,
            status          TEXT NOT NULL DEFAULT 'searched',
            ai_tip          TEXT DEFAULT '',
            transport_json  TEXT DEFAULT '[]',
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS hotel_bookmarks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            plan_id     INTEGER REFERENCES travel_plans(id),
            hotel_name  TEXT NOT NULL,
            price       TEXT NOT NULL,
            stars       INTEGER NOT NULL DEFAULT 3,
            destination TEXT NOT NULL DEFAULT '',
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS search_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            query       TEXT NOT NULL,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """)
    db.commit()
    db.close()
    print(f"[DB] Ready → {os.path.abspath(DB_PATH)}")


# ── helpers ──────────────────────────────────────────────────────────

def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def _row(r):
    return dict(r) if r else None


# ── users ────────────────────────────────────────────────────────────

def user_create(name, email, hashed_pw):
    db = _conn()
    try:
        db.execute("INSERT INTO users(name,email,password,created_at) VALUES(?,?,?,?)",
                   (name, email, hashed_pw, now_iso()))
        db.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        db.close()


def user_by_email(email):
    db = _conn()
    r = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    db.close()
    return _row(r)


def user_by_id(uid):
    db = _conn()
    r = db.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    db.close()
    return _row(r)


def user_touch_login(uid):
    db = _conn()
    db.execute("UPDATE users SET last_login=? WHERE id=?", (now_iso(), uid))
    db.commit()
    db.close()


# ── OTP ──────────────────────────────────────────────────────────────

def otp_save(email, code, purpose, expires_at, meta=""):
    db = _conn()
    db.execute("UPDATE otps SET used=1 WHERE email=? AND purpose=? AND used=0", (email, purpose))
    db.execute("INSERT INTO otps(email,code,purpose,meta,expires_at,created_at) VALUES(?,?,?,?,?,?)",
               (email, code, purpose, meta, expires_at, now_iso()))
    db.commit()
    db.close()


def otp_verify(email, code, purpose):
    db = _conn()
    r = db.execute(
        "SELECT * FROM otps WHERE email=? AND code=? AND purpose=? AND used=0 AND expires_at>?",
        (email, code, purpose, now_iso())
    ).fetchone()
    if r:
        db.execute("UPDATE otps SET used=1 WHERE id=?", (r["id"],))
        db.commit()
    db.close()
    return _row(r)


def otp_get_meta(email, purpose):
    """Retrieve stored meta without consuming the OTP."""
    db = _conn()
    r = db.execute(
        "SELECT meta FROM otps WHERE email=? AND purpose=? AND used=0 AND expires_at>? ORDER BY id DESC LIMIT 1",
        (email, purpose, now_iso())
    ).fetchone()
    db.execute("UPDATE otps SET used=1 WHERE email=? AND purpose=? AND used=0", (email, purpose))
    db.commit()
    db.close()
    return r["meta"] if r else None


# ── sessions ─────────────────────────────────────────────────────────

def session_create(uid, token, expires_at):
    db = _conn()
    db.execute("INSERT INTO sessions(user_id,token,expires_at,created_at) VALUES(?,?,?,?)",
               (uid, token, expires_at, now_iso()))
    db.commit()
    db.close()


def session_get(token):
    db = _conn()
    r = db.execute(
        "SELECT s.*,u.name,u.email FROM sessions s JOIN users u ON u.id=s.user_id "
        "WHERE s.token=? AND s.expires_at>?", (token, now_iso())
    ).fetchone()
    db.close()
    return _row(r)


def session_delete(token):
    db = _conn()
    db.execute("DELETE FROM sessions WHERE token=?", (token,))
    db.commit()
    db.close()


# ── plans ────────────────────────────────────────────────────────────

def plan_create(uid, origin, dest, date, passengers, travel_class, transport_json, ai_tip=""):
    db = _conn()
    cur = db.execute(
        "INSERT INTO travel_plans(user_id,origin,destination,travel_date,passengers,travel_class,transport_json,ai_tip,created_at)"
        " VALUES(?,?,?,?,?,?,?,?,?)",
        (uid, origin, dest, date, passengers, travel_class, json.dumps(transport_json), ai_tip, now_iso())
    )
    pid = cur.lastrowid
    db.commit()
    db.close()
    return pid


def plan_select(plan_id, mode, price, duration):
    db = _conn()
    db.execute(
        "UPDATE travel_plans SET selected_mode=?,selected_price=?,selected_dur=?,status='booked' WHERE id=?",
        (mode, price, duration, plan_id)
    )
    db.commit()
    db.close()


def plan_list(uid, limit=50):
    db = _conn()
    rows = db.execute(
        "SELECT * FROM travel_plans WHERE user_id=? ORDER BY created_at DESC LIMIT ?", (uid, limit)
    ).fetchall()
    db.close()
    result = []
    for r in rows:
        d = dict(r)
        d["transport"] = json.loads(d.get("transport_json") or "[]")
        result.append(d)
    return result


# ── hotel bookmarks ───────────────────────────────────────────────────

def hotel_bookmark(uid, plan_id, name, price, stars, destination):
    db = _conn()
    db.execute(
        "INSERT INTO hotel_bookmarks(user_id,plan_id,hotel_name,price,stars,destination,created_at) VALUES(?,?,?,?,?,?,?)",
        (uid, plan_id, name, price, stars, destination, now_iso())
    )
    db.commit()
    db.close()


def hotel_list(uid):
    db = _conn()
    rows = db.execute(
        "SELECT * FROM hotel_bookmarks WHERE user_id=? ORDER BY created_at DESC", (uid,)
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


# ── search history ────────────────────────────────────────────────────

def search_add(uid, query):
    db = _conn()
    db.execute("INSERT INTO search_history(user_id,query,created_at) VALUES(?,?,?)",
               (uid, query, now_iso()))
    db.commit()
    db.close()


def search_list(uid, limit=40):
    db = _conn()
    rows = db.execute(
        "SELECT * FROM search_history WHERE user_id=? ORDER BY created_at DESC LIMIT ?", (uid, limit)
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]
