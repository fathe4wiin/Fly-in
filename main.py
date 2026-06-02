import sys
from src.parser.map_parser import MapParser
from src.parser.network_factory import create_network
from src.simulation.engine import SimulationEngine
from src.visuals.visualizer import Visualizer

def main() -> None:
    # 1. Argument Validation
    if len(sys.argv) < 2:
        print("Usage: python main.py <map_file>")
        sys.exit(1)

    map_path = sys.argv[1]

    try:
        # Parse the map file
        parser = MapParser(map_path)
        parser.run()

        # Build the network
        sd = parser.structured_data
        network = create_network(sd)
        
        # Extract number of drones from structured data
        nb_drones = int(sd.get("nb_drones", 1))
        
        # Initialize the visualizer
        visualizer = Visualizer(network)
        
        # Initialize the simulation engine
        engine = SimulationEngine(network, nb_drones, visualizer)
        
        # Run the simulation
        engine.run()

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()