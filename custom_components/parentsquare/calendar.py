from __future__ import annotations

from datetime import datetime

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import ParentSquareCoordinator
from .helpers import as_local_datetime, overlaps


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([ParentSquareCalendar(hass.data[DOMAIN][entry.entry_id], entry)])


class ParentSquareCalendar(CoordinatorEntity[ParentSquareCoordinator], CalendarEntity):
    _attr_has_entity_name = True
    _attr_name = "Calendar"
    _attr_icon = "mdi:school"

    def __init__(self, coordinator: ParentSquareCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_calendar"

    @property
    def event(self) -> CalendarEvent | None:
        if not self.coordinator.data:
            return None
        now = dt_util.now()
        candidates = sorted(
            (
                event
                for event in self.coordinator.data.calendar_events
                if as_local_datetime(event.end, now.tzinfo) > now
            ),
            key=lambda item: as_local_datetime(item.start, now.tzinfo),
        )
        if not candidates:
            return None
        return self._to_ha_event(candidates[0], now.tzinfo)

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        if not self.coordinator.data:
            return []
        return [
            self._to_ha_event(event, start_date.tzinfo)
            for event in self.coordinator.data.calendar_events
            if overlaps(event, start_date, end_date, start_date.tzinfo)
        ]

    @staticmethod
    def _to_ha_event(event, tzinfo) -> CalendarEvent:
        if event.all_day:
            start = event.start
            end = event.end
        else:
            start = as_local_datetime(event.start, tzinfo)
            end = as_local_datetime(event.end, tzinfo)
        return CalendarEvent(
            summary=event.title,
            start=start,
            end=end,
            description=event.description,
            location=event.location,
        )
