"""Adds config flow for Blueprint."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_DEVICE, CONF_NAME
from homeassistant.helpers import selector

from .const import DOMAIN, LOGGER


class BlueprintFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Blueprint."""

    VERSION = 1

    def _get_schema(self):
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_DEVICE
                ): selector.DeviceSelector(
                    selector.DeviceSelectorConfig(multiple=False,
                                                  filter=selector.DeviceFilterSelectorConfig(
                                                      integration="philips_airpurifier_coap"),
                                                  )

                ),
                vol.Required(
                    CONF_NAME
                ): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT
                    ),
                )
            }
        )
        return schema

    async def async_step_user(
            self,
            user_input: dict | None = None,
    ) -> config_entries.FlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        # devices = await hass.async_add_executor_job(my_pypi_dependency.discover)
        if user_input is not None:
            LOGGER.info('hello')
            await self.async_set_unique_id(user_input[CONF_NAME])
            self._abort_if_unique_id_configured()
            LOGGER.info(user_input)
        else:
            LOGGER.info('nothing')
            schema = self._get_schema()
            return self.async_show_form(step_id="user", data_schema=schema, errors=_errors)
