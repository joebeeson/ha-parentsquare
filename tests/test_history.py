from custom_components.parentsquare.history import PostHistory


def test_history_baselines_and_deduplicates() -> None:
    history = PostHistory(["old"])
    assert history.add(["old", "new", "new"]) == ["new"]
    assert history.post_ids == ["old", "new"]


def test_history_is_bounded() -> None:
    history = PostHistory(limit=2)
    history.add(["1", "2", "3"])
    assert history.post_ids == ["2", "3"]
