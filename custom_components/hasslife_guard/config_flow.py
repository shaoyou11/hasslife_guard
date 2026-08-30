"""Config flow for the HassLife whitelist guard."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback

from .const import (
    CONF_AUTO_DISABLE_HASSLIFE,
    CONF_CHECK_INTERVAL_HOURS,
    DEFAULT_AUTO_DISABLE_HASSLIFE,
    DEFAULT_CHECK_INTERVAL_HOURS,
    DOMAIN,
    MAX_CHECK_INTERVAL_HOURS,
    MIN_CHECK_INTERVAL_HOURS,
    NAME,
)
from .settings import settings_from


def _schema(settings: dict) -> vol.Schema:
    """Build the shared user/options form schema."""

    return vol.Schema(
        {
            vol.Required(
                CONF_CHECK_INTERVAL_HOURS,
                default=settings[CONF_CHECK_INTERVAL_HOURS],
            ): vol.All(
                vol.Coerce(int),
                vol.Range(
                    min=MIN_CHECK_INTERVAL_HOURS,
                    max=MAX_CHECK_INTERVAL_HOURS,
                ),
            ),
            vol.Required(
                CONF_AUTO_DISABLE_HASSLIFE,
                default=settings[CONF_AUTO_DISABLE_HASSLIFE],
            ): bool,
        }
    )


def _form_settings(data: dict, options: dict) -> dict:
    """Return normalized values for a form."""

    current = settings_from(data, options)
    return {
        CONF_CHECK_INTERVAL_HOURS: current.check_interval_hours,
        CONF_AUTO_DISABLE_HASSLIFE: current.auto_disable_hasslife,
    }


class HassLifeGuardConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle initial setup of the guard."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> ConfigFlowResult:
        """Create the single guard config entry."""

        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if user_input is not None:
            return self.async_create_entry(
                title=NAME,
                data={
                    CONF_CHECK_INTERVAL_HOURS: int(
                        user_input[CONF_CHECK_INTERVAL_HOURS]
                    ),
                    CONF_AUTO_DISABLE_HASSLIFE: bool(
                        user_input[CONF_AUTO_DISABLE_HASSLIFE]
                    ),
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(
                {
                    CONF_CHECK_INTERVAL_HOURS: DEFAULT_CHECK_INTERVAL_HOURS,
                    CONF_AUTO_DISABLE_HASSLIFE: DEFAULT_AUTO_DISABLE_HASSLIFE,
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow."""

        return HassLifeGuardOptionsFlow()


class HassLifeGuardOptionsFlow(OptionsFlow):
    """Allow changing the check cadence and failure action."""

    async def async_step_init(
        self,
        user_input: dict | None = None,
    ) -> ConfigFlowResult:
        """Show and save guard options."""

        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={
                    CONF_CHECK_INTERVAL_HOURS: int(
                        user_input[CONF_CHECK_INTERVAL_HOURS]
                    ),
                    CONF_AUTO_DISABLE_HASSLIFE: bool(
                        user_input[CONF_AUTO_DISABLE_HASSLIFE]
                    ),
                },
            )

        entry = self.config_entry
        return self.async_show_form(
            step_id="init",
            data_schema=_schema(
                _form_settings(dict(entry.data), dict(entry.options))
            ),
        )
