import argparse
import sys

from src.parser.map_parser import MapParser
from src.parser.network_factory import create_network
from src.simulation.engine import SimulationEngine


def main() -> None:
    parser = argparse.ArgumentParser(description="Fly-in drone routing simulation")
    parser.add_argument("map_file", help="Path to a .txt map file")
    args = parser.parse_args()

    try:
        map_parser = MapParser(args.map_file)
        map_parser.run()

        network = create_network(map_parser.structured_data)
        nb_drones = int(map_parser.structured_data.get("nb_drones", 1))

        engine = SimulationEngine(network, nb_drones, visualizer=None)
        engine.run()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
