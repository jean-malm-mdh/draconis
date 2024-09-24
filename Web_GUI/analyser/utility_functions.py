import json
import os
import subprocess
import tempfile
import sys

from django.db.models.fields.files import FieldFile

from .models import ReportModel, MetricsModel

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), "../.."))
from draconis_parser.renderer import render_program_to_svg, generate_image_of_program
from draconis_parser.helper_functions import parse_pou_content


def renderToReport(reportData, imageName, program, scale=None):
    _scale = scale or 7.0
    imageWidth, imageHeight, imageSVGString = render_program_to_svg(program, _scale)
    reportData[imageName] = imageSVGString
    reportData[imageName + "_Size"] = (imageWidth, imageHeight)


def getImageDiffAsSvg(program1, program2, storage_path: str, renderscale=5.0):
    fpp_dir = tempfile.gettempdir()
    fpp = os.path.join(fpp_dir, "prog1.jpg")
    fpp2 = os.path.join(fpp_dir, "prog2.jpg")
    fpp_diff = os.path.join(storage_path, "images", ".generated", "prog_diff.jpg")
    generate_image_of_program(program1, fpp, scale=renderscale, generate_report_in_image=False)
    generate_image_of_program(program2, fpp2, scale=renderscale, generate_report_in_image=False)
    try:
        runresult = subprocess.run(["magick", "compare", "-metric", "AE", "-fuzz", "15%", fpp, fpp2, fpp_diff],
                                   capture_output=True)
    except Exception as e:
        print(e)
        return None
    if runresult.returncode == 2:
        print(runresult.stderr)
        return None
    return "images/.generated/prog_diff.jpg"


def make_and_save_program_model_instance(_form, additional_metrics_form):
    model_instance = _form.save(commit=False)
    metrics_instance = additional_metrics_form.save(commit=False)

    program_content = get_file_content_as_single_string(model_instance.program_content)
    aProgram = parse_pou_content(program_content)

    reports = [[v0, v1, v2.replace("\n", "<br>")] for [v0, v1, v2] in (aProgram.check_rules())]

    variable_info = aProgram.getVarDataColumns(
        "name", "paramType", "valueType", "initVal", "description"
    )
    backward_trace = aProgram.getDependencyPathsByName()

    # Populate model instance object based on analysis
    model_instance.program_name = aProgram.progName
    model_instance.program_variables = json.dumps(variable_info)
    model_instance.variable_dependencies = json.dumps(backward_trace)

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
                            it_passed=verdict == "Pass")
         .save())
    # Compute the DRACONIS Core metrics
    metrics = aProgram.getMetrics()

    # Add any additional metrics computed
    additional_metrics = metrics_instance.additional_metrics
    the_additional_metrics = additional_metrics
    # Create Metrics objects for the core metrics
    (MetricsModel.create(model_instance, metrics, additional_metrics)
     .save())  # then save it

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
    return aProgram, report_data


def get_file_content_as_single_string(file_field: FieldFile):
    return "\n".join([str(s, "UTF-8") for s in file_field.readlines()])


def replace_fst_with_snd(collection, fst, snd):
    def replace_if_matches(v, replace_this, with_this):
        if v == replace_this:
            return with_this
        else:
            return v

    return [replace_if_matches(e, fst, snd) for e in collection]
