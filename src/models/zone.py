from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, PositiveInt, field_validator, model_validator

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
        self.name = name
        self.x = x
        self.y = y
        self.z_type = z_type
        self.max_drones = max_drones
        self.color = color

class ZoneRole(Enum):
    START = "start"
    END = "end"
    NORMAL = "normal"

class ZoneModel(BaseModel):
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
        if "-" in v or " " in v:
            raise ValueError("Zone name cannot contain dashes or spaces")
        return v
