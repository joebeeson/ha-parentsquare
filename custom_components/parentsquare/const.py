from datetime import timedelta

DOMAIN = "parentsquare"
PLATFORMS = ["calendar", "event", "sensor"]
DEFAULT_SCAN_INTERVAL = timedelta(minutes=15)
STORAGE_VERSION = 1
STORAGE_KEY_PREFIX = "parentsquare.post_history"
EVENT_TYPE_POST = "post"

# Config-entry options. Values are strings because Home Assistant selectors
# serialize their choices as strings, while the ParentSquare client uses ints.
CONF_SCHOOL_IDS = "school_ids"
CONF_INCLUDE_COMBINED_CALENDAR = "include_combined_calendar"
CONF_GROUP_KEYS = "group_keys"
CONF_INCLUDE_UNASSIGNED_GROUPS = "include_unassigned_groups"
