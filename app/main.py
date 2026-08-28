from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import engine, get_db, Base
from app import models, schemas
from app.utils import generate_short_code

# Create tables on startup if they don't already exist.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="URL Shortener API",
    description="A basic URL shortener built with FastAPI and PostgreSQL.",
    version="1.0.0",
)

BASE_URL = "http://localhost:8000"
MAX_GENERATION_ATTEMPTS = 5


@app.post("/shorten", response_model=schemas.URLShortenResponse, status_code=201)
def shorten_url(payload: schemas.URLShortenRequest, db: Session = Depends(get_db)):
    """
    Accept a long URL and return a shortened version of it.

    If the same URL has already been shortened, the existing short
    code is returned instead of creating a duplicate entry.
    """
    original_url = str(payload.url)

    # Return the existing mapping if this URL was shortened before.
    existing = (
        db.query(models.URLMapping)
        .filter(models.URLMapping.original_url == original_url)
        .first()
    )
    if existing:
        return _to_response(existing)

    # Try a few times in case of a rare short_code collision.
    for _ in range(MAX_GENERATION_ATTEMPTS):
        code = generate_short_code()
        mapping = models.URLMapping(short_code=code, original_url=original_url)
        db.add(mapping)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            continue
        db.refresh(mapping)
        return _to_response(mapping)

    raise HTTPException(
        status_code=500,
        detail="Could not generate a unique short code, please try again.",
    )


@app.get("/{short_code}")
def redirect_to_original(short_code: str, db: Session = Depends(get_db)):
    """
    Redirect the caller to the original long URL for the given short code.
    """
    mapping = (
        db.query(models.URLMapping)
        .filter(models.URLMapping.short_code == short_code)
        .first()
    )
    if mapping is None:
        raise HTTPException(status_code=404, detail="Short URL not found.")

    mapping.visit_count += 1
    db.commit()

    return RedirectResponse(url=mapping.original_url, status_code=307)


@app.get("/api/stats/{short_code}", response_model=schemas.URLStatsResponse)
def get_stats(short_code: str, db: Session = Depends(get_db)):
    """
    Bonus endpoint: return metadata about a short code without redirecting.
    Useful for verifying the mapping and visit count during testing.
    """
    mapping = (
        db.query(models.URLMapping)
        .filter(models.URLMapping.short_code == short_code)
        .first()
    )
    if mapping is None:
        raise HTTPException(status_code=404, detail="Short URL not found.")
    return mapping


def _to_response(mapping: models.URLMapping) -> schemas.URLShortenResponse:
    return schemas.URLShortenResponse(
        short_code=mapping.short_code,
        short_url=f"{BASE_URL}/{mapping.short_code}",
        original_url=mapping.original_url,
        created_at=mapping.created_at,
    )
