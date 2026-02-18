"""
scraper.py - Scrape a website for the Director Agent pipeline.

Uses Firecrawl (primary) with BrowserUse as fallback.
Returns a normalized dict: { title, tagline, description, gallery, raw_browse_data, source }
"""

import requests
import sys
import os
import json
from dotenv import load_dotenv

load_dotenv()

FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY")
FIRECRAWL_ENDPOINT = "https://api.firecrawl.dev/v1/scrape"

BROWSER_USE_API_KEY = "bu_lUvYypnKh8hsbNpKrYxpQKckPTHvcPIYlNaUnlT3XWg"
BROWSER_USE_ENDPOINT = "https://api.browser-use.com/api/v2/skills/d68e4535-36d8-402c-b637-79207245b916/execute"


def scrape_url(url: str) -> dict | None:
    """
    Scrape a website. Tries Firecrawl first, falls back to BrowserUse.
    Returns normalized dict or None on total failure.
    """
    # Try Firecrawl first
    if FIRECRAWL_API_KEY:
        result = _scrape_firecrawl(url)
        if result:
            return result
        print("[scraper] Firecrawl failed, trying BrowserUse fallback...")

    # Fallback to BrowserUse
    result = _scrape_browseruse(url)
    if result:
        return result

    print("[scraper] All scraping methods failed.")
    return None


def _scrape_firecrawl(url: str) -> dict | None:
    """Scrape using Firecrawl API. Returns normalized dict or None."""
    print(f"[scraper] Scraping {url} via Firecrawl...")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
    }
    payload = {
        "url": url,
        "formats": ["markdown", "extract"],
        "extract": {
            "schema": {
                "type": "object",
                "properties": {
                    "product_name": {"type": "string"},
                    "tagline": {"type": "string"},
                    "description": {"type": "string"},
                    "features": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "og_image": {"type": "string"},
                },
            }
        },
    }

    try:
        r = requests.post(FIRECRAWL_ENDPOINT, json=payload, headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()

        print(f"[scraper] Firecrawl response status: {data.get('success')}")

        if not data.get("success"):
            print(f"[scraper] Firecrawl error: {data.get('error', 'unknown')}")
            return None

        fc_data = data.get("data", {})
        metadata = fc_data.get("metadata", {})
        extract = fc_data.get("extract", {})
        markdown = fc_data.get("markdown", "")

        title = (
            extract.get("product_name")
            or metadata.get("og:title")
            or metadata.get("title")
            or ""
        )
        description = extract.get("description") or metadata.get("og:description") or ""
        tagline = extract.get("tagline") or metadata.get("description") or ""
        og_image = extract.get("og_image") or metadata.get("og:image") or ""

        # Build gallery from og_image + any images in metadata
        gallery = []
        if og_image:
            gallery.append(og_image)

        # Include markdown content as raw context for the analyst
        raw_data = {
            "metadata": metadata,
            "extract": extract,
            "markdown_preview": markdown[:5000] if markdown else "",
            "features": extract.get("features", []),
        }

        normalized = {
            "title": title or "Unknown Product",
            "tagline": tagline,
            "description": description + "\n\n" + "\n".join(extract.get("features", [])),
            "gallery": gallery,
            "raw_browse_data": raw_data,
            "source": "firecrawl",
        }

        print(f"[scraper] Scraped '{normalized['title']}' via Firecrawl")
        print(f"[scraper]   description length: {len(normalized['description'])}")
        print(f"[scraper]   gallery: {len(gallery)} images")
        print(f"[scraper]   markdown length: {len(markdown)}")

        # Validate we got meaningful content
        if len(normalized["description"].strip()) < 20 and len(markdown) < 100:
            print("[scraper] Warning: Firecrawl returned very little content")
            return None

        # Attach full markdown so analyst has rich context
        if markdown:
            normalized["raw_browse_data"]["full_markdown"] = markdown[:15000]

        return normalized

    except Exception as e:
        print(f"[scraper] Firecrawl error: {e}")
        if "r" in locals():
            print(f"[scraper] Response: {r.text[:500]}")
        return None


def _scrape_browseruse(url: str) -> dict | None:
    """Scrape using BrowserUse Skills API. Returns normalized dict or None."""
    print(f"[scraper] Scraping {url} via BrowserUse API...")

    headers = {
        "Content-Type": "application/json",
        "X-Browser-Use-API-Key": BROWSER_USE_API_KEY,
    }
    payload = {"parameters": {"url": url}}

    try:
        r = requests.post(BROWSER_USE_ENDPOINT, json=payload, headers=headers, timeout=60)
        r.raise_for_status()
        data = r.json()

        # Check for API-level failure
        if data.get("success") is False:
            print(f"[scraper] BrowserUse API error: {data.get('error', 'unknown')}")
            return None

        result = data
        if "result" in data and isinstance(data["result"], dict):
            result = data["result"]
        elif "output" in data and isinstance(data["output"], dict):
            result = data["output"]

        # Check we got actual content
        product_name = result.get("product_name", "")
        description = result.get("description", "")

        if not product_name and not description:
            print("[scraper] BrowserUse returned empty content")
            return None

        normalized = {
            "title": product_name or "Unknown Product",
            "tagline": result.get("tagline", ""),
            "description": (
                description
                + "\n\n"
                + result.get("problem", "")
                + "\n\n"
                + result.get("solution", "")
            ),
            "gallery": [result.get("og_image")] if result.get("og_image") else [],
            "raw_browse_data": result,
            "source": "browser-use",
        }

        print(f"[scraper] Scraped '{normalized['title']}' via BrowserUse")
        return normalized

    except Exception as e:
        print(f"[scraper] BrowserUse error: {e}")
        if "r" in locals():
            print(f"[scraper] Response: {r.text[:500]}")
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m src.agents.scraper <url>")
    else:
        data = scrape_url(sys.argv[1])
        if data:
            # Print without raw markdown for readability
            display = {k: v for k, v in data.items() if k != "raw_browse_data"}
            print(json.dumps(display, indent=2, default=str))
            print(f"\nraw_browse_data keys: {list(data.get('raw_browse_data', {}).keys())}")
        else:
            print("Scraping failed completely.")
