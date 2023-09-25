import networkx as nx

from AST.program import Program
from AST.path import PathDivide
def program_to_graph(prog: Program):
    resultGraph = nx.Graph()
    traces = prog.getBackwardTrace()
    edges = set()
    for _, trace in traces.items():
        trace_unpacked = PathDivide.unpack_pathlist(trace)
        for path in trace_unpacked:
            for tLIndex in range(len(trace_unpacked)-1):
                edges.add((path[tLIndex], path[tLIndex+1]))
            #assert edges == [
             #   [9, 12, 10, 15, 13, 7],
             #   [9, 12, 10, 15, 14, 8],
             #   [9, 12, 11, 6],]
            # [(9, 12), (12,10), (10,15), (15,13), (13, 7)]
    for eF, eT in edges:
        resultGraph.add_edge(eF, eT)
