"""Constants for the HassLife whitelist guard."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "hasslife_guard"
NAME = "HassLife Whitelist Guard"
VERSION = "0.1.0"

HASSLIFE_DOMAIN = "hasslife"
CONF_CHECK_INTERVAL_HOURS = "check_interval_hours"
CONF_AUTO_DISABLE_HASSLIFE = "auto_disable_hasslife"
CONF_BASELINE_DIGEST = "baseline_digest"
CONF_BASELINE_CREATED_AT = "baseline_created_at"

DEFAULT_CHECK_INTERVAL_HOURS = 12
MIN_CHECK_INTERVAL_HOURS = 1
MAX_CHECK_INTERVAL_HOURS = 168
DEFAULT_AUTO_DISABLE_HASSLIFE = True

PLATFORMS = ("binary_sensor", "button")

NOTIFICATION_ID = "hasslife_guard_whitelist"
NOTIFICATION_TITLE = "HassLife 白名单保护"

STATUS_HEALTHY = "healthy"
STATUS_BASELINE_REQUIRED = "baseline_required"
STATUS_CHANGED_SINCE_BASELINE = "changed_since_baseline"
STATUS_MISSING_PROTECTION = "missing_protection"
STATUS_SOURCE_MISSING = "source_missing"
STATUS_NOT_CONFIGURED = "hasslife_not_configured"


def check_interval(hours: int) -> timedelta:
    """Return the coordinator interval for a validated hour count."""

    return timedelta(hours=hours)
