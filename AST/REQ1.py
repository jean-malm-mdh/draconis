from langdetect import detect, lang_detect_exception
from program import Program

"""
{
  "name": "Meta-Llama-3-8B-Instruct-imatrix",
  "arch": "llama",
  "quant": "Q4_K_M",
  "context_length": 8192,
  "embedding_length": 4096,
  "num_layers": 32,
  "rope": {
    "freq_base": 500000,
    "dimension_count": 128
  },
  "head_count": 32,
  "head_count_kv": 8,
  "parameters": "7B"
}
Prompt:
Write a checker that uses the properties of the program class to checks if all comments and variable descriptions are in english. 
The solution shall run offline. Do not generate a class, use functions that take a program instance as input

Time to first token: 15.66s
Generation time: 30.13s
"""


def check_comments(program: Program) -> bool:
    for block in program.behaviourElements:
        if block.getBlockType() == "Comment":
            comment_text = block.getVarExpr()
            try:
                language_code = detect(comment_text)
                if language_code != 'en':
                    return False
            except lang_detect_exception.LangDetectException:
                # If the detection fails, assume it's not English
                return False
    return True


def check_variable_descriptions(program: Program) -> bool:
    for var in program.varHeader.getAllVariables():
        description = var.getDescription()
        try:
            language_code = detect(description)
            if language_code != 'en':
                return False
        except lang_detect_exception.LangDetectException:
            # If the detection fails, assume it's not English
            return False
    return True


def check_all(program: Program) -> bool:
    return check_comments(program) and check_variable_descriptions(program)
