from django.db import models
from django.contrib.auth.models import User

class Resume(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="resumes" )
    label = models.CharField(max_length=120, default="Base Resume")
    file = models.FileField(upload_to="resumes/")
    parsed_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.label

class GeneratedDoc(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="generated_docs")
    KIND = [("bullets","Bullets"), ("coverletter","CoverLetter"), ("resume","Resume")]
    job = models.ForeignKey('jobs.JobPosting', on_delete=models.CASCADE, related_name="generated_docs")
    kind = models.CharField(max_length=20, choices=KIND)
    content_md = models.TextField()
    file = models.FileField(upload_to="generated/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.kind} for {self.job}"
