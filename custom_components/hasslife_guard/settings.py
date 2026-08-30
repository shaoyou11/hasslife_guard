"""Configuration value normalization for the guard."""

from __future__ import annotations

from dataclasses import dataclass

from .const import (
    CONF_AUTO_DISABLE_HASSLIFE,
    CONF_CHECK_INTERVAL_HOURS,
    DEFAULT_AUTO_DISABLE_HASSLIFE,
    DEFAULT_CHECK_INTERVAL_HOURS,
    MAX_CHECK_INTERVAL_HOURS,
    MIN_CHECK_INTERVAL_HOURS,
)


@dataclass(frozen=True)
class GuardSettings:
    """Effective guard settings after merging entry data and options."""

    check_interval_hours: int
    auto_disable_hasslife: bool


def settings_from(data: dict, options: dict) -> GuardSettings:
    """Merge persisted initial data with newer options-flow values."""

    merged = dict(data or {})
    merged.update(options or {})
    try:
        hours = int(merged.get(CONF_CHECK_INTERVAL_HOURS, DEFAULT_CHECK_INTERVAL_HOURS))
    except (TypeError, ValueError):
        hours = DEFAULT_CHECK_INTERVAL_HOURS
    if not MIN_CHECK_INTERVAL_HOURS <= hours <= MAX_CHECK_INTERVAL_HOURS:
        hours = DEFAULT_CHECK_INTERVAL_HOURS

    auto_disable = merged.get(
        CONF_AUTO_DISABLE_HASSLIFE,
        DEFAULT_AUTO_DISABLE_HASSLIFE,
    )
    return GuardSettings(
        check_interval_hours=hours,
        auto_disable_hasslife=bool(auto_disable),
    )
