"""
api.py - FastAPI service for the Director Agent.
Accepts a Website URL, runs the pipeline, and returns a job ID.
All work happens in background tasks with granular stage reporting.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import json
import uuid
import asyncio
from typing import Optional

from src.agents.schemas import ShowcaseProps
from src.agents.pipeline import orchestrate_pipeline
from src.agents.scraper import scrape_url
from src.agents.agents import Agents
from src.sandbox.render import render_video, RENDER_MODE

# In-memory job store
jobs = {}

app = FastAPI(title="Director Agent API")

os.makedirs("outputs", exist_ok=True)
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")


class GenerateRequest(BaseModel):
    url: str


class GenerateResponse(BaseModel):
    job_id: str
    status: str
    message: str


class StatusResponse(BaseModel):
    job_id: str
    status: str
    stage: Optional[str] = None
    stage_detail: Optional[str] = None
    video_path: Optional[str] = None
    message: Optional[str] = None


def _update_job(job_id: str, **kwargs):
    """Update job fields."""
    if job_id in jobs:
        jobs[job_id].update(kwargs)


async def process_video_templated(job_id: str, url: str):
    """Background: templated mode — scrape, analyze, direct, render template."""
    try:
        # Stage 1: Scraping
        _update_job(job_id, stage="scraping", stage_detail="Scraping website content...")
        scraped_data = scrape_url(url)
        if not scraped_data:
            raise ValueError("Scraping failed: Could not retrieve data from website.")
        _update_job(job_id, stage_detail=f"Scraped '{scraped_data.get('title', 'site')}'")

        # Stage 2: Analyzing
        _update_job(job_id, stage="analyzing", stage_detail="AI analyzing website content...")
        analysis = Agents.analyze(scraped_data)
        _update_job(job_id, stage_detail=f"Hook: {analysis.hook[:60]}...")

        # Stage 3: Generating
        _update_job(job_id, stage="generating", stage_detail="Generating video props...")
        project_title = scraped_data.get("title", "Project")
        gallery_images = scraped_data.get("gallery", [])
        direction = Agents.direct(project_title, analysis, gallery_images)
        showcase_props = ShowcaseProps(config=direction)

        props_path = os.path.abspath(f"outputs/temp_props_{job_id}.json")
        with open(props_path, "w") as f:
            f.write(showcase_props.model_dump_json(indent=2))
        _update_job(job_id, stage_detail=f"Props ready for '{direction.product.name}'")

        # Stage 4: Rendering
        _update_job(job_id, stage="rendering", stage_detail="Rendering video from template...")
        video_path = await render_video(props_path)

        _update_job(
            job_id,
            status="completed",
            stage="done",
            stage_detail="Video ready!",
            video_path=f"/api/outputs/{os.path.basename(video_path)}",
            message="Render successful",
        )
        print(f"[Job {job_id}] Complete: {video_path}")

    except Exception as e:
        _update_job(job_id, status="failed", message=str(e), stage_detail=f"Error: {e}")
        print(f"[Job {job_id}] Failed: {e}")


async def process_video_agentic(job_id: str, url: str):
    """Background: agentic mode — scrape, analyze, storyboard, Cline builds from scratch."""
    try:
        # Stage 1: Scraping
        _update_job(job_id, stage="scraping", stage_detail="Scraping website content...")
        scraped_data = scrape_url(url)
        if not scraped_data:
            raise ValueError("Scraping failed: Could not retrieve data from website.")
        title = scraped_data.get("title", "site")
        _update_job(job_id, stage_detail=f"Scraped '{title}'")

        # Stage 2: Analyst Agent
        _update_job(job_id, stage="analyzing", stage_detail="Analyst AI extracting key insights...")
        analysis = Agents.analyze(scraped_data)
        _update_job(job_id, stage_detail=f"Hook: {analysis.hook[:60]}...")

        # Stage 3: Creative Director Agent → Storyboard
        _update_job(job_id, stage="storyboarding", stage_detail="Creative Director designing storyboard...")
        raw = scraped_data.get("raw_browse_data", {})
        storyboard = Agents.storyboard(
            product_name=scraped_data.get("title", "Product"),
            analysis=analysis,
            available_images=scraped_data.get("gallery", []),
            website_description=scraped_data.get("description", ""),
            features=raw.get("features", []),
        )
        _update_job(
            job_id,
            stage_detail=f"{len(storyboard.scenes)} scenes, {storyboard.total_duration_seconds}s video",
        )

        # Stage 4: Audio generation
        _update_job(job_id, stage="generating_audio", stage_detail="Generating voiceover with ElevenLabs...")

        # Stage 5: Cline builds and renders
        _update_job(job_id, stage="rendering", stage_detail="Cline is building the video from scratch...")
        dummy_props_path = os.path.abspath(f"outputs/temp_props_{job_id}.json")
        video_path = await render_video(
            dummy_props_path,
            url=url,
            scraped_data=scraped_data,
            storyboard=storyboard,
        )

        _update_job(
            job_id,
            status="completed",
            stage="done",
            stage_detail="Video ready!",
            video_path=f"/api/outputs/{os.path.basename(video_path)}",
            message="Render successful",
        )
        print(f"[Job {job_id}] Complete: {video_path}")

    except Exception as e:
        _update_job(job_id, status="failed", message=str(e), stage_detail=f"Error: {e}")
        print(f"[Job {job_id}] Failed: {e}")


@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest, background_tasks: BackgroundTasks):
    """
    Kicks off video generation immediately and returns a job ID.
    All work (scraping, analysis, storyboard, render) happens in the background.
    Poll /status/{job_id} for granular progress.
    """
    job_id = str(uuid.uuid4())[:8]

    jobs[job_id] = {
        "status": "processing",
        "stage": "queued",
        "stage_detail": "Starting...",
        "video_path": None,
        "message": None,
    }

    if RENDER_MODE == "agentic":
        background_tasks.add_task(process_video_agentic, job_id, request.url)
        return GenerateResponse(
            job_id=job_id,
            status="processing",
            message="Multi-agent pipeline started.",
        )
    else:
        background_tasks.add_task(process_video_templated, job_id, request.url)
        return GenerateResponse(
            job_id=job_id,
            status="processing",
            message="Templated pipeline started.",
        )


@app.get("/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job ID not found")

    job = jobs[job_id]
    return StatusResponse(
        job_id=job_id,
        status=job["status"],
        stage=job.get("stage"),
        stage_detail=job.get("stage_detail"),
        video_path=job.get("video_path"),
        message=job.get("message"),
    )


@app.get("/health")
def health_check():
    return {"status": "ok", "render_mode": RENDER_MODE}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
