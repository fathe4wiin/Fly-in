from typing import List, Tuple
from src.models.zone import Zone

class Drone:
    def __init__(self, drone_id: str, start_zone: Zone) -> None:
        self.drone_id = drone_id
        self.start_zone = start_zone
        self.current_zone = start_zone
        # future: path, state, payload, etc.