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
        # Priority Queue stores: (f_score, current_turn, zone_name, path_history)
        # G-score = current_turn
        # H-score = self.get_h(zone_name)
        # F-score = G + H
        pass