from typing import Any

from homeassistant.components.fan import ATTR_PRESET_MODE, SERVICE_SET_PRESET_MODE, DOMAIN as FAN_DOMAIN
from homeassistant.components.humidifier import HumidifierEntity, HumidifierDeviceClass, HumidifierEntityFeature, \
    HumidifierAction
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SOURCE, CONF_ENTITY_ID, CONF_NAME, STATE_UNAVAILABLE, STATE_ON, ATTR_ENTITY_ID, \
    SERVICE_TURN_OFF, SERVICE_TURN_ON
from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import EventStateChangedData, async_track_state_change_event
from homeassistant.helpers.typing import EventType
from homeassistant.helpers import entity_registry as er, device_registry as dr

from .const import LOGGER, FAN_FUNCTION_SELECT, HumidifierFunction


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback
):
    """Set up humidifier platform."""
    LOGGER.debug("async_setup_entry called for platform humidifier")
    registry = er.async_get(hass)
    # Validate + resolve entity registry id to entity_id
    fan_entity_id = er.async_validate_entity_id(
        registry, config_entry.data[CONF_SOURCE]
    )
    humidity_entity_id = er.async_validate_entity_id(
        registry, config_entry.data[CONF_ENTITY_ID]
    )

    fan_entity = registry.async_get(fan_entity_id)
    dev_reg = dr.async_get(hass)
    # Resolve source entity device
    if (
            (fan_entity is not None)
            and (fan_entity.device_id is not None)
            and (
            (
                    device := dev_reg.async_get(
                        device_id=fan_entity.device_id,
                    )
            )
            is not None
    )
    ):
        device_info = DeviceInfo(
            identifiers=device.identifiers,
            connections=device.connections,
        )
        entries = er.async_entries_for_device(registry, device.id)
        filtered_entries = [entity for entity in entries if FAN_FUNCTION_SELECT in entity.original_name]
        function_entity_id = next(iter(filtered_entries)).entity_id
        LOGGER.debug(f"Function entity id: {function_entity_id}")
    else:
        device_info = None
        function_entity_id = None

    humidifier = PhilipsHumidifier(
        name=config_entry.data[CONF_NAME],
        fan_entity=fan_entity_id,
        humidity_entity=humidity_entity_id,
        function_entity=function_entity_id,
        unique_id=config_entry.entry_id,
        device_info=device_info
    )

    async_add_entities([humidifier], update_before_add=True)


class PhilipsHumidifier(HumidifierEntity):
    """Class to manage a Philips Humidifier."""

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(  # noqa: D107
            self,
            name: str | None,
            fan_entity: str,
            humidity_entity: str,
            function_entity: str | None,
            unique_id: str | None,
            device_info: DeviceInfo | None = None
    ):
        super().__init__()
        self._attr_unique_id = unique_id
        self._attr_device_info = device_info
        self._attr_device_class = HumidifierDeviceClass.HUMIDIFIER
        self._attr_supported_features = HumidifierEntityFeature.MODES
        self._fan_source_id = fan_entity
        self._humidity_source_id = humidity_entity
        self._function_source_id = function_entity
        self._entities = [self._fan_source_id, self._humidity_source_id, self._function_source_id]
        self._name = name
        self._attr_target_humidity = 35

        self._available = False
        self._is_on = False
        self._available_modes = []
        self._action: HumidifierAction | None = None
        self._current_humidity = None
        self._mode = None
        self._target_humidity = None
        self._function: HumidifierFunction | None = None

    @property
    def name(self) -> str:
        """Return the name of the humidifier."""
        return self._name

    @property
    def available(self) -> bool:
        """Return if the device is available."""
        return self._available

    @property
    def is_on(self) -> bool | None:
        """Return if the humidifier is on."""
        return self._is_on

    @property
    def available_modes(self) -> list[str] | None:
        """Return the available modes for the humidifier."""
        return self._available_modes

    @property
    def action(self) -> HumidifierAction | None:
        """Return the current action of the humidifier."""
        return self._action

    @property
    def current_humidity(self) -> float | None:
        """Return the current humidity."""
        return self._current_humidity

    @property
    def mode(self) -> str | None:
        """Return the current mode of the humidifier."""
        return self._mode

    async def async_set_humidity(self, humidity: int) -> None:
        """Set the humidity target."""
        self._attr_target_humidity = humidity

    async def async_set_mode(self, mode: str) -> None:
        """Set the mode of the humidifier."""
        await self.hass.services.async_call(
            FAN_DOMAIN,
            SERVICE_SET_PRESET_MODE,
            {ATTR_ENTITY_ID: self._fan_source_id, ATTR_PRESET_MODE: mode},
            blocking=True,
            context=self._context,
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the humidifier on."""
        await self.hass.services.async_call(
            FAN_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: self._fan_source_id},
            blocking=True,
            context=self._context,
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the humidifier off."""
        await self.hass.services.async_call(
            FAN_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: self._fan_source_id},
            blocking=True,
            context=self._context,
        )

    async def async_update(self):
        """Update the state of the humidifier."""
        if not self:
            self._available = False
            return

        states = [
            state.state
            for entity_id in self._entities
            if (state := self.hass.states.get(entity_id)) is not None
        ]
        LOGGER.debug(f"States: {states}")
        # Set group as unavailable if all members are unavailable or missing
        self._available = not any(state == STATE_UNAVAILABLE for state in states)

        self._function = self.hass.states.get(self._function_source_id).state
        self._action = HumidifierFunction.ACTION_MAP[self._function]

        fan_state = self.hass.states.get(self._fan_source_id)
        attributes = fan_state.attributes
        self._is_on = fan_state.state == STATE_ON
        self._available_modes = attributes["preset_modes"]
        self._mode = attributes["preset_mode"]
        if self._function is not None:
            self._action = HumidifierFunction.ACTION_MAP[
                self._function] if fan_state == STATE_ON else HumidifierAction.OFF

        self._current_humidity = self.hass.states.get(self._humidity_source_id).state

        LOGGER.debug("First update done")

    async def async_added_to_hass(self) -> None:
        """Register listeners."""
        await super().async_added_to_hass()
        LOGGER.debug("Adding to hass")

        @callback
        def async_state_changed_listener(
                event: EventType[EventStateChangedData],
        ) -> None:
            """Handle the sensor state changes."""
            state = event.data["new_state"].state
            self._available = state != STATE_UNAVAILABLE
            if event.data["entity_id"] == self._fan_source_id:
                if self._current_humidity is None:
                    self._current_humidity = self.hass.states.get(self._humidity_source_id).state

                if self._function is None:
                    self._function = self.hass.states.get(self._function_source_id).state
                    self._action = HumidifierFunction.ACTION_MAP[self._function]

                attributes = event.data["new_state"].attributes

                self._is_on = state == STATE_ON
                self._available_modes = attributes["preset_modes"]
                self._mode = attributes["preset_mode"]
                if self._function is not None:
                    self._action = HumidifierFunction.ACTION_MAP[
                        self._function] if state == STATE_ON else HumidifierAction.OFF

            elif event.data["entity_id"] == self._humidity_source_id:
                LOGGER.debug(event.data["new_state"])
                self._current_humidity = state

            elif event.data["entity_id"] == self._function_source_id:
                LOGGER.debug(event.data["new_state"])
                self._function = self.hass.states.get(self._function_source_id).state
                self._action = HumidifierFunction.ACTION_MAP[self._function]

            self.async_write_ha_state()

        self.async_on_remove(
            async_track_state_change_event(
                self.hass, self._entities, async_state_changed_listener
            )
        )
