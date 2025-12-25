#!/usr/bin/env python3
"""PDF builder for BookCrafter."""

from weasyprint import HTML
from instance import BASE_DIR


def build(html_string, output_path):
    """Generate PDF from HTML."""
    html = HTML(string=html_string, base_url=str(BASE_DIR))
    html.write_pdf(output_path)
    print(f"Built: {output_path}")
