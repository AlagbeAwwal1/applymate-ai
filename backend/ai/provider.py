# backend/ai/provider.py
import os, re, json
from typing import Dict, Any
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

SENIORITY_ENUM = [
    "Intern/Co-op","Junior","Mid","Senior","Lead","Manager","Director","VP","C-level",""
]

SYSTEM_MSG = (
    "You are a precise extractor for job descriptions. "
    "Return ONLY the structured fields via the provided function. "
    "Rules:\n"
    "- title: exact role name (no dates like 'for Sept 2025').\n"
    "- company: company or org if stated (domain names like 'naptha.ai' are ok).\n"
    "- location: city/state/country if stated, otherwise 'Remote' if clearly remote, else empty.\n"
    "- seniority: one of "
    + ", ".join([repr(s) for s in SENIORITY_ENUM[:-1]])
    + " (or empty if unknown).\n"
    "- skills: concise deduped skill/tool/framework nouns (<=20).\n"
    "- must_haves: items explicitly required (e.g., 'required', 'must') (<=12).\n"
    "- nice_to_haves: items marked 'preferred'/'nice to have' (<=12).\n"
    "- summary: 1–2 sentences from the overview.\n"
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

def _ensure_shape(d: Dict[str, Any]) -> Dict[str, Any]:
    out = DEFAULT_JD.copy()
    if not isinstance(d, dict): return out
    out.update({k: d.get(k, out[k]) for k in out.keys()})
    # normalize types
    for k in ("skills","must_haves","nice_to_haves"):
        v = out.get(k, [])
        out[k] = [str(x).strip() for x in (v or []) if str(x).strip()]
    for k in ("title","company","location","seniority","summary"):
        out[k] = str(out.get(k,"") or "").strip()
    # cap lengths to keep UI snappy
    out["skills"] = out["skills"][:20]
    out["must_haves"] = out["must_haves"][:12]
    out["nice_to_haves"] = out["nice_to_haves"][:12]
    return out

def _openai_extract_strict(text: str) -> Dict[str, Any]:
    if not (settings.AI_PROVIDER == "openai" and settings.AI_API_KEY and OpenAI):
        raise RuntimeError("OpenAI not configured")
    client = OpenAI(api_key=settings.AI_API_KEY)

    messages = [
        {"role":"system","content": SYSTEM_MSG},
        {"role":"user","content": f"Extract fields from this JD:\n{text}"}
    ]

    resp = client.chat.completions.create(
        model=os.environ.get("OPENAI_MODEL","gpt-4o-mini"),
        messages=messages,
        tools=TOOLS,
        tool_choice={"type":"function","function":{"name":"set_jd"}},
        temperature=float(os.environ.get("AI_TEMPERATURE","0.1")),
        max_tokens=int(os.environ.get("AI_MAX_TOKENS","700")),
        timeout=int(os.environ.get("AI_TIMEOUT","12")),
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

def extract_jd(text: str) -> Dict[str, Any]:
    """Public API used by the view. AI-first; optional heuristic fallback."""
    strict_only = str(os.environ.get("AI_STRICT_ONLY","0")).lower() in ("1","true","yes")
    try:
        return _openai_extract_strict(text)
    except Exception as e:
        print("LLM extract failed:", e)
        if strict_only:
            # Pure AI mode: return empty shape with summary so UI isn't blank.
            d = DEFAULT_JD.copy()
            d["seniority"] = "Intern/Co-op" if re.search(r"\bintern|co-?op|student\b", text, re.I) else ""
            d["summary"] = (re.sub(r"\s+"," ", text).strip())[:600]
            return d
        # If you kept your old heuristic extractor, fall back here:
        # return _heuristic_extract(text)
        # Otherwise:
        d = DEFAULT_JD.copy()
        d["summary"] = (re.sub(r"\s+"," ", text).strip())[:600]
        return d
