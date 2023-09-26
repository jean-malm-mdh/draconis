import functools
from typing import Set, Dict
from AST import Program, FBD_Block, Rectangle
from graph_utilities import islands_from_program


def check_position_of_networks(prog: Program):
    def bounding_box_from_block_networks(networks: Dict[int, Set[int]]):
        """
        {1: {0, 1, 2, 4, 5, 6},
         2: {12, 13, 14, 16, 17, 18},
         3: {8, 7}}
        Args:
            networks:

        Returns:
        """
        converted_to_blockIDs = {i: set(map(lambda e: prog.ports[e].blockID, v)) for i, v in networks.items()}
        converted_to_block_boxes = {i: list(map(lambda e: prog.behaviour_id_map[e].getBoundingBox().getAsTuple(), v)) for i, v
                                    in converted_to_blockIDs.items()}
        converted_to_bounding_boxes = {}
        for i, boxes in converted_to_block_boxes.items():
            left = functools.reduce(min, map(lambda e: e[0], boxes))
            top = functools.reduce(min, map(lambda e: e[1], boxes))
            right = functools.reduce(max, map(lambda e: e[2], boxes))
            bottom = functools.reduce(max, map(lambda e: e[3], boxes))
            converted_to_bounding_boxes[i] = Rectangle.fromTuple(left, top, right, bottom)
        return converted_to_bounding_boxes

    networks = islands_from_program(prog)
    if len(networks) <= 1:
        return []

    # Make bounding boxes around all networks
    bounding_boxed_networks = bounding_box_from_block_networks(networks)
    boxed_networks_as_list = [(i, b.getAsTuple()) for i, b in bounding_boxed_networks.items()]
    networks_midpoints_as_list = [(i, (l+r//2, t+b//2)) for i, (l, t, r, b) in boxed_networks_as_list]

    # Sort based on ascending y-value
    sorted_by_midpoints = sorted(networks_midpoints_as_list, key=lambda e: e[1][1])

    result = set()
    MARGIN_VALUE = -5
    # check that all succeeding boxes in the list are either below or to the right
    for index in range(len(sorted_by_midpoints)):
        net_id, (curr_px, curr_py) = sorted_by_midpoints[index]
        for next_index in range(index+1, len(sorted_by_midpoints)):
            next_net_id, (next_px, next_py) = sorted_by_midpoints[next_index]
            if next_px - curr_px < MARGIN_VALUE:
                result.add(net_id)

    return [f"Network {net_id} is misaligned. Networks shall be positioned top-to-bottom and left-to-right" for net_id in result]
