import argparse
import difflib
import html
import os
from html.parser import HTMLParser
from pathlib import Path

from dotenv import load_dotenv


TEXT_EXTENSIONS = {".txt", ".md"}
HTML_EXTENSIONS = {".html", ".htm"}
SUPPORTED_EXTENSIONS = TEXT_EXTENSIONS | HTML_EXTENSIONS


class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        if data:
            self.parts.append(data)

    def get_text(self) -> str:
        return html.unescape("".join(self.parts))


def load_config():
    load_dotenv()
    output_dir = Path(os.getenv("OUTPUT_DIR", "G:\\VoiceMemo\\transcripts"))
    iphone_subdir = os.getenv("IPHONE_SUBDIR", "transcript_iphone")
    compare_output = os.getenv("COMPARE_OUTPUT_DIR", str(output_dir / "comparisons"))
    return output_dir, iphone_subdir, Path(compare_output)


def read_transcript(path: Path) -> str:
    content = path.read_text(encoding="utf-8")
    if path.suffix.lower() in HTML_EXTENSIONS:
        parser = HTMLTextExtractor()
        parser.feed(content)
        return parser.get_text()
    return content


def find_matching_transcript(transcripts_dir: Path, base_name: str) -> Path | None:
    for extension in SUPPORTED_EXTENSIONS:
        candidate = transcripts_dir / f"{base_name}{extension}"
        if candidate.exists():
            return candidate
    return None


def build_diff(original_path: Path, iphone_path: Path) -> str:
    original_text = read_transcript(original_path)
    iphone_text = read_transcript(iphone_path)
    diff_lines = list(
        difflib.unified_diff(
            original_text.splitlines(),
            iphone_text.splitlines(),
            fromfile=str(original_path),
            tofile=str(iphone_path),
            lineterm="",
        )
    )
    if not diff_lines:
        return "No differences found."
    return "\n".join(diff_lines)


def compare_transcripts(transcripts_dir: Path, iphone_dir: Path, compare_output_dir: Path) -> int:
    if not transcripts_dir.exists():
        raise FileNotFoundError(f"Transcripts directory not found: {transcripts_dir}")
    if not iphone_dir.exists():
        raise FileNotFoundError(f"iPhone transcripts directory not found: {iphone_dir}")

    compare_output_dir.mkdir(parents=True, exist_ok=True)

    iphone_files = [path for path in iphone_dir.iterdir() if path.suffix.lower() in SUPPORTED_EXTENSIONS]
    if not iphone_files:
        print(f"No transcript files found in {iphone_dir}")
        return 1

    compared = 0
    for iphone_path in sorted(iphone_files):
        stem = iphone_path.stem
        if not stem.endswith("_iphone"):
            print(f"Skipping (missing _iphone suffix): {iphone_path.name}")
            continue
        base_name = stem[: -len("_iphone")]
        original_path = find_matching_transcript(transcripts_dir, base_name)
        if not original_path:
            print(f"Missing original transcript for {iphone_path.name}")
            continue

        diff_text = build_diff(original_path, iphone_path)
        output_path = compare_output_dir / f"{base_name}_comparison.txt"
        output_path.write_text(diff_text, encoding="utf-8")
        compared += 1
        print(f"Wrote comparison for {base_name}: {output_path}")

    if compared == 0:
        print("No matching transcript pairs were found.")
        return 1
    return 0


def main():
    parser = argparse.ArgumentParser(description="Compare original transcripts to iPhone transcripts.")
    parser.add_argument(
        "--transcripts-dir",
        help="Directory that contains the original transcripts",
    )
    parser.add_argument(
        "--iphone-dir",
        help="Directory containing iPhone transcripts (default: <transcripts>/transcript_iphone)",
    )
    parser.add_argument(
        "--output-dir",
        help="Directory to write comparison reports",
    )
    args = parser.parse_args()

    transcripts_dir, iphone_subdir, compare_output_dir = load_config()
    if args.transcripts_dir:
        transcripts_dir = Path(args.transcripts_dir)
    if args.iphone_dir:
        iphone_dir = Path(args.iphone_dir)
    else:
        iphone_dir = transcripts_dir / iphone_subdir
    if args.output_dir:
        compare_output_dir = Path(args.output_dir)

    exit_code = compare_transcripts(transcripts_dir, iphone_dir, compare_output_dir)
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
