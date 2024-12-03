from program import Program

"""
Time to first token: 11.79s

gen t: 24.30s
"""


def check_variable_count(program: Program) -> bool:
    return len(program.varHeader.getAllVariables()) < 20


def check_variable_count2(program: Program) -> bool:
    if len(program.varHeader.getAllVariables()) >= 20:
        print("Warning: Too many variables (more than 20)")
    return True
