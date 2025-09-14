# backend/ai/provider.py
import os, re, json
from typing import Dict, Any, List, Tuple
from django.conf import settings

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

# default empty shape so the frontend always has fields
DEFAULT_JD: Dict[str, Any] = {
    "title": "", "company": "", "location": "", "seniority": "",
    "skills": [], "must_haves": [], "nice_to_haves": [], "summary": ""
}

SENIORITY_INTERN = "Intern/Co-op"
DEFAULT_TITLE = "Software Engineer"
SENIORITY_ENUM = [
    SENIORITY_INTERN,"Junior","Mid","Senior","Lead","Manager","Director","VP","C-level",""
]

SYSTEM_MSG = (
    "You are a precise extractor for job descriptions.\n"
    "Respond ONLY by calling the provided function with strictly structured fields.\n\n"
    "Extraction rules:\n"
    "- title: infer the most likely job title from the description when not explicit (e.g., 'Software Engineering Intern', 'Frontend Engineer'). Use concise, standard role names; no dates or qualifiers.\n"
    "- company: company or org if stated (domain names like 'acme.ai' are ok).\n"
    "- location: city/state/country if stated; if clearly remote, return 'Remote'; else empty.\n"
    "- seniority: one of " + ", ".join([repr(s) for s in SENIORITY_ENUM[:-1]]) + " (or empty).\n"
    "- skills: concise, deduped nouns for skills/tools/languages/frameworks (e.g., 'Python', 'React'). No duties, no soft skills unless explicitly named (e.g., 'Agile' ok). Max 20.\n"
    "- must_haves: ONLY items explicitly required (look for 'required', 'must', 'minimum', 'at least', 'need to have', 'we require').\n"
    "  Include concrete skills, certifications, years with a skill (e.g., '3+ years Python'), degrees if explicit, and work eligibility if stated. Max 12.\n"
    "- nice_to_haves: ONLY items marked as preferred/bonus (look for 'preferred', 'nice to have', 'bonus', 'plus'). Max 12.\n"
    "- Do NOT include responsibilities/duties, company benefits, culture statements, or generic fluff in any list.\n"
    "- Normalize items by removing trailing punctuation, parentheticals that are examples, and version numbers unless critical (e.g., 'Python 3.10' -> 'Python').\n"
    "- Deduplicate across lists; if an item appears in both, keep in 'must_haves' and omit from others.\n"
    "- summary: 1–2 sentences capturing the opportunity and focus.\n"
)

TOOLS = [{
    "type": "function",
    "function": {
        "name": "set_jd",
        "description": "Return the extracted job fields as structured JSON.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type":"string"},
                "company": {"type":"string"},
                "location": {"type":"string"},
                "seniority": {"type":"string", "enum": SENIORITY_ENUM},
                "skills": {"type":"array","items":{"type":"string"}},
                "must_haves": {"type":"array","items":{"type":"string"}},
                "nice_to_haves": {"type":"array","items":{"type":"string"}},
                "summary": {"type":"string"}
            },
            "required": ["title","company","location","seniority","skills","must_haves","nice_to_haves","summary"],
            "additionalProperties": False
        }
    }
}]

_SKILL_WORDS = [
    # languages / runtimes
    "python","javascript","typescript","java","c++","c#","go","rust","ruby","php",
    # web / frameworks
    "react","react native","node","express","django","flask","fastapi","next.js","vue","angular",
    # data / infra
    "sql","postgres","mysql","mongodb","redis","kafka","spark","hadoop",
    # devops
    "aws","gcp","azure","docker","kubernetes","git","linux","ci/cd","terraform",
]

_REQ_CUES = re.compile(r"\b(must|required|minimum|min\.?|at least|need to have|we require|currently pursuing)\b", re.I)
_PREF_CUES = re.compile(r"\b(preferred|nice to have|bonus|plus|strongly preferred)\b", re.I)
_REMOTE_CUE = re.compile(r"\bremote\b", re.I)

def _ensure_shape(d: Dict[str, Any]) -> Dict[str, Any]:
    out = DEFAULT_JD.copy()
    if not isinstance(d, dict): return out
    out.update({k: d.get(k, out[k]) for k in out.keys()})
    # normalize types
    for k in ("skills","must_haves","nice_to_haves"):
        v = out.get(k, [])
        # basic normalization: strip, trim trailing punctuation, drop empties
        norm = []
        seen = set()
        for x in (v or []):
            s = re.sub(r"\s+[()\[\]{},;:]+$","", str(x or "").strip())
            s = re.sub(r"\s+"," ", s)
            if not s: continue
            if s.lower() in seen: continue
            seen.add(s.lower())
            norm.append(s)
        out[k] = norm
    for k in ("title","company","location","seniority","summary"):
        out[k] = str(out.get(k,"") or "").strip()
    # cap lengths to keep UI snappy
    out["skills"] = out["skills"][:20]
    # ensure no overlaps: priority to must_haves
    must = {s.lower() for s in out["must_haves"]}
    out["nice_to_haves"] = [s for s in out["nice_to_haves"] if s.lower() not in must]
    out["skills"] = [s for s in out["skills"] if s.lower() not in must]
    out["must_haves"] = out["must_haves"][:12]
    out["nice_to_haves"] = out["nice_to_haves"][:12]
    return out

def _split_lines(text: str) -> List[str]:
    raw_lines = [ln.strip(" \t•-*–—") for ln in (text or "").splitlines()]
    return [re.sub(r"\s+", " ", ln).strip() for ln in raw_lines if ln.strip()]

def _detect_sections(lines: List[str]) -> List[Tuple[str, List[str]]]:
    sections: List[Tuple[str, List[str]]] = []
    current_name, current_lines = "", []
    for ln in lines:
        if re.match(r"^(requirements?|qualifications?|what you[’']ll do|responsibilities|preferred|bonus|nice to have)s?\:?$", ln, re.I):
            if current_lines:
                sections.append((current_name, current_lines))
                current_lines = []
            current_name = ln.lower()
        else:
            current_lines.append(ln)
    if current_lines:
        sections.append((current_name, current_lines))
    return sections

def _collect_skills_from_line(line: str) -> List[str]:
    found = set()
    for w in _SKILL_WORDS:
        if re.search(rf"(?<![\w-]){re.escape(w)}(?![\w-])", line, re.I):
            found.add(w.title() if w.isalpha() else w)
    for m in re.findall(r"\b(AWS|GCP|Azure|SQL|GraphQL|REST|React(?: Native)?|Next\.js|Node\.js)\b", line, re.I):
        found.add(m if m.isupper() else m.title())
    return list(found)

def _classify_line(section_name: str, line: str) -> str:
    if re.search(r"preferred|bonus|nice to have", section_name or "", re.I) or _PREF_CUES.search(line):
        return "nice"
    if _REQ_CUES.search(line) or re.search(r"\b(experience|proficiency|knowledge)\b", line, re.I):
        return "must"
    return ""

def _is_requirement_line(line: str) -> bool:
    """Filter out headers, instructions, and non-requirement content."""
    line = line.strip()
    # Skip headers and section markers
    if re.match(r"^(qualifications?|requirements?|additional information|in your application|application questions?|submit|email|process)s?\:?\s*$", line, re.I):
        return False
    # Skip instruction lines
    if re.search(r"\b(include|answer|submit|email|forward|process|application)\b", line, re.I) and len(line) < 100:
        return False
    # Skip very short lines that are likely headers
    if len(line) < 20 and re.search(r"\:$", line):
        return False
    # Must be a substantial requirement statement
    return len(line) > 30 and not line.startswith(("http", "www."))

def _normalize_unique(items: List[str]) -> List[str]:
    norm, seen = [], set()
    for x in items:
        s = re.sub(r"\s+[()\[\]{},;:]+$", "", str(x or "").strip())
        s = re.sub(r"\s+", " ", s)
        k = s.lower()
        if not s or k in seen:
            continue
        seen.add(k)
        norm.append(s)
    return norm

def _guess_title(text: str) -> str:
    t = text.lower()
    if re.search(r"\bintern|co-?op\b", t):
        if re.search(r"front\s*end|react", t):
            return "Frontend Engineering Intern"
        if re.search(r"back\s*end|api|node|django|flask|fastapi", t):
            return "Backend Engineering Intern"
        if re.search(r"mobile|react native", t):
            return "Mobile Engineering Intern"
        if re.search(r"full[- ]?stack", t):
            return "Full Stack Engineering Intern"
        return "Software Engineering Intern"
    if re.search(r"full[- ]?stack", t):
        return "Full Stack Engineer"
    if re.search(r"front\s*end|react", t):
        return "Frontend Engineer"
    if re.search(r"back\s*end|api|node|django|flask|fastapi", t):
        return "Backend Engineer"
    if re.search(r"data\s+engineer|spark|hadoop", t):
        return "Data Engineer"
    if re.search(r"software\s+engineer|developer", t):
        return "Software Engineer"
    return ""

def _guess_company(text: str) -> str:
    # Try to capture a bare domain if present
    m = re.search(r"\b([a-z0-9-]+\.(?:ai|com|io|co|org|net))\b", text, re.I)
    if m:
        return m.group(1)
    # Look for patterns like 'at Acme' or 'join Acme'
    m = re.search(r"\b(?:at|join)\s+([A-Z][A-Za-z0-9&'\-]+)\b", text)
    if m:
        return m.group(1)
    return ""

def _deterministic_extract(text: str) -> Dict[str, Any]:
    t = str(text or "")
    out = DEFAULT_JD.copy()
    # seniority heuristic
    out["seniority"] = SENIORITY_INTERN if re.search(r"\bintern|co-?op|student\b", t, re.I) else ""
    out["location"] = "Remote" if _REMOTE_CUE.search(t) else ""
    out["title"] = _guess_title(t)
    out["company"] = _guess_company(text)
    # section-aware split
    lines = _split_lines(t)
    sections = _detect_sections(lines)

    must, nice, skills = _scan_blocks(sections if sections else [("", lines)])

    # if we have bullets but no cues, treat short bullet lines as must
    if not must and any(len(ln) < 140 for ln in lines):
        for ln in lines:
            if len(ln) <= 140:
                must.append(ln)

    # normalize lists
    out["must_haves"] = _normalize_unique(must)[:12]
    out["nice_to_haves"] = [s for s in _normalize_unique(nice) if s.lower() not in {m.lower() for m in out["must_haves"]}][:12]
    out["skills"] = [s for s in sorted({*skills}, key=lambda x: x.lower()) if s.lower() not in {m.lower() for m in out["must_haves"]}][:20]
    # fallback summary
    out["summary"] = (re.sub(r"\s+", " ", t).strip())[:600]
    return out

def _scan_blocks(blocks: List[Tuple[str, List[str]]]) -> Tuple[List[str], List[str], set]:
    must: List[str] = []
    nice: List[str] = []
    skills: set = set()
    for name, block in blocks:
        for ln in block:
            for s in _collect_skills_from_line(ln):
                skills.add(s)
            cls = _classify_line(name, ln)
            if cls == "nice" and _is_requirement_line(ln):
                nice.append(ln)
            elif cls == "must" and _is_requirement_line(ln):
                must.append(ln)
            # If no explicit classification but looks like a requirement, treat as must-have
            elif not cls and _is_requirement_line(ln) and re.search(r"\b(you|have|are|take|enjoy|love|passion|commitment)\b", ln, re.I):
                must.append(ln)
    return must, nice, skills

def _openai_extract_strict(text: str) -> Dict[str, Any]:
    if not (settings.AI_PROVIDER == "openai" and settings.AI_API_KEY and OpenAI):
        raise RuntimeError("OpenAI not configured")
    client = OpenAI(api_key=settings.AI_API_KEY)

    messages = [
        {"role":"system","content": SYSTEM_MSG},
        {"role":"user","content": (
            "Extract the fields from this job description. Infer a realistic job title based on responsibilities and technologies when an explicit title is not provided.\n"
            "Focus on explicit requirement cues for must_haves vs preferred cues for nice_to_haves.\n"
            "If a section header like 'Requirements', 'Qualifications', 'Preferred', 'Bonus' appears, use it to guide classification.\n\n"
            f"Job Description:\n{text}"
        )}
    ]

    resp = client.chat.completions.create(
        model=os.environ.get("OPENAI_MODEL","gpt-4o-mini"),
        messages=messages,
        tools=TOOLS,
        tool_choice={"type":"function","function":{"name":"set_jd"}},
        temperature=float(os.environ.get("AI_TEMPERATURE","0.0")),
        max_tokens=int(os.environ.get("AI_MAX_TOKENS","700")),
    )

    msg = resp.choices[0].message
    if not getattr(msg, "tool_calls", None):
        # Some models reply with plain JSON—try to parse it as a fallback
        content = (msg.content or "").strip()
        m = re.search(r"\{.*\}", content, re.S)
        if not m:
            raise RuntimeError("No tool call and no JSON in content")
        data = json.loads(m.group(0))
        return _ensure_shape(data)

    # Parse function call args (guaranteed JSON)
    args_str = msg.tool_calls[0].function.arguments
    data = json.loads(args_str)
    return _ensure_shape(data)

def _merge_ai_over_base(base: Dict[str, Any], ai: Dict[str, Any]) -> Dict[str, Any]:
    data = base.copy()
    for k in ("skills","must_haves","nice_to_haves"):
        if ai.get(k):
            data[k] = ai[k]
    for k in ("title","company","location","seniority","summary"):
        data[k] = ai.get(k) or data.get(k) or ""
    return data

def extract_jd(text: str) -> Dict[str, Any]:
    """Public API used by the view. AI-first; optional heuristic fallback."""
    strict_only = str(os.environ.get("AI_STRICT_ONLY","0")).lower() in ("1","true","yes")
    try:
        base = _deterministic_extract(text)
        data = base
        # try AI and merge if available
        try:
            ai = _openai_extract_strict(text)
            data = _merge_ai_over_base(base, ai)
        except Exception:
            pass
        if not (data.get("skills") or data.get("must_haves") or data.get("nice_to_haves")):
            data = base
        return data
    except Exception as e:
        print("LLM extract failed:", e)
        if strict_only:
            # Pure AI mode: return empty shape with summary so UI isn't blank.
            d = DEFAULT_JD.copy()
            d["seniority"] = SENIORITY_INTERN if re.search(r"\bintern|co-?op|student\b", text, re.I) else ""
            d["summary"] = (re.sub(r"\s+"," ", text).strip())[:600]
            return d
        # Deterministic fallback to extract requirements and skills
        return _deterministic_extract(text)

def suggest_resume_patches(jd_struct: Dict[str, Any], resume_text: str) -> Dict[str, Any]:
    """Generate resume improvement suggestions based on job requirements."""
    if not jd_struct or not resume_text:
        return {"keywords_to_add": [], "bullets": [], "summary": "No suggestions available"}
    
    must_haves = jd_struct.get("must_haves", [])
    nice_to_haves = jd_struct.get("nice_to_haves", [])
    skills = jd_struct.get("skills", [])
    
    # Simple heuristic-based suggestions
    resume_lower = resume_text.lower()
    missing_must = [item for item in must_haves if not any(word in resume_lower for word in item.lower().split() if len(word) > 3)]
    missing_nice = [item for item in nice_to_haves if not any(word in resume_lower for word in item.lower().split() if len(word) > 3)]
    missing_skills = [skill for skill in skills if skill.lower() not in resume_lower]
    
    # Generate bullet suggestions
    bullets = []
    if missing_must:
        bullets.append(f"Add experience with: {', '.join(missing_must[:3])}")
    if missing_skills:
        bullets.append(f"Highlight skills: {', '.join(missing_skills[:3])}")
    if missing_nice:
        bullets.append(f"Consider mentioning: {', '.join(missing_nice[:2])}")
    
    # Summary
    summary = "Focus on adding missing must-have requirements and highlighting relevant technical skills."
    if not missing_must and not missing_skills:
        summary = "Your resume already covers most requirements well. Consider emphasizing leadership or project impact."
    
    return {
        "keywords_to_add": missing_skills[:5],
        "bullets": bullets,
        "summary": summary
    }

def generate_bullets(jd_struct: Dict[str, Any], resume_text: str) -> str:
    """Generate tailored resume bullets based on job requirements."""
    if not jd_struct or not resume_text:
        return "No job requirements or resume text provided."
    
    must_haves = jd_struct.get("must_haves", [])
    skills = jd_struct.get("skills", [])
    title = jd_struct.get("title", DEFAULT_TITLE)
    
    # Extract key requirements
    key_skills = skills[:5] if skills else ["programming", "problem-solving"]
    key_requirements = must_haves[:3] if must_haves else ["technical skills", "collaboration"]
    
    # Generate tailored bullets
    bullets = [
        f"• Developed and maintained software applications using {', '.join(key_skills[:3])}",
        "• Collaborated with cross-functional teams to deliver high-quality solutions",
        f"• Demonstrated strong {key_requirements[0] if key_requirements else 'technical'} skills in previous projects"
    ]
    
    if len(key_skills) > 3:
        bullets.append(f"• Experience with {', '.join(key_skills[3:])} and related technologies")
    
    if "intern" in title.lower() or "co-op" in title.lower():
        bullets.append("• Eager to learn and contribute to innovative software development projects")
    
    return "\n".join(bullets)

def generate_cover_letter(jd_struct: Dict[str, Any], _resume_text: str) -> str:
    """Generate a cover letter based on job requirements."""
    if not jd_struct:
        return "No job information provided."
    
    title = jd_struct.get("title", DEFAULT_TITLE)
    company = jd_struct.get("company", "your company")
    must_haves = jd_struct.get("must_haves", [])
    skills = jd_struct.get("skills", [])
    
    # Extract key points
    key_skills = skills[:4] if skills else ["programming", "problem-solving", "collaboration"]
    key_requirements = must_haves[:2] if must_haves else ["technical skills"]
    
    cover_letter = f"""Dear Hiring Manager,

I am writing to express my strong interest in the {title} position at {company}. 

With experience in {', '.join(key_skills[:3])}, I am excited about the opportunity to contribute to your team. I have demonstrated {key_requirements[0] if key_requirements else 'strong technical skills'} and am passionate about creating innovative solutions.

I am particularly drawn to this role because it aligns with my interests in {', '.join(key_skills[:2])} and my desire to work on challenging projects. I believe my background and enthusiasm make me a strong candidate for this position.

Thank you for considering my application. I look forward to discussing how I can contribute to {company}'s success.

Best regards,
[Your Name]"""
    
    return cover_letter
