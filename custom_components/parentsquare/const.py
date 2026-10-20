from datetime import timedelta

DOMAIN = "parentsquare"
PLATFORMS = ["calendar", "event", "sensor"]
DEFAULT_SCAN_INTERVAL = timedelta(minutes=15)
STORAGE_VERSION = 1
STORAGE_KEY_PREFIX = "parentsquare.post_history"
EVENT_TYPE_POST = "post"
