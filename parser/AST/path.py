from dataclasses import dataclass
from typing import List


@dataclass()
class PathDivide:
    def __init__(self, paths: List[list[int]]):
        self.paths = paths

    def __eq__(self, other):
        signature__ = str(type(other))
        if "PathDivide" in str(signature__):
            return self.paths == other.paths
        return False

    def __ne__(self, other):
        return not (self.__eq__(other))

    def __str__(self):
        f'D({";".join([str(e) for e in self.paths])})'

    def __len__(self):
        return max(map(self.__len__, self.paths))

    @classmethod
    def unpack_pathlist(cls, pathList):
        """Take a list of paths and unpack all PathDivide objects into separate lists"""
        result = []
        for p in pathList:
            accList = []
            NoDividingPath = True
            for p_e in p:
                if isinstance(p_e, PathDivide):
                    NoDividingPath = False
                    _divPaths = PathDivide.unpack_pathlist(p_e.paths)
                    for _p in _divPaths:
                        _fin = [e for e in accList]  # Copy accumulated path until here
                        _fin.extend(_p)  # Extend with the flattened path
                        result.append(_fin)
                else:
                    accList.append(p_e)
            if len(accList) and NoDividingPath:
                result.append(accList)
        return result

    def flatten(self):
        return PathDivide.unpack_pathlist(self.paths)


def test_can_flatten_pathdivide_to_path_sequences():
    assert PathDivide.unpack_pathlist([[1, 2], [3, 4]]) == [[1, 2], [3, 4]]


def test_flatten_shall_handle_empty_paths_through_removal():
    assert PathDivide.unpack_pathlist([[1, 2], []]) == [[1, 2]]
    assert PathDivide.unpack_pathlist([[], [1, 2]]) == [[1, 2]]


def test_can_flatten_multiple_levels_of_pathdivides():
    div_prime = PathDivide([[3, 4], [5, 6]])
    actual_input = PathDivide([[1, 2, div_prime], [7, 8]])
    assert actual_input.flatten() == [[1, 2, 3, 4], [1, 2, 5, 6], [7, 8]]

    div_prime_prime = PathDivide([[10, 11, 12], [13, 14, 15]])
    div_prime_2 = PathDivide([[3, 4, div_prime], [5, div_prime_prime]])
    actual_input = PathDivide([[1, 2, div_prime_2], [7, 8], [99, 100]])
    assert actual_input.flatten() == [
        [1, 2, 3, 4, 3, 4],
        [1, 2, 3, 4, 5, 6],
        [1, 2, 5, 10, 11, 12],
        [1, 2, 5, 13, 14, 15],
        [7, 8],
        [99, 100],
    ]
