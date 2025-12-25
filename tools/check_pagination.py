#!/usr/bin/env python3
"""
Pagination Quality Checker for BookCrafter PDF output.

Detects typesetting issues:
- Orphans/widows (paragraph fragments < 3 lines)
- Stranded headings (heading at page bottom without content)
- Split tables (tables spanning page boundaries)
- Excessive whitespace (> 30% empty pages)

Usage:
    python3 check_pagination.py <pdf_path> [--json] [--markdown] [--fix-css <output.css>]

Exit codes:
    0 - No issues found
    1 - Warnings found
    2 - Errors found
    3 - Script error
"""

import argparse
import json
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any

try:
    import pdfplumber
except ImportError:
    print("Error: pdfplumber not installed. Run: pip install pdfplumber", file=sys.stderr)
    sys.exit(3)


class Severity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class Issue:
    type: str
    page: int
    severity: Severity
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    fix_suggestion: Optional[str] = None


@dataclass
class Config:
    """Page configuration - can be initialized from BookCrafter target specs."""
    orphan_min_lines: int = 3
    widow_min_lines: int = 3
    whitespace_threshold: float = 0.30
    heading_danger_zone_pct: float = 0.15
    # Default A5 page metrics (in points, 1mm = 2.83465pt)
    page_width: float = 419.53   # 148mm
    page_height: float = 595.28  # 210mm
    margin_top: float = 56.69    # 20mm
    margin_bottom: float = 70.87 # 25mm
    margin_sides: float = 42.52  # 15mm

    @classmethod
    def from_target_spec(cls, spec: dict) -> 'Config':
        """Create Config from BookCrafter target specification."""
        mm_to_pt = 2.83465

        page = spec.get('page', {})
        margins = spec.get('margins', {})

        return cls(
            page_width=page.get('width', 148) * mm_to_pt,
            page_height=page.get('height', 210) * mm_to_pt,
            margin_top=margins.get('top', 20) * mm_to_pt,
            margin_bottom=margins.get('bottom', 25) * mm_to_pt,
            margin_sides=margins.get('outer', 15) * mm_to_pt,
        )


class PaginationChecker:
    def __init__(self, pdf_path: str, config: Optional[Config] = None):
        self.pdf_path = Path(pdf_path)
        self.config = config or Config()
        self.issues: List[Issue] = []

    def analyze(self) -> List[Issue]:
        """Run all detection algorithms and return issues."""
        self.issues = []

        with pdfplumber.open(self.pdf_path) as pdf:
            pages = pdf.pages

            # Run detectors
            self.issues.extend(self._detect_stranded_headings(pages))
            self.issues.extend(self._detect_split_tables(pages))
            self.issues.extend(self._detect_excessive_whitespace(pages))
            self.issues.extend(self._detect_orphans_widows(pages))

        # Sort by page number
        self.issues.sort(key=lambda x: x.page)
        return self.issues

    def _group_chars_into_lines(self, chars) -> List[Dict]:
        """Group characters into lines based on Y position."""
        if not chars:
            return []

        # Sort by Y position (top), then X
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
                    lines.append(self._create_line_dict(current_line))
                current_line = [char]
                current_top = char_top

        if current_line:
            lines.append(self._create_line_dict(current_line))

        return lines

    def _create_line_dict(self, chars) -> Dict:
        """Create a line dictionary from characters."""
        text = ''.join(c.get('text', '') for c in chars)
        sizes = [c.get('size', 11) for c in chars if c.get('size')]
        fontnames = [c.get('fontname', '') for c in chars if c.get('fontname')]

        return {
            'text': text,
            'top': min(c['top'] for c in chars),
            'bottom': max(c['bottom'] for c in chars),
            'x0': min(c['x0'] for c in chars),
            'x1': max(c['x1'] for c in chars),
            'fontname': fontnames[0] if fontnames else '',
            'size': max(sizes) if sizes else 11
        }

    def _is_heading(self, line: Dict) -> bool:
        """Check if line is a heading based on font characteristics."""
        fontname = line.get('fontname', '').lower()
        size = line.get('size', 0)
        # Larger size or bold font indicates heading
        return 'bold' in fontname or size > 13

    def _is_section_heading(self, line: Dict) -> bool:
        """Check if line is a real section heading (h2/h3/h4), not decorative text."""
        text = line.get('text', '').strip()
        fontname = line.get('fontname', '').lower()
        size = line.get('size', 0)

        # Must have bold font or larger size
        if not ('bold' in fontname or size > 12):
            return False

        # Filter out decorative/cover elements:
        # - Too short (< 3 chars)
        # - ALL CAPS (decorative text like "PUBLISHER NAME")
        # - Single words that are likely labels or running header fragments
        if len(text) < 3:
            return False
        if text.isupper() and len(text) < 30:
            return False
        # Require at least 2 words (filters out "Biggest", "The", etc.)
        if len(text.split()) < 2:
            return False

        # Should look like a heading:
        # - Starts with capital letter or number
        # - Contains actual words (not just symbols)
        # - Common patterns: "Chapter X", "Part X", "The ...", section titles
        if not text[0].isupper() and not text[0].isdigit():
            return False

        # Typical section heading keywords
        heading_patterns = ['chapter', 'part', 'appendix', 'section', 'the ', 'how ', 'why ', 'what ']
        text_lower = text.lower()
        has_heading_pattern = any(p in text_lower for p in heading_patterns)

        # Or reasonable length title (3-80 chars, not a paragraph)
        reasonable_title = 3 <= len(text) <= 80

        return has_heading_pattern or reasonable_title

    def _detect_stranded_headings(self, pages) -> List[Issue]:
        """Detect headings at page bottom without following content."""
        issues = []

        content_top = self.config.margin_top
        content_bottom = self.config.page_height - self.config.margin_bottom
        content_height = content_bottom - content_top
        danger_zone = content_bottom - (content_height * self.config.heading_danger_zone_pct)

        # Skip cover pages (first 5 and last 5 pages)
        skip_pages = set(range(5)) | set(range(max(0, len(pages) - 5), len(pages)))

        for page_num, page in enumerate(pages):
            if page_num in skip_pages:
                continue

            chars = page.chars
            if not chars:
                continue

            lines = self._group_chars_into_lines(chars)
            if not lines:
                continue

            for i, line in enumerate(lines):
                # Use stricter section heading check
                if self._is_section_heading(line) and line['bottom'] > danger_zone:
                    # Check for substantial content after heading on same page
                    following_lines = [ln for ln in lines[i+1:]
                                      if ln['text'].strip() and not self._is_heading(ln)]

                    if len(following_lines) < 2:
                        heading_text = line['text'].strip()[:50]
                        issues.append(Issue(
                            type="stranded_heading",
                            page=page_num + 1,
                            severity=Severity.ERROR,
                            description=f"Heading at page bottom: \"{heading_text}...\"",
                            details={
                                "heading_text": line['text'].strip(),
                                "following_lines": len(following_lines),
                                "position_from_bottom": round(content_bottom - line['bottom'], 1)
                            },
                            fix_suggestion="Add page-break-before to this heading or adjust preceding content"
                        ))

        return issues

    def _detect_split_tables(self, pages) -> List[Issue]:
        """Detect tables split across pages."""
        issues = []
        content_bottom = self.config.page_height - self.config.margin_bottom

        for page_num, page in enumerate(pages):
            tables = page.find_tables()

            for table in tables:
                if not table.bbox:
                    continue

                bbox = table.bbox  # (x0, top, x1, bottom)

                # Check if table extends to bottom of content area
                if bbox[3] > content_bottom - 30:  # Within 30pt of bottom
                    # Check next page for table at top
                    if page_num + 1 < len(pages):
                        next_page = pages[page_num + 1]
                        next_tables = next_page.find_tables()

                        for next_table in next_tables:
                            if not next_table.bbox:
                                continue
                            next_bbox = next_table.bbox

                            # Table at top of next page?
                            if next_bbox[1] < self.config.margin_top + 50:
                                issues.append(Issue(
                                    type="split_table",
                                    page=page_num + 1,
                                    severity=Severity.WARNING,
                                    description=f"Table split across pages {page_num + 1}-{page_num + 2}",
                                    details={
                                        "start_page": page_num + 1,
                                        "end_page": page_num + 2
                                    },
                                    fix_suggestion="OK if headers repeat; otherwise use break-inside: avoid or split manually"
                                ))
                                break

        return issues

    def _detect_excessive_whitespace(self, pages) -> List[Issue]:
        """Detect pages with too much empty space."""
        issues = []

        content_top = self.config.margin_top
        content_bottom = self.config.page_height - self.config.margin_bottom
        content_height = content_bottom - content_top
        content_width = self.config.page_width - 2 * self.config.margin_sides
        content_height * content_width

        for page_num, page in enumerate(pages):
            chars = page.chars
            tables = page.find_tables()

            if not chars and not tables:
                # Possibly intentionally blank or cover page
                continue

            # Calculate vertical extent of content
            min_y = content_bottom
            max_y = content_top

            if chars:
                lines = self._group_chars_into_lines(chars)
                if lines:
                    min_y = min(min_y, min(ln['top'] for ln in lines))
                    max_y = max(max_y, max(ln['bottom'] for ln in lines))

            for table in tables:
                if table.bbox:
                    min_y = min(min_y, table.bbox[1])
                    max_y = max(max_y, table.bbox[3])

            # Calculate empty space at bottom
            max_y - min_y
            empty_at_bottom = content_bottom - max_y

            # Only flag if significant empty space at bottom (not top, which is normal for chapters)
            if empty_at_bottom > content_height * self.config.whitespace_threshold:
                empty_pct = round((empty_at_bottom / content_height) * 100, 1)

                # Analyze likely cause
                cause = "page_break_rule"
                if chars:
                    lines = self._group_chars_into_lines(chars)
                    if lines and self._is_heading(lines[-1]):
                        cause = "heading_pushed_to_next_page"
                if tables:
                    cause = "table_avoid_split"

                issues.append(Issue(
                    type="excessive_whitespace",
                    page=page_num + 1,
                    severity=Severity.WARNING,
                    description=f"Page has {empty_pct}% empty space at bottom",
                    details={
                        "empty_percentage": empty_pct,
                        "likely_cause": cause,
                        "empty_height_pt": round(empty_at_bottom, 1)
                    },
                    fix_suggestion=self._get_whitespace_fix(cause)
                ))

        return issues

    def _get_whitespace_fix(self, cause: str) -> str:
        """Get fix suggestion based on whitespace cause."""
        fixes = {
            "heading_pushed_to_next_page": "Adjust content before heading to fill space",
            "table_avoid_split": "Consider splitting table or adjusting preceding content",
            "page_break_rule": "Review page-break-before rules"
        }
        return fixes.get(cause, "Review page break and content flow")

    def _detect_orphans_widows(self, pages) -> List[Issue]:
        """Detect orphan and widow lines."""
        issues = []

        content_top = self.config.margin_top
        content_bottom = self.config.page_height - self.config.margin_bottom

        for page_num, page in enumerate(pages):
            chars = page.chars
            if not chars:
                continue

            lines = self._group_chars_into_lines(chars)
            if len(lines) < 2:
                continue

            # Filter to content area lines only
            content_lines = [ln for ln in lines
                           if ln['top'] >= content_top - 10 and ln['bottom'] <= content_bottom + 10]

            if not content_lines:
                continue

            # Check for orphans (continuation at page top)
            first_lines = [ln for ln in content_lines if ln['top'] < content_top + 40]
            if 0 < len(first_lines) < self.config.orphan_min_lines:
                first_line = first_lines[0]
                text = first_line['text'].strip()
                # Check if looks like paragraph continuation (starts lowercase, no indent)
                if text and text[0].islower():
                    issues.append(Issue(
                        type="orphan",
                        page=page_num + 1,
                        severity=Severity.WARNING,
                        description=f"Possible orphan: {len(first_lines)} line(s) at page top",
                        details={
                            "line_count": len(first_lines),
                            "text_preview": text[:60]
                        },
                        fix_suggestion="Increase orphans CSS value or adjust preceding content"
                    ))

            # Check for widows (continuation to next page)
            if page_num + 1 < len(pages):
                last_lines = [ln for ln in content_lines if ln['bottom'] > content_bottom - 40]
                if 0 < len(last_lines) < self.config.widow_min_lines:
                    # Check if next page starts with paragraph continuation
                    next_page = pages[page_num + 1]
                    next_chars = next_page.chars
                    if next_chars:
                        next_lines = self._group_chars_into_lines(next_chars)
                        if next_lines:
                            next_first = next_lines[0]['text'].strip()
                            if next_first and next_first[0].islower():
                                issues.append(Issue(
                                    type="widow",
                                    page=page_num + 1,
                                    severity=Severity.WARNING,
                                    description=f"Possible widow: {len(last_lines)} line(s) at page bottom",
                                    details={
                                        "line_count": len(last_lines),
                                        "text_preview": last_lines[-1]['text'].strip()[:60]
                                    },
                                    fix_suggestion="Increase widows CSS value or add page-break-before"
                                ))

        return issues

    def generate_report(self, format: str = "console") -> str:
        """Generate report in specified format."""
        if format == "json":
            return self._report_json()
        elif format == "markdown":
            return self._report_markdown()
        else:
            return self._report_console()

    def _report_console(self) -> str:
        """Generate console-friendly report."""
        if not self.issues:
            return "No pagination issues found."

        lines = [
            f"\nPagination Analysis: {self.pdf_path.name}",
            "=" * 60,
            ""
        ]

        errors = [i for i in self.issues if i.severity == Severity.ERROR]
        warnings = [i for i in self.issues if i.severity == Severity.WARNING]

        lines.append(f"Found {len(errors)} error(s), {len(warnings)} warning(s)\n")

        for issue in self.issues:
            icon = "!!" if issue.severity == Severity.ERROR else "--"
            lines.append(f"[{icon}] Page {issue.page}: {issue.type}")
            lines.append(f"    {issue.description}")
            if issue.fix_suggestion:
                lines.append(f"    Fix: {issue.fix_suggestion}")
            lines.append("")

        return "\n".join(lines)

    def _report_json(self) -> str:
        """Generate JSON report."""
        return json.dumps({
            "pdf": str(self.pdf_path),
            "total_issues": len(self.issues),
            "errors": len([i for i in self.issues if i.severity == Severity.ERROR]),
            "warnings": len([i for i in self.issues if i.severity == Severity.WARNING]),
            "issues": [
                {
                    "type": i.type,
                    "page": i.page,
                    "severity": i.severity.value,
                    "description": i.description,
                    "details": i.details,
                    "fix_suggestion": i.fix_suggestion
                }
                for i in self.issues
            ]
        }, indent=2)

    def _report_markdown(self) -> str:
        """Generate Markdown report."""
        lines = [
            f"# Pagination Analysis: {self.pdf_path.name}",
            "",
            f"**Total issues:** {len(self.issues)}",
            ""
        ]

        for severity in [Severity.ERROR, Severity.WARNING, Severity.INFO]:
            issues = [i for i in self.issues if i.severity == severity]
            if issues:
                lines.append(f"## {severity.value.title()}s ({len(issues)})")
                lines.append("")
                for issue in issues:
                    lines.append(f"### Page {issue.page}: {issue.type}")
                    lines.append(f"{issue.description}")
                    if issue.fix_suggestion:
                        lines.append(f"\n**Fix:** {issue.fix_suggestion}")
                    lines.append("")

        return "\n".join(lines)

    def get_exit_code(self) -> int:
        """Return exit code based on issues found."""
        if not self.issues:
            return 0
        if any(i.severity == Severity.ERROR for i in self.issues):
            return 2
        return 1


def generate_css_fixes(issues: List[Issue]) -> str:
    """Generate CSS fixes for detected issues."""
    lines = ["/* Auto-generated pagination fixes */", "/* Review and merge into style.css */", ""]

    # Track what fixes we've already suggested
    added_fixes = set()

    for issue in issues:
        if issue.type == "stranded_heading" and "heading" not in added_fixes:
            lines.append(f"/* Fix stranded headings (e.g., page {issue.page}) */")
            lines.append("h3, h4 {")
            lines.append("  break-after: avoid-page;")
            lines.append("  page-break-after: avoid;")
            lines.append("}")
            lines.append("")
            added_fixes.add("heading")

        elif issue.type == "split_table" and "table" not in added_fixes:
            lines.append(f"/* Fix split tables (e.g., page {issue.page}) */")
            lines.append("table {")
            lines.append("  break-inside: avoid-page;")
            lines.append("  page-break-inside: avoid;")
            lines.append("}")
            lines.append("")
            added_fixes.add("table")

        elif issue.type in ("orphan", "widow") and "orphan_widow" not in added_fixes:
            lines.append(f"/* Fix orphans/widows (e.g., page {issue.page}) */")
            lines.append("p {")
            lines.append("  orphans: 4;")
            lines.append("  widows: 4;")
            lines.append("}")
            lines.append("")
            added_fixes.add("orphan_widow")

        elif issue.type == "excessive_whitespace":
            cause = issue.details.get("likely_cause", "unknown")
            lines.append(f"/* Page {issue.page}: {issue.details.get('empty_percentage', '?')}% empty */")
            lines.append(f"/* Cause: {cause} */")
            lines.append(f"/* Suggestion: {issue.fix_suggestion} */")
            lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Check PDF pagination quality",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exit codes:
  0 - No issues
  1 - Warnings only
  2 - Errors found
  3 - Script error
        """
    )
    parser.add_argument("pdf", help="Path to PDF file")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--markdown", action="store_true", help="Output as Markdown")
    parser.add_argument("--fix-css", metavar="FILE", help="Generate CSS fixes to file")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")

    args = parser.parse_args()

    if not Path(args.pdf).exists():
        print(f"Error: PDF not found: {args.pdf}", file=sys.stderr)
        sys.exit(3)

    try:
        checker = PaginationChecker(args.pdf)
        issues = checker.analyze()

        # Generate report
        if args.json:
            print(checker.generate_report("json"))
        elif args.markdown:
            print(checker.generate_report("markdown"))
        else:
            print(checker.generate_report("console"))

        # Generate CSS fixes if requested
        if args.fix_css:
            fixes = generate_css_fixes(issues)
            with open(args.fix_css, 'w') as f:
                f.write(fixes)
            print(f"\nCSS fixes written to {args.fix_css}")

        # Return exit code
        exit_code = checker.get_exit_code()
        if args.strict and exit_code == 1:
            exit_code = 2

        sys.exit(exit_code)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(3)


if __name__ == "__main__":
    main()
