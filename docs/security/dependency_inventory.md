# Dependency Inventory and Review Procedure

## Runtime components

| Layer | Key components | Source of exact version evidence |
|---|---|---|
| Frontend | Vue 3, Vue Router, Pinia, Axios, Vite, TypeScript, Tailwind CSS | `E-Learn/frontend/package.json` and installed lockfile |
| Backend | FastAPI, Starlette, Uvicorn, SQLAlchemy, Alembic, Pydantic, passlib/bcrypt, python-jose, SlowAPI | `E-Learn/Backend/requirements.txt` |
| Data | SQLite locally; PostgreSQL/Supabase for production/staging | `database/connection.py` and deployment configuration |
| File/media | Cloudinary, PDF/Word/PowerPoint processing libraries | Backend requirements and storage configuration |
| Recognition | OpenCV, MediaPipe, scikit-learn and NumPy | Backend requirements and model artifacts |
| Browser/PWA | Browser storage, service worker/offline cache and camera APIs | Frontend source and browser deployment |

This is a lightweight software-bill-of-materials index, not a vulnerability scan. Transitive dependencies and deployed platform packages must also be inventoried from lockfiles and hosting records.

## Review procedure

Run in a clean development environment before releases:

```text
npm audit
npm outdated
python -m pip check
python -m pip_audit -r requirements.txt
```

If `pip-audit` is unavailable, install it in an isolated development environment rather than adding it to production runtime requirements. Record the date, tool version, findings, severity, affected version, decision, owner and target date.

## Update policy

- Do not blindly upgrade every package.
- Prioritize remotely exploitable authentication, web framework, parsing, upload and cryptography vulnerabilities.
- Test updates with the frontend build, backend suite and critical user flows.
- Keep exact production dependency resolution in lockfiles or a generated requirements lock.
- Remove unused packages and review packages without pinned versions/ranges.
- Re-scan monthly during development and immediately before deployment.

## Current limitations

- Backend `opencv-python` is not exactly pinned and NumPy uses a version range.
- Frontend manifest uses compatible-version ranges; the lockfile is required for exact deployed versions.
- Automated CI scanning, signed artifacts and a generated CycloneDX/SPDX SBOM are not yet configured.

## Latest local review

On 2026-10-28, `npm audit --omit=dev --audit-level=high` initially reported seven high-severity advisory groups in the resolved frontend dependency tree. `npm audit fix` applied compatible updates, after which npm reported zero known vulnerabilities and the production frontend build passed. This result reflects the npm advisory database at scan time and must be repeated regularly.

The Python environment did not have `pip-audit` installed, so no claim is made that the backend dependency set is vulnerability-free. A backend audit remains required before production deployment.
