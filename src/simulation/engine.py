from src.models.network import Network
from src.models.drone import Drone
from src.visuals.visualizer import Visualizer

class SimulationEngine:
    def __init__(self, network: Network, nb_drones: int, visualizer: Visualizer = None) -> None:
        self.network = network
        self.nb_drones = nb_drones
        self.visualizer = visualizer
        self.turn = 0
        self.max_turns = 500

    def run(self) -> None:
        """Executes the simulation turn by turn until all drones reach end_hub."""
        running = True
        
        while running and self.turn < self.max_turns:
            # Update visualization
            if self.visualizer:
                self.visualizer.update({})
            
            # Simulate one turn
            self.turn += 1
