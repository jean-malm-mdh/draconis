from program import Program
def check_for_overlapping_blocks(program: Program) -> None:
    block_ids = set()
    for block in program.behaviourElements:
        if block.getBlockType() == "FunctionBlock":
            boundary_box = block.data.boundary_box
            if boundary_box:
                x1, y1, x2, y2 = boundary_box
                for other_block in program.behaviourElements:
                    if other_block != block and other_block.getBlockType() == "FunctionBlock":
                        other_boundary_box = other_block.data.boundary_box
                        if other_boundary_box:
                            ox1, oy1, ox2, oy2 = other_boundary_box
                            if x1 <= ox2 and ox1 <= x2 and y1 <= oy2 and oy1 <= y2:
                                print(f"Warning: Blocks with IDs {block.getID()} and {other_block.getID()} overlap.")