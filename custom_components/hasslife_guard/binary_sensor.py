"""Binary sensor platform for the HassLife whitelist guard."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.binary_sensor import BinarySensorEntity

from .const import DOMAIN
from .coordinator import HassLifeGuardCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the guard health sensor."""

    coordinator: HassLifeGuardCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([HassLifeGuardSensor(coordinator, entry)])


class HassLifeGuardSensor(
    CoordinatorEntity[HassLifeGuardCoordinator],
    BinarySensorEntity,
):
    """Report whether HassLife passes the current whitelist checks."""

    _attr_has_entity_name = True
    _attr_name = "白名单保护"
    _attr_icon = "mdi:shield-check"

    def __init__(
        self,
        coordinator: HassLifeGuardCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_whitelist_protection"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "HassLife 白名单守卫",
            "manufacturer": "shaoyou11",
            "model": "Whitelist Guard",
        }

    @property
    def is_on(self) -> bool:
        """Return true when the source passes or HassLife is not configured."""

        return bool(self.coordinator.data and self.coordinator.data.ok)

    @property
    def extra_state_attributes(self) -> dict:
        """Expose non-secret diagnostic state."""

        return self.coordinator.attributes
