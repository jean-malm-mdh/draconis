import json
import os.path

from django.core.files.uploadedfile import UploadedFile
from django.db.models.fields.files import FieldFile
from django.shortcuts import render
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import os
import sys

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), "../.."))
from parser.helper_functions import parse_pou_file, parse_pou_content

# Create your views here.
from django import forms
from .forms import BlockModelForm
from .models import ReportModel
from AST import PathDivide
from parser.renderer import generate_image_of_program, render_program_to_svg

ANALYSER_DATA_STORE_PATH = os.path.abspath(os.path.dirname(__file__)) + "/static"


def get_file_content_as_single_string(file_field: FieldFile):
    return "\n".join([str(s, "UTF-8") for s in file_field.readlines()])


def make_and_save_program_model_instance(form):
    model_instance = form.save(commit=False)
    program_content = get_file_content_as_single_string(model_instance.program_content)
    program = parse_pou_content(program_content)
    reports = program.check_rules()
    metrics = program.getMetrics()
    variable_info = program.getVarDataColumns(
        "name", "paramType", "valueType", "initVal", "description"
    )
    backward_trace = {}
    for name, paths in program.getBackwardTrace().items():
        backward_trace[name] = [
            program.behaviour_id_map[e[-1]].expr.expr
            for e in PathDivide.unpack_pathlist([paths])
        ]
    # Populate model instance object based on analysis
    model_instance.program_name = program.progName
    model_instance.program_metrics = json.dumps(metrics)
    model_instance.program_variables = json.dumps(variable_info)
    model_instance.program_vardependencies = json.dumps(backward_trace)
    # Finally, save the analysed model instance to DB
    # We do this first to generate the primary key value
    # As this is needed for the report generation step
    model_instance.save()
    # Create ReportModel objects for each report
    # Note: model_instance.id is the primary key for the model
    for (ruleName, verdict, explanation) in reports:
        new_report = ReportModel.create(model_instance,
                                        ruleName,
                                        report_text=explanation,
                                        it_passed=verdict == "Passed")
        new_report.save()
    reportData = {
        "pou_progName": program.progName,
        "rule_reports": reports,
        "metrics": metrics,
        "backward_trace": backward_trace,
        "variable_info": variable_info,
    }
    return program, reportData


def home_page(request):
    if request.method == "POST":
        form = BlockModelForm(request.POST, request.FILES)
        if form.is_valid():
            program, reportData = make_and_save_program_model_instance(form)

            shouldRenderImage = True
            if shouldRenderImage:
                imageWidth, imageHeight, imageSVGString = render_program_to_svg(program, scale=7.0)
                reportData["ImageSVG"] = imageSVGString
                reportData["ImageDimension"] = (imageWidth, imageHeight)
            return render(request, "analyser/pou_report.html", reportData)
        else:
            return render(request, "analyser/home.html", {"form": form})
    else:
        form = BlockModelForm()
        return render(request, "analyser/home.html", {"form": form})
