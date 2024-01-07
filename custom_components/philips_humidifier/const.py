"""Constants for philips_humidifier."""
from logging import Logger, getLogger

from homeassistant.components.humidifier import HumidifierAction

LOGGER: Logger = getLogger(__package__)

NAME = "Philips Humidifier"
DOMAIN = "philips_humidifier"
VERSION = "0.0.0"
ATTRIBUTION = "Data provided by http://jsonplaceholder.typicode.com/"

DATA_KEY_FAN = "fan"
DATA_KEY_SENSOR = "humidifier_sensor"
FAN_FUNCTION_SELECT = "Function"


class HumidifierFunction:
    HUMIDIFICATION = "Purification and Humidification",
    IDLE = "Purification"

    ACTION_MAP = {
        HUMIDIFICATION: HumidifierAction.HUMIDIFYING,
        IDLE: HumidifierAction.IDLE,
    }
