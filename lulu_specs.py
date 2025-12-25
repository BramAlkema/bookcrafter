#!/usr/bin/env python3
"""
Lulu Print-on-Demand specifications for BookCrafter.

This module contains all Lulu product specifications including trim sizes,
margins, bleed requirements, and pod_package_id construction.

Sources:
- https://api.lulu.com/docs/
- https://www.lulu.com/products
- https://help.lulu.com/en/support/solutions/articles/64000255584-what-is-full-bleed-
"""

from dataclasses import dataclass
from typing import Dict, Tuple, Optional


# =============================================================================
# Constants
# =============================================================================

BLEED = 0.125  # inches, all sides
SAFETY_MARGIN = 0.5  # inches, minimum from trim edge
TRIM_VARIANCE = 0.125  # inches, printing tolerance


# =============================================================================
# Trim Sizes
# =============================================================================

@dataclass
class TrimSize:
    """Book trim size specification."""
    name: str
    code: str  # For pod_package_id (e.g., "0600X0900")
    width: float  # inches
    height: float  # inches
    min_pages: int = 32
    gutter: float = 0.75  # inside margin, varies by page count


TRIM_SIZES: Dict[str, TrimSize] = {
    # Portrait/Standard
    "pocket": TrimSize("Pocket Book", "0425X0687", 4.25, 6.875, gutter=0.5),
    "digest": TrimSize("Digest", "0550X0850", 5.5, 8.5, gutter=0.625),
    "novella": TrimSize("Novella", "0500X0800", 5.0, 8.0, gutter=0.625),
    "a5": TrimSize("A5", "0583X0827", 5.83, 8.27, gutter=0.625),
    "us_trade": TrimSize("US Trade", "0600X0900", 6.0, 9.0, gutter=0.75),
    "royal": TrimSize("Royal", "0614X0921", 6.14, 9.21, gutter=0.75),
    "comic": TrimSize("Comic Book", "0663X1025", 6.63, 10.25, gutter=0.75),
    "executive": TrimSize("Executive", "0700X1000", 7.0, 10.0, gutter=0.875),
    "crown_quarto": TrimSize("Crown Quarto", "0744X0968", 7.44, 9.68, gutter=0.875),
    "a4": TrimSize("A4", "0827X1169", 8.27, 11.69, gutter=1.0),
    "us_letter": TrimSize("US Letter", "0850X1100", 8.5, 11.0, gutter=1.0),

    # Square
    "small_square": TrimSize("Small Square", "0750X0750", 7.5, 7.5, gutter=0.75),
    "square": TrimSize("Square", "0850X0850", 8.5, 8.5, gutter=0.875),

    # Landscape
    "small_landscape": TrimSize("Small Landscape", "0900X0700", 9.0, 7.0, gutter=0.75),
    "us_letter_landscape": TrimSize("US Letter Landscape", "1100X0850", 11.0, 8.5, gutter=1.0),
    "a4_landscape": TrimSize("A4 Landscape", "1169X0827", 11.69, 8.27, gutter=1.0),
}


# =============================================================================
# Paper Types
# =============================================================================

@dataclass
class PaperType:
    """Paper specification."""
    name: str
    code: str  # For pod_package_id
    weight: int  # pounds
    coated: bool
    color: str  # "white" or "cream"
    ppi: int  # pages per inch (for spine calculation)


PAPER_TYPES: Dict[str, PaperType] = {
    "60_cream": PaperType("60# Cream", "060UC", 60, False, "cream", 444),
    "60_white": PaperType("60# White", "060UW", 60, False, "white", 444),
    "80_white_coated": PaperType("80# Coated White", "080CW", 80, True, "white", 382),
}


# =============================================================================
# Binding Types
# =============================================================================

@dataclass
class BindingType:
    """Binding specification."""
    name: str
    code: str  # For pod_package_id
    min_pages: int
    max_pages: int
    has_spine: bool


BINDING_TYPES: Dict[str, BindingType] = {
    "perfect_bound": BindingType("Perfect Bound Paperback", "PB", 32, 800, True),
    "coil": BindingType("Coil Bound", "CO", 24, 300, False),
    "saddle_stitch": BindingType("Saddle Stitch", "SS", 8, 80, False),
    "casewrap": BindingType("Hardcover Casewrap", "CW", 24, 800, True),
    "linen_wrap": BindingType("Hardcover Linen Wrap", "LW", 24, 800, True),
    "dust_jacket": BindingType("Dust Jacket Hardcover", "DJ", 24, 800, True),
}


# =============================================================================
# Color & Quality Options
# =============================================================================

@dataclass
class ColorOption:
    """Interior color specification."""
    name: str
    code: str


COLOR_OPTIONS: Dict[str, ColorOption] = {
    "bw_standard": ColorOption("Standard Black & White", "BW"),
    "bw_premium": ColorOption("Premium Black & White", "BP"),
    "color_standard": ColorOption("Standard Color", "FC"),
    "color_premium": ColorOption("Premium Color", "FP"),
}

PRINT_QUALITY = {
    "standard": "STD",
    "premium": "PRE",
}

COVER_FINISH = {
    "matte": "M",
    "gloss": "G",
}

LINEN_COLORS = {
    "navy": "N",
    "black": "B",
    "gray": "G",
    "red": "R",
    "tan": "T",
    "forest": "F",
}

FOIL_COLORS = {
    "gold": "G",
    "black": "B",
    "white": "W",
    "none": "X",
}


# =============================================================================
# Product Configuration
# =============================================================================

@dataclass
class LuluProduct:
    """Complete Lulu product specification."""
    name: str
    trim: TrimSize
    color: ColorOption
    quality: str
    binding: BindingType
    paper: PaperType
    finish: str
    linen: Optional[str] = None
    foil: Optional[str] = None

    @property
    def pod_package_id(self) -> str:
        """Generate the 27-character pod_package_id."""
        linen_code = self.linen or "X"
        foil_code = self.foil or "X"

        return (
            f"{self.trim.code}"
            f"{self.color.code}"
            f"{self.quality}"
            f"{self.binding.code}"
            f"{self.paper.code}"
            f"{self.paper.ppi}"
            f"{self.finish}"
            f"{linen_code}"
            f"{foil_code}"
        )


# =============================================================================
# Common Product Presets
# =============================================================================

PRODUCTS: Dict[str, LuluProduct] = {
    # Paperback Black & White
    "paperback_6x9_bw": LuluProduct(
        name="6x9 Paperback B&W",
        trim=TRIM_SIZES["us_trade"],
        color=COLOR_OPTIONS["bw_standard"],
        quality="STD",
        binding=BINDING_TYPES["perfect_bound"],
        paper=PAPER_TYPES["60_white"],
        finish="M",
    ),
    "paperback_5.5x8.5_bw": LuluProduct(
        name="5.5x8.5 Digest Paperback B&W",
        trim=TRIM_SIZES["digest"],
        color=COLOR_OPTIONS["bw_standard"],
        quality="STD",
        binding=BINDING_TYPES["perfect_bound"],
        paper=PAPER_TYPES["60_white"],
        finish="M",
    ),
    "paperback_5x8_bw": LuluProduct(
        name="5x8 Novella Paperback B&W",
        trim=TRIM_SIZES["novella"],
        color=COLOR_OPTIONS["bw_standard"],
        quality="STD",
        binding=BINDING_TYPES["perfect_bound"],
        paper=PAPER_TYPES["60_white"],
        finish="M",
    ),
    "paperback_pocket_bw": LuluProduct(
        name="Pocket Paperback B&W",
        trim=TRIM_SIZES["pocket"],
        color=COLOR_OPTIONS["bw_standard"],
        quality="STD",
        binding=BINDING_TYPES["perfect_bound"],
        paper=PAPER_TYPES["60_white"],
        finish="M",
    ),

    # Paperback with Cream Paper
    "paperback_6x9_cream": LuluProduct(
        name="6x9 Paperback Cream",
        trim=TRIM_SIZES["us_trade"],
        color=COLOR_OPTIONS["bw_standard"],
        quality="STD",
        binding=BINDING_TYPES["perfect_bound"],
        paper=PAPER_TYPES["60_cream"],
        finish="M",
    ),
    "paperback_5.5x8.5_cream": LuluProduct(
        name="5.5x8.5 Digest Paperback Cream",
        trim=TRIM_SIZES["digest"],
        color=COLOR_OPTIONS["bw_standard"],
        quality="STD",
        binding=BINDING_TYPES["perfect_bound"],
        paper=PAPER_TYPES["60_cream"],
        finish="M",
    ),

    # Paperback Color
    "paperback_6x9_color": LuluProduct(
        name="6x9 Paperback Color",
        trim=TRIM_SIZES["us_trade"],
        color=COLOR_OPTIONS["color_standard"],
        quality="STD",
        binding=BINDING_TYPES["perfect_bound"],
        paper=PAPER_TYPES["80_white_coated"],
        finish="G",
    ),
    "paperback_8.5x11_color": LuluProduct(
        name="8.5x11 Letter Paperback Color",
        trim=TRIM_SIZES["us_letter"],
        color=COLOR_OPTIONS["color_standard"],
        quality="STD",
        binding=BINDING_TYPES["perfect_bound"],
        paper=PAPER_TYPES["80_white_coated"],
        finish="G",
    ),

    # Hardcover
    "hardcover_6x9_bw": LuluProduct(
        name="6x9 Hardcover Casewrap B&W",
        trim=TRIM_SIZES["us_trade"],
        color=COLOR_OPTIONS["bw_standard"],
        quality="STD",
        binding=BINDING_TYPES["casewrap"],
        paper=PAPER_TYPES["60_white"],
        finish="M",
    ),
    "hardcover_6x9_color": LuluProduct(
        name="6x9 Hardcover Casewrap Color",
        trim=TRIM_SIZES["us_trade"],
        color=COLOR_OPTIONS["color_standard"],
        quality="STD",
        binding=BINDING_TYPES["casewrap"],
        paper=PAPER_TYPES["80_white_coated"],
        finish="G",
    ),
}


# =============================================================================
# Dimension Calculations
# =============================================================================

def get_page_dimensions(product_key: str) -> Tuple[float, float]:
    """
    Get page dimensions WITH bleed for PDF creation.

    Returns (width, height) in inches.
    """
    product = PRODUCTS[product_key]
    width = product.trim.width + (2 * BLEED)
    height = product.trim.height + (2 * BLEED)
    return (width, height)


def get_spine_width(product_key: str, page_count: int) -> float:
    """
    Calculate spine width based on page count and paper type.

    Returns width in inches.
    """
    product = PRODUCTS[product_key]
    ppi = product.paper.ppi
    return page_count / ppi


def get_cover_dimensions(product_key: str, page_count: int) -> Dict[str, float]:
    """
    Calculate full cover spread dimensions.

    Returns dict with width, height, spine_width, spine_start_x.
    """
    product = PRODUCTS[product_key]
    trim = product.trim
    spine = get_spine_width(product_key, page_count)

    # Full wrap: back + spine + front + bleed on outside
    cover_width = (2 * trim.width) + spine + (2 * BLEED)
    cover_height = trim.height + (2 * BLEED)

    return {
        "width": cover_width,
        "height": cover_height,
        "spine_width": spine,
        "spine_start_x": trim.width + BLEED,  # x position where spine begins
        "front_start_x": trim.width + BLEED + spine,  # x position where front cover begins
    }


def get_gutter(product_key: str, page_count: int) -> float:
    """
    Get inside margin (gutter) based on page count.

    Thicker books need larger gutters.
    """
    product = PRODUCTS[product_key]
    base_gutter = product.trim.gutter

    # Increase gutter for thicker books
    if page_count > 400:
        return base_gutter + 0.25
    elif page_count > 200:
        return base_gutter + 0.125
    return base_gutter


# =============================================================================
# CSS Generation
# =============================================================================

def generate_page_css(product_key: str, page_count: int = 200) -> str:
    """
    Generate CSS @page rules for Lulu specifications.

    Args:
        product_key: Key from PRODUCTS dict
        page_count: Estimated page count (affects gutter)

    Returns:
        CSS string with @page rules
    """
    product = PRODUCTS[product_key]
    trim = product.trim
    gutter = get_gutter(product_key, page_count)

    return f"""
/* Lulu specifications for {product.name} */
/* pod_package_id: {product.pod_package_id} */

@page {{
    size: {trim.width}in {trim.height}in;
    margin-top: {SAFETY_MARGIN}in;
    margin-bottom: {SAFETY_MARGIN}in;
    margin-outside: {SAFETY_MARGIN}in;
    margin-inside: {gutter}in;

    /* Bleed area for full-bleed elements */
    bleed: {BLEED}in;

    /* Marks for proofing (disable for final) */
    /* marks: crop; */
}}

@page :left {{
    margin-left: {gutter}in;
    margin-right: {SAFETY_MARGIN}in;
}}

@page :right {{
    margin-left: {SAFETY_MARGIN}in;
    margin-right: {gutter}in;
}}

@page :first {{
    /* Front matter pages may have different margins */
}}
"""


def generate_bleed_css() -> str:
    """Generate CSS for full-bleed elements."""
    return f"""
/* Full bleed images and backgrounds */
.full-bleed {{
    margin-left: -{BLEED}in;
    margin-right: -{BLEED}in;
    width: calc(100% + {2 * BLEED}in);
}}

.full-bleed-all {{
    margin: -{BLEED}in;
    width: calc(100% + {2 * BLEED}in);
    height: calc(100% + {2 * BLEED}in);
}}
"""


# =============================================================================
# Validation
# =============================================================================

def validate_page_count(product_key: str, page_count: int) -> Tuple[bool, str]:
    """
    Validate page count against product limits.

    Returns (is_valid, message).
    """
    product = PRODUCTS[product_key]
    binding = product.binding

    if page_count < binding.min_pages:
        return False, f"Minimum {binding.min_pages} pages required for {binding.name}"

    if page_count > binding.max_pages:
        return False, f"Maximum {binding.max_pages} pages allowed for {binding.name}"

    return True, "Page count valid"


def list_products() -> None:
    """Print all available product presets."""
    print("Available Lulu Products:")
    print("-" * 60)
    for key, product in PRODUCTS.items():
        print(f"  {key}")
        print(f"    {product.name}")
        print(f"    Trim: {product.trim.width}\" x {product.trim.height}\"")
        print(f"    pod_package_id: {product.pod_package_id}")
        print()


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        product_key = sys.argv[1]
        page_count = int(sys.argv[2]) if len(sys.argv) > 2 else 200

        if product_key in PRODUCTS:
            print(f"Product: {PRODUCTS[product_key].name}")
            print(f"pod_package_id: {PRODUCTS[product_key].pod_package_id}")
            print(f"Page dimensions (with bleed): {get_page_dimensions(product_key)}")
            print(f"Spine width ({page_count} pages): {get_spine_width(product_key, page_count):.3f}\"")
            print(f"Cover dimensions: {get_cover_dimensions(product_key, page_count)}")
            print()
            print("CSS:")
            print(generate_page_css(product_key, page_count))
        else:
            print(f"Unknown product: {product_key}")
            print()
            list_products()
    else:
        list_products()
