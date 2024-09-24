from django.db import models


# Create your models here.
class BlockModel(models.Model):
    program_name = models.TextField(blank=False)
    program_content = models.FileField(upload_to="DATASTORE/")
    uploaded_at = models.DateTimeField("Date uploaded", auto_now_add=True)
    program_variables = models.JSONField(verbose_name="Program Variables", blank=False)
    variable_dependencies = models.JSONField("Dependency analysis", blank=False)

class MetricsModel(models.Model):
    block_program = models.ForeignKey(BlockModel, on_delete=models.CASCADE)
    core_metrics = models.JSONField(verbose_name="Program Metrics", blank=False)
    additional_metrics = models.FileField(upload_to="DATASTORE/")

    @classmethod
    def create(cls, program_id, core_metrics_json, additional_metrics=None):
        metrics = cls(block_program=program_id, core_metrics=core_metrics_json, additional_metrics=additional_metrics)
        return metrics


class ReportModel(models.Model):
    class ReportReviewStatus(models.IntegerChoices):
        UNVIEWED = 0
        REVIEWED = 1
        CONFIRMED = 2
        FALSE_POSITIVE = 3

    class CheckStatus(models.IntegerChoices):
        FAIL = 0
        PASS = 1

    block_program = models.ForeignKey(BlockModel, on_delete=models.CASCADE)
    check_name = models.TextField()
    check_verbose_name = models.TextField()
    report_content = models.TextField()
    report_check_status = models.IntegerField(choices=CheckStatus.choices, default=CheckStatus.FAIL)
    report_review_status = models.IntegerField(choices=ReportReviewStatus.choices, default=ReportReviewStatus.UNVIEWED)
    report_review_notes = models.TextField(default="")

    @classmethod
    def create(cls, program_id, check_name, report_text, it_passed=False):
        report = cls(block_program=program_id,
                     check_name=check_name,
                     check_verbose_name=check_name,
                     report_content=report_text,
                     report_check_status=int(it_passed),
                     report_review_notes="")
        return report
