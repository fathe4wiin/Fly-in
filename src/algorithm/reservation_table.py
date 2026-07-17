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
        # Cumulative reservations per zone across *all* turns. Unlike zone_usage
        # (which is keyed per turn and only says whether a zone is full at one
        # specific instant), this tracks whether a zone is already part of an
        # established route at all, regardless of which turn each drone passes
        # through it. Used to bias tie-breaks toward reusing hubs that already
        # have capacity committed instead of spilling into untouched ones.
        self.zone_total_usage: Dict[str, int] = defaultdict(int)

    def _connection_key(self, connection: Connection) -> Tuple[str, str]:
        name_a, name_b = sorted((connection.zone_a.name, connection.zone_b.name))
        return (name_a, name_b)

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
        self.zone_total_usage[zone_name] += 1

    def reserve_connection(self, connection: Connection, turn: int) -> None:
        key = self._connection_key(connection)
        self.conn_usage[turn][key] += 1

    def _connection_from_label(self, label: str) -> Connection | None:
        """Resolve a "zoneA-zoneB" transit label (see SpaceTimeAStar.find_path)
        back to its Connection object."""
        if "-" not in label:
            return None
        zone_a_name, zone_b_name = label.split("-", 1)
        if zone_a_name not in self.network.zones or zone_b_name not in self.network.zones:
            return None
        return self.network.get_connection(
            self.network.zones[zone_a_name], self.network.zones[zone_b_name]
        )

    def reserve_path(self, path: List[Tuple[str, int]]) -> None:
        """Reserve all zone and connection slots used by a space-time path.

        A path entry is either a real zone name (occupying that zone at that
        turn) or a "zoneA-zoneB" transit label (occupying that connection at
        that turn, while in flight toward a restricted zone). Only real zones
        consume zone capacity.
        """
        if not path:
            return

        for name, turn in path:
            if name in self.network.zones:
                self.reserve_zone(name, turn)

        for i in range(len(path) - 1):
            z0, t0 = path[i]
            z1, t1 = path[i + 1]
            if z0 == z1:
                continue

            if z0 in self.network.zones and z1 in self.network.zones:
                # Single-turn move directly between two real zones.
                connection = self.network.get_connection(
                    self.network.zones[z0], self.network.zones[z1]
                )
            elif z0 in self.network.zones:
                # z1 is the transit label for a restricted move starting here.
                connection = self._connection_from_label(z1)
            else:
                # z0 is a transit label; the connection was already reserved
                # when it was pushed above (arriving at z1 reserves no link).
                continue

            if connection is not None:
                self.reserve_connection(connection, t1)
