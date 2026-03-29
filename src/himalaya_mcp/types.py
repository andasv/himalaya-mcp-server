import os
from enum import Enum


class Mode(Enum):
    READONLY = "readonly"
    FULL = "full"
    DANGERZONE = "dangerzone"


DANGER_WRITE = "[DANGER: WRITE]"
DANGER_SEND = "[DANGERZONE: SENDS EMAIL]"

SEND_TIMEOUT = int(os.environ.get("HIMALAYA_SEND_TIMEOUT", "15"))
