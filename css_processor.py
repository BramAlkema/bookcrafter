#!/usr/bin/env python3
"""CSS processor for unified PDF/EPUB styling.

Processes CSS from a single source for different output formats:
- PDF: Uses CSS as-is (WeasyPrint supports CSS variables)
- EPUB: Resolves CSS variables to values (EPUB readers don't support them)
"""

import re
from pathlib import Path


def extract_css_variables(css: str) -> dict:
    """Extract CSS custom properties from all :root blocks.

    Later :root blocks override earlier ones (for instance overrides).
    """
    variables = {}

    # Find all :root blocks and merge them
    for root_match in re.finditer(r':root\s*\{([^}]+)\}', css):
        root_content = root_match.group(1)
        # Extract --name: value pairs
        for match in re.finditer(r'--([a-zA-Z0-9-]+)\s*:\s*([^;]+);', root_content):
            name = match.group(1)
            value = match.group(2).strip()
            variables[name] = value

    return variables


def resolve_css_variables(css: str, variables: dict = None) -> str:
    """Replace var(--name) with actual values.

    If variables dict not provided, extracts from :root in the CSS.
    """
    if variables is None:
        variables = extract_css_variables(css)

    def replace_var(match):
        var_name = match.group(1)
        fallback = match.group(2)
        if var_name in variables:
            return variables[var_name]
        elif fallback:
            return fallback.strip()
        else:
            return match.group(0)  # Keep original if not found

    # Replace var(--name) and var(--name, fallback)
    resolved = re.sub(
        r'var\(--([a-zA-Z0-9-]+)(?:\s*,\s*([^)]+))?\)',
        replace_var,
        css
    )

    return resolved


def adjust_font_paths_for_epub(css: str) -> str:
    """Adjust font paths for EPUB structure.

    PDF: fonts are at ../fonts/ relative to styles/
    EPUB: fonts are at ../fonts/ relative to styles/ (same structure)
    """
    # The paths should be the same if we maintain consistent structure
    return css


def strip_print_media(css: str) -> str:
    """Remove @page, @media print, and unsupported selectors for EPUB."""

    def remove_at_rules(css_text, at_rule):
        """Remove @-rules with balanced braces."""
        result = []
        i = 0
        rule_len = len(at_rule)
        while i < len(css_text):
            # Check for the @-rule
            if css_text[i:i+rule_len].lower() == at_rule.lower():
                # Find the opening brace
                brace_start = css_text.find('{', i)
                if brace_start == -1:
                    result.append(css_text[i])
                    i += 1
                    continue
                # Count balanced braces
                depth = 1
                j = brace_start + 1
                while j < len(css_text) and depth > 0:
                    if css_text[j] == '{':
                        depth += 1
                    elif css_text[j] == '}':
                        depth -= 1
                    j += 1
                # Skip the entire block
                i = j
            else:
                result.append(css_text[i])
                i += 1
        return ''.join(result)

    # Remove @page rules
    css = remove_at_rules(css, '@page')

    # Remove @media print rules
    css = remove_at_rules(css, '@media print')

    # Remove :has() selectors (not supported in EPUB)
    # Match entire rule block containing :has()
    css = re.sub(r'[^{}]*:has\([^)]*\)\s*\{[^}]*\}', '', css)

    return css


def strip_css_variables_block(css: str) -> str:
    """Remove all :root blocks after variables are resolved."""
    return re.sub(r':root\s*\{[^}]*\}', '', css, flags=re.MULTILINE)


def rename_fonts_for_epub(css: str) -> str:
    """Rename fonts to avoid conflicts with system fonts.

    Apple Books may prefer system fonts over embedded ones.
    Using unique names forces use of embedded fonts.
    """
    # Rename Montserrat to avoid system font conflict
    css = css.replace('"Montserrat"', '"Montserrat Embedded"')
    css = css.replace("'Montserrat'", "'Montserrat Embedded'")
    return css


def process_for_epub(css: str) -> str:
    """Process CSS for EPUB output.

    1. Extract CSS variables
    2. Resolve all var() references
    3. Remove :root block
    4. Strip print-specific rules
    5. Rename fonts to avoid system conflicts
    6. Adjust paths if needed
    """
    # Extract variables first
    variables = extract_css_variables(css)

    # Resolve all var() references
    css = resolve_css_variables(css, variables)

    # Remove :root block (no longer needed)
    css = strip_css_variables_block(css)

    # Remove print media rules
    css = strip_print_media(css)

    # Rename fonts to avoid system font conflicts
    css = rename_fonts_for_epub(css)

    # Adjust font paths
    css = adjust_font_paths_for_epub(css)

    # Clean up extra whitespace
    css = re.sub(r'\n\s*\n\s*\n', '\n\n', css)

    return css.strip()


def process_for_pdf(css: str) -> str:
    """Process CSS for PDF output.

    Mostly pass-through since WeasyPrint supports CSS variables.
    """
    return css


def load_and_process(styles_dir: Path, output_format: str = 'pdf',
                     instance_styles_dir: Path = None) -> str:
    """Load CSS files and process for target format.

    Args:
        styles_dir: Path to styles directory
        output_format: 'pdf' or 'epub'
        instance_styles_dir: Optional path to instance-specific styles

    Returns:
        Processed CSS string
    """
    # Load base brand.css first
    combined_css = ""
    brand_path = styles_dir / 'brand.css'
    if brand_path.exists():
        combined_css += brand_path.read_text() + "\n"

    # Load instance brand overrides (before base.css, so variables are set)
    if instance_styles_dir:
        instance_brand = instance_styles_dir / "brand.css"
        if instance_brand.exists():
            combined_css += "\n/* Instance brand overrides */\n"
            combined_css += instance_brand.read_text() + "\n"

    # Load base.css (uses the variables)
    base_path = styles_dir / 'base.css'
    if base_path.exists():
        combined_css += base_path.read_text() + "\n"

    if output_format == 'epub':
        return process_for_epub(combined_css)
    else:
        return process_for_pdf(combined_css)


# Test
if __name__ == '__main__':
    test_css = """
:root {
    --color-primary: #070325;
    --color-accent: #A88500;
    --font-body: "Montserrat", sans-serif;
}

body {
    color: var(--color-primary);
    font-family: var(--font-body);
}

h1 {
    border-bottom: 2px solid var(--color-accent);
}

@page {
    size: A5;
    margin: 20mm;
}
"""

    print("=== Original CSS ===")
    print(test_css)

    print("\n=== Processed for EPUB ===")
    print(process_for_epub(test_css))
