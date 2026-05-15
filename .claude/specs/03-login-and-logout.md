# Spec: Login and Logout

## Overview

Wire up real session-based authentication for Spendly. Visitors can already register an account (Step 02) but the `/login` route only renders the form and `/logout` is a placeholder string. This step implements the `POST /login` handler that verifies the submitted email/password against the `users` table using `werkzeug.security.check_password_hash`, establishes a Flask session keyed by `user_id`, and clears that session on `GET /logout`. It also makes the navbar reflect the authenticated state. Sessions unblock every authenticated feature that follows: profile (Step 04) and the expense CRUD routes.

## Depends on

- Step 01 — Database setup (`users` table and `get_db()` connection helper).
- Step 02 — Registration (so there is a way to create accounts with hashed passwords for login to verify against).

## Routes

- `GET /login` — render the sign-in form — public (already exists, keep as-is but accept GET on the same view function).
- `POST /login` — verify credentials, set `session["user_id"]`, redirect to `/profile` on success or re-render `login.html` with an error on failure — public.
- `GET /logout` — clear the session and redirect to `/` (landing) — logged-in (silently redirects to `/` even if not logged in; no error).

## Database changes

No database changes. Step 01 already stores `password_hash` on `users` with a `UNIQUE` constraint on `email`, which is all login needs.

## Templates

- **Create:** none.
- **Modify:**
  - `templates/login.html` — the form already POSTs to `/login`, renders `{{ error }}` inside `.auth-error`, and shows the post-registration success banner via `request.args.get('registered')`. Add a hidden-but-preserved `value="{{ email or '' }}"` on the email input so a failed login keeps the email the user typed. No other structural changes.
  - `templates/base.html` — replace the static "Sign in" / "Get started" nav links with a `{% if session.get('user_id') %}` block that shows a "Sign out" link pointing to `url_for('logout')` (and optionally a "Profile" link to `url_for('profile')`) when logged in, and keeps the existing Sign in / Get started links when logged out.

## Files to change

- `app.py`
  - Set `app.secret_key` from an environment variable `SPENDLY_SECRET_KEY` with a deterministic dev fallback (e.g. `"dev-secret-change-me"`) so Flask sessions work locally without extra setup. Import `os` for this.
  - Import `session` from `flask` and `check_password_hash` from `werkzeug.security`.
  - Replace the existing `@app.route("/login")` view (currently GET-only, returning the template) with a single view that handles both `GET` and `POST`:
    - `GET` → render `login.html` (unchanged behaviour).
    - `POST` → trim/lowercase the submitted email, look up the user with a parameterised `SELECT id, password_hash FROM users WHERE email = ?`, verify the password with `check_password_hash`, set `session["user_id"]`, and redirect to `url_for("profile")`. On any failure (missing fields, no such user, wrong password) re-render `login.html` with a single generic error: `"Invalid email or password."` — never reveal whether the email exists.
  - Replace the placeholder `/logout` handler with one that calls `session.pop("user_id", None)` (or `session.clear()`) and returns `redirect(url_for("landing"))`. Accept `GET` (a plain `<a href>` in the navbar must work).
- `templates/login.html` — preserve the submitted email on re-render after a failed POST (see Templates above).
- `templates/base.html` — conditional nav links based on `session.get('user_id')` (see Templates above).

## Files to create

None.

## New dependencies

No new dependencies. `flask.session` and `werkzeug.security.check_password_hash` ship with the existing pinned versions in `requirements.txt`.

## Rules for implementation

- No SQLAlchemy or ORMs — use `sqlite3` via `get_db()` only.
- Parameterised queries only — never format SQL with user input.
- Verify passwords with `werkzeug.security.check_password_hash` against the stored `password_hash`; never compare plaintext or re-hash for comparison.
- Always close the DB connection in a `try/finally` after the lookup.
- Trim whitespace on `email` and lowercase it before the DB lookup so login matches the casing used at registration.
- Server-side validation: if either field is empty after stripping, treat it as an invalid credential and show the same generic error — do not branch the error message on which field was missing.
- Use a single generic error message for all login failures (missing fields, unknown email, wrong password) — exposing "no such user" leaks account existence.
- Set `app.secret_key` before any request handler runs; read it from `os.environ.get("SPENDLY_SECRET_KEY", "dev-secret-change-me")`. The fallback is for local dev only — leave a short comment noting it must be overridden in production.
- Store only the user's `id` in the session (`session["user_id"]`). Do not put the email, name, or password hash in the session.
- On successful login redirect with HTTP 302 to `url_for("profile")` — even though `/profile` is still a Step 04 placeholder, the redirect target is correct.
- On `/logout`, always redirect (302) to `url_for("landing")`; do not render a "you have been logged out" page.
- The `password` field is never echoed back into the form on a failed POST; the `email` value is.
- Use CSS variables from `static/css/style.css` — never hardcode hex values if any new styles are introduced (the existing `.auth-error` / `.auth-success` classes should be sufficient).
- All templates extend `base.html` (the existing ones already do).
- Do not introduce `flash()` messaging in this step — login uses the existing `error=` re-render pattern from Step 02 for consistency.

## Definition of done

- [ ] `GET /login` still renders the sign-in form unchanged, including the "Account created — please sign in." banner when arriving from `/register?registered=1`.
- [ ] `POST /login` with the seeded demo credentials (`demo@spendly.com` / `demo123`) sets `session["user_id"]` and redirects (302) to `/profile`.
- [ ] `POST /login` with a freshly registered account (created via the Step 02 flow) logs in successfully — confirming the password hash written at registration round-trips through `check_password_hash`.
- [ ] `POST /login` with a wrong password re-renders `login.html` with the error `"Invalid email or password."` and preserves the entered `email`. No `user_id` is set in the session.
- [ ] `POST /login` with an unknown email shows the same generic `"Invalid email or password."` error — the response does not differ between "no such user" and "wrong password" (verifiable by comparing the two responses).
- [ ] `POST /login` with an empty email or empty password re-renders with the same generic error.
- [ ] The `password` field is never re-populated in the form after a failed login.
- [ ] `GET /logout` clears `session["user_id"]` and redirects (302) to `/`. Calling `/logout` while already logged out still redirects to `/` without error.
- [ ] After logging in, the navbar shows a "Sign out" link (and any other logged-in-only links) instead of "Sign in" / "Get started". After logging out, it reverts.
- [ ] `app.secret_key` is set from `SPENDLY_SECRET_KEY` if present, otherwise from the documented dev fallback; running the app without the env var still works locally.
- [ ] Only the user's `id` is stored in the Flask session cookie — no email, name, or hash (inspect `session` contents during a request or decode the cookie).
- [ ] No SQL string concatenation introduced; every query uses `?` placeholders.
- [ ] App starts and all existing routes (`/`, `/register`, `/terms`, `/privacy`) continue to work.
