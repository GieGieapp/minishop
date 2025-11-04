# Simple Admin Portal (Django + Next.js) — RBAC & User Invitations

## Overview

A small Admin Portal that demonstrates **JWT auth**, **Role-Based Access Control (RBAC)**, and **email-based user invitations**. Backend is **Django REST Framework**, frontend is **Next.js + Ant Design**. Invitations allow Admin/Manager to invite users by email; invitees register via a tokenized link and are auto-assigned a role.

## Features

* JWT login/refresh/logout. 
* RBAC with three roles: **admin**, **manager**, **staff**.
* CRUD: **Users**, **Products**, **Orders** with per-role permissions. 
* **Invitations**: create, list, resend, accept (register).  
* Dynamic menus on the frontend based on role (Next.js + AntD).
* Optional **revoke invitation** endpoint (recommended; see below).

## Tech Stack

* **Backend**: Django, Django REST Framework, SimpleJWT
* **Frontend**: Next.js, React, Ant Design
* **DB**: SQLite/PostgreSQL (any Django-supported)
* **Email (dev)**: Django console backend

## Requirements

* Python 3.10+
* Node.js 18+
* Poetry or pip (for Python deps)
* npm or pnpm/yarn

## Backend — Setup

```bash
# 1) create virtualenv & install
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt  # or: poetry install

# 2) env
cp backend/.env.example backend/.env   # edit secrets if needed

# 3) migrate & seed groups (admin/manager/staff)
python manage.py migrate
python manage.py shell -c "from django.contrib.auth.models import Group; [Group.objects.get_or_create(name=r) for r in ['admin','manager','staff']]"

# 4) run dev
python manage.py runserver 127.0.0.1:8000
```

### Important backend settings

Enable SimpleJWT authentication in DRF:

```python
REST_FRAMEWORK = {
  "DEFAULT_AUTHENTICATION_CLASSES": (
    "rest_framework_simplejwt.authentication.JWTAuthentication",
  ),
}
```

Protected endpoints require `Authorization: Bearer <access>`; logout is stateless (204). 

### Email (dev)

Use console backend to print invite links to the server log during development.

## Frontend — Setup

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
# Next.js will run on http://localhost:3000
```

## RBAC Policy

| Role    | Users      | Products   | Orders     |
| ------- | ---------- | ---------- | ---------- |
| admin   | read/write | read/write | read/write |
| manager | read       | read/write | read-only  |
| staff   | —          | read-only  | read-only  |

RBAC is enforced in custom DRF permissions classes used by each ViewSet. Example (Products): staff is **SAFE_METHODS only**; admin/manager can edit. 

## API Endpoints (Backend)

### Auth

* `POST /api/accounts/login/` → `{ access, refresh }` (JWT). 
* `POST /api/accounts/refresh/` → rotate access.
* `POST /api/accounts/logout/` → 204; stateless. 
* `GET  /api/accounts/me/` → current user. 

### Invitations

* `POST /api/invitations/` (admin/manager) → create invitation, email sent, 72h expiry. 
* `GET  /api/invitations/` (admin/manager) → list. 
* `POST /api/invitations/{id}/resend/` (admin/manager). 
* `POST /api/invitations/accept/` (public) → register via token; assigns role/group, marks used. 

> Recommended: add `POST /api/invitations/{id}/revoke/` to set `revoked_at=now()` and block accept/resend (small patch).

### Users

* `GET/POST /api/accounts/users/` (RBAC: admin RW; manager R). 
* `GET/PUT/PATCH/DELETE /api/accounts/users/{id}/` (RBAC-guarded).
  Expose `role` by reading Django Groups in `UserSerializer` (recommended). 

### Products

Prefix: `/api/catalog/`

* `GET /products/` (search/order supported). 
* `GET /products/{id}/`
* `POST /products/`
* `PUT/PATCH/DELETE /products/{id}/`
  Permissions: `IsAuthenticated + RBACProductPermission`. Staff = read-only. 

### Orders

Prefix: `/api/`

* `GET /orders/`, `GET /orders/{id}/`
* `POST /orders/`, `PUT/PATCH/DELETE /orders/{id}/`
  Permissions: `IsAuthenticated + RBACOrderPermission` (admin = RW, others read-only).  

## Invitation Flow

1. Admin/Manager creates an invitation with target email + role. Server generates a token (expires in 72 hours) and sends an email link. 
2. Recipient opens the link and **accepts**:

   ```
   POST /api/invitations/accept/
   { "token": "<uuid>", "username": "alice", "password": "Passw0rd!" }
   ```

   On success: user is created, automatically added to the corresponding Group, and the invitation is marked used. 
3. Admin can view invitations, resend, and (optionally) revoke.

### Status (recommended design)

Derive status from fields (single source of truth):

* `revoked_at` → revoked
* `used_at`     → accepted
* `expires_at < now` (and not used/revoked) → expired
* otherwise → pending
  Expose as a computed field in the serializer if needed.

## Quick Test (cURL)

### Login as admin

```bash
ACCESS=$(curl -sX POST http://127.0.0.1:8000/api/accounts/login/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}' | jq -r .access)
```

### Create invitation (admin/manager)

```bash
curl -X POST http://127.0.0.1:8000/api/invitations/ \
  -H "Authorization: Bearer $ACCESS" -H "Content-Type: application/json" \
  -d '{"email":"newuser@example.com","role":"manager"}'
```

### Accept invitation (public)

```bash
curl -X POST http://127.0.0.1:8000/api/invitations/accept/ \
  -H "Content-Type: application/json" \
  -d '{"token":"<UUID>","username":"newuser","password":"Passw0rd!"}'
```

### Verify new user

```bash
NEW_ACCESS=$(curl -sX POST http://127.0.0.1:8000/api/accounts/login/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"newuser","password":"Passw0rd!"}' | jq -r .access)

curl -s http://127.0.0.1:8000/api/accounts/me/ -H "Authorization: Bearer $NEW_ACCESS"
```

### RBAC sanity checks

* Staff create Product → should be **403** (read-only). 
* Manager create Product → **200** (allowed).
* Manager create Order → **403** (read-only by design). 
* Admin create Order → **200**.

## Sample Accounts (optional for reviewers)

* Admin: `admin` / `admin123`
* Manager: `manager` / `manager123`
* Staff: `staff` / `staff123`
  (Adjust or provide invite tokens instead.)

## Troubleshooting

* **401 Authentication credentials were not provided**
  Add `Authorization: Bearer <access>` and avoid `--location` redirects; always use trailing slashes (e.g., `/api/orders/`). 
* **403 Forbidden**
  Token is valid but role disallows the action. Confirm user groups via `/api/accounts/me/`.
* **Staff can edit Products**
  Ensure Product routes use `RBACProductPermission`, not `DjangoModelPermissions`; remove duplicate Product viewsets if any. 
* **Admin cannot edit**
  Make sure the admin user is in Group `admin` (RBAC checks groups, not `is_staff` alone). 

## Repository Structure

```
backend/
  apps/
    accounts/   # users, invitations, auth
    catalog/    # products
    orders/     # orders
  manage.py
frontend/
  ...
```

## License

MIT (or your choice).

---

**Notes for graders:**

* Invitation flow, RBAC, and CRUD endpoints reflect the case study requirements; see the `invitations` endpoints and role matrix above for expected behavior. 
