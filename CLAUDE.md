# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

Warehouse inventory management system for a solar research and development team. Tracks stock levels across physical storage spaces, logs all transactions for audit purposes, and supports a multi-user team with role-based access.

## Commands

```bash
# Run development server
python manage.py runserver

# Apply migrations
python manage.py migrate

# Create/apply new migrations
python manage.py makemigrations
python manage.py migrate

# Collect static files (required before production deploy)
python manage.py collectstatic --noinput

# Create superuser from env vars (idempotent)
DJANGO_SUPERUSER_USERNAME=admin DJANGO_SUPERUSER_EMAIL=admin@example.com DJANGO_SUPERUSER_PASSWORD=password python manage.py create_superuser_env

# Create Staff/Admin groups with permissions
python manage.py create_groups
```

No test runner or linter is currently configured.

## Architecture

Single Django project (`warehouse/`) with one app (`inventory/`) deployed on Railway.

### Data Model

```
StorageSpace ←────────┐
                       │ FK
InventoryType ─── InventoryItem ─── StockTransaction
                  (unique on:           FK to User
                   type+size+space)
```

- **StorageSpace**: Physical locations; `room_type` is `humidity_controlled` or `normal`; has `used_capacity`/`available_capacity` properties derived from items
- **InventoryType**: Item categories with a `standard_sizes` JSONField and `preferred_storage` FK; SKU prefix for grouping
- **InventoryItem**: Unique per `(inventory_type, size, storage_space)`; has `is_low_stock` property; quantity never goes below 0
- **StockTransaction**: Immutable audit log; `transaction_type` is `add`, `use`, or `adjust`; all stock changes go through atomic transactions

### Authentication & Authorization

Two groups are created by `create_groups`:
- **Staff**: Can view all models; add/change items and transactions
- **Admin**: Full CRUD on all models

New users register via `/register/` and are created as **inactive** (`is_active=False`) with the Staff group assigned. A Django admin must activate them via the custom `approve_users` admin action on the User model.

### URL Structure

- `/` → dashboard (login required)
- `/item/<id>/` → item detail + transaction history
- `/add-stock/`, `/use-stock/`, `/use-stock/<id>/` → stock operations
- `/capacity/` → storage capacity estimator
- `/register/`, `/pending-approval/` → auth flow
- `/login/`, `/logout/` → Django auth views
- `/admin/` → Django admin

### Settings & Deployment

Settings are entirely environment-variable driven for Railway:
- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DATABASE_URL`, `CSRF_TRUSTED_ORIGINS`
- `RAILWAY_PUBLIC_DOMAIN` is auto-detected and added to `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`
- Database defaults to SQLite locally; set `DATABASE_URL` for PostgreSQL in production
- Static files served by WhiteNoise with `CompressedManifestStaticFilesStorage`
- Procfile: `gunicorn warehouse.wsgi`
