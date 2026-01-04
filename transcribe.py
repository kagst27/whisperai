import argparse
import html
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import whisper

AUDIO_EXTENSIONS = {".m4a", ".mp3", ".wav", ".mp4"}


def load_config():
    load_dotenv()
    input_dir = os.getenv("INPUT_DIR", "G:\\VoiceMemo")
    output_dir = os.getenv("OUTPUT_DIR", "G:\\VoiceMemo\\transcripts")
    model_name = os.getenv("MODEL_NAME", "base")
    watch_mode = os.getenv("WATCH_MODE", "true").lower() == "true"
    return Path(input_dir), Path(output_dir), model_name, watch_mode


def render_html(title: str, text: str) -> str:
    safe_text = html.escape(text)
    return (
        "<!doctype html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        f"  <meta charset=\"utf-8\">\n  <title>{html.escape(title)}</title>\n"
        "  <style>body{font-family:Arial,Helvetica,sans-serif;max-width:900px;"
        "margin:40px auto;line-height:1.6}pre{white-space:pre-wrap}</style>\n"
        "</head>\n"
        "<body>\n"
        f"  <h1>{html.escape(title)}</h1>\n"
        f"  <pre>{safe_text}</pre>\n"
        "</body>\n"
        "</html>\n"
    )


def transcribe_file(model, audio_path: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    result = model.transcribe(str(audio_path))
    html_content = render_html(audio_path.stem, result["text"])
    output_path = output_dir / f"{audio_path.stem}.html"
    output_path.write_text(html_content, encoding="utf-8")
    return output_path


class MemoHandler(FileSystemEventHandler):
    def __init__(self, model, output_dir: Path):
        self.model = model
        self.output_dir = output_dir

    def on_created(self, event):
        if event.is_directory:
            return
        audio_path = Path(event.src_path)
        if audio_path.suffix.lower() not in AUDIO_EXTENSIONS:
            return
        print(f"Transcribing {audio_path}...")
        output_path = transcribe_file(self.model, audio_path, self.output_dir)
        print(f"Wrote {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Transcribe voice memos locally with Whisper.")
    parser.add_argument("--file", help="Transcribe a single audio file")
    args = parser.parse_args()

    input_dir, output_dir, model_name, watch_mode = load_config()

    print(f"Loading Whisper model '{model_name}'...")
    model = whisper.load_model(model_name)

    if args.file:
        audio_path = Path(args.file)
        if not audio_path.exists():
            print(f"File not found: {audio_path}")
            sys.exit(1)
        output_path = transcribe_file(model, audio_path, output_dir)
        print(f"Wrote {output_path}")
        return

    if not watch_mode:
        print("WATCH_MODE is false and no --file provided. Nothing to do.")
        return

    if not input_dir.exists():
        print(f"Input directory does not exist: {input_dir}")
        sys.exit(1)

    event_handler = MemoHandler(model, output_dir)
    observer = Observer()
    observer.schedule(event_handler, str(input_dir), recursive=False)
    observer.start()
    print(f"Watching {input_dir} for new memos...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


if __name__ == "__main__":
    main()
