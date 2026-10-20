from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.core import callback
from homeassistant.helpers import selector
from parentsquare import AsyncParentSquareClient, AuthenticationError, MFARequired

from .const import (
    CONF_GROUP_KEYS,
    CONF_INCLUDE_COMBINED_CALENDAR,
    CONF_SCHOOL_IDS,
    DOMAIN,
)
from .selection import group_key

LOGGER = logging.getLogger(__name__)


class ParentSquareConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._client: AsyncParentSquareClient | None = None
        self._credentials: dict[str, str] = {}
        self._reauth_entry = None
        self._mfa_hint = ""

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return ParentSquareOptionsFlow()

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
                await self._client.discover_account()
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
            data_schema=vol.Schema(  # pyrefly: ignore [bad-argument-type]
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
                await self._client.discover_account()
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
            data_schema=vol.Schema({vol.Required("code"): str}),  # pyrefly: ignore [bad-argument-type]
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


class ParentSquareOptionsFlow(config_entries.OptionsFlowWithReload):
    """Select which discovered ParentSquare sources Home Assistant exposes."""

    def __init__(self) -> None:
        self._schools = []
        self._groups = []

    async def async_step_init(self, user_input=None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            school_ids = [str(value) for value in user_input.get(CONF_SCHOOL_IDS, [])]
            if not school_ids:
                errors["base"] = "no_school"
            else:
                return self.async_create_entry(
                    title="",
                    data={
                        CONF_SCHOOL_IDS: school_ids,
                        CONF_INCLUDE_COMBINED_CALENDAR: bool(
                            user_input.get(CONF_INCLUDE_COMBINED_CALENDAR, True)
                        ),
                        CONF_GROUP_KEYS: [
                            str(value) for value in user_input.get(CONF_GROUP_KEYS, [])
                        ],
                    },
                )

        try:
            await self._discover_sources()
        except AuthenticationError:
            errors["base"] = "invalid_auth"
        except Exception:
            errors["base"] = "cannot_connect"

        options = [{"value": str(school.id), "label": school.name} for school in self._schools]
        group_options = [
            {
                "value": group_key(group),
                "label": f"{group.school_name or f'School {group.school_id}'} · {group.name}",
            }
            for group in self._groups
        ]
        current_school_ids = self.config_entry.options.get(CONF_SCHOOL_IDS)
        if not isinstance(current_school_ids, (list, tuple, set)) or not current_school_ids:
            current_school_ids = [str(school.id) for school in self._schools]
        current_group_keys = self.config_entry.options.get(CONF_GROUP_KEYS, [])
        if not isinstance(current_group_keys, (list, tuple, set)):
            current_group_keys = []
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(  # pyrefly: ignore [bad-argument-type]
                {
                    vol.Required(
                        CONF_SCHOOL_IDS,
                        default=[str(value) for value in current_school_ids],
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=options,
                            multiple=True,
                            mode=selector.SelectSelectorMode.LIST,
                        )
                    ),
                    vol.Required(
                        CONF_INCLUDE_COMBINED_CALENDAR,
                        default=self.config_entry.options.get(CONF_INCLUDE_COMBINED_CALENDAR, True),
                    ): bool,
                    vol.Optional(
                        CONF_GROUP_KEYS,
                        default=[str(value) for value in current_group_keys],
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=group_options,
                            multiple=True,
                            mode=selector.SelectSelectorMode.LIST,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def _discover_sources(self) -> None:
        client = AsyncParentSquareClient(
            self.config_entry.data["username"], self.config_entry.data["password"]
        )
        try:
            await client.ensure_authenticated()
            account = await client.discover_account(force_refresh=True)
            self._schools = list(account.schools)
            groups = []
            for school in self._schools:
                try:
                    groups.extend(await client.fetch_groups(school))
                except AuthenticationError:
                    raise
                except Exception:
                    # Group pages are optional in the unofficial source. Keep
                    # school selection usable if one school hides that page.
                    LOGGER.debug("Unable to discover groups for school %s", school.id)
            self._groups = groups
        finally:
            await client.close()
