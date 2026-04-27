# Project Plan: Fly-in Drone Routing System

## Phase 1: Environment and Standards
- [ ] Initialize Git repository with `.gitignore`.
- [ ] Create `Makefile` containing mandatory rules: `install`, `run`, `debug`, `clean`, `lint`.
- [ ] Configure `flake8` and `mypy` for strict type safety and PEP 8 compliance.

## Phase 2: Core Domain Model (OOP)
- [ ] Define `Zone` class: Handle coordinates, types (Normal, Restricted, etc.), and `max_drones` capacity.
- [ ] Define `Connection` class: Manage bidirectional links and `max_link_capacity`.
- [ ] Define `Drone` class: Track unique ID, current position, and scheduled path.
- [ ] Define `DroneNetwork` class: Store the graph structure without forbidden libraries.

## Phase 3: Input Parser
- [ ] Implement line-by-line parser for `.map` files.
- [ ] Use regex to extract metadata within brackets `[...]`.
- [ ] Implement error handling for:
    - Missing `start_hub` or `end_hub`.
    - Duplicate zone names.
    - Invalid coordinates or zone types.
    - Connection definitions referencing non-existent zones.

## Phase 4: Pathfinding Logic
- [ ] Implement a graph search algorithm (e.g., A* or Dijkstra) adapted for temporal constraints.
- [ ] Incorporate zone movement costs:
    - Normal/Priority: 1 turn.
    - Restricted: 2 turns (occupies connection during transit).
- [ ] Implement conflict resolution to respect `max_drones` and `max_link_capacity` over simulation turns.

## Phase 5: Simulation Engine
- [ ] Create a turn-based execution loop.
- [ ] Logic for drone movement, strategic waiting, and capacity updates.
- [ ] Logic for multi-turn traversal into Restricted zones.
- [ ] Ensure drones are removed from tracking upon reaching the `end_hub`.

## Phase 6: Output and Visualization
- [ ] Generate terminal output in the format: `D<ID>-<target>`.
- [ ] Implement visual feedback (colored terminal output or graphical interface).
- [ ] Track performance metrics (total turns, average turns per drone).

## Phase 7: Documentation
- [ ] Create `README.md` following the curriculum template.
- [ ] Detail algorithm complexity and optimization strategies.
- [ ] Document AI usage as per instructions.