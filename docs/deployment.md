# Deployment Guide

This project is easiest to host in a free-friendly setup with:

- Frontend: Vercel
- Backend: Render web service
- Database: Supabase Postgres
- Redis: Upstash Redis

## Recommended Free-Friendly Mode

Use sync execution for the public demo:

```env
JOB_EXECUTION_MODE=sync
```

This keeps the job-based API and SSE UX, but avoids needing a paid background worker.

## Backend Deployment

Create a Render web service from the `Backend` folder.

Build command:

```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
```

Start command:

```bash
gunicorn intelliblogger_backend.wsgi:application
```

Set these environment variables:

```env
SECRET_KEY=replace-me
DEBUG=false
ALLOWED_HOSTS=your-backend-service.onrender.com
CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app
CSRF_TRUSTED_ORIGINS=https://your-frontend.vercel.app
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
CELERY_BROKER_URL=redis://...
CELERY_RESULT_BACKEND=redis://...
JOB_EVENT_STREAM_URL=redis://...
JOB_EXECUTION_MODE=sync
LOG_LEVEL=INFO
GEMINI_API_KEY=replace-me
ASSEMBLY_API_KEY=replace-me
```

## Frontend Deployment

Deploy the `Frontend` folder to Vercel.

Build command:

```bash
npm ci && npm run build
```

Output directory:

```text
dist/frontend/browser
```

Before deploying, update `Frontend/src/environments/environment.production.ts` with your real backend URL.

## Post-Deploy Checks

1. Open `/api/health/` on the backend and confirm it returns `status: ok`.
2. Sign up from the deployed frontend.
3. Generate a blog and confirm the job status updates.
4. Save a blog and verify it appears in the saved blogs list.

## Notes

- Render free web services may sleep after inactivity.
- Supabase and Upstash both have free tiers, but they also have usage limits.
- If you later move to paid hosting, switch `JOB_EXECUTION_MODE` to `celery` and run a separate Celery worker.
