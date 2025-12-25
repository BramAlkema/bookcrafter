#!/usr/bin/env python3
"""EPUB builder for BookCrafter."""

import re
import uuid
from datetime import datetime

import epub_patched as epub
from css_processor import load_and_process as load_css_for_format
import instance


def build(frontmatter, content, backmatter, config, output_path):
    """Generate professional EPUB3 with proper structure, CSS, and navigation."""
    book = epub.EpubBook()

    # Enhanced metadata - generate proper UUID
    book.set_identifier(f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_DNS, config['slug'])}")
    book.set_title(config["title"])
    book.set_language(config.get("language", "en"))
    book.add_author(config.get("author", "Unknown"))

    # Additional metadata
    if config.get("publisher"):
        book.add_metadata('DC', 'publisher', config["publisher"])
    book.add_metadata('DC', 'date', datetime.now().strftime('%Y-%m-%d'))
    if config.get("description"):
        book.add_metadata('DC', 'description', config["description"])
    book.add_metadata(None, 'meta', '', {'name': 'generator', 'content': 'BookCrafter'})

    # Add cover image
    cover_path = instance.ASSETS_DIR / config.get("cover", "cover.png")
    if cover_path.exists():
        cover_content = cover_path.read_bytes()
        book.set_cover("images/cover.png", cover_content)

    # Load CSS from shared stylesheets, processed for EPUB (variables resolved)
    epub_css = load_css_for_format(instance.STYLES_DIR, 'epub')
    css_item = epub.EpubItem(
        uid="style",
        file_name="styles/main.css",
        media_type="text/css",
        content=epub_css.encode('utf-8')
    )
    book.add_item(css_item)

    # Embed fonts
    _add_fonts(book, instance.FONTS_DIR)

    spine = ['nav']
    toc = []
    landmarks = []

    def make_chapter(title, filename, body_html, add_css=True):
        """Create an EPUB chapter with proper XHTML structure."""
        ch = epub.EpubHtml(title=title, file_name=filename, lang=config.get("language", "en"))
        if not body_html or not body_html.strip():
            body_html = f'<p>{title}</p>'
        ch.set_content(body_html)
        if add_css:
            ch.add_item(css_item)
        return ch

    # Front matter
    _build_frontmatter(frontmatter, config, make_chapter, book, spine, landmarks)

    # Main content
    chapter_num = _build_content(content, config, make_chapter, book, spine, toc, epub)

    # Add bodymatter landmark
    if chapter_num > 0:
        landmarks.append({'type': 'bodymatter', 'href': 'content/ch01.xhtml', 'title': 'Start of Content'})

    # Back matter
    _build_backmatter(backmatter, make_chapter, book, spine, toc, epub)

    # Navigation
    book.toc = toc
    book.add_item(epub.EpubNcx())
    nav = epub.EpubNav()
    nav.add_item(css_item)
    book.add_item(nav)
    book.spine = spine

    # Write EPUB
    epub.write_epub(output_path, book, {'epub3_landmark': landmarks})
    print(f"Built: {output_path}")


def _add_fonts(book, fonts_dir):
    """Embed fonts in EPUB."""
    font_files = [
        ("Montserrat-Light.ttf", "font-montserrat-light"),
        ("Montserrat-Regular.ttf", "font-montserrat-regular"),
        ("Montserrat-Medium.ttf", "font-montserrat-medium"),
        ("Montserrat-SemiBold.ttf", "font-montserrat-semibold"),
        ("Montserrat-Italic.ttf", "font-montserrat-italic"),
        ("BalooBhai2-Regular.ttf", "font-baloo-regular"),
        ("BalooBhai2-SemiBold.ttf", "font-baloo-semibold"),
        ("BalooBhai2-Bold.ttf", "font-baloo-bold"),
    ]
    for font_file, uid in font_files:
        font_path = fonts_dir / font_file
        if font_path.exists():
            font_item = epub.EpubItem(
                uid=uid,
                file_name=f"fonts/{font_file}",
                media_type="application/font-sfnt",
                content=font_path.read_bytes()
            )
            book.add_item(font_item)


def _build_frontmatter(frontmatter, config, make_chapter, book, spine, landmarks):
    """Build EPUB front matter sections."""
    # Half-title
    if 'half-title' in frontmatter:
        half_title_text = frontmatter['half-title'].get('content', config.get('title', ''))
        ch = make_chapter("Half Title", "frontmatter/halftitle.xhtml",
            f'<div class="half-title"><span class="half-title-text">{half_title_text}</span></div>')
        book.add_item(ch)
        spine.append(ch)

    # Title page
    subtitle = frontmatter.get('title-page', {}).get('meta', {}).get('subtitle', '')
    title_html = f'''<div class="title-page">
    <div class="title-page-title">{config.get("title", "")}</div>
    <div class="title-page-subtitle">{subtitle}</div>
    <div class="title-page-author">By {config.get("author", "")}</div>
    <div class="title-page-publisher">{config.get("publisher", "")}</div>
</div>'''
    ch_title = make_chapter("Title Page", "frontmatter/title.xhtml", title_html)
    book.add_item(ch_title)
    spine.append(ch_title)
    landmarks.append({'type': 'titlepage', 'href': 'frontmatter/title.xhtml', 'title': 'Title Page'})

    # Copyright
    if 'copyright' in frontmatter and frontmatter['copyright'].get('content', '').strip():
        copyright_html = frontmatter['copyright'].get('html', '')
        if not copyright_html:
            copyright_html = '<p>' + frontmatter['copyright']['content'].replace('\n\n', '</p><p>').replace('\n', '<br/>') + '</p>'
        ch = make_chapter("Copyright", "frontmatter/copyright.xhtml",
            f'<div class="copyright">{copyright_html}</div>')
        book.add_item(ch)
        spine.append(ch)
        landmarks.append({'type': 'copyright-page', 'href': 'frontmatter/copyright.xhtml', 'title': 'Copyright'})

    # Dedication
    if 'dedication' in frontmatter and frontmatter['dedication'].get('content', '').strip():
        ch = make_chapter("Dedication", "frontmatter/dedication.xhtml",
            f'<div class="dedication">{frontmatter["dedication"]["content"]}</div>')
        book.add_item(ch)
        spine.append(ch)
        landmarks.append({'type': 'dedication', 'href': 'frontmatter/dedication.xhtml', 'title': 'Dedication'})


def _build_content(content, config, make_chapter, book, spine, toc, epub_module):
    """Build EPUB main content from HTML."""
    html_content = content['html']
    h1_splits = re.split(r'(<h1[^>]*>.*?</h1>)', html_content, flags=re.DOTALL)

    chapter_num = 0
    current_part = None
    current_part_chapters = []

    def clean_title(html_title):
        return re.sub(r'<[^>]+>', '', html_title).strip()

    def save_part_to_toc():
        nonlocal current_part, current_part_chapters
        if current_part and current_part_chapters:
            toc.append((current_part, current_part_chapters))
        elif current_part_chapters:
            toc.extend(current_part_chapters)
        current_part = None
        current_part_chapters = []

    for i, segment in enumerate(h1_splits):
        if not segment.strip():
            continue

        h1_match = re.match(r'<h1[^>]*>(.*?)</h1>', segment, re.DOTALL)

        if h1_match:
            save_part_to_toc()
            part_title = clean_title(h1_match.group(1))
            chapter_num += 1
            next_segment = h1_splits[i + 1] if i + 1 < len(h1_splits) else ""

            if re.search(r'<h2[^>]*>', next_segment):
                ch = make_chapter(part_title, f"content/part{chapter_num:02d}.xhtml",
                    f'<div class="part-title"><h1>{part_title}</h1></div>')
                book.add_item(ch)
                spine.append(ch)
                current_part = epub_module.Link(f"content/part{chapter_num:02d}.xhtml", part_title, f"part{chapter_num}")

                chapter_num, current_part_chapters = _process_h2_segments(
                    next_segment, chapter_num, make_chapter, book, spine, current_part_chapters, clean_title
                )
                h1_splits[i + 1] = ""
            else:
                ch = make_chapter(part_title, f"content/ch{chapter_num:02d}.xhtml", f'<h1>{part_title}</h1>')
                book.add_item(ch)
                spine.append(ch)
                current_part_chapters.append(ch)

        elif segment.strip() and not re.match(r'<h1', segment):
            if re.search(r'<h2[^>]*>', segment):
                chapter_num, current_part_chapters = _process_h2_segments(
                    segment, chapter_num, make_chapter, book, spine, current_part_chapters, clean_title
                )
            elif segment.strip():
                chapter_num += 1
                ch = make_chapter("Introduction", f"content/ch{chapter_num:02d}.xhtml", segment)
                book.add_item(ch)
                spine.append(ch)
                current_part_chapters.append(ch)

    save_part_to_toc()
    return chapter_num


def _process_h2_segments(segment, chapter_num, make_chapter, book, spine, part_chapters, clean_title):
    """Process h2 segments within content."""
    h2_splits = re.split(r'(<h2[^>]*>.*?</h2>)', segment, flags=re.DOTALL)
    current_chapter_content = []
    current_chapter_title = None

    for h2_seg in h2_splits:
        if not h2_seg.strip():
            continue

        h2_match = re.match(r'<h2[^>]*>(.*?)</h2>', h2_seg, re.DOTALL)
        if h2_match:
            if current_chapter_title:
                chapter_num += 1
                ch_content = ''.join(current_chapter_content)
                ch = make_chapter(current_chapter_title, f"content/ch{chapter_num:02d}.xhtml",
                    f'<div class="chapter-opener"><h2>{current_chapter_title}</h2></div>{ch_content}')
                book.add_item(ch)
                spine.append(ch)
                part_chapters.append(ch)

            current_chapter_title = clean_title(h2_match.group(1))
            current_chapter_content = []
        else:
            current_chapter_content.append(h2_seg)

    if current_chapter_title:
        chapter_num += 1
        ch_content = ''.join(current_chapter_content)
        ch = make_chapter(current_chapter_title, f"content/ch{chapter_num:02d}.xhtml",
            f'<div class="chapter-opener"><h2>{current_chapter_title}</h2></div>{ch_content}')
        book.add_item(ch)
        spine.append(ch)
        part_chapters.append(ch)

    return chapter_num, part_chapters


def _build_backmatter(backmatter, make_chapter, book, spine, toc, epub_module):
    """Build EPUB back matter sections."""
    backmatter_order = [
        ('bibliography', 'Bibliography'),
        ('suggested-reading', 'Suggested Reading'),
        ('glossary', 'Glossary'),
        ('index', 'Index'),
        ('about-author', 'About the Author'),
        ('colophon', 'Colophon'),
    ]

    backmatter_chapters = []
    for key, title in backmatter_order:
        if key in backmatter and backmatter[key].get('html', '').strip():
            ch = make_chapter(title, f"backmatter/{key.replace('-', '_')}.xhtml",
                f'<div class="{key}"><h1>{title}</h1>{backmatter[key]["html"]}</div>')
            book.add_item(ch)
            spine.append(ch)
            backmatter_chapters.append(ch)

    if backmatter_chapters:
        toc.append((epub_module.Section('Back Matter'), backmatter_chapters))
