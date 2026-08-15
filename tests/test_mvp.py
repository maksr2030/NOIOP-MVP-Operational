from app import app, assess


def test_health():
    client = app.test_client()
    response = client.get('/health')
    assert response.status_code == 200
    assert response.get_json()['status'] == 'ok'


def test_priority_candidate():
    out = assess({
        'opportunity_id': 'T-1',
        'title': 'Industrial AI',
        'demand': .95,
        'strategic_alignment': .94,
        'readiness': .86,
        'risk_inverse': .78,
        'evidence_quality': .93,
        'timing': .90,
    })
    assert out['decision'] == 'PRIORITY_CANDIDATE'
    assert out['material_execution_authority'] is False
    assert len(out['evidence_hash']) == 64


def test_abstain_on_weak_evidence():
    out = assess({
        'demand': .95,
        'strategic_alignment': .94,
        'readiness': .86,
        'risk_inverse': .78,
        'evidence_quality': .30,
        'timing': .90,
    })
    assert out['decision'] == 'ABSTAIN'
    assert out['human_approval_required'] is False


def test_abstain_on_low_readiness():
    out = assess({
        'demand': .95,
        'strategic_alignment': .94,
        'readiness': .20,
        'risk_inverse': .78,
        'evidence_quality': .95,
        'timing': .90,
    })
    assert out['decision'] == 'ABSTAIN'


def test_score_is_bounded():
    out = assess({
        'demand': 5,
        'strategic_alignment': 5,
        'readiness': 5,
        'risk_inverse': 5,
        'evidence_quality': 5,
        'timing': 5,
    })
    assert out['score'] == 100.0
