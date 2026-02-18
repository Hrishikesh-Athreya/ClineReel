"""
render.py - Render Remotion video locally using either templated or agentic mode.

Modes (controlled by RENDER_MODE env var):
  - "templated": Copies props/assets into a pre-cloned Remotion project and runs
                 `npx remotion render` directly via subprocess.
  - "agentic":   Scrapes the target URL, writes a creative brief, invokes Cline CLI
                 headlessly to create a brand-new Remotion video from scratch and render it.
                 Cline has full creative freedom — no existing template is used.

Exposes `render_video(...)` for programmatic use.
"""

import os
import sys
import json
import shutil
import asyncio
import subprocess
import tempfile
from dotenv import load_dotenv
from .assets import upload_standard_assets
from .audio import generate_scene_voiceovers, prepare_background_music

load_dotenv()

RENDER_MODE = os.environ.get("RENDER_MODE", "templated")
REMOTION_PROJECT_DIR = os.path.expanduser(
    os.environ.get("REMOTION_PROJECT_DIR", "~/remotion-demo-2")
)
DEFAULT_PROPS_FILE = "showcase-props.json"


def _output_name_from_props(local_props_path: str) -> str:
    """Derive an output filename from the props file name."""
    basename = os.path.basename(local_props_path)
    if "temp_props_" in basename:
        job_id = basename.replace("temp_props_", "").replace(".json", "")
        return f"video_{job_id}.mp4"
    if "showcase-props" in basename:
        return "motionforge.mp4"
    return "rendered_video.mp4"


async def render_video(
    local_props_path: str = DEFAULT_PROPS_FILE,
    url: str | None = None,
    scraped_data: dict | None = None,
    storyboard=None,
) -> str:
    """
    Render a Remotion video locally.

    In templated mode, uses local_props_path (pre-generated ShowcaseProps JSON).
    In agentic mode, uses a storyboard (from the Creative Director agent) to
    give Cline a detailed scene-by-scene plan to implement.

    Returns the absolute path to the rendered .mp4 file.
    """
    local_props_path = os.path.abspath(local_props_path)

    if RENDER_MODE == "agentic":
        return await _render_agentic(
            local_props_path, url=url, scraped_data=scraped_data, storyboard=storyboard,
        )
    else:
        if not os.path.exists(local_props_path):
            raise FileNotFoundError(f"Props file not found: {local_props_path}")
        return await _render_templated(local_props_path)


# ---------------------------------------------------------------------------
# Templated mode
# ---------------------------------------------------------------------------

async def _render_templated(local_props_path: str) -> str:
    """Copy props + assets into the local Remotion project and render."""
    project_dir = REMOTION_PROJECT_DIR
    if not os.path.isdir(project_dir):
        raise FileNotFoundError(
            f"Remotion project not found at {project_dir}. "
            "Clone it first: git clone <repo> ~/remotion-demo-2 && cd ~/remotion-demo-2 && npm install"
        )

    # Load props
    with open(local_props_path, "r") as f:
        props_data = json.load(f)

    # Download assets into project public/
    upload_standard_assets(project_dir, props_data)

    # Write updated props (with local asset filenames) back
    with open(local_props_path, "w") as f:
        json.dump(props_data, f, indent=2)

    # Copy props to project config location
    remote_props_path = os.path.join(project_dir, "src", "configs", "signal.json")
    os.makedirs(os.path.dirname(remote_props_path), exist_ok=True)
    shutil.copy(local_props_path, remote_props_path)
    print(f"Copied props to {remote_props_path}")

    # Determine output name
    output_name = _output_name_from_props(local_props_path)
    out_dir = os.path.join(project_dir, "out")
    os.makedirs(out_dir, exist_ok=True)
    remote_output = os.path.join(out_dir, output_name)

    # Build render command
    render_cmd = [
        "npx", "remotion", "render",
        "PromoVideo",
        f"out/{output_name}",
        f"--props={remote_props_path}",
        "--concurrency=1",
    ]

    print(f"Starting render -> {output_name}")
    print("-" * 60)

    proc = await asyncio.create_subprocess_exec(
        *render_cmd,
        cwd=project_dir,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    while True:
        line = await proc.stdout.readline()
        if not line:
            break
        print(line.decode(), end="")

    await proc.wait()
    print("-" * 60)

    if proc.returncode != 0:
        raise RuntimeError(f"Remotion render failed with exit code {proc.returncode}")

    print("Render finished.")

    os.makedirs("outputs", exist_ok=True)
    local_video_path = os.path.abspath(f"outputs/{output_name}")
    shutil.copy(remote_output, local_video_path)

    size = os.path.getsize(local_video_path)
    print(f"Output: {local_video_path} ({size / 1024 / 1024:.2f} MB)")
    return local_video_path


# ---------------------------------------------------------------------------
# Agentic mode
# ---------------------------------------------------------------------------

async def _render_agentic(
    local_props_path: str,
    url: str | None = None,
    scraped_data: dict | None = None,
    storyboard=None,
) -> str:
    """
    Multi-agent agentic render. Takes a storyboard designed by the Creative Director
    agent and hands it to Cline to implement as a Remotion video from scratch.

    Creates a temporary copy of the Remotion project so the original template
    stays untouched for future templated renders.
    """
    source_dir = REMOTION_PROJECT_DIR
    if not os.path.isdir(source_dir):
        raise FileNotFoundError(
            f"Remotion project not found at {source_dir}. "
            "Clone it first: git clone <repo> ~/remotion-demo-2 && cd ~/remotion-demo-2 && npm install"
        )

    output_name = _output_name_from_props(local_props_path)

    # --- 1. Create a fresh working copy (symlink node_modules to save space) ---
    # Use a directory under home to avoid shell spawn issues in deep /var/folders paths
    job_id = os.path.basename(local_props_path).replace("temp_props_", "").replace(".json", "")
    agentic_base = os.path.expanduser("~/.remotion-agentic")
    os.makedirs(agentic_base, exist_ok=True)
    work_dir = os.path.join(agentic_base, f"work-{job_id}")
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)

    print(f"[agentic] Creating working copy at {work_dir}...")
    # Copy everything except node_modules and out/
    shutil.copytree(
        source_dir,
        work_dir,
        ignore=shutil.ignore_patterns("node_modules", "out", ".git"),
    )
    # Symlink node_modules from the original so we don't re-install
    os.symlink(
        os.path.join(source_dir, "node_modules"),
        os.path.join(work_dir, "node_modules"),
    )
    os.makedirs(os.path.join(work_dir, "out"), exist_ok=True)

    # Ensure .cline and .agents directories are present (for Remotion skills)
    # They may already be copied by copytree; if not, copy them now
    for skills_dir in [".cline", ".agents"]:
        src_skills = os.path.join(source_dir, skills_dir)
        dst_skills = os.path.join(work_dir, skills_dir)
        if os.path.isdir(src_skills) and not os.path.isdir(dst_skills):
            shutil.copytree(src_skills, dst_skills)

    print(f"[agentic] Working copy ready.")

    # --- 2. Ensure we have a storyboard ---
    if storyboard is None:
        # Fallback: run the multi-agent pipeline inline
        if scraped_data is None and url:
            from src.agents.scraper import scrape_url
            print(f"[agentic] Scraping {url}...")
            scraped_data = scrape_url(url)

        if not scraped_data:
            raise ValueError("Agentic mode requires a URL, scraped data, or storyboard.")

        from src.agents.agents import Agents
        print("[agentic] Running Analyst agent...")
        analysis = Agents.analyze(scraped_data)
        print(f"[agentic] Analysis: {analysis.hook[:80]}")

        raw = scraped_data.get("raw_browse_data", {})
        print("[agentic] Running Creative Director agent...")
        storyboard = Agents.storyboard(
            product_name=scraped_data.get("title", "Product"),
            analysis=analysis,
            available_images=scraped_data.get("gallery", []),
            website_description=scraped_data.get("description", ""),
            features=raw.get("features", []),
        )
        print(f"[agentic] Storyboard ready: {len(storyboard.scenes)} scenes")

    # --- 3. Generate audio (voiceovers + background music) ---
    public_dir = os.path.join(work_dir, "public")
    os.makedirs(public_dir, exist_ok=True)

    audio_metadata = []
    background_music_file = None
    try:
        audio_metadata = generate_scene_voiceovers(storyboard, public_dir)
        sb_dict = storyboard.model_dump() if hasattr(storyboard, "model_dump") else storyboard
        music_style = sb_dict.get("background_music_style", "upbeat")
        background_music_file = prepare_background_music(music_style, public_dir)
    except Exception as e:
        print(f"[agentic] Warning: Audio generation failed, continuing without audio: {e}")

    # --- 4. Build the implementation brief from the storyboard ---
    brief_path = os.path.join(work_dir, "TASK_BRIEF.md")
    brief = _build_agentic_brief(storyboard, output_name, audio_metadata=audio_metadata, background_music_file=background_music_file)
    with open(brief_path, "w") as f:
        f.write(brief)

    task_prompt = (
        "Read the file TASK_BRIEF.md in your working directory. "
        "It contains the website content you need to promote and full instructions. "
        "You must create a completely new Remotion video from scratch — "
        "DELETE all existing scene files and create your own. "
        "You have Remotion skills installed — use them for best practices."
    )

    cline_cmd = [
        "cline", "-y",
        "--timeout", "900",
        task_prompt,
    ]

    print(f"[agentic] Invoking Cline agent for render -> {output_name}")
    print(f"[agentic] Brief written to {brief_path}")
    print(f"[agentic] Working directory: {work_dir}")
    print("-" * 60)

    proc = await asyncio.create_subprocess_exec(
        *cline_cmd,
        cwd=work_dir,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    while True:
        line = await proc.stdout.readline()
        if not line:
            break
        print(line.decode(), end="")

    await proc.wait()
    print("-" * 60)

    if proc.returncode != 0:
        print(f"Warning: Cline exited with code {proc.returncode}")

    # --- 4. Find the output video ---
    remote_output = os.path.join(work_dir, "out", output_name)
    if not os.path.exists(remote_output):
        out_dir = os.path.join(work_dir, "out")
        if os.path.isdir(out_dir):
            mp4s = [f for f in os.listdir(out_dir) if f.endswith(".mp4")]
            if mp4s:
                mp4s.sort(
                    key=lambda f: os.path.getmtime(os.path.join(out_dir, f)),
                    reverse=True,
                )
                remote_output = os.path.join(out_dir, mp4s[0])
                print(f"[agentic] Found output: {remote_output}")
            else:
                raise FileNotFoundError(f"No .mp4 files found in {out_dir}")
        else:
            raise FileNotFoundError(f"Output directory not found: {out_dir}")

    os.makedirs("outputs", exist_ok=True)
    local_video_path = os.path.abspath(f"outputs/{output_name}")
    shutil.copy(remote_output, local_video_path)

    size = os.path.getsize(local_video_path)
    print(f"Output: {local_video_path} ({size / 1024 / 1024:.2f} MB)")

    # --- 5. Cleanup working copy ---
    try:
        shutil.rmtree(work_dir)
        print(f"[agentic] Cleaned up working copy.")
    except Exception as e:
        print(f"[agentic] Warning: could not clean up {work_dir}: {e}")

    return local_video_path


def _build_agentic_brief(storyboard, output_name: str, audio_metadata: list[dict] | None = None, background_music_file: str | None = None) -> str:
    """
    Build an implementation brief for Cline from a VideoStoryboard object
    designed by the Creative Director agent.
    """
    # Handle both pydantic model and dict
    if hasattr(storyboard, "model_dump"):
        sb = storyboard.model_dump()
    else:
        sb = storyboard

    product_name = sb.get("product_name", "Product")
    concept = sb.get("video_concept", "")
    colors = sb.get("color_palette", ["#000000", "#ffffff", "#0066ff"])
    total_dur = sb.get("total_duration_seconds", 20)
    scenes = sb.get("scenes", [])
    image_urls = sb.get("image_urls", [])
    cta = sb.get("closing_cta", "")

    total_frames = int(total_dur * 30)

    # Format color palette
    color_list = "\n".join(f"  - `{c}`" for c in colors)

    # Build audio lookup by scene number
    audio_by_scene = {}
    if audio_metadata:
        for am in audio_metadata:
            audio_by_scene[am["scene_number"]] = am

    # Format scenes
    scenes_section = ""
    for s in scenes:
        dur_frames = int(s.get("duration_seconds", 4) * 30)
        scene_num = s.get("scene_number", 0)
        scenes_section += f"""
### Scene {scene_num}: {s.get('scene_name', 'Untitled')}
- **Duration**: {s.get('duration_seconds', 4)}s ({dur_frames} frames)
- **Headline**: "{s.get('headline_text', '')}"
- **Supporting text**: "{s.get('supporting_text', '')}"
- **Visual concept**: {s.get('visual_concept', '')}
- **Animation notes**: {s.get('animation_notes', '')}
"""
        if scene_num in audio_by_scene:
            am = audio_by_scene[scene_num]
            scenes_section += f"""- **Voiceover audio**: `{am['filename']}` (script: "{am['script']}", ~{am['duration_estimate']}s)
"""

    # Format image URLs
    images_section = ""
    if image_urls:
        images_section = "## Images to Download\nDownload these to `public/` and use via `staticFile()`:\n"
        for img in image_urls:
            images_section += f"- {img}\n"

    # Format audio section
    audio_section = ""
    if audio_metadata or background_music_file:
        audio_section = "## Audio Files\n\nPre-generated audio files are in `public/`. Wire them into your Remotion components.\n\n"
        if audio_metadata:
            audio_section += "### Voiceovers (per scene)\n"
            for am in audio_metadata:
                audio_section += f"- Scene {am['scene_number']}: `{am['filename']}` — \"{am['script']}\"\n"
            audio_section += "\n"
        if background_music_file:
            audio_section += f"### Background Music\n- `{background_music_file}` (loops, low volume)\n\n"

    return f"""# Video Implementation Brief

> This storyboard was designed by the Creative Director AI agent.
> Your job is to implement it exactly as described using Remotion.

## Product: {product_name}

## Creative Concept
{concept}

## Color Palette
{color_list}

## Closing CTA
"{cta}"

{images_section}

{audio_section}

## Scene-by-Scene Storyboard
Total duration: {total_dur}s ({total_frames} frames at 30fps)
{scenes_section}

---

## Implementation Instructions

You are an expert Remotion developer. Implement the storyboard above as a Remotion video.
Each scene description tells you exactly what to build — follow the visual concepts and
animation notes closely.

### Steps

1. **Delete ALL existing files** in `src/scenes/` — start completely fresh
2. **Create one `.tsx` component per scene** in `src/scenes/`
3. **Create `src/PromoVideo.tsx`** that composes all scenes using `<Series>` or `<TransitionSeries>`
4. **Update `src/Root.tsx`** to register the composition:
   - id: `"PromoVideo"`
   - Width: 1920, Height: 1080, FPS: 30
   - Duration: {total_frames} frames
5. **Download any images** listed above to `public/` using curl
6. **Render**: `npx remotion render PromoVideo out/{output_name} --concurrency=1`
7. **Verify**: Confirm `out/{output_name}` exists and is non-empty

### Audio Integration
- Import `{{Audio, staticFile}}` from `remotion`
- For each scene with a voiceover file, add inside the scene component:
  `<Audio src={{staticFile("voiceover_scene_N.mp3")}} volume={{0.8}} />`
- For background music, add at the root composition level (in `PromoVideo.tsx`):
  `<Audio src={{staticFile("background_music.mp3")}} loop volume={{0.15}} />`
- Audio files are already in `public/` — do NOT download them
- **IMPORTANT: Scene timing must accommodate voiceover duration.** Each scene's
  `<Series.Sequence>` duration MUST be at least the voiceover duration + 1 second of buffer.
  If a voiceover is ~3s, the scene should be at least 4s (120 frames). Voiceovers that get
  cut off by a scene transition sound broken — always leave breathing room at the end.

### Animation Toolkit (use these!)
- `spring({{ frame, fps, config: {{ damping: 15, stiffness: 100 }} }})` — organic entrances
- `interpolate(frame, [start, end], [from, to], {{ extrapolateRight: 'clamp' }})` — smooth transitions
- `<Sequence from={{N}}>` — delay element appearance
- `<Series>` / `<Series.Sequence>` — sequential scene timing
- `<TransitionSeries>` from `@remotion/transitions` — transitions between scenes
- `staticFile('name.png')` — reference images in `public/`

### Typography
- Font: `system-ui, -apple-system, sans-serif`
- Use bold weights (700-900) for headlines, light (300-400) for subtext
- Vary sizes dramatically: 80-120px headlines, 24-36px body

### What NOT to do
- Do NOT keep any existing template code — delete `src/scenes/*`, `src/types.ts`, `src/SignalPromo.tsx`
- Do NOT install new npm packages
- Do NOT use placeholder text — use the exact text from the storyboard
- Do NOT make it generic — follow the creative concept precisely

### Output
Final video MUST be at: `out/{output_name}`
"""


if __name__ == "__main__":
    props_arg = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PROPS_FILE
    url_arg = sys.argv[2] if len(sys.argv) > 2 else None
    asyncio.run(render_video(props_arg, url=url_arg))
