# DocAssist Cloud API

E2E Encrypted Backup Service for DocAssist EMR - A zero-knowledge cloud backend that enables secure backup and sync between desktop and mobile apps.

## Features

- **Zero-Knowledge Architecture**: Server cannot decrypt patient data
- **E2E Encryption**: All encryption happens client-side
- **JWT Authentication**: Secure token-based authentication
- **Rate Limiting**: Protection against abuse
- **RESTful API**: Clean, documented endpoints
- **Async/Await**: High-performance async operations
- **SQLite Database**: Lightweight metadata storage

## Quick Start

### 1. Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Generate JWT secret key
openssl rand -hex 32

# Edit .env and add your JWT secret key
nano .env
```

### 3. Run Server

```bash
# Development mode (with auto-reload)
python main.py

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 4. Access API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

## API Endpoints

### Authentication

#### Register New User
```http
POST /auth/register
Content-Type: application/json

{
  "email": "doctor@example.com",
  "password": "securepassword",
  "name": "Dr. John Doe",
  "phone": "+919876543210",
  "license_number": "MH-12345"
}
```

Response:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 604800,
  "user": {
    "id": 1,
    "email": "doctor@example.com",
    "name": "Dr. John Doe",
    ...
  }
}
```

#### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "doctor@example.com",
  "password": "securepassword"
}
```

### Backup Management

#### Upload Backup
```http
POST /backup/upload
Authorization: Bearer {token}
Content-Type: multipart/form-data

file: (binary encrypted backup)
device_id: "desktop-123"
device_name: "Desktop PC"
```

#### Get Latest Backup Metadata
```http
GET /backup/latest
Authorization: Bearer {token}
```

Response:
```json
{
  "backup_id": "uuid-here",
  "filename": "backup.enc",
  "size_bytes": 1024000,
  "checksum": "sha256-hash",
  "device_name": "Desktop PC",
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### Download Backup
```http
GET /backup/download/{backup_id}
Authorization: Bearer {token}
```

#### Get Sync Status
```http
GET /backup/sync/status
Authorization: Bearer {token}
```

Response:
```json
{
  "last_backup_time": "2024-01-15T10:30:00Z",
  "backup_count": 5,
  "total_size_bytes": 5120000,
  "devices": ["Desktop PC", "Laptop"]
}
```

## Security Features

### Zero-Knowledge Architecture
- Server stores only encrypted blobs
- No access to encryption keys
- Cannot decrypt patient data
- WhatsApp-style privacy model

### Authentication
- Passwords hashed with bcrypt (cost factor: 12)
- JWT tokens with 7-day expiration
- Secure token validation on every request

### Rate Limiting
- Downloads: 10 requests/minute
- Uploads: 5 requests/minute
- Configurable per endpoint

### Data Isolation
- Each user's backups stored separately
- No cross-user access possible
- Strict authorization checks

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test class
pytest tests/test_api.py::TestAuthentication -v
```

## Deployment

### Production Checklist

1. **Environment Variables**
   - [ ] Generate strong JWT secret key
   - [ ] Set production database path
   - [ ] Configure CORS allowed origins
   - [ ] Set appropriate rate limits

2. **Security**
   - [ ] Use HTTPS (TLS/SSL certificate)
   - [ ] Configure firewall rules
   - [ ] Enable request logging
   - [ ] Set up monitoring

3. **Database**
   - [ ] Regular backups of metadata DB
   - [ ] Set up backup rotation policy
   - [ ] Monitor disk usage

4. **Performance**
   - [ ] Use production ASGI server (uvicorn with workers)
   - [ ] Set up reverse proxy (nginx)
   - [ ] Configure caching headers
   - [ ] Monitor response times

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV DATABASE_PATH=/data/cloud_api.db
ENV BACKUP_STORAGE_PATH=/data/backups

VOLUME ["/data"]

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t docassist-cloud-api .
docker run -d -p 8000:8000 -v /path/to/data:/data docassist-cloud-api
```

### Systemd Service

```ini
[Unit]
Description=DocAssist Cloud API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/docassist-cloud-api
Environment="PATH=/opt/docassist-cloud-api/venv/bin"
ExecStart=/opt/docassist-cloud-api/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

## Architecture

### Directory Structure
```
cloud-api/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (not in git)
├── src/
│   ├── database.py      # SQLite database layer
│   ├── auth/            # Authentication module
│   │   ├── router.py    # Auth endpoints
│   │   ├── models.py    # Pydantic models
│   │   └── jwt.py       # JWT utilities
│   └── backup/          # Backup module
│       ├── router.py    # Backup endpoints
│       ├── models.py    # Pydantic models
│       └── storage.py   # File storage
├── data/                # Runtime data (not in git)
│   ├── cloud_api.db     # Metadata database
│   └── backups/         # Encrypted backup files
└── tests/
    └── test_api.py      # API tests
```

### Database Schema

**users**
- id, email, password_hash, name, phone, license_number
- created_at, last_login, is_active

**backups**
- id, backup_id, user_id, filename, size_bytes
- checksum, device_id, device_name, created_at

## License

Proprietary - DocAssist EMR

## Support

For issues or questions, contact: support@docassist.in
