# IntelliBlogger

IntelliBlogger is an AI-powered content repurposing app that converts YouTube videos into editable blog posts. It is built as a full-stack project with Angular on the frontend and Django on the backend, with job-based generation flows designed to scale beyond a simple demo.

## What This Project Shows

- JWT authentication and protected APIs
- AI-driven blog generation with tone and length controls
- Saved blog management and editing workflows
- Redis-backed caching and real-time job updates with SSE
- Job-based generation architecture with sync and Celery execution modes
- Production-oriented backend configuration with environment-based settings

## Tech Stack

- Frontend: Angular, TypeScript
- Backend: Django, Django REST Framework
- Database: SQLite locally, Postgres in hosted environments
- Queue / cache: Redis
- AI services: Gemini, AssemblyAI

## Local Development

### Backend

```bash
cd Backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py runserver
```

### Frontend

```bash
cd Frontend
npm install
npm start
```

### Optional Celery Worker

For full async local development:

```bash
cd Backend
venv\Scripts\activate
python -m celery -A intelliblogger_backend worker --pool=solo --loglevel=info
```

## Execution Modes

The backend supports two generation modes:

- `JOB_EXECUTION_MODE=celery`
  Uses Redis + Celery workers for background processing.
- `JOB_EXECUTION_MODE=sync`
  Processes generation inline in the web service. This is useful for cheaper or free hosting.

## Deployment

Deployment instructions are in [docs/deployment.md](/C:/Projects/Intelliblogger/docs/deployment.md).

The recommended free-friendly setup is:

- Frontend: Vercel
- Backend: Render web service
- Database: Supabase Postgres
- Redis: Upstash Redis

For public demo hosting, use:

```env
JOB_EXECUTION_MODE=sync
```

This keeps the job-based product flow without requiring a paid background worker.
