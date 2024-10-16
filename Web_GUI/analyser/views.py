import itertools
import os.path
import sys
from wsgiref.util import FileWrapper

from django.forms import formset_factory
from django.http import Http404, HttpResponseBadRequest, HttpResponse, FileResponse
from django.shortcuts import render, get_object_or_404, get_list_or_404

from .forms import BlockModelForm, MetricsModelForm
from .models import BlockModel, ReportModel, MetricsModel, DiffModel
from .utility_functions import renderToReport, make_and_save_diff_image, make_and_save_program_model_instance, \
    get_file_content_as_single_string, make_excel_report

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
        selected_models = request.POST.getlist("diff_selections[]")
        renderScale = 5.0
        if selected_models is not None:
            fileHandles = [get_object_or_404(BlockModel, pk=int(ID)) for ID in selected_models]
            programs = dict(
                (f.id, parse_pou_content(get_file_content_as_single_string(f.program_content))) for f in fileHandles)
            all_pairs = itertools.combinations(fileHandles, 2)
            diffData["data"] = []
            for p1, p2 in all_pairs:
                new_diff = None
                # TODO: The lookup should be symmetric. For now we don't care
                diff_entry = DiffModel.objects.filter(prog1=p1, prog2=p2)
                prog1 = programs.get(p1.pk)
                prog2 = programs.get(p2.pk)
                if len(diff_entry) == 0:
                    # No diff has been done between these two program instances
                    # Generate diff, then save in DB
                    delta_report = "\n".join(prog1.compute_delta(prog2)).replace("\n", "<br>")

                    diff_img_path = make_and_save_diff_image(prog1, prog2, ANALYSER_DATA_STORE_PATH,
                                                             renderscale=renderScale,
                                                             name_postfix=f"_{p1.pk}_{p2.pk}")
                    new_diff = DiffModel.create(
                        p1, p2, delta_report, diff_img_path
                    )
                    new_diff.save()
                else:
                    assert len(diff_entry) == 1
                    new_diff = diff_entry[0]
                assert isinstance(new_diff, DiffModel)

                diffData["data"].append((new_diff.diff_report_infotext,
                                         (renderToReport("ImageSVG_" + str(p1.pk), prog1, renderScale),
                                          renderToReport("ImageSVG_" + str(p2.pk), prog2, renderScale)),
                                         new_diff.diff_picture))

            return render(request, "analyser/diff_result.html",
                          context=diffData)
    else:
        return HttpResponseBadRequest("Only accepts POST requests")


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

        def handle_review_update(post_data):
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
            report_id = post_data.get(REPORT_ID_NAME)
            # Handle justification
            justification_text = post_data.get(JUSTIFICATION_NAME)
            update_report(report_id, justification_text, 'report_justification_notes',
                          ReportModel.ReportReviewStatus.JUSTIFIED)
            # Handle review notes
            note_text = post_data.get(NOTE_NAME)
            update_report(report_id, note_text, 'report_review_notes', ReportModel.ReportReviewStatus.REVIEWED)
            # Handle false positive
            false_positive_text = post_data.get(FALSE_POSITIVE_NAME)
            update_report(report_id, false_positive_text, 'report_review_notes',
                          ReportModel.ReportReviewStatus.FALSE_POSITIVE)

        def handle_actions(post_data):
            if post_data.get("Download", None) is not None:
                model = get_object_or_404(BlockModel, pk=model_id)
                metrics = get_object_or_404(MetricsModel, block_program=model_id)
                the_reports = get_list_or_404(ReportModel, block_program_id=model_id)

                report_file, file_name = make_excel_report(model, metrics, the_reports)
                response = FileResponse(report_file,
                                        as_attachment=True,
                                        filename=file_name)
                return response

            return None

        handle_review_update(data)
        return handle_actions(data)

    if request.method == "POST":
        resp = handle_post_requests()
        if resp is not None:
            # Handle response
            return resp
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
               "FALSE_POSITIVE_NAME": FALSE_POSITIVE_NAME, }
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
