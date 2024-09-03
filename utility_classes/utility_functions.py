def dropWhile(aList: list, p):
    for i in range(len(aList)):
        if not (p(aList[i])):
            return aList[i:]
    return []
