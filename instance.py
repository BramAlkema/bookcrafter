#!/usr/bin/env python3
"""Instance management for BookCrafter."""

import sys
import importlib.util
from pathlib import Path

BASE_DIR = Path(__file__).parent.absolute()
INSTANCES_DIR = BASE_DIR / "instances"
STYLES_DIR = BASE_DIR / "styles"
FONTS_DIR = BASE_DIR / "fonts"

# Set by setup()
INSTANCE_DIR = None
CONTENT_DIR = None
INSTANCE_STYLES_DIR = None
ASSETS_DIR = None
OUTPUT_DIR = None
config = None


def setup(instance_name=None):
    """Set up paths for the specified instance."""
    global INSTANCE_DIR, CONTENT_DIR, INSTANCE_STYLES_DIR, ASSETS_DIR, OUTPUT_DIR, config

    if instance_name:
        INSTANCE_DIR = INSTANCES_DIR / instance_name
        if not INSTANCE_DIR.exists():
            print(f"Error: Instance '{instance_name}' not found in {INSTANCES_DIR}")
            print("Available instances:")
            list_instances()
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


def list_instances():
    """List available instances."""
    if not INSTANCES_DIR.exists():
        print("  (no instances directory)")
        return
    for d in sorted(INSTANCES_DIR.iterdir()):
        if d.is_dir() and (d / "book_config.py").exists():
            spec = importlib.util.spec_from_file_location("book_config", d / "book_config.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            title = module.config.get("title", "Untitled")
            print(f"  {d.name}: {title}")


def load_file(filename):
    """Load a content file from CONTENT_DIR."""
    filepath = CONTENT_DIR / filename
    if filepath.exists():
        return filepath.read_text()
    return ""
