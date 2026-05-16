# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project context

Spendly is a teaching scaffold for a Flask + SQLite expense tracker. It's built step-by-step from numbered specs in `.claude/specs/`. Each step lives on its own `feature/<slug>` branch and corresponds to one spec file. Current progress is tracked by which specs exist and what's wired up in `app.py`:

- `01-database-setup` — schema + seed (done)
- `02-registration` — done
- `03-login-and-logout` — done
- `04-profile-page-design` — **in progress** on `feature/profile-page-design`
- Anything beyond is still a stub route in `app.py` returning a placeholder string

When implementing the current step, always read its spec in `.claude/specs/` first — specs are the source of truth for routes, schema, templates, and the definition of done.

## Common commands

PowerShell (the default shell on this machine):

```powershell
# One-time setup
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Run the dev server (auto-creates and seeds spendly.db on first start)
python app.py            # serves on http://localhost:5001 with debug=True

# Run a single test (pytest + pytest-flask are installed; no test suite yet)
pytest path/to/test_file.py::test_name -q

# Seed helpers
python scripts/seed_user.py    # inserts one random Indian-name user (password: password123)
```

Slash commands defined in `.claude/commands/`:

- `/create-spec <step> <feature name>` — clean-tree guard, creates `feature/<slug>` branch off `main` and writes a spec to `.claude/specs/<NN>-<slug>.md`. Don't skip its preflight checks.
- `/code-review-feature <spec-name>` — runs security + quality reviewers in parallel against `git diff` for the spec. Won't edit anything without explicit user approval.
- `/seed-user`, `/seed-expense` — generate dummy data via raw `sqlite3` using `database/db.get_db()`.

## Architecture

Single-process Flask app, no blueprints, no ORM, no factory. Everything wires through `app.py`:

- **`app.py`** — all routes; calls `init_db()` and `seed_db()` inside `app.app_context()` at import time so the dev DB exists before the first request. Secret key comes from `SPENDLY_SECRET_KEY` (fallback is dev-only).
- **`database/db.py`** — `get_db()` returns a fresh `sqlite3` connection per call with `row_factory = sqlite3.Row` and `PRAGMA foreign_keys = ON`. **Always close connections in a `try/finally`** — the existing routes follow this pattern; mirror it. The DB file is `spendly.db` at the project root (path is computed from `__file__`, not hardcoded).
- **`templates/`** — Jinja, all extending `base.html`. The navbar swaps Sign in/Sign out based on `session.get('user_id')`. The footer links to `/terms` and `/privacy`.
- **`static/css/style.css`** — shared site styles. **All colors come from CSS variables** declared in `:root` (`--ink`, `--paper`, `--accent`, `--danger`, etc.). Page-specific CSS (e.g. `landing.css`) is pulled in via `{% block head %}`.

### Schema (defined in `database/db.py`)

- `users(id, name, email UNIQUE, password_hash, created_at)`
- `expenses(id, user_id FK → users.id, amount REAL, category, date TEXT 'YYYY-MM-DD', description, created_at)`

### Fixed expense categories

Use exactly: `Food, Transport, Bills, Health, Entertainment, Shopping, Other`. These are the only allowed `category` values throughout the app (forms, seeds, badges).

## Hard rules for implementation

These come from the specs and apply to every feature:

- **No SQLAlchemy or any ORM** — use `sqlite3` via `get_db()`.
- **Parameterised queries only** — never string-format or f-string SQL.
- **Passwords hashed with `werkzeug.security`** (`generate_password_hash` / `check_password_hash`).
- **Foreign keys must be enforced** — `get_db()` already sets the pragma; don't bypass it.
- **All templates extend `base.html`.** No standalone HTML pages.
- **CSS variables only — never hardcode hex values** in templates or new CSS. Add a new variable in `:root` if you need a new color.
- **No inline styles.** Category badges and similar must use CSS classes.
- **Auth guard:** protected routes check `session.get("user_id")` and `redirect(url_for("login"))` when absent. Email validation uses the `EMAIL_RE` already in `app.py`; minimum password length is 8.
- **Currency is ₹ (INR)** — use it consistently in UI copy and mock data.

## Workflow conventions

- Work on a feature branch named `feature/<slug>` created by `/create-spec`. Don't commit directly to `main`.
- `.claude/plans/` is gitignored — use it as a scratchpad. `.claude/specs/` is committed and is the contract.
- The `/profile`, `/expenses/add`, `/expenses/<id>/edit`, `/expenses/<id>/delete` routes are intentionally stubs until their step lands. Don't "fix" them outside of their assigned step.
- Don't commit `spendly.db` changes from local seeding unless that's the point of the change — the DB is auto-seeded on first run.
