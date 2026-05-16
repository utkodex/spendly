import os
import re
import sqlite3

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import get_db, init_db, seed_db
from database.queries import (
    get_user_by_id,
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown,
)

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

    user_id = session["user_id"]

    # === SECTION A: USER + STATS (Subagent 2) ============================
    # Fills `user` and `stats` dicts from get_user_by_id + get_summary_stats.
    # Adds UI extras:
    #   - user["initials"]: first letter of each whitespace-split name part,
    #     uppercased, max 2 chars.
    #   - stats["top_category_key"]: top_category.lower() ("other" when "—").
    user = get_user_by_id(user_id)
    if user is None:
        return redirect(url_for("logout"))
    parts = user["name"].split()
    user["initials"] = "".join(p[0] for p in parts).upper()[:2]

    stats = get_summary_stats(user_id)
    top_category = stats["top_category"]
    stats["top_category_key"] = "other" if top_category == "—" else top_category.lower()
    stats["total_spent"] = "%.2f" % stats["total_spent"]
    # === END SECTION A ==================================================

    # === SECTION B: TRANSACTIONS (Subagent 1) ============================
    # Calls get_recent_transactions(user_id, limit=10) and adapts each row:
    #   - date: parse "YYYY-MM-DD" -> "DD Mon" (e.g. "16 May")
    #   - key:  category.lower()
    #   - amount: "%.2f" formatted string
    from datetime import datetime
    transactions = [
        {
            "date": datetime.strptime(row["date"], "%Y-%m-%d").strftime("%d %b"),
            "description": row["description"],
            "category": row["category"],
            "key": row["category"].lower(),
            "amount": "%.2f" % row["amount"],
        }
        for row in get_recent_transactions(user_id, limit=10)
    ]
    # === END SECTION B ==================================================

    # === SECTION C: CATEGORIES (Subagent 3) ==============================
    # Calls get_category_breakdown(user_id) and adapts each row:
    #   - rename `amount` -> `total` (string, "%.2f")
    #   - rename `pct`    -> `percent`
    #   - add `key`: name.lower()
    categories = [
        {
            "name": row["name"],
            "key": row["name"].lower(),
            "total": "%.2f" % row["amount"],
            "percent": row["pct"],
        }
        for row in get_category_breakdown(user_id)
    ]
    # === END SECTION C ==================================================

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
