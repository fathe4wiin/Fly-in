from typing import Dict, Set

class ReservationTable:
    def __init__(self) -> None:
        # turn -> zone_name -> count
        pass

    def is_available(self, zone_name: str, turn: int, max_cap: int) -> bool:
        pass

    def reserve(self, zone_name: str, turn: int) -> None:
        pass