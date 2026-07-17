from src.models.zone import Zone


class Drone:
    """Runtime representation of a single drone in the fleet."""

    def __init__(self, drone_id: str, start_zone: Zone) -> None:
        self.drone_id = drone_id
        self.start_zone = start_zone
        self.current_zone = start_zone
        # future: path, state, payload, etc.
