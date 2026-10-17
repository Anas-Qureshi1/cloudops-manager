# CloudOps Manager — Secure DevSecOps CI/CD Pipeline

[![CI Pipeline](https://img.shields.io/badge/Jenkins-CI%2FCD-blue?logo=jenkins)](http://localhost:8080)
[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.3-black?logo=flask)](https://flask.palletsprojects.com/)
[![Docker](https://img.shields.io/badge/Docker-Multi--Stage-blue?logo=docker)](https://www.docker.com/)
[![Security](https://img.shields.io/badge/Gitleaks-Passed-brightgreen)](https://github.com/gitleaks/gitleaks)
[![SAST](https://img.shields.io/badge/SonarQube-Active-blue?logo=sonarqube)](http://localhost:9000)
[![Container Security](https://img.shields.io/badge/Trivy-Audited-brightgreen)](https://github.com/aquasecurity/trivy)

> **Portfolio Showcase:** An end-to-end cloud infrastructure monitoring dashboard built with Python &amp; Flask, hardened with non-root Docker multi-stage builds, and protected by an automated 10-stage DevSecOps CI/CD pipeline enforcing static code quality, secret detection, dependency vulnerability analysis, and container image security scanning.

---

## 1. Project Architecture & Pipeline Flow

The project implements a "Shift-Left" security model where code is automatically scanned for credentials, tested for functional correctness, analyzed for code smells and security hotspots, audited for vulnerable packages, and scanned for container vulnerabilities before artifacts are packaged and verified.

```mermaid
flowchart TD
    subgraph SCM["1. Source Control"]
        A[Git Commit &amp; Push] --> B[Jenkins SCM Trigger]
    end

    subgraph ShiftLeft["2. Shift-Left Security &amp; Testing"]
        B --> C[Stage 1: Checkout]
        C --> D[Stage 2: Gitleaks Secret Scan]
        D --> E[Stage 3: Install Dependencies]
        E --> F[Stage 4: Python Unit Tests (pytest)]
        F --> G[Generate JUnit XML Report]
    end

    subgraph SAST["3. Code Quality &amp; SAST"]
        G --> H[Stage 5: SonarQube Scanner Analysis]
        H --> I[Stage 6: SonarQube Quality Gate]
        I -.->|Webhook Notification| J[Jenkins /sonarqube-webhook/]
    end

    subgraph SCA["4. Software Composition Analysis (SCA)"]
        I --> K[Stage 7: Dependency Scan (pip-audit)]
        K --> L[Archive pip-audit-report.json]
    end

    subgraph Containerization["5. Container Security &amp; Packaging"]
        L --> M[Stage 8: Docker Multi-Stage Build]
        M --> N[Stage 9: Trivy Container Image Scan]
        N --> O[Stage 10: Docker Image Inspection &amp; Verification]
    end

    classDef pass fill:#22c55e,stroke:#15803d,color:#ffffff;
    classDef step fill:#1e293b,stroke:#3b82f6,color:#ffffff;
    class A,B,C,D,E,F,H,I,K,M,N,O step;
    class G,J,L pass;
```

---

## 2. Technology Stack & Constraints

- **Backend Framework:** Python 3.12, Flask 3.1.3
- **Templating:** Jinja2
- **Database:** SQLite3 (parameterized queries, isolated in-memory/temp DBs for testing, mounted file storage for containers)
- **Frontend / Styling:** Vanilla CSS3 (responsive flexbox and CSS grid, high contrast accessibility, **Zero JavaScript**)
- **CI/CD Automation:** Jenkins (Windows pipeline agent with `bat` steps)
- **Security & Quality Tooling:**
  - **Secret Detection:** Gitleaks 8.30+
  - **Unit Testing:** Pytest 9.1+ with JUnit XML reporting
  - **SAST & Quality Gate:** SonarQube Community Edition &amp; SonarScanner CLI
  - **SCA (Dependency Vulnerability Scanning):** `pip-audit` (PyPA &amp; OSV database)
  - **Container Vulnerability Scanning:** Aqua Security Trivy (Dockerized)
- **Containerization:** Docker multi-stage build running as a non-privileged `appuser` (UID unprivileged).

---

## 3. Application Features & Dashboard

The application provides four primary views, with comprehensive empty-state handling and explicit demo data indicators:

1. **Dashboard (`/`):**
   - Summary statistics cards: Total Servers, Running Servers, Stopped Servers, Total Deployments, and Pipeline Security status.
   - Recent deployment activity history.
   - Live security check summary indicators.
2. **Servers (`/servers`):**
   - Cloud inventory displaying server names, real-time statuses (Running / Stopped), simulated CPU load, and AWS deployment region codes.
   - Includes graceful empty-state handling if database tables contain 0 rows.
3. **Deployments (`/deployments`):**
   - Deployment records dynamically queried from SQLite (`version`, `environment`, `status`).
   - Clean status badges (`SUCCESS` / `FAILED`).
4. **Security (`/security`):**
   - DevSecOps checklist tracking automated scanning tools (Gitleaks, pytest, SonarQube, pip-audit, Trivy).
   - Clear distinction between demo checklist entries and live CI/CD pipeline execution logs.
5. **Production Hardening & Error Handling:**
   - Custom `404 Not Found` and `500 Internal Server Error` templates preventing stack trace leaks.
   - HTTP security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `X-XSS-Protection`).
   - Explicit `GET` method routing.

---

## 4. Local Quickstart (Windows PowerShell)

### Prerequisites
- Python 3.12+
- Git
- Docker Desktop (optional, for containerization)

### 1. Clone the repository
```powershell
git clone https://github.com/Anas-Qureshi1/cloudops-manager.git
cd "cloudops-manager"
```

### 2. Set up virtual environment and install dependencies
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pytest pytest-cov pip-audit
```

### 3. Initialize and seed the demo database
```powershell
python -m app.seed
```
*Note: The SQLite database initializes at `cloudops.db` by default. Set `$env:DATABASE_PATH="data\cloudops.db"` to use a custom location.*

### 4. Run the Flask development server
```powershell
python -m flask --app app.app run --host=127.0.0.1 --port=5000
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.

---

## 5. Running Automated Tests & Code Coverage

The test suite runs with pytest, generating both a JUnit XML report (`test-results.xml`) and a coverage report (`coverage.xml`) ingested by Jenkins and SonarQube:

```powershell
python -m pytest --cov=app --cov-report=term --cov-report=xml:coverage.xml --junitxml=test-results.xml
```

### Test Coverage Highlights (95% Line Coverage, 12 Tests Passing)
- `test_pages_use_configured_database`: Validates all routes (`/`, `/servers`, `/deployments`, `/security`) respond with HTTP 200.
- `test_pages_show_data_from_configured_database`: Verifies dynamic SQLite data rendering.
- `test_server_data`: Validates server name, region, and running status rendering.
- `test_deployments_show_data_from_configured_database`: Validates dynamic deployments table.
- `test_security_show_data_from_configured_database`: Validates dynamic security checks table.
- `test_empty_database_rendering`: Verifies that empty tables render clean empty-state UI without unhandled 500 errors.
- `test_404_error_page`: Verifies custom 404 page is rendered for undefined paths.
- `test_security_headers_present`: Verifies HTTP security headers (`X-Content-Type-Options`, `X-Frame-Options`).
- `test_seed_database`: Verifies idempotent database initialization and data seeding.

---

## 6. Docker Containerization & Verification

The application uses a secure multi-stage Docker build:
- **Builder Stage (`python:3.12-slim`):** Upgrades pip and pre-compiles wheels into an isolated prefix.
- **Production Stage (`python:3.12-slim`):**
  - Runs as non-root user `appuser` (created with `/usr/sbin/nologin`).
  - Stores SQLite database in `/app/data/` suitable for Docker volume mounting.
  - Container health check: verifies `http://127.0.0.1:5000/` every 30 seconds.
  - Production mode: `FLASK_DEBUG=0`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`.

### Build the Docker image
```powershell
docker build -t cloudops-manager .
```

### Run the container with persistent storage
```powershell
docker run -d --name cloudops-container -p 5000:5000 -v cloudops-data:/app/data cloudops-manager
```

### Verify container health & logs
```powershell
docker logs cloudops-container
docker inspect --format='{{json .State.Health.Status}}' cloudops-container
```

---

## 7. DevSecOps CI/CD Pipeline Implementation

The pipeline is orchestrated via [Jenkinsfile](file:///Jenkinsfile) across 10 stages:

| Stage # | Stage Name | Tool | DevSecOps Purpose |
|:---:|:---|:---|:---|
| **1** | **Checkout** | Git | Clones the repository revision from GitHub. |
| **2** | **Gitleaks Secret Scan** | Gitleaks | Detects committed credentials, API keys, tokens, and private keys. Fails build if leaks are detected (`--exit-code 1`). |
| **3** | **Install Dependencies** | Pip | Installs production requirements, pytest, and pip-audit in CI agent. |
| **4** | **Python Tests** | Pytest | Executes 11 unit tests; publishes `test-results.xml` via Jenkins JUnit plugin. |
| **5** | **SonarQube Analysis** | SonarScanner | Static Application Security Testing (SAST) analyzing code quality, maintainability, and security hotspots. |
| **6** | **SonarQube Quality Gate** | SonarQube Webhook | Evaluates quality gate; blocks build until SonarQube returns `OK` via webhook callback. |
| **7** | **Dependency Vulnerability Scan** | pip-audit | Software Composition Analysis (SCA) querying OSV &amp; PyPA databases for known CVEs. Generates `pip-audit-report.json`. |
| **8** | **Docker Image Build** | Docker Engine | Builds multi-stage production image tagged `cloudops-manager:ci`. |
| **9** | **Trivy Image Scan** | Aqua Trivy | Scans container OS and library layers for vulnerabilities. Blocks build on critical application library CVEs. |
| **10** | **Docker Image Verification** | Docker Engine | Inspects final container image configuration and metadata before release. |

---

## 8. Security Tools Configuration & Setup

### Gitleaks
Gitleaks detects hardcoded secrets across the entire Git history:
- Stable system path: `C:\Tools\gitleaks\gitleaks.exe`
- Pipeline execution:
  ```powershell
  gitleaks git . --redact --exit-code 1
  ```

### SonarQube & Quality Gate
1. **Container Setup:**
   SonarQube Community Edition runs in Docker Desktop:
   ```powershell
   docker run -d --name sonarqube -p 9000:9000 `
     -e SONAR_ES_BOOTSTRAP_CHECKS_DISABLE=true `
     -v sonarqube-data:/opt/sonarqube/data `
     -v sonarqube-extensions:/opt/sonarqube/extensions `
     -v sonarqube-logs:/opt/sonarqube/logs `
     sonarqube:community
   ```
2. **Project Key:** `cloudops-manager`
3. **Jenkins Server Configuration:**
   - In Jenkins &gt; *Manage Jenkins* &gt; *System* &gt; *SonarQube servers*, ensure the server is named `SonarQube` with Server URL `http://localhost:9000`.
   - Add a Jenkins Secret Text credential containing the SonarQube user analysis token.
4. **Webhook Configuration:**
   - In SonarQube &gt; *Administration* &gt; *Configuration* &gt; *Webhooks*, create a webhook:
     - **Name:** `Jenkins-Webhook`
     - **URL:** `http://host.docker.internal:8080/sonarqube-webhook/`
   - *Why `host.docker.internal`?* Because SonarQube runs inside a Docker Desktop container and needs to reach Jenkins running on the Windows host on port 8080.

### pip-audit (Software Composition Analysis)
- `pip-audit` is the official PyPA-recommended auditing tool.
- Why `pip-audit` instead of legacy OWASP Dependency-Check for Python?
  - OWASP Dependency-Check relies heavily on NVD CPE matching, often causing high false positives for Python packages or requiring extensive NVD API rate-limit caching.
  - `pip-audit` connects directly to the PyPA Advisory Database and Google OSV database, providing pinpoint vulnerability identification with zero false-positive CPE matching.

### Trivy Container Scanning
- Trivy scans both operating-system packages (Debian 12) and installed Python wheels.
- Scans run with Docker socket mounting and persistent cache volume:
  ```powershell
  docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v trivy-cache:/root/.cache/ aquasec/trivy:latest image --severity HIGH,CRITICAL cloudops-manager:ci
  ```
- Vulnerability Policy: Displays all `HIGH` and `CRITICAL` findings for auditability, and fails the build if `CRITICAL` vulnerabilities exist in application libraries (`--vuln-type library --severity CRITICAL --exit-code 1`).

---

## 9. Troubleshooting Common Windows & CI/CD Issues

| Issue / Error Message | Root Cause | Solution |
|:---|:---|:---|
| `Call to URL [http://localhost:9000/api/v2/analysis/version] failed: null` | SonarQube container was stopped or Docker Desktop engine was not running. | Start Docker Desktop, then execute `docker start sonarqube`. Wait for `http://localhost:9000/api/system/status` to report `status: UP`. |
| `Both 'sonar.login' and 'sonar.token' are set` | Passing `-Dsonar.token` manually while `withSonarQubeEnv` is already setting token environment variables. | Use `withSonarQubeEnv('SonarQube')` and let the scanner automatically read `SONAR_TOKEN`. |
| `failed to connect to docker API at npipe:////./pipe/dockerDesktopLinuxEngine` | Docker Desktop was closed or WSL2 backend was restarting. | Launch Docker Desktop (`Docker Desktop.exe`) and confirm `docker ps` returns successfully. |
| `Selected Git installation does not exist. Using Default` | Jenkins global tool configuration has a missing named Git tool reference. | Non-blocking warning; Jenkins automatically falls back to system Git on PATH. |
| `Gitleaks not recognized` under Jenkins LocalSystem account | User-level winget links in `AppData\Local` are not accessible to `LocalSystem`. | Store `gitleaks.exe` in `C:\Tools\gitleaks\gitleaks.exe` which is globally accessible. |

---

## 10. Security Boundaries & Demo Disclaimer

> [!NOTE]
> **Demo Data Notice:** CloudOps Manager is a learning and portfolio demonstration project. Server inventories, deployment histories, and security check items displayed in the web dashboard are seeded demo data populated from SQLite to demonstrate interface layout, operational metrics, and error states. This application does not connect to live AWS credentials or provision actual cloud instances.

---

## 11. Future Roadmap

- [ ] Dynamic Application Security Testing (DAST) using OWASP ZAP against running container.
- [ ] Terraform infrastructure-as-code manifests for automated AWS VPC &amp; ECS Fargate provisioning.
- [ ] AWS ECR image push with AWS IAM least-privilege role assumption.
- [ ] Production WSGI server (Gunicorn / Waitress) configuration behind Nginx reverse proxy.
- [ ] GitHub Actions parallel workflow mirroring Jenkins pipeline for hybrid CI/CD comparison.
