# NOIOP Full-Stack Deployment

The repository now contains two distinct deployment layers.

1. Public frontend: GitHub Pages.
2. Persistent operational backend: Flask + SQLite + Gunicorn, deployable through the included `render.yaml` Blueprint.

## Runtime architecture

Browser -> HTTPS Backend API -> Flask -> Opportunity Engine -> SQLite persistent store -> Audit Log

## Backend capabilities

- Persistent opportunity creation and retrieval
- Governed assessment
- Live portfolio generation
- Human decision recording
- Decision rationale retention
- Value-realization events
- Cryptographically hashed audit events
- Health endpoint
- Cross-origin support for the GitHub Pages frontend

## Deployment configuration

The included `render.yaml` defines a Docker web service with a persistent disk mounted at `/data` and the database stored at `/data/noiop.db`.

Required production verification after deployment:

1. `/health` returns `status=ok` and `persistent_store=true`.
2. GitHub Pages connects to the HTTPS backend.
3. A created opportunity persists across browser refresh.
4. A human decision can be recorded and retrieved.
5. Audit events are returned with cryptographic hashes.
6. A value-realization event can be persisted.

The public frontend intentionally requires a backend URL until a production domain is assigned. The URL is stored only in the user's browser local storage.
