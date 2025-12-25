#!/usr/bin/env python3
"""
Pumbo.nl Print-on-Demand specifications for BookCrafter.

Pumbo is a Dutch POD service for trade books (novels, non-fiction).
No public API, but we can generate compliant PDFs.

Specs source: https://www.pumbo.nl/support/cover
"""

from dataclasses import dataclass
from typing import Dict, Tuple


# =============================================================================
# Constants (Pumbo uses metric)
# =============================================================================

BLEED_MM = 3.0  # mm, all sides
SAFETY_MARGIN_MM = 5.0  # mm, minimum from trim edge
SPINE_GLUE_MARGIN_MM = 5.0  # mm, white space for glue at spine

# Conversion
MM_TO_INCH = 0.0393701
INCH_TO_MM = 25.4


# =============================================================================
# Paper Types with Bulk Factor (opdikkingsfactor)
# =============================================================================

@dataclass
class PaperType:
    """Paper specification with bulk factor."""
    name: str
    name_nl: str
    weight_gsm: int  # grams per square meter
    bulk_factor: float  # opdikkingsfactor
    coated: bool
    color: str  # "white", "cream", "natural"
    color_profile: str  # FOGRA profile

    @property
    def thickness_mm_per_sheet(self) -> float:
        """Calculate paper thickness per sheet (2 pages) in mm."""
        # Formula: (weight_gsm / 1000) * bulk_factor
        return (self.weight_gsm / 1000) * self.bulk_factor

    @property
    def thickness_mm_per_page(self) -> float:
        """Calculate paper thickness per page in mm."""
        return self.thickness_mm_per_sheet / 2


PAPER_TYPES: Dict[str, PaperType] = {
    # Uncoated - White
    "hvo_80_white": PaperType(
        "Offset White 80gsm", "HVO wit 80 grs",
        80, 1.30, False, "white", "Uncoated FOGRA 29"
    ),
    "hvo_90_white": PaperType(
        "Offset White 90gsm", "HVO wit 90 grs",
        90, 1.30, False, "white", "Uncoated FOGRA 29"
    ),
    "hvo_100_white": PaperType(
        "Offset White 100gsm", "HVO wit 100 grs",
        100, 1.30, False, "white", "Uncoated FOGRA 29"
    ),
    "hvo_120_white": PaperType(
        "Offset White 120gsm", "HVO wit 120 grs",
        120, 1.30, False, "white", "Uncoated FOGRA 29"
    ),

    # Uncoated - Natural/Cream
    "hvo_80_natural": PaperType(
        "Offset Natural 80gsm", "HVO naturel 80 grs",
        80, 1.30, False, "natural", "Uncoated FOGRA 29"
    ),
    "hvo_90_natural": PaperType(
        "Offset Natural 90gsm", "HVO naturel 90 grs",
        90, 1.30, False, "natural", "Uncoated FOGRA 29"
    ),

    # Romandruk (Novel paper - bulky)
    "romandruk_90": PaperType(
        "Novel Paper 90gsm", "Romandruk 90 grs",
        90, 1.95, False, "cream", "Uncoated FOGRA 29"
    ),

    # Coated (for color printing)
    "mc_115_silk": PaperType(
        "Silk Coated 115gsm", "MC half mat 115 grs",
        115, 1.01, True, "white", "Coated FOGRA 39"
    ),
    "mc_135_silk": PaperType(
        "Silk Coated 135gsm", "MC half mat 135 grs",
        135, 1.01, True, "white", "Coated FOGRA 39"
    ),
    "mc_170_silk": PaperType(
        "Silk Coated 170gsm", "MC half mat 170 grs",
        170, 1.01, True, "white", "Coated FOGRA 39"
    ),
}


# =============================================================================
# Common Book Formats (Pumbo is flexible, these are typical)
# =============================================================================

@dataclass
class BookFormat:
    """Book format specification."""
    name: str
    name_nl: str
    width_mm: float
    height_mm: float
    typical_use: str


FORMATS: Dict[str, BookFormat] = {
    # Standard formats
    "a5": BookFormat("A5", "A5", 148, 210, "Novels, general"),
    "a5_pumbo": BookFormat("A5 Pumbo", "A5 Pumbo", 145, 207, "Pumbo standard (3mm smaller)"),
    "b5": BookFormat("B5", "B5", 176, 250, "Textbooks, manuals"),
    "a4": BookFormat("A4", "A4", 210, 297, "Workbooks, portfolios"),

    # Trade book formats
    "pocket": BookFormat("Pocket", "Pocket", 110, 178, "Mass market paperback"),
    "royal": BookFormat("Royal", "Royal", 156, 234, "Trade paperback"),
    "crown": BookFormat("Crown", "Crown", 135, 216, "Literary fiction"),

    # Square
    "square_200": BookFormat("Square 20cm", "Vierkant 20cm", 200, 200, "Photo books, art"),
    "square_150": BookFormat("Square 15cm", "Vierkant 15cm", 150, 150, "Gift books"),

    # Custom - Pumbo accepts any size to the millimeter
}


# =============================================================================
# Binding Types
# =============================================================================

@dataclass
class BindingType:
    """Binding specification."""
    name: str
    name_nl: str
    min_pages: int
    max_pages: int  # POD max is ~500 pages (5cm spine)
    has_spine: bool
    cover_wrap_mm: float  # Extra for cover wrap (hardcover)


BINDING_TYPES: Dict[str, BindingType] = {
    "paperback": BindingType("Paperback", "Paperback", 24, 800, True, 0),
    "hardcover": BindingType("Hardcover", "Hardcover", 24, 600, True, 15),  # 15mm wrap
    "ringband": BindingType("Ring Binding", "Ringband", 8, 300, False, 0),
}


# =============================================================================
# Product Configuration
# =============================================================================

@dataclass
class PumboProduct:
    """Complete Pumbo product specification."""
    name: str
    format: BookFormat
    paper: PaperType
    binding: BindingType
    color_interior: bool  # Full color or B&W

    def get_spine_width_mm(self, page_count: int) -> float:
        """Calculate spine width in mm based on page count."""
        # Each sheet = 2 pages
        sheets = page_count / 2
        return sheets * self.paper.thickness_mm_per_sheet

    def get_cover_dimensions_mm(self, page_count: int) -> Dict[str, float]:
        """Calculate full cover spread dimensions in mm."""
        spine = self.get_spine_width_mm(page_count)
        wrap = self.binding.cover_wrap_mm

        if self.binding.name == "Hardcover":
            # Hardcover has extra wrap
            cover_width = (2 * self.format.width_mm) + spine + (2 * wrap) + (2 * BLEED_MM)
            cover_height = self.format.height_mm + (2 * wrap) + (2 * BLEED_MM)
        else:
            # Paperback
            cover_width = (2 * self.format.width_mm) + spine + (2 * BLEED_MM)
            cover_height = self.format.height_mm + (2 * BLEED_MM)

        return {
            "width_mm": cover_width,
            "height_mm": cover_height,
            "spine_width_mm": spine,
            "spine_start_mm": self.format.width_mm + BLEED_MM,
            "front_start_mm": self.format.width_mm + BLEED_MM + spine,
        }


# =============================================================================
# Common Product Presets
# =============================================================================

PRODUCTS: Dict[str, PumboProduct] = {
    # Paperback B&W - Offset paper
    "a5_paperback_bw": PumboProduct(
        "A5 Paperback B&W",
        FORMATS["a5_pumbo"],
        PAPER_TYPES["hvo_90_white"],
        BINDING_TYPES["paperback"],
        color_interior=False,
    ),
    "a5_paperback_cream": PumboProduct(
        "A5 Paperback Cream",
        FORMATS["a5_pumbo"],
        PAPER_TYPES["hvo_90_natural"],
        BINDING_TYPES["paperback"],
        color_interior=False,
    ),

    # Paperback B&W - Romandruk (bulky novel paper)
    "a5_paperback_roman": PumboProduct(
        "A5 Paperback Romandruk",
        FORMATS["a5_pumbo"],
        PAPER_TYPES["romandruk_90"],
        BINDING_TYPES["paperback"],
        color_interior=False,
    ),

    # Paperback Color
    "a5_paperback_color": PumboProduct(
        "A5 Paperback Color",
        FORMATS["a5_pumbo"],
        PAPER_TYPES["mc_135_silk"],
        BINDING_TYPES["paperback"],
        color_interior=True,
    ),

    # B5 format
    "b5_paperback_bw": PumboProduct(
        "B5 Paperback B&W",
        FORMATS["b5"],
        PAPER_TYPES["hvo_90_white"],
        BINDING_TYPES["paperback"],
        color_interior=False,
    ),

    # Royal (trade) format
    "royal_paperback_bw": PumboProduct(
        "Royal Paperback B&W",
        FORMATS["royal"],
        PAPER_TYPES["hvo_90_white"],
        BINDING_TYPES["paperback"],
        color_interior=False,
    ),
    "royal_paperback_roman": PumboProduct(
        "Royal Paperback Romandruk",
        FORMATS["royal"],
        PAPER_TYPES["romandruk_90"],
        BINDING_TYPES["paperback"],
        color_interior=False,
    ),

    # Hardcover
    "a5_hardcover_bw": PumboProduct(
        "A5 Hardcover B&W",
        FORMATS["a5_pumbo"],
        PAPER_TYPES["hvo_90_white"],
        BINDING_TYPES["hardcover"],
        color_interior=False,
    ),
    "a5_hardcover_color": PumboProduct(
        "A5 Hardcover Color",
        FORMATS["a5_pumbo"],
        PAPER_TYPES["mc_135_silk"],
        BINDING_TYPES["hardcover"],
        color_interior=True,
    ),
}


# =============================================================================
# CSS Generation
# =============================================================================

def generate_page_css(product_key: str, page_count: int = 200) -> str:
    """Generate CSS @page rules for Pumbo specifications."""
    product = PRODUCTS[product_key]
    fmt = product.format

    # Convert to inches for WeasyPrint
    width_in = fmt.width_mm * MM_TO_INCH
    height_in = fmt.height_mm * MM_TO_INCH
    bleed_in = BLEED_MM * MM_TO_INCH
    margin_in = SAFETY_MARGIN_MM * MM_TO_INCH

    # Gutter depends on book thickness
    spine_mm = product.get_spine_width_mm(page_count)
    gutter_mm = max(15, 10 + (spine_mm / 10))  # Minimum 15mm, grows with thickness
    gutter_in = gutter_mm * MM_TO_INCH

    return f"""
/* Pumbo.nl specifications for {product.name} */
/* Format: {fmt.width_mm}mm x {fmt.height_mm}mm */
/* Paper: {product.paper.name_nl} (bulk: {product.paper.bulk_factor}) */
/* Spine width ({page_count} pages): {spine_mm:.1f}mm */

@page {{
    size: {width_in:.4f}in {height_in:.4f}in;
    margin-top: {margin_in:.4f}in;
    margin-bottom: {margin_in:.4f}in;
    margin-outside: {margin_in:.4f}in;
    margin-inside: {gutter_in:.4f}in;

    /* Bleed: {BLEED_MM}mm */
    bleed: {bleed_in:.4f}in;
}}

@page :left {{
    margin-left: {gutter_in:.4f}in;
    margin-right: {margin_in:.4f}in;
}}

@page :right {{
    margin-left: {margin_in:.4f}in;
    margin-right: {gutter_in:.4f}in;
}}
"""


def generate_bleed_css() -> str:
    """Generate CSS for full-bleed elements (3mm Pumbo standard)."""
    bleed_in = BLEED_MM * MM_TO_INCH
    return f"""
/* Full bleed (3mm / {bleed_in:.4f}in) */
.full-bleed {{
    margin-left: -{bleed_in:.4f}in;
    margin-right: -{bleed_in:.4f}in;
    width: calc(100% + {2 * bleed_in:.4f}in);
}}
"""


# =============================================================================
# Validation
# =============================================================================

def validate_page_count(product_key: str, page_count: int) -> Tuple[bool, str]:
    """Validate page count against Pumbo limits."""
    product = PRODUCTS[product_key]
    binding = product.binding

    if page_count < binding.min_pages:
        return False, f"Minimum {binding.min_pages} pages required for {binding.name}"

    if page_count > binding.max_pages:
        return False, f"Maximum {binding.max_pages} pages allowed for {binding.name}"

    # Check spine width (max 50mm for POD)
    spine = product.get_spine_width_mm(page_count)
    if spine > 50:
        return False, f"Spine too thick ({spine:.1f}mm). Maximum 50mm for POD."

    return True, "Page count valid"


def get_file_requirements() -> str:
    """Return Pumbo file requirements summary."""
    return """
Pumbo.nl File Requirements:
===========================

INTERIOR (binnenwerk):
- Single PDF, all pages sequential (not spreads)
- 3mm bleed, content must extend into bleed
- Crop marks required
- Safety margin: 5mm from trim edge
- Fonts embedded
- B&W interior: use K only (no CMY)
- Color profile: Uncoated FOGRA 29 (uncoated) or Coated FOGRA 39 (coated)
- Images: 300 DPI preferred, 150 DPI minimum
- Lines: minimum 0.3mm, 100% K
- Ink coverage: max 300%

COVER (omslag):
- Single PDF: back + spine + front as one spread
- 3mm bleed on all outside edges
- Safety margin: 5mm from trim edge
- Use Coated FOGRA 39 (always)
- Spine: let colors extend across (1-2mm binding variance)
- If printing inside cover: leave spine + 5mm each side white for glue

Cover calculator: https://www.pumbo.nl/support/cover
"""


def list_products() -> None:
    """Print all available Pumbo product presets."""
    print("Available Pumbo Products:")
    print("-" * 60)
    for key, product in PRODUCTS.items():
        spine_200 = product.get_spine_width_mm(200)
        print(f"  {key}")
        print(f"    {product.name}")
        print(f"    Format: {product.format.width_mm}mm x {product.format.height_mm}mm")
        print(f"    Paper: {product.paper.name_nl}")
        print(f"    Spine (200 pages): {spine_200:.1f}mm")
        print()


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "--requirements":
            print(get_file_requirements())
        else:
            product_key = sys.argv[1]
            page_count = int(sys.argv[2]) if len(sys.argv) > 2 else 200

            if product_key in PRODUCTS:
                product = PRODUCTS[product_key]
                cover = product.get_cover_dimensions_mm(page_count)

                print(f"Product: {product.name}")
                print(f"Format: {product.format.width_mm}mm x {product.format.height_mm}mm")
                print(f"Paper: {product.paper.name_nl}")
                print(f"Bulk factor: {product.paper.bulk_factor}")
                print()
                print(f"Spine width ({page_count} pages): {cover['spine_width_mm']:.1f}mm")
                print(f"Cover spread: {cover['width_mm']:.1f}mm x {cover['height_mm']:.1f}mm")
                print()
                print("CSS:")
                print(generate_page_css(product_key, page_count))
            else:
                print(f"Unknown product: {product_key}")
                print()
                list_products()
    else:
        list_products()
