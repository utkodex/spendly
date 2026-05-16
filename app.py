import os
import re
import sqlite3

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import get_db, init_db, seed_db

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

app = Flask(__name__)
# Dev fallback only — override SPENDLY_SECRET_KEY in production.
app.secret_key = os.environ.get("SPENDLY_SECRET_KEY", "dev-secret-change-me")

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    if session.get("user_id"):
        return redirect(url_for("profile"))
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("profile"))

    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    error = None
    if not name:
        error = "Please enter your name."
    elif not EMAIL_RE.match(email):
        error = "Please enter a valid email address."
    elif len(password) < 8:
        error = "Password must be at least 8 characters."

    if error is None:
        conn = get_db()
        try:
            existing = conn.execute(
                "SELECT 1 FROM users WHERE email = ?", (email,)
            ).fetchone()
            if existing:
                error = "An account with that email already exists."
            else:
                try:
                    conn.execute(
                        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                        (name, email, generate_password_hash(password)),
                    )
                    conn.commit()
                except sqlite3.IntegrityError:
                    error = "An account with that email already exists."
        finally:
            conn.close()

    if error:
        return render_template("register.html", error=error, name=name, email=email)

    return redirect(url_for("login", registered=1))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("profile"))

    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if email and password:
        conn = get_db()
        try:
            row = conn.execute(
                "SELECT id, name, password_hash FROM users WHERE email = ?", (email,)
            ).fetchone()
        finally:
            conn.close()

        if row and check_password_hash(row["password_hash"], password):
            session["user_id"] = row["id"]
            session["user_name"] = row["name"]
            return redirect(url_for("profile"))

    return render_template(
        "login.html", error="Invalid email or password.", email=email
    )


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("user_name", None)
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user = {
        "name": "Demo User",
        "email": "demo@spendly.com",
        "initials": "DU",
        "member_since": "January 2026",
    }

    stats = {
        "total_spent": "8,420",
        "transaction_count": 8,
        "top_category": "Bills",
        "top_category_key": "bills",
    }

    transactions = [
        {"date": "16 May", "description": "Electricity bill",       "category": "Bills",         "key": "bills",         "amount": "1,200"},
        {"date": "14 May", "description": "Weekly groceries",       "category": "Food",          "key": "food",          "amount": "640"},
        {"date": "12 May", "description": "Metro card top-up",      "category": "Transport",     "key": "transport",     "amount": "300"},
        {"date": "11 May", "description": "Movie night",            "category": "Entertainment", "key": "entertainment", "amount": "450"},
        {"date": "09 May", "description": "Pharmacy run",           "category": "Health",        "key": "health",        "amount": "220"},
        {"date": "06 May", "description": "Cotton kurta",           "category": "Shopping",      "key": "shopping",      "amount": "1,150"},
        {"date": "04 May", "description": "Cafe with Riya",         "category": "Food",          "key": "food",          "amount": "380"},
        {"date": "02 May", "description": "Streaming subscription", "category": "Other",         "key": "other",         "amount": "199"},
    ]

    categories = [
        {"name": "Bills",         "key": "bills",         "total": "3,200", "percent": 38},
        {"name": "Food",          "key": "food",          "total": "1,840", "percent": 22},
        {"name": "Shopping",      "key": "shopping",      "total": "1,150", "percent": 14},
        {"name": "Entertainment", "key": "entertainment", "total": "650",   "percent": 8},
        {"name": "Transport",     "key": "transport",     "total": "560",   "percent": 7},
        {"name": "Health",        "key": "health",        "total": "440",   "percent": 5},
        {"name": "Other",         "key": "other",         "total": "380",   "percent": 4},
    ]

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        categories=categories,
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
