"""Button platform for manual HassLife whitelist actions."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HassLifeGuardCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the manual guard action buttons."""

    coordinator: HassLifeGuardCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            HassLifeGuardCheckButton(coordinator, entry),
            HassLifeGuardAcceptButton(coordinator, entry),
        ]
    )


class _HassLifeGuardButton(
    CoordinatorEntity[HassLifeGuardCoordinator],
    ButtonEntity,
):
    """Common entity metadata for manual guard actions."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HassLifeGuardCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "HassLife 白名单守卫",
            "manufacturer": "shaoyou11",
            "model": "Whitelist Guard",
        }

    @property
    def available(self) -> bool:
        """Keep actions unavailable while the first check is incomplete."""

        return self.coordinator.last_update_success


class HassLifeGuardCheckButton(_HassLifeGuardButton):
    """Run a check without changing the saved baseline."""

    _attr_name = "立即检查白名单"
    _attr_icon = "mdi:shield-refresh"

    def __init__(
        self,
        coordinator: HassLifeGuardCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_check_now"

    async def async_press(self) -> None:
        """Run the check immediately."""

        await self.coordinator.async_check_now()


class HassLifeGuardAcceptButton(_HassLifeGuardButton):
    """Accept the current, validated source as the new baseline."""

    _attr_name = "接受当前版本为基线"
    _attr_icon = "mdi:shield-check"

    def __init__(
        self,
        coordinator: HassLifeGuardCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_accept_baseline"

    async def async_press(self) -> None:
        """Validate and accept the current source."""

        await self.coordinator.async_accept_current_baseline()
