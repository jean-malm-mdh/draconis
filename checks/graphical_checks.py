import functools
from typing import Set, Dict
from AST import Program, FBD_Block, Rectangle
from graph_utilities import islands_from_program
def check_position_of_networks(prog:Program):
    def bounding_box_from_block_networks(networks:Dict[int, Set[int]]):
        """
        {1: {0, 1, 2, 4, 5, 6},
         2: {12, 13, 14, 16, 17, 18},
         3: {8, 7}}
        Args:
            networks:

        Returns:
        """
        converted_to_blockIDs = {i: set(map(lambda e: prog.ports[e].blockID, v)) for i, v in networks.items()}
        converted_to_block_boxes = {i: map(lambda e: prog.behaviour_id_map[e].getBoundingBox().getAsTuple(), v) for i, v in converted_to_blockIDs.items()}
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
    # Sort based on ascending y-value
    # Starting with top-left midpoint, check that all other unprocessed boxes are

    return ["Network 2 is misaligned. Networks shall be positioned top-to-bottom and left-to-right"]