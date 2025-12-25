# Technical Stack

> Last Updated: 2024-12-25
> Version: 1.1.0

## Application Framework

- **Framework:** Python 3.8+
- **Version:** 3.8+ (tested with 3.11+)

## Core Dependencies

### PDF Generation
- **WeasyPrint:** 67.0 - CSS Paged Media to PDF renderer
- **pydyf:** 0.12.1 - PDF library used by WeasyPrint
- **fonttools:** 4.61.1 - Font subsetting and embedding
- **pyphen:** 0.17.2 - Hyphenation library

### EPUB Generation
- **ebooklib:** 0.20 - EPUB3 creation library (with local patches)
- **lxml:** 6.0.2 - XML processing

### Content Processing
- **Markdown:** 3.10 - Markdown to HTML conversion
- **pymdown-extensions:** 10.19.1 - Extended markdown features (tables, fenced code)
- **pyyaml:** 6.0.3 - YAML frontmatter parsing
- **tinycss2:** 1.5.1 - CSS parser
- **tinyhtml5:** 2.0.0 - HTML5 parser

### PDF Analysis & Quality Assurance
- **pdfplumber:** 0.11.8 - PDF content extraction and analysis
- **pdfminer.six:** 20251107 - PDF text extraction
- **pypdfium2:** 5.2.0 - PDF rendering

### Supporting Libraries
- **pillow:** 12.0.0 - Image processing
- **brotli:** 1.2.0 - Compression
- **zopfli:** 0.4.0 - Compression
- **cryptography:** 46.0.3 - Security utilities
- **watchdog:** 6.0.0 - File system monitoring for live preview

## Project Structure

```
bookcrafter/
├── build.py              # Main build orchestrator (26KB)
├── book_config.py        # Book metadata configuration
├── content_parser.py     # 4-file content parser with smart typography
├── typography.py         # Typography system with font pairs & density presets
├── typography_processor.py # Smart typography transforms (quotes, dashes)
├── templates.py          # HTML template renderers
├── css_processor.py      # Format-specific CSS processing
├── lulu_specs.py         # Lulu POD platform specifications
├── pumbo_specs.py        # Pumbo.nl POD platform specifications
├── font_downloader.py    # Google Fonts downloader
├── font_metrics.py       # TTF font metrics extraction
├── epub_patched.py       # Patched ebooklib for BookCrafter
├── watch.py              # Live development server with hot reload
├── requirements.txt      # Python dependencies
├── content/
│   ├── FrontMatter.md    # Cover, title, copyright, dedication
│   ├── Content.md        # Main chapters
│   ├── Backmatter.md     # Bibliography, glossary, index
│   ├── Decisions.md      # Non-printable editorial notes
│   └── cover.png         # Cover image
├── styles/
│   ├── base.css          # Typography and page layout (19KB)
│   ├── brand.css         # Color scheme and font declarations
│   └── screen.css        # Screen/digital output overrides
├── fonts/                # Embedded TTF fonts (Montserrat, Baloo Bhai 2, etc.)
├── templates/            # HTML template files (if any)
├── tools/
│   ├── check_pagination.py  # Pagination quality checker (23KB)
│   └── preflight.py         # Production preflight validator (12KB)
└── venv/                 # Python virtual environment
```

## CLI Interface

```bash
# Build commands
python build.py build              # Build PDF (default)
python build.py build -f epub      # Build EPUB
python build.py build -f html      # Build HTML
python build.py build -f screen    # Build screen-optimized PDF
python build.py build -f all       # Build all formats

# Platform-specific builds
python build.py build -t lulu:paperback_6x9_bw      # Lulu 6x9 paperback
python build.py build -t pumbo:a5_paperback_roman   # Pumbo A5 paperback

# Typography presets
python build.py build -y playfair-lora:relaxed      # Font pair + density

# Quality checks
python build.py check              # Check pagination issues
python build.py preflight          # Production readiness check

# Development
python build.py preview            # Open HTML preview in browser
python build.py watch              # Live development with auto-rebuild

# Reference
python build.py lulu-products      # List Lulu trim sizes
python build.py pumbo-products     # List Pumbo formats
python build.py typography-fonts   # List font pairs
python build.py typography-densities  # List density presets
```

## Typography System

### Font Pairs (11+ combinations)
- **Serif:** Playfair Display + Lora, Libre Baskerville + Crimson Text
- **Sans:** Inter + Source Sans 3, Poppins + Open Sans
- **Mixed:** Merriweather + Lato, Source Serif + Inter

### Density Presets
- **tight** - Compact text for space efficiency
- **snug** - Slightly compact
- **normal** - Standard book typography
- **relaxed** - More generous spacing
- **loose** - Maximum readability

### Smart Typography Processing
- Curly quotes (straight → typographic)
- En/em dashes (-- → – , --- → —)
- Ellipsis (... → …)
- Non-breaking spaces (abbreviations, numerals)

## CSS Features Used

### CSS Paged Media
- `@page` rules for page size (A5, 6x9, etc.)
- `@page :left` / `@page :right` for facing pages
- Running headers via `string-set` and `string()`
- Page counters with `counter(page)`
- `leader(dotted)` for TOC dot leaders
- `target-counter()` for TOC page numbers

### Typography
- `@font-face` for custom font embedding
- `hyphens: auto` with hyphenation limits
- OpenType features (kerning, ligatures, oldstyle figures)
- `orphans` and `widows` control
- `break-inside: avoid` for keeping elements together

## Print-on-Demand Support

### Lulu.com
- 18+ trim sizes (pocket, digest, A5, US Trade, Royal, etc.)
- Multiple paper types (60#/80# cream/white)
- Binding types with page count constraints
- Cover dimension calculator

### Pumbo.nl
- European POD standard (metric measurements)
- Paper bulk factors for spine calculation
- Format specifications with bleed/margin rules

## Current Implementation Status

**Fully Implemented:**
- PDF generation with WeasyPrint and CSS Paged Media
- EPUB3 generation with embedded fonts
- 4-file content parsing with YAML frontmatter
- HTML template rendering for all sections
- Custom font loading with absolute paths
- 11+ font pair presets with 5 density levels
- Smart typography processing
- TOC generation with dot leaders
- Running headers from chapter titles
- Pagination analysis for widows/orphans
- Preflight production checks
- Live watch mode with hot reload
- Lulu and Pumbo POD specifications

**Not Yet Implemented:**
- Cover image generation with spine calculation
- Multiple book templates (novel, non-fiction, etc.)
- PDF/X-1a export for commercial printing
- CMYK color profile conversion
- Index generation

## Platform Support

- **macOS:** Fully tested
- **Linux:** Should work (WeasyPrint supported)
- **Windows:** Should work (WeasyPrint supported, may need GTK)

## Output Formats

| Format | Engine | Features |
|--------|--------|----------|
| PDF | WeasyPrint | Full CSS Paged Media, fonts, running headers |
| EPUB | ebooklib (patched) | Embedded fonts, chapter navigation |
| HTML | Built-in | Full styling, browser preview |
| Screen PDF | WeasyPrint | RGB colors, no bleed, digital-optimized |
