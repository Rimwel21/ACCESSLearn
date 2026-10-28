# Privacy and Compliance Considerations

This document treats the Philippine Data Privacy Act of 2012 and National Privacy Commission guidance as design considerations. It does not state or imply that SIGNHEAR has been audited, certified, or formally declared compliant.

## Purpose and necessity

SIGNHEAR processes account, profile, accessibility, class, learning, assessment, progress and audit information to provide and administer accessible Grade 4 science learning. Before deployment, the school/system operator must document the lawful and authorized purpose for each collected field and remove fields that are not necessary for that purpose.

## Data minimization

- Collect only information required for account administration, classroom assignment, accessibility, learning delivery, progress monitoring, recovery and security.
- Avoid placing real learner data in development databases, screenshots, test fixtures or demonstrations.
- Review whether address, guardian, contact, LRN, IP and user-agent fields are required and how long each must be retained.

## Access and confidentiality

- Students access their own learning/profile data.
- Teachers access records within assigned classes/sections and functions required for instruction.
- Administrators receive management and audit access only for authorized duties.
- Hosting, database, mail, media and backup accounts must use least privilege and named maintainers.

## Notice, consent and authorization

Before real use, provide a clear privacy notice identifying the operator/controller, purposes, data categories, recipients/processors, retention, security measures, data-subject contact and complaint process. Because learners are minors, obtain and record the school/parent/guardian authorization required by the responsible institution. Consent should not be described as the legal basis without qualified review.

## Retention and deletion

The responsible school/operator must approve a written schedule for accounts, learner records, assessment history, uploaded media, audit logs, OTPs and backups. Expired OTPs should be removed promptly. When retention ends, securely delete or anonymize database, media, browser-cache and backup copies, subject to authorized academic or legal needs.

## Security safeguards

Use production HTTPS, protected secrets, role and ownership checks, secure cookies, bounded uploads, audit logging, encrypted/tested backups, vulnerability management, account review, incident response, and staff confidentiality practices. Technical controls do not replace organizational and physical safeguards.

## Data-subject and breach handling

Establish a verified process for access, correction, deletion/objection requests and complaints. Requests involving minors must be validated through the responsible school/guardian process. Suspected breaches follow the incident-response plan; the designated privacy/legal contact determines notification obligations and deadlines.

## Accountability

Before deployment, name the system operator, data protection/privacy contact, technical maintainer, backup owner and incident coordinator. Record third-party processors such as database, hosting, mail and media providers, and review their security/privacy terms.
