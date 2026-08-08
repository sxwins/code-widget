"""md_to_pdf.py — Convert a Markdown file to PDF via WeasyPrint.

Usage:
    uv run python tools/md_to_pdf.py docs/cn/01_业务需求.md
    uv run python tools/md_to_pdf.py docs/cn/01_业务需求.md -o output/01_业务需求.pdf
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import markdown
import weasyprint

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC&family=Noto+Sans+JP&display=swap');

@page {
    size: A4;
    margin: 25mm 20mm 25mm 20mm;
    @bottom-right {
        content: counter(page) " / " counter(pages);
        font-size: 9pt;
        color: #888;
    }
}

body {
    font-family: "Noto Sans SC", "Noto Sans JP", "Microsoft YaHei", "Hiragino Sans", sans-serif;
    font-size: 10.5pt;
    line-height: 1.8;
    color: #1a1a1a;
}

h1 { font-size: 18pt; border-bottom: 2px solid #333; padding-bottom: 6px; margin-top: 0; }
h2 { font-size: 14pt; border-bottom: 1px solid #ccc; padding-bottom: 4px; margin-top: 24px; }
h3 { font-size: 11.5pt; margin-top: 16px; }
h4 { font-size: 10.5pt; margin-top: 12px; }

p  { margin: 6px 0; }

code {
    font-family: "Courier New", monospace;
    font-size: 9pt;
    background: #f4f4f4;
    padding: 1px 4px;
    border-radius: 3px;
}

pre {
    background: #f4f4f4;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 10px 14px;
    font-size: 8.5pt;
    line-height: 1.5;
    overflow-x: auto;
    page-break-inside: avoid;
}

pre code {
    background: none;
    padding: 0;
}

table {
    border-collapse: collapse;
    width: 100%;
    margin: 12px 0;
    font-size: 9.5pt;
    page-break-inside: avoid;
}

th {
    background: #f0f0f0;
    font-weight: bold;
    text-align: left;
    padding: 6px 10px;
    border: 1px solid #bbb;
}

td {
    padding: 5px 10px;
    border: 1px solid #ccc;
    vertical-align: top;
}

tr:nth-child(even) td { background: #fafafa; }

blockquote {
    border-left: 3px solid #aaa;
    margin: 8px 0;
    padding: 4px 12px;
    color: #555;
}

hr { border: none; border-top: 1px solid #ddd; margin: 16px 0; }

ul, ol { padding-left: 1.6em; margin: 6px 0; }
li { margin: 3px 0; }

a { color: #1a73e8; text-decoration: none; }

img { max-width: 100%; page-break-inside: avoid; }
"""

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<style>{css}</style>
</head>
<body>
{body}
</body>
</html>
"""


def convert(md_path: Path, pdf_path: Path) -> None:
    md_text = md_path.read_text(encoding="utf-8")

    body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "toc", "nl2br"],
    )

    html = HTML_TEMPLATE.format(css=CSS, body=body)

    base_url = md_path.parent.as_uri() + "/"
    weasyprint.HTML(string=html, base_url=base_url).write_pdf(str(pdf_path))
    print(f"Written: {pdf_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert Markdown to PDF via WeasyPrint.")
    parser.add_argument("input", type=Path, help="Input .md file")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Output .pdf file")
    args = parser.parse_args()

    md_path: Path = args.input.resolve()
    if not md_path.exists():
        print(f"Error: {md_path} not found", file=sys.stderr)
        sys.exit(1)

    pdf_path: Path = args.output.resolve() if args.output else md_path.with_suffix(".pdf")
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    convert(md_path, pdf_path)


if __name__ == "__main__":
    main()
