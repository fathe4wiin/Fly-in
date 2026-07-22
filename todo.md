# Project Plan: Fly-in Drone Routing System

## Phase 1: Environment and Standards
- [x] Initialize Git repository with `.gitignore`.
- [x] Create `Makefile` containing mandatory rules: `install`, `run`, `debug`, `clean`, `lint`.
- [ ] Configure `flake8` and `mypy` for strict type safety and PEP 8 compliance (run `make lint` locally).

## Phase 2: Core Domain Model (OOP)
- [x] Define `Zone` class: Handle coordinates, types (Normal, Restricted, etc.), and `max_drones` capacity.
- [x] Define `Connection` class: Manage bidirectional links and `max_link_capacity`.
- [x] Define `Drone` class: Track unique ID, current position, and scheduled path.
- [x] Define `DroneNetwork` class: Store the graph structure without forbidden libraries.

## Phase 3: Input Parser
- [x] Implement line-by-line parser for `.map` files.
- [x] Use regex to extract metadata within brackets `[...]`.
- [x] Implement error handling for:
    - Missing `start_hub` or `end_hub`.
    - Duplicate zone names.
    - Invalid coordinates or zone types (via Pydantic `NetworkModel`).
    - Connection definitions referencing non-existent zones.

## Phase 4: Pathfinding Logic
- [x] Implement a graph search algorithm (Space-time A* with backward Dijkstra heuristic).
- [x] Incorporate zone movement costs:
    - Normal/Priority: 1 turn.
    - Restricted: 2 turns (occupies connection during transit).
- [x] Implement conflict resolution to respect `max_drones` and `max_link_capacity` over simulation turns.

## Phase 5: Simulation Engine
- [x] Create a turn-based execution loop.
- [x] Logic for drone movement, strategic waiting, and capacity updates.
- [x] Logic for multi-turn traversal into Restricted zones.
- [x] Ensure drones are removed from tracking upon reaching the `end_hub`.

## Phase 6: Output and Visualization
- [x] Generate terminal output in the format: `D<ID>-<target>`.
- [x] Implement visual feedback (pygame with `--visual` flag).
- [x] Track performance metrics (total turns, average turns per drone).

## Phase 7: Documentation
- [x] Create `README.md` following the curriculum template.
- [x] Detail algorithm complexity and optimization strategies.
- [x] Document AI usage as per instructions.



<!-- todo.md -->
## parsing handing: 
- [x] multiple colors in metadata (multi data)
- [x] comnts inline #
- color value error
- color rainbow
- color default shouldbe transparent
- implemet the `--benchmark` flag to see the benchmark of the network