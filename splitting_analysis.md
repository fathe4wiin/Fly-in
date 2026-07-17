# Why `maze_b1` sits unused in `hard/01_maze_nightmare.txt`

This documents a specific, deliberate behavior: at the `maze_a1` fork, the
planner routes every drone through `maze_a2` (queuing/waiting for it when
busy) and never uses the parallel `maze_b1` branch, even though `maze_b1` is
a perfectly legal, always-available alternative. This is not a bug — using
it would not reduce the total simulation time, and preferring it over
waiting would reintroduce a different, previously-fixed problem. This note
records the reasoning so it isn't re-litigated (or "fixed" into a regression)
later.

## The fork

From `maze_a1`, a drone can either:

- Move to `maze_a2` (continue toward `maze_c2`), or
- Move to `maze_b1` (a parallel route that reaches `maze_c2` via `maze_b2`
  instead), or
- Wait one turn at `maze_a1`.

Heuristic distance-to-goal (`h`, precomputed via backward Dijkstra from the
goal):

| Zone | h (turns to goal) |
|---|---|
| `maze_a1` | 4.9 |
| `maze_a2` | 3.9 (strictly closer) |
| `maze_b1` | 4.9 (exactly tied with *not moving at all*) |

`maze_a2` is the closest option, so it's always preferred when available.
`maze_b1` isn't "the second-best option" the way `gate1` was in
`hard/02_capacity_hell.txt` — it's exactly as good as standing still. That
distinction matters a lot for what follows.

## The real-cost tie

When `maze_a2` is momentarily busy (its single-capacity inbound link is
already used by the drone ahead), a drone at `maze_a1` has two ways to make
progress:

```
Wait one turn, then take maze_a2 directly:
  maze_a1 --(wait)--> maze_a1 --(move)--> maze_a2 --(move)--> maze_c2
  = 1 wait + 2 moves = 3 turns to reach maze_c2

Detour immediately through maze_b1:
  maze_a1 --(move)--> maze_b1 --(move)--> maze_b2 --(move)--> maze_c2
  = 3 moves = 3 turns to reach maze_c2
```

Both options take **exactly 3 turns** to reach `maze_c2`. From there on, the
rest of the route (`maze_c2 → bottleneck → final_stretch → goal`) is
identical either way. So for the drone making this specific choice, the two
options are not "slightly worse vs. better" — they are mathematically tied,
turn for turn, all the way to the goal.

## Why "wait" wins the tie (on purpose)

Since real cost is tied, some tie-break has to pick one. The planner biases
ties toward *fewer real hub-to-hub moves* (a `move_count` field in the
search's sort key — see `src/algorithm/pathfinder.py`), so "wait, then go
direct" beats "detour through an extra hub" when they cost the same.

This isn't an arbitrary preference — it's there specifically because the
opposite default caused a real, previously-observed problem: a drone would
reach a strictly better zone (lower `h`), find the very next link
momentarily busy, and then *backtrack* through an equal-cost detour instead
of just waiting one turn — burning an extra hub's and an extra link's
capacity for zero benefit, capacity that a later-queued drone might have
actually needed. Flipping the tie-break to prefer detours again would bring
that exact pattern back.

## Why splitting into `maze_b1` doesn't help *this* map

In `hard/02_capacity_hell.txt`, unlocking `gate1` genuinely mattered: `gate1`
sits behind its **own**, previously-unused `start → gate1` link, and using
it lets a 3rd drone leave `start` on the same turn as two others — real,
additional, uncontended parallel capacity.

`maze_nightmare` doesn't have that kind of slack anywhere downstream. The
entire map — both the `maze_a2` route and the `maze_b1` detour — eventually
funnels through one single-capacity link: `maze_c2 → bottleneck`
(`max_link_capacity` defaults to `1`, unset in the map file). That link can
carry at most 1 drone per turn, no matter how many parallel routes feed into
`maze_c2` from upstream. With 8 drones:

- Earliest any drone can reach `maze_c2` is turn 3 (`start → maze_a1 →
  maze_a2 → maze_c2`), so the bottleneck link can't start being used before
  turn 4.
- It can carry 1 drone/turn, so draining all 8 needs turns 4 through 11 —
  8 consecutive turns, zero gaps.
- The last drone then needs 2 more moves (`bottleneck → final_stretch →
  goal`), landing at turn 13.

The current plan hits turns 4–11 on that link back-to-back with **no idle
turns** — that's already the maximum possible throughput starting at the
earliest possible moment. Splitting drones across `maze_a1`'s two exits
would only change how fast they *arrive* at `maze_c2`, not how fast
`maze_c2 → bottleneck` can drain them, since that link's capacity is fixed
at 1/turn regardless of arrival pattern. Speeding up the upstream fork just
means drones queue at `maze_c2` instead of at `maze_a1` — the total time for
the last drone to reach the goal is unchanged. 13 turns is a hard floor set
by that single link, not by how the maze is navigated before it.

## The risk of "splitting/using more zones" as a general instinct

The broader lesson, generalized beyond this one map:

- **Splitting across parallel routes only helps when it relieves an actual
  bottleneck.** If two routes reconverge on the same fixed-capacity link or
  zone before reaching the goal, spreading drones across the routes earlier
  doesn't increase total throughput — it just moves the queue from one place
  to another.
- **Splitting has a real cost when it doesn't help.** Every extra hub and
  link a detour uses is capacity that isn't free — it's capacity some other,
  later-queued drone might have needed. Preferring a "slightly more
  expensive but parallel" option indiscriminately, even when it's genuinely
  tied in cost, can inflate resource usage elsewhere and cause knock-on
  congestion for drones planned afterward (planning is sequential: each
  drone's choice becomes a hard constraint for every drone planned after it).
- **The two are only reliably distinguishable by checking for a shared
  downstream constraint.** `gate1` was worth unlocking because it used
  capacity nothing else was touching. `maze_b1` is not, because it
  reconverges on the same capacity-1 link everything else already funnels
  through. A general "always split when tied" rule would have been right
  for one map and wrong for the other — which is exactly why this is a
  case-by-case judgment call rather than a rule worth hard-coding.

## Bottom line

`maze_nightmare` already runs in 13 turns, which is the proven optimum given
the `maze_c2 → bottleneck` link's capacity. Making `maze_b1` get used
wouldn't lower that number — it would only make the trace look "more
explored" while adding risk of reintroducing the wasteful-detour bug this
tie-break was built to prevent. Left as-is on purpose.
