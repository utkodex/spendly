"""Pure query helpers for the Spendly profile page.

Each helper opens a connection via ``database.db.get_db()`` and closes it
in a ``try/finally`` before returning. No Flask imports here — these are
plain functions so they can be unit-tested without a request context.
"""

from database.db import get_db
from datetime import datetime


def get_user_by_id(user_id):
    """Return ``{"name", "email", "member_since"}`` or ``None``.

    ``member_since`` is ``users.created_at`` formatted as "Month YYYY".
    """
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT name, email, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None

    try:
        created = datetime.fromisoformat(row["created_at"])
    except ValueError:
        created = datetime.strptime(row["created_at"], "%Y-%m-%d %H:%M:%S")

    return {
        "name": row["name"],
        "email": row["email"],
        "member_since": created.strftime("%B %Y"),
    }


def get_summary_stats(user_id):
    """Return ``{"total_spent", "transaction_count", "top_category"}``.

    For a user with no expenses, returns zeros and ``top_category = "—"``.
    """
    conn = get_db()
    try:
        agg = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS cnt "
            "FROM expenses WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        top = conn.execute(
            "SELECT category, SUM(amount) AS total FROM expenses "
            "WHERE user_id = ? GROUP BY category ORDER BY total DESC LIMIT 1",
            (user_id,),
        ).fetchone()
    finally:
        conn.close()

    if agg["cnt"] == 0:
        return {"total_spent": 0, "transaction_count": 0, "top_category": "—"}

    return {
        "total_spent": float(agg["total"]),
        "transaction_count": agg["cnt"],
        "top_category": top["category"] if top else "—",
    }


def get_recent_transactions(user_id, limit=10):
    """Return a list of ``{"date", "description", "category", "amount"}``
    ordered newest-first. Empty list when the user has no expenses.
    """
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT date, description, category, amount FROM expenses "
            "WHERE user_id = ? ORDER BY date DESC, id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return [
            {
                "date": row["date"],
                "description": row["description"],
                "category": row["category"],
                "amount": row["amount"],
            }
            for row in rows
        ]
    finally:
        conn.close()


def get_category_breakdown(user_id):
    """Return a list of ``{"name", "amount", "pct"}`` ordered by amount
    descending. ``pct`` values are integers summing to 100 (the largest
    category absorbs any rounding remainder). Empty list when none.
    """
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT category, SUM(amount) AS total FROM expenses "
            "WHERE user_id = ? GROUP BY category ORDER BY total DESC",
            (user_id,),
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        return []

    result = [
        {"name": row["category"], "amount": float(row["total"]), "pct": 0}
        for row in rows
    ]
    grand_total = sum(item["amount"] for item in result)
    for item in result:
        item["pct"] = round(item["amount"] / grand_total * 100)

    delta = 100 - sum(item["pct"] for item in result)
    if delta:
        result[0]["pct"] += delta

    return result
