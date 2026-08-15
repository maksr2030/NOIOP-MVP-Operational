# NOIOP Pilot Data & Security Boundary v1.0

## Permitted Data Classes

The baseline pilot permits synthetic data, anonymized or de-identified data where appropriate, sandbox data, public data with lawful use rights, and institutional data expressly approved for the pilot.

## Restricted by Default

Production credentials, unrestricted personal data, secrets, private keys, authentication tokens, regulated data without approved controls, confidential third-party material without authorization, and production-system write access are restricted by default.

## Minimum Pilot Controls

1. Least-privilege access.
2. Named pilot users and attributable actions.
3. Separation between public demonstration assets and confidential pilot evidence.
4. No credentials committed to source control.
5. Approved retention and deletion rules for institutional pilot data.
6. Incident logging and escalation.
7. Evidence integrity controls for acceptance artifacts.
8. Explicit authorization before any production integration.

## Disclosure Classification

PUBLIC_SAFE: suitable for the public repository.
PILOT_CONTROLLED: pilot operational evidence with controlled access.
CONFIDENTIAL_DILIGENCE: buyer or institutional diligence material.
TRADE_SECRET: protected implementation knowledge requiring the highest disclosure control.

## Security Decision Rule

The existence of an MVP or successful pilot does not constitute a production security certification. Production deployment requires a separate security architecture, threat assessment, privacy assessment where applicable, penetration testing strategy, operational monitoring design and institutional approval.