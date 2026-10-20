from __future__ import annotations

from collections.abc import Iterable, Mapping

from parentsquare import Group, Post, School

from .const import CONF_GROUP_KEYS, CONF_SCHOOL_IDS


def selected_schools(schools: Iterable[School], options: Mapping[str, object]) -> list[School]:
    """Return configured schools, preserving discovery order.

    Missing options means an entry created before the options flow existed and
    therefore keeps the original all-schools behavior. An empty configured
    selection also falls back to all schools so a stale or hand-edited entry
    cannot silently stop polling.
    """
    discovered = list(schools)
    configured = options.get(CONF_SCHOOL_IDS)
    if not isinstance(configured, (list, tuple, set)) or not configured:
        return discovered
    allowed = {str(value) for value in configured}
    return [school for school in discovered if str(school.id) in allowed]


def group_key(group: Group) -> str:
    """Return a stable option value for a group within its school."""
    return f"{group.school_id}:{group.id}"


def selected_groups(groups: Iterable[Group], options: Mapping[str, object]) -> list[Group]:
    discovered = list(groups)
    if CONF_GROUP_KEYS not in options:
        # Entries created before group selection existed keep the useful
        # all-groups behavior.  The options flow writes an explicit list when
        # a user wants to narrow or disable group feeds.
        return discovered
    configured = options.get(CONF_GROUP_KEYS)
    if not isinstance(configured, (list, tuple, set)):
        return []
    allowed = {str(value) for value in configured}
    return [group for group in discovered if group_key(group) in allowed]


def merge_posts(*post_lists: Iterable[Post]) -> list[Post]:
    """Merge school and selected-group feeds without duplicate post IDs."""
    merged: list[Post] = []
    indexes: dict[str, int] = {}
    for posts in post_lists:
        for post in posts:
            index = indexes.get(post.id)
            if index is None:
                indexes[post.id] = len(merged)
                merged.append(post)
            elif merged[index].group_id is None and post.group_id is not None:
                # A school feed and a group feed can contain the same post.
                # Keep the richer group source metadata when it is available.
                merged[index] = post
    return merged
