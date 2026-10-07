from pathlib import Path
import runpy

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("filename", ["build-desktop-app.yml", "release-desktop-app.yml"])
def test_desktop_workflow_uses_supported_build_and_existing_helpers(filename):
    workflow = yaml.safe_load((ROOT / ".github/workflows" / filename).read_text())
    steps = workflow["jobs"]["build"]["steps"]
    build = next(step for step in steps if step.get("name") == "Build app (PyInstaller)")
    assert build["run"].strip() == "python packaging/pyinstaller/build.py"
    assert build["env"]["CBP_WINDOWED"] == "1"
    for path in (
        "packaging/pyinstaller/build.py",
        "scripts/release/ci/sign_windows.ps1",
        "scripts/release/ci/sign_macos.sh",
        "scripts/release/ci/package_dist.py",
    ):
        assert (ROOT / path).is_file()
        assert any(path in step.get("run", "") for step in steps)


def test_package_helper_uses_repository_dist():
    namespace = runpy.run_path(str(ROOT / "scripts/release/ci/package_dist.py"))
    assert namespace["REPO"] == ROOT
    assert namespace["DIST"] == ROOT / "dist"
    assert namespace["OUT"] == ROOT / "dist_artifacts"


def test_release_glob_matches_downloaded_artifact_layout(tmp_path):
    workflow = yaml.safe_load((ROOT / ".github/workflows/release-desktop-app.yml").read_text())
    release_steps = workflow["jobs"]["release"]["steps"]
    download = next(step for step in release_steps if step.get("uses", "").startswith("actions/download-artifact@"))
    publish = next(step for step in release_steps if step.get("uses", "").startswith("softprops/action-gh-release@"))
    artifact = tmp_path / download["with"]["path"] / "CryptoBotPro-macos-latest" / "app.zip"
    artifact.parent.mkdir(parents=True)
    artifact.write_bytes(b"fixture")
    assert list(tmp_path.glob(publish["with"]["files"].strip())) == [artifact]
