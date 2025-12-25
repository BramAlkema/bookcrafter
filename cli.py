#!/usr/bin/env python3
"""CLI for BookCrafter."""

import sys
import argparse

import instance
import styles
import pdf_builder
import epub_builder
from content_parser import parse_frontmatter_file, parse_content_file, parse_backmatter_file
from templates import render_frontmatter, render_backmatter, assemble_book
from lulu_specs import (
    PRODUCTS as LULU_PRODUCTS,
    validate_page_count as lulu_validate,
    get_cover_dimensions as lulu_cover,
    list_products as list_lulu_products,
)
from pumbo_specs import (
    PRODUCTS as PUMBO_PRODUCTS,
    validate_page_count as pumbo_validate,
    list_products as list_pumbo_products,
)
from typography import list_font_pairs, list_densities


def main():
    parser = argparse.ArgumentParser(description="BookCrafter - Build books with Python")
    parser.add_argument("command", choices=[
        "build", "check", "preflight", "preview", "watch",
        "lulu-products", "pumbo-products",
        "typography-fonts", "typography-densities",
        "instances"
    ], help="Command to run")
    parser.add_argument("--instance", "-i", help="Instance to build (e.g., disinfonomics-v1)")
    parser.add_argument("--format", "-f", choices=["pdf", "epub", "html", "all", "screen"],
                        default="pdf", help="Output format (screen = PDF for digital viewing)")
    parser.add_argument("--target", "-t", help="Target platform (e.g., lulu:paperback_6x9_bw)")
    parser.add_argument("--typography", "-y", help="Typography preset (e.g., playfair-lora:relaxed)")
    parser.add_argument("--pages", "-p", type=int, default=200, help="Estimated page count")
    args = parser.parse_args()

    # Handle listing commands (no instance needed)
    if args.command == "instances":
        print("Available instances:")
        instance.list_instances()
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
    config = instance.setup(args.instance)
    content_config = config.get("content", {})
    slug = config["slug"]

    # Load and parse content files
    frontmatter_raw = instance.load_file(content_config.get("frontmatter", "FrontMatter.md"))
    content_raw = instance.load_file(content_config.get("content", "Content.md"))
    backmatter_raw = instance.load_file(content_config.get("backmatter", "Backmatter.md"))

    frontmatter = parse_frontmatter_file(frontmatter_raw) if frontmatter_raw else {}
    content = parse_content_file(content_raw) if content_raw else {'html': '', 'toc': []}
    backmatter = parse_backmatter_file(backmatter_raw) if backmatter_raw else {}

    # Load styles
    css = styles.load(target=args.target, page_count=args.pages, typography=args.typography)

    # Render sections
    frontmatter_html = render_frontmatter(frontmatter, content['toc'], config)
    backmatter_html = render_backmatter(backmatter, config)

    # Assemble complete book
    full_html = assemble_book(frontmatter_html, content['html'], backmatter_html, css, config)

    if args.command == "build":
        _cmd_build(args, config, slug, full_html, frontmatter, content, backmatter, css,
                   frontmatter_html, backmatter_html)

    elif args.command == "check":
        _cmd_check(slug, args.target)

    elif args.command == "preflight":
        _cmd_preflight(slug)

    elif args.command == "preview":
        _cmd_preview(slug, full_html)

    elif args.command == "watch":
        _cmd_watch(args)


def _cmd_build(args, config, slug, full_html, frontmatter, content, backmatter, css,
               frontmatter_html, backmatter_html):
    """Handle build command."""
    if args.format in ["pdf", "all"]:
        # Validate page count
        if args.target:
            _validate_page_count(args.target, args.pages)

        output_path = instance.OUTPUT_DIR / f"{slug}.pdf"
        pdf_builder.build(full_html, output_path)

        # Show cover dimensions
        if args.target:
            _show_cover_dimensions(args.target, args.pages)

    if args.format in ["epub", "all"]:
        output_path = instance.OUTPUT_DIR / f"{slug}.epub"
        epub_builder.build(frontmatter, content, backmatter, config, output_path)

    if args.format in ["html", "all"]:
        output_path = instance.OUTPUT_DIR / f"{slug}.html"
        output_path.write_text(full_html)
        print(f"Built: {output_path}")

    if args.format == "screen":
        screen_css_path = instance.STYLES_DIR / "screen.css"
        screen_css = screen_css_path.read_text() if screen_css_path.exists() else ""
        screen_html = assemble_book(frontmatter_html, content['html'], backmatter_html,
                                    css + "\n" + screen_css, config)
        output_path = instance.OUTPUT_DIR / f"{slug}-screen.pdf"
        pdf_builder.build(screen_html, output_path)


def _cmd_check(slug, target):
    """Handle check command."""
    from tools.check_pagination import PaginationChecker

    pdf_path = instance.OUTPUT_DIR / f"{slug}.pdf"
    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}")
        print("Run 'python build.py build' first")
        sys.exit(3)

    checker_config = _get_checker_config(target)
    checker = PaginationChecker(str(pdf_path), checker_config)
    checker.analyze()
    print(checker.generate_report("console"))
    sys.exit(checker.get_exit_code())


def _cmd_preflight(slug):
    """Handle preflight command."""
    from tools.preflight import PreflightChecker

    pdf_path = instance.OUTPUT_DIR / f"{slug}.pdf"
    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}")
        sys.exit(3)

    checker = PreflightChecker(str(pdf_path), str(instance.CONTENT_DIR))
    checker.check_all()
    print(checker.generate_report("console"))


def _cmd_preview(slug, full_html):
    """Handle preview command."""
    import webbrowser
    output_path = instance.OUTPUT_DIR / f"{slug}.html"
    output_path.write_text(full_html)
    webbrowser.open(f"file://{output_path}")


def _cmd_watch(args):
    """Handle watch command."""
    import subprocess
    cmd = [sys.executable, str(instance.BASE_DIR / "watch.py")]
    if args.instance:
        cmd.extend(["--instance", args.instance])
    if args.target:
        cmd.extend(["--target", args.target])
    if args.typography:
        cmd.extend(["--typography", args.typography])
    if args.pages:
        cmd.extend(["--pages", str(args.pages)])
    subprocess.run(cmd)


def _validate_page_count(target, pages):
    """Validate page count for target platform."""
    if target.startswith("lulu:"):
        product_key = target.split(":", 1)[1]
        is_valid, message = lulu_validate(product_key, pages)
        if not is_valid:
            print(f"Error: {message}")
            sys.exit(1)
    elif target.startswith("pumbo:"):
        product_key = target.split(":", 1)[1]
        is_valid, message = pumbo_validate(product_key, pages)
        if not is_valid:
            print(f"Error: {message}")
            sys.exit(1)


def _show_cover_dimensions(target, pages):
    """Show cover dimensions for target platform."""
    if target.startswith("lulu:"):
        product_key = target.split(":", 1)[1]
        cover = lulu_cover(product_key, pages)
        print(f"\nCover dimensions for {pages} pages:")
        print(f"  Full spread: {cover['width']:.3f}\" x {cover['height']:.3f}\"")
        print(f"  Spine width: {cover['spine_width']:.3f}\"")
    elif target.startswith("pumbo:"):
        product_key = target.split(":", 1)[1]
        product = PUMBO_PRODUCTS[product_key]
        cover = product.get_cover_dimensions_mm(pages)
        print(f"\nCover dimensions for {pages} pages:")
        print(f"  Full spread: {cover['width_mm']:.1f}mm x {cover['height_mm']:.1f}mm")
        print(f"  Spine width: {cover['spine_width_mm']:.1f}mm")


def _get_checker_config(target):
    """Get pagination checker config for target."""
    from tools.check_pagination import Config

    if not target:
        return Config()

    if target.startswith("pumbo:"):
        product_key = target.split(":", 1)[1]
        if product_key in PUMBO_PRODUCTS:
            spec = PUMBO_PRODUCTS[product_key]
            return Config.from_target_spec({
                'page': {'width': spec.format.width_mm, 'height': spec.format.height_mm},
                'margins': {'top': 20, 'bottom': 25, 'outer': 15}
            })
    elif target.startswith("lulu:"):
        product_key = target.split(":", 1)[1]
        if product_key in LULU_PRODUCTS:
            spec = LULU_PRODUCTS[product_key]
            inch_to_mm = 25.4
            return Config.from_target_spec({
                'page': {'width': spec.trim_width * inch_to_mm, 'height': spec.trim_height * inch_to_mm},
                'margins': {'top': 20, 'bottom': 25, 'outer': 15}
            })

    return Config()


if __name__ == "__main__":
    main()
