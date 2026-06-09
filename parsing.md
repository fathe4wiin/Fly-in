# Parser Requirements Checklist

## 1. Syntax and Structure
- [x] **Prefix Recognition:** Correctly identifies `nb_drones:`, `start_hub:`, `end_hub:`, `hub:`, and `connection:`.
- [x] **Comments:** Lines starting with `#` are ignored.
- [x] **Empty Lines:** Whitespace-only lines are ignored.
- [x] **Field Separation:** Prefix is separated from data by a colon `:`. Data within hub lines is separated by spaces.
- [x] **Metadata Brackets:** Optional metadata is enclosed in `[...]`.
- [x] **Line Order:** Connections are only processed after the zones they reference have been defined.

## 2. Global Constraints
- [x] **Drone Count:** `nb_drones` is present, a positive integer, and defined only once.
- [x] **Required Hubs:** Exactly one `start_hub` and exactly one `end_hub` are defined.
- [x] **Program Termination:** Any parsing error stops execution immediately with a clear error message including line number.

## 3. Zone Validation
- [x] **Uniqueness:** Every zone name is unique.
- [x] **Naming Rules:** Zone names do not contain dashes `-` or spaces (Pydantic validator).
- [x] **Coordinates:** Coordinates `x` and `y` are valid integers (Pydantic).
- [x] **Coordinate Collision:** No two zones share the same `(x, y)` location.
- [x] **Zone Types:** `zone=<type>` is one of: `normal`, `blocked`, `restricted`, `priority`.
- [x] **Defaulting:** Unspecified zone type defaults to `normal`.
- [x] **Capacity:** `max_drones` is a positive integer. Defaults to `1`.

## 4. Connection Validation
- [x] **Endpoint Existence:** Both zones in a connection string exist in the network.
- [x] **Syntax:** Connection follows the `<name1>-<name2>` format.
- [x] **Self-Loops:** A zone does not connect to itself (Pydantic `NetworkModel`).
- [x] **Duplicate Links:** Bidirectional duplicates (e.g., `A-B` and `B-A`) are rejected.
- [x] **Link Capacity:** `max_link_capacity` is a positive integer. Defaults to `1`.

## 5. Metadata Validation
- [x] **Syntax:** Metadata follows `key=value` format inside brackets.
- [x] **Key Validity:** Rejects invalid keys per context (zone vs connection).
- [x] **Order Independence:** Tags inside brackets can appear in any order.

## 6. Technical Implementation
- [x] **Language:** Written in Python 3.10+.
- [ ] **Typesafety:** Includes type hints and passes `mypy` without errors (verify with `make lint`).
- [ ] **Standard:** Adheres to `flake8` coding standard.
- [x] **OOP:** Implementation is strictly object-oriented.
- [x] **Forbidden Libraries:** No use of `networkx`, `graphlib`, or similar graph logic libraries.
