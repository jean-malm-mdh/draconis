import os.path

from django.core.files.uploadedfile import UploadedFile
from django.shortcuts import render
import os
import sys

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), "../.."))
from parser.helper_functions import parse_pou_file

# Create your views here.
from django import forms

from AST import PathDivide
from parser.renderer import generate_image_of_program


class UploadFileForm(forms.Form):
    file = forms.FileField()


ANALYSER_DATA_STORE_PATH = (
    "/Users/jmm01/Documents/SmartDelta/safeprogparser/Web_GUI/analyser/static"
)


def save_file_to_django_space(upload_file: UploadedFile):
    file_path_on_target = os.path.join(ANALYSER_DATA_STORE_PATH, upload_file.name)
    with open(file_path_on_target, "wb") as destination:
        for chunk in upload_file.chunks():
            destination.write(chunk)
    return file_path_on_target


def home_page(request):
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file_path = save_file_to_django_space(request.FILES["file"])
            program = parse_pou_file(file_path)
            generated_image_django_path = "images/.generated/tmp.png"
            image_file_path = os.path.join(ANALYSER_DATA_STORE_PATH, generated_image_django_path)
            generate_image_of_program(program, image_file_path, scale=7.0)
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

            reportData = {
                "file_name": request.FILES["file"].name,
                "pou_progName": program.progName,
                "rule_reports": reports,
                "metrics": metrics,
                "backward_trace": backward_trace,
                "variable_info": variable_info,
            }
            hasImageFile = os.path.exists(image_file_path)
            if hasImageFile:
                reportData["Image"] = generated_image_django_path
            return render(request, "pou_report.html", reportData)
        else:
            return render(request, "home.html", {"form": form})
    else:
        form = UploadFileForm()
        return render(request, "home.html", {"form": form})
