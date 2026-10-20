from __future__ import annotations

from homeassistant.components.event import EventEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, EVENT_TYPE_POST
from .coordinator import ParentSquareCoordinator
from .helpers import post_event_attributes


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([ParentSquarePostEvent(hass.data[DOMAIN][entry.entry_id], entry)])


class ParentSquarePostEvent(
    CoordinatorEntity[ParentSquareCoordinator], EventEntity
):
    _attr_has_entity_name = True
    _attr_name = "New post"
    _attr_icon = "mdi:school-outline"
    _attr_event_types = [EVENT_TYPE_POST]

    def __init__(self, coordinator: ParentSquareCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_new_post"

    @callback
    def _handle_coordinator_update(self) -> None:
        if self.coordinator.data:
            for post in self.coordinator.data.new_posts:
                self._trigger_event(EVENT_TYPE_POST, post_event_attributes(post))
            if self.coordinator.data.new_posts:
                self.async_write_ha_state()
        super()._handle_coordinator_update()
