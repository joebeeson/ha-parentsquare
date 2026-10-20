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
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[ParentSquareCalendar] = []
    if coordinator.include_combined_calendar:
        entities.append(ParentSquareCalendar(coordinator, entry))
    entities.extend(
        ParentSquareCalendar(coordinator, entry, school_id=school.id, school_name=school.name)
        for school in coordinator.data.schools
    )
    async_add_entities(entities)


class ParentSquareCalendar(CoordinatorEntity[ParentSquareCoordinator], CalendarEntity):
    _attr_has_entity_name = True
    _attr_name = "Calendar"
    _attr_icon = "mdi:school"

    def __init__(
        self,
        coordinator: ParentSquareCoordinator,
        entry: ConfigEntry,
        *,
        school_id: int | None = None,
        school_name: str | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._school_id = school_id
        self._attr_name = f"{school_name} Calendar" if school_name else "Calendar"
        self._attr_unique_id = (
            f"{entry.entry_id}_calendar_school_{school_id}"
            if school_id is not None
            else f"{entry.entry_id}_calendar"
        )

    @property
    def _events(self):
        if not self.coordinator.data:
            return ()
        if self._school_id is None:
            return self.coordinator.data.calendar_events
        return tuple(
            event
            for event in self.coordinator.data.calendar_events
            if event.school_id == self._school_id
        )

    @property
    def event(self) -> CalendarEvent | None:
        now = dt_util.now()
        candidates = sorted(
            (event for event in self._events if as_local_datetime(event.end, now.tzinfo) > now),
            key=lambda item: as_local_datetime(item.start, now.tzinfo),
        )
        if not candidates:
            return None
        return self._to_ha_event(candidates[0], now.tzinfo)

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        return [
            self._to_ha_event(event, start_date.tzinfo)
            for event in self._events
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
