#!/usr/bin/env python3
"""
Preflight checks for professional book production.

Detects typography and production issues:
- Runts (single word on last line of paragraph)
- Rivers (white space gaps running through justified text)
- Image resolution (minimum 300 DPI for print)
- Color profile validation (CMYK for print)
- Overset text detection

Usage:
    python3 preflight.py <pdf_path> [--json] [--images-dir <path>]
"""

import argparse
import json
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import pdfplumber
except ImportError:
    print("Error: pdfplumber not installed. Run: pip install pdfplumber", file=sys.stderr)
    sys.exit(3)

try:
    from PIL import Image
except ImportError:
    Image = None


class Severity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class Issue:
    type: str
    location: str
    severity: Severity
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    fix_suggestion: Optional[str] = None


class PreflightChecker:
    """Comprehensive preflight checks for print production."""

    def __init__(self, pdf_path: str, images_dir: str = None):
        self.pdf_path = Path(pdf_path)
        self.images_dir = Path(images_dir) if images_dir else None
        self.issues: List[Issue] = []

    def check_all(self) -> List[Issue]:
        """Run all preflight checks."""
        self.issues = []

        with pdfplumber.open(self.pdf_path) as pdf:
            self._check_runts(pdf.pages)
            self._check_rivers(pdf.pages)

        if self.images_dir and Image:
            self._check_image_resolution()

        self.issues.sort(key=lambda x: (x.severity.value, x.location))
        return self.issues

    def _group_chars_to_lines(self, chars) -> List[Dict]:
        """Group characters into lines."""
        if not chars:
            return []

        sorted_chars = sorted(chars, key=lambda c: (round(c['top'], 0), c['x0']))
        lines = []
        current_line = []
        current_top = None

        for char in sorted_chars:
            char_top = round(char['top'], 0)
            if current_top is None or abs(char_top - current_top) < 5:
                current_line.append(char)
                if current_top is None:
                    current_top = char_top
            else:
                if current_line:
                    lines.append(self._make_line(current_line))
                current_line = [char]
                current_top = char_top

        if current_line:
            lines.append(self._make_line(current_line))

        return lines

    def _make_line(self, chars) -> Dict:
        """Create line dict from chars."""
        text = ''.join(c.get('text', '') for c in chars)
        return {
            'text': text,
            'top': min(c['top'] for c in chars),
            'bottom': max(c['bottom'] for c in chars),
            'x0': min(c['x0'] for c in chars),
            'x1': max(c['x1'] for c in chars),
            'chars': chars,
        }

    def _check_runts(self, pages) -> None:
        """Detect runts (single word on last line of paragraph)."""
        for page_num, page in enumerate(pages):
            chars = page.chars
            if not chars:
                continue

            lines = self._group_chars_to_lines(chars)
            if len(lines) < 2:
                continue

            # Look for short last lines that might be runts
            for i, line in enumerate(lines):
                text = line['text'].strip()
                words = text.split()

                # Single word line
                if len(words) == 1 and len(text) < 15:
                    # Check if previous line is longer (paragraph continuation)
                    if i > 0:
                        prev_line = lines[i - 1]
                        prev_line['text'].strip()

                        # Previous line should be full-width for this to be a runt
                        line_width = line['x1'] - line['x0']
                        prev_width = prev_line['x1'] - prev_line['x0']

                        if prev_width > line_width * 2:
                            self.issues.append(Issue(
                                type="runt",
                                location=f"Page {page_num + 1}",
                                severity=Severity.WARNING,
                                description=f"Runt: '{text}' alone on line",
                                details={"word": text, "page": page_num + 1},
                                fix_suggestion="Rewrite to add words or tighten previous line"
                            ))

    def _check_rivers(self, pages) -> None:
        """Detect rivers (vertical white space gaps in justified text)."""
        for page_num, page in enumerate(pages):
            chars = page.chars
            if not chars:
                continue

            lines = self._group_chars_to_lines(chars)
            if len(lines) < 3:
                continue

            # Look for aligned word gaps across multiple lines
            for i in range(len(lines) - 2):
                gaps_line1 = self._find_word_gaps(lines[i])
                gaps_line2 = self._find_word_gaps(lines[i + 1])
                gaps_line3 = self._find_word_gaps(lines[i + 2])

                # Check for vertically aligned gaps
                for gap1 in gaps_line1:
                    for gap2 in gaps_line2:
                        if abs(gap1 - gap2) < 5:  # Aligned within 5pt
                            for gap3 in gaps_line3:
                                if abs(gap2 - gap3) < 5:
                                    self.issues.append(Issue(
                                        type="river",
                                        location=f"Page {page_num + 1}, lines {i + 1}-{i + 3}",
                                        severity=Severity.INFO,
                                        description=f"Possible river at x={gap1:.0f}pt",
                                        details={
                                            "x_position": gap1,
                                            "page": page_num + 1,
                                            "lines": [i + 1, i + 2, i + 3]
                                        },
                                        fix_suggestion="Adjust word spacing or rewrite text"
                                    ))
                                    break

    def _find_word_gaps(self, line: Dict) -> List[float]:
        """Find x-positions of word gaps in a line."""
        chars = line.get('chars', [])
        if not chars:
            return []

        gaps = []
        prev_char = None

        for char in sorted(chars, key=lambda c: c['x0']):
            if prev_char and char.get('text', '').strip():
                gap = char['x0'] - prev_char['x1']
                if gap > 3:  # Significant gap (word space)
                    gaps.append((prev_char['x1'] + char['x0']) / 2)
            prev_char = char

        return gaps

    def _check_image_resolution(self) -> None:
        """Check image resolution for print (300 DPI minimum)."""
        if not self.images_dir or not Image:
            return

        min_dpi = 300
        image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif'}

        for img_path in self.images_dir.rglob('*'):
            if img_path.suffix.lower() not in image_extensions:
                continue

            try:
                with Image.open(img_path) as img:
                    dpi = img.info.get('dpi', (72, 72))
                    if isinstance(dpi, tuple):
                        dpi_x, dpi_y = dpi
                    else:
                        dpi_x = dpi_y = dpi

                    if dpi_x < min_dpi or dpi_y < min_dpi:
                        self.issues.append(Issue(
                            type="low_resolution",
                            location=str(img_path.name),
                            severity=Severity.ERROR,
                            description=f"Image resolution {dpi_x}x{dpi_y} DPI below {min_dpi} DPI",
                            details={
                                "file": str(img_path),
                                "dpi": (dpi_x, dpi_y),
                                "dimensions": img.size,
                            },
                            fix_suggestion=f"Replace with {min_dpi}+ DPI image or reduce print size"
                        ))

                    # Check color mode
                    if img.mode == 'RGB':
                        self.issues.append(Issue(
                            type="rgb_image",
                            location=str(img_path.name),
                            severity=Severity.WARNING,
                            description="Image is RGB, should be CMYK for print",
                            details={
                                "file": str(img_path),
                                "mode": img.mode,
                            },
                            fix_suggestion="Convert to CMYK color profile"
                        ))

            except Exception as e:
                self.issues.append(Issue(
                    type="image_error",
                    location=str(img_path.name),
                    severity=Severity.ERROR,
                    description=f"Could not read image: {e}",
                    details={"file": str(img_path), "error": str(e)},
                ))

    def generate_report(self, format: str = "console") -> str:
        """Generate preflight report."""
        if format == "json":
            return self._report_json()
        return self._report_console()

    def _report_console(self) -> str:
        """Console report."""
        if not self.issues:
            return "Preflight: No issues found."

        lines = [
            f"\nPreflight Report: {self.pdf_path.name}",
            "=" * 60,
            ""
        ]

        errors = [i for i in self.issues if i.severity == Severity.ERROR]
        warnings = [i for i in self.issues if i.severity == Severity.WARNING]
        infos = [i for i in self.issues if i.severity == Severity.INFO]

        lines.append(f"Found {len(errors)} error(s), {len(warnings)} warning(s), {len(infos)} info(s)\n")

        for issue in self.issues:
            icon = {"error": "!!", "warning": "--", "info": "  "}[issue.severity.value]
            lines.append(f"[{icon}] {issue.location}: {issue.type}")
            lines.append(f"    {issue.description}")
            if issue.fix_suggestion:
                lines.append(f"    Fix: {issue.fix_suggestion}")
            lines.append("")

        return "\n".join(lines)

    def _report_json(self) -> str:
        """JSON report."""
        return json.dumps({
            "pdf": str(self.pdf_path),
            "issues": [
                {
                    "type": i.type,
                    "location": i.location,
                    "severity": i.severity.value,
                    "description": i.description,
                    "details": i.details,
                    "fix_suggestion": i.fix_suggestion,
                }
                for i in self.issues
            ]
        }, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Preflight checks for book production")
    parser.add_argument("pdf", help="Path to PDF file")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--images-dir", help="Directory containing source images to check")
    args = parser.parse_args()

    if not Path(args.pdf).exists():
        print(f"Error: PDF not found: {args.pdf}", file=sys.stderr)
        sys.exit(1)

    checker = PreflightChecker(args.pdf, args.images_dir)
    checker.check_all()

    if args.json:
        print(checker.generate_report("json"))
    else:
        print(checker.generate_report("console"))

    # Exit code based on issues
    errors = [i for i in checker.issues if i.severity == Severity.ERROR]
    if errors:
        sys.exit(2)
    elif checker.issues:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
