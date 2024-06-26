import json
import os.path
import shutil
import subprocess
import tempfile

from django.core.files.uploadedfile import UploadedFile
from django.db.models.fields.files import FieldFile
from django.forms import formset_factory
from django.shortcuts import render
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import os
import sys

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), "../.."))
from draconis_parser.helper_functions import parse_pou_file, parse_pou_content

from django import forms
from .forms import BlockModelForm
from .models import ReportModel
from AST import PathDivide
from draconis_parser.renderer import generate_image_of_program, render_program_to_svg

ANALYSER_DATA_STORE_PATH = os.path.abspath(os.path.dirname(__file__)) + "/static"


def get_file_content_as_single_string(file_field: FieldFile):
    return "\n".join([str(s, "UTF-8") for s in file_field.readlines()])


def replaceValWithVal(collection, valtoReplace, valToReplaceWith):
    def replaceifmatches(v, replacethis, withthis):
        if v == replacethis:
            return withthis
        else:
            return v

    return [replaceifmatches(e, valtoReplace, valToReplaceWith) for e in collection]


BlockModelFormset_Differ = formset_factory(BlockModelForm, min_num=2, max_num=2, absolute_max=4, can_delete_extra=True)


def renderToReport(reportData, imageName, program, scale=None):
    _scale = scale or 7.0
    imageWidth, imageHeight, imageSVGString = render_program_to_svg(program, _scale)
    reportData[imageName] = imageSVGString
    reportData[imageName + "_Size"] = (imageWidth, imageHeight)

def getImageDiffAsSvg(program1, program2, renderscale=5.0):
    fpp_dir = tempfile.gettempdir()
    fpp = os.path.join(fpp_dir, "prog1.jpg")
    fpp2 = os.path.join(fpp_dir, "prog2.jpg")
    fpp_diff = os.path.join(ANALYSER_DATA_STORE_PATH, "images", ".generated", "prog_diff.jpg")
    generate_image_of_program(program1, fpp, scale=renderscale, generate_report_in_image=False)
    generate_image_of_program(program2, fpp2, scale=renderscale, generate_report_in_image=False)
    print(fpp_dir)
    try:
        runresult = subprocess.run(["magick", "compare", "-metric", "AE", "-fuzz", "15%", fpp, fpp2, fpp_diff], capture_output=True)
    except Exception as e:
        print(e)
        return None
    if runresult.returncode == 2:
        print(runresult.stderr)
        return None
    return "images/.generated/prog_diff.jpg"



# Create your views here.
def diff_page(request):
    if request.GET.get("dark", None) is not None:
        diffData = {"darkMode": True}
    else:
        diffData = dict()

    if request.method == "POST":
        fileHandles = request.FILES.values()
        programs = [parse_pou_content(get_file_content_as_single_string(f)) for f in fileHandles]
        prog1 = programs[0]
        prog2 = programs[1]
        diffData["data"] = "\n".join(prog1.compute_delta(prog2)).replace("\n", "<br>")
        renderScale = 5.0
        renderToReport(diffData, "ImageSVG1", programs[0], renderScale)
        renderToReport(diffData, "ImageSVG2", programs[1], renderScale)
        diffpath = getImageDiffAsSvg(programs[0], programs[1], renderscale=renderScale)
        if diffpath:
            diffData["diffPath"] = diffpath
        return render(request, "analyser/diff_result.html",
                      context=diffData)

    else:
        # Create the formset
        diffData["modelFormSet"] = BlockModelFormset_Differ()
        return render(request, "analyser/diff.html", context=diffData)


def home_page(request):
    if request.GET.get("dark", None) is not None:
        pageData = {"darkMode": True}
    else:
        pageData = dict()

    def make_and_save_program_model_instance(_form):
        model_instance = _form.save(commit=False)
        program_content = get_file_content_as_single_string(model_instance.program_content)
        aProgram = parse_pou_content(program_content)
        reports = aProgram.check_rules()
        reports = [[v0, v1, v2.replace("\n", "<br>")] for [v0, v1, v2] in reports]
        metrics = aProgram.getMetrics()
        variable_info = aProgram.getVarDataColumns(
            "name", "paramType", "valueType", "initVal", "description"
        )
        backward_trace = aProgram.getDependencyPathsByName()
        # Populate model instance object based on analysis
        model_instance.program_name = aProgram.progName
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
        variable_info = [replaceValWithVal(replaceValWithVal(vList, "UNINIT", ""),
                                           None, "") for vList in variable_info]
        metrics_info = metrics.copy()
        metrics_explained = aProgram.getMetricsExplanations()
        for k, v in metrics_info.items():
            metrics_info[k] = (v, metrics_explained.get(k, "").replace("\n", "<br>"))
        report_data = {
            "pou_progName": aProgram.progName,
            "rule_reports": reports,
            "metrics": metrics_info,
            "backward_trace": backward_trace,
            "variable_info": variable_info,
        }
        return aProgram, report_data

    if request.method == "POST":
        form = BlockModelForm(request.POST, request.FILES)
        if form.is_valid():
            program, reportData = make_and_save_program_model_instance(form)
            for k, v in reportData.items():
                pageData[k] = v
            shouldRenderImage = True
            if shouldRenderImage:
                renderToReport(pageData, "ImageSVG", program)
            return render(request, "analyser/pou_report.html", pageData)
        else:
            pageData["form"] = form
        return render(request, "analyser/home.html", pageData)
    else:
        pageData["form"] = BlockModelForm()
        return render(request, "analyser/home.html", pageData)
