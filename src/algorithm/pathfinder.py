from typing import List, Tuple
from src.models.network import Network
from src.algorithm.reservation_table import ReservationTable
from src.models.zone import ZoneType

import heapq
from typing import List, Tuple, Dict

class SpaceTimeAStar:
    def __init__(self, network: Network, reservation_table: ReservationTable) -> None:
        self.network = network
        self.res_table = reservation_table
        # Pre-calculate distances from every hub to the end_hub
        self.h_scores: Dict[str, int] = self._precalculate_heuristics()

    def _precalculate_heuristics(self) -> Dict[str, int]:
        """Backward Dijkstra to find the minimum turns to goal for every zone."""
        distances = {name: float('inf') for name in self.network.zones}
        end_zone = self.network.end_zone
        distances[end_zone.name] = 0
        
        pq = [(0, end_zone.name)]
        
        while pq:
            current_dist, u_name = heapq.heappop(pq)
            
            if current_dist > distances[u_name]:
                continue
                
            u_zone = self.network.zones[u_name]
            for v_zone in self.network.get_neighbors(u_zone):
                if v_zone.type == ZoneType.BLOCKED:
                    continue
                
                # Turn cost is based on entering the zone 'u'
                # (Since we are going backwards, we use the cost of the node we came FROM)
                cost = 2 if u_zone.type == ZoneType.RESTRICTED else 1
                
                # Priority optimization: slightly favor priority zones in the heuristic
                # by reducing cost by a tiny fraction (0.99) so the H-score is smaller
                if u_zone.type == ZoneType.PRIORITY:
                    cost = 0.9 

                new_dist = current_dist + cost
                if new_dist < distances[v_zone.name]:
                    distances[v_zone.name] = new_dist
                    heapq.heappush(pq, (new_dist, v_zone.name))
        
        return distances

    def get_h(self, zone_name: str) -> float:
        """Returns the pre-calculated distance to the end_hub."""
        return self.h_scores.get(zone_name, float('inf'))

    def find_path(self, start_zone_name: str, end_zone_name: str, start_turn: int) -> List[Tuple[str, int]]:
        """
        Finds a collision-free path in space-time for a single drone.
        State: (zone_name, turn)
        """
        # (f_score, current_turn, zone_name, path_history)
        start_h = self.h_scores.get(start_zone_name, float('inf'))
        pq = [(start_h + start_turn, start_turn, start_zone_name, [(start_zone_name, start_turn)])]
        
        # Track visited states to prevent loops in space-time
        visited = set()
        
        # Max turn limit to prevent infinite search on unsolvable maps
        max_turn_limit = 200 

        while pq:
            f_score, current_turn, u_name, path = heapq.heappop(pq)

            if u_name == end_zone_name:
                return path

            if (u_name, current_turn) in visited or current_turn > max_turn_limit:
                continue
            visited.add((u_name, current_turn))

            u_zone = self.network.zones[u_name]

            # ACTION 1: Wait in current zone
            # The end_hub allows infinite capacity, start_hub follows occupancy rules after turn 0
            wait_turn = current_turn + 1
            if self.res_table.is_zone_available(u_name, wait_turn, u_zone.max_drones):
                new_path = path + [(u_name, wait_turn)]
                h = self.h_scores.get(u_name, float('inf'))
                heapq.heappush(pq, (wait_turn + h, wait_turn, u_name, new_path))

            # ACTION 2: Move to neighbors
            for v_zone in self.network.get_neighbors(u_zone):
                if v_zone.type == ZoneType.BLOCKED:
                    continue

                # Determine move cost and arrival time
                move_cost = 2 if v_zone.type == ZoneType.RESTRICTED else 1
                arrival_turn = current_turn + move_cost
                
                # Check Zone Capacity at arrival turn
                if not self.res_table.is_zone_available(v_zone.name, arrival_turn, v_zone.max_drones):
                    continue

                # Check Connection Capacity
                # For normal zones, transit happens in 1 turn. 
                # For restricted, transit happens during current_turn + 1.
                connection = self.network.get_connection(u_zone, v_zone)
                if connection:
                    transit_turn = current_turn + 1
                    if not self.res_table.is_connection_available(connection, transit_turn):
                        continue

                # State is valid, add to expansion
                new_path = path + [(v_zone.name, arrival_turn)]
                h = self.h_scores.get(v_zone.name, float('inf'))
                heapq.heappush(pq, (arrival_turn + h, arrival_turn, v_zone.name, new_path))

        return [] # No path found