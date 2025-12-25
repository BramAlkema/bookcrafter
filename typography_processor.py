#!/usr/bin/env python3
"""Smart typography preprocessor for professional book typography.

Transforms plain ASCII text into typographically correct text:
- Straight quotes → curly quotes
- Double/triple hyphens → en/em dashes
- Three dots → ellipsis
- Adds thin spaces around em dashes
- Handles abbreviations and special cases
"""

import re


# Unicode characters
LSQUO = '\u2018'  # '
RSQUO = '\u2019'  # '
LDQUO = '\u201C'  # "
RDQUO = '\u201D'  # "
NDASH = '\u2013'  # –
MDASH = '\u2014'  # —
ELLIP = '\u2026'  # …
THINSP = '\u2009'  # thin space
HAIRSP = '\u200A'  # hair space
NBSP = '\u00A0'   # non-breaking space


def smart_quotes(text: str) -> str:
    """Convert straight quotes to curly quotes."""
    result = []
    prev_char = ' '

    i = 0
    while i < len(text):
        char = text[i]

        if char == '"':
            # Check if opening or closing
            if prev_char in ' \n\t([{' or prev_char == MDASH or prev_char == NDASH:
                result.append(LDQUO)
            else:
                result.append(RDQUO)

        elif char == "'":
            # Handle contractions (don't, it's, '90s)
            next_char = text[i + 1] if i + 1 < len(text) else ''

            # Apostrophe in contractions
            if prev_char.isalpha() and next_char.isalpha():
                result.append(RSQUO)
            # 's, 't, 'll, 're, etc. at word end
            elif prev_char.isalpha() and next_char in 'stdlmrv':
                result.append(RSQUO)
            # '90s style year abbreviations
            elif next_char.isdigit():
                result.append(RSQUO)
            # Opening quote
            elif prev_char in ' \n\t([{' or prev_char == MDASH:
                result.append(LSQUO)
            # Closing quote
            else:
                result.append(RSQUO)

        else:
            result.append(char)

        prev_char = char
        i += 1

    return ''.join(result)


def smart_dashes(text: str) -> str:
    """Convert double/triple hyphens to en/em dashes."""
    # Triple hyphen or double hyphen with spaces → em dash with thin spaces
    text = re.sub(r'\s*---\s*', f'{THINSP}{MDASH}{THINSP}', text)
    text = re.sub(r'\s+--\s+', f'{THINSP}{MDASH}{THINSP}', text)

    # Double hyphen without spaces (ranges) → en dash
    text = re.sub(r'(?<=\d)--(?=\d)', NDASH, text)  # 1990--2000
    text = re.sub(r'(?<=\w)--(?=\w)', NDASH, text)  # word--word

    # Remaining double hyphens → em dash
    text = re.sub(r'--', MDASH, text)

    return text


def smart_ellipsis(text: str) -> str:
    """Convert three dots to proper ellipsis."""
    # Three or more dots → ellipsis
    text = re.sub(r'\.{3,}', ELLIP, text)
    return text


def smart_spaces(text: str) -> str:
    """Fix spacing issues."""
    # Non-breaking space before punctuation that shouldn't break
    text = re.sub(r' ([?!:;»])', f'{NBSP}\\1', text)

    # Non-breaking space after opening quotes/guillemets
    text = re.sub(rf'([«{LDQUO}]) ', f'\\1{NBSP}', text)

    # Remove double spaces
    text = re.sub(r'  +', ' ', text)

    return text


def fix_abbreviations(text: str) -> str:
    """Handle common abbreviations with non-breaking spaces."""
    # Mr. Mrs. Dr. Prof. etc.
    abbrevs = ['Mr', 'Mrs', 'Ms', 'Dr', 'Prof', 'Sr', 'Jr', 'vs', 'etc', 'Vol', 'No', 'Fig', 'Ch', 'p', 'pp']
    for abbr in abbrevs:
        # Mr. X → Mr.NBSP X (non-breaking)
        text = re.sub(rf'\b({abbr})\.\s+', f'\\1.{NBSP}', text)

    return text


def process_typography(text: str, options: dict = None) -> str:
    """Apply all smart typography transformations.

    Options:
        quotes: bool = True - Convert to curly quotes
        dashes: bool = True - Convert to en/em dashes
        ellipsis: bool = True - Convert to ellipsis
        spaces: bool = True - Fix spacing
        abbreviations: bool = True - Non-breaking spaces for abbreviations
    """
    if options is None:
        options = {}

    # Default all options to True
    opts = {
        'quotes': True,
        'dashes': True,
        'ellipsis': True,
        'spaces': True,
        'abbreviations': True,
    }
    opts.update(options)

    # Apply transformations in order
    if opts['ellipsis']:
        text = smart_ellipsis(text)
    if opts['dashes']:
        text = smart_dashes(text)
    if opts['quotes']:
        text = smart_quotes(text)
    if opts['abbreviations']:
        text = fix_abbreviations(text)
    if opts['spaces']:
        text = smart_spaces(text)

    return text


def process_markdown_preserving_code(text: str, options: dict = None) -> str:
    """Process typography while preserving code blocks, tables, and inline code."""
    # Patterns to preserve
    code_block_pattern = re.compile(r'```.*?```', re.DOTALL)
    inline_code_pattern = re.compile(r'`[^`]+`')
    html_tag_pattern = re.compile(r'<[^>]+>')
    # Markdown table rows (lines starting with |)
    table_row_pattern = re.compile(r'^\|.*\|$', re.MULTILINE)
    # Table separator lines (|---|---|)
    table_sep_pattern = re.compile(r'^\|[-:\|\s]+\|$', re.MULTILINE)
    # Horizontal rules (--- or *** or ___ on own line)
    hr_pattern = re.compile(r'^[-*_]{3,}\s*$', re.MULTILINE)
    # YAML frontmatter
    frontmatter_pattern = re.compile(r'^---\s*\n.*?\n---\s*$', re.MULTILINE | re.DOTALL)

    # Extract and replace with placeholders
    preserved = []

    def preserve(match):
        preserved.append(match.group(0))
        return f'\x00PRESERVED{len(preserved) - 1}\x00'

    # Preserve in order (frontmatter, hr, tables, then code)
    text = frontmatter_pattern.sub(preserve, text)
    text = hr_pattern.sub(preserve, text)
    text = table_sep_pattern.sub(preserve, text)
    text = table_row_pattern.sub(preserve, text)
    text = code_block_pattern.sub(preserve, text)
    text = inline_code_pattern.sub(preserve, text)
    text = html_tag_pattern.sub(preserve, text)

    # Process typography
    text = process_typography(text, options)

    # Restore preserved content
    for i, content in enumerate(preserved):
        text = text.replace(f'\x00PRESERVED{i}\x00', content)

    return text


# Quick test
if __name__ == '__main__':
    test = '''
"Hello," she said. "It's a lovely day -- don't you think?"

The years 1990--2000 were transformative...

Mr. Smith went to Dr. Johnson's office.

Here's some `code that shouldn't change` and "quotes outside".

```python
# Code block with "quotes" and -- dashes
print("hello")
```
'''
    print("Original:")
    print(test)
    print("\nProcessed:")
    print(process_markdown_preserving_code(test))
