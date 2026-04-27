from enum import Enum
from typing import Optional

class ZoneType(Enum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"

class Zone:
    def __init__(
        self, 
        name: str, 
        x: int, 
        y: int, 
        z_type: ZoneType, 
        max_drones: int, 
        color: Optional[str]
    ) -> None:
        pass