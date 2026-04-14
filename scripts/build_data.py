"""
build_data.py — Interactive resume data builder.

Reads the user's existing resume (PDF or DOCX), extracts the content using
Ollama (mistral:7b), then walks the user through confirming and correcting
each section. Outputs a ready-to-use data.json.

Usage:
    python scripts/build_data.py                  # guided Q&A only
    python scripts/build_data.py resume.pdf       # AI-assisted from file
    python scripts/build_data.py resume.docx      # AI-assisted from file

Requirements:
    pip install requests pdfplumber python-docx
    Ollama + mistral:7b for AI mode:
        https://ollama.com  →  ollama pull mistral:7b
"""

import json
import re
import sys
from pathlib import Path

ROOT        = Path(__file__).parent.parent
OUTPUT_PATH = ROOT / "resume" / "data.json"
TEMPLATE    = ROOT / "resume" / "data.template.json"
OLLAMA_URL  = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "mistral:7b"

SEP = "\n" + "─" * 60 + "\n"


# ── HELPERS ───────────────────────────────────────────────────────────────────

def ask(prompt: str, default: str = "") -> str:
    hint = f" [{default}]" if default else ""
    val = input(f"{prompt}{hint}: ").strip()
    return val if val else default


def ask_yn(prompt: str, default: bool = True) -> bool:
    hint = "Y/n" if default else "y/N"
    val = input(f"{prompt} ({hint}): ").strip().lower()
    if not val:
        return default
    return val.startswith("y")


def ollama_running() -> bool:
    try:
        import requests
        requests.get("http://localhost:11434", timeout=2)
        return True
    except Exception:
        return False


def ask_ollama(prompt: str) -> str:
    import requests
    resp = requests.post(OLLAMA_URL, json={
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }, timeout=120)
    return resp.json()["response"].strip()


def extract_text_pdf(path: Path) -> str:
    import pdfplumber
    with pdfplumber.open(path) as pdf:
        return "\n".join(
            p.extract_text() for p in pdf.pages if p.extract_text()
        )


def extract_text_docx(path: Path) -> str:
    import docx
    doc = docx.Document(path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_text_pdf(path)
    if suffix in (".docx", ".doc"):
        return extract_text_docx(path)
    raise ValueError(f"Unsupported file type: {suffix}")


# ── AI EXTRACTION ─────────────────────────────────────────────────────────────

EXTRACT_PROMPT = """You are a resume parser. Extract structured information from the resume text below.
Return ONLY valid JSON matching this exact schema — no explanation, no markdown, just the JSON object.

Schema:
{{
  "name_full": "FULL NAME IN UPPERCASE",
  "name_short": "First Last",
  "subtitle": "Job Title or Degree (e.g. Software Engineering Student)",
  "role": "Short tagline for a visual resume header",
  "tagline": "One punchy sentence about what you do",
  "phone": "phone number",
  "email": "email",
  "linkedin_handle": "handle only (no https://)",
  "linkedin_url": "full LinkedIn URL",
  "github_handle": "github.com/username",
  "github_url": "full GitHub URL",
  "location": "City, Country",
  "profile": "2-4 sentence professional summary",
  "skills": [
    {{"category": "Languages & Scripting", "color": "blue", "items": ["Skill1", "Skill2"]}},
    {{"category": "Cloud & DevOps", "color": "teal", "items": ["Skill1"]}},
    {{"category": "APIs & Automation", "color": "grape", "items": ["Skill1"]}},
    {{"category": "Tools", "color": "slate", "items": ["Tool1"]}}
  ],
  "languages": [
    {{"name": "English", "level": "Full Professional", "dots": 5}}
  ],
  "certifications": [
    {{"name": "Cert Name", "sub": "Issuing Body", "status": "done"}}
  ],
  "projects": [
    {{
      "title": "Project Name",
      "badge_label": "",
      "badge_style": "",
      "date": "Mon YYYY - Present",
      "location": "City, Country",
      "url": "",
      "url_label": "",
      "bullets": ["bullet 1", "bullet 2"]
    }}
  ],
  "experience": [
    {{
      "title": "Job Title",
      "org": "Company",
      "date": "Mon YYYY - Mon YYYY",
      "location": "City, Country",
      "bullets": ["bullet 1", "bullet 2"]
    }}
  ],
  "education": [
    {{
      "degree": "Degree — Major",
      "org": "University",
      "date": "Mon YYYY - Mon YYYY",
      "location": "City, Country",
      "note": "GPA, scholarship, relevant awards"
    }}
  ]
}}

RESUME TEXT:
{resume_text}
"""


def ai_extract(resume_text: str) -> dict:
    print("Sending to Ollama (mistral:7b) for extraction — takes ~30 seconds...")
    prompt = EXTRACT_PROMPT.format(resume_text=resume_text[:4000])
    raw = ask_ollama(prompt)
    # Strip markdown code fences if present
    raw = re.sub(r"^```[a-z]*\n?", "", raw.strip())
    raw = re.sub(r"\n?```$", "", raw.strip())
    return json.loads(raw)


# ── INTERACTIVE REVIEW ────────────────────────────────────────────────────────

def review_section(title: str, current: str) -> str:
    print(f"\n{title}:")
    print(f"  {current}")
    if not ask_yn("  Looks good?"):
        return ask(f"  Enter correct value", default=current)
    return current


def review_list(title: str, items: list) -> list:
    print(f"\n{title}: {', '.join(items)}")
    if not ask_yn("  Looks good?"):
        raw = ask("  Enter comma-separated list", default=", ".join(items))
        return [i.strip() for i in raw.split(",") if i.strip()]
    return items


def review_entries(section_name: str, entries: list, fields: list) -> list:
    print(SEP)
    print(f"  {section_name.upper()} ({len(entries)} entries found)")
    result = []
    for i, entry in enumerate(entries):
        print(f"\n  Entry {i + 1}:")
        for field in fields:
            val = entry.get(field, "")
            if isinstance(val, list):
                entry[field] = review_list(f"    {field}", val)
            else:
                entry[field] = review_section(f"    {field}", str(val))
        result.append(entry)
        if i < len(entries) - 1:
            if not ask_yn("\n  Review next entry?"):
                result.extend(entries[i + 1:])
                break
    if ask_yn(f"\n  Add another {section_name[:-1]}?", default=False):
        new_entry = {}
        for field in fields:
            new_entry[field] = ask(f"    {field}", default="")
        result.append(new_entry)
    return result


# ── MANUAL BUILD ──────────────────────────────────────────────────────────────

def manual_build() -> dict:
    print(SEP)
    print("  PERSONAL DETAILS")
    name_full  = ask("Full legal name (UPPERCASE)").upper()
    name_short = ask("Short name (e.g. First Last)")
    subtitle   = ask("Title/role (e.g. Software Engineering Student)")
    role       = ask("Visual resume role tagline (e.g. CS Student · AWS DVA-C02)")
    tagline    = ask("One-liner: what you do and why it matters")
    phone      = ask("Phone")
    email      = ask("Email")
    linkedin   = ask("LinkedIn handle (without https://linkedin.com/in/)")
    github_u   = ask("GitHub username")
    location   = ask("Location (City, Country)")

    print(SEP)
    print("  PROFILE SUMMARY")
    profile = ask("2-4 sentence professional summary")

    print(SEP)
    print("  SKILLS  (press Enter to skip a category)")
    skill_cats = [
        ("Languages & Scripting", "blue"),
        ("Cloud & DevOps", "teal"),
        ("APIs & Automation", "grape"),
        ("Tools", "slate"),
    ]
    skills = []
    for cat, color in skill_cats:
        raw = ask(f"  {cat} (comma-separated)")
        if raw:
            items = [i.strip() for i in raw.split(",") if i.strip()]
            skills.append({"category": cat, "color": color, "items": items})

    print(SEP)
    print("  LANGUAGES")
    langs = []
    while True:
        lang_name = ask("  Language (or Enter to finish)")
        if not lang_name:
            break
        level = ask(f"  {lang_name} — proficiency level")
        dots  = int(ask(f"  {lang_name} — dots 1-5", default="5"))
        langs.append({"name": lang_name, "level": level, "dots": dots})

    print(SEP)
    print("  CERTIFICATIONS")
    certs = []
    while True:
        cert_name = ask("  Cert name (or Enter to finish)")
        if not cert_name:
            break
        sub    = ask(f"  {cert_name} — issuing body or description")
        status = "in_progress" if ask_yn(f"  {cert_name} — still in progress?", False) else "done"
        certs.append({"name": cert_name, "sub": sub, "status": status})

    print(SEP)
    print("  PROJECTS")
    projects = []
    while True:
        proj_title = ask("  Project title (or Enter to finish)")
        if not proj_title:
            break
        date     = ask("  Date (e.g. Jan 2025 – Present)")
        location_p = ask("  Location")
        url      = ask("  GitHub/project URL (or Enter to skip)")
        bullets  = []
        print("  Enter bullets (empty line to finish):")
        while True:
            b = input("    • ").strip()
            if not b:
                break
            bullets.append(b)
        projects.append({
            "title": proj_title, "badge_label": "", "badge_style": "",
            "date": date, "location": location_p,
            "url": url, "url_label": url.replace("https://", "") if url else "",
            "bullets": bullets,
        })

    print(SEP)
    print("  EXPERIENCE")
    experience = []
    while True:
        job_title = ask("  Job/role title (or Enter to finish)")
        if not job_title:
            break
        org      = ask("  Organisation")
        date     = ask("  Date (e.g. Jan 2023 – Dec 2024)")
        location_e = ask("  Location")
        bullets  = []
        print("  Enter bullets (empty line to finish):")
        while True:
            b = input("    • ").strip()
            if not b:
                break
            bullets.append(b)
        experience.append({
            "title": job_title, "org": org,
            "date": date, "location": location_e, "bullets": bullets,
        })

    print(SEP)
    print("  EDUCATION")
    education = []
    while True:
        degree = ask("  Degree (or Enter to finish)")
        if not degree:
            break
        org    = ask("  University/institution")
        date   = ask("  Date (e.g. Jan 2026 – Dec 2028)")
        loc    = ask("  Location")
        note   = ask("  Note (GPA, scholarship, awards)")
        education.append({
            "degree": degree, "org": org,
            "date": date, "location": loc, "note": note,
        })

    return {
        "header": {
            "name_full": name_full, "name_short": name_short,
            "role": role, "tagline": tagline, "subtitle": subtitle,
        },
        "contact": {
            "phone": phone, "email": email,
            "linkedin_handle": linkedin,
            "linkedin_url": f"https://linkedin.com/in/{linkedin}",
            "github_handle": f"github.com/{github_u}",
            "github_url": f"https://github.com/{github_u}",
            "location": location,
        },
        "profile": profile,
        "skills": skills,
        "languages": langs,
        "certifications": certs,
        "projects": projects,
        "experience": experience,
        "education": education,
    }


# ── AI REVIEW FLOW ────────────────────────────────────────────────────────────

def review_extracted(data: dict) -> dict:
    print(SEP)
    print("  REVIEW EXTRACTED DATA\n")
    print("  Go through each section and correct anything that looks wrong.\n")

    h = data["header"]
    c = data["contact"]

    h["name_full"]  = review_section("Full name",   h.get("name_full", ""))
    h["name_short"] = review_section("Short name",  h.get("name_short", ""))
    h["subtitle"]   = review_section("Subtitle",    h.get("subtitle", ""))
    h["role"]       = review_section("Role tagline",h.get("role", ""))
    h["tagline"]    = review_section("One-liner",   h.get("tagline", ""))

    c["phone"]    = review_section("Phone",    c.get("phone", ""))
    c["email"]    = review_section("Email",    c.get("email", ""))
    c["location"] = review_section("Location", c.get("location", ""))

    linkedin = review_section("LinkedIn handle", c.get("linkedin_handle", ""))
    c["linkedin_handle"] = linkedin
    c["linkedin_url"]    = f"https://linkedin.com/in/{linkedin}"

    github_h = review_section("GitHub handle (username only)", c.get("github_handle", "").replace("github.com/", ""))
    c["github_handle"] = f"github.com/{github_h}"
    c["github_url"]    = f"https://github.com/{github_h}"

    data["profile"] = review_section("Profile summary", data.get("profile", ""))

    print(SEP)
    print("  SKILLS")
    for cat in data.get("skills", []):
        cat["items"] = review_list(f"  {cat['category']}", cat["items"])

    data["projects"]   = review_entries("Projects",   data.get("projects", []),   ["title", "date", "location", "url", "bullets"])
    data["experience"] = review_entries("Experience", data.get("experience", []), ["title", "org", "date", "location", "bullets"])
    data["education"]  = review_entries("Education",  data.get("education", []),  ["degree", "org", "date", "location", "note"])

    data["header"]  = h
    data["contact"] = c
    return data


# ── ASSEMBLE FINAL JSON ───────────────────────────────────────────────────────

def assemble(raw: dict) -> dict:
    """Map flat extracted dict into the final data.json schema."""
    if "header" in raw:
        return raw  # already structured (from review_extracted)
    return {
        "header": {
            "name_full":  raw.get("name_full", ""),
            "name_short": raw.get("name_short", ""),
            "role":       raw.get("role", ""),
            "tagline":    raw.get("tagline", ""),
            "subtitle":   raw.get("subtitle", ""),
        },
        "contact": {
            "phone":           raw.get("phone", ""),
            "email":           raw.get("email", ""),
            "linkedin_handle": raw.get("linkedin_handle", ""),
            "linkedin_url":    raw.get("linkedin_url", ""),
            "github_handle":   raw.get("github_handle", ""),
            "github_url":      raw.get("github_url", ""),
            "location":        raw.get("location", ""),
        },
        "profile":        raw.get("profile", ""),
        "skills":         raw.get("skills", []),
        "languages":      raw.get("languages", []),
        "certifications": raw.get("certifications", []),
        "projects":       raw.get("projects", []),
        "experience":     raw.get("experience", []),
        "education":      raw.get("education", []),
    }


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "═" * 60)
    print("  RESUME DATA BUILDER")
    print("  Powered by Ollama mistral:7b  |  resume-pipeline")
    print("═" * 60)

    resume_file = Path(sys.argv[1]) if len(sys.argv) > 1 else None

    if resume_file:
        if not resume_file.exists():
            print(f"ERROR: File not found: {resume_file}")
            sys.exit(1)

        if not ollama_running():
            print("\nWARNING: Ollama is not running.")
            print("  To use AI extraction: install Ollama and run 'ollama pull mistral:7b'")
            print("  Falling back to manual Q&A...\n")
            data = manual_build()
        else:
            print(f"\nExtracting text from: {resume_file.name}")
            resume_text = extract_text(resume_file)
            print(f"  Extracted {len(resume_text)} characters.")
            extracted = ai_extract(resume_text)
            structured = assemble(extracted)
            data = review_extracted(structured)
    else:
        if ollama_running():
            print("\nOllama is running. You can also pass your resume file for AI extraction:")
            print("  python scripts/build_data.py your_resume.pdf\n")
        data = manual_build()

    print(SEP)
    print("  Saving to resume/data.json...")
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  Saved: {OUTPUT_PATH}")
    print("\n  Next step: python scripts/compile_resume.py")
    print("═" * 60 + "\n")


if __name__ == "__main__":
    main()
