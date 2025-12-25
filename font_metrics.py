#!/usr/bin/env python3
"""
Font metrics extraction for BookCrafter.

Extracts real font metrics (x-height, cap-height, ascender, descender)
from TTF files using fontTools. Based on TokenMoulds approach.
"""

import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, Optional

from fontTools.ttLib import TTFont


# =============================================================================
# Font Metrics
# =============================================================================

@dataclass
class FontMetrics:
    """Font metrics extracted from TTF file."""
    family_name: str
    style_name: str
    file_path: str
    weight: int

    # Core metrics in font units
    units_per_em: int
    x_height: float
    cap_height: float
    ascender: float
    descender: float
    line_gap: float

    @property
    def x_height_ratio(self) -> float:
        """X-height as ratio of units_per_em (typically 0.4-0.55)."""
        return self.x_height / self.units_per_em

    @property
    def cap_height_ratio(self) -> float:
        """Cap-height as ratio of units_per_em (typically 0.65-0.75)."""
        return self.cap_height / self.units_per_em

    def optical_size_factor(self, reference_x_ratio: float = 0.50) -> float:
        """
        Calculate optical size adjustment factor.

        Fonts with smaller x-height need larger point sizes to appear
        the same size as fonts with larger x-height.

        Args:
            reference_x_ratio: Reference x-height ratio (default 0.50)

        Returns:
            Multiplier to apply to point size (e.g., 1.1 means use 110%)
        """
        return reference_x_ratio / self.x_height_ratio


def extract_metrics(ttf_path: Path) -> Optional[FontMetrics]:
    """Extract metrics from a single TTF file."""
    try:
        font = TTFont(ttf_path)

        # Basic font info
        head = font['head']
        hhea = font['hhea']
        os2 = font.get('OS/2')
        name = font['name']

        # Extract font names
        family_name = _get_font_name(name, 1) or "Unknown"
        style_name = _get_font_name(name, 2) or "Regular"

        # Core metrics
        units_per_em = head.unitsPerEm

        # Get x-height and cap-height from OS/2 table if available
        if os2 and hasattr(os2, 'sxHeight') and os2.sxHeight > 0:
            x_height = float(os2.sxHeight)
        else:
            # Fallback: estimate as 50% of units_per_em
            x_height = float(units_per_em * 0.5)

        if os2 and hasattr(os2, 'sCapHeight') and os2.sCapHeight > 0:
            cap_height = float(os2.sCapHeight)
        else:
            # Fallback: estimate as 70% of units_per_em
            cap_height = float(units_per_em * 0.7)

        # Ascender and descender
        ascender = float(hhea.ascent)
        descender = float(hhea.descent)  # Usually negative
        line_gap = float(hhea.lineGap)

        # Determine weight
        weight = _determine_weight(ttf_path.name, os2)

        font.close()

        return FontMetrics(
            family_name=family_name,
            style_name=style_name,
            file_path=str(ttf_path),
            weight=weight,
            units_per_em=units_per_em,
            x_height=x_height,
            cap_height=cap_height,
            ascender=ascender,
            descender=descender,
            line_gap=line_gap,
        )

    except Exception as e:
        print(f"Error extracting metrics from {ttf_path}: {e}")
        return None


def _get_font_name(name_table, name_id: int) -> Optional[str]:
    """Extract font name from name table."""
    try:
        for record in name_table.names:
            if record.nameID == name_id and record.platformID == 3:
                return record.toUnicode()
    except Exception:
        pass
    return None


def _determine_weight(filename: str, os2_table) -> int:
    """Determine font weight from filename or OS/2 table."""
    # Try OS/2 table first
    if os2_table and hasattr(os2_table, 'usWeightClass'):
        return os2_table.usWeightClass

    # Fallback to filename parsing
    filename_lower = filename.lower()

    weight_map = {
        'thin': 100,
        'extralight': 200,
        'ultralight': 200,
        'light': 300,
        'regular': 400,
        'normal': 400,
        'medium': 500,
        'semibold': 600,
        'semi-bold': 600,
        'bold': 700,
        'extrabold': 800,
        'ultrabold': 800,
        'black': 900,
        'heavy': 900
    }

    for weight_name, weight_value in weight_map.items():
        if weight_name in filename_lower:
            return weight_value

    return 400  # Default to regular


# =============================================================================
# Metrics Cache
# =============================================================================

CACHE_FILE = Path(__file__).parent / "fonts" / "metrics_cache.json"


def load_metrics_cache() -> Dict[str, FontMetrics]:
    """Load cached metrics from JSON file."""
    if not CACHE_FILE.exists():
        return {}

    try:
        with open(CACHE_FILE) as f:
            data = json.load(f)

        metrics = {}
        for key, values in data.items():
            metrics[key] = FontMetrics(**values)
        return metrics
    except Exception as e:
        print(f"Error loading metrics cache: {e}")
        return {}


def save_metrics_cache(metrics: Dict[str, FontMetrics]) -> None:
    """Save metrics to JSON cache file."""
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

    data = {}
    for key, m in metrics.items():
        data[key] = asdict(m)

    with open(CACHE_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def get_font_metrics(font_name: str, fonts_dir: Path = None) -> Optional[FontMetrics]:
    """
    Get metrics for a font, using cache if available.

    Args:
        font_name: Font family name (e.g., "Merriweather", "Playfair Display")
        fonts_dir: Directory containing font files

    Returns:
        FontMetrics or None if font not found
    """
    if fonts_dir is None:
        fonts_dir = Path(__file__).parent / "fonts"

    # Check cache first
    cache = load_metrics_cache()
    cache_key = font_name.lower().replace(" ", "-")

    if cache_key in cache:
        return cache[cache_key]

    # Search for font file
    # Try various naming conventions
    patterns = [
        f"{font_name.replace(' ', '')}*.ttf",
        f"{font_name.replace(' ', '-')}*.ttf",
        f"{font_name.replace(' ', '_')}*.ttf",
    ]

    ttf_file = None
    for pattern in patterns:
        matches = list(fonts_dir.glob(pattern))
        # Prefer Regular weight
        for m in matches:
            if 'regular' in m.name.lower() or m.name.lower().endswith('-regular.ttf'):
                ttf_file = m
                break
        if ttf_file:
            break
        if matches:
            ttf_file = matches[0]
            break

    if not ttf_file:
        return None

    # Extract and cache
    metrics = extract_metrics(ttf_file)
    if metrics:
        cache[cache_key] = metrics
        save_metrics_cache(cache)

    return metrics


def extract_all_fonts(fonts_dir: Path = None) -> Dict[str, FontMetrics]:
    """Extract metrics from all TTF files in fonts directory."""
    if fonts_dir is None:
        fonts_dir = Path(__file__).parent / "fonts"

    metrics = {}
    for ttf_file in fonts_dir.glob("*.ttf"):
        m = extract_metrics(ttf_file)
        if m:
            key = m.family_name.lower().replace(" ", "-")
            # Keep Regular weight, or first found
            if key not in metrics or m.weight == 400:
                metrics[key] = m

    save_metrics_cache(metrics)
    return metrics


# =============================================================================
# CLI
# =============================================================================

def main():
    """CLI interface."""
    import sys

    fonts_dir = Path(__file__).parent / "fonts"

    if len(sys.argv) < 2:
        print("Usage: python font_metrics.py <command> [font_name]")
        print()
        print("Commands:")
        print("  extract    Extract metrics from all fonts in fonts/")
        print("  show       Show cached metrics")
        print("  get <name> Get metrics for specific font")
        print()
        return

    command = sys.argv[1]

    if command == "extract":
        print(f"Extracting metrics from {fonts_dir}...")
        metrics = extract_all_fonts(fonts_dir)
        print(f"\nExtracted {len(metrics)} fonts:")
        for key, m in sorted(metrics.items()):
            print(f"  {m.family_name}")
            print(f"    x-height ratio: {m.x_height_ratio:.3f}")
            print(f"    cap-height ratio: {m.cap_height_ratio:.3f}")
            print()

    elif command == "show":
        metrics = load_metrics_cache()
        if not metrics:
            print("No cached metrics. Run 'extract' first.")
            return

        print("Cached font metrics:")
        print("-" * 60)
        for key, m in sorted(metrics.items()):
            print(f"{m.family_name} ({m.style_name})")
            print(f"  Weight: {m.weight}")
            print(f"  Units/EM: {m.units_per_em}")
            print(f"  X-height: {m.x_height} ({m.x_height_ratio:.3f})")
            print(f"  Cap-height: {m.cap_height} ({m.cap_height_ratio:.3f})")
            print(f"  Optical factor: {m.optical_size_factor():.3f}")
            print()

    elif command == "get":
        if len(sys.argv) < 3:
            print("Usage: python font_metrics.py get <font_name>")
            return

        font_name = " ".join(sys.argv[2:])
        metrics = get_font_metrics(font_name, fonts_dir)

        if metrics:
            print(f"{metrics.family_name}")
            print(f"  X-height ratio: {metrics.x_height_ratio:.3f}")
            print(f"  Cap-height ratio: {metrics.cap_height_ratio:.3f}")
            print(f"  Optical size factor: {metrics.optical_size_factor():.3f}")
        else:
            print(f"Font not found: {font_name}")

    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
