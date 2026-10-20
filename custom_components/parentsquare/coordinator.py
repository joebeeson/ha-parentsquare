from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from parentsquare import (
    AsyncParentSquareClient,
    AuthenticationError,
    CalendarEvent,
    MFARequired,
    Post,
    RateLimitError,
)

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, STORAGE_KEY_PREFIX, STORAGE_VERSION
from .history import PostHistory

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ParentSquareData:
    posts: tuple[Post, ...]
    calendar_events: tuple[CalendarEvent, ...]
    new_posts: tuple[Post, ...]


class ParentSquareCoordinator(DataUpdateCoordinator[ParentSquareData]):
    """Fetch ParentSquare data and own duplicate suppression."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.client = AsyncParentSquareClient(entry.data["username"], entry.data["password"])
        self._store = Store(
            hass,
            STORAGE_VERSION,
            f"{STORAGE_KEY_PREFIX}.{entry.entry_id}",
        )
        self._history = PostHistory()
        self._baseline_complete = False
        super().__init__(
            hass,
            logger=LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=DEFAULT_SCAN_INTERVAL,
        )

    async def async_initialize(self) -> None:
        stored = await self._store.async_load()
        if isinstance(stored, dict):
            self._history = PostHistory(stored.get("post_ids", []))
            self._baseline_complete = bool(stored.get("baseline_complete", False))
        await self.async_config_entry_first_refresh()

    async def _async_update_data(self) -> ParentSquareData:
        try:
            posts = await self.client.fetch_all_posts()
            events = await self.client.fetch_all_calendar_events()
        except MFARequired as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except AuthenticationError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except RateLimitError as err:
            if err.retry_after is not None:
                self.update_interval = timedelta(seconds=min(max(err.retry_after, 60), 6 * 60 * 60))
            raise UpdateFailed(str(err)) from err
        except Exception as err:
            raise UpdateFailed("Unable to read ParentSquare") from err

        self.update_interval = DEFAULT_SCAN_INTERVAL
        post_ids = [post.id for post in posts]
        if not self._baseline_complete:
            self._history.add(post_ids)
            new_posts: list[Post] = []
            self._baseline_complete = True
        else:
            new_ids = set(self._history.add(post_ids))
            new_posts = [post for post in posts if post.id in new_ids]
        await self._store.async_save(
            {
                "post_ids": self._history.post_ids,
                "baseline_complete": self._baseline_complete,
            }
        )
        return ParentSquareData(tuple(posts), tuple(events), tuple(new_posts))

    async def async_shutdown(self) -> None:
        await self.client.close()
