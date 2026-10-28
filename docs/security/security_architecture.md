# Security Architecture

## Components and trust boundaries

1. The Vue 3 PWA runs in the learner, teacher, or administrator browser.
2. The browser calls the FastAPI backend over HTTP during local development and HTTPS in production.
3. FastAPI validates requests, authenticates JWTs, enforces account status and role checks, and performs business authorization.
4. SQLAlchemy accesses SQLite for local development or Supabase PostgreSQL for staging/production.
5. Cloud/media storage receives profile images; local upload directories hold learning materials and generated artifacts.
6. Mail infrastructure delivers registration and password-reset OTPs.
7. Audit records are stored in the application database and exposed only through administrator routes.

Each browser-to-API, API-to-database, API-to-mail, and API-to-media connection crosses a trust boundary. Input received across a boundary must be authenticated where required, validated, bounded, and safely logged.

## Implemented controls

- bcrypt password hashing; plaintext passwords are not stored by the backend.
- Signed JWT access and refresh tokens with configured expiration.
- HttpOnly refresh cookie with environment-aware `Secure` and `SameSite` settings.
- Central rejection of blocked, suspended, archived, inactive, pending, or otherwise unauthorized accounts using existing tokens.
- Student, teacher, and administrator route guards, supplemented by ownership checks in services.
- Per-IP rate limits on login, registration, OTP and major application endpoints.
- Pydantic request validation and SQLAlchemy ORM operations.
- Restricted CORS origin/method/header configuration.
- Upload extension, MIME, size, server-generated filename, path sanitization, and file-signature checks.
- API security headers: `nosniff`, frame denial, referrer policy, permissions policy, and production-only HSTS.
- Audit events for successful login, failed login, inactive-token use, forbidden role access, and administrative/business actions.
- Environment-based secret loading; `.env` and local databases are ignored by Git.

## Known architectural limitations

- Access tokens remain in browser `localStorage`; migrating to an HttpOnly-cookie or backend-for-frontend design requires coordinated authentication changes.
- Refresh tokens are stateless and are not yet rotated or server-side revoked.
- Offline login is disabled by default because a locally stored password verifier increases device-compromise risk.
- Malware scanning is not provided; file-type checks reduce but do not eliminate malicious-document risk.
- Content Security Policy belongs on the frontend hosting layer and must be tested against camera, PWA, media, and development requirements before enforcement.
