from django.contrib import admin

# Register your models here.
from .models import BlockModel, ProjectModel
admin.site.register(BlockModel)
admin.site.register(ProjectModel)