#!/usr/bin/env python3
"""
BookCrafter Typography System

Adapted from TokenMoulds FormulaicTokenEngine.
Generates a complete typography system from minimal inputs.

The system is based on:
- Baseline grid (default 18pt)
- Modular scale for font sizes
- Spacing scale for vertical rhythm
- Density axis (tight → normal → loose)
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
from pathlib import Path


# =============================================================================
# Scales
# =============================================================================

# Typography scale multipliers (for font sizes)
# Based on musical intervals / golden ratio approximations
TYPE_SCALE = [0.75, 0.875, 1, 1.125, 1.25, 1.5, 1.75, 2, 2.5, 3]

# Spacing scale multipliers (for margins, padding, gaps)
SPACE_SCALE = [0.25, 0.5, 0.75, 1, 1.5, 2, 3, 4, 6, 8]

# Density presets
DENSITY_PRESETS = {
    "tight": {
        "name": "Tight",
        "description": "Dense academic text, reference books, pocket editions",
        "line_height_body": 1.2,
        "line_height_heading": 1.1,
        "para_spacing_factor": 0.5,
        "margin_factor": 0.85,
        "base_size_pt": 10,
    },
    "snug": {
        "name": "Snug",
        "description": "Compact but readable, mass market paperbacks",
        "line_height_body": 1.3,
        "line_height_heading": 1.15,
        "para_spacing_factor": 0.75,
        "margin_factor": 0.9,
        "base_size_pt": 11,
    },
    "normal": {
        "name": "Normal",
        "description": "Standard trade books, novels, general non-fiction",
        "line_height_body": 1.4,
        "line_height_heading": 1.2,
        "para_spacing_factor": 1.0,
        "margin_factor": 1.0,
        "base_size_pt": 12,
    },
    "relaxed": {
        "name": "Relaxed",
        "description": "Easy reading, older audiences, quality editions",
        "line_height_body": 1.5,
        "line_height_heading": 1.25,
        "para_spacing_factor": 1.25,
        "margin_factor": 1.1,
        "base_size_pt": 13,
    },
    "loose": {
        "name": "Loose",
        "description": "Large print, children's books, luxury editions",
        "line_height_body": 1.6,
        "line_height_heading": 1.3,
        "para_spacing_factor": 1.5,
        "margin_factor": 1.2,
        "base_size_pt": 14,
    },
}


# =============================================================================
# Font Pairs
# =============================================================================

# Reference x-height ratio for optical size normalization
# Fonts with smaller x-height will be scaled up to appear equivalent
REFERENCE_X_HEIGHT = 0.50

@dataclass
class FontPair:
    """A curated font pairing for books."""
    name: str
    display: str  # For headings, titles
    body: str  # For body text
    style: str  # Description
    fallback_display: str = "Georgia"
    fallback_body: str = "Georgia"
    # X-height ratios (extracted from font files, or estimated)
    # These are used for optical size normalization
    display_x_height: float = 0.50  # Default/fallback
    body_x_height: float = 0.50  # Default/fallback

    def optical_adjustment(self, reference: float = REFERENCE_X_HEIGHT) -> float:
        """
        Calculate optical size adjustment for body font.

        Returns multiplier to apply to base size so fonts with different
        x-heights appear optically equivalent.
        """
        if self.body_x_height <= 0:
            return 1.0
        return reference / self.body_x_height


# X-height ratios extracted from font files
# Run `python font_metrics.py extract` to update from actual fonts
FONT_X_HEIGHTS = {
    # Serif fonts (extracted 2025-12-25)
    "Playfair Display": 0.514,
    "Lora": 0.500,
    "Libre Baskerville": 0.530,
    "Crimson Text": 0.420,  # Smallest x-height - elegant
    "Merriweather": 0.555,  # Large x-height - very readable
    "Source Serif 4": 0.475,
    "Source Serif Pro": 0.475,  # Alias
    "Spectral": 0.450,
    "PT Serif": 0.500,

    # Sans-serif fonts
    "Lato": 0.506,
    "Open Sans": 0.535,
    "Poppins": 0.548,
    "Inter": 0.546,  # Large x-height
    "Work Sans": 0.500,
    "Montserrat": 0.526,

    # Display fonts
    "Baloo Bhai 2": 0.460,
}


def _get_x_height(font_name: str) -> float:
    """Get x-height ratio for a font, with fallback."""
    return FONT_X_HEIGHTS.get(font_name, 0.50)


FONT_PAIRS: Dict[str, FontPair] = {
    # Serif pairs (classic book typography)
    "playfair-lora": FontPair(
        "Playfair + Lora",
        "Playfair Display", "Lora",
        "Elegant literary fiction",
        display_x_height=_get_x_height("Playfair Display"),
        body_x_height=_get_x_height("Lora"),
    ),
    "libre-crimson": FontPair(
        "Libre Baskerville + Crimson",
        "Libre Baskerville", "Crimson Text",
        "Classic traditional",
        display_x_height=_get_x_height("Libre Baskerville"),
        body_x_height=_get_x_height("Crimson Text"),
    ),
    "merriweather-merriweather": FontPair(
        "Merriweather",
        "Merriweather", "Merriweather",
        "Warm readable serif",
        display_x_height=_get_x_height("Merriweather"),
        body_x_height=_get_x_height("Merriweather"),
    ),
    "source-serif": FontPair(
        "Source Serif Pro",
        "Source Serif Pro", "Source Serif Pro",
        "Clean modern serif",
        display_x_height=_get_x_height("Source Serif Pro"),
        body_x_height=_get_x_height("Source Serif Pro"),
    ),
    "spectral-spectral": FontPair(
        "Spectral",
        "Spectral", "Spectral",
        "Refined book typography",
        display_x_height=_get_x_height("Spectral"),
        body_x_height=_get_x_height("Spectral"),
    ),

    # Mixed pairs (serif headings, sans body or vice versa)
    "playfair-lato": FontPair(
        "Playfair + Lato",
        "Playfair Display", "Lato",
        "Elegant with modern readability",
        display_x_height=_get_x_height("Playfair Display"),
        body_x_height=_get_x_height("Lato"),
    ),
    "merriweather-opensans": FontPair(
        "Merriweather + Open Sans",
        "Merriweather", "Open Sans",
        "Warm headers, clean body",
        display_x_height=_get_x_height("Merriweather"),
        body_x_height=_get_x_height("Open Sans"),
    ),
    "poppins-lora": FontPair(
        "Poppins + Lora",
        "Poppins", "Lora",
        "Modern headers, classic body",
        display_x_height=_get_x_height("Poppins"),
        body_x_height=_get_x_height("Lora"),
    ),

    # Sans pairs (modern non-fiction)
    "inter-inter": FontPair(
        "Inter",
        "Inter", "Inter",
        "Clean technical documentation",
        "Arial", "Arial",
        display_x_height=_get_x_height("Inter"),
        body_x_height=_get_x_height("Inter"),
    ),
    "work-sans-source": FontPair(
        "Work Sans + Source Serif",
        "Work Sans", "Source Serif Pro",
        "Professional business books",
        display_x_height=_get_x_height("Work Sans"),
        body_x_height=_get_x_height("Source Serif Pro"),
    ),

    # Your current default
    "baloo-montserrat": FontPair(
        "Baloo Bhai 2 + Montserrat",
        "Baloo Bhai 2", "Montserrat",
        "Distinctive warm display",
        display_x_height=_get_x_height("Baloo Bhai 2"),
        body_x_height=_get_x_height("Montserrat"),
    ),
}


# =============================================================================
# Typography System
# =============================================================================

@dataclass
class TypographySystem:
    """
    Complete typography system for a book.

    Generate from minimal inputs:
    - font_pair: Key from FONT_PAIRS
    - density: Key from DENSITY_PRESETS or custom value 0.0-1.0
    - base_size_pt: Override base font size (optional)
    - normalize_optical: Apply optical size adjustment based on x-height
    """

    font_pair: str = "merriweather-merriweather"
    density: str = "normal"
    base_size_pt: Optional[float] = None
    normalize_optical: bool = True  # Adjust for x-height differences

    # Computed values (populated by __post_init__)
    fonts: FontPair = field(init=False)
    density_config: Dict = field(init=False)
    baseline_pt: float = field(init=False)
    optical_factor: float = field(init=False)
    type_scale_pt: Dict[str, float] = field(init=False)
    space_scale_pt: Dict[str, float] = field(init=False)
    line_heights: Dict[str, float] = field(init=False)

    def __post_init__(self):
        # Get font pair
        self.fonts = FONT_PAIRS.get(self.font_pair, FONT_PAIRS["merriweather-merriweather"])

        # Get density config
        if isinstance(self.density, str):
            self.density_config = DENSITY_PRESETS.get(self.density, DENSITY_PRESETS["normal"])
        else:
            # Interpolate between presets based on numeric value
            self.density_config = self._interpolate_density(self.density)

        # Calculate optical size adjustment
        self.optical_factor = self.fonts.optical_adjustment() if self.normalize_optical else 1.0

        # Set baseline (base font size), applying optical adjustment
        raw_baseline = self.base_size_pt or self.density_config["base_size_pt"]
        self.baseline_pt = round(raw_baseline * self.optical_factor, 2)

        # Generate scales
        self._generate_scales()

    def _interpolate_density(self, value: float) -> Dict:
        """Interpolate between tight (0.0) and loose (1.0)."""
        # Clamp to 0-1
        value = max(0.0, min(1.0, value))

        # Define the gradient
        presets = ["tight", "snug", "normal", "relaxed", "loose"]
        positions = [0.0, 0.25, 0.5, 0.75, 1.0]

        # Find which two presets to interpolate between
        for i in range(len(positions) - 1):
            if positions[i] <= value <= positions[i + 1]:
                t = (value - positions[i]) / (positions[i + 1] - positions[i])
                p1 = DENSITY_PRESETS[presets[i]]
                p2 = DENSITY_PRESETS[presets[i + 1]]

                return {
                    "name": f"Custom ({value:.2f})",
                    "description": "Interpolated density",
                    "line_height_body": p1["line_height_body"] + t * (p2["line_height_body"] - p1["line_height_body"]),
                    "line_height_heading": p1["line_height_heading"] + t * (p2["line_height_heading"] - p1["line_height_heading"]),
                    "para_spacing_factor": p1["para_spacing_factor"] + t * (p2["para_spacing_factor"] - p1["para_spacing_factor"]),
                    "margin_factor": p1["margin_factor"] + t * (p2["margin_factor"] - p1["margin_factor"]),
                    "base_size_pt": p1["base_size_pt"] + t * (p2["base_size_pt"] - p1["base_size_pt"]),
                }

        return DENSITY_PRESETS["normal"]

    def _generate_scales(self):
        """Generate the type and spacing scales."""
        # Type scale (font sizes)
        self.type_scale_pt = {}
        for i, multiplier in enumerate(TYPE_SCALE):
            size = round(self.baseline_pt * multiplier, 2)
            self.type_scale_pt[f"size-{i+1}"] = size

        # Also add semantic names
        self.type_scale_pt["small"] = self.type_scale_pt["size-1"]  # 0.75x
        self.type_scale_pt["caption"] = self.type_scale_pt["size-2"]  # 0.875x
        self.type_scale_pt["body"] = self.type_scale_pt["size-3"]  # 1x
        self.type_scale_pt["lead"] = self.type_scale_pt["size-4"]  # 1.125x
        self.type_scale_pt["h6"] = self.type_scale_pt["size-5"]  # 1.25x
        self.type_scale_pt["h5"] = self.type_scale_pt["size-6"]  # 1.5x
        self.type_scale_pt["h4"] = self.type_scale_pt["size-7"]  # 1.75x
        self.type_scale_pt["h3"] = self.type_scale_pt["size-8"]  # 2x
        self.type_scale_pt["h2"] = self.type_scale_pt["size-9"]  # 2.5x
        self.type_scale_pt["h1"] = self.type_scale_pt["size-10"]  # 3x

        # Spacing scale
        para_factor = self.density_config["para_spacing_factor"]
        self.space_scale_pt = {}
        for i, multiplier in enumerate(SPACE_SCALE):
            space = round(self.baseline_pt * multiplier * para_factor, 2)
            self.space_scale_pt[f"space-{i+1}"] = space

        # Semantic spacing names
        self.space_scale_pt["xs"] = self.space_scale_pt["space-1"]
        self.space_scale_pt["sm"] = self.space_scale_pt["space-2"]
        self.space_scale_pt["md"] = self.space_scale_pt["space-4"]  # = baseline
        self.space_scale_pt["lg"] = self.space_scale_pt["space-6"]
        self.space_scale_pt["xl"] = self.space_scale_pt["space-8"]
        self.space_scale_pt["2xl"] = self.space_scale_pt["space-10"]

        # Line heights
        self.line_heights = {
            "tight": 1.1,
            "heading": self.density_config["line_height_heading"],
            "body": self.density_config["line_height_body"],
            "loose": 1.8,
        }

        # Calculate baseline grid
        self._calculate_baseline_grid()

    def _calculate_baseline_grid(self):
        """
        Calculate baseline grid and heading snap margins.

        The baseline grid ensures all text aligns to a consistent vertical rhythm.
        Headings must have margins calculated so following text lands on grid.
        """
        # Baseline unit = body size × body line-height
        body_size = self.type_scale_pt["body"]
        body_lh = self.line_heights["body"]
        self.baseline_unit_pt = round(body_size * body_lh, 3)

        # Calculate heading snap for each heading level
        # Each heading needs: margin-top (visual space) + margin-bottom (snap to grid)
        heading_lh = self.line_heights["heading"]

        self.heading_grid = {}

        for level in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            size = self.type_scale_pt[level]

            # Natural height of heading (size × heading line-height)
            natural_height = size * heading_lh

            # How many baseline units does this span? Round up.
            baseline_spans = natural_height / self.baseline_unit_pt
            snapped_spans = int(baseline_spans) + (1 if baseline_spans % 1 > 0.01 else 0)

            # Total height needed to snap to grid
            snapped_height = snapped_spans * self.baseline_unit_pt

            # Padding needed to reach grid
            snap_padding = snapped_height - natural_height

            # Determine margin-top (visual separation) based on heading level
            # Larger headings get more space above
            margin_top_baselines = {
                "h1": 4,  # Chapter headings: lots of space
                "h2": 3,
                "h3": 2,
                "h4": 2,
                "h5": 1,
                "h6": 1,
            }

            margin_top = margin_top_baselines[level] * self.baseline_unit_pt

            # margin-bottom = snap_padding (to land next text on grid)
            # If snap_padding is tiny, add a full baseline for readability
            margin_bottom = snap_padding if snap_padding >= self.baseline_unit_pt * 0.25 else snap_padding + self.baseline_unit_pt

            self.heading_grid[level] = {
                "size_pt": size,
                "natural_height_pt": round(natural_height, 3),
                "baseline_spans": snapped_spans,
                "snapped_height_pt": round(snapped_height, 3),
                "margin_top_pt": round(margin_top, 3),
                "margin_bottom_pt": round(margin_bottom, 3),
                "total_height_pt": round(margin_top + snapped_height + margin_bottom, 3),
            }

        # Paragraph spacing (1 baseline between paragraphs)
        self.para_margin_pt = self.baseline_unit_pt

    def to_css_variables(self) -> str:
        """Generate CSS custom properties with baseline grid."""
        lines = [
            "/* BookCrafter Typography System */",
            f"/* Font pair: {self.fonts.name} */",
            f"/* Density: {self.density_config['name']} */",
            f"/* Baseline grid: {self.baseline_unit_pt}pt */",
            "",
            ":root {",
            "    /* Fonts */",
            f'    --font-display: "{self.fonts.display}", {self.fonts.fallback_display}, serif;',
            f'    --font-body: "{self.fonts.body}", {self.fonts.fallback_body}, serif;',
            "",
            "    /* Baseline Grid */",
            f"    --baseline-unit: {self.baseline_unit_pt}pt;",
            f"    --body-size: {self.type_scale_pt['body']}pt;",
            "",
            "    /* Type Scale */",
        ]

        for name, size in self.type_scale_pt.items():
            lines.append(f"    --{name}: {size}pt;")

        lines.extend([
            "",
            "    /* Heading Grid Margins (snapped to baseline) */",
        ])

        for level in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            grid = self.heading_grid[level]
            lines.append(f"    --{level}-margin-top: {grid['margin_top_pt']}pt;")
            lines.append(f"    --{level}-margin-bottom: {grid['margin_bottom_pt']}pt;")

        lines.extend([
            "",
            "    /* Spacing Scale (baseline multiples) */",
        ])

        for name, space in self.space_scale_pt.items():
            lines.append(f"    --{name}: {space}pt;")

        lines.extend([
            "",
            "    /* Line Heights */",
        ])

        for name, lh in self.line_heights.items():
            lines.append(f"    --line-height-{name}: {lh};")

        lines.extend([
            "}",
            "",
            "/* ==========================================================================",
            "   Baseline Grid Typography",
            "   All vertical spacing aligns to the baseline grid.",
            "   ========================================================================== */",
            "",
            "body {",
            "    font-family: var(--font-body);",
            "    font-size: var(--body-size);",
            "    line-height: var(--line-height-body);",
            "}",
            "",
            "/* Paragraphs: 1 baseline between */",
            "p {",
            "    margin-top: 0;",
            "    margin-bottom: var(--baseline-unit);",
            "}",
            "",
            "/* Remove margin from last paragraph in container */",
            "p:last-child {",
            "    margin-bottom: 0;",
            "}",
            "",
            "/* Headings: calculated margins to snap following text to grid */",
            "h1, h2, h3, h4, h5, h6 {",
            "    font-family: var(--font-display);",
            "    line-height: var(--line-height-heading);",
            "}",
            "",
        ])

        # Generate individual heading rules with calculated margins
        for level in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            grid = self.heading_grid[level]
            lines.extend([
                f"{level} {{",
                f"    font-size: var(--{level});",
                f"    margin-top: var(--{level}-margin-top);",
                f"    margin-bottom: var(--{level}-margin-bottom);",
                "}",
                "",
            ])

        # First heading on page (no top margin)
        lines.extend([
            "/* First heading on page/section: no top margin */",
            ".chapter > h1:first-child,",
            "section > h1:first-child,",
            "article > h1:first-child,",
            ".frontmatter h1:first-child {",
            "    margin-top: 0;",
            "}",
            "",
            "/* Lists: align to baseline */",
            "ul, ol {",
            "    margin-top: 0;",
            "    margin-bottom: var(--baseline-unit);",
            "    padding-left: calc(var(--baseline-unit) * 1.5);",
            "}",
            "",
            "li {",
            "    margin-bottom: calc(var(--baseline-unit) * 0.5);",
            "}",
            "",
            "li:last-child {",
            "    margin-bottom: 0;",
            "}",
            "",
            "/* Blockquotes: indented, baseline-aligned */",
            "blockquote {",
            "    margin-top: var(--baseline-unit);",
            "    margin-bottom: var(--baseline-unit);",
            "    margin-left: var(--baseline-unit);",
            "    padding-left: var(--baseline-unit);",
            "    border-left: 2pt solid currentColor;",
            "}",
            "",
            "/* Lead paragraph */",
            ".lead {",
            "    font-size: var(--lead);",
            "}",
            "",
            "/* Small text */",
            ".small, small, figcaption {",
            "    font-size: var(--small);",
            "}",
            "",
            ".caption {",
            "    font-size: var(--caption);",
            "    color: var(--color-muted, #666);",
            "}",
        ])

        return "\n".join(lines)

    def to_css_debug_grid(self) -> str:
        """Generate CSS for debug baseline grid overlay."""
        return f"""
/* Debug: Baseline Grid Overlay
   Add class="show-grid" to body to display */
body.show-grid {{
    background-image: linear-gradient(
        to bottom,
        rgba(200, 50, 50, 0.15) 1px,
        transparent 1px
    );
    background-size: 100% {self.baseline_unit_pt}pt;
    background-position: 0 0;
}}

/* Alternative: highlight each baseline */
body.show-grid-lines {{
    background-image: repeating-linear-gradient(
        to bottom,
        transparent 0,
        transparent calc({self.baseline_unit_pt}pt - 1px),
        rgba(200, 50, 50, 0.3) calc({self.baseline_unit_pt}pt - 1px),
        rgba(200, 50, 50, 0.3) {self.baseline_unit_pt}pt
    );
}}
"""

    def to_css_page_rules(self, page_width_in: float, page_height_in: float) -> str:
        """Generate @page rules with typography-aware margins."""
        margin_factor = self.density_config["margin_factor"]

        # Base margins in inches, scaled by density
        margin_top = round(0.75 * margin_factor, 3)
        margin_bottom = round(0.875 * margin_factor, 3)
        margin_outside = round(0.625 * margin_factor, 3)
        margin_inside = round(0.875 * margin_factor, 3)  # Gutter

        return f"""
@page {{
    size: {page_width_in}in {page_height_in}in;
    margin-top: {margin_top}in;
    margin-bottom: {margin_bottom}in;
    margin-outside: {margin_outside}in;
    margin-inside: {margin_inside}in;
}}

@page :left {{
    margin-left: {margin_inside}in;
    margin-right: {margin_outside}in;
}}

@page :right {{
    margin-left: {margin_outside}in;
    margin-right: {margin_inside}in;
}}
"""

    def summary(self) -> str:
        """Return a human-readable summary."""
        optical_info = ""
        if self.normalize_optical and self.optical_factor != 1.0:
            optical_info = f" (optical: {self.optical_factor:.2f}x)"

        # Build heading grid table
        heading_lines = []
        for level in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            g = self.heading_grid[level]
            heading_lines.append(
                f"  {level}: {g['size_pt']:>5.1f}pt  "
                f"↑{g['margin_top_pt']:>5.1f}  ↓{g['margin_bottom_pt']:>5.1f}  "
                f"({g['baseline_spans']} baselines)"
            )

        return f"""Typography System Summary
========================
Font Pair: {self.fonts.name}
  Display: {self.fonts.display} (x: {self.fonts.display_x_height:.3f})
  Body: {self.fonts.body} (x: {self.fonts.body_x_height:.3f}){optical_info}

Density: {self.density_config['name']}
  {self.density_config['description']}

Baseline Grid:
  Body: {self.type_scale_pt['body']}pt × {self.line_heights['body']} = {self.baseline_unit_pt}pt
  Paragraph spacing: {self.para_margin_pt}pt

Heading Grid (size, margin-top, margin-bottom):
{chr(10).join(heading_lines)}

Type Scale:
  body:    {self.type_scale_pt['body']}pt
  lead:    {self.type_scale_pt['lead']}pt
  h6-h1:   {self.type_scale_pt['h6']}pt → {self.type_scale_pt['h1']}pt

Line Heights:
  heading: {self.line_heights['heading']}
  body:    {self.line_heights['body']}
"""

    def to_dict(self) -> Dict:
        """Export as dictionary."""
        return {
            "font_pair": self.font_pair,
            "fonts": {
                "display": self.fonts.display,
                "body": self.fonts.body,
            },
            "density": self.density,
            "density_config": self.density_config,
            "baseline_pt": self.baseline_pt,
            "type_scale_pt": self.type_scale_pt,
            "space_scale_pt": self.space_scale_pt,
            "line_heights": self.line_heights,
        }


# =============================================================================
# Convenience functions
# =============================================================================

def list_font_pairs():
    """Print available font pairs."""
    print("Available Font Pairs:")
    print("-" * 60)
    for key, pair in FONT_PAIRS.items():
        optical = pair.optical_adjustment()
        optical_note = f" (optical: {optical:.2f}x)" if optical != 1.0 else ""
        print(f"  {key}")
        print(f"    {pair.name}")
        print(f"    Display: {pair.display} (x: {pair.display_x_height:.3f})")
        print(f"    Body: {pair.body} (x: {pair.body_x_height:.3f}){optical_note}")
        print(f"    Style: {pair.style}")
        print()


def list_densities():
    """Print available density presets."""
    print("Available Density Presets:")
    print("-" * 50)
    for key, preset in DENSITY_PRESETS.items():
        print(f"  {key}")
        print(f"    {preset['name']}: {preset['description']}")
        print(f"    Base size: {preset['base_size_pt']}pt")
        print(f"    Line height: {preset['line_height_body']}")
        print()


def update_x_heights_from_fonts(fonts_dir: Path = None):
    """
    Update FONT_X_HEIGHTS from actual font files.

    This reads TTF files and extracts real x-height ratios.
    """
    try:
        from font_metrics import extract_all_fonts
    except ImportError:
        print("font_metrics module not available")
        return

    if fonts_dir is None:
        fonts_dir = Path(__file__).parent / "fonts"

    print(f"Extracting x-heights from {fonts_dir}...")
    metrics = extract_all_fonts(fonts_dir)

    if not metrics:
        print("No fonts found. Run: python font_downloader.py download-all")
        return

    print("\nExtracted x-height ratios:")
    print("-" * 50)
    for key, m in sorted(metrics.items()):
        print(f'    "{m.family_name}": {m.x_height_ratio:.3f},')

    print("\nCopy these values to FONT_X_HEIGHTS in typography.py")


def compare_densities(font_pair: str = "merriweather-merriweather"):
    """Compare all density presets side by side."""
    print(f"Density Comparison ({FONT_PAIRS[font_pair].name})")
    print("=" * 70)

    print(f"{'':15} {'tight':>10} {'snug':>10} {'normal':>10} {'relaxed':>10} {'loose':>10}")
    print("-" * 70)

    systems = {d: TypographySystem(font_pair, d) for d in DENSITY_PRESETS.keys()}

    # Base size
    print(f"{'Base size':15}", end="")
    for d in DENSITY_PRESETS.keys():
        print(f"{systems[d].baseline_pt:>10.1f}", end="")
    print(" pt")

    # Line height body
    print(f"{'Line height':15}", end="")
    for d in DENSITY_PRESETS.keys():
        print(f"{systems[d].line_heights['body']:>10.2f}", end="")
    print()

    # H1 size
    print(f"{'H1 size':15}", end="")
    for d in DENSITY_PRESETS.keys():
        print(f"{systems[d].type_scale_pt['h1']:>10.1f}", end="")
    print(" pt")

    # Body size
    print(f"{'Body size':15}", end="")
    for d in DENSITY_PRESETS.keys():
        print(f"{systems[d].type_scale_pt['body']:>10.1f}", end="")
    print(" pt")

    # Paragraph spacing
    print(f"{'Para spacing':15}", end="")
    for d in DENSITY_PRESETS.keys():
        print(f"{systems[d].space_scale_pt['md']:>10.1f}", end="")
    print(" pt")


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python typography.py <command> [options]")
        print()
        print("Commands:")
        print("  fonts              List available font pairs with x-heights")
        print("  densities          List density presets")
        print("  compare            Compare all densities")
        print("  generate <pair> <density>  Generate CSS")
        print("  summary <pair> <density>   Show summary")
        print("  extract-x-heights  Extract x-heights from font files")
        print()
        print("Examples:")
        print("  python typography.py fonts")
        print("  python typography.py compare")
        print("  python typography.py generate merriweather-merriweather normal")
        print("  python typography.py generate playfair-lora relaxed")
        print("  python typography.py summary playfair-lora normal")
        sys.exit(0)

    command = sys.argv[1]

    if command == "fonts":
        list_font_pairs()

    elif command == "densities":
        list_densities()

    elif command == "compare":
        font_pair = sys.argv[2] if len(sys.argv) > 2 else "merriweather-merriweather"
        compare_densities(font_pair)

    elif command == "generate":
        font_pair = sys.argv[2] if len(sys.argv) > 2 else "merriweather-merriweather"
        density = sys.argv[3] if len(sys.argv) > 3 else "normal"

        system = TypographySystem(font_pair, density)
        print(system.to_css_variables())

    elif command == "summary":
        font_pair = sys.argv[2] if len(sys.argv) > 2 else "merriweather-merriweather"
        density = sys.argv[3] if len(sys.argv) > 3 else "normal"

        system = TypographySystem(font_pair, density)
        print(system.summary())

    elif command == "extract-x-heights":
        update_x_heights_from_fonts()

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
