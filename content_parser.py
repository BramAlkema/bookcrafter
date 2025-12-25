#!/usr/bin/env python3
"""Content parser for BookCrafter - parses the 4-file content structure."""

import re
import markdown
from typography_processor import process_markdown_preserving_code


def extract_yaml_frontmatter(content):
    """Extract YAML frontmatter from markdown content."""
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if match:
        yaml_content = match.group(1)
        remaining = content[match.end():]
        # Simple YAML parsing (key: value)
        meta = {}
        for line in yaml_content.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                meta[key.strip()] = value.strip()
        return meta, remaining
    return {}, content


def split_sections(content):
    """Split content by top-level headers (# section-name)."""
    sections = {}
    current_section = None
    current_content = []

    for line in content.split('\n'):
        # Match top-level headers like "# cover" or "# title-page"
        match = re.match(r'^#\s+([a-z][-a-z0-9]*)\s*$', line.lower())
        if match:
            # Save previous section
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = match.group(1)
            current_content = []
        else:
            current_content.append(line)

    # Save last section
    if current_section:
        sections[current_section] = '\n'.join(current_content).strip()

    return sections


def parse_metadata_block(content):
    """Parse ::key:: value metadata from content."""
    meta = {}
    remaining_lines = []

    for line in content.split('\n'):
        match = re.match(r'^::([a-z-]+)::\s*(.*)$', line)
        if match:
            meta[match.group(1)] = match.group(2)
        else:
            remaining_lines.append(line)

    return meta, '\n'.join(remaining_lines).strip()


def parse_frontmatter_file(content):
    """Parse FrontMatter.md into sections with metadata."""
    yaml_meta, content = extract_yaml_frontmatter(content)
    sections = split_sections(content)

    result = {'_meta': yaml_meta}

    for section_name, section_content in sections.items():
        meta, text = parse_metadata_block(section_content)
        result[section_name] = {
            'meta': meta,
            'content': text
        }

    return result


def parse_content_file(content, smart_typography=True):
    """Parse Content.md and extract TOC structure."""
    yaml_meta, content = extract_yaml_frontmatter(content)

    # Apply smart typography (curly quotes, em dashes, etc.)
    if smart_typography:
        content = process_markdown_preserving_code(content)

    # Extract heading hierarchy for TOC
    toc = []
    heading_pattern = re.compile(r'^(#{1,3})\s+(.+)$', re.MULTILINE)

    for match in heading_pattern.finditer(content):
        level = len(match.group(1))
        title = match.group(2).strip()
        # Generate ID from title
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        slug = re.sub(r'[-\s]+', '-', slug).strip('-')

        toc.append({
            'level': level,
            'title': title,
            'id': slug
        })

    # Convert markdown to HTML
    md = markdown.Markdown(extensions=[
        'tables',
        'fenced_code',
        'toc',
        'attr_list',
        'md_in_html',
        'pymdownx.blocks.html',  # /// html | div.class fenced blocks
    ])
    html = md.convert(content)

    return {
        '_meta': yaml_meta,
        'html': html,
        'toc': toc
    }


def parse_backmatter_file(content):
    """Parse Backmatter.md into sections."""
    yaml_meta, content = extract_yaml_frontmatter(content)
    sections = split_sections(content)

    result = {'_meta': yaml_meta}

    md = markdown.Markdown(extensions=[
        'tables',
        'fenced_code',
        'md_in_html',
        'pymdownx.blocks.html',
    ])

    for section_name, section_content in sections.items():
        html = md.convert(section_content)
        md.reset()
        result[section_name] = {
            'content': section_content,
            'html': html
        }

    return result


def parse_decisions_file(content):
    """Parse Decisions.md (non-printable editorial notes)."""
    yaml_meta, content = extract_yaml_frontmatter(content)
    sections = split_sections(content)

    result = {
        '_meta': yaml_meta,
        'print': yaml_meta.get('print', 'true').lower() != 'false'
    }

    for section_name, section_content in sections.items():
        result[section_name] = section_content

    return result


def generate_toc_html(toc_entries):
    """Generate HTML for table of contents with dot leaders."""
    if not toc_entries:
        return '<p>No table of contents available.</p>'

    html_parts = ['<nav role="doc-toc">', '<h2>Table of Contents</h2>', '<ol>']

    current_level = 1
    for entry in toc_entries:
        level = entry['level']
        title = entry['title']
        slug = entry['id']

        # Adjust nesting
        while current_level < level:
            html_parts.append('<ol>')
            current_level += 1
        while current_level > level:
            html_parts.append('</ol></li>')
            current_level -= 1

        # Add entry with leader dots
        html_parts.append(
            f'<li><a href="#{slug}">{title}</a></li>'
        )

    # Close remaining lists
    while current_level > 1:
        html_parts.append('</ol></li>')
        current_level -= 1

    html_parts.extend(['</ol>', '</nav>'])

    return '\n'.join(html_parts)


def slugify(text):
    """Convert text to URL-friendly slug."""
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    return re.sub(r'[-\s]+', '-', slug).strip('-')
