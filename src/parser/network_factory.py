from typing import Dict, List, Union

from src.models.network import Network, NetworkModel
from src.models.zone import Zone, ZoneModel, ZoneRole, ZoneType
from src.models.connection import Connection, ConnectionModel
from src.models.drone import Drone


def create_network(model_or_structured: Union[NetworkModel, Dict]) -> Network:
    """Create a runtime `Network` from either a `NetworkModel` or the
    parser's structured dictionary.

    If a dict is provided, this function will construct the required
    `ZoneModel` and `ConnectionModel` instances and then create a
    `NetworkModel` which performs pydantic validation.
    """
    # If caller passed a raw structured dict (parser output), convert it
    if not isinstance(model_or_structured, NetworkModel):
        sd: Dict = model_or_structured

        # build pydantic zone models
        zones: Dict[str, ZoneModel] = {}
        for name, zd in sd.get("zones", {}).items():
            role = zd.get("role", "normal")
            zone_type = zd.get("zone", ZoneType.NORMAL)
            if isinstance(zone_type, str):
                zone_type = ZoneType(zone_type)

            zones[name] = ZoneModel(
                name=zd.get("name", name),
                role=ZoneRole(role),
                x=int(zd.get("x")),
                y=int(zd.get("y")),
                zone=zone_type,
                max_drones=int(zd.get("max_drones", 1)),
                color=zd.get("color", None),
            )

        # build pydantic connection models
        connections: List[ConnectionModel] = []
        for cd in sd.get("connections", []):
            connections.append(
                ConnectionModel(
                    node_a=cd["node_a"],
                    node_b=cd["node_b"],
                    max_link_capacity=int(cd.get("max_link_capacity", 1)),
                )
            )

        nb = int(sd.get("nb_drones", 1)) if sd.get("nb_drones") else 1
        model = NetworkModel(nb_drones=nb, zones=zones, connections=connections)

    # At this point `model` is a validated NetworkModel
    network = Network()

    # instantiate runtime Zone objects
    for name, zone_model in model.zones.items():
        z = Zone(
            name=zone_model.name,
            x=zone_model.x,
            y=zone_model.y,
            z_type=zone_model.zone,
            max_drones=zone_model.max_drones,
            color=zone_model.color,
        )
        network.zones[name] = z

        if zone_model.role == ZoneRole.START:
            network.start_zone = z
        elif zone_model.role == ZoneRole.END:
            network.end_zone = z

    # instantiate connections
    for conn_model in model.connections:
        zone_a = network.zones[conn_model.node_a]
        zone_b = network.zones[conn_model.node_b]
        conn = Connection(zone_a=zone_a, zone_b=zone_b, max_link_capacity=conn_model.max_link_capacity)
        network.connections.append(conn)

    # instantiate drones and place them at the start hub
    if model.nb_drones:
        if network.start_zone is None:
            raise ValueError("Cannot place drones: no start_zone defined in network")
        for i in range(model.nb_drones):
            drone = Drone(drone_id=str(i + 1), start_zone=network.start_zone)
            network.drones.append(drone)

    return network