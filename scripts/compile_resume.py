"""
compile_resume.py — Inject data.json into both resume HTML templates.

Usage:
    python scripts/compile_resume.py

Reads:
    resume/data.json          — single source of truth for all content
    resume/resume.html        — ATS template (BUILD markers replaced)
    resume/resume_visual.html — visual template (BUILD markers replaced)

Each section between <!-- BUILD:X_START --> and <!-- BUILD:X_END --> is replaced
with freshly generated HTML from data.json. Everything else (CSS, layout) is untouched.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_PATH    = ROOT / "resume" / "data.json"
ATS_PATH     = ROOT / "resume" / "resume.html"
VISUAL_PATH  = ROOT / "resume" / "resume_visual.html"


def load_data() -> dict:
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def inject(html: str, marker: str, content: str) -> str:
    """Replace content between <!-- BUILD:MARKER_START --> and <!-- BUILD:MARKER_END -->."""
    pattern = rf"(<!-- BUILD:{marker}_START -->)(.*?)(<!-- BUILD:{marker}_END -->)"
    replacement = rf"\1\n{content}\n\3"
    result, count = re.subn(pattern, replacement, html, flags=re.DOTALL)
    if count == 0:
        print(f"  WARNING: BUILD:{marker} markers not found — skipped.")
    return result


# ── ATS BUILDERS ─────────────────────────────────────────────────────────────

def ats_header(d: dict) -> str:
    c = d["contact"]
    h = d["header"]
    linkedin_url   = c["linkedin_url"]
    linkedin_label = f'linkedin.com/in/{c["linkedin_handle"]}'
    github_url     = c["github_url"]
    github_label   = c["github_handle"]
    return (
        f'<h1>{h["name_full"]}</h1>\n'
        f'<p class="subtitle">{h["subtitle"]}</p>\n'
        f'<p class="contact">{c["location"]} &nbsp;|&nbsp; {c["phone"]} &nbsp;|&nbsp; '
        f'{c["email"]} &nbsp;|&nbsp; '
        f'<a href="{linkedin_url}">{linkedin_label}</a> &nbsp;|&nbsp; '
        f'<a href="{github_url}">{github_label}</a></p>'
    )


def ats_profile(d: dict) -> str:
    return f'<p>{d["profile"]}</p>'


def ats_skills(d: dict) -> str:
    all_items = []
    for cat in d["skills"]:
        all_items.extend(cat["items"])
    return "<p>" + " &nbsp;&middot;&nbsp; ".join(all_items) + "</p>"


def ats_certs(d: dict) -> str:
    lines = ["<ul>"]
    for c in d["certifications"]:
        status = " (In Progress)" if c["status"] == "in_progress" else ""
        lines.append(f'  <li>{c["name"]} &mdash; {c["sub"]}{status}</li>')
    lines.append("</ul>")
    return "\n".join(lines)


def ats_projects(d: dict) -> str:
    blocks = []
    for p in d["projects"]:
        bullets = "\n".join(f'    <li>{b}</li>' for b in p["bullets"])
        blocks.append(
            f'<div class="entry">\n'
            f'  <div class="entry-header">\n'
            f'    <span class="entry-title">{p["title"]}</span>\n'
            f'    <span class="entry-date">{p["date"]} &nbsp;|&nbsp; {p["location"]}</span>\n'
            f'  </div>\n'
            f'  <ul>\n{bullets}\n  </ul>\n'
            f'</div>'
        )
    return "\n\n".join(blocks)


def ats_experience(d: dict) -> str:
    blocks = []
    for e in d["experience"]:
        bullets = "\n".join(f'    <li>{b}</li>' for b in e["bullets"])
        org_line = f'  <p class="entry-sub">{e["org"]}</p>\n' if e.get("org") else ""
        blocks.append(
            f'<div class="entry">\n'
            f'  <div class="entry-header">\n'
            f'    <span class="entry-title">{e["title"]}</span>\n'
            f'    <span class="entry-date">{e["date"]} &nbsp;|&nbsp; {e["location"]}</span>\n'
            f'  </div>\n'
            f'{org_line}'
            f'  <ul>\n{bullets}\n  </ul>\n'
            f'</div>'
        )
    return "\n\n".join(blocks)


def ats_education(d: dict) -> str:
    blocks = []
    for e in d["education"]:
        blocks.append(
            f'<div class="entry" style="break-inside: avoid; page-break-inside: avoid;">\n'
            f'  <div class="entry-header">\n'
            f'    <span class="entry-title">{e["degree"]}</span>\n'
            f'    <span class="entry-date">{e["date"]} &nbsp;|&nbsp; {e["location"]}</span>\n'
            f'  </div>\n'
            f'  <p class="entry-sub" style="font-weight: bold; color: #000;">{e["org"]}</p>\n'
            f'  <p class="entry-sub">{e["note"]}</p>\n'
            f'</div>'
        )
    return "\n\n".join(blocks)


def ats_languages(d: dict) -> str:
    parts = [f'{l["name"]} ({l["level"]})' for l in d["languages"]]
    return "<p>" + " &nbsp;&middot;&nbsp; ".join(parts) + "</p>"


# ── VISUAL BUILDERS ───────────────────────────────────────────────────────────

def visual_name(d: dict) -> str:
    h = d["header"]
    return (
        f'        <div class="hdr-name">{h["name_short"]}</div>\n'
        f'        <div class="hdr-role">{h["role"]}</div>'
    )


def visual_contact(d: dict) -> str:
    c = d["contact"]
    return (
        f'  <div class="sb-row">\n'
        f'    <div class="sb-icon-wrap">&#9742;</div>\n'
        f'    <span class="sb-val">{c["phone"]}</span>\n'
        f'  </div>\n'
        f'  <div class="sb-row">\n'
        f'    <div class="sb-icon-wrap" style="font-size:6.5pt;">@</div>\n'
        f'    <span class="sb-val">'
        f'<a href="mailto:{c["email"]}">{c["email"]}</a></span>\n'
        f'  </div>\n'
        f'  <div class="sb-row">\n'
        f'    <div class="sb-icon-wrap" style="font-size:6pt;font-weight:900;">in</div>\n'
        f'    <span class="sb-val">'
        f'<a href="{c["linkedin_url"]}">{c["linkedin_handle"]}</a></span>\n'
        f'  </div>\n'
        f'  <div class="sb-row">\n'
        f'    <div class="sb-icon-wrap" style="font-size:7pt;">&#9654;</div>\n'
        f'    <span class="sb-val">'
        f'<a href="{c["github_url"]}">{c["github_handle"]}</a></span>\n'
        f'  </div>\n'
        f'  <div class="sb-row">\n'
        f'    <div class="sb-icon-wrap" style="font-size:7pt;">&#9679;</div>\n'
        f'    <span class="sb-val">{c["location"]}</span>\n'
        f'  </div>'
    )


def visual_tagline(d: dict) -> str:
    return f'<div class="hdr-tagline">{d["header"]["tagline"]}</div>'


def visual_skills(d: dict) -> str:
    lines = []
    for cat in d["skills"]:
        lines.append(f'  <div class="sk-cat">{cat["category"]}</div>')
        lines.append(f'  <div class="sk-wrap">')
        for item in cat["items"]:
            lines.append(f'    <span class="sk-tag sk-{cat["color"]}">{item}</span>')
        lines.append(f'  </div>')
    return "\n".join(lines)


def visual_languages(d: dict) -> str:
    blocks = []
    for lang in d["languages"]:
        dots_on  = '<span class="dot-on"></span>' * lang["dots"]
        dots_off = '<span class="dot-off"></span>' * (5 - lang["dots"])
        blocks.append(
            f'  <div class="lang-item">\n'
            f'    <div class="lang-name">{lang["name"]}</div>\n'
            f'    <div class="lang-level">{lang["level"]}</div>\n'
            f'    <div class="lang-dots">{dots_on}{dots_off}</div>\n'
            f'  </div>'
        )
    return "\n".join(blocks)


def visual_certs(d: dict) -> str:
    lines = []
    for c in d["certifications"]:
        if c["status"] == "in_progress":
            sub_html = f'<div class="cert-inprogress">&#8226; In progress</div>'
        else:
            sub_html = f'<div class="cert-sub">{c["sub"]}</div>'
        lines.append(f'  <div class="cert-card"><div class="cert-name">{c["name"]}</div>{sub_html}</div>')
    return "\n".join(lines)


def visual_profile(d: dict) -> str:
    return f'    <p class="profile-text">{d["profile"]}</p>'


def visual_projects(d: dict) -> str:
    blocks = []
    for p in d["projects"]:
        bullets = "\n".join(f'      <li>{b}</li>' for b in p["bullets"])
        badge = f' <span class="badge" style="{p["badge_style"]}">{p["badge_label"]}</span>' if p.get("badge_label") else ""
        url_part = f'&nbsp;&middot;&nbsp; <a href="{p["url"]}" style="color:#2563eb;text-decoration:none;">{p["url_label"]}</a>' if p.get("url") else ""
        blocks.append(
            f'  <div class="entry">\n'
            f'    <div class="e-title">{p["title"]}{badge}</div>\n'
            f'    <div class="e-meta">{p["date"]}{url_part}</div>\n'
            f'    <ul class="bul">\n{bullets}\n    </ul>\n'
            f'  </div>'
        )
    return "\n".join(blocks)


def visual_experience(d: dict) -> str:
    blocks = []
    for e in d["experience"]:
        bullets = "\n".join(f'      <li>{b}</li>' for b in e["bullets"])
        org_line = f'    <div class="e-org">{e["org"]}</div>\n' if e.get("org") else ""
        blocks.append(
            f'  <div class="entry">\n'
            f'    <div class="e-title">{e["title"]}</div>\n'
            f'{org_line}'
            f'    <div class="e-meta">{e["date"]} &nbsp;&middot;&nbsp; {e["location"]}</div>\n'
            f'    <ul class="bul">\n{bullets}\n    </ul>\n'
            f'  </div>'
        )
    return "\n".join(blocks)


def visual_education(d: dict) -> str:
    blocks = []
    for e in d["education"]:
        blocks.append(
            f'  <div class="ed-entry">\n'
            f'    <div class="ed-deg">{e["degree"]}</div>\n'
            f'    <div class="ed-org">{e["org"]}</div>\n'
            f'    <div class="ed-meta">{e["date"]} &nbsp;&middot;&nbsp; {e["location"]}</div>\n'
            f'    <div class="ed-note">{e["note"]}</div>\n'
            f'  </div>'
        )
    return "\n".join(blocks)


# ── MAIN ──────────────────────────────────────────────────────────────────────

def compile_ats(d: dict):
    html = ATS_PATH.read_text(encoding="utf-8")
    html = inject(html, "HEADER",     ats_header(d))
    html = inject(html, "PROFILE",    ats_profile(d))
    html = inject(html, "SKILLS",     ats_skills(d))
    html = inject(html, "CERTS",      ats_certs(d))
    html = inject(html, "PROJECTS",   ats_projects(d))
    html = inject(html, "EXPERIENCE", ats_experience(d))
    html = inject(html, "EDUCATION",  ats_education(d))
    html = inject(html, "LANGUAGES",  ats_languages(d))
    ATS_PATH.write_text(html, encoding="utf-8")
    print(f"  ATS resume updated: {ATS_PATH}")


def compile_visual(d: dict):
    html = VISUAL_PATH.read_text(encoding="utf-8")
    html = inject(html, "NAME",       visual_name(d))
    html = inject(html, "CONTACT",    visual_contact(d))
    html = inject(html, "TAGLINE",    visual_tagline(d))
    html = inject(html, "SKILLS",     visual_skills(d))
    html = inject(html, "LANGUAGES",  visual_languages(d))
    html = inject(html, "CERTS",      visual_certs(d))
    html = inject(html, "PROFILE",    visual_profile(d))
    html = inject(html, "PROJECTS",   visual_projects(d))
    html = inject(html, "EXPERIENCE", visual_experience(d))
    html = inject(html, "EDUCATION",  visual_education(d))
    VISUAL_PATH.write_text(html, encoding="utf-8")
    print(f"  Visual resume updated: {VISUAL_PATH}")


if __name__ == "__main__":
    print("Loading data.json...")
    data = load_data()
    print("Compiling ATS resume...")
    compile_ats(data)
    print("Compiling visual resume...")
    compile_visual(data)
    print("Done. Both resumes are in sync.")
