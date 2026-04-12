# Deployment Guide (Vercel + Supabase)

This setup deploys everything on Vercel by using two Vercel projects from the same repo:

- Project 1: frontend (root directory: `frontend`)
- Project 2: backend API (root directory: `backend`)

Database is Supabase PostgreSQL.

## 1) Prepare Supabase

1. Create a Supabase project.
2. Copy the PostgreSQL connection string from Settings -> Database.
3. Use the URI format with SSL enabled, e.g. `...?sslmode=require`.

## 2) Deploy Backend on Vercel

Backend Vercel config files are already added:

- `backend/api/index.py`
- `backend/vercel.json`

These route all requests to Django running as a Python serverless function.

### Create backend project

1. In Vercel, click Add New -> Project.
2. Select this repository.
3. Set Root Directory to `backend`.
4. Keep Framework Preset as Other.
5. Deploy once.

### Backend environment variables

Set these in the backend Vercel project:

- `DJANGO_SECRET_KEY=<strong-secret>`
- `DJANGO_DEBUG=false`
- `DJANGO_ALLOWED_HOSTS=<backend-project>.vercel.app`
- `DJANGO_SECURE_SSL_REDIRECT=true`
- `DATABASE_URL=<supabase-postgres-uri>`
- `CORS_ALLOWED_ORIGINS=https://<frontend-project>.vercel.app`
- `CSRF_TRUSTED_ORIGINS=https://<frontend-project>.vercel.app`
- `ACCESS_TOKEN_TTL_HOURS=12`
- `ALLOW_DEV_AUTH_ENDPOINTS=false`
- `OPENAI_API_KEY=<key>`
- `OPENAI_MODEL=gpt-4.1-mini`
- `OPENAI_TIMEOUT_SECONDS=4`
- `OPENAI_MAX_RETRIES=1`
- `LOG_LEVEL=INFO`

Redeploy after saving env vars.

### Run migrations for backend

Use Vercel Build/Function shell or run migrations from local against the same env:

- `python backend/manage.py migrate`

Verify backend health:

- `https://<backend-project>.vercel.app/api/auth/health`

## 3) Deploy Frontend on Vercel

1. Create another Vercel project from the same repo.
2. Set Root Directory to `frontend`.
3. Framework preset: Vite.
4. Add env variable:
	- `VITE_API_BASE=https://<backend-project>.vercel.app/api`
5. Deploy.

## 4) Final Cross-Origin Update

After both domains are final, ensure backend env vars exactly match frontend origin:

- `CORS_ALLOWED_ORIGINS=https://<frontend-project>.vercel.app`
- `CSRF_TRUSTED_ORIGINS=https://<frontend-project>.vercel.app`

Redeploy backend if you changed these values.

## 5) Verify End-to-End

1. Open frontend URL.
2. Create user/start session.
3. Send one message and confirm API call succeeds.
4. Check browser console has no CORS/CSRF errors.

## 6) Local Development

Backend:

- `cd backend`
- `..\.venv\Scripts\python.exe -m pip install -r requirements.txt`
- `copy .env.example .env`
- `..\.venv\Scripts\python.exe manage.py migrate`
- `..\.venv\Scripts\python.exe manage.py runserver`

Frontend:

- `cd frontend`
- `npm install`
- `copy .env.example .env`
- `npm run dev`

With `VITE_API_BASE=/api` and Vite proxy enabled, frontend calls route to local backend at `http://127.0.0.1:8000`.
