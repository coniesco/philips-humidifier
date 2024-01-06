from homeassistant.components.humidifier import HumidifierEntity, HumidifierDeviceClass, HumidifierEntityFeature, \
    HumidifierAction
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SOURCE, CONF_ENTITY_ID, CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import EventStateChangedData, async_track_state_change_event
from homeassistant.helpers.typing import HomeAssistantType, EventType
from homeassistant.helpers import entity_registry as er, device_registry as dr

from .const import LOGGER


async def async_setup_entry(
        hass: HomeAssistantType,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback
):
    LOGGER.debug("async_setup_entry called for platform humidifier")
    registry = er.async_get(hass)
    # Validate + resolve entity registry id to entity_id
    source_entity_id = er.async_validate_entity_id(
        registry, config_entry.data[CONF_SOURCE]
    )
    humidifier_entity_id = er.async_validate_entity_id(
        registry, config_entry.data[CONF_ENTITY_ID]
    )

    source_entity = registry.async_get(source_entity_id)
    dev_reg = dr.async_get(hass)
    # Resolve source entity device
    if (
            (source_entity is not None)
            and (source_entity.device_id is not None)
            and (
            (
                    device := dev_reg.async_get(
                        device_id=source_entity.device_id,
                    )
            )
            is not None
    )
    ):
        device_info = DeviceInfo(
            identifiers=device.identifiers,
            connections=device.connections,
        )
    else:
        device_info = None

    humidifier = PhilipsHumidifier(
        name=config_entry.data[CONF_NAME],
        source_entity=source_entity_id,
        humidity_entity=humidifier_entity_id,
        unique_id=config_entry.entry_id,
        device_info=device_info
    )

    async_add_entities([humidifier])


class PhilipsHumidifier(HumidifierEntity):
    _attr_should_poll = False

    def __init__(
            self,
            name: str | None,
            source_entity: str,
            humidity_entity: str,
            unique_id: str | None,
            device_info: DeviceInfo | None = None
    ):
        self._attr_unique_id = unique_id
        self._attr_device_info = device_info
        self._sensor_source_id = source_entity
        self._humidity_source_id = humidity_entity
        self._attr_device_class = HumidifierDeviceClass.HUMIDIFIER
        self._attr_supported_features = HumidifierEntityFeature.MODES
        self._attr_has_entity_name = True
        self._name = name

        self._attr_action: HumidifierAction | None = None
        self._attr_available_modes = ['auto', 'night', 'speed 1', 'speed 2', 'speed 3', 'turbo']
        self._attr_current_humidity = None
        self._attr_is_on = False
        self._attr_mode = None
        self._target_humidity = None

    @property
    def name(self) -> str:
        return self._name

    async def async_added_to_hass(self) -> None:
        """Register listeners."""
        await super().async_added_to_hass()
        entity_ids = [self._sensor_source_id, self._humidity_source_id]

        @callback
        def async_state_changed_listener(
                event: EventType[EventStateChangedData],
        ) -> None:
            """Handle child updates."""
            self.async_set_context(event.context)
            LOGGER.debug(event)
            # self.async_update_supported_features(
            #     event.data["entity_id"], event.data["new_state"]
            # )
            # self.async_defer_or_update_ha_state()

        self.async_on_remove(
            async_track_state_change_event(
                self.hass, entity_ids, async_state_changed_listener
            )
        )
