# SIGNHEAR

SIGNHEAR is an accessible and inclusive Science e-learning system for intermediate learners with hearing impairment. It supports Grades 4 to 6 with sign-language-supported learning materials, assessments, learning activities, camera-based sign alphabet recognition, and learner progress monitoring.

This repository contains the academic capstone implementation developed for Claro M. Recto Memorial Central School in Tiaong, Quezon.

## Core features

- Recorded sign-language-supported Science lessons and learning materials
- Quizzes, activities, remediation, retakes, and attempt history
- Camera-based sign language alphabet and Science vocabulary practice
- Learner progress, scores, completion, and performance monitoring
- Teacher tools for classes, modules, assessments, records, and interventions
- Administrator tools for accounts, grade levels, sections, datasets, audit logs, and system monitoring
- Progressive Web App support for approved offline learning resources
- Upload and presentation processing for instructional materials

## User roles

| Role | Main capabilities |
| --- | --- |
| Student | Access assigned lessons and activities, complete assessments, practise signs, and view permitted progress records |
| Science Teacher | Manage authorized classes, learning materials, assessments, learner progress, remediation, and retakes |
| Administrator | Manage accounts, academic structures, account status, datasets, audit records, and system monitoring |

Authorization is enforced by the backend. Interface visibility alone is not treated as access control.

## Technology stack

- Frontend: Vue 3, TypeScript, Vite, Pinia, Vue Router, and Tailwind CSS
- Backend: Python, FastAPI, SQLAlchemy, and Alembic
- Data: SQLite for local development and Supabase PostgreSQL for production or cloud staging
- Media: Cloudinary and controlled local static storage
- Recognition: OpenCV, MediaPipe, scikit-learn, and trained gesture models
- PWA: Web App Manifest, service worker, offline storage, and synchronization controls

## Repository structure

```text
SIGNHEAR/
|-- E-Learn/frontend/    Vue and TypeScript application
|-- routes/              FastAPI route definitions
|-- services/            Application and business logic
|-- models/              SQLAlchemy database models
|-- schemas/             Request and response validation
|-- repositories/        Data-access operations
|-- alembic/             Database migrations
|-- model/               Sign-recognition training files and models
|-- static/              Approved media and generated presentation assets
|-- tests/               Backend and security tests
|-- docs/                Cybersecurity plan and demonstration guides
|-- main.py              FastAPI application entry point
`-- requirements.txt     Python dependencies
```

## Local development

### Requirements

- Python 3.11 or a compatible Python version
- Node.js and npm
- Git LFS for the trained models and media tracked through LFS

### Backend

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn main:app --reload
```

The example environment uses `sqlite:///./local.db`. Replace placeholder values in `.env` only on your local machine. Never commit real credentials.

### Frontend

```powershell
Set-Location E-Learn\frontend
npm install
npm run dev
```

The development frontend is available at `http://localhost:5173` by default. The FastAPI documentation is normally available at `http://127.0.0.1:8000/docs` while the backend is running.

## Useful checks

```powershell
pytest
Set-Location E-Learn\frontend
npm run build
```

## Security and privacy

SIGNHEAR handles educational and accessibility-related information. Development and deployment should preserve least-privilege access, private learner records, secure password handling, server-side authorization, safe uploads, restricted PWA caching, protected secrets, audit logging, and tested backup procedures.

Security implementation notes and demonstration steps are available in [`docs/`](docs/).

## Project status

SIGNHEAR is an academic capstone project under active development and validation. Features, security controls, deployment settings, and recognition accuracy should be tested before production use.

## Repository access

This is a private project repository. Access and reuse require authorization from the project owner and team.
