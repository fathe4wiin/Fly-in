import sys
from src.parser.map_parser import MapParser
from src.parser.network_factory import create_network

def main() -> None:
    # 1. Argument Validation
    if len(sys.argv) < 2:
        print("Usage: python main.py <map_file>")
        sys.exit(1)

    map_path = sys.argv[1]

    try:
        parser = MapParser(map_path)
        parser.run()

        sd = parser.structured_data
        network = create_network(sd)
        print(f"Built network with {len(network.zones)} zones and {len(network.connections)} connections")
        for zone in network.zones.values():
            print(network.get_neighbors(zone))

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()