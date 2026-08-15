from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import os
import sqlite3
import uuid
from typing import Dict, Any, List

from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder='.')
DB_PATH = os.getenv('NOIOP_DB_PATH', os.path.join(os.path.dirname(__file__), 'noiop.db'))
ALLOWED_ORIGIN = os.getenv('NOIOP_ALLOWED_ORIGIN', '*')

WEIGHTS = {
    'demand': 0.22,
    'strategic_alignment': 0.22,
    'readiness': 0.18,
    'risk_inverse': 0.14,
    'evidence_quality': 0.14,
    'timing': 0.10,
}

PUBLIC_BOUNDARY = (
    'Controlled public demonstration only. No production certification, external institutional pilot, '
    'regulatory approval, market validation, or independent penetration-test clearance is claimed.'
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clamp(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


def canonical_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    return sha256(raw).hexdigest()


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with db() as conn:
        conn.executescript('''
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
            created_at TEXT NOT NULL,
            FOREIGN KEY(opportunity_id) REFERENCES opportunities(id)
        );
        CREATE TABLE IF NOT EXISTS value_events (
            id TEXT PRIMARY KEY,
            opportunity_id TEXT NOT NULL,
            expected_value REAL NOT NULL DEFAULT 0,
            realized_value REAL NOT NULL DEFAULT 0,
            currency TEXT NOT NULL DEFAULT 'SAR',
            created_at TEXT NOT NULL,
            FOREIGN KEY(opportunity_id) REFERENCES opportunities(id)
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
        ''')


def audit(event_type: str, entity_id: str | None, actor: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    event = {
        'event_id': str(uuid.uuid4()),
        'event_type': event_type,
        'entity_id': entity_id,
        'actor': actor,
        'payload': payload,
        'created_at': utc_now(),
    }
    event['event_hash'] = canonical_hash(event)
    with db() as conn:
        conn.execute(
            'INSERT INTO audit_log(event_id,event_type,entity_id,actor,payload_json,event_hash,created_at) VALUES(?,?,?,?,?,?,?)',
            (event['event_id'], event_type, entity_id, actor, json.dumps(payload, ensure_ascii=False), event['event_hash'], event['created_at'])
        )
    return event


def assess(payload: Dict[str, Any]) -> Dict[str, Any]:
    signals = {k: clamp(payload.get(k, 0)) for k in WEIGHTS}
    score = 100.0 * sum(signals[k] * WEIGHTS[k] for k in WEIGHTS)
    if signals['evidence_quality'] < 0.55 or signals['readiness'] < 0.45:
        decision = 'ABSTAIN'
    elif score >= 82:
        decision = 'PRIORITY_CANDIDATE'
    elif score >= 68:
        decision = 'ADVANCE_WITH_CONDITIONS'
    else:
        decision = 'REVIEW'
    result = {
        'engine': 'NOIOP Operational Assessment Engine',
        'engine_version': '2.0.0-mvp',
        'opportunity_id': str(payload.get('opportunity_id', payload.get('id', 'PUBLIC-DEMO'))),
        'tenant_id': str(payload.get('tenant_id', 'PUBLIC-DEMO-ENTITY')),
        'title': str(payload.get('title', 'Untitled Opportunity')),
        'signals': signals,
        'score': round(score, 2),
        'decision': decision,
        'material_execution_authority': False,
        'human_approval_required': decision != 'ABSTAIN',
        'public_demo_boundary': PUBLIC_BOUNDARY,
    }
    result['evidence_hash'] = canonical_hash(result)
    return result


def portfolio(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    assessments = [assess(r) for r in records]
    assessments.sort(key=lambda x: x['score'], reverse=True)
    counts: Dict[str, int] = {}
    for item in assessments:
        counts[item['decision']] = counts.get(item['decision'], 0) + 1
    out = {
        'engine': 'NOIOP Operational Portfolio Engine',
        'engine_version': '2.0.0-mvp',
        'opportunity_count': len(assessments),
        'decision_counts': counts,
        'ranked_opportunities': assessments,
        'material_execution_authority': False,
        'public_demo_boundary': PUBLIC_BOUNDARY,
    }
    out['portfolio_hash'] = canonical_hash(out)
    return out


def decision_trace(payload: Dict[str, Any]) -> Dict[str, Any]:
    assessed = assess(payload)
    trace = {
        'opportunity_id': assessed['opportunity_id'],
        'tenant_id': assessed['tenant_id'],
        'stages': [
            {'stage': 'INGEST', 'state': 'RECORDED'},
            {'stage': 'SIGNAL_NORMALIZATION', 'state': 'COMPLETE'},
            {'stage': 'EVIDENCE_GATE', 'state': 'PASS' if assessed['signals']['evidence_quality'] >= 0.55 else 'ABSTAIN'},
            {'stage': 'READINESS_GATE', 'state': 'PASS' if assessed['signals']['readiness'] >= 0.45 else 'ABSTAIN'},
            {'stage': 'PRIORITIZATION', 'state': assessed['decision']},
            {'stage': 'MATERIAL_AUTHORITY', 'state': 'HUMAN_APPROVAL_REQUIRED' if assessed['human_approval_required'] else 'NO_EXECUTION'},
        ],
        'assessment_hash': assessed['evidence_hash'],
        'material_execution_authority': False,
        'public_demo_boundary': PUBLIC_BOUNDARY,
    }
    trace['trace_hash'] = canonical_hash(trace)
    return trace


def value_realization(payload: Dict[str, Any]) -> Dict[str, Any]:
    expected = max(0.0, float(payload.get('expected_value', 0)))
    realized = max(0.0, float(payload.get('realized_value', 0)))
    ratio = (realized / expected) if expected > 0 else 0.0
    state = 'ON_OR_ABOVE_TARGET' if expected > 0 and ratio >= 1 else ('PARTIAL_REALIZATION' if realized > 0 else 'NO_REALIZATION_EVIDENCE')
    out = {
        'engine': 'NOIOP Operational Value Realization Engine',
        'engine_version': '2.0.0-mvp',
        'opportunity_id': str(payload.get('opportunity_id', 'PUBLIC-DEMO')),
        'currency': str(payload.get('currency', 'SAR')),
        'expected_value': round(expected, 2),
        'realized_value': round(realized, 2),
        'realization_ratio': round(ratio, 4),
        'state': state,
        'financial_outcome_guarantee': False,
        'public_demo_boundary': PUBLIC_BOUNDARY,
    }
    out['realization_hash'] = canonical_hash(out)
    return out


def row_to_opportunity(row: sqlite3.Row) -> Dict[str, Any]:
    return dict(row)


@app.after_request
def cors(response):
    response.headers['Access-Control-Allow-Origin'] = ALLOWED_ORIGIN
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-NOIOP-Actor'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
    return response


@app.route('/api/<path:_>', methods=['OPTIONS'])
def options_api(_):
    return ('', 204)


@app.get('/')
def home():
    return send_from_directory('.', 'index.html')


@app.get('/health')
def health():
    with db() as conn:
        count = conn.execute('SELECT COUNT(*) AS c FROM opportunities').fetchone()['c']
    return jsonify({'status': 'ok', 'service': 'noiop-operational-mvp', 'version': '2.0.0-mvp', 'persistent_store': True, 'opportunity_count': count})


@app.get('/api/v1/opportunities')
def list_opportunities():
    with db() as conn:
        rows = conn.execute('SELECT * FROM opportunities ORDER BY updated_at DESC').fetchall()
    items = [row_to_opportunity(r) for r in rows]
    return jsonify({'count': len(items), 'items': items})


@app.post('/api/v1/opportunities')
def create_opportunity():
    body = request.get_json(force=True) or {}
    now = utc_now(); oid = str(body.get('id') or uuid.uuid4())
    record = {
        'id': oid,
        'tenant_id': str(body.get('tenant_id', 'ENTITY-A')),
        'title': str(body.get('title', 'Untitled Opportunity')),
        'description': str(body.get('description', '')),
        **{k: clamp(body.get(k, 0)) for k in WEIGHTS},
        'status': str(body.get('status', 'DRAFT')),
        'created_at': now,
        'updated_at': now,
    }
    with db() as conn:
        conn.execute('''INSERT INTO opportunities(id,tenant_id,title,description,demand,strategic_alignment,readiness,risk_inverse,evidence_quality,timing,status,created_at,updated_at)
                        VALUES(:id,:tenant_id,:title,:description,:demand,:strategic_alignment,:readiness,:risk_inverse,:evidence_quality,:timing,:status,:created_at,:updated_at)''', record)
    audit('OPPORTUNITY_CREATED', oid, request.headers.get('X-NOIOP-Actor','public-demo-user'), record)
    return jsonify(record), 201


@app.get('/api/v1/opportunities/<oid>')
def get_opportunity(oid: str):
    with db() as conn:
        row = conn.execute('SELECT * FROM opportunities WHERE id=?', (oid,)).fetchone()
    if not row: return jsonify({'error':'not_found'}), 404
    record = row_to_opportunity(row)
    record['assessment'] = assess(record)
    record['decision_trace'] = decision_trace(record)
    return jsonify(record)


@app.put('/api/v1/opportunities/<oid>')
def update_opportunity(oid: str):
    body = request.get_json(force=True) or {}
    with db() as conn:
        existing = conn.execute('SELECT * FROM opportunities WHERE id=?', (oid,)).fetchone()
        if not existing: return jsonify({'error':'not_found'}), 404
        current = dict(existing)
        for k in ['tenant_id','title','description','status']:
            if k in body: current[k] = str(body[k])
        for k in WEIGHTS:
            if k in body: current[k] = clamp(body[k])
        current['updated_at'] = utc_now()
        conn.execute('''UPDATE opportunities SET tenant_id=:tenant_id,title=:title,description=:description,demand=:demand,strategic_alignment=:strategic_alignment,readiness=:readiness,risk_inverse=:risk_inverse,evidence_quality=:evidence_quality,timing=:timing,status=:status,updated_at=:updated_at WHERE id=:id''', current)
    audit('OPPORTUNITY_UPDATED', oid, request.headers.get('X-NOIOP-Actor','public-demo-user'), body)
    return jsonify(current)


@app.post('/api/v1/opportunities/<oid>/assess')
def assess_saved_opportunity(oid: str):
    with db() as conn:
        row = conn.execute('SELECT * FROM opportunities WHERE id=?', (oid,)).fetchone()
    if not row: return jsonify({'error':'not_found'}), 404
    result = assess(dict(row))
    audit('ASSESSMENT_GENERATED', oid, request.headers.get('X-NOIOP-Actor','public-demo-user'), result)
    return jsonify(result)


@app.post('/api/v1/opportunities/<oid>/decisions')
def record_decision(oid: str):
    body = request.get_json(force=True) or {}
    with db() as conn:
        row = conn.execute('SELECT * FROM opportunities WHERE id=?', (oid,)).fetchone()
        if not row: return jsonify({'error':'not_found'}), 404
    actor = str(body.get('actor') or request.headers.get('X-NOIOP-Actor','decision-owner'))
    decision = str(body.get('decision','REVIEW')).upper()
    rationale = str(body.get('rationale',''))
    assessment = assess(dict(row)); did = str(uuid.uuid4()); created = utc_now()
    with db() as conn:
        conn.execute('INSERT INTO decisions(id,opportunity_id,actor,decision,rationale,assessment_hash,created_at) VALUES(?,?,?,?,?,?,?)',
                     (did, oid, actor, decision, rationale, assessment['evidence_hash'], created))
        conn.execute('UPDATE opportunities SET status=?, updated_at=? WHERE id=?', (decision, created, oid))
    payload = {'id':did,'opportunity_id':oid,'actor':actor,'decision':decision,'rationale':rationale,'assessment_hash':assessment['evidence_hash'],'created_at':created}
    audit('HUMAN_DECISION_RECORDED', oid, actor, payload)
    return jsonify(payload), 201


@app.get('/api/v1/opportunities/<oid>/decisions')
def list_decisions(oid: str):
    with db() as conn:
        rows = conn.execute('SELECT * FROM decisions WHERE opportunity_id=? ORDER BY created_at DESC', (oid,)).fetchall()
    return jsonify({'count':len(rows),'items':[dict(r) for r in rows]})


@app.post('/api/v1/opportunities/<oid>/value-events')
def record_value_event(oid: str):
    body = request.get_json(force=True) or {}; payload = dict(body); payload['opportunity_id'] = oid
    result = value_realization(payload); vid = str(uuid.uuid4()); created = utc_now()
    with db() as conn:
        exists = conn.execute('SELECT id FROM opportunities WHERE id=?',(oid,)).fetchone()
        if not exists: return jsonify({'error':'not_found'}),404
        conn.execute('INSERT INTO value_events(id,opportunity_id,expected_value,realized_value,currency,created_at) VALUES(?,?,?,?,?,?)',
                     (vid, oid, result['expected_value'], result['realized_value'], result['currency'], created))
    result.update({'id':vid,'created_at':created})
    audit('VALUE_REALIZATION_RECORDED', oid, request.headers.get('X-NOIOP-Actor','public-demo-user'), result)
    return jsonify(result), 201


@app.get('/api/v1/opportunities/<oid>/audit')
def opportunity_audit(oid: str):
    with db() as conn:
        rows = conn.execute('SELECT seq,event_id,event_type,entity_id,actor,payload_json,event_hash,created_at FROM audit_log WHERE entity_id=? ORDER BY seq DESC', (oid,)).fetchall()
    items=[]
    for r in rows:
        d=dict(r); d['payload']=json.loads(d.pop('payload_json')); items.append(d)
    return jsonify({'count':len(items),'items':items})


@app.post('/api/v1/assess')
def assess_api():
    return jsonify(assess(request.get_json(force=True) or {}))


@app.post('/api/v1/portfolio')
def portfolio_api():
    body = request.get_json(force=True) or {}
    return jsonify(portfolio(body.get('opportunities', [])))


@app.get('/api/v1/portfolio/live')
def live_portfolio_api():
    with db() as conn:
        rows=conn.execute('SELECT * FROM opportunities ORDER BY updated_at DESC').fetchall()
    return jsonify(portfolio([dict(r) for r in rows]))


@app.post('/api/v1/decision-trace')
def decision_trace_api():
    return jsonify(decision_trace(request.get_json(force=True) or {}))


@app.post('/api/v1/value-realization')
def value_realization_api():
    return jsonify(value_realization(request.get_json(force=True) or {}))


@app.get('/api/v1/public-evidence')
def public_evidence_api():
    evidence = {
        'release': 'NOIOP-MVP-Operational/full-stack-2.0',
        'capabilities': ['persistent-opportunity-workspace','assessment','portfolio-ranking','decision-trace','human-decision-record','value-realization','audit-log'],
        'sensitive_ip_exposed': False,
        'material_execution_authority': False,
        'public_demo_boundary': PUBLIC_BOUNDARY,
    }
    evidence['evidence_hash'] = canonical_hash(evidence)
    return jsonify(evidence)


init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT','8080')))
