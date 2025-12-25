#!/usr/bin/env python3
"""BookCrafter - Python-based book building tool using WeasyPrint."""

import sys
import argparse
import importlib.util
from pathlib import Path
from weasyprint import HTML
# Use patched ebooklib with fixed CSS relative paths
import epub_patched as epub

from content_parser import (
    parse_frontmatter_file,
    parse_content_file,
    parse_backmatter_file,
)
from templates import (
    render_frontmatter,
    render_backmatter,
    assemble_book,
)
from lulu_specs import (
    PRODUCTS as LULU_PRODUCTS,
    generate_page_css as lulu_page_css,
    generate_bleed_css as lulu_bleed_css,
    validate_page_count as lulu_validate,
    get_cover_dimensions as lulu_cover,
    list_products as list_lulu_products,
)
from pumbo_specs import (
    PRODUCTS as PUMBO_PRODUCTS,
    generate_page_css as pumbo_page_css,
    generate_bleed_css as pumbo_bleed_css,
    validate_page_count as pumbo_validate,
    list_products as list_pumbo_products,
)
from typography import (
    TypographySystem,
    FONT_PAIRS,
    DENSITY_PRESETS,
    list_font_pairs,
    list_densities,
)
from css_processor import load_and_process as load_css_for_format

BASE_DIR = Path(__file__).parent.absolute()
INSTANCES_DIR = BASE_DIR / "instances"
STYLES_DIR = BASE_DIR / "styles"
FONTS_DIR = BASE_DIR / "fonts"

# These get set by setup_instance()
INSTANCE_DIR = None
CONTENT_DIR = None
INSTANCE_STYLES_DIR = None
ASSETS_DIR = None
OUTPUT_DIR = None
config = None


def setup_instance(instance_name=None):
    """Set up paths for the specified instance."""
    global INSTANCE_DIR, CONTENT_DIR, INSTANCE_STYLES_DIR, ASSETS_DIR, OUTPUT_DIR, config

    if instance_name:
        INSTANCE_DIR = INSTANCES_DIR / instance_name
        if not INSTANCE_DIR.exists():
            print(f"Error: Instance '{instance_name}' not found in {INSTANCES_DIR}")
            print("Available instances:")
            for d in INSTANCES_DIR.iterdir():
                if d.is_dir() and (d / "book_config.py").exists():
                    print(f"  - {d.name}")
            sys.exit(1)
    else:
        INSTANCE_DIR = None

    # Set content directory
    if INSTANCE_DIR and (INSTANCE_DIR / "content").exists():
        CONTENT_DIR = INSTANCE_DIR / "content"
    else:
        CONTENT_DIR = BASE_DIR / "content"

    # Set instance styles directory
    INSTANCE_STYLES_DIR = INSTANCE_DIR / "styles" if INSTANCE_DIR else None

    # Set assets directory
    if INSTANCE_DIR and (INSTANCE_DIR / "assets").exists():
        ASSETS_DIR = INSTANCE_DIR / "assets"
    else:
        ASSETS_DIR = BASE_DIR / "content"

    # Set output directory
    if INSTANCE_DIR:
        OUTPUT_DIR = INSTANCE_DIR / "output"
        OUTPUT_DIR.mkdir(exist_ok=True)
    else:
        OUTPUT_DIR = BASE_DIR

    # Load config
    if INSTANCE_DIR and (INSTANCE_DIR / "book_config.py").exists():
        spec = importlib.util.spec_from_file_location("book_config", INSTANCE_DIR / "book_config.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        config = module.config
    else:
        from book_config import config as default_config
        config = default_config

    return config


def load_file(filename):
    """Load a content file."""
    filepath = CONTENT_DIR / filename
    if filepath.exists():
        return filepath.read_text()
    return ""


def load_styles(target=None, page_count=200, typography=None):
    """Load and process CSS files.

    Args:
        target: Optional POD target (e.g., "lulu:paperback_6x9_bw")
        page_count: Estimated page count for margin calculations
        typography: Optional typography spec (e.g., "playfair-lora:relaxed")
    """
    css_files = ["brand.css", "base.css"]
    combined_css = ""

    # Add typography CSS first (base styles)
    if typography:
        parts = typography.split(":", 1)
        font_pair = parts[0]
        density = parts[1] if len(parts) > 1 else "normal"

        if font_pair not in FONT_PAIRS:
            print(f"Unknown font pair: {font_pair}")
            print("Available pairs:")
            list_font_pairs()
            sys.exit(1)

        if density not in DENSITY_PRESETS:
            print(f"Unknown density: {density}")
            print("Available densities:")
            list_densities()
            sys.exit(1)

        typo_system = TypographySystem(font_pair, density)
        print(f"Typography: {typo_system.fonts.name} ({density})")
        print(f"  Display: {typo_system.fonts.display}")
        print(f"  Body: {typo_system.fonts.body}")
        print(f"  Base size: {typo_system.baseline_pt}pt, line-height: {typo_system.line_heights['body']}")
        combined_css += typo_system.to_css_variables() + "\n"

    for css_file in css_files:
        css_path = STYLES_DIR / css_file
        if css_path.exists():
            css_content = css_path.read_text()
            # Fix font paths for WeasyPrint (needs absolute paths)
            css_content = css_content.replace(
                'url("../fonts/',
                f'url("{FONTS_DIR}/'
            )
            combined_css += css_content + "\n"

    # Load instance style overrides (if they exist)
    if INSTANCE_STYLES_DIR:
        instance_brand = INSTANCE_STYLES_DIR / "brand.css"
        if instance_brand.exists():
            combined_css += "\n/* Instance brand overrides */\n"
            combined_css += instance_brand.read_text() + "\n"

    # Add platform-specific CSS if target specified
    if target:
        if target.startswith("lulu:"):
            product_key = target.split(":", 1)[1]
            if product_key in LULU_PRODUCTS:
                print(f"Using Lulu specs: {LULU_PRODUCTS[product_key].name}")
                print(f"pod_package_id: {LULU_PRODUCTS[product_key].pod_package_id}")
                combined_css = lulu_page_css(product_key, page_count) + "\n" + combined_css
                combined_css += lulu_bleed_css()
            else:
                print(f"Unknown Lulu product: {product_key}")
                print("Available products:")
                list_lulu_products()
                sys.exit(1)

        elif target.startswith("pumbo:"):
            product_key = target.split(":", 1)[1]
            if product_key in PUMBO_PRODUCTS:
                product = PUMBO_PRODUCTS[product_key]
                print(f"Using Pumbo specs: {product.name}")
                print(f"Format: {product.format.width_mm}mm x {product.format.height_mm}mm")
                print(f"Paper: {product.paper.name_nl}")
                combined_css = pumbo_page_css(product_key, page_count) + "\n" + combined_css
                combined_css += pumbo_bleed_css()
            else:
                print(f"Unknown Pumbo product: {product_key}")
                print("Available products:")
                list_pumbo_products()
                sys.exit(1)

        else:
            print(f"Unknown target platform: {target}")
            print("Supported platforms: lulu, pumbo")
            sys.exit(1)

    return combined_css


def build_pdf(html_string, output_path):
    """Generate PDF from HTML."""
    html = HTML(string=html_string, base_url=str(BASE_DIR))
    html.write_pdf(output_path)
    print(f"Built: {output_path}")


def build_epub(frontmatter, content, backmatter, output_path):
    """Generate professional EPUB3 with proper structure, CSS, and navigation."""
    import re
    from datetime import datetime

    import uuid

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
    cover_path = ASSETS_DIR / config.get("cover", "cover.png")
    if cover_path.exists():
        cover_content = cover_path.read_bytes()
        book.set_cover("images/cover.png", cover_content)

    # Load CSS from shared stylesheets, processed for EPUB (variables resolved)
    epub_css = load_css_for_format(STYLES_DIR, 'epub')
    css_item = epub.EpubItem(
        uid="style",
        file_name="styles/main.css",
        media_type="text/css",
        content=epub_css.encode('utf-8')
    )
    book.add_item(css_item)

    # Embed fonts for consistent typography
    # Use application/font-sfnt for broader EPUB reader compatibility
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
        font_path = FONTS_DIR / font_file
        if font_path.exists():
            font_item = epub.EpubItem(
                uid=uid,
                file_name=f"fonts/{font_file}",
                media_type="application/font-sfnt",
                content=font_path.read_bytes()
            )
            book.add_item(font_item)

    spine = ['nav']
    toc = []
    landmarks = []

    def make_chapter(title, filename, body_html, add_css=True):
        """Create an EPUB chapter with proper XHTML structure."""
        ch = epub.EpubHtml(title=title, file_name=filename, lang=config.get("language", "en"))
        # Ensure body is not empty
        if not body_html or not body_html.strip():
            body_html = f'<p>{title}</p>'
        # Let ebooklib handle CSS linking via add_item - it resolves paths automatically
        ch.set_content(body_html)
        if add_css:
            ch.add_item(css_item)
        return ch

    # === FRONT MATTER ===

    # Half-title page
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

    # Copyright page
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

    # === MAIN CONTENT ===
    # Split by h1 (Parts) containing h2 (Chapters)

    html_content = content['html']

    # Split on h1 tags to get parts
    h1_splits = re.split(r'(<h1[^>]*>.*?</h1>)', html_content, flags=re.DOTALL)

    chapter_num = 0
    current_part = None
    current_part_chapters = []

    def clean_title(html_title):
        """Remove HTML tags from title."""
        return re.sub(r'<[^>]+>', '', html_title).strip()

    def save_part_to_toc():
        """Save current part with its chapters to TOC."""
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

        # Check if this is an h1 heading
        h1_match = re.match(r'<h1[^>]*>(.*?)</h1>', segment, re.DOTALL)

        if h1_match:
            # Save previous part
            save_part_to_toc()

            # Start new part
            part_title = clean_title(h1_match.group(1))
            chapter_num += 1

            # Check if next segment has chapters (h2s) or is just content
            next_segment = h1_splits[i + 1] if i + 1 < len(h1_splits) else ""

            if re.search(r'<h2[^>]*>', next_segment):
                # This is a Part with chapters - create part page
                ch = make_chapter(part_title, f"content/part{chapter_num:02d}.xhtml",
                    f'<div class="part-title"><h1>{part_title}</h1></div>')
                book.add_item(ch)
                spine.append(ch)
                current_part = epub.Link(f"content/part{chapter_num:02d}.xhtml", part_title, f"part{chapter_num}")

                # Now split next segment by h2 for chapters
                h2_splits = re.split(r'(<h2[^>]*>.*?</h2>)', next_segment, flags=re.DOTALL)
                current_chapter_content = []
                current_chapter_title = None

                for h2_seg in h2_splits:
                    if not h2_seg.strip():
                        continue

                    h2_match = re.match(r'<h2[^>]*>(.*?)</h2>', h2_seg, re.DOTALL)
                    if h2_match:
                        # Save previous chapter
                        if current_chapter_title:
                            chapter_num += 1
                            ch_content = ''.join(current_chapter_content)
                            ch = make_chapter(current_chapter_title, f"content/ch{chapter_num:02d}.xhtml",
                                f'<div class="chapter-opener"><h2>{current_chapter_title}</h2></div>{ch_content}')
                            book.add_item(ch)
                            spine.append(ch)
                            current_part_chapters.append(ch)

                        current_chapter_title = clean_title(h2_match.group(1))
                        current_chapter_content = []
                    else:
                        current_chapter_content.append(h2_seg)

                # Save last chapter
                if current_chapter_title:
                    chapter_num += 1
                    ch_content = ''.join(current_chapter_content)
                    ch = make_chapter(current_chapter_title, f"content/ch{chapter_num:02d}.xhtml",
                        f'<div class="chapter-opener"><h2>{current_chapter_title}</h2></div>{ch_content}')
                    book.add_item(ch)
                    spine.append(ch)
                    current_part_chapters.append(ch)

                # Mark next segment as processed
                h1_splits[i + 1] = ""

            else:
                # This h1 has no h2 children - treat as standalone chapter
                ch = make_chapter(part_title, f"content/ch{chapter_num:02d}.xhtml",
                    f'<h1>{part_title}</h1>')
                book.add_item(ch)
                spine.append(ch)
                current_part_chapters.append(ch)

        elif segment.strip() and not re.match(r'<h1', segment):
            # Content without preceding h1 (intro or orphaned content)
            if re.search(r'<h2[^>]*>', segment):
                # Has h2s - split them
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
                                f'<h2>{current_chapter_title}</h2>{ch_content}')
                            book.add_item(ch)
                            spine.append(ch)
                            current_part_chapters.append(ch)

                        current_chapter_title = clean_title(h2_match.group(1))
                        current_chapter_content = []
                    else:
                        current_chapter_content.append(h2_seg)

                if current_chapter_title:
                    chapter_num += 1
                    ch_content = ''.join(current_chapter_content)
                    ch = make_chapter(current_chapter_title, f"content/ch{chapter_num:02d}.xhtml",
                        f'<h2>{current_chapter_title}</h2>{ch_content}')
                    book.add_item(ch)
                    spine.append(ch)
                    current_part_chapters.append(ch)
            elif segment.strip():
                # Pure content with no headings - add to intro
                chapter_num += 1
                ch = make_chapter("Introduction", f"content/ch{chapter_num:02d}.xhtml", segment)
                book.add_item(ch)
                spine.append(ch)
                current_part_chapters.append(ch)

    # Save final part
    save_part_to_toc()

    # Add bodymatter landmark
    if chapter_num > 0:
        landmarks.append({'type': 'bodymatter', 'href': 'content/ch01.xhtml', 'title': 'Start of Content'})

    # === BACK MATTER ===
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
        toc.append((epub.Section('Back Matter'), backmatter_chapters))

    # === NAVIGATION ===

    # Set TOC
    book.toc = toc

    # Add NCX for EPUB2 compatibility
    book.add_item(epub.EpubNcx())

    # Add EPUB3 Nav with landmarks and CSS styling
    nav = epub.EpubNav()
    nav.add_item(css_item)  # Link CSS for TOC styling
    book.add_item(nav)

    # Set spine
    book.spine = spine

    # Write EPUB
    epub.write_epub(output_path, book, {'epub3_landmark': landmarks})
    print(f"Built: {output_path}")


def check_pagination(pdf_path, target=None):
    """Check for pagination issues using the full checker."""
    from tools.check_pagination import PaginationChecker, Config

    # Configure checker for target if specified
    checker_config = Config()
    if target:
        if target.startswith("pumbo:"):
            product_key = target.split(":", 1)[1]
            if product_key in PUMBO_PRODUCTS:
                spec = PUMBO_PRODUCTS[product_key]
                checker_config = Config.from_target_spec({
                    'page': {
                        'width': spec.format.width_mm,
                        'height': spec.format.height_mm,
                    },
                    'margins': {
                        'top': 20,
                        'bottom': 25,
                        'outer': 15,
                    }
                })
        elif target.startswith("lulu:"):
            product_key = target.split(":", 1)[1]
            if product_key in LULU_PRODUCTS:
                spec = LULU_PRODUCTS[product_key]
                # Lulu uses inches, convert to mm
                inch_to_mm = 25.4
                checker_config = Config.from_target_spec({
                    'page': {
                        'width': spec.trim_width * inch_to_mm,
                        'height': spec.trim_height * inch_to_mm,
                    },
                    'margins': {
                        'top': 20,  # Defaults for Lulu
                        'bottom': 25,
                        'outer': 15,
                    }
                })

    checker = PaginationChecker(str(pdf_path), checker_config)
    checker.analyze()

    # Print report
    print(checker.generate_report("console"))

    # Return exit code for CI use
    return checker.get_exit_code()


def list_instances():
    """List available instances."""
    print("Available instances:")
    if not INSTANCES_DIR.exists():
        print("  (no instances directory)")
        return
    for d in sorted(INSTANCES_DIR.iterdir()):
        if d.is_dir() and (d / "book_config.py").exists():
            # Load config to show title
            spec = importlib.util.spec_from_file_location("book_config", d / "book_config.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            title = module.config.get("title", "Untitled")
            print(f"  {d.name}: {title}")


def main():
    parser = argparse.ArgumentParser(description="BookCrafter - Build books with Python")
    parser.add_argument("command", choices=[
        "build", "check", "preflight", "preview", "watch",
        "lulu-products", "pumbo-products",
        "typography-fonts", "typography-densities",
        "instances"
    ], help="Command to run")
    parser.add_argument("--instance", "-i",
                        help="Instance to build (e.g., disinfonomics-v1)")
    parser.add_argument("--format", "-f", choices=["pdf", "epub", "html", "all", "screen"],
                        default="pdf", help="Output format (screen = PDF for digital viewing)")
    parser.add_argument("--target", "-t",
                        help="Target platform (e.g., lulu:paperback_6x9_bw)")
    parser.add_argument("--typography", "-y",
                        help="Typography preset (e.g., playfair-lora:relaxed)")
    parser.add_argument("--pages", "-p", type=int, default=200,
                        help="Estimated page count (for margin calculations)")
    args = parser.parse_args()

    # Handle listing commands (no instance needed)
    if args.command == "instances":
        list_instances()
        return

    if args.command == "lulu-products":
        list_lulu_products()
        return

    if args.command == "pumbo-products":
        list_pumbo_products()
        return

    if args.command == "typography-fonts":
        list_font_pairs()
        return

    if args.command == "typography-densities":
        list_densities()
        return

    # Set up instance (required for build commands)
    setup_instance(args.instance)

    content_config = config.get("content", {})
    slug = config["slug"]

    # Load and parse all content files
    frontmatter_raw = load_file(content_config.get("frontmatter", "FrontMatter.md"))
    content_raw = load_file(content_config.get("content", "Content.md"))
    backmatter_raw = load_file(content_config.get("backmatter", "Backmatter.md"))

    # Parse content
    frontmatter = parse_frontmatter_file(frontmatter_raw) if frontmatter_raw else {}
    content = parse_content_file(content_raw) if content_raw else {'html': '', 'toc': []}
    backmatter = parse_backmatter_file(backmatter_raw) if backmatter_raw else {}

    # Load styles (with optional target and typography)
    css = load_styles(target=args.target, page_count=args.pages, typography=args.typography)

    # Render sections
    frontmatter_html = render_frontmatter(frontmatter, content['toc'], config)
    backmatter_html = render_backmatter(backmatter, config)

    # Assemble complete book
    full_html = assemble_book(
        frontmatter_html,
        content['html'],
        backmatter_html,
        css,
        config
    )

    if args.command == "build":
        if args.format in ["pdf", "all"]:
            # Validate page count if target specified
            if args.target:
                if args.target.startswith("lulu:"):
                    product_key = args.target.split(":", 1)[1]
                    is_valid, message = lulu_validate(product_key, args.pages)
                    if not is_valid:
                        print(f"Error: {message}")
                        sys.exit(1)
                elif args.target.startswith("pumbo:"):
                    product_key = args.target.split(":", 1)[1]
                    is_valid, message = pumbo_validate(product_key, args.pages)
                    if not is_valid:
                        print(f"Error: {message}")
                        sys.exit(1)

            output_path = OUTPUT_DIR / f"{slug}.pdf"
            build_pdf(full_html, output_path)

            # Show cover dimensions for targets
            if args.target:
                if args.target.startswith("lulu:"):
                    product_key = args.target.split(":", 1)[1]
                    cover = lulu_cover(product_key, args.pages)
                    print(f"\nCover dimensions for {args.pages} pages:")
                    print(f"  Full spread: {cover['width']:.3f}\" x {cover['height']:.3f}\"")
                    print(f"  Spine width: {cover['spine_width']:.3f}\"")
                elif args.target.startswith("pumbo:"):
                    product_key = args.target.split(":", 1)[1]
                    product = PUMBO_PRODUCTS[product_key]
                    cover = product.get_cover_dimensions_mm(args.pages)
                    print(f"\nCover dimensions for {args.pages} pages:")
                    print(f"  Full spread: {cover['width_mm']:.1f}mm x {cover['height_mm']:.1f}mm")
                    print(f"  Spine width: {cover['spine_width_mm']:.1f}mm")

        if args.format in ["epub", "all"]:
            output_path = OUTPUT_DIR / f"{slug}.epub"
            build_epub(frontmatter, content, backmatter, output_path)

        if args.format in ["html", "all"]:
            output_path = OUTPUT_DIR / f"{slug}.html"
            output_path.write_text(full_html)
            print(f"Built: {output_path}")

        if args.format == "screen":
            # Screen PDF - no bleed, RGB, clickable links
            screen_css_path = STYLES_DIR / "screen.css"
            screen_css = ""
            if screen_css_path.exists():
                screen_css = screen_css_path.read_text()

            # Rebuild HTML with screen CSS appended
            screen_html = assemble_book(
                frontmatter_html,
                content['html'],
                backmatter_html,
                css + "\n" + screen_css,
                config
            )
            output_path = OUTPUT_DIR / f"{slug}-screen.pdf"
            build_pdf(screen_html, output_path)

    elif args.command == "check":
        pdf_path = OUTPUT_DIR / f"{slug}.pdf"
        if pdf_path.exists():
            exit_code = check_pagination(pdf_path, target=args.target)
            sys.exit(exit_code)
        else:
            print(f"PDF not found: {pdf_path}")
            print("Run 'python build.py build' first")
            sys.exit(3)

    elif args.command == "preflight":
        pdf_path = OUTPUT_DIR / f"{slug}.pdf"
        if pdf_path.exists():
            from tools.preflight import PreflightChecker
            checker = PreflightChecker(str(pdf_path), str(CONTENT_DIR))
            checker.check_all()
            print(checker.generate_report("console"))
        else:
            print(f"PDF not found: {pdf_path}")
            sys.exit(3)

    elif args.command == "preview":
        import webbrowser
        output_path = OUTPUT_DIR / f"{slug}.html"
        output_path.write_text(full_html)
        webbrowser.open(f"file://{output_path}")

    elif args.command == "watch":
        # Delegate to watch.py
        import subprocess
        cmd = [sys.executable, str(BASE_DIR / "watch.py")]
        if args.instance:
            cmd.extend(["--instance", args.instance])
        if args.target:
            cmd.extend(["--target", args.target])
        if args.typography:
            cmd.extend(["--typography", args.typography])
        if args.pages:
            cmd.extend(["--pages", str(args.pages)])
        subprocess.run(cmd)


if __name__ == "__main__":
    main()
