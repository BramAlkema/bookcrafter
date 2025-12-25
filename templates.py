#!/usr/bin/env python3
"""HTML templates for BookCrafter book sections."""

# Base document wrapper
BASE_TEMPLATE = """<!DOCTYPE html>
<html lang="{language}">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
{css}
    </style>
</head>
<body>
{content}
</body>
</html>"""

# Front matter templates
COVER_TEMPLATE = """<section class="front-cover">
    <div class="cover-content">
        {publisher_badge}
        <h1 class="cover-title">{title}</h1>
        <p class="cover-subtitle-main">{subtitle}</p>
        <p class="cover-author">{author}</p>
    </div>
</section>"""

HALF_TITLE_TEMPLATE = """<section class="half-title">
    <p class="half-title-text">{title}</p>
</section>"""

TITLE_PAGE_TEMPLATE = """<section class="title-page">
    <h1 class="title-page-title">{title}</h1>
    <p class="title-page-subtitle">{subtitle}</p>
    <p class="title-page-description">{description}</p>
    <p class="title-page-author">{author}</p>
    <p class="title-page-publisher">{publisher}</p>
</section>"""

COPYRIGHT_TEMPLATE = """<section class="copyright">
{content}
</section>"""

DEDICATION_TEMPLATE = """<section class="dedication">
    <p>{content}</p>
</section>"""

TOC_TEMPLATE = """<nav role="doc-toc">
    <h2>Table of Contents</h2>
    {toc_content}
</nav>"""

# Back matter templates
BIBLIOGRAPHY_TEMPLATE = """<section id="suggested-reading">
    <h1>Bibliography</h1>
    {content}
</section>"""

GLOSSARY_TEMPLATE = """<section id="glossary">
    <h1>Glossary</h1>
    {content}
</section>"""

INDEX_TEMPLATE = """<section id="index">
    <h1>Index</h1>
    {content}
</section>"""

COLOPHON_TEMPLATE = """<section class="colophon">
    <h1>Colophon</h1>
    {content}
</section>"""

ABOUT_AUTHOR_TEMPLATE = """<section class="about-author">
    <h1>About the Author</h1>
    {content}
</section>"""

BACK_COVER_TEMPLATE = """<section class="back-cover">
    <div class="cover-content">
        <div class="back-cover-text">
            {content}
        </div>
    </div>
</section>"""


def render_cover(data, config):
    """Render front cover."""
    meta = data.get('meta', {})
    # Optional publisher badge (e.g., '<div class="saufex-report">SAUFEX REPORT</div>')
    publisher_badge = meta.get('publisher_badge', config.get('publisher_badge', ''))
    return COVER_TEMPLATE.format(
        title=meta.get('title', config.get('title', 'Untitled')),
        subtitle=meta.get('subtitle', ''),
        author=meta.get('author', config.get('author', '')),
        publisher_badge=publisher_badge
    )


def render_half_title(data, config):
    """Render half-title (bastard title) page."""
    content = data.get('content', '')
    return HALF_TITLE_TEMPLATE.format(
        title=content or config.get('title', 'Untitled')
    )


def render_title_page(data, config):
    """Render full title page."""
    meta = data.get('meta', {})
    return TITLE_PAGE_TEMPLATE.format(
        title=meta.get('title', config.get('title', 'Untitled')),
        subtitle=meta.get('subtitle', ''),
        description=meta.get('description', ''),
        author=meta.get('author', config.get('author', '')),
        publisher=meta.get('publisher', '')
    )


def render_copyright(data, config):
    """Render copyright page."""
    import markdown
    md = markdown.Markdown()
    content = data.get('content', '')
    html = md.convert(content)
    return COPYRIGHT_TEMPLATE.format(content=html)


def render_dedication(data, config):
    """Render dedication page."""
    content = data.get('content', '')
    return DEDICATION_TEMPLATE.format(content=content)


def render_toc(toc_entries):
    """Render table of contents."""
    if not toc_entries:
        return ''

    html_parts = ['<ol>']
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

        # Simple link - CSS handles the leader dots via ::after
        html_parts.append(
            f'<li><a href="#{slug}">{title}</a></li>'
        )

    while current_level > 1:
        html_parts.append('</ol></li>')
        current_level -= 1

    html_parts.append('</ol>')
    toc_content = '\n'.join(html_parts)

    return TOC_TEMPLATE.format(toc_content=toc_content)


def render_bibliography(data, config):
    """Render bibliography/references section."""
    html = data.get('html', '')
    return BIBLIOGRAPHY_TEMPLATE.format(content=html)


def render_glossary(data, config):
    """Render glossary section."""
    html = data.get('html', '')
    return GLOSSARY_TEMPLATE.format(content=html)


def render_index(data, config):
    """Render index section."""
    html = data.get('html', '')
    return INDEX_TEMPLATE.format(content=html)


def render_colophon(data, config):
    """Render colophon section."""
    html = data.get('html', '')
    return COLOPHON_TEMPLATE.format(content=html)


def render_about_author(data, config):
    """Render about the author section."""
    html = data.get('html', '')
    return ABOUT_AUTHOR_TEMPLATE.format(content=html)


def render_back_cover(data, config):
    """Render back cover."""
    html = data.get('html', data.get('content', ''))
    return BACK_COVER_TEMPLATE.format(content=html)


# Section renderers mapping
FRONTMATTER_RENDERERS = {
    'cover': render_cover,
    'half-title': render_half_title,
    'title-page': render_title_page,
    'copyright': render_copyright,
    'dedication': render_dedication,
}

BACKMATTER_RENDERERS = {
    'bibliography': render_bibliography,
    'glossary': render_glossary,
    'index': render_index,
    'colophon': render_colophon,
    'about-author': render_about_author,
    'back-cover': render_back_cover,
}


def render_frontmatter(frontmatter_data, toc_entries, config):
    """Render all front matter sections in order."""
    sections = []

    # Standard front matter order
    order = ['cover', 'half-title', 'title-page', 'copyright', 'dedication']

    for section_name in order:
        if section_name in frontmatter_data:
            renderer = FRONTMATTER_RENDERERS.get(section_name)
            if renderer:
                sections.append(renderer(frontmatter_data[section_name], config))

    # Add TOC after dedication (or at end of front matter)
    if toc_entries:
        sections.append(render_toc(toc_entries))

    return '\n\n'.join(sections)


def render_backmatter(backmatter_data, config):
    """Render all back matter sections in order."""
    sections = []

    # Standard back matter order
    order = ['bibliography', 'glossary', 'index', 'about-author', 'colophon', 'back-cover']

    for section_name in order:
        if section_name in backmatter_data:
            renderer = BACKMATTER_RENDERERS.get(section_name)
            if renderer:
                sections.append(renderer(backmatter_data[section_name], config))

    return '\n\n'.join(sections)


def assemble_book(frontmatter_html, content_html, backmatter_html, css, config):
    """Assemble complete book HTML."""
    full_content = '\n\n'.join([
        '<!-- Front Matter -->',
        frontmatter_html,
        '<!-- Main Content -->',
        f'<main>{content_html}</main>',
        '<!-- Back Matter -->',
        backmatter_html
    ])

    return BASE_TEMPLATE.format(
        language=config.get('language', 'en'),
        title=config.get('title', 'Untitled'),
        css=css,
        content=full_content
    )
