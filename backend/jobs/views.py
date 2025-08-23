# backend/jobs/views.py
import io
from datetime import datetime
from django.db.models import Q
from django.http import FileResponse, HttpResponse
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status
from .models import Company, JobPosting, Application
from .serializers import CompanySerializer, JobPostingSerializer, ApplicationSerializer, ResumeSerializer, GeneratedDocSerializer
from docs_app.models import Resume, GeneratedDoc
from utils.resume_parse import extract_text_from_file
from utils.docx_export import markdown_to_docx
from utils.ics_utils import simple_ics
from ai import provider as ai_provider
from django.conf import settings
import requests
from bs4 import BeautifulSoup
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from rest_framework.decorators import api_view, parser_classes, permission_classes,authentication_classes
from rest_framework.permissions import AllowAny


@api_view(['GET'])
@permission_classes([AllowAny])
def health(_request):
    ...
    return Response({'ok': True, 'time': datetime.utcnow().isoformat()})


@api_view(['GET'])
def health(_request):
    return Response({'ok': True, 'time': datetime.utcnow().isoformat()})


@api_view(['GET', 'POST'])
def job_list_create(request):
    if request.method == 'GET':
        q = request.query_params.get('q', '').strip()
        qs = JobPosting.objects.select_related(
            'company').order_by('-created_at')
        if q:
            qs = qs.filter(Q(title__icontains=q) |
                           Q(company__name__icontains=q))
        data = JobPostingSerializer(qs, many=True).data
        return Response(data)
    else:
        serializer = JobPostingSerializer(data=request.data)
        if serializer.is_valid():
            job = serializer.save()
            return Response(JobPostingSerializer(job).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
def job_detail(request, pk: int):
    try:
        job = JobPosting.objects.get(pk=pk)
    except JobPosting.DoesNotExist:
        return Response({'detail': 'Not found'}, status=404)

    if request.method == 'GET':
        return Response(JobPostingSerializer(job).data)
    elif request.method == 'PATCH':
        ser = JobPostingSerializer(job, data=request.data, partial=True)
        if ser.is_valid():
            ser.save()
            return Response(ser.data)
        return Response(ser.errors, status=400)
    else:
        job.delete()
        return Response(status=204)


def _fetch_text_from_url(url: str) -> str:
    try:
        # ⬇️ user-agent helps with some sites
        headers = {'User-Agent': 'Mozilla/5.0 (ApplyMateAI)'}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        for tag in soup(['script', 'style', 'noscript', 'nav', 'header', 'footer']):
            tag.decompose()
        text = ' '.join(soup.get_text(separator=' ').split())
        return text[:15000]
    except Exception:
        return ""


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def extract_jd_view(request):  
    jd_text = request.data.get("jd_text", "")
    url = request.data.get("url")
    if url and not jd_text:
        jd_text = _fetch_text_from_url(url)
    if not jd_text:
        return Response({"detail": "Provide jd_text or url"}, status=400)
    # ⬇️ call the AI helper via the module alias
    jd_struct = ai_provider.extract_jd(jd_text)
    return Response(jd_struct)


@api_view(['GET', 'POST'])
def app_list_create(request):
    if request.method == 'GET':
        job_id = request.query_params.get('job_id')
        qs = Application.objects.all().order_by('-id')
        if job_id:
            qs = qs.filter(job_id=job_id)
        return Response(ApplicationSerializer(qs, many=True).data)
    else:
        ser = ApplicationSerializer(data=request.data)
        if ser.is_valid():
            app = ser.save()
            return Response(ApplicationSerializer(app).data, status=201)
        return Response(ser.errors, status=400)


@api_view(['GET', 'PATCH', 'DELETE'])
def app_detail(request, pk: int):
    try:
        app = Application.objects.get(pk=pk)
    except Application.DoesNotExist:
        return Response({'detail': 'Not found'}, status=404)

    if request.method == 'GET':
        return Response(ApplicationSerializer(app).data)
    elif request.method == 'PATCH':
        ser = ApplicationSerializer(app, data=request.data, partial=True)
        if ser.is_valid():
            app = ser.save()
            return Response(ApplicationSerializer(app).data)
        return Response(ser.errors, status=400)
    else:
        app.delete()
        return Response(status=204)


@api_view(['POST'])
def fit_score(request):
    job_id = request.data.get('job_id')
    resume_id = request.data.get('resume_id')
    if not job_id or not resume_id:
        return Response({'detail': 'job_id and resume_id required'}, status=400)
    try:
        job = JobPosting.objects.get(pk=job_id)
        resume = Resume.objects.get(pk=resume_id)
    except (JobPosting.DoesNotExist, Resume.DoesNotExist):
        return Response({'detail': 'Not found'}, status=404)

    jd = job.jd_struct or {}
    rtxt = (resume.parsed_text or "").lower()

    must = {s.lower() for s in (jd.get('must_haves') or [])}
    nice = {s.lower() for s in (jd.get('nice_to_haves') or [])}
    other = {s.lower() for s in (jd.get('skills') or [])}
    all_sk = must | nice | other

    match = sorted({s for s in all_sk if s in rtxt})
    miss_must = sorted(list(must - set(match)))
    miss_nice = sorted(list(nice - set(match)))
    miss_other = sorted(
        list((other - set(match)) - set(miss_must) - set(miss_nice)))
    gaps = miss_must + miss_nice + miss_other

    # Weighted score: must-have=2, nice-to-have=1, others=1
    total_pts = 2*len(must) + 1*len(nice) + 1*len(other - must - nice)
    hit_pts = 2*len(set(match) & must) + 1*len(set(match) &
                                               nice) + 1*len(set(match) & (other - must - nice))
    score = int(round(100 * (hit_pts / max(1, total_pts))))
    score = max(5, min(100, score))

    # Advice (LLM or heuristic)
    from ai import provider as ai_provider
    advice = ai_provider.suggest_resume_patches(jd, resume.parsed_text or "")

    # Also produce a short human-readable checklist
    recommendations = []
    if miss_must:
        recommendations.append(
            "Add concrete bullets for must-haves: " + ", ".join(miss_must[:6]) + ".")
    if miss_nice:
        recommendations.append(
            "Weave in preferred skills where relevant: " + ", ".join(miss_nice[:6]) + ".")

    return Response({
        "score": score,
        "match": match,
        "gaps": gaps,
        "recommendations": recommendations,
        "advice": advice,   # <--- new: {keywords_to_add, bullets, summary}
    })


@api_view(['POST'])
def generate_doc(request):
    kind = request.data.get('type', 'bullets')
    job_id = request.data.get('job_id')
    resume_id = request.data.get('resume_id')
    export = bool(request.data.get('export', False))

    if not job_id:
        return Response({'detail': 'job_id is required'}, status=400)
    try:
        job = JobPosting.objects.get(pk=job_id)
    except JobPosting.DoesNotExist:
        return Response({'detail': 'Job not found'}, status=404)

    resume_text = ""
    if resume_id:
        try:
            resume = Resume.objects.get(pk=resume_id)
            resume_text = resume.parsed_text or ""
        except Resume.DoesNotExist:
            pass

    # ⬇️ call via alias
    if kind == 'coverletter':
        content_md = ai_provider.generate_cover_letter(
            job.jd_struct or {}, resume_text)
        title = f"Cover Letter - {job.title} at {job.company.name}"
    else:
        content_md = ai_provider.generate_bullets(
            job.jd_struct or {}, resume_text)
        title = f"Resume Bullets - {job.title} at {job.company.name}"

    gen = GeneratedDoc.objects.create(
        job=job, kind=kind, content_md=content_md)

    file_url = None
    if export:
        doc = markdown_to_docx(content_md, title=title)
        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        filename = f"{kind}-{job.id}-{int(datetime.utcnow().timestamp())}.docx"
        path = default_storage.save(
            f"generated/{filename}", ContentFile(buf.read()))
        gen.file.name = path
        gen.save()
        file_url = settings.MEDIA_URL + path

    data = {'id': gen.id, 'kind': gen.kind, 'content_md': gen.content_md,
            'file': gen.file.url if gen.file else None, 'file_url': file_url}
    return Response(data)


@api_view(['GET', 'POST'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def resume_list_create(request):
    if request.method == 'GET':
        qs = Resume.objects.order_by('-created_at')
        return Response(ResumeSerializer(qs, many=True).data)
    else:
        label = request.data.get('label', 'Base Resume')
        f = request.FILES.get('file')
        if not f:
            return Response({'detail': 'file is required'}, status=400)
        resume = Resume.objects.create(label=label, file=f)
        resume.parsed_text = extract_text_from_file(resume.file.path)
        resume.save()
        return Response(ResumeSerializer(resume).data, status=201)


@api_view(['GET', 'POST'])
def job_list_create(request):
    if request.method == 'GET':
        q = request.query_params.get('q', '').strip()
        qs = JobPosting.objects.select_related('company').filter(
            user=request.user).order_by('-created_at')
        if q:
            qs = qs.filter(Q(title__icontains=q) |
                           Q(company__name__icontains=q))
        return Response(JobPostingSerializer(qs, many=True).data)
    else:
        serializer = JobPostingSerializer(
            data=request.data, context={'request': request})
        if serializer.is_valid():
            job = serializer.save()
            return Response(JobPostingSerializer(job).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
def app_list_create(request):
    if request.method == 'GET':
        job_id = request.query_params.get('job_id')
        qs = Application.objects.filter(job__user=request.user).order_by('-id')
        if job_id:
            qs = qs.filter(job_id=job_id)
        return Response(ApplicationSerializer(qs, many=True).data)
    else:
        # ensure the job belongs to the user
        job_id = request.data.get("job")
        if not JobPosting.objects.filter(id=job_id, user=request.user).exists():
            return Response({'detail': 'Forbidden'}, status=403)
        ser = ApplicationSerializer(data=request.data)
        if ser.is_valid():
            app = ser.save()
            return Response(ApplicationSerializer(app).data, status=201)
        return Response(ser.errors, status=400)


@api_view(['GET', 'POST'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def resume_list_create(request):
    if request.method == 'GET':
        qs = Resume.objects.filter(user=request.user).order_by('-created_at')
        return Response(ResumeSerializer(qs, many=True).data)
    else:
        label = request.data.get('label', 'Base Resume')
        f = request.FILES.get('file')
        if not f:
            return Response({'detail': 'file is required'}, status=400)
        resume = Resume.objects.create(user=request.user, label=label, file=f)
        resume.parsed_text = extract_text_from_file(resume.file.path)
        resume.save()
        return Response(ResumeSerializer(resume).data, status=201)
@api_view(['POST'])
def generate_doc(request):
    ...
    try:
        job = JobPosting.objects.get(pk=job_id, user=request.user)
    except JobPosting.DoesNotExist:
        return Response({'detail':'Job not found'}, status=404)
    ...
    gen = GeneratedDoc.objects.create(user=request.user, job=job, kind=kind, content_md=content_md)
    ...
