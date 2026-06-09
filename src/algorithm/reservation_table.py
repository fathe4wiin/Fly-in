from collections import defaultdict
from typing import Dict, List, Tuple

from src.models.connection import Connection
from src.models.network import Network


class ReservationTable:
    """Tracks zone and connection occupancy per simulation turn."""

    def __init__(self, network: Network) -> None:
        self.network = network
        self.zone_usage: Dict[int, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.conn_usage: Dict[int, Dict[Tuple[str, str], int]] = defaultdict(
            lambda: defaultdict(int)
        )

    def _connection_key(self, connection: Connection) -> Tuple[str, str]:
        return tuple(sorted((connection.zone_a.name, connection.zone_b.name)))

    def is_zone_available(self, zone_name: str, turn: int, max_cap: int) -> bool:
        if self.network.end_zone and zone_name == self.network.end_zone.name:
            return True
        if (
            self.network.start_zone
            and zone_name == self.network.start_zone.name
            and turn == 0
        ):
            return True
        return self.zone_usage[turn][zone_name] < max_cap

    def is_connection_available(self, connection: Connection, turn: int) -> bool:
        key = self._connection_key(connection)
        return self.conn_usage[turn][key] < connection.max_link_capacity

    def reserve_zone(self, zone_name: str, turn: int) -> None:
        self.zone_usage[turn][zone_name] += 1

    def reserve_connection(self, connection: Connection, turn: int) -> None:
        key = self._connection_key(connection)
        self.conn_usage[turn][key] += 1

    def reserve_path(self, path: List[Tuple[str, int]]) -> None:
        """Reserve all zone and connection slots used by a space-time path."""
        if not path:
            return

        for zone_name, turn in path:
            self.reserve_zone(zone_name, turn)

        for i in range(len(path) - 1):
            z0, t0 = path[i]
            z1, t1 = path[i + 1]
            if z0 == z1:
                continue

            zone_a = self.network.zones[z0]
            zone_b = self.network.zones[z1]
            connection = self.network.get_connection(zone_a, zone_b)
            if connection is None:
                continue

            if t1 - t0 == 1:
                self.reserve_connection(connection, t0 + 1)
            elif t1 - t0 == 2:
                self.reserve_connection(connection, t0 + 1)
