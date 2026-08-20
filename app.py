import os
import sqlite3
from datetime import date, datetime
from functools import wraps
from hashlib import sha256

from flask import Flask, flash, g, redirect, render_template, request, session, url_for

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "food-saver-secret-key")
app.config["JSON_SORT_KEYS"] = False

DB_PATH = os.path.join(BASE_DIR, "food_waste.db")

CATEGORIES = [
    "Vegetables",
    "Fruits",
    "Dairy",
    "Meat",
    "Bakery",
    "Grains",
    "Prepared Meals",
    "Other",
]

STORAGE_LOCATIONS = ["Fridge", "Freezer", "Pantry", "Counter"]


def hash_password(password: str) -> str:
    return sha256(password.strip().encode("utf-8")).hexdigest()


def get_db():
    if "db" not in g:
        connection = sqlite3.connect(DB_PATH)
        connection.row_factory = sqlite3.Row
        g.db = connection
    return g.db


@app.teardown_appcontext
def close_db(_exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS food_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            storage_location TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit TEXT NOT NULL,
            purchase_date TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            risk_level TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )

    demo_user = db.execute(
        "SELECT id FROM users WHERE username = ?",
        ("demo",),
    ).fetchone()
    if demo_user is None:
        db.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            ("demo", "demo@foodsaver.app", hash_password("demo123")),
        )
        demo_user = db.execute(
            "SELECT id FROM users WHERE username = ?",
            ("demo",),
        ).fetchone()

    existing_items = db.execute(
        "SELECT COUNT(*) AS count FROM food_items WHERE user_id = ?",
        (demo_user["id"],),
    ).fetchone()["count"]

    if existing_items == 0:
        today = date.today()
        demo_items = [
            (demo_user["id"], "Spinach", "Vegetables", "Fridge", 1.5, "kg", (today).isoformat(), (today).isoformat(), "Medium", "Expiring Soon"),
            (demo_user["id"], "Milk", "Dairy", "Fridge", 2, "liters", (today).isoformat(), (today).isoformat(), "High", "Expiring Soon"),
            (demo_user["id"], "Apples", "Fruits", "Counter", 4, "pcs", (today).isoformat(), (today).isoformat(), "Low", "Fresh"),
            (demo_user["id"], "Bread", "Bakery", "Pantry", 1, "loaf", (today).isoformat(), (today).isoformat(), "Medium", "Fresh"),
        ]
        for item in demo_items:
            db.execute(
                """
                INSERT INTO food_items (
                    user_id, name, category, storage_location, quantity, unit,
                    purchase_date, expiry_date, risk_level, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                item,
            )
    db.commit()


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return get_db().execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


def calculate_risk(category, storage_location, expiry_date):
    try:
        expiry = datetime.strptime(expiry_date, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return "Medium"

    days_left = (expiry - date.today()).days

    if days_left <= 2:
        return "High"
    if days_left <= 5:
        return "Medium"
    if category in ["Vegetables", "Fruits"] and storage_location in ["Counter", "Pantry"]:
        return "Medium"
    return "Low"


def determine_status(expiry_date):
    try:
        expiry = datetime.strptime(expiry_date, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return "Needs review"

    days_left = (expiry - date.today()).days
    if days_left < 0:
        return "Expired"
    if days_left <= 3:
        return "Expiring Soon"
    return "Fresh"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    user = current_user()
    search_query = request.args.get("q", "").strip()
    risk_filter = request.args.get("risk", "All")

    query = "SELECT * FROM food_items WHERE user_id = ?"
    params = [user["id"]]

    if search_query:
        query += " AND name LIKE ?"
        params.append(f"%{search_query}%")

    if risk_filter and risk_filter != "All":
        query += " AND risk_level = ?"
        params.append(risk_filter)

    query += " ORDER BY expiry_date ASC"
    items = db.execute(query, params).fetchall()

    summary = {
        "total_items": len(items),
        "low_risk": sum(1 for item in items if item["risk_level"] == "Low"),
        "medium_risk": sum(1 for item in items if item["risk_level"] == "Medium"),
        "high_risk": sum(1 for item in items if item["risk_level"] == "High"),
        "expiring_soon": sum(1 for item in items if item["status"] == "Expiring Soon"),
    }

    return render_template(
        "dashboard.html",
        items=items,
        summary=summary,
        search_query=search_query,
        risk_filter=risk_filter,
        risk_levels=["All", "Low", "Medium", "High"],
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Both username and password are required.", "danger")
            return render_template("login.html")

        user = get_db().execute(
            "SELECT * FROM users WHERE username = ?",
            (username,),
        ).fetchone()

        if user and user["password_hash"] == hash_password(password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash("Login successful. Welcome back!", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid username or password. Try demo / demo123", "danger")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not email or not password:
            flash("Please complete all fields.", "danger")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        existing_user = get_db().execute(
            "SELECT id FROM users WHERE username = ? OR email = ?",
            (username, email),
        ).fetchone()
        if existing_user:
            flash("This username or email is already registered.", "warning")
            return render_template("register.html")

        get_db().execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, hash_password(password)),
        )
        get_db().commit()
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/add_food", methods=["GET", "POST"])
@login_required
def add_food():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "")
        storage_location = request.form.get("storage_location", "")
        quantity = request.form.get("quantity", "0")
        unit = request.form.get("unit", "units").strip() or "units"
        purchase_date = request.form.get("purchase_date", "")
        expiry_date = request.form.get("expiry_date", "")

        if not all([name, category, storage_location, purchase_date, expiry_date]):
            flash("Please fill in all required fields.", "danger")
            return render_template("add_food.html", categories=CATEGORIES, storage_locations=STORAGE_LOCATIONS)

        try:
            quantity_value = float(quantity)
        except ValueError:
            flash("Quantity must be a valid number.", "danger")
            return render_template("add_food.html", categories=CATEGORIES, storage_locations=STORAGE_LOCATIONS)

        if quantity_value <= 0:
            flash("Quantity must be greater than zero.", "danger")
            return render_template("add_food.html", categories=CATEGORIES, storage_locations=STORAGE_LOCATIONS)

        if expiry_date < purchase_date:
            flash("Expiry date cannot be before purchase date.", "danger")
            return render_template("add_food.html", categories=CATEGORIES, storage_locations=STORAGE_LOCATIONS)

        risk_level = calculate_risk(category, storage_location, expiry_date)
        status = determine_status(expiry_date)

        get_db().execute(
            """
            INSERT INTO food_items (
                user_id, name, category, storage_location, quantity, unit,
                purchase_date, expiry_date, risk_level, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                current_user()["id"],
                name,
                category,
                storage_location,
                quantity_value,
                unit,
                purchase_date,
                expiry_date,
                risk_level,
                status,
            ),
        )
        get_db().commit()
        flash(f"{name} added successfully. Waste risk: {risk_level}.", "success")
        return redirect(url_for("dashboard"))

    return render_template("add_food.html", categories=CATEGORIES, storage_locations=STORAGE_LOCATIONS)


@app.route("/delete_food/<int:item_id>", methods=["POST"])
@login_required
def delete_food(item_id):
    db = get_db()
    item = db.execute(
        "SELECT * FROM food_items WHERE id = ? AND user_id = ?",
        (item_id, current_user()["id"]),
    ).fetchone()

    if item is None:
        flash("Food item not found.", "danger")
        return redirect(url_for("dashboard"))

    db.execute("DELETE FROM food_items WHERE id = ? AND user_id = ?", (item_id, current_user()["id"]))
    db.commit()
    flash(f"{item['name']} removed from your inventory.", "success")
    return redirect(url_for("dashboard"))


@app.route("/reports")
@login_required
def reports():
    db = get_db()
    items = db.execute(
        "SELECT * FROM food_items WHERE user_id = ? ORDER BY expiry_date ASC",
        (current_user()["id"],),
    ).fetchall()

    total_items = len(items)
    category_counts = {}
    risk_counts = {"Low": 0, "Medium": 0, "High": 0}
    status_counts = {"Fresh": 0, "Expiring Soon": 0, "Expired": 0}

    for item in items:
        category_counts[item["category"]] = category_counts.get(item["category"], 0) + 1
        risk_counts[item["risk_level"]] = risk_counts.get(item["risk_level"], 0) + 1
        status_counts[item["status"]] = status_counts.get(item["status"], 0) + 1

    return render_template(
        "reports.html",
        total_items=total_items,
        category_counts=category_counts,
        risk_counts=risk_counts,
        status_counts=status_counts,
    )


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


with app.app_context():
    init_db()


if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
    )
