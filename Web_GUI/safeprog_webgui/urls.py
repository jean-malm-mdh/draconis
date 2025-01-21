"""
URL configuration for safeprog_webgui project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from analyser import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.start_page, name="DRACONIS-Start-Page"),
    path("upload/", views.model_upload_page, name="Model-Upload"),
    path("diff/", views.diff_page, name="diff"),
    path("models/", views.models_page, name="Models"),
    path("dev/false-positives/", views.false_positive_page, name="False-Positive-Reports"),
    path("<int:model_id>/report", views.reports_page, name="report"),
    path("<int:model_id>/append_metrics", views.append_metrics, name="Metrics-Append"),
    path("batch", views.batch_page, name="Batch-Upload"),
    path("projects/", views.projects_page, name="Projects"),
    path("projects/<int:project_id>", views.single_project_page, name="Single-Project"),
    path("metrics/", views.metrics_page, name="Metrics")

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
