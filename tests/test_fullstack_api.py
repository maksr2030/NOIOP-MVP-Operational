import os
import tempfile
import unittest

fd, path = tempfile.mkstemp(prefix='noiop-test-', suffix='.db')
os.close(fd)
os.environ['NOIOP_DB_PATH'] = path

import app as noiop


class FullStackApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = noiop.app.test_client()

    def test_health_reports_database_ready(self):
        r = self.client.get('/health')
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertTrue(data['database_ready'])
        self.assertEqual(data['status'], 'ok')
        self.assertIn('persistent_store', data)

    def test_create_assess_decide_audit_value_lifecycle(self):
        payload = {
            'tenant_id':'TEST-ENTITY','title':'Full-stack lifecycle','description':'test',
            'demand':.9,'strategic_alignment':.9,'readiness':.8,'risk_inverse':.7,'evidence_quality':.9,'timing':.8
        }
        create = self.client.post('/api/v1/opportunities', json=payload, headers={'X-NOIOP-Actor':'tester'})
        self.assertEqual(create.status_code, 201)
        oid = create.get_json()['id']

        get = self.client.get(f'/api/v1/opportunities/{oid}')
        self.assertEqual(get.status_code, 200)
        self.assertIn('assessment', get.get_json())
        self.assertIn('decision_trace', get.get_json())

        assessment = self.client.post(f'/api/v1/opportunities/{oid}/assess', json={})
        self.assertEqual(assessment.status_code, 200)
        self.assertTrue(assessment.get_json()['human_approval_required'])

        decision = self.client.post(
            f'/api/v1/opportunities/{oid}/decisions',
            json={'actor':'decision-owner','decision':'APPROVE','rationale':'controlled approval'}
        )
        self.assertEqual(decision.status_code, 201)
        self.assertEqual(decision.get_json()['decision'], 'APPROVE')

        value = self.client.post(
            f'/api/v1/opportunities/{oid}/value-events',
            json={'expected_value':100,'realized_value':80,'currency':'SAR'}
        )
        self.assertEqual(value.status_code, 201)
        self.assertEqual(value.get_json()['state'], 'PARTIAL_REALIZATION')

        audit = self.client.get(f'/api/v1/opportunities/{oid}/audit')
        self.assertEqual(audit.status_code, 200)
        types = {x['event_type'] for x in audit.get_json()['items']}
        self.assertIn('OPPORTUNITY_CREATED', types)
        self.assertIn('ASSESSMENT_GENERATED', types)
        self.assertIn('HUMAN_DECISION_RECORDED', types)
        self.assertIn('VALUE_REALIZATION_RECORDED', types)

    def test_low_evidence_abstains(self):
        r = self.client.post('/api/v1/assess', json={
            'readiness':.9,'evidence_quality':.2,'demand':1,
            'strategic_alignment':1,'risk_inverse':1,'timing':1
        })
        self.assertEqual(r.get_json()['decision'], 'ABSTAIN')


if __name__ == '__main__':
    unittest.main()
