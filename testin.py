
from app.database import SessionLocal
from app.models import URL

db = SessionLocal()

try:
    new_url = URL(
        short_code="python001",
        original_url="https://www.google.com"
    )

    db.add(new_url)
    db.commit()
    db.refresh(new_url)

    print("URL inserted successfully!")
    print("ID:", new_url.id)
    print("Short code:", new_url.short_code)
    print("Original URL:", new_url.original_url)

except Exception as e:
    db.rollback()
    print("Error:", e)
finally:
    db.close()
