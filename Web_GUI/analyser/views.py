import http
import io
import itertools
import json
import logging
import os.path
import sys

from django.forms import formset_factory
from django.http import Http404, HttpResponseBadRequest, HttpResponse, FileResponse
from django.shortcuts import render, get_object_or_404, get_list_or_404
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.datastructures import MultiValueDict
from django.views.decorators.csrf import csrf_exempt

from .forms import BlockModelForm, MetricsModelForm
from .models import BlockModel, ReportModel, MetricsModel, DiffModel, SVGModel, ProjectModel
from .utility_functions import renderToReport, make_and_save_diff_image, make_and_save_program_model_instance, \
    get_file_content_as_single_string, make_excel_report, from_model_content_create_and_add_model_in_db

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
                                                             render_scale=renderScale,
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
                                         (renderToReport(prog1, renderScale),
                                          renderToReport(prog2, renderScale)),
                                         new_diff.diff_picture))

            return render(request, "analyser/diff_result.html",
                          context=diffData)
    else:
        return HttpResponseBadRequest("Only accepts POST requests")


def start_page(request):
    return render(request, "analyser/index.html")


@csrf_exempt
def append_metrics(request, model_id):
    if request.method == "POST":
        additional_metrics = request.FILES.get("additional_metrics", None)
        if model_id is None or additional_metrics is None:
            resp = HttpResponseBadRequest()
            resp.content = "Both model id and additional metrics file needs to be provided"
            return resp

        target_metrics_model = get_object_or_404(MetricsModel, block_program=model_id)
        new_metrics = json.load(additional_metrics)

        # add any metrics that do not already exist
        # If they are different, assume newer is better => overwrite all
        for metrics_id, metrics_value in new_metrics.items():
            target_metrics_model.additional_metrics[metrics_id] = metrics_value

        target_metrics_model.save()
        return HttpResponse(content=f"<p>New Metrics added to model {model_id})</p>",
                            status=200)
    else:
        return HttpResponseBadRequest("Only accepts POST requests")


@csrf_exempt
def batch_page(request):
    """
    The view/entrypoint used for serving programmatically uploaded files
    """
    if request.method != "POST":
        return HttpResponseBadRequest()
    # Check if user has provided the files
    the_program_file = request.FILES.get("program_file_path", None)
    the_metrics_file = request.FILES.get("metrics_file_path", None)

    project_name = request.POST.get("project_name", None)
    project_model = ProjectModel.objects.filter(project_name=project_name)
    if not project_model:
        # Project does not exist, we create it
        project_model = ProjectModel.create(project_name).save()
    else:
        project_model = get_object_or_404(ProjectModel, project_name=project_name)
    if the_program_file is not None:
        files = MultiValueDict()
        files.setlist('program_content', [the_program_file])

        # But the metrics file is optional, otherwise defaults to an empty dict
        if the_metrics_file is not None:
            files.setlist('additional_metrics', [the_metrics_file])

        else:
            metrics_file_mem = InMemoryUploadedFile(io.BytesIO("{}".encode(encoding="utf-8")),
                                                    'file', "___metric_empty___.json",
                                                    None, len("{}"), None)
            files.setlist('additional_metrics', [metrics_file_mem])

        additional_metrics_json = get_file_content_as_single_string(files.getlist('additional_metrics')[0])
        program, prog_model_id = from_model_content_create_and_add_model_in_db(the_program_file,
                                                                               additional_metrics_json, project_model)
        return HttpResponse(f"<p>Models are uploaded and analysed</p>",
                            status=http.HTTPStatus.OK)

    return HttpResponseBadRequest()


def model_upload_page(request):
    if request.GET.get("dark", None) is not None:
        pageData = {"darkMode": True}
    else:
        pageData = dict()
    if request.method == "POST":
        modelform = BlockModelForm(request.POST, request.FILES, prefix="model")
        metricsform = MetricsModelForm(request.POST, request.FILES, prefix="metrics")

        if all([modelform.is_valid(), metricsform.is_valid()]):
            program, reportData, _model_instance = make_and_save_program_model_instance(modelform, metricsform)
            for k, v in reportData.items():
                pageData[k] = v
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
    REVIEWS_CLEAR_NAME = "clear_reviews"

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


            def clear_reviews(report_id):
                the_report = get_object_or_404(ReportModel, pk=report_id)
                the_report.report_review_status = ReportModel.ReportReviewStatus.UN_VIEWED
                the_report.report_review_notes = ""
                the_report.report_justification_notes = ""
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
            report_clear_click = post_data.get(REVIEWS_CLEAR_NAME)
            if report_clear_click:
                clear_reviews(report_id)

        def handle_actions(post_data):
            if post_data.get("Download", None) is not None:
                model = get_object_or_404(BlockModel, pk=model_id)
                the_metrics = get_object_or_404(MetricsModel, block_program=model_id)
                the_reports = get_list_or_404(ReportModel, block_program_id=model_id)

                report_file, file_name = make_excel_report(model, the_metrics, the_reports)
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
    metrics = get_object_or_404(MetricsModel, block_program=model_id)
    mapper = ReportModel.ReportReviewStatus.get_value_to_label_map()
    report_status_pairs = [(rep, mapper.get(rep.report_review_status))
                           for rep in reports]

    context = {"model": model_inst, "reports": report_status_pairs,
               # Some constants to reduce code duplication between template and logic
               "REPORT_ID_NAME": REPORT_ID_NAME,
               "JUSTIFICATION_NAME": JUSTIFICATION_NAME,
               "NOTE_NAME": NOTE_NAME,
               "FALSE_POSITIVE_NAME": FALSE_POSITIVE_NAME,
               "REVIEWS_CLEAR_NAME": REVIEWS_CLEAR_NAME,
               "Variables": json.loads(model_inst.program_variables),
               "Dependencies": json.loads(model_inst.variable_dependencies),
               "metrics": metrics.core_metrics,
               "additional_metrics": metrics.additional_metrics}
    SVG = SVGModel.objects.filter(block_program=model_id)
    if len(SVG) == 0:
        # Legacy - no SVG exists for model
        # Some error handling should exist in the render template
        program_content = get_file_content_as_single_string(model_inst.program_content)
        aProgram = parse_pou_content(program_content)
        SVG_content, width, height = renderToReport(aProgram, scale=7.0)
        SVGModel.create(model_inst, SVG_content, width, height).save()
        pass
    else:
        assert len(SVG) == 1
        context["modelSVG"] = (SVG[0].svg_content,
                               SVG[0].svg_width, SVG[0].svg_height)
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


def show_models(request, models, project_name=None):
    context_data = {"models": models}
    if project_name is not None:
        context_data["project"] = project_name
    return render(request, "analyser/model_listview.html", context_data)


def models_page(request):
    models = BlockModel.objects.all()
    return show_models(request, models, project_name=None)


def projects_page(request):
    projects = ProjectModel.objects.all()
    context_data = {"projects": projects}
    return render(request, "analyser/projects_listview.html", context_data)


def single_project_page(request, project_id):
    project = get_object_or_404(ProjectModel, id=project_id)
    models = get_list_or_404(BlockModel, project=project_id)
    return show_models(request, models, project.project_name)


def metrics_page(request):
    all_models = BlockModel.objects.all()
    all_metrics = [m.core_metrics for m in MetricsModel.objects.all()]
    total_nr_of_models = len(all_models)
    total_nr_potentially_impure_blocks = len([m for m in all_metrics if m["IsPotentiallyImpure"]])
    metrics_total = {
        "total_amount_impure_FBDs": total_nr_potentially_impure_blocks
    }
    for metrics in all_metrics:
        for k, v in metrics.items():
            thetype = type(v)
            if type(v) is int:
                metrics_total[k] = metrics_total.get(k, 0) + v
    return render(request, "analyser/metrics_view.html", {"metrics": metrics_total})


def dashboard_page(request):
    all_reports = ReportModel.objects.all()
    # Get all reports, divide them into check name, and then whether they passed or failed.
    check_names = set()
    for rep in all_reports:
        check_names.add(rep.check_name)

    report_label_map = ReportModel.ReportReviewStatus.get_label_to_value_map()
    REVIEW_STATUS_UNVIEWED  = report_label_map["Unviewed"]
    REVIEW_STATUS_REVIEWED  = report_label_map["Reviewed"]
    REVIEW_STATUS_CONFIRMED = report_label_map["Confirmed"]
    REVIEW_STATUS_FALSEPOS = report_label_map["False Positive"]
    REVIEW_STATUS_JUSTIFIED = report_label_map["Justified"]

    check_status = {"reports": {}}
    for name in check_names:
        theReps = ReportModel.objects.filter(check_name=name)
        checks_failed = len(list(filter(lambda e: e.report_check_status == 0, theReps)))
        checks_passed = len(list(filter(lambda e: e.report_check_status == 1, theReps)))
        checks_unreviewed = len(list(filter(lambda e: e.report_review_status == REVIEW_STATUS_UNVIEWED, theReps)))
        checks_reviewed = len(list(filter(lambda e: e.report_review_status == REVIEW_STATUS_REVIEWED, theReps)))
        checks_confirmed = len(list(filter(lambda e: e.report_review_status == REVIEW_STATUS_CONFIRMED, theReps)))
        checks_false_positive = len(list(filter(lambda e: e.report_review_status == REVIEW_STATUS_FALSEPOS, theReps)))
        checks_justified = len(list(filter(lambda e: e.report_review_status == REVIEW_STATUS_JUSTIFIED, theReps)))
        check_status["reports"][name] = (checks_passed, checks_failed,
                                         checks_unreviewed, checks_reviewed, checks_confirmed,
                                         checks_false_positive,
                                         checks_justified)
    return render(request, "analyser/dashboard.html", check_status)
