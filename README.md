# BookCrafter

Python-based book production system for creating professional PDF and EPUB books from Markdown.

## Features

- **PDF Generation** — WeasyPrint with CSS Paged Media (dot-leader TOCs, running headers, page counters)
- **EPUB3 Generation** — Valid e-books with embedded fonts
- **4-File Structure** — FrontMatter.md, Content.md, Backmatter.md, Decisions.md
- **Typography System** — 11+ font pairs, 5 density presets, smart quotes/dashes
- **Print-on-Demand** — Lulu and Pumbo specifications built-in
- **Quality Checks** — Pagination analysis for widows/orphans, preflight validation

## Installation

```bash
git clone https://github.com/yourusername/bookcrafter.git
cd bookcrafter
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Quick Start

1. Create an instance for your book:

```bash
mkdir -p instances/my-book/content instances/my-book/styles instances/my-book/output
```

2. Copy and edit the sample files:

```bash
cp content/*.md instances/my-book/content/
cp book_config.py instances/my-book/
```

3. Edit `instances/my-book/book_config.py` with your book's metadata.

4. Build:

```bash
python build.py build -i my-book -f pdf
python build.py build -i my-book -f epub
python build.py build -i my-book -f all
```

## Commands

```bash
# Build
python build.py build -i <instance> -f pdf|epub|html|all|screen

# With platform specs
python build.py build -i <instance> -t lulu:paperback_6x9_bw
python build.py build -i <instance> -t pumbo:a5_paperback_roman

# With typography
python build.py build -i <instance> -y playfair-lora:relaxed

# Quality checks
python build.py check -i <instance>
python build.py preflight -i <instance>

# Preview
python build.py preview -i <instance>
python build.py watch -i <instance>

# List available options
python build.py instances
python build.py lulu-products
python build.py pumbo-products
python build.py typography-fonts
python build.py typography-densities
```

## Project Structure

```
bookcrafter/
├── build.py              # Main CLI
├── book_config.py        # Default config template
├── content/              # Sample content files
├── styles/
│   ├── base.css          # Core typography
│   └── brand.css         # Default colors/fonts
├── fonts/                # Embedded fonts
├── instances/            # Your book projects (gitignored)
│   └── my-book/
│       ├── book_config.py
│       ├── content/
│       ├── styles/
│       │   └── brand.css # Color overrides
│       ├── assets/
│       └── output/       # Built files
└── tools/                # Quality checkers
```

## Content Structure

### FrontMatter.md
```markdown
# cover
::title:: Your Book Title
::subtitle:: A Subtitle
::author:: Author Name

# title-page
::title:: Your Book Title
...

# copyright
Copyright text...

# dedication
*For someone special.*

# toc
```

### Content.md
```markdown
# Part I: Introduction

## Chapter 1: Getting Started

Your content here...

## Chapter 2: Next Chapter
```

### Backmatter.md
```markdown
# bibliography
## References
...

# about-author
## About the Author
...
```

## Typography Presets

| Font Pair | Style |
|-----------|-------|
| playfair-lora | Classic serif |
| merriweather-lato | Modern mixed |
| inter-source-sans | Clean sans |
| libre-baskerville-crimson | Traditional |

Density: `tight`, `snug`, `normal`, `relaxed`, `loose`

Usage: `-y playfair-lora:relaxed`

## License

MIT
