#!/usr/bin/env python3
"""Style loading for BookCrafter."""

import sys
from instance import STYLES_DIR, FONTS_DIR, INSTANCE_STYLES_DIR
from typography import TypographySystem, FONT_PAIRS, DENSITY_PRESETS, list_font_pairs, list_densities
from lulu_specs import (
    PRODUCTS as LULU_PRODUCTS,
    generate_page_css as lulu_page_css,
    generate_bleed_css as lulu_bleed_css,
    list_products as list_lulu_products,
)
from pumbo_specs import (
    PRODUCTS as PUMBO_PRODUCTS,
    generate_page_css as pumbo_page_css,
    generate_bleed_css as pumbo_bleed_css,
    list_products as list_pumbo_products,
)


def load(target=None, page_count=200, typography=None):
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
        combined_css = _apply_target_css(target, combined_css, page_count)

    return combined_css


def _apply_target_css(target, combined_css, page_count):
    """Apply platform-specific CSS for POD targets."""
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
