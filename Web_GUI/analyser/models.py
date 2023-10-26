from django.db import models

# Create your models here.
class BlockModel(models.Model):
    program_name = models.TextField(blank=False)
    program_content = models.FileField(upload_to="DATASTORE/")
    uploaded_at = models.DateTimeField("Date uploaded", auto_now_add=True)
    program_picture = models.ImageField()

class ReportModel(models.Model):
    block_program = models.ForeignKey(BlockModel, on_delete=models.CASCADE)
    check_name = models.TextField()
    check_verbose_name = models.TextField()
    report_content = models.TextField()