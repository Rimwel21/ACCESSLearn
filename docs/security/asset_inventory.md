# Asset Inventory

## Scope and ownership

The project team owns the application code and configuration. The deployed system operator is responsible for accounts, databases, secrets, backups, media storage, logs, and access reviews. A named individual should be assigned these operational responsibilities before deployment.

| Asset | Actual use in SIGNHEAR | Primary protection need |
|---|---|---|
| Student accounts | Username, email when available, role, verification and account status | Confidentiality, integrity, availability |
| Teacher accounts | Email, role, verification and account status | Confidentiality, integrity, availability |
| Administrator accounts | Privileged account used for management and audit access | Strong confidentiality and integrity |
| Password hashes | bcrypt hashes in the accounts table | Confidentiality and integrity; never export unnecessarily |
| JWT and refresh tokens | Authenticate API requests and renew access | Confidentiality, short lifetime, secure transport |
| OTP records | Hashed OTP, role, expiry, usage state, and attempt count | Confidentiality, integrity, prompt expiry |
| Student profiles | Name, LRN, age, sex, grade, section, accessibility profile, guardian/contact and address fields | Sensitive personal information |
| Teacher profiles | Name, age, sex, contact number, grade assignments, address and email | Confidential personal information |
| Learning progress | Topic status, quiz/activity answers, scores, attempts, remediation and retake information | Confidentiality and integrity |
| Classes and sections | Membership, teacher assignments, grade levels and school years | Confidentiality and integrity |
| Learning materials | PDF, Word and presentation uploads plus generated topics and images | Integrity, availability, safe processing |
| Handsign datasets/models | Training samples, tutorial media, practice results and recognition model artifacts | Integrity and availability; practice records may be confidential |
| Profile/media storage | Profile images and generated/uploaded learning media | Confidentiality appropriate to content, integrity, availability |
| Audit logs | Actor, role, action, affected record, IP, user agent, device and timestamp | Integrity, restricted access, retention controls |
| PostgreSQL database | Production account, profile, class, learning, progress, OTP and audit data | Confidentiality, integrity, availability |
| SQLite database | Local/offline development data in `local.db` | Local access control; never commit or use production data casually |
| Backend API | FastAPI services and authorization decisions | Integrity, availability, restricted network access |
| Frontend/PWA | Vue application, browser caches and offline data | Integrity and protection of browser-stored data |
| Secrets/configuration | JWT secret, database URL, mail, Cloudinary and VAPID credentials | Strict confidentiality; environment-based loading only |
| Backups | Database dumps, media copies and configuration recovery material | Encryption, access control, tested restoration |

## Review cadence

Review quarterly during active development and before every production deployment. Add new third-party services, data categories, secrets, and storage locations when introduced.
