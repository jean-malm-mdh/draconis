

"""
Time to first token: 12.18s

gen t: 45.69s
"""
from program import Program
def check_for_signal_line_collisions(program: Program) -> None:
    signal_lines = {}
    for block in program.behaviourElements:
        if block.getBlockType() == "SignalLine":
            line_id = block.getID()
            if line_id not in signal_lines:
                signal_lines[line_id] = []
            for other_block in program.behaviourElements:
                if other_block != block and other_block.getBlockType() == "SignalLine":
                    other_line_id = other_block.getID()
                    if other_line_id not in signal_lines:
                        signal_lines[other_line_id] = []
                    line1 = [int(x) for x in block.getCoords().split(",")]
                    line2 = [int(x) for x in other_block.getCoords().split(",")]
                    if len(set(line1 + line2)) < 4:  # Check if the lines overlap
                        print(f"Warning: Signal lines {line_id} and {other_line_id} overlap.")
                    elif abs((line1[0] - line1[2]) * (line2[3] - line2[1]) -
                             (line1[2] - line1[0]) * (line2[1] - line2[3])) < 1e-6:  # Check if the lines intersect
                        print(f"Warning: Signal lines {line_id} and {other_line_id} cross over.")