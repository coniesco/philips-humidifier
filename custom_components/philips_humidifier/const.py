"""Constants for philips_humidifier."""
from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

NAME = "Philips Humidifier"
DOMAIN = "philips_humidifier"
VERSION = "0.0.0"
ATTRIBUTION = "Data provided by http://jsonplaceholder.typicode.com/"

DATA_KEY_FAN = "fan"
DATA_KEY_SENSOR = "humidifier_sensor"