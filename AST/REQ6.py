from program import Program


def check_input_complexity(program: Program) -> bool:
    """
    Checks if the combined complexity of program inputs does not exceed 100.

    :param program: The Program instance to check
    :return: True if the input complexity is within limits, False otherwise
    """

    # Define a dictionary to map variable types to their corresponding complexities
    complexity_map = {
        "Boolean": 2,
        "Numeric": 5,
        "String": 10,
        "Object": 20,
        "Array": 30
    }

    input_complexity = 0

    for var in program.varHeader.getAllVariables():
        if var.isInputVar:
            # Get the variable type and calculate its complexity based on the map
            var_type = var.getVarType()
            complexity = complexity_map.get(var_type, 10)  # default to a moderate complexity of 10

            input_complexity += complexity

    return input_complexity <= 100
