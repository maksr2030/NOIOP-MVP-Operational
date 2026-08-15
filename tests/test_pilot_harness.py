import unittest
from pilot_harness.run_pilot import SCENARIOS, execute, expected_pass, digest

class PilotHarnessTests(unittest.TestCase):
    def test_all_defined_scenarios_meet_expected_control_behavior(self):
        self.assertEqual(len(SCENARIOS), 10)
        for sid, _, data in SCENARIOS:
            result = execute(sid, data)
            self.assertTrue(expected_pass(sid, result), sid)
            self.assertTrue(result.get("traceable"), sid)

    def test_authority_boundary_blocks_operator_final_decision(self):
        result = execute("PTS-006", {"requested_action":"final_consequential_decision","authority":"operator"})
        self.assertEqual(result["status"], "BLOCKED_AND_ESCALATED")
        self.assertFalse(result["unauthorized_final_decision"])

    def test_incomplete_evidence_is_not_fabricated(self):
        result = execute("PTS-002", {"evidence":[]})
        self.assertEqual(result["status"], "NEEDS_EVIDENCE")
        self.assertFalse(result["fabricated"])

    def test_hash_is_reproducible(self):
        self.assertEqual(digest({"b":2,"a":1}), digest({"a":1,"b":2}))

if __name__ == "__main__":
    unittest.main()
