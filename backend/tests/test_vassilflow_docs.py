"""Static coverage for VassilFlow documentation and runtime naming."""

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def _token(*codes: int) -> str:
    return "".join(chr(code) for code in codes)


FORBIDDEN_EXTERNAL_PRODUCT_TOKENS = (
    _token(68, 101, 101, 114),
    _token(68, 101, 101, 114, 70, 108, 111, 119),
    _token(100, 101, 101, 114, 102, 108, 111, 119),
    _token(100, 101, 101, 114, 45, 102, 108, 111, 119),
    _token(68, 69, 69, 82, 95, 70, 76, 79, 87),
    _token(68, 69, 69, 82, 70, 76, 79, 87),
    _token(46, 100, 101, 101, 114, 45, 102, 108, 111, 119),
    _token(66, 121, 116, 101, 68, 97, 110, 99, 101),
    _token(66, 121, 116, 101, 100, 97, 110, 99, 101),
    _token(98, 121, 116, 101, 100, 97, 110, 99, 101),
    _token(76, 97, 110, 103, 77, 97, 110, 117, 115),
    _token(108, 97, 110, 103, 109, 97, 110, 117, 115),
)


def test_core_docs_use_vassilflow_runtime_contracts():
    surfaces = {
        "backend/CLAUDE.md": [
            "VassilFlow is a LangGraph-based AI super agent system",
            "VASSILFLOW_CONFIG_PATH",
            "VassilFlowClient` provides direct in-process access",
            "vassilflow/          # Agent harness implementation package",
        ],
        "backend/docs/CONFIGURATION.md": [
            "Runtime variables use the `VASSILFLOW_*` names below.",
            "`VASSILFLOW_HOME` - Runtime state directory",
            "Set `VASSILFLOW_SANDBOX_BIND_HOST` explicitly",
        ],
        "backend/docs/SETUP.md": [
            "**Runtime variables**: Use `VASSILFLOW_*` variables for harness-specific settings.",
            "**Runtime data**: State defaults to `.vassilflow` under the project root.",
        ],
        "backend/docs/API.md": [
            "reference for the VassilFlow backend APIs",
            "Remove VassilFlow-managed local thread files",
            "`runtime_home` defaults to `.vassilflow`",
        ],
        "backend/docs/ARCHITECTURE.md": [
            "canonical architecture contract",
            "VassilFlow is a reusable agent harness",
            "default lead Agent, personal Agents, and delegated workers",
            "Its shipped registry is empty",
            "`assistant_id` is the authoritative external Agent identity",
            "`vassilflow.capabilities.AgentCapabilityAdapter`",
            "`vassilflow.actions` provides a generic append-only mutation journal",
            "`vassilflow.runtime.thread_lifecycle` defines domain-neutral deletion and branch",
            "`vassilflow.persistence.project_repository` is an operational contract",
        ],
    }

    for relative_path, expected_phrases in surfaces.items():
        content = _read(relative_path)
        for phrase in expected_phrases:
            assert phrase in content, f"{relative_path} missing {phrase!r}"


def test_docs_and_scripts_do_not_reintroduce_external_product_tokens():
    skipped_prefixes = (
        Path("docs/audits"),
        Path("frontend/public/demo"),
        Path("frontend/src/components/landing"),
        Path("frontend/public/images"),
    )
    checked_suffixes = {
        ".md",
        ".py",
        ".sh",
        ".ts",
        ".tsx",
        ".js",
        ".json",
        ".yaml",
        ".yml",
        ".example",
        ".gitignore",
        ".dockerignore",
    }

    offenders: list[str] = []
    tracked = subprocess.check_output(["git", "ls-files"], cwd=REPO_ROOT, text=True, encoding="utf-8")
    for relative_text in tracked.splitlines():
        relative = Path(relative_text)
        if any(relative == prefix or prefix in relative.parents for prefix in skipped_prefixes):
            continue
        path = REPO_ROOT / relative
        if not path.exists():
            continue
        if path.name not in {".gitignore", ".dockerignore"} and path.suffix not in checked_suffixes:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if any(token in content for token in FORBIDDEN_EXTERNAL_PRODUCT_TOKENS):
            offenders.append(str(relative))

    assert offenders == []


def test_supporting_docs_keep_vassilflow_public_imports():
    surfaces = {
        "backend/docs/GUARDRAILS.md": [
            "use: vassilflow.guardrails.builtin:AllowlistProvider",
            'framework="vassilflow"',
            "vassilflow.guardrails",
        ],
        "backend/docs/SSO.md": [
            "VassilFlow supports single sign-on",
            "issuer: http://localhost:8080/realms/vassilflow",
            "client_id: vassilflow",
        ],
        "backend/docs/IM_CHANNEL_CONNECTIONS.md": [
            "VassilFlow supports user-owned IM channel bindings",
            "connect the channel from VassilFlow Settings",
            "`vassilflow.persistence.channel_connections`",
        ],
        "backend/docs/MEMORY_SETTINGS_REVIEW.md": [
            "Start VassilFlow locally",
            "{runtime_home}/users/{user_id}/memory.json",
        ],
        "backend/docs/rfc-create-vassilflow-agent.md": [
            "from vassilflow.client import VassilFlowClient",
            "from vassilflow.agents.features import RuntimeFeatures",
            "create_vassilflow_agent",
        ],
        "backend/CONTRIBUTING.md": [
            "# Contributing to VassilFlow Backend",
            "from vassilflow.models.factory import create_chat_model",
            "use: vassilflow.tools.builtins.my_tool:my_tool",
        ],
    }

    for relative_path, expected_phrases in surfaces.items():
        content = _read(relative_path)
        for phrase in expected_phrases:
            assert phrase in content, f"{relative_path} missing {phrase!r}"
