from typing import List, Set
import networkx as nx

from AST import PathDivide, Port
from draconis_parser import Program


def path_list_to_graph_edges(path_list: List[List[List[int]]]):
    edges = set()
    for trace in path_list:
        for path in trace:
            for tLIndex in range(len(path) - 1):
                edges.add((path[tLIndex], path[tLIndex + 1]))
    return edges


def graph_from_program(prog: Program):
    resultGraph = nx.Graph()
    all_edges = set()
    traces = prog.getBackwardTrace()
    for out_var_name, path in traces.items():
        flat_paths = PathDivide.unpack_pathlist([path])
        curr_edges = path_list_to_graph_edges([flat_paths])
        all_edges = all_edges.union(curr_edges)

    for edgeF, edgeT in all_edges:
        resultGraph.add_edge(edgeF, edgeT)
    return resultGraph


def islands_from_graph(graph: nx.Graph):
    return {i + 1: island for i, island in enumerate(nx.connected_components(graph))}


def islands_from_program(prog: Program, display="IDs"):
    def blockID_to_display_name(ID):
        port = prog.ports.get(ID, None)
        if port is None:
            return ID
        assert isinstance(port, Port)
        block = prog.behaviour_id_map[port.blockID]
        name = block.getName()
        return f"{name}_{port.blockID}"

    islands = islands_from_graph(graph_from_program(prog))
    if display == "Names":
        return {i: set(map(blockID_to_display_name, v)) for i, v in islands.items()}
    else:
        return islands


def cycles_in_program(prog: Program):
    def cycles_in_graph(graph: nx.Graph):
        return nx.cycle_basis(graph)

    return cycles_in_graph(graph_from_program(prog))
