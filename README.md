# ClineReel

**Turn any website into a polished promo video — powered by a multi-agent pipeline with Cline as core infrastructure.**

ClineReel is a system that treats [Cline](https://cline.bot) not as a coding assistant, but as a **programmable component** — a headless subprocess that generates production Remotion video code on demand, orchestrated by upstream AI agents.

Paste a URL. Get a video. No templates required.

---

## Hackathon Challenge: Cline as a Building Block

> *Use Cline not as your coding assistant, but as a building block. Integrate the Cline CLI into a larger system, pipeline, or application. Think of Cline as a programmable component.*

ClineReel answers this by making Cline the **render engine** in a multi-agent video generation pipeline. Four AI agents collaborate to scrape a website, analyze its value proposition, design a creative storyboard, and then **invoke Cline as a subprocess** to write brand-new Remotion code from scratch — no templates, no human intervention.

The key insight: Cline isn't helping a developer write code. Cline **is** the developer — called programmatically by a Python backend, given a creative brief, and expected to produce working React/Remotion components autonomously.

```python
# The core innovation — Cline as infrastructure (src/sandbox/render.py)
proc = await asyncio.create_subprocess_exec(
    "cline", "-y", "--timeout", "900",
    "Read TASK_BRIEF.md and create a new Remotion video from scratch...",
    cwd=work_dir,
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.STDOUT,
)
```

---

## Architecture

```
                          +-----------------------+
                          |      React Frontend   |
                          |  URL input + polling  |
                          +----------+------------+
                                     |
                                POST /generate
                                GET  /status/:id
                                     |
                          +----------v------------+
                          |   FastAPI Backend      |
                          |   (src/api.py)         |
                          |   Job queue + routing  |
                          +----------+------------+
                                     |
                    +----------------+----------------+
                    |                                  |
             TEMPLATED MODE                    AGENTIC MODE
             (fast, consistent)                (unique, creative)
                    |                                  |
        +-----------+-----------+          +-----------+-----------+
        |                       |          |                       |
   +----v----+           +------v---+  +---v------+         +-----v------+
   | Scraper |           | Director |  | Scraper  |         | Storyboard |
   | Agent   |           | Agent    |  | Agent    |         | Agent      |
   +---------+           +----------+  +----------+         +-----+------+
        |                       |          |                       |
   Firecrawl /            GPT-4o fills   Firecrawl /         GPT-4o designs
   BrowserUse             template props  BrowserUse         scene-by-scene
        |                       |          |                  creative brief
        v                       v          v                       |
   +----+----+           +------+---+  +---+------+               |
   | Analyst |           | Remotion |  | Analyst  |               |
   | Agent   |           | Template |  | Agent    |               v
   +---------+           | Render   |  +----------+     +---------+--------+
        |                +----------+       |           |  TASK_BRIEF.md   |
   GPT-4o extracts            |        GPT-4o extracts  |  (written to     |
   hook/solution/stack        v        hook/solution     |   work dir)      |
        |                  MP4 out          |            +---------+--------+
        v                                   v                      |
   analysis.json                      analysis.json                v
                                                         +---------+--------+
                                                         |   Cline CLI      |
                                                         |   (subprocess)   |
                                                         |                  |
                                                         |  1. Reads brief  |
                                                         |  2. Deletes old  |
                                                         |     scene files  |
                                                         |  3. Writes new   |
                                                         |     React/TSX    |
                                                         |  4. Downloads    |
                                                         |     images       |
                                                         |  5. Runs npx     |
                                                         |     remotion     |
                                                         |     render       |
                                                         +---------+--------+
                                                                   |
                                                                   v
                                                                MP4 out
```

### The Four Agents

| Agent | Role | Model | Input | Output |
|-------|------|-------|-------|--------|
| **Scraper** | Extract structured data from any URL | Firecrawl + BrowserUse APIs | Raw URL | `{ title, tagline, description, gallery }` |
| **Analyst** | Distill the core value proposition | GPT-4o (structured output) | Scraped data | `{ hook, solution, stack }` |
| **Director** | Design visual direction (templated) or full storyboard (agentic) | GPT-4o (structured output) | Analysis + images | `DirectorOutput` or `VideoStoryboard` |
| **Cline** | Generate production Remotion code from a creative brief | Cline CLI (subprocess) | `TASK_BRIEF.md` | Working `.tsx` components + rendered MP4 |

### Why Cline as Infrastructure?

Most AI coding tools sit in a terminal waiting for human prompts. ClineReel flips this:

- **Headless invocation** — `cline -y --timeout 900` runs non-interactively with auto-approval
- **File-based communication** — The Python backend writes `TASK_BRIEF.md`; Cline reads it and produces code
- **Isolated execution** — Each job gets a fresh working directory (`~/.remotion-agentic/work-{job_id}/`) with symlinked `node_modules`
- **Autonomous end-to-end** — Cline deletes old templates, creates new scene components, downloads assets, and runs the Remotion render — all without human input

This is Cline as a **programmable code generation service**, not a chat interface.

---

## Data Flow (Agentic Mode)

```
1. User enters URL
   ↓
2. Scraper Agent hits Firecrawl API (fallback: BrowserUse)
   → { title: "Acme AI", description: "...", gallery: ["img1.png", ...] }
   ↓
3. Analyst Agent (GPT-4o structured output)
   → { hook: "Teams waste 40% of time on...", solution: "Acme automates...", stack: "RAG + GPT-4" }
   ↓
4. Storyboard Agent (GPT-4o structured output)
   → VideoStoryboard with 5 scenes, color palette, animation notes
   ↓
5. System writes TASK_BRIEF.md to isolated work directory
   ↓
6. Cline subprocess invoked:
   $ cline -y --timeout 900 "Read TASK_BRIEF.md and create a Remotion video..."
   ↓
7. Cline autonomously:
   - Reads the brief
   - Creates src/scenes/Hook.tsx, Problem.tsx, Solution.tsx, Features.tsx, CTA.tsx
   - Creates src/PromoVideo.tsx composing scenes with <Series>
   - Downloads images to public/
   - Runs: npx remotion render PromoVideo out/video.mp4
   ↓
8. Backend collects MP4, serves at /api/outputs/video_{job_id}.mp4
   ↓
9. Frontend polls /status/{job_id}, displays video player
```

---

## Project Structure

```
.
├── src/
│   ├── api.py                    # FastAPI server, job queue, endpoints
│   ├── agents/
│   │   ├── scraper.py            # Firecrawl + BrowserUse dual scraper
│   │   ├── agents.py             # Analyst, Director, Storyboard agents
│   │   ├── schemas.py            # Pydantic models for all agent I/O
│   │   └── pipeline.py           # CLI orchestrator
│   └── sandbox/
│       ├── render.py             # Render orchestration + Cline invocation
│       └── assets.py             # Image downloading with fallbacks
├── frontend/
│   └── src/
│       ├── App.jsx               # Main React app
│       ├── api/client.js         # API client (generate, poll status)
│       ├── hooks/useJobPolling.js # 2-second status polling
│       └── components/
│           ├── UrlInput.jsx      # URL input form
│           ├── ProcessingStatus.jsx  # 5-stage pipeline progress
│           ├── VideoPreview.jsx  # Video player
│           └── ActionButtons.jsx # Generate/download buttons
├── outputs/                      # Rendered videos + debug JSON (gitignored)
├── .env.example                  # Environment variable template
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- [Cline CLI](https://cline.bot) installed and on PATH
- A Remotion project at `~/remotion-demo-2` (or configure `REMOTION_PROJECT_DIR`)

### Setup

```bash
# Clone the repo
git clone https://github.com/your-username/clinereel.git
cd clinereel

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Copy env template and fill in your keys
cp .env.example .env
# Edit .env with your API keys

# Install frontend dependencies
cd frontend && npm install && cd ..
```

### Environment Variables

```bash
OPENAI_API_KEY=          # GPT-4o for Analyst/Director/Storyboard agents
FIRECRAWL_API_KEY=       # Primary web scraper
RENDER_MODE=templated    # "templated" (fast) or "agentic" (Cline-powered)
REMOTION_PROJECT_DIR=~/remotion-demo-2  # Path to Remotion project
```

### Run

```bash
# Start the backend
python -m uvicorn src.api:app --host 0.0.0.0 --port 8000

# Start the frontend (separate terminal)
cd frontend && npm run dev
```

Open `http://localhost:5173`, paste a URL, and hit Generate.

---

## How Cline Is Invoked

The critical code lives in `src/sandbox/render.py`. Here's the flow:

**1. Isolated workspace creation**
```python
work_dir = os.path.expanduser(f"~/.remotion-agentic/work-{job_id}")
shutil.copytree(project_dir, work_dir)
# Symlink node_modules to save disk space
os.symlink(os.path.join(project_dir, "node_modules"),
           os.path.join(work_dir, "node_modules"))
```

**2. Creative brief generation** — The storyboard JSON is converted into a `TASK_BRIEF.md`:
```markdown
# Video Implementation Brief
## Product: Acme AI
## Creative Concept
A high-energy promo showcasing Acme's RAG pipeline...

## Scene 1: Hook (3s, 90 frames)
- Headline: "Your Data Is Scattered Everywhere"
- Visual: Dark background, floating document icons drifting apart
- Animation: Icons scatter outward, then freeze. Text slams in from bottom.
...
## Implementation Instructions
1. DELETE all existing files in src/scenes/
2. Create one .tsx component per scene
3. Compose with <Series> in src/PromoVideo.tsx
4. Download images to public/
5. Run: npx remotion render PromoVideo out/video.mp4
```

**3. Subprocess invocation**
```python
proc = await asyncio.create_subprocess_exec(
    "cline", "-y", "--timeout", "900",
    "Read TASK_BRIEF.md and create a new Remotion video from scratch...",
    cwd=work_dir,
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.STDOUT,
)
```

**4. Output collection** — The backend finds the rendered MP4 in `work_dir/out/` and copies it to `outputs/`.

---

## Schemas

### AnalystOutput
```python
class AnalystOutput(BaseModel):
    hook: str        # "Teams waste 40% of time on manual data entry"
    solution: str    # "Acme uses RAG to auto-populate forms from any source"
    stack: str       # "RAG pipeline, GPT-4o, vector DB, React frontend"
```

### VideoStoryboard (Agentic Mode)
```python
class VideoStoryboard(BaseModel):
    product_name: str
    video_concept: str              # Overall creative vision
    color_palette: list[str]        # 3-6 hex codes
    total_duration_seconds: float   # 15-25s
    scenes: list[SceneDescription]  # 3-7 scenes
    image_urls: list[str]           # Assets to download
    closing_cta: str                # Final call-to-action
```

### DirectorOutput (Templated Mode)
```python
class DirectorOutput(BaseModel):
    product: Product         # Name (max 10 chars), tagline, logo
    problem: Problem         # Two-line hook with accent color
    solution: Solution       # Headline + subline
    screenshots: list[Screenshot]  # 1-2 images with callouts
    outro: Outro             # CTA + optional badge
    theme: Theme             # Primary, accent, background, text colors
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/generate` | Start video generation. Body: `{ "url": "https://..." }`. Returns `{ job_id, status }` |
| `GET` | `/status/{job_id}` | Poll job progress. Returns stage (`scraping` → `analyzing` → `storyboarding` → `rendering` → `done`), detail text, and video path when complete |
| `GET` | `/health` | Health check. Returns `{ status: "ok", render_mode: "agentic" }` |
| `GET` | `/outputs/{file}` | Serve rendered video files |

---

## License

MIT
