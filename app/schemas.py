
from datetime import datetime, timezone

from pydantic import BaseModel, HttpUrl, field_validator


# Request schema for creating a short URL
class URLCreate(BaseModel):
    url: HttpUrl
    expires_at: datetime | None = None

    @field_validator("expires_at")
    @classmethod
    def validate_expiration(cls, value):
        if value is not None:

            if value.tzinfo is None:
                raise ValueError(
                    "Expiration must include a timezone"
                )

            if value <= datetime.now(timezone.utc):
                raise ValueError(
                    "Expiration must be in the future"
                )

        return value

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "url": "https://www.example.com",
                    "expires_at": "2027-12-31T23:59:59Z"
                }
            ]
        }
    }


# Response after creating a short URL
class URLResponse(BaseModel):
    short_code: str
    short_url: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "short_code": "1",
                    "short_url": "http://127.0.0.1:8000/1"
                }
            ]
        }
    }


# Response containing URL details
class URLDetailResponse(BaseModel):
    short_code: str
    original_url: str
    created_at: datetime

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "short_code": "1",
                    "original_url": "https://www.example.com",
                    "created_at": "2026-11-20T10:30:00"
                }
            ]
        }
    }


# Response containing URL analytics
class URLAnalyticsResponse(BaseModel):
    short_code: str
    original_url: str
    total_clicks: int
    created_at: datetime

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "short_code": "1",
                    "original_url": "https://www.example.com",
                    "total_clicks": 25,
                    "created_at": "2026-11-20T10:30:00"
                }
            ]
        }
    }
