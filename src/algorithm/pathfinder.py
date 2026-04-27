from typing import List, Tuple
from src.models.network import Network
from src.algorithm.reservation_table import ReservationTable

class SpaceTimeAStar:
    def __init__(self, network: Network, reservation_table: ReservationTable) -> None:
        pass

    def find_path(self, start_zone_name: str, end_zone_name: str, start_turn: int) -> List[Tuple[str, int]]:
        """Returns a list of (zone_name, arrival_turn)."""
        pass