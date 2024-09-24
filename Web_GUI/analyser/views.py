import os.path
import sys

from django.forms import formset_factory
from django.http import Http404
from django.shortcuts import render

from .forms import BlockModelForm, MetricsModelForm
from .models import BlockModel
from .utility_functions import renderToReport, getImageDiffAsSvg, make_and_save_program_model_instance, \
    get_file_content_as_single_string

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), "../.."))
from draconis_parser.helper_functions import parse_pou_content

ANALYSER_DATA_STORE_PATH = os.path.abspath(os.path.dirname(__file__)) + "/static"

BlockModelFormset_Differ = formset_factory(BlockModelForm, min_num=2, max_num=2, absolute_max=4, can_delete_extra=True)


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
        diffpath = getImageDiffAsSvg(programs[0], programs[1], ANALYSER_DATA_STORE_PATH, renderscale=renderScale)
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

    if request.method == "POST":
        modelform = BlockModelForm(request.POST, request.FILES, prefix="model")
        metricsform = MetricsModelForm(request.POST, request.FILES, prefix="metrics")
        if all([modelform.is_valid(), metricsform.is_valid()]):
            program, reportData = make_and_save_program_model_instance(modelform, metricsform)
            for k, v in reportData.items():
                pageData[k] = v
            shouldRenderImage = True
            if shouldRenderImage:
                renderToReport(pageData, "ImageSVG", program)
            return render(request, "analyser/pou_report.html", pageData)
        else:
            pageData["modelForm"] = modelform
            pageData["metricsForm"] = metricsform
        return render(request, "analyser/home.html", pageData)
    else:
        pageData["modelForm"] = BlockModelForm(prefix="model")
        pageData["metricsForm"] = MetricsModelForm(prefix="metrics")
        return render(request, "analyser/home.html", pageData)

def reports_page(request, model_id):
    try:
        model_inst = BlockModel.objects.get(pk=model_id)
    except BlockModel.DoesNotExist:
        raise Http404("The requested Model does not exist")
    return render(request, "analyser/modelreport.html", {"model": model_inst})