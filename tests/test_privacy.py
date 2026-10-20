from datetime import datetime, timezone

from parentsquare import Post

from custom_components.parentsquare.helpers import post_event_attributes


def test_event_attributes_do_not_include_body_or_attachments() -> None:
    post = Post(
        id="123",
        title="Field trip",
        author="School Office",
        published_at=datetime(2026, 10, 20, tzinfo=timezone.utc),
        source_url="https://www.parentsquare.com/feeds/123",
        school_id=101,
        school_name="School",
        summary="Private body text",
    )
    attrs = post_event_attributes(post)
    assert attrs["id"] == "123"
    assert "summary" not in attrs
    assert "body" not in attrs
    assert "attachments" not in attrs
    assert "group_name" in attrs
