from pydantic import BaseModel, Field
from typing import List, Optional, Literal

# --- Intermediate Agent Schemas ---

class AnalystOutput(BaseModel):
    hook: str = Field(..., description="The core problem or 'hook' of the project")
    solution: str = Field(..., description="What the app does to solve the problem")
    stack: str = Field(..., description="The key technologies used (Secret Sauce)")

# Director Output (Visual Direction)
class Logo(BaseModel):
    icon: Literal["pulse", "rocket", "chart", "bolt"]
    primaryColor: str = Field(..., description="Main brand color hex code")
    secondaryColor: str = Field(..., description="Gradient end color hex code")

class Product(BaseModel):
    name: str = Field(..., max_length=10, description="Product name (ALL CAPS preferred)")
    tagline: str = Field(..., max_length=50, description="Short descriptor shown below logo")
    logo: Logo

class Problem(BaseModel):
    line1: str = Field(..., max_length=40, description="First line (setup)...")
    line2: str = Field(..., max_length=25, description="Punch line (impact)")
    accentColor: str = Field(..., description="Color for impact line hex code")

class Solution(BaseModel):
    headline: str = Field(..., max_length=45, description="Main solution statement")
    subline: str = Field(..., max_length=30, description="Supporting detail or benefit")

class Callout(BaseModel):
    icon: str = Field(..., description="Single emoji")
    text: str = Field(..., max_length=30, description="Feature description")

class Screenshot(BaseModel):
    src: str = Field(..., description="Filename (e.g. 'dashboard.png')")
    callouts: List[Callout] = Field(..., max_length=3)

class Badge(BaseModel):
    icon: str = Field(..., description="Single emoji")
    text: str = Field(..., max_length=35)
    color: str = Field(..., description="Badge accent color hex code")

class Outro(BaseModel):
    tagline: str = Field(..., max_length=40, description="Final CTA or memorable phrase")
    badge: Optional[Badge] = Field(None, description="Optional award badge, set to null if none")

class Theme(BaseModel):
    primary: str = Field(..., description="Hex code")
    accent: str = Field(..., description="Hex code")
    background: str = Field(..., description="Hex code")
    text: str = Field(..., description="Hex code")

class DirectorOutput(BaseModel):
    product: Product
    problem: Problem
    solution: Solution
    screenshots: List[Screenshot] = Field(..., min_length=1, max_length=2, description="1-2 screenshots")
    outro: Outro
    theme: Theme


# --- Final Output Schema (Remotion Props) ---

class ShowcaseProps(BaseModel):
    config: DirectorOutput


# --- Agentic Mode: Storyboard Schema (free-form, not tied to template) ---

class SceneDescription(BaseModel):
    scene_number: int = Field(..., description="Scene order (1, 2, 3, ...)")
    scene_name: str = Field(..., description="Short name like 'Hero', 'Problem', 'Features'")
    duration_seconds: float = Field(..., description="How long this scene lasts (2-8 seconds)")
    headline_text: str = Field(..., description="Primary text shown in this scene")
    supporting_text: str = Field("", description="Secondary/subtext if any")
    visual_concept: str = Field(
        ...,
        description=(
            "Detailed visual description: layout, colors, shapes, background style, "
            "image placement, animation ideas. Be specific enough for a developer to implement."
        ),
    )
    animation_notes: str = Field(
        "",
        description="Specific animation ideas: entrances, exits, motion, timing",
    )


class VideoStoryboard(BaseModel):
    product_name: str = Field(..., description="The product/website name")
    video_concept: str = Field(
        ...,
        description=(
            "One-paragraph creative concept for the whole video. "
            "What story does it tell? What's the visual theme?"
        ),
    )
    color_palette: List[str] = Field(
        ...,
        min_length=3,
        max_length=6,
        description="Hex color codes for the video (primary, accent, background, text, etc.)",
    )
    total_duration_seconds: float = Field(
        ..., description="Total video length in seconds (15-25 recommended)"
    )
    scenes: List[SceneDescription] = Field(
        ..., min_length=3, max_length=7, description="Ordered list of scenes"
    )
    image_urls: List[str] = Field(
        default_factory=list,
        description="URLs of images to download and use (logos, screenshots, etc.)",
    )
    closing_cta: str = Field(..., description="Final call-to-action text")
