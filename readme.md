
# URL Shortener API

A backend URL shortening service built using **Python, FastAPI, PostgreSQL, and SQLAlchemy**.

This application converts long URLs into short, unique URLs and redirects users to the original destination. It also supports click tracking, URL expiration, analytics, and deletion.

## Features

- Create unique short URLs
- Redirect short URLs to original URLs
- Base62 encoding for short codes
- Track the number of clicks
- Retrieve URL details
- View URL analytics
- Set expiration dates for short URLs
- Reject expired URLs
- Delete shortened URLs
- Input validation using Pydantic
- Database connection pooling
- Atomic click counting
- Automated testing with pytest
- Interactive API documentation with Swagger

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| FastAPI | REST API framework |
| PostgreSQL | Relational database |
| SQLAlchemy | ORM and database operations |
| Psycopg | PostgreSQL driver |
| Pydantic | Request validation and schemas |
| Pytest | Automated testing |
| Uvicorn | ASGI server |

## Project Structure

```text
url-shortener/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   └── utils.py
│
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   └── test_utils.py
│
├── .env
├── requirements.txt
└── README.md
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd url-shortener
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
venv\Scripts\Activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure PostgreSQL

Create a PostgreSQL database:

```sql
CREATE DATABASE url_shortener;
```

Configure your `.env` file:

```env
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/url_shortener
```

Replace `YOUR_PASSWORD` with your PostgreSQL password.

**Never commit your `.env` file or database credentials to GitHub.**

### 5. Run the application

```bash
uvicorn app.main:app --reload
```

The API will run at:

```text
http://127.0.0.1:8000
```

## API Documentation

FastAPI automatically generates interactive API documentation.

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

ReDoc:

```text
http://127.0.0.1:8000/redoc
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Health check |
| POST | `/api/shorten` | Create a short URL |
| GET | `/{short_code}` | Redirect to original URL |
| GET | `/api/urls/{short_code}` | Retrieve URL details |
| GET | `/api/analytics/{short_code}` | Retrieve URL analytics |
| DELETE | `/api/urls/{short_code}` | Delete a short URL |

## Example Request

### Create a short URL

**POST** `/api/shorten`

Request body:

```json
{
    "url": "https://www.example.com",
    "expires_at": "2027-12-31T23:59:59Z"
}
```

Example response:

```json
{
    "short_code": "1",
    "short_url": "http://127.0.0.1:8000/1"
}
```

The short code and URL above are illustrative examples.

## Testing

Run the automated test suite:

```bash
python -m pytest -v
```

The tests cover:

- URL creation
- Invalid URL validation
- Redirect functionality
- Click tracking
- Analytics
- URL deletion
- Expiration handling
- Nonexistent URLs
- Concurrent click requests
- Base62 encoding

## Key Technical Concepts

- REST API development
- Database modeling and relationships
- SQLAlchemy ORM
- Base62 encoding
- Input validation
- HTTP status codes
- Database transactions
- Atomic database updates
- Connection pooling
- Timezone-aware expiration
- Automated testing
- Concurrent request handling

## Future Improvements

- User authentication
- Custom short codes
- Rate limiting
- QR code generation
- Redis caching
- Advanced analytics
- Docker deployment
- Cloud deployment

## Author

Developed as a backend engineering project to explore API development, database management, and scalable application design.
