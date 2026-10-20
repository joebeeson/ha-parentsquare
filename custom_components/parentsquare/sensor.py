from __future__ import annotations

from datetime import datetime, timezone

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ParentSquareCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            ParentSquareLatestPostSensor(coordinator, entry),
            ParentSquarePostCountSensor(coordinator, entry),
        ]
    )


class ParentSquareLatestPostSensor(CoordinatorEntity[ParentSquareCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Latest post"
    _attr_icon = "mdi:message-text-outline"

    def __init__(self, coordinator: ParentSquareCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_latest_post"

    @property
    def native_value(self) -> str | None:
        if not self.coordinator.data or not self.coordinator.data.posts:
            return None
        latest = max(
            self.coordinator.data.posts,
            key=lambda post: post.published_at
            or datetime.min.replace(tzinfo=timezone.utc),
        )
        return latest.title or None


class ParentSquarePostCountSensor(CoordinatorEntity[ParentSquareCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Recent post count"
    _attr_icon = "mdi:counter"

    def __init__(self, coordinator: ParentSquareCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_recent_post_count"

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.posts) if self.coordinator.data else 0
