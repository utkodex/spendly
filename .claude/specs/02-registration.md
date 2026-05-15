# Spec: Registration

## Overview

Wire up the existing `/register` page so visitors can create a Spendly account. The GET handler already renders `register.html`; this step adds the POST handler that validates the submitted name, email, and password, hashes the password with `werkzeug`, inserts the new user into the `users` table, and redirects to the login page on success. This is the first feature that writes user-generated data into the database and unblocks every subsequent authenticated feature (login, profile, expense CRUD).

## Depends on

- Step 01 — Database setup (the `users` table and `get_db()` connection helper must exist).

## Routes

- `GET /register` — render the registration form — public (already exists, keep as-is)
- `POST /register` — process the submitted form, create the user, redirect to `/login` on success or re-render with an error on failure — public

## Database changes

No database changes. The existing `users` table from Step 01 already has the required columns (`name`, `email`, `password_hash`, `created_at`) and the `UNIQUE` constraint on `email`.

## Templates

- **Create:** none
- **Modify:**
  - `templates/register.html` — the form already posts to `/register` and already renders `{{ error }}` inside `.auth-error`. Confirm the markup still works with the new POST handler; no structural changes expected. If success messages are surfaced on `/login` (e.g. "Account created — please sign in"), add a `{% if message %}` block to `templates/login.html` using the existing `auth-error` style or a new `auth-success` class defined via CSS variables.

## Files to change

- `app.py` — replace the single `@app.route("/register")` view with a handler that accepts both `GET` and `POST`, performs validation, inserts the user, and redirects. Add `request`, `redirect`, `url_for`, and `flash`/message handling imports from `flask` as needed.
- `templates/register.html` — only if the existing markup needs a tweak to display server-side validation errors (it already supports `{{ error }}`, so likely no change).
- `templates/login.html` — optional: surface a success message after registration.

## Files to create

None.

## New dependencies

No new dependencies. `werkzeug.security.generate_password_hash` is already imported by `database/db.py` and ships with Flask.

## Rules for implementation

- No SQLAlchemy or ORMs — use `sqlite3` via `get_db()` only.
- Parameterised queries only — never format SQL strings with user input.
- Hash passwords with `werkzeug.security.generate_password_hash` before insert; never store plaintext.
- Always close the DB connection (use `try/finally` or a context manager) and commit explicitly after the insert.
- Trim whitespace on `name` and `email`; lowercase the email before storing and before checking for duplicates.
- Validate on the server even though HTML5 `required` is set on the client:
  - `name` non-empty after stripping
  - `email` non-empty and matches a basic email shape (a single `@` with text on both sides is enough at this stage)
  - `password` at least 8 characters (matches the placeholder hint already in the template)
- Detect duplicate email **before** insert with a `SELECT 1 FROM users WHERE email = ?`, and also catch `sqlite3.IntegrityError` as a fallback in case of a race.
- On validation failure, re-render `register.html` with an `error` string and the previously entered `name` and `email` (never re-render the password).
- On success, redirect (HTTP 302) to `/login` — do not auto-login (session handling is Step 03).
- Use CSS variables from `static/css/style.css` — never hardcode hex values if any new styles are introduced.
- All templates extend `base.html` (the existing ones already do).

## Definition of done

- [ ] `GET /register` still renders the form unchanged.
- [ ] Submitting the form with valid data inserts exactly one row into `users` with a hashed password (verify with `sqlite3 spendly.db "SELECT id, name, email, substr(password_hash,1,20) FROM users ORDER BY id DESC LIMIT 1"`).
- [ ] After a successful submission, the browser is redirected to `/login` (302 response).
- [ ] Submitting with an email that already exists re-renders `register.html` with a visible error message and does not create a duplicate row.
- [ ] Submitting with an empty name, malformed email, or password shorter than 8 characters re-renders the form with a specific error and preserves `name` and `email`.
- [ ] The `password` field is never echoed back into the form.
- [ ] Passwords stored in the DB start with the `werkzeug` scheme prefix (e.g. `pbkdf2:sha256:` or `scrypt:`), confirming hashing.
- [ ] App starts and the existing seeded demo user (`demo@spendly.com`) is still rejected as a duplicate on registration.
- [ ] No SQL string concatenation introduced; every query uses `?` placeholders.
