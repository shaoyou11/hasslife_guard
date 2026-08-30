from __future__ import annotations

import json
import sys
import tempfile
import types
import unittest
from pathlib import Path

PACKAGE_DIR = Path(__file__).parents[1] / "custom_components" / "hasslife_guard"


def prepare_package_import() -> None:
    """Load pure modules without importing Home Assistant runtime modules."""

    package_name = "custom_components.hasslife_guard"
    if package_name in sys.modules:
        return
    package = types.ModuleType(package_name)
    package.__path__ = [str(PACKAGE_DIR)]
    sys.modules[package_name] = package

MARKERS = {
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


def checker():
    prepare_package_import()
    try:
        from custom_components.hasslife_guard.guard_core import check_hasslife_source
    except ModuleNotFoundError as exc:
        raise AssertionError("guard_core is not implemented") from exc
    return check_hasslife_source


def make_source(root: Path, *, missing: tuple[str, str] | None = None) -> Path:
    source = root / "custom_components" / "hasslife"
    source.mkdir(parents=True)
    for filename, required in MARKERS.items():
        content = "\n".join(required)
        if missing and missing[0] == filename:
            content = content.replace(missing[1], "")
        (source / filename).write_text(content, encoding="utf-8")
    (source / "manifest.json").write_text(
        json.dumps({"domain": "hasslife", "version": "3.8.5"}),
        encoding="utf-8",
    )
    return source


class GuardCoreTests(unittest.TestCase):
    def test_valid_source_requires_a_baseline_on_first_check(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = checker()(make_source(Path(temp_dir)))

        self.assertTrue(result.ok)
        self.assertEqual(result.status, "baseline_required")
        self.assertEqual(result.version, "3.8.5")
        self.assertTrue(result.observed_digest)
        self.assertEqual(result.missing, ())

    def test_missing_control_gate_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = make_source(
                Path(temp_dir),
                missing=("client_optimized.py", "any(not self.is_entity_allowed(entity_id)"),
            )
            result = checker()(source)

        self.assertFalse(result.ok)
        self.assertEqual(result.status, "missing_protection")
        self.assertIn(
            "client_optimized.py:any(not self.is_entity_allowed(entity_id)",
            result.missing,
        )

    def test_changed_source_is_rejected_against_saved_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = make_source(Path(temp_dir))
            first = checker()(source)
            (source / "client_optimized.py").write_text(
                (source / "client_optimized.py").read_text(encoding="utf-8") + "\nchanged\n",
                encoding="utf-8",
            )
            result = checker()(source, expected_digest=first.observed_digest)

        self.assertFalse(result.ok)
        self.assertEqual(result.status, "changed_since_baseline")

    def test_invalid_manifest_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = make_source(Path(temp_dir))
            (source / "manifest.json").write_text("{}", encoding="utf-8")
            result = checker()(source)

        self.assertFalse(result.ok)
        self.assertEqual(result.status, "invalid_manifest")

    def test_non_object_manifest_is_rejected_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = make_source(Path(temp_dir))
            (source / "manifest.json").write_text("[]", encoding="utf-8")
            result = checker()(source)

        self.assertFalse(result.ok)
        self.assertEqual(result.status, "invalid_manifest")
