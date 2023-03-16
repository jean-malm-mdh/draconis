import re
import nltk

nltk.download('punkt')
nltk.download("stopwords")
nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet')
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

def remove_nonessential_words(words, words_to_remove):
    return [w for w in words
            if w.casefold() not in words_to_remove]

def any_of_in(words, source):
    for word in words:
        if word in source:
            return True
    return False

def classify_as_metric_check(tagged_words, numbers):
    res = dict()
    res["check_type"] = "metric"
    if len(numbers) > 1:
        res["val"] = re.sub("[ ']", "", str(sorted(numbers, reverse=True)))
    elif len(numbers) > 0:
        res["val"] = str(numbers[0])

    lemmatized_words = [n for n, _ in tagged_words]

    if "between" in lemmatized_words:
        res["target_func"] = "interval"
    elif "exceed" in lemmatized_words:
        res["target_func"] = ">"

    if "not" in lemmatized_words:
        res["target_func"] = f"not({res['target_func']})"
    properties = [n for n, t in tagged_words if str(t).startswith("NN") or t.startswith("JJ")]
    res["property"] = "variable"
    return res

def get_issue_level(tagged_words):
    issue_level_qualifier = [n for n, t in tagged_words if t == "MD"]
    if any_of_in(["shall", "must", "cannot", "need", "will", "couldn't"], issue_level_qualifier):
        return "error"
    else:
        return "warning"


def classify(req_text: str):
    res = dict()
    lemmatizer = WordNetLemmatizer()
    token_words = word_tokenize(req_text)
    stopwords_to_include = {"not", "between"}
    words = remove_nonessential_words(token_words, set(stopwords.words("english")).difference(stopwords_to_include))
    lemmatized_words = [lemmatizer.lemmatize(word) for word in words]
    tagged_words = nltk.pos_tag(lemmatized_words)
    numbers = [n for n, t in tagged_words if t == "CD"]  # CD = numeral/cardinal
    issue_level_qualifier = [n for n, t in tagged_words if t == "MD"]
    print(tagged_words)
    if len(numbers):
        res = classify_as_metric_check(tagged_words, numbers)
    res["issue_level"] = get_issue_level(tagged_words)
    return res
