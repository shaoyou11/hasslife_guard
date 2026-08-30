"""Coordinator for periodic HassLife whitelist integrity checks."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Any

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry, ConfigEntryDisabler
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_BASELINE_CREATED_AT,
    CONF_BASELINE_DIGEST,
    HASSLIFE_DOMAIN,
    NOTIFICATION_ID,
    NOTIFICATION_TITLE,
    STATUS_NOT_CONFIGURED,
    STATUS_BASELINE_REQUIRED,
    check_interval,
)
from .guard_core import SourceCheckResult, check_hasslife_source
from .settings import settings_from


LOGGER = logging.getLogger(__name__)


class HassLifeGuardCoordinator(DataUpdateCoordinator[SourceCheckResult]):
    """Run the local source check and apply the fail-closed action."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.settings = settings_from(dict(entry.data), dict(entry.options))
        self.source_root = Path(hass.config.path("custom_components", HASSLIFE_DOMAIN))
        self.last_checked_at: datetime | None = None
        self.target_entry_ids: list[str] = []
        self.disabled_entry_ids: list[str] = []

        super().__init__(
            hass,
            LOGGER,
            name="HassLife whitelist guard",
            update_interval=check_interval(self.settings.check_interval_hours),
            update_method=self._async_update_data,
        )

    def _hasslife_entries(self) -> list[ConfigEntry]:
        return list(self.hass.config_entries.async_entries(HASSLIFE_DOMAIN))

    def _save_baseline(self, result: SourceCheckResult) -> None:
        if not result.observed_digest:
            return
        options = dict(self.entry.options)
        options[CONF_BASELINE_DIGEST] = result.observed_digest
        options[CONF_BASELINE_CREATED_AT] = datetime.now(timezone.utc).isoformat()
        self.hass.config_entries.async_update_entry(self.entry, options=options)

    def _check_source(self, expected_digest: str | None = None) -> SourceCheckResult:
        """Convert an unexpected checker error into a fail-closed result."""

        try:
            return check_hasslife_source(
                self.source_root,
                expected_digest=expected_digest,
            )
        except Exception as exc:  # pragma: no cover - defensive HA safeguard
            LOGGER.exception("Unexpected HassLife source check failure")
            return SourceCheckResult(
                ok=False,
                status="guard_error",
                observed_digest=None,
                version=None,
                error=f"守卫检查异常：{type(exc).__name__}",
            )

    async def _async_update_data(self) -> SourceCheckResult:
        self.last_checked_at = datetime.now(timezone.utc)
        entries = self._hasslife_entries()
        self.target_entry_ids = [entry.entry_id for entry in entries]
        self.disabled_entry_ids = [
            entry.entry_id for entry in entries if entry.disabled_by is not None
        ]

        if not entries:
            persistent_notification.async_dismiss(self.hass, NOTIFICATION_ID)
            return SourceCheckResult(
                ok=True,
                status=STATUS_NOT_CONFIGURED,
                observed_digest=None,
                version=None,
            )

        expected_digest = self.entry.options.get(CONF_BASELINE_DIGEST)
        result = self._check_source(expected_digest)

        if result.ok and result.status == STATUS_BASELINE_REQUIRED:
            self._save_baseline(result)
            result = replace(result, status="healthy")

        if result.ok:
            persistent_notification.async_dismiss(self.hass, NOTIFICATION_ID)
            return result

        return await self._handle_failure(result, entries)

    async def _handle_failure(
        self,
        result: SourceCheckResult,
        entries: list[ConfigEntry] | None = None,
    ) -> SourceCheckResult:
        entries = entries if entries is not None else self._hasslife_entries()
        disable_errors: list[str] = []
        if self.settings.auto_disable_hasslife:
            for entry in entries:
                if entry.disabled_by is not None:
                    continue
                try:
                    disabled = await self.hass.config_entries.async_set_disabled_by(
                        entry.entry_id,
                        ConfigEntryDisabler.USER,
                    )
                    if disabled:
                        self.disabled_entry_ids.append(entry.entry_id)
                except Exception as exc:  # pragma: no cover - HA-only safeguard
                    LOGGER.exception("Unable to disable HassLife config entry")
                    disable_errors.append(type(exc).__name__)

        message = self._failure_message(result, disable_errors)
        persistent_notification.async_create(
            self.hass,
            message,
            title=NOTIFICATION_TITLE,
            notification_id=NOTIFICATION_ID,
        )
        if disable_errors:
            result = replace(
                result,
                error=(result.error or "")
                + f"; unable to disable HassLife: {', '.join(disable_errors)}",
            )
        return result

    def _failure_message(
        self,
        result: SourceCheckResult,
        disable_errors: list[str],
    ) -> str:
        details = [
            f"检查状态：{result.status}",
            f"HassLife 版本：{result.version or '未知'}",
        ]
        if result.missing:
            details.append("缺失项目：" + "、".join(result.missing[:6]))
        if result.error:
            details.append(f"说明：{result.error}")
        if self.settings.auto_disable_hasslife and not disable_errors:
            details.append("HassLife 已停用，请检查代码后再重新启用。")
        elif disable_errors:
            details.append("HassLife 自动停用失败，请立即在集成页面手动停用。")
        else:
            details.append("自动停用当前为关闭状态，请确认后手动处理 HassLife。")
        details.append("确认代码无误后，使用“接受当前版本为白名单基线”，再启用 HassLife。")
        return "\n".join(details)

    async def async_check_now(self) -> None:
        """Run a check immediately without accepting a changed baseline."""

        await self.async_refresh()

    async def async_accept_current_baseline(self) -> None:
        """Accept the current source only when all protection markers pass."""

        entries = self._hasslife_entries()
        if not entries:
            raise HomeAssistantError("未找到 HassLife 配置条目")

        result = self._check_source()
        if not result.ok or not result.observed_digest:
            result = await self._handle_failure(result, entries)
            self.async_set_updated_data(result)
            raise HomeAssistantError("当前 HassLife 代码未通过白名单保护校验")

        self._save_baseline(result)
        await self.async_refresh()

    @property
    def attributes(self) -> dict[str, Any]:
        """Return compact, non-secret diagnostic attributes for the sensor."""

        result = self.data
        if result is None:
            return {"status": "starting"}
        return {
            "status": result.status,
            "hasslife_version": result.version,
            "checked_at": self.last_checked_at.isoformat()
            if self.last_checked_at
            else None,
            "baseline_digest": self.entry.options.get(CONF_BASELINE_DIGEST),
            "observed_digest": result.observed_digest,
            "missing_protection": list(result.missing),
            "hasslife_entries": list(self.target_entry_ids),
            "disabled_hasslife_entries": list(self.disabled_entry_ids),
            "check_interval_hours": self.settings.check_interval_hours,
            "auto_disable_hasslife": self.settings.auto_disable_hasslife,
            "error": result.error,
        }
