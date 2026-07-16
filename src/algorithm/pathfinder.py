import heapq
from typing import Dict, List, Tuple

from src.models.network import Network
from src.models.zone import ZoneType
from src.algorithm.reservation_table import ReservationTable


class SpaceTimeAStar:
    def __init__(self, network: Network, reservation_table: ReservationTable) -> None:
        self.network = network
        self.res_table = reservation_table
        self.h_scores: Dict[str, float] = self._precalculate_heuristics()

    def _precalculate_heuristics(self) -> Dict[str, float]:
        """Backward Dijkstra: minimum turns from each zone to the end hub."""
        if self.network.end_zone is None:
            return {}

        distances: Dict[str, float] = {name: float("inf") for name in self.network.zones}
        end_name = self.network.end_zone.name
        distances[end_name] = 0.0
        pq: List[Tuple[float, str]] = [(0.0, end_name)]

        while pq:
            current_dist, u_name = heapq.heappop(pq)
            if current_dist > distances[u_name]:
                continue

            u_zone = self.network.zones[u_name]
            for v_zone in self.network.get_neighbors(u_zone):
                if v_zone.z_type == ZoneType.BLOCKED:
                    continue

                cost = 2.0 if u_zone.z_type == ZoneType.RESTRICTED else 1.0
                if u_zone.z_type == ZoneType.PRIORITY:
                    cost = 0.9

                new_dist = current_dist + cost
                if new_dist < distances[v_zone.name]:
                    distances[v_zone.name] = new_dist
                    heapq.heappush(pq, (new_dist, v_zone.name))

        return distances

    def find_path(
        self, start_zone_name: str, end_zone_name: str, start_turn: int
    ) -> List[Tuple[str, int]]:
        """
        Find a collision-free space-time path for one drone.
        Returns a list of (zone_name, arrival_turn) states.
        """
        start_h = self.h_scores.get(start_zone_name, float("inf"))
        pq: List[Tuple[float, int, str, List[Tuple[str, int]]]] = [
            (start_h + start_turn, start_turn, start_zone_name, [(start_zone_name, start_turn)])
        ]
        visited: set[Tuple[str, int]] = set()
        max_turn_limit = 500
        visited_zones_count: Dict[str, int] = {}  # Track how many times zone is visited in path

        while pq:
            _, current_turn, u_name, path = heapq.heappop(pq)

            if u_name == end_zone_name:
                return path

            if (u_name, current_turn) in visited or current_turn > max_turn_limit:
                continue
            visited.add((u_name, current_turn))

            u_zone = self.network.zones[u_name]

            current_h = self.h_scores.get(u_name, float("inf"))
            
            # Prefer moves over waits by adding a small penalty to waiting
            # This encourages drones to explore alternative paths when congested
            wait_turn = current_turn + 1
            if self.res_table.is_zone_available(u_name, wait_turn, u_zone.max_drones):
                new_path = path + [(u_name, wait_turn)]
                h = self.h_scores.get(u_name, float("inf"))
                wait_penalty = 0.1  # Penalize waiting to prefer movement
                heapq.heappush(pq, (wait_turn + h + wait_penalty, wait_turn, u_name, new_path))

            for v_zone in self.network.get_neighbors(u_zone):
                if v_zone.z_type == ZoneType.BLOCKED:
                    continue

                v_h = self.h_scores.get(v_zone.name, float("inf"))
                
                # Only explore moves that make progress or maintain progress toward goal.
                # Block strictly worse heuristics (dead ends) but allow equal heuristics (alternative paths)
                # This prevents drones from exploring dead ends while allowing path splitting
                if v_h > current_h:
                    continue

                move_cost = 2 if v_zone.z_type == ZoneType.RESTRICTED else 1
                arrival_turn = current_turn + move_cost

                if not self.res_table.is_zone_available(
                    v_zone.name, arrival_turn, v_zone.max_drones
                ):
                    continue

                connection = self.network.get_connection(u_zone, v_zone)
                if connection:
                    transit_turn = current_turn + 1
                    if not self.res_table.is_connection_available(connection, transit_turn):
                        continue

                new_path = path + [(v_zone.name, arrival_turn)]
                h = self.h_scores.get(v_zone.name, float("inf"))
                
                # Penalize revisiting zones to discourage backtracking
                # Count how many times this zone appears in the path
                revisit_count = sum(1 for zone, _ in new_path if zone == v_zone.name)
                revisit_penalty = (revisit_count - 1) * 0.5  # 0 for first visit, 0.5 for second, 1.0 for third, etc.
                
                # Add occupancy bonus to encourage load balancing:
                # Zones with more drones already in them get a small bonus (lower f-score)
                # This helps distribute drones evenly across equally viable paths
                occupancy_count = self.res_table.zone_usage[arrival_turn].get(v_zone.name, 0)
                max_cap = v_zone.max_drones if v_zone.max_drones < float("inf") else 1
                occupancy_bonus = -(occupancy_count / max_cap) * 0.03  # Negative = bonus (lower f_score)
                
                f_score = arrival_turn + h + revisit_penalty + occupancy_bonus
                heapq.heappush(pq, (f_score, arrival_turn, v_zone.name, new_path))

        return []
