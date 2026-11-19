
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, Depends, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import update

from app.database import get_db
from app.models import URL
from app.schemas import (
    URLCreate,
    URLResponse,
    URLDetailResponse,
    URLAnalyticsResponse
)
from app.utils import encode_base62


app = FastAPI(
    title="URL Shortener API",
    description="""
    A URL shortening service built using FastAPI and PostgreSQL.

    Features:
    - Create short URLs
    - Redirect to original URLs
    - Track clicks
    - URL expiration
    - URL analytics
    - Delete short URLs
    """,
    version="1.0.0",
    contact={
        "name": "API Developer"
    }
)


# Health check
@app.get(
    "/",
    summary="Health check",
    description="Check whether the URL Shortener API is running."
)
def home():
    return {"message": "URL Shortener API is running"}


# Create a short URL
@app.post(
    "/api/shorten",
    response_model=URLResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a short URL",
    description="Convert a long URL into a unique short URL. An optional expiration date can be provided."
)
def shorten_url(
    data: URLCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        new_url = URL(
            short_code="p" + uuid4().hex[:19],
            original_url=str(data.url),
            expires_at=data.expires_at
        )

        db.add(new_url)
        db.flush()

        new_url.short_code = encode_base62(new_url.id)

        db.commit()
        db.refresh(new_url)

        short_url = (
            f"{str(request.base_url).rstrip('/')}/"
            f"{new_url.short_code}"
        )

        return URLResponse(
            short_code=new_url.short_code,
            short_url=short_url
        )

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database operation failed"
        )


# Redirect and track clicks
@app.get(
    "/{short_code}",
    summary="Redirect to original URL",
    description="Redirect to the original URL and increment its click count. Returns 410 if the URL has expired."
)
def redirect_url(
    short_code: str,
    db: Session = Depends(get_db)
):
    url_record = db.query(URL).filter(
        URL.short_code == short_code
    ).first()

    if url_record is None:
        raise HTTPException(
            status_code=404,
            detail="Short URL not found"
        )

    # Check whether the URL has expired
    if (
        url_record.expires_at is not None
        and url_record.expires_at <= datetime.now(timezone.utc)
    ):
        raise HTTPException(
            status_code=410,
            detail="This short URL has expired"
        )

    # Atomically increase click count
    db.execute(
        update(URL)
        .where(URL.id == url_record.id)
        .values(
            click_count=URL.click_count + 1
        )
    )

    db.commit()

    return RedirectResponse(
        url=url_record.original_url,
        status_code=302
    )


# Retrieve URL details
@app.get(
    "/api/urls/{short_code}",
    response_model=URLDetailResponse,
    summary="Get URL details",
    description="Retrieve information about a shortened URL."
)
def get_url_details(
    short_code: str,
    db: Session = Depends(get_db)
):
    url_record = db.query(URL).filter(
        URL.short_code == short_code
    ).first()

    if url_record is None:
        raise HTTPException(
            status_code=404,
            detail="Short URL not found"
        )

    return URLDetailResponse(
        short_code=url_record.short_code,
        original_url=url_record.original_url,
        created_at=url_record.created_at
    )


# Retrieve URL analytics
@app.get(
    "/api/analytics/{short_code}",
    response_model=URLAnalyticsResponse,
    summary="Get URL analytics",
    description="Retrieve click statistics and other analytics for a shortened URL."
)
def get_url_analytics(
    short_code: str,
    db: Session = Depends(get_db)
):
    url_record = db.query(URL).filter(
        URL.short_code == short_code
    ).first()

    if url_record is None:
        raise HTTPException(
            status_code=404,
            detail="Short URL not found"
        )

    return URLAnalyticsResponse(
        short_code=url_record.short_code,
        original_url=url_record.original_url,
        total_clicks=url_record.click_count,
        created_at=url_record.created_at
    )


# Delete a short URL
@app.delete(
    "/api/urls/{short_code}",
    summary="Delete a short URL",
    description="Permanently delete a shortened URL from the database."
)
def delete_url(
    short_code: str,
    db: Session = Depends(get_db)
):
    url_record = db.query(URL).filter(
        URL.short_code == short_code
    ).first()

    if url_record is None:
        raise HTTPException(
            status_code=404,
            detail="Short URL not found"
        )

    db.delete(url_record)
    db.commit()

    return {
        "message": "URL deleted successfully",
        "short_code": short_code
    }
