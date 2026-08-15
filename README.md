# NOIOP-MVP-Operational

National Opportunity Intelligence & Orchestration Platform

[![NOIOP Operational MVP CI](https://github.com/maksr2030/NOIOP-MVP-Operational/actions/workflows/ci.yml/badge.svg)](https://github.com/maksr2030/NOIOP-MVP-Operational/actions/workflows/ci.yml)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/maksr2030/NOIOP-MVP-Operational)

NOIOP is a governed opportunity-intelligence and institutional decision-orchestration platform designed to connect opportunity discovery, evidence, prioritization, human authority, execution controls and value-realization tracking within one traceable operating lifecycle.

This public repository contains the public-safe Full-Stack MVP. Confidential trade secrets, transaction valuation materials, negotiation parameters, restricted data-room documents and protected implementation details remain excluded.

## Current Full-Stack MVP

The current release includes:

- public web interface on GitHub Pages
- Flask 2.0.0 MVP backend
- persistent opportunity records
- server-side assessment
- live portfolio generation
- human decision recording
- expected-versus-realized value events
- SHA-256 audit-event evidence
- SQLite persistent-store support
- configurable cross-origin access from the public interface
- Docker runtime
- Gunicorn production process
- Render Blueprint configuration
- automated pytest verification
- GitHub Actions continuous integration
- pilot validation harness and evidence assets

## Verification status

The Full-Stack code baseline passes Continuous Integration on the current main branch. The backend and persistence lifecycle are covered by automated tests. GitHub Pages publishes the frontend, while the Flask backend requires a real web-service runtime.

Public frontend:

`https://maksr2030.github.io/NOIOP-MVP-Operational/`

The frontend accepts the backend URL manually or through an `api` query parameter and then stores that HTTPS endpoint locally in the browser.

Example after backend deployment:

`https://maksr2030.github.io/NOIOP-MVP-Operational/?api=https://YOUR-BACKEND.onrender.com`

## Deploy the backend

The repository includes `render.yaml`, `Dockerfile`, Gunicorn and the required environment configuration for a Render web-service deployment.

Use the Deploy to Render button above, review the Blueprint and approve it in the Render account. The configured service uses:

- Docker runtime
- health check: `/health`
- persistent SQLite path: `/data/noiop.db`
- persistent disk mounted at `/data`
- allowed frontend origin: `https://maksr2030.github.io`

A persistent Render disk requires a paid compatible web-service plan. The repository currently uses the `starter` plan so that the SQLite data remains available across deploys and restarts.

After Render reports the service as Live, copy its HTTPS `onrender.com` URL and connect it from the public frontend. The operational acceptance test is then:

1. Health endpoint returns `status=ok`, version `2.0.0-mvp`, and `persistent_store=true`.
2. Create an opportunity from the browser.
3. Refresh the frontend and verify the opportunity remains available.
4. Run server-side assessment.
5. Record a human decision with rationale.
6. Record a value-realization event.
7. Inspect the hashed audit chain.
8. Reopen the application and confirm the persistent record remains available.

## Run locally

```bash
python -m pip install -r requirements.txt
python app.py
```

Open `http://localhost:8080`.

## Public API

- `GET /health`
- `GET /api/v1/opportunities`
- `POST /api/v1/opportunities`
- `GET /api/v1/opportunities/<id>`
- `PUT /api/v1/opportunities/<id>`
- `POST /api/v1/opportunities/<id>/assess`
- `POST /api/v1/opportunities/<id>/decisions`
- `GET /api/v1/opportunities/<id>/decisions`
- `POST /api/v1/opportunities/<id>/value-events`
- `GET /api/v1/opportunities/<id>/audit`
- `GET /api/v1/portfolio/live`
- `POST /api/v1/assess`
- `POST /api/v1/portfolio`
- `GET /api/v1/demo/portfolio`
- `POST /api/v1/decision-trace`
- `POST /api/v1/value-realization`
- `GET /api/v1/public-evidence`

## Acquisition and due-diligence boundary

The public repository is intended to establish technical provenance and inspectable operating behavior. It does not disclose the full confidential architecture, protected algorithms, confidential chain-of-title records, valuation, negotiation logic or restricted acquisition materials.

## Explicit non-claims

This repository does not claim production certification, independent penetration-test clearance, regulatory approval, external institutional acceptance, guaranteed financial outcomes or unrestricted production readiness.

## Rights

All rights reserved.

Recorded rights holder: Eng. Mohamed Abdulkarim Sulaiman Rihan

Jeddah, Saudi Arabia
