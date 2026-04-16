# MedRights Patient Media & Consent Portal

A fully offline, containerized clinical portal for managing patient Master Patient Index (MPI) records, patient-facing clinical media with originality tracking, time-bound consents, offline manual financials with compensating-entry accounting, and tamper-evident audit trails. Built for single-clinic deployments with zero external dependencies.

## Architecture & Tech Stack

* **Frontend:** React 18, TypeScript, Vite, TailwindCSS, shadcn/ui, React Query, React Router
* **Backend:** Django 5, Django REST Framework, Celery (hexagonal architecture)
* **Database:** MySQL 8.0
* **Cache/Broker:** Redis 7
* **Web Server:** Nginx (reverse proxy + SPA host), Gunicorn (WSGI)
* **Containerization:** Docker & Docker Compose (Required)

## Project Structure

```text
.
├── backend/                # Django backend, Celery tasks, Dockerfile
├── frontend/               # React SPA, Nginx config, Dockerfile
├── e2e/                    # Playwright end-to-end tests
├── docker-compose.yml      # Multi-container orchestration - MANDATORY
├── run_tests.sh            # Standardized test execution script - MANDATORY
└── README.md               # Project documentation - MANDATORY
```

## Prerequisites

To ensure a consistent environment, this project is designed to run entirely within containers. You must have the following installed:
* [Docker](https://docs.docker.com/get-docker/)
* [Docker Compose](https://docs.docker.com/compose/install/)

## Running the Application

1. **Build and Start Containers:**
   Use Docker Compose to build the images and spin up the entire stack in detached mode.
   ```bash
   docker-compose up --build -d
   ```

   The `docker-compose.yml` ships with safe development defaults for all secrets
   (master key, secret key, database passwords), so no `.env` file is required
   for local development. Override any value with environment variables for
   production deployments.

2. **Seed Initial Users:**
   Create the default admin and role-test users after the stack is healthy.
   ```bash
   docker compose exec backend python manage.py seed_initial_data \
     --e2e --admin-password 'MedRights2026!'
   ```

3. **Access the App:**
   * Frontend: `http://localhost:3000`
   * Backend API: `http://localhost:8000/api/v1/`
   * Health Check: `http://localhost:8000/api/v1/health/`

4. **Verify the System is Working:**

   Confirm the backend is healthy:
   ```bash
   curl -s http://localhost:8000/api/v1/health/ | python -m json.tool
   ```
   You should see `{"status": "healthy", ...}`.

   Then open `http://localhost:3000` in a browser, log in with the admin credentials below (`admin` / `MedRights2026!`), and verify the dashboard loads with navigation to Patients, Media, Financials, and Admin sections.

5. **Stop the Application:**
   ```bash
   docker-compose down -v
   ```

## Testing

All unit, integration, and E2E tests are executed via a single, standardized shell script. This script automatically handles any necessary container orchestration for the test environment.

Make sure the script is executable, then run it:

```bash
chmod +x run_tests.sh
./run_tests.sh
```

The script runs:
1. **Backend tests** — 373 pytest tests (205 unit/integration + 168 black-box API tests)
2. **Frontend tests** — 80 Vitest component/unit tests
3. **E2E tests** — 70 Playwright browser tests against the live stack

*Note: The `run_tests.sh` script outputs a standard exit code (`0` for success, non-zero for failure) to integrate smoothly with CI/CD validators.*

## Seeded Credentials

The database is pre-seeded (via `seed_initial_data --e2e`) with the following test users. Use these credentials to verify authentication and role-based access controls.

| Role | Username | Password | Notes |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `MedRights2026!` | Full access: user management, bulk export, audit purge, system config. |
| **Front Desk** | `frontdesk` | `MedRights2026!` | Patient registration, MPI search, orders, payments, media upload. |
| **Clinician** | `clinician` | `MedRights2026!` | Patient records, attach media to patient materials. |
| **Compliance** | `compliance` | `MedRights2026!` | Break-glass review, infringement reports, disputes, audit logs. |
