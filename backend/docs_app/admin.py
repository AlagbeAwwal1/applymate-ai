from django.contrib import admin
from .models import Resume, GeneratedDoc

@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('id','label','file','created_at')

@admin.register(GeneratedDoc)
class GeneratedDocAdmin(admin.ModelAdmin):
    list_display = ('id','job','kind','file','created_at')
