from rest_framework import serializers
from .models import Company, JobPosting, Application
from docs_app.models import Resume, GeneratedDoc

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id','name','website']

class JobPostingSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)
    company_id = serializers.PrimaryKeyRelatedField(
        source='company', queryset=Company.objects.all(), write_only=True, required=False)
    company_name = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = JobPosting
        fields = ['id','company','company_id','company_name','title','location','seniority','url','jd_raw','jd_struct','created_at']

    def create(self, validated_data):
        request = self.context['request']
        company = validated_data.pop('company', None)
        company_name = validated_data.pop('company_name', None)
        if not company and company_name:
            company, _ = Company.objects.get_or_create(user=request.user, name=company_name)
        if not company:
            raise serializers.ValidationError("company_id or company_name is required")
        validated_data['company'] = company
        validated_data['user'] = request.user
        return super().create(validated_data)

class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ['id','job','stage','applied_at','next_action','next_action_due','notes']

class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ['id','label','file','parsed_text','created_at']

class GeneratedDocSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedDoc
        fields = ['id','job','kind','content_md','file','created_at']
