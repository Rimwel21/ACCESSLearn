# SIGNHEAR Cybersecurity Demonstration and Oral-Defense Guide

Use this guide with the corrected [`cybersecurity-plan.md`](cybersecurity-plan.md). The demonstration is designed for approximately 10 to 15 minutes and must use local test accounts and non-production data.

## 1. What the demonstration must prove

The goal is not to claim that SIGNHEAR is impossible to breach. The goal is to prove that the team:

1. identified important assets and credible risks;
2. implemented selected controls in the existing architecture;
3. tested those controls with authorized local evidence;
4. understands the controls' limitations; and
5. has a realistic plan for remaining work.

Recommended opening statement:

> SIGNHEAR uses defense in depth. The frontend improves the user experience, but the FastAPI backend remains responsible for authentication, authorization, validation, and protected data access. Our implementation is partial, so we will show both the controls that work and the controls that remain planned.

## 2. Preparation before meeting the professor

### Accounts and data

- Prepare one safe local Student account, one Science Teacher account, and one Administrator account.
- Use invented names and non-production records.
- Prepare one small valid PDF or PPTX and one harmless invalid file such as a text file renamed for the upload-rejection demonstration.
- Never display a real password, JWT, refresh cookie value, `.env` file, API key, database connection string, learner LRN, guardian contact, or production record.
- Close unrelated browser tabs, notifications, terminals, and files before presenting.

### Start the local backend

Open PowerShell in the repository root. Load the existing local environment without printing it, then start FastAPI:

```powershell
$configFile = 'E-Learn\Backend\.env'
Get-Content -LiteralPath $configFile | ForEach-Object {
  $entry = $_.Trim()
  if ($entry -and -not $entry.StartsWith('#') -and $entry.Contains('=')) {
    $parts = $entry.Split('=', 2)
    [Environment]::SetEnvironmentVariable(
      $parts[0].Trim(),
      $parts[1].Trim().Trim('"').Trim("'"),
      'Process'
    )
  }
}
python -m uvicorn main:app --reload
```

Do not open or project the `.env` file.

### Start the frontend

Open a second PowerShell window:

```powershell
Set-Location E-Learn\frontend
npm.cmd run dev
```

Use the URL printed by Vite, normally `http://localhost:5173`.

### Prepare the test command

Keep a third terminal ready in the repository root. Load the environment using the same non-printing procedure, then run:

```powershell
python -m unittest discover -s tests -v
```

Expected local evidence at the time this guide was prepared: **20 tests passed, 0 failed**.

## 3. Recommended 10–15 minute demonstration

### Step 1 — Scope and architecture (1 minute)

Show the system overview and architecture in the cybersecurity plan.

Say:

> SIGNHEAR protects learner identities, accessibility information, educational records, scores, learning materials, accounts, audit logs, and recognition assets. A request travels from the Vue frontend to FastAPI, where authentication, account status, role, ownership, and input are checked before SQLAlchemy accesses the database.

Be explicit that HTTPS, a WAF, production backups, and some provider controls are deployment-dependent or planned, not proven by the local repository.

### Step 2 — Login validation and authentication (2 minutes)

1. Open the SIGNHEAR login page.
2. Submit one deliberately invalid local login.
3. Show that the response does not reveal a password or token.
4. Log in using the safe Student account.

Explain:

> Login requests are rate-limited. The backend trims identifiers, rejects control characters, requires exactly one username or email, verifies the bcrypt password hash, checks account status, and records selected login successes and failures.

Do not deliberately trigger the full rate limit during the live presentation; one failed test login is enough.

### Step 3 — Role-based access control (2 minutes)

1. While authenticated as a Student, attempt to navigate to `/admin/audit-log`.
2. Show the Forbidden page or role redirect.
3. Explain that the frontend route guard is only the visible layer.
4. Show the backend guard code or the passing cross-role test as the real security evidence.

Say:

> Hiding an administrator page is not our security boundary. Backend dependencies verify the signed access token, current account status, and required role. Student, Teacher, and Administrator operations also apply ownership or class-scope checks where appropriate.

### Step 4 — Session protection and honest limitation (1.5 minutes)

Open browser developer tools only if you can avoid projecting credential values.

Demonstrate:

- the refresh cookie is marked HttpOnly;
- production configuration requires a Secure cookie;
- logout removes the refresh cookie and selected frontend account state; and
- access and refresh tokens now have different purposes and cannot be substituted.

Say:

> Token-purpose separation prevents a refresh token from being accepted as an API bearer token and prevents an access token from being used at the refresh endpoint. However, the access token is still stored in local storage, and server-side refresh-token rotation and revocation remain future work.

Never expand or read the actual token value to the audience.

### Step 5 — Input and file-upload validation (1.5 minutes)

1. Sign in as the safe Science Teacher.
2. Open Learning Materials.
3. Select the harmless invalid upload file.
4. Show the rejection message.
5. If time permits, select a small valid PDF/PPTX and show that the ordinary workflow remains functional.

Explain:

> The backend checks allowed extensions, declared MIME type, content signature, and configured size, and selected files receive server-controlled names. Quarantine and malware scanning are not yet implemented, so upload protection is rated Partly rather than Yes.

Do not use malware, exploit documents, or real confidential files.

### Step 6 — Audit evidence (1.5 minutes)

1. Log out and sign in as the safe Administrator.
2. Open **Audit Log** from the administrator sidebar.
3. Point out the failed local login and any authorization-denied event generated during the demo.
4. Do not expose sensitive learner fields or full network metadata.

Explain:

> SIGNHEAR records selected authentication, authorization, and administrative events. The feature branch also redacts structured password, token, secret, OTP, cookie, authorization, and API-key fields and limits request metadata lengths. Central alerting and production retention remain planned.

### Step 7 — HTTP response protections (1 minute)

In the browser Network panel, select an API response and point only to header names:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: no-referrer`
- `Permissions-Policy`
- `Content-Security-Policy` on backend API responses
- `Cache-Control: no-store` on selected authentication/private API paths
- HSTS when production HTTPS configuration enables it

Say:

> These headers reduce content-type confusion, framing, referrer leakage, unnecessary browser capabilities, and caching of selected sensitive responses. The backend API now has a restrictive CSP baseline. A separate frontend-compatible CSP and complete production-host header verification remain unfinished.

### Step 8 — Automated testing evidence (2 minutes)

Run the prepared test command and show the final result only.

Summarize the tested areas:

- password policy;
- login success/failure auditing;
- malformed login identifiers;
- access/refresh token substitution rejection;
- invalid and expired JWT rejection;
- blocked-account token rejection;
- Student/Teacher/Administrator role separation;
- secure-cookie production behavior;
- security headers and unauthenticated-route behavior;
- upload extension, MIME, signature, and size validation;
- audit secret redaction;
- student draft isolation, progress monitoring, retakes, and deadline behavior.

Say:

> All 20 authorized local tests passed. This evidence covers the defined local scope, but it does not prove production TLS, WAF behavior, provider security, backup restoration, or complete penetration resistance.

### Step 9 — Risk ratings and conclusion (1 minute)

Show the risk register and checklist.

Say:

> High does not mean the system is automatically easy to breach. Likelihood describes how easily a scenario may occur, impact describes the possible damage, and priority combines both. We keep a High priority where the potential harm is serious until implementation and testing justify a lower residual rating.

Close with:

> SIGNHEAR currently demonstrates partial alignment across the cybersecurity checklist. We implemented selected high-value controls without redesigning the learning system, tested them locally, documented limitations, and identified the next controls required before production.

## 4. Evidence map for code questions

| Professor asks about | Evidence to open |
|---|---|
| Password hashing and token creation | `auth/account_auth.py` |
| Access-token authentication and account-status checks | `utils/dependencies.py` |
| Refresh validation and logout cookie deletion | `routes/refresh_token.py` |
| Login schema validation | `schemas/accounts_schema.py` |
| Login logic and refresh-cookie flags | `services/auth_service.py` |
| Administrator/Teacher/Student guards | `utils/admin_guard.py`, `utils/teacher_guard.py`, `utils/student_guard.py` |
| CORS, error handling and security headers | `main.py` |
| Audit secret redaction | `services/audit_service.py` |
| Upload checks and generated filenames | `services/teacher_module_service.py` |
| Service-worker caching boundaries | `E-Learn/frontend/public/sw.js` |
| Current access-token storage gap | `E-Learn/frontend/src/stores/auth.ts` |
| Offline API caching gap | `E-Learn/frontend/src/lib/api.ts` |
| Automated evidence | `tests/test_security_controls.py`, `tests/test_progress_monitoring.py` |

## 5. Likely professor questions and suggested answers

### “Is SIGNHEAR already secure?”

> It has meaningful controls, but we describe it as partially implemented rather than fully secure. Local authentication, authorization, validation, upload, logging, header, and test evidence exists. Production infrastructure, complete session revocation, CSP, malware scanning, automated backups, MFA, and formal privacy review remain incomplete or unverified.

### “Why is a risk marked High?”

> High priority means the likelihood-impact combination needs urgent treatment. It does not automatically mean exploitation is easy. For example, compromised administrator credentials may have Medium likelihood but High impact, producing a High treatment priority.

### “Why do you not rely on the frontend role check?”

> Browser code can be modified by a user. The frontend guard improves navigation, but FastAPI verifies the token, account status, role, ownership, and scope before protected data is returned or changed.

### “How do you prevent SQL injection?”

> Input is validated by Pydantic schemas, and database access uses SQLAlchemy bound expressions instead of concatenating untrusted input into raw SQL. This reduces injection risk, although endpoint review and testing must continue.

### “Are passwords encrypted?”

> Passwords are not reversibly encrypted. They are salted and hashed using bcrypt through Passlib. OWASP prefers Argon2id for new systems, so migration evaluation is listed as future work.

### “Does logout invalidate every stolen token?”

> Not yet. Logout deletes the browser refresh cookie and clears selected frontend state, and blocked accounts are rejected on protected requests. Full refresh-token rotation and server-side revocation remain planned, so Session Management is rated Partly.

### “Why is localStorage a concern?”

> JavaScript in the same origin can read local storage, so an XSS flaw could expose the access token. The current implementation is documented honestly as a gap. A safer cookie or backend-for-frontend design requires coordinated architecture and CSRF protection.

### “Do you have antivirus scanning for uploads?”

> No. Current controls validate extension, MIME, content signature and size and use controlled filenames. Quarantine and malware scanning are planned, which is why upload protection is Partial.

### “Are production backups working?”

> The repository documents and can test a local SQLite backup procedure. Production PostgreSQL/Supabase scheduling, encryption and restoration are not verified and must be owned and evidenced by the authorized deployment administrator.

### “Do you comply fully with the Data Privacy Act or ISO 27002?”

> We demonstrate partial alignment, not certification or legal compliance. Formal privacy, legal, organizational and production-control assessments are still required.

### “What happens to camera images?”

> The policy is to process camera frames only for recognition and not retain them by default. We present this as a requirement until every deployed recognition, logging and provider path has been verified.

## 6. What not to claim or demonstrate

- Do not say every control is implemented or every checklist category is Yes.
- Do not call WAF, frontend-host CSP, staff MFA, malware scanning, refresh rotation, automated production backup, or production alerting implemented without separate evidence.
- Do not show `.env`, JWT values, cookies, real learner data, real passwords, API keys, database URLs, or guardian information.
- Do not run destructive attacks or upload actual malicious content.
- Do not change High risks to Medium merely to make the system appear safer.
- Do not use the unlinked `SystemMonitoringPage.vue` as cybersecurity evidence; it is currently not registered in the active administrator router.
- Do not describe the 20 tests as a penetration test or proof that no vulnerabilities exist.

## 7. Final presentation checklist

- [ ] Local Student, Teacher and Administrator test accounts work.
- [ ] Demo records contain no real personal information.
- [ ] Backend and frontend start before presentation.
- [ ] Valid and invalid sample upload files are ready.
- [ ] Browser developer tools are positioned without exposing secret values.
- [ ] Audit Log is reachable from the administrator sidebar.
- [ ] Test terminal is prepared and expected output is understood.
- [ ] The corrected paper is open at the architecture, risk register, status table and checklist.
- [ ] The team can explain at least three implemented controls and three remaining limitations.
- [ ] A fallback recording or screenshots contain only sanitized test data.
