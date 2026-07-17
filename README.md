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

## Visualization

`--visual` opens a pygame window rendering the network and playing back the
planned drone movements turn by turn.

- **Hubs**: drawn as circles at their map coordinates, colored per the
  zone's `color` metadata (default blue). A red ring marks `restricted`
  zones, a green ring marks `priority` zones. `max N` is shown above any
  hub with capacity greater than 1.
- **Connections**: drawn as lines between hubs; a `C:N` label appears on
  any connection whose `max_link_capacity` is greater than 1.
- **Drones**: gold circles labeled with their numeric ID, drawn at their
  hub — or, while in flight toward a restricted zone, at the midpoint of
  the connection they're transiting (matching the `D<ID>-<connection>`
  output token). When several drones share a hub or connection, they're
  arranged in a compact, bounded grid (shrinking as the count grows)
  instead of stacking in a single column, so large maps (e.g. the
  25-drone challenger map) never push drones off-screen.
- **F cost overlay**: press **`C`** to toggle a per-zone label showing the
  precomputed heuristic (minimum turns to goal) next to each hub — useful
  for understanding *why* the planner picked one route over another. Its
  starting state is controlled by `SHOW_F_COST_ON_START` at the top of
  `src/visuals/visualizer.py`.
- **Controls**: `←`/`→` or the on-screen buttons step one turn at a time,
  `Home`/`End` jump to the first/last turn, `Space` also steps forward.
  The bottom bar shows the current turn, the movement tokens for that
  turn, and a progress bar.

This turns the terminal's flat `D<ID>-<zone>` log into a spatial, replayable
view of the whole fleet — useful for spotting congestion, verifying
capacity limits are respected, and (with the F cost overlay) understanding
the pathfinder's decisions directly on the graph.

## Resources

- [42 subject PDF](en.subject.pdf) — movement rules, parser format, scoring
- [A* pathfinding](https://en.wikipedia.org/wiki/A*_search_algorithm)
- [Multi-agent pathfinding overview](https://en.wikipedia.org/wiki/Multi-agent_pathfinding)

### AI usage

AI assisted with parser hardening (`parsing_changes.md`), space-time pathfinding structure, and pygame font workaround documentation. It was also used to diagnose and fix several pathfinding correctness bugs (unfair tie-breaking between equal-cost routes, a capacity check missing on retried drone start turns, an overly strict heuristic-based pruning rule that blocked competitive moves — see `splitting_analysis.md` for when splitting across parallel routes does and doesn't help), to fix a visualizer bug where large drone clusters rendered off-screen, to add the optional F-cost overlay, and to run a full compliance pass against `en.subject.pdf` (parser error coverage, flake8/mypy/`--strict` cleanliness via `autopep8`, Makefile targets). See `session_changes.md` for the full list. All AI-suggested changes were verified against the subject text and cross-checked with concrete test runs (turn-by-turn traces, capacity-violation scans across every provided map) before being accepted.
