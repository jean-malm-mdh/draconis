import re
import nltk
import word2number.w2n
from typing import List, Tuple

nltk.download('punkt')
nltk.download("stopwords")
nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet')
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

from word2number.w2n import word_to_num


def remove_nonessential_words(words, words_to_remove):
    return [w for w in words
            if w.casefold() not in words_to_remove]


def any_of_in(words, source):
    for word in words:
        if word in source:
            return True
    return False

def get_stub_pairs():
    res = dict()
    res["in"] = "out"
    return res

def iter_partition(pred, iterable):
    _in, _out = [], []
    for e in iterable:
        if pred(e):
            _in.append(e)
        else:
            _out.append(e)
    return _in, _out

def get_index_by_property(pred, iterable):
    """Returns the index of the first item in `iterable` that matches the predicate `pred`
    Returns None if no item matches property"""
    for i in range(len(iterable)):
        if pred(iterable[i]):
            return i
    return None


def classify_as_metric_check(tagged_words:List[Tuple[str,str]], numbers):
    def classify_target_func(words):
        if "between" in words:
            return "interval"
        elif any_of_in(["exceed", "above", "more"], words):
            return ">"
        elif any_of_in(["below", "less", "under"], words):
            return "<"

    def negate_function(func):
        switcher = {"<": ">=", ">": "<=", "==": "!=", ">=": "<", "<=": ">", "!=": "=="}
        return switcher.get(func, f"not({func})")

    res = dict()
    res["check_type"] = "metric"
    if len(numbers) > 1:
        numbers_sorted = sorted(list(map(lambda s: int(s), numbers)))
        res["val"] = re.sub("[ ']", "", str(numbers_sorted))
    elif len(numbers) > 0:
        res["val"] = str(numbers[0])

    lemmatized_words = [n for n, _ in tagged_words]

    res["target_function"] = classify_target_func(lemmatized_words)

    if "not" in lemmatized_words:
        res["target_function"] = negate_function(res["target_function"])

    enumeration, properties = iter_partition(lambda e: e.endswith("-"),
                                             [n for n, t in tagged_words if t.startswith("NN") or t.startswith("JJ")])
    connector_word_index = get_index_by_property(lambda e: e == "and" or e == "or", lemmatized_words)
    if connector_word_index is not None and res["target_function"] != "interval":
        """It is an combined property"""
        if "total" in properties:
            """all parts shall be summed"""
            res["property"] = "SUM"
            properties.remove("total")
        if "number" in properties:
            """We already know it is a number"""
            properties.remove("number")
        if enumeration and connector_word_index is not None and tagged_words[connector_word_index+1][0] in properties:
            # stubs should be part of enumeration, where the last word is a combination of the stub and the root
            # For now we assume that enumerations are on the form of r"(stub-,? ) and (stub)(root)"
            first_stub = enumeration[0].rstrip("-")
            last_enum_word, last_enum_tag = tagged_words[connector_word_index+1]
            root_part = last_enum_word.replace(get_stub_pairs().get(first_stub, None), "")
            assert (root_part != last_enum_word and "there was no extraction of root part")
            unstubbed = [e.replace("-", root_part) for e in enumeration]
            unstubbed.append(last_enum_word)
            properties.remove(last_enum_word)
            suffix = "_".join(properties)
            unstubbed = [e + "_" + suffix for e in unstubbed]
            res["property"] = f"{res['property']}([{','.join(unstubbed)}])"
    else:
        res["property"] = "variable"
    return res


def get_issue_level(tagged_words):
    issue_level_qualifier = [n for n, t in tagged_words if t == "MD"]
    if any_of_in(["shall", "must", "cannot", "need", "will", "couldn't"], issue_level_qualifier):
        return "error"
    else:
        return "warning"


def get_numstr_orNone_from_word(word):
    try:
        res = word_to_num(word)
        return str(res)
    except ValueError as e:
        return None


def classify(req_text: str):
    res = dict()
    lemmatizer = WordNetLemmatizer()
    token_words = word_tokenize(req_text)
    stopwords_to_include = {"not", "between", "above"}
    filtered_stopwords = [w for w in stopwords.words("english") if len(w) < 3]
    filtered_stopwords.append("the")
    words = remove_nonessential_words(token_words,
                                      set(filtered_stopwords).difference(stopwords_to_include))
    lemmatized_words = [lemmatizer.lemmatize(word) for word in words]
    tagged_words = nltk.pos_tag(lemmatized_words)
    numbers = [n for n, t in tagged_words if t == "CD" or t == "NNP"]  # CD = numeral/cardinal
    numbers.extend([n for n in [get_numstr_orNone_from_word(w) for w, t in tagged_words if t != "CD"] if n is not None])
    issue_level_qualifier = [n for n, t in tagged_words if t == "MD"]
    print(tagged_words)
    if len(numbers):
        res = classify_as_metric_check(tagged_words, numbers)
    res["issue_level"] = get_issue_level(tagged_words)
    return res


def complies(data, req):
    classified_req = classify(req)
    if classified_req["target_function"] == "interval":
        l = eval(classified_req["val"])
        res = eval(f"{data[classified_req['property']]} >= {l[0]}")
        res2 = eval(f"{data[classified_req['property']]} <= {l[1]}")
        return res and res2
    else:
        res = eval(f"{data[classified_req['property']]} {classified_req['target_function']} {classified_req['val']}")
        return res
