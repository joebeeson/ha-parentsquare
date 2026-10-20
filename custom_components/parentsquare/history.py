from __future__ import annotations

from collections.abc import Iterable


class PostHistory:
    """Bounded post-ID history used to make polling idempotent."""

    def __init__(self, post_ids: Iterable[str] = (), *, limit: int = 500) -> None:
        self.limit = limit
        self._post_ids = list(dict.fromkeys(post_ids))[-limit:]

    @property
    def post_ids(self) -> list[str]:
        return list(self._post_ids)

    def add(self, post_ids: Iterable[str]) -> list[str]:
        new_ids: list[str] = []
        known = set(self._post_ids)
        for post_id in post_ids:
            value = post_id
            if value not in known:
                new_ids.append(value)
                known.add(value)
                self._post_ids.append(value)
        if len(self._post_ids) > self.limit:
            self._post_ids = self._post_ids[-self.limit :]
        return new_ids
