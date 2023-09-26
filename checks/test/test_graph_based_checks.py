from checks.graph_utilities import (
    path_list_to_graph_edges,
    graph_from_program,
    islands_from_graph,
    islands_from_program
)
import os
import pytest
import networkx as nx
from matplotlib import pyplot as plt

from checks.graphical_checks import check_position_of_networks
from parser.helper_functions import parse_pou_file

from parser.test import programs


def test_path_list_to_graph():
    path = [[[9, 12, 10, 15, 13, 7]]]
    actual = path_list_to_graph_edges(path)
    assert {(9, 12), (12, 10), (10, 15), (15, 13), (13, 7)} == actual


def test_path_list_to_graph_duplicate_edges_are_ignored():
    path = [[[9, 12, 10, 15, 13, 7], [9, 12, 10, 15, 13, 7], [9, 12, 10, 15, 13, 7]]]
    actual = path_list_to_graph_edges(path)
    assert {(9, 12), (12, 10), (10, 15), (15, 13), (13, 7)} == actual




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


def test_given_program_with_multiple_networks_can_identify_each_with_element_names_and_ids(programs):
    prog = programs["feedback_example"]
    expected_with_qualified_names = {1: {"Output_Feedback_6", "ADD_S_3", "Input_A_4", "Input_B_5"},
                           2: {"Output_asd_18", "ADD_15", "Input_In1_16", "Input_hello_17"},
                           3: {"Output_B_8", "Input_Feedback_7"}}
    expected_with_IDs = {1: {0, 1, 2, 4, 5, 6},
                         2: {12, 13, 14, 16, 17, 18},
                         3: {8, 7}}
    assert expected_with_IDs == islands_from_program(prog)
    assert expected_with_qualified_names == islands_from_program(prog, display="Names")

def test_check_can_identify_graphically_misaligned_networks(programs):
    conforming_single_network_program = programs["MultiAND"]
    conforming_multi_network_program = programs["feedback_example"]
    nonconforming_multi_network = programs["feedback_example_misaligned_networks"]

    # Positive Cases
    assert [] == check_position_of_networks(conforming_single_network_program)
    assert [] == check_position_of_networks(conforming_multi_network_program)

    # Negative Cases
    assert ["Network 2 is misaligned. Networks shall be positioned top-to-bottom and left-to-right"] == \
           check_position_of_networks(nonconforming_multi_network)