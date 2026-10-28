# Backup and Restore Plan

## Scope

Back up the production PostgreSQL database, uploaded learning materials, generated media that cannot be recreated, profile/media-storage references and assets, audit logs, migration files, and a securely stored list of required configuration keys. Never place secret values in ordinary project backups or source control.

Local `local.db` files are development artifacts. They must not be treated as the production backup and must not contain copied production learner data without authorization.

## Recommended schedule

- Database: daily encrypted backup; retain daily copies for 14 days and monthly copies for the approved academic retention period.
- Uploaded media: daily incremental backup and weekly integrity check.
- Before migrations or major releases: on-demand database and media snapshot.
- Source code: protected Git hosting on feature/release branches; secrets remain separate.

The system owner must approve actual retention periods based on school requirements and privacy advice.

## Storage and protection

- Keep at least one backup in a separate account or failure domain from production.
- Encrypt backups in transit and at rest.
- Restrict backup access to named maintainers; enable MFA on storage accounts.
- Record backup job success/failure without logging secrets.
- Protect encryption keys separately from the backups they protect.

## Restore procedure

1. Declare the restore reason, recovery point, responsible person, and target environment.
2. Isolate the target and confirm it cannot overwrite a healthy production system accidentally.
3. Verify backup integrity, timestamp, encryption and authorization.
4. Restore PostgreSQL into a clean database and apply only required migrations.
5. Restore media/uploads and confirm object paths and permissions.
6. load configuration from the approved secret store and rotate credentials if compromise is suspected.
7. Validate login, roles, class membership, materials, assessments, progress, audit logs and media access.
8. Record the recovery time, data loss window, failures and corrective actions.

## Testing and responsibility

The designated system operator owns backup monitoring. Conduct a non-production restore test at least once per academic term and before final deployment. A backup is not considered reliable until restoration has been demonstrated and documented.
