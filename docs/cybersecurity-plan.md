# CYBERSECURITY PLAN FOR SIGNHEAR: AN ACCESSIBLE AND INCLUSIVE SCIENCE E-LEARNING SYSTEM FOR GRADES 4 TO 6 LEARNERS WITH HEARING IMPAIRMENT

Prepared by:

- Rymuel I. Bugarin
- Denmhar S. Dimaculangan
- Aguiluz Emmanuele D. Peregrin

Group: SIGNHEAR  
Document status: Partial implementation and proposed controls  
Review date: November 5, 2026

> This plan distinguishes controls verified in the local `feature/denmhar` branch from controls that are only partly implemented, planned, or not yet verified in a deployed environment. It does not claim full OWASP, ISO/IEC 27002, or Philippine Data Privacy Act compliance.

## 1. System Overview and Asset Inventory

### 1.1 System overview and scope

SIGNHEAR is a Science e-learning system for intermediate learners with hearing impairment at Claro M. Recto Memorial Central School in Tiaong, Quezon. It supports Grades 4 to 6 through recorded sign-language-supported learning materials, quizzes, activities, alphabet-learning features, camera-based sign recognition, and learner progress monitoring.

SIGNHEAR has three application roles:

- **Student:** accesses assigned lessons, activities, quizzes, and the student's permitted learning records.
- **Science Teacher:** manages authorized classes, learning materials, quizzes, activities, learner progress, and retakes.
- **Administrator:** manages accounts, official grade levels and sections, account status, the hand-sign dataset, audit information, and other administrative operations.

The current technical environment uses Vue 3 and TypeScript for the frontend; a custom service worker for PWA behavior; Python and FastAPI for backend services; SQLAlchemy and Alembic for data access and migrations; SQLite for local development; PostgreSQL/Supabase for the intended deployed structured-data environment; Cloudinary for selected media; and `python-jose` for JWT handling.

The plan addresses confidentiality, integrity, and availability. Confidentiality protects learner and staff data from unauthorized disclosure. Integrity protects scores, progress, permissions, learning materials, and recognition assets from unauthorized modification. Availability supports continued access to learning resources and recovery after failure.

### 1.2 Major components and assets

| Component or asset | Information or function | Classification | Primary protection requirement |
|---|---|---|---|
| Frontend and PWA | Interface, navigation, learning display, browser storage | Operational | Controlled builds, safe rendering, restricted caching |
| FastAPI backend | Authentication, authorization, assessments, uploads, administration | Critical operational | Server-side authorization, validation, rate limiting |
| SQLite/PostgreSQL data | Accounts, enrollment, classes, scores, attempts, progress | Restricted | Least privilege, protected connections, verified backups |
| Learner and staff records | Identity, age, contact, education, accessibility information | Restricted sensitive personal information | Data minimization and record-level authorization |
| Assessment records | Answers, scores, attempts, retakes, progress | Restricted educational records | Server-side validation and transaction integrity |
| Uploaded learning resources | Modules, presentations, videos, profile images | Private unless approved for learning delivery | Format and size validation, controlled publication |
| Recognition assets | Hand-sign dataset, model files, configuration | Controlled technical assets | Restricted modification, versioning, integrity evidence |
| Secrets, logs, and backups | Credentials, signing keys, audit events, recovery copies | Highly restricted | Secret management, restricted access, retention and restoration testing |

Camera frames and hand landmarks should be processed only for their approved recognition purpose and should not be retained by default. This remains a policy requirement until every deployed recognition, logging, and provider path has been verified.

### 1.3 Roles and access boundaries

| Role | Permitted access | Restrictions |
|---|---|---|
| Student | Assigned learning resources and own permitted profile, answers, scores, attempts, and progress | Cannot view another learner's records, grant retakes, change roles, or administer datasets |
| Science Teacher | Authorized classes, materials, assessments, class progress, and retakes | Cannot change roles, administer unrelated classes, or modify official structures without authorization |
| Administrator | Accounts, official grade/section structures, account status, approved dataset operations, audit functions | Application administration does not automatically grant direct unrestricted database access |
| Authorized school personnel | Advisory or evaluation functions approved by the school | No separate application access unless explicitly authorized |

Backend authorization must verify authentication, account status, role, record ownership, and class scope. Hiding a frontend control is not sufficient authorization.

### 1.4 Protected data flow

1. A user accesses SIGNHEAR through a browser or installed PWA.
2. Protected production communication must use HTTPS.
3. The backend validates the token, token purpose, account status, and requested operation.
4. Server-side authorization determines whether database or media access is permitted.
5. Selected authentication, authorization, and administrative operations generate audit events.
6. The service worker caches the application shell and static assets but bypasses API requests. Separate application-level offline storage currently caches selected student responses and requires further privacy review.
7. Synchronization must revalidate authentication, ownership, authorization, and duplicate submissions.

## 2. Risk and Threat Assessment

### 2.1 Method and Priority Matrix

OWASP Top 10:2025 is used to group relevant application-security threat scenarios, not to assert that the vulnerabilities have been proven in SIGNHEAR [2]. Likelihood estimates the conditions and opportunity required for misuse; impact estimates harm to learners, records, or service availability; priority follows the project risk matrix. "High priority" indicates that a threat scenario requires immediate, validated controls, not that it is automatically easy to exploit.

#### Likelihood and Impact Rating Definitions

| Rating | Likelihood Definition | Impact Definition |
| :--- | :--- | :--- |
| **High** | Routine workflow creates a direct opportunity when safeguards are absent | Restricted data exposure, privileged takeover, widespread alteration, or major service outage |
| **Medium** | An additional condition or compromise is required (e.g. compromised token, malicious upload) | Limited exposure, recoverable modification, or temporary disruption |
| **Low** | Several uncommon conditions are required (e.g. multi-step failure under isolated conditions) | Minor constrained exposure or brief interruption |

#### Priority Determination Matrix

| Likelihood \ Impact | Low Impact | Medium Impact | High Impact |
| :--- | :---: | :---: | :---: |
| **Low Likelihood** | Low | Low | Medium |
| **Medium Likelihood** | Low | Medium | **High** |
| **High Likelihood** | Medium | **High** | **High** |

---

### 2.2 Initial Risk Register

| ID | OWASP Top 10:2025 Mapping | Grade 4 SIGNHEAR Threat Scenario | Likelihood | Impact | Priority |
| :---: | :--- | :--- | :---: | :---: | :---: |
| **R1** | A01 Broken Access Control | Student accesses another learner’s record; teacher accesses an unrelated class | High | Medium | Medium |
| **R2** | A07 Authentication Failures | Compromised staff/admin credentials enable unauthorized privileged actions | Medium | High | **High** |
| **R3** | A02 Security Misconfiguration | Debug output, unsafe CORS, or publicly accessible private media | Medium | High | **High** |
| **R4** | A04 Cryptographic Failures | Exposed signing key, weak password storage, or unprotected database snapshot | Medium | Medium | Medium |
| **R5** | A05 Injection | Unsafe user input reaches queries or rendered lesson content | Medium | High | **High** |
| **R6** | A03 Supply Chain Failures | Compromised dependency or build action reaches production release | Medium | Medium | Medium |
| **R7** | A08 Software or Data Integrity Failures | Unauthorized recognition model or dataset modification | Medium | Medium | Medium |
| **R8** | A06 Insecure Design | Replayed submissions change progress or consume retake quota twice | Medium | Medium | Medium |
| **R9** | A07 Authentication Failures / A02 Misconfiguration | Prior user session or private cached data accessible on a shared computer lab browser | Medium | Medium | Medium |
| **R10** | A09 Logging and Alerting Failures | Abuse, mass access, or privilege escalation remains unnoticed by administrators | Medium | High | **High** |
| **R11** | A10 Exceptional Conditions | Service exhaustion or failed operations damage system availability | Medium | High | **High** |
| **R12** | A06 Insecure Design | Insufficient restrictions permit dangerous uploaded file type or processing payload | Medium | Medium | Medium |

#### System Operational Triage vs. Paper Prioritization
In the academic risk assessment register above (on paper), threat scenarios such as **R1 (Broken Access Control)**, **R4 (Cryptographic Failures)**, **R8 (Insecure Design)**, and **R12 (Unsafe Upload Design)** are classified with a **Medium** priority rating based on Grade 4 classroom constraints and compensatory controls. However, in the **live SIGNHEAR system implementation** (Administrator Audit Log & alert telemetry), all operational events involving access denial, authentication failures, and database backup/restoration lifecycles are explicitly elevated to **HIGH** severity (or **CRITICAL** for integrity validation failures). This intentional elevation guarantees that administrators receive immediate, high-priority visual badges and telemetry alerts in the live console whenever sensitive operations or potential policy violations occur.

#### Mapping Notes and Priority Distribution
- **R9 Mapping Context**: Concerns lingering authentication/session state and browser-storage configuration in shared school environments; a separate record-level permission failure would also involve A01.
- **R12 Upload Design Context**: Primarily addresses unsafe upload-control design, for which OWASP identifies unrestricted dangerous file types under A06; A05 is added only where a specifically identified injection path exists [2].
- **Priority Summary**: The matrix identifies **five High-priority scenarios** (**R2, R3, R5, R10, and R11**) and **seven Medium-priority scenarios**. These represent inherent, design-based assessments rather than residual-risk ratings. Risk reduction requires verified implementation evidence, automated testing, and ongoing administrative review.

## 3. Security Architecture and Controls

### 3.1 Current and proposed architecture

```text
User browser/PWA
        |
        | HTTPS required in production
        v
Hosting / reverse proxy / WAF (planned or deployment-dependent)
        |
        v
FastAPI: authentication -> authorization -> validation -> service logic
        |                                      |
        v                                      v
SQLite/PostgreSQL                         approved media services
        |
        v
restricted audit and operational records
```

A WAF and reverse proxy supplement application controls; they do not replace backend authorization. Their production configuration is not verified by this repository.

### 3.2 Control implementation status

| Control | Current evidence | Status | Remaining work |
|---|---|---|---|
| C1 Authorization | Authenticated account checks and role guards; ownership/class checks on selected operations | Partly implemented | Complete endpoint-by-endpoint authorization review |
| C2 Account protection | Individual accounts, bcrypt hashing, password rules, login rate limit, OTP-supported recovery | Partly implemented | Staff MFA, compromised-password screening, Argon2id migration evaluation |
| C3 Session management | Expiring JWTs, HttpOnly refresh cookie, secure production-cookie setting, token-purpose separation, logout cookie deletion | Partly implemented | Remove access token from local storage; rotation, revocation, issuer/audience, inactivity and absolute limits, CSRF design |
| C4 Network and transport | Restricted CORS configuration and production HSTS option | Partly implemented | Verify HTTPS, proxy/WAF, database-network restrictions, least-privilege production credentials |
| C5 Browser security | API CSP baseline, X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy, selected no-store responses | Partly implemented | Frontend-host CSP/header verification; camera policy validation |
| C6 Input/output handling | Pydantic validation, SQLAlchemy bound queries, login normalization, safe error responses | Partly implemented | Complete input/output and stored-content review |
| C7 Upload protection | Extension, MIME, signature and size checks; server-generated filenames on selected uploads | Partly implemented | Quarantine, malware scanning, private-delivery review |
| C8 Encryption and secrets | Environment-based secrets and expanded ignore rules | Partly implemented | Rotation procedure, secret manager, backup encryption verification |
| C9 Supply chain and model integrity | Pinned Python requirements and frontend lockfile | Partly implemented | Automated vulnerability/secret scans; model and dataset hashes; release records |
| C10 PWA and synchronization | Service worker bypasses APIs; logout clears selected browser state; backend rechecks queued mutations | Partly implemented | Review IndexedDB/profile caching, offline login, shared-device data clearing and account isolation |
| C11 Backup and recovery | Automated atomic SQLite backup, PostgreSQL snapshot export, SHA-256 cryptographic verification, sandbox dry-run restoration, pre-restore safety snapshot rollback, and Admin GUI integration (verified by test_backup_restore.py) | Implemented (Feature Branch) | Production cron orchestration, off-site encrypted replica sync |
| C12 Monitoring and alerts | 13-action audit logging engine with automated severity triage (CRITICAL, HIGH, MEDIUM, LOW), sensitive payload redaction, and Admin GUI security monitoring (verified by test_security_controls.py) | Implemented (Feature Branch) | External SIEM webhook forwarding, automated email/SMS alerts on critical security events |

### 3.3 Authentication, authorization and sessions

Current local configuration uses a 30-minute access-token lifetime and a seven-day refresh-token lifetime. The refresh token is sent in an HttpOnly cookie. Access and refresh tokens have separate token-purpose claims in the local feature branch. Account status is checked when protected APIs are accessed.

The frontend currently stores the access token in browser local storage. Therefore the safer cookie/BFF design below is a target, not a completed control.

| Session parameter | Current evidence | Target subject to testing |
|---|---|---|
| Access-token lifetime | 30 minutes in `.env.example` | 15 minutes |
| Refresh-token lifetime | 7 days in `.env.example` | Fit within an approved absolute session lifetime |
| Absolute session lifetime | Not implemented | 8 hours |
| Inactivity limit | Not implemented | 20 minutes |
| Failed login | 5 requests/minute endpoint rate limit | Evaluate progressive delay or account-safe throttling |
| Logout | Deletes browser refresh cookie and frontend state | Server-side refresh revocation and complete shared-device cleanup |

The target JWT validation should include signature, explicitly permitted algorithm, expiration, issuer, audience, and token purpose. Cookie-authenticated state-changing operations require a documented CSRF and Origin-validation design.

### 3.4 HTTP, validation and upload controls

The backend currently applies an API-focused Content Security Policy (`default-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'`), `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, selected `Cache-Control: no-store`, and optional production HSTS. FastAPI's local interactive documentation is excluded from the API CSP so its required development assets continue to work. The Vue frontend host or deployment proxy must define and verify a separate frontend-compatible CSP.

Backend schemas validate selected types, lengths, ranges, required fields, and allowed values. SQLAlchemy is used for bound database operations. Login identifiers are trimmed, control characters are rejected, and exactly one username or email is required in the local feature branch.

Selected learning-material uploads check extension, declared MIME type, content signature, and file size, and generate server-controlled filenames. Quarantine and malware scanning remain planned. Recognition models must not be accepted through ordinary media-upload paths.

### 3.5 PWA, secrets and software integrity

The custom service worker caches the application shell and static assets and bypasses API requests. Separate application code currently stores selected student API responses in IndexedDB and stores the access token in local storage. This conflicts with the target rule that profiles, scores, answer keys, tokens, and administrative responses should not persist in shared-browser storage. That gap requires design and usability review before production.

Database credentials, JWT keys, provider credentials, and other secrets must remain server-side. `.env`, private-key formats, and local backup files are excluded from version control in the feature branch. Dependency scanning, secret scanning, and model/dataset integrity hashes remain planned.

## 4. Standards, Compliance and Governance

### 4.1 ISO/IEC 27002 alignment

This mapping demonstrates design alignment only; it is not an ISO certification or a complete control audit.

| SIGNHEAR control | ISO/IEC 27002:2022 theme | Current evidence | Remaining work |
|---|---|---|---|
| Role, ownership and class authorization | Identity management and access control | Backend authentication, account-status checks and role guards | Complete endpoint-by-endpoint authorization review |
| Password and session protection | Authentication information and secure authentication | bcrypt password hashing, expiring JWTs, protected refresh cookie and token-purpose separation | MFA, safer browser storage, rotation, revocation and absolute/inactivity limits |
| Audit logging and secret redaction | Logging, monitoring activities and protection of records | Selected authentication/administrative events and redacted bounded metadata | Central alerts, protected retention and formal log review procedure |
| Input and upload validation | Secure coding and application-security requirements | Pydantic validation, SQLAlchemy bound expressions, extension/MIME/signature/size checks | Malware scanning, quarantine and complete stored-content review |
| Backup and restoration | Information backup and ICT readiness for continuity | Documented local SQLite copy and isolated-restore procedure | Encrypted production schedule, RPO/RTO and recorded restoration exercise |
| Incident response | Incident management planning, assessment and response | Documented detection, containment, recovery, reporting and corrective-action process | Approved contact list, exercise, evidence-retention rules and provider escalation paths |

### 4.2 PCI DSS applicability

SIGNHEAR does not process, store or transmit payment-card data in its documented scope. PCI DSS is therefore not applicable to the current system. If payment functionality is introduced later, the project owner must reassess scope before deployment and must not reuse this non-applicability statement.

### 4.3 Privacy and data protection

Learner age, education records, and health or accessibility-related information can qualify as sensitive personal information under Republic Act No. 10173. Processing must follow transparency, legitimate purpose, proportionality, data minimization, accuracy, limited retention, and appropriate safeguards.

Before production, the school or authorized project owner should document:

- the lawful and institutional basis for each collected field;
- parent or guardian processes applicable to minor learners;
- retention and deletion periods;
- procedures for access, correction, and authorized disclosure;
- responsibilities for Supabase, Cloudinary, hosting, email, and other processors;
- a designated privacy or data-protection contact; and
- breach assessment and notification procedures.

Not every technical error is automatically a legally notifiable personal-data breach. The authorized privacy contact must assess the incident and, where mandatory-notification criteria apply, follow the applicable National Privacy Commission timeline and requirements.

### 4.4 Fortinet NSE 1–3 concepts applied

The assignment's NSE 1–3 tie-in is reflected through the following cybersecurity-fundamentals concepts. These are design influences, not a claim that Fortinet products are deployed or that certification has been awarded:

- the threat-landscape and attack-surface concepts inform the SIGNHEAR asset inventory and risk register;
- confidentiality, integrity and availability guide protection of learner records, scores, learning materials and service continuity;
- social-engineering and credential-theft concepts support individual accounts, password protection, rate limiting, staff MFA as future work and user-awareness recommendations;
- malware and malicious-content concepts support upload validation and the planned quarantine/scanning workflow;
- defense in depth supports combining backend authorization, validation, browser headers, restricted CORS, audit logging, backups and a proposed WAF/reverse proxy; and
- firewall and network-security concepts inform the proposed placement of a WAF/reverse proxy at the public boundary while preserving application-level authorization.

## 5. Backup, Recovery and Incident Response

### 5.1 Verified local procedure

The local API must be stopped before copying SQLite data. `local.db` should be copied to an access-controlled location outside the repository, checked for non-zero size, and restored only into a separate test location. A safe test account should confirm expected data after restoration. Temporary restored copies must be removed when no longer required.

### 5.2 Production requirements

Production PostgreSQL/Supabase backup scheduling, encryption, retention, access, recovery point objective, recovery time objective, and restoration testing are not verified by this repository. The authorized deployment owner must configure and record them.

### 5.3 Minimal incident process

Detection sources include failed-login and authorization events, Administrator Audit Log records, unexpected server errors, upload failures, account-status changes and reports from users or service providers. Centralized alerting is not yet verified, so the designated Administrator must review available evidence and escalate suspicious patterns.

| Role | Incident responsibility |
|---|---|
| Reporter or school user | Stop the affected activity, preserve what was observed and notify the designated Administrator without sharing passwords or tokens |
| SIGNHEAR Administrator | Record the incident, restrict affected accounts, preserve audit evidence and coordinate technical containment |
| Development/technical owner | Investigate affected code and services, rotate exposed secrets when authorized, restore from verified backups and validate corrective changes |
| School/project owner | Approve high-impact containment, coordinate service-provider actions and decide when learning operations may safely resume |
| Authorized privacy or data-protection contact | Assess personal-data impact and determine applicable institutional or National Privacy Commission reporting obligations |

1. Record the time, affected function, account, and observed behavior without copying passwords or tokens.
2. Preserve relevant audit and operational evidence with restricted access.
3. Contain the incident by suspending affected accounts, disabling exposed integration keys, or isolating affected services as authorized.
4. Determine affected records, users, providers, and time range.
5. Rotate exposed secrets and restore only from a verified backup.
6. Validate authentication, authorization, data integrity, and primary learning functions after recovery.
7. Escalate possible personal-data breaches to the authorized school/privacy contact for legal assessment and notification.
8. Record corrective actions and reassess residual risk.

The incident record should include a unique reference, detection time, reporter, affected assets and accounts, observed indicators, containment actions, evidence locations, notifications, recovery validation, residual risk, responsible owners and closure approval. Store the record in an access-controlled location; the public application and ordinary learner accounts must not expose it.

## 6. Testing and Evidence

The local feature branch contains automated tests for authentication, authorization, input validation, token-purpose separation, audit-log redaction, security headers, cookie settings, material-upload validation, account blocking, invalid/expired tokens, progress-monitoring isolation, retakes, deadlines, complete 35-student progress roster, atomic database backup generation, SHA-256 cryptographic verification, automated backup schedule configuration and persistence, system High-severity event classification, path traversal prevention, tamper detection, and production restoration safeguards.

Latest authorized local result: **30 tests passed, 0 failed** (`python -m unittest discover -s tests -v`). Python compilation and `git diff --check` also passed. These results do not verify the production hosting environment, WAF, TLS termination, Supabase backup restoration, Cloudinary delivery controls, centralized alerting, full browser security, or penetration resistance.

## 7. Cybersecurity Checklist

| Area | Yes | Partly | No | Evidence and limitation |
|---|:---:|:---:|:---:|---|
| A. System and Assets |  | ✓ |  | Architecture and sensitive assets are identified; no approved complete asset register exists |
| B. Authentication and Access Control |  | ✓ |  | Password hashing, status checks, rate limits, role guards, login validation and token-purpose checks exist; MFA and complete authorization review remain |
| C. Session Management |  | ✓ |  | Expiration and protected refresh cookie exist; local-storage access token, no rotation/revocation, and no absolute/inactivity limits remain |
| D. Input Handling and Data Protection |  | ✓ |  | Schema validation, bound queries, upload checks and log redaction exist; complete content/data-flow review remains |
| E. Configuration, Components and Network |  | ✓ |  | Environment secrets, restricted CORS, API CSP baseline, other headers and ignore rules exist; frontend-host CSP, deployment TLS/WAF and dependency scans are unverified |
| F. Logging, Backup and Incident Response |  | ✓ |  | Audit events, redaction and local procedures exist; production backups, alerts and exercises are unverified |
| G. Standards and Compliance |  | ✓ |  | Controls are mapped to OWASP, six ISO/IEC 27002 themes, Philippine privacy principles and NSE 1–3 concepts; PCI DSS is documented as not applicable; no formal certification or legal assessment exists |
| H. Testing and Evidence | ✓* |  |  | 30 automated tests passed; deployed-environment and penetration testing remain outside the evidence scope |

\*The Yes rating for H applies only to the defined local automated-test scope. It is not evidence of penetration testing or production-environment verification.

## 8. Remaining Work and Approval

Highest-priority future work includes removing access tokens and private learner data from inappropriate persistent browser storage, implementing refresh-token rotation/revocation, adding staff MFA, verifying the frontend-host CSP and production HTTPS/CORS/header behavior, conducting dependency and secret scans, implementing protected production backup/restoration exercises, and completing formal privacy and endpoint-authorization reviews.

Residual risk must be reviewed and accepted by the authorized school/project owner before production use. A high rating should be reduced only when implementation and verification evidence supports the change.

## 9. Demonstration and Oral Defense

The approved demonstration should use local test accounts and non-production data. The presenter should demonstrate authentication, role separation, session behavior, validation, upload rejection, audit evidence, security headers, automated backup schedule configuration, vault storage, and automated tests while clearly identifying incomplete controls. The complete preparation checklist, presentation sequence, speaking script, evidence map, and likely professor questions are provided in [`cybersecurity-demo-guide.md`](cybersecurity-demo-guide.md).

## References

1. SIGNHEAR Project Team. (2026). *SIGNHEAR system documentation and source-code review*. Internal project documentation.
2. OWASP Foundation. (2025). [OWASP Top 10:2025](https://top10.owasp.org/2025/).
3. OWASP Foundation. [Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html).
4. OWASP Foundation. [Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html).
5. OWASP Foundation. [Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html).
6. OWASP Foundation. [Cross-Site Request Forgery Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html).
7. OWASP Foundation. [HTTP Headers Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html).
8. OWASP Foundation. [REST Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html).
9. OWASP Foundation. [File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html).
10. International Organization for Standardization. (2022). [ISO/IEC 27002:2022 overview](https://www.iso.org/standard/75652.html).
11. Republic of the Philippines. (2012). [Republic Act No. 10173: Data Privacy Act of 2012](https://lawphil.net/statutes/repacts/ra2012/ra_10173_2012.html).
12. National Privacy Commission. (2016). [Implementing Rules and Regulations of Republic Act No. 10173](https://privacy.gov.ph/implementing-rules-regulations-data-privacy-act-2012/).
13. OWASP Foundation. [Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html).

---

# APPENDIX A. SECURITY CODE LOCATIONS AND DEMONSTRATION EVIDENCE

All paths below are relative to the SIGNHEAR repository root unless otherwise indicated. Backend paths such as `routes/`, `services/`, `schemas/`, `utils/`, `models/`, and `tests/` refer to their corresponding locations inside `E-Learn/Backend/`.

All demonstrations must use test accounts and non-sensitive data. Passwords, token values, signing keys, database credentials, environment variables, and real learner information must never be displayed.

## A.1 Authentication and Login Validation

**Visible system location:** Grade 4 Student and Science Teacher login page (`/login`) and Administrator login page (`/admin/login`).

**Code locations:**
- `E-Learn/frontend/src/pages/auth/LoginPage.vue`
- `E-Learn/frontend/src/pages/admin/AdminLoginPage.vue`
- `E-Learn/frontend/src/stores/auth.ts`
- `E-Learn/Backend/routes/accounts_route.py`
- `E-Learn/Backend/schemas/accounts_schema.py`
- `E-Learn/Backend/services/auth_service.py`
- `E-Learn/Backend/auth/account_auth.py`
- `E-Learn/Backend/limiter.py`
- `E-Learn/Backend/scripts/demo_account_check.py`

**Demonstration:**
1. Open the Student or Science Teacher login page.
2. Submit an invalid test login and show that the system safely rejects the request.
3. Sign in using an authorized test account.
4. Show that the user is redirected to the dashboard corresponding to the account's actual role.
5. If demonstrating the Administrator login, use a separate authorized Administrator test account.

**Evidence and limitation:** Backend login-payload validation, bcrypt password verification, account-status checking, token-purpose separation, and SlowAPI IP-based rate limiting are active. The login endpoint enforces a limit of five requests per minute, with an emergency demonstration environment toggle (`ENABLE_RATE_LIMITING=false`) and automated unlock utility (`scripts/demo_account_check.py`) to prevent lockouts during oral defense demonstrations. Staff MFA and complete self-service recovery remain planned.

## A.2 Backend Role-Based Access Control

**Visible system location:** Administrator Dashboard and Audit Log page (`/admin/audit-log`).

**Code locations:**
- `E-Learn/Backend/utils/dependencies.py`
- `E-Learn/Backend/utils/admin_guard.py`
- `E-Learn/Backend/routes/admin_route.py`
- `E-Learn/frontend/src/router/index.ts`

**Demonstration:**
1. Sign in using a Grade 4 Student or Science Teacher test account.
2. Attempt to navigate directly to `/admin/audit-log` or invoke `/admin/audit-logs`. Show that the route is blocked with an HTTP 403 Forbidden rejection and recorded in audit logs.
3. Sign in using an authorized Administrator test account and open `/admin/audit-log`. Show that access is granted.

**Evidence and limitation:** `get_current_user` decodes and validates JWT claims, and `require_admin` strictly enforces administrative role checks. Menu hiding on the frontend is treated solely as a UI affordance, not a primary security boundary.

## A.3 Session Management and Logout

**Visible system location:** Logout controls across role navigation bars and browser Developer Tools under Application -> Storage.

**Code locations:**
- `E-Learn/frontend/src/stores/auth.ts`
- `E-Learn/Backend/routes/refresh_token.py`
- `E-Learn/Backend/auth/account_auth.py`
- `E-Learn/Backend/core/config.py`

**Demonstration:**
1. Sign in with a test account and inspect browser storage.
2. Note the short-lived access token in local storage and the `HttpOnly` refresh token cookie.
3. Click Logout and verify that stored auth state is cleared and authenticated API calls are rejected.

**Evidence and limitation:** Tokens have bounded lifetimes and purpose separation. Storing access tokens in browser local storage remains a documented risk on shared computers; server-side token revocation and absolute session limits remain proposed.

## A.4 Cryptographic Controls, Automated Backup Cadence, and Storage Vault

**Visible system location:** Administrator Console -> Audit Log -> **Database Backup & Restore** tab (`/admin/audit-log`).

**Code locations:**
- `E-Learn/Backend/services/backup_service.py`
- `E-Learn/Backend/services/restore_service.py`
- `E-Learn/Backend/routes/backup_route.py`
- `E-Learn/Backend/schemas/backup_schema.py`
- `E-Learn/Backend/tests/test_backup_restore.py`
- `E-Learn/frontend/src/pages/admin/AuditLogPage.vue`
- `E-Learn/frontend/src/services/adminService.ts`

**Demonstration:**
1. Navigate to the **Database Backup & Restore** tab in the Admin Console.
2. Inspect the **Automated Backup Cadence & Storage Vault** section:
   - Cadence options: Change between **Every 2 Weeks (Recommended)** and **Every 1 Month** (or Weekly / Daily).
   - Verify next scheduled run calculation and countdown.
   - Inspect the Storage Vault path: `./backups/` (`<project_root>/backups/`) and manifest index `backups/manifest.json`.
3. Click **Create Database Backup** to trigger an immediate snapshot.
4. Click **Verify** on the generated backup row to demonstrate cryptographic SHA-256 integrity verification.
5. Click **Dry-Run** to demonstrate safe isolated sandbox table restoration without modifying live database state.
6. Click **Restore**, review pre-restoration warnings, and demonstrate guarded live restoration with typed `RESTORE` confirmation.

**Physical Storage Location and Bare-Metal Recovery:**
- All backup snapshots are saved to the server local vault directory `./backups/`.
- File naming format: `backup_YYYYMMDD_HHMMSS_<token>.db` (SQLite) or `.json` (PostgreSQL).
- In the event of bare-metal recovery or an offline server crash, the administrator can retrieve the verified `.db` file directly from `./backups/` and copy it to `local.db`.

**Evidence and limitation:** Online SQLite backups use consistent SQLite online backup APIs, SHA-256 hashing, path traversal prevention, and pre-restoration safety snapshots. Automated backups run on the configured schedule (Every 2 Weeks / Every 1 Month). Production multi-tenant PostgreSQL restrictions block accidental overwrites on remote cloud staging.

## A.5 Audit Logging, Redaction, and System High-Severity Classification

**Visible system location:** Administrator Console -> Audit Log -> **Security Events & Audit Logs** tab.

**Code locations:**
- `E-Learn/Backend/services/audit_service.py`
- `E-Learn/Backend/models/audit_log.py`
- `E-Learn/Backend/routes/admin_route.py`
- `E-Learn/Backend/tests/test_security_controls.py`
- `E-Learn/frontend/src/pages/admin/AuditLogPage.vue`

**Demonstration:**
1. Open the Audit Log page as an Administrator.
2. Note that security-critical events (such as `Backup requested`, `Backup completed`, `Backup verified`, `Access denied`, `Login failed`) are displayed with high-visibility **HIGH** severity badges.
3. Click on any log row to inspect bounded, sanitized metadata (IP address, user agent, action timestamp).
4. Demonstrate that sensitive data (passwords, tokens, database secrets) are strictly redacted.

**System vs. Paper Severity Distinction:**
- **On Paper (Section 2.2 Initial Risk Register):** Threats R1 (Broken Access Control), R4 (Cryptographic Failures), R8 (Insecure Design), and R12 (Upload Validation) are categorized with priority **Medium** based on Grade 4 classroom threat models.
- **In System (Audit Log & SIEM):** All associated operational actions (`backup_*`, `restore_*`, `access_denied`, `login_failed`) are categorized with **HIGH** severity (or **CRITICAL** for failures) to ensure immediate administrative attention.

## A.6 Security HTTP Headers and Restricted CORS

**Visible system location:** Browser Developer Tools -> Network tab -> Response Headers.

**Code locations:**
- `E-Learn/Backend/main.py`
- `E-Learn/Backend/core/config.py`
- `E-Learn/Backend/tests/test_security_controls.py`

**Demonstration:**
1. Send an HTTP GET request to `/health` or any API endpoint.
2. Inspect the HTTP response headers in Developer Tools:
   - `Content-Security-Policy: default-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'`
   - `X-Content-Type-Options: nosniff`
   - `X-Frame-Options: DENY`
   - `Referrer-Policy: strict-origin-when-cross-origin`
   - `Permissions-Policy: geolocation=(), camera=(), microphone=()`

**Evidence and limitation:** Security headers mitigate clickjacking, MIME-sniffing, and cross-site framing. Production TLS enforcement is configured via reverse proxy.

## A.7 Input Validation and File Upload Security Controls

**Visible system location:** Science Teacher lesson material upload modal.

**Code locations:**
- `E-Learn/Backend/services/teacher_module_service.py`
- `E-Learn/Backend/schemas/`
- `E-Learn/Backend/tests/test_security_controls.py`

**Demonstration:**
1. Attempt to upload an unauthorized file type (e.g., an executable `.exe` or mismatched magic-byte file).
2. Show that the backend immediately rejects the payload with HTTP 400 Bad Request.
3. Upload an authorized presentation or document file within allowed size limits.

**Evidence and limitation:** Whitelisted extension checks, declared MIME type validation, file header magic-byte signatures, and size limits (15 MB standard, 50 MB for presentations) prevent dangerous script upload. Virus scanning and quarantine pipelines remain planned for cloud deployment.

## A.8 Progress Monitoring and Assessment Isolation

**Visible system location:** Grade 4 Science Teacher Dashboard and Student Activities page.

**Code locations:**
- `E-Learn/Backend/services/student_content_service.py`
- `E-Learn/Backend/services/teacher_dashboard_service.py`
- `E-Learn/Backend/tests/test_progress_monitoring.py`

**Demonstration:**
1. Sign in as a Science Teacher and open Grade 4 section monitoring.
2. Show that student progress percentages cover the complete 0% to 100% spectrum and all 35 enrolled learners are reported.
3. Demonstrate deadline enforcement: unsubmitted activities past deadline are marked missing, and late submissions are flagged late.
4. Sign in as Student A and Student B in separate browsers: show that activity answers and quiz retakes are strictly isolated per student.

**Evidence and limitation:** Independent progress tracking prevents duplicate score overrides and replay attacks across learners.

## A.9 Automated Test Suite Execution and Verification Evidence

**Visible system location:** Terminal command-line test runner.

**Code location:**
- `E-Learn/Backend/tests/`

**Demonstration:**
1. Execute the comprehensive unit test suite:
   ```bash
   python -m unittest discover -s tests -v
   ```
2. Verify that all **30 automated tests pass with 0 failures** in approximately 13–16 seconds.

**Test Suite Coverage Summary:**
- **`test_backup_restore.py` (9 tests):** Role-based backup protection, path traversal blocking, atomic backup lifecycle, SHA-256 verification, tamper rejection, isolated dry-run sandbox recovery, production PostgreSQL safeguards, automated schedule cadence persistence, and system High-severity event classification.
- **`test_security_controls.py` (14 tests):** Password complexity, token-purpose separation, access vs. refresh token substitution blocking, SlowAPI login rate limiting, audit log secret redaction, role guards, security headers, cookie flags, and upload signature verification.
- **`test_progress_monitoring.py` (7 tests):** 35-student roster completeness, progress percentage bounds (0–100%), deadline enforcement, retake isolation, student activity draft independence, and teacher section scoping.
