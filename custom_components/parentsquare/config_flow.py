from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from parentsquare import AsyncParentSquareClient, AuthenticationError, MFARequired

from .const import DOMAIN


class ParentSquareConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._client: AsyncParentSquareClient | None = None
        self._credentials: dict[str, str] = {}
        self._reauth_entry = None
        self._mfa_hint = ""

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            username = user_input["username"].strip()
            password = user_input["password"]
            if self._reauth_entry is None:
                await self.async_set_unique_id(username.casefold())
                self._abort_if_unique_id_configured()
            self._credentials = {"username": username, "password": password}
            self._client = AsyncParentSquareClient(username, password)
            try:
                await self._client.ensure_authenticated()
                await self._client.discover_schools()
            except MFARequired as err:
                self._mfa_hint = err.contact_hint
                return await self.async_step_mfa()
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except Exception:
                errors["base"] = "cannot_connect"
            else:
                return await self._async_create_or_update_entry()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("username"): str,
                    vol.Required("password"): str,
                }
            ),
            errors=errors,
        )

    async def async_step_mfa(self, user_input=None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None and self._client is not None:
            try:
                await self._client.submit_mfa_code(user_input["code"])
                await self._client.discover_schools()
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except Exception:
                errors["base"] = "cannot_connect"
            else:
                return await self._async_create_or_update_entry()
        description = f"A code was sent to {self._mfa_hint}" if self._mfa_hint else None
        return self.async_show_form(
            step_id="mfa",
            description_placeholders={"destination": description or "your verified contact"},
            data_schema=vol.Schema({vol.Required("code"): str}),
            errors=errors,
        )

    async def async_step_reauth(self, user_input=None) -> ConfigFlowResult:
        self._reauth_entry = self._get_reauth_entry()
        return await self.async_step_user(user_input)

    async def _async_create_or_update_entry(self) -> ConfigFlowResult:
        assert self._client is not None
        await self._client.close()
        if self._reauth_entry is not None:
            return self.async_update_reload_and_abort(
                self._reauth_entry,
                data_updates=self._credentials,
            )
        return self.async_create_entry(title=self._credentials["username"], data=self._credentials)
