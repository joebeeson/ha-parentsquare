from datetime import datetime, timezone

from parentsquare import Group, Post, School

from custom_components.parentsquare.const import CONF_INCLUDE_UNASSIGNED_GROUPS
from custom_components.parentsquare.selection import (
    group_key,
    merge_posts,
    selected_groups,
    selected_schools,
)


def test_school_selection_defaults_to_all_and_preserves_order() -> None:
    schools = [School(101, "Middle"), School(202, "Elementary")]

    assert selected_schools(schools, {}) == schools
    assert selected_schools(schools, {"school_ids": ["202"]}) == [schools[1]]


def test_group_selection_is_scoped_by_school_and_stable_key() -> None:
    groups = [
        Group(55, "Cooking Club", 101, "Middle"),
        Group(56, "Robotics", 101, "Middle", student_ids=(7,)),
    ]

    assert group_key(groups[0]) == "101:55"
    assert selected_groups(groups, {}) == [groups[1]]
    assert selected_groups(groups, {CONF_INCLUDE_UNASSIGNED_GROUPS: True}) == groups
    assert selected_groups(groups, {"group_keys": []}) == []
    assert selected_groups(groups, {"group_keys": ["101:56"]}) == [groups[1]]
    assert selected_groups(groups, {"group_keys": ["101:55"]}) == []
    assert selected_groups(
        groups,
        {"group_keys": ["101:55"], CONF_INCLUDE_UNASSIGNED_GROUPS: True},
    ) == [groups[0]]


def test_merge_posts_deduplicates_overlapping_school_and_group_feeds() -> None:
    first = Post(
        "1",
        "First",
        None,
        datetime(2026, 10, 20, tzinfo=timezone.utc),
        "https://example.test/1",
        101,
        "Middle",
    )
    duplicate = first
    second = Post(
        "2",
        "Second",
        None,
        datetime(2026, 10, 21, tzinfo=timezone.utc),
        "https://example.test/2",
        101,
        "Middle",
        group_id=55,
    )

    enriched = Post(
        "1",
        "First",
        None,
        datetime(2026, 10, 20, tzinfo=timezone.utc),
        "https://example.test/1",
        101,
        "Middle",
        group_id=55,
        group_name="Cooking Club",
    )

    assert merge_posts([first], [duplicate, second]) == [first, second]
    assert merge_posts([first], [enriched])[0] == enriched
