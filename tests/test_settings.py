from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path

PACKAGE_DIR = Path(__file__).parents[1] / "custom_components" / "hasslife_guard"


def prepare_package_import() -> None:
    """Load the pure settings module without Home Assistant installed."""

    package_name = "custom_components.hasslife_guard"
    if package_name in sys.modules:
        return
    package = types.ModuleType(package_name)
    package.__path__ = [str(PACKAGE_DIR)]
    sys.modules[package_name] = package


def settings_helper():
    prepare_package_import()
    try:
        from custom_components.hasslife_guard.settings import settings_from
    except ModuleNotFoundError as exc:
        raise AssertionError("settings helper is not implemented") from exc
    return settings_from


class SettingsTests(unittest.TestCase):
    def test_defaults_use_a_twelve_hour_check_interval_and_auto_disable(self) -> None:
        settings = settings_helper()({}, {})

        self.assertEqual(settings.check_interval_hours, 12)
        self.assertTrue(settings.auto_disable_hasslife)

    def test_options_override_initial_config(self) -> None:
        settings = settings_helper()(
            {"check_interval_hours": 24, "auto_disable_hasslife": False},
            {"check_interval_hours": 2, "auto_disable_hasslife": True},
        )

        self.assertEqual(settings.check_interval_hours, 2)
        self.assertTrue(settings.auto_disable_hasslife)
