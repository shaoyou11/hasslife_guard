"""Pure source checks for the HassLife whitelist customization."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path


MAX_SOURCE_FILE_BYTES = 2 * 1024 * 1024

REQUIRED_FILES = (
    "__init__.py",
    "const.py",
    "client_optimized.py",
    "state_manager.py",
    "config_flow.py",
    "manifest.json",
)

REQUIRED_MARKERS: dict[str, tuple[str, ...]] = {
    "__init__.py": (
        "allowlist = entry.options.get(CONF_ENTITY_ALLOWLIST)",
        "allowed_entity_ids=allowlist",
    ),
    "const.py": (
        'CONF_ENTITY_ALLOWLIST = "entity_allowlist"',
        "SUPPORTED_DOMAINS = [",
    ),
    "client_optimized.py": (
        "def is_entity_allowed",
        "or not self.is_entity_allowed(state.entity_id)",
        "any(not self.is_entity_allowed(entity_id)",
    ),
    "state_manager.py": (
        "or not self.client.is_entity_allowed(entity_id)",
        "and self.client.is_entity_allowed(entity_id)",
    ),
    "config_flow.py": (
        "async_get_options_flow",
        "CONF_ENTITY_ALLOWLIST",
    ),
}


@dataclass(frozen=True)
class SourceCheckResult:
    """Result of validating one HassLife source tree."""

    ok: bool
    status: str
    observed_digest: str | None
    version: str | None
    missing: tuple[str, ...] = ()
    error: str | None = None


def _digest(files: dict[str, bytes]) -> str:
    digest = hashlib.sha256()
    for filename in sorted(files):
        digest.update(filename.encode("utf-8"))
        digest.update(b"\0")
        digest.update(files[filename])
        digest.update(b"\0")
    return digest.hexdigest()


def check_hasslife_source(
    root: Path,
    expected_digest: str | None = None,
) -> SourceCheckResult:
    """Validate the HassLife whitelist contract and optional baseline."""

    root = Path(root)
    if not root.is_dir():
        return SourceCheckResult(
            ok=False,
            status="source_missing",
            observed_digest=None,
            version=None,
            error=f"HassLife source directory not found: {root}",
        )

    files: dict[str, bytes] = {}
    missing_files = tuple(
        filename for filename in REQUIRED_FILES if not (root / filename).is_file()
    )
    if missing_files:
        return SourceCheckResult(
            ok=False,
            status="source_missing",
            observed_digest=None,
            version=None,
            missing=missing_files,
        )

    for filename in REQUIRED_FILES:
        path = root / filename
        try:
            content = path.read_bytes()
        except OSError as exc:
            return SourceCheckResult(
                ok=False,
                status="read_error",
                observed_digest=None,
                version=None,
                error=f"Unable to read {filename}: {exc}",
            )
        if len(content) > MAX_SOURCE_FILE_BYTES:
            return SourceCheckResult(
                ok=False,
                status="read_error",
                observed_digest=None,
                version=None,
                error=f"Source file is unexpectedly large: {filename}",
            )
        files[filename] = content

    try:
        manifest = json.loads(files["manifest.json"].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return SourceCheckResult(
            ok=False,
            status="invalid_manifest",
            observed_digest=None,
            version=None,
            error=f"Invalid HassLife manifest: {exc}",
        )

    if not isinstance(manifest, dict):
        return SourceCheckResult(
            ok=False,
            status="invalid_manifest",
            observed_digest=None,
            version=None,
            error="HassLife manifest must be a JSON object",
        )

    version = manifest.get("version")
    if manifest.get("domain") != "hasslife" or not isinstance(version, str) or not version:
        return SourceCheckResult(
            ok=False,
            status="invalid_manifest",
            observed_digest=None,
            version=version if isinstance(version, str) else None,
        )

    missing_markers = tuple(
        f"{filename}:{marker}"
        for filename, markers in REQUIRED_MARKERS.items()
        for marker in markers
        if marker not in files[filename].decode("utf-8", errors="replace")
    )
    observed_digest = _digest(files)
    if missing_markers:
        return SourceCheckResult(
            ok=False,
            status="missing_protection",
            observed_digest=observed_digest,
            version=version,
            missing=missing_markers,
        )

    if expected_digest and expected_digest != observed_digest:
        return SourceCheckResult(
            ok=False,
            status="changed_since_baseline",
            observed_digest=observed_digest,
            version=version,
            error="HassLife source differs from the saved whitelist baseline",
        )

    return SourceCheckResult(
        ok=True,
        status="healthy" if expected_digest else "baseline_required",
        observed_digest=observed_digest,
        version=version,
    )
