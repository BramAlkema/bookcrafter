#!/usr/bin/env python3
"""
Google Fonts downloader for BookCrafter.

Downloads font families from Google Fonts GitHub repository.
"""

from pathlib import Path
from typing import List, Dict
from urllib.request import urlopen, Request
from urllib.parse import quote


# =============================================================================
# Google Fonts Configuration
# =============================================================================

# Fonts needed for BookCrafter typography presets
# Format: "Font Name": ("github_path", "filename_pattern")
# filename_pattern: None = use standard naming, otherwise specific pattern
REQUIRED_FONTS: Dict[str, str] = {
    # Serif fonts (ofl = Open Font License)
    "Playfair Display": "ofl/playfairdisplay",
    "Lora": "ofl/lora",
    "Libre Baskerville": "ofl/librebaskerville",
    "Crimson Text": "ofl/crimsontext",
    "Merriweather": "ofl/merriweather",
    "Source Serif 4": "ofl/sourceserif4",  # Was "Source Serif Pro"
    "Spectral": "ofl/spectral",
    "PT Serif": "ofl/ptserif",  # Uses PT_Serif-Web-* naming

    # Sans-serif fonts
    "Lato": "ofl/lato",
    "Open Sans": "ofl/opensans",
    "Poppins": "ofl/poppins",
    "Inter": "ofl/inter",
    "Work Sans": "ofl/worksans",
    "Montserrat": "ofl/montserrat",

    # Display fonts
    "Baloo Bhai 2": "ofl/baloobhai2",
}

# Special naming patterns for some fonts
FONT_FILENAME_PATTERNS: Dict[str, List[str]] = {
    "PT Serif": ["PT_Serif-Web-Regular.ttf", "PT_Serif-Web-Bold.ttf"],
}

# Weights to download
WEIGHTS = ["Regular", "Bold"]

# User agent
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) BookCrafter/1.0"

# GitHub raw URL base
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/google/fonts/main"


# =============================================================================
# Download Functions
# =============================================================================

def download_font_file(url: str, target: Path) -> bool:
    """Download a single font file."""
    try:
        request = Request(url, headers={"User-Agent": USER_AGENT})
        response = urlopen(request, timeout=30)
        target.write_bytes(response.read())
        return True
    except Exception:
        return False


def download_font_family(family: str, output_dir: Path, weights: List[str] = None) -> bool:
    """
    Download a font family from Google Fonts GitHub repo.

    Handles both static TTF files and variable fonts.

    Args:
        family: Font family name (e.g., "Playfair Display")
        output_dir: Directory to save TTF files
        weights: List of weights to download (default: ["Regular", "Bold"])

    Returns:
        True if successful, False otherwise
    """
    if weights is None:
        weights = WEIGHTS

    output_dir.mkdir(parents=True, exist_ok=True)

    # Check if already downloaded
    family_slug = family.replace(" ", "")
    existing = list(output_dir.glob(f"{family_slug}*.ttf"))
    if len(existing) >= 1:  # Have at least one file
        print(f"  {family}: Already have {len(existing)} files")
        return True

    # Get GitHub path
    if family not in REQUIRED_FONTS:
        print(f"  {family}: Not in REQUIRED_FONTS, skipping")
        return False

    github_path = REQUIRED_FONTS[family]
    family_slug_clean = family.replace(" ", "")

    print(f"  {family}: Downloading from GitHub...")

    downloaded = 0

    # First try variable font (modern format)
    # Variable fonts have axis info in brackets - needs URL encoding
    variable_patterns = [
        # Simple weight-only variable
        f"{GITHUB_RAW_BASE}/{github_path}/{quote(family_slug_clean + '[wght].ttf')}",
        # Multi-axis variable fonts
        f"{GITHUB_RAW_BASE}/{github_path}/{quote(family_slug_clean + '[opsz,wdth,wght].ttf')}",
        f"{GITHUB_RAW_BASE}/{github_path}/{quote(family_slug_clean + '[opsz,wght].ttf')}",
        f"{GITHUB_RAW_BASE}/{github_path}/{quote(family_slug_clean + '[wdth,wght].ttf')}",
        f"{GITHUB_RAW_BASE}/{github_path}/{quote(family_slug_clean + '[slnt,wght].ttf')}",
        # Legacy format
        f"{GITHUB_RAW_BASE}/{github_path}/{family_slug_clean}-VariableFont_wght.ttf",
        f"{GITHUB_RAW_BASE}/{github_path}/{family_slug_clean}-VariableFont_opsz,wght.ttf",
    ]

    for url in variable_patterns:
        filename = f"{family_slug_clean}-Variable.ttf"
        target = output_dir / filename

        if download_font_file(url, target):
            print(f"    Downloaded: {filename} (variable)")
            downloaded += 1
            return True  # Variable font contains all weights

    # Check for special naming patterns
    if family in FONT_FILENAME_PATTERNS:
        for filename in FONT_FILENAME_PATTERNS[family]:
            url = f"{GITHUB_RAW_BASE}/{github_path}/{filename}"
            target = output_dir / filename.replace("_", "").replace("-Web", "")

            if target.exists():
                downloaded += 1
                continue

            if download_font_file(url, target):
                print(f"    Downloaded: {target.name}")
                downloaded += 1

        if downloaded > 0:
            print(f"  {family}: Got {downloaded} files")
            return True

    # Then try static fonts (older format)
    for weight in weights:
        patterns = [
            f"{GITHUB_RAW_BASE}/{github_path}/static/{family_slug_clean}-{weight}.ttf",
            f"{GITHUB_RAW_BASE}/{github_path}/{family_slug_clean}-{weight}.ttf",
        ]

        for url in patterns:
            filename = f"{family_slug_clean}-{weight}.ttf"
            target = output_dir / filename

            if target.exists():
                downloaded += 1
                break

            if download_font_file(url, target):
                print(f"    Downloaded: {filename}")
                downloaded += 1
                break

    if downloaded > 0:
        print(f"  {family}: Got {downloaded} files")
        return True
    else:
        print(f"  {family}: Could not download")
        return False


def download_all_fonts(output_dir: Path = None) -> dict:
    """
    Download all required fonts.

    Args:
        output_dir: Directory to save fonts (default: ./fonts)

    Returns:
        Dict of {font_name: success_bool}
    """
    if output_dir is None:
        output_dir = Path(__file__).parent / "fonts"

    print(f"Downloading {len(REQUIRED_FONTS)} font families to {output_dir}...")
    print()

    results = {}
    for family in REQUIRED_FONTS.keys():
        results[family] = download_font_family(family, output_dir)

    print()
    success = sum(1 for v in results.values() if v)
    print(f"Downloaded {success}/{len(REQUIRED_FONTS)} font families")

    return results


def list_downloaded_fonts(fonts_dir: Path = None) -> List[str]:
    """List all downloaded font families."""
    if fonts_dir is None:
        fonts_dir = Path(__file__).parent / "fonts"

    if not fonts_dir.exists():
        return []

    # Group by family
    families = set()
    for ttf in fonts_dir.glob("*.ttf"):
        # Extract family name (remove weight suffix)
        name = ttf.stem
        # Remove common suffixes
        for suffix in ['-Regular', '-Bold', '-Medium', '-Light', '-SemiBold',
                       '-Italic', '-BoldItalic', '_Regular', '_Bold']:
            name = name.replace(suffix, '')
        families.add(name)

    return sorted(families)


def list_required_fonts() -> List[str]:
    """List all required font names."""
    return list(REQUIRED_FONTS.keys())


# =============================================================================
# CLI
# =============================================================================

def main():
    """CLI interface."""
    import sys

    fonts_dir = Path(__file__).parent / "fonts"

    if len(sys.argv) < 2:
        print("Usage: python font_downloader.py <command> [font_name]")
        print()
        print("Commands:")
        print("  download-all    Download all required fonts from GitHub")
        print("  download <name> Download specific font family")
        print("  list            List downloaded fonts")
        print("  required        Show required fonts with GitHub paths")
        print()
        return

    command = sys.argv[1]

    if command == "download-all":
        download_all_fonts(fonts_dir)

    elif command == "download":
        if len(sys.argv) < 3:
            print("Usage: python font_downloader.py download <font_name>")
            return
        family = " ".join(sys.argv[2:])
        download_font_family(family, fonts_dir)

    elif command == "list":
        families = list_downloaded_fonts(fonts_dir)
        if families:
            print(f"Downloaded fonts ({len(families)}):")
            for f in families:
                print(f"  {f}")
        else:
            print("No fonts downloaded yet.")
            print("Run: python font_downloader.py download-all")

    elif command == "required":
        print(f"Required fonts ({len(REQUIRED_FONTS)}):")
        for name, path in REQUIRED_FONTS.items():
            print(f"  {name}")
            print(f"    GitHub: {path}")

    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
