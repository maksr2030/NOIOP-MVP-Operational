from __future__ import annotations

from hashlib import sha256
import json
from typing import Dict, Any, List

from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder='.')

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


def clamp(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


def canonical_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    return sha256(raw).hexdigest()


def assess(payload: Dict[str, Any]) -> Dict[str, Any]:
    signals = {
        'demand': clamp(payload.get('demand', 0)),
        'strategic_alignment': clamp(payload.get('strategic_alignment', 0)),
        'readiness': clamp(payload.get('readiness', 0)),
        'risk_inverse': clamp(payload.get('risk_inverse', 0)),
        'evidence_quality': clamp(payload.get('evidence_quality', 0)),
        'timing': clamp(payload.get('timing', 0)),
    }
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
        'engine': 'NOIOP Public MVP Assessment Engine',
        'engine_version': '1.1.0-public',
        'opportunity_id': str(payload.get('opportunity_id', 'PUBLIC-DEMO')),
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
        'engine': 'NOIOP Public Portfolio Engine',
        'engine_version': '1.1.0-public',
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
        'engine': 'NOIOP Public Value Realization Engine',
        'engine_version': '1.1.0-public',
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


DEMO_RECORDS = [
    {'opportunity_id': 'DEMO-001', 'tenant_id': 'ENTITY-A', 'title': 'Industrial AI Energy Optimization', 'demand': .92, 'strategic_alignment': .90, 'readiness': .80, 'risk_inverse': .74, 'evidence_quality': .93, 'timing': .86},
    {'opportunity_id': 'DEMO-002', 'tenant_id': 'ENTITY-A', 'title': 'Smart Logistics Route Intelligence', 'demand': .84, 'strategic_alignment': .82, 'readiness': .71, 'risk_inverse': .70, 'evidence_quality': .86, 'timing': .78},
    {'opportunity_id': 'DEMO-101', 'tenant_id': 'ENTITY-B', 'title': 'Water Infrastructure Predictive Optimization', 'demand': .88, 'strategic_alignment': .87, 'readiness': .76, 'risk_inverse': .72, 'evidence_quality': .90, 'timing': .81},
    {'opportunity_id': 'DEMO-102', 'tenant_id': 'ENTITY-B', 'title': 'Low-Evidence Demonstration Case', 'demand': .94, 'strategic_alignment': .91, 'readiness': .70, 'risk_inverse': .75, 'evidence_quality': .32, 'timing': .90},
]


@app.get('/')
def home():
    return send_from_directory('.', 'index.html')


@app.get('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'noiop-public-mvp', 'version': '1.1.0-public'})


@app.post('/api/v1/assess')
def assess_api():
    return jsonify(assess(request.get_json(force=True) or {}))


@app.post('/api/v1/portfolio')
def portfolio_api():
    body = request.get_json(force=True) or {}
    return jsonify(portfolio(body.get('opportunities', [])))


@app.get('/api/v1/demo/portfolio')
def demo_portfolio_api():
    return jsonify(portfolio(DEMO_RECORDS))


@app.post('/api/v1/decision-trace')
def decision_trace_api():
    return jsonify(decision_trace(request.get_json(force=True) or {}))


@app.post('/api/v1/value-realization')
def value_realization_api():
    return jsonify(value_realization(request.get_json(force=True) or {}))


@app.get('/api/v1/public-evidence')
def public_evidence_api():
    evidence = {
        'release': 'NOIOP-MVP-Operational/public-1.1',
        'capabilities': ['assessment', 'portfolio-ranking', 'decision-trace', 'value-realization', 'multi-entity-demo'],
        'sensitive_ip_exposed': False,
        'material_execution_authority': False,
        'public_demo_boundary': PUBLIC_BOUNDARY,
    }
    evidence['evidence_hash'] = canonical_hash(evidence)
    return jsonify(evidence)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
