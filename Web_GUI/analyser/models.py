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
    additional_metrics = models.JSONField(verbose_name="External Metrics", blank=False, default=dict)

    @classmethod
    def create(cls, program_id, core_metrics_json, additional_metrics=None):
        metrics = cls(block_program=program_id, core_metrics=core_metrics_json, additional_metrics=additional_metrics)
        return metrics


class DiffModel(models.Model):
    prog1 = models.ForeignKey(BlockModel, on_delete=models.CASCADE, related_name="firstProg")
    prog2 = models.ForeignKey(BlockModel, on_delete=models.CASCADE, related_name="secondProg")

    diff_report_infotext = models.TextField(verbose_name="Diff Info")
    # The picture is in SVG format, so represent using text
    diff_picture = models.TextField(verbose_name="Diff Image")

    @classmethod
    def create(cls, prog1, prog2, report_info, diff_picture):
        return cls(prog1=prog1, prog2=prog2, diff_report_infotext=report_info, diff_picture=diff_picture)


class ReportModel(models.Model):
    class ReportReviewStatus(models.IntegerChoices):
        UN_VIEWED = 0, "Unviewed"
        REVIEWED = 1, "Reviewed"
        CONFIRMED = 2, "Confirmed"
        FALSE_POSITIVE = 3, "False Positive"
        JUSTIFIED = 4, "Justified"

        @classmethod
        def get_value_to_label_map(cls):
            """Returns a dictionary mapping values to their string representation."""
            return {status.value: status.label for status in cls}

        def __str__(self):
            return self.get_value_to_label_map()[self.value]

    class CheckStatus(models.IntegerChoices):
        FAIL = 0, "Fail"
        PASS = 1, "Pass"

        @classmethod
        def get_value_to_label_map(cls):
            """Returns a dictionary mapping values to their string representation."""
            return {status.value: status.label for status in cls}

        def __str__(self):
            return self.get_value_to_label_map()[self.value]

    block_program = models.ForeignKey(BlockModel, on_delete=models.CASCADE)
    check_name = models.TextField()
    report_content = models.TextField()
    report_check_status = models.IntegerField(choices=CheckStatus.choices, default=CheckStatus.FAIL)
    report_review_status = models.IntegerField(choices=ReportReviewStatus.choices, default=ReportReviewStatus.UN_VIEWED)
    report_review_notes = models.TextField(default="")
    report_justification_notes = models.TextField(default="")

    def __str__(self):
        return self.report_content


    def get_stringified_fields(self):
        return [
            self.check_name,
            self.report_content,
            ReportModel.CheckStatus.get_value_to_label_map()
            [int(self.report_check_status)],
            self.report_review_notes,
            ReportModel.ReportReviewStatus.get_value_to_label_map()
            [int(self.report_review_status)],
            self.report_justification_notes
        ]

    @classmethod
    def create(cls, program_id, check_name, report_text, it_passed=False):
        report = cls(block_program=program_id,
                     check_name=check_name,
                     report_content=report_text,
                     report_check_status=int(it_passed),
                     report_review_notes="")
        return report

