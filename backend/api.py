from __future__ import annotations

import os
import subprocess
import sys
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

REPO_ROOT = os.getenv("CBP_REPO_ROOT", "/app")

@app.get("/health")
def health():
    return {"ok": True}

class RunScriptReq(BaseModel):
    script: str               # e.g. "scripts/preflight_check.py"
    args: list[str] = []      # e.g. ["--exchange", "coinbase"]
    timeout_s: int = 60

@app.post("/run_script")
def run_script(req: RunScriptReq):
    script_path = os.path.join(REPO_ROOT, req.script)
    if not os.path.exists(script_path):
        raise HTTPException(status_code=404, detail=f"missing script: {req.script}")

    try:
        cp = subprocess.run(
            [sys.executable, script_path, *req.args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=req.timeout_s,
            check=False,
        )
        return {
            "ok": cp.returncode == 0,
            "returncode": cp.returncode,
            "stdout": cp.stdout or "",
            "stderr": cp.stderr or "",
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="timeout")
