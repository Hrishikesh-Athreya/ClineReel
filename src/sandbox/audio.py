"""
audio.py - Audio generation orchestrator.

Generates per-scene voiceover MP3s via ElevenLabs and copies bundled
background music into the Remotion project's public/ directory.
"""

import os
import shutil

from src.agents.elevenlabs import generate_voiceover

# Directory containing bundled background music loops
_MUSIC_DIR = os.path.join(os.path.dirname(__file__), "music")

# Mapping from style name to bundled filename
_MUSIC_FILES = {
    "upbeat": "background_upbeat.mp3",
    "calm": "background_calm.mp3",
    "dramatic": "background_dramatic.mp3",
    "corporate": "background_corporate.mp3",
}


def generate_scene_voiceovers(storyboard, output_dir: str) -> list[dict]:
    """
    Generate voiceover MP3 files for each scene that has a voiceover_script.

    Args:
        storyboard: A VideoStoryboard (pydantic model or dict).
        output_dir: Directory to write MP3 files (typically work_dir/public/).

    Returns:
        List of metadata dicts: [{scene_number, filename, duration_estimate, script}, ...]
    """
    os.makedirs(output_dir, exist_ok=True)

    if hasattr(storyboard, "model_dump"):
        sb = storyboard.model_dump()
    else:
        sb = storyboard

    scenes = sb.get("scenes", [])
    audio_metadata = []

    for scene in scenes:
        script = scene.get("voiceover_script", "").strip()
        scene_num = scene.get("scene_number", 0)

        if not script:
            continue

        filename = f"voiceover_scene_{scene_num}.mp3"
        filepath = os.path.join(output_dir, filename)

        try:
            print(f"[audio] Generating voiceover for Scene {scene_num}: \"{script[:60]}...\"")
            audio_bytes = generate_voiceover(script)
            with open(filepath, "wb") as f:
                f.write(audio_bytes)

            # Rough duration estimate: ~150 words/min, average 5 chars/word
            word_count = len(script.split())
            duration_estimate = round(word_count / 2.5, 1)  # seconds

            audio_metadata.append({
                "scene_number": scene_num,
                "filename": filename,
                "duration_estimate": duration_estimate,
                "script": script,
            })
            print(f"[audio] Scene {scene_num} voiceover saved: {filename}")

        except Exception as e:
            print(f"[audio] Warning: Failed to generate voiceover for Scene {scene_num}: {e}")
            # Graceful fallback — scene simply has no voiceover

    return audio_metadata


def prepare_background_music(music_style: str, output_dir: str) -> str | None:
    """
    Copy a bundled background music loop into the output directory.

    Args:
        music_style: One of "upbeat", "calm", "dramatic", "corporate", "none".
        output_dir: Directory to copy the MP3 into (typically work_dir/public/).

    Returns:
        Filename of the copied music file, or None if style is "none".
    """
    if music_style == "none":
        return None

    os.makedirs(output_dir, exist_ok=True)

    source_filename = _MUSIC_FILES.get(music_style, _MUSIC_FILES["upbeat"])
    source_path = os.path.join(_MUSIC_DIR, source_filename)

    if not os.path.exists(source_path):
        print(f"[audio] Warning: Music file not found: {source_path}")
        return None

    dest_filename = "background_music.mp3"
    dest_path = os.path.join(output_dir, dest_filename)
    shutil.copy2(source_path, dest_path)
    print(f"[audio] Background music ({music_style}) copied: {dest_filename}")
    return dest_filename
