"""Validate literature-discovery checkpoint safety and audit coverage."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
DISCOVERY=str(ROOT/"scripts/discovery")
if DISCOVERY not in sys.path:sys.path.insert(0,DISCOVERY)
from discovery_coverage import validate_repository

if __name__=="__main__":
    try:
        report=validate_repository(ROOT)
        q=report["candidateQueue"]
        print(
            "PASS: discovery coverage policy valid; "
            f"{report['completeAudits']}/{report['audits']} v2 audits complete; "
            f"candidate queue selected={q['selected']} deferred={q['deferred']} "
            f"excluded={q['excluded']} duplicate={q['duplicate']}; "
            f"checkpoint={report['lastSuccessfulSearchAt']}."
        )
    except (ValueError,KeyError,TypeError,OSError) as exc:
        print("FAIL:",exc,file=sys.stderr);raise SystemExit(1)
