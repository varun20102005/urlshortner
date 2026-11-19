
from uuid import uuid4

from app.database import SessionLocal
from app.models import URL
from app.utils import encode_base62

db = SessionLocal()

try:
    # Create a temporary unique code
    new_url = URL(
        short_code="p" + uuid4().hex[:19],
        original_url="https://www.google.com"
    )

    db.add(new_url)

    # Insert into database and obtain generated ID
    db.flush()

    # Convert database ID into Base62
    new_url.short_code = encode_base62(new_url.id)

    # Save everything
    db.commit()
    db.refresh(new_url)

    print("URL created successfully!")
    print("Database ID:", new_url.id)
    print("Short code:", new_url.short_code)

except Exception as e:
    db.rollback()
    print("Error:", e)

finally:
    db.close()
