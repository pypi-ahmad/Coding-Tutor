"""Tests for app configuration and core module imports."""
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "module_name",
    [
        "app",
        "coding_tutor",
        "coding_tutor.ui",
        "coding_tutor.providers",
        "coding_tutor.database",
        "coding_tutor.dataset",
        "coding_tutor.generation",
        "coding_tutor.evaluation",
        "coding_tutor.quiz",
    ],
)
def test_core_modules_import(module_name):
    result = subprocess.run(
        [sys.executable, "-c", f"import {module_name}"],
        cwd=ROOT,
        check=False,
    )
    assert result.returncode == 0, f"Could not import {module_name}"


def test_env_example_contains_only_blank_supported_variables():
    variables = {}
    for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            name, value = line.split("=", 1)
            variables[name] = value

    assert variables == {
        "OPENAI_API_KEY": "",
        "OPENAI_BASE_URL": "",
        "AGNES_API_KEY": "",
        "GOOGLE_API_KEY": "",
    }


@pytest.mark.parametrize(
    "path",
    [
        ".env",
        ".env.local",
        ".streamlit/secrets.toml",
        "progress.duckdb",
        "runner_tmp/job.tmp",
        ".ruff_cache/cache",
        ".coverage.worker",
        "app.log",
    ],
)
def test_local_artifacts_are_gitignored(path):
    result = subprocess.run(
        ["git", "check-ignore", "--quiet", "--no-index", path],
        cwd=ROOT,
        check=False,
    )
    assert result.returncode == 0, f"{path} must be ignored"


def test_env_example_is_not_gitignored():
    result = subprocess.run(
        ["git", "check-ignore", "--quiet", "--no-index", ".env.example"],
        cwd=ROOT,
        check=False,
    )
    assert result.returncode == 1


def test_all_model_options_have_required_fields():
    from coding_tutor.providers.config import ALL_MODELS
    for model in ALL_MODELS:
        assert model.provider, f"Missing provider for {model}"
        assert model.model_id, f"Missing model_id for {model}"
        assert model.display_name, f"Missing display_name for {model}"
        assert model.documentation_url, f"Missing documentation URL for {model}"
        if not model.verified:
            assert model.unverified_reason, f"Unverified model {model.model_id} must have a reason"


def test_agnes_model_is_verified():
    from coding_tutor.providers.config import AGNES_MODELS
    assert len(AGNES_MODELS) == 1
    assert AGNES_MODELS[0].model_id == "agnes-2.5-flash"
    assert AGNES_MODELS[0].verified is True


def test_openai_model_is_verified():
    from coding_tutor.providers.config import OPENAI_MODELS

    assert len(OPENAI_MODELS) == 1
    model = OPENAI_MODELS[0]
    assert model.model_id == "gpt-5.6-luna"
    assert model.verified is True
    assert model.extra_params == {"reasoning_effort": "medium"}
    assert model.documentation_url.startswith("https://developers.openai.com/")


def test_gemini_model_verification_matches_official_documentation():
    from coding_tutor.providers.config import GEMINI_MODELS

    models = {model.model_id: model for model in GEMINI_MODELS}
    assert set(models) == {"gemini-3.5-flash-lite", "gemini-3.7-flash"}
    assert models["gemini-3.5-flash-lite"].verified is True
    assert models["gemini-3.7-flash"].verified is True
    assert all(
        model.extra_params == {"thinking_level": "medium"}
        for model in models.values()
    )
    assert models["gemini-3.7-flash"].documentation_url == (
        "https://ai.google.dev/gemini-api/docs/thinking"
    )


def test_streamlit_config_exists():
    import tomllib

    config_path = ROOT / ".streamlit" / "config.toml"
    assert config_path.exists(), ".streamlit/config.toml must exist"
    with config_path.open("rb") as f:
        cfg = tomllib.load(f)
    assert cfg["server"]["port"] == 8551
    assert cfg["server"]["address"] == "127.0.0.1"


def test_windows_launcher_bootstraps_root_venv_and_starts_app():
    launcher = (ROOT / "launch_app.cmd").read_text(encoding="utf-8")

    assert 'cd /d "%~dp0"' in launcher
    assert "https://astral.sh/uv/install.ps1" in launcher
    assert 'set "UV_PROJECT_ENVIRONMENT=%CD%\\.venv"' in launcher
    assert 'call "%UV_EXE%" sync --locked' in launcher
    assert (
        'call "%UV_EXE%" run --locked streamlit run app.py '
        "--server.address 127.0.0.1 --server.port 8551"
    ) in launcher
    assert all(
        secret_name not in launcher
        for secret_name in (
            "OPENAI_API_KEY",
            "OPENAI_BASE_URL",
            "AGNES_API_KEY",
            "GOOGLE_API_KEY",
        )
    )


@pytest.mark.skipif(sys.platform != "win32", reason="Windows launcher test")
def test_windows_launcher_runs_expected_uv_commands(tmp_path):
    log_path = tmp_path / "uv-commands.log"
    fake_uv = tmp_path / "uv.cmd"
    fake_uv.write_text(
        "@echo off\n"
        '>>"%UV_LAUNCH_LOG%" echo ARGS:%*\n'
        '>>"%UV_LAUNCH_LOG%" echo VENV:%UV_PROJECT_ENVIRONMENT%\n'
        "exit /b 0\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}{os.pathsep}{env['PATH']}"
    env["UV_LAUNCH_LOG"] = str(log_path)

    result = subprocess.run(
        ["cmd.exe", "/d", "/c", str(ROOT / "launch_app.cmd")],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    log = log_path.read_text(encoding="utf-8")
    assert "ARGS:sync --locked" in log
    assert (
        "ARGS:run --locked streamlit run app.py "
        "--server.address 127.0.0.1 --server.port 8551"
    ) in log
    assert f"VENV:{ROOT}\\.venv" in log
