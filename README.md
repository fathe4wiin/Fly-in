*This project has been created as part of the 42 curriculum by bfathi.*

## Description

**Fly-in** is a multi-agent turn-based drone routing simulator. A fleet of drones must navigate from a `start_hub` to an `end_hub` through a graph of zones and connections while respecting capacity constraints, zone types, and movement costs, with the goal of minimizing total simulation turns.

### Key Features

- **Strict map parser** with comprehensive line-numbered error reporting for syntax and constraint violations
- **Object-oriented domain model** using Pydantic validation (zones, connections, drones, network)
- **Space-time A* pathfinding** with conflict-aware reservation table for multi-agent coordination
- **Turn-by-turn simulation output** in subject format: `D<ID>-<zone>` (or `D<ID>-<connection>` for restricted transit)
- **Turn-by-turn terminal output** with drone movement tracking and simulation statistics

### Problem Domain

Drones start at a single origin and must reach a single destination within a network where:
- **Zone types** determine movement cost and accessibility: `normal` (1-turn, 1 capacity default), `priority` (1-turn preferred), `restricted` (2-turn slower), `blocked` (impassable)
- **Capacity limits** on zones (`max_drones`) and connections (`max_link_capacity`) create bottlenecks
- **Simultaneous multi-agent planning** requires conflict resolution to avoid collisions in space-time

Success is measured by minimizing the total simulation turns to get all drones through.

---

## Instructions

### Requirements

- **Python 3.10+**
- Dependencies listed in `requirements.txt`:
  - `pydantic>=2.0` — type validation and parsing
  - `pygame>=2.0` — optional visualization
  - `Pillow>=10.0` — image support for visualization
  - `flake8>=7.0`, `mypy>=1.0` — code quality checks

### Installation

```bash
make install
```

This installs all dependencies into your Python environment using `pip`.

### Running the Simulator

**Basic usage** (terminal-only output):

```bash
python main.py maps/easy/01_linear_path.txt
```

**With map parameter** (via Makefile):

```bash
make run                                    # Runs default easy map
make run MAP=maps/medium/01_dead_end_trap.txt
make run-visual                             # Interactive visualization
```



### Debug Mode

```bash
make debug
```

Runs the default map under Python's built-in debugger (`pdb`).

### Cleaning Build Artifacts

```bash
make clean
```

Removes `__pycache__`, `.mypy_cache`, `*.pyc`, and `.pytest_cache` directories.

### Code Quality

```bash
make lint              # Runs flake8 and mypy with required flags
make lint-strict       # Runs mypy with --strict mode for enhanced checking
```

---

## Algorithm & Implementation Strategy

### High-Level Pipeline

1. **Parse map file** → `MapParser` reads zones, connections, drone count, and metadata with strict error reporting (line numbers for all failures)
2. **Build network graph** → `create_network()` converts structured data into validated Pydantic models, then OOP runtime objects (`Network`, `Zone`, `Drone`, `Connection`)
3. **Plan drone paths** → `SimulationEngine._plan_paths()` uses **space-time A*** to compute conflict-free routes sequentially
4. **Execute simulation** → `SimulationEngine.run()` outputs movements turn-by-turn per subject specification
5. **Visualize (optional)** → `Visualizer` replays the planned paths frame-by-frame with user controls

### Pathfinding: Space-Time A\*

Each drone is planned **sequentially** (D1, then D2, etc.) to maximize reuse of the search-space and simplify conflict detection.

**Algorithm steps:**

1. **Heuristic computation** (once per map):
   - Backward Dijkstra from `end_hub` computes per-zone minimum turns-to-goal (`h` value)
   - Zone type reduces cost: `priority` zones cost 0.9 turns per step, others cost 1
   - This heuristic is consistent and admissible, powering A* optimality

2. **Forward A\* search per drone**:
   - State: `(zone, turn)` pair
   - Start: `(start_hub, max(0, start_turn))`
   - Goal: `(end_hub, any_turn)`
   - Actions: **wait** (remain at zone, turn+1) or **move** (to neighbor, turn+1 or turn+2 for restricted)
   - F-score: `f(s) = g(s) + h(neighbor) + penalties + bonus`
     - `g(s)`: actual turns elapsed
     - `h(neighbor)`: precomputed heuristic
     - penalties: occupancy costs prevent clustering
     - bonus: occupancy history ties (preferring established routes)

3. **Conflict avoidance**:
   - **Reservation table** tracks zone occupancy and connection usage per turn
   - A* search checks `is_zone_available()` and `is_connection_available()` before expanding a node
   - Upon success, `res_table.reserve_path()` locks the path for later drones

4. **Retry logic**:
   - If no path exists at `start_turn`, increment and retry (up to 200 retries)
   - This lets later drones naturally "wait" if the start hub is congested

### Movement Rules

| Action | Cost | Output Format | Conditions |
|--------|------|---------------|-----------|
| Move to normal/priority zone | 1 turn | `D<ID>-<zone>` on arrival | Zone must be available |
| Move to restricted zone | 2 turns (split) | `D<ID>-<connection>` at turn 1, then `D<ID>-<zone>` at turn 2 | Connection must allow transit |
| Wait at zone | 1 turn | (no output, implicit) | Zone capacity not exceeded |
| Move to blocked zone | N/A | (forbidden) | Zone type blocks all access |

**Start hub exceptions:**
- All drones may occupy `start_hub` at turn 0 regardless of `max_drones` (subject requirement)
- Retried drones at later turns respect normal capacity

**End hub exceptions:**
- `end_hub` accepts unlimited drones simultaneously (no capacity limit)

### Key Algorithmic Decisions

1. **Sequential drone planning** (not parallel):
   - Simplifies correctness (each drone sees all predecessors' paths)
   - Allows single reservation table without backtracking
   - Trade-off: Not optimal across all drones, but sufficient for subject maps

2. **Consistent heuristic**:
   - Ensures A\* finds shortest paths without re-expansion
   - Heuristic never overestimates (h ≤ actual cost) due to priority-zone bonus

3. **Tie-breaking in A\***:
   - Equal f-scores prefer zones with lower cumulative usage (occupancy bonus)
   - Then prefer paths with fewer hub-to-hub transitions (move_count)
   - Then prefer the path that spent more of its moves in `priority` zones
     (a running per-path count of non-priority moves, compared low-to-high),
     so "priority zones should be preferred" (subject VII.1/VII.3) holds even
     when two branches are otherwise perfectly tied on cost
   - Averts wasteful detours, clustering, and arbitrary alphabetical bias

4. **No external graph libraries**:
   - Graph stored as hand-rolled `List[Zone]` and `Dict[str, Connection]`
   - Avoids hidden assumptions and maximizes code clarity

---

## Visual Representation

Fly-in provides an optional graphical replay of the simulation, built with `pygame` (`src/visuals/visualizer.py`). It's enabled with the `--visual` flag:

```bash
python main.py maps/easy/01_linear_path.txt --visual
# or
make run-visual
```

### What it shows

- **Zone graph layout** — every zone is drawn at its map `(x, y)` coordinate, connected by lines representing each `connection`.
- **Zone colors** — the `color=` metadata from the map file is rendered directly on each zone (including an animated `color=rainbow` option), so the visual state matches what the map author intended.
- **Zone-type rings** — `restricted` zones get a red ring, `priority` zones a green ring, making the zones that drive movement-cost and routing decisions visually distinct at a glance, without needing to re-read the map file.
- **Capacity labels** — zones with `max_drones > 1` are labeled `max N`, and connections with `max_link_capacity > 1` are labeled `C:N`, so bottlenecks and high-capacity shortcuts are immediately obvious.
- **Drone positions and clustering** — drones are drawn at their current zone (or at the midpoint of a connection while in 2-turn restricted transit) and automatically arranged in a compact grid when many drones share one location, so even a 25-drone fleet sharing the start/end hub stays legible.
- **H-cost overlay** (toggle with `C`) — displays each zone's precomputed heuristic (turns-to-goal), which is useful for understanding *why* the pathfinder chose the routes it did.
- **Turn-by-turn playback controls** — a control bar with first/prev/next/last buttons (or arrow keys / Home / End / Space), a progress bar, and a live readout of the current turn's movement tokens, letting a reviewer step through the exact same output that's printed to the terminal at their own pace.

### Why it helps

Because the simulation itself is a purely turn-by-turn algorithm producing a static list of moves, the biggest risk for a human reviewer is *not seeing* congestion, capacity limits, or zone-type effects while reading a wall of `D<ID>-<zone>` text. The visualizer turns that same output into a spatial, replayable scene: capacity bottlenecks are visibly labeled, restricted/priority zones are visually flagged, and drone clustering makes it obvious when many drones share a hub versus when they're spread across parallel routes — all without re-deriving any of it from the map file by hand.

For a terminal-only run (no `--visual`), the same information is available as plain per-turn text (see below); the graphical mode is the enhanced option described by the subject ("colored terminal output and/or a graphical interface").

---

## Output Format

### Terminal Simulation Output

The simulation runs entirely in the terminal without a graphical interface. Output is simple and efficient:

**Format:**
- **One line per turn** listing all drone movements that occur during that turn
- **Movement tokens** show drone ID and destination:
  - `D<ID>-<zone>` — drone moves to/arrives at a zone
  - `D<ID>-<zoneA-zoneB>` — drone in transit through a restricted connection (2-turn movement)

### Example Input and Output

Given `maps/easy/02_simple_fork.txt`:

```
nb_drones: 4

start_hub: start 0 0 [color=green]
hub: junction 1 0 [color=yellow max_drones=2]
hub: path_a 2 1 [color=blue]
hub: path_b 2 -1 [color=blue]
end_hub: goal 3 0 [color=red]

connection: start-junction [max_link_capacity=2]
connection: junction-path_a
connection: junction-path_b
connection: path_a-goal
connection: path_b-goal
```

Running `python main.py maps/easy/02_simple_fork.txt` produces:

```
D1-junction D2-junction
D1-path_a D2-path_b D3-junction
D1-goal D2-goal D3-path_a D4-junction
D3-goal D4-path_a
D4-goal
# Simulation complete in 5 turns
# Drones: 4, avg turns/drone: 1.25
```

The `junction` zone has `max_drones=2`, so only D1 and D2 can occupy it on turn 1; D3 and D4 wait at `start` (and are omitted from that line) until capacity frees up. D1/D2 then fork onto `path_a`/`path_b` in parallel, and every drone is delivered to `goal` by turn 5.

**Summary:**
- Total simulation turns to complete all movements
- Average turns per drone

---

## File Structure

```
.
├── main.py                          # Application entry point
├── Makefile                         # Build and development tasks
├── requirements.txt                 # Python dependencies
├── README.md                        # This file
├── how_it_works.md                  # Detailed architecture walkthrough
├── parsing.md                       # Parser requirements checklist
├── parsing_changes.md               # Parser implementation notes
├── splitting_analysis.md            # Multi-route decision analysis
├── session_changes.md               # AI-assisted changes and verification
│
├── src/
│   ├── __init__.py
│   ├── algorithm/
│   │   ├── pathfinder.py            # Space-time A* implementation
│   │   └── reservation_table.py     # Conflict tracking
│   ├── models/
│   │   ├── network.py               # Graph structure
│   │   ├── zone.py                  # Zone (hub) definition
│   │   ├── connection.py            # Edge between zones
│   │   └── drone.py                 # Drone agent
│   ├── parser/
│   │   ├── map_parser.py            # `.txt` → structured data
│   │   └── network_factory.py       # Structured data → OOP objects
│   └── simulation/
│       └── engine.py                # Turn-by-turn execution
│
└── maps/
    ├── README.md                    # Challenge map descriptions
    ├── easy/
    │   ├── 01_linear_path.txt
    │   ├── 02_simple_fork.txt
    │   └── 03_basic_capacity.txt
    ├── medium/
    │   ├── 01_dead_end_trap.txt
    │   ├── 02_circular_loop.txt
    │   └── 03_priority_puzzle.txt
    ├── hard/
    │   ├── 01_maze_nightmare.txt
    │   ├── 02_capacity_hell.txt
    │   └── 03_ultimate_challenge.txt
    └── challenger/
        └── 01_the_impossible_dream.txt
```

---

## Resources

### Classic References

- **[A\* Search Algorithm](https://en.wikipedia.org/wiki/A*_search_algorithm)** — foundational heuristic search technique
- **[Multi-Agent Pathfinding Overview](https://en.wikipedia.org/wiki/Multi-agent_pathfinding)** — survey of cooperative and conflict-avoidant planning
- **[Conflict-Based Search](https://en.wikipedia.org/wiki/Conflict-based_search)** — hierarchical multi-agent framework (CBS)
- **Pydantic documentation** — [Pydantic v2](https://docs.pydantic.dev/latest/) for validation and serialization
- **Pygame documentation** — [Pygame Docs](https://www.pygame.org/docs/) for visualization

### Project Documentation

- `how_it_works.md` — Detailed walkthrough of the architecture and data flow
- `parsing.md` — Map parser requirements and validation rules
- `parsing_changes.md` — Enhancements made to the parser
- `splitting_analysis.md` — Analysis of multi-route behavior (why certain parallel paths are not used)
- `maps/README.md` — Challenge map descriptions and difficulty rankings
- `en.subject.pdf` — Official 42 project specification (movement rules, scoring, constraints)

### AI Usage

**Tasks assisted by AI:**

1. **Parser hardening** (`parsing_changes.md`)
   - Structured multi-phase parsing with line-number error reporting
   - Metadata validation with regex and context-specific key whitelisting

2. **Space-time A* structure and correctness fixes**:
   - Initial pathfinding framework for `(zone, turn)` state space
   - **Unfair tie-breaking fix**: Added occupancy bonus to prevent alphabet-based clustering of equal-cost routes
   - **In-flight state fix**: Made restricted-zone 2-turn transits explicit with intermediate `zoneA-zoneB` labels
   - **Capacity check fix**: Added missing `is_zone_available` check on retried drone starts to prevent capacity violations
   - **Heuristic pruning fix**: Removed overly strict filter that permanently banned otherwise-competitive routes from being explored

3. **Visualizer correctness and scalability**:
   - Fixed off-screen rendering of large drone fleets via compact grid layout
   - Added optional H-cost heuristic overlay for algorithm transparency

4. **Full compliance pass**:
   - Verified parser error coverage against subject requirements
   - Code cleanup: flake8 and mypy compliance, including `--strict` mode
   - Makefile targets and build automation

**Verification method:**

All AI-suggested changes were verified against the official subject text and cross-checked with concrete test runs:
- **Capacity scans** across all 10 provided maps (easy, medium, hard, challenger)
- **Turn-by-turn traces** of drone movements to ensure correctness
- **Byte-for-byte output comparison** before/after each fix to isolate behavioral changes
- **Performance benchmarks** to confirm no regressions

See `session_changes.md` for a complete change log with verification details.
