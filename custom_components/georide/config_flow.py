""" Georide config flow """

import logging
from homeassistant import config_entries
import voluptuous as vol
import georideapilib.api as GeorideApi
import georideapilib.exception as GeorideException


from .const import CONF_EMAIL, CONF_PASSWORD, CONF_TOKEN


_LOGGER = logging.getLogger(__name__)

@config_entries.HANDLERS.register("georide")
class GeorideConfigFlow(config_entries.ConfigFlow):
    """Georide config flow """
    
    async def async_step_user(self, user_input=None): #pylint: disable=W0613
        """ handle info to help to configure georide """

        if self._async_current_entries():
            return self.async_abort(reason="one_instance_allowed")

        return self.async_show_form(step_id='georide_login', data_schema=vol.Schema({
            vol.Required(CONF_EMAIL): vol.All(str, vol.Length(min=3)),
            vol.Required(CONF_PASSWORD): vol.All(str)
        }))

    async def async_step_import(self, user_input=None): #pylint: disable=W0613
        """Import a config flow from configuration."""
        if self._async_current_entries():
            return self.async_abort(reason="one_instance_allowed")

        return self.async_show_form(step_id='georide_login', data_schema=vol.Schema({
            vol.Required(CONF_EMAIL): vol.All(str, vol.Length(min=3)),
            vol.Required(CONF_PASSWORD): vol.All(str)
        }))



    async def async_step_georide_login(self, user_input):
        """ try to seupt GeoRide Account """
        errors = {}
        try:
            account = GeorideApi.get_authorisation_token(
                user_input[CONF_EMAIL],
                user_input[CONF_PASSWORD])
            return self.async_create_entry(
                title=user_input[CONF_EMAIL],
                data={
                    CONF_EMAIL: user_input[CONF_EMAIL],
                    CONF_PASSWORD: user_input[CONF_PASSWORD],
                    CONF_TOKEN: account.auth_token
                }
            )
        except (GeorideException.SeverException, GeorideException.LoginException):
            _LOGGER.error("Invalid credentials provided, config not created")
            errors["base"] = "faulty_credentials"
            return self.async_show_form(step_id="georide_login", errors=errors)
        except: 
            _LOGGER.error("Unknown error")
            errors["base"] = "faulty_credentials"
            return self.async_show_form(step_id="georide_login", errors=errors)

        
        