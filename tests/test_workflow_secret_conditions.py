import re
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ["build-desktop-app.yml", "release-desktop-app.yml",
             "ci-signing.yml", "release-publish.yml"]
PFX_WIN = "secrets.WIN_SIGN_PFX_B64 != '' && secrets.WIN_SIGN_PFX_PASSWORD != ''"
PFX_MAC = "secrets.MAC_SIGN_P12_B64 != '' && secrets.MAC_SIGN_P12_PASSWORD != '' && secrets.APPLE_ID != '' && secrets.APPLE_APP_PASSWORD != '' && secrets.APPLE_TEAM_ID != ''"
CERT_WIN = "secrets.WIN_CERTIFICATE_BASE64 != '' && secrets.WIN_CERT_PASSWORD != '' && (secrets.WIN_CERT_SHA1 != '' || secrets.WIN_CERT_NAME != '')"
CERT_MAC = "secrets.MAC_CERT_P12_BASE64 != '' && secrets.MAC_CERT_PASSWORD != '' && secrets.MAC_KEYCHAIN_PASSWORD != ''"
IDENTITY_MAC = CERT_MAC + " && secrets.MAC_SIGN_IDENTITY != ''"
NOTARY_MAC = "secrets.MAC_APPLE_ID != '' && secrets.MAC_APP_PASSWORD != '' && secrets.MAC_TEAM_ID != ''"


@pytest.mark.parametrize("name", WORKFLOWS)
def test_secret_condition_rewrite_preserves_signing_requirements(name):
    path = f".github/workflows/{name}"
    after = yaml.load((ROOT / path).read_text(), Loader=yaml.BaseLoader)
    rewrites = 0
    for key, job in after["jobs"].items():
        flags = job.get("env", {})
        if key in {"release", "publish_release"}:
            assert not flags
            continue
        if name in {"build-desktop-app.yml", "release-desktop-app.yml"}:
            expected = {"WIN_SIGNING_READY": PFX_WIN, "MAC_SIGNING_READY": PFX_MAC}
        elif "windows" in key:
            expected = {"WIN_SIGNING_READY": CERT_WIN}
        else:
            expected = {"MAC_CERT_READY": CERT_MAC, "MAC_SIGNING_READY": IDENTITY_MAC,
                        "MAC_NOTARY_READY": NOTARY_MAC}
        assert flags == {flag: "${{ " + predicate + " }}" for flag, predicate in expected.items()}
        for step in job.get("steps", []):
            condition = step.get("if", "")
            assert "secrets." not in condition
            for flag, expression in flags.items():
                assert flag not in step.get("env", {}), "Step must not override readiness"
                reference = f"env.{flag} == 'true'"
                if reference in condition:
                    rewrites += 1
                    if name in {"build-desktop-app.yml", "release-desktop-app.yml"}:
                        platform = "Windows" if flag.startswith("WIN") else "macOS"
                        assert condition == "${{ runner.os == '" + platform + "' && " + reference + " }}"
                    else:
                        assert condition == "${{ " + reference + " }}"
    assert rewrites > 0


@pytest.mark.parametrize("name", WORKFLOWS)
def test_readiness_flags_do_not_export_secret_values(name):
    workflow = yaml.load((ROOT / ".github/workflows" / name).read_text(), Loader=yaml.BaseLoader)
    for job in workflow["jobs"].values():
        flags = job.get("env", {})
        used = set()
        for flag, expression in flags.items():
            # Only presence comparisons and boolean connectors, never a raw value.
            residue = re.sub(r"secrets\.[A-Z0-9_]+ != ''", "", expression[4:-3])
            assert not re.sub(r"[\s()&|]", "", residue)
        for step in job.get("steps", []):
            for flag in re.findall(r"env\.([A-Z_]+_READY)", step.get("if", "")):
                assert flag in flags
                used.add(flag)
        assert used == set(flags)
