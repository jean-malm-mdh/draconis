from django.db import models


# Create your models here.
class BlockModel(models.Model):
    program_name = models.TextField(blank=False)
    program_content = models.FileField(upload_to="DATASTORE/")
    uploaded_at = models.DateTimeField("Date uploaded", auto_now_add=True)
    program_variables = models.JSONField(verbose_name="Program Variables", blank=False)
    program_metrics = models.JSONField(verbose_name="Program Metrics", blank=False)
    program_vardependencies = models.JSONField("Dependency analysis", blank=False)
    # program_picture = models.ImageField()


class ReportModel(models.Model):
    class ReportStatus(models.IntegerChoices):
        UNVIEWED = 0
        UNDER_REVIEW = 1
        REVIEWED = 2

    block_program = models.ForeignKey(BlockModel, on_delete=models.CASCADE)
    check_name = models.TextField()
    check_verbose_name = models.TextField()
    report_content = models.TextField()
    report_status = models.IntegerField(choices=ReportStatus.choices)
