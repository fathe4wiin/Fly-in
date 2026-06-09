*This project has been created as part of the 42 curriculum by `<login>`.*

## Description

Fly-in is a turn-based drone routing simulator for the 42 curriculum. A fleet of drones must travel from a `start_hub` to an `end_hub` through a graph of zones and connections, respecting zone types, capacities, and movement costs while minimizing total simulation turns.

The project includes:

- A strict `.map` file parser with line-numbered error reporting
- An object-oriented domain model (zones, connections, drones, network)
- Space-time A* pathfinding with a reservation table for conflict avoidance
- Turn-by-turn terminal output in the format `D<ID>-<zone>` (or `D<ID>-<connection>` for restricted transit)
- Optional pygame visualization (`--visual`)

## Instructions

### Requirements

- Python 3.10+
- Dependencies in `requirements.txt` (`pydantic`, `pygame` for visualization)

### Install

```bash
make install
```

### Run

```bash
python main.py maps/easy/01_linear_path.txt
# or
make run MAP=maps/medium/01_dead_end_trap.txt
```

With graphical visualization:

```bash
python main.py maps/easy/01_linear_path.txt --visual
```

### Lint

```bash
make lint
```

## Algorithm

Each drone is planned sequentially using **space-time A\***:

1. A backward Dijkstra pass computes a heuristic (minimum turns to goal) per zone, with lower cost for `priority` zones.
2. For each drone, A* searches in `(zone, turn)` space with actions: wait or move to a neighbor.
3. Movement costs follow destination zone type: `normal`/`priority` = 1 turn, `restricted` = 2 turns (`blocked` is skipped).
4. A **reservation table** tracks zone and connection occupancy per turn so later drones avoid conflicts.
5. The simulation prints one line per turn listing all movements that occur that turn.

`start_hub` allows all drones to share turn 0; `end_hub` has unlimited arrival capacity.

## Resources

- [42 subject PDF](en.subject.pdf) — movement rules, parser format, scoring
- [A* pathfinding](https://en.wikipedia.org/wiki/A*_search_algorithm)
- [Multi-agent pathfinding overview](https://en.wikipedia.org/wiki/Multi-agent_pathfinding)

### AI usage

AI assisted with parser hardening (`parsing_changes.md`), space-time pathfinding structure, and pygame font workaround documentation. All code was reviewed and integrated manually; path reservation and simulation output were implemented to match the subject specification.
