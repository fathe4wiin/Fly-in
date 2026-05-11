from src.models.zone import Zone
from pydantic import BaseModel, PositiveInt, Field

class Connection:
    def __init__(self, zone_a: Zone, zone_b: Zone, max_link_capacity: int) -> None:
        pass




class ConnectionModel(BaseModel):
    node_a: str
    node_b: str
    max_link_capacity: PositiveInt = Field(default=1)


