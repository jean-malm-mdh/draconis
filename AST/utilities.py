def swap_in_string(s, s1, s2):
    dummyString = "€€€&&ASDFGHJK"
    return str(s).replace(f"{s1}", dummyString).replace(f'{s2}', f"{s1}").replace(dummyString, f'{s2}')


def AllindexOrNone(aList, elem, startIndex=0):
    """

    Args:
        aList: enumerable to search through
        elem: element to search for

    Returns: A list of all indices matching element. If elem cannot be found, returns None

    """
    return [i for i, val in enumerate(aList[startIndex:]) if val == elem] or None


def indexOrNone(aList, elem, startIndex=0):
    """

    Args:
        aList: enumerable to search through
        elem: element to search for

    Returns: Index of element elem in list aList. If elem cannot be found, returns None

    """
    for i in range(startIndex, len(aList)):
        if aList[i] == elem:
            return i
    return None
