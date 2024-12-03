"""
2.40s

gen t: 25.45s
"""
from program import Program
def check_variable_name_length(program: Program) -> bool:
    for var in program.varHeader.getAllVariables():
        if len(var.getName()) > 20:
            print(f"Warning: Variable name '{var.getName()}' is too long (more than 20 characters)")
            return False
    return True