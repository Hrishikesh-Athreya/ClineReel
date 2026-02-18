"""
assets.py - Download and place assets locally for Remotion rendering.
"""
import os
import re
import shutil
import requests
from urllib.parse import urlparse


def upload_dynamic_assets(project_dir, props_data):
    """
    Traverses props_data to find image URLs, downloads them to the local
    Remotion project's public/ directory, and updates the JSON to use local filenames.
    """
    if not isinstance(props_data, dict):
        return

    def process_node(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if isinstance(v, (dict, list)):
                    process_node(v)
                elif k in ["src", "image", "url"]:
                    if isinstance(v, str) and len(v) < 5:
                        continue

                    if not v or (isinstance(v, str) and not v.strip()):
                        print(f"   Warning: Found empty {k}, using placeholder")
                        v = "https://placehold.co/1920x1080/CCCCCC/666666.png?text=No+Image+Available"
                        node[k] = v

                    if isinstance(v, str):
                        if v.startswith("//"):
                            v = "https:" + v

                        if v.startswith("http://") or v.startswith("https://"):
                            new_val = upload_single_asset(project_dir, v)
                            if new_val:
                                node[k] = new_val
                        else:
                            print(f"   Warning: Found invalid asset source '{v}', replacing with placeholder")
                            v = "https://placehold.co/1920x1080/CCCCCC/666666.png?text=Placeholder"
                            new_val = upload_single_asset(project_dir, v)
                            if new_val:
                                node[k] = new_val

        elif isinstance(node, list):
            for item in node:
                process_node(item)

    process_node(props_data)


def upload_single_asset(project_dir, url):
    """
    Downloads an image from a URL and saves it to {project_dir}/public/.
    Returns the filename on success, None on failure.
    """
    try:
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)
        if not filename or "." not in filename:
            filename = f"asset_{abs(hash(url))}.png"

        filename = re.sub(r'[^a-zA-Z0-9_.-]', '', filename)

        # Fallback: minimal valid 1x1 gray PNG
        valid_png_bytes = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
            b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00'
            b'\x00\x00\x0cIDATx\x9cc`\x00\x00\x00\x02\x00\x01'
            b'\x2e\x1b\xe0\x1c\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        content = valid_png_bytes

        if url.startswith("http"):
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                r = requests.get(url, headers=headers, timeout=10)
                if r.status_code == 200 and len(r.content) > 100:
                    is_png = r.content.startswith(b'\x89PNG')
                    is_jpg = r.content.startswith(b'\xff\xd8')
                    if is_png or is_jpg:
                        content = r.content
                        print(f"   Downloaded valid image ({len(content)} bytes)")
                    else:
                        print(f"   Warning: Not PNG/JPG, using fallback")
                else:
                    print(f"   Warning: Download failed ({r.status_code}), using placeholder")
            except Exception as e:
                print(f"   Warning: Download error ({e}), using placeholder")

        # Save to public/
        public_dir = os.path.join(project_dir, "public")
        os.makedirs(public_dir, exist_ok=True)
        local_path = os.path.join(public_dir, filename)
        with open(local_path, "wb") as f:
            f.write(content)
        print(f"   Saved asset to {local_path}")

        # Also save to public/public/ for staticFile path ambiguity
        nested_dir = os.path.join(public_dir, "public")
        os.makedirs(nested_dir, exist_ok=True)
        nested_path = os.path.join(nested_dir, filename)
        with open(nested_path, "wb") as f:
            f.write(content)

        return filename

    except Exception as e:
        print(f"   Asset save error: {e}")
    return None


def upload_standard_assets(project_dir, props_data=None):
    """
    Downloads standard placeholder assets AND dynamic assets to the local project.
    """
    assets = {
        "studio_ui.png": "https://placehold.co/1920x1080/1E88E5/FFFFFF.png?text=MotionForge+Studio+UI",
        "export_feature.png": "https://placehold.co/1920x1080/42A5F5/FFFFFF.png?text=Export+Feature",
        "analytics.png": "https://placehold.co/1920x1080/66BB6A/FFFFFF.png?text=Analytics+Dashboard",
    }

    print("Uploading standard assets...")
    public_dir = os.path.join(project_dir, "public")
    os.makedirs(public_dir, exist_ok=True)

    for filename, url in assets.items():
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                with open(os.path.join(public_dir, filename), "wb") as f:
                    f.write(r.content)
        except Exception:
            pass

    if props_data:
        print("Processing dynamic assets from props...")
        upload_dynamic_assets(project_dir, props_data)
