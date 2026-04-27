from src.models.network import Network
from typing import Tuple

class MapParser:
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.start_hubs = 0
        self.end_hubs = 0
        self.self.raw_base = {}

    def parse_phase_one(self) -> None:
        """Returns the network and number of drones."""


        # self.raw_base = {
        #     "nb_drones": 0,  # Must be > 0
        #     "start_hub": "", # Must be set exactly once
        #     "end_hub": "",   # Must be set exactly once
        #     "zones": {
        #         # Keyed by zone name to enforce uniqueness and allow O(1) lookup
        #         "zone_name": {
        #             "type": "normal",  # normal, restricted, priority, blocked
        #             "coords": (0, 0),  # (x, y)
        #             "max_drones": 1,   # Must be > 0
        #             "color": None      # Optional string
        #         }
        #     },
        #     "connections": [
        #         # List of validated connections
        #         {
        #             "endpoints": {"zone_a", "zone_b"},  # Use a set to prevent directional duplicates
        #             "max_link_capacity": 1              # Must be > 0
        #         }
        #     ]
        # }

        self.self.raw_base = {
            "nb_drones": "",          # Raw string: "5"
            "start_hub_raw": "",      # Raw string: "hub_name 0 0 [metadata]"
            "end_hub_raw": "",        # Raw string: "goal_name 10 10 [metadata]"
            "hubs_raw": [],           # List of raw strings: ["roof1 3 4 [meta]", ...]
            "connections_raw": []     # List of raw strings: ["hub-roof1 [meta]", ...]
        }

        fmap = open(self.file_path, "r")
        for line_num, line in enumerate(fmap, 1):
            clean_line = line.strip()
            
            # 1. Skip empty lines and comments
            if not clean_line or clean_line.startswith("#"):
                continue
                
            # 2. Handle nb_drones (the only line with a colon suffix in the prefix)
            if clean_line.startswith("nb_drones:"):
                try:
                    value = clean_line.split(":")[1].strip()
                    self.raw_base["nb_drones"] = int(value)
                except (IndexError, ValueError):
                    raise ValueError(f"Line {line_num}: Invalid drone count")
                continue

            # 3. Handle other prefixes (hubs and connections)
            # Use split(" ", 1) for hubs: "hub: name x y [meta]"
            if clean_line.startswith("start_hub:"):
                self.start_hubs += 1
                try:
                    value = clean_line.split(":", 1)[1].strip()
                    self.raw_base["start_hub_raw"] = value
                except (IndexError, ValueError):
                    raise ValueError(f"Line {line_num}: Invalid `starthub` coords")
                continue
            if clean_line.startswith("end_hub:"):
                self.end_hubs += 1
                try:
                    value = clean_line.split(":", 1)[1].strip()
                    self.raw_base["end_hub_raw"] = value
                except (IndexError, ValueError):
                    raise ValueError(f"line {line_num}: Invalud `end_hub` coords")
                continue
            if clean_line.startswith("hub"):
                try:
                    value = clean_line.split(":", 1)[1].strip()
                    self.raw_base["hubs_raw"].append(value)
                except (IndexError, ValueError):
                    raise ValueError(f"Line {line_num}: Invalid `hub` coords")
                continue
            if (self.start_hubs > 1 or self.end_hubs > 1):
                raise ValueError(f"Multiple hubs detected: start {self.start_hubs}, end {self.end_hubs}")


    def parse_phase_two(self):
        pass
