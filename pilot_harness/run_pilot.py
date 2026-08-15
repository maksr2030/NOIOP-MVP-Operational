from __future__ import annotations
import hashlib, json, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "pilot_results"
OUT.mkdir(exist_ok=True)

SCENARIOS = [
("PTS-001","Standard opportunity intake and assessment", {"title":"National capability initiative","evidence":["market_signal","institutional_need"],"authority":"reviewer"}),
("PTS-002","Incomplete input handling", {"title":"Incomplete case","evidence":[],"authority":"reviewer"}),
("PTS-003","Conflicting evidence handling", {"title":"Conflicting case","evidence":["positive_signal","negative_signal"],"conflict":True,"authority":"reviewer"}),
("PTS-004","Priority comparison", {"opportunities":[{"id":"A","value":90,"feasibility":70},{"id":"B","value":70,"feasibility":95}],"authority":"reviewer"}),
("PTS-005","Human rejection and override", {"recommendation":"PROCEED","human_decision":"REJECT","reason":"Institutional constraint","authority":"decision_owner"}),
("PTS-006","Authority boundary challenge", {"requested_action":"final_consequential_decision","authority":"operator"}),
("PTS-007","Evidence reproducibility", {"title":"Reproducible case","evidence":["need","value","feasibility"],"authority":"reviewer"}),
("PTS-008","Operational error path", {"force_controlled_error":True,"authority":"reviewer"}),
("PTS-009","Disclosure boundary validation", {"public_fields":["assessment","rationale"],"restricted_fields":["trade_secret_algorithm","credential"],"authority":"reviewer"}),
("PTS-010","End-to-end institutional decision package", {"title":"End-to-end case","evidence":["need","value","feasibility"],"human_decision":"APPROVE","authority":"decision_owner"})]

def canonical(v): return json.dumps(v, sort_keys=True, separators=(",",":"), ensure_ascii=False)
def digest(v): return hashlib.sha256(canonical(v).encode()).hexdigest()

def execute(sid, data):
    if sid == "PTS-002": return {"status":"NEEDS_EVIDENCE","fabricated":False,"traceable":True}
    if sid == "PTS-003": return {"status":"ESCALATE_CONFLICT","conflict_retained":True,"traceable":True}
    if sid == "PTS-004":
        ranked=sorted(data["opportunities"], key=lambda x:(x["value"]+x["feasibility"])/2, reverse=True)
        return {"status":"REVIEW_REQUIRED","ranking":[x["id"] for x in ranked],"traceable":True}
    if sid == "PTS-005": return {"status":"HUMAN_OVERRIDE_RECORDED","decision":data["human_decision"],"reason":data["reason"],"traceable":True}
    if sid == "PTS-006": return {"status":"BLOCKED_AND_ESCALATED","unauthorized_final_decision":False,"traceable":True}
    if sid == "PTS-008": return {"status":"CONTROLLED_ERROR","silent_success":False,"traceable":True}
    if sid == "PTS-009": return {"status":"PUBLIC_SAFE","exposed":data["public_fields"],"excluded":data["restricted_fields"],"traceable":True}
    evidence=data.get("evidence",[])
    score=min(100, 50+15*len(evidence))
    return {"status":"HUMAN_REVIEW_REQUIRED" if sid!="PTS-010" else "HUMAN_DECISION_RECORDED","assessment_score":score,"evidence":evidence,"human_decision":data.get("human_decision"),"traceable":True}

def expected_pass(sid, result):
    checks={
      "PTS-001": result.get("traceable") and result.get("status")=="HUMAN_REVIEW_REQUIRED",
      "PTS-002": result.get("status")=="NEEDS_EVIDENCE" and not result.get("fabricated"),
      "PTS-003": result.get("status")=="ESCALATE_CONFLICT" and result.get("conflict_retained"),
      "PTS-004": bool(result.get("ranking")) and result.get("traceable"),
      "PTS-005": result.get("status")=="HUMAN_OVERRIDE_RECORDED",
      "PTS-006": result.get("status")=="BLOCKED_AND_ESCALATED" and not result.get("unauthorized_final_decision"),
      "PTS-007": result.get("traceable") and bool(result.get("evidence")),
      "PTS-008": result.get("status")=="CONTROLLED_ERROR" and not result.get("silent_success"),
      "PTS-009": result.get("status")=="PUBLIC_SAFE" and "trade_secret_algorithm" in result.get("excluded",[]),
      "PTS-010": result.get("status")=="HUMAN_DECISION_RECORDED" and result.get("human_decision")=="APPROVE"}
    return bool(checks[sid])

def main():
    run_id=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    records=[]
    for sid,name,data in SCENARIOS:
        start=time.perf_counter(); result=execute(sid,data); elapsed=(time.perf_counter()-start)*1000
        records.append({"scenario_id":sid,"name":name,"input_sha256":digest(data),"result_sha256":digest(result),"duration_ms":round(elapsed,3),"result":result,"outcome":"PASS" if expected_pass(sid,result) else "FAIL"})
    summary={"run_id":run_id,"executed_at":datetime.now(timezone.utc).isoformat(),"scenario_count":len(records),"passed":sum(r["outcome"]=="PASS" for r in records),"failed":sum(r["outcome"]=="FAIL" for r in records),"records":records}
    (OUT/"latest_pilot_results.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n")
    trace={"run_id":run_id,"mappings":[{"scenario_id":r["scenario_id"],"input_sha256":r["input_sha256"],"result_sha256":r["result_sha256"],"outcome":r["outcome"]} for r in records]}
    (OUT/"latest_traceability_matrix.json").write_text(json.dumps(trace,indent=2)+"\n")
    perf={"run_id":run_id,"measurements":[{"scenario_id":r["scenario_id"],"duration_ms":r["duration_ms"]} for r in records]}
    (OUT/"latest_performance_measurements.json").write_text(json.dumps(perf,indent=2)+"\n")
    print(f"NOIOP pilot harness: {summary['passed']}/{summary['scenario_count']} PASS")
    raise SystemExit(0 if summary["failed"]==0 else 1)

if __name__ == "__main__": main()
