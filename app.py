from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
import json
from typing import Dict, Any

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


def clamp(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


def canonical_hash(payload: Dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')
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
        'engine_version': '1.0.0-public',
        'opportunity_id': str(payload.get('opportunity_id', 'PUBLIC-DEMO')),
        'title': str(payload.get('title', 'Untitled Opportunity')),
        'signals': signals,
        'score': round(score, 2),
        'decision': decision,
        'material_execution_authority': False,
        'human_approval_required': decision != 'ABSTAIN',
        'public_demo_boundary': 'No production, pilot, regulatory, market-validation, or external-security certification claim.'
    }
    result['evidence_hash'] = canonical_hash(result)
    return result


@app.get('/')
def home():
    return send_from_directory('.', 'index.html')


@app.get('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'noiop-public-mvp', 'version': '1.0.0-public'})


@app.post('/api/v1/assess')
def assess_api():
    return jsonify(assess(request.get_json(force=True) or {}))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
