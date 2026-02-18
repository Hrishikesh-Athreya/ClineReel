import sys
import os
import json
from .schemas import ShowcaseProps
from .agents import Agents
from .scraper import scrape_url

def orchestrate_pipeline(url: str) -> ShowcaseProps:
    """
    Runs the agent pipeline: Scrape -> Analyze -> Direct -> Props.
    Returns the ShowcaseProps object.
    Raises exceptions on failure.
    """
    # 1. Ingestion
    print(f"📥 Starting Ingestion for {url}...")
    raw_data = scrape_url(url)
    if not raw_data:
        raise ValueError("Scraping failed: Could not retrieve data from Website.")

    print(f"[pipeline] Scrape result: title='{raw_data.get('title')}', "
          f"source={raw_data.get('source')}, "
          f"desc_len={len(raw_data.get('description', ''))}, "
          f"gallery={len(raw_data.get('gallery', []))}")

    # 2. Analyst
    try:
        analysis = Agents.analyze(raw_data)
        print(f"✅ Analysis Hook: {analysis.hook}")
        print(f"[pipeline] Analysis Solution: {analysis.solution[:100]}")
    except Exception as e:
        raise RuntimeError(f"Analysis failed: {e}")

    # 3. Director
    project_title = raw_data.get("title", "Hackathon Project")
    gallery_images = raw_data.get("gallery", [])
    print(f"[pipeline] Directing: title='{project_title}', images={gallery_images}")
    try:
        direction = Agents.direct(project_title, analysis, gallery_images)
        print(f"✅ Direction Product: {direction.product.name}")
    except Exception as e:
        raise RuntimeError(f"Direction failed: {e}")

    # 4. Finalize Props
    print("🎬 Finalizing Video Configuration...")
    showcase_props = ShowcaseProps(config=direction)

    # Save scraped context for agentic mode to pick up
    try:
        os.makedirs("outputs", exist_ok=True)
        with open("outputs/last_scraped_context.json", "w") as f:
            # Save a clean version without huge markdown blobs
            ctx = {k: v for k, v in raw_data.items() if k != "raw_browse_data"}
            json.dump(ctx, f, indent=2, default=str)
    except Exception:
        pass

    return showcase_props

def main(url: str):
    try:
        props = orchestrate_pipeline(url)
        
        # Output
        output_path = "showcase-props.json"
        with open(output_path, "w") as f:
            f.write(props.model_dump_json(indent=2))
            
        print(f"🎉 Success! Props saved to {os.path.abspath(output_path)}")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pipeline.py <url>")
        sys.exit(1)
        
    url = sys.argv[1]
    main(url)
