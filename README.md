# Screenshot Notes Processor

Processes a folder of iPhone screenshots using Gemini 2.5 Flash. For each image it extracts a structured summary — source type, title, and notes — and writes everything to a single timestamped text file per run.

---

## How it works

1. Drop screenshots into the `inbox/` folder.
2. Run the script.
3. Each screenshot is sent to Gemini 2.5 Flash with a structured extraction prompt.
4. Results are written to `output/notes_YYYY-MM-DD_HH-MM.txt`.
5. Processed images are moved to `inbox/processed/` (or deleted if `DELETE_AFTER = True`).

---

## Setup

**Requirements:** Python 3.10+

```bash
pip install google-generativeai Pillow
```

**API key**

Copy `.env.example` to `.env` and add your Gemini API key:

```bash
cp .env.example .env
```

Then either load the `.env` file with a tool like `python-dotenv`, or export the variable directly:

```bash
export GEMINI_API_KEY=your_api_key_here
```

Get a key at [aistudio.google.com](https://aistudio.google.com).

---

## Configuration

All configurable options are at the top of `main.py`:

| Variable | Default | Description |
|---|---|---|
| `INBOX_FOLDER` | `inbox/` | Folder to watch for screenshots |
| `PROCESSED_FOLDER` | `inbox/processed/` | Where processed images are moved |
| `OUTPUT_FOLDER` | `output/` | Where notes files are written |
| `DELETE_AFTER` | `False` | Delete originals instead of moving them |
| `WORKERS` | `10` | Max screenshots per run |

For macOS with iCloud or Google Drive sync, point `INBOX_FOLDER` directly at your sync folder, for example:

```python
INBOX_FOLDER = Path.home() / "Desktop" / "Notes To-Do"
```

---

## Output format

```
SCREENSHOT NOTES
Generated : 2025-01-15 14:30
Count     : 3 screenshots

────────────────────────────────────────────────────────────
[1] Title of the screenshot
    File   : IMG_0042.png
    Type   : article
────────────────────────────────────────────────────────────

  SUMMARY
  Two to four sentence summary of what the screenshot contains.

  NOTES
  Any additional context extracted from the image.
```

---

## Supported formats

`.png`, `.jpg`, `.jpeg`, `.heic`, `.webp`

---

## License

MIT
