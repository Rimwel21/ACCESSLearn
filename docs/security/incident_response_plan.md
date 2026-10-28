# Incident Response Plan

## Roles

Assign one incident coordinator, one technical responder, and one school/privacy contact before deployment. For a small capstone team, one person may hold multiple roles, but every decision and action must be recorded.

## Process

### 1. Identification

Confirm the report, affected accounts/data/functions, approximate start time, current indicators, and reporter. Preserve relevant audit, application, hosting and database logs. Do not copy tokens, passwords or OTPs into the incident record.

### 2. Containment

Disable or block affected accounts, revoke/rotate exposed credentials where possible, restrict network access, stop malicious uploads, and preserve evidence. Prefer reversible containment over deleting data.

### 3. Investigation

Build a timeline from audit and infrastructure records. Identify the entry point, affected data, attacker actions, authorization failures, persistence and scope. Work from evidence and record uncertainty.

### 4. Eradication

Remove malicious files or accounts, patch the root cause, rotate secrets, correct unsafe configuration, and validate database integrity. Do not return to service until the cause is addressed or an explicit risk decision is recorded.

### 5. Recovery

Restore clean data/media if necessary, deploy reviewed fixes, test critical student/teacher/admin flows, monitor closely, and return services in stages.

### 6. Notification

Notify the project adviser, school authority, affected service providers, and privacy/legal contact as appropriate. They determine whether affected individuals or the National Privacy Commission must be notified. Do not make unsupported claims about scope.

### 7. Documentation

Record who did what and when, evidence references, affected assets/data, decisions, notifications, recovery validation and outstanding risk. Restrict incident records because they may contain sensitive information.

### 8. Lessons learned

Within one week, review control gaps, response delays, logging quality and communications. Assign owners and deadlines for corrective actions and update the threat model, tests and this plan.

## Immediate reporting triggers

- Suspected exposure of learner information, credentials, tokens or backups.
- Administrator-account compromise or unexplained privilege changes.
- Malicious uploads, database modification, repeated authorization failures, or loss of audit logs.
- Extended outage or failed restore affecting required learning access.
