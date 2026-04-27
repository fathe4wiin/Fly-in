from typing import Dict, List
from src.models.zone import Zone
from src.models.connection import Connection

class Network:
    def __init__(self) -> None:
        self.zones: Dict[str, Zone] = {}
        self.connections: List[Connection] = []
        self.start_zone: Optional[Zone] = None
        self.end_zone: Optional[Zone] = None