from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from parentsquare import Post

from .const import DOMAIN
from .coordinator import ParentSquareCoordinator
from .helpers import post_event_attributes

_RECENT_POST_LIMIT = 20


def _post_sort_key(post: Post) -> datetime:
    return post.published_at or datetime.min.replace(tzinfo=timezone.utc)


def _latest_post(posts: tuple[Post, ...] | list[Post]) -> Post | None:
    return max(posts, key=_post_sort_key) if posts else None


def _post_record(post: Post, *, include_excerpt: bool = False) -> dict[str, Any]:
    record = post_event_attributes(post)
    if include_excerpt and post.summary:
        excerpt = " ".join(post.summary.split())
        record["excerpt"] = excerpt[:240] + ("…" if len(excerpt) > 240 else "")
    return record


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [
        ParentSquareLatestPostSensor(coordinator, entry),
        ParentSquarePostCountSensor(coordinator, entry),
        ParentSquareRecentPostsSensor(coordinator, entry),
    ]
    for school in coordinator.data.schools:
        entities.extend(
            (
                ParentSquareSourceLatestSensor(
                    coordinator,
                    entry,
                    source_kind="school",
                    source_id=str(school.id),
                    source_name=school.name,
                    school_id=school.id,
                ),
                ParentSquareSourceCountSensor(
                    coordinator,
                    entry,
                    source_kind="school",
                    source_id=str(school.id),
                    source_name=school.name,
                    school_id=school.id,
                ),
            )
        )
    for group in coordinator.data.groups:
        entities.extend(
            (
                ParentSquareSourceLatestSensor(
                    coordinator,
                    entry,
                    source_kind="group",
                    source_id=f"{group.school_id}_{group.id}",
                    source_name=group.name,
                    school_id=group.school_id,
                    group_id=group.id,
                    student_ids=group.student_ids,
                ),
                ParentSquareSourceCountSensor(
                    coordinator,
                    entry,
                    source_kind="group",
                    source_id=f"{group.school_id}_{group.id}",
                    source_name=group.name,
                    school_id=group.school_id,
                    group_id=group.id,
                    student_ids=group.student_ids,
                ),
            )
        )
    async_add_entities(entities)


class ParentSquareLatestPostSensor(CoordinatorEntity[ParentSquareCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Latest post"
    _attr_icon = "mdi:message-text-outline"

    def __init__(self, coordinator: ParentSquareCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_latest_post"

    @property
    def _latest(self) -> Post | None:
        return _latest_post(self.coordinator.data.posts) if self.coordinator.data else None

    @property
    def native_value(self) -> str | None:
        latest = self._latest
        return latest.title or None if latest else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        latest = self._latest
        return _post_record(latest) if latest else {}


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


class ParentSquareRecentPostsSensor(CoordinatorEntity[ParentSquareCoordinator], SensorEntity):
    """A bounded, clickable feed for dashboards and templates."""

    _attr_has_entity_name = True
    _attr_name = "Recent posts"
    _attr_icon = "mdi:message-text-multiple-outline"

    def __init__(self, coordinator: ParentSquareCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_recent_posts"

    @property
    def native_value(self) -> int:
        return (
            min(len(self.coordinator.data.posts), _RECENT_POST_LIMIT)
            if self.coordinator.data
            else 0
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if not self.coordinator.data:
            return {"posts": []}
        posts = sorted(self.coordinator.data.posts, key=_post_sort_key, reverse=True)
        return {
            "posts": [
                _post_record(post, include_excerpt=True) for post in posts[:_RECENT_POST_LIMIT]
            ]
        }


class _ParentSquareSourceSensor(CoordinatorEntity[ParentSquareCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ParentSquareCoordinator,
        entry: ConfigEntry,
        *,
        source_kind: str,
        source_id: str,
        source_name: str,
        school_id: int,
        group_id: int | None = None,
        student_ids: tuple[int, ...] = (),
    ) -> None:
        super().__init__(coordinator)
        self._source_kind = source_kind
        self._source_id = source_id
        self._school_id = school_id
        self._group_id = group_id
        self._student_ids = student_ids
        self._attr_name = f"{source_name} {self._name_suffix}"
        self._attr_unique_id = f"{entry.entry_id}_{source_kind}_{source_id}_{self._unique_suffix}"

    @property
    def _name_suffix(self) -> str:
        return "posts"

    @property
    def _unique_suffix(self) -> str:
        return "posts"

    @property
    def _posts(self) -> tuple[Post, ...]:
        if not self.coordinator.data:
            return ()
        if self._group_id is not None:
            return tuple(
                post
                for post in self.coordinator.data.posts
                if post.school_id == self._school_id and post.group_id == self._group_id
            )
        return tuple(
            post for post in self.coordinator.data.posts if post.school_id == self._school_id
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        latest = _latest_post(self._posts)
        attrs: dict[str, Any] = {
            "source_type": self._source_kind,
            "source_id": self._source_id,
            "school_id": self._school_id,
        }
        if self._group_id is not None:
            attrs["group_id"] = self._group_id
            attrs["student_ids"] = list(self._student_ids)
        if latest:
            attrs.update(_post_record(latest))
        return attrs


class ParentSquareSourceLatestSensor(_ParentSquareSourceSensor):
    _attr_icon = "mdi:message-text-outline"

    @property
    def _name_suffix(self) -> str:
        return "latest post"

    @property
    def _unique_suffix(self) -> str:
        return "latest_post"

    @property
    def native_value(self) -> str | None:
        latest = _latest_post(self._posts)
        return latest.title or None if latest else None


class ParentSquareSourceCountSensor(_ParentSquareSourceSensor):
    _attr_icon = "mdi:counter"

    @property
    def _name_suffix(self) -> str:
        return "post count"

    @property
    def _unique_suffix(self) -> str:
        return "post_count"

    @property
    def native_value(self) -> int:
        return len(self._posts)
