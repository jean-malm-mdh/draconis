
from typing import List, Dict, Tuple
import re

def unique(xs):
    if "__len__" not in dir(xs):
        xs = list(xs)
    return len(xs) == len(set(xs))

def any_match(pat, s):
    return bool(re.search(pat, s))

def full_match(pat, s):
    return bool(re.fullmatch(pat, s))

def in_list(targetList, inputList):
    return set(targetList).issuperset(inputList)

def is_magic_named_constant(potential_constant):
    magic_constant_words = ["MILLION", "THOUSAND", "HUNDRED","ZERO", "ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN", "EIGHT", "NINE", "C_True", "C_False"]
    for w in magic_constant_words:
        if w in potential_constant:
            return True
    return False

def conforms_to(name_groups: Dict[str, List[str]], pattern: str, input: str) -> bool:
    def consume_until_template_start(pattern: str, result: str) -> Tuple[str, str]:
        i = 0
        length = len(pattern)
        while i < length and pattern[i] != "<":
            if pattern[i] != result[i]:
                return None
            i += 1
        return pattern[i:], result[i:]

    def read_until_template_end(s: str) -> str:
        acc = ""
        i = 0
        while s[i] != ">":
            acc += s[i]
            i += 1
        acc += ">"
        return acc

    def found_entry_in_string_start(aString: str, list_entries: List[str]):
        """Returns the longest match from list_entries found at start of string

        Args:
            aString (str): string to match against
            list_entries (List[str]): list of entities to match. Supports basic regular expressions

        Returns:
            _type_: None if no matches found, otherwise the string value of the match
        """
        result = [
            m for m in [re.match(e, aString) for e in list_entries] if m is not None
        ]
        result.sort(key=lambda m: len(m.group(0)))
        if result:
            return result[-1].group(0)
        return None

    def consume_group(pattern: str):
        acc = ""
        i = 0
        while pattern and pattern[i] != ")":
            acc += pattern[i]
            i += 1
        acc += ")"
        i += 1
        return acc, pattern[i:]

    def check_template_conformance(pattern: str, result: str) -> Tuple[str, str]:
        ## If pattern begins with <, append characters until > to group, then check name_groups[group] values using string.startswith
        templateTag = read_until_template_end(pattern)
        pattern = pattern[len(templateTag) :]
        ZeroOrMore = bool(pattern) and pattern[0] == "*"
        OneOrMore = bool(pattern) and pattern[0] == "+"
        ZeroOrOne = bool(pattern) and pattern[0] == "?"
        if ZeroOrMore or OneOrMore or ZeroOrOne:
            pattern = pattern[1:]
        template_list_entries = name_groups.get(templateTag, None)
        if template_list_entries is None:
            raise ValueError(f"Tag {templateTag} does not exist in {name_groups}")

        finding = found_entry_in_string_start(result, template_list_entries)
        if OneOrMore and finding is None:
            return None
        if ZeroOrMore or OneOrMore:
            # Match until it cannot be matched anymore
            while finding is not None:
                result = result[len(finding) :]
                finding = found_entry_in_string_start(result, template_list_entries)
        elif ZeroOrOne:
            if finding is None:
                # OK! matched zero times
                return pattern, result
            else:
                result = result[len(finding) :]
                # Try to match a second time
                finding = found_entry_in_string_start(result, template_list_entries)
                if finding is not None:
                    return None  # forbidden, matched it twice
        else:
            if finding is None:
                return None
            result = result[len(finding) :]
        return pattern, result

    def check_group_conformance(group, result, timesToMatch=None):
        pattern = group[1:-1]
        _result = result
        timesToMatch = timesToMatch or "once"
        if timesToMatch == "oneOrMore":
            tmpres = process_pattern(pattern, result)
            if tmpres is None:
                return None
            while tmpres is not None:
                _result = tmpres
                tmpres = process_pattern(pattern, _result)
        elif timesToMatch == "zeroOrMore":
            tmpres = process_pattern(pattern, result)
            if tmpres is None:
                return result
            else:
                while tmpres is not None:
                    _result = tmpres
                    tmpres = process_pattern(pattern, _result)                
        else:
            tmpres = process_pattern(pattern, result)
            if tmpres is not None:
                _result = tmpres                
                # Try to match a second time
                tmpres = process_pattern(pattern, _result)
                if tmpres is not None and _result != tmpres:
                    return None  # forbidden, matched it twice
        return _result

    def process_pattern(pattern, inString):
        while pattern != "":
            tmpres = process_next_item(pattern, inString)
            if tmpres is None:
                return None
            inString, pattern = tmpres
        return inString

    def process_next_item(pattern: str, result: str) -> Tuple[str, str]:
        # Get next entity from pattern to process

        if pattern[0] == "<":
            tmpres = check_template_conformance(pattern, result)
            if tmpres == None:
                return None
            pattern, result = tmpres
        elif pattern[0] == "(":
            group, pattern = consume_group(pattern)
            assert group[0] == "(" and group[-1] == ")"
            repeatZeroOrMore = bool(pattern) and pattern[0] == "*"
            repeatOneOrMore = bool(pattern) and pattern[0] == "+"
            repeatZeroOrOne = bool(pattern) and pattern[0] == "?"
            repeatOption = (
                "oneOrMore"
                if repeatOneOrMore
                else "zeroOrMore"
                if repeatZeroOrMore
                else "exactlyOnce"
            )
            result = check_group_conformance(group, result, repeatOption)

            if repeatZeroOrMore or repeatOneOrMore or repeatZeroOrOne:
                pattern = pattern[1:]
        else:
            ## If pattern does not begin with <, consume all characters from result and pattern until < is found
            tmpres = consume_until_template_start(pattern, result)
            if tmpres == None:
                return None
            pattern, result = tmpres
        return result, pattern

    # degenerative cases
    if pattern == "":
        return input == ""
    if input == "":
        if not (re.search(r"^.*?[*?].*$", pattern)):
            return pattern == ""
    # pattern has no templates, boils down to string comparison
    if not re.search(r"<[a-zA-Z]+>", pattern):
        return pattern == input

    result = input
    while pattern != "":
        tmpres = process_next_item(pattern, result)
        if tmpres is not None:
            result, pattern = tmpres
        else:
            return False

    # Since we remove elements from both result and pattern, string conforms to the pattern iff both are empty at the end
    return pattern == "" and result == ""