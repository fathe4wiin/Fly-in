from src.models.zone import Zone
from pydantic import BaseModel, PositiveInt, Field


class Connection:
    def __init__(self, zone_a: Zone, zone_b: Zone, max_link_capacity: int) -> None:
        self.zone_a = zone_a
        self.zone_b = zone_b
        self.max_link_capacity = max_link_capacity
        # convenience properties
        self.nodes = (zone_a.name, zone_b.name)


class ConnectionModel(BaseModel):
    node_a: str
    node_b: str
    max_link_capacity: PositiveInt = Field(default=1)
