from app import app, assess, portfolio, decision_trace, value_realization


def test_health():
    client = app.test_client()
    response = client.get('/health')
    assert response.status_code == 200
    body = response.get_json()
    assert body['status'] == 'ok'
    assert body['service'] == 'noiop-operational-mvp'
    assert body['version'] == '2.0.1-mvp'
    assert body['database_ready'] is True
    assert isinstance(body['persistent_store'], bool)


def test_priority_candidate():
    out = assess({
        'opportunity_id': 'T-1', 'tenant_id': 'A', 'title': 'Industrial AI',
        'demand': .95, 'strategic_alignment': .94, 'readiness': .86,
        'risk_inverse': .78, 'evidence_quality': .93, 'timing': .90,
    })
    assert out['decision'] == 'PRIORITY_CANDIDATE'
    assert out['material_execution_authority'] is False
    assert len(out['evidence_hash']) == 64


def test_abstain_on_weak_evidence():
    out = assess({'demand': .95, 'strategic_alignment': .94, 'readiness': .86,
                  'risk_inverse': .78, 'evidence_quality': .30, 'timing': .90})
    assert out['decision'] == 'ABSTAIN'
    assert out['human_approval_required'] is False


def test_abstain_on_low_readiness():
    out = assess({'demand': .95, 'strategic_alignment': .94, 'readiness': .20,
                  'risk_inverse': .78, 'evidence_quality': .95, 'timing': .90})
    assert out['decision'] == 'ABSTAIN'


def test_score_is_bounded():
    out = assess({'demand': 5, 'strategic_alignment': 5, 'readiness': 5,
                  'risk_inverse': 5, 'evidence_quality': 5, 'timing': 5})
    assert out['score'] == 100.0


def test_portfolio_is_ranked_descending():
    p = portfolio([
        {'opportunity_id':'A','title':'A','demand':.5,'strategic_alignment':.5,'readiness':.6,'risk_inverse':.5,'evidence_quality':.8,'timing':.5},
        {'opportunity_id':'B','title':'B','demand':.9,'strategic_alignment':.9,'readiness':.8,'risk_inverse':.8,'evidence_quality':.9,'timing':.9},
    ])
    assert p['opportunity_count'] == 2
    assert p['ranked_opportunities'][0]['opportunity_id'] == 'B'
    assert len(p['portfolio_hash']) == 64


def test_portfolio_preserves_tenant_identity():
    p = portfolio([
        {'opportunity_id':'A','tenant_id':'ENTITY-A','title':'A','demand':.8,'strategic_alignment':.8,'readiness':.7,'risk_inverse':.7,'evidence_quality':.8,'timing':.8},
        {'opportunity_id':'B','tenant_id':'ENTITY-B','title':'B','demand':.8,'strategic_alignment':.8,'readiness':.7,'risk_inverse':.7,'evidence_quality':.8,'timing':.8},
    ])
    assert {x['tenant_id'] for x in p['ranked_opportunities']} == {'ENTITY-A','ENTITY-B'}


def test_decision_trace_ends_in_human_authority_for_actionable_case():
    t = decision_trace({'opportunity_id':'T','demand':.9,'strategic_alignment':.9,'readiness':.8,
                        'risk_inverse':.8,'evidence_quality':.9,'timing':.9})
    assert t['stages'][-1]['state'] == 'HUMAN_APPROVAL_REQUIRED'
    assert t['material_execution_authority'] is False
    assert len(t['trace_hash']) == 64


def test_decision_trace_abstains_on_evidence_gate():
    t = decision_trace({'opportunity_id':'T','demand':.9,'strategic_alignment':.9,'readiness':.8,
                        'risk_inverse':.8,'evidence_quality':.2,'timing':.9})
    evidence_stage = [x for x in t['stages'] if x['stage'] == 'EVIDENCE_GATE'][0]
    assert evidence_stage['state'] == 'ABSTAIN'


def test_value_realization_partial():
    v = value_realization({'opportunity_id':'V','expected_value':100,'realized_value':70})
    assert v['state'] == 'PARTIAL_REALIZATION'
    assert v['realization_ratio'] == .7
    assert v['financial_outcome_guarantee'] is False


def test_value_realization_on_target():
    v = value_realization({'expected_value':100,'realized_value':110})
    assert v['state'] == 'ON_OR_ABOVE_TARGET'


def test_demo_portfolio_endpoint():
    client = app.test_client()
    response = client.get('/api/v1/demo/portfolio')
    assert response.status_code == 200
    body = response.get_json()
    assert body['opportunity_count'] == 4
    assert body['decision_counts']['ABSTAIN'] == 1


def test_public_evidence_endpoint_has_nonclaims():
    client = app.test_client()
    body = client.get('/api/v1/public-evidence').get_json()
    assert body['sensitive_ip_exposed'] is False
    assert body['material_execution_authority'] is False
    assert len(body['evidence_hash']) == 64
