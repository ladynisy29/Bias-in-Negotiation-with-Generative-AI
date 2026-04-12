# Deployment Guide (Free Tier Friendly)

## Recommended Architecture

- Deploy frontend on Vercel.
- Deploy Django backend on a Python host (Render, Railway, Fly.io, etc.).
- Use managed PostgreSQL (Neon/Supabase or provider database add-on).

This avoids serverless filesystem limitations for SQLite.

## 1) Backend Deployment

### Required environment variables

Set these on your backend host:

- DJANGO_SECRET_KEY
- DJANGO_DEBUG=false
- DJANGO_ALLOWED_HOSTS=your-backend-domain.com
- DJANGO_SECURE_SSL_REDIRECT=true
- CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app
- CSRF_TRUSTED_ORIGINS=https://your-frontend.vercel.app
- ACCESS_TOKEN_TTL_HOURS=12
- ALLOW_DEV_AUTH_ENDPOINTS=false
- OPENAI_API_KEY=...
- OPENAI_MODEL=gpt-4.1-mini
- OPENAI_TIMEOUT_SECONDS=8
- OPENAI_MAX_RETRIES=2
- DATABASE_URL=postgres://...

### Backend start command

Use your platform's process/start command with gunicorn:

- gunicorn core.wsgi:application --chdir backend

### Apply migrations

Run once after deploy:

- python backend/manage.py migrate

## 2) Frontend Deployment on Vercel

Vercel is configured with repository-root vercel.json:

- buildCommand: cd frontend && npm ci && npm run build
- outputDirectory: frontend/dist

Set frontend environment variable in Vercel:

- VITE_API_BASE=https://your-backend-domain.com/api

Then deploy.

## 3) Local Development

Backend:

- cd backend
- ..\.venv\Scripts\python.exe -m pip install -r requirements.txt
- copy .env.example .env
- ..\.venv\Scripts\python.exe manage.py migrate
- ..\.venv\Scripts\python.exe manage.py runserver

Frontend:

- cd frontend
- npm install
- copy .env.example .env
- npm run dev

With VITE_API_BASE=/api and Vite proxy enabled, frontend calls route to local backend at http://127.0.0.1:8000.
