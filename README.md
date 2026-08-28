# URL Shortener API

A basic URL shortener built with **FastAPI** and **PostgreSQL**. Given a long URL,
the API generates a short, random alphanumeric code and stores the mapping in
Postgres. Visiting the short code redirects the caller to the original URL.

## Features

- `POST /shorten` — accepts a long URL and returns a shortened URL
- `GET /{short_code}` — redirects (HTTP 307) to the original URL
- `GET /api/stats/{short_code}` — bonus endpoint that returns the mapping's
  metadata (original URL, visit count, creation time) without redirecting,
  useful for verifying behavior while testing
- Duplicate URLs reuse the same short code instead of creating a new row
- Visit counting on every redirect
- Auto-generated interactive API docs via FastAPI at `/docs`

## Tech Stack

- **FastAPI** — web framework and request/response validation
- **PostgreSQL** — persistent storage for URL mappings
- **SQLAlchemy** — ORM / database access layer
- **Pydantic** — request and response schema validation
- **Uvicorn** — ASGI server

## Project Structure

```
url-shortener/
├── app/
│   ├── __init__.py
│   ├── main.py        # FastAPI app and route handlers
│   ├── models.py       # SQLAlchemy ORM model (URLMapping)
│   ├── schemas.py       # Pydantic request/response schemas
│   ├── database.py      # DB engine, session, and Base
│   └── utils.py         # Short code generation helper
├── requirements.txt
├── .env.example
└── README.md
```

## How It Works

1. `POST /shorten` receives a JSON body `{ "url": "<long url>" }`. Pydantic's
   `HttpUrl` type validates that it is a well-formed URL.
2. The API checks if that exact URL has already been shortened. If so, it
   returns the existing short code (avoids duplicate rows for the same URL).
3. Otherwise, it generates a random 6-character alphanumeric code
   (`utils.generate_short_code`), inserts a new row into the `url_mappings`
   table, and retries (up to 5 times) on the rare chance of a collision on
   the `short_code` unique constraint.
4. `GET /{short_code}` looks up the code in the database. If found, it
   increments `visit_count` and issues an HTTP redirect to the
   `original_url`. If not found, it returns a `404`.

### Database Schema

Table: `url_mappings`

| Column        | Type          | Notes                          |
|---------------|---------------|---------------------------------|
| id            | Integer (PK)  | Auto-incrementing primary key   |
| short_code    | String(10)    | Unique, indexed                 |
| original_url  | String(2048)  | The long URL                    |
| created_at    | DateTime      | Set automatically on insert     |
| visit_count   | Integer       | Incremented on each redirect    |

The table is created automatically on application startup
(`Base.metadata.create_all`), so no manual migration step is required for
this assessment-sized project.

## Setup & Running Locally

### Prerequisites

- Python 3.10+
- PostgreSQL running locally (or accessible via a connection string)

### 1. Clone / unzip the project and install dependencies

```bash
cd url-shortener
python -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Create the PostgreSQL database

```bash
psql -U postgres -c "CREATE DATABASE url_shortener;"
```

### 3. Configure the connection string

Copy `.env.example` to `.env` and adjust if your Postgres credentials differ,
or simply export the variable directly:

```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/url_shortener"
```

If `DATABASE_URL` is not set, the app defaults to
`postgresql://postgres:postgres@localhost:5432/url_shortener`.

### 4. Run the server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`, with interactive
Swagger docs at `http://localhost:8000/docs`.

## Example Usage

**Shorten a URL:**

```bash
curl -X POST http://localhost:8000/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.example.com/some/very/long/path"}'
```

Response:

```json
{
  "short_code": "aZ3xQ1",
  "short_url": "http://localhost:8000/aZ3xQ1",
  "original_url": "https://www.example.com/some/very/long/path",
  "created_at": "2026-08-27T12:00:00"
}
```

**Follow the short URL:**

```bash
curl -L http://localhost:8000/aZ3xQ1
```

This redirects to the original URL.

**Check stats:**

```bash
curl http://localhost:8000/api/stats/aZ3xQ1
```

## Design Decisions

- **Random short codes over sequential IDs**: sequential IDs (e.g. base62
  of the row id) would leak how many URLs exist and be easy to guess/scan.
  Random 6-character codes (62^6 ≈ 56 billion combinations) keep codes
  short while avoiding that.
- **Deduplication on `original_url`**: shortening the same URL twice returns
  the existing code rather than creating redundant rows.
- **307 redirect** (instead of 301/302): preserves the HTTP method of the
  original request and avoids browsers/CDNs permanently caching the
  redirect target, which matters if a mapping's target were ever updated.
- **Dependency-injected DB sessions** (`Depends(get_db)`): keeps each
  request's session properly scoped and closed, following FastAPI's
  recommended pattern for SQLAlchemy.

## Testing

The endpoints were manually verified end-to-end (shorten → redirect →
stats → 404 on unknown code → duplicate URL reuse) during development.
For a production version, `pytest` + `httpx`/`TestClient` with a test
database would be the natural next step.

## Possible Extensions (not implemented, out of scope for this assessment)

- Custom/user-chosen short codes
- URL expiration (TTL)
- Rate limiting
- Authentication for creating links
- Alembic migrations instead of `create_all`
