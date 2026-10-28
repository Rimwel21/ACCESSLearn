# Threat Model

## Method and assumptions

This lightweight model considers users, browsers, the API, database, uploads, media/mail providers, and administrators. It assumes production uses HTTPS, secrets are not committed, and hosting accounts are separately protected.

| Threat | Example impact | Existing/added mitigation | Remaining action |
|---|---|---|---|
| Unauthorized account access | Attacker reads learner records or changes scores | bcrypt, generic invalid-credential response, rate limiting, OTP recovery, failed-login audit | Add privileged-account MFA and alerting |
| Broken access control | Student invokes teacher/admin endpoint | Central authentication, role guards, ownership filters, 401/403 responses | Continue endpoint-level authorization tests |
| Privilege escalation | Teacher attempts administrator action | Administrator dependency and service checks | Periodic route inventory and access review |
| Token theft | Stolen access token impersonates a user | Short expiry, blocked-account check on every protected request, HTTPS requirement | Remove access tokens from localStorage in a future auth redesign |
| Session theft/reuse | Stolen refresh token renews access | HttpOnly, SameSite, production Secure cookie, logout cookie clearing | Add rotation, unique token IDs and revocation storage |
| Cross-Site Scripting | Script steals local data/token | Vue escaping by default, no observed `v-html`, restricted dependencies | Deploy and test a frontend CSP; perform XSS testing |
| SQL injection | Crafted input changes database query | SQLAlchemy ORM and bound parameters in maintenance SQL | Review every new raw SQL statement |
| Malicious upload | Polyglot or oversized document exhausts or attacks processing | Allowlist, MIME and signature checks, size limit, sanitized/server-generated name | Add sandboxing and malware scanning in production |
| Brute-force login/OTP | Account or recovery takeover | Per-IP limits, OTP expiry and attempt counters, failed-login audit | Add account-aware throttling/alerts and enforce OTP attempt lockout consistently |
| Data exposure | Personal records leak through logs, responses, backups or browser cache | Response models, restricted roles, no-store auth headers, data classification | Formal retention, encrypted backups, privacy review |
| Improper CORS | Malicious origin invokes credentialed requests | Explicit origins, methods and headers; no wildcard | Keep production `CORS_ORIGINS` minimal |
| Compromised dependency | Malicious/vulnerable library executes | Version inventory and pinned backend dependencies | Automate recurring dependency scans and review lockfiles |
| Audit tampering | Attacker hides activity | Administrator-only viewing and database audit records | Export to append-only/central storage and monitor access |
| Service or data loss | Database/media failure interrupts learning | Backup and restore plan | Implement, encrypt and test actual backups |

## Highest-priority residual risks

1. Browser access-token storage.
2. Stateless refresh tokens without rotation/revocation.
3. No production malware scanner or document-processing sandbox.
4. No demonstrated encrypted backup and restore test.
5. No centralized security monitoring or alerting.
