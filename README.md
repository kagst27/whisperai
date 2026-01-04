# Whisper Local Voice Memo Transcriber

This project transcribes voice memos using **local** OpenAI Whisper and writes the output to an HTML file.
It is designed for Windows and works well with Google Drive–synced folders.

## Features
- Local Whisper transcription (no API cost)
- Watches a folder for new audio files or runs one-off transcription
- Writes the transcript to an HTML file (future PDF export is easy to add)

## Prerequisites
- **Python 3.10+** installed
- **FFmpeg** installed and on your PATH
  - Windows install options: https://ffmpeg.org/download.html

## Setup
```bash
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -U pip
pip install -r requirements.txt
```

## Configuration
Copy `.env.example` to `.env` and edit paths:
```bash
copy .env.example .env
```

Example `.env` values for Windows:
```
INPUT_DIR=G:\\VoiceMemo
OUTPUT_DIR=G:\\VoiceMemo\\transcripts
MODEL_NAME=base
WATCH_MODE=true
IPHONE_SUBDIR=transcript_iphone
COMPARE_OUTPUT_DIR=G:\\VoiceMemo\\transcripts\\comparisons
```

### Audio file types
The watcher and one-off command support: `.m4a`, `.mp3`, `.wav`, `.mp4`.

## Usage
### Watch a folder for new audio
```bash
python transcribe.py
```

### One-off transcription
```bash
python transcribe.py --file "G:\\VoiceMemo\\my_memo.m4a"
```

## Output
Each transcript is written as `*.html` in the output folder. Example:
```
G:\VoiceMemo\transcripts\my_memo.html
```

## Compare transcripts (original vs. iPhone)
Place your original transcripts in `OUTPUT_DIR` and the iPhone copy/pasted versions in
`OUTPUT_DIR\\transcript_iphone`. The iPhone versions should use the same base filename,
ending in `_iphone` and saved as `.txt` (for example: `idea.html` and `idea_iphone.txt`).

Generate comparisons:
```bash
python compare_transcripts.py
```

Custom directories:
```bash
python compare_transcripts.py --transcripts-dir "G:\\VoiceMemo\\transcripts" --iphone-dir "G:\\VoiceMemo\\transcripts\\transcript_iphone" --output-dir "G:\\VoiceMemo\\transcripts\\comparisons"
```

Comparison reports are written as `*_comparison.html` files in `COMPARE_OUTPUT_DIR`.

## Notes
- Larger Whisper models are slower but more accurate. Edit `MODEL_NAME` in `.env` as needed.
- Google Drive–synced folders are supported as long as the files are fully downloaded locally.
