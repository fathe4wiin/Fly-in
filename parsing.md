# Parser Requirements Checklist

## 1. Syntax and Structure
- [ ] **Prefix Recognition:** Correctly identifies `nb_drones:`, `start_hub:`, `end_hub:`, `hub:`, and `connection:`.
- [ ] **Comments:** Lines starting with `#` are ignored.
- [ ] **Empty Lines:** Whitespace-only lines are ignored.
- [ ] **Field Separation:** Prefix is separated from data by a colon `:`. Data within hub lines is separated by spaces.
- [ ] **Metadata Brackets:** Optional metadata is enclosed in `[...]`.
- [ ] **Line Order:** Connections are only processed after the zones they reference have been defined.

## 2. Global Constraints
- [ ] **Drone Count:** `nb_drones` is present, a positive integer, and defined only once.
- [ ] **Required Hubs:** Exactly one `start_hub` and exactly one `end_hub` are defined.
- [ ] **Program Termination:** Any parsing error stops execution immediately with a clear error message including line number.

## 3. Zone Validation
- [ ] **Uniqueness:** Every zone name is unique.
- [ ] **Naming Rules:** Zone names do not contain dashes `-` or spaces.
- [ ] **Coordinates:** Coordinates `x` and `y` are valid integers.
- [ ] **Coordinate Collision:** No two zones share the same `(x, y)` location.
- [ ] **Zone Types:** `zone=<type>` is one of: `normal`, `blocked`, `restricted`, `priority`.
- [ ] **Defaulting:** Unspecified zone type defaults to `normal`.
- [ ] **Capacity:** `max_drones` is a positive integer. Defaults to `1`.

## 4. Connection Validation
- [ ] **Endpoint Existence:** Both zones in a connection string exist in the network.
- [ ] **Syntax:** Connection follows the `<name1>-<name2>` format.
- [ ] **Self-Loops:** A zone does not connect to itself.
- [ ] **Duplicate Links:** Bidirectional duplicates (e.g., `A-B` and `B-A`) are rejected.
- [ ] **Link Capacity:** `max_link_capacity` is a positive integer. Defaults to `1`.

## 5. Metadata Validation
- [ ] **Syntax:** Metadata follows `key=value` format inside brackets.
- [ ] **Key Validity:** Rejects or correctly handles invalid keys (e.g., `max_drones` on a connection).
- [ ] **Order Independence:** Tags inside brackets can appear in any order.

## 6. Technical Implementation
- [ ] **Language:** Written in Python 3.10+.
- [ ] **Typesafety:** Includes type hints and passes `mypy` without errors.
- [ ] **Standard:** Adheres to `flake8` coding standard.
- [ ] **OOP:** Implementation is strictly object-oriented.
- [ ] **Forbidden Libraries:** No use of `networkx`, `graphlib`, or similar graph logic libraries.