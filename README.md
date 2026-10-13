# CloudOps Manager

CloudOps Manager is a small Flask dashboard for viewing cloud server, deployment, and security-check information. It uses SQLite for storage and includes sample data for local development and container demos.

## Features

- Dashboard with total and running server counts, deployment count, recent deployments, and security checks.
- Server inventory showing status, CPU utilization, and region.
- Security-check listing with descriptions and pass/fail status.
- SQLite schema initialization and repeatable sample-data seeding.
- Docker image built in separate dependency and runtime stages; the app runs as a non-root user.

## Requirements

- Python 3.12 or newer
- Docker Desktop or another Docker Engine (optional, for container usage)

## Run locally

From the project root, create and activate a virtual environment in PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Initialize the database and seed the demo data:

```powershell
python -m app.seed
```

Start the Flask development server:

```powershell
python -m flask --app app.app run --debug
```

Open <http://127.0.0.1:5000/>.

By default, SQLite creates `cloudops.db` in the current working directory. Set `DATABASE_PATH` before running the seeder and Flask app to use a different file:

```powershell
New-Item -ItemType Directory -Force data
$env:DATABASE_PATH = "data\cloudops.db"
python -m app.seed
python -m flask --app app.app run --debug
```

The seeder initializes the schema and inserts sample rows when each table is empty. It does not add duplicate sample rows to tables that already contain data.

## Run tests

With the virtual environment activated:

```powershell
python -m pytest
```

The tests use a separate temporary SQLite database and verify that the main routes respond and server data is displayed.

## Run with Docker

Build the image from the project root:

```powershell
docker build -t cloudops-manager .
```

Run it with a named volume so the SQLite database persists when the container is replaced:

```powershell
docker run --rm -p 5000:5000 -v cloudops-data:/app/data cloudops-manager
```

The container sets `DATABASE_PATH=/app/data/cloudops.db`, initializes and seeds that database at startup, and serves the app on port 5000. Open <http://localhost:5000/>.

To use a different database path, set `DATABASE_PATH` to a location writable by the container's `appuser`. Mount persistent storage at that location when persistence is required.

## Project structure

```text
app/
  __init__.py
  app.py
  database.py
  seed.py
  static/
    css/
      style.css
  templates/
    base.html
    dashboard.html
    deployments.html
    security.html
    servers.html
tests/
  test_app.py
.dockerignore
.gitignore
Dockerfile
README.md
requirements.txt
```

## Database tables

- `servers`: name, status, CPU value, and region.
- `deployments`: version, environment, and status.
- `security_checks`: tool, description, and status.

## Current limitations

- The deployments route reads deployment rows from SQLite, but the deployments template currently displays hard-coded sample rows rather than the queried values.
- The container runs Flask's built-in server. Use a production WSGI server and production hardening before exposing this demo application to production traffic.
