# SIGNHEAR Partial Cybersecurity Operations Note

This note records a limited set of controls and operational steps. It does not claim full OWASP, ISO/IEC 27002, or Philippine Data Privacy Act compliance.

## Assets and sensitive data

- Vue frontend, FastAPI API, SQLAlchemy data layer, SQLite for local development, and PostgreSQL/Supabase for deployed environments.
- JWT access tokens and an HTTP-only refresh cookie provide authentication. Student, teacher, and administrator roles restrict protected operations.
- Sensitive data includes password hashes, tokens, student LRNs, accessibility profiles, guardian contact details, assessment records, uploaded learning materials, and audit metadata.

## Local SQLite backup and restore

Only perform these steps while the local API is stopped so the database is not being written.

1. Copy `local.db` to an access-controlled location outside the repository. Use a dated filename and do not commit it.
2. Verify that the backup file exists and has a non-zero size.
3. To test restoration, copy the backup into a separate temporary development directory as `local.db` and start SIGNHEAR against that copy.
4. Confirm that the application starts and that a safe test account can read expected non-production records.
5. Delete temporary restored copies securely when testing is complete.

Production PostgreSQL/Supabase backup scheduling and restore testing must be configured and verified by the authorized deployment owner. This repository does not prove that automated production backups exist.

## Minimal incident response

1. Preserve relevant audit logs and record the date, affected account, endpoint, and observed behavior. Never copy passwords or tokens into an incident note.
2. Suspend affected accounts through the existing administrator controls and rotate exposed application secrets through the deployment platform.
3. Review authentication failures and authorization-denied events, then determine the affected records and time range.
4. Restore data only from a verified backup and document the validation performed after restoration.
5. Notify the project adviser and authorized data-protection contact when personal data may be affected. Follow the institution's approved breach-assessment and notification process.

## Standards mapping

- Token separation, role checks, and login validation partially align with OWASP authentication, identification, and access-control guidance.
- Secret redaction, audit logging, and backup procedures partially align with ISO/IEC 27002 controls for logging, information backup, access control, and incident management.
- Data minimization in logs and the incident procedure support principles relevant to the Philippine Data Privacy Act, but legal compliance has not been independently assessed.
