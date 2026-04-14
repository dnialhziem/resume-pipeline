# resume-pipeline

Automated resume builder — fill in one JSON file, get two professional PDFs (ATS-clean + visual) compiled automatically via GitHub Actions on every push.

---

## How It Works

```
data.json  →  compile_resume.py  →  resume.html + resume_visual.html  →  PDF × 2
```

- **ATS resume** (`resume.pdf`) — single-column, no graphics, optimised for applicant tracking systems
- **Visual resume** (`resume_visual.pdf`) — two-column with colour, photo, and skill tags

---

## Quick Start

### 1. Clone and set up

```bash
git clone https://github.com/YOUR_USERNAME/resume-pipeline.git
cd resume-pipeline
```

### 2. Install Python dependencies

```bash
pip install requests websocket-client pdfplumber python-docx
```

### 3. Build your data.json

**Option A — AI-assisted (recommended, requires Ollama):**

```bash
# Install Ollama: https://ollama.com
ollama pull mistral:7b
python scripts/build_data.py your_existing_resume.pdf
```

**Option B — Manual guided Q&A:**

```bash
python scripts/build_data.py
```

Both options walk you through each section interactively. You review and correct the output before saving.

### 4. Compile your resumes locally

```bash
python scripts/compile_resume.py
```

Your personalised `resume.html` and `resume_visual.html` are ready in `resume/`.

### 5. Set up CI/CD (optional but recommended)

Fork or push to your own GitHub repo. GitHub Actions will automatically compile PDFs and publish them to GitHub Releases on every push.

No extra setup needed — the workflow is already included.

---

## Ollama Setup (AI extraction)

| Step | Command |
|---|---|
| Install Ollama | Download from [ollama.com](https://ollama.com) |
| Pull the model | `ollama pull mistral:7b` |
| Start Ollama | `ollama serve` (runs in background) |
| Disk space needed | ~4.5 GB |
| RAM needed | 8 GB minimum, 16 GB recommended |

The pipeline always uses `mistral:7b`. Do not change the model — it affects extraction quality.

---

## File Structure

```
resume-pipeline/
  resume/
    data.template.json   ← copy this, fill it in as data.json
    data.json            ← YOUR personal data (gitignored, never committed)
    resume.html          ← ATS template (do not edit manually)
    resume_visual.html   ← Visual template (do not edit manually)
  scripts/
    build_data.py        ← interactive data.json builder
    compile_resume.py    ← injects data.json into both templates
  .github/workflows/
    resume-pipeline.yml  ← CI/CD: auto-compiles PDFs on every push
```

---

## Updating Your Resume

1. Edit `resume/data.json` directly, or re-run `python scripts/build_data.py`
2. Run `python scripts/compile_resume.py` to preview locally
3. `git push` — GitHub Actions compiles and publishes fresh PDFs automatically

---

## Built by

[Muhammad Danial Haziem](https://github.com/dnialhziem) — CS student, University of Melbourne
