from django.contrib import admin
from .models import Company, JobPosting, Application

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('id','name','website')

@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ('id','title','company','location','seniority','url','created_at')
    search_fields = ('title','company__name')

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('id','job','stage','applied_at','next_action','next_action_due')
    list_filter = ('stage',)
