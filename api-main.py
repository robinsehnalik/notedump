"""
Screenshot → Text Notes Processor
Uses Gemini 2.5 Flash to extract structured notes from screenshots
and writes everything to a single readable text file.
"""
 
import json
import shutil
import time
from pathlib import Path
from datetime import datetime
import google.generativeai as genai
from PIL import Image
import sys
 
# ── CONFIG ──────────────────────────────────────────────────────────────────
 
GEMINI_API_KEY = "AIzaSyD0SWz44kd83Xj2e_GYNgpDdLnpA3LJnw8"
 
# Folder where your iCloud/Google Drive syncs screenshots to
INBOX_FOLDER = Path.home() / "/Users/robinsehnalik/Desktop/Notes To-Do"
 
# Processed screenshots move here (set DELETE_AFTER = True to delete instead)
PROCESSED_FOLDER = Path.home() / "/Users/robinsehnalik/Desktop/Notes To-Do/Processed"
DELETE_AFTER = False
 
# Output notes file — a new timestamped file is created per run
OUTPUT_FOLDER = Path.home() / "/Users/robinsehnalik/Desktop/Notes To-Do"

# Number of screenshots to process in parallel 
WORKERS = 10
 
# ────────────────────────────────────────────────────────────────────────────
 
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".heic", ".webp"}
 
EXTRACT_PROMPT = """
You are a screenshot summary assistant. You are given an iPhone screenshot.
Describe what the screenshot is about in a short, human-readable way.

Return ONLY valid JSON with this object structure and no other text:
{
  "source_type": "one of: reddit_post, reddit_comment, article, website, tweet, app, other",
  "title": "Short title or description of the screenshot",
  "summary": "2-4 sentence summary of the screenshot content and main point",
  "notes": "Optional additional details or useful context"
}

Rules:
- Use null for missing strings.
- Do not include URLs, usernames, tags, or any extra fields.
- Do not include markdown, fences, or explanations.
"""
 
 
def setup():
    INBOX_FOLDER.mkdir(parents=True, exist_ok=True)
    PROCESSED_FOLDER.mkdir(parents=True, exist_ok=True)
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
 
    if "YOUR_" in GEMINI_API_KEY:
        print("❌ Please set your GEMINI_API_KEY in the script.")
        sys.exit(1)
 
    genai.configure(api_key=GEMINI_API_KEY)
    print(f"✅ Gemini 2.5 Flash ready")
    print(f"✅ Inbox  : {INBOX_FOLDER}")
    print(f"✅ Output : {OUTPUT_FOLDER}")
 
 
def analyze_screenshot(image_path: Path) -> dict:
    model = genai.GenerativeModel("gemini-2.5-flash")
    image = Image.open(image_path)
 
    response = model.generate_content(
        [EXTRACT_PROMPT, image],
        generation_config={"temperature": 0.1}  # Low temp = precise, consistent output
    )
    raw = response.text.strip()
 
    # Strip markdown fences if model wraps its output
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
 
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print(f"  ⚠️  JSON parse failed, saving raw text")
        return {
            "source_type": "other",
            "title": f"Screenshot {image_path.name}",
            "summary": raw[:1000],
            "url": None,
            "url_clues": None,
            "action_items": [],
            "things_to_learn": [],
            "quotes": [],
            "links_mentioned": [],
            "tags": [],
            "needs_link": False
        }
 
 
def format_entry(data: dict, image_path: Path, index: int) -> str:
    """Format one screenshot's data as a clean readable text block."""
 
    divider = "─" * 60
    lines = []
 
    lines.append(f"\n{divider}")
    lines.append(f"[{index}] {data.get('title', image_path.name)}")
    lines.append(f"    File      : {image_path.name}")
    lines.append(f"    Type      : {data.get('source_type', 'unknown')}")
    lines.append(f"    Tags      : {', '.join(data.get('tags', [])) or '—'}")
 
    url = data.get("url")
    url_clues = data.get("url_clues")
    if url:
        lines.append(f"    URL       : {url}")
    elif url_clues:
        lines.append(f"    URL clues : {url_clues}  ⟵ needs link")
 
    lines.append(divider)
 
    summary = data.get("summary", "").strip()
    if summary:
        lines.append(f"\n  SUMMARY\n  {summary}\n")
 
    def section(label: str, items: list, emoji: str):
        if not items:
            return
        lines.append(f"  {emoji} {label}")
        for item in items:
            lines.append(f"     • {item}")
        lines.append("")
 
    section("ACTION ITEMS",       data.get("action_items", []),    "✅")
    section("THINGS TO LEARN",    data.get("things_to_learn", []), "📚")
    section("QUOTES & HIGHLIGHTS",data.get("quotes", []),          "💬")
    section("LINKS MENTIONED",    data.get("links_mentioned", []), "🔗")
 
    return "\n".join(lines)
 
 
def process_file(image_path: Path, index: int) -> str | None:
    print(f"  🔍 [{index}] {image_path.name}")
    try:
        data = analyze_screenshot(image_path)
        entry = format_entry(data, image_path, index)
 
        if DELETE_AFTER:
            image_path.unlink()
        else:
            dest = PROCESSED_FOLDER / image_path.name
            shutil.move(str(image_path), str(dest))
 
        return entry
 
    except Exception as e:
        print(f"  ❌ Error processing {image_path.name}: {e}")
        return None
 
 
def run():
    setup()
 
    images = sorted([
        f for f in INBOX_FOLDER.iterdir()
        if f.suffix.lower() in SUPPORTED_EXTENSIONS
    ])
 
    if not images:
        print("\n📭 No screenshots found in inbox.")
        return
 
    print(f"\n📥 Found {len(images)} screenshot(s) to process...\n")
 
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    output_file = OUTPUT_FOLDER / f"notes_{timestamp}.txt"
 
    header = (
        f"SCREENSHOT NOTES\n"
        f"Generated : {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        f"Count     : {len(images)} screenshots\n"
    )
 
    entries = [header]
 
    for i, image_path in enumerate(images, start=1):
        entry = process_file(image_path, i)
        if entry:
            entries.append(entry)
        time.sleep(0.3)  # Small delay to stay well within rate limits
 
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(entries))
        f.write("\n")
 
    print(f"\n✅ Done! Notes saved to:\n   {output_file}")
    print(f"   {len(entries) - 1} entries written.")
 
 
if __name__ == "__main__":
    run()