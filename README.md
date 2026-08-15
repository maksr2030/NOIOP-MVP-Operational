# NOIOP-MVP-Operational

National Opportunity Intelligence & Orchestration Platform

[![NOIOP Operational MVP CI](https://github.com/maksr2030/NOIOP-MVP-Operational/actions/workflows/ci.yml/badge.svg)](https://github.com/maksr2030/NOIOP-MVP-Operational/actions/workflows/ci.yml)

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

## Current verification status

- GitHub Actions continuous integration: passing on the current main branch
- automated tests: passing in CI
- Python application compilation: passing in CI
- previous failing Pages workflow: removed because GitHub Pages is not yet enabled at repository-settings level
- root `index.html`: ready for branch-based GitHub Pages publication
- intended public URL after Pages activation: `https://maksr2030.github.io/NOIOP-MVP-Operational/`

The repository is therefore operationally green at code/CI level. Public web publication remains a repository setting, not an application defect.

## Public web release configuration

For GitHub Pages, configure the repository once as follows:

1. Open `Settings` → `Pages`.
2. Under `Build and deployment`, select `Deploy from a branch`.
3. Select branch `main`.
4. Select folder `/(root)`.
5. Save.

After GitHub publishes the site, the expected public URL is:

`https://maksr2030.github.io/NOIOP-MVP-Operational/`

No separate Pages workflow is required because the browser demonstration is fully static and self-contained in `index.html`.

## Run locally

```bash
python -m pip install -r requirements.txt
python app.py
```

Open `http://localhost:8080`.

## Run tests

```bash
python -m pytest -q
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

## Acquisition and due-diligence boundary

The public repository is designed to let an evaluator inspect source, run tests, review commit history, execute the browser demonstration and API, and verify that analytical output does not autonomously create material execution authority.

Deeper architecture, protected feature specifications, sensitive intellectual-property evidence, source-level trade secrets, acquisition valuation, negotiation logic, and controlled data-room materials are not published here.

## Explicit non-claims

The repository does not claim production certification, independent penetration-test clearance, regulatory approval, market validation, production-calibrated causal validity, financial outcome guarantees, or an external institutional pilot deployment.

## Rights

All rights reserved.

Recorded rights holder: Eng. Mohamed Abdulkarim Sulaiman Rihan

Jeddah, Saudi Arabia
