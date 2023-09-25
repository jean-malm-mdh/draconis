from typing import List, Set
import networkx as nx

from AST import PathDivide
from parser import Program


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
