"""Offline regression checks, not a GitHub runner or full Actions validator."""

from __future__ import annotations

import ast
import itertools
import re
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
WIN_CERT = (
    "secrets.WIN_CERTIFICATE_BASE64 != '' && secrets.WIN_CERT_PASSWORD != '' && "
    "(secrets.WIN_CERT_SHA1 != '' || secrets.WIN_CERT_NAME != '')"
)
MAC_CERT = (
    "secrets.MAC_CERT_P12_BASE64 != '' && secrets.MAC_CERT_PASSWORD != '' && "
    "secrets.MAC_KEYCHAIN_PASSWORD != ''"
)
MAC_NOTARY = (
    "secrets.MAC_APPLE_ID != '' && secrets.MAC_APP_PASSWORD != '' && "
    "secrets.MAC_TEAM_ID != ''"
)
WINDOWS = {"WINDOWS_SIGNING_AVAILABLE": (WIN_CERT, 2, None)}
MACOS = {
    "MAC_CERT_AVAILABLE": (MAC_CERT, 1, None),
    "MAC_SIGNING_AVAILABLE": (MAC_CERT + " && secrets.MAC_SIGN_IDENTITY != ''", 1, None),
    "MAC_NOTARY_AVAILABLE": (MAC_NOTARY, 3, None),
}
MATRIX = {
    "WINDOWS_SIGNING_AVAILABLE": (
        "secrets.WIN_SIGN_PFX_B64 != '' && secrets.WIN_SIGN_PFX_PASSWORD != ''",
        1,
        "Windows",
    ),
    "MAC_SIGNING_AVAILABLE": (
        "secrets.MAC_SIGN_P12_B64 != '' && secrets.MAC_SIGN_P12_PASSWORD != '' && "
        "secrets.APPLE_ID != '' && secrets.APPLE_APP_PASSWORD != '' && "
        "secrets.APPLE_TEAM_ID != ''",
        1,
        "macOS",
    ),
}
CASES = [
    ("release-publish.yml", "build_windows", WINDOWS),
    ("release-publish.yml", "build_macos", MACOS),
    ("ci-signing.yml", "windows_sign_pyinstaller", WINDOWS),
    ("ci-signing.yml", "macos_codesign_and_notarize_briefcase", MACOS),
    ("build-desktop-app.yml", "build", MATRIX),
    ("release-desktop-app.yml", "build", MATRIX),
]
FILES = sorted({case[0] for case in CASES})


def load_workflow(name):
    # BaseLoader retains the Actions 'on' key rather than YAML 1.1's boolean True.
    return yaml.load((ROOT / ".github/workflows" / name).read_text(), Loader=yaml.BaseLoader)


def expression(body):
    return "${{ " + body + " }}"


def evaluate_subset(value, contexts):
    """Evaluate only this fixture's string comparisons and boolean operators."""
    assert value.startswith("${{ ") and value.endswith(" }}")
    body = value[4:-3].replace("&&", " and ").replace("||", " or ")

    def visit(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            return contexts[node.value.id].get(node.attr, "")
        if isinstance(node, ast.BoolOp) and isinstance(node.op, (ast.And, ast.Or)):
            values = [visit(child) for child in node.values]
            return all(values) if isinstance(node.op, ast.And) else any(values)
        if isinstance(node, ast.Compare) and len(node.ops) == 1:
            left, right = visit(node.left), visit(node.comparators[0])
            if isinstance(node.ops[0], ast.Eq):
                return left == right
            if isinstance(node.ops[0], ast.NotEq):
                return left != right
        raise AssertionError(f"Outside regression-expression subset: {ast.dump(node)}")

    return visit(ast.parse(body, mode="eval").body)


@pytest.mark.parametrize("filename", FILES)
def test_step_conditions_do_not_reference_secrets(filename):
    for job in load_workflow(filename)["jobs"].values():
        for step in job["steps"]:
            assert not re.search(r"\bsecrets\b", step.get("if", "")), step.get("name")


@pytest.mark.parametrize("filename,job_name,gates", CASES)
def test_exact_availability_predicates_and_os_guards(filename, job_name, gates):
    job = load_workflow(filename)["jobs"][job_name]
    assert job.get("env") == {name: expression(rule) for name, (rule, _, _) in gates.items()}
    for name, (_, count, os_name) in gates.items():
        guard = f"env.{name} == 'true'"
        if os_name:
            guard = f"runner.os == '{os_name}' && " + guard
        assert sum(step.get("if") == expression(guard) for step in job["steps"]) == count


@pytest.mark.parametrize("filename,job_name,gates", CASES)
def test_all_secret_presence_combinations_preserve_decisions(filename, job_name, gates):
    job = load_workflow(filename)["jobs"][job_name]
    flags = job.get("env", {})
    assert set(flags) == set(gates)
    names = sorted(set(re.findall(r"secrets\.(\w+)", " ".join(rule for rule, _, _ in gates.values()))))
    for present in itertools.product((False, True), repeat=len(names)):
        # Include a literal 'false' secret: presence, not its truthiness, is the rule.
        secrets = {name: "false" for name, enabled in zip(names, present) if enabled}
        env = {
            name: str(evaluate_subset(value, {"secrets": secrets})).lower()
            for name, value in flags.items()
        }
        for os_name in ("Windows", "macOS", "Linux"):
            contexts = {"secrets": secrets, "env": env, "runner": {"os": os_name}}
            for name, (rule, count, required_os) in gates.items():
                matching = [step for step in job["steps"] if f"env.{name} " in step.get("if", "")]
                assert len(matching) == count
                original = f"runner.os == '{required_os}' && {rule}" if required_os else rule
                expected = evaluate_subset(expression(original), contexts)
                for step in matching:
                    assert evaluate_subset(step["if"], contexts) == expected
