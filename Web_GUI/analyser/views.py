import os.path
import sys

from django.forms import formset_factory
from django.http import Http404
from django.shortcuts import render, get_object_or_404, get_list_or_404

from .forms import BlockModelForm, MetricsModelForm
from .models import BlockModel, ReportModel, MetricsModel
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
    REPORT_ID_NAME = "report_id"
    JUSTIFICATION_NAME = "justification"
    NOTE_NAME = "made_note"
    def handle_post_requests():
        data = request.POST
        justification_text = data.get(JUSTIFICATION_NAME)
        if justification_text is not None:
            # It is a justification
            # The post request should contain the report ID
            report_id = data.get(REPORT_ID_NAME)
            the_report = get_object_or_404(ReportModel, pk=report_id)
            the_report.report_justification_notes = ("\n".join([the_report.report_justification_notes, justification_text])).strip()
            the_report.report_review_status = ReportModel.ReportReviewStatus.JUSTIFIED
            the_report.save()
        note_text = data.get(NOTE_NAME)
        if note_text is not None:
            report_id = data.get(REPORT_ID_NAME)
            the_report = get_object_or_404(ReportModel, pk=report_id)
            the_report.report_review_notes = ("\n".join([the_report.report_review_notes, note_text])).strip()
            the_report.report_review_status = ReportModel.ReportReviewStatus.REVIEWED
            the_report.save()


    if request.method == "POST":
        handle_post_requests()
    model_inst = get_object_or_404(BlockModel, pk=model_id)
    reports = get_list_or_404(ReportModel, block_program_id=model_id)
    context = {"model": model_inst, "reports": reports,
               # Some constants to reduce code duplication between template and logic
               "REPORT_ID_NAME": REPORT_ID_NAME,
               "JUSTIFICATION_NAME": JUSTIFICATION_NAME,
               "NOTE_NAME": NOTE_NAME}
    return render(request, "analyser/modelreport.html",
                  context)


def models_page(request):
    models = BlockModel.objects.all()
    return render(request, "analyser/model_listview.html", {"models": models})
