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


def start_page(request):
    return render(request, "analyser/index.html")

def model_upload_page(request):
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
    FALSE_POSITIVE_NAME = "false_positive"



    def handle_post_requests():
        data = request.POST

        # Helper function to update the report based on the provided field and status
        def update_report(report_id, text, field_name, status):
            if text is not None:
                the_report = get_object_or_404(ReportModel, pk=report_id)
                current_notes = getattr(the_report, field_name)
                updated_notes = "\n".join([current_notes, text]).strip()
                setattr(the_report, field_name, updated_notes)
                the_report.report_review_status = status
                the_report.save()

        # Retrieve report ID once, as it's used for all updates
        report_id = data.get(REPORT_ID_NAME)

        # Handle justification
        justification_text = data.get(JUSTIFICATION_NAME)
        update_report(report_id, justification_text, 'report_justification_notes',
                      ReportModel.ReportReviewStatus.JUSTIFIED)

        # Handle review notes
        note_text = data.get(NOTE_NAME)
        update_report(report_id, note_text, 'report_review_notes', ReportModel.ReportReviewStatus.REVIEWED)

        # Handle false positive
        false_positive_text = data.get(FALSE_POSITIVE_NAME)
        update_report(report_id, false_positive_text, 'report_review_notes',
                      ReportModel.ReportReviewStatus.FALSE_POSITIVE)

    if request.method == "POST":
        handle_post_requests()
    model_inst = get_object_or_404(BlockModel, pk=model_id)
    reports = get_list_or_404(ReportModel, block_program_id=model_id)
    mapper = ReportModel.ReportReviewStatus.get_value_to_label_map()
    report_status_pairs = [(rep, mapper.get(rep.report_review_status))
                           for rep in reports]
    context = {"model": model_inst, "reports": report_status_pairs,
               # Some constants to reduce code duplication between template and logic
               "REPORT_ID_NAME": REPORT_ID_NAME,
               "JUSTIFICATION_NAME": JUSTIFICATION_NAME,
               "NOTE_NAME": NOTE_NAME,
               "FALSE_POSITIVE_NAME": FALSE_POSITIVE_NAME,}
    return render(request, "analyser/modelreport.html",
                  context)

def false_positive_page(request):
    def handle_post_response():
        # Make a summary of the false positives
        ##
        # Send report to Admin
        pass
    if request.method == "POST":
        handle_post_response()
    reports = get_list_or_404(ReportModel, report_review_status=ReportModel.ReportReviewStatus.FALSE_POSITIVE)
    report_model_pairs = [(rep, rep.block_program) for rep in reports]
    return render(request, "analyser/falsepositives.html", {"report_models": report_model_pairs})

def models_page(request):
    models = BlockModel.objects.all()
    return render(request, "analyser/model_listview.html", {"models": models})
