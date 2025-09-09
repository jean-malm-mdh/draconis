import io
import json
import logging
import os
import subprocess
import tempfile
import sys
from typing import List

from django.db.models.fields.files import FieldFile

from .models import ReportModel, MetricsModel, BlockModel, SVGModel
from PIL import Image, ImageChops

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), "../.."))
from draconis_parser.renderer import render_program_to_svg, generate_image_of_program
from draconis_parser.helper_functions import parse_pou_content, parse_pou_file

DEFAULT_RENDER_SCALE = 5.0


def renderToReport(program, scale=None):
    _scale = scale or DEFAULT_RENDER_SCALE
    imageWidth, imageHeight, imageSVGString = render_program_to_svg(program, _scale)
    return imageSVGString, imageWidth, imageHeight


def highlight_differences_in_red(img1, img2):
    def isInImgRect(w, h, px, py):
        return px <= w and py <= h

    diff = ImageChops.difference(img1, img2)
    # diff's size seems to based on smallest image.

    red_diff = diff.convert("RGB")
    dummy_pixel = diff.getpixel((0, 0))

    # Create a new image to store the result
    # This needs to be the size of the biggest image
    maxSize = (max(img1.width, img2.width), max(img1.height, img2.height))
    result = Image.new("RGB", maxSize)

    # Starting from top left corner, iterate over the difference
    for x in range(red_diff.width):
        for y in range(red_diff.height):
            r, g, b = red_diff.getpixel((x, y))
            # If there's a difference (non-zero pixel), make it red
            if r + g + b > 0:
                result.putpixel((x, y), (255, 0, 0))  # Red color
            else:
                result.putpixel((x, y), img1.getpixel((x, y)))  # Original color

    if red_diff.width < maxSize[0]:
        blendColor, theWidestImage = ((0, 0, 50), img1) if img1.width > img2.width else ((0, 50, 0), img2)

        # Right-most column is not filled in
        # Fill it with some blend of the image and a hue color
        for y in range(red_diff.height):
            for x in range(red_diff.width, maxSize[0]):
                thePixel = theWidestImage.getpixel((x, y))
                result.putpixel((x, y), (
                    thePixel[0], int(thePixel[1] / 2 + blendColor[1]), int(thePixel[2] / 2 + blendColor[2])))
    if red_diff.height < maxSize[1]:
        blendColor, theTallestImage = ((0, 0, 50), img1) if img1.height > img2.height else ((0, 50, 0), img2)

        # Right-most column is not filled in
        # Fill it with some blend of the image and a hue color
        for y in range(red_diff.height, maxSize[1]):
            for x in range(red_diff.width):
                thePixel = theTallestImage.getpixel((x, y))
                result.putpixel((x, y), (
                    thePixel[0], int(thePixel[1] / 2 + blendColor[1]), int(thePixel[2] / 2 + blendColor[2])))

    if red_diff.width < maxSize[0] and red_diff.height < maxSize[1]:
        px, py = (red_diff.width + maxSize[0] / 2, red_diff.height + maxSize[1] / 2)
        for img in [i for i in [img1, img2] if isInImgRect(i.width, i.height, px, py)]:
            for y in range(red_diff.height, img.height):
                for x in range(red_diff.width, img.width):
                    result.putpixel((x, y), img.getpixel((x, y)))
    return result


def make_and_save_diff_image(program1, program2, storage_path: str, render_scale=2.0, name_postfix=""):
    fpp_dir = tempfile.gettempdir()
    fpp = os.path.join(fpp_dir, "prog1.jpg")
    fpp2 = os.path.join(fpp_dir, "prog2.jpg")
    fpp_diff = f"prog_diff{name_postfix}.jpg"
    generate_image_of_program(program1, fpp, scale=render_scale, generate_report_in_image=False,
                              surpress_components=["comments"])
    generate_image_of_program(program2, fpp2, scale=render_scale, generate_report_in_image=False,
                              surpress_components=["comments"])
    img1 = Image.open(fpp)
    img2 = Image.open(fpp2)
    diff = highlight_differences_in_red(img1, img2)
    diff.save(os.path.join(storage_path, "images", ".generated", fpp_diff))
    return fpp_diff


def add_modelfile_to_db(program_file, additional_metrics_json_str, project):
    program_content = get_file_content_as_single_string(program_file)
    aProgram = parse_pou_content(program_content)

    reports = [[v0, v1, v2.replace("\n", "<br>")] for [v0, v1, v2] in (aProgram.check_rules())]

    variable_info = aProgram.getVarDataColumns(
        "name", "paramType", "valueType", "initVal", "description"
    )
    backward_trace = aProgram.getDependencyPathsByName()

    # Populate model instance object based on analysis
    model_instance = BlockModel.create(aProgram.progName,
                                       program_file,
                                       json.dumps(variable_info),
                                       json.dumps(backward_trace),
                                       project)

    # Finally, save the analysed model instance to DB
    # We do this first to generate the primary key value
    # As this is needed for the report generation step
    model_instance.save()
    # Create ReportModel objects for each report
    # Note: model_instance.id is the primary key for the model
    for (ruleName, verdict, explanation) in reports:
        (ReportModel.create(model_instance,
                            ruleName,
                            report_text=explanation,
                            checkPassed=verdict == "Pass")
         .save())
    # Compute the DRACONIS Core metrics
    metrics = aProgram.getMetrics()

    # Create Metrics objects for the core metrics
    (MetricsModel.create(model_instance, metrics, additional_metrics_json_str)
     .save())  # then save it

    # Finally, we create the SVG model
    SVG_content, width, height = renderToReport(aProgram, scale=DEFAULT_RENDER_SCALE)
    SVGModel.create(model_instance, SVG_content, width, height).save()

    return aProgram, model_instance.id



def make_and_save_program_model_instance(_form, additional_metrics_form):
    model_instance = _form.save(commit=False)
    metrics_instance = additional_metrics_form.save(commit=False)

    aProgram, backward_trace, reports, variable_info, model = analyse_model(model_instance)

    # save the analysed model instance to DB
    model.save()

    # Create ReportModel objects for each report
    for (ruleName, verdict, explanation) in reports:
        (ReportModel.create(model_instance,
                            ruleName,
                            report_text=explanation,
                            checkPassed=verdict == "Pass")
         .save())
    # Compute the DRACONIS Core metrics
    metrics = aProgram.getMetrics()

    # Add any additional metrics computed
    the_additional_metrics = metrics_instance.additional_metrics
    # Create Metrics objects for the core metrics
    (MetricsModel.create(model_instance, metrics, metrics_instance.additional_metrics)
     .save())  # then save it

    SVG_content, width, height = renderToReport(aProgram, scale=DEFAULT_RENDER_SCALE)
    SVGModel.create(model_instance, SVG_content, width, height).save()
    variable_info = [replace_fst_with_snd(replace_fst_with_snd(vList, "UNINIT", ""),
                                          None, "") for vList in variable_info]
    metrics_info = metrics.copy()
    metrics_explained = aProgram.getMetricsExplanations()
    for k, v in metrics_info.items():
        metrics_info[k] = (v, metrics_explained.get(k, "").replace("\n", "<br>"))
    report_data = {
        "pou_progName": aProgram.progName,
        "rule_reports": reports,
        "metrics": metrics_info,
        "additional_metrics": the_additional_metrics,
        "backward_trace": backward_trace,
        "variable_info": variable_info,
    }
    return aProgram, report_data, model_instance.id


def analyse_model(model_instance):
    program_content = get_file_content_as_single_string(model_instance.program_content)
    aProgram, backward_trace, reports, variable_info = analyse(program_content)
    # Populate model instance object based on analysis
    model_instance.program_name = aProgram.progName
    model_instance.program_variables = json.dumps(variable_info)
    model_instance.variable_dependencies = json.dumps(backward_trace)
    return aProgram, backward_trace, reports, variable_info, model_instance


def analyse(program_content):
    aProgram = parse_pou_content(program_content)
    reports = [[v0, v1, v2.replace("\n", "<br>")] for [v0, v1, v2] in (aProgram.check_rules())]
    variable_info = aProgram.getVarDataColumns(
        "name", "paramType", "valueType", "initVal", "description"
    )
    backward_trace = aProgram.getDependencyPathsByName()
    return aProgram, backward_trace, reports, variable_info


def get_file_content_as_single_string(file_field: FieldFile):
    return "\n".join([str(s, "UTF-8") for s in file_field.readlines()])


def replace_fst_with_snd(collection, fst, snd):
    def replace_if_matches(v, replace_this, with_this):
        if v == replace_this:
            return with_this
        else:
            return v

    return [replace_if_matches(e, fst, snd) for e in collection]


def make_excel_report(model: BlockModel, metrics: MetricsModel, reports: List[ReportModel]):
    import xlsxwriter as xls
    # Create report file
    output = io.BytesIO()
    workbook = xls.Workbook(output,
                            {
                                'in_memory': True,
                                'strings_to_numbers': True})
    metrics_sheet = workbook.add_worksheet("Metrics")
    core_metrics = metrics.core_metrics
    additional_metrics = json.loads(metrics.additional_metrics)
    metrics_sheet.write(0, 0, model.program_name)

    # Header is row 0, hence start at one
    row = 1
    for k, v in core_metrics.items():
        metrics_sheet.write(row, 0, k)

        metrics_sheet.write(row, 1, v)
        row += 1

    for k, v in additional_metrics.items():
        metrics_sheet.write(row, 0, k)
        metrics_sheet.write(row, 1, v)
        row += 1
    report_sheet = workbook.add_worksheet("Reports")
    header_strs = ["Check ID", "Content", "Status",
                   "Review Notes", "Review Status", "Justifications"]
    for i, s in enumerate(header_strs):
        report_sheet.write(0, i, s)

    row = 1
    for rep in reports:
        for i, v in enumerate(rep.get_stringified_fields()):
            report_sheet.write(row, i, v)

        row += 1
    IMAGE_OFFSET_FROM_REPORT_END = 2
    fpp_dir = tempfile.gettempdir()
    fpp = os.path.join(fpp_dir, "report_img.jpg")
    #try:
    theProgram = parse_pou_content(get_file_content_as_single_string(model.program_content))
    result_path = generate_image_of_program(theProgram,
                                            img_result_path=fpp,
                                            scale=5.0)
    print("Got past image generation")
    print(result_path)
    report_sheet.insert_image(row=row+IMAGE_OFFSET_FROM_REPORT_END,
                              col=0,
                              filename=result_path)

    #except Exception as e:
        # Image generation was not successful
        #print(e)
        #print(e.args)

    metrics_sheet.autofit()
    report_sheet.autofit()

    workbook.close()
    output.seek(0)
    filename = f"{model.program_name}_Report.xlsx"
    return output, filename
