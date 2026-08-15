# NOIOP Pilot Execution Harness

This harness converts the ten controlled pilot scenarios into executable, reproducible checks.

Run locally:

python -m unittest tests.test_pilot_harness -v
python pilot_harness/run_pilot.py

Generated evidence is written to pilot_results/ and includes scenario results, SHA-256 traceability mappings and measured execution durations.

The harness validates controlled MVP behavior only. It does not claim that a real institution has completed or accepted a pilot. Institutional acceptance remains NOT TESTED until an authorized external pilot is executed and signed off under the Pilot Final Evaluation process.
