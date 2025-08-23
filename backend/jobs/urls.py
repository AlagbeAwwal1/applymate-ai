# backend/jobs/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("health/", views.health),

    path("jobs/", views.job_list_create),
    path("jobs/<int:pk>/", views.job_detail),
    path("jobs/extract/", views.extract_jd_view),  

    path("apps/", views.app_list_create),
    path("apps/<int:pk>/", views.app_detail),

    path("fit/score/", views.fit_score),
    path("docs/generate/", views.generate_doc),

    path("resume/", views.resume_list_create),
]
