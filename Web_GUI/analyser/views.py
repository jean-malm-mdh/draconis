import os.path

from django.core.files.uploadedfile import UploadedFile
from django.shortcuts import render
from parser.helper_functions import parse_pou_file
# Create your views here.
from django import forms

from Web_GUI.parser.AST.path import PathDivide


class UploadFileForm(forms.Form):
    file = forms.FileField()
ANALYSER_DATA_STORE_PATH="/Users/jmm01/Documents/SmartDelta/safeprogparser/Web_GUI/analyser/DATASTORE"
def save_file_to_django_space(upload_file:UploadedFile):
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
            reports = program.check_rules()
            metrics = program.getMetrics()
            variable_info = program.getVarDataColumns("name", "varType", "valueType", "initVal", "description")
            backward_trace = {}
            for name, paths in program.getBackwardTrace().items():
                backward_trace[name] = [program.behaviour_id_map[e[-1]].expr.expr for e in PathDivide.unpack_pathlist([paths])]
            print(backward_trace)
            return render(request, "pou_report.html", { "file_name": request.FILES["file"].name,
                                                        "pou_progName": program.progName,
                                                        "rule_reports": reports,
                                                        "metrics": metrics,
                                                        "backward_trace": backward_trace,
                                                        "variable_info": variable_info})
        else:
            return render(request, "home.html", {"form": form})
    else:
        form = UploadFileForm()
        return render(request, "home.html", {"form": form})