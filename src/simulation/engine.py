from typing import Any, Dict, List, Tuple

from src.algorithm.pathfinder import SpaceTimeAStar
from src.algorithm.reservation_table import ReservationTable
from src.models.network import Network


class SimulationEngine:
    def __init__(
        self,
        network: Network,
        nb_drones: int,
        visualizer: Any | None = None,
    ) -> None:
        self.network = network
        self.nb_drones = nb_drones
        self.visualizer = visualizer
        self.res_table = ReservationTable(network)
        self.pathfinder = SpaceTimeAStar(network, self.res_table)
        self.drone_paths: Dict[str, List[Tuple[str, int]]] = {}

        if self.visualizer is not None:
            self.visualizer.set_zone_costs(self.pathfinder.h_scores)

    def _plan_paths(self) -> None:
        if self.network.start_zone is None or self.network.end_zone is None:
            raise ValueError("Network must define start_hub and end_hub")

        start_name = self.network.start_zone.name
        end_name = self.network.end_zone.name

        for drone in self.network.drones:
            path: List[Tuple[str, int]] = []
            start_turn = 0
            while not path and start_turn < 200:
                path = self.pathfinder.find_path(start_name, end_name, start_turn)
                if not path:
                    start_turn += 1
            if not path:
                raise ValueError(f"No valid path found for drone D{drone.drone_id}")
            self.res_table.reserve_path(path)
            self.drone_paths[drone.drone_id] = path

    def _build_turn_events(self) -> Dict[int, List[str]]:
        """Map simulation turns to movement tokens (D<ID>-<zone|connection>).

        Each path entry is already an explicit state for its turn (a real
        zone, or a "zoneA-zoneB" transit label while in flight toward a
        restricted zone — see SpaceTimeAStar.find_path), so every state
        change simply becomes a D<ID>-<state> token at that turn.
        """
        events: Dict[int, List[str]] = {}

        for drone in self.network.drones:
            path = self.drone_paths.get(drone.drone_id, [])
            label = f"D{drone.drone_id}"

            for i in range(len(path) - 1):
                z0, t0 = path[i]
                z1, t1 = path[i + 1]
                if z0 == z1:
                    continue
                events.setdefault(t1, []).append(f"{label}-{z1}")

        return events

    def _drone_positions_at_turn(self, turn: int) -> Dict[str, str]:
        """Each drone's explicit state (zone, or in-flight connection label)
        as of the given turn, read directly from its planned path."""
        positions: Dict[str, str] = {}

        for drone in self.network.drones:
            label = f"D{drone.drone_id}"
            path = self.drone_paths.get(drone.drone_id, [])
            state_at_turn = None
            for state, arrival in path:
                if arrival <= turn:
                    state_at_turn = state

            if state_at_turn:
                positions[label] = state_at_turn
        return positions

    def _build_frames(self, max_turn: int) -> List[Dict[str, str]]:
        return [self._drone_positions_at_turn(t) for t in range(0, max_turn + 1)]

    def run(self) -> None:
        """Plan paths, simulate turn-by-turn, and print subject output format."""
        self._plan_paths()
        events = self._build_turn_events()

        if not events:
            return

        max_turn = max(events.keys())

        for turn in range(1, max_turn + 1):
            if turn in events:
                print(" ".join(events[turn]))

        total_turns = max_turn
        avg_turns = total_turns / self.nb_drones if self.nb_drones else 0.0
        print(f"# Simulation complete in {total_turns} turns")
        print(f"# Drones: {self.nb_drones}, avg turns/drone: {avg_turns:.2f}")

        if self.visualizer:
            frames = self._build_frames(max_turn)
            self.visualizer.load_playback(frames, events, max_turn)
            self.visualizer.run_playback()
