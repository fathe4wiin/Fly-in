from typing import Dict, List, Optional

from pydantic import BaseModel, PositiveInt, model_validator

from src.models.connection import Connection, ConnectionModel
from src.models.drone import Drone
from src.models.zone import Zone, ZoneModel, ZoneRole


class Network:
    """Hand-rolled graph of zones and connections, plus the drone fleet."""

    def __init__(self) -> None:
        self.zones: Dict[str, Zone] = {}
        self.connections: List[Connection] = []
        self.drones: List[Drone] = []
        self.start_zone: Optional[Zone] = None
        self.end_zone: Optional[Zone] = None

    def get_neighbors(self, zone: Zone) -> List[Zone]:
        """Return every zone directly connected to `zone`."""
        neighbors = []
        for connection in self.connections:
            if connection.zone_a == zone:
                neighbors.append(connection.zone_b)
            elif connection.zone_b == zone:
                neighbors.append(connection.zone_a)
        return neighbors

    def get_connection(self, zone_a: Zone, zone_b: Zone) -> Optional[Connection]:
        """Return the connection between `zone_a` and `zone_b`, if any."""
        for connection in self.connections:
            if (
                (connection.zone_a == zone_a and connection.zone_b == zone_b)
                or (connection.zone_a == zone_b and connection.zone_b == zone_a)
            ):
                return connection
        return None


class NetworkModel(BaseModel):
    """Pydantic validation model for the whole parsed network."""

    nb_drones: PositiveInt
    zones: Dict[str, ZoneModel]
    connections: List[ConnectionModel]

    @model_validator(mode="after")
    def validate_integrity(self) -> "NetworkModel":
        """Cross-field checks pydantic's per-field validation can't express."""
        # 1. Check for presence of required hub roles
        roles = [z.role for z in self.zones.values()]
        if ZoneRole.START not in roles:
            raise ValueError("Network missing start_hub")
        if ZoneRole.END not in roles:
            raise ValueError("Network missing end_hub")

        # 2. Validate connection endpoints
        for conn in self.connections:
            if conn.node_a not in self.zones:
                raise ValueError(f"Connection references undefined zone: {conn.node_a}")
            if conn.node_b not in self.zones:
                raise ValueError(f"Connection references undefined zone: {conn.node_b}")
            if conn.node_a == conn.node_b:
                raise ValueError(f"Self-connection detected on zone: {conn.node_a}")

        # 3. Coordinate collision check
        coords = [z.x for z in self.zones.values()], [z.y for z in self.zones.values()]
        points = list(zip(*coords))
        if len(points) != len(set(points)):
            raise ValueError("Multiple zones share the same coordinates")

        return self
