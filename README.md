# NOIOP-MVP-Operational

National Opportunity Intelligence & Orchestration Platform

NOIOP is a governed opportunity-intelligence and institutional decision-orchestration platform designed to connect opportunity discovery, evidence, prioritization, simulation, human authority, execution controls, and value-realization tracking within one traceable operating lifecycle.

This public repository contains a controlled operational MVP prepared for technical demonstration, validation, and acquisition due diligence. It intentionally excludes confidential trade secrets, transaction valuation materials, negotiation parameters, private data-room documents, production secrets, and sensitive intellectual-property disclosures.

## Public operational scope

The current public release demonstrates:

- evidence-grounded opportunity assessment
- readiness and evidence gates
- explicit abstention behavior
- multi-opportunity portfolio ranking
- multi-entity synthetic demonstration
- decision-stage trace generation
- human material-authority boundary
- deterministic evidence hashes in the Python runtime
- expected-versus-realized value tracking
- public evidence endpoint
- browser-only interactive demonstration
- Flask API runtime
- automated pytest verification
- GitHub Actions continuous integration
- Docker runtime definition
- public-safe architecture and evidence documentation

The closed internal F001-F050 feature baseline is referenced but not disclosed in full in this public repository.

## Run locally

```bash
python -m pip install -r requirements.txt
python app.py
```

Open `http://localhost:8080`.

## Run tests

```bash
pytest -q
```

## Public API endpoints

- `GET /health`
- `POST /api/v1/assess`
- `POST /api/v1/portfolio`
- `GET /api/v1/demo/portfolio`
- `POST /api/v1/decision-trace`
- `POST /api/v1/value-realization`
- `GET /api/v1/public-evidence`

## Public evidence documents

- `docs/ARCHITECTURE_OVERVIEW.md`
- `docs/FEATURE_COVERAGE_MATRIX.md`
- `docs/PUBLIC_EVIDENCE_REPORT.md`
- `demo_data/portfolio_public.json`

## Current repository status

Public operational MVP hardening in progress.

The repository does not claim production certification, independent penetration-test clearance, regulatory approval, market validation, production-calibrated causal validity, financial outcome guarantees, or an external institutional pilot deployment.

## Acquisition and due-diligence boundary

The public repository is designed to let an evaluator inspect source, run tests, review commit history, execute the browser demonstration and API, and verify that analytical output does not autonomously create material execution authority.

Deeper architecture, protected feature specifications, sensitive intellectual-property evidence, source-level trade secrets, acquisition valuation, negotiation logic, and controlled data-room materials are not published here.

## Rights

All rights reserved.

Recorded rights holder: Eng. Mohamed Abdulkarim Sulaiman Rihan

Jeddah, Saudi Arabia
