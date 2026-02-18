import json
import os
from openai import OpenAI
from pydantic import BaseModel
from .schemas import AnalystOutput, DirectorOutput, ShowcaseProps, VideoStoryboard
import sys

# Load env
from dotenv import load_dotenv
load_dotenv()

_client = None

def get_client():
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


class Agents:
    
    @staticmethod
    def analyze(raw_context: dict) -> AnalystOutput:
        print("🤖 Analyst Agent reasoning...")
        context_str = json.dumps(raw_context, default=str)
        # Truncate to safety limit (approx 30k chars is fine for GPT-4o but let's be safe)
        if len(context_str) > 30000:
            context_str = context_str[:30000] + "...(truncated)"
            
        print(f"Analyzing context length: {len(context_str)}")
        
        system_prompt = "You are a Senior Tech Journalist. Extract the core value proposition from this hackathon project. Ignore marketing fluff. Focus on the Problem (Hook), Solution, and Tech Stack."
        
        try:
            completion = get_client().beta.chat.completions.parse(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context_str},
                ],
                response_format=AnalystOutput,
            )
            parsed = completion.choices[0].message.parsed
            if not parsed:
                raise ValueError("Analyst returned no content")
            return parsed
        except Exception as e:
            print(f"❌ Analyst Error: {e}")
            # Retry with heavy truncation if 400
            if "context_length_exceeded" in str(e) or "400" in str(e):
                 print("Retrying with truncated context...")
                 truncated = context_str[:10000]
                 completion = get_client().beta.chat.completions.parse(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a Senior Tech Journalist. Extract the core value proposition."},
                        {"role": "user", "content": truncated},
                    ],
                    response_format=AnalystOutput,
                )
                 return completion.choices[0].message.parsed
            raise e

    @staticmethod
    def direct(project_title: str, analysis: AnalystOutput, available_images: list[str] = None) -> DirectorOutput:
        print("🎨 Director Agent designing...")
        
        system_prompt = """You are a Creative Director and Copywriter for a high-impact promo video.
Your goal is to translate the project details into a JSON configuration for a video template.

---
# PROMO VIDEO GUIDE

## Tone & Style
- **Problem**: Hook the viewer immediately. Create tension. Typewriter effect.
- **Solution**: The "Aha!" moment. Bold headline. 
- **Aesthetics**: Choose colors that match the industry.

## Constraints (STRICT)
- **Product Name**: Max 10 chars. Use ALL CAPS.
- **Problem Line 1**: Max 40 chars.
- **Problem Line 2**: Max 25 chars.
- **Solution Headline**: Max 45 chars.
- **Badge**: Use emojis for icons.

## Colors
- Return valid Hex codes (e.g. #FF0000).
- Ensure high contrast between text and background.

## Assets
- You have access to a list of 'Available Images' (scraped from the project).
- PLEASE USE THESE URLs for the 'src' fields in 'screenshots' if they are relevant.
- If no images are available, USE A PLACEHOLDER URL (e.g. from placehold.co).
- DO NOT leave 'src' empty.
- DO NOT invent filenames like "dashboard.png" unless you are sure they exist or are placeholders.
- Prefer using the full URL from 'Available Images'.

---

Generate the JSON configuration based on the provided Analysis.
"""
        
        
        user_content = f"Project Title: {project_title}\n\nAnalysis: {analysis.model_dump_json()}\n\nAvailable Images: {available_images}"
        
        completion = get_client().beta.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            response_format=DirectorOutput,
        )
        
        parsed = completion.choices[0].message.parsed
        # Save debug
        with open("outputs/last_director_response.json", "w") as f:
            f.write(completion.choices[0].message.content or "")

        return parsed

    @staticmethod
    def storyboard(
        product_name: str,
        analysis: AnalystOutput,
        available_images: list[str] = None,
        website_description: str = "",
        features: list[str] = None,
    ) -> VideoStoryboard:
        """
        Creative Director agent for agentic mode.
        Produces a free-form video storyboard (not tied to any template).
        """
        print("🎬 Creative Director Agent designing storyboard...")

        system_prompt = """You are a world-class Creative Director and Motion Designer.
Your job: design an original, visually stunning promotional video storyboard.

You are NOT filling in a template. You are creating a video concept from scratch.
A Remotion developer will implement your vision, so be specific about visuals and animations.

## Guidelines

**Story Arc**: Every great promo follows a narrative:
1. HOOK — grab attention in the first 2 seconds (bold statement, visual surprise)
2. PROBLEM/CONTEXT — why does this product exist?
3. SOLUTION/SHOWCASE — what does it do? Show features visually.
4. PROOF/DETAILS — key features, how it works, or social proof
5. CTA — memorable close with a call to action

**Visual Design**: Think like a motion designer, not a slide deck maker:
- Use interesting layouts: split-screen, cards, asymmetric, overlapping elements
- Background: gradients, subtle patterns, floating shapes, NOT just solid colors
- Typography: big bold headlines, small elegant subtexts, animated entrances
- Color: pick a cohesive palette that matches the brand/industry

**Animation Ideas**: Be specific:
- "Text fades up word-by-word with 100ms stagger"
- "Cards slide in from left with spring physics"
- "Background gradient slowly rotates 360 degrees"
- "Logo pulses with a glow effect"
- "Feature icons pop in one by one with scale spring"

**Scene Descriptions**: For each scene, describe:
- What the viewer SEES (layout, elements, colors)
- What TEXT is displayed (headlines, subtext)
- How things MOVE (animations, transitions)
- The MOOD/FEEL of that moment

**Voiceover & Audio**:
- For EACH scene, write a `voiceover_script`: a short, punchy narration (1-2 sentences, 50-150 characters).
  - Use conversational, active voice. Speak directly to the viewer.
  - Example: "Tired of slow dashboards? Meet Bolt — your data, instantly."
- Choose a `background_music_style` that matches the product's energy:
  - "upbeat" for fun/energetic products
  - "calm" for productivity/wellness tools
  - "dramatic" for security/enterprise products
  - "corporate" for B2B/SaaS products
  - "none" if music would distract
- IMPORTANT: Each scene's `duration_seconds` must be long enough for the voiceover to finish
  plus ~1 second of breathing room. A 2-second scene is too short for most voiceovers —
  aim for at least 3-5 seconds per scene.

**Practical Constraints**:
- Total video: 15-25 seconds (30fps, so 450-750 frames)
- Resolution: 1920x1080
- Use system fonts only (system-ui, -apple-system, sans-serif)
- Available libraries: remotion, react, @remotion/transitions
- Images must come from the provided URLs list (will be downloaded to public/)
- If no good images available, design with typography, shapes, and color instead

Generate a storyboard that would make this product look amazing."""

        features_str = ""
        if features:
            features_str = "\n".join(f"- {f}" for f in features)

        images_str = "None available — design with typography and shapes"
        if available_images:
            images_str = "\n".join(f"- {img}" for img in available_images)

        user_content = f"""Product: {product_name}

Analysis:
- Hook: {analysis.hook}
- Solution: {analysis.solution}
- Tech Stack: {analysis.stack}

Description:
{website_description}

Key Features:
{features_str or "Not specified — infer from description"}

Available Images:
{images_str}"""

        completion = get_client().beta.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            response_format=VideoStoryboard,
        )

        parsed = completion.choices[0].message.parsed
        if not parsed:
            raise ValueError("Creative Director returned no storyboard")

        # Save debug
        with open("outputs/last_storyboard.json", "w") as f:
            f.write(completion.choices[0].message.content or "")

        return parsed
