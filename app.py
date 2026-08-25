from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import os
import sqlite3
import uuid
from typing import Any

from flask import Flask, jsonify, request, send_from_directory


# ============================================================
# NOIOP Operational MVP
# National Opportunity Intelligence & Orchestration Platform
# Public-safe Full-Stack MVP
# ============================================================


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULT_DB_PATH = os.path.join(
    "/tmp",
    "noiop",
    "noiop.db"
)

DB_PATH = os.getenv(
    "NOIOP_DB_PATH",
    DEFAULT_DB_PATH
)

ALLOWED_ORIGIN = os.getenv(
    "NOIOP_ALLOWED_ORIGIN",
    "*"
)

PORT = int(
    os.getenv(
        "PORT",
        "8080"
    )
)


app = Flask(
    __name__,
    static_folder="."
)


# ============================================================
# GOVERNANCE CONFIGURATION
# ============================================================


WEIGHTS = {
    "demand": 0.22,
    "strategic_alignment": 0.22,
    "readiness": 0.18,
    "risk_inverse": 0.14,
    "evidence_quality": 0.14,
    "timing": 0.10,
}


PUBLIC_BOUNDARY = (
    "Controlled public demonstration only. "
    "No production certification, external institutional pilot, "
    "regulatory approval, market validation, guaranteed financial "
    "outcomes, or independent penetration-test clearance is claimed."
)


DEMO_RECORDS = [
    {
        "opportunity_id": "DEMO-001",
        "tenant_id": "ENTITY-A",
        "title": "Industrial AI Energy Optimization",
        "demand": 0.92,
        "strategic_alignment": 0.90,
        "readiness": 0.80,
        "risk_inverse": 0.74,
        "evidence_quality": 0.93,
        "timing": 0.86,
    },
    {
        "opportunity_id": "DEMO-002",
        "tenant_id": "ENTITY-A",
        "title": "Smart Logistics Route Intelligence",
        "demand": 0.84,
        "strategic_alignment": 0.82,
        "readiness": 0.71,
        "risk_inverse": 0.70,
        "evidence_quality": 0.86,
        "timing": 0.78,
    },
    {
        "opportunity_id": "DEMO-101",
        "tenant_id": "ENTITY-B",
        "title": "Water Infrastructure Predictive Optimization",
        "demand": 0.88,
        "strategic_alignment": 0.87,
        "readiness": 0.76,
        "risk_inverse": 0.72,
        "evidence_quality": 0.90,
        "timing": 0.81,
    },
    {
        "opportunity_id": "DEMO-102",
        "tenant_id": "ENTITY-B",
        "title": "Low-Evidence Demonstration Case",
        "demand": 0.94,
        "strategic_alignment": 0.91,
        "readiness": 0.70,
        "risk_inverse": 0.75,
        "evidence_quality": 0.32,
        "timing": 0.90,
    },
]


# ============================================================
# DATABASE SCHEMA
# ============================================================


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS opportunities (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    demand REAL NOT NULL DEFAULT 0,
    strategic_alignment REAL NOT NULL DEFAULT 0,
    readiness REAL NOT NULL DEFAULT 0,
    risk_inverse REAL NOT NULL DEFAULT 0,
    evidence_quality REAL NOT NULL DEFAULT 0,
    timing REAL NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'DRAFT',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS decisions (
    id TEXT PRIMARY KEY,
    opportunity_id TEXT NOT NULL,
    actor TEXT NOT NULL,
    decision TEXT NOT NULL,
    rationale TEXT NOT NULL DEFAULT '',
    assessment_hash TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS value_events (
    id TEXT PRIMARY KEY,
    opportunity_id TEXT NOT NULL,
    expected_value REAL NOT NULL DEFAULT 0,
    realized_value REAL NOT NULL DEFAULT 0,
    currency TEXT NOT NULL DEFAULT 'SAR',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    entity_id TEXT,
    actor TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    event_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_opportunities_updated_at
ON opportunities(updated_at);

CREATE INDEX IF NOT EXISTS idx_decisions_opportunity_id
ON decisions(opportunity_id);

CREATE INDEX IF NOT EXISTS idx_value_events_opportunity_id
ON value_events(opportunity_id);

CREATE INDEX IF NOT EXISTS idx_audit_log_entity_id
ON audit_log(entity_id);

CREATE INDEX IF NOT EXISTS idx_audit_log_created_at
ON audit_log(created_at);
"""


# ============================================================
# CORE UTILITIES
# ============================================================


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clamp(value: Any) -> float:
    try:
        return max(
            0.0,
            min(
                1.0,
                float(value)
            )
        )
    except (TypeError, ValueError):
        return 0.0


def canonical_hash(payload: Any) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )

    return sha256(
        canonical.encode("utf-8")
    ).hexdigest()


def ensure_database_directory() -> None:
    directory = os.path.dirname(
        os.path.abspath(DB_PATH)
    )

    if directory:
        os.makedirs(
            directory,
            exist_ok=True
        )


def _connect() -> sqlite3.Connection:
    ensure_database_directory()

    conn = sqlite3.connect(
        DB_PATH,
        timeout=30
    )

    conn.row_factory = sqlite3.Row

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    conn.execute(
        "PRAGMA busy_timeout = 30000"
    )

    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(
            SCHEMA_SQL
        )
        conn.commit()


def db() -> sqlite3.Connection:
    conn = _connect()

    conn.executescript(
        SCHEMA_SQL
    )

    conn.commit()

    return conn


def persistent_store_enabled() -> bool:
    absolute_path = os.path.abspath(
        DB_PATH
    )

    return (
        absolute_path == "/data/noiop.db"
        or absolute_path.startswith("/data/")
    )


# ============================================================
# AUDIT ENGINE
# ============================================================


def audit(
    event_type: str,
    entity_id: str | None,
    actor: str,
    payload: Any,
) -> dict:

    event = {
        "event_id": str(
            uuid.uuid4()
        ),
        "event_type": str(
            event_type
        ),
        "entity_id": entity_id,
        "actor": str(
            actor
        ),
        "payload": payload,
        "created_at": utc_now(),
    }

    event["event_hash"] = canonical_hash(
        event
    )

    with db() as conn:
        conn.execute(
            """
            INSERT INTO audit_log (
                event_id,
                event_type,
                entity_id,
                actor,
                payload_json,
                event_hash,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event["event_id"],
                event["event_type"],
                event["entity_id"],
                event["actor"],
                json.dumps(
                    payload,
                    ensure_ascii=False,
                    default=str,
                ),
                event["event_hash"],
                event["created_at"],
            ),
        )

        conn.commit()

    return event


# ============================================================
# ASSESSMENT ENGINE
# ============================================================


def assess(payload: dict) -> dict:

    signals = {
        key: clamp(
            payload.get(
                key,
                0
            )
        )
        for key in WEIGHTS
    }

    score = 100 * sum(
        signals[key] * WEIGHTS[key]
        for key in WEIGHTS
    )

    if (
        signals["evidence_quality"] < 0.55
        or signals["readiness"] < 0.45
    ):
        decision = "ABSTAIN"

    elif score >= 82:
        decision = "PRIORITY_CANDIDATE"

    elif score >= 68:
        decision = "ADVANCE_WITH_CONDITIONS"

    else:
        decision = "REVIEW"

    result = {
        "engine":
            "NOIOP Operational Assessment Engine",

        "engine_version":
            "2.0.1-mvp",

        "opportunity_id":
            str(
                payload.get(
                    "opportunity_id",
                    payload.get(
                        "id",
                        "PUBLIC-DEMO"
                    )
                )
            ),

        "tenant_id":
            str(
                payload.get(
                    "tenant_id",
                    "PUBLIC-DEMO-ENTITY"
                )
            ),

        "title":
            str(
                payload.get(
                    "title",
                    "Untitled Opportunity"
                )
            ),

        "signals":
            signals,

        "score":
            round(
                score,
                2
            ),

        "decision":
            decision,

        "material_execution_authority":
            False,

        "human_approval_required":
            decision != "ABSTAIN",

        "public_demo_boundary":
            PUBLIC_BOUNDARY,
    }

    result["evidence_hash"] = canonical_hash(
        result
    )

    return result


# ============================================================
# PORTFOLIO ENGINE
# ============================================================


def portfolio(records: list[dict]) -> dict:

    items = [
        assess(record)
        for record in records
    ]

    items.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    counts = {}

    for item in items:
        decision = item["decision"]

        counts[decision] = (
            counts.get(
                decision,
                0
            )
            + 1
        )

    result = {
        "engine":
            "NOIOP Operational Portfolio Engine",

        "engine_version":
            "2.0.1-mvp",

        "opportunity_count":
            len(items),

        "decision_counts":
            counts,

        "ranked_opportunities":
            items,

        "material_execution_authority":
            False,

        "public_demo_boundary":
            PUBLIC_BOUNDARY,
    }

    result["portfolio_hash"] = canonical_hash(
        result
    )

    return result


# ============================================================
# DECISION TRACE ENGINE
# ============================================================


def decision_trace(payload: dict) -> dict:

    assessment = assess(
        payload
    )

    result = {
        "opportunity_id":
            assessment["opportunity_id"],

        "tenant_id":
            assessment["tenant_id"],

        "stages": [
            {
                "stage":
                    "INGEST",

                "state":
                    "RECORDED",
            },

            {
                "stage":
                    "SIGNAL_NORMALIZATION",

                "state":
                    "COMPLETE",
            },

            {
                "stage":
                    "EVIDENCE_GATE",

                "state":
                    (
                        "PASS"
                        if assessment["signals"]["evidence_quality"] >= 0.55
                        else "ABSTAIN"
                    ),
            },

            {
                "stage":
                    "READINESS_GATE",

                "state":
                    (
                        "PASS"
                        if assessment["signals"]["readiness"] >= 0.45
                        else "ABSTAIN"
                    ),
            },

            {
                "stage":
                    "PRIORITIZATION",

                "state":
                    assessment["decision"],
            },

            {
                "stage":
                    "MATERIAL_AUTHORITY",

                "state":
                    (
                        "HUMAN_APPROVAL_REQUIRED"
                        if assessment["human_approval_required"]
                        else "NO_EXECUTION"
                    ),
            },
        ],

        "assessment_hash":
            assessment["evidence_hash"],

        "material_execution_authority":
            False,

        "public_demo_boundary":
            PUBLIC_BOUNDARY,
    }

    result["trace_hash"] = canonical_hash(
        result
    )

    return result


# ============================================================
# VALUE REALIZATION ENGINE
# ============================================================


def value_realization(payload: dict) -> dict:

    try:
        expected = max(
            0.0,
            float(
                payload.get(
                    "expected_value",
                    0
                )
            )
        )
    except (TypeError, ValueError):
        expected = 0.0

    try:
        realized = max(
            0.0,
            float(
                payload.get(
                    "realized_value",
                    0
                )
            )
        )
    except (TypeError, ValueError):
        realized = 0.0

    ratio = (
        realized / expected
        if expected > 0
        else 0
    )

    if (
        expected > 0
        and ratio >= 1
    ):
        state = "ON_OR_ABOVE_TARGET"

    elif realized > 0:
        state = "PARTIAL_REALIZATION"

    else:
        state = "NO_REALIZATION_EVIDENCE"

    result = {
        "engine":
            "NOIOP Operational Value Realization Engine",

        "engine_version":
            "2.0.1-mvp",

        "opportunity_id":
            str(
                payload.get(
                    "opportunity_id",
                    "PUBLIC-DEMO"
                )
            ),

        "currency":
            str(
                payload.get(
                    "currency",
                    "SAR"
                )
            ),

        "expected_value":
            round(
                expected,
                2
            ),

        "realized_value":
            round(
                realized,
                2
            ),

        "realization_ratio":
            round(
                ratio,
                4
            ),

        "state":
            state,

        "financial_outcome_guarantee":
            False,

        "public_demo_boundary":
            PUBLIC_BOUNDARY,
    }

    result["realization_hash"] = canonical_hash(
        result
    )

    return result


# ============================================================
# HTTP AND CORS
# ============================================================


@app.after_request
def cors(response):

    response.headers[
        "Access-Control-Allow-Origin"
    ] = ALLOWED_ORIGIN

    response.headers[
        "Access-Control-Allow-Headers"
    ] = (
        "Content-Type, "
        "X-NOIOP-Actor"
    )

    response.headers[
        "Access-Control-Allow-Methods"
    ] = (
        "GET, POST, PUT, OPTIONS"
    )

    response.headers[
        "Cache-Control"
    ] = "no-store"

    return response


@app.route(
    "/api/<path:_>",
    methods=["OPTIONS"]
)
def options_api(_):
    return "", 204


# ============================================================
# FRONTEND
# ============================================================


@app.get("/")
def home():

    return send_from_directory(
        BASE_DIR,
        "index.html"
    )


# ============================================================
# HEALTH
# ============================================================


@app.get("/health")
def health():

    init_db()

    with db() as conn:

        row = conn.execute(
            """
            SELECT COUNT(*) AS c
            FROM opportunities
            """
        ).fetchone()

        count = (
            row["c"]
            if row
            else 0
        )

    return jsonify(
        {
            "status":
                "ok",

            "service":
                "noiop-operational-mvp",

            "version":
                "2.0.1-mvp",

            "database_ready":
                True,

            "persistent_store":
                persistent_store_enabled(),

            "opportunity_count":
                count,
        }
    )


# ============================================================
# OPPORTUNITY WORKSPACE
# ============================================================


@app.get(
    "/api/v1/opportunities"
)
def list_opportunities():

    init_db()

    with db() as conn:

        rows = conn.execute(
            """
            SELECT *
            FROM opportunities
            ORDER BY updated_at DESC
            """
        ).fetchall()

    return jsonify(
        {
            "count":
                len(rows),

            "items":
                [
                    dict(row)
                    for row in rows
                ],
        }
    )


@app.post(
    "/api/v1/opportunities"
)
def create_opportunity():

    init_db()

    body = (
        request.get_json(
            silent=True
        )
        or {}
    )

    now = utc_now()

    opportunity_id = str(
        body.get("id")
        or uuid.uuid4()
    )

    record = {
        "id":
            opportunity_id,

        "tenant_id":
            str(
                body.get(
                    "tenant_id",
                    "ENTITY-A"
                )
            ),

        "title":
            str(
                body.get(
                    "title",
                    "Untitled Opportunity"
                )
            ),

        "description":
            str(
                body.get(
                    "description",
                    ""
                )
            ),

        **{
            key:
                clamp(
                    body.get(
                        key,
                        0
                    )
                )
            for key in WEIGHTS
        },

        "status":
            str(
                body.get(
                    "status",
                    "DRAFT"
                )
            ),

        "created_at":
            now,

        "updated_at":
            now,
    }

    with db() as conn:

        conn.execute(
            """
            INSERT INTO opportunities (
                id,
                tenant_id,
                title,
                description,
                demand,
                strategic_alignment,
                readiness,
                risk_inverse,
                evidence_quality,
                timing,
                status,
                created_at,
                updated_at
            )
            VALUES (
                :id,
                :tenant_id,
                :title,
                :description,
                :demand,
                :strategic_alignment,
                :readiness,
                :risk_inverse,
                :evidence_quality,
                :timing,
                :status,
                :created_at,
                :updated_at
            )
            """,
            record,
        )

        conn.commit()

    audit(
        "OPPORTUNITY_CREATED",
        opportunity_id,
        request.headers.get(
            "X-NOIOP-Actor",
            "public-demo-user"
        ),
        record,
    )

    return jsonify(
        record
    ), 201


@app.get(
    "/api/v1/opportunities/<oid>"
)
def get_opportunity(oid: str):

    init_db()

    with db() as conn:

        row = conn.execute(
            """
            SELECT *
            FROM opportunities
            WHERE id = ?
            """,
            (oid,),
        ).fetchone()

    if not row:
        return jsonify(
            {
                "error":
                    "not_found"
            }
        ), 404

    record = dict(
        row
    )

    record["assessment"] = assess(
        record
    )

    record["decision_trace"] = decision_trace(
        record
    )

    return jsonify(
        record
    )


@app.put(
    "/api/v1/opportunities/<oid>"
)
def update_opportunity(oid: str):

    init_db()

    body = (
        request.get_json(
            silent=True
        )
        or {}
    )

    with db() as conn:

        row = conn.execute(
            """
            SELECT *
            FROM opportunities
            WHERE id = ?
            """,
            (oid,),
        ).fetchone()

        if not row:
            return jsonify(
                {
                    "error":
                        "not_found"
                }
            ), 404

        current = dict(
            row
        )

        for key in [
            "tenant_id",
            "title",
            "description",
            "status",
        ]:
            if key in body:
                current[key] = str(
                    body[key]
                )

        for key in WEIGHTS:
            if key in body:
                current[key] = clamp(
                    body[key]
                )

        current[
            "updated_at"
        ] = utc_now()

        conn.execute(
            """
            UPDATE opportunities
            SET
                tenant_id = :tenant_id,
                title = :title,
                description = :description,
                demand = :demand,
                strategic_alignment = :strategic_alignment,
                readiness = :readiness,
                risk_inverse = :risk_inverse,
                evidence_quality = :evidence_quality,
                timing = :timing,
                status = :status,
                updated_at = :updated_at
            WHERE id = :id
            """,
            current,
        )

        conn.commit()

    audit(
        "OPPORTUNITY_UPDATED",
        oid,
        request.headers.get(
            "X-NOIOP-Actor",
            "public-demo-user"
        ),
        body,
    )

    return jsonify(
        current
    )


# ============================================================
# SAVED OPPORTUNITY ASSESSMENT
# ============================================================


@app.post(
    "/api/v1/opportunities/<oid>/assess"
)
def assess_saved_opportunity(oid: str):

    init_db()

    with db() as conn:

        row = conn.execute(
            """
            SELECT *
            FROM opportunities
            WHERE id = ?
            """,
            (oid,),
        ).fetchone()

    if not row:
        return jsonify(
            {
                "error":
                    "not_found"
            }
        ), 404

    result = assess(
        dict(row)
    )

    audit(
        "ASSESSMENT_GENERATED",
        oid,
        request.headers.get(
            "X-NOIOP-Actor",
            "public-demo-user"
        ),
        result,
    )

    return jsonify(
        result
    )


# ============================================================
# HUMAN DECISION RECORD
# ============================================================


@app.post(
    "/api/v1/opportunities/<oid>/decisions"
)
def record_decision(oid: str):

    init_db()

    body = (
        request.get_json(
            silent=True
        )
        or {}
    )

    with db() as conn:

        row = conn.execute(
            """
            SELECT *
            FROM opportunities
            WHERE id = ?
            """,
            (oid,),
        ).fetchone()

    if not row:
        return jsonify(
            {
                "error":
                    "not_found"
            }
        ), 404

    actor = str(
        body.get("actor")
        or request.headers.get(
            "X-NOIOP-Actor",
            "decision-owner"
        )
    )

    decision = str(
        body.get(
            "decision",
            "REVIEW"
        )
    ).upper()

    rationale = str(
        body.get(
            "rationale",
            ""
        )
    )

    assessment = assess(
        dict(row)
    )

    decision_id = str(
        uuid.uuid4()
    )

    created_at = utc_now()

    with db() as conn:

        conn.execute(
            """
            INSERT INTO decisions (
                id,
                opportunity_id,
                actor,
                decision,
                rationale,
                assessment_hash,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                decision_id,
                oid,
                actor,
                decision,
                rationale,
                assessment["evidence_hash"],
                created_at,
            ),
        )

        conn.execute(
            """
            UPDATE opportunities
            SET
                status = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                decision,
                created_at,
                oid,
            ),
        )

        conn.commit()

    payload = {
        "id":
            decision_id,

        "opportunity_id":
            oid,

        "actor":
            actor,

        "decision":
            decision,

        "rationale":
            rationale,

        "assessment_hash":
            assessment["evidence_hash"],

        "created_at":
            created_at,
    }

    audit(
        "HUMAN_DECISION_RECORDED",
        oid,
        actor,
        payload,
    )

    return jsonify(
        payload
    ), 201


@app.get(
    "/api/v1/opportunities/<oid>/decisions"
)
def list_decisions(oid: str):

    init_db()

    with db() as conn:

        rows = conn.execute(
            """
            SELECT *
            FROM decisions
            WHERE opportunity_id = ?
            ORDER BY created_at DESC
            """,
            (oid,),
        ).fetchall()

    return jsonify(
        {
            "count":
                len(rows),

            "items":
                [
                    dict(row)
                    for row in rows
                ],
        }
    )


# ============================================================
# VALUE REALIZATION
# ============================================================


@app.post(
    "/api/v1/opportunities/<oid>/value-events"
)
def record_value_event(oid: str):

    init_db()

    body = (
        request.get_json(
            silent=True
        )
        or {}
    )

    with db() as conn:

        exists = conn.execute(
            """
            SELECT id
            FROM opportunities
            WHERE id = ?
            """,
            (oid,),
        ).fetchone()

    if not exists:
        return jsonify(
            {
                "error":
                    "not_found"
            }
        ), 404

    payload = dict(
        body
    )

    payload[
        "opportunity_id"
    ] = oid

    result = value_realization(
        payload
    )

    event_id = str(
        uuid.uuid4()
    )

    created_at = utc_now()

    with db() as conn:

        conn.execute(
            """
            INSERT INTO value_events (
                id,
                opportunity_id,
                expected_value,
                realized_value,
                currency,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                oid,
                result["expected_value"],
                result["realized_value"],
                result["currency"],
                created_at,
            ),
        )

        conn.commit()

    result.update(
        {
            "id":
                event_id,

            "created_at":
                created_at,
        }
    )

    audit(
        "VALUE_REALIZATION_RECORDED",
        oid,
        request.headers.get(
            "X-NOIOP-Actor",
            "public-demo-user"
        ),
        result,
    )

    return jsonify(
        result
    ), 201


# ============================================================
# AUDIT CHAIN
# ============================================================


@app.get(
    "/api/v1/opportunities/<oid>/audit"
)
def opportunity_audit(oid: str):

    init_db()

    with db() as conn:

        rows = conn.execute(
            """
            SELECT
                seq,
                event_id,
                event_type,
                entity_id,
                actor,
                payload_json,
                event_hash,
                created_at
            FROM audit_log
            WHERE entity_id = ?
            ORDER BY seq DESC
            """,
            (oid,),
        ).fetchall()

    items = []

    for row in rows:

        item = dict(
            row
        )

        try:
            item["payload"] = json.loads(
                item.pop(
                    "payload_json"
                )
            )

        except Exception:
            item["payload"] = item.pop(
                "payload_json",
                None
            )

        items.append(
            item
        )

    return jsonify(
        {
            "count":
                len(items),

            "items":
                items,
        }
    )


# ============================================================
# PUBLIC OPERATIONAL API
# ============================================================


@app.post(
    "/api/v1/assess"
)
def assess_api():

    body = (
        request.get_json(
            silent=True
        )
        or {}
    )

    return jsonify(
        assess(
            body
        )
    )


@app.post(
    "/api/v1/portfolio"
)
def portfolio_api():

    body = (
        request.get_json(
            silent=True
        )
        or {}
    )

    opportunities = body.get(
        "opportunities",
        []
    )

    if not isinstance(
        opportunities,
        list
    ):
        return jsonify(
            {
                "error":
                    "opportunities_must_be_list"
            }
        ), 400

    return jsonify(
        portfolio(
            opportunities
        )
    )


@app.get(
    "/api/v1/demo/portfolio"
)
def demo_portfolio_api():

    return jsonify(
        portfolio(
            DEMO_RECORDS
        )
    )


@app.get(
    "/api/v1/portfolio/live"
)
def live_portfolio_api():

    init_db()

    with db() as conn:

        rows = conn.execute(
            """
            SELECT *
            FROM opportunities
            ORDER BY updated_at DESC
            """
        ).fetchall()

    records = [
        dict(row)
        for row in rows
    ]

    return jsonify(
        portfolio(
            records
        )
    )


@app.post(
    "/api/v1/decision-trace"
)
def decision_trace_api():

    body = (
        request.get_json(
            silent=True
        )
        or {}
    )

    return jsonify(
        decision_trace(
            body
        )
    )


@app.post(
    "/api/v1/value-realization"
)
def value_realization_api():

    body = (
        request.get_json(
            silent=True
        )
        or {}
    )

    return jsonify(
        value_realization(
            body
        )
    )


# ============================================================
# PUBLIC EVIDENCE
# ============================================================


@app.get(
    "/api/v1/public-evidence"
)
def public_evidence_api():

    evidence = {
        "release":
            "NOIOP-MVP-Operational/full-stack-2.0.1",

        "capabilities": [
            "persistent-opportunity-workspace",
            "assessment",
            "portfolio-ranking",
            "decision-trace",
            "human-decision-record",
            "value-realization",
            "audit-log",
        ],

        "sensitive_ip_exposed":
            False,

        "material_execution_authority":
            False,

        "public_demo_boundary":
            PUBLIC_BOUNDARY,
    }

    evidence[
        "evidence_hash"
    ] = canonical_hash(
        evidence
    )

    return jsonify(
        evidence
    )


# ============================================================
# STARTUP INITIALIZATION
# ============================================================


try:
    init_db()

except Exception as startup_error:

    print(
        "NOIOP database initialization error:",
        repr(startup_error),
        flush=True,
    )


# ============================================================
# LOCAL ENTRY POINT
# ============================================================


if __name__ == "__main__":

    init_db()

    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False,
    )
