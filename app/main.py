
from datetime import datetime, timezone
from uuid import uuid4
from pathlib import Path
import math

from fastapi import FastAPI, Depends, Request, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import update

from app.database import get_db
from app.models import URL
from app.schemas import (
    URLCreate,
    URLResponse,
    URLDetailResponse,
    URLAnalyticsResponse,
    URLDashboardItem
)
from app.utils import encode_base62
from app.cache import get_cache, set_cache, delete_cache
from app.logger import logger
from app.rate_limit import check_rate_limit


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
    - Dashboard listing
    - Redis caching
    - Application logging
    - Rate limiting
    """,
    version="1.0.0",
    contact={
        "name": "API Developer"
    }
)


# Static files
STATIC_DIR = Path(__file__).parent / "static"

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static"
)


# Dashboard
@app.get("/dashboard", include_in_schema=False)
def dashboard():
    return FileResponse(STATIC_DIR / "dashboard.html")


# Health check
@app.get(
    "/",
    summary="Health check",
    description="Check whether the URL Shortener API is running."
)
def home():
    return {"message": "URL Shortener API is running"}


# List all shortened URLs
@app.get(
    "/api/urls",
    response_model=list[URLDashboardItem],
    summary="List all shortened URLs",
    description="Retrieve all shortened URLs and their click statistics."
)
def list_urls(db: Session = Depends(get_db)):
    url_records = db.query(URL).order_by(
        URL.id.desc()
    ).all()

    return [
        URLDashboardItem(
            short_code=url.short_code,
            original_url=url.original_url,
            total_clicks=url.click_count,
            created_at=url.created_at,
            expires_at=url.expires_at
        )
        for url in url_records
    ]


# Create a short URL with rate limiting
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
    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"

    rate_limit_key = f"rate_limit:shorten:{client_ip}"

    if not check_rate_limit(
        rate_limit_key,
        limit=5,
        window=60
    ):
        logger.warning(
            "RATE LIMIT EXCEEDED | endpoint=/api/shorten | client=%s",
            client_ip
        )

        raise HTTPException(
            status_code=429,
            detail="Too many URL creation requests. Please try again later."
        )

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

        logger.info(
            "URL CREATED | short_code=%s",
            new_url.short_code
        )

        return URLResponse(
            short_code=new_url.short_code,
            short_url=short_url
        )

    except SQLAlchemyError:
        db.rollback()

        logger.exception("DATABASE ERROR | URL creation failed")

        raise HTTPException(
            status_code=500,
            detail="Database operation failed"
        )


# Redirect and track clicks using Redis
@app.get(
    "/{short_code}",
    summary="Redirect to original URL",
    description="Redirect to the original URL and increment its click count. Returns 410 if the URL has expired."
)
def redirect_url(
    short_code: str,
    db: Session = Depends(get_db)
):
    cache_key = f"url:{short_code}"

    # 1. Try Redis cache
    cached_url = get_cache(cache_key)

    if cached_url is not None:

        # Atomically increase clicks only if URL still exists
        result = db.execute(
            update(URL)
            .where(URL.short_code == short_code)
            .values(
                click_count=URL.click_count + 1
            )
        )

        # URL may have been deleted while cached
        if result.rowcount == 0:
            delete_cache(cache_key)

            logger.warning(
                "URL NOT FOUND | short_code=%s",
                short_code
            )

            raise HTTPException(
                status_code=404,
                detail="Short URL not found"
            )

        db.commit()

        logger.info(
            "CACHE HIT | short_code=%s",
            short_code
        )

        logger.info(
            "REDIRECT | short_code=%s",
            short_code
        )

        return RedirectResponse(
            url=cached_url,
            status_code=302
        )

    # 2. Cache miss: fetch from PostgreSQL
    logger.info(
        "CACHE MISS | short_code=%s",
        short_code
    )

    url_record = db.query(URL).filter(
        URL.short_code == short_code
    ).first()

    if url_record is None:
        logger.warning(
            "URL NOT FOUND | short_code=%s",
            short_code
        )

        raise HTTPException(
            status_code=404,
            detail="Short URL not found"
        )

    # 3. Check expiration
    now = datetime.now(timezone.utc)

    if (
        url_record.expires_at is not None
        and url_record.expires_at <= now
    ):
        delete_cache(cache_key)

        logger.warning(
            "URL EXPIRED | short_code=%s",
            short_code
        )

        raise HTTPException(
            status_code=410,
            detail="This short URL has expired"
        )

    original_url = url_record.original_url

    # 4. Cache the destination
    cache_ttl = 300

    if url_record.expires_at is not None:
        remaining_seconds = (
            url_record.expires_at - now
        ).total_seconds()

        cache_ttl = min(
            cache_ttl,
            math.floor(remaining_seconds)
        )

    if cache_ttl > 0:
        set_cache(
            cache_key,
            original_url,
            expiry=cache_ttl
        )

    # 5. Atomically increase click count
    db.execute(
        update(URL)
        .where(URL.id == url_record.id)
        .values(
            click_count=URL.click_count + 1
        )
    )

    db.commit()

    logger.info(
        "REDIRECT | short_code=%s",
        short_code
    )

    # 6. Redirect
    return RedirectResponse(
        url=original_url,
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
        logger.warning(
            "URL NOT FOUND FOR DELETION | short_code=%s",
            short_code
        )

        raise HTTPException(
            status_code=404,
            detail="Short URL not found"
        )

    # Remove cached destination
    delete_cache(f"url:{short_code}")

    db.delete(url_record)
    db.commit()

    logger.info(
        "URL DELETED | short_code=%s",
        short_code
    )

    return {
        "message": "URL deleted successfully",
        "short_code": short_code
    }
