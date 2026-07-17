# Session changes & subject compliance audit

This documents every change made during this AI-assisted session, plus a
full pass over `en.subject.pdf` to check for anything missed. Everything
below was verified with actual test runs, not just reasoning — see the
"How this was verified" note at the end of each section.

---

## 1. Pathfinding correctness fixes (`src/algorithm/`)

### 1.1 Unfair tie-breaking between equal-cost routes

**Problem:** when two zones were genuinely tied in real cost, the search
fell back to comparing raw zone names alphabetically (via Python's tuple
comparison inside the heap), instead of anything meaningful. This caused
drones to cluster onto whichever hub's name happened to sort first, and — in
one traced case — to detour needlessly through an extra hub when simply
waiting one turn would have reached the same result with less network
footprint.

**Fix:**
- Added `ReservationTable.zone_total_usage` (cumulative per-zone usage
  across all turns, not just one instant) and `_occupancy_bonus()` in
  `pathfinder.py`, applied identically to both "wait" and "move" options,
  so a hub already part of an established route (with room left) is
  preferred over spilling into an untouched one — but only enough to settle
  genuine ties, never to override a real cost difference.
- Added a `move_count` field to the search's sort key so that when two
  paths are *exactly* tied on cost, the one using fewer real hub-to-hub
  transitions wins, instead of falling through to alphabetical order.

**Verified:** hand-traced reservation timelines against `hard/01_maze_nightmare.txt`
turn-by-turn output; confirmed the specific wasteful detour
(`maze_b2 → maze_a2`) stopped recurring; re-ran all 10 provided maps and
confirmed identical or improved turn counts, zero capacity violations.

### 1.2 In-flight state made explicit, not inferred

**Problem:** for a 2-turn restricted-zone move, the drone's internal `path`
list jumped straight from the departure turn to the arrival turn, with no
entry at all for the turn in between. Downstream code (`engine.py`) then had
to *infer* the connection-transit token from that gap. It produced the
correct output, but the state during that turn wasn't a first-class fact
anywhere in the data.

**Fix:** restricted moves now push two explicit path entries — the
`"zoneA-zoneB"` transit label at the middle turn, then the destination zone
at the arrival turn — so every turn has a real, explicit state. Simplified
`ReservationTable.reserve_path`, `SimulationEngine._build_turn_events`, and
`_drone_positions_at_turn` to consume this directly instead of re-deriving
it from turn deltas.

**Verified:** confirmed byte-for-byte identical turn counts across all maps
before/after; printed D1's full path in `challenger/01_the_impossible_dream.txt`
turn-by-turn to confirm every turn (including the in-flight ones) now has an
explicit entry.

### 1.3 Missing capacity check on retried drone start turns

**Problem:** `SimulationEngine._plan_paths` retries a drone at a later
`start_turn` when turn 0 didn't yield a path. That retried starting
placement was pushed onto the search queue without ever checking
`is_zone_available` — every *subsequent* wait/move was checked, but not this
initial one. This let two drones both occupy the `start` hub on the same
turn beyond its capacity, whenever an earlier drone was still legitimately
waiting there.

**Fix:** added the missing `is_zone_available` check before the search
begins in `SpaceTimeAStar.find_path`.

**Verified:** wrote a capacity-violation scanner (zone usage, connection
usage, vs. `max_drones`/`max_link_capacity`, respecting the `start`-at-turn-0
and `end`-always exemptions) and ran it across all 10 maps. Before the fix:
1 violation (`easy/02_simple_fork.txt`, two drones sharing `start` at turn 1
against its default capacity of 1). After: zero violations everywhere.
Turn count for that map correctly increased from 4 to 5 (the 4-turn result
was only reachable by violating capacity).

### 1.4 Overly strict heuristic pruning rule removed

**Problem:** `if v_h > current_h: continue` permanently banned any neighbor
whose *standalone* heuristic looked worse than the current zone's — even
when, once real congestion (a busy gate, a forced wait) was accounted for,
that neighbor turned out to be exactly as good. This isn't how A* is
supposed to work — the algorithm should let the f-score (which already
includes real arrival turn) decide, not a separate static filter. This was
caught via a concrete user-reported example: in `hard/02_capacity_hell.txt`,
`gate1` (heuristic 5.8, worse than `start`'s 5.0) was permanently forbidden,
even though its full route to the goal ties exactly with waiting for
`gate2`/`gate3` to free up.

**Fix:** removed the filter entirely. The existing f-score computation
(`arrival_turn + h + penalties + bonus`) already naturally deprioritizes bad
options (including true dead ends) without permanently forbidding ones that
turn out to be competitive; the existing `visited` set and `max_turn_limit`
already bound the search space.

**Verified:** confirmed `gate1` is now used in parallel with `gate2`/`gate3`
at turn 1 of `capacity_hell` (3 drones move instead of 2). Re-ran all 10
maps: identical turn counts everywhere (this change only *unlocks*
previously-forbidden-but-competitive options — it can't make anything
worse), zero capacity violations, and no measurable performance impact
(~400ms per map, dominated by interpreter startup, not search time).

### 1.5 Why `hard/01_maze_nightmare.txt` still doesn't "split" at its analogous fork — and why that's correct

Removing the pruning rule (1.4) did **not** change `maze_nightmare`'s
behavior at its own parallel-route fork (`maze_a1 → maze_a2` vs.
`maze_a1 → maze_b1`), and that's expected, not a leftover bug:

- `maze_b1`'s heuristic (4.9) was never *worse* than `maze_a1`'s (4.9) — it
  was always an allowed, considered option, both before and after 1.4. The
  pruning rule change literally cannot affect this fork.
- The actual reason `maze_b1` goes unused is the tie-break from 1.1
  (`move_count`), which deliberately prefers "wait, then go direct" over
  "detour through an equal-cost neighbor" — and the two are proven,
  turn-for-turn, exactly tied here.
- Unlike `gate1` in `capacity_hell`, using `maze_b1` wouldn't change the
  map's total makespan at all: every route in this map funnels through the
  single-capacity `maze_c2 → bottleneck` link, which is already at 100%
  utilization with zero idle turns from the earliest possible moment. 13
  turns is a hard floor set by that one link, not by how the maze is
  navigated before it.

Full derivation, including the exact turn-by-turn arithmetic proving the
tie and the bottleneck-saturation argument, is in **`splitting_analysis.md`**
— written specifically so this doesn't get "fixed" into a regression later.

---

## 2. Visualizer fixes & additions (`src/visuals/visualizer.py`)

### 2.1 Large drone clusters rendered off-screen

**Problem:** co-located drones were stacked in a single unbounded vertical
column (22px per drone). With 25 drones sharing `start`/`impossible_goal` in
the challenger map (and 12–15 in `capacity_hell`/`ultimate_challenge`), most
of the stack rendered off the top of the canvas — drones didn't just look
crowded, they were literally invisible.

**Fix:** replaced the single-column stack with a bounded, roughly-square
grid (`_cluster_offsets`) centered on the hub, with a radius that shrinks as
the cluster grows (`_drone_cluster_radius`), so any cluster size stays
visually contained.

**Verified:** computed exact screen coordinates for all 25 drones at
`start` before/after (before: 16 of 25 landed at negative y, i.e.
off-screen; after: all 25 within `[19, 101] × [175, 258]`, fully on-screen).
Rendered actual headless screenshots (SDL dummy driver) at turn 0 and the
final turn confirming all 25 numbered drones visible in both cases.

### 2.2 F cost (heuristic) overlay

Added a toggleable per-zone label showing the precomputed heuristic
(minimum turns to goal), displayed the same way `max N` already is.

- `SHOW_F_COST_ON_START` constant at the top of `visualizer.py` — flip to
  `True`/`False` to control the overlay's state when the window opens
  (requested explicitly, so it's editable without touching runtime code).
- `C` key toggles it live regardless of that default.
- `SimulationEngine.__init__` wires `pathfinder.h_scores` into the
  visualizer automatically — no extra setup needed.

**Verified:** headless-rendered screenshots with the overlay off vs. on;
confirmed displayed values (`goal`=0, `bottleneck`=1.9, `maze_a2`=3.9,
`start`=5.9, etc.) exactly match hand-computed heuristic values used
throughout this session's debugging.

---

## 3. Documentation added

- **`splitting_analysis.md`** — deep-dive on why `maze_nightmare` correctly
  leaves `maze_b1` unused (see 1.5), including the general principle:
  splitting across parallel routes only helps when it relieves an *actual*
  downstream bottleneck; when routes reconverge on the same fixed-capacity
  link, spreading early is cosmetic at best and risks starving
  later-planned drones of resources at worst (planning is sequential, so
  each drone's choice becomes a hard constraint for every drone planned
  after it).
- **`session_changes.md`** (this file).
- **README.md**: added a "Visualization" section (previously missing —
  the subject requires "Documentation of the visual representation
  features and how they enhance the user experience," VIII) describing the
  pygame UI, controls, and the new F-cost overlay; updated the AI usage
  section to describe this session's work.

---

## 4. Lint / type-checking cleanup

Ran a full compliance pass against III.1/III.2 (General Rules, Makefile):

| Check | Before | After |
|---|---|---|
| `flake8 .` | 19 violations (long lines, blank-line issues, missing final newlines) across 5 files | **0 violations** |
| `mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs` | 3 real type errors (`text_render.py` ×2, `visualizer.py` ×1) | **0 errors** |
| `mypy . --strict` (optional) | 2 errors (`network_factory.py`, missing generic type args) | **0 errors** |

Fixes:
- Ran `autopep8 --in-place --aggressive --aggressive --max-line-length=100`
  across `src/` and `main.py`, then manually re-wrapped the handful of long
  lines autopep8 couldn't cleanly reformat (two error-message f-strings in
  `map_parser.py`, four `pygame.draw.polygon` calls in `visualizer.py`).
- **Added `setup.cfg`** with an explicit `[flake8] max-line-length = 100`.
  This matters: before this, `flake8 .` was implicitly using a
  **100-character line length from some ambient, unpinned environment
  setting** (`pycodestyle`'s real default is 79) — meaning `make lint`
  was not reproducible on a different machine (e.g. a peer reviewer's).
  It's now pinned explicitly in the repo.
- Fixed real type errors: `Image.new()` size tuples needed explicit
  `int()` casts (`text_render.py`); a hub's `color` variable needed a
  `Tuple[int,int,int] | pygame.Color` annotation to cover both its default
  value and the `pygame.Color(...)` override (`visualizer.py`);
  `Dict` → `Dict[str, Any]` for `--strict`'s generic-type-args check
  (`network_factory.py`).
- Added the optional `lint-strict` target to the `Makefile` (flake8 +
  `mypy --strict`) since the codebase now passes it cleanly, and fixed
  `.PHONY` to include `run-visual` (it was missing).

**Side note, not a repo fix:** while running `mypy` in this session's
environment (Windows Python reaching the project over a `\\wsl.localhost\...`
network path), it crashed with `sqlite3.OperationalError: database is
locked` — `mypy`'s cache database doesn't like living on a network share.
Worked around with `--cache-dir` pointing at a local temp folder. This is an
artifact of this specific dev environment, not something a native Linux
grading environment would hit, so no repo change was made for it — just
noting it here in case it resurfaces.

---

## 5. Parser error-handling audit (VII.4)

Built a battery of ~20 deliberately-broken map files covering every bullet
in VII.4 and ran them through `MapParser` + `create_network` to check both
"does it correctly reject this" and "does the error include a line number
and clear cause," per: *"Any other parsing error must stop the program and
return a clear error message indicating the line and cause."*

**Confirmed working correctly, with a clear line-numbered message:**

| Case | Result |
|---|---|
| `nb_drones` non-positive | `Line 1: nb_drones must be a positive integer` |
| Duplicate `start_hub` | `Line 3: Multiple start hubs` |
| Duplicate zone name | `Line 4: Duplicate zone name: mid` |
| Connection to undefined zone | `Line 4: Connection references undefined zone(s): ...` |
| Duplicate/reversed connection (`a-b` + `b-a`) | `Line 6: Duplicate/bidirectional connection: ...` |
| Invalid metadata key | `Line 2: Invalid metadata key for context: 'foo'` |
| Malformed metadata brackets | `Line 2: Metadata format Error: ...` |
| Unknown line prefix | `Line 2: Unknown prefix 'foo'` |
| Negative `max_drones` (caught by the `\w+` regex in metadata tokenizing) | `Line 3: Invalid metadata token: 'max_drones=-2'` |

**Gaps found — these do get rejected (the program never crashes or
produces an invalid simulation), but the resulting error message is missing
a line number, or in one case the constraint isn't checked at all:**

| Case | What happens now | Issue |
|---|---|---|
| `nb_drones` line isn't literally the first line of the file | **Silently accepted** — no error at all | VII.4: *"The first line must define the number of drones."* Not enforced; a map with a `hub:` line before `nb_drones:` currently parses fine. |
| Non-integer coordinate (`start_hub: start a b`) | `ValueError: invalid literal for int() with base 10: 'a'` | No line number — this happens later in `network_factory.py`'s `int(zd.get("x"))`, after the line-number context (`zd["line"]`) has been read but not used in the error. |
| Invalid `zone=` type (e.g. `zone=fancy`) | `ValueError: 'fancy' is not a valid ZoneType` | No line number — raised by the `ZoneType(...)` enum constructor in `network_factory.py`. |
| `max_drones=0` / negative via the *value* (not the token regex) | pydantic `ValidationError` (verbose, multi-line) | No line number — raised by `ZoneModel`'s `PositiveInt` field during pydantic validation, several layers away from the parser's line-tracking. |
| `max_link_capacity=0` | Same pydantic `ValidationError` pattern | Same issue. |
| Zone name containing a dash or space | Confusing knock-on error from connection parsing (splits on `-`, so a dashed zone name breaks *connection* parsing before name validation ever runs), or a line-number-less pydantic error if never referenced by a connection | The dash/space check exists (`ZoneModel.validate_name`) but runs too late — after connections have already tried (and failed) to parse using dash-delimited splitting. |
| Self-connection (`a-a`), duplicate coordinates | Line-number-less pydantic `ValidationError` | These aren't explicitly required by VII.4, but the codebase already added them as extra validation — just without a line number, same as the others above. |
| Missing `nb_drones` / missing `start_hub` / missing `end_hub` entirely | `Missing nb_drones definition` / `Missing start_hub definition` / `Missing end_hub definition` | No line number, but arguably reasonable since there's no single offending line for an *absence* — flagging for awareness, not necessarily a defect. |

**Root cause, in one sentence:** `map_parser.py` tracks a line number for
every zone/connection it reads, but that line number gets dropped the
moment validation crosses into `network_factory.py` / pydantic (`int()`
conversions, `ZoneType(...)`, and all `ZoneModel`/`ConnectionModel`/`NetworkModel`
field/model validators) — none of those exceptions currently get caught and
re-raised with the original line attached.

**Not fixed in this pass.** These are real gaps worth closing, but doing so
properly means either (a) validating types/ranges/names directly in
`map_parser.py` before line numbers are discarded, or (b) wrapping the
`network_factory`/pydantic calls to catch validation errors and re-attach
the stored `line` field — a real design decision, not a one-line patch, so
it wasn't made without checking first. Happy to implement either approach
if wanted.

**Confirmed NOT a parser gap (works correctly, tested for completeness):**
`blocked` zones parse fine as regular zones (only rejected as a *path*
choice by the pathfinder, per VII.3 — correct, since the subject only says
drones can't traverse them, not that they can't exist in the file).

---

## 6. Other subject requirements checked and confirmed passing

- **V. Constraints**: no `networkx`/`graphlib` (or any graph library)
  anywhere in the codebase; fully object-oriented (`Zone`, `Connection`,
  `Drone`, `Network`, `SpaceTimeAStar`, `ReservationTable`,
  `SimulationEngine`, `Visualizer` classes); typesafe per `mypy --strict`
  (see §4).
- **III.1 General Rules**: Python 3.13 in use (≥3.10 required); `main.py`
  wraps the whole run in `try/except Exception`, printing `Error: ...` and
  exiting 1 — verified gracefully handles both a missing map file and a
  missing CLI argument without a raw traceback; file I/O uses `with open(...)`
  context managers; full type hints throughout, `mypy --strict` clean;
  docstrings present on parser/engine/pathfinder classes and methods.
- **VII.2 Zone Occupancy Rules** / **VII.3 Movement and Turn Mechanics**:
  re-verified this session (see §1.3's capacity scanner) — zero violations
  across all 10 provided maps, including the `start`-at-turn-0 and
  `end`-always exemptions.
- **VII.5 Output format**: `D<ID>-<zone>` / `D<ID>-<connection>` tokens,
  omitted-when-not-moving, delivered-drones-untracked — all confirmed via
  direct trace inspection earlier this session (see §1.2).
- **VII.7 Performance benchmarks**: all maps beat their targets after this
  session's fixes:

  | Map | Target | Actual |
  |---|---|---|
  | `easy/01_linear_path` | ≤ 6 | 4 |
  | `easy/02_simple_fork` | ≤ 8 | 5 |
  | `easy/03_basic_capacity` | ≤ 6 | 4 |
  | `medium/01_dead_end_trap` | ≤ 12 | 8 |
  | `medium/02_circular_loop` | ≤ 15 | 10 |
  | `medium/03_priority_puzzle` | ≤ 12 | 6 |
  | `hard/01_maze_nightmare` | ≤ 30 | 13 (proven optimal, §1.5) |
  | `hard/02_capacity_hell` | ≤ 35 | 16 |
  | `hard/03_ultimate_challenge` | ≤ 45 | 26 |
  | `challenger` (optional) | beat 45 | 43 |

- **VIII Readme Requirements**: Description/Instructions/Resources sections
  present; AI usage described; algorithm strategy documented; visual
  representation documentation was **missing and has been added** this
  session (see §3). One action item remains: the first line's `` `<login>` ``
  placeholder needs the actual 42 login(s) filled in before submission —
  can't be done on your behalf since I don't know it.

---

## Summary of open items (not auto-fixed, flagged for your decision)

1. Parser errors that lose their line number once validation crosses into
   `network_factory.py`/pydantic (§5) — real gap, fixable, needs a design
   choice on where the fix belongs.
2. `nb_drones` "must be the first line" isn't enforced at all (§5).
3. README's first line still has the `<login>` placeholder — needs your
   actual 42 login before submission.

Everything else audited in this pass is confirmed compliant and verified
with concrete test runs, not just code reading.
