from src.models.zone import Zone
from pydantic import BaseModel, PositiveInt, Field


class Connection:
    """Runtime representation of a bidirectional edge between two zones."""

    def __init__(self, zone_a: Zone, zone_b: Zone, max_link_capacity: int) -> None:
        """Create a connection between two zones.

        Args:
            zone_a: One endpoint of the connection.
            zone_b: The other endpoint of the connection.
            max_link_capacity: Maximum drones allowed to traverse this
                connection simultaneously.
        """
        self.zone_a = zone_a
        self.zone_b = zone_b
        self.max_link_capacity = max_link_capacity
        # convenience properties
        self.nodes = (zone_a.name, zone_b.name)


class ConnectionModel(BaseModel):
    """Pydantic validation model for a parsed connection definition."""

    node_a: str
    node_b: str
    max_link_capacity: PositiveInt = Field(default=1)
