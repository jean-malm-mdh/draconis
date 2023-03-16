import re
import nltk

nltk.download('punkt')
nltk.download("stopwords")
nltk.download('averaged_perceptron_tagger')
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize


def remove_nonessential_words(words, words_to_remove):
    return [w for w in words
            if w.casefold() not in words_to_remove]


def classify(req_text: str):
    res = dict()
    token_words = word_tokenize(req_text)
    stopwords_to_include = {"not", "between"}
    words = remove_nonessential_words(token_words, set(stopwords.words("english")).difference(stopwords_to_include))
    tagged_words = nltk.pos_tag(words)
    numbers = [n for n, t in tagged_words if t == "CD"]  # CD = numeral/cardinal
    print(tagged_words)
    if len(numbers):
        res["check_type"] = "metric"

    if len(numbers) > 1:
        res["val"] = re.sub("[ ']", "", str(sorted(numbers, reverse=True)))
    elif len(numbers) > 0:
        res["val"] = str(numbers[0])
    if "between" in req_text:
        res["target_func"] = "interval"
    elif "exceed" in req_text:
        res["target_func"] = ">"

    if "not" in req_text:
        res["target_func"] = f"not({res['target_func']})"
    res["property"] = "variable"
    if "shall" in req_text:
        res["issue_level"] = "error"
    else:
        res["issue_level"] = "warning"
    return res
