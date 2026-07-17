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

    def _occupancy_bonus(self, zone_name: str, max_drones: int) -> float:
        """
        Small negative f-score bonus for hubs already part of an established
        route (still under capacity), so ties prefer reusing them over
        spilling into an untouched hub. Capped at 1.0 so it can only settle
        genuine ties (h/turn differences are always >= 0.9) and never
        override them. Shared between "wait here" and "move to a neighbor"
        so the two compete on equal footing.
        """
        max_cap = max_drones if max_drones < float("inf") else 1
        occupancy_ratio = min(self.res_table.zone_total_usage.get(zone_name, 0) / max_cap, 1.0)
        return -occupancy_ratio * 0.03

    def find_path(
        self, start_zone_name: str, end_zone_name: str, start_turn: int
    ) -> List[Tuple[str, int]]:
        """
        Find a collision-free space-time path for one drone.
        Returns a list of (zone_name, arrival_turn) states.
        """
        start_zone = self.network.zones[start_zone_name]
        if not self.res_table.is_zone_available(start_zone_name, start_turn, start_zone.max_drones):
            # Every subsequent wait/move is capacity-checked before being
            # queued, but this initial state never was. That's invisible when
            # start_turn is 0 (the start hub is exempt then), but SimulationEngine
            # retries later drones at start_turn > 0 when turn 0 didn't work out,
            # and an earlier drone can legitimately still be waiting in the start
            # hub at that exact turn — so this placement needs the same check.
            return []

        start_h = self.h_scores.get(start_zone_name, float("inf"))
        # move_count (element 3) tracks how many *actual* hub-to-hub transitions
        # a path has taken (waiting in place never increments it). It sits
        # between arrival_turn and zone_name in the sort key so that when two
        # paths are genuinely tied on (f_score, arrival_turn), the one that got
        # there via fewer real moves wins the tie instead of falling through to
        # an arbitrary alphabetical comparison of zone names / path contents.
        # This is what makes "just wait one turn for the direct route to clear"
        # beat "detour through an equally-costed neighbor hub" when both
        # options are otherwise identical.
        pq: List[Tuple[float, int, int, str, List[Tuple[str, int]]]] = [
            (start_h + start_turn, start_turn, 0, start_zone_name, [(start_zone_name, start_turn)])
        ]
        visited: set[Tuple[str, int]] = set()
        max_turn_limit = 500

        while pq:
            _, current_turn, move_count, u_name, path = heapq.heappop(pq)

            if u_name == end_zone_name:
                return path

            if (u_name, current_turn) in visited or current_turn > max_turn_limit:
                continue
            visited.add((u_name, current_turn))

            u_zone = self.network.zones[u_name]

            # Waiting competes with moving on equal footing: same occupancy
            # bonus, no artificial penalty. A flat "prefer moves" penalty used
            # to make ties always resolve in favor of movement, so drones would
            # take equal-cost detours through extra hubs (burning shared zone
            # and connection capacity other drones might need) instead of
            # simply waiting one turn for a busy direct route to free up.
            wait_turn = current_turn + 1
            if self.res_table.is_zone_available(u_name, wait_turn, u_zone.max_drones):
                new_path = path + [(u_name, wait_turn)]
                h = self.h_scores.get(u_name, float("inf"))
                wait_bonus = self._occupancy_bonus(u_name, u_zone.max_drones)
                heapq.heappush(
                    pq,
                    (wait_turn +
                     h +
                     wait_bonus,
                     wait_turn,
                     move_count,
                     u_name,
                     new_path))

            for v_zone in self.network.get_neighbors(u_zone):
                if v_zone.z_type == ZoneType.BLOCKED:
                    continue

                # Deliberately no "only explore if this neighbor's heuristic is no
                # worse than the current zone's" filter here. That used to
                # permanently ban any neighbor whose static per-zone heuristic
                # looked worse than the current one — but a neighbor can
                # have a worse standalone heuristic and *still* be exactly as good
                # once you account for real congestion (e.g. every other gate is
                # momentarily busy, so waiting costs exactly as much as detouring
                # through the "worse" gate). The f-score below already accounts
                # for real arrival turn + heuristic, so it naturally deprioritizes
                # genuinely bad options (dead ends included) without permanently
                # forbidding ones that turn out to be competitive; visited-set and
                # max_turn_limit already bound the search.
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

                # Restricted moves are explicitly recorded as two path entries:
                # first the connection label at the transit turn (the subject
                # requires the drone to be shown occupying the connection,
                # never "nowhere"), then the real zone at the arrival turn.
                # This makes every turn have a first-class, explicit state
                # instead of leaving a gap that downstream code has to infer
                # from the arrival-turn delta.
                if move_cost == 2:
                    transit_label = f"{u_name}-{v_zone.name}"
                    new_path = path + [(transit_label, current_turn + 1),
                                       (v_zone.name, arrival_turn)]
                else:
                    new_path = path + [(v_zone.name, arrival_turn)]
                h = self.h_scores.get(v_zone.name, float("inf"))

                # Penalize revisiting zones to discourage backtracking
                # Count how many times this zone appears in the path
                revisit_count = sum(1 for zone, _ in new_path if zone == v_zone.name)
                # 0 for first visit, 0.5 for second, 1.0 for third, etc.
                revisit_penalty = (revisit_count - 1) * 0.5

                # See _occupancy_bonus: prefer hubs already part of an
                # established route (with room) over spilling into an
                # untouched one, on genuine ties only.
                occupancy_bonus = self._occupancy_bonus(v_zone.name, v_zone.max_drones)

                f_score = arrival_turn + h + revisit_penalty + occupancy_bonus
                heapq.heappush(pq, (f_score, arrival_turn, move_count + 1, v_zone.name, new_path))

        return []
