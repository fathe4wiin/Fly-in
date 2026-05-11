import sys
from src.parser.map_parser import MapParser
from src.models.network import NetworkModel
from src.models.network import Network
from src.models.zone import Zone, ZoneType
from src.models.connection import Connection

def main() -> None:
    # 1. Argument Validation
    if len(sys.argv) < 2:
        print("Usage: python main.py <map_file>")
        sys.exit(1)

    map_path = sys.argv[1]

    try:
        # 2. Parsing Stages
        parser = MapParser(map_path)
        parser.parse_phase_one()
        parser.parse_phase_two()
        parser.handle_metadata()

        # 3. Pydantic Validation
        # This converts raw strings to types and enforces constraints
        print(parser.structured_data)
        # NEXT STEP: Initialize Simulation Engine and Algorithm

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()