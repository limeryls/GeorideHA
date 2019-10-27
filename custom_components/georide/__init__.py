""" georide custom conpennt """
from collections import defaultdict

from georideapilib.objects import GeorideAccount
import georideapilib.api as GeorideApi

import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_WEBHOOK_ID
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
from homeassistant.setup import async_when_setup

from .const import (
    CONF_EMAIL,
    CONF_PASSWORD,
    TRACKER_ID
)

DOMAIN = "georide"

_LOGGER = logging.getLogger(__name__)


CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(DOMAIN, default={}): {
            vol.Optional(CONF_EMAIL): vol.All(str, vol.Length(min=3)),
            vol.Optional(CONF_PASSWORD): vol.All(str)
        }
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass, config):
    """Setup  Georide component."""
    hass.data[DOMAIN] = {"config": config[DOMAIN], "devices": {}, "unsub": None}
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data={}
        )
    )

    _LOGGER.info("Georide-setup ")


    # Return boolean to indicate that initialization was successful.
    return True



async def async_setup_entry(hass, entry):
    """Set up Georide entry."""
    config = hass.data[DOMAIN]["config"]
    email = config.get(CONF_EMAIL) or entry.data[CONF_EMAIL]
    password = config.get(CONF_PASSWORD) or entry.data[CONF_PASSWORD]

    if email is None or password is None:
        return False

    account = GeorideApi.get_authorisation_token(email, password)
    context = GeorideContext(
        hass,
        email,
        password,
        account.auth_token
    )

    hass.data[DOMAIN]["context"] = context
    hass.async_create_task(hass.config_entries.async_forward_entry_setup(entry, "device_tracker"))

    return True

async def async_unload_entry(hass, entry):
    """Unload an Georide config entry."""
    await hass.config_entries.async_forward_entry_unload(entry, "device_tracker")
    hass.data[DOMAIN]["unsub"]()

    return True


class GeorideContext:
    """Hold the current Georide context."""

    def __init__(self, hass, email, password, token):
        """Initialize an Georide context."""
        self._hass = hass
        self._email = email
        self._password = password
        self._georide_trackers = defaultdict(set)
        self._token = token

    @property
    def hass(self):
        """ hass """
        return self._hass

    @property
    def email(self):
        """ current email """
        return self._email
    
    @property
    def password(self):
        """ password """
        return self._password

    @property
    def token(self):
        """ current jwt token """
        return self._token

    @property
    def georide_trackers(self):
        """ georide tracker list """
        return self._georide_trackers
    
    @callback
    def async_see_beacons(self, hass, dev_id, kwargs_param):
        """Set active beacons to the current location."""
        kwargs = kwargs_param.copy()

        # Mobile beacons should always be set to the location of the
        # tracking device. I get the device state and make the necessary
        # changes to kwargs.
        device_tracker_state = hass.states.get(f"device_tracker.{dev_id}")

        if device_tracker_state is not None:
            lat = device_tracker_state.attributes.get("latitude")
            lon = device_tracker_state.attributes.get("longitude")

            if lat is not None and lon is not None:
                kwargs["gps"] = (lat, lon)
            else:
                kwargs["gps"] = None

        for tracker in self.georide_trackers[dev_id]:
            kwargs["dev_id"] = f"{TRACKER_ID}_{tracker}"
            kwargs["host_name"] = tracker
    
    
    

