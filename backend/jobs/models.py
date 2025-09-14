from django.db import models
from django.contrib.auth.models import User

class Company(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="companies" )
    name = models.CharField(max_length=200)
    website = models.URLField(blank=True, null=True)
    def __str__(self): return self.name

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "name"], name="uniq_company_user_name")
        ]

class JobPosting(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="jobs" )
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='jobs')
    title = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True)
    seniority = models.CharField(max_length=50, blank=True)
    url = models.URLField(blank=True)
    jd_raw = models.TextField()
    jd_struct = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.title} @ {self.company.name}"

class Application(models.Model):
    STAGES = [
        ("saved","Saved"), ("applied","Applied"), ("oa","OA"),
        ("interview","Interview"), ("offer","Offer"), ("rejected","Rejected")
    ]
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applications')
    stage = models.CharField(max_length=20, choices=STAGES, default="saved")
    applied_at = models.DateField(blank=True, null=True)
    next_action = models.CharField(max_length=200, blank=True)
    next_action_due = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)
    def __str__(self): return f"{self.job} - {self.stage}"
