# Basic Banking API

A secure REST API for user registration and login, account access, deposits, withdrawals,
and transfers. It uses FastAPI, SQLite, SQLAlchemy, Pydantic validation, JWT authentication,
and password hashing. Swagger documentation is available at `/docs`.

## 1. Project overview
A REST API for a basic banking application. Users can register, log in, view their
account, deposit, withdraw, transfer money to another account, see their transaction
history and log out. Every protected endpoint needs a JWT.

## Project layout
The root `main.py` exposes the FastAPI application for `uvicorn main:app --reload`.
Inside `app/`, HTTP routes live in `api/`, SQLAlchemy tables in `models/`, validation
in `schemas/`, database setup in `db/`, settings and security helpers in `core/`, and
banking rules in `services/`. Database queries are kept in `repositories/`.

## 2. Technology stack
- Python 3.11+
- FastAPI (web framework, generates Swagger docs)
- SQLAlchemy 2.x (ORM) with SQLite (PostgreSQL / MySQL work by changing `DATABASE_URL`)
- Pydantic v2 (request / response validation)
- PyJWT (tokens) and bcrypt (password hashing)
- pytest + httpx (tests)

## 3. Prerequisites
- Python 3.11 or newer
- Git

## 4. Installation instructions
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

## 5. Environment variables
Open `.env` and replace `SECRET_KEY` with a private random value. Generate one with:
```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```
| Variable | Meaning |
|---|---|
| DATABASE_URL | Database connection string (default `sqlite:///./bank.db`) |
| SECRET_KEY | Long random string used to sign JWTs (required) |
| ALGORITHM | JWT signing algorithm (default `HS256`) |
| ACCESS_TOKEN_EXPIRE_MINUTES | Token lifetime in minutes (default `30`) |

## 6. Database setup
Nothing to run manually. Tables are created automatically when the app starts.
With SQLite the file `bank.db` appears in the project folder on first start.

## 7. How to run the application
```powershell
uvicorn main:app --reload
```
Run this from the project folder, beside `requirements.txt` and `main.py`. The API is
available at http://127.0.0.1:8000.

## 8. API documentation
Swagger UI: http://127.0.0.1:8000/docs (ReDoc: `/redoc`).
To try protected operations, register a user and log in. Copy the returned `accessToken`,
click **Authorize** in Swagger, and enter the token. Deposit and withdrawal requests use
`amount`; transfers use `receiverAccountId` and `amount`.

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | /api/auth/register | No | Register a user (an account is created automatically) |
| POST | /api/auth/login | No | Get a JWT access token |
| POST | /api/auth/logout | Yes | Revoke the current token |
| GET | /api/account | Yes | Current user's account details |
| POST | /api/deposit | Yes | Deposit money |
| POST | /api/withdraw | Yes | Withdraw money |
| POST | /api/transfer | Yes | Transfer to another account id |
| GET | /api/accounts/transactions | Yes | Current user's transaction history |

The former `/api/accounts/me`, `/api/accounts/deposit`, `/api/accounts/withdraw`, and
`/api/accounts/transfer` paths remain available for existing clients.

If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
in that terminal, then activate the virtual environment again.

## 9. Authentication approach (including logout strategy)
- Passwords are hashed with bcrypt. Plain passwords are never stored or logged.
- Login returns a signed JWT (`sub` = user id, `exp`, and a unique `jti`) that is sent as
  `Authorization: Bearer <token>`.
- Missing, invalid, expired or revoked tokens return `401 Unauthorized`.
- **Logout strategy: token blacklist.** JWTs are stateless, so on logout the token's
  `jti` is stored in the `blacklisted_tokens` table. Every request checks that table, so a
  logged-out token stops working immediately. Rows are deleted once the token would have
  expired anyway. Access tokens are also short lived (30 minutes by default).

## 10. Database design
- `users`: id, name, email (unique), password_hash, created_at
- `accounts`: id, user_id (unique, FK), account_number (unique), balance, created_at
- `transactions`: id, account_id (FK), type, amount, status, reference_id, created_at
- `blacklisted_tokens`: id, jti (unique), expires_at

One user has one account. Money uses `Numeric(12, 2)` (never float) and a database
`CHECK (balance >= 0)` guards against negative balances.

## 11. Design decisions
- **Layers:** api (HTTP) -> services (business rules) -> repositories (database queries).
- **Atomic transfers:** debit, credit and both transaction rows happen in one database
  transaction with a single `commit()`. Any error triggers `rollback()`.
- **Concurrency:** account rows are locked with `SELECT ... FOR UPDATE` and, in a transfer,
  always in ascending id order so two opposite transfers cannot deadlock.
- **Transfers create two history rows** (`TRANSFER_DEBIT` for sender, `TRANSFER_CREDIT` for
  receiver) that share a `reference_id`, so each user only sees their own side.
- **Errors:** 400 business rule broken, 401 auth problem, 404 not found, 409 duplicate
  email, 422 validation, 500 generic message (details only go to the server log).
- **Login errors are generic** ("Invalid email or password") so attackers cannot discover
  which emails are registered.

## 12. How to run tests
```bash
python -m pytest -v
```
Tests use an in-memory SQLite database, so your real data is never touched.

## 13. Known limitations
- SQLite ignores `FOR UPDATE`; it serialises writes instead. Use PostgreSQL for true
  row-level locking under heavy concurrency.
- Tables are created with `create_all`, not migrations.
- No refresh tokens, rate limiting or pagination.
- One account per user.
