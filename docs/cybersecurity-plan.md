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

### 2.1 Assessment method

The assessment uses the OWASP Top 10:2025 as an application-security risk framework. The categories identify credible threat classes and do not mean every vulnerability has been demonstrated in SIGNHEAR.

| Rating | Likelihood | Impact |
|---|---|---|
| High | A normal or public workflow gives a direct opportunity for misuse when controls are absent | Restricted-data exposure, privileged takeover, widespread record alteration, or substantial interruption |
| Medium | Misuse requires an additional condition such as compromised credentials, a malicious file, or a compromised dependency | Limited exposure, disruption, or alteration requiring recovery |
| Low | Several uncommon conditions are required | Minor and limited disruption or exposure |

Priority matrix:

| Likelihood \ Impact | Low | Medium | High |
|---|---:|---:|---:|
| Low | Low | Low | Medium |
| Medium | Low | Medium | High |
| High | Medium | High | High |

> A High priority does not mean SIGNHEAR is automatically easy to breach. It means the combination of likelihood and potential impact requires urgent treatment. Ratings may be reduced only after controls are implemented, tested, and reassessed.

### 2.2 Initial risk register

| ID | OWASP mapping | Scenario | Likelihood | Impact | Initial priority |
|---|---|---|---|---|---|
| R1 | A01 Broken Access Control | A learner requests another learner's record, or a teacher requests an unrelated class | Medium | Medium | Medium |
| R2 | A07 Authentication Failures | Compromised teacher or administrator credentials enable unauthorized actions | Medium | High | High |
| R3 | A02 Security Misconfiguration | Unsafe CORS, debugging, public media, or excessive database access exposes information | Medium | High | High |
| R4 | A04 Cryptographic Failures | Exposed signing keys or unprotected backups compromise accounts or records | Medium | Medium | Medium |
| R5 | A05 Injection | Malicious input reaches a database operation or unsafe content-rendering path | Medium | High | High |
| R6 | A03 Software Supply Chain Failures | A compromised package, build action, or dependency reaches production | Medium | Medium | Medium |
| R7 | A08 Software or Data Integrity Failures | Unauthorized model or dataset replacement changes recognition behavior | Medium | Medium | Medium |
| R8 | A06 Insecure Design | Replayed or concurrent requests create duplicate attempts or repeated retake use | Medium | Medium | Medium |
| R9 | A07 Authentication Failures / A02 Security Misconfiguration | A second learner sees private information from a prior shared-browser session | Medium | Medium | Medium |
| R10 | A09 Security Logging and Alerting Failures | Abuse, mass access, or privilege changes are not detected | Medium | High | High |
| R11 | A10 Mishandling of Exceptional Conditions | Exhaustion or failure interrupts recognition, uploads, or database operations | Medium | High | High |
| R12 | A06 Insecure Design / A08 Integrity Failures / A10 Exceptional Conditions | A malicious uploaded file reaches a user or processing component | Medium | Medium | Medium |

This register represents inherent, design-based risk. A future treatment register should record the control owner, due date, verification evidence, residual likelihood, residual impact, and formal risk acceptance.

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
| C11 Backup and recovery | Manual local SQLite backup/restore procedure | Partly implemented | Authorized encrypted production schedule, RPO/RTO, restoration exercise |
| C12 Monitoring and alerts | Authentication/authorization audit events and local secret-redaction controls | Partly implemented | Central alerts, protected retention, WAF/server/backup monitoring |

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

The local feature branch contains automated tests for authentication, authorization, input validation, token-purpose separation, audit-log redaction, security headers, cookie settings, material-upload validation, account blocking, invalid/expired tokens, progress-monitoring isolation, retakes, deadlines, and a complete 35-student progress roster.

Latest authorized local result: **20 tests passed, 0 failed**. Python compilation and `git diff --check` also passed. These results do not verify the production hosting environment, WAF, TLS termination, Supabase backup restoration, Cloudinary delivery controls, centralized alerting, full browser security, or penetration resistance.

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
| H. Testing and Evidence | ✓* |  |  | 20 automated tests passed; deployed-environment and penetration testing remain outside the evidence scope |

\*The Yes rating for H applies only to the defined local automated-test scope. It is not evidence of penetration testing or production-environment verification.

## 8. Remaining Work and Approval

Highest-priority future work includes removing access tokens and private learner data from inappropriate persistent browser storage, implementing refresh-token rotation/revocation, adding staff MFA, verifying the frontend-host CSP and production HTTPS/CORS/header behavior, conducting dependency and secret scans, implementing protected production backup/restoration exercises, and completing formal privacy and endpoint-authorization reviews.

Residual risk must be reviewed and accepted by the authorized school/project owner before production use. A high rating should be reduced only when implementation and verification evidence supports the change.

## 9. Demonstration and Oral Defense

The approved demonstration should use local test accounts and non-production data. The presenter should demonstrate authentication, role separation, session behavior, validation, upload rejection, audit evidence, security headers, and automated tests while clearly identifying incomplete controls. The complete preparation checklist, presentation sequence, speaking script, evidence map, and likely professor questions are provided in [`cybersecurity-demo-guide.md`](cybersecurity-demo-guide.md).

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
