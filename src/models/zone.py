from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, PositiveInt, field_validator


class ZoneType(Enum):
    """The four zone kinds recognized by the map format (VII, "Zone types")."""

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class Zone:
    """Runtime representation of a single zone (hub) in the network."""

    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        z_type: ZoneType,
        max_drones: int,
        color: Optional[str],
    ) -> None:
        self.name = name
        self.x = x
        self.y = y
        self.z_type = z_type
        self.max_drones = max_drones
        self.color = color


class ZoneRole(Enum):
    """Whether a zone is the network's start hub, end hub, or a regular hub."""

    START = "start"
    END = "end"
    NORMAL = "normal"


class ZoneModel(BaseModel):
    """Pydantic validation model for a parsed zone definition."""

    name: str
    role: ZoneRole
    x: int
    y: int
    zone: ZoneType = Field(default=ZoneType.NORMAL)
    max_drones: PositiveInt = Field(default=1)
    color: Optional[str] = Field(default=None)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Reject zone names containing dashes or spaces (VII.4)."""
        if "-" in v or " " in v:
            raise ValueError("Zone name cannot contain dashes or spaces")
        return v
