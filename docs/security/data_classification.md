# Data Classification

## Levels

### Public

Information intentionally available without authentication, such as public landing-page content and non-sensitive system descriptions. Public does not mean unowned; integrity still matters.

### Internal

Source code, non-secret deployment instructions, grade/section definitions, generic learning-resource metadata, and operational documentation intended for the project team.

### Confidential

Teacher contact/profile information, class membership, uploaded learning materials that are not public, assessment definitions and answers, learner progress, scores, attempt history, remediation records, audit logs, IP addresses, user agents, and local cached learning responses.

### Sensitive personal information / high-impact credentials

Student LRN, accessibility profile, guardian/contact information, address, account recovery data, password hashes, JWTs, refresh tokens, OTP hashes, database credentials, JWT signing secret, mail credentials, Cloudinary credentials, VAPID private key, and backups containing any of these values.

## Handling rules

| Level | Storage | Access | Transmission | Disposal |
|---|---|---|---|---|
| Public | Approved application locations | Public read; controlled write | HTTPS recommended | Normal content lifecycle |
| Internal | Project-controlled repositories/services | Team members with a work need | Authenticated channels | Remove when obsolete |
| Confidential | Access-controlled database or approved media storage | Role- and ownership-based access | HTTPS required in production | Delete or anonymize under an approved retention schedule |
| Sensitive/high-impact | Secret manager/environment or tightly controlled database | Least privilege only | Encrypted transport only | Secure deletion and rotation where applicable |

## Restrictions

- Never commit `.env`, database files, plaintext passwords, OTP codes, tokens, or private keys.
- Do not use real learner records in demonstrations or tests unless explicitly authorized and protected.
- Do not place confidential data in logs unless required, minimized, and access-controlled.
- Browser offline storage must not be treated as encrypted storage.
