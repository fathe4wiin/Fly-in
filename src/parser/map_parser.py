import re
from typing import Dict


class MapParser:
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.raw_base = {}
        self.structured_data = {}


    def run(self):
        self.parse_phase_one()
        self.parse_phase_two()
        self.handle_metadata()

    def parse_phase_one(self) -> None:
        """Stage 1: Categorize lines into raw strings based on prefix."""
        start_hubs = 0
        end_hubs = 0
        # store raw values along with their source line numbers for better errors
        self.raw_base = {
            "nb_drones": ("", 0),
            "start_hub_raw": ("", 0),
            "end_hub_raw": ("", 0),
            "hubs_raw": [],  # list of (raw_str, line_num)
            "connections_raw": []  # list of (raw_str, line_num)
        }

        # track seen zone names so we can enforce connection ordering
        encountered_zones = set()
        # track seen undirected edges to reject duplicates (A-B and B-A)
        seen_edges = set()

        with open(self.file_path, "r") as fmap:
            for line_num, line in enumerate(fmap, 1):
                clean_line = line.strip()
                if not clean_line or clean_line.startswith("#"):
                    continue
                
                prefix, _, value = clean_line.partition(":")
                prefix = prefix.strip()
                value = value.strip()

                if prefix == "nb_drones":
                    # must be defined only once
                    if self.raw_base["nb_drones"][0]:
                        raise ValueError(f"Line {line_num}: Multiple nb_drones definitions")
                    self.raw_base["nb_drones"] = (value, line_num)
                elif prefix == "start_hub":
                    if start_hubs > 0:
                        raise ValueError(f"Line {line_num}: Multiple start hubs")
                    start_hubs += 1
                    self.raw_base["start_hub_raw"] = (value, line_num)
                    # register name immediately for ordering checks
                    name = value.split(maxsplit=1)[0] if value else ""
                    if name:
                        encountered_zones.add(name)
                elif prefix == "end_hub":
                    if end_hubs > 0:
                        raise ValueError(f"Line {line_num}: Multiple end hubs")
                    end_hubs += 1
                    self.raw_base["end_hub_raw"] = (value, line_num)
                    name = value.split(maxsplit=1)[0] if value else ""
                    if name:
                        encountered_zones.add(name)
                elif prefix == "hub":
                    self.raw_base["hubs_raw"].append((value, line_num))
                    name = value.split(maxsplit=1)[0] if value else ""
                    if name:
                        encountered_zones.add(name)
                elif prefix == "connection":
                    # validate connection references appear after zone definitions
                    parts = value.split("-", 1)
                    if len(parts) < 2:
                        raise ValueError(f"Line {line_num}: Malformed connection '{value}'")
                    node_a = parts[0].strip()
                    remaining = parts[1].split(maxsplit=1)
                    node_b = remaining[0].strip()

                    if node_a not in encountered_zones or node_b not in encountered_zones:
                        raise ValueError(
                            f"Line {line_num}: Connection references undefined zone(s): {node_a},{node_b}"
                        )

                    edge_key = tuple(sorted((node_a, node_b)))
                    edge_id = (edge_key[0], edge_key[1])
                    if frozenset(edge_id) in seen_edges:
                        raise ValueError(f"Line {line_num}: Duplicate/bidirectional connection: {node_a}-{node_b}")
                    seen_edges.add(frozenset(edge_id))

                    self.raw_base["connections_raw"].append((value, line_num))
                else:
                    raise ValueError(f"Line {line_num}: Unknown prefix '{prefix}'")

        if not self.raw_base["nb_drones"][0]:
            raise ValueError("Missing nb_drones definition")
        try:
            if int(self.raw_base["nb_drones"][0]) < 1:
                raise ValueError
        except ValueError as exc:
            ln = self.raw_base["nb_drones"][1]
            raise ValueError(f"Line {ln}: nb_drones must be a positive integer") from exc

        if start_hubs == 0:
            raise ValueError("Missing start_hub definition")
        if end_hubs == 0:
            raise ValueError("Missing end_hub definition")

    def parse_phase_two(self) -> None:
        """Stage 2: Split strings into coordinate and name components."""
        self.structured_data = {
            "nb_drones": self.raw_base["nb_drones"][0] if isinstance(self.raw_base["nb_drones"], tuple) else self.raw_base["nb_drones"],
            "zones": {},
            "connections": []
        }

        # Process all hubs (including start/end)
        def _unpack_hub(entry):
            # entry may be (raw_str, line_num) or ("", 0)
            if not entry or entry == ("", 0):
                return ("", "", 0)
            raw_str, ln = entry
            return (raw_str, ln)

        all_hubs = []
        if self.raw_base["start_hub_raw"] and self.raw_base["start_hub_raw"] != ("", 0):
            s_raw, s_ln = _unpack_hub(self.raw_base["start_hub_raw"])
            all_hubs.append(("start", s_raw, s_ln))
        if self.raw_base["end_hub_raw"] and self.raw_base["end_hub_raw"] != ("", 0):
            e_raw, e_ln = _unpack_hub(self.raw_base["end_hub_raw"])
            all_hubs.append(("end", e_raw, e_ln))
        for h_raw, h_ln in self.raw_base["hubs_raw"]:
            all_hubs.append(("normal", h_raw, h_ln))

        for role, raw_str, ln in all_hubs:
            if not raw_str:
                continue
            parts = raw_str.split(maxsplit=3)
            if len(parts) < 3:
                raise ValueError(f"Line {ln}: Malformed hub definition: {raw_str}")

            name = parts[0]
            x = parts[1]
            y = parts[2]
            meta = parts[3] if len(parts) > 3 else ""

            if name in self.structured_data["zones"]:
                raise ValueError(f"Line {ln}: Duplicate zone name: {name}")

            self.structured_data["zones"][name] = {
                "role": role,
                "x": x,
                "y": y,
                "metadata": meta,
                "line": ln
            }

        # Process connections
        for raw_conn, ln in self.raw_base["connections_raw"]:
            parts = raw_conn.split("-", 1)
            if len(parts) < 2:
                raise ValueError(f"Line {ln}: Malformed connection line: {raw_conn}")

            node_a = parts[0].strip()
            remaining = parts[1].split(maxsplit=1)
            node_b = remaining[0].strip()
            meta = remaining[1].strip() if len(remaining) > 1 else ""

            self.structured_data["connections"].append({
                "node_a": node_a,
                "node_b": node_b,
                "metadata": meta,
                "line": ln
            })

    def handle_metadata(self) -> None:
        """Stage 3: Extract bracketed metadata and merge into structured dicts."""
        # Process Zones
        for name in list(self.structured_data["zones"]):
            entry = self.structured_data["zones"][name]
            meta_str = entry.pop("metadata", "").strip()
            ln = entry.get("line", 0)
            if meta_str:
                # allowed keys for zones
                allowed = {"zone", "max_drones", "color"}
                entry.update(self._meta_to_dict(meta_str, allowed, ln))

        # Process Connections
        for entry in self.structured_data["connections"]:
            meta_str = entry.pop("metadata", "").strip()
            ln = entry.get("line", 0)
            if meta_str:
                # allowed keys for connections
                allowed = {"max_link_capacity"}
                entry.update(self._meta_to_dict(meta_str, allowed, ln))

    def _meta_to_dict(self, meta_str: str, allowed_keys: set, line_num: int) -> Dict[str, str]:
        """Helper to transform '[k=v k=v]' string into a dictionary and validate keys.

        Ensures every token inside the brackets matches `key=value` and that keys
        are in `allowed_keys`. Raises ValueError with the original line number on error.
        """
        if not (meta_str.startswith("[") and meta_str.endswith("]")):
            raise ValueError(f"Line {line_num}: Metadata format Error: {meta_str}")

        content = meta_str[1:-1].strip()
        if not content:
            return {}

        tokens = content.split()
        result: Dict[str, str] = {}
        for tok in tokens:
            m = re.fullmatch(r"(\w+)=(\w[\w\d]*)", tok)
            if not m:
                raise ValueError(f"Line {line_num}: Invalid metadata token: '{tok}'")
            k, v = m.group(1), m.group(2)
            if k not in allowed_keys:
                raise ValueError(f"Line {line_num}: Invalid metadata key for context: '{k}'")
            result[k] = v

        return result

