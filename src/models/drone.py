from src.models.zone import Zone


class Drone:
    """Runtime representation of a single drone in the fleet."""

    def __init__(self, drone_id: str, start_zone: Zone) -> None:
        """Create a drone positioned at `start_zone`.

        Args:
            drone_id: Unique numeric-string identifier (e.g. "1" for `D1`).
            start_zone: The zone the drone begins the simulation in.
        """
        self.drone_id = drone_id
        self.start_zone = start_zone
        self.current_zone = start_zone
        # future: path, state, payload, etc.
