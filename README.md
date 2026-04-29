# Legacy Inventory Monolith

> **WARNING: This application is INTENTIONALLY VULNERABLE.**
> It is designed as an educational demo target for observability and security tools.
> **DO NOT deploy to production or expose to the internet.**

## Overview

A deliberately vulnerable legacy-style monolithic inventory management system.
Built to demonstrate how modern observability tools (Prometheus, eBPF, SBOM scanners, LLM analysis) can detect issues in legacy systems.

## Architecture

```
┌──────────────────────────────┐
│  Frontend (Express + jQuery) │ :3000
│  Proxy → Backend             │
└──────────┬───────────────────┘
           │
┌──────────▼───────────────────┐
│  Backend (Flask)             │ :5000
│  REST API + SSR Templates    │
│                              │
└──────────┬───────────────────┘
           │
┌──────────▼───────────────────┐
│  PostgreSQL                  │ :5432
└──────────────────────────────┘
```

## Quick Start

```bash
docker-compose up
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:5000

### Test Credentials

| Username | Password  | Role  |
| -------- | --------- | ----- |
| admin    | admin123  | admin |
| user1    | password1 | user  |
| test     | test      | user  |

## Intentional Vulnerabilities

All vulnerabilities are marked with `# VULN:` comments in the source code.

| #   | Type                        | File                                                    | OWASP 2021 |
| --- | --------------------------- | ------------------------------------------------------- | ---------- |
| 1   | SQL Injection               | `backend/routes/inventory_api.py`                       | A03        |
| 2   | XSS (Reflected/Stored)      | `backend/templates/*.html`, `frontend/public/js/app.js` | A03        |
| 3   | IDOR                        | `backend/routes/warehouse_api.py`                       | A01        |
| 4   | Hardcoded Credentials       | `backend/config.py`                                     | A07        |
| 5   | Insecure Deserialization    | `backend/routes/inventory_api.py` (import)              | A08        |
| 6   | Path Traversal              | `backend/routes/reports_api.py`                         | A01        |
| 7   | Weak Password Hashing (MD5) | `backend/utils/security.py`                             | A02        |
| 8   | Debug Mode in Production    | `backend/config.py`                                     | A05        |
| 9   | No CSRF Protection          | All state-changing endpoints                            | A01        |
| 10  | Command Injection           | `backend/utils/export.py`                               | A03        |
| 11  | Information Disclosure      | `backend/routes/metrics.py` (/debug)                    | A01        |
| 12  | No Rate Limiting            | All endpoints                                           | A04        |

## API Endpoints

| Method | Endpoint                        | Description                                     |
| ------ | ------------------------------- | ----------------------------------------------- |
| POST   | `/api/auth/login`               | Login                                           |
| POST   | `/api/auth/register`            | Register                                        |
| GET    | `/api/inventory`                | List inventory (search, category, warehouse_id) |
| GET    | `/api/inventory/:id`            | Get item detail                                 |
| POST   | `/api/inventory`                | Create item                                     |
| PUT    | `/api/inventory/:id`            | Update item                                     |
| DELETE | `/api/inventory/:id`            | Delete item                                     |
| POST   | `/api/inventory/import`         | Import from YAML/pickle                         |
| GET    | `/api/inventory/low-stock`      | Low stock items                                 |
| GET    | `/api/warehouses`               | List warehouses                                 |
| GET    | `/api/warehouses/:id`           | Warehouse detail                                |
| POST   | `/api/warehouses/:id/stock-in`  | Receive stock                                   |
| POST   | `/api/warehouses/:id/stock-out` | Dispatch stock                                  |
| GET    | `/api/reports/summary`          | Inventory summary                               |
| GET    | `/api/reports/export/:id`       | CSV export                                      |
| GET    | `/api/reports/download`         | File download                                   |
| GET    | `/api/debug`                    | Debug info                                      |

## Vulnerability Demonstration

```bash
# SQL Injection
curl "http://localhost:5000/api/inventory?search=' OR '1'='1"

# IDOR - Access any warehouse without auth
curl http://localhost:5000/api/warehouses/2

# Path Traversal
curl "http://localhost:5000/api/reports/download?path=/etc/passwd"

# Debug Info Leak (exposes env vars including DB password)
curl http://localhost:5000/api/debug

# Command Injection via export
curl "http://localhost:5000/api/reports/export/1?format=csv;id"
```

## License

MIT — Educational use only.
