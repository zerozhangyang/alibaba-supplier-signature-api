# Alibaba Supplier Signature Registration API

A FastAPI backend service for receiving and processing SMS signature registration push notifications from Alibaba Cloud (阿里云短信签名报备接口三方对接).

## Features

- Receive AES-CBC encrypted push data from Alibaba Cloud
- Decrypt, validate, and persist registration tasks to MySQL
- Internal management API: list tasks, query detail, trigger callback/submit/query to Alibaba
- Full event logging for every inbound/outbound operation
- Static web UI for operations management (`/static/opss.html`)

## Architecture

```
Alibaba Cloud ──push──▶ POST /openapi/ali/register/push
                              │
                        AES Decrypt (CBC)
                              │
                        Validate fields
                              │
                        Save to MySQL (SignatureRegisterTask)
                              │
                        Internal API ──▶ callback / submit / query ──▶ Alibaba Cloud
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | FastAPI + Uvicorn |
| ORM | SQLAlchemy |
| Database | MySQL |
| Encryption | AES-CBC (PyCryptodome) |
| Data validation | Pydantic v2 |

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your actual credentials
```

Key variables in `.env`:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | MySQL connection string |
| `SUPPLIER_ID` | Your supplier ID from Alibaba |
| `THIRD_DECRYPT_KEY` / `THIRD_DECRYPT_IV` | AES key/IV for decrypting push data |
| `THIRD_UPLOAD_KEY` / `THIRD_UPLOAD_IV` | AES key/IV for encrypting outbound requests |

> AES keys and supplier ID are issued by Alibaba Cloud upon supplier onboarding.

### 3. Initialize database

```bash
mysql -u root -p ali_supplier < sql/init.sql
```

### 4. Run the service

```bash
python run.py
```

Service starts on `http://0.0.0.0:5772`

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/openapi/ali/register/push` | Receive third-party push |
| POST | `/openapi/ali/register/direct/push` | Receive direct-supplier push |
| GET | `/internal/register/tasks` | List all tasks (with filters) |
| GET | `/internal/register/{flow_id}` | Get task detail + event log |
| POST | `/internal/register/{flow_id}/callback` | Trigger callback to Alibaba |
| POST | `/internal/register/{flow_id}/submit` | Submit registration to Alibaba |
| POST | `/internal/register/query` | Query registration status |
| GET | `/health` | Health check |

Interactive docs available at `http://localhost:5772/docs` after startup.

## Project Structure

```
.
├── run.py                    # Entry point
├── app/
│   ├── main.py               # FastAPI app, CORS, startup
│   ├── config.py             # Settings (env-based)
│   ├── crypto/
│   │   └── aes_util.py       # AES-CBC encrypt/decrypt
│   ├── db/
│   │   ├── models.py         # SQLAlchemy ORM models
│   │   └── session.py        # DB engine and session
│   ├── routers/
│   │   ├── push.py           # Inbound push endpoints
│   │   └── internal.py       # Management endpoints
│   └── services/
│       ├── push_service.py   # Push handling logic
│       └── ali_client.py     # Outbound Alibaba API calls
├── sql/
│   └── init.sql              # Database schema
├── static/
│   └── opss.html             # Operations web UI
├── .env.example
└── requirements.txt
```
