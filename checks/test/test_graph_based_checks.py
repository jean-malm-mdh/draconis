from checks.graph_based_checks import (
    path_list_to_graph_edges,
    graph_from_program,
    islands_from_graph,
    islands_from_program
)
import os
import pytest
import networkx as nx
from matplotlib import pyplot as plt

from parser.helper_functions import parse_pou_file


def test_path_list_to_graph():
    path = [[[9, 12, 10, 15, 13, 7]]]
    actual = path_list_to_graph_edges(path)
    assert {(9, 12), (12, 10), (10, 15), (15, 13), (13, 7)} == actual


def test_path_list_to_graph_duplicate_edges_are_ignored():
    path = [[[9, 12, 10, 15, 13, 7], [9, 12, 10, 15, 13, 7], [9, 12, 10, 15, 13, 7]]]
    actual = path_list_to_graph_edges(path)
    assert {(9, 12), (12, 10), (10, 15), (15, 13), (13, 7)} == actual


@pytest.fixture(scope="session", autouse=True)
def programs():
    testDir = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "../../parser/test"
    )
    programs = dict(
        [
            (n, parse_pou_file(p))
            for n, p in [
            (
                "Calc_Odd",
                f"{testDir}/Collatz_Calculator_Odd/Collatz_Calculator_Odd.pou",
            ),
            (
                "Calc_Even",
                f"{testDir}/Collatz_Calculator_Even/Collatz_Calculator_Even.pou",
            ),
            (
                "Calc_Even_SafeVer",
                f"{testDir}/Collatz_Calculator_Even/Collatz_Calculator_Even_UnsafeIn_SafeOut.pou",
            ),
            ("MultiAND", f"{testDir}/MultiANDer.pou"),
            ("MultiANDAddedVariable", f"{testDir}/MultiANDAddedVariables.pou"),
            ("MultiANDRemovedVariable", f"{testDir}/MultiANDRemovedVariable.pou"),
            (
                "SingleIn_MultiOut",
                f"{testDir}/TestPOU_SingleInput_MultipleOutput.pou",
            ),
            ("output_has_non_outputs", f"{testDir}/output_has_non_output_vars.pou"),
            ("input_has_non_inputs", f"{testDir}/input_has_non_input_vars.pou"),
            ("empty_no_proper_groups", f"{testDir}/empty_prog_no_groups.pou"),
            ("feedback_example", f"{testDir}/Feedback_Exampple.pou"),
        ]
        ]
    )
    return programs


def test_graph_from_empty_program_is_empty_graph(programs):
    prog = programs["empty_no_proper_groups"]
    expected = nx.Graph()
    expected.add_edges_from([])
    actual = graph_from_program(prog)
    assert expected.adj == actual.adj


def test_graph_from_program_makes_graph_of_portIDs(programs):
    prog = programs["MultiAND"]
    expected = nx.Graph()
    expected.add_edges_from([(9, 2), (2, 0), (0, 5), (2, 1), (1, 7), (2, 4), (4, 8)])
    actual = graph_from_program(prog)
    assert expected.adj == actual.adj


def test_given_multiple_islands_can_identify_each():
    graph = nx.Graph()
    island1 = [(1, 2), (2, 3), (3, 4)]
    island2 = [(10, 20), (20, 30), (30, 40)]
    graph.add_edges_from(island1)
    graph.add_edges_from(island2)
    expected = {1: {1, 2, 3, 4}, 2: {10, 20, 30, 40}}
    actual = islands_from_graph(graph)
    assert expected == actual


def test_given_program_with_multiple_networks_can_identify_each(programs):
    prog = programs["feedback_example"]
    expected_with_qualified_names = {1: {"Output_Feedback_6", "ADD_S_3", "Input_A_4", "Input_B_5"},
                           2: {"Output_asd_18", "ADD_15", "Input_In1_16", "Input_hello_17"},
                           3: {"Output_B_8", "Input_Feedback_7"}}
    expected_with_IDs = {1: {0, 1, 2, 4, 5, 6},
                         2: {12, 13, 14, 16, 17, 18},
                         3: {8, 7}}
    assert expected_with_IDs == islands_from_program(prog)
    assert expected_with_qualified_names == islands_from_program(prog, display="Names")
