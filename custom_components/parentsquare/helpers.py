from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any

from parentsquare import CalendarEvent, Post


def post_event_attributes(post: Post) -> dict[str, Any]:
    """Return the deliberately small, privacy-conscious event payload."""
    return {
        "id": post.id,
        "title": post.title,
        "author": post.author,
        "published_at": post.published_at.isoformat() if post.published_at else None,
        "source_url": post.source_url,
        "school_id": post.school_id,
        "school_name": post.school_name,
    }


def as_local_datetime(value: date | datetime, tzinfo) -> datetime:
    if isinstance(value, datetime):
        return value.astimezone(tzinfo) if value.tzinfo else value.replace(tzinfo=tzinfo)
    return datetime.combine(value, time.min, tzinfo=tzinfo)


def overlaps(event: CalendarEvent, start: datetime, end: datetime, tzinfo) -> bool:
    event_start = as_local_datetime(event.start, tzinfo)
    event_end = as_local_datetime(event.end, tzinfo)
    return event_start < end and event_end > start
