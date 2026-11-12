"""Run the new atomicity tests against saved pre-R12 storage, in this process only."""
from pathlib import Path
import sys
import os

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import pytest
from storage import paper_trading_sqlite as store

baseline = Path(os.environ.get("CBP_R12_STORAGE_BASELINE") or
                Path(__file__).with_name("storage__paper_trading_sqlite.py.before"))
exec(compile(baseline.read_bytes(), str(baseline), "exec"), store.__dict__)
args = [
    "-q", "-p", "no:cacheprovider", str(ROOT / "tests/test_paper_exit_atomicity.py"),
    "--tb=no", "--junitxml=" + str(os.environ.get("CBP_R12_STORAGE_XML") or
                                  Path(__file__).with_name("storage.before.xml")),
]
if os.environ.get("CBP_R12_STORAGE_SELECTION"):
    args += ["-k", os.environ["CBP_R12_STORAGE_SELECTION"]]
result = pytest.main(args)
print("EXPECTED_BASELINE_PYTEST_EXIT", int(result))
assert result == 1, "Saved baseline must fail the new atomicity regression suite"
