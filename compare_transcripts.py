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
IPHONE_EXTENSIONS = {".txt"}


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


def build_diff_html(original_path: Path, iphone_path: Path) -> str:
    original_text = read_transcript(original_path)
    iphone_text = read_transcript(iphone_path)
    differ = difflib.HtmlDiff(wrapcolumn=80)
    diff_table = differ.make_table(
        original_text.splitlines(),
        iphone_text.splitlines(),
        fromdesc=str(original_path),
        todesc=str(iphone_path),
        context=True,
        numlines=2,
    )
    has_changes = original_text != iphone_text
    summary = "Differences detected." if has_changes else "No differences found."
    return (
        "<!doctype html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        "  <meta charset=\"utf-8\">\n"
        f"  <title>{html.escape(original_path.stem)} comparison</title>\n"
        "  <style>\n"
        "    body{font-family:Arial,Helvetica,sans-serif;max-width:1100px;margin:40px auto;line-height:1.5}\n"
        "    table.diff{font-family:Consolas,monospace;border:1px solid #ccc;width:100%;border-collapse:collapse}\n"
        "    .diff_header{background:#f0f0f0}\n"
        "    td,th{padding:4px 6px;border:1px solid #ddd;vertical-align:top}\n"
        "    .diff_add{background:#d1f7c4}\n"
        "    .diff_chg{background:#fff3b0}\n"
        "    .diff_sub{background:#ffd1d1}\n"
        "  </style>\n"
        "</head>\n"
        "<body>\n"
        f"  <h1>{html.escape(original_path.stem)} comparison</h1>\n"
        f"  <p>{html.escape(summary)}</p>\n"
        f"{diff_table}\n"
        "</body>\n"
        "</html>\n"
    )


def compare_transcripts(transcripts_dir: Path, iphone_dir: Path, compare_output_dir: Path) -> int:
    if not transcripts_dir.exists():
        raise FileNotFoundError(f"Transcripts directory not found: {transcripts_dir}")
    if not iphone_dir.exists():
        raise FileNotFoundError(f"iPhone transcripts directory not found: {iphone_dir}")

    compare_output_dir.mkdir(parents=True, exist_ok=True)

    iphone_files = [path for path in iphone_dir.iterdir() if path.suffix.lower() in IPHONE_EXTENSIONS]
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

        diff_html = build_diff_html(original_path, iphone_path)
        output_path = compare_output_dir / f"{base_name}_comparison.html"
        output_path.write_text(diff_html, encoding="utf-8")
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
