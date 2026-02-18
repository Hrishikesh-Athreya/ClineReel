"""
elevenlabs.py - Simple ElevenLabs TTS API client.

Generates MP3 voiceover audio from text using the ElevenLabs REST API.
"""

import os
import requests

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")
ELEVENLABS_MODEL = "eleven_turbo_v2_5"
ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"


def generate_voiceover(text: str) -> bytes:
    """
    Generate MP3 audio bytes from text using ElevenLabs TTS.

    Args:
        text: The text to convert to speech.

    Returns:
        Raw MP3 audio bytes.

    Raises:
        ValueError: If API key is not configured.
        requests.HTTPError: If the API request fails.
    """
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY environment variable is not set")

    url = f"{ELEVENLABS_BASE_URL}/text-to-speech/{ELEVENLABS_VOICE_ID}"

    response = requests.post(
        url,
        headers={
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
        json={
            "text": text,
            "model_id": ELEVENLABS_MODEL,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
            },
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.content
