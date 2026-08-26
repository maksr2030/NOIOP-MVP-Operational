# NOIOP Internal Acquisition Gate Register v1.0

Classification: SELLER INTERNAL - DO NOT PROVIDE AS A PUBLIC BUYER DOCUMENT

## Objective

This register controls the transition from operational MVP evidence to acquisition-ready technical diligence. It is intentionally stricter than the buyer-visible summary and records what must be closed before the seller represents NOIOP as technically acquisition-ready.

## Gate register

| Gate | Requirement | Current status | Required closure evidence |
|---|---|---|---|
| T-01 | Public backend reachable over HTTPS | PASS | Live endpoint response |
| T-02 | Database initialization and readiness | PASS | /health database_ready=true |
| T-03 | Persistent opportunity creation | PASS | Persistent records=1 and retained opportunity identifier |
| T-04 | Browser session reload persistence | PASS | Same opportunity identifier after interface reopen |
| T-05 | Full Render redeploy persistence | OPEN | Same opportunity retrievable after fresh deployment |
| T-06 | Server assessment on persisted opportunity | OPEN | Score, decision, evidence hash, human approval flag |
| T-07 | Human decision record | OPEN | Actor, decision, rationale, assessment hash, timestamp |
| T-08 | Value realization event | OPEN | Expected value, realized value, ratio, state, hash |
| T-09 | Audit chain completeness | OPEN | Creation, assessment, decision, value event hashes |
| T-10 | Live portfolio generation from persisted records | OPEN | Ranked live portfolio response |
| T-11 | Health/runtime semantics consistent with persistent storage | OPEN | Health output consistent with mounted runtime architecture |
| T-12 | Automated lifecycle tests preserved | PASS | tests/test_fullstack_api.py and CI evidence |
| T-13 | Buyer-visible disclosure boundary documented | PASS | BUYER_VISIBLE_TECHNICAL_SUMMARY_v1.0.md |
| T-14 | Technical acquisition closure record created | PASS | TECHNICAL_ACQUISITION_CLOSURE_v1.0.md |
| T-15 | Credentials and secrets excluded from diligence package | REQUIRED CONTROL | Manual package review before release |
| T-16 | IP chain-of-title linked to transaction package | OPEN LEGAL | Separate signed ownership and chain-of-title record |
| T-17 | Source inventory and dependency register frozen | OPEN | Final source manifest and dependency/SBOM record |
| T-18 | Release hash manifest frozen | OPEN | Final acquisition release commit plus artifact hashes |

## Release rule

NOIOP must not be labelled FINAL TECHNICAL ACQUISITION READY until T-05 through T-11, T-16, T-17, and T-18 are closed or explicitly accepted as transaction conditions by the seller.

## Buyer access rule

Preliminary buyer review receives only buyer-visible evidence. Source-level confidential diligence is released in stages and only after the seller approves the disclosure scope. Secrets, credentials, infrastructure tokens, private negotiation parameters, and seller-only strategy are never part of a general buyer package.

## Immediate next live test sequence

1. Perform a fresh Render deployment without creating another opportunity first.
2. Reopen the operational interface and verify that Persistent records remains 1.
3. Retrieve the retained opportunity through the API.
4. Run server assessment on that opportunity.
5. Record one human decision with rationale.
6. Record one value-realization event.
7. Retrieve and verify the audit chain.
8. Generate the live portfolio.
9. Capture the resulting identifiers, hashes, timestamps, and endpoint responses into the acquisition evidence record.

## Current internal conclusion

The platform has crossed the minimum threshold from static demonstration to operational full-stack evidence. It is now in acquisition technical closure, not yet final technical closure.
