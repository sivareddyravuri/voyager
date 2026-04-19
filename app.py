"""
Voyager Travel Planner — Flask Application
Deploy to Render / Railway / Heroku / VPS with zero config
"""
import os, sys, json
from flask import Flask, request, jsonify, send_from_directory, send_file

# ── resolve backend module path ─────────────────────────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "backend"))

import database as db
import auth as au
from travel_data import transport_options, hotels_for, attractions_for

# ── app setup ───────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder="static", static_url_path="")

# initialise DB on startup
with app.app_context():
    db.init_db()

# ── CORS helper (no flask-cors needed) ──────────────────────────────────────
def _cors(resp):
    resp.headers["Access-Control-Allow-Origin"]  = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    resp.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return resp

@app.after_request
def after(resp):
    return _cors(resp)

@app.route("/api/<path:p>", methods=["OPTIONS"])
def preflight(p):
    return jsonify({}), 204

# ── auth helper ──────────────────────────────────────────────────────────────
def get_session():
    hdr = request.headers.get("Authorization", "")
    if not hdr.startswith("Bearer "):
        return None
    return db.session_get(hdr[7:])

def require_auth():
    s = get_session()
    if not s:
        return None, jsonify({"ok": False, "error": "Authentication required"}), 401
    return s, None, None

# ── short helpers ─────────────────────────────────────────────────────────────
def ok(msg="OK", **kw):
    return jsonify({"ok": True, "message": msg, **kw})

def err(msg, code=400):
    return jsonify({"ok": False, "error": msg}), code

def body():
    return request.get_json(silent=True) or {}

# ════════════════════════════════════════════════════════════════════════════
#  STATIC — serve the frontend SPA
# ════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.errorhandler(404)
def not_found(e):
    # SPA fallback
    idx = os.path.join(BASE, "static", "index.html")
    if os.path.exists(idx):
        return send_file(idx)
    return err("Not found", 404)

# ════════════════════════════════════════════════════════════════════════════
#  AUTH ROUTES
# ════════════════════════════════════════════════════════════════════════════

@app.route("/api/auth/signup", methods=["POST"])
def auth_signup():
    b     = body()
    name  = b.get("name","").strip()
    email = b.get("email","").strip().lower()
    pw    = b.get("password","")

    if not all([name, email, pw]):
        return err("All fields are required")
    if "@" not in email:
        return err("Invalid email address")
    if len(pw) < 8:
        return err("Password must be at least 8 characters")
    if db.user_by_email(email):
        return err("Email already registered — please sign in")

    otp  = au.gen_otp()
    meta = f"{name}||{au.hash_password(pw)}"
    db.otp_save(email, otp, "signup", au.expires_otp(), meta)

    _log_otp(email, otp, "SIGNUP")
    return ok(f"Code sent to {email}", otp_demo=otp)


@app.route("/api/auth/verify-signup", methods=["POST"])
def auth_verify_signup():
    b     = body()
    email = b.get("email","").strip().lower()
    code  = b.get("code","").strip()

    row = db.otp_verify(email, code, "signup")
    if not row:
        return err("Invalid or expired code")

    name, hpw = row["meta"].split("||", 1)
    if not db.user_create(name, email, hpw):
        return err("Email already registered — please sign in")

    user  = db.user_by_email(email)
    token = au.gen_token()
    db.session_create(user["id"], token, au.expires_session())
    db.user_touch_login(user["id"])
    return jsonify({"ok": True, "token": token,
                    "user": {"id": user["id"], "name": user["name"], "email": user["email"]}})


@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    b     = body()
    email = b.get("email","").strip().lower()
    pw    = b.get("password","")
    user  = db.user_by_email(email)

    if not user or not au.verify_password(pw, user["password"]):
        return err("Invalid email or password")

    otp = au.gen_otp()
    db.otp_save(email, otp, "login", au.expires_otp())
    _log_otp(email, otp, "LOGIN")
    return ok(f"Code sent to {email}", otp_demo=otp)


@app.route("/api/auth/verify-login", methods=["POST"])
def auth_verify_login():
    b     = body()
    email = b.get("email","").strip().lower()
    code  = b.get("code","").strip()

    if not db.otp_verify(email, code, "login"):
        return err("Invalid or expired code")

    user  = db.user_by_email(email)
    token = au.gen_token()
    db.session_create(user["id"], token, au.expires_session())
    db.user_touch_login(user["id"])
    return jsonify({"ok": True, "token": token,
                    "user": {"id": user["id"], "name": user["name"], "email": user["email"]}})


@app.route("/api/auth/logout", methods=["POST"])
def auth_logout():
    hdr = request.headers.get("Authorization","")
    if hdr.startswith("Bearer "):
        db.session_delete(hdr[7:])
    return ok("Logged out")


@app.route("/api/me")
def me():
    s, resp, code = require_auth()
    if resp: return resp, code
    return jsonify({"ok": True, "user": {"id": s["user_id"], "name": s["name"], "email": s["email"]}})

# ════════════════════════════════════════════════════════════════════════════
#  TRAVEL ROUTES
# ════════════════════════════════════════════════════════════════════════════

@app.route("/api/plans/search", methods=["POST"])
def plans_search():
    s, resp, code = require_auth()
    if resp: return resp, code

    b          = body()
    origin     = b.get("origin","").strip()
    dest       = b.get("destination","").strip()
    date       = b.get("travel_date","").strip()
    passengers = int(b.get("passengers", 1))
    t_class    = b.get("travel_class", "Economy")

    if not all([origin, dest, date]):
        return err("Origin, destination, and date are required")

    opts = transport_options(origin, dest, passengers)
    pid  = db.plan_create(s["user_id"], origin, dest, date, passengers, t_class, opts)
    db.search_add(s["user_id"], f"{origin} → {dest}")

    return jsonify({"ok": True, "plan_id": pid, "origin": origin,
                    "destination": dest, "travel_date": date,
                    "passengers": passengers, "options": opts})


@app.route("/api/plans/select", methods=["POST"])
def plans_select():
    s, resp, code = require_auth()
    if resp: return resp, code

    b    = body()
    pid  = b.get("plan_id")
    mode = b.get("mode","")
    price= b.get("price","")
    dur  = b.get("duration","")

    if not all([pid, mode]):
        return err("plan_id and mode required")

    db.plan_select(pid, mode, price, dur)
    return ok("Transport selected", plan_id=pid)


@app.route("/api/plans")
def plans_list():
    s, resp, code = require_auth()
    if resp: return resp, code
    return jsonify({"ok": True, "plans": db.plan_list(s["user_id"])})


@app.route("/api/hotels")
def hotels():
    s, resp, code = require_auth()
    if resp: return resp, code

    dest  = request.args.get("destination","")
    bmax  = int(request.args.get("budget_max", 0)) or None
    smin  = int(request.args.get("stars_min",  0)) or None

    return jsonify({"ok": True, "hotels": hotels_for(dest, bmax, smin), "destination": dest})


@app.route("/api/hotels/bookmark", methods=["POST"])
def hotels_bookmark():
    s, resp, code = require_auth()
    if resp: return resp, code

    b = body()
    db.hotel_bookmark(s["user_id"],
        b.get("plan_id"), b.get("hotel_name",""),
        b.get("price",""), b.get("stars", 3), b.get("destination",""))
    return ok(f"{b.get('hotel_name','')} bookmarked!")


@app.route("/api/attractions")
def attractions():
    s, resp, code = require_auth()
    if resp: return resp, code

    dest = request.args.get("destination","")
    return jsonify({"ok": True, "attractions": attractions_for(dest), "destination": dest})


@app.route("/api/history")
def history():
    s, resp, code = require_auth()
    if resp: return resp, code

    return jsonify({
        "ok": True,
        "plans":     db.plan_list(s["user_id"]),
        "bookmarks": db.hotel_list(s["user_id"]),
        "searches":  db.search_list(s["user_id"]),
    })

# ════════════════════════════════════════════════════════════════════════════
#  UTIL
# ════════════════════════════════════════════════════════════════════════════

def _log_otp(email, otp, label):
    print(f"\n  {'='*48}")
    print(f"  📧  {label} OTP  ·  {email}")
    print(f"      CODE: {otp}")
    print(f"  {'='*48}\n", flush=True)


# ════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n  ✈  Voyager running → http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False)
