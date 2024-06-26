from antlr4 import InputStream, CommonTokenStream

import MyPOUVisitor
import MyXMLVisitor
from antlr_generated.python import POULexer, POUParser
from antlr_generated.python import XMLLexer, XMLParser

from pathlib import Path
import xml.etree.ElementTree as ET

# Helpers


def get_worksheets_from_input(input_program: str):
    index_start_of_XML = input_program.index("<?xml version")
    end_of_xml_tag = "</FBD>"
    index_end_of_XML = input_program.index(end_of_xml_tag)
    input_varWorkSheet = input_program[0:index_start_of_XML]
    input_codeSheet = input_program[
        index_start_of_XML : (index_end_of_XML + len(end_of_xml_tag))
    ]

    return input_varWorkSheet, input_codeSheet


def parse_variable_worksheet(input_varWorkSheet):
    inputDataVarHeader = InputStream(input_varWorkSheet)
    lexer = POULexer.POULexer(inputDataVarHeader)
    tokens = CommonTokenStream(lexer)
    parser = POUParser.POUParser(tokens)
    tree = parser.safe_program_POU()  # Begin parsing at this rule
    result = MyPOUVisitor.MyPOUVisitor().visitSafe_program_POU(tree)
    return result


def parse_code_worksheet(input_codeWorkSheet: str):
    """
    Parses the code worksheet defined by the input string
    Returns the elements and an ID map
    """
    inputDataVarHeader = InputStream(input_codeWorkSheet)
    lexer = XMLLexer.XMLLexer(inputDataVarHeader)
    tokens = CommonTokenStream(lexer)
    parser = XMLParser.XMLParser(tokens)
    tree = parser.document()  # Begin parsing at this rule
    visitor = MyXMLVisitor.MyXMLVisitor()
    visitor.visitDocument(tree)
    return visitor.elements, visitor.local_id_map, visitor.lines, visitor.comments


def clean_pou_string(input_pou_prog: str):
    """Removes useless parts of the program before parsing"""
    return input_pou_prog.replace("﻿", "")

def parse_pou_content(pou_content_str):
    program_string = clean_pou_string(pou_content_str)
    varSheet, codeSheet = get_worksheets_from_input(program_string)

    resultProgram = parse_variable_worksheet(varSheet)
    (
        resultProgram.behaviourElements,
        resultProgram.behaviour_id_map,
        resultProgram.lines,
        resultProgram.comments,
    ) = parse_code_worksheet(codeSheet)
    resultProgram.post_parsing_analysis()
    return resultProgram

def parse_pou_file(pou_file_path: str):
    return parse_pou_content(clean_pou_string(Path(pou_file_path).read_text()))


def change_pou_description(description_file, description):
    parsed_tree = ET.parse(description_file)
    for translation in parsed_tree.iter("translation"):
        translation.text = description
    parsed_tree.write(description_file)


def get_pou_description(pou_description_file):
    """Grabs description from DescriptionTranslation_SF.xml file"""
    parsed_tree = ET.parse(pou_description_file)
    res_trans = list(parsed_tree.iter("translation"))[0]

    return res_trans.text


ANALYSIS_GENERATED_HEADER = (
    "%%%Autogenerated Analysis Report. Do not edit below this line!%%%"
)


def append_analysis_to_text(original_description_content, prog_report):
    return f"{original_description_content}\n{ANALYSIS_GENERATED_HEADER}\n{prog_report}"


def append_analysis_to_pou_description_file(pou_description_file, analysis_report):
    original_content = get_pou_description(pou_description_file)
    new_content = append_analysis_to_text(original_content, analysis_report)
    change_pou_description(pou_description_file, new_content)


def remove_analysis_from_pou_description_file(pou_description_file):
    content = get_pou_description(pou_description_file)
    non_analysis_content = content[: content.index(ANALYSIS_GENERATED_HEADER)]
    change_pou_description(pou_description_file, non_analysis_content)
