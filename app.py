import os
import secrets
import sqlite3
from functools import wraps
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, send_from_directory, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
# Locally this lives in the project folder. Render sets POOLGUYZ_DATA_DIR to
# its attached disk so admin content and uploaded photos survive deployments.
DATA_DIR = Path(os.environ.get("POOLGUYZ_DATA_DIR", BASE_DIR / "instance"))
DATABASE = DATA_DIR / "poolguyz.db"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_secret_key():
    if os.environ.get("SECRET_KEY"):
        return os.environ["SECRET_KEY"]
    secret_file = DATABASE.parent / ".secret_key"
    if not secret_file.exists():
        secret_file.write_text(secrets.token_hex(32), encoding="utf-8")
    return secret_file.read_text(encoding="utf-8").strip()

app = Flask(__name__)
app.config.update(
    SECRET_KEY=load_secret_key(),
    DATABASE=str(DATABASE),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    MAX_CONTENT_LENGTH=8 * 1024 * 1024,
)

ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

SERVICE_BASE = {"install": 500000, "resurface": 30000, "repair": 150000, "maintenance": 1500}
POOL_TYPE_MULTIPLIER = {"concrete": 1.25, "fibreglass": 1.0, "vinyl": 0.85, "above_ground": 0.5}
SIZE_MULTIPLIER = {"small": 0.8, "medium": 1.0, "large": 1.4}
EXTRA_COST = {"heating": 4500, "lighting": 1200, "fencing": 3800, "landscaping": 6000, "water_feature": 3200}
EXTRA_LABELS = {"heating": "Pool heating", "lighting": "LED lighting", "fencing": "Pool fencing", "landscaping": "Landscaping", "water_feature": "Water feature"}


def get_db():
    connection = sqlite3.connect(app.config["DATABASE"])
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with get_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS admin_user (
                id INTEGER PRIMARY KEY CHECK (id = 1), password_hash TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
                description TEXT NOT NULL, icon TEXT NOT NULL DEFAULT '💧',
                sort_order INTEGER NOT NULL DEFAULT 0, is_published INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS works (
                id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
                location TEXT NOT NULL DEFAULT '', image_url TEXT NOT NULL DEFAULT '',
                sort_order INTEGER NOT NULL DEFAULT 0, is_published INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT, quote TEXT NOT NULL,
                customer_name TEXT NOT NULL, location TEXT NOT NULL DEFAULT '',
                sort_order INTEGER NOT NULL DEFAULT 0, is_published INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS treatments (
                id INTEGER PRIMARY KEY AUTOINCREMENT, audience TEXT NOT NULL,
                title TEXT NOT NULL, description TEXT NOT NULL,
                icon TEXT NOT NULL DEFAULT '💧', features TEXT NOT NULL DEFAULT '',
                sort_order INTEGER NOT NULL DEFAULT 0, is_published INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS team_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
                role TEXT NOT NULL, bio TEXT NOT NULL, image_url TEXT NOT NULL DEFAULT '',
                sort_order INTEGER NOT NULL DEFAULT 0, is_published INTEGER NOT NULL DEFAULT 1
            );
        """)
        if db.execute("SELECT COUNT(*) FROM services").fetchone()[0] == 0:
            db.executemany(
                "INSERT INTO services (title, description, icon, sort_order) VALUES (?, ?, ?, ?)",
                [
                    ("Cleaning & Maintenance", "Weekly skims, vacuums, chemical balancing, and filter checks. Set a schedule and forget it.", "🧽", 1),
                    ("Repairs", "Pumps, leaks, tiles, and lights diagnosed fast and fixed right.", "🔧", 2),
                    ("New Installs", "From first dig to first swim, including concrete and fibreglass pools.", "🏗️", 3),
                    ("Water Testing", "On-site testing and a clear answer about what your water needs.", "🧪", 4),
                ],
            )
        if db.execute("SELECT COUNT(*) FROM works").fetchone()[0] == 0:
            db.executemany(
                "INSERT INTO works (title, location, sort_order) VALUES (?, ?, ?)",
                [("Backyard resurface", "Ernakulam", 1), ("New fibreglass install", "Kozhikode", 2), ("Pump & filter overhaul", "Thiruvananthapuram", 3), ("Weekly service client", "Alappuzha", 4)],
            )
        if db.execute("SELECT COUNT(*) FROM reviews").fetchone()[0] == 0:
            db.executemany(
                "INSERT INTO reviews (quote, customer_name, location, sort_order) VALUES (?, ?, ?, ?)",
                [
                    ("Turned my green disaster into a swimmable pool in two days. Actually explained what went wrong, too.", "Sarah M.", "Ernakulam", 1),
                    ("Been on their weekly plan for three years. Never had to think about the pool once.", "David K.", "Alappuzha", 2),
                    ("Fair quote, showed up on time, cleaned up after themselves. Rare combo.", "Priya R.", "Kozhikode", 3),
                ],
            )
        if db.execute("SELECT COUNT(*) FROM treatments").fetchone()[0] == 0:
            db.executemany(
                "INSERT INTO treatments (audience, title, description, icon, features, sort_order) VALUES (?, ?, ?, ?, ?, ?)",
                [
                    ("household", "Whole-house filtration", "Cleaner, better-tasting water from every tap with a system selected for your home and local water conditions.", "🏠", "Sediment and chlorine reduction\nImproved taste and odour\nSolutions for hard water\nProfessional installation and servicing", 1),
                    ("household", "Drinking water systems", "Compact under-sink and reverse-osmosis options for fresh drinking and cooking water.", "🚰", "Multi-stage filtration\nReverse osmosis options\nFilter replacement plans\nNeat under-sink installation", 2),
                    ("commercial", "Commercial filtration systems", "Reliable, scalable treatment for offices, hospitality, retail, strata and light industrial sites.", "🏢", "Site water assessment\nHigh-capacity filtration\nScheduled maintenance\nSystem performance monitoring", 1),
                    ("commercial", "Specialised water treatment", "Purpose-designed solutions for higher demand, equipment protection and water-quality targets.", "⚙️", "Water softening\nUV disinfection\nReverse osmosis\nCustom treatment plans", 2),
                ],
            )
        if db.execute("SELECT COUNT(*) FROM team_members").fetchone()[0] == 0:
            db.executemany(
                "INSERT INTO team_members (name, role, bio, image_url, sort_order) VALUES (?, ?, ?, ?, ?)",
                [
                    ("Arjun Menon", "Founder & Pool Specialist", "Leads inspections, equipment advice, and complex pool-care plans so each customer gets the right solution.", "/static/images/team/team-lead-profile.webp", 1),
                    ("Rahul Krishnan", "Service Technician", "Handles routine servicing, pump checks, and practical repairs to keep your pool clean and ready to use.", "/static/images/team/team-technician-profile.webp", 2),
                    ("Nisha Anil", "Water Care Technician", "Tests and balances water carefully, helping families enjoy water that looks clear and feels comfortable.", "/static/images/team/member-2.png", 3),
                    ("Vishnu Mohan", "Equipment & Repairs", "Diagnoses filtration, pump, and plumbing issues, then explains the repair in simple, honest language.", "/static/images/team/member-3.png", 4),
                    ("Fathima Saleem", "Customer Care Coordinator", "Keeps bookings organised and customers informed, from the first quote through to the final follow-up.", "/static/images/team/member-4.png", 5),
                    ("Jithin Das", "Pool Installation Technician", "Supports new equipment installations and upgrades, making sure every system is set up for long-term reliability.", "/static/images/team/member-5.png", 6),
                ],
            )


def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


app.jinja_env.globals["csrf_token"] = csrf_token


def require_csrf():
    expected = session.get("csrf_token", "")
    supplied = request.form.get("csrf_token", "")
    if not expected or not secrets.compare_digest(supplied, expected):
        abort(400, "Invalid form token")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def save_uploaded_image(upload, prefix):
    if not upload or not upload.filename:
        return ""
    filename = secure_filename(upload.filename)
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError("Use a JPG, PNG, or WebP image.")
    upload_folder = DATA_DIR / "uploads"
    upload_folder.mkdir(parents=True, exist_ok=True)
    stored_name = f"{prefix}-{secrets.token_hex(8)}.{extension}"
    upload.save(upload_folder / stored_name)
    return url_for("uploaded_file", filename=stored_name)


@app.get("/uploads/<path:filename>")
def uploaded_file(filename):
    """Serve admin-uploaded images from the persistent data directory."""
    return send_from_directory(DATA_DIR / "uploads", filename)


def calculate_quote(service, pool_type, size, extras):
    base = SERVICE_BASE.get(service, 0)
    if service in ("install", "resurface"):
        base *= POOL_TYPE_MULTIPLIER.get(pool_type, 1.0)
        base *= SIZE_MULTIPLIER.get(size, 1.0)
    subtotal = base + sum(EXTRA_COST.get(extra, 0) for extra in extras)
    is_recurring = service == "maintenance"
    rounding = -1 if is_recurring else -2
    return {
        "low": int(round(subtotal * 0.9, rounding)),
        "high": int(round(subtotal * 1.15, rounding)),
        "is_recurring": is_recurring,
        "extras_chosen": [EXTRA_LABELS[item] for item in extras if item in EXTRA_LABELS],
    }


@app.route("/")
def home():
    with get_db() as db:
        services = db.execute("SELECT * FROM services WHERE is_published = 1 ORDER BY sort_order, id").fetchall()
        works = db.execute("SELECT * FROM works WHERE is_published = 1 ORDER BY sort_order, id").fetchall()
        reviews = db.execute("SELECT * FROM reviews WHERE is_published = 1 ORDER BY sort_order, id").fetchall()
        team_members = db.execute("SELECT * FROM team_members WHERE is_published = 1 ORDER BY sort_order, id").fetchall()
    return render_template("index.html", services=services, works=works, reviews=reviews, team_members=team_members)


@app.route("/quote", methods=["GET", "POST"])
def quote():
    result, form_data = None, {}
    if request.method == "POST":
        service = request.form.get("service", "")
        pool_type = request.form.get("pool_type", "")
        size = request.form.get("size", "")
        extras = request.form.getlist("extras")
        form_data = {"service": service, "pool_type": pool_type, "size": size, "extras": extras}
        result = calculate_quote(service, pool_type, size, extras)
    return render_template("quote.html", result=result, form_data=form_data)


@app.route("/water-treatment")
def water_treatment():
    with get_db() as db:
        household = db.execute("SELECT * FROM treatments WHERE is_published = 1 AND audience = 'household' ORDER BY sort_order, id").fetchall()
        commercial = db.execute("SELECT * FROM treatments WHERE is_published = 1 AND audience = 'commercial' ORDER BY sort_order, id").fetchall()
    return render_template("water_treatment.html", household=household, commercial=commercial)


@app.route("/admin/setup", methods=["GET", "POST"])
def admin_setup():
    with get_db() as db:
        if db.execute("SELECT 1 FROM admin_user WHERE id = 1").fetchone():
            return redirect(url_for("admin_login"))
        if request.method == "POST":
            require_csrf()
            password = request.form.get("password", "")
            if len(password) < 8:
                flash("Use at least 8 characters.", "error")
            elif password != request.form.get("confirmation", ""):
                flash("The passwords do not match.", "error")
            else:
                db.execute("INSERT INTO admin_user (id, password_hash) VALUES (1, ?)", (generate_password_hash(password),))
                db.commit()
                session.clear()
                flash("Admin password created. You can now sign in.", "success")
                return redirect(url_for("admin_login"))
    return render_template("admin/setup.html")


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    with get_db() as db:
        admin = db.execute("SELECT * FROM admin_user WHERE id = 1").fetchone()
    if not admin:
        return redirect(url_for("admin_setup"))
    if request.method == "POST":
        require_csrf()
        if check_password_hash(admin["password_hash"], request.form.get("password", "")):
            session.clear()
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        flash("Incorrect password.", "error")
    return render_template("admin/login.html")


@app.post("/admin/logout")
@login_required
def admin_logout():
    require_csrf()
    session.clear()
    return redirect(url_for("home"))


@app.route("/admin")
@login_required
def admin_dashboard():
    with get_db() as db:
        services = db.execute("SELECT * FROM services ORDER BY sort_order, id").fetchall()
        works = db.execute("SELECT * FROM works ORDER BY sort_order, id").fetchall()
        reviews = db.execute("SELECT * FROM reviews ORDER BY sort_order, id").fetchall()
        treatments = db.execute("SELECT * FROM treatments ORDER BY audience, sort_order, id").fetchall()
        team_members = db.execute("SELECT * FROM team_members ORDER BY sort_order, id").fetchall()
    return render_template("admin/dashboard.html", services=services, works=works, reviews=reviews, treatments=treatments, team_members=team_members)


ADMIN_TABLES = {
    "services": ("title", "description", "icon", "sort_order", "is_published"),
    "works": ("title", "location", "image_url", "sort_order", "is_published"),
    "reviews": ("quote", "customer_name", "location", "sort_order", "is_published"),
    "treatments": ("audience", "title", "description", "icon", "features", "sort_order", "is_published"),
    "team_members": ("name", "role", "bio", "image_url", "sort_order", "is_published"),
}


@app.post("/admin/<section>/save")
@login_required
def admin_save(section):
    require_csrf()
    fields = ADMIN_TABLES.get(section)
    if not fields:
        abort(404)
    item_id = request.form.get("id", type=int)
    values = []
    for field in fields:
        if field == "is_published":
            values.append(1 if request.form.get(field) else 0)
        elif field == "sort_order":
            values.append(request.form.get(field, type=int) or 0)
        elif field == "image_url" and section in {"works", "team_members"}:
            try:
                prefix = "team" if section == "team_members" else "work"
                uploaded_url = save_uploaded_image(request.files.get("image_file"), prefix)
            except ValueError as error:
                flash(str(error), "error")
                return redirect(url_for("admin_dashboard", tab=section))
            values.append(uploaded_url or request.form.get(field, "").strip())
        else:
            values.append(request.form.get(field, "").strip())
    required = {"services": (0, 1), "works": (0,), "reviews": (0, 1), "treatments": (0, 1, 2), "team_members": (0, 1, 2)}[section]
    if any(not values[index] for index in required):
        flash("Please complete all required fields.", "error")
        return redirect(url_for("admin_dashboard", tab=section))
    with get_db() as db:
        if item_id:
            assignments = ", ".join(f"{field} = ?" for field in fields)
            db.execute(f"UPDATE {section} SET {assignments} WHERE id = ?", (*values, item_id))
            message = "Item updated."
        else:
            columns = ", ".join(fields)
            placeholders = ", ".join("?" for _ in fields)
            db.execute(f"INSERT INTO {section} ({columns}) VALUES ({placeholders})", values)
            message = "Item added."
        db.commit()
    flash(message, "success")
    return redirect(url_for("admin_dashboard", tab=section))


@app.post("/admin/<section>/<int:item_id>/delete")
@login_required
def admin_delete(section, item_id):
    require_csrf()
    if section not in ADMIN_TABLES:
        abort(404)
    with get_db() as db:
        db.execute(f"DELETE FROM {section} WHERE id = ?", (item_id,))
        db.commit()
    flash("Item deleted.", "success")
    return redirect(url_for("admin_dashboard", tab=section))


init_db()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
